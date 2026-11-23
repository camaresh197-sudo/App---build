#!/usr/bin/env python3
"""Render the instrument sample bank from a General MIDI soundfont.

Writes godot/hula/audio/<inst>_r<midi>[_2].ogg, the names sound.gd's _pick() reads:
one root every 2 semitones across each instrument's RANGE, two takes per root
(take 2 is struck softer so repeated notes don't sound identical).

Every instrument is levelled to the same RMS target with a peak ceiling, so the
per-instrument TRIM balance in sound.gd can be 1.0 for rendered instruments.

Needs fluidsynth and soundfile:
    python3 render_bank.py --sf2 /usr/share/sounds/sf2/FluidR3_GM.sf2

Only the instruments listed in INSTRUMENTS are touched; drums, grunts and SFX stay as they are.
"""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / "godot" / "hula" / "audio"
SR = 48000           # matches the game mix rate, so playback resamples nothing
HOLD_S = 3.2          # sustain before note-off (matches the existing bank length)
TAIL_S = 3.0          # release captured after note-off, so the cut lands on silence
# Per-instrument RMS targets: the levels the mix was already balanced to
# (file RMS x the old sound.gd TRIM), so the mix balance is unchanged.
PEAK_CEIL_DB = -1.0

# RANGE from sound.gd, and a General MIDI program for each instrument.
INSTRUMENTS = {
    #  name        (RANGE)       GM program  target RMS dB
    "accordion": ((48, 84), 21, -23.4),
    "bass":      ((28, 64), 33, -16.0),
    "bell":      ((60, 100), 14, -36.3),
    "choir":     ((48, 84), 52, -20.3),
    "guitar":    ((40, 88), 25, -24.0),
    "pad":       ((40, 80), 89, -32.4),
    "trumpet":   ((52, 88), 56, -24.6),
    "violin":    ((55, 99), 40, -22.5),
}
TAKES = [("", 100), ("_2", 84)]   # (suffix, velocity)


def vlq(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def write_midi(path: Path, note: int, vel: int, prog: int, hold_s: float, tail_s: float):
    tpq, bpm = 480, 120
    ticks_per_s = tpq * bpm / 60
    trk = vlq(0) + bytes([0xC0, prog])
    trk += vlq(0) + bytes([0x90, note, vel])
    trk += vlq(int(hold_s * ticks_per_s)) + bytes([0x80, note, 0])
    trk += vlq(int(tail_s * ticks_per_s)) + b"\xff\x2f\x00"
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, tpq)
                     + b"MTrk" + struct.pack(">I", len(trk)) + trk)


def render_note(sf2: Path, note: int, vel: int, prog: int, tmp: Path, sr: int, dry: bool) -> np.ndarray:
    mid, wav = tmp / "n.mid", tmp / "n.wav"
    write_midi(mid, note, vel, prog, HOLD_S, TAIL_S)
    cmd = ["fluidsynth", "-ni", "-T", "wav", "-F", str(wav), "-r", str(sr)]
    if dry:
        # the Music bus carries the room, so the samples stay bone-dry: no baked reverb or chorus
        cmd += ["-o", "synth.reverb.active=no", "-o", "synth.chorus.active=no"]
    cmd += [str(sf2), str(mid)]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    x, _ = sf.read(wav, dtype="float32", always_2d=True)
    return x


def process(x: np.ndarray, rms_db: float) -> np.ndarray:
    """Trim silence, fade the edges, level to the instrument target, keep the peak under the ceiling."""
    mono = x.mean(axis=1)
    loud = np.where(np.abs(mono) > 10 ** (-50 / 20))[0]
    if loud.size == 0:
        return x[:0]
    a, b = loud[0], loud[-1] + 1
    x = x[a:b]
    fi = min(int(0.003 * SR), len(x) // 2)
    fo = min(int(0.1 * SR), len(x) // 2)
    x[:fi] *= np.linspace(0, 1, fi)[:, None]
    x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    rms = np.sqrt(np.mean(x ** 2)) + 1e-12
    gain = 10 ** (rms_db / 20) / rms
    peak = np.abs(x).max() + 1e-12
    gain = min(gain, 10 ** (PEAK_CEIL_DB / 20) / peak)
    return x * gain


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sf2", type=Path, required=True)
    ap.add_argument("--only", default="", help="comma list of instruments to render")
    ap.add_argument("--out", type=Path, default=AUDIO)
    ap.add_argument("--sr", type=int, default=SR, help="render rate; 48000 matches the game mix")
    ap.add_argument("--wet", action="store_true",
                    help="keep the soundfont's own reverb/chorus (default: render dry)")
    args = ap.parse_args()
    want = {s for s in args.only.split(",") if s} or set(INSTRUMENTS)
    total = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for inst, ((lo, hi), prog, rms_db) in INSTRUMENTS.items():
            if inst not in want:
                continue
            for midi in range(lo, hi + 1, 2):
                for suffix, vel in TAKES:
                    x = process(render_note(args.sf2, midi, vel, prog, tmp, args.sr, not args.wet), rms_db)
                    if x.size == 0:
                        raise SystemExit(f"{inst} r{midi}{suffix}: rendered silence")
                    sf.write(args.out / f"{inst}_r{midi}{suffix}.ogg", x, args.sr, format="OGG", subtype="VORBIS")
                    total += 1
            print(f"{inst}: {len(range(lo, hi + 1, 2)) * len(TAKES)} files")
    print(f"done: {total} samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
