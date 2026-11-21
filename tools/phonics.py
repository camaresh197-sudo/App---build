#!/usr/bin/env python3
"""Build data/data_phonics.json: the word-by-word phonics the singer reads.

For every word in the victory lyrics:
  say        text handed to Piper (pronunciation overrides live here)
  ipa        what Piper actually phonemizes for `say`
  pron       what the lyric sheet shows under the word
  syllables  syllable count of the sung form

`piper_sing.py` loads this once on first render, so the engine no longer has to
guess a pronunciation from the spelling on every call.

    python tools/phonics.py
"""
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
HULA = ROOT / "godot" / "hula"
OUT = HULA / "data" / "data_phonics.json"

sys.path.insert(0, str(TOOLS))
import piper_sing as ps  # noqa: E402

# Hand-authored phonics. The engine only needs `say`; the rest is for the sheet.
MANUAL = {
    "gay": {
        "ipa": "ɡeɪ",
        "pron": "/ɡeɪ/",
        "say": "gay",
        "phonics": [
            {"grapheme": "g", "sound": "/ɡ/", "hint": "hard G, as in give or go"},
            {"grapheme": "ay", "sound": "/eɪ/", "hint": "vowel team (digraph), long A, as in day, stay, play"},
        ],
        "nato": ["Golf", "Alpha", "Yankee"],
    },
}


def main():
    lyrics = json.loads((HULA / "data" / "data_lyrics.json").read_text(encoding="utf-8"))
    texts = lyrics["victory_vocals"].values()
    words = sorted({w.lower() for t in texts for w in ps.words_of(t)})

    from piper import PiperVoice
    voice = PiperVoice.load(str(TOOLS / "models" / "en_US-ryan-high.onnx"),
                            config_path=str(TOOLS / "models" / "en_US-ryan-high.onnx.json"),
                            use_cuda=False)

    data = {}
    for w in words:
        say = MANUAL.get(w, {}).get("say", ps.SAY.get(w, w))
        chunks = voice.phonemize(say)
        toks = [t for sent in chunks for t in sent if t.strip() and t not in ",.!?;:"]
        ipa = "".join(toks)
        nuclei, prev = 0, False
        for t in toks:
            v = bool(t) and t[0] in ps.VOWELS
            if v and not prev:
                nuclei += 1
            prev = v
        entry = {
            "say": say,
            "ipa": ipa,
            "pron": ps.PRON.get(w, ipa),
            "syllables": max(1, nuclei),
        }
        entry.update({k: v for k, v in MANUAL.get(w, {}).items()
                      if k in ("ipa", "pron", "phonics", "nato")})
        data[w] = entry

    OUT.write_text(json.dumps({"words": data}, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(data)} words)")


if __name__ == "__main__":
    main()
