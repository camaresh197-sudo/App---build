import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps

v = ps.aligned_voice('en_US-patrick-medium')
for w in ['to', 'too', 'toe', 'two', 'tuh', 'tuh,', 'tou', 'tew', 'took', 'put', 'took,', 'to,', 'towe']:
    ph = list(v.phonemize(w))[0]
    print(f'{w!r:8}', ' '.join(ph))
