#!/usr/bin/env python3
"""Cut a snip of the victory track from the saved instrument stem and re-place the sung clips.

No Godot run and no re-rendering. The stem, the vocal buses and the clip positions are
cached in the stems folder, so a snip only reads the window it needs.

Usage:
  snip_from_stem.py --stems stems --clips-dir godot/hula/audio/vox --start 19.36 --end 33.5 \
                    [--clips A0,B0] [--out snip.wav|snip.mp3] [--rebuild-positions]

Files in --stems (made once per Godot run):
  instruments.flac   stem = pre-limiter master minus k * vox bus
  voxbus_post.flac   game vox bus (used for the level calibration)
  voxbus_dry.flac    dry vox bus (used to locate the clips)
  meta.json          k, source run, sample rate
  positions.json     cached clip positions + calibration gain (rebuilt when clips or stem change)
"""
import argparse, hashlib, json, os, subprocess
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, resample_poly

SR = 44100


def clip_key(clips_dir, ids, stems):
    """Fingerprint of the inputs that positions depend on: clip files, the dry bus and the stem."""
    h = hashlib.sha1()
    for cid in ids:
        p = os.path.join(clips_dir, cid + ".ogg")
        st = os.stat(p)
        h.update(("%s:%d:%d" % (cid, st.st_size, st.st_mtime_ns)).encode())
    for f in ("voxbus_dry.flac", "instruments.flac", "voxbus_post.flac"):
        st = os.stat(os.path.join(stems, f))
        h.update(("%s:%d:%d" % (f, st.st_size, st.st_mtime_ns)).encode())
    return h.hexdigest()


def load_clip(path):
    """Decode an OGG/WAV clip directly (no ffmpeg), stereo, at SR."""
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    if sr != SR:
        x = resample_poly(x, SR, sr, axis=0).astype(np.float32)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x


def locate(dry_mono, clip_mono):
    """Best start (s) of the clip in the dry vox bus and its normalised score. Float64 for stability."""
    c = clip_mono.astype(np.float64); c -= c.mean()
    d = dry_mono.astype(np.float64); d -= d.mean()
    cc = fftconvolve(d, c[::-1], mode="valid")
    e = np.sqrt(np.maximum(fftconvolve(d * d, np.ones(len(c)), mode="valid"), 0.0)) + 1e-9
    ncc = cc / (e * np.linalg.norm(c) + 1e-9)
    i = int(np.argmax(ncc))
    return i / SR, float(ncc[i])


def build_positions(args, ids, key, meta):
    """Search the dry bus once per stem/clip set; store positions and the full-track gain."""
    dry, _ = sf.read(os.path.join(args.stems, "voxbus_dry.flac"), dtype="float32")
    vpost, _ = sf.read(os.path.join(args.stems, "voxbus_post.flac"), dtype="float32")
    n = min(len(dry), len(vpost))
    dry, vpost = dry[:n, 0], vpost[:n, 0]         # both on one channel; vpost is duplicated to stereo below
    found, canvas = {}, np.zeros((n, 2), dtype=np.float32)
    for cid in ids:
        clip = load_clip(os.path.join(args.clips_dir, cid + ".ogg"))
        t, score = locate(dry, clip[:, 0])
        if score < args.min_score:
            continue
        found[cid] = {"t": round(t, 4), "score": round(score, 3)}
        i = int(round(t * SR))
        canvas[i:i + len(clip)] += clip[: n - i]
    x = canvas.ravel(); y = np.repeat(vpost, 2)   # vpost is the mono channel, duplicated to stereo
    gain = float(np.dot(x, y) / max(np.dot(x, x), 1e-12))
    data = {"key": key, "positions": found, "gain_full_track": round(gain, 5), "k": meta["k_vox_in_master"]}
    with open(os.path.join(args.stems, "positions.json"), "w") as f:
        json.dump(data, f, indent=1)
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stems", required=True)
    ap.add_argument("--clips-dir", required=True)
    ap.add_argument("--clips", default="", help="comma-separated ids (default: every .ogg in clips-dir)")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--min-score", type=float, default=0.5)
    ap.add_argument("--rebuild-positions", action="store_true", help="ignore the position cache")
    ap.add_argument("--out", required=True, help=".wav (default for speed) or .mp3")
    a = ap.parse_args()
    if a.end <= a.start:
        ap.error("--end must be after --start")

    meta = json.load(open(os.path.join(a.stems, "meta.json")))
    ids = [c for c in a.clips.split(",") if c] or sorted(
        os.path.splitext(f)[0] for f in os.listdir(a.clips_dir) if f.endswith(".ogg"))

    # 1 + 6: positions and calibration come from the cache unless the inputs changed
    key = clip_key(a.clips_dir, ids, a.stems)
    cache_p = os.path.join(a.stems, "positions.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    if a.rebuild_positions or cache.get("key") != key:
        cache = build_positions(a, ids, key, meta)
        print("positions rebuilt for %d clips" % len(cache["positions"]))
    k, gain = cache["k"], cache["gain_full_track"]

    # 3: read only the window from the stems
    info = sf.info(os.path.join(a.stems, "instruments.flac"))
    a0 = max(0, int(a.start * SR)); b0 = min(info.frames, int(a.end * SR))
    stem = sf.read(os.path.join(a.stems, "instruments.flac"), start=a0, frames=b0 - a0, dtype="float32", always_2d=True)[0]

    # 4: decode and place only the clips that overlap the window
    canvas = np.zeros_like(stem)
    placed = 0
    for cid, p in cache["positions"].items():
        if cid not in ids:
            continue
        i = int(round(p["t"] * SR))
        clip_len = sf.info(os.path.join(a.clips_dir, cid + ".ogg")).frames
        if i >= b0 or i + clip_len <= a0:
            continue  # outside the window: never decoded
        clip = load_clip(os.path.join(a.clips_dir, cid + ".ogg"))
        s = max(a0, i)
        e = min(b0, i + len(clip))
        canvas[s - a0:e - a0] += clip[s - i:e - i]
        placed += 1

    # 2 + 5 + 6: no ffmpeg; cached gain and k
    vocals = k * gain * canvas
    mix = stem + vocals
    fi = min(int(0.02 * SR), len(mix) // 4); mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = min(int(0.5 * SR), len(mix) // 4); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    pk = float(np.max(np.abs(mix)))
    if pk > 0.98:
        mix *= 0.98 / pk
    if a.out.lower().endswith(".mp3"):
        tmp = os.path.splitext(a.out)[0] + ".tmp.wav"
        sf.write(tmp, mix, SR, subtype="PCM_16")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libmp3lame", "-b:a", "192k", a.out], check=True)
        os.remove(tmp)
    else:
        sf.write(a.out, mix, SR, subtype="PCM_16")
    print("placed %d clips, gain %.3f, k %.3f, wrote %s (%.2f s, peak %.2f)" % (
        placed, gain, k, a.out, len(mix) / SR, float(np.max(np.abs(mix)))))


if __name__ == "__main__":
    main()
