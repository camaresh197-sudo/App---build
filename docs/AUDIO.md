# AUDIO.md — music, SFX, samples

Entry point: `godot/hula/scripts/sound.gd` (~7k tokens whole; get line anchors from
`docs/CODEMAP.md`). Samples: `godot/hula/audio/` — generated, never scan it.

## How it works

- No audio engine: every note is an Ogg sample triggered by a step sequencer in `sound.gd`.
- Bank naming: `audio/<inst>_r<midi>[_2].ogg` (two takes), roots every 2 semitones.
  `RANGE` sets each instrument's span; `_pick()` snaps a requested midi to the nearest
  root and pitch-shifts. Add an octave by extending `RANGE` and rendering samples.
- Drums: `kick[_2/_3]`, `snare[_2/_3]`, `hat`, `tom`, `shaker`, `clap`, `cymbal`.
  One-shots without a sample of their own borrow the closest drum (see `sfx()`).
- `TRIM` = per-instrument balance; `SFX_LVL` = one-shot level; `boost` = per-track gain
  set in `start_music()`. `SMP_MUS` scales sequencer notes.
- Buses: Music / SFX / Vox → Master. Vox has a compressor (threshold −10 dB, ratio 2,
  12 ms attack, 180 ms release) + short reverb; Master has a hard limiter at −0.5 dB.
  `set_volumes()` is the player-facing mix (music also scales the Vox bus by 0.7).
- `have` is gated on `res://audio/kick.ogg`; with no assets pack the game runs silent
  by design — every audio path is guarded.

## Songs and data

Step length: game `E = 0.13 s` (6 steps/bar, 6/8), victory `VE = 0.105 s` (16 steps/bar),
title `TE = 0.125 s` (16 steps/bar). Each JSON file is an array of bar records:

- `data_song.json`: `[root, fifth, chord, melody, inst, bar, end_flag]`
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
  in `data_vox.json`. Lines start on bar 0 of their section; each clip is pre-rolled by
  its lead-in so the first syllable lands on the downbeat, and plays at `VOX_GAIN` (2.4)
  on the Vox bus.
- Chorus grunts: bank `audio/grunt_r<midi>[_2].ogg` (`RANGE["grunt"]`), scheduled by
  `VGRUNT` as `[section, bar, step]`, pitched to the bar's chord root `r`, routed to Vox.
  Keep them off `v-hold` bars and the final bar.

## Where to change what

| Goal | Change |
|---|---|
| Instrument balance | `TRIM` in `sound.gd` |
| One-shot SFX loudness | `SFX_LVL` + `sfx()` |
| Track loudness | `boost` in `start_music()` |
| Song notes / structure | `data_song.json`, `data_title.json`, `data_victory.json` |
| Victory lyric clips | `data_vox.json` + `audio/vox/` |
| Grunt placements / level | `VGRUNT`, `VGRUNT_V` + `tools/vox_grunt.py` |
| Re-render a sample bank | the matching `tools/vox_*.py`, then `--import` |

## Tools

`py` has numpy + soundfile; these do not need Blender.

```powershell
py tools\vox_grunt.py          # rebuild the grunt bank (all roots, 2 takes)
py tools\vox_choir.py --src <dir-of-original-ogg>
py tools\vox_singer.py         # WORLD voice conversion; see --style/--lisp/--tipsy/--dopey
```

Audio QA is part of the main harness (see `AGENTS.md`): `mix victory 30` plays a track in
real time and prints PRE/POST peak/RMS/crest/clip plus music-bus levels, and writes a wav.

## Gotchas

- Audio `.import` files are intentionally untracked: every one uses default settings
  (`loop=false`, `bpm=0`), so `godot --headless --import` regenerates them. Art `.import`
  files are still tracked.
- New samples need `--import` before `load()` sees them; the bank is loaded by `res://`
  path (case-sensitive), not by UID.
- The Vox bus runs a compressor: pushing `VGRUNT_V`/`VOX_GAIN` too hard will duck the
  sung line for ~180 ms. Check the mix with the harness, not by ear alone.
