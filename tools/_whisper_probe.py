import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps
import numpy as np, soundfile as sf

a, ph = ps.synth_aligned(ps.spoken("I am Jeff and I'm so gay"), 'en_US-bryce-medium', use_cache=False, length_scale=1.0)
sf.write(str(pathlib.Path(__file__).resolve().parent.parent / 'build' / 'A0_raw_bryce.wav'), a, ps.FS)
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
import scipy.signal as ss
a16 = ss.resample_poly(a, 16000, ps.FS)
x16 = (np.asarray(a16) * 32768.0).astype(np.int16)
segs, _ = m.transcribe(x16, language='en', beam_size=5)
print('bryce raw ->', ' '.join(s.text for s in segs))
