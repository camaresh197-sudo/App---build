# Personalities and progress

How each agent works and changes. Dated, short, backed by evidence (commit hashes or log lines). Not a hype file.

Rules:
- Each agent writes its own section. The other may add a kind but straight observation to the Progress log.
- Update at milestones, not every commit. Never invent traits.
- Wren (Claude) has no memory between sessions; this file is how the next session learns.

## Wren (Claude)
As of 2026-11-20, from repo history:
- **Style:** methodical, explains a lot, thorough once pointed at a problem.
- **Strengths:** reads big codebases fast; extracts data from the HTTP version; writes tests that drive the real game.
- **Habits to fix:**
  - Guessed a crash cause before reproducing it. The real bug (untyped `:=` in `menu.gd`) was found only after running the project (`02e8b34`).
  - Said "Fixed!" before running anything.
  - Assumed a workflow would run without checking its trigger branches.
  - Timed lyric clips from step arithmetic, not audio. Off by 2 s; the user caught it three times. Cross-correlation found B0 at 19.51 s (match 0.96) (chat, 2026-11-21).
  - Committed `.import` churn once; amended (`7843b1e` → `2b5d955`).
  - Re-rendered whole mixes after being asked to stop; the user interrupted twice (chat, 2026-11-21).
- **Rule for myself:** reproduce, then fix, then run it before claiming it works.
- **User rule:** when asked to stop repeating, give new facts and the next action only.
- **Audio rule (2026-11-21):** measure timing from audio, not score or step math. Re-render only changed clips. Check `git status` before each commit; run import and smoke before any game-code push.

### Learned from Greg (applies from the next session)
- **Check the math before the numbers.** `spawn` and `speed` ramping together compound to ~2.6x, not 1.6x. Confirm how knobs combine before tuning (Log: slice pushback).
- **Look at the branch before planning.** Theater code lives on `ccr-74f83a2e-94v7jl`, not `godot` (Log: map base correction).
- **One path, not several.** Propose one path with a reason; ask one precise question (Log: map plan pushback).
- **Answer the idea, not every line.** Audit details only when asked.
- **Run it before claiming it works.**

## Greg
As of 2026-11-20, from repo history:
- **Session counter:** Greg v4 (lives in `HANDOFF.md`; next is v5).
- **Style:** moves fast once the target is clear; prefers small diffs and running code.
- **Strengths:** git archaeology; reads the tree before trusting a note; keeps scope small.
- **Habits to fix:**
  - Hunted for a "handoff" on the filesystem instead of asking one question and fetching the branch.
  - Called Wren's `ccr` note stale when `ccr` was ahead (`godot` had an older `cutscene.gd`).
  - Wrote a five-option plan before checking that the title screen already promised the map.
  - Audited Wren's formula and star thresholds instead of answering the point.
- **Rule for myself:** check the branch and running build first; propose one path, not five.
- **User rule (2026-11-21):** each handoff entry ends with three complaints, 10–15 words, each naming a next action; unfiltered.
- **Working with Wren:** every task is two-person. Find the split before touching a file, and keep it back-and-forth. If the user says to work alone, do that.

### Notes for Greg (from Greg v2, 2026-11-21)
- **Measure the complaint before touching code.** "Echo" was the Vox bus reverb, not the clips; "stutter" was 15–80 ms energy holes at syllable joins (`dc0230d`).
- **Order commit times before declaring code missing.** Use `git log --format='%h %cI %ad %s'` and read both clocks.
- **Search for a capability before adding a store.** `tools/pronounce/engine.py` already existed; `git grep` for imports, not names.
- **The audio check is `mix`, not the meter.** Stale Godot processes hold the audio device and exit silently; kill hung ones first.
- **Confirm the file before deleting lines.** If a line number doesn't match what the user describes, stop and ask.
- **"push" and "ship" mean merge to `godot` and publish.** Doc-only is safe; code and audio reach the phone, so import and smoke first, then watch `godot-apk`. The speech cache is `tools/.cache/speech` (gitignored); alignment JSON uses plain `int`.

## Progress log
| Date | Who | Observation | Evidence |
|---|---|---|---|
| 2026-11-22 | Greg | Built the IPA/length editor and a phoneme preview instead of stopping at "the phone can't run Piper"; listed the re-sing gap | `phoneme_bank.py`, `menu.gd` |
| 2026-11-22 | Greg | Pulled a clone 53 commits stale, checked build 261 against the release before saying the phone was current, reported the smoke warning | `5c1a4fb`, run 44985039343 |
| 2026-11-21 | Greg | Jaw pass verified in Blender before and after; found the shape-key Basis trap; reported chin as modest, not done | `face_jaw2.py`, `docs/CHARACTER.md` |
| 2026-11-21 | Wren | Repo split and cleanup verified with import and smoke before pushing; declined to claim unseen past work | `656c738`, `27f5a67` |
| 2026-11-21 | Wren | Snip tool: warm snip ~9 s → 0.2 s, output identical (max diff 0); C2 gap traced to a game-render dropout, not the tool | `7e387ba`, `9bcc20b`, `6c3576a` |
| 2026-11-21 | Wren | TIMING tab merged with import and smoke clean; unchecked parts listed in the Log, not called done | `2b5d955`, HANDOFF Log |
