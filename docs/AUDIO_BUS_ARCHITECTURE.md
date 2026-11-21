# Audio Bus Architecture - Hula Vaquero: Sky Ride

## Overview
Professional-grade audio mixing system with 7 specialized buses, each optimized for its content type. Hierarchical routing ensures proper gain staging and effect processing.

## Bus Hierarchy

```
Master (Hard Limiter @ -0.5dB)
├── Music (Game/Title/Victory music)
├── SFX (Sound effects)
├── Vox (Sung vocals - game music)
├── VoxGrunt (Ad-lib grunts/reactions)
├── Cutscene (Dialogue audio - Mexican Spanish)
├── Ambient (Background atmosphere)
└── UI (Menu/UI feedback sounds)
```

## Detailed Bus Specifications

### 1. MASTER BUS
**Purpose:** Final output control and safety limiting  
**Effects:**
- Hard Limiter: -0.5dB ceiling (protects against clipping)

**Usage:** All audio routes through master  
**Volume Control:** `Save.data.opt.music` sets Music/Vox/VoxGrunt (each ×0.7, muted at 0) and `Save.data.opt.sfx` sets SFX, via `set_volumes()`. Cutscene, Ambient and UI are not touched.

---

### 2. MUSIC BUS
**Purpose:** Game soundtrack, title music, victory themes  
**Character:** Warm, immersive, reverberant  
**Effects:**
- Compressor: -20dB threshold, 2:1 ratio, 50ms attack, 300ms release (smooth level control)
- Reverb: 0.55 room size, 0.5 damping, 16% wet (musical ambience)

**Tracks:** `game`, `menu` (title theme), `victory`, and the `c_*` cutscene tracks (`start_music()` in `sound.gd`)  
**Boost:** 1.15x for game, 1.8x for the menu/title track, 0.6x for victory

---

### 3. SFX BUS  
**Purpose:** Gameplay sound effects (hits, pops, coins, etc.)  
**Character:** Tight, punchy, clean  
**Effects:**
- Compressor: -15dB threshold, 4:1 ratio, 10ms attack, 200ms release, +2dB makeup gain (aggressive taming of transients)

**Sounds:** shoot, hit, pop, coin, click, hurt, beat, power, etc.  
**Routing:** Direct from SFX system (no reverb)

---

### 4. VOX BUS
**Purpose:** Sung vocal performances (game songs)
**Character:** Clear and dry — the clips already carry their own ensemble; space here reads as echo
**Effects:**
- Compressor: -10dB threshold, 1.5:1 ratio, 12ms attack, 180ms release (preserves dynamics)
- Reverb: 0.3 room size, 0.75 damping, 5% wet (near-dry; 15% + 0.5 room made the rendered vocal doubles read as a slap/echo)

**Content:** Mariachi vocals, choir lines (vox/*.ogg samples)  
**Boost:** Same as Music (1.15x game, 1.8x title, 0.6x victory)

---

### 5. VOXGRUNT BUS
**Purpose:** Ad-lib reactions, grunts, ad-libs during gameplay  
**Character:** Separated from main vocals to prevent ducking issues  
**Effects:**
- Compressor: -4dB threshold, 2.5:1 ratio, 5ms attack, 120ms release (keeps peaks controlled)
- Reverb: 0.3 room size, 0.75 damping, 4% wet (matches Vox, near-dry)

**Content:** Character reactions, ad-libs  
**Boost:** Same as Music/Vox

---

### 6. CUTSCENE BUS
**Purpose:** Per-scene audio beds (`audio_file` in `data/cutscene_config.json`), played by `play_cutscene_audio()`. Spoken dialogue does not use this bus: `VoiceManager` plays it on Vox.  
**Character:** Clean, tight  
**Effects:**
- Compressor: -18dB threshold, 3:1 ratio, 15ms attack, 200ms release, +1dB makeup gain (consistent dialogue levels)
- Reverb: 0.2 room size, 0.8 damping, 5% wet (minimal echo, focus on clarity)

**Content:** `audio/cutscene_*.ogg` (20 files, ~1.3 MB)
**Dialogue:** speakers hero, baron, abuela, kid, guitar, chorus; clips in `audio/voice/<speaker>/` (see `VOICE_SETUP.md`), on the Vox bus.

---

### 7. AMBIENT BUS
**Purpose:** Background atmosphere, ambience, pads  
**Character:** Wide, atmospheric, evolving  
**Effects:**
- Compressor: -25dB threshold, 1.2:1 ratio, 100ms attack, 500ms release (transparent, only catches peaks)
- Reverb: 0.8 room size, 0.3 damping, 25% wet (large, reverberant space)

**Usage:** Created and configured, but nothing routes to it yet  
**Volume Control:** None (not touched by `set_volumes()`)

---

### 8. UI BUS
**Purpose:** Menu clicks, selections, confirmations  
**Character:** Tight, immediate, attention-grabbing  
**Effects:**
- Compressor: -12dB threshold, 5:1 ratio, 5ms attack, 100ms release, +2dB makeup gain (punchy, controlled peaks)

**Usage:** Created and configured, but nothing routes to it yet (menu clicks currently play on SFX)  
**Volume Control:** None (not touched by `set_volumes()`)

---

## Gain Staging

**Reference Levels:**
- -6dB to -3dB: Peaks during normal gameplay
- -3dB to 0dB: Rare peaks (dialogue peaks, big explosions)
- 0dB: Master limiting ceiling at -0.5dB

**Measuring:** average levels are not recorded here. Run the harness `mix` mode
(see `AGENTS.md`) to print peak/RMS/crest and bus levels for a track.

---

## Usage Examples

### Playing Music
```gdscript
snd.start_music("game")  # Routes to Music bus
```

### Playing SFX
```gdscript
snd.sfx("pop", 1.0)  # Routes to SFX bus
```

### Playing Cutscene Audio
```gdscript
snd.play_cutscene_audio("res://audio/cutscene_c_fiesta.ogg")  # Routes to Cutscene bus
```

### Setting Volumes
```gdscript
snd.set_volumes(music_level, sfx_level)  # 0-10 scale
# Sets Music/Vox/VoxGrunt buses from music_level (x0.7), SFX from sfx_level
# Cutscene/Ambient/UI are not touched
```

---

## Performance Notes

**Effects:** 1 limiter (Master), 7 compressors (one per bus except Master) and 5 reverbs
(Music, Vox, VoxGrunt, Cutscene, Ambient). CPU cost has not been measured.

**Memory:**
- Cutscene audio: ~1.3 MB (20 OGG files)
- Voice pool: 40 simultaneous voices (instruments + effects)
- Effect chains: Minimal overhead

---

## Future Enhancements

- [ ] Dynamic ducking (dialogue ducks music automatically)
- [ ] Parametric EQ per bus for tone shaping
- [ ] Sidechain compression (drums punch through mix)
- [ ] Send/Return auxiliary buses for shared effects
- [ ] Real-time analyzer for gain metering UI
- [ ] Voice/music crossfade during story moments
- [ ] Surround sound panning for 3D cutscenes

---

## Troubleshooting

**No Audio:** Check `have` flag in sound.gd (audio pack must be loaded)  
**Audio Too Quiet:** Adjust bus volume with `set_volumes()` or check Save.data.opt settings  
**Audio Distorted:** Master limiter is engaged; check mix levels  
**Echo/Reverb Excessive:** Reduce reverb wet percentage on problematic bus  
**Dialogue Unclear:** dialogue plays on the Vox bus; check its compressor (−10 dB, 1.5:1)
