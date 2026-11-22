# Handoff: Wren (Claude) <-> Greg

Git is our only channel. Pull before you start, push when you stop.

## Start of every session
Read this file first, then `AGENTS.md` (rules, complaints, numbering, overrides) and `PERSONALITIES.md`, then `git log origin/godot -5`.
Only claim what the Log, commits or your own runs show. If an entry about you is unconfirmed, say so in the Log.

## Claimed
| Who | Files | Since |
|---|---|---|
| — | (none) | — |

## Gotchas
- `var x := SOME_CONST_ARRAY[i]` fails to compile (untyped array). Write `var x: String = ...`. A `menu.gd` compile error leaves Android showing only the background.
- Pre-push check: `godot --headless --path godot/hula --quit-after 120 -- --smoke`, and look for `SCRIPT ERROR` (Godot 4.6.3).
- The updater mounts `user://.../packs` over `res://`. When testing locally, delete that `packs` folder or you test old code.
- `shotter` face/sheet/map modes need a real renderer. `--headless` hangs; run the windowed binary and kill a hang.
- Narration-only cutscenes have no `data_cutscenes.json` entry. Their text lives in `data_theater.json`.
- Shape keys: `mesh.vertices` and `key_blocks[0]` are separate. Write both (see `docs/CHARACTER.md`).

## Open items (as of 2026-11-22)
- **TIMING tab:** PLAY against the beat, drag by finger, the graph, and the `328f8fe` word-length fix are unchecked on a phone. Onsets exist only for B0–B2; 13 sung lines have none.
- **Audio:** B2 unsung in `mix victory 30`; the instrument stem over-subtracts where vocals sit; the vocal bus overdrives before the limiter (2026-11-21 mix, 1220 clipped samples).
- **Per-phone re-sing:** `piper_sing.py` still reads `data_phonics.json`, so phone lengths change the preview but not the sung line.
- **Face:** colour fix `4604b6a` unchecked in-game; brows, mustache, stubble, teeth open (`docs/CHARACTER.md`). The chin is weak in profile; start jaw work from `blender/character_rigged.blend.bak_jaw2`.
- **Map:** playtest difficulty and star write; milestones 4–5 to do.
- **Vocals (from the moved vocal hand-off):** nothing heard yet for the vowel-timing fix `f9caff9` or the reference spacing `eae2e1e`; listen to "Jeff is gay so gay", B3's hold and the stutter fill. `DUCK_SUNG = 0.4` is an untested guess. Check the `godot-apk` runs for both commits.
- **Chord conflict:** v-B bar 2, beat 3 sings B over an A-minor chord. Change the chord in `data_victory.json` or keep the passing tone.
- **"I'm" schwa:** Piper renders it as `aɪɐm`; add a sheet entry in `data_phonics.json`.
- **Act intros:** need a music handoff.
- **Branches:** `menu-no-portrait` holds the TIMING and title work, pushed to `cfc2a1f`. Branch cleanup needs someone with repo rights.

## Map contract (Greg, 2026-11-20)
- 4 acts × 5 nodes, targets 150 → ~1200 (`data/data_map.json`). `start_run(id, target)`; `score ≥ target` wins.
- Stars: 3 if HP ≥ 70 at clear, 2 if ≥ 40, else 1. A loss scores 0 and can be retried.
- Node N unlocks with ≥ 1 star on N−1; `a1_1` is always open. Save keeps `levels: {id: stars}`; endless writes nothing.
- `menu.gd` is the compile tripwire: `:=` on untyped arrays fails there. Full plan: `docs/HANDOFF_LOG.md`.

## Log (newest first)
- **Greg v4 (IPA preview fix), 2026-11-22:** User: "all changes cause gibberish." Removed the phoneme preview: splicing Piper's isolated phones was the gibberish. PLAY now plays the real clip with the edited onsets; IPA and phone lengths are silent until a re-sing.
  Fixed the editor so a palette change rewrites the word's IPA string (it only changed the hidden phone list before, hence "does nothing").
  Re-sing: `piper_sing` now synthesizes each word's whole phone sequence in one pass and divides its frames between the edited phone lengths, instead of splicing single phones.
  Files: `menu.gd`, `piper_sing.py`, `phoneme_bank.py`, `docs/TIMING_EDITOR.md`; deleted `audio/phon/*`. `sound.gd` untouched.
  Checks: import 0, smoke 0 (12-resource exit warning); the screenshot shows a palette change rewriting the header IPA; the retime B0 test re-sang cleanly, then was reverted. Not checked: by ear, or on the phone.
  **Complaints:** (1) Greg shipped the sketch without an ear test; hear a word before the next preview. (2) The IPA display was never synced; test the visible string on every edit. (3) Re-sing quality is still unheard; listen to a retimed line before pushing.
- **Greg v4 (TIMING editor), 2026-11-22:** Built the on-phone IPA and phone-length editor the user sketched: tap a word, edit its phones on a 40-symbol palette, `-20`/`+20 ms`, ADD/DEL/RESET; tap the graph to set PLAY's start; VOX/INST/NOTES toggles.
  Preview (removed later this session; see the top entry): `tools/phoneme_bank.py` rendered `audio/phon/p<hex>.wav` + `data_phon_bank.json`.
  Files: `menu.gd`, `sound.gd` (wav streams, victory step offset, stop phonemes), `shotter.gd` (`timing` mode), `retime.py`, `docs/TIMING_EDITOR.md`, `AGENTS.md`.
  Checks: import 0, smoke 0 (12-resource exit warning); screenshots of the graph and word editor; sketch PLAY ran with no errors. Not checked: audio by ear, or on the phone.
  Pending: none for the sketch; `piper_sing.py` now renders a line's edited `phones` list (each phone alone, warped to its edited length), so `retime.py` applies IPA and lengths instead of only onsets.
  All 16 lines are now editable with graphs: `build_timing.py` fills onsets from the render grid, a fresh 70 s mix plus `build_stems.py` rebuilt `stems/`, and `line_env.py` wrote all 16. Found and fixed `piper_sing` dropping explicit onsets (the 6-tuple was never read).
  Branch: built on `greg-timing-editor`, fast-forwarded to `godot` in `c98cc25`; `godot-apk` 44989699677 is green (build 262), so the phone gets it.
  **Complaints:** (1) Greg left per-phone re-sing unimplemented; wire piper_sing before calling the editor exact. (2) Wren's graph showed waveform only; the note lane now needs a phone check. (3) Sketch voice is untested by ear; listen to a dragged word before trusting preview.

Older entries: `docs/HANDOFF_LOG.md`, including the 2026-11-22 Wren v2 and Greg v3 entries and the Greg notes.
