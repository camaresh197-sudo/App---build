#!/usr/bin/env python3
"""Build the offline diphone bank for the TIMING preview.

Single phones spliced together were gibberish. A diphone keeps the transition (the part
the ear needs), so the game can assemble arbitrary IPA from these clips and stay
intelligible.

Outputs:
  godot/hula/audio/di_bank.ogg          one mono stream, every pair back to back
  godot/hula/data/data_diphone_bank.json  pair "p1|p2" -> start/dur in the stream

Usage (from the repo root):
  python tools/diphone_bank.py [--voice en_US-ryan-high] [--force]
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from piper import PiperVoice

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "tools" / "models"
DATA = ROOT / "godot" / "hula" / "data"
OUT_OGG = ROOT / "godot" / "hula" / "audio" / "di_bank.ogg"
OUT_JSON = DATA / "data_diphone_bank.json"

FS = 22050
GAP = 0.02          # silence between pairs so a seek cannot bleed the previous one
SILENCE = 0.0025


def trim(x: np.ndarray) -> np.ndarray:
    if x.size == 0:
        return x
    loud = np.abs(x) > SILENCE
    if not loud.any():
        return x
    a = int(np.argmax(loud))
    b = int(len(loud) - np.argmax(loud[::-1]))
    pad = int(0.004 * FS)
    return x[max(0, a - pad):min(len(x), b + pad)]


def find_ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    for p in packages.rglob("ffmpeg.exe"):
        return str(p)
    raise FileNotFoundError("ffmpeg not found; run: winget install ffmpeg")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="en_US-ryan-high")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if OUT_OGG.exists() and not a.force:
        print("bank exists; pass --force to rebuild")
        return 0

    phones = list(json.loads((DATA / "data_phon_bank.json").read_text(encoding="utf-8"))["phones"].keys())
    voice = PiperVoice.load(str(MODELS / f"{a.voice}.onnx"))
    pmap = voice.config.phoneme_id_map
    pad = pmap["_"][0]   # Piper trained with a pad id after every phoneme; without it the output is gibberish
    voice_ids = {(p, b): [pmap["^"][0], pad, pmap[p][0], pad, pmap[b][0], pad, pmap["$"][0]]
                 for p in phones for b in phones}
    pieces, bank = [], {}
    t = 0.0
    for p in phones:
        for b in phones:
            ids = voice_ids[(p, b)]
            try:
                x = np.asarray(voice.phoneme_ids_to_audio(ids), dtype=np.float64)
            except Exception as e:
                print("skip", p, b, e)
                continue
            x = trim(x)
            if x.size < int(0.03 * FS):
                continue
            peak = float(np.max(np.abs(x))) or 1.0
            x = x / peak * 0.9
            bank[f"{p}|{b}"] = {"start": round(t, 4), "dur": round(x.size / FS, 4)}
            pieces.append(x)
            pieces.append(np.zeros(int(GAP * FS)))
            t += x.size / FS + GAP
            if len(bank) % 200 == 0:
                print(f"  {len(bank)} pairs, {t:.1f}s", flush=True)
    if not pieces:
        print("nothing rendered")
        return 1
    y = np.concatenate(pieces).astype(np.float32)
    OUT_OGG.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "bank.wav"
        sf.write(str(tmp), y, FS, subtype="PCM_16")
        r = subprocess.run([find_ffmpeg(), "-y", "-i", str(tmp), "-ar", str(FS), "-ac", "1",
                            "-c:a", "libvorbis", "-q:a", "4", str(OUT_OGG)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr[-800:])
    OUT_JSON.write_text(json.dumps({"voice": a.voice, "rate": FS, "pairs": bank},
                                   ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(bank)} pairs, {t:.1f}s, {OUT_OGG.stat().st_size / 1e6:.2f} MB")
    print("wrote", OUT_OGG.relative_to(ROOT), "and", OUT_JSON.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
