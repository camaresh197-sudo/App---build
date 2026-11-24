import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps

v = ps.aligned_voice('en_US-amy-medium')
text = "Jeff lost his limp dick and balls"
ph = v.phonemize(text)[0]
m = v.config.phoneme_id_map
for p in ph:
    if p in m:
        continue
    print('BAD', repr(p), [hex(ord(c)) for c in p], '-> latin1:', end=' ')
    try:
        b = p.encode('latin-1')
        print(b, '-> utf8:', repr(b.decode('utf-8')), 'in map:', b.decode('utf-8') in m)
    except Exception as e:
        print('FAIL', e)
