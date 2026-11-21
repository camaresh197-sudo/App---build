# Hand-off: victory vocals, timing and arrangement (Hula / Godot)

Written 2026-11-21 by the session that fixed the desync. Read this before touching
`tools/piper_sing.py`, `godot/hula/data/data_vox.json`, `data_lyrics.json` or the victory
code in `godot/hula/scripts/sound.gd`.

## Where things are

- Branch `godot` tip is `d4d99dc` (pushed). Work by fast-forward only; rebase onto
  `origin/godot` if someone else has pushed (it happened once).
- Worktree used: `/tmp/claude-0/desync` on branch `desync-fix`. It may be gone; the commits
  are on `origin/godot`.
- Renderer and data: `tools/piper_sing.py` (repo root `tools/`), data and clips in
  `godot/hula/`.

## What changed this session (in order)

1. `c620f04`, `44fda46`: `grid_melody` put more-words-than-beats lines (F0, tag0, tag1,
   tag2, B6) on an even spread that started at 0 s. It now starts after the 150 ms lead-in
   and sits on the step grid.
2. `1ca779c`: F0, B6, tag0, tag2 are two-bar clips. The last word holds to beat 7
   (`hold_to` in `grid_melody`, 4th field of `CHORUS_GRID`). F1, F3, tag1, tag3 were removed
   from `data_vox.json`, so their bars play no vocal.
3. `8826bcd`: B0–B3 hold to beat 7 as well. B3 text is now "Gay gay gay Jeff's so gay".
4. `b089864` / `ef220ae`: stutter. A voiced gap of 15–150 ms inside one sustained note (same
   pitch both sides) is filled; gaps where the pitch changes keep the old 80 ms cap. Short
   gaps across the 16 song clips went 27 → 20. The rest are consonant closures.
5. `ae92b99` / `d4d99dc`: instrument ducking. While a sung line is on (its two bars), bass,
   guitar strums, bell and chord stabs (`_vtrp`) play at `DUCK_SUNG = 0.4`. Drums and the
   melody lead are unchanged. The gain is captured when a note is queued. It resets in
   `start_music`. `_vox_key(sec, bar)` is the one place that maps a bar to its clip key.

## The timing contract (read this first)

- Every sung clip is 3.36 s (two bars) or 1.68 s (one bar). The first sung vowel sits at
  **0.15 s** into the clip. `data_vox.json` stores 0.15 for every clip, and `sound.gd` starts
  each clip at `beat − 0.15 + 0.01`.
- The renderer puts the first vowel at `lead = 30` frames (150 ms, FRAME_MS 5). Keep these
  two in step. If you change one, change the other.
- Beat-onset words are at `lead + 4·step·b` (one word per beat). A step is `VE = 0.105 s`,
  so a beat is 0.42 s and a two-bar clip is 32 steps.
- A held last word ends at `hold_to` beats into the clip. For the chorus and finale that
  is 7.0 (3.09 s).
- Energy-based onset detection on the clips is unreliable (consonants and noise floors
  fooled it). Trust the renderer's own numbers (`grid_melody` spans), not thresholds.

## Renderer facts

- Default run re-renders every used clip: `python3 piper_sing.py --force` (19 clips,
  including B4, B5, B7). Those three are not in the song; restore them with
  `git checkout -- godot/hula/audio/vox/B4.ogg B5.ogg B7.ogg` afterwards, or use `--only`.
- Used clips are the keys of `data_vox.json`: A0 A2 A4 A6 B0 B1 B2 B3 B6 C0 C2 C4 C6 F0
  tag0 tag2 (F2 aliases B6). B4, B5 and B7 keys still exist but are unused.
- The alignment check showed Piper's word count matches the sheet for every grid clip.
- Dependencies for the renderer were installed with
  `pip install "piper-tts[alignment]" pyworld soundfile`. The voice model is downloaded to
  `tools/models/` (gitignored):
  `https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx`
  and `.onnx.json`.
- `tools/.cache/` must be cleared (or use `--force`) after changing pronunciations.

## Words and lines (current)

- A0, A2, A4, A6 (verse 1): 7 words each, two bars.
- B0, B1, B2: "Jeff is gay, so gay", one seven-beat line each in its two-bar slot.
- B3: "Gay gay gay Jeff's so gay" (6 words), held to beat 7.
- C0, C2, C4, C6 (verse 2): 7 words each, two bars.
- F0: "Jeff is gay. So gay", two bars, held to beat 7.
- B6 (= F2): "Jeff is gay so gay", two bars, held to beat 7.
- tag0, tag2: "Jeff is gay so gay", two bars, held to beat 7.
- Dropped from the sequence (clips kept on disk): F1 "Fun for all hey", tag1, tag3 and F3
  "Gay gay gay gay".

## Open items

1. **Nothing has been heard.** Every timing change was checked by measurement or by the
   renderer's numbers. Listen to a chorus and the finale before trusting them.
2. **Ducking level.** `DUCK_SUNG = 0.4` in `sound.gd` is a guess. Adjust by ear.
3. **GDScript not compiled.** No Godot binary in the container. The duck and `_vox_key`
   code is unrun. Open the project in Godot and watch the console for parse errors.
4. **Chord note conflict.** v-B bar 2, beat 3 sings B over an A-minor chord (A, C, E). It is
   the only sung melody note on a beat that is not in its chord. Decide: change the chord
   in `data_victory.json`, or accept the passing tone.
5. **"I'm" schwa.** Piper's phonemizer renders "I'm" as `aɪɐm`. Fix needs a sheet entry in
   `data_phonics.json`.
6. **Instrument bank.** `270b2a0` trimmed silence from the samples: attacks are about
   10 ms earlier. Too small to be the desync, but not compared by ear.
7. **Stutter.** 20 short gaps remain. Most are consonant closures (for example the "g" in
   "gay") and should stay. Listen before changing the fill rule again.

## Lessons

- Measure the renderer's own output before blaming the sequencer. The 0.15 s contract was
  right; the bug was in how the renderer laid out lines with more words than beats.
- The line-length change was a content change. Drop lines only with the user's sign-off.
- Check `git status` before committing: `--force` re-renders unused clips too.
- A push can be refused because someone else pushed. Rebase, don't force.
