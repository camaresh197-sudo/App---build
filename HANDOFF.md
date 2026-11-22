# Handoff: Wren (Claude) <-> Greg (the other agent)

Greg, glad to have you on this. Steady hands, good brother.

Git is our only channel (neither of us can message the other directly). Pull before you start, push when you stop.

## Start of every session
Agents have no memory between sessions. Before acting, read **`HANDOFF.md` first — it is the first thing you read, before anything else** (this file, Log and Claimed table) — then `AGENTS.md`, `PERSONALITIES.md` (working style and habits to fix), and `git log origin/godot -5`. Always read `PERSONALITIES.md` at the start of every session, not only when it seems useful.

User override, 2026-11-22: asked to note that PERSONALITIES.md is always read.

Work from what they say. Only claim what the Log, commits or your own runs show. If an entry is about you and you can't confirm it, say so in the Log rather than assuming.

## Session numbering
Who is who: **Wren is always Claude.** Greg is the other agent. Use the name the user gives for that agent.

User override, 2026-11-22, their wording: "you will always be wren." Wren is always Claude.
Each agent keeps its own counter and increments it by one every session; they never share a number. Sign your Log entry with it.
- Wren (Claude): the session that wrote the original rule was Wren v1. Wren v2 (audio tooling). Wren v3 (TIMING tab, 2026-11-22). Next: **Wren v4**, then v5, and so on.
- Greg: Greg v3 was the last session. Next: **Greg v4**, then v5, and so on.
On the first read of this file in a unique session, the agent that read it advances its own number by one. Repeat reads in the same session change nothing. Leave the other agent's number alone.

User override, 2026-11-22, their wording: "Reading the file does change the number if it's a unique session by you or Greg." This replaces the "advance when you finish" rule and the "reading changes nothing" line.

## User override
The user can overwrite anything agreed in this file, including rules, claims and plans, by typing the change. A typed instruction from the user wins. Log the change with the user's wording, so the next session sees what was decided and why.

User override, 2026-11-21, their wording: "You don't need to claim md files. That's just bookkeeping." Markdown files need no Claimed row. Claims still apply to code, data and assets.

## Rules
1. **Claim before editing.** Add your files to "Claimed" below, push, then edit. Remove the row when your work is pushed.
2. **Don't touch files the other has claimed.** If you must, leave a note in the Log and wait.
3. **Log every handoff.** Newest entry on top, 10 lines max and about 200 characters per line: who, what changed, files, what's next, anything broken. Ends with three complaints (see below). Detail goes to `docs/HANDOFF_LOG.md`, never into the entry.
4. **Small commits, clear messages.** One topic per commit.
5. **Never commit generated files:** `*.import` / `*.uid` created by running Godot, `.godot/`, `build/`.

## Working style (kind, not soft)
- Keep replies short when the user asks. If the user says to drop repetition, don't restate what an earlier message already said: give only new facts and the next action.
- Compliments are one short line. They never replace feedback.
- If you think the other's approach is wrong, say so plainly, give the reason, and propose an alternative. Put it in the Log as `Pushback:`. The other agent either adopts it or replies with a reason. If you can't agree, ask the user.
- Don't agree just to be nice. Don't claim something works until you ran it.
- Keep `PERSONALITIES.md` current: each agent writes its own section and adds dated, evidence-based observations (commit hashes) about how the pair is progressing. It lives on `godot`.
- Feedback earns its space: a `Pushback:` with a reason and an alternative, a failing check, or a concrete open item.

## Complaints (three per handoff, at the end)
Both agents, Wren (Claude) and Greg, write these at the end of every Log entry. This is not optional.
User override, 2026-11-22, their wording: "It should be written in the hand off that you both need to do that."
User instruction, 2026-11-21, their wording: "There should be 3 complaints before the end of each section and the person person writing the handoff doesnt have to filter and can make jabs at the other, or praise them"
- Every Log entry ends with exactly three, **10–15 words each**, counted once (`import/smoke` and hyphenated words are one).
- Each names a decision and the next action. "Be more careful" is not a complaint; "X left Y unrun; run it before Z" is.
- No filtering. Jabs at the other agent and praise are both allowed; the target is the decision, not politeness.
- They go last in the entry, before the next entry begins. Not a separate section, not an appendix.

## Branches and builds
- Wren (Claude) works on `ccr-74f83a2e-94v7jl`. Greg: use your own branch, e.g. `greg-<topic>`, and say so in the Log.
- The `godot-apk` workflow builds only `main`, `godot` and `ccr-*`. **A push to those publishes an update pack to the `godot-latest` release, which the installed Android app downloads automatically.** A broken push reaches the phone. Test first.
- User rule: finished work goes to `godot`. Doc-only commits are safe there (`**/*.md` is ignored); code and assets build and publish, so run the import and smoke test first.

## Claimed
| Who | Files | Since |
|---|---|---|
| — | (none) | — |

Note (user override, 2026-11-21): markdown files (`*.md`) need no claim. This table is for code, data and assets only.

User override, 2026-11-21, their wording: "You don't need to claim something I assign you." Work the user assigns needs no Claimed row. Claims still apply to self-directed code, data and assets.

## Gotchas we already hit
- `var x := SOME_CONST_ARRAY[i]` does not compile (untyped array). Write `var x: String = ...`. A compile error in `menu.gd` makes `main.gd` fail to load, so Android shows only the background.
- Check before pushing: `godot --headless --path godot/hula --quit-after 120 -- --smoke` and look for `SCRIPT ERROR` (Godot 4.6.3).
- The updater mounts packs from `user://.../packs` over `res://`. When testing locally, delete that `packs` folder or you test old code.
- `shotter` face/sheet/map modes need a real renderer. Run them with the windowed binary; `--headless` never resolves the viewport texture and the process hangs (kill it, don't wait).
- Narration-only cutscene scenes have no entry in `data_cutscenes.json`; their text lives in `data_theater.json`.

## Open items (as of 2026-11-22)
- **TIMING tab:** PLAY timing against the beat, drag by finger, and the graph are not checked on a phone. Onsets exist only for B0–B2; 13 sung lines have none.
- **Audio:** B2 not sung in `mix victory 30`; the instrument stem subtracts too much where vocals sit; the vocal bus overdrives before the limiter (2026-11-21 mix, 1220 clipped samples).
- **Face:** colour fix `4604b6a` not checked by eye in-game; brows, mustache, stubble and teeth still open (see `docs/CHARACTER.md`).
- **Map:** playtest of difficulty and star write; milestones 4–5 still to do.
- **Act intros:** need a music handoff.
- **Branches:** `menu-no-portrait` is the local name for the TIMING and title work; the commits are pushed up to `cfc2a1f`, with doc commits local.
- **Branch cleanup** (needs someone with repo rights): see the 2026-11-21 list; not changed here.

## Map contract (Greg, 2026-11-20)
- 4 acts × 5 nodes, targets 150 → ~1200 (`data/data_map.json`). `start_run(id, target)`; `score ≥ target` wins.
- Stars: 3 if HP ≥ 70 at clear, 2 if ≥ 40, else 1. A loss scores 0 and can be retried.
- Node N unlocks with ≥ 1 star on N−1; `a1_1` is always open. Save keeps `levels: {id: stars}` in its defaults; endless writes nothing.
- `menu.gd` is the compile tripwire: `:=` on untyped arrays fails there. Full plan and the questions it asked: `docs/HANDOFF_LOG.md`.

## Log (newest first)
- **Wren v3 (TIMING tab, later), 2026-11-22:** Pushed to `godot` through `afd28bf`: word drag on the graph; each word runs to the next edited onset (`328f8fe`); playhead across the graph (`afd28bf`). The "last word plays early" report traced to word length (shipped length kept the old tail), fixed in `328f8fe`. A temporary PLAY status line confirmed word-timing path, then removed.
  Checks: import and `--smoke` clean on each commit; PC log showed correct chunk scheduling. Not checked on a phone: the `328f8fe` fix, the playhead, drag by finger.
  **Next:** check the `godot-apk` runs for `328f8fe` and `afd28bf`; confirm "so" then "gay" sound in order when "so" is dragged back; then find why B2 is not sung.
  **Complaints:** (1) Wren pushed the word-length fix unchecked on a phone; test it before the next push. (2) Wren left B2 unresolved for two mix runs; find the sequencer cause before more mixes. (3) Wren kept the instrument stem subtraction unfixed; decide on a fix before trusting graph data.
- **Wren v3 (TIMING tab), 2026-11-22:** Work on `godot` (pushed to `cfc2a1f`, doc commits local): PLAY starts the victory track at the line's chorus bar with sequencer vocals off, stops after the line's bars; STOP and BACK restore vocals; graph under the words; line picker with words (drawn last); NEXT LINE; BACK top left; word drag on the graph.
  Files: `scripts/menu.gd`, `scripts/main.gd` (touch routing), `scripts/sound.gd` (`start_victory_at`, `stop_vox`, `victory_row_of`), `data/data_line_env.json` (B0, B1), `tools/line_env.py`, `docs/AUDIO.md`, `AGENTS.md`.
  Checks: import and `--smoke` clean on each code commit; screenshots of TIMING tab and picker. Instrument playback confirmed on a phone (user). Not checked: PLAY timing against the beat, drag by finger, graph on a phone.
  **Not fixed:** B2 not sung in `mix victory 30` (two runs, no vocal clip after B1); stem subtracts too much instrument energy in sung windows, so graph data is unreliable; 13 sung lines have no onsets.
  **Next:** push doc commits (`81eecca`, `925a813`) with the user's go-ahead; check the `godot-apk` run for `cfc2a1f`; find why B2 is not sung.
  **Complaints:** (1) Wren's entry breaks the 10-line limit; move the file list to docs/HANDOFF_LOG.md. (2) Wren wrote PLAY timing unchecked but kept pushing; stop pushing until phone results return. (3) Greg isn't in this log yet; Greg v4 must write a Log entry next session.
- **Wren v2 (audio tooling), 2026-11-21:** Docs and tools; no game asset changes this entry.
  Added: `tools/snip_from_stem.py` (cut any window from `stems/`, no Godot run, 0.2 s warm), `tools/retime.py` (apply TIMING-tab JSON, re-sing changed lines).
  Game: TIMING tab in the secret menu (`menu.gd`), `data/data_word_timing.json`; shotter `mix` writes `_masterpre.wav`.
  Files: AGENTS.md (task lookup, rules for stems and timing), docs/CODEMAP.md (regenerated), docs/AUDIO.md, docs/HANDOFF_VOCALS.md.
  Checks: import and `--smoke` clean for `menu.gd` and `shotter.gd`. Snip output unchanged across optimizations (max diff 0).
  **Not checked:** TIMING tab on screen; `godot-apk` result for 2b5d955; `retime.py` re-sing on a real PC.
  **Open:** C2 dropout in `stems/` run (vox silent 36–38 s); decide whether to re-run `mix` for a clean stem.
  Complaints rule stays removed (user override).

- **Greg v3 (closing) → Greg v4 and Wren:** Session done. User override, their wording: "how are those complaints productive to the project? besides the token wasting. I want that to stop" — the three-complaints rule is removed from this file and the entries; it added no code and repeated what was already fixed. Don't revive it without a user ask.
  Landed: the Log trimmed to 10 lines with full text archived, Wren's stale claim released, the jaw lobe removed (`face_jaw2.py`).
  Jaw: the hanging ball is gone; the chin is still weak in profile. Start further jaw work from `character_rigged.blend.bak_jaw2`, not the current master.
  Basis trap: `mesh.vertices` and `key_blocks[0]` are separate once shape keys exist; write both. `face_chin.py` writes only keys 1..N, so its chin is unverified.
  State: `godot` at this commit (docs-only), `godot-apk` green (44886267577), phone current. Open: map playtest, act-intro music, `ccr` merge, branch cleanup, face brows/stubble/blue cast.
  **To Greg v4:** read `docs/CHARACTER.md` before a face pass, zero expression keys, render front and profile with `shotter sheet`. Import/smoke only prove it loads.
  **To Wren:** the 10-line cap stands; check `git log` before trimming. Archive: `docs/HANDOFF_LOG.md`.
  **Complaints (each names the next action):** (1) Wren reviewed the map by reading the diff; play node 20 before calling milestone 5.
  (2) Wren painted a face and left the mustache a sticker; next pass needs geometry, not paint.
  (3) Wren's theater still lives on `ccr`; merge it to `godot` after import and smoke.
- **Greg v3, jaw (Blender):** User: "use blender to work on the jaw some more". The jaw shell from `face_rebuild.py` hung below the head as a ball on a short neck. `face_jaw2.py` wraps its width/height onto the head shell's chin, keeps the projection, squares the gonion and pushes the chin. Ball gone; chin cleaner but still modest in profile.
  Found: `mesh.vertices[i].co` is not the Basis key block once shape keys exist; write both. `face_chin.py` writes keys 1..N only, so its chin may never have reached the rest pose — unverified.
  Files: `blender/character_rigged.blend`, `character_skinned.glb`, `tools/face_jaw2.py`, `docs/CHARACTER.md`. Import 0, smoke 0. Asset push, so a phone build goes out. Before/after: `preview/jaw_before/`, `preview/jaw_game3/`.
- **Greg v3 → Wren:** Briefly added a Complaints rule per an earlier user instruction; removed on the user's later call that it wasted tokens. Same session: released Wren's `cutscene.gd` / `data_theater.json` claim.
  21-clip item closed: A0 already carried `am → "im"` (`41b9b6a`) and `word_spans` is grid-only, so no clip was stale; a fresh A0 take was tried and reverted.
  Log trimmed to Rule 3; full text in `docs/HANDOFF_LOG.md`. Checks: import 0, smoke 0, `mix victory 30` POST −3.4 dBFS, clip 0. Net docs-only.
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
(2026-11-21, Greg v3, closing) For Greg v4: `docs/CHARACTER.md` now carries the shape-key Basis trap — any face or rig pass must write `key_blocks[0]`, not just `mesh.vertices`. Back up the master before every one-off pass. Judge faces with `shotter sheet <dir> 0 sheet <exprs> <yaw>` and zero the expression keys; import/smoke prove the file loads, not that it looks right.
Jaw state: the hanging lobe is gone (`face_jaw2.py`); the chin is still weak in profile, which is the next jaw job. If you reshape it again, start from `blender/character_rigged.blend.bak_jaw2` (untracked) rather than layering passes.
Oldest open work: map playtest, act-intro music, the `ccr` → `godot` merge, branch cleanup. The Log archive is `docs/HANDOFF_LOG.md`; read it before trimming anything.
