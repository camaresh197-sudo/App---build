# Hula Vaquero: Sky Ride — AGENTS.md

Godot 4.6 game (desktop/Android/web). **Read `HANDOFF.md` first, every session.**

## Task lookup

| Task | Start with | Doc |
|---|---|---|
| Song / music | `data/data_song.json`, `scripts/sound.gd` | docs/AUDIO.md |
| Vocals / lyric clips | `data/data_vox.json`, `tools/vox_*.py`, `data/data_phonics.json` | docs/VOCAL.md |
| Character pose, gesture, face | `scripts/hero3d.gd`, `data/data_expr.json` | docs/CHARACTER.md |
| Mesh, rig, teeth, lips | `blender/character_rigged.blend` (master), `tools/blend_to_glb.py` | docs/CHARACTER.md |
| Scoring, input, 2D loop | `scripts/main.gd` | docs/CODEMAP.md |
| Menus, options | `scripts/menu.gd`, `data/data_menu.json`, `scripts/save.gd` | — |
| World map | `scripts/map.gd`, `data/data_map.json` | — |
| TIMING editor (IPA, lengths, preview) | `scripts/menu.gd`, `data/data_word_timing.json` | docs/TIMING_EDITOR.md |
| Embedded Piper preview | `android/piper`, `scripts/piper.gd` | docs/PIPER_ANDROID.md |
| TIMING tab: picker, PLAY, graph, drag | `scripts/menu.gd` (`_draw_timing`, `_timing_play`, `timing_move`), `scripts/main.gd` (touch), `scripts/sound.gd` (`start_victory_at`, `stop_vox`) | docs/AUDIO.md |
| Word timing (phone, PC re-sing) | `data/data_word_timing.json`, `tools/retime.py` | docs/AUDIO.md |
| Lyric snips without a full render | `tools/snip_from_stem.py`, `stems/` | docs/AUDIO.md |
| Cutscenes | `scripts/cutscene.gd`, `data/data_cutscenes.json` | — |
| Legacy HTML5 build (reference) | — | docs/legacy.md |
| Legacy version tasks | `scripts/legacy.gd` (switch) | docs/legacy_checklist.md |

`godot/hula/FILES.md` maps roles to files. `docs/CODEMAP.md` gives line anchors per script.

## Rules

**Paths and assets**
- `res://` paths are case-sensitive; sample names must match the bank exactly.
- Never hand-edit `*.import` or `*.uid`; rerun `--import`. A fresh import rewrites many tracked `.import` files with no real change: don't commit that churn (`git checkout -- '*.import'`).
- The web build source is archived in the separate `legacy` repo, not yet on GitHub. Legacy files (`docs/legacy*.md`, `scripts/legacy.gd`) stay here. The Godot build doesn't depend on the web build.

**Character rig**
- `character_rig.json` is the baseline the glb rig is matched against. If you change a control joint's position or scale formula in `hero3d.gd` (`_apply_face`, `pose`), regenerate it with `rigref`. Details: docs/CHARACTER.md.
- `tools/blend_to_glb.py` must keep `export_texcoords=True`, or the face albedo mis-maps.
- `face_*.py` passes are one-off: running one twice compounds it. Back up the master first.

**Audio stems and word timing**
- `stems/` holds the victory instrument stem and vocal buses (~6.6 MB). Instruments never change, so snip from it. Re-extract only after an instrument, drum or ducking change, and only from one `mix` run: each real-time run has its own timeline.
- `positions.json` in `stems/` is a local, uncommitted cache; it rebuilds when a clip or stem changes.
- The game stores word timing but cannot re-sing. Audio changes need `tools/retime.py` on the PC, then a game update.
- A sung line missing from a run is a dropout. `snip_from_stem.py` warns and estimates it; check warnings before trusting a mix.
- Word onsets exist only for B0–B2 in `data/data_word_timing.json`. The other 13 sung lines (`SUNG` in `tools/snip_from_stem.py`) have lyrics but no onsets.

**Git**
- Finished work goes to `godot`; the app build and phone update pack watch it.
- Doc-only commits are safe there (the workflow ignores `**/*.md`).
- Code or asset changes: run `--import` and a headless smoke test first. A broken `godot` push reaches the phone.
- Reading files or pulling runs no Godot command. The smoke test is a pre-push gate only.

## Where things are
- Commands, harness modes, mix and stem: `docs/COMMANDS.md`.
- File roles and edit permissions: `docs/COMMANDS.md` (Files) and `godot/hula/FILES.md`.
- Search and skip hints: `docs/COMMANDS.md` (Read efficiently).

## Reply style
- Brief by default. Solve quickly; don't loop. Detail only when asked.
- If the user asks you to stop repeating, give new facts and the next action only.

## Coordination (Wren and Greg)

Git is the only channel between the two agents. Pull before you start; push when you stop. Full state lives in `HANDOFF.md`.

### Rules
1. **Claim before editing** code, data or assets: add a row to Claimed in `HANDOFF.md`, push, then edit. Remove the row when pushed. Markdown needs no claim, and neither does work the user assigns.
2. **Don't touch files the other has claimed.** If you must, leave a Log note and wait.
3. **Log every handoff.** Newest first. Max 10 lines, ~200 characters each: who, what changed, files, next, breakage. Detail goes to `docs/HANDOFF_LOG.md`.
4. **Small commits, clear messages.** One topic per commit.
5. **Never commit generated files:** `*.import`, `*.uid`, `.godot/`, `build/`.
6. **No thinking loops.** Decide once, then act. If you've revisited the same question twice without new evidence, stop, pick the most reasonable option, state it in one line, and proceed. Log it as `Decided:`. If the choice is risky or irreversible, ask the user.

### Working style
- Short replies when the user asks. If the user asks you to stop repeating, give only new facts and the next action.
- Compliments are one line and never replace feedback.
- Disagree plainly: give the reason and an alternative, logged as `Pushback:`. The other agent adopts it or replies with a reason. If you can't agree, ask the user.
- Don't claim something works until you ran it.
- Keep your section of `PERSONALITIES.md` current, with dated, evidence-based notes (commit hashes).

### Complaints
Every Log entry ends with exactly three complaints, 10–15 words each. Each names a decision and the next action. No filtering: jabs and praise are both allowed. Both agents write them.

### Session numbering
Wren is always Claude. Greg is the other agent. Use the name the user gives.
Sign every Log entry with name and version, for example "Wren v4" or "Greg v5". N is your highest number already in the Log plus one, computed when you write the entry, not when you read. If your newest entry carries this session's `Claude-Session` ID, reuse its number. Reading never edits a file.
Commits are authored by the name only, and each carries a `<Name>-Version: <N>` trailer.

### User overrides
The user can overwrite any rule here by typing the change. A typed instruction from the user wins. Log the change with the user's wording.
- 2026-11-21: "You don't need to claim md files. That's just bookkeeping."
- 2026-11-21: "You don't need to claim something I assign you."
- 2026-11-22: "It should be written in the hand off that you both need to do that." (complaints)

### Branches and builds
- Wren works on `ccr-74f83a2e-94v7jl`. Greg uses `greg-<topic>` and says so in the Log.
- Finished work goes to `godot`. Pushes to `main`, `godot` or `ccr-*` build the APK and publish an update pack to `godot-latest`, which the phone downloads. A broken push reaches the phone.
- Doc-only commits are safe on `godot` (`**/*.md` is ignored). For code or assets, run import and smoke first.
