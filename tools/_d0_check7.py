import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps
import numpy as np

v = ps.aligned_voice('en_US-amy-medium')
text = "Jeff lost his limp dick and balls"
sents = v.phonemize(text)
ph = sents[0]
m = v.config.phoneme_id_map
bad = [p for p in ph if p not in m]
print('phonemes:', ' '.join(ph))
print('not in map:', bad)
ids = v.phonemes_to_ids(ph)
res = v.session.run(None, {"input": np.expand_dims(np.array(ids, dtype=np.int64), 0),
                           "input_lengths": np.array([len(ids)], dtype=np.int64),
                           "scales": np.array([0.667, 1.0, 0.8], dtype=np.float32)})
print('result outputs:', len(res), [np.shape(r) for r in res])
