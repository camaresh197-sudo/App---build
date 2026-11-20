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
**Volume Control:** Set via `Save.data.opt.music` (affects Music/Vox/VoxGrunt) and `Save.data.opt.sfx` (affects SFX)

---

### 2. MUSIC BUS
**Purpose:** Game soundtrack, title music, victory themes  
**Character:** Warm, immersive, reverberant  
**Effects:**
- Compressor: -20dB threshold, 2:1 ratio, 50ms attack, 300ms release (smooth level control)
- Reverb: 0.55 room size, 0.5 damping, 16% wet (musical ambience)

**Tracks:** game.gd, title.gd, victory.gd  
**Boost:** Applied during gameplay (1.15x) and title (1.8x), reduced during victory (0.6x)

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
**Character:** Clear, cohesive, with gentle space  
**Effects:**
- Compressor: -10dB threshold, 1.5:1 ratio, 12ms attack, 180ms release (preserves dynamics)
- Reverb: 0.5 room size, 0.6 damping, 15% wet (vocals sound like an ensemble in a small room)

**Content:** Mariachi vocals, choir lines (vox/*.ogg samples)  
**Boost:** Same as Music (1.15x game, 1.8x title, 0.6x victory)

---

### 5. VOXGRANT BUS
**Purpose:** Ad-lib reactions, grunts, ad-libs during gameplay  
**Character:** Separated from main vocals to prevent ducking issues  
**Effects:**
- Compressor: -4dB threshold, 2.5:1 ratio, 5ms attack, 120ms release (keeps peaks controlled)
- Reverb: 0.5 room size, 0.6 damping, 10% wet (matches Vox but slightly drier)

**Content:** Character reactions, ad-libs  
**Boost:** Same as Music/Vox

---

### 6. CUTSCENE BUS
**Purpose:** Story dialogue audio (Mexican Spanish text-to-speech)  
**Character:** Clean, intelligible, intimate  
**Effects:**
- Compressor: -18dB threshold, 3:1 ratio, 15ms attack, 200ms release, +1dB makeup gain (consistent dialogue levels)
- Reverb: 0.2 room size, 0.8 damping, 5% wet (minimal echo, focus on clarity)

**Content:** cutscene_*.ogg files (10 cutscenes, ~1.2 MB total)  
**Voices:** Mexican Spanish (es-mx) with different voices per character:
- hero: male voice 1
- baron: male voice 2  
- abuela: female voice 1
- kid: child voice
- guitar: male voice 3
- chorus: female voice 2

---

### 7. AMBIENT BUS
**Purpose:** Background atmosphere, ambience, pads  
**Character:** Wide, atmospheric, evolving  
**Effects:**
- Compressor: -25dB threshold, 1.2:1 ratio, 100ms attack, 500ms release (transparent, only catches peaks)
- Reverb: 0.8 room size, 0.3 damping, 25% wet (large, reverberant space)

**Usage:** Optional background atmosphere tracks  
**Volume Control:** Linked to Music volume

---

### 8. UI BUS
**Purpose:** Menu clicks, selections, confirmations  
**Character:** Tight, immediate, attention-grabbing  
**Effects:**
- Compressor: -12dB threshold, 5:1 ratio, 5ms attack, 100ms release, +2dB makeup gain (punchy, controlled peaks)

**Sounds:** Menu clicks, button presses, confirmations  
**Volume Control:** Linked to SFX volume

---

## Gain Staging

**Reference Levels:**
- -6dB to -3dB: Peaks during normal gameplay
- -3dB to 0dB: Rare peaks (dialogue peaks, big explosions)
- 0dB: Master limiting ceiling at -0.5dB

**Current Calibration:**
- Music: -15dB average
- SFX: -20dB average (heavily compressed)
- Vox: -18dB average
- Dialogue: -16dB average (consistent)
- Master: -6dB to -3dB peaks

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
# Sets Music/Vox/VoxGrunt bus to music_level
# Sets SFX/UI bus to sfx_level
```

---

## Performance Notes

**CPU Cost:**
- 2x Compressor + 1x Limiter = ~8% CPU on average game
- 2x Reverb effects = ~12% CPU
- Total audio system: ~20% CPU (acceptable)

**Memory:**
- Cutscene audio: ~1.2 MB (10 OGG files)
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
**Dialogue Unclear:** Cutscene bus compression may be too aggressive; reduce ratio or threshold
