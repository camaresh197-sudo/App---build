#!/usr/bin/env python3
"""Re-sing the victory-fanfare lyric clips as a *different* singer.

The sung lines in the victory track were a single low synthetic male voice
(median F0 ~ G2-D3).  This tool re-renders the lyric clips with WORLD (pyworld):
it edits pitch and spectral envelope (formants) independently, so a take can be
turned into a genuinely different vocalist while keeping the original words,
phrasing and timing.

Two styles are provided:

  * ``--style lead`` (the verses: A*, C*, tag*, orig_*)
      a bright female lead - F0 up an octave into a mezzo register, formants
      warped x1.20 (a female tract), a little delayed vibrato.

  * ``--style belt`` (the chorus: B0 B1 B2 B6 B7, reused by the v-F reprise)
      a flamboyant, theatrical show-tune belt - F0 up an octave into a big male
      belt/baritenor range with the *male* tract kept (formant x1.00, a clear
      ~3-semitone tract difference from the female verses), a wide vibrato, and
      a brassy saturation stage.  Extra, optional character on top:
        --lisp   soften only the sibilants (an interdental 's': the fricative
                 frames of the clean source are tilted down a few hundred Hz,
                 rolled off at the top and sat a touch lower).  Words/timing
                 untouched.
        --tipsy  a loose, tippy show-tune phrasing: a slow irregular pitch
                 waver, a small pitch droop at the end of each phrase, a tiny
                 diffuse smear on the consonants, and a hair of lateness.
        --dopey  an over-eager goofball: a slow sample-and-hold accent that
                 pushes some syllables a little too hard, plus a touch of
                 chesty/dim tone.  A dynamic performance cue only - it never
                 touches the words or the intelligibility, and it is a cartoon
                 big-lug, never an imitation of any real speech condition.

How it works (per clip):

  * WORLD (pyworld) analysis -> F0, spectral envelope (formants), aperiodicity.
    Pitch and the spectral envelope are then edited *independently*: F0 is
    transposed (default +12), smoothed (jitter removed) and given a delayed
    vibrato on the held notes; the spectral envelope is warped (default x1.20
    female / x1.00 male) to change the vocal tract.  Shifting pitch *and*
    formants is what turns the take into a genuinely different singer instead of
    a chipmunked version of the old one.
  * WORLD synthesis -> a clean, artefact-light vocal that still carries the
    original consonants.
  * A second take (a few cents and a hair of formant away, slightly delayed and
    panned) is layered for width.  This is a real detuned double, not the old
    unison random-offset double that comb-filtered into a metallic edge.
  * Tone shaping (high-pass, warmth, presence, de-ess, gentle compression),
    optional brass drive / lisp / tipsy / dopey stages, line-to-line loudness
    matching, then stereo 44.1 kHz Ogg Vorbis.

The pristine input clips are the pre-choir takes that shipped before the
"pre-rendered choir" commit (b4fbb53).  Recover them with:

    git archive --format=tar --output=voxsrc.tar b4fbb53~1 -- godot/hula/audio/vox
    tar -xf voxsrc.tar -C <tmpdir>          # -> <tmpdir>/godot/hula/audio/vox/*.ogg

and point --src at that directory.  Running the tool on the already-choired
clips would process them a second time, so keep a clean source.

Knobs left for tuning (all on the command line or in render()):
    --semis     how far the pitch moves (12 = up an octave, 7 = up a fifth)
    --formant   how far the formants move (1.20 = a female tract, 1.00 = male)
    --vib-cents / --vib-hz   the added singer's vibrato
    --lisp / --tipsy / --dopey   the chorus character stages (0..1)
    dbl_* in render()        the detuned double (level, detune, pan, delay)

Usage:
    python tools/vox_singer.py --src <pristine-ogg-dir> [--out <vox-dir>]
                               [--style lead|belt] [--only B0,B1,B2,B6,B7]
                               [--lisp 0.7] [--tipsy 1.0] [--dopey 1.0]
"""

import os
import sys
import glob
import argparse

import numpy as np
import soundfile as sf
import pyworld as pw

try:
    import librosa
    def _resample(x, sr_in, sr_out):
        if sr_in == sr_out:
            return x
        return librosa.resample(x.astype(np.float64), orig_sr=sr_in, target_sr=sr_out,
                                res_type="soxr_vhq")
except Exception:                                   # fall back to a plain sinc resampler
    def _resample(x, sr_in, sr_out):
        if sr_in == sr_out:
            return x
        n = int(round(len(x) * sr_out / sr_in))
        pos = np.arange(n) * (sr_in / sr_out)
        i0 = np.floor(pos).astype(np.int64)
        fr = pos - i0
        h = 24
        k = np.arange(-h + 1, h + 1)
        w = np.sinc(k[None, :] - fr[:, None]) * np.kaiser(2 * h, 8.0)[None, :]
        w /= np.sum(w, axis=1, keepdims=True)
        ii = np.clip(i0[:, None] + k[None, :], 0, len(x) - 1)
        return np.sum(x[ii] * w, axis=1)

SR_OUT = 44100
FP = 5.0                    # WORLD frame period, ms


# ------------------------------------------------------------------ WORLD edit
def _warp_sp(sp, ratio):
    """Move every formant up by `ratio` (sample the envelope at f/ratio)."""
    if abs(ratio - 1.0) < 1e-9:
        return sp
    n, m = sp.shape
    old = np.arange(m)
    new = old / ratio
    out = np.empty_like(sp)
    for i in range(n):
        out[i] = np.interp(new, old, sp[i])
    return out


def _smooth_f0(f0, n=5):
    """Median + light moving-average on the voiced runs: kills tracking jitter."""
    v = f0 > 0
    if not np.any(v):
        return f0
    y = f0.copy()
    idx = np.flatnonzero(v)
    seg = f0[idx]
    if len(seg) >= n:
        med = seg.copy()
        h = n // 2
        for i in range(len(seg)):
            a = max(0, i - h); b = min(len(seg), i + h + 1)
            med[i] = np.median(seg[a:b])
        k = np.hanning(9); k /= k.sum()
        med = np.convolve(med, k, mode="same")
        y[idx] = med
    return y


def _vibrato(f0, sr_frame, cents=22.0, rate=5.4, onset=0.22):
    """Add a delayed, gentle vibrato to the voiced notes (a singer's trait)."""
    v = f0 > 0
    if not np.any(v):
        return f0
    t = np.arange(len(f0)) / sr_frame
    depth = (2.0 ** (cents / 1200.0) - 1.0)
    # one continuous phase so the vibrato does not jump between notes
    mod = np.sin(2 * np.pi * rate * t)
    # fade in per voiced run so the start of each note stays steady
    env = np.zeros(len(f0))
    i = 0
    while i < len(v):
        if v[i]:
            j = i
            while j < len(v) and v[j]:
                j += 1
            L = j - i
            nf = max(1, int(onset * sr_frame))
            env[i:j] = np.clip(np.arange(L) / nf, 0, 1)
            i = j
        else:
            i += 1
    y = f0.copy()
    y[v] = f0[v] * (1.0 + depth * mod[v] * env[v])
    return y


def _waver(f0, sr_frame, cents, hz=1.7, hz2=2.5):
    """A slow, irregular wobble on top of the vibrato - the loose, 'tipsy' pitch
    drift of a performer who is enjoying the number a little too much."""
    v = f0 > 0
    if not np.any(v) or cents <= 0:
        return f0
    t = np.arange(len(f0)) / sr_frame
    d = 2.0 ** (cents / 1200.0) - 1.0
    mod = 0.6 * np.sin(2 * np.pi * hz * t) + 0.4 * np.sin(2 * np.pi * hz2 * t + 1.1)
    y = f0.copy()
    y[v] = f0[v] * (1.0 + d * mod[v])
    return y


def _droop(f0, sr_frame, cents, frac=0.4, max_s=0.25):
    """Let the end of every phrase sag a little (a downward glide) - the pitch
    droop of a slightly tiddly singer.  `cents` is negative."""
    v = f0 > 0
    if not np.any(v) or cents == 0:
        return f0
    y = f0.copy()
    n = len(v)
    i = 0
    while i < n:
        if v[i]:
            j = i
            while j < n and v[j]:
                j += 1
            L = j - i
            nl = min(int(max_s * sr_frame), max(1, int(L * frac)))
            if nl >= 2:
                r = np.linspace(0.0, 1.0, nl)
                r = r * r * (3.0 - 2.0 * r)          # smoothstep
                y[i + L - nl:j] = f0[i + L - nl:j] * (2.0 ** (cents * r / 1200.0))
            i = j
        else:
            i += 1
    return y


def _convert(x, sr, semis, formant, vib_cents, vib_hz, vib_onset=0.22, tipsy=0.0, ret_f0=False):
    x = np.ascontiguousarray(x.astype(np.float64))
    f0, t = pw.harvest(x, sr, f0_floor=65, f0_ceil=520, frame_period=FP)
    f0 = pw.stonemask(x, f0, t, sr)
    sp = pw.cheaptrick(x, f0, t, sr)
    ap = pw.d4c(x, f0, t, sr)
    sr_frame = 1000.0 / FP
    f0 = _smooth_f0(f0, 5)
    v = f0 > 0
    f0[v] = f0[v] * (2.0 ** (semis / 12.0))
    if vib_cents > 0:
        f0 = _vibrato(f0, sr_frame, vib_cents, vib_hz, vib_onset)
    if tipsy > 0.0:
        f0 = _waver(f0, sr_frame, 14.0 * tipsy, 1.7, 2.5)
        f0 = _droop(f0, sr_frame, -55.0 * tipsy, 0.4, 0.25)
    sp = _warp_sp(sp, formant)
    y = pw.synthesize(f0, sp, ap, sr, FP)
    y = y.astype(np.float64)
    return (y, f0, t) if ret_f0 else y


# --------------------------------------------------------------------- biquads
def _hp(fs, f0, Q=0.707):
    w0 = 2 * np.pi * f0 / fs; c = np.cos(w0); s = np.sin(w0); a = s / (2 * Q)
    return [(1 + c) / 2, -(1 + c), (1 + c) / 2], [1 + a, -2 * c, 1 - a]

def _peak(fs, f0, Q, db):
    A = 10 ** (db / 40); w0 = 2 * np.pi * f0 / fs; c = np.cos(w0); s = np.sin(w0); a = s / (2 * Q)
    return [1 + a * A, -2 * c, 1 - a * A], [1 + a / A, -2 * c, 1 - a / A]

def _lowshelf(fs, f0, db, S=1.0):
    A = 10 ** (db / 40); w0 = 2 * np.pi * f0 / fs; c = np.cos(w0); s = np.sin(w0)
    a = s / 2 * np.sqrt((A + 1 / A) * (1 / S - 1) + 2); t = 2 * np.sqrt(A) * a
    return ([A * ((A + 1) - (A - 1) * c + t), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - t)],
            [(A + 1) + (A - 1) * c + t, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - t])

def _highshelf(fs, f0, db, S=1.0):
    A = 10 ** (db / 40); w0 = 2 * np.pi * f0 / fs; c = np.cos(w0); s = np.sin(w0)
    a = s / 2 * np.sqrt((A + 1 / A) * (1 / S - 1) + 2); t = 2 * np.sqrt(A) * a
    return ([A * ((A + 1) + (A - 1) * c + t), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) - (A - 1) * c - t)],
            [(A + 1) - (A - 1) * c + t, 2 * ((A - 1) + (A + 1) * c), (A + 1) - (A - 1) * c - t])

def _resp(b, d, w):
    z1 = np.exp(-1j * w); z2 = z1 * z1
    return (b[0] + b[1] * z1 + b[2] * z2) / (d[0] + d[1] * z1 + d[2] * z2)

def _apply(x, specs):
    n = len(x); w = 2 * np.pi * np.fft.rfftfreq(n, 1.0)
    H = np.ones_like(w, dtype=complex)
    for b, d in specs:
        H *= _resp(b, d, w)
    return np.fft.irfft(np.fft.rfft(x) * np.abs(H), n)


# ------------------------------------------------------------------- dynamics
def _rms_env(x, sr, ms):
    N = max(1, int(sr * ms / 1000.0))
    return np.sqrt(np.maximum(np.convolve(x * x, np.ones(N) / N, mode="same"), 0.0))

def _compress(x, sr, thr_db=-20.0, ratio=2.5, atk_ms=12.0, rel_ms=160.0):
    e_db = 20 * np.log10(np.maximum(_rms_env(x, sr, 20.0), 1e-6))
    over = np.maximum(e_db - thr_db, 0.0)
    gain = 10 ** ((-over * (1.0 - 1.0 / ratio)) / 20.0)
    return x * _rms_env(gain, sr, max(atk_ms, rel_ms))

def _deess(x, sr, band_lo=6500.0, thr_db=-26.0, max_db=-8.0):
    band = _apply(x, [_hp(sr, band_lo, 0.707)])
    e_db = 20 * np.log10(np.maximum(_rms_env(band, sr, 12.0), 1e-6))
    gr = np.where(e_db > thr_db, np.maximum(max_db, -(e_db - thr_db) * 0.6), 0.0)
    gain = _rms_env(10 ** (gr / 20.0), sr, 6.0)
    return x - band + band * gain


# --------------------------------------------------------------------- brass / lisp
def _drive(x, drive=1.7, mix=0.45):
    """Soft saturation: the odd harmonics that read as a brassy, belted edge.
    Peak-preserving so the line-to-line loudness matching downstream still holds."""
    pk = np.max(np.abs(x)) + 1e-9
    xn = x / pk
    d = np.tanh(xn * drive) / np.tanh(drive)
    y = (1.0 - mix) * xn + mix * d
    return y * pk / (np.max(np.abs(y)) + 1e-9)


def _lisp(src, sr_src, y, amount=0.7, n_fft=1024, hop=256):
    """A light interdental lisp: soften only the sibilants.

    The sibilant frames are found on the *clean source* take (real neural
    fricatives: high spectral centroid, high spectral flatness, HF-dominated),
    then the matching frames of the converted take `y` get a spectral tilt that
    pulls the 's' peak down a few hundred Hz (fill 2-3.5 kHz, roll off above
    4.5 kHz) and sits a touch lower overall, so the s comes out slushy/'th'-ish
    instead of crisp.  Voiced frames, the words and the timing are untouched."""
    if amount <= 0.0:
        return y
    try:
        import librosa
    except Exception:
        return y

    def _sib_mask(x, sr):
        S = librosa.stft(x, n_fft=n_fft, hop_length=hop, window="hann")
        mag = np.abs(S) + 1e-12
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
        times = librosa.frames_to_time(np.arange(mag.shape[1]), sr=sr, hop_length=hop, n_fft=n_fft)
        tot = mag.sum(axis=0)
        cent = (mag * freqs[:, None]).sum(axis=0) / tot
        flat = np.exp(np.log(mag).mean(axis=0)) / (mag.mean(axis=0) + 1e-12)
        hf = mag[freqs >= 4500.0].sum(axis=0) / tot
        e = tot
        floor = 0.02 * np.percentile(e, 95.0)
        sib = (cent > 4000.0) & (flat > 0.30) & (hf > 0.35) & (e > floor)
        k = np.array([0.12, 0.76, 0.12])        # smooth the on/off so it never clicks
        m = np.clip(np.convolve(sib.astype(np.float64), k, mode="same"), 0.0, 1.0)
        return times, m

    t_src, m_src = _sib_mask(src, sr_src)
    Sy = librosa.stft(y, n_fft=n_fft, hop_length=hop, window="hann")
    magy = np.abs(Sy); phasey = np.angle(Sy)
    freqs = librosa.fft_frequencies(sr=SR_OUT, n_fft=n_fft)
    t_y = librosa.frames_to_time(np.arange(magy.shape[1]), sr=SR_OUT, hop_length=hop, n_fft=n_fft)
    m = np.interp(t_y, t_src, m_src, left=0.0, right=0.0)
    a = amount
    px = np.array([0.0, 1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6500.0, 9000.0, 13000.0, 20000.0])
    py = np.array([1.0, 1.0 + 0.12 * a, 1.0 + 0.30 * a, 1.0 + 0.22 * a, 1.0 - 0.05 * a,
                   1.0 - 0.35 * a, 1.0 - 0.62 * a, 1.0 - 0.80 * a, 1.0 - 0.88 * a, 1.0 - 0.88 * a])
    g = np.interp(freqs, px, py)
    dip = 10.0 ** (-(1.8 * a) / 20.0)           # sibilants sit a touch lower overall
    G = 1.0 + m[None, :] * (g[:, None] * dip - 1.0)
    return librosa.istft(magy * G * np.exp(1j * phasey), hop_length=hop, window="hann", length=len(y))


def _smear(x, sr, amount=0.14, dur_ms=8.0, seed=7):
    """A tiny diffuse smear so consonants land a touch soft/slurred (a tipsy
    diction), without adding noise or changing the length of the line."""
    if amount <= 0.0:
        return x
    n = max(2, int(sr * dur_ms / 1000.0))
    rng = np.random.RandomState(seed)
    ir = rng.randn(n) * np.exp(-np.arange(n) / (sr * 0.0022))
    lp = np.hanning(max(3, int(sr * 0.0015)) | 1)
    lp /= lp.sum()
    ir = np.convolve(ir, lp, mode="same")
    ir /= (np.sum(np.abs(ir)) + 1e-9)
    sm = np.convolve(x, ir, mode="full")[:len(x)]
    return (1.0 - amount) * x + amount * sm


def _accents(x, sr, amount=1.0, seed=3, seg_ms=170.0, db=2.5):
    """Over-eager, uneven commitment: a slow sample-and-hold gain that pushes some
    syllables a little too hard and backs off others (the goofball who belts the
    wrong word, then beams about it).  Smoothed so it never clicks; purely a
    dynamic performance cue, it never touches the words or the intelligibility."""
    if amount <= 0.0:
        return x
    n = len(x)
    seg = max(1, int(sr * seg_ms / 1000.0))
    rng = np.random.RandomState(seed)
    nseg = n // seg + 2
    g = rng.uniform(-1.0, 1.0, nseg)
    gg = np.repeat(g, seg)[:n]
    if len(gg) < n:
        gg = np.concatenate([gg, np.full(n - len(gg), gg[-1] if len(gg) else 0.0)])
    k = np.hanning(int(sr * 0.05) | 1)
    k /= k.sum()
    gg = np.convolve(gg, k, mode="same")
    gain = 10.0 ** ((db * amount * gg) / 20.0)
    return x * gain


# --------------------------------------------------------------------- the take
def render(x, sr, semis, formant, vib_cents=14.0, vib_hz=5.2, style="lead",
           drive=0.0, drive_mix=0.45, lisp=0.0, tipsy=0.0, dopey=0.0,
           dbl_cents=12.0, dbl_formant=1.04, dbl_delay=0.015, dbl_gain=0.33, dbl_pan=0.5):
    onset = 0.18 if style == "belt" else 0.22
    lead = _convert(x, sr, semis, formant, vib_cents, vib_hz, onset, tipsy)
    lead = _resample(lead, sr, SR_OUT)
    # second take: a few cents up and a hair brighter.  This is a *detuned*
    # double (a real chorus/ADT), so the two takes beat instead of sitting at the
    # same pitch and comb-filtering the way the old unison double did.
    dbl = _convert(x, sr, semis + dbl_cents / 100.0, formant * dbl_formant, vib_cents, vib_hz + 0.3, onset, tipsy)
    dbl = _resample(dbl, sr, SR_OUT)
    # align lengths
    n = min(len(lead), len(dbl))
    lead = lead[:n]; dbl = dbl[:n]
    d = int(SR_OUT * dbl_delay)
    dbl = np.concatenate([np.zeros(d), dbl[:n - d]]) if d < n else np.zeros(n)

    if style == "belt":
        # a stage belt: forward presence + twang ring, a little low-mid body, the
        # top tamed; the brass comes from the saturation stage below.
        specs = [
            _hp(SR_OUT, 80.0, 0.707),
            _lowshelf(SR_OUT, 200.0, 1.4, S=0.9),
            _peak(SR_OUT, 1000.0, 1.0, -1.0),
            _peak(SR_OUT, 2700.0, 1.0, 3.0),        # singer's formant / presence
            _peak(SR_OUT, 3600.0, 1.4, 2.2),        # twang / ring
            _peak(SR_OUT, 5200.0, 1.2, -2.5),       # tame harshness
            _highshelf(SR_OUT, 9000.0, -3.0, S=0.9),
        ]
        if dopey > 0.0:
            # a touch dim and chesty: the big warm lug, not the sharp operator
            specs += [
                _lowshelf(SR_OUT, 300.0, 1.0 * dopey, S=0.9),
                _peak(SR_OUT, 4500.0, 1.2, -1.0 * dopey),
                _highshelf(SR_OUT, 7000.0, -1.0 * dopey, S=0.9),
            ]
    else:
        # tone: female lead shaping (keep it bright but do not re-introduce the
        # 2-5 kHz harshness the old take was criticised for)
        specs = [
            _hp(SR_OUT, 75.0, 0.707),
            _lowshelf(SR_OUT, 260.0, 1.0, S=0.9),
            _peak(SR_OUT, 900.0, 1.1, -1.5),        # take out a little boxiness
            _peak(SR_OUT, 3200.0, 0.9, 1.2),        # presence / intelligibility
            _peak(SR_OUT, 5200.0, 1.2, -2.0),       # tame harshness
            _highshelf(SR_OUT, 9500.0, -3.0, S=0.9),
        ]
    lead = _apply(lead, specs)
    dbl = _apply(dbl, specs)
    if drive > 0.0:
        lead = _drive(lead, drive, drive_mix)
        dbl = _drive(dbl, drive, drive_mix)
    if lisp > 0.0:
        lead = _lisp(x, sr, lead, lisp)
        dbl = _lisp(x, sr, dbl, lisp)
    if tipsy > 0.0:
        lead = _smear(lead, SR_OUT, 0.14 * tipsy)
        dbl = _smear(dbl, SR_OUT, 0.14 * tipsy)
    if dopey > 0.0:
        lead = _accents(lead, SR_OUT, dopey)
        dbl = _accents(dbl, SR_OUT, dopey)
    lead = _deess(lead, SR_OUT, band_lo=(7200.0 if style == "belt" else 6500.0),
                  max_db=(-6.0 if style == "belt" else -8.0))
    dbl = _deess(dbl, SR_OUT, band_lo=(7200.0 if style == "belt" else 6500.0),
                 max_db=(-6.0 if style == "belt" else -8.0))
    lead = _compress(lead, SR_OUT)
    dbl = _compress(dbl, SR_OUT)

    st = np.zeros((n, 2))
    st[:, 0] += lead * 0.92 + dbl * dbl_gain * np.sqrt(0.5 * (1 - dbl_pan))
    st[:, 1] += lead * 0.92 + dbl * dbl_gain * np.sqrt(0.5 * (1 + dbl_pan))

    if tipsy > 0.0:
        # a hair behind the beat: nudge the whole line later, keeping its length
        # (and so data_vox.json's per-line offsets) exactly as they were.
        d = int(SR_OUT * 0.018 * tipsy)
        if d > 0:
            st = np.concatenate([np.zeros((d, 2)), st[:len(st) - d]])

    f = int(SR_OUT * 0.004)
    if f > 0:
        st[:f] *= np.linspace(0, 1, f)[:, None]
        st[-f:] *= np.linspace(1, 0, f)[:, None]
    st /= (np.max(np.abs(st)) + 1e-9)
    st = np.tanh(st * 1.1) / np.tanh(1.1)
    st /= (np.max(np.abs(st)) + 1e-9)
    st *= 0.17 / (np.sqrt(np.mean(st ** 2)) + 1e-9)
    pk = np.max(np.abs(st)) + 1e-9
    if pk > 0.92:
        st *= 0.92 / pk
    return st.astype(np.float32)


def _lead_offset(x, thr_db=-45.0):
    """Seconds of leading near-silence (what data_vox.json stores per line)."""
    mono = np.abs(x).mean(axis=1) if x.ndim > 1 else np.abs(x)
    thr = 10 ** (thr_db / 20.0)
    idx = np.flatnonzero(mono > thr)
    return float(idx[0] / SR_OUT) if len(idx) else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--style", default="lead", choices=["lead", "belt"])
    ap.add_argument("--semis", type=float, default=None)
    ap.add_argument("--formant", type=float, default=None)
    ap.add_argument("--vib-cents", type=float, default=None)
    ap.add_argument("--vib-hz", type=float, default=None)
    ap.add_argument("--drive", type=float, default=None)
    ap.add_argument("--lisp", type=float, default=0.0)
    ap.add_argument("--tipsy", type=float, default=0.0)
    ap.add_argument("--dopey", type=float, default=0.0)
    ap.add_argument("--only", default=None, help="comma-separated clip names (no .ogg) to process")
    a = ap.parse_args()
    if a.style == "belt":
        semis = 12.0 if a.semis is None else a.semis
        formant = 1.00 if a.formant is None else a.formant
        vib_cents = 55.0 if a.vib_cents is None else a.vib_cents
        vib_hz = 6.0 if a.vib_hz is None else a.vib_hz
        drive = 1.7 if a.drive is None else a.drive
        dbl_gain = 0.26
    else:
        semis = 12.0 if a.semis is None else a.semis
        formant = 1.20 if a.formant is None else a.formant
        vib_cents = 14.0 if a.vib_cents is None else a.vib_cents
        vib_hz = 5.2 if a.vib_hz is None else a.vib_hz
        drive = 0.0 if a.drive is None else a.drive
        dbl_gain = 0.33
    only = None if not a.only else set(s.strip() for s in a.only.split(",") if s.strip())
    out = a.out or a.src
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(a.src, "*.ogg")))
    files = [p for p in files if not os.path.basename(p).startswith(".")]
    if not files:
        print("no .ogg in", a.src); return 1
    offsets = {}
    for p in files:
        name = os.path.splitext(os.path.basename(p))[0]
        if name.endswith("_lo"):                 # old unison double, never re-used
            continue
        if only is not None and name not in only:
            continue
        x, sr = sf.read(p, always_2d=True)
        x = x.mean(axis=1).astype(np.float64)
        y = render(x, sr, semis, formant, vib_cents, vib_hz, style=a.style,
                   drive=drive, lisp=a.lisp, tipsy=a.tipsy, dopey=a.dopey, dbl_gain=dbl_gain)
        dst = os.path.join(out, name + ".ogg")
        sf.write(dst, y, SR_OUT, format="OGG", subtype="VORBIS", compression_level=0.0)
        off = _lead_offset(y)
        offsets[name] = off
        print("%-10s %5.2fs -> %5.2fs  off=%.4f  %7dB -> %7dB" % (
            name, len(x) / sr, len(y) / SR_OUT, off, os.path.getsize(p), os.path.getsize(dst)))
    print("\noffsets:", {k: round(v, 4) for k, v in sorted(offsets.items())})
    return 0


if __name__ == "__main__":
    sys.exit(main())
