#!/usr/bin/env python3
"""Fast chorus renderer: instruments from a cached Godot run + vocals rebuilt offline.

Usage: chorus_fast.py <master.wav> <voxpost.wav> <vox_clip_dir> <out.mp3> [anchor_B0_s]

- stem = master - voxpost (instruments, ducking already applied by the game)
- vocals = vox clips placed at B0 anchor + 3.36 s * k (bars are contiguous in v-B)
- each clip position is refined by raw cross-correlation (+-60 ms)
- vocal gain is calibrated against the game's own Vox bus over the chorus
Only the vox clips change between runs; the Godot run is reused.
"""
import subprocess, sys, tempfile, os
import numpy as np
import soundfile as sf

SR = 44100
CHORUS_START, CHORUS_END = 19.45, 33.55     # cut window in track seconds
BAR2 = 2 * 16 * 0.105                        # two bars of v-B = 3.36 s
CLIPS = ["B0", "B1", "B2", "B3"]
CLIP_STEP = BAR2                              # B(k) follows B(k-1) every 2 bars

def load_clip(path):
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "2", "-ar", str(SR), tmp], check=True)
    x, _ = sf.read(tmp, dtype="float32")
    os.remove(tmp)
    return x

def place(canvas, clip, t):
    i = int(round(t * SR))
    j = min(len(canvas), i + len(clip))
    if i < 0 or i >= len(canvas):
        return
    canvas[i:j] += clip[: j - i]

def find_in_dry(dry_mono, clip_mono, near=None):
    """Best position of a clip in the dry vocal bus: normalised cross-correlation over the whole track."""
    from scipy.signal import fftconvolve
    c = clip_mono - clip_mono.mean()
    d = dry_mono - dry_mono.mean()
    cc = fftconvolve(d, c[::-1], mode="valid")
    e = np.sqrt(fftconvolve(d ** 2, np.ones(len(c)), mode="valid")) + 1e-9
    ncc = cc / (e * np.linalg.norm(c) + 1e-9)
    i = int(np.argmax(ncc))
    return i / SR, float(ncc[i])

def refine(target, clip, t, win=0.06):
    """Shift t by the lag (within +-win) that maximises correlation with the game's vox bus."""
    a = int(round((t - win) * SR)); b = int(round((t + win) * SR)) + len(clip)
    seg = target[max(0, a):b, 0]
    c = clip[:, 0]
    if len(seg) < len(c):
        return t
    cc = np.correlate(seg - seg.mean(), c - c.mean(), mode="valid")
    lag = int(np.argmax(cc)) + max(0, a) - int(round(t * SR))
    return t + lag / SR

def main():
    master_p, vox_p, clip_dir, out_p = sys.argv[1:5]
    anchor = float(sys.argv[5]) if len(sys.argv) > 5 else 19.506
    master, _ = sf.read(master_p, dtype="float32")
    vox, _ = sf.read(vox_p, dtype="float32")
    n = min(len(master), len(vox))
    master, vox = master[:n], vox[:n]
    stem = master - vox                       # instruments only (no vocals)

    canvas = np.zeros_like(master)
    times = {}
    dry_p = vox_p.replace("voxpost", "voxpre")
    dry = sf.read(dry_p, dtype="float32")[0] if os.path.exists(dry_p) else vox
    for name in CLIPS:
        clip = load_clip(os.path.join(clip_dir, name + ".ogg"))
        t, score = find_in_dry(dry[:, 0], clip[:, 0])
        print("  %s found at %.3f s (score %.2f)" % (name, t, score))
        times[name] = t
        place(canvas, clip, t)

    # calibrate the rebuilt vocals against the game's Vox bus over the chorus
    a = int(CHORUS_START * SR); b = int(CHORUS_END * SR)
    x = canvas[a:b].ravel(); y = vox[a:b].ravel()
    gain = float(np.dot(x, y) / max(1e-9, np.dot(x, x)))
    resid = np.sqrt(np.mean((gain * x - y) ** 2)) / max(1e-9, np.sqrt(np.mean(y ** 2)))
    print("clip positions (s):", {k: round(v, 3) for k, v in times.items()})
    print("vocal gain vs game vox bus: %.3f  (relative residual %.2f)" % (gain, resid))

    mix = stem[a:b] + gain * canvas[a:b]
    fade = int(0.02 * SR); out_len = len(mix)
    mix[:fade] *= np.linspace(0, 1, fade)[:, None]
    fo = int(0.5 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    wav = out_p.replace(".mp3", ".wav")
    sf.write(wav, mix, SR, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k", out_p], check=True)
    os.remove(wav)
    print("wrote", out_p, "%.2f s" % (out_len / SR), "peak %.2f" % np.max(np.abs(mix)))

if __name__ == "__main__":
    main()
