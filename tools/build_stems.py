#!/usr/bin/env python3
"""Rebuild stems/ from one Godot `mix` capture (see shotter.gd, "mix" mode).

Inputs are the files `shotter` writes next to the out wav:
  <name>.wav  (post-limiter master, unused here), <name>_masterpre.wav,
  <name>_voxpost.wav, <name>_voxpre.wav.

The bus captures start a few hundred samples apart, so the script finds the lag on a
vocal-heavy window, shifts the vox buses onto the master's timeline, then solves
instruments = masterpre - k * voxpost by least squares. Everything is resampled to 44.1 kHz
because tools/line_env.py and snip_from_stem.py assume it.

Usage (from the repo root):
  python tools/build_stems.py C:/path/to/mix_full
"""
import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.ndimage import median_filter
from scipy.signal import istft, resample_poly, stft

SR = 44100


def read(path: Path):
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    if sr != SR:
        x = resample_poly(x, SR, sr, axis=0).astype(np.float32)
    return x, sr


def find_lag(m: np.ndarray, v: np.ndarray, rate: int) -> int:
    """Samples the master is ahead of the vox capture, on a sung window."""
    a, b = int(19 * rate), int(31 * rate)
    a = max(0, min(a, len(m) - 1))
    b = max(a + 1, min(b, len(m)))
    best_lag, best = 0, None
    for lag in range(-2000, 2001, 4):
        if lag >= 0:
            x, y = m[a + lag:b], v[a:b - lag]
        else:
            x, y = m[a:b + lag], v[a - lag:b]
        c = float(np.dot(x, y))
        if best is None or c > best:
            best, best_lag = c, lag
    for lag in range(best_lag - 4, best_lag + 5):
        if lag >= 0:
            x, y = m[a + lag:b], v[a:b - lag]
        else:
            x, y = m[a:b + lag], v[a - lag:b]
        c = float(np.dot(x, y))
        if c > best:
            best, best_lag = c, lag
    return best_lag


def shift(x: np.ndarray, lag: int, n: int) -> np.ndarray:
    """Put x on the master timeline: out[i] = x[i - lag]."""
    out = np.zeros((n, x.shape[1]), dtype=x.dtype)
    if lag >= 0:
        out[lag:] = x[:n - lag]
    else:
        out[:n + lag] = x[-lag:n]
    return out


def tv_low_subtract(master: np.ndarray, post: np.ndarray, k0: float, rate: int = SR,
                    low_hz: float = 1000.0, smooth_frames: int = 19,
                    kmin: float = 0.3, kmax: float = 0.8) -> np.ndarray:
    """Instruments with a time-varying vocal gain below low_hz (Wren v11, W029/W030).

    A single gain fits above ~1 kHz, but below it the best gain per frame spreads
    (about 0.35 to 0.71), so the global subtraction over- and under-removes there.
    Below low_hz this uses a least-squares gain per STFT bin, median-smoothed over
    smooth_frames frames (~0.2 s) and clamped to [kmin, kmax]; elsewhere, and where
    the vocal bus is quiet, it keeps k0. Gains come from the mid signal and are
    applied to every channel.
    """
    n = min(len(master), len(post))
    mid_m = master[:n].mean(axis=1).astype(np.float64)
    mid_p = post[:n].mean(axis=1).astype(np.float64)
    nper = 2048
    f, _, Zm = stft(mid_m, fs=rate, nperseg=nper)
    _, _, P = stft(mid_p, fs=rate, nperseg=nper)
    low = f < low_hz
    ls = np.real(np.conj(P) * Zm) / (np.real(np.conj(P) * P) + 1e-12)
    ls = np.clip(median_filter(ls, size=(1, smooth_frames)), kmin, kmax)
    loud = np.abs(P) ** 2 > np.percentile(np.abs(P) ** 2, 50)
    kfin = np.where(low[:, None] & loud, ls, k0)
    out = np.zeros((n, master.shape[1]), dtype=np.float64)
    for c in range(master.shape[1]):
        _, _, Zc = stft(master[:n, c].astype(np.float64), fs=rate, nperseg=nper)
        _, _, Pc = stft(post[:n, c].astype(np.float64), fs=rate, nperseg=nper)
        Yc = Zc - kfin[:, :Zc.shape[1]] * Pc
        _, y = istft(Yc, fs=rate, nperseg=nper)
        out[:, c] = y[:n]
    return out.astype(np.float32)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base", help="path without _masterpre/_voxpost/_voxpre, or the .wav")
    ap.add_argument("--out", default="stems")
    ap.add_argument("--note", default="")
    ap.add_argument("--global-k", action="store_true",
                    help="old behaviour: one vocal gain for the whole track (default: time-varying gain below 1 kHz, Wren v11)")
    a = ap.parse_args()
    base = Path(a.base)
    if base.suffix:
        base = base.with_suffix("")
    master, sr0 = read(Path(str(base) + "_masterpre.wav"))
    post, _ = read(Path(str(base) + "_voxpost.wav"))
    dry, _ = read(Path(str(base) + "_voxpre.wav"))
    n = min(len(master), len(post), len(dry))
    master, post, dry = master[:n], post[:n], dry[:n]
    lag = find_lag(master.mean(axis=1), post.mean(axis=1), SR)
    post = shift(post, lag, n)
    dry = shift(dry, lag, n)
    denom = float(np.sum(post.astype(np.float64) ** 2))
    k = float(np.sum(master.astype(np.float64) * post.astype(np.float64)) / denom) if denom > 0 else 0.0
    inst = (master.astype(np.float64) - k * post.astype(np.float64)).astype(np.float32)
    if not a.global_k:
        inst = tv_low_subtract(master, post, k)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sf.write(str(out / "instruments.flac"), inst, SR)
    sf.write(str(out / "voxbus_post.flac"), post, SR)
    sf.write(str(out / "voxbus_dry.flac"), dry, SR)
    meta = {"source_run": Path(a.base).name + f": mix capture at {sr0} Hz, rebuilt to {SR}",
            "sr": SR, "frames": int(n), "lag_samples": int(lag),
            "instruments": "master pre-limiter minus k * voxbus_post" + ("" if a.global_k else " (time-varying gain below 1 kHz, Wren v11)"),
            "k_vox_in_master": round(k, 4),
            "note": a.note or "instruments change only if the arrangement/ducking changes; rebuild after any such change"}
    (out / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"lag={lag}  k={k:.4f}  {n} frames  {n / SR:.2f} s -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
