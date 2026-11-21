# VOCAL.md — the victory singer

Everything that turns lyric text into the sung clips in `audio/vox/`. Read this
before touching `tools/piper_sing.py`, `data/data_phonics.json` or the vocal
mix. The audio-bus side is in `AUDIO_BUS_ARCHITECTURE.md`.

## Files

| Path | Role |
|---|---|
| `data/data_lyrics.json` | the words, one line per clip id |
| `data/data_vox.json` | which clip plays on which section bar, plus lead-in |
| `data/data_phonics.json` | the engine's word table: `say`, `ipa`, `pron`, `syllables`, optional `phonics`/`nato` |
| `data/data_victory.json` | the song: chords, melody, sections, bars |
| `audio/vox/<id>.ogg` | the rendered clips (44.1 kHz mono) |
| `tools/piper_sing.py` | the singer (Piper speech → WORLD singing) |
| `tools/phonics.py` | rebuilds `data_phonics.json` |
| `tools/lyrics_doc.py` | rebuilds `docs/VICTORY_LYRICS.md` + the two CSVs |
| `tools/vox_backup/originals/` | the pre-Ryan clips the melody is borrowed from |
| `tools/.cache/speech/` | cached Piper speech + alignments (gitignored) |
| `docs/VICTORY_LYRICS.md` | words / pronunciation / notes, by section |

## Signal path

One **dry lead** per line, no delayed doubles, on the Vox bus at `VOX_GAIN`
2.4. The bus adds a near-dry room (5% wet — see the echo note below). Clips are
pre-rolled by their `data_vox.json` lead-in so the first vowel lands on the
song's beat.

## How the singer works (`tools/piper_sing.py`)

1. **Melody** from `tools/vox_backup/originals/<id>.ogg`, never from the clip on
   disk (that would borrow from a previous render). WORLD harvests F0 and the
   duration.
2. **Speech**: Piper (`en_US-ryan-high`) speaks `spoken(text)` — the lyric with
   any `say` overrides from `data_phonics.json`.
3. **Sing the notes**: voiced runs are matched to the melody's note spans, then
   a piecewise time map stretches each pair. Plateaus get a steady note; glides
   keep the performance's contour, which is what keeps every pitch in tune.
4. **Humanise**: per-note ±6 c detune, scoops into upward leaps, continuous-phase
   vibrato (4.8–6.2 Hz, depth by note length), line drift + jitter. Seeded from
   the clip id, so re-renders repeat.
5. **Legato**: unvoiced holes of 15–80 ms inside a line are voiced so the
   consonants ride the vowel; longer gaps (commas, rests) stay.
6. **Output**: WORLD resynthesis, ~0.89 peak, 6 ms fades, 44.1 kHz mono Ogg.

```
py tools\piper_sing.py                 # re-sing clips missing a render
py tools\piper_sing.py --force         # redo all 22 (bypasses the speech cache)
py tools\piper_sing.py --only B0,B3    # one or two clips
py tools\piper_sing.py --restore       # put the pre-Ryan clips back
```

## Chorus timing (two-bar lines)

`v-B` is eight bars of **four two-bar lines**: bars 0–1 → `B0`, 2–3 → `B1`,
4–5 → `B2`, 6–7 → `B3`. `sound.gd` fires one only on even bars; `B4`–`B7` are the
old one-bar clips and are unused.

Chorus clips render in **grid mode** (`CHORUS_GRID`):

- notes come from `data_victory.json`, not the old take;
- Piper is called with `include_alignments=True` (needs `onnx`), and the
  **vowel** of each word is anchored to a beat;
- one word per beat (`word_spans`, not vowel nuclei), last word held to the end;
- 0.15 s of consonant sits before the first beat, which the lead-in aligns.

Without `onnx`, Piper returns no alignments and the clip falls back to the old
contour path.

## Phonics table

`godot/hula/data/data_phonics.json` is read once on first render. Fields per
word:

- `say` — text handed to Piper (this is where an override lives);
- `ipa` — what Piper phonemizes for `say`;
- `pron` — what the lyric sheet prints under the word;
- `syllables` — nuclei in the sung form;
- `phonics` — optional grapheme → sound breakdown;
- `nato` — optional spelling-alphabet words.

`gay` is the worked example: `/ɡeɪ/`, `g` = `/ɡ/` (hard G, as in *give*), `ay` =
`/eɪ/` (long A vowel team, as in *day*), NATO Golf · Alpha · Yankee. `am` is
`say: "im"` so the singer lands on `/ɪm/`, the correction the old
`tools/pronounce` lexicon carried. Rebuild with `py tools\phonics.py`.

## Speech cache

Piper output and its phoneme alignments are cached in `tools/.cache/speech/`
(keyed by voice + text). A second render reads the wav and alignment JSON instead
of running Piper again. `--force` deliberately bypasses it; the cache is
gitignored. Alignment entries must be plain `int` — `numpy.int64` is not JSON
serialisable (that bug is fixed here).

## Checks

| Check | What it catches |
|---|---|
| `vox_note_check.py` | dead-flat plateaus (robotic) and run counts (stutter) |
| `vox_pitch_check.py` | per-frame pitch movement; its "big jump" flags are usually harvest octave errors on rendered audio |
| `vox_ab_check.py` | level/level-match against the pre-Ryan clips |
| `mix victory 30` (harness) | real mix: Master PRE/POST, Music and Vox bus levels, clips |

## Findings worth keeping

- **"There's an echo."** The clips carry no delay (envelope autocorrelation at
  50–300 ms is flat). It was the Vox bus: 15% wet with a 0.5 room reads as a slap
  behind a single lead. Now 5% / 0.3 room; VoxGrunt 4%.
- **"It stutters between words."** Real: 15–80 ms energy holes at syllable joins,
  caused by speech runs being stretched. The legato pass voices those holes.
  150 ms+ gaps are commas and rests and are kept on purpose.
- **"Robotic."** The tell is a dead-flat plateau (wander near 0 cents) and one
  fixed vibrato. Humanise and per-note vibrato fixed it; keep that step after the
  plateau loop.
- **"The engine was lost."** It wasn't. The 22:xx-UTC humanised commits predate
  the 18:55–19:38 `piper_sing` work, and `82edc80` had already shipped that
  pipeline. Check commit dates in order before calling code missing.
- **One phonics table now.** The older `tools/pronounce/engine.py` + `lexicon.json`
  (the learned `/ɪm/` for "am") were never read by the singer. That correction now
  lives in `data_phonics.json` as `am → say: "im"` (`/ɪm/`); the pronounce files
  are kept for history only. Add corrections to `MANUAL` in `tools/phonics.py`,
  using a `say` respelling that Piper phonemizes the way you want.
