import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, soundfile as sf

x, sr = sf.read(str(pathlib.Path(__file__).resolve().parent.parent / 'build' / 'rev_A0.wav'))
if x.ndim > 1:
    x = x.mean(axis=1)
# "gay" starts at ~2.52 s; scan 2.4 s..end for sample-level jumps
a = int(2.4 * sr)
seg = x[a:]
d = np.abs(np.diff(seg))
k = int(np.argmax(d))
t = (a + k) / sr
print(f'sample rate {sr}, clip {len(x)/sr:.2f}s')
print(f'biggest sample jump: {d[k]:.3f} at {t:.3f}s (value {seg[k]:.3f} -> {seg[k+1]:.3f})')
# top 8 jumps and their times
idx = np.argsort(d)[-8:][::-1]
for i in idx:
    print(f'  jump {d[i]:.3f} at {(a + i) / sr:.3f}s')
# short-window envelope steps: RMS per 10ms
w = int(0.01 * sr)
rms = np.sqrt(np.convolve(seg ** 2, np.ones(w) / w, mode='same'))
steps = np.abs(np.diff(rms))
for i in np.argsort(steps)[-6:][::-1]:
    print(f'  rms step {steps[i]:.3f} at {(a + i) / sr:.3f}s')
