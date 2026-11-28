"""C6 prototype: render each word alone (clean attacks, no z->s context), warp each
onto its own note span, then join. If the ear approves, this folds into piper_sing."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np
import pyworld
import piper_sing as ps

CID = "C6"
VOICE = "en_US-patrick-medium"
grid = ps.CHORUS_GRID[CID]
line = ps.WORD_LINES[CID]
words = line["words"]
_mel, spans = ps.grid_melody(grid[0], grid[1], grid[2], syllables=len(words),
                             hold_to=grid[3] if len(grid) > 3 else 0.0,
                             word_secs=grid[4] if len(grid) > 4 else 0.0,
                             onsets=grid[5] if len(grid) > 5 else None)
n = int(round(grid[2] * 16 * (ps.VE * 1000.0 / ps.FRAME_MS)))
nsamp = int(round(n * ps.FS * ps.FRAME_MS / 1000.0))
out = np.zeros(nsamp, dtype=np.float64)
rng = np.random.default_rng(ps.SEED_OFFSET + 1)

prev_hz = 0.0
for k, wtext in enumerate(words):
    a, b, hz = spans[k]
    L = b - a
    audio, phon = ps.synth_aligned(ps.spoken(wtext), VOICE, True, length_scale=ps.GRID_LS)
    f0_r, sp_r, ap_r = ps.analyze(audio)
    nr = len(f0_r)
    nuc = ps.word_spans(phon)
    vs, ve = (nuc[0] if nuc else (0, nr))
    vsf, vef = vs / ps.FS * 1000.0 / ps.FRAME_MS, ve / ps.FS * 1000.0 / ps.FRAME_MS
    # consonant head sits before the vowel, in whatever room the previous word left
    head = min(vsf, max(6, a - (spans[k-1][1] if k else 0)))
    anchors_src = [0.0, vsf, vef, float(nr)]
    anchors_out = [float(a - head), float(a), float(min(a + 0.93 * L, n - 1)), float(b)]
    o0 = max(0, int(a - head))
    wlen = int(b - o0)
    src_idx = np.interp(np.arange(o0, b), anchors_out, anchors_src)
    src_idx = np.clip(src_idx, 0.0, float(nr - 1))
    sp_w = ps.warp_along(sp_r, src_idx)
    ap_w = ps.warp_along(ap_r, src_idx)
    f0_new = np.zeros(wlen)
    vstart = a - o0
    # legato from the previous note, then the word's own note with light vibrato
    kk = min(6, L - vstart) if L > vstart else 0
    t = np.arange(L - vstart)
    note = hz
    f0_new[vstart:] = note
    if prev_hz > 0 and kk > 0:
        cents = 1200.0 * np.log2(note / prev_hz)
        f0_new[vstart:vstart + kk] = prev_hz * np.power(2.0, cents * (np.arange(kk) + 1) / kk / 1200.0)
    if L - vstart >= 24:
        rate = float(rng.uniform(4.8, 6.2))
        depth = 20.0
        ramp = np.clip((t - 0.10 * (1000.0 / ps.FRAME_MS)) / (0.15 * (1000.0 / ps.FRAME_MS)), 0.0, 1.0)
        f0_new[vstart:] *= np.power(2.0, depth * np.sin(2.0 * np.pi * rate * t / (1000.0 / ps.FRAME_MS)) * ramp / 1200.0)
    y = pyworld.synthesize(f0_new, sp_w[:wlen], ap_w[:wlen], ps.FS, frame_period=ps.FRAME_MS)
    print(f"  {wtext:10s} y peak={float(np.max(np.abs(y))):.3f} rms={float(np.sqrt(np.mean(y**2))):.4f} wlen={wlen} f0[:8]={np.round(f0_new[:8],1)}")
    s0 = int(round(o0 * ps.FS * ps.FRAME_MS / 1000.0))
    seg = y[:min(len(y), nsamp - s0)].copy()
    f = int(0.006 * ps.FS)                      # the engine's declick: 6 ms fades both ends
    if len(seg) > 2 * f:
        seg[:f] *= np.linspace(0.0, 1.0, f)
        seg[-f:] *= np.linspace(1.0, 0.0, f)
    out[s0:s0 + len(seg)] += seg
    prev_hz = hz
    print(f"{wtext:10s} note={hz:6.1f}Hz span {a}-{b} voiced {vsf:.0f}-{vef:.0f} frames")

peak = float(np.max(np.abs(out))) or 1.0
out = out / peak * 0.89
import soundfile as sf
sf.write(r"C:\Users\Camden\Documents\Default Project\godot-build\build\C6_byword.wav", out, ps.FS)
print("wrote build/C6_byword.wav")
