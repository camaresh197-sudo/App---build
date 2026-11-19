#!/usr/bin/env python3
"""Re-sing the victory-fanfare lyric clips as a *different* singer.

The sung lines in the victory track were a single low synthetic male voice
(median F0 ~ G2-D3).  This tool re-renders every lyric clip as a bright female
lead so the chorus is a clearly distinct vocalist, while keeping the original
words, phrasing and timing intact.

How it works (per clip):

  * WORLD (pyworld) analysis -> F0, spectral envelope (formants), aperiodicity.
    The pitch and the spectral envelope are then edited *independently*:
      - F0 is transposed up (default +12 semitones, an octave) into a female
        mezzo register, smoothed (jitter removed) and given a little delayed
        vibrato on the held notes,
      - the spectral envelope is warped up (default x1.20) so the formants move
        from a male tract to a female one.  Shifting pitch *and* formants is
        what turns the take into a genuinely different singer instead of a
        chipmunked version of the old one.
  * WORLD synthesis -> a clean, artefact-light vocal that still carries the
    original consonants.
  * A second take (a few cents and a hair of formant away, slightly delayed and
    panned) is layered for width.  This is a real detuned double, not the old
    unison random-offset double that comb-filtered into a metallic edge.
  * Tone shaping (high-pass, warmth, presence, de-ess, gentle compression) and
    line-to-line loudness matching, then stereo 44.1 kHz Ogg Vorbis.

The pristine input clips are the pre-choir takes that shipped before the
"pre-rendered choir" commit (b4fbb53).  Recover them with:

    git archive --format=tar --output=voxsrc.tar b4fbb53~1 -- godot/hula/audio/vox
    tar -xf voxsrc.tar -C <tmpdir>          # -> <tmpdir>/godot/hula/audio/vox/*.ogg

and point --src at that directory.  Running the tool on the already-choired
clips would process them a second time, so keep a clean source.

Knobs left for tuning (all on the command line or in render()):
    --semis     how far the pitch moves (12 = up an octave, 7 = up a fifth)
    --formant   how far the formants move (1.20 = a female tract)
    --vib-cents / --vib-hz   the added singer's vibrato
    dbl_* in render()        the detuned double (level, detune, pan, delay)

Usage:
    python tools/vox_singer.py --src <pristine-ogg-dir> [--out <vox-dir>]
                               [--semis 12] [--formant 1.20]
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


def _convert(x, sr, semis, formant, vib_cents, vib_hz):
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
        f0 = _vibrato(f0, sr_frame, vib_cents, vib_hz)
    sp = _warp_sp(sp, formant)
    y = pw.synthesize(f0, sp, ap, sr, FP)
    return y.astype(np.float64)


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


# --------------------------------------------------------------------- the take
def render(x, sr, semis, formant, vib_cents=14.0, vib_hz=5.2,
           dbl_cents=12.0, dbl_formant=1.04, dbl_delay=0.015, dbl_gain=0.33, dbl_pan=0.5):
    lead = _convert(x, sr, semis, formant, vib_cents, vib_hz)
    lead = _resample(lead, sr, SR_OUT)
    # second take: a few cents up and a hair brighter.  This is a *detuned*
    # double (a real chorus/ADT), so the two takes beat instead of sitting at the
    # same pitch and comb-filtering the way the old unison double did.
    dbl = _convert(x, sr, semis + dbl_cents / 100.0, formant * dbl_formant, vib_cents, vib_hz + 0.3)
    dbl = _resample(dbl, sr, SR_OUT)
    # align lengths
    n = min(len(lead), len(dbl))
    lead = lead[:n]; dbl = dbl[:n]
    d = int(SR_OUT * dbl_delay)
    dbl = np.concatenate([np.zeros(d), dbl[:n - d]]) if d < n else np.zeros(n)

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
    lead = _deess(lead, SR_OUT)
    dbl = _deess(dbl, SR_OUT)
    lead = _compress(lead, SR_OUT)
    dbl = _compress(dbl, SR_OUT)

    st = np.zeros((n, 2))
    st[:, 0] += lead * 0.92 + dbl * dbl_gain * np.sqrt(0.5 * (1 - dbl_pan))
    st[:, 1] += lead * 0.92 + dbl * dbl_gain * np.sqrt(0.5 * (1 + dbl_pan))

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
    ap.add_argument("--semis", type=float, default=12.0)
    ap.add_argument("--formant", type=float, default=1.20)
    ap.add_argument("--vib-cents", type=float, default=14.0)
    ap.add_argument("--vib-hz", type=float, default=5.2)
    a = ap.parse_args()
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
        x, sr = sf.read(p, always_2d=True)
        x = x.mean(axis=1).astype(np.float64)
        y = render(x, sr, a.semis, a.formant, a.vib_cents, a.vib_hz)
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
