import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import piper_sing as ps

text = "Jeff lost his limp dick and balls"
audio, phonemes = ps.synth_aligned(ps.spoken(text), 'en_US-amy-medium', use_cache=False, length_scale=1.0)
nuc = ps.word_spans(phonemes)
grid = ('v-D', 0, 2, 7.6)
melody, spans = ps.grid_melody(*grid[:3], syllables=len(ps.words_of(text)), hold_to=grid[3])
print('words:', len(ps.words_of(text)), 'nuclei:', len(nuc), 'note spans:', len(spans))
print('nuclei starts (s):', [round(s / ps.FS, 2) for s, _ in nuc])
print('note starts (s):', [round(a * ps.FRAME_MS / 1000, 2) for a, b, _ in spans])
