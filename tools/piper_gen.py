#!/usr/bin/env python3
"""Generate voice lines with Piper TTS, ready for WORLD processing.

Usage:
    python piper_gen.py --text "Hello world" [--output out.wav] [--voice en_US-male-medium]
    python piper_gen.py --text "Line 1" --text "Line 2" --prefix vox_

Options:
    --text TEXT         Text to synthesize (repeatable)
    --output PATH       Output WAV file (default: stdout)
    --voice VOICE       Piper voice model (default: en_US-male-medium)
    --prefix PREFIX     Prefix for batch output files (auto-numbered)
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


def synthesize(text, voice_name="en_US-male-medium", output_file=None):
    """Synthesize text with Piper TTS.

    Args:
        text: Text to synthesize
        voice_name: Piper voice model ID
        output_file: Path to write WAV, or None for bytes

    Returns:
        WAV bytes or None if written to file
    """
    voice = PiperVoice.load(voice_name, use_cuda=False)

    # Piper returns (audio_data, sample_rate)
    wav_file = io.BytesIO()
    voice.synthesize(text, wav_file)
    wav_file.seek(0)

    if output_file:
        with open(output_file, 'wb') as f:
            f.write(wav_file.read())
        return None
    else:
        return wav_file.getvalue()


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
            synthesize(text, args.voice, output_path)
        print(f"Generated {len(args.text)} files with prefix '{args.prefix}'", file=sys.stderr)
        return 0

    # Single mode
    if len(args.text) > 1:
        print("Error: use --prefix for multiple texts", file=sys.stderr)
        return 1

    text = args.text[0]
    if args.output:
        print(f"Generating: {args.output}", file=sys.stderr)
        synthesize(text, args.voice, args.output)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        # Write to stdout
        wav_bytes = synthesize(text, args.voice)
        sys.stdout.buffer.write(wav_bytes)

    return 0


if __name__ == "__main__":
    sys.exit(main())
