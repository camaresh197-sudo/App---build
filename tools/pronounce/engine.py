#!/usr/bin/env python3
"""Piper voice with a learned pronunciation lexicon.

Words in lexicon.json override the phonemes espeak would pick. Each correction is kept in
the word's history, so the current choice can be changed later without losing what was tried.

  python3 engine.py learn am "ɪ m" "reference recording"   record a preferred pronunciation
  python3 engine.py show                                    list learned words
  python3 engine.py say "I am Jeff" out.wav                 render a line with the current lexicon
"""
import json, re, subprocess, sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEX = HERE / "lexicon.json"
DEFAULT_MODEL = Path("/tmp/claude-0/-home-user-App---build/52614612-3053-58a7-bee3-6afd8b0ea48b/scratchpad/piper/ryan.onnx")
PUNCT = set(",.!?;:'\"-")


def load_lex():
    return json.loads(LEX.read_text()) if LEX.exists() else {}


def learn(word, ipa, note=""):
    lex = load_lex()
    key = word.lower()
    entry = lex.setdefault(key, {"ipa": [], "history": []})
    tokens = ipa.split()
    entry["history"].append({"ipa": tokens, "note": note, "date": date.today().isoformat()})
    entry["ipa"] = tokens
    LEX.write_text(json.dumps(lex, ensure_ascii=False, indent=2) + "\n")
    return entry


def _norm(tok):
    return re.sub(r"[^a-z']", "", tok.lower())


def _sheet_words():
    """Words the lyric sheet defines (data_phonics.json). The sheet is the source of truth for
    the song, so lexicon overrides skip these and the sung phrase keeps Piper's in-context forms."""
    p = HERE.parents[1] / "godot" / "hula" / "data" / "data_phonics.json"
    if not p.exists():
        return set()
    return {k.lower() for k in json.loads(p.read_text(encoding="utf-8")).get("words", {})}


SHEET = _sheet_words()


def _overridden(key, lex):
    return key in lex and bool(lex[key]["ipa"]) and key not in SHEET


def phonemize_with_lexicon(text, base_phonemize, lex):
    """Lines with no lexicon word keep espeak's sentence output unchanged. Otherwise each word is
    phonemized alone, lexicon words are substituted, and the words are joined with spaces."""
    if not any(_overridden(_norm(w), lex) for w in text.split()):
        return base_phonemize(text)
    sentences = [[]]
    for w in text.split():
        key = _norm(w)
        tail = [c for c in w if c in ",.!?;:"]
        if _overridden(key, lex):
            seg = list(lex[key]["ipa"]) + tail
        else:
            seg = [t for s in base_phonemize(w) for t in s]
        if sentences[-1]:
            sentences[-1].append(" ")
        sentences[-1].extend(seg)
    return sentences


def attach_lexicon(voice):
    """Route a loaded PiperVoice's phonemizer through lexicon.json (used by the singer and piper_gen)."""
    if getattr(voice, "_lexicon_attached", False):
        return voice
    base = voice.phonemize

    def phonemize(text):
        return phonemize_with_lexicon(text, base, load_lex())

    voice.phonemize = phonemize
    voice._lexicon_attached = True
    return voice


def load_voice(model=DEFAULT_MODEL):
    from piper import PiperVoice
    voice = PiperVoice.load(str(model), include_alignments=True)
    base = voice.phonemize

    def phonemize(text):
        return phonemize_with_lexicon(text, base, load_lex())

    voice.phonemize = phonemize
    return voice


def say(text, out_path):
    import numpy as np, soundfile as sf
    from piper import SynthesisConfig
    voice = load_voice()
    cfg = SynthesisConfig(length_scale=1.25, noise_scale=0.4, noise_w_scale=0.5)
    audio = np.concatenate([c.audio_float_array for c in voice.synthesize(text, syn_config=cfg)])
    sf.write(out_path, audio, voice.config.sample_rate)
    return out_path


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "learn":
        e = learn(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
        print(f"{sys.argv[2]}: {' '.join(e['ipa'])}  ({len(e['history'])} recorded choices)")
    elif cmd == "say":
        print(say(sys.argv[2], sys.argv[3]))
    else:
        for w, e in load_lex().items():
            print(f"{w:12s} {' '.join(e['ipa']):12s} {len(e['history'])} choice(s)")
