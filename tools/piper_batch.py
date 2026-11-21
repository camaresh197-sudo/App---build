#!/usr/bin/env python3
"""Batch-generate cutscene voice lines with Piper TTS -> OGG for Godot.

Reads every (speaker, line) pair from godot/hula/data/data_cutscenes.json,
synthesizes each with the speaker's Piper voice, converts to 48 kHz mono
OGG, and writes to godot/hula/audio/voice/<speaker>/<line>.ogg.

Voice map:
  hero   -> en_US-ryan-high (single take: multi-take mixes smear like a chorus)
  baron  -> en_US-danny-low
  abuela -> en_US-amy-medium
  kid    -> en_US-bryce-medium (pitched up ~25% so he sounds young)
  guitar -> en_US-joe-medium
  chorus -> bryce + joe layered (a crowd, not one person)

Filename rule mirrors voice_manager.gd: lowercase, spaces -> '_',
minus characters Windows filenames cannot contain (? * : " < > | / \\).

Usage:
    python piper_batch.py            # generate missing lines only
    python piper_batch.py --force    # regenerate everything
    python piper_batch.py --only hero --force   # one speaker only
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
HULA = ROOT / "godot" / "hula"
MODELS = TOOLS / "models"
DATA = HULA / "data" / "data_cutscenes.json"
VOICE_DIR = HULA / "audio" / "voice"

sys.path.insert(0, str(TOOLS))
import piper_gen  # noqa: E402

VOICES = {
    "hero": ["en_US-ryan-high"],
    "baron": ["en_US-danny-low"],
    "abuela": ["en_US-amy-medium"],
    "kid": ["en_US-bryce-medium"],
    "guitar": ["en_US-joe-medium"],
    "chorus": ["en_US-bryce-medium", "en_US-joe-medium"],
}

KID_PITCH = 1.25  # pitch factor for the kid voice

# amix with normalize=0 sums the inputs; weights keep layered voices off the ceiling
MIX_WEIGHTS = {
    "chorus": "1 1",
}


def safe_name(text: str) -> str:
    """Mirror voice_manager.gd's audio filename rule."""
    name = text.lower().replace(" ", "_")
    for c in '?*:"<>|/\\':
        name = name.replace(c, "")
    return name


def find_ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    for p in packages.rglob("ffmpeg.exe"):
        return str(p)
    raise FileNotFoundError("ffmpeg not found; run: winget install ffmpeg")


def wav_rate(path: Path) -> int:
    with wave.open(str(path)) as w:
        return w.getframerate()


def to_ogg(ff: str, wav: Path, ogg: Path, pitch: float = 1.0) -> None:
    """Convert WAV -> 48 kHz mono OGG, optionally pitch-shifting."""
    cmd = [ff, "-y", "-i", str(wav)]
    if pitch != 1.0:
        cmd += ["-af", f"rubberband=pitch={pitch}"]
    cmd += ["-ar", "48000", "-ac", "1", str(ogg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 and pitch != 1.0:
        # rubberband missing in this build: fall back to unshifted audio
        cmd = [ff, "-y", "-i", str(wav), "-ar", "48000", "-ac", "1", str(ogg)]
        r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {wav.name}:\n{r.stderr[-800:]}")


def mix_ogg(ff: str, wavs: list, ogg: Path, weights: str = "") -> None:
    """Layer several WAVs into one 48 kHz mono OGG. normalize=0 keeps amix from
    auto-attenuating, but it also means the inputs SUM, so a 3-take hero needs
    weights or the peaks clip."""
    cmd = [ff, "-y"]
    for w in wavs:
        cmd += ["-i", str(w)]
    n = len(wavs)
    spec = f"amix=inputs={n}:duration=longest:normalize=0"
    if weights:
        spec += f":weights={weights}"
    # normalize=0 means the inputs sum: keep the summed peaks off the ceiling
    spec += ",alimiter=limit=0.95"
    cmd += ["-filter_complex", spec, "-ar", "48000", "-ac", "1", str(ogg)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg amix failed:\n{r.stderr[-800:]}")


def collect_lines() -> list:
    data = json.loads(DATA.read_text(encoding="utf-8"))["data"]
    lines = set()
    for scenes in data.values():
        for arr in scenes.values():
            for line in arr:
                who, say = line.get("who", ""), line.get("say", "")
                if who in VOICES and say:
                    lines.add((who, say))
    return sorted(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="regenerate existing files")
    ap.add_argument("--only", default="", help="regenerate only this speaker (e.g. hero)")
    args = ap.parse_args()

    ff = find_ffmpeg()
    lines = collect_lines()
    if args.only:
        lines = [ln for ln in lines if ln[0] == args.only]
    print(f"Dialogue lines found: {len(lines)}")

    made = skipped = 0
    for who, say in lines:
        out = VOICE_DIR / who / (safe_name(say) + ".ogg")
        if out.exists() and not args.force:
            skipped += 1
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            wavs = []
            for i, voice in enumerate(VOICES[who]):
                wav = Path(td) / f"{i}.wav"
                piper_gen.synthesize(say, voice, str(wav), str(MODELS))
                wavs.append(wav)
            if len(wavs) == 1:
                pitch = KID_PITCH if who == "kid" else 1.0
                to_ogg(ff, wavs[0], out, pitch)
            else:
                mix_ogg(ff, wavs, out, MIX_WEIGHTS.get(who, ""))
        made += 1
        print(f"  {who}: {out.name}")

    print(f"Generated {made}, already present {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
