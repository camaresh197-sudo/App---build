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
from scipy.signal import resample_poly

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base", help="path without _masterpre/_voxpost/_voxpre, or the .wav")
    ap.add_argument("--out", default="stems")
    ap.add_argument("--note", default="")
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
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sf.write(str(out / "instruments.flac"), inst, SR)
    sf.write(str(out / "voxbus_post.flac"), post, SR)
    sf.write(str(out / "voxbus_dry.flac"), dry, SR)
    meta = {"source_run": Path(a.base).name + f": mix capture at {sr0} Hz, rebuilt to {SR}",
            "sr": SR, "frames": int(n), "lag_samples": int(lag),
            "instruments": "master pre-limiter minus k * voxbus_post",
            "k_vox_in_master": round(k, 4),
            "note": a.note or "instruments change only if the arrangement/ducking changes; rebuild after any such change"}
    (out / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"lag={lag}  k={k:.4f}  {n} frames  {n / SR:.2f} s -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
