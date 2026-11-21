# Hand-off: Godot audio work (Hula)

For the next session picking up sound, vocals and pronunciation work. Written 2026-11-21.

## Where things are

- **Godot project:** `godot/hula/` on branch `godot` (the main line). Work by fast-forward
  only. Use a worktree (`git worktree add -b <name> <path> origin/godot`), commit, then
  `git push origin <name>:refs/heads/godot`. Remove the worktree afterwards.
- **This branch** (`ccr-27ddf814-hu5evs`): holds `data/g2p/` (CMUdict-derived word→IPA,
  135k rows) and this file.
- **Hula (web/JS game):** `camaresh197-sudo/hula`, read-only in these sessions. Its formant
  synth patch is only a file in a scratchpad, never applied.
- Other branches (`godot-full-lexicon`, `godot-singing-rerender`, `godot-song-sheet-fix`,
  `godot-verse-two-bars`, `godot-grid-all`, `godot-deeper-voice`, `godot-instrument-bank`) are
  already merged into `godot` and can be deleted.

## Pronunciation engine

- `godot/hula/tools/pronounce/engine.py` runs Piper with `lexicon.json` overriding word
  pronunciations. `attach_lexicon(voice)` hooks any loaded PiperVoice.
- `lexicon.json`: 124,912 entries from CMUdict (18.7 MB), plus two learned entries
  (`am`, `jake's`). Each entry is `{"ipa": [chars], "history": [...]}`.
- Overrides skip any word in `data_phonics.json` (the lyric sheet). Reason: CMU citation
  forms stress function words ("is", "to", "so") and drop reductions; the sheet is the source
  of truth for the song.
- The voice `en_US-ryan-high` has no `ɝ`. Spell it `ɜ ɹ` (already done in the lexicon).
  Check any new symbols against `phoneme_id_map` in the voice's `.onnx.json`.

## Victory vocals (`tools/piper_sing.py`)

- Clips in `godot/hula/audio/vox/`, timed by `CHORUS_GRID` (despite the name, it covers all
  sung lines now). Two-bar lines = 3.36 s; one-bar lines = 1.68 s (a step is 0.105 s, 16 steps per bar).
- Grid melodies are written two octaves high; `OCTAVE_SHIFT = -24` brings them to the band's
  key. The original-melody path (B4, B5) is already in key and is not shifted.
- Render command (from `tools/`): `python3 piper_sing.py --voice en_US-ryan-high --force`
  (add `--only A0,A2` for a subset). Needs `pip install piper-tts[alignment] pyworld`.
- Voice model is not in the repo. Get it:
  `https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx`
  and `.onnx.json`. Put both in `tools/models/` (gitignored).
- Clear `tools/.cache/` before re-rendering after changing pronunciation, or old audio is reused.
- Playback (sound.gd): a line starts on the first bar of its section with a 0.15 s lead-in.
  Keys: `A%d`, `B%d` (chorus, even bars only → B0–B3), `C%d`, `tag%d`, `F%d`. The bank maps
  `F2`→`B6`, `F3`→`B7`. `B4` and `B5` are never played. `F2`/`F3` have no files of their own.

## Instrument samples

- `godot/hula/audio/<inst>_r<midi>[_2].ogg`, one root every 2 semitones (`RANGE` in sound.gd).
- `tools/sample_bank/render_bank.py --sf2 <soundfont>` re-renders accordion, bass, bell, choir,
  guitar, pad, trumpet, violin. Targets are set per instrument so the mix is unchanged; `TRIM`
  is 1.0 for these. Install the soundfont with `apt-get install fluidsynth fluid-soundfont-gm`
  (`/usr/share/sounds/sf2/FluidR3_GM.sf2`).
- Drums, grunts and SFX were not touched.

## Open items

1. **Desync report, unresolved.** The user said the vocals were out of sync with the beat after
   the pitch change. Clip lengths and voiced onsets were unchanged (within about 0.1 s). Ask which
   section drifts and whether it starts early, late, or drifts gradually. Test with
   `shotter.gd` `voxonly`.
2. **Nothing has been listened to.** All checks were by measurement. Every change above needs an ear check.
3. "I'm" comes out as `aɪɐm`: Piper's own phonemizer adds a schwa. Fixing it needs a sheet entry.
4. Instrument samples: the new bank has not been compared by ear with the old one.

## Lessons from this session

- A glob like `rm godot/hula/audio/*_r*.ogg` also matched grunt and cutscene files. Name the
  instrument explicitly, or check `git status` before committing.
- Piper's phonemize is on the voice object; hooks must wrap it after loading.
- Measure before claiming a fix. Noise-floor metrics on sustained notes mislead; measure tails and
  played levels (file RMS × TRIM) directly.
- Ask before changing timing or levels for the whole song. Several changes here moved the mix.

## Commit conventions

Trailers used: `Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>` and
`Claude-Session: https://claude.ai/code/session_01AyF4c3kaWePpb91TAgZVQS`.
Do not put model names in pull requests or repo text other than these trailers.
