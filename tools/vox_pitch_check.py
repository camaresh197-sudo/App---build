#!/usr/bin/env python3
"""Measure pitch discontinuities in the sung vox bank vs the originals.

The crack check: per-frame pitch movement (cents) and how many frames jump
more than 300 cents. NOTE: WORLD's harvest can flip octaves on resynthesized
audio, so a lone big-jump reading in a render can be detector error, not an
imposed step. Cross-check with piper_sing's slope cap (50 c/frame) before
believing it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import piper_sing as ps

VOX = ps.VOX
BACKUP = ps.BACKUP


def jumps(f0):
    v = (f0[:-1] > 0) & (f0[1:] > 0)
    d = np.abs(1200.0 * np.log2(np.maximum(f0[1:], 1e-6) / np.maximum(f0[:-1], 1e-6)))
    d = d[v]
    return (d.mean() if len(d) else 0.0), int((d > 300).sum()), (float(d.max()) if len(d) else 0.0)


print("clip     | orig: mean  big  max      | render: mean  big  max")
for cid in ["A0", "A2", "B3", "C4", "tag3", "F1", "B0", "C0"]:
    x = ps.load_wav_mono(VOX / f"{cid}.ogg", ps.FS)
    xo = ps.load_wav_mono(BACKUP / f"{cid}.ogg", ps.FS)
    f0r, _, _ = ps.analyze(x)
    f0o, _, _ = ps.analyze(xo)
    m1, b1, mx1 = jumps(f0r)
    m2, b2, mx2 = jumps(f0o)
    print(f"{cid:8} |  {m2:7.1f} {b2:4d} {mx2:7.0f}c  |  {m1:7.1f} {b1:4d} {mx1:7.0f}c")
