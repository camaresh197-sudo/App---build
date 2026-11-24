import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, soundfile as sf

x, sr = sf.read(str(pathlib.Path(__file__).resolve().parent.parent / 'build' / 'rev_A4.wav'))
if x.ndim > 1:
    x = x.mean(axis=1)
# "day" is the last word: onset ~2.52 s to end (3.36 s). Envelope onset detection.
a, b = int(2.45 * sr), len(x)
seg = x[a:b]
w = int(0.005 * sr)  # 5 ms windows
rms = np.array([np.sqrt((seg[i:i + w] ** 2).mean()) for i in range(0, len(seg) - w, w)])
thr = 0.25 * rms.max()
on = rms > thr
d = np.diff(on.astype(np.int8))
starts = np.where(d == 1)[0] + 1
times = [(a + s * w) / sr for s in starts]
print('onsets after 2.45s:', [f'{t:.3f}' for t in times[:14]])
if len(times) > 2:
    gaps = np.diff(times)
    print('burst gaps (ms):', [f'{g*1000:.0f}' for g in gaps[:12]])
    print('median gap (ms):', f'{np.median(gaps)*1000:.0f}')
# F0 in the day region via autocorrelation on 30ms hops
hop, win = int(0.010 * sr), int(0.030 * sr)
f0s = []
for i in range(0, len(seg) - win, hop):
    fr = seg[i:i + win]
    if np.sqrt((fr ** 2).mean()) < thr:
        f0s.append(0.0); continue
    ac = np.correlate(fr, fr, 'full')[sr // 2:]
    if len(ac) <= 20:
        f0s.append(0.0); continue
    pk = int(np.argmax(ac[20:])) + 20
    f0s.append(sr / pk if ac[pk] > 0.3 * ac[0] else 0.0)
print('f0 hop (Hz):', [f'{f:.0f}' if f else '--' for f in f0s[:30]])
