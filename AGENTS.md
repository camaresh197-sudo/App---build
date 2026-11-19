# AGENTS.md — Hula Vaquero: Sky Ride

A Godot 4.6 game (desktop + Android + a web wrapper) about a dancing vaquero, with a
small Blender character pipeline and a Python audio pipeline.

**The code is tiny (~7 GDScript files, 12 tools). The assets are huge.** Read this file,
then open only what you need. Task detail lives in two child docs:

- **Music, SFX, samples** → `docs/AUDIO.md`
- **Mesh, rig, face, animation** → `docs/CHARACTER.md`

## Read in this order

1. This file.
2. `godot/hula/project.godot` + `godot/hula/main.tscn` (autoloads, scene wiring). Both are tiny.
3. `docs/CODEMAP.md` for line anchors, then **read only the slice** of the script you need.
4. The one task doc above, if the task touches audio or the character.
5. `godot/hula/data_*.json` only for music / menu content tasks.

## Repo map

| Path | What it is | Scan? |
|---|---|---|
| `godot/hula/scripts/main.gd` | Game loop, state machine, scoring, input, 2D field (772×360 logical) | yes |
| `godot/hula/scripts/hero3d.gd` | Real-time 3D vaquero: procedural rig, poses/gestures, face expressions, SubViewport sprite | yes |
| `godot/hula/scripts/sound.gd` | Sample-bank music sequencer for 3 songs, SFX, mixer buses | yes |
| `godot/hula/scripts/menu.gd` | Title screen + options hub (skills/wardrobe/trophies/stats/settings) | yes |
| `godot/hula/scripts/save.gd` | `user://save.json` persistence + `data_menu.json` statics | yes |
| `godot/hula/scripts/updater.gd` | Autoload "Updater": mounts downloaded packs, self-update on next launch | yes |
| `godot/hula/scripts/shotter.gd` | Test harness: screenshots, clips, GLB export, audio QA. No-op on normal launch | yes |
| `docs/CODEMAP.md` | Generated line-number index of the 7 scripts (~2.9k tokens vs ~49k whole) | yes |
| `docs/AUDIO.md` | Music/SFX pipeline, song data shapes, sample banks, audio tools | yes |
| `docs/CHARACTER.md` | Blender master, GLB publish, runtime rig, face shape keys | yes |
| `godot/hula/data_song.json` | Main game song (6/8 mariachi), 6-step bars | data |
| `godot/hula/data_title.json` | Title song (ranchera polka), 16-step bars | data |
| `godot/hula/data_victory.json` | Victory fanfare, 16-step bars + held half-bars | data |
| `godot/hula/data_vox.json` | Victory lyric clips: line id → `[clip, lead-in]` | data |
| `godot/hula/data_menu.json`, `data_expr.json` | Menu statics; face expression keyframes | data |
| `godot/hula/audio/` | ~400 Ogg samples. Generated bank; `.import` files are not tracked | **no** |
| `godot/hula/art/` | `.glb`, albedo PNGs, screenshots. Binary | **no** |
| `godot/hula/.godot/` | Godot import cache. Generated | **no** |
| `tools/` | Python: Blender character passes + audio synthesis | yes |
| `blender/character_rigged.blend` | **Master** character mesh/rig (6 MB). Edit in Blender only | no |
| `reference/audio/` | Older tracked web asset packs (`audio_*.v1.ogg`) used only by `prepare.mjs` | no |
| `reference/release.yml` | Stale duplicate; GitHub only runs `.github/workflows/release.yml` | no |
| `index.html` | 1.4 MB minified web game bundle (source artifact, not generated here) | **no** |
| `updater.js`, `prepare.mjs`, `native-setup.mjs` | Web/Capacitor packaging + self-updater | yes |
| `build.ps1` | Local build: smoke test → import → Code/Assets packs → optional APK | yes |
| `build/`, `dist/`, `www/`, `node_modules/` | Build output. Ignored | **no** |

Outside the repo: `..\preview\` holds reference renders/screenshots (untracked).

## Commands

```powershell
$godot = "C:\Users\Camden\AppData\Local\Programs\Godot\4.6.3\Godot_v4.6.3-stable_win64_console.exe"
$proj  = "C:\Users\Camden\Documents\Default Project\godot-build\godot\hula"

# 3 s boot smoke test (must show 0 SCRIPT ERROR / Parse Error)
& $godot --path $proj --resolution 800x600 main.tscn --quit-after 180 -- --smoke

# Import assets; also the fastest full parse check (regenerates the audio .import files)
& $godot --headless --path $proj --import

# Build update packs (and the debug APK with -Apk)
powershell -File .\build.ps1

# Regenerate the code map after moving functions
py tools\codemap.py
```

### Test harness (`shotter.gd`)

Only runs when args follow `--`. First arg is output, second is frames. Useful modes:

```powershell
# screenshot (append "play" to let the game run first)
& $godot --path $proj main.tscn -- out.png 1
# audio QA: play one track in real time, print PRE/POST + music-bus levels, write a wav
& $godot --path $proj main.tscn -- "$env:TEMP\vic.wav" 1 mix victory 30
# SFX-only levels
& $godot --path $proj main.tscn -- "-" 1 mix sfx coin,click,hit
# jump straight into a song (optional 4th arg "voxonly")
& $godot --path $proj main.tscn -- "-" 1 secret victory
# face pose render, GLB export, menu hub tab
& $godot --path $proj main.tscn -- face.png 1 face 3.2
```

Harness runs are seeded (`seed=NNN` anywhere in the args) so audio/pose logs are repeatable.

## Conventions and gotchas

- `res://` paths are case-sensitive; sample names must match the bank exactly.
- Never hand-edit `*.import` or `*.uid`; rerun `--import` instead. Audio `.import` files
  are intentionally untracked (all settings are defaults); art `.import` files are tracked.
- Web build uses the `reference/audio/*.v1.ogg` packs (served under `reference/audio/`);
  the Godot build uses `godot/hula/audio/`. Don't mix the two.
- The web bundle is `index.html`; `prepare.mjs` injects `updater.js` and copies the
  reference audio packs into `dist/`.
- `build/`, `dist/`, `www/`, `node_modules/`, `.godot/`, `__pycache__/` are generated.
- Commit messages in history are detailed; `git log -1 --format=%B` on a relevant commit
  often documents intent and measurements. Prefer history over guessing.

## Token hygiene

- `.ignore` filters assets out of ripgrep/grep. Do not delete it or add asset globs back;
  if you must search audio, pass an explicit path. (`glob` still walks assets — use a
  specific pattern.)
- `.gitattributes` marks binary assets so `git diff`/`git show` never dump them.
- Read slices, not whole files: `hero3d.gd` is ~26k tokens, `sound.gd` ~7k. Use
  `docs/CODEMAP.md` for the line, then `offset`/`limit`.
- Prefer `grep` with `include`/`path` over recursive scans.

## Do not scan

`godot/hula/audio/`, `godot/hula/art/`, `godot/hula/.godot/`, `blender/`, `reference/audio/`,
`index.html`, `build/`, `dist/`, `www/`, `node_modules/`, `*.import`, `*.uid`, `*.glb`,
`*.blend`, `*.png`, `*.webp`, `*.ogg`, `*.wav`.
