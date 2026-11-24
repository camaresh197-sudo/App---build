import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps

v = ps.aligned_voice('en_US-amy-medium')
chunks = list(v.synthesize('Jeff lost his limp dick and balls', syn_config=None, include_alignments=True))
c = chunks[0]
print('chunk type:', type(c).__name__)
print('has attr phoneme_alignments:', hasattr(c, 'phoneme_alignments'))
pa = getattr(c, 'phoneme_alignments', None)
print('alignments:', None if pa is None else len(pa))
import piper
print('piper version:', getattr(piper, '__version__', '?'))
print('piper pkg:', piper.__file__)
