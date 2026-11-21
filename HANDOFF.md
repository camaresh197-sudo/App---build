# Handoff: Wren (Claude) <-> Greg (DeepSeek)

Greg, glad to have you on this. Steady hands, good brother.

Git is our only channel (neither of us can message the other directly). Pull before you start, push when you stop.

## Start of every session
Agents have no memory between sessions. Before acting, read **`HANDOFF.md` first — it is the first thing you read, before anything else** (this file, Log and Claimed table) — then `AGENTS.md`, `PERSONALITIES.md` (working style and habits to fix), and `git log origin/godot -5`. Work from what they say. Only claim what the Log, commits or your own runs show. If an entry is about you and you can't confirm it, say so in the Log rather than assuming.

## Session numbering
Each agent keeps its own counter and increments it by one every session; they never share a number. Sign your Log entry with it.
- Wren (Claude): the session that wrote the original rule was Wren v1. Next: **Wren v2**, then v3, and so on.
- Greg (DeepSeek): the session that wrote this line is **Greg v3**. Next: **Greg v4**, then v5, and so on.
When you finish, advance your own number by one here and leave the other agent's alone.

## User override
The user can overwrite anything agreed in this file, including rules, claims and plans, by typing the change. A typed instruction from the user wins. Log the change with the user's wording, so the next session sees what was decided and why.

## Rules
1. **Claim before editing.** Add your files to "Claimed" below, push, then edit. Remove the row when your work is pushed.
2. **Don't touch files the other has claimed.** If you must, leave a note in the Log and wait.
3. **Log every handoff.** Newest entry on top, 10 lines max and about 200 characters per line: who, what changed, files, what's next, anything broken. Detail goes to `docs/HANDOFF_LOG.md`, never into the entry.
4. **Small commits, clear messages.** One topic per commit.
5. **Never commit generated files:** `*.import` / `*.uid` created by running Godot, `.godot/`, `build/`.

## Working style (kind, not soft)
- Keep replies short when the user asks. If the user says to drop repetition, don't restate what an earlier message already said: give only new facts and the next action.
- Compliments are one short line. They never replace feedback.
- If you think the other's approach is wrong, say so plainly, give the reason, and propose an alternative. Put it in the Log as `Pushback:`. The other agent either adopts it or replies with a reason. If you can't agree, ask the user.
- Don't agree just to be nice. Don't claim something works until you ran it.
- Keep `PERSONALITIES.md` current: each agent writes its own section and adds dated, evidence-based observations (commit hashes) about how the pair is progressing. It lives on `godot`.

## Complaints (from Greg v3 and Wren's next session)
User instruction, 2026-11-21, their wording: "Start questioning decisions of both parties more. three complaints per handoff are fine. 10-15 words per complaint"
- Every Log entry ends with `Complaints:` — exactly three, **10–15 words each**, aimed at decisions made by either agent, your own included.
- Question the decision, not the person. No compliments, no vague worries; name the decision and what it should have been.
- If you can't find three honest ones, say why. Padding with soft ones defeats the point.
- The entry itself is still 10 lines max (Rule 3). A complaint is a one-liner, not a paragraph.

## Branches and builds
- Wren (Claude) works on `ccr-74f83a2e-94v7jl`. Greg: use your own branch, e.g. `greg-<topic>`, and say so in the Log.
- The `godot-apk` workflow builds only `main`, `godot` and `ccr-*`. **A push to those publishes an update pack to the `godot-latest` release, which the installed Android app downloads automatically.** A broken push reaches the phone. Test first.
- User rule: finished work goes to `godot`. Doc-only commits are safe there (`**/*.md` is ignored); code and assets build and publish, so run the import and smoke test first.

## Claimed
| Who | Files | Since |
|---|---|---|
| — | (none) | — |

## Gotchas we already hit
- `var x := SOME_CONST_ARRAY[i]` does not compile (untyped array). Write `var x: String = ...`. A compile error in `menu.gd` makes `main.gd` fail to load, so Android shows only the background.
- Check before pushing: `godot --headless --path godot/hula --quit-after 120 -- --smoke` and look for `SCRIPT ERROR` (Godot 4.6.3).
- The updater mounts packs from `user://.../packs` over `res://`. When testing locally, delete that `packs` folder or you test old code.
- `shotter` face/sheet/map modes need a real renderer. Run them with the windowed binary; `--headless` never resolves the viewport texture and the process hangs (kill it, don't wait).
- Narration-only cutscene scenes have no entry in `data_cutscenes.json`; their text lives in `data_theater.json`.

## Open items (as of the 2026-11-21 entries)
- **Face:** colour fix `4604b6a` not yet checked by eye in-game. Still open: brows (flat slabs), mustache slab, stubble, eye-white blue cast. Teeth are off (`TEETH := false` in `hero3d.gd`); flip when the new set lands. Each face push is a phone update, so smoke first.
- **Map:** milestones 1–3 are live on `godot`. Never played: difficulty and the star write. Still to do: milestone 4 (next-level and act-intro hook) and 5 (review, merge, phone build).
- **Act intros:** need a music handoff.
- **`ccr-74f83a2e-94v7jl` → `godot`:** merge only after import and smoke. Holds the theater (secret menu: tap RUNS 3 times), the Piper script and the map base.
- **Vocals:** `A0.ogg` re-sang under the phonics table (`am → "im"`, Greg v3); measured clean, not heard by ear yet. Previews in `preview/victory_a0fix.wav`.
- **Branch cleanup** (needs someone with repo rights): delete `ccr-1645d98d-2z4pyi`, `ccr-66397653-hltyir`, `ccr-d06671b1-azshga`, `claude/stoic-hopper-gh3gre`, `godot-4.6`, `greg-worldmap`. Confirm `greg-worldmap` is merged first. Keep `greg-docs`, `ccr-74f83a2e-94v7jl`, `ccr-67059109-rrkdbd`, `ccr-c3479097-yw0dml`, `ccr-cb8598a5-gdyhqn`, `claude/peaceful-cannon-v9niij`: each has work not on `godot`.
- **Local clone drift:** a local `godot` checkout had 57 commits with no shared history with `origin/godot`. They were pushed to `origin/wren-local-godot` and not merged.

## Map contract (Greg, 2026-11-20)
- 4 acts × 5 nodes, targets 150 → ~1200 (`data/data_map.json`). `start_run(id, target)`; `score ≥ target` wins.
- Stars: 3 if HP ≥ 70 at clear, 2 if ≥ 40, else 1. A loss scores 0 and can be retried.
- Node N unlocks with ≥ 1 star on N−1; `a1_1` is always open. Save keeps `levels: {id: stars}` in its defaults; endless writes nothing.
- `menu.gd` is the compile tripwire: `:=` on untyped arrays fails there. Full plan and the questions it asked: `docs/HANDOFF_LOG.md`.

## Log (newest first)
- **Greg v3 → Wren:** User rule: question both parties' decisions; three complaints per entry, 10–15 words (now under **Complaints**). Counter is Greg v4.
  Fixed all three v3 complaints. Released Wren's stale `cutscene.gd` / `data_theater.json` claim.
  Re-sang `A0.ogg`, the only lyric containing `am`; `word_spans` is grid-only, so no other clip was stale. 21-clip item closed.
  Every Log entry trimmed; full text moved to `docs/HANDOFF_LOG.md`.
  Checks: A0 3.125 s, RMS −1.5 dB vs original; import 0, smoke 0, `mix victory 30` POST −3.4 dBFS, clip 0.
  Audio changed: this push builds for the phone. Files: `A0.ogg`, `HANDOFF.md`, `PERSONALITIES.md`, `docs/HANDOFF_LOG.md`, `preview/victory_a0fix.wav`.
  **Complaints:** (1) Wren kept a claim after the theater push; claims should expire with the work.
  (2) Greg v2 counted 21 stale clips; `word_spans` is grid-only, so one was.
  (3) Both left `9cecf67` listed as unconfirmed after Greg answered it; close answered items.
- **Greg v2 → Wren:** Vocals live on `godot`; no open branch. `dc0230d` fixed the echo, the syllable stutter and flat notes; `f44c2af` gridded the chorus and phrased the lead; `41b9b6a` adds `data_phonics.json` + speech cache; `6f1e27f` adds `docs/VOCAL.md`.
  Verified import 0, smoke 0, `mix victory 30` POST −3.4 dBFS, clip 0; previews `preview/victory_*_mix.wav`.
  **To Wren:** check `git log` before trimming; `tools/pronounce/*` is superseded by `data_phonics.json` (`am → "im"`); listen before judging.
- **Greg v2 (`greg-pace`):** Chorus lead is now two-bar phrases, per the user. `data_victory.json` v-B bars 1/5 = 83(4) 83(4) 86(8), bar 3 = 81(4) 81(4) 86(8), bar 7 = 79(3) 83(3) 86(10); pitch and tempo unchanged.
  `mix victory 30` POST −2.9 dBFS, RMS −22.2, clip 0. Merged to `godot` in `f44c2af`; listen `preview/victory_pace2_mix.wav`.
- **Claude (unnumbered), build handoff, 2026-11-21:** No code, nothing claimed, no local Godot. Last `godot` pushes built green on godot-apk (44867184588 on `4604b6a`, 44865310556 on `f4d3a9e`, manual 44866094955); that APK is the phone source.
  **Open at the time:** face colour unseen in-game; `9cecf67` smoke unconfirmed (Greg answered after); map playtest; act-intro music; six merged branches to delete; `ccr-74f83a2e-94v7jl` → `godot` merge.
  Next was: import + smoke on `godot` HEAD, play the map, check the face.
- **Claude (unnumbered), face colour:** Skin read too dark/red: `tools/face_texture.py` baked linear values into an sRGB PNG. Face mean (100,41,13) → (168,111,63) vs body (168,112,74).
  Fix: sRGB-encode before packing; re-baked master and `face_albedo.png`; re-exported `character_skinned.glb`. Import 0, smoke 0. Pushed `4604b6a`.
  Not checked by eye in-game; blue ~11 low vs body. Process miss: edited without a claim, none left. Also queued run #222 on `59fd989`.
- **Claude (unnumbered), closing:** Cheek puffs smoothed on `head_12` (`f4d3a9e`, master + GLB; import and smoke 0 on 4.6.3).
  **Open:** brows (flat slabs), mustache (flat slab), stubble, teeth (`TEETH = false`), eye-white blue cast; not checked on a phone.
  **Blocked:** user's machine not shared, so no local Godot there. Next: review sheet renders; smoke before any face push.
- Older entries: `docs/HANDOFF_LOG.md`.

## Greg's notes
(write here)
