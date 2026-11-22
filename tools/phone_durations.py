#!/usr/bin/env python3
"""Rebuild the `dur` of every phone in data_phon_bank.json from real, in-context Piper renders.

The old values came from phones synthesized alone without Piper's pad ids, so a vowel could read
0.43 s and the TIMING tab's default phone lengths were nonsense. Here every sung lyric line (plus
every word in data_phonics.json, in short carrier phrases) is rendered through `piper_sing.line_audio`
and each phone's length is the median of its aligned spans.

Usage: python3 tools/phone_durations.py [--voice en_US-ryan-high] [--dry-run]
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import piper_sing as ps  # noqa: E402

DATA = ps.HULA / "data"
BANK = DATA / "data_phon_bank.json"
MARKS = "ˈˌːˑ"


COVER = ("ship fish wash think thank mouth bath this that mother yes you yellow young red run rain very vine "
         "love sing song ring long thing finger bird word turn her butter water little city later better "
         "pizza hello button certain bottle uh-huh yeah zoo zebra pleasure measure vision chair church "
         "judge jump gym cheese bell fall milk pool woo wow what why when who how here there hour fire "
         "poor sure cure door more floor four boat coat road go no oh eight day way say hey ray play "
         "bee see tree free key me we she be sky my fly eye high pie buy cow now house brown out loud "
         "boy toy oil join coin cup up sun fun bus cut book look good put foot pull moon food blue true "
         "cat hat man map bad sad dad pen ten red bed said head get set let pig big sit hit kid fish").split()


FALLBACK = {"ɾ": 0.04, "ʔ": 0.05, "ː": 0.08}


def split_ipa(ipa: str) -> list:
    """Phones with their stress mark (m) and length mark (x), the shape the TIMING tab stores."""
    out, mark = [], ""
    for ch in ipa:
        if ch in "ˈˌ":
            mark += ch
        elif ch in "ːˑ":
            if out:
                out[-1]["x"] = out[-1].get("x", "") + ch
        elif ch not in "./ ":
            out.append({"p": ch, "m": mark})
            mark = ""
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="en_US-ryan-high")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    phonics = json.loads((DATA / "data_phonics.json").read_text(encoding="utf-8"))
    table = phonics.get("words", phonics)
    lyrics = json.loads((DATA / "data_lyrics.json").read_text(encoding="utf-8"))["victory_vocals"]
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    known = set(bank["phones"])

    def ipa_of(word: str) -> str:
        e = table.get(word.lower().strip(",.!?'\" "))
        return str(e.get("ipa", "")) if e else ""

    lines = []
    for text in lyrics.values():
        ws = [ipa_of(w) for w in ps.words_of(text)]
        if all(ws):
            lines.append(ws)
    words = sorted({str(e.get("ipa", "")) for e in table.values() if isinstance(e, dict) and e.get("ipa")})
    for i in range(0, len(words), 4):   # four words per carrier phrase, so each keeps context
        lines.append(words[i:i + 4])

    # extra coverage: common words phonemized by espeak, four to a phrase, so rare phones get samples
    model = ps.aligned_voice(a.voice)
    extra = [model.phonemize(w) for w in COVER]
    extra = ["".join(p for s in e for p in s) for e in extra]
    for i in range(0, len(extra), 4):
        lines.append(extra[i:i + 4])

    seen = {}
    for n, ws in enumerate(lines):
        phones = [split_ipa(w) for w in ws]
        if any(not p for p in phones):
            continue
        x, bounds = ps.line_audio(a.voice, phones)
        for wi, w in enumerate(phones):
            for j, ph in enumerate(w):
                lo, hi = bounds[wi][j]
                # spans include the next pad id; keep them as the phone's length
                seen.setdefault(ph["p"], []).append((hi - lo) / ps.FS)
        if n % 25 == 0:
            print("  line %d/%d" % (n, len(lines)), flush=True)

    changed = 0
    for p, rec in bank["phones"].items():
        v = seen.get(p)
        if v and len(v) >= 3:
            d = round(float(statistics.median(v)), 3)
        else:   # espeak en-us never emits these; borrow a neighbour or use a typical value
            alias = {"r": "ɹ"}.get(p)
            d = float(statistics.median(seen[alias])) if alias in seen else FALLBACK.get(p, 0.1)
            d = round(d, 3)
            print("  no samples for %r; using %.3f" % (p, d))
        if abs(d - float(rec.get("dur", 0))) > 1e-6:
            changed += 1
        rec["dur"] = d
        rec["n"] = len(v or [])
    print("phones: %d, changed: %d" % (len(bank["phones"]), changed))
    for p in sorted(bank["phones"], key=lambda k: -bank["phones"][k]["dur"])[:6]:
        print("  longest", p, bank["phones"][p]["dur"])
    if not a.dry_run:
        BANK.write_text(json.dumps(bank, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("wrote", BANK)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
