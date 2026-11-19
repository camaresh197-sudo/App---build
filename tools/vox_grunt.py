#!/usr/bin/env python3
"""Synthesize the victory chorus singer's deep grunt ad-libs.

The chorus is a big, brassy show-tune belt (see vox_singer.py --style belt).
This tool makes a small *sample bank* of deep, funky "unh!" grunts for that same
character, pitched at every even root in RANGE["grunt"], so the sequencer can
trigger them on chord tones via the usual note/pitch machinery.

Each grunt is a short, formant-shaped voiced burst:
  * a rolled harmonic stack on a falling pitch contour (a quick scoop in, then
    the "unh" drop),
  * a little breath and a short 'h' noise burst at the onset,
  * a subharmonic + low-rate AM for the funk/R&B growl,
  * /V/ formants on a deep male tract, then the belt's brass drive and presence.

Output is stereo 44.1 kHz Ogg Vorbis in the audio pack.

Usage:
    python tools/vox_grunt.py [--out <audio-dir>] [--roots 40,42,...,52]
"""

import os
import sys
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vox_singer as V

SR = 44100


def _grunt(root_midi, seed=0, variant=0):
    f0 = 440.0 * 2.0 ** ((root_midi - 69) / 12.0)
    dur = 0.20 + 0.02 * variant
    n = int(SR * dur)
    t = np.arange(n) / SR
    # pitch: quick scoop in, then a gentle "unh" drop (stays near the chord tone)
    a = max(1, int(SR * 0.025))
    semi = np.empty(n)
    semi[:a] = np.linspace(-1.5 + 0.4 * variant, 0.4, a)
    semi[a:] = np.linspace(0.4, -1.6 - 0.3 * variant, n - a)
    f0c = f0 * 2.0 ** (semi / 12.0)
    ph = 2 * np.pi * np.cumsum(f0c) / SR
    # glottal source: a rolled harmonic stack
    src = np.zeros(n)
    h = 1
    while h * f0 < 5200.0:
        src += (1.0 / h ** 0.72) * np.sin(h * ph + h * 0.37 + seed)
        h += 1
    src /= (np.max(np.abs(src)) + 1e-9)
    rng = np.random.RandomState(1000 + seed)
    breath = rng.randn(n) * 0.16
    hb = np.zeros(n)
    hl = int(SR * 0.03)
    hb[:hl] = rng.randn(hl) * np.linspace(0.9, 0.0, hl)     # the 'h' onset
    sub = np.sin(0.5 * ph) * 0.05                           # a whisper of subharmonic
    am = 1.0 + 0.14 * np.sin(2 * np.pi * 38.0 * t)          # rough, funky (sidebands, no pitch shift)
    x = (src + sub + breath + hb) * am
    # vowel formants (/V/, a deep male tract)
    x = V._apply(x, [
        V._hp(SR, 60.0, 0.707),
        V._lowshelf(SR, 260.0, 5.0, S=0.8),     # chest, keep the fundamental strong
        V._peak(SR, 540.0, 3.5, 12.0),
        V._peak(SR, 1100.0, 5.0, 10.0),
        V._peak(SR, 2400.0, 7.0, 7.0),
        V._peak(SR, 3400.0, 9.0, 3.0),
        V._highshelf(SR, 4500.0, -6.0, S=0.9),
    ])
    # the belt's brass + presence so it belongs to the same character
    x = V._drive(x, 1.6, 0.35)
    x = V._apply(x, [V._peak(SR, 2700.0, 1.1, 2.5), V._highshelf(SR, 9000.0, -3.0, S=0.9)])
    # envelope: fast attack, body, release
    at = int(SR * 0.010)
    rl = int(SR * 0.075)
    env = np.ones(n)
    env[:at] = np.linspace(0.0, 1.0, at)
    env[-rl:] = np.linspace(1.0, 0.0, rl) ** 1.5
    x = x * env
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    # a touch of width (a close, centred ad-lib, not a wide double)
    st = np.stack([x, np.concatenate([np.zeros(int(SR * 0.003)), x[:n - int(SR * 0.003)]])], axis=1)
    return st.astype(np.float32)


def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(repo, "godot", "hula", "audio")
    roots = list(range(40, 52, 2))
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out = args[i + 1]
        elif args[i] == "--roots" and i + 1 < len(args):
            roots = [int(s) for s in args[i + 1].split(",") if s.strip()]
        i += 1
    os.makedirs(out, exist_ok=True)
    for root in roots:
        for variant, tag in ((0, ""), (1, "_2")):
            y = _grunt(root, seed=root + variant * 7, variant=variant)
            dst = os.path.join(out, "grunt_r%d%s.ogg" % (root, tag))
            sf.write(dst, y, SR, format="OGG", subtype="VORBIS", compression_level=0.0)
            print("grunt_r%d%s  %6dB  %5.2fs" % (root, tag, os.path.getsize(dst), len(y) / SR))
    return 0


if __name__ == "__main__":
    sys.exit(main())
