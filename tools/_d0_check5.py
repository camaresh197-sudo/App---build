import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps

v = ps.aligned_voice('en_US-amy-medium')
text = "Jeff lost his limp dick and balls"
ph = list(v.phonemize(text))[0]
m = v.config.phoneme_id_map
print('phonemes:', ' '.join(ph))
bad = [p for p in ph if p not in m]
print('NOT in map:', bad)
print('stress in map:', 'ˈ' in m, repr([k for k in m if 'ˈ' in k][:5]))
print('ɪ in map:', 'ɪ' in m, 'i' in m, 'I' in m)
