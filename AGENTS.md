# Hula Vaquero: Sky Ride — AGENTS.md

Godot 4.6 game: dancing vaquero (desktop/Android/web). ~7 GDScript files + 12 tools + Blender rig + Python audio.

**Working with another agent? Read `HANDOFF.md` first (file claims, log, build gotchas).**

## Quick lookup by task

| Task | Files | Doc |
|---|---|---|
| Fix/compose a song | `data/data_song.json`, `sound.gd` (7k) | AUDIO.md |
| Character pose/gesture/face | `hero3d.gd` (26k), `data/data_expr.json` | CHARACTER.md |
| Add menu option | `menu.gd`, `data/data_menu.json`, `save.gd` | — |
| Menu layout/text | `data/data_menu.json` | — |
| Audio SFX or levels | `sound.gd`, AUDIO.md | AUDIO.md |
| Game scoring/input logic | `main.gd` (772×360 2D) | CODEMAP.md |

**→ See `godot/hula/FILES.md` for fast role-based file access**

## Critical path (80% of edits)

**Scripts:** `main.gd`, `hero3d.gd`, `sound.gd`  
**Data:** `data_song.json`, `data_menu.json`  
**Docs:** Use `docs/CODEMAP.md` to slice files by line instead of reading whole

**Intro:** This file → project.godot + main.tscn → CODEMAP.md → task doc

## Token savings (optimizations done)

- Deleted `reference/release.yml` (stale duplicate)
- Consolidated AGENTS.md: cut prose, added task lookup, critical path, token budgets
- Next: could consolidate `data_vox.json` → `data_song.json` (568 bytes + file overhead) if refactoring `sound.gd` load logic

## Files

| Path | Purpose | Tokens | Edit? |
|---|---|---|---|
| **godot/hula/scripts/** | | | |
| `main.gd` | Game loop, scoring, input, 2D (772×360) | ~8k | ✓ |
| `hero3d.gd` | 3D rig, poses, face, sprite export | ~26k | ✓ slice |
| `sound.gd` | Music sequencer (3 songs), SFX, mixer | ~7k | ✓ |
| `menu.gd` | Menus (skills/wardrobe/trophies/stats) | ~8k | ✓ |
| `save.gd` | Persistence, menu statics | ~3k | ✓ |
| `updater.gd` | Autoload: pack mount, self-update | ~2k | — |
| `shotter.gd` | Test harness (screenshots, GLB, audio QA) | ~4k | — |
| **docs/** | | | |
| `CODEMAP.md` | Line anchors for 7 scripts | ~2.9k | ✓ |
| `AUDIO.md` | Music/SFX pipeline, song data, tools | — | ✓ |
| `CHARACTER.md` | Blender, GLB, rig, face keys | — | ✓ |
| **Data files (godot/hula/data/)** | | | |
| `data_song.json` | Main game song (6/8 mariachi), 6-step | — | ✓ |
| `data_title.json` | Title song (ranchera polka), 16-step | — | ✓ |
| `data_victory.json` | Victory fanfare, 16-step + half-bars | — | ✓ |
| `data_vox.json` | Victory lyric clips: id → `[clip, lead-in]` | — | ✓ |
| `data_menu.json` | Menu text, structure, statics | — | ✓ |
| `data_expr.json` | Face expression keyframes | — | ✓ |
| `character_rig.json` | Blender rig export metadata | — | ✗ |
| **Assets (binary/generated)** | | | |
| `audio/` | ~400 Ogg samples (.import untracked) | — | ✗ |
| `art/` | GLBs, PNGs, screenshots | — | ✗ |
| `.godot/` | Godot import cache | — | ✗ |
| **Source files** | | | |
| `tools/` | Python: Blender passes, audio synthesis | — | ✓ |
| `blender/character_rigged.blend` | Master rig (Blender only, 6 MB) | — | ✗ |
| **Web/packaging** | | | |
| `updater.js`, `prepare.mjs`, `native-setup.mjs` | Web/Capacitor packaging | — | ✓ |
| `build.ps1` | Local: test → import → packs → APK | — | ✓ |
| `index.html` | Web bundle (1.4 MB, source artifact) | — | ✗ |
| `reference/audio/` | Old web asset packs (prepare.mjs only) | — | ✗ |
| `reference/release.yml` | Stale (use `.github/workflows/release.yml`) | — | ✗ |
| **Generated/ignored** | | | |
| `build/`, `dist/`, `www/`, `node_modules/` | Build output | — | ✗ |

## Commands

Point Godot to `godot/hula/`, then:

| Task | Command |
|---|---|
| **Smoke test** (3 s, checks parse) | `--resolution 800x600 main.tscn --quit-after 180 -- --smoke` |
| **Import** (regenerate .import, fastest parse check) | `--headless --import` |
| **Build packs/APK** | `powershell -File build.ps1` (Windows) or `python build.py` (cross-platform) |
| **Regenerate codemap** | `python tools/codemap.py` |

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

## Essentials

**Paths & assets:**
- `res://` paths case-sensitive; sample names must match bank exactly
- Never hand-edit `*.import`/`*.uid`; rerun `--import` (audio .import untracked, art tracked)
- Web: `reference/audio/*.v1.ogg` + `prepare.mjs` → `dist/`; Godot: `godot/hula/audio/` — don't mix
- Generated: `build/`, `dist/`, `www/`, `node_modules/`, `.godot/`, `__pycache__/`

**Token hygiene:**
- Use `docs/CODEMAP.md` to slice big files: `hero3d.gd` (26k) + `sound.gd` (7k) → read only the lines you need
- `.ignore` filters assets, `.gitattributes` marks binary — keep both
- `grep --include/--path` faster than recursive scan; audio search needs explicit path

**Git history:**
- Commit messages are detailed: `git log -1 --format=%B <commit>` often documents intent & measurements

**Skip/don't scan:**  
`godot/hula/audio/`, `godot/hula/art/`, `godot/hula/.godot/`, `blender/`, `reference/audio/`, `index.html`, `build/`, `dist/`, `www/`, `node_modules/`, plus binary/generated: `*.import`, `*.uid`, `*.glb`, `*.blend`, `*.png`, `*.webp`, `*.ogg`, `*.wav`

## Code token savings (future)

**Data consolidation:**
- Merge `data_vox.json` (568 B) → `data_song.json` as `vox` key — requires: change `sound.gd` load
- Merge `data_expr.json` (20K) → separate `data_character.json` or inline in `hero3d.gd` as constant — big refactor

**Script utilities:**
- Extract input handling → `input_util.gd` (shared by main.gd + menu.gd)
- Extract state machine → `state_machine.gd` (shared by main.gd + updater.gd)
- **Saves:** ~1-2k tokens (dedup ~300 LOC)
