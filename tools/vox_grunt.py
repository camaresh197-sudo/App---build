#!/usr/bin/env python3
"""Synthesize the victory chorus singer's deep grunt ad-libs.

The chorus is a big, brassy show-tune belt (see vox_singer.py --style belt).
This tool makes a small *sample bank* of deep, funky "unh!" grunts for that same
character, pitched at every even root in RANGE["grunt"], so the sequencer can
trigger them on chord tones via the usual note/pitch machinery.

Each grunt is a short, formant-shaped voiced burst:
  * a rolled harmonic stack on a violent pitch contour (a crowing scoop UP into
    the hit, then a long ugly "unh" drop),
  * a hard 'h' noise burst at the onset,
  * a fat subharmonic + deep AM for the funk/R&B growl,
  * wide-open /UH-AH/ formants on a deep male tract, then the belt's brass drive,
    presence and a hard tanh squash so it stays loud for its whole length.

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
    # long enough to read as a whole word, not a blip
    dur = 0.22 + 0.02 * variant      # a grunt is a short vocal burst, not a held tone
    n = int(SR * dur)
    t = np.arange(n) / SR
    # pitch: a fast crowing scoop UP into the hit, then a long ugly "unh" drop.
    # The body still resolves onto the chord root (the drop stays under a whole tone).
    a = max(1, int(SR * 0.020))
    b = max(a + 1, int(SR * 0.050))
    semi = np.empty(n)
    semi[:a] = np.linspace(-3.0 - 0.8 * variant, 1.5, a)      # a short scoop up into the hit
    semi[a:b] = np.linspace(1.5, 1.0, b - a)
    semi[b:] = np.linspace(1.0, -4.0 - 0.7 * variant, n - b)  # the "uh" falls away
    f0c = f0 * 2.0 ** (semi / 12.0)
    ph = 2 * np.pi * np.cumsum(f0c) / SR
    # glottal source: a bright, rolled harmonic stack (cartoon big-lug, not polite)
    src = np.zeros(n)
    h = 1
    while h * f0 < 3500.0:          # fewer high harmonics: less buzz
        src += (1.0 / h ** 1.2) * np.sin(h * ph + h * 0.37 + seed)
        h += 1
    src /= (np.max(np.abs(src)) + 1e-9)
    rng = np.random.RandomState(1000 + seed)
    breath = rng.randn(n) * 0.15
    sub = np.sin(0.5 * ph) * 0.22            # a little subharmonic: chest weight, not a sub-thump
    # deep 34 Hz AM growl (sidebands, no pitch shift) + a little 68 Hz grit
    am = np.ones(n)                  # no 34/68 Hz wobble: that was the buzz
    x = (src + sub + breath) * am
    # vowel formants: wide-open /UH-AH/, deep male tract
    x = V._apply(x, [
        V._hp(SR, 72.0, 0.707),                  # keep the chest, lose the sub that eats the bass and limiter
        V._lowshelf(SR, 300.0, 7.0, S=0.9),      # chest, keep the fundamental strong
        V._peak(SR, 620.0, 2.2, 13.0),
        V._peak(SR, 1180.0, 3.5, 12.0),
        V._peak(SR, 2500.0, 6.0, 9.0),
        V._peak(SR, 3300.0, 8.0, 6.0),
        V._highshelf(SR, 6000.0, -3.0, S=0.9),
    ])
    # envelope: near-instant attack, body, quick-but-not-clicky release
    at = int(SR * 0.004)
    rl = int(SR * 0.090)
    env = np.ones(n)
    env[:at] = np.linspace(0.0, 1.0, at)
    env[-rl:] = np.linspace(1.0, 0.0, rl) ** 2.0
    x = x * env
    # the belt's brass drive and a hard tanh squash so the body stays loud and dirty
    x = V._drive(x, 1.6, 0.4)
    x = np.tanh(x * (1.6 / (np.max(np.abs(x)) + 1e-9))) / np.tanh(1.6)
    # fixed body loudness before the consonant (the body is re-normalized after
    # the 'h' below, so this only sets a stable starting point):
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * (10.0 ** (-12.5 / 20.0))
    # hard 'h' plosive on the very front: a short bright burst that owns the 0.98
    # peak, so the hit reads as a consonant + vowel and pokes out of the mix.
    hl = int(SR * 0.014)
    click = np.diff(rng.randn(hl), prepend=0.0) * np.exp(-np.arange(hl) / (SR * 0.004))
    click = V._apply(click, [V._hp(SR, 700.0, 0.707), V._peak(SR, 2400.0, 0.9, 4.0)])
    click /= (np.max(np.abs(click)) + 1e-9)
    fade = np.linspace(1.0, 0.0, hl) ** 1.5
    x[:hl] = x[:hl] * (1.0 - fade) + click * 0.98
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.98
    # Body loudness: the 'h' owns the peak, so a peak-normalized take leaves the
    # vowel ~12 dB down and the Vox bus compressor + master limiter then duck it
    # (the click retriggers them for the whole word). Scale the vowel body itself
    # to a fixed RMS after the consonant, so the *body* survives the gain chain.
    body = x[hl:].copy()
    bpk = np.max(np.abs(body)) + 1e-9
    body = np.tanh(body / bpk * 2.5) / np.tanh(2.5)     # flatten the AM peaks a little
    body *= (10.0 ** (-6.0 / 20.0)) / (np.sqrt(np.mean(body ** 2)) + 1e-9)
    body = np.clip(body, -0.99, 0.99)                    # keep every root's vowel body at the same RMS
    x[hl:] = body
    x = np.clip(x, -0.99, 0.99)
    # The old bank's 16 kHz hiss came from the broken high shelf; the hard tanh and
    # the 'h' still leave a fizzy top octave. The formants live below 4 kHz, so a
    # gentle 9-12 kHz low-pass keeps the body and removes the fizz/hiss.
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1.0 / SR)
    w = np.ones_like(fr)
    w[fr >= 12000.0] = 0.0
    tr = (fr > 9000.0) & (fr < 12000.0)
    w[tr] = 0.5 * (1.0 + np.cos(np.pi * (fr[tr] - 9000.0) / 3000.0))
    x = np.fft.irfft(X * w, n=len(x))
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.98
    # a touch of width (a close, centred ad-lib, not a wide double)
    dl = int(SR * (0.004 + 0.001 * variant))
    st = np.stack([x, np.concatenate([np.zeros(dl), x[:n - dl]])], axis=1)
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
