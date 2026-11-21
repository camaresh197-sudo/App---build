#!/usr/bin/env python3
"""Generate voice lines with Piper TTS, ready for WORLD processing.

Usage:
    python piper_gen.py --text "Hello world" [--output out.wav] [--voice en_US-male-medium] [--model-dir ./models]
    python piper_gen.py --text "Line 1" --text "Line 2" --prefix vox_ [--model-dir ./models]

Options:
    --text TEXT         Text to synthesize (repeatable)
    --output PATH       Output WAV file (default: stdout)
    --voice VOICE       Piper voice model (default: en_US-male-medium)
    --prefix PREFIX     Prefix for batch output files (auto-numbered)
    --model-dir DIR     Directory with downloaded .onnx/.json model files
    --list-voices       Show available voices and exit
"""

import argparse
import sys
import io
from pathlib import Path

try:
    from piper.voice import PiperVoice
except ImportError:
    print("Error: piper-tts not installed. Run: pip install piper-tts", file=sys.stderr)
    sys.exit(1)

try:
    import soundfile as sf
except ImportError:
    print("Error: soundfile not installed. Run: pip install soundfile", file=sys.stderr)
    sys.exit(1)


def _attach(voice):
    """Use pronounce/lexicon.json for word pronunciations, when the pronounce tool is present."""
    try:
        from pronounce.engine import attach_lexicon
    except ImportError:
        return voice
    return attach_lexicon(voice)


def list_voices():
    """Show available Piper voices."""
    voices = {
        "en_US-male-medium": "Medium male voice (US English)",
        "en_US-female-medium": "Medium female voice (US English)",
        "en_US-male-low": "Low male voice (US English)",
        "en_US-female-low": "Low female voice (US English)",
    }
    print("Available voices:")
    for voice_id, desc in voices.items():
        print(f"  {voice_id:30} {desc}")


def synthesize(text, voice_name="en_US-male-medium", output_file=None, model_dir=None, _cache={}):
    """Synthesize text with Piper TTS.

    Args:
        text: Text to synthesize
        voice_name: Piper voice model ID
        output_file: Path to write WAV, or None for bytes
        model_dir: Directory containing .onnx/.json model files

    Returns:
        WAV bytes or None if written to file
    """
    key = (str(model_dir), voice_name)
    if key not in _cache:
        if model_dir:
            # Load from local model files
            model_path = Path(model_dir) / f"{voice_name}.onnx"
            config_path = Path(model_dir) / f"{voice_name}.json"
            if not config_path.exists():
                # Piper's standard download naming is "<voice>.onnx.json"
                config_path = Path(model_dir) / f"{voice_name}.onnx.json"
            if not model_path.exists() or not config_path.exists():
                raise FileNotFoundError(f"Model files not found in {model_dir}: {voice_name}.onnx/.json")
            _cache[key] = PiperVoice.load(str(model_path), config_path=str(config_path), use_cuda=False)
            _cache[key] = _attach(_cache[key])
        else:
            # Try to load from installed models
            _cache[key] = PiperVoice.load(voice_name, use_cuda=False)
            _cache[key] = _attach(_cache[key])
    voice = _cache[key]

    # New piper-tts (>=1.3) API: synthesize() returns an iterable of AudioChunk
    chunks = voice.synthesize(text)
    first = next(iter(chunks), None)
    if first is None:
        raise RuntimeError(f"Piper produced no audio for text: {text!r}")

    import wave as _wave
    with _wave.open(str(output_file), "wb") as wav_out:
        wav_out.setframerate(first.sample_rate)
        wav_out.setsampwidth(first.sample_width)
        wav_out.setnchannels(getattr(first, "sample_channels", 1))
        chunk: Any = first
        while chunk is not None:
            wav_out.writeframes(chunk.audio_int16_bytes)
            chunk = next(iter(chunks), None)

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate voice lines with Piper TTS for WORLD processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--text", action="append", help="Text to synthesize (repeatable)")
    parser.add_argument("--output", help="Output WAV file")
    parser.add_argument("--voice", default="en_US-male-medium", help="Piper voice model")
    parser.add_argument("--prefix", help="Prefix for batch output (auto-numbered)")
    parser.add_argument("--model-dir", help="Directory with .onnx/.json model files")
    parser.add_argument("--list-voices", action="store_true", help="Show available voices")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return 0

    if not args.text:
        print("Error: provide --text to synthesize", file=sys.stderr)
        parser.print_help()
        return 1

    # Batch mode: multiple --text with --prefix
    if args.prefix:
        for i, text in enumerate(args.text):
            output_path = f"{args.prefix}{i:02d}.wav"
            print(f"Generating: {output_path}", file=sys.stderr)
            synthesize(text, args.voice, output_path, args.model_dir)
        print(f"Generated {len(args.text)} files with prefix '{args.prefix}'", file=sys.stderr)
        return 0

    # Single mode
    if len(args.text) > 1:
        print("Error: use --prefix for multiple texts", file=sys.stderr)
        return 1

    text = args.text[0]
    if args.output:
        print(f"Generating: {args.output}", file=sys.stderr)
        synthesize(text, args.voice, args.output, args.model_dir)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        wav_bytes = synthesize(text, args.voice, model_dir=args.model_dir)
        sys.stdout.buffer.write(wav_bytes)

    return 0


if __name__ == "__main__":
    sys.exit(main())
