#!/usr/bin/env python3
"""A/B loudness check: Ryan renders vs the original vox clips."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from piper_sing import load_wav_mono, FS  # noqa: E402

vox = Path(__file__).resolve().parent.parent / "godot" / "hula" / "audio" / "vox"
bak = Path(__file__).resolve().parent / "vox_backup" / "originals"

print(f"{'clip':6} {'orig rms':>9} {'ryan rms':>9} {'diff dB':>8}")
for p in sorted(bak.glob("*.ogg")):
    a = load_wav_mono(p, FS)
    b = load_wav_mono(vox / p.name, FS)
    ra, rb = np.sqrt((a ** 2).mean()), np.sqrt((b ** 2).mean())
    d = 20 * np.log10(rb / ra) if ra > 0 else float("nan")
    print(f"{p.stem:6} {ra:9.4f} {rb:9.4f} {d:8.1f}")
