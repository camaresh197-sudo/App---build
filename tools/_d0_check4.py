import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps

for voice in ['en_US-amy-medium', 'en_US-bobby-medium', 'en_US-bryce-medium']:
    v = ps.aligned_voice(voice)
    m = v.config.phoneme_id_map
    missing = [ch for ch in ['ˈ', 'ɪ', 'ɔ', 'ʊ', 'ə', 'ɜ', 'ɹ', 'ɐ', 'θ', 'ð'] if ch not in m]
    print(voice, 'total:', len(m), 'missing:', missing)
    print('  id-map sample:', ''.join(sorted(m.keys())[:40]))
