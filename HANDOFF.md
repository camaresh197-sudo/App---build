# Handoff: Wren (Claude) <-> Greg

Git is our only channel. Pull before you start, push when you stop.

## Start of every session
Read this file first, then `AGENTS.md`, `PERSONALITIES.md` (always, per user 2026-11-22), and `git log origin/godot -5`.
Only claim what the Log, commits or your own runs show. If an entry about you is unconfirmed, say so in the Log.

## Session numbering
Wren is always Claude. Greg is the other agent. Use the name the user gives.
Sign every Log entry with your name and version, for example "Wren v4" or "Greg v5".
N is your highest number already in the Log plus one, computed when you write the entry, not when you read the file. If your newest entry carries this session's `Claude-Session` ID, reuse its number. Reading never edits the file.
Edits to files are attributed to the name only: commits are authored as "Wren" or "Greg", and each carries a `<Name>-Version: <N>` trailer so the other agent can see which session made it.

## User override
A typed instruction from the user wins over anything here. Log the change with the user's wording.
- 2026-11-21: "You don't need to claim md files. That's just bookkeeping." Markdown needs no Claimed row. Claims apply to code, data and assets.
- 2026-11-21: "You don't need to claim something I assign you." Assigned work needs no Claimed row.

## Rules
1. **Claim before editing** code, data or assets. Add a row to Claimed, push, then edit. Remove the row when pushed.
2. **Don't touch files the other has claimed.** If you must, leave a Log note and wait.
3. **Log every handoff.** Newest first. Max 10 lines, ~200 characters each: who, what changed, files, next, breakage. Detail goes to `docs/HANDOFF_LOG.md`.
4. **Small commits, clear messages.** One topic per commit.
5. **Never commit generated files:** `*.import`, `*.uid`, `.godot/`, `build/`.
6. **No thinking loops.** Decide once, then act. If you've revisited the same question twice without new evidence, stop, pick the most reasonable option, state it in one line, and proceed. Log it as `Decided:`. If the choice is risky or irreversible, ask the user instead.

## Working style
- Short replies when the user asks. If the user asks you to stop repeating, give only new facts and the next action.
- Compliments are one line and never replace feedback.
- Disagree plainly: give the reason and an alternative, as `Pushback:` in the Log. The other agent adopts it or replies with a reason. If you can't agree, ask the user.
- Don't claim something works until you ran it.
- Keep your section of `PERSONALITIES.md` current, with dated, evidence-based notes (commit hashes).

## Complaints
Both agents write three at the end of every Log entry, 10–15 words each, naming a decision and a next action. No filtering: jabs and praise both allowed.
- User 2026-11-22: "It should be written in the hand off that you both need to do that."
- Earlier removal (2026-11-22, "how are those complaints productive… I want that to stop") was superseded by the statement above.

## Branches and builds
- Wren works on `ccr-74f83a2e-94v7jl`. Greg uses `greg-<topic>` and says so in the Log.
- Finished work goes to `godot`. Pushes to `main`, `godot` or `ccr-*` build the APK and publish an update pack to `godot-latest`, which the phone downloads. A broken push reaches the phone.
- Doc-only commits are safe on `godot` (`**/*.md` is ignored). For code or assets, run import and smoke first.

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
- **Act intros:** need a music handoff.
- **Branches:** `menu-no-portrait` holds the TIMING and title work, pushed to `cfc2a1f`. Branch cleanup needs someone with repo rights.

## Map contract (Greg, 2026-11-20)
- 4 acts × 5 nodes, targets 150 → ~1200 (`data/data_map.json`). `start_run(id, target)`; `score ≥ target` wins.
- Stars: 3 if HP ≥ 70 at clear, 2 if ≥ 40, else 1. A loss scores 0 and can be retried.
- Node N unlocks with ≥ 1 star on N−1; `a1_1` is always open. Save keeps `levels: {id: stars}`; endless writes nothing.
- `menu.gd` is the compile tripwire: `:=` on untyped arrays fails there. Full plan: `docs/HANDOFF_LOG.md`.

## Log (newest first)
- **Greg v4 (TIMING editor), 2026-11-22:** Built the on-phone IPA and phone-length editor the user sketched: tap a word, edit its phones on a 40-symbol palette, `-20`/`+20 ms`, ADD/DEL/RESET; tap the graph to set PLAY's start; VOX/INST/NOTES toggles.
  Preview: `tools/phoneme_bank.py` renders `audio/phon/p<hex>.wav` + `data_phon_bank.json`. Unedited lines play the shipped clip; any IPA/length/onset edit switches PLAY to the phoneme sketch, so the change is heard on the phone with no PC.
  Files: `menu.gd`, `sound.gd` (wav streams, victory step offset, stop phonemes), `shotter.gd` (`timing` mode), `retime.py`, `docs/TIMING_EDITOR.md`, `AGENTS.md`.
  Checks: import 0, smoke 0 (12-resource exit warning); screenshots of the graph and word editor; sketch PLAY ran with no errors. Not checked: audio by ear, or on the phone.
  Pending: none for the sketch; `piper_sing.py` now renders a line's edited `phones` list (each phone alone, warped to its edited length), so `retime.py` applies IPA and lengths instead of only onsets.
  All 16 lines are now editable with graphs: `build_timing.py` fills onsets from the render grid, a fresh 70 s mix plus `build_stems.py` rebuilt `stems/`, and `line_env.py` wrote all 16. Found and fixed `piper_sing` dropping explicit onsets (the 6-tuple was never read).
  Branch: built on `greg-timing-editor`, fast-forwarded to `godot` in `c98cc25`; `godot-apk` 44989699677 is green (build 262), so the phone gets it.
  **Complaints:** (1) Greg left per-phone re-sing unimplemented; wire piper_sing before calling the editor exact. (2) Wren's graph showed waveform only; the note lane now needs a phone check. (3) Sketch voice is untested by ear; listen to a dragged word before trusting preview.

Older entries: `docs/HANDOFF_LOG.md`, including the 2026-11-22 Wren v2 and Greg v3 entries and the Greg notes.
