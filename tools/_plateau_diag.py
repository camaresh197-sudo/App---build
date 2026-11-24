#!/usr/bin/env python3
"""How well do plateau/glide segments track the shaped melody?"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import piper_sing as ps

for cid in ["A0", "A2", "tag3", "C4"]:
    x = ps.load_wav_mono(ps.BACKUP / f"{cid}.ogg", ps.FS)
    f0_c, _, _ = ps.analyze(x)
    nc = len(f0_c)
    melody = ps.shape_melody(ps.fill_gaps(f0_c), vib=0.65)
    ref = max(float(np.median(melody[melody > 0])), 1e-6)
    cents = 1200.0 * np.log2(np.maximum(melody, 1e-6) / ref)
    vmask = melody > 0
    segs = ps.melody_segments(cents, vmask)
    # reconstruction error over voiced frames: plateaus vs their note, glides exact
    step = np.zeros(nc)
    npl = ng = 0
    for (s, e, kind, n_) in segs:
        if kind == "plateau":
            step[s:e] = n_
            npl += 1
        else:
            step[s:e] = cents[s:e]
            ng += 1
    err = np.abs((cents - step)[vmask])
    held = sum(e - s for (s, e, k, _) in segs if k == "plateau") / max(1, sum(e - s for (s, e, k, _) in segs))
    print(f"{cid:5} plateaus {npl:3d}  glides {ng:3d}  held {held * 100:4.0f}%  "
          f"mean |err| {err.mean():5.1f}c  p95 {np.percentile(err, 95):5.1f}c  max {err.max():5.0f}c")
