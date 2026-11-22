# Commands and file map

Moved from AGENTS.md. Read when running Godot or the tools.

## Read efficiently
- `hero3d.gd` is ~1750 lines. Find your section with `grep -n '^## ' docs/CODEMAP.md`, then read only that range. Never read it whole.
- After an import, `git status` lists hundreds of `.import` files. Use `git status -s -- . ':(exclude)*.import' ':(exclude)*.uid'`.
- Search scoped to `godot/hula/scripts/`, `tools/`, `docs/`, `data/`.
- Skip binary or generated: `godot/hula/audio/`, `godot/hula/art/`, `godot/hula/.godot/`, `blender/`, `build/`, `stems/`, `android/`, and `*.import`, `*.uid`, `*.glb`, `*.blend`, `*.png`, `*.webp`, `*.ogg`, `*.wav`, `*.flac`. Keep `.ignore` and `.gitattributes`. The embedded Piper sources are `android/piper/` (docs/PIPER_ANDROID.md).
- `git log -1 --format=%B <sha>` usually records the measurements and intent behind a change.

## Commands
Run Godot from `godot/hula/`:

| Task | Command |
|---|---|
| Regenerate `.import` (after pulling) | `godot --headless --import` |
| Smoke test (3 s) | `godot --resolution 800x600 main.tscn --quit-after 180 -- --smoke` |
| Regenerate codemap | `python tools/codemap.py` |
| Apply word timing from phone | `python3 tools/retime.py <file> [--dry-run]` (re-sings changed lines) |
| Sound graph envelopes | `python3 tools/line_env.py` (writes `data/data_line_env.json`) |
| Snip a window from stem | `python3 tools/snip_from_stem.py --stems stems --clips-dir godot/hula/audio/vox --start S --end E --out x.wav` |
| Build packs/APK | `powershell -File build.ps1` (Windows) |

### Harness (`scripts/shotter.gd`)
Format: `godot --path godot/hula -- <out> <frames> [mode] [args]`

| Mode | Example | Output |
|---|---|---|
| (default) | `out.png 1` | Screenshot |
| `play` | `out.png 30 play` | Screenshot after the game runs |
| `sheet` | `dir 0 sheet neutral,roar,sad` | One face close-up per expression |
| `face` | `face.png 1 face 3.2` | Face pose |
| `rigref` | `/tmp/x 0 rigref [expr]` | Rewrites `data/character_rig.json` |
| `mix` | `wav 1 victory 30` | Audio mix; also `_masterpre.wav`, `_voxpre.wav`, `_voxpost.wav` |
| `secret` | `- 1 victory [voxonly]` | Jump to a song, optional vocals only |
| `map` | `out.png 6 map [act] [node]` | World map |

`glb` (legacy GLB writer) is frozen; use Blender for mesh edits. Add `seed=NNN` for repeatable output.

### Mix and stem
The mix needs a display even though audio is offline. Run under Xvfb:

```bash
xvfb-run -a -s "-screen 0 1600x900x24" godot --path godot/hula -- /abs/out/victory.wav 1 mix victory 30
```

Rebuild the stem from `_masterpre` and `_voxpost` with a fitted `k`. Check each clip with `snip_from_stem.py`'s `locate` (scores near 1.0 mean the clip is in that run). An instrument stem that drops well below the master where vocals sit is a subtraction error (docs/AUDIO.md, Known problems).


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
| `data/data_word_timing.json` | Word onsets B0–B2 (TIMING tab; applied by `tools/retime.py`) | ✓ |
| `tools/snip_from_stem.py` | Snip from `stems/`, re-place sung clips (no Godot run) | ✓ |
| `tools/retime.py` | Apply copied word timing; re-sing changed lines only | ✓ |
| `tools/snip_fast.py` | Older snip tool needing a full mix; superseded | — |
| `stems/` | Instrument stem, vocal buses, meta | — |
| `data/*.json` | Songs, vox, menu, expressions, map, cutscenes | ✓ |
| `data/character_rig.json` | Rig baseline (regenerate with `rigref`) | via `rigref` |
| `art/character_skinned.glb` | Exported mesh (from Blender master) | via export |
| `blender/character_rigged.blend` | Master mesh and rig (Blender only) | ✓ (Blender) |
| `tools/` | Python: Blender passes, audio synthesis, codemap | ✓ |
| `docs/` | CODEMAP, AUDIO, VOCAL, CHARACTER, AUDIO_BUS_ARCHITECTURE | ✓ |
| `build/`, `dist/`, `www/`, `node_modules/` | Generated | ✗ |

