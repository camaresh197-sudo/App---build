#!/usr/bin/env python3
"""Envelopes for the TIMING tab graph: the sung line against the instruments.

For each timed line (B0-B2 by default) writes godot/hula/data/data_line_env.json with:
  vox   envelope of the rendered clip (the sound the phone plays)
  inst  envelope of the instrument stem over the same stretch of the track
  word  onset of each word in the clip (shipped onsets + the 0.15 s lead-in)
Both envelopes share one bin rate (ENV_HZ), so they line up bar for bar in the game.

Uses the stem and the clip positions from snip_from_stem.py (no Godot run). Re-run it when the
instruments, a clip or data_word_timing.json change.

  python3 tools/line_env.py [--lines B0,B1,B2] [--out godot/hula/data/data_line_env.json]
"""
import argparse, json, os, sys
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snip_from_stem import SR, load_clip, locate  # noqa: E402

VOX_LEAD = 0.15   # data_vox.json lead-in: the clip starts this long before its first word
ENV_HZ = 50       # envelope bins per second


def envelope(x, n_bins):
    """Peak per bin of the mono signal x, scaled to 0..1 for the whole line."""
    edges = np.linspace(0, len(x), n_bins + 1).astype(int)
    peaks = np.array([np.max(np.abs(x[a:b])) if b > a else 0.0 for a, b in zip(edges[:-1], edges[1:])])
    top = peaks.max() if peaks.max() > 0 else 1.0
    return np.round(peaks / top, 3).tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stems", default="stems")
    ap.add_argument("--clips-dir", default="godot/hula/audio/vox")
    ap.add_argument("--word-timing", default="godot/hula/data/data_word_timing.json")
    ap.add_argument("--out", default="godot/hula/data/data_line_env.json")
    ap.add_argument("--lines", default="B0,B1,B2")
    args = ap.parse_args()

    inst, _ = sf.read(os.path.join(args.stems, "instruments.flac"), dtype="float32", always_2d=True)
    dry, _ = sf.read(os.path.join(args.stems, "voxbus_dry.flac"), dtype="float32", always_2d=True)
    inst_m = inst.mean(axis=1)
    dry_m = dry[:, 0]
    timing = json.load(open(args.word_timing))["lines"]

    out = {"hz": ENV_HZ, "vox_lead": VOX_LEAD, "lines": {}}
    for lid in [s for s in args.lines.split(",") if s]:
        clip = load_clip(os.path.join(args.clips_dir, lid + ".ogg"))
        clip_m = clip[:, 0]
        t, score = locate(dry_m, clip_m)
        start = int(round(t * SR))
        span = min(len(clip_m), len(inst_m) - start)
        if score < 0.5 or span <= 0:
            print("WARNING: %s not located in the stem (score %.2f); skipped" % (lid, score))
            continue
        dur = span / SR
        n_bins = max(1, int(round(dur * ENV_HZ)))
        onsets = timing[lid]["onsets"]
        out["lines"][lid] = {
            "start": round(t, 4),
            "dur": round(dur, 4),
            "vox": envelope(clip_m[:span], n_bins),
            "inst": envelope(inst_m[start:start + span], n_bins),
            "word": [round(VOX_LEAD + float(o), 4) for o in onsets],
        }
        print("%s: stem %.3f s, score %.3f, %d bins" % (lid, t, score, n_bins))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
