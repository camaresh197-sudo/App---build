#!/usr/bin/env python3
"""Do the vox clips hold notes? Within-run pitch wander: render vs original.

A sung vowel sits on one note (wander = vibrato only, ~30-40 cents). A spoken
vowel glides. If the render's voiced runs wander much more than the original's,
the clips read as pitched speech, not singing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import piper_sing as ps


def voiced_runs(mask, min_len=10):
    idx = np.where(mask)[0]
    if len(idx) == 0:
        return []
    br = np.where(np.diff(idx) > 1)[0]
    starts = np.concatenate(([idx[0]], idx[br + 1]))
    ends = np.concatenate((idx[br], [idx[-1]]))
    return [(int(s), int(e) + 1) for s, e in zip(starts, ends) if e + 1 - s >= min_len]


def wander(f0):
    """Per voiced run >=150 ms: cents std after removing the linear trend."""
    out = []
    for s, e in voiced_runs(f0 > 0, min_len=30):
        seg = f0[s:e].astype(float)
        v = seg > 0
        if v.sum() < 8:
            continue
        t = np.arange(len(seg))[v]
        c = 1200.0 * np.log2(seg[v] / np.median(seg[v]))
        a = np.polyfit(t, c, 1)
        out.append(float(np.std(c - np.polyval(a, t))))
    return out


print(f"{'clip':6} {'orig runs':>9} {'orig wander':>12}   {'render runs':>11} {'render wander':>13}")
for cid in ["A0", "A2", "B3", "C4", "tag3", "F1", "B0", "C0"]:
    xr = ps.load_wav_mono(ps.BACKUP / f"{cid}.ogg", ps.FS)
    x = ps.load_wav_mono(ps.VOX / f"{cid}.ogg", ps.FS)
    f0o, _, _ = ps.analyze(xr)
    f0r, _, _ = ps.analyze(x)
    wo = wander(f0o)
    wr = wander(f0r)
    mo = f"{np.mean(wo):5.0f}" if wo else "  -"
    mr = f"{np.mean(wr):5.0f}" if wr else "  -"
    print(f"{cid:6} {len(wo):9d} {mo:>9}c    {len(wr):11d} {mr:>11}c")
