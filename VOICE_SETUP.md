# Cutscene Voice Setup

Cutscenes use dialogue from extracted data with custom voice recordings.

## Voice File Organization

Place pre-recorded voice lines in:
```
godot/hula/audio/voice/[speaker]/[dialogue].ogg
```

**Speakers:** hero, baron, abuela, kid, guitar, chorus

**Dialogue filename:** 
- Lowercase, spaces → underscores
- Characters Windows filenames can't hold (`? * : " < > | / \`) are stripped
- Example: "Promise me" → `promise_me.ogg`, "Why? I looked up to you." → `why_i_looked_up_to_you..ogg`

## Example Structure

```
godot/hula/audio/voice/
├── hero/
│   ├── promise_me.ogg
│   ├── adios_globo.ogg
│   └── ...
├── baron/
│   ├── impossible.ogg
│   └── ...
├── abuela/
│   └── come_come_tamales.ogg
└── chorus/
    └── we_promise.ogg
```

## Recording Guidelines

1. **Format:** OGG Vorbis, 48kHz, mono
2. **Quality:** Clean, clear voice acting
3. **Timing:** Match dialogue pacing (~2.5 chars/sec estimate, or use `gap` field)
4. **Consistency:** Keep speaker voices distinct and consistent

## Linking to Cutscenes

Voice lines auto-load when cutscene plays:
- Speaker name + dialogue text → looks for matching `.ogg` file
- Falls back to timing duration if no audio

## Alternative: Text-to-Speech

Piper TTS pipeline (implemented):
- `tools/piper_batch.py` — generates every cutscene line in `data_cutscenes.json` with per-character voices
  (hero=ryan-high, baron=danny-low, abuela=amy, kid=bryce pitched +25%, guitar=joe, chorus=bryce+joe layered)
  and files them under `audio/voice/`. Run `python tools/piper_batch.py [--force] [--only <speaker>]`.
  Prefer one model per character: independently-spoken takes smear like a chorus when mixed.
- `tools/piper_sing.py` — sings the vox bank: speak the clip's lyric with `--voice` (default `en_US-ryan-high`,
  one take), time-warp the speech to the clip's melody and duration, resynthesize. The melody always comes
  from `tools/vox_backup/originals/` when present, so re-running never borrows the melody from a previous render.
- `tools/piper_gen.py` — single-line generator (model dir: `tools/models/`, `.onnx` + `.onnx.json`);
  loaded models are cached per voice so a batch doesn't reload a 120 MB model per line.
- `voice_manager.gd` resolves lines via `_safe_name()` (same rule as `piper_batch.py`) and plays them on the Vox bus.
- Cutscene playback is wired in `cutscene.gd`: each line speaks when shown, and the scene waits for the voice.

Enable: `voice_mgr.tts_enabled = true`

## Silence Lines

If a speaker shouldn't have audio (chorus reactions, etc), create empty/silent `.ogg` file or leave blank for text-only display.
