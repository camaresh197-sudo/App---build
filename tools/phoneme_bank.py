#!/usr/bin/env python3
"""Build the phoneme duration table used by the TIMING editor and by piper_sing.

The phone cannot run Piper. An early attempt to preview edits with one WAV per phoneme
spliced together sounded like gibberish and was removed; PLAY now uses the real clip.
`data_phon_bank.json` is still useful: the editor lists its phones in the palette and
uses their natural lengths as defaults, and piper_sing divides a word render between its
phones with those lengths.

Outputs:
  godot/hula/data/data_phon_bank.json  ipa -> natural length, voiced flag
  godot/hula/audio/phon/p<hex>.wav     only with --wavs (not used by the game anymore)

Usage (from the repo root):
  python tools/phoneme_bank.py [--voice en_US-ryan-high] [--force] [--wavs]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
from piper import PiperVoice
from piper.config import SynthesisConfig

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "tools" / "models"
DATA_IN = ROOT / "godot" / "hula" / "data"
OUT_DIR = ROOT / "godot" / "hula" / "audio" / "phon"
OUT_JSON = DATA_IN / "data_phon_bank.json"

FS = 22050
BASE_HZ = 240.0     # the model's isolated phones already sit near this; menu.gd shifts from it
LENGTH_SCALE = 4.0
SILENCE = 0.0025

# phones the editor should treat as carrying the note (vowels and sonorants)
VOICED = set("aeiouɪʊɛæʌəɜɔɐɑɒɘɚɞɨʉɯɵɶʏmnŋlrɹɾɻɽjw")

# phonemes that occur in no lyric but are likely to be typed in the editor
CORE = list("ptkbdgfvszʃʒθðmnŋlrjwhaɪʊɛæʌəɜɔoʊuː") + ["ɡ", "ɹ", "ɾ", "ʔ"]


def used_phones() -> list:
    words = json.loads((DATA_IN / "data_phonics.json").read_text(encoding="utf-8"))["words"]
    phones = set()
    for w in words.values():
        for key in ("ipa", "pron"):
            for ch in str(w.get(key, "")):
                if ch in "ˈˌːˑ/() ":
                    continue
                phones.add(ch)
    phones.update(CORE)
    return sorted(phones)


def trim(x: np.ndarray) -> np.ndarray:
    if x.size == 0:
        return x
    loud = np.abs(x) > SILENCE
    if not loud.any():
        return x
    a = int(np.argmax(loud))
    b = int(len(loud) - np.argmax(loud[::-1]))
    pad = int(FS * 0.01)
    return x[max(0, a - pad):min(len(x), b + pad)]


def save_wav(path: Path, x: np.ndarray) -> None:
    import wave
    pcm = (np.clip(x, -1.0, 1.0) * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FS)
        w.writeframes(pcm.tobytes())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="en_US-ryan-high")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--wavs", action="store_true", help="also write audio/phon/*.wav (unused by the game)")
    a = ap.parse_args()

    model = MODELS / f"{a.voice}.onnx"
    if not model.exists():
        sys.exit(f"missing model: {model}")
    voice = PiperVoice.load(str(model))
    cfg = SynthesisConfig(length_scale=LENGTH_SCALE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    phones = used_phones()
    bank = {"voice": a.voice, "rate": FS, "base_hz": BASE_HZ, "phones": {}}
    made = skipped = 0
    for ph in phones:
        name = "p%04x" % ord(ph)
        out = OUT_DIR / f"{name}.wav"
        try:
            ids = voice.phonemes_to_ids([ph])
            if 1 not in ids or len(ids) <= 3:
                skipped += 1
                continue
            x = np.asarray(voice.phoneme_ids_to_audio(ids, cfg), dtype=np.float64)
        except Exception as e:
            print(f"skip {ph!r}: {e}")
            skipped += 1
            continue
        x = trim(x)
        if x.size < int(FS * 0.02):
            skipped += 1
            continue
        peak = float(np.max(np.abs(x))) or 1.0
        x = x / peak * 0.9
        if a.wavs and (a.force or not out.exists()):
            save_wav(out, x)
            made += 1
        bank["phones"][ph] = {"file": f"phon/{name}.wav", "dur": round(x.size / FS, 3), "voiced": ph in VOICED}

    OUT_JSON.write_text(json.dumps(bank, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    total = sum(p["dur"] for p in bank["phones"].values())
    print(f"{len(bank['phones'])} phones ({made} written, {skipped} skipped), {total:.2f}s total")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
