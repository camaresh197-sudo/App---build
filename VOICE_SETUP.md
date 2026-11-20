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
- Example: "Promise me" → `promise_me.ogg`

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

For quick testing, implement TTS in `voice_manager.gd`:
- Google Cloud TTS API
- Local espeak/festival
- Other TTS service

Enable: `voice_mgr.tts_enabled = true`

## Silence Lines

If a speaker shouldn't have audio (chorus reactions, etc), create empty/silent `.ogg` file or leave blank for text-only display.
