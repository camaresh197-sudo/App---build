import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps

v = ps.aligned_voice('en_US-bryce-medium')
m = v.config.phoneme_id_map
for w in ['I', 'am', "I'm", 'gay']:
    ph = list(v.phonemize(w))[0]
    bad = [p for p in ph if p not in m]
    print(f'{w!r}:', ' '.join(ph), '| not in map:', bad)
print('map has:', {c: (c in m) for c in ['æ', 'ɛ', 'e', 'ɐ', 'a']})
