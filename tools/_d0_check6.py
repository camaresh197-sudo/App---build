import sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps

audio, phonemes = ps.synth_aligned(ps.spoken('Jeff lost his limp dick and balls'), 'en_US-amy-medium', use_cache=False, length_scale=1.0)
nuc = ps.word_spans(phonemes)
grid = ('v-D', 0, 2, 7.6)
melody, spans = ps.grid_melody(*grid[:3], syllables=7, hold_to=grid[3])
print('phonemes:', len(phonemes), 'nuclei(word spans):', len(nuc), 'note spans:', len(spans))
print('word starts (s):', [round(s / ps.FS, 2) for s, _ in nuc])
