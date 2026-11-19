# Hula Vaquero: Sky Ride — AGENTS.md

Godot 4.6 game: dancing vaquero (desktop/Android/web). ~7 GDScript files + 12 tools + Blender rig + Python audio.

**Task docs:** `docs/AUDIO.md` (music/SFX), `docs/CHARACTER.md` (rig/anim).

## Quick start
1. This file
2. `godot/hula/project.godot` + `main.tscn` (autoloads, wiring)
3. `docs/CODEMAP.md` → read only the slice you need
4. Task doc (audio/character) if needed
5. `data_*.json` for music/menu tasks

## Files

| Path | Purpose |
|---|---|
| **godot/hula/scripts/** | |
| `main.gd` | Game loop, scoring, input, 2D field (772×360) |
| `hero3d.gd` | 3D rig, poses, face expressions, sprite export |
| `sound.gd` | Music sequencer (3 songs), SFX, mixer |
| `menu.gd` | Title + menus (skills/wardrobe/trophies/stats) |
| `save.gd` | Persistence, menu statics |
| `updater.gd` | Autoload: pack mounting, self-update |
| `shotter.gd` | Test harness (screenshots, GLB, audio QA) |
| **docs/** | |
| `CODEMAP.md` | Line anchors for 7 scripts (~2.9k tokens) |
| `AUDIO.md` | Music/SFX pipeline, song data, tools |
| `CHARACTER.md` | Blender, GLB, rig, face keys |
| **godot/hula/data_*.json** | Song data (main/title/victory), menu statics, expressions |
| **godot/hula/audio/** | ~400 Ogg samples (generated, .import untracked) |
| **godot/hula/art/** | GLBs, PNGs, screenshots (binary) |
| **tools/** | Python: Blender passes, audio synthesis |
| **blender/character_rigged.blend** | Master rig (edit in Blender only) |
| **reference/audio/** | Old web asset packs (prepare.mjs only) |
| **reference/release.yml** | Stale (use `.github/workflows/release.yml`) |
| **updater.js, prepare.mjs, native-setup.mjs** | Web/Capacitor packaging |
| **build.ps1** | Local: test → import → packs → APK |
| **build/, dist/, www/, node_modules/** | Generated (ignored) |

## Commands

Set `$godot` and `$proj` paths, then:
- **Smoke test** (3 s): `& $godot --path $proj --resolution 800x600 main.tscn --quit-after 180 -- --smoke`
- **Import** (checks parse): `& $godot --headless --path $proj --import`
- **Build packs/APK**: `powershell -File .\build.ps1`
- **Regenerate codemap**: `py tools\codemap.py`

### Test harness (`shotter.gd` — args after `--`)

Format: `main.tscn -- <output> <frames> [mode] [args]`

| Mode | Args | Output |
|---|---|---|
| (default) | `out.png 1` | Screenshot |
| `play` | `out.png 1` | Screenshot after game runs |
| `mix` | `wav 1 victory 30` | Audio mix (victory song, 30 s) |
| `mix sfx` | `- 1 sfx coin,click,hit` | SFX levels |
| `secret` | `- 1 victory [voxonly]` | Jump to song ± vocals |
| `face` | `face.png 1 face 3.2` | Face pose + GLB export |

Add `seed=NNN` anywhere for repeatable audio/poses.

## Notes

- `res://` paths case-sensitive; sample names must match bank exactly
- Never hand-edit `*.import`/`*.uid`; rerun `--import` (audio .import untracked, art tracked)
- Web build: `reference/audio/*.v1.ogg`; Godot build: `godot/hula/audio/` — don't mix
- Web bundle: `index.html` + `prepare.mjs` → `updater.js` + copies audio to `dist/`
- Generated: `build/`, `dist/`, `www/`, `node_modules/`, `.godot/`, `__pycache__/`
- Check commit history for intent/measurements: `git log -1 --format=%B <commit>`

## Token tips

- `.ignore` filters assets; `.gitattributes` marks binary (keep both)
- Read slices: `hero3d.gd` ~26k, `sound.gd` ~7k. Use CODEMAP.md → `offset`/`limit`
- `grep --include/--path` faster than recursive scan
- For audio search, pass explicit path (not glob)

## Skip these

`godot/hula/audio/`, `godot/hula/art/`, `godot/hula/.godot/`, `blender/`, `reference/audio/`, `index.html`, `build/`, `dist/`, `www/`, `node_modules/`, plus `*.import`, `*.uid`, `*.glb`, `*.blend`, `*.png`, `*.webp`, `*.ogg`, `*.wav`
