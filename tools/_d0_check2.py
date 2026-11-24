import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps

for voice in ['en_US-amy-medium', 'en_US-bobby-medium', 'en_US-bryce-medium']:
    for ls in (1.0, 2.6):
        audio, phonemes = ps.synth_aligned(ps.spoken('Jeff lost his limp dick and balls'), voice, use_cache=False, length_scale=ls)
        a2, ph2 = ps.synth_aligned(ps.spoken("I am Jeff and I'm so gay"), voice, use_cache=False, length_scale=ls)
        print(voice, ls, 'D0 ph:', len(phonemes), 'A0 ph:', len(ph2), 'D0 aud:', None if audio is None else len(audio))
