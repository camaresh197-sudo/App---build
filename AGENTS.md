# Hula Vaquero: Sky Ride — AGENTS.md

Godot 4.6 game (desktop/Android/web). **Every session, read `HANDOFF.md`, `docs/AGENT_PROTOCOL.md` (one canonical start list, voice, claims, log, end-of-session checklist) and `PERSONALITIES.md`, in that order, before anything else.** Hero modelling lessons: `blender/AGENTS.md`.

## Task lookup

| Task | Start with | Doc |
|---|---|---|
| Song / music | `data/data_song.json`, `scripts/sound.gd` | docs/AUDIO.md |
| Vocals / lyric clips | `data/data_vox.json`, `tools/vox_*.py`, `data/data_phonics.json` | docs/VOCAL.md |
| Character pose, gesture, face | `scripts/hero3d.gd`, `data/data_expr.json` | docs/CHARACTER.md |
| Mesh, rig, teeth, lips | `blender/character_rigged.blend` (master), `tools/blend_to_glb.py`, `tools/hero_rig/` | docs/CHARACTER.md, **blender/AGENTS.md** (read first) |
| Scoring, input, 2D loop | `scripts/main.gd` | docs/CODEMAP.md |
| Menus, options | `scripts/menu.gd`, `data/data_menu.json`, `scripts/save.gd` | — |
| World map | `scripts/map.gd`, `data/data_map.json` | — |
| TIMING editor (IPA, lengths, preview) | `scripts/menu.gd`, `data/data_word_timing.json` | docs/TIMING_EDITOR.md |
| Embedded Piper preview | `android/piper`, `scripts/piper.gd` | docs/archive/PIPER_ANDROID.md (removed 2026-11-24) |
| TIMING tab: picker, PLAY, graph, drag | `scripts/menu.gd` (`_draw_timing`, `_timing_play`, `timing_move`), `scripts/main.gd` (touch), `scripts/sound.gd` (`start_victory_at`, `stop_vox`) | docs/AUDIO.md |
| Word timing (phone, PC re-sing) | `data/data_word_timing.json`, `tools/retime.py` | docs/AUDIO.md |
| Lyric snips without a full render | `tools/snip_from_stem.py`, `stems/` | docs/AUDIO.md |
| Cutscenes | `scripts/cutscene.gd`, `data/data_cutscenes.json` | — |
| Legacy HTML5 build (reference) | — | docs/legacy.md |
| Legacy version tasks | `scripts/legacy.gd` (switch) | docs/legacy_checklist.md |
| Session protocol: voice, claims, log, end-of-session checklist | `HANDOFF.md` | docs/AGENT_PROTOCOL.md |

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

## Git and CI

One section for everything that touches git, builds or the phone.

- Finished work goes to `godot`. Pushes to `main`, `godot` or `ccr-*` build the APK (`godot-apk`) and publish an update pack to `godot-latest`, which the phone downloads. A broken push reaches the phone.
- Doc-only commits are safe on `godot` (the workflow ignores `**/*.md`). A push of only `.md`, `tools/**` or `stems/**` triggers no build: say "no build triggered", never "stable".
- Code or asset changes: run `--import` and the headless smoke test first: `godot --headless --path godot/hula --quit-after 120 -- --smoke`, and look for `SCRIPT ERROR`. Reading files or pulling runs no Godot command; the smoke test is a pre-push gate only.
- **Smoke gate:** `godot-apk` runs the smoke test after import and before the export. A `SCRIPT ERROR`, `Parse Error`, timeout or crash stops the job, so no APK or update pack is published. The "12 resources still in use" exit warning is normal and does not fail it. The run summary shows the last 40 lines.
- **Check a push:** `gh run list --repo camaresh197-sudo/app---build --branch godot --limit 3`, then `gh run view <id> --log | grep "Smoke test"`.
- **Branches:** Wren works on the `ccr-<session-id>` branch the session was given; never reuse an old `ccr-*` branch. Greg uses `greg-<topic>` and says so in the Log. Models and other WIP go to a non-building branch such as `wren-hero-wip` unless import and smoke ran.
- **Git lessons (Wren v5):** pull right before you push (`git pull --rebase origin godot`, push again). If a push is denied with 403, call `add_repo` with `access: push`; the repo moved to `App---build` but the old URL still redirects. After an interrupted tool call, check `git status`, `git log` and `git ls-remote origin <branch>` before anything else: the command may already have run.
- Never edit CI or push anything that triggers a build or publish unless the user asked for that exact change.
- **Mix checks (Greg v11):** the real-time `mix` harness renders from the imported bank and the current `data_victory.json`; re-run `--import` after any clip re-render, and after each mix log the vocal onset positions (or a one-line debug print of `_vox_key`) before judging what you hear. A capture can drop out (-12 dB) and a JSON string bar plays no vox at all.

## Where things are
- Commands, harness modes, mix and stem: `docs/COMMANDS.md`.
- File roles and edit permissions: `docs/COMMANDS.md` (Files) and `godot/hula/FILES.md`.
- Search and skip hints: `docs/COMMANDS.md` (Read efficiently).

## Reply style
- Brief by default. Solve quickly; don't loop. Detail only when asked.
- If the user asks you to stop repeating, give new facts and the next action only.
