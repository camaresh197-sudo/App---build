# AUDIO.md — music, SFX, samples

Entry point: `godot/hula/scripts/sound.gd` (~7k tokens whole; get line anchors from
`docs/CODEMAP.md`). Samples: `godot/hula/audio/` — generated, never scan it.

## How it works

- No audio engine: every note is an Ogg sample triggered by a step sequencer in `sound.gd`.
- Bank naming: `audio/<inst>_r<midi>[_2].ogg` (two takes), roots every 2 semitones.
  `RANGE` sets each instrument's span; `_pick()` snaps a requested midi to the nearest
  root and pitch-shifts. Add an octave by extending `RANGE` and rendering samples.
- Rendering: `tools/sample_bank/render_bank.py --sf2 <soundfont.sf2>` rebuilds the
  melodic instrument bank (accordion, bass, bell, choir, guitar, pad, trumpet, violin) from a
  General MIDI soundfont. Each instrument has a target RMS that matches the mix it had, so
  its `TRIM` is 1.0; edit the target there, not in `TRIM`.
- Drums: `kick[_2/_3]`, `snare[_2/_3]`, `hat`, `tom`, `shaker`, `clap`, `cymbal`.
  One-shots without a sample of their own borrow the closest drum (see `sfx()`).
- `TRIM` = per-instrument balance; `SFX_LVL` = one-shot level; `SMP_MUS` scales sequencer
  notes. `boost` = per-track gain set in `start_music()` (menu/title 1.8, game 1.15,
  victory 0.6), applied to the Music, Vox and VoxGrunt buses only.
- Buses: seven, all → Master (hard limiter, −0.5 dB ceiling): Music, SFX, Vox, VoxGrunt,
  Cutscene, Ambient, UI. Per-bus effects and routing are in `AUDIO_BUS_ARCHITECTURE.md`.
  Ambient and UI are created with effects but nothing routes to them yet.
- `set_volumes()` is the player-facing mix: the music slider sets Music, Vox and VoxGrunt
  (each ×0.7, muted at 0); the SFX slider sets SFX. It does not touch Cutscene, Ambient or UI.
- `have` is gated on `res://audio/kick.ogg`; with no assets pack the game runs silent
  by design — every audio path is guarded.

## Songs and data

Step length: game `E = 0.13 s` (6 steps/bar, 6/8), victory `VE = 0.105 s` (16 steps/bar),
title `TE = 0.125 s` (16 steps/bar). Each JSON file is an array of bar records:

- `data_song.json`: `[root, fifth, chord, melody, inst, bar, end_run, intro]` — `end_run` = 1
  plays the end-of-section run; `intro` = 1 marks intro bars (the loop restarts at the
  first bar with `intro` = 0).
- `data_title.json`: `[root, fifth, chord, melody, lead, intensity, section, bar,
  bars_in_section, first, is_end, next_root]`
- `data_victory.json`: `[root, fifth, chord, melody, lead, intensity, section, bar,
  bars_in_section, first, is_end, hold, from_section, finale, last, next_root,
  pickup, half_bar]` — index 17 = 1 means an 8-step held bar (the sequencer skips its
  second half, then the next section starts on the beat).
- `data_vox.json`: line id → `[clip, lead-in]` (see below).

`chord` is a midi array, `melody` is one midi per step (0 = rest, −1 = hold). `root` is
the chord root used for bass/grunt pitch; `fifth` is the alternate bass note.

## Vocals and ad-libs

- Victory lyrics: one clip per line, `audio/vox/<id>.ogg` (`A0`, `B7`, `tag2`, …), keyed
  in `data_vox.json`; the words live in `data_lyrics.json`. Lines start on bar 0 of their
  section; each clip is pre-rolled by its lead-in so the first syllable lands on the
  downbeat, and plays at `VOX_GAIN` (2.4) on the Vox bus.
- The clips are rendered, not recorded: Piper speech is re-pitched to the song's melody
  with WORLD (`tools/piper_sing.py`). The originals are backed up in
  `tools/vox_backup/originals/` (`--restore` puts them back).
- Chorus grunts: bank `audio/grunt_r<midi>[_2].ogg` (`RANGE["grunt"]`), scheduled by
  `VGRUNT` as `[section, bar, step]`, pitched to the bar's chord root `r`, routed to the
  separate VoxGrunt bus (its own compressor, so grunts don't pump the sung line).
  Keep them off `v-hold` bars and the final bar.

### How the singer works (`tools/piper_sing.py`)

See `docs/VOCAL.md` for the full vocal pipeline — singer, chorus grid, phonics
table, speech cache and the findings behind the echo/stutter/robotic fixes.

The pipeline is a mouth transplant, not a vocoder trick: Ryan sings the lyric on a
melody borrowed from the *original* performance, never from the current clip (re-running
on an already-sung clip would borrow from itself).

1. **Melody** — `tools/vox_backup/originals/<id>.ogg` is analyzed with WORLD; its F0
   contour and duration are the target.
2. **Speech** — Piper (`en_US-ryan-high` by default) speaks the words from
   `data_lyrics.json`.
3. **Sing the notes.** Ryan's voiced runs are merged to match the song's note spans in
   order (`equalize_runs`), then a piecewise time map stretches each pair onto its span.
   The melody is classified into **plateaus** (held) and **glides** (slides). A plateau
   gets one steady note; a glide keeps the performance's own contour. Every pitch is
   therefore the performance's, never an average across a slide — that is what keeps the
   line in tune.
4. **Humanise.** A singer is never dead on the grid: each note lands ±6 cents off centre,
   upward leaps get a scoop, vibrato (4.8–6.2 Hz, per-note depth) keeps one phase across
   note boundaries, and the whole line drifts and jitters by a few cents. The RNG is
   seeded from the clip id, so a re-render is repeatable.
5. **Legato.** Unvoiced holes of 15–80 ms inside a line are voiced so the consonants ride
   the vowel; syllables join instead of stuttering. Longer gaps (commas, musical rests)
   are kept.
6. **Output.** WORLD resynthesis, normalize (0.89 peak), 6 ms edge fades, 44.1 kHz mono
   Ogg. The clip is a **single dry lead** — no delayed doubles, so the Vox bus reverb is
   not doubled into an echo.

### Chorus timing (two-bar lines)

See `docs/VICTORY_LYRICS.md` for every line's bars, words, syllables and notes.
`v-B` is eight bars but **four two-bar lines**: bars 0–1, 2–3, 4–5, 6–7 map to `B0`–`B3`,
and `sound.gd` plays one only on even bars. Clips `B4`–`B7` are no longer triggered.

Chorus clips are rendered in **grid mode** (B0–B2 take explicit onsets from `data_word_timing.json` when present) (`CHORUS_GRID` in `piper_sing.py`): the notes
come from `data_victory.json`, not from the old take, and each syllable's **vowel** is
anchored to a beat using Piper's phoneme alignments (one syllable per beat, last one held
to the end of the phrase; 0.15 s of consonant sits before the first beat, which
`data_vox.json`'s lead-in puts ahead of the downbeat). This needs `onnx`
(`pip install onnx`, or `piper-tts[alignment]`); without it Piper returns no alignments
and the clip falls back to the old contour path.

Flags: `--flow notes|contour` (`notes` is the singer above; `contour` is the old
speech-rhythm path), `--vibrato 0..1`, `--only A2,B0` for a quick single-clip render,
`--force` to re-render, `--restore`, `--dry-run`.

Checks: `vox_note_check.py` reports voiced-run wander (robotic = too flat) and run count;
`vox_pitch_check.py` reports per-frame movement (its "big jump" flags are usually harvest
octave errors on rendered audio — see its docstring); `vox_ab_check.py` compares takes.


## Word timing from the phone

Status: the TIMING tab is on `godot`. Its PLAY, graph and drag are not yet checked on a phone.

Secret menu (tap RUNS three times on the title), **TIMING** tab:

- **Line box** (left of the words): shows the current line. Tap it for a picker with each line's
  words (B0, B1, B2). The picker draws over everything else on the tab.
- **NEXT LINE >**: moves to the next line, wrapping after the last.
- **Words**: five per row, each with `-` and `+` (0.01 s). Or drag a green onset tick on the
  graph: it stays between its neighbours and rounds to 0.01 s on release.
- **PLAY**: starts the victory instruments at the line's chorus bar (B0 bar 0, B1 bar 2, B2 bar 4),
  with the sequencer's own vocals off, and sings the line with the edited onsets. Each word runs to the
  next word's edited onset, so dragging a word also moves where it ends; the last word runs to the end
  of the clip. The track stops after the line's bars (`bars` x 16 steps x 0.105 s).
- **Playhead:** a white vertical line moves left to right across the graph while the line plays.
- **STOP**: stops the track and restores vocals. Leaving the tab or BACK does the same.
- **SAVE** (kept on the phone) or **COPY** (JSON to the clipboard; paste it into the chat or a file).
  Data lives in `godot/hula/data/data_word_timing.json`.

Shipped clips are not re-sung by PLAY. It shifts each word's audio to its edited onset (no stretch),
so timing and pitch are unchanged. Edits reach the rendered clip only after a PC re-sing.

**Sound graph** (under the word rows): the sung clip (yellow) over the instrument stem (blue), for the
line's stretch of the track, from `godot/hula/data/data_line_env.json`. White ticks: shipped onsets;
green ticks: edited onsets. Made by `tools/line_env.py`. It needs a stem and clip positions that match
the current clips (see "Known problems" below). It is shown only when the picker is closed.

On the PC, from the repo root:

```bash
python3 tools/retime.py timing_from_phone.json --dry-run   # shows what changed
python3 tools/retime.py timing_from_phone.json              # writes the data, re-sings only changed lines
```

`piper_sing.py` reads the onsets from the data file, so a re-sing needs `piper-tts[alignment]`,
`pyworld`, `soundfile` and the Ryan voice model in `tools/models/`. The phone shows edits
immediately but plays the old clip until the PC re-sing is merged and the app is updated.

**Coverage:** word onsets exist only for B0, B1 and B2. The song has 16 sung lines (the `SUNG` list in
`tools/snip_from_stem.py`); the others have lyrics in `data_lyrics.json` but no onsets, so they cannot be
timed in the tab yet.

## Known problems

See `HANDOFF.md` (Open items). Full text was moved to `docs/HANDOFF_LOG.md`.

## Snips without re-rendering the song

The instruments are fixed, so a lyric or timing change does not need a full `mix victory`.
The stem and vocal buses are saved once in `stems/`, and `tools/snip_from_stem.py` cuts any
window from them and re-places the sung clips.

```bash
python3 tools/snip_from_stem.py --stems stems --clips-dir godot/hula/audio/vox \
    --start 19.36 --end 33.50 --out snip.wav        # .mp3 also works
```

- `stems/instruments.flac` = pre-limiter master minus `k` × vox bus (`k` in `meta.json`).
  The stem correlates at zero with the vox bus, so no vocals are left in it.
- `stems/voxbus_post.flac` is the calibration reference; `stems/voxbus_dry.flac` is used to
  find each clip's position by normalised cross-correlation.
- `stems/positions.json` caches positions and the clip-to-bus gain. It rebuilds when a clip
  or stem file changes, or with `--rebuild-positions`. A warm snip takes about 0.2 s (no scipy import, cached clip lengths).
- Clips are decoded with `soundfile`, not `ffmpeg`: `ffmpeg` upmixes mono to stereo with a
  −3 dB pan law, which is why older gains read 1.587 instead of about 1.10.
- Limits: the output is not passed through the master limiter, so levels can differ slightly
  from the game. Instrument, drum or ducking changes need a new extraction. Every real-time
  run has a slightly different timeline (the game clock is frame-driven), so the stem, its
  vox bus and the clip positions must come from the same run.
- Re-extracting the stem needs the master before the limiter. `shotter.gd` `mix` writes it as
  `<out>_masterpre.wav`, next to the post-limiter master and the `_voxpre`/`_voxpost` files.
  The stem is `masterpre − k × voxbus_post`; `k` (about 0.563) is the vox level inside the master,
  fitted over the chorus and stored in `meta.json`.
- Dropouts: a run can lose a sung line. In the run in `stems/`, the vox bus is silent from 36 to
  38 s, so `C2` never played. The snip tool warns and places a missing line at the spacing of its
  neighbours (two bars = one line apart). Only lines the sequence sings are placed or estimated
  (`SUNG` in `tools/snip_from_stem.py`); the calibration gain uses only lines that were actually sung.
  Check the warnings after every new run, and find out why a line dropped before trusting the mix.

## Where to change what

| Goal | Change |
|---|---|
| Instrument balance | `TRIM` in `sound.gd` |
| One-shot SFX loudness | `SFX_LVL` + `sfx()` |
| Track loudness | `boost` in `start_music()` |
| Song notes / structure | `data_song.json`, `data_title.json`, `data_victory.json` |
| Victory lyric clips | `data_vox.json` + `audio/vox/` |
| Vocal tone (robotic / stutter) | humanise + legato in `tools/piper_sing.py` |
| Grunt placements / level | `VGRUNT`, `VGRUNT_V` + `tools/vox_grunt.py` |
| Re-render a sample bank | the matching `tools/vox_*.py`, then `--import` |
| Change a lyric's timing or audio, without a full render | `tools/snip_from_stem.py` (see above) |
| Word onsets for B0–B2 | `godot/hula/data/data_word_timing.json` (edit in the TIMING tab, or directly) |

## Tools

`py` has numpy + soundfile; these do not need Blender.

```powershell
py tools\vox_grunt.py          # rebuild the grunt bank (all roots, 2 takes)
py tools\vox_choir.py --src <dir-of-original-ogg>
py tools\piper_sing.py         # the singer: Piper on the melody (--force, --only A2,B0, --flow, --vibrato, --restore, --dry-run)
py tools\vox_singer.py --src <dir>   # older WORLD voice conversion; --style/--lisp/--tipsy/--dopey
py tools\lyrics_doc.py             # rebuild docs/VICTORY_LYRICS.md (bars, words, syllables, notes, IPA)
python3 tools/retime.py <file> [--dry-run]     # apply word timing copied from the TIMING tab; re-sings changed lines
python3 tools/snip_from_stem.py --stems stems --clips-dir godot/hula/audio/vox --start S --end E --out x.wav
```

Checks: `vox_pitch_check.py`, `vox_note_check.py`, `vox_ab_check.py`.

Audio QA is part of the main harness (see `AGENTS.md`): `mix victory 30` plays a track in
real time and prints PRE/POST peak/RMS/crest/clip plus music-bus levels, and writes a wav.

## Gotchas

- **"There's an echo."** Check the Vox bus before the clips: `AudioEffectReverb` at 15% wet with a 0.5 room reads as a slap behind a single dry lead. The clips themselves carry no delay (verify with an envelope autocorrelation at 50–300 ms); they are one dry take by design.
- **"It stutters between words."** Measure holes, don't guess: 15–80 ms unvoiced gaps inside a line are the singer's fault (fixed by the legato pass), while 150 ms+ gaps are commas and musical rests and should stay. `vox_note_check.py` reports run counts; the spectrogram of a clip makes the holes obvious.
- **"Robotic."** A dead-flat plateau is the tell: `vox_note_check.py` wander near 0 cents. The singer adds per-note detune, scoops, vibrato and drift; if it comes back, check that the humanise step still runs after the plateau loop.
- Audio and art `.import` files are tracked, and every audio one uses default settings
  (`loop=false`, `bpm=0`). A fresh `godot --headless --import` rewrites many of them with
  no real change; don't commit that churn (`git checkout -- '*.import'`).
- New samples need `--import` before `load()` sees them; the bank is loaded by `res://`
  path (case-sensitive), not by UID.
- The Vox bus runs a compressor (−10 dB, 1.5:1): pushing `VOX_GAIN` too hard squashes the
  sung line. Grunts (`VGRUNT_V`) go to VoxGrunt instead, but still check the mix with the
  harness, not by ear alone.
