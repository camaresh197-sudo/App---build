#!/usr/bin/env python3
"""
Generate voice lines for cutscenes using text-to-speech.
Supports multiple TTS backends: espeak, festival, or REST API
"""

import json
import os
import subprocess
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "godot" / "hula" / "audio" / "voice"

def load_cutscene_data():
    """Load cutscene dialogue data"""
    path = Path(__file__).parent.parent / "godot" / "hula" / "data" / "data_cutscenes.json"
    with open(path) as f:
        return json.load(f)

def sanitize_filename(text: str) -> str:
    """Convert dialogue to valid filename"""
    return text.lower().replace(" ", "_").replace("!", "").replace(".", "").replace("?", "")[:50]

def generate_voice_espeak(speaker: str, text: str, voice_rate: int = 150) -> bool:
    """Generate voice using espeak"""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        speaker_dir = OUTPUT_DIR / speaker
        speaker_dir.mkdir(exist_ok=True)

        filename = sanitize_filename(text)
        output_path = speaker_dir / f"{filename}.wav"

        # espeak parameters per speaker
        voices = {
            "hero": "en-us+m3",
            "baron": "en-us+m5",
            "abuela": "en-us+f1",
            "kid": "en-us+f4",
            "guitar": "en-us+m2",
            "chorus": "en-us+f2"
        }

        voice = voices.get(speaker, "en-us+m1")
        cmd = ["espeak", "-v", voice, "-s", str(voice_rate), "-w", str(output_path), text]

        result = subprocess.run(cmd, capture_output=True, timeout=5)
        if result.returncode == 0:
            # Convert WAV to OGG
            ogg_path = output_path.with_suffix(".ogg")
            convert_cmd = ["ffmpeg", "-i", str(output_path), "-q:a", "5", "-y", str(ogg_path)]
            subprocess.run(convert_cmd, capture_output=True, timeout=10)
            output_path.unlink()  # Delete WAV
            return ogg_path.exists()
        return False
    except Exception as e:
        print(f"  ✗ {speaker}: {text[:40]} - {e}")
        return False

def main():
    if not shutil.which("espeak"):
        print("espeak not found. Install with: apt-get install espeak-ng")
        return False

    if not shutil.which("ffmpeg"):
        print("ffmpeg not found. Install with: apt-get install ffmpeg")
        return False

    data = load_cutscene_data()
    total = 0
    generated = 0

    print("Generating cutscene voice lines...")
    for cs_id, scenes in data["data"].items():
        print(f"\n{cs_id}:")
        for scene_name, events in scenes.items():
            for event in events:
                speaker = event.get("who", "")
                text = event.get("say", "")
                if speaker and text:
                    total += 1
                    if generate_voice_espeak(speaker, text):
                        generated += 1
                        print(f"  ✓ {speaker}: {text[:40]}")

    print(f"\n✓ Generated {generated}/{total} voice lines")
    return generated > 0

if __name__ == "__main__":
    import shutil
    sys.exit(0 if main() else 1)
