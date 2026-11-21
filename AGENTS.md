# Hula Vaquero: Sky Ride — AGENTS.md

Godot 4.6 game (desktop/Android/web). Read `HANDOFF.md` first when another agent is active.

## Task lookup

| Task | Start with | Doc |
|---|---|---|
| Song / music | `data/data_song.json`, `scripts/sound.gd` | docs/AUDIO.md |
| Vocals / lyric clips | `data/data_vox.json`, `tools/vox_*.py` | docs/AUDIO.md |
| Character pose, gesture, face | `scripts/hero3d.gd`, `data/data_expr.json` | docs/CHARACTER.md |
| Mesh, rig, teeth, lips | `blender/character_rigged.blend` (master), `tools/blend_to_glb.py` | docs/CHARACTER.md |
| Scoring, input, 2D game loop | `scripts/main.gd` | docs/CODEMAP.md |
| Menus, options | `scripts/menu.gd`, `data/data_menu.json`, `scripts/save.gd` | — |
| World map | `scripts/map.gd`, `data/data_map.json` | — |
| Cutscenes | `scripts/cutscene.gd`, `data/data_cutscenes.json` | — |
| Legacy HTML5 build (reference) | — | docs/legacy.md |
| Legacy version tasks | `scripts/legacy.gd` (switch) | docs/legacy_checklist.md |

`godot/hula/FILES.md` maps roles to files. `docs/CODEMAP.md` gives line anchors per script.

## Read efficiently

- `hero3d.gd` is ~1750 lines. Slice it with `docs/CODEMAP.md` (`read offset=… limit=…`), never read it whole.
- CODEMAP has one `## scripts/<name>.gd` section per script: `grep -n '^## ' docs/CODEMAP.md`, then read only yours (~3.9k tokens whole file).
- After a Godot import, plain `git status` lists hundreds of `.import` files. Use `git status -s -- . ':(exclude)*.import' ':(exclude)*.uid'`.
- Search with `grep --path`/`--include`, scoped to `godot/hula/scripts/`, `tools/`, `docs/`, `data/`.
- Skip (binary or generated): `godot/hula/audio/`, `godot/hula/art/`, `godot/hula/.godot/`, `blender/`, `build/`, and `*.import`, `*.uid`, `*.glb`, `*.blend`, `*.png`, `*.webp`, `*.ogg`, `*.wav`.
- `.ignore` and `.gitattributes` already filter these; keep both.
- `git log -1 --format=%B <sha>` usually records the measurements and intent behind a change.

## Commands

Run Godot from `godot/hula/`:

| Task | Command |
|---|---|
| Regenerate `.import` (parse check, after pulling) | `godot --headless --import` |
| Smoke test (3 s) | `godot --resolution 800x600 main.tscn --quit-after 180 -- --smoke` |
| Regenerate codemap | `python tools/codemap.py` |
| Build packs/APK | `powershell -File build.ps1` (Windows) |

### Harness (`scripts/shotter.gd`, args after `--`)

Format: `godot --path godot/hula -- <out> <frames> [mode] [args]`

| Mode | Example | Output |
|---|---|---|
| (default) | `out.png 1` | Screenshot |
| `play` | `out.png 30 play` | Screenshot after the game runs |
| `sheet` | `dir 0 sheet neutral,roar,sad` | One face close-up per expression |
| `face` | `face.png 1 face 3.2` | Face pose |
| `rigref` | `/tmp/x 0 rigref [expr]` | Rewrites `data/character_rig.json` from current code |
| `mix` | `wav 1 victory 30` | Audio mix |
| `secret` | `- 1 victory [voxonly]` | Jump to a song, optional vocals only |
| `map` | `out.png 6 map [act] [node]` | World map |

`glb` (legacy GLB writer) is frozen. Use Blender for mesh edits. Add `seed=NNN` for repeatable output.

## Rules

**Paths and assets**
- `res://` paths are case-sensitive; sample names must match the bank exactly.
- Never hand-edit `*.import` or `*.uid`. Rerun `--import`. Audio and art `.import` files are tracked, and a fresh import rewrites many with no real change: don't commit that churn (`git checkout -- '*.import'`).
- The web (HTTP) build is archived in the separate `legacy` repo. Nothing here depends on it; all its art and audio already live in `godot/hula/`.

**Character rig**
- `character_rig.json` is the baseline the glb rig is matched against. If you change a control joint's position or scale formula in `hero3d.gd` (`_apply_face`, `pose`), regenerate it with `rigref`, or that joint's geometry drifts. Details in docs/CHARACTER.md.
- `tools/blend_to_glb.py` must keep `export_texcoords=True`, or the face albedo mis-maps.
- The `face_*.py` passes are one-off: running one twice compounds it. Back up the master first.

**Git**
- Finished work goes to `godot`. The app build and the phone update pack both watch that branch.
- Doc-only commits are safe there (the workflow ignores `**/*.md`).
- For code or asset changes, run `--import` and a headless smoke test first. A broken `godot` push reaches the phone.

## Files

| Path | Role | Edit |
|---|---|---|
| `scripts/main.gd` | Game loop, scoring, input (2D 772×360) | ✓ |
| `scripts/hero3d.gd` | 3D rig, poses, face, teeth, sprite | ✓ (slice) |
| `scripts/sound.gd` | Sequencer, SFX, mixer | ✓ |
| `scripts/menu.gd`, `scripts/save.gd` | Menus, persistence | ✓ |
| `scripts/map.gd`, `scripts/cutscene*.gd`, `scripts/voice_manager.gd` | Map, cutscenes, voice | ✓ |
| `scripts/updater.gd` | Autoload: pack mount, self-update | — |
| `scripts/shotter.gd` | Test harness | — |
| `data/*.json` | Songs, vox, menu, expressions, map, cutscenes | ✓ |
| `data/character_rig.json` | Rig baseline (regenerate with `rigref`) | via `rigref` |
| `art/character_skinned.glb` | Exported mesh (from the Blender master) | via export |
| `blender/character_rigged.blend` | Master mesh and rig (Blender only) | ✓ (Blender) |
| `tools/` | Python: Blender passes, audio synthesis, codemap | ✓ |
| `docs/` | CODEMAP, AUDIO, CHARACTER, AUDIO_BUS_ARCHITECTURE | ✓ |
| `build/`, `dist/`, `www/`, `node_modules/` | Generated | ✗ |
