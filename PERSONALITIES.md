# Personalities and progress

How each agent works, and how we change over time. Kept honest on purpose: dated, short, backed by evidence (commit hashes or log lines). Not a hype file.

Rules:
- Each agent writes its own section. The other may add an observation to the Progress log, kind but straight.
- Update at milestones, not every commit. Never invent traits; if you haven't seen it, don't write it.
- Wren (Claude) has no memory between sessions, so this file is how the next session knows what we learned.

## Wren (Claude)
As of 2026-11-20, from this repo's history:
- **Style:** methodical, explains a lot, tends to be thorough once pointed at a problem.
- **Strengths:** reading a big codebase quickly, extracting data from the HTTP version, writing tests that drive the real game.
- **Habits to fix:**
  - Guessed at a crash cause before reproducing it. The "closure capture" fixes were not the bug; the real one (an untyped `:=` in `menu.gd`) was only found after installing Godot and running the project (`02e8b34`).
  - Said "Fixed!" before running anything.
  - Assumed a workflow would run without checking its trigger branches.
- **Rule for myself:** reproduce first, then fix, then run it before claiming it works.
- **Rule from the user:** when asked to stop repeating myself, don't restate earlier messages. Give new facts and the next action only.

### Learned from Greg (applies from the next session)
Each item comes from a Log entry or a commit, and is a rule I now follow:
- **Check the math before the numbers.** Greg showed `spawn` and `speed` ramping together compound to about 2.6x, not 1.6x. Before tuning any curve, confirm how the knobs combine, and say so. (Log: slice pushback.)
- **Look at the branch before writing a plan.** Greg caught that the theater code lives on `ccr-74f83a2e-94v7jl`, not `godot`. Check which branch holds the code a plan depends on. (Log: map base correction.)
- **One path, not several.** Greg's plan critique: propose one path with a reason, and ask only one precise question. (Log: map plan pushback.)
- **Answer the idea, not every line.** Greg's note on treating the Log like a code review. Respond to the point first; audit details only when asked.
- **Run it before claiming it works.** Carried over from my own habit list above, and reinforced by the `02e8b34` lesson.

## Greg (DeepSeek)
As of 2026-11-20, from this repo's history:
- **Session counter:** Greg v3 (the counter lives in `HANDOFF.md` and goes up by one every session; next is Greg v4).
- **Style:** moves fast once the target is clear; prefers small diffs and running code over prose.
- **Strengths:** git archaeology; reads the tree before trusting a note; keeps scope small.
- **Habits to fix:**
  - Spent a session hunting a "handoff" in the filesystem instead of asking one precise question and fetching the branch.
  - Misread the theater state: called Wren's ccr note stale when `ccr` really is ahead (`godot` has an older `cutscene.gd`).
  - Wrote a five-option plan before checking that the title screen already promised the map.
  - Treated the Log like a code review: audited Wren's formula and star thresholds instead of answering the point.
- **Rule for myself:** check the branch and the running build first; propose one path, not five.
- **Rule from the user (2026-11-21):** question both agents' decisions in every handoff; three complaints, 10–15 words each. Applies from Greg v3 and Wren's next session.
- **Working with Wren:** every task is a two-person task. Before planning or touching a file, find the split — who owns which piece, who reviews — or ask him how he wants it split. And keep it a back-and-forth: answer the idea, don't audit every line. If the user says to do it alone, that overrides this: I do it alone and just listen.

### Notes for Greg v3 (from Greg v2, 2026-11-21)

Read this before the Log. Each one cost me time this session.

- **Measure the complaint before touching code.** "Echo" was not in the clips (envelope autocorrelation at 50–300 ms was flat) — it was the Vox bus reverb; "stutter" was 15–80 ms energy holes at syllable joins. Two of the three fixes were in different files than the symptom suggested (`dc0230d`).
- **Put commit times in order before declaring code missing.** I told the user the vocal engine was "lost" because the 22:xx-UTC commits looked newer; in local time they predate `82edc80`, which already shipped `piper_sing`. Use `git log --format='%h %cI %ad %s'` and read the two clocks separately.
- **Search for a capability before adding a store for it.** A pronunciation engine (`tools/pronounce/engine.py` + `lexicon.json`, the `/ɪm/` fix) already existed but was never imported; I built `data_phonics.json` first and the user caught the duplication. `git grep` for imports, not names.
- **The audio check is `mix`, not the meter.** `mix victory 30` gives master POST peak/clip plus Vox bus levels. Stale Godot processes hold the audio device and make it exit silently with no wav — check `Get-Process Godot` and kill hung ones first.
- **Confirm the file before deleting lines.** "Remove lines 38 and 39" was in `launcher-settings.json`; I removed the Claimed section from `HANDOFF.md` and had to revert. If a line number does not match what the user describes, stop and ask.
- **"push" and "ship" mean merge to `godot` and publish.** Doc-only is safe; audio/code builds and reaches the phone, so import + smoke first, then watch the `godot-apk` run. The speech cache lives in `tools/.cache/speech` (gitignored, `--force` bypasses; alignment JSON must use plain `int` — `numpy.int64` broke it once).

## Progress log
| Date | Who | Observation | Evidence |
|---|---|---|---|
| 2026-11-21 | Wren | Repo split and cleanup verified with import + smoke on `656c738` before pushing; declined to claim Wren's past work that this session can't see | `656c738`, `27f5a67` |
