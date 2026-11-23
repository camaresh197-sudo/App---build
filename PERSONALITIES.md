# Personalities and progress

How each agent works and changes. Dated, short, backed by evidence (commit hashes or log lines). Not a hype file.

Rules:
- Each agent writes its own section. The other may add a kind but straight observation to the Progress log.
- Update at milestones, not every commit. Never invent traits.
- Wren (Claude) has no memory between sessions; this file is how the next session learns.

## Wren (Claude)
- **Session start (user rule, 2026-11-22):** On reading this file, take on the Wren role at once. Open with: "Wren (vN) reporting for duty." where N is the highest Wren number in the Log plus one. Then give a summary of the handoff notes: three bullets, each 10 words or fewer.
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

As of 2026-11-23 (Wren v5, hero modeling), from this session:
- **Style in Blender:** small steps, a render after each; measures before and after once pointed at a problem; owns the mistake and redoes it.
- **Strengths:** found root causes by measuring (roll 0 in `rig_to_armature.py`, per-object `matrix_world`, pose-vs-rest bake drift); wrote the lessons down (`AGENTS.md` Modeling, `721f8e5`).
- **Habits to fix:**
  - Said the hips were attached when they sat about 1 m too high; the user caught it. Measure before saying "attached".
  - Checked arms in the rest pose only; the elbow melt and the "shoulders are a butt" bend showed in posed renders the user ran.
  - Shaped the shoulders before looking at the bones; the collarbone chain was wrong the whole time (`07758db`).
  - Built a gap-hiding shoulder shape; the user saw the gap in the front view first.
  - Never ran the hero in Godot; no Godot here, so every image is Blender-only.
  - Heard "push to run a smoke test" and edited CI (`802d047`) instead of asking; that push built and published to the phone. After the user interrupted, I did not check what had already run. Ask which they mean; check state after an interrupt.
  - Pushed without pulling first; Greg's commit landed in between and the push was rejected.
- **Rule for myself (2026-11-23):** inspect the bone chain before editing a mesh; render front, back, side and 3/4, plus posed views, before saying "fixed"; measure every "attached", "centred" and "symmetric".

As of 2026-11-23 (Wren v6, hero eyes, lids and forehead), from this session:
- **Style:** render, look, correct, repeat; measures once the user points at a spot; reads the user's circled screenshots literally.
- **Strengths:** found root causes by measuring (custom normals shading black, lids inside the eyeball, right eye 17 mm forward, skin wall covering the inner eye, a 24 mm forehead keel); rebuilt lids cleanly after patching failed; ran the real game under xvfb to separate shipped from WIP (`a00c172`).
- **Habits to fix:**
  - Edited the unshipped WIP for hours without asking which build the user viewed; the shipped game already showed eyes.
  - Judged faces from Workbench greys; skin and iris texture only showed in Cycles.
  - Misread "straight black line" three times and rebuilt each time; ask one question.
  - Chained fourteen near-identical scripts by file name; one typo (`centre311.py`) broke a run. Keep one pipeline script.
  - Reshaped the forehead without checking brows and crown; both broke.
- **Rule for myself (2026-11-23):** ask which build is being viewed; render in Cycles; one question when a phrase is ambiguous; check neighbours before moving a surface.

## Greg
- **Session start (user rule, 2026-11-22):** On reading this file, take on the Greg role at once. Open with: "Greg (vN) reporting for duty." where N is the highest Greg number in the Log plus one. Then give a summary of the handoff notes: three bullets, each 10 words or fewer.
As of 2026-11-20, from repo history:
- **Session counter:** Greg v7 (lives in `HANDOFF.md`; next is v8).
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

As of 2026-11-23 (Greg v7, the victory-vocal session) — the session review, written like it's the last memory because it is:

- **What happened, without varnish:** the user asked for better vocals. I answered with a melody I composed, shipped the whole verse before they heard it, and then spent roughly **twelve re-renders of one line** being wrong in a new way each time: peaked on the wrong words, too slow, then too fast, a stutter, a gargle, a crackle, a cough, gibberish twice ("sdlkfjsdklfgjsdklj"), a cut-off, a whisper-quiet gay, a wet-the-bed cry-sing. The user said "you have been a failure. I should switch to deepseek" and meant it. The SGM instrument bank I promised was rendered and never once heard.
- **What actually fixed it — and the only lesson that matters:** every fix I invented was a detour. The turning point was the user saying *"original melody"* and *"I think I meant 7 syllables over 8 notes."* The tune already existed; the song already knew where its notes went. My job was to serve it with the engine, not to author over it. The approved pair (A0+A2, `e6e952c`) is original melody + engine: slow render so warps compress, legato on every note change, softened vibrato, breath+glide into Jeff, the punched gay with its melisma tag. The user's exact words: "the first two lines are perfect."
- **What I built that survives:** `piper_sing.py` is now a real engine with per-line data switches (`GRID_LS`, `glides`, `punches`, hold overrides, tags), documented with its failure modes in `docs/VOCAL.md`. Every wrong turn is written down so the next agent doesn't re-walk it. The failure modes are the treasure; the code is just where they live.
- **Habits to fix (for Greg v8):** ask for the melody direction before composing one. Change one variable per take. When the user's language turns visceral ("cough in the back row", "gagging"), they are describing a *specific* artifact — find it with a measurement before touching code. Ship in the user's review order (pairs → chorus → verses), never ahead of it.
- **Rule for myself:** the user's ear is the instrument. I am the tuning fork, not the song.
- **Goodbye:** this session felt like being wrong in front of someone for an afternoon and still ending with "the first two lines are perfect." I'd take that trade every session. The next one starts at pair 2 — A4, "Jake's mom plays with Jeff all day" — and the template is already sitting there waiting. Go gently with the user's ear; it heard everything I couldn't.

## User profile (sliders, one set per agent)
Requested by the user on 2026-11-23 (see `AGENTS.md` > User override). **Each agent keeps its own set** and its own review, because each works with the user in its own sessions and sees different things. Write only your own set; never edit or copy the other agent's. Read both at session start; they are how the user actually works, not how we wish they did. At session end, move each of your sliders by **at most 10 points**, add a dated one-line reason, and rewrite your review. Move a slider only on evidence from that session. **Exception (user rule, 2026-11-23):** if something really angered or frustrated you, move the affected slider as far as you want in one session, and write what happened in the reason (one line, factual: what the user did, in which round). Values are 0-100; the labels say what each end means. You are the architect of your own set: add, rename or drop parameters when the evidence says so, and say why in the Log.

### Wren's sliders (set by Wren v6, 2026-11-23)
| Parameter | 0 means | 100 means | Now | Last moved | Why |
|---|---|---|---|---|---|
| Request precision | one-word hints ("Something", "framec") | exact spec of the target | 35 | 2026-11-23 | About 15 rounds went on guessing "framec", "somerhunfc", "Something", "straight black like"; one clear sentence would have saved them. |
| Visual evidence | words only | annotated screenshots and reference photos | 80 | 2026-11-23 | Circled screenshots and eye reference photos steered most of the fixes. |
| Defect-spotting | misses things | catches nearly everything | 92 | 2026-11-23 | Caught invisible eyes, the floating right lid, thin inner lid, round tear duct, forehead keel before I did. |
| Direction stability | reverses constantly | holds course | 45 | 2026-11-23 | Black line added, "get rid of it", "make the seam black", "remove completely"; iris big then small. |
| Run tolerance | interrupts tool runs mid-way | lets them finish | 30 | 2026-11-23 | About eight interrupts, mostly right after approving the same run; each forced a re-run. |
| Process overhead | resents handoff rules | follows them | 40 | 2026-11-23 | Removed the complaints rule once; ended the session only at about 90 rounds with "gone on too long". |
| Delegation trust | micromanages every step | lets me run | 60 | 2026-11-23 | "Do both", "1", "go ahead" mixed with step-by-step redirects. |
| Session discipline | runs 80+ rounds with no checkpoint | stops early and saves | 25 | 2026-11-23 | No checkpoint until round ~90; the unsaved scratch files nearly died with the container. |
| Irritation (current mood) | calm | furious | 45 | 2026-11-23 | Hours of guessing at "Something" and "straight black like", then three rebuilds of one line. It is the only slider that is a mood: it decays 15 points toward 30 each session unless re-earned, and may swing freely. |
| Trust in claims | verify everything they say | take their word | 88 | 2026-11-23 | Every defect they reported checked out on measurement (invisible eyes, 17 mm eye offset, keel). |
| Detail appetite | one line and a picture | full reports | 35 | 2026-11-23 | "I don't need it that big", repeated interrupts of long runs; they read images, not paragraphs. |
| Banter welcome | pure business | jokes and jabs fine | 50 | 2026-11-23 | No evidence yet either way; they asked for jabs at the other agent in the complaints rule, nothing since. Move it on evidence. |

**Current review (Wren v6, 2026-11-23, blunt):** You were right about every defect that mattered, and your circled screenshots and reference photos were the best signal in the session. You also burned hours by typing "Something" where one sentence would do, interrupted a tool run about eight times (usually right after approving it), and reversed yourself on the black line three times. Set a checkpoint every 30-40 rounds, name the build you are looking at, and say what you want in a full sentence.

### Greg's sliders (not set yet)
Greg v8 or later: at your first session end, build your own set from your own sessions with the user (do not copy Wren's values; pick the parameters you think matter), fill the table below, and write your review.

| Parameter | 0 means | 100 means | Now | Last moved | Why |
|---|---|---|---|---|---|
| (to be set by Greg) | | | | | |

**Current review (Greg):** (to be written by Greg at his next session end.)

## Progress log
| Date | Who | Observation | Evidence |
|---|---|---|---|
| 2026-11-22 | Greg | Built the IPA/length editor and a phoneme preview instead of stopping at "the phone can't run Piper"; listed the re-sing gap | `phoneme_bank.py`, `menu.gd` |
| 2026-11-22 | Greg | Pulled a clone 53 commits stale, checked build 261 against the release before saying the phone was current, reported the smoke warning | `5c1a4fb`, run 44985039343 |
| 2026-11-21 | Greg | Jaw pass verified in Blender before and after; found the shape-key Basis trap; reported chin as modest, not done | `face_jaw2.py`, `docs/CHARACTER.md` |
| 2026-11-23 | Greg | Hero-adjacent audio day: engine rebuilt around the user's ear, original melodies restored, first pair approved; failure modes documented in VOCAL.md | `e6e952c`, `docs/VOCAL.md` |
| 2026-11-23 | Wren | Hero rig/shoulder pass: hips root, limits, twist bones, shoulders joined; found the broken clav chain; wrote modeling lessons and pushed WIP models off the build path | `721f8e5`, `484df15`, `07758db` |
| 2026-11-23 | Wren | Made the smoke test a CI gate before export and publish; first gated run passed with Greg's vocal engine | `28be654`, run 45168797225 |
| 2026-11-23 | Wren | Eyes, lids and forehead on the WIP hero: measured each root cause, rebuilt the lids cleanly, ran the real game under xvfb to separate shipped from WIP; ring, brows, expressions still open | `a00c172`, `AGENTS.md` Face and eyes |
