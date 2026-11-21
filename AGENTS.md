# Hula Vaquero: Sky Ride — AGENTS.md

Godot 4.6 game (desktop/Android/web). **Read `HANDOFF.md` first, every session, before acting** (see its Start of every session).

## Task lookup

| Task | Start with | Doc |
|---|---|---|
| Song / music | `data/data_song.json`, `scripts/sound.gd` | docs/AUDIO.md |
| Vocals / lyric clips | `data/data_vox.json`, `tools/vox_*.py`, `data/data_phonics.json` | docs/VOCAL.md |
| Character pose, gesture, face | `scripts/hero3d.gd`, `data/data_expr.json` | docs/CHARACTER.md |
| Mesh, rig, teeth, lips | `blender/character_rigged.blend` (master), `tools/blend_to_glb.py` | docs/CHARACTER.md |
| Scoring, input, 2D game loop | `scripts/main.gd` | docs/CODEMAP.md |
| Menus, options | `scripts/menu.gd`, `data/data_menu.json`, `scripts/save.gd` | — |
| World map | `scripts/map.gd`, `data/data_map.json` | — |
| Cutscenes | `scripts/cutscene.gd`, `data/data_cutscenes.json` | — |
| Word timing (phone TIMING tab, PC re-sing) | `scripts/menu.gd` (`_draw_timing`), `data/data_word_timing.json`, `tools/retime.py` | docs/AUDIO.md |
| Lyric audio snips without a full render | `tools/snip_from_stem.py`, `stems/` | docs/AUDIO.md |
| Legacy HTML5 build (reference) | — | docs/legacy.md |
| Legacy version tasks | `scripts/legacy.gd` (switch) | docs/legacy_checklist.md |

`godot/hula/FILES.md` maps roles to files. `docs/CODEMAP.md` gives line anchors per script.

## Read efficiently

- `hero3d.gd` is ~1750 lines: find your section with `grep -n '^## ' docs/CODEMAP.md`, then read only that range (`offset`/`limit`). Never read it whole.
- After a Godot import, plain `git status` lists hundreds of `.import` files. Use `git status -s -- . ':(exclude)*.import' ':(exclude)*.uid'`.
- Search with `grep --path`/`--include`, scoped to `godot/hula/scripts/`, `tools/`, `docs/`, `data/`.
- Skip (binary or generated): `godot/hula/audio/`, `godot/hula/art/`, `godot/hula/.godot/`, `blender/`, `build/`, `stems/`, and `*.import`, `*.uid`, `*.glb`, `*.blend`, `*.png`, `*.webp`, `*.ogg`, `*.wav`, `*.flac`.
- `.ignore` and `.gitattributes` already filter these; keep both.
- `git log -1 --format=%B <sha>` usually records the measurements and intent behind a change.

## Commands

Run Godot from `godot/hula/`:

| Task | Command |
|---|---|
| Regenerate `.import` (parse check, after pulling) | `godot --headless --import` |
| Smoke test (3 s) | `godot --resolution 800x600 main.tscn --quit-after 180 -- --smoke` |
| Regenerate codemap | `python tools/codemap.py` |
| Apply word timing from the phone | `python3 tools/retime.py <file> [--dry-run]` (re-sings changed lines) |
| Snip a window from the stem | `python3 tools/snip_from_stem.py --stems stems --clips-dir godot/hula/audio/vox --start S --end E --out x.wav` |
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
| `mix` | `wav 1 victory 30` | Audio mix; also writes `_masterpre.wav` (before the limiter), `_voxpre.wav`, `_voxpost.wav` |
| `secret` | `- 1 victory [voxonly]` | Jump to a song, optional vocals only |
| `map` | `out.png 6 map [act] [node]` | World map |

`glb` (legacy GLB writer) is frozen. Use Blender for mesh edits. Add `seed=NNN` for repeatable output.

## Rules

**Paths and assets**
- `res://` paths are case-sensitive; sample names must match the bank exactly.
- Never hand-edit `*.import` or `*.uid`. Rerun `--import`. Audio and art `.import` files are tracked, and a fresh import rewrites many with no real change: don't commit that churn (`git checkout -- '*.import'`).
- The web (HTTP) build source is archived in the separate `legacy` repo, which is not yet on GitHub. Until it is published, the legacy files (`docs/legacy*.md`, `scripts/legacy.gd`) stay here. Nothing in the Godot build depends on the web build; its art and audio already live in `godot/hula/`.

**Character rig**
- `character_rig.json` is the baseline the glb rig is matched against. If you change a control joint's position or scale formula in `hero3d.gd` (`_apply_face`, `pose`), regenerate it with `rigref`, or that joint's geometry drifts. Details in docs/CHARACTER.md.
- `tools/blend_to_glb.py` must keep `export_texcoords=True`, or the face albedo mis-maps.
- The `face_*.py` passes are one-off: running one twice compounds it. Back up the master first.

**Audio stems and word timing**
- `stems/` holds the victory instrument stem and vocal buses (about 6.6 MB). Instruments never change, so snip from it. Re-extract only after an instrument, drum or ducking change, and only from one `mix` run: each real-time run has its own timeline.
- `positions.json` in `stems/` is a local cache; it is not committed. It rebuilds when a clip or stem file changes.
- The game stores word timing but cannot re-sing. Audio changes need `tools/retime.py` on the PC, then a game update.
- A sung line missing from a run is a dropout. `snip_from_stem.py` warns and estimates it; check the warnings before trusting a mix.

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
| `data/data_word_timing.json` | Word onsets for B0–B2 (edited in the TIMING tab, applied by `tools/retime.py`) | ✓ |
| `tools/snip_from_stem.py` | Cut a snip from `stems/` and re-place the sung clips (no Godot run) | ✓ |
| `tools/retime.py` | Apply copied word timing and re-sing only the changed lines | ✓ |
| `tools/snip_fast.py` | Older snip tool that needs a full mix run; superseded by `snip_from_stem.py` | — |
| `stems/` | Instrument stem, vocal buses, meta; `positions.json` is a local cache | — |
| `data/*.json` | Songs, vox, menu, expressions, map, cutscenes | ✓ |
| `data/character_rig.json` | Rig baseline (regenerate with `rigref`) | via `rigref` |
| `art/character_skinned.glb` | Exported mesh (from the Blender master) | via export |
| `blender/character_rigged.blend` | Master mesh and rig (Blender only) | ✓ (Blender) |
| `tools/` | Python: Blender passes, audio synthesis, codemap | ✓ |
| `docs/` | CODEMAP, AUDIO, VOCAL, CHARACTER, AUDIO_BUS_ARCHITECTURE | ✓ |
| `build/`, `dist/`, `www/`, `node_modules/` | Generated | ✗ |

## Reply style
- Keep replies brief by default. Solve quickly, don't loop. Give more detail only when the user asks.
- When the user asks to stop repeating, don't restate earlier messages: give new facts and the next action only.
