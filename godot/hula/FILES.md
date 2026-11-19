# File Index — Quick Navigation

## By Role

### Composers (music/audio)
- **Main song:** `data/data_song.json` → `scripts/sound.gd:146`
- **Title theme:** `data/data_title.json` → `scripts/sound.gd:148`
- **Victory fanfare:** `data/data_victory.json` → `scripts/sound.gd:149`
- **Lyric clips:** `data/data_vox.json` → `scripts/sound.gd:147`
- **SFX routing:** `scripts/sound.gd:1-100` (mixer buses)

### Character Artists
- **Face expressions:** `data/data_expr.json` (20K keyframes)
- **3D rig code:** `scripts/hero3d.gd:1-100` (procedural rig)
- **Master blend:** `../blender/character_rigged.blend` (edit in Blender)
- **GLB export:** `art/character.glb`

### UI/Menu Designers
- **Menu structure:** `data/data_menu.json` → `scripts/menu.gd`
- **Skills/items:** `data/data_menu.json:{"skills":[...]}`
- **Achievements:** `data/data_menu.json:{"achs":[...]}`
- **Wardrobe/cosmetics:** `data/data_menu.json:{"cos":[...]}`

### Game Logic
- **Main loop:** `scripts/main.gd:1-50` (state machine)
- **Scoring:** `scripts/main.gd:150-200` (points, combos)
- **Input handling:** `scripts/main.gd:50-100` (controls)
- **Persistence:** `scripts/save.gd` ↔ `user://save.json`

### DevOps/Build
- **Web build:** `prepare.mjs` + `reference/audio/` → `dist/`
- **APK build:** `build.ps1` → Android `.apk`
- **Asset import:** `godot --headless --import`
- **Test harness:** `scripts/shotter.gd` → screenshots, audio QA

## By Frequency

### Touch Often
```
data/data_song.json       main game music
data/data_menu.json       game content (skills, items)
scripts/main.gd           game logic
scripts/sound.gd          music sequencer
```

### Touch Sometimes
```
scripts/hero3d.gd         character poses/faces
scripts/menu.gd           UI layout
data/data_expr.json       face expressions (read with CODEMAP.md)
```

### Touch Rarely
```
scripts/save.gd           persistence
scripts/updater.gd        autoload, updates
scripts/shotter.gd        test harness
```

## File Sizes (tokens)

| File | Size | Notes |
|---|---|---|
| `data/data_expr.json` | ~20K | Don't read whole; use CODEMAP.md |
| `scripts/hero3d.gd` | ~26K | Don't read whole; use CODEMAP.md |
| `scripts/sound.gd` | ~7K | Readable whole |
| `data/data_song.json` | 6K | Compact array format |
| `data/data_menu.json` | 5K | Main game content |

## Paths Reference

```
godot/hula/
├── data/              ← All JSON config & data
│   ├── data_song.json
│   ├── data_title.json
│   ├── data_victory.json
│   ├── data_vox.json
│   ├── data_menu.json
│   ├── data_expr.json
│   └── character_rig.json
├── scripts/           ← All GDScript
│   ├── main.gd
│   ├── hero3d.gd
│   ├── sound.gd
│   ├── menu.gd
│   ├── save.gd
│   ├── updater.gd
│   └── shotter.gd
├── audio/             ← Generated samples (don't track)
├── art/               ← Binary assets
├── main.tscn          ← Scene root
├── project.godot      ← Engine config
└── .godot_manifest.json ← This index (machine-readable)
```
