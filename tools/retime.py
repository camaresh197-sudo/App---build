#!/usr/bin/env python3
"""Apply word timing copied from the game's secret menu (TIMING tab), re-sing only what changed.

Usage (from the repo root):
  python3 tools/retime.py timing_from_phone.json [--dry-run]

1. Checks the file: every line needs words and onsets of the same length, onsets increasing.
2. Writes changed lines into godot/hula/data/data_word_timing.json.
3. Re-sings only the changed lines with tools/piper_sing.py (--only, --force).
4. Prints the snip command so you can hear the chorus without a Godot run.
"""
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "godot" / "hula" / "data" / "data_word_timing.json"


def check(lines):
    for lid, line in lines.items():
        words, onsets = line.get("words", []), line.get("onsets", [])
        if len(words) != len(onsets):
            sys.exit("%s: %d words but %d onsets" % (lid, len(words), len(onsets)))
        if any(b <= a for a, b in zip(onsets, onsets[1:])):
            sys.exit("%s: onsets must increase" % lid)
        if onsets and onsets[0] < 0:
            sys.exit("%s: first onset is negative" % lid)
        ipa = line.get("ipa")
        if ipa is not None and len(ipa) != len(words):
            sys.exit("%s: %d words but %d IPA entries" % (lid, len(words), len(ipa)))
        phones = line.get("phones")
        if phones is not None:
            if len(phones) != len(words):
                sys.exit("%s: %d words but %d phone lists" % (lid, len(words), len(phones)))
            for i, ph in enumerate(phones):
                for p in ph:
                    if not p.get("p") or float(p.get("d", 0)) <= 0:
                        sys.exit("%s: word %d has an empty phone" % (lid, i))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_file")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    incoming = json.loads(Path(a.json_file).read_text(encoding="utf-8-sig")).get("lines", {})
    check(incoming)
    current = json.loads(DATA.read_text(encoding="utf-8"))
    changed = [lid for lid in incoming
               if lid not in current["lines"]
               or any(current["lines"][lid].get(k) != incoming[lid].get(k) for k in ("onsets", "ipa", "phones"))]
    if not changed:
        print("nothing changed; no re-sing needed")
        return
    for lid in changed:
        print("%s: %s -> %s" % (lid, current["lines"].get(lid, {}).get("onsets"), incoming[lid]["onsets"]))
    if a.dry_run:
        return

    for lid in changed:
        current["lines"].setdefault(lid, {}).update(incoming[lid])
    DATA.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("updated", DATA.relative_to(ROOT))
    ipa_changed = [lid for lid in changed if incoming[lid].get("ipa") or incoming[lid].get("phones")]
    if ipa_changed:
        print("note: IPA/phone-length edits are stored for the game; piper_sing still sings")
        print("      the text in data_phonics.json, so it does not apply them yet: %s" % ", ".join(ipa_changed))

    subprocess.run([sys.executable, str(ROOT / "tools" / "piper_sing.py"), "--only", ",".join(changed), "--force"],
                   cwd=str(ROOT / "tools"), check=True)
    print("\nre-sung: %s" % ", ".join(changed))
    print("hear it with the stem (run a Godot mix first only when the stem needs re-extracting):")
    print("  python3 tools/snip_from_stem.py --stems stems --clips-dir godot/hula/audio/vox "
          "--start 19.36 --end 33.50 --out chorus.wav")


if __name__ == "__main__":
    main()
