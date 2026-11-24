"""Write the generated iris texture (amber centre, light collarette ring, fibres, dark limbal ring).
Run with plain python3 (numpy only), from a directory that has no file named inspect.py:
    python3 iris_png.py <out.png>
Then pack it with iris_pack.py. The original iris_tex_v38.png was never committed."""
import sys, zlib, struct
import numpy as np
N = 512
ys, xs = np.mgrid[0:N, 0:N]
u = (xs+0.5)/N-0.5; v = (ys+0.5)/N-0.5
r = np.sqrt(u*u+v*v)/0.5; a = np.arctan2(v, u)
fib = 0.5+0.5*np.sin(a*70+3*np.sin(a*9))*np.sin(a*23)
amber = np.array([0.62,0.36,0.10]); light = np.array([0.86,0.66,0.30]); dark = np.array([0.10,0.05,0.02])
t = np.clip((r-0.18)/0.82, 0, 1)[..., None]
col = amber*(1-t)+dark*t
col = col*(0.85+0.3*fib[..., None])
collar = np.exp(-((r-0.36)/0.05)**2)[..., None]
col = col*(1-0.5*collar)+light*0.5*collar
limbal = np.exp(-((r-0.95)/0.05)**2)[..., None]
col = col*(1-0.7*limbal)+dark*0.7*limbal
rgb = (np.clip(col, 0, 1)*255).astype(np.uint8)
raw = b''.join(b'\x00'+rgb[y].tobytes() for y in range(N))
def chunk(t, d): return struct.pack('>I', len(d))+t+d+struct.pack('>I', zlib.crc32(t+d) & 0xffffffff)
png = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 2, 0, 0, 0))+chunk(b'IDAT', zlib.compress(raw, 9))+chunk(b'IEND', b'')
open(sys.argv[1], 'wb').write(png)
