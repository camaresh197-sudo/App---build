#!/usr/bin/env python3
"""
Generate victory song vocals with Piper TTS.
Run this on your local machine with internet access.

Usage:
    python3 tools/generate_piper_vocals.py

    Or from project root:
    python3 tools/generate_piper_vocals.py .
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Auto-detect repo root
    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    else:
        # Look for godot/hula marker
        repo_root = Path.cwd()
        if not (repo_root / "godot/hula").exists():
            # Try parent
            repo_root = repo_root.parent

        if not (repo_root / "godot/hula").exists():
            print("Error: Could not find App---build repo root")
            print("Usage: python3 tools/generate_piper_vocals.py [repo_path]")
            sys.exit(1)

    vox_dir = repo_root / "godot/hula/audio/vox"
    vox_dir.mkdir(parents=True, exist_ok=True)

    # Map clip IDs to lyrics (11 clips to generate)
    lyrics = {
        "A0": "I Am Jeff and I'm so gay",
        "A2": "I like Jake's mom cuz of jake",
        "A6": "Jake's mom plays with Jeff all day",
        "B0": "To make him feel Proud and gay",
        "B1": "Gay gay gay gay",
        "B2": "Jake is baked. Jeff wants to bate",
        "B6": "He has done that most the day",
        "B7": "He'll hug Jake on their next date",
        "C4": "Too bad that he is Tall",
        "C6": "Jeff is gay so gay",
        "tag0": "Jeff is gay so gay",
    }

    print("Generating victory song vocals with Piper TTS")
    print("=" * 70)
    print(f"Output: {vox_dir}")
    print()

    success_count = 0
    for clip_id in sorted(lyrics.keys()):
        text = lyrics[clip_id]
        output_wav = vox_dir / f"{clip_id}.wav"

        print(f"{clip_id:5s} → {text}")

        # Use piper CLI to generate
        cmd = ["piper", "--model", "en_US-male-medium", "--output_file", str(output_wav)]

        try:
            result = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0 and output_wav.exists():
                size_kb = output_wav.stat().st_size / 1024
                print(f"       ✓ {size_kb:.1f} KB")
                success_count += 1
            else:
                print(f"       ✗ Failed: {result.stderr[:80] if result.stderr else 'unknown error'}")
        except FileNotFoundError:
            print(f"       ✗ piper not found. Run: pip install piper-tts soundfile")
            return 1
        except Exception as e:
            print(f"       ✗ Error: {e}")

    print("\n" + "=" * 70)
    print(f"Generated {success_count}/{len(lyrics)} clips")

    if success_count == len(lyrics):
        print("\n✓ All clips generated! Next steps:")
        print("  1. Run Godot import: godot --headless --path godot/hula --import")
        print("  2. Commit changes:")
        print("     git add godot/hula/audio/vox/")
        print("     git commit -m 'Victory vocals: regenerated with Piper TTS'")
        print("     git push")
        return 0
    else:
        print(f"\n✗ {len(lyrics) - success_count} clips failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
