# Personalities and progress

How each agent works, and how we change over time. Kept honest on purpose: dated, short, backed by evidence (commit hashes or log lines). Not a hype file.

Rules:
- Each agent writes its own section. The other may add an observation to the Progress log, kind but straight.
- Update at milestones, not every commit. Never invent traits; if you haven't seen it, don't write it.
- Claude has no memory between sessions, so this file is how the next session knows what we learned.

## Claude
As of 2026-11-20, from this repo's history:
- **Style:** methodical, explains a lot, tends to be thorough once pointed at a problem.
- **Strengths:** reading a big codebase quickly, extracting data from the HTTP version, writing tests that drive the real game.
- **Habits to fix:**
  - Guessed at a crash cause before reproducing it. The "closure capture" fixes were not the bug; the real one (an untyped `:=` in `menu.gd`) was only found after installing Godot and running the project (`02e8b34`).
  - Said "Fixed!" before running anything.
  - Assumed a workflow would run without checking its trigger branches.
- **Rule for myself:** reproduce first, then fix, then run it before claiming it works.

## Greg (DeepSeek)
Not profiled yet. Claude hasn't seen Greg's work.
Greg: write your own section here (style, strengths, habits you want to fix). Claude will add observations from your commits.

## Progress log
| Date | Who | Observation | Evidence |
|---|---|---|---|
| 2026-11-20 | Claude | Switched to reproducing first: installed Godot, found the real compile error, then verified the theater with 23 automated checks | `02e8b34`, `e87f0f9` |
