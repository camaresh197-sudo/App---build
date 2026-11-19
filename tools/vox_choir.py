#!/usr/bin/env python3
"""Render the victory-fanfare lyric clips into a small detuned choir.

The sung lines in the victory track are single synthetic takes.  Playing one
together with a near-identical take at the same pitch (the old "_lo" unison
double) comb-filtered into a metallic edge, and the takes themselves are bright
and harsh around 2-5 kHz.  This tool re-renders every clip as a small ensemble:

  * a zero-phase EQ front end (rumble out, warmth, a little presence, the harsh
    band pulled down and the fizz rolled off),
  * a simple de-esser and a gentle compressor,
  * six detuned, lightly-vibratoed doubles spread across the stereo field.

The detuned doubles use OLA time-stretch + windowed-sinc resampling, so the
pitch of a layer moves without changing the length of the line (the per-line
start offset in data_vox.json stays valid).  Output is stereo 44.1 kHz Ogg
Vorbis at the highest encoder quality, level-matched line to line.

The pristine input clips are the ones that shipped before this tool; recover
them from git (the commit before "Victory vocals: pre-rendered choir ...") and
point --src at that directory.  Running it against already-processed clips will
process them a second time, so keep a clean source.

Usage:
    python tools/vox_choir.py --src <dir-with-original-ogg> [--out <vox-dir>]
"""

import os
import sys
import glob
import numpy as np
import soundfile as sf

# ---------------------------------------------------------------- biquads (RBJ)
def _hp(fs, f0, Q=0.707):
    w0 = 2*np.pi*f0/fs; c = np.cos(w0); s = np.sin(w0); a = s/(2*Q)
    return [(1+c)/2, -(1+c), (1+c)/2], [1+a, -2*c, 1-a]

def _peak(fs, f0, Q, db):
    A = 10**(db/40); w0 = 2*np.pi*f0/fs; c = np.cos(w0); s = np.sin(w0); a = s/(2*Q)
    return [1+a*A, -2*c, 1-a*A], [1+a/A, -2*c, 1-a/A]

def _lowshelf(fs, f0, db, S=1.0):
    A = 10**(db/40); w0 = 2*np.pi*f0/fs; c = np.cos(w0); s = np.sin(w0)
    a = s/2*np.sqrt((A+1/A)*(1/S-1)+2); t = 2*np.sqrt(A)*a
    return ([A*((A+1)-(A-1)*c+t), 2*A*((A-1)-(A+1)*c), A*((A+1)-(A-1)*c-t)],
            [(A+1)+(A-1)*c+t, -2*((A-1)+(A+1)*c), (A+1)+(A-1)*c-t])

def _highshelf(fs, f0, db, S=1.0):
    A = 10**(db/40); w0 = 2*np.pi*f0/fs; c = np.cos(w0); s = np.sin(w0)
    a = s/2*np.sqrt((A+1/A)*(1/S-1)+2); t = 2*np.sqrt(A)*a
    return ([A*((A+1)+(A-1)*c+t), -2*A*((A-1)+(A+1)*c), A*((A+1)+(A-1)*c-t)],
            [(A+1)-(A-1)*c+t, 2*((A-1)-(A+1)*c), (A+1)-(A-1)*c-t])

def _resp(b, d, w):
    z1 = np.exp(-1j*w); z2 = z1*z1
    return (b[0] + b[1]*z1 + b[2]*z2) / (d[0] + d[1]*z1 + d[2]*z2)

def _apply(x, specs):
    """Zero-phase magnitude EQ: multiply the spectrum by |H| of each biquad."""
    n = len(x); w = 2*np.pi*np.fft.rfftfreq(n, 1.0)
    H = np.ones_like(w, dtype=complex)
    for b, d in specs:
        H *= _resp(b, d, w)
    return np.fft.irfft(np.fft.rfft(x)*np.abs(H), n)

# ------------------------------------------------- resample / time-stretch
def _resample_pos(x, pos, taps=32):
    h = taps//2
    k = np.arange(-h+1, h+1)
    idx = np.floor(pos).astype(np.int64)
    frac = pos - idx
    sinc = np.sinc(k[None, :] - frac[:, None])*np.kaiser(taps, 8.0)[None, :]
    sinc /= np.sum(sinc, axis=1, keepdims=True)
    ii = idx[:, None] + k[None, :]
    np.clip(ii, 0, len(x)-1, out=ii)
    return np.sum(x[ii]*sinc, axis=1)

def _resample_rate(x, sr_in, sr_out):
    n_out = int(round(len(x)*sr_out/sr_in))
    return _resample_pos(x, np.arange(n_out)*(sr_in/sr_out))

def _ola_stretch(x, factor, frame=2048, hop=512):
    """Overlap-add time-stretch: pitch unchanged, length x factor."""
    hop_out = max(1, int(round(hop*factor)))
    n_out = int(len(x)*factor) + frame
    out = np.zeros(n_out); wsum = np.zeros(n_out)
    win = np.hanning(frame)
    i = 0; o = 0
    while i + frame <= len(x) and o + frame <= n_out:
        out[o:o+frame] += x[i:i+frame]*win
        wsum[o:o+frame] += win
        i += hop; o += hop_out
    return out/np.maximum(wsum, 1e-6)

def _pitch(x, sr, cents, vib_cents=0.0, vib_hz=0.0):
    """Pitch x by `cents` (plus optional vibrato) keeping its length."""
    r0 = 2.0**(cents/1200.0)
    vd = (2.0**(vib_cents/1200.0) - 1.0) if vib_cents else 0.0
    xs = _ola_stretch(x, r0*(1.0 + vd*1.6))
    n = len(x); u = np.arange(n)
    rate = r0*(1.0 + vd*np.sin(2*np.pi*vib_hz*u/sr)) if vd else np.full(n, r0)
    pos = np.clip(np.cumsum(rate), 0, len(xs)-1)
    return _resample_pos(xs, pos)

# --------------------------------------------------- dynamics (moving-RMS)
def _rms_env(x, sr, ms):
    N = max(1, int(sr*ms/1000.0))
    return np.sqrt(np.maximum(np.convolve(x*x, np.ones(N)/N, mode='same'), 0.0))

def _compress(x, sr, thr_db=-20.0, ratio=2.5, atk_ms=12.0, rel_ms=160.0):
    e_db = 20*np.log10(np.maximum(_rms_env(x, sr, 20.0), 1e-6))
    over = np.maximum(e_db - thr_db, 0.0)
    gain = 10**((-over*(1.0 - 1.0/ratio))/20.0)
    return x*_rms_env(gain, sr, max(atk_ms, rel_ms))

def _deess(x, sr, band_lo=5000.0, thr_db=-24.0, max_db=-7.0):
    band = _apply(x, [_hp(sr, band_lo, 0.707)])
    e_db = 20*np.log10(np.maximum(_rms_env(band, sr, 12.0), 1e-6))
    gr = np.where(e_db > thr_db, np.maximum(max_db, -(e_db - thr_db)*0.6), 0.0)
    gain = _rms_env(10**(gr/20.0), sr, 6.0)
    return x - band + band*gain

# --------------------------------------------------------------- the ensemble
# (cents, vib_cents, vib_hz, delay_ms, gain, pan, tilt_lo_db, tilt_hi_db)
LAYERS = [
    (0,    0,  0.0,  0,  1.00,  0.00,  0.0,  0.0),   # centre
    (10,   5,  4.7,  8,  0.60, -0.50,  1.0, -1.0),
    (-11,  5,  5.3, 15,  0.60,  0.50, -1.0,  1.0),
    (19,   6,  5.0,  4,  0.42, -0.30,  0.6,  0.6),
    (-21,  6,  4.4, 21,  0.42,  0.30, -0.6, -0.6),
    (4,    4,  5.6, 12,  0.30, -0.16,  0.8,  0.0),
    (-5,   4,  4.9, 27,  0.30,  0.16, -0.8,  0.0),
]

def _build_choir(x, sr):
    out = np.zeros((len(x), 2))
    for (c, vib, vhz, dl, g, pan, tlo, thi) in LAYERS:
        y = x.copy() if (c == 0 and vib == 0) else _pitch(x, sr, c, vib, vhz)
        if dl > 0:
            d = int(sr*dl/1000.0)
            y = np.concatenate([np.zeros(d), y[:len(x)-d]])
        if tlo or thi:
            specs = []
            if tlo: specs.append(_lowshelf(sr, 400.0, tlo))
            if thi: specs.append(_highshelf(sr, 4000.0, thi))
            y = _apply(y, specs)
        out[:, 0] += y*g*np.sqrt(0.5*(1.0-pan))
        out[:, 1] += y*g*np.sqrt(0.5*(1.0+pan))
    return out

def render(x, sr_in, sr_out=44100):
    if sr_in != sr_out:
        x = _resample_rate(x, sr_in, sr_out)
    sr = sr_out
    specs = [
        _hp(sr, 45.0, 0.707),           # keep the low D2 fundamentals, drop sub-rumble
        _lowshelf(sr, 300.0, 1.5, S=0.9),
        _peak(sr, 1400.0, 0.9, 2.5),    # presence / intelligibility
        _peak(sr, 3500.0, 0.9, -2.0),   # tame the harsh, metallic edge
        _peak(sr, 6000.0, 1.5, -1.5),
        _highshelf(sr, 9000.0, -4.0, S=0.9),
    ]
    x = _apply(x, specs)
    x = _deess(x, sr)
    x = _compress(x, sr)
    f = int(sr*0.004)
    if f > 0:
        x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
    st = _build_choir(x, sr)
    st /= (np.max(np.abs(st)) + 1e-9)
    st = np.tanh(st*1.1)/np.tanh(1.1)               # gentle glue
    st /= (np.max(np.abs(st)) + 1e-9)
    st *= 0.16/(np.sqrt(np.mean(st**2)) + 1e-9)     # consistent line-to-line loudness
    pk = np.max(np.abs(st)) + 1e-9
    if pk > 0.9:
        st *= 0.9/pk
    return st.astype(np.float32)

def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vox = os.path.join(repo, "godot", "hula", "audio", "vox")
    src = vox; out = vox
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--src" and i+1 < len(args): src = args[i+1]
        if a == "--out" and i+1 < len(args): out = args[i+1]
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(src, "*.ogg")))
    if not files:
        print("no .ogg files in", src); return 1
    for p in files:
        name = os.path.splitext(os.path.basename(p))[0]
        x, sr = sf.read(p, always_2d=True)
        x = x.mean(axis=1).astype(np.float64)
        y = render(x, sr, 44100)
        dst = os.path.join(out, name + ".ogg")
        sf.write(dst, y, 44100, format='OGG', subtype='VORBIS', compression_level=0.0)
        print(f"{name:12s} {os.path.getsize(p):7d}B -> {os.path.getsize(dst):7d}B")
    return 0

if __name__ == "__main__":
    sys.exit(main())
