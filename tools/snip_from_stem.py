#!/usr/bin/env python3
"""Cut a snip from the saved instrument stem and re-place the sung clips. No Godot run needed.

Usage: snip_from_stem.py --stems DIR --clips-dir godot/hula/audio/vox --start S --end E [--clips A0,B0] --out x.mp3
"""
import argparse, json, os, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import fftconvolve
SR = 44100

def load_clip(path):
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "2", "-ar", str(SR), tmp], check=True)
    x, _ = sf.read(tmp, dtype="float32"); os.remove(tmp); return x

def find_in_dry(dry_mono, clip_mono):
    c = clip_mono.astype(np.float64) - clip_mono.mean(); d = dry_mono.astype(np.float64) - dry_mono.mean()
    cc = fftconvolve(d, c[::-1], mode="valid")
    e = np.sqrt(fftconvolve(d ** 2, np.ones(len(c)), mode="valid")) + 1e-9
    ncc = cc / (e * np.linalg.norm(c) + 1e-9); i = int(np.argmax(ncc))
    return i / SR, float(ncc[i])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stems", required=True); ap.add_argument("--clips-dir", required=True)
    ap.add_argument("--clips", default=""); ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True); ap.add_argument("--min-score", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    meta = json.load(open(os.path.join(a.stems, "meta.json")))
    k = meta["k_vox_in_master"]
    stem, _ = sf.read(os.path.join(a.stems, "instruments.flac"), dtype="float32")
    vpost, _ = sf.read(os.path.join(a.stems, "voxbus_post.flac"), dtype="float32")
    dry, _ = sf.read(os.path.join(a.stems, "voxbus_dry.flac"), dtype="float32")
    n = min(len(stem), len(vpost), len(dry))
    stem, vpost, dry = stem[:n], vpost[:n], dry[:n]
    ids = [c for c in a.clips.split(",") if c] or sorted(os.path.splitext(f)[0] for f in os.listdir(a.clips_dir) if f.endswith(".ogg"))
    canvas = np.zeros_like(stem); n_placed = 0
    for cid in ids:
        clip = load_clip(os.path.join(a.clips_dir, cid + ".ogg"))
        t, score = find_in_dry(dry[:, 0], clip[:, 0])
        if score < a.min_score: continue
        i = int(round(t * SR)); canvas[i:i + len(clip)] += clip[: len(canvas) - i]; n_placed += 1
    a0, b0 = int(a.start * SR), min(n, int(a.end * SR))
    x = canvas[a0:b0].ravel(); y = vpost[a0:b0].ravel()
    g = float(np.dot(x, y) / np.dot(x, x))           # clip level -> game vox bus level
    vocals = k * g * canvas[a0:b0]                  # what the game's master actually receives
    mix = stem[a0:b0] + vocals
    fi = min(int(0.02 * SR), len(mix) // 4); mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = min(int(0.5 * SR), len(mix) // 4); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    pk = float(np.max(np.abs(mix)))
    if pk > 0.98: mix *= 0.98 / pk
    wav = os.path.splitext(a.out)[0] + ".wav"
    sf.write(wav, mix, SR, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k", a.out], check=True)
    os.remove(wav)
    print("clips placed %d, clip->vox gain %.3f, k %.3f, wrote %s (%.2f s, peak %.2f)" % (n_placed, g, k, a.out, len(mix) / SR, float(np.max(np.abs(mix)))))

if __name__ == "__main__":
    main()
