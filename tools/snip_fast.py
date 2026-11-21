#!/usr/bin/env python3
"""Fast offline snip renderer for the victory track: cached instruments + vocals rebuilt from clips.

Usage:
  snip_fast.py --master master.wav --voxpost voxpost.wav --voxpre voxpre.wav \
               --clips-dir godot/hula/audio/vox --start 19.45 --end 33.55 \
               [--clips B0,B1,B2,B3] [--min-score 0.5] --out snip.mp3

Inputs come from one Godot run: `godot ... -- out.wav 1 mix victory <secs>` writes
out.wav (master), out_voxpost.wav and out_voxpre.wav. The run needs a display (xvfb-run)
and the project imported first.

How it works
- Instruments = master minus voxpost (the game's own mix and ducking, reused as-is).
- Each vocal clip is located in the dry vox bus (voxpre) by normalised cross-correlation
  over the whole track, so no timing is assumed.
- The rebuilt vocals are scaled to the game's vox bus over the snip window (least squares).
- Only the instruments and the clip positions change between runs. Any change to instruments,
  ducking or the sung-bar pattern needs a fresh Godot run first.
"""
import argparse, os, subprocess, tempfile
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve

SR = 44100


def load_clip(path):
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "2", "-ar", str(SR), tmp], check=True)
    x, _ = sf.read(tmp, dtype="float32")
    os.remove(tmp)
    return x


def find_in_dry(dry_mono, clip_mono):
    """Best start time (s) of the clip in the dry vox bus, and its normalised score."""
    c = clip_mono - clip_mono.mean()
    d = dry_mono - dry_mono.mean()
    cc = fftconvolve(d, c[::-1], mode="valid")
    e = np.sqrt(fftconvolve(d ** 2, np.ones(len(c)), mode="valid")) + 1e-9
    ncc = cc / (e * np.linalg.norm(c) + 1e-9)
    i = int(np.argmax(ncc))
    return i / SR, float(ncc[i])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--master", required=True)
    ap.add_argument("--voxpost", required=True)
    ap.add_argument("--voxpre", required=True, help="dry vox bus, used to locate clips")
    ap.add_argument("--clips-dir", required=True)
    ap.add_argument("--clips", default="", help="comma-separated clip ids (default: every .ogg in clips-dir)")
    ap.add_argument("--start", type=float, required=True, help="snip start, seconds into the track")
    ap.add_argument("--end", type=float, required=True, help="snip end, seconds into the track")
    ap.add_argument("--min-score", type=float, default=0.5, help="ignore clips that do not match the track")
    ap.add_argument("--out", required=True, help="output .mp3 (a .wav is written next to it and removed)")
    a = ap.parse_args()
    if a.end <= a.start:
        ap.error("--end must be after --start")

    master, _ = sf.read(a.master, dtype="float32")
    vox, _ = sf.read(a.voxpost, dtype="float32")
    dry, _ = sf.read(a.voxpre, dtype="float32")
    n = min(len(master), len(vox), len(dry))
    master, vox, dry = master[:n], vox[:n], dry[:n]
    stem = master - vox

    ids = [c.strip() for c in a.clips.split(",") if c.strip()] or sorted(
        os.path.splitext(f)[0] for f in os.listdir(a.clips_dir) if f.endswith(".ogg"))

    canvas = np.zeros_like(master)
    placed = {}
    for cid in ids:
        clip = load_clip(os.path.join(a.clips_dir, cid + ".ogg"))
        t, score = find_in_dry(dry[:, 0], clip[:, 0])
        if score < a.min_score:
            print("  %-6s skipped (score %.2f)" % (cid, score))
            continue
        i = int(round(t * SR))
        canvas[i:i + len(clip)] += clip[: len(canvas) - i]
        placed[cid] = (t, score)
        print("  %-6s at %.3f s (score %.2f)" % (cid, t, score))
    if not placed:
        raise SystemExit("no clips matched the track; check --master/--voxpre and the clips")

    a0, b0 = int(a.start * SR), min(n, int(a.end * SR))
    x = canvas[a0:b0].ravel(); y = vox[a0:b0].ravel()
    gain = float(np.dot(x, y) / max(1e-9, np.dot(x, x))) if np.dot(x, x) > 0 else 1.0
    resid = np.sqrt(np.mean((gain * x - y) ** 2)) / max(1e-9, np.sqrt(np.mean(y ** 2)))
    print("vocal gain vs game vox bus: %.3f (relative residual %.2f)" % (gain, resid))

    mix = stem[a0:b0] + gain * canvas[a0:b0]
    fade = min(int(0.02 * SR), len(mix) // 4)
    mix[:fade] *= np.linspace(0, 1, fade)[:, None]
    fo = min(int(0.5 * SR), len(mix) // 4)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    peak = float(np.max(np.abs(mix)))
    if peak > 0.98:
        mix *= 0.98 / peak
    wav = os.path.splitext(a.out)[0] + ".wav"
    sf.write(wav, mix, SR, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k", a.out], check=True)
    os.remove(wav)
    print("wrote %s (%.2f s, peak %.2f)" % (a.out, len(mix) / SR, float(np.max(np.abs(mix)))))


if __name__ == "__main__":
    main()
