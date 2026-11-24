#!/usr/bin/env python3
"""Fill data_word_timing.json for every sung line, so every line is editable in the TIMING tab.

Word onsets come from the same grid/reference layout piper_sing uses (`grid_melody`), so a
re-sing and the game agree. Existing onsets (e.g. B0-B2 hand edits) are kept. Run
`tools/line_env.py --lines <all>` afterwards to rebuild the graphs.

Usage (from the repo root):
  python tools/build_timing.py [--dry-run]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import piper_sing as ps  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TIMING = ROOT / "godot" / "hula" / "data" / "data_word_timing.json"
LYRICS = ROOT / "godot" / "hula" / "data" / "data_lyrics.json"

# the lines the victory sequence actually plays, in song order (F2 aliases B6)
LINES = ["A0", "A2", "A4", "A6", "B0", "B1", "B2", "B3",
         "C0", "C2", "C4", "C6", "D0", "D2", "D4", "D6",
         "tag0", "tag2", "F0", "B6"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    lyrics = json.loads(LYRICS.read_text(encoding="utf-8"))["victory_vocals"]
    old = json.loads(TIMING.read_text(encoding="utf-8")).get("lines", {})
    out = {"_note": ("Word onsets in seconds from the start of each sung clip's first word "
                     "(the 0.15 s lead-in is added by data_vox.json). Every sung line is editable "
                     "in the secret menu TIMING tab; tools/retime.py re-sings the changed lines."),
           "order": LINES, "lines": {}}
    for lid in LINES:
        text = lyrics[lid]
        words = ps.words_of(text)
        grid = list(ps.CHORUS_GRID.get(lid, []))
        if len(grid) > 5:
            grid = grid[:5]          # ignore the explicit-onsets override; use the layout
        kept = old.get(lid, {}).get("onsets", [])
        if len(kept) == len(words):
            onsets = kept
            how = "kept"
        elif grid:
            _melody, spans = ps.grid_melody(
                *grid[:3], syllables=len(words),
                hold_to=grid[3] if len(grid) > 3 else 0.0,
                word_secs=grid[4] if len(grid) > 4 else 0.0)
            onsets = [max(0.0, round(float(s[0]) * ps.FRAME_MS / 1000.0 - 0.15, 2)) for s in spans]
            how = "grid"
        else:
            onsets = [round(i * 0.27, 2) for i in range(len(words))]
            how = "even"
        out["lines"][lid] = {
            "section": grid[0] if grid else "v-B",
            "bar": int(grid[1]) if grid else 0,
            "bars": int(grid[2]) if grid else 2,
            "words": words, "onsets": onsets,
        }
        print("%-5s %-4s %2d words  %s" % (lid, how, len(words), onsets))
    if a.dry_run:
        return 0
    TIMING.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", TIMING.relative_to(ROOT))
    print("next: python tools/line_env.py --lines " + ",".join(LINES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
