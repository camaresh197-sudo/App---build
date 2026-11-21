#!/usr/bin/env python3
"""Generate the victory lyric sheets: docs/VICTORY_LYRICS.md + CSV exports.

The lyric sheet puts the IPA in a row directly under the words, one column per
word. The chorus sheet does the same per beat. IPA comes from the same Piper
voice the singer uses.

    python tools/lyrics_doc.py
"""
import csv
import json
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
DOC = ROOT / "docs" / "VICTORY_LYRICS.md"
CSV_LINES = ROOT / "docs" / "victory_lines.csv"
CSV_CHORUS = ROOT / "docs" / "victory_chorus.csv"
HULA = ROOT / "godot" / "hula"

sys.path.insert(0, str(TOOLS))
import piper_sing as ps  # noqa: E402

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def nn(m):
    return f"{NAMES[int(m) % 12]}{int(m) // 12 - 1}"


def load():
    v = json.loads((HULA / "data" / "data_victory.json").read_text(encoding="utf-8"))
    lyr = json.loads((HULA / "data" / "data_lyrics.json").read_text(encoding="utf-8"))["victory_vocals"]
    vox = json.loads((HULA / "data" / "data_vox.json").read_text(encoding="utf-8"))
    return v, lyr, vox


def row(v, section, bar):
    for b in v:
        if b[6] == section and int(b[7]) == bar:
            return b
    return None


def notes_for(v, section, bars):
    out = []
    for i, bar in enumerate(bars):
        b = row(v, section, bar)
        if not b:
            continue
        for s, m in enumerate(b[3]):
            if int(m) > 0:
                out.append((i * 16 + s, int(m)))
    return out


def words_of(text):
    return re.findall(r"[A-Za-z']+", text)


def ipa_of(text, voice, cache):
    out = []
    for w in words_of(text):
        key = w.lower()
        if key not in cache:
            chunks = voice.phonemize(w)
            toks = [t for sent in chunks for t in sent if t.strip() and t not in ",.!?;:"]
            cache[key] = "".join(toks)
        out.append(cache[key])
    return out


def spec():
    return [
        ("A", "v-A", [("A0", 0), ("A2", 2), ("A4", 4), ("A6", 6)], 1),
        ("B", "v-B", [("B0", 0), ("B1", 2), ("B2", 4), ("B3", 6)], 2),
        ("C", "v-C", [("C0", 0), ("C2", 2), ("C4", 4), ("C6", 6)], 1),
        ("tag", "v-tag", [("tag0", 0), ("tag1", 1), ("tag2", 2), ("tag3", 3)], 1),
        ("F", "v-F", [("F0", 0), ("F1", 1), ("F2", 2), ("F3", 3)], 1),
    ]


def grid_table(add, rows_in, max_words):
    """Rows come in pairs: a word row and an IPA row directly under it."""
    head = ["Line", "Section", "Bars", "Syll."] + [str(i + 1) for i in range(max_words)]
    add("| " + " | ".join(head) + " |")
    add("|" + "---|" * len(head))
    for r in rows_in:
        w = r["words"] + [""] * (max_words - len(r["words"]))
        p = r["ipa"] + [""] * (max_words - len(r["ipa"]))
        add(f"| **{r['line']}** | {r['section']} | {r['bars']} | {r['syllables']} | "
            + " | ".join(w) + " |")
        add("| ↳ IPA | | | | " + " | ".join(p) + " |")
        add(f"| ↳ notes | | | | " + " | ".join(
            [r["notes"][0]] + [""] * (max_words - 1)) + " |")


def main():
    v, lyr, vox = load()
    from piper import PiperVoice
    voice = PiperVoice.load(str(TOOLS / "models" / "en_US-ryan-high.onnx"),
                            config_path=str(TOOLS / "models" / "en_US-ryan-high.onnx.json"),
                            use_cuda=False)
    cache = {}
    lines, chorus_rows = [], []

    for group, sec_name, entries, span in spec():
        for cid, start in entries:
            clip = vox.get(cid, [cid])[0]
            text = lyr.get(clip)
            if not text:
                continue
            bars = list(range(start, start + span))
            words = words_of(text)
            ipa = ipa_of(text, voice, cache)
            bars_s = f"{bars[0]}–{bars[-1]}" if span > 1 else str(bars[0])
            if group == "B":
                mel = []
                for bar in bars:
                    mel += [int(x) for x in row(v, "v-B", bar)[3]]
                pitch, cur = [], 0
                for m in mel:
                    if m > 0:
                        cur = m
                    pitch.append(cur)
                k = ps.syllable_count(text)
                nts = [(b * 4, pitch[b * 4]) for b in range(k)]
                note_s = " ".join(f"{s}:{nn(m)}" for s, m in nts) + " (last held)"
                chorus_rows.append({
                    "line": cid, "bars": bars_s, "words": words[:k], "ipa": ipa[:k],
                    "notes": nts, "note_s": note_s,
                })
            else:
                nts = notes_for(v, sec_name, bars)
                note_s = " ".join(f"{s}:{nn(m)}" for s, m in nts)
                if len(nts) > 16:
                    note_s += " ..."
            lines.append({
                "line": clip, "section": sec_name, "bars": bars_s,
                "syllables": ps.syllable_count(text), "lyric": text,
                "words": words, "ipa": ipa, "note_s": note_s,
                "notes": [note_s], "nts": nts,
            })

    max_words = max(len(r["words"]) for r in lines)

    out = []
    add = out.append
    add("# Victory lyrics — words with IPA underneath")
    add("")
    add("Generated by `tools/lyrics_doc.py`. Each line is two rows: the words, then")
    add("the IPA the `en_US-ryan-high` voice says directly beneath them; the melody")
    add("notes sit in the last column. The chorus sheet adds a note row under each word.")
    add("Step = sixteenth slot (0.105 s, 16 per bar); four steps = one beat.")
    add("Excel copies: `docs/victory_lines.csv`, `docs/victory_chorus.csv`.")
    add("")

    add("## Lyrics sheet")
    add("")
    add("| Line | Section | Bars | Syll. | Row | " + " | ".join(
        str(i + 1) for i in range(max_words)) + " | Notes (step:note) |")
    add("|---|---|---|---|---|" + "---|" * max_words + "---|")

    def line_rows(rows_in):
        out2 = []
        for r in rows_in:
            w = r["words"] + [""] * (max_words - len(r["words"]))
            p = r["ipa"] + [""] * (max_words - len(r["ipa"]))
            out2.append(f"| **{r['line']}** | {r['section']} | {r['bars']} | "
                        f"{r['syllables']} | words | " + " | ".join(w)
                        + f" | {r['note_s']} |")
            out2.append("| | | | | IPA | " + " | ".join(p) + " | |")
        return out2

    for r in line_rows(lines):
        add(r)

    add("")
    add("## Chorus sheet — one word per beat")
    add("")
    add("`v-B` is four two-bar lines (bars 0–1, 2–3, 4–5, 6–7); one syllable per")
    add("beat, last held. Bars 6–7 (`B3`) use seven beats.")
    add("")
    add("| Line | Bars | Row | " + " | ".join(str(i + 1) for i in range(8)) + " |")
    add("|---|---|---|" + "---|" * 8)
    for r in chorus_rows:
        w = r["words"] + [""] * (8 - len(r["words"]))
        p = r["ipa"] + [""] * (8 - len(r["ipa"]))
        add(f"| **{r['line']}** | {r['bars']} | words | " + " | ".join(w) + " |")
        add("| | | IPA | " + " | ".join(p) + " |")
        nts = [f"{nn(m)}" for _s, m in r["notes"]] + [""] * (8 - len(r["notes"]))
        add("| | | note | " + " | ".join(nts) + " |")
    add("")
    add("### Chorus notes on the grid")
    add("")
    add("| Beat | Step | " + " | ".join(r["line"] for r in chorus_rows) + " |")
    add("|---|" + "---|" * (len(chorus_rows) + 1))
    for beat in range(8):
        step = beat * 4
        cells = []
        for r in chorus_rows:
            d = dict(r["notes"])
            cells.append(nn(d[step]) if step in d else "·")
        add(f"| {beat + 1} | {step} | " + " | ".join(cells) + " |")
    add("")
    add("`B4`–`B7` are the old one-bar chorus clips and are no longer triggered.")
    add("")
    DOC.write_text("\n".join(out), encoding="utf-8")

    with CSV_LINES.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["line", "section", "bars", "syllables"] +
                   [f"word{i+1}" for i in range(max_words)] +
                   [f"ipa{i+1}" for i in range(max_words)] + ["notes"])
        for r in lines:
            w.writerow([r["line"], r["section"], r["bars"], r["syllables"]] +
                       r["words"] + [""] * (max_words - len(r["words"])) +
                       r["ipa"] + [""] * (max_words - len(r["ipa"])) + [r["note_s"]])
    with CSV_CHORUS.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["line", "bars", "beat", "step", "word", "ipa", "note", "midi"])
        for r in chorus_rows:
            for i, ((step, m), word, ipa) in enumerate(zip(r["notes"], r["words"], r["ipa"])):
                w.writerow([r["line"], r["bars"], i + 1, step, word, ipa, nn(m), m])
    print(f"wrote {DOC.relative_to(ROOT)}, {CSV_LINES.relative_to(ROOT)}, {CSV_CHORUS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
