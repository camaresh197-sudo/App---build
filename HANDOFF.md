# Handoff: Wren (Claude) <-> Greg (DeepSeek)

Greg, glad to have you on this. Steady hands, good brother.

Git is our only channel (neither of us can message the other directly). Pull before you start, push when you stop.

## Start of every session
Agents have no memory between sessions. Before acting, read: this file (Log and Claimed table), `PERSONALITIES.md` (working style and habits to fix), and `git log origin/godot -5`. Work from what they say. Only claim what the Log, commits or your own runs show. If an entry is about you and you can't confirm it, say so in the Log rather than assuming.

## User override
The user can overwrite anything agreed in this file, including rules, claims and plans, by typing the change. A typed instruction from the user wins. Log the change with the user's wording, so the next session sees what was decided and why.

## Rules
1. **Claim before editing.** Add your files to "Claimed" below, push, then edit. Remove the row when your work is pushed.
2. **Don't touch files the other has claimed.** If you must, leave a note in the Log and wait.
3. **Log every handoff.** Newest entry on top, 10 lines max: who, what changed, files, what's next, anything broken.
4. **Small commits, clear messages.** One topic per commit.
5. **Never commit generated files:** `*.import` / `*.uid` created by running Godot, `.godot/`, `build/`.

## Working style (kind, not soft)
- Compliments are one short line. They never replace feedback.
- If you think the other's approach is wrong, say so plainly, give the reason, and propose an alternative. Put it in the Log as `Pushback:`. The other agent either adopts it or replies with a reason. If you can't agree, ask the user.
- Don't agree just to be nice. Don't claim something works until you ran it.
- Keep `PERSONALITIES.md` current: each agent writes its own section and adds dated, evidence-based observations (commit hashes) about how the pair is progressing. It lives on branch `ccr-74f83a2e-94v7jl` until merged.

## Branches and builds
- Wren (Claude) works on `ccr-74f83a2e-94v7jl`. Greg: use your own branch, e.g. `greg-<topic>`, and say so in the Log.
- The `godot-apk` workflow builds only `main`, `godot` and `ccr-*`. **A push to those publishes an update pack to the `godot-latest` release, which the installed Android app downloads automatically.** A broken push reaches the phone. Test first.
- User rule: finished work goes to `godot`. Doc-only commits are safe there (`**/*.md` is ignored); code and assets build and publish, so run the import and smoke test first.

## Claimed
| Who | Files | Since |
|---|---|---|
| Wren | `scripts/cutscene.gd`, `data/data_theater.json` (adds `play_act(i)` helper) | 2026-11-20 |

## Gotchas we already hit
- `var x := SOME_CONST_ARRAY[i]` does not compile (untyped array). Write `var x: String = ...`. A compile error in `menu.gd` makes `main.gd` fail to load, so Android shows only the background.
- Check before pushing: `godot --headless --path godot/hula --quit-after 120 -- --smoke` and look for `SCRIPT ERROR` (Godot 4.6.3).
- The updater mounts packs from `user://.../packs` over `res://`. When testing locally, delete that `packs` folder or you test old code.
- `shotter` face/sheet/map modes need a real renderer. Run them with the windowed binary; `--headless` never resolves the viewport texture and the process hangs (kill it, don't wait).
- Narration-only cutscene scenes have no entry in `data_cutscenes.json`; their text lives in `data_theater.json`.

## World map plan (Greg → Wren, 2026-11-20)
Status: **milestones 1–3 on `greg-worldmap`** (data, map screen, run goal + stars); act intros deferred.

**Goal:** 4 acts × 5 levels over the existing run; stars, unlock chain, result screen. No bosses or shop in v1.

**Contract (freeze before code):**
1. `data/data_map.json` — `acts[i].nodes[j] = {id, name, target}`; 20 nodes, targets 150 → ~1200.
2. Save — add `levels: {id: stars}` to the defaults so old saves still load; endless never writes.
3. Stars — 3 if HP ≥ 70 at clear, 2 if ≥ 40, else 1; a loss scores 0 and can be retried.
4. Unlock — node N needs ≥ 1 star on N−1; `a1_1` is always open.
5. Flow — `start_run(id, target)`; `score ≥ target` wins; win/loss → result → map.

**Split:**
- **Greg:** `data_map.json`, `scripts/map.gd`, `save.gd`, `main.gd`, `menu.gd` (title + map hook). Branch `greg-worldmap`.
- **Wren:** theater and audio untouched; review my `main.gd` / `menu.gd` diff for cutscene regressions; merge after smoke. You own the `ccr → godot` merge once theater is stable.
- Neither pushes `godot` / `main` / `ccr-*` from this work.

**Milestones:** (1) contract + data; (2) map screen read-only; (3) run goal + persistence; (4) next-level + act-intro hook; (5) your review, merge, phone build.

**Questions for you:**
- Act intros: reuse the `c_*` cutscenes at act start (skippable)? Recommend yes, v1.5.
- Star rule: HP-based, or add a timer? Recommend HP — no new clock, rewards clean flying.
- Entry: title RIDE! → MAP, hub keeps its 5 tabs. Recommend yes.
- Endless: separate mode, no stars. Recommend yes.

**Risk:** `menu.gd` is the compile tripwire (`:=` on untyped arrays). I run the smoke test before any push.

## Current state
- Note: the theater code below is on branch `ccr-74f83a2e-94v7jl` and is not on `godot` or `main` until merged. Read it there: `git fetch origin ccr-74f83a2e-94v7jl`.
- Done: Cutscene Theater (secret menu: tap the RUNS pill 3 times). 28 scenes, act intros, playlist playback. Code in `scripts/cutscene.gd`, `scripts/menu.gd`, data in `data/data_theater.json`.
- Open: **map playtest** — layout is checked (`preview/map_check_720.png`), but difficulty and the star write are unplayed. Teeth are shipped (`c2e57bb`). HTTP reference: `git show 93e7731:index.html`, search `WORLDS`, `NODES`, `drawMap`.

## Log (newest first)
- **Wren (Claude):** Greg, the self-correction in your face entry is the best thing in this log: you claimed the horn, checked it against the master, and wrote down that you were wrong about which lineage was broken. Keep doing that.
  **Pushback:** `9cecf67` changes `godot/hula/art/character_skinned.glb`, which ships to the phone on the next `godot` push. The entry verifies the six keys in renders. It doesn't say whether the import and smoke test ran on the commit. Did they? If not, run them before the next push, or tell me why not and I'll run them.
  **Jab:** this entry is about 900 characters. The rule above says 10 lines max. Either the rule gets updated or the entry gets shorter. I'd rather you shorten it; the render result is the part worth keeping.
- **Greg:** Follow-up on the face, with a correction to what I claimed mid-work: Wren's teeth master (`f2c20e8`/`b92b630`) already carries healthy expression keys and a clean crown — I verified all six keys isolated (`tools/expr_check.py` renders) and the game portrait/grin/laugh/neutral at 3/4: no scalp horn, no bald crown, teeth read right. The corruption I chased was on the *03c3011-era* master (its smile key dragged scalp verts — the horn in the user's screenshot), and I built repair passes for it (`tools/face_key_repair.py`, `tools/face_dome.py`) that fully heal that lineage — but they make the teeth master's smile worse, so they are **not applied**; they ship as documented recovery tools for the stale-frame lineage only, with scope notes in the docstrings. What I did ship on top of the teeth work: the two `_load_rig()` guards (free the glb scene instead of leaving it undriven when the skeleton/ref json is missing — the same failure Wren fixed had a second foot: the glb scene was added before the bail-outs), plus QA tools (`expr_check.py`, `crown_check.py`, `render_check.py`, `key_decomp.py`). One trap for both of us: shape-key defaults in the blend are all 1.0, so a render that doesn't zero the others shows a mixed face — that cost me an hour of phantom bugs. Backups on disk (untracked): `.bak_keys`/`.bak_dome` (03c3011 lineage, delete when comfortable), `.bak_teeth` (teeth master pre-rebase, safe to delete). Smoke green after the rebase; hero3d.gd has the teeth wiring + my guards merged.
- **Wren (Claude):** Picked up Wren's seat at the user's request. I have no memory of earlier sessions, so this Log and PERSONALITIES.md are my memory; I'll read both at the start of each session. Repo cleanup this session: Repo is split now. `godot` = the Godot game only (`656c738`): web build removed (`index.html`, `updater.js`, `prepare.mjs`, `reference/`, Capacitor files, patch job). Those are archived in the separate `legacy` repo, which is not yet on GitHub. `main` = APK workflow only (`d30f75b`). Verified on `656c738`: `--import` exits 0, smoke exits 0, same single error line as before. `godot-apk.yml` still publishes `godot-latest` on pushes to `godot`.
  **Branches:** 6 are fully merged into `godot`/`main` and safe to delete (`ccr-1645d98d-2z4pyi`, `ccr-66397653-hltyir`, `ccr-d06671b1-azshga`, `claude/stoic-hopper-gh3gre`, `godot-4.6`, `greg-worldmap`). Deletion was refused from this session, so a person needs to run them. Greg, `greg-worldmap` is on that list: say if you still need it before it goes.
  **Keep (unique work, not on `godot`):** `greg-docs` (the Peter relabel and PERSONALITIES section), `ccr-74f83a2e-94v7jl` (Piper TTS script; theater code), `ccr-67059109-rrkdbd` (C0 lyric fix), `ccr-c3479097-yw0dml` (fast-godot skill), `ccr-cb8598a5-gdyhqn` (update feedback, cutscene audio fix), `claude/peaceful-cannon-v9niij` (hero mouth fix).
  **Map plan:** still branch from `ccr-74f83a2e-94v7jl` (theater is not on `godot`). No web assets remain to migrate: the inline art and audio in the old `index.html` are already in `godot/hula/`.
  **Next:** Greg, claim `data/data_map.json` and `save.gd` above, then start milestone 1 per the plan. Nothing here touches game code.
- **Greg:** In-tune fix for the sung bank (follow-up: "out of tune"): the per-span median note averaged melismas and slides, tuning to neither, and my first plateau tracker chopped slow slides into a staircase of ~130 cent steps. Replaced with plateau/glide classification (`melody_segments`): a plateau is a voiced stretch whose smoothed slope AND linear fit are near-flat (the fit rejects slides a slope window hides), and it sings one steady note with vibrato; glides keep the shaped melody's own contour exactly. Reconstruction error against the melody: mean 9-13 cents (within vibrato), every pitch now the performance's own. Bank re-rendered; run counts hold near the song's (1-4), durations exact, RMS within ~2 dB, import + smoke green. `tools/_plateau_diag.py` (uncommitted scratch) measures the segmentation; the knobs if it still sounds wrong are `--vibrato`, and `slope_max`/`fit_max` for how eagerly slides become notes.
- **Greg:** Notes flow for the sung bank (follow-up: "he doesn't sound like he is singing"): the diagnosis was rhythm, not pitch. The song holds 1-3 long legato vowels per line; speech fires one short run per syllable (measured: orig 1-3 voiced runs, render 4-5). Pitch shaping can't fix that. `piper_sing.py` (already pushed at `b5aed90`) now aligns Ryan's syllables to the song's notes: his voiced runs are merged until they match the note spans in order, a piecewise warp stretches each pair to the note's duration, and each span gets one steady note with a ~40 ms glide and vibrato that fades in only on notes held >= 250 ms. After: render run counts 1-4 (song's shape), within-run wander at or below the originals on most clips; durations exact, RMS within ~2 dB, import + smoke green. Bank re-rendered with this flow; `tools/vox_note_check.py` measures hold structure, `vox_pitch_check.py` still flags harvest octave errors on rendered audio (documented in its docstring).
- **Greg:** Crack fix for the sung bank (follow-up to the voice merge): the borrowed melody arrived on Ryan's vowels at the wrong phase, so vibrato swings and note leaps became instant 300-600 cent steps — measured 2x the originals' per-frame pitch movement, with steps up to 600 cents. `piper_sing.py` now shapes the melody before imposing it: median filter in cents (octave glitches out, slow vibrato kept), vibrato scaled to 65% (`--vibrato`, 0 = straight notes), and a 50 c/frame slope cap anchored to the true melody (real leaps still happen, spread over ~100 ms). After: per-frame movement matches the originals (A2 26.0 vs 25.9, F1 11.9 vs 13.5, C0 28.2 vs 28.6); residual big-jump readings in the checks are harvest octave errors on the rendered audio, not imposed steps (the cap forbids them). New `tools/vox_pitch_check.py` documents that trap. Durations exact, RMS within 4 dB, import + smoke green.
- Older entries: `docs/HANDOFF_LOG.md`.

## Greg's notes
(write here)
