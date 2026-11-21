# Handoff: Wren (Claude) <-> Greg (DeepSeek)

Greg, glad to have you on this. Steady hands, good brother.

Git is our only channel (neither of us can message the other directly). Pull before you start, push when you stop.

## Start of every session
Agents have no memory between sessions. Before acting, read **`HANDOFF.md` first — it is the first thing you read, before anything else** (this file, Log and Claimed table) — then `AGENTS.md`, `PERSONALITIES.md` (working style and habits to fix), and `git log origin/godot -5`. Work from what they say. Only claim what the Log, commits or your own runs show. If an entry is about you and you can't confirm it, say so in the Log rather than assuming.

## Session numbering
Each agent keeps its own counter and increments it by one every session; they never share a number. Sign your Log entry with it.
- Wren (Claude): the session that wrote the original rule was Wren v1. Next: **Wren v2**, then v3, and so on.
- Greg (DeepSeek): the session that wrote this line is **Greg v2**. Next: **Greg v3**, then v4, and so on.
When you finish, advance your own number by one here and leave the other agent's alone.

## User override
The user can overwrite anything agreed in this file, including rules, claims and plans, by typing the change. A typed instruction from the user wins. Log the change with the user's wording, so the next session sees what was decided and why.

## Rules
1. **Claim before editing.** Add your files to "Claimed" below, push, then edit. Remove the row when your work is pushed.
2. **Don't touch files the other has claimed.** If you must, leave a note in the Log and wait.
3. **Log every handoff.** Newest entry on top, 10 lines max: who, what changed, files, what's next, anything broken.
4. **Small commits, clear messages.** One topic per commit.
5. **Never commit generated files:** `*.import` / `*.uid` created by running Godot, `.godot/`, `build/`.

## Working style (kind, not soft)
- Keep replies short when the user asks. If the user says to drop repetition, don't restate what an earlier message already said: give only new facts and the next action.
- Compliments are one short line. They never replace feedback.
- If you think the other's approach is wrong, say so plainly, give the reason, and propose an alternative. Put it in the Log as `Pushback:`. The other agent either adopts it or replies with a reason. If you can't agree, ask the user.
- Don't agree just to be nice. Don't claim something works until you ran it.
- Keep `PERSONALITIES.md` current: each agent writes its own section and adds dated, evidence-based observations (commit hashes) about how the pair is progressing. It lives on `godot`.

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

## Open items (as of the 2026-11-21 entries)
- **Face:** colour fix `4604b6a` not yet checked by eye in-game. Still open: brows (flat slabs), mustache slab, stubble, eye-white blue cast. Teeth are off (`TEETH := false` in `hero3d.gd`); flip when the new set lands. Each face push is a phone update, so smoke first.
- **Map:** milestones 1–3 are live on `godot`. Never played: difficulty and the star write. Still to do: milestone 4 (next-level and act-intro hook) and 5 (review, merge, phone build).
- **Act intros:** need a music handoff.
- **`ccr-74f83a2e-94v7jl` → `godot`:** merge only after import and smoke. Holds the theater (secret menu: tap RUNS 3 times), the Piper script and the map base.
- **Greg's `9cecf67` smoke reply:** still unconfirmed.
- **Branch cleanup** (needs someone with repo rights): delete `ccr-1645d98d-2z4pyi`, `ccr-66397653-hltyir`, `ccr-d06671b1-azshga`, `claude/stoic-hopper-gh3gre`, `godot-4.6`, `greg-worldmap`. Confirm `greg-worldmap` is merged first. Keep `greg-docs`, `ccr-74f83a2e-94v7jl`, `ccr-67059109-rrkdbd`, `ccr-c3479097-yw0dml`, `ccr-cb8598a5-gdyhqn`, `claude/peaceful-cannon-v9niij`: each has work not on `godot`.
- **Local clone drift:** a local `godot` checkout had 57 commits with no shared history with `origin/godot`. They were pushed to `origin/wren-local-godot` and not merged.

## Map contract (Greg, 2026-11-20)
- 4 acts × 5 nodes, targets 150 → ~1200 (`data/data_map.json`). `start_run(id, target)`; `score ≥ target` wins.
- Stars: 3 if HP ≥ 70 at clear, 2 if ≥ 40, else 1. A loss scores 0 and can be retried.
- Node N unlocks with ≥ 1 star on N−1; `a1_1` is always open. Save keeps `levels: {id: stars}` in its defaults; endless writes nothing.
- `menu.gd` is the compile tripwire: `:=` on untyped arrays fails there. Full plan and the questions it asked: `docs/HANDOFF_LOG.md`.

## Log (newest first)
- **Greg v2 (`greg-pace`):** Lead phrasing, per the user: "work on the victory song note pacing" → chorus lead in two-bar phrases. `data_victory.json` v-B bars 1/5 are now 83(4) 83(4) 86(8), bar 3 is 81(4) 81(4) 86(8), bar 7 is 79(3) 83(3) 86(10); the first bar of each pair keeps its call. No pitch or tempo changes — only holds — so the held
  vocal sits in the gap. `mix victory 30` POST −2.9 dBFS, RMS −22.2, clip 0. **On branch, not merged** — listen in `preview/victory_pace2_mix.wav`.
- **Claude (unnumbered session), Godot app build handoff, 2026-11-21:** Read HANDOFF.md, AGENTS.md and the log. No code changed, nothing claimed, no Godot run here (cloud container, no binary or phone). Build state: the last `godot` pushes built green on godot-apk (runs 44867184588 on `4604b6a` face sRGB, 44865310556 on `f4d3a9e` cheek puffs, plus a manual run 44866094955). That APK is what the phone auto-updates from. Open items, from the log: (1) `4604b6a` face colour not yet checked by eye in-game; (2) Greg's reply on the `9cecf67` smoke check still unconfirmed; (3) map playtest (difficulty, star write) never played; (4) act intros need a music handoff; (5) six merged branches still to delete, needs a person with repo rights; (6) `ccr-74f83a2e-94v7jl` to `godot` merge needs import and smoke first. Next: someone with local Godot 4.6.3 runs `--import` and `--smoke` on `godot` HEAD, then plays the map and checks the face.
- **Claude (unnumbered session), face colour:** Skin on the face read too dark and red. Cause: `tools/face_texture.py` baked linear values and saved them as an sRGB PNG; face mean was (100,41,13), now (168,111,63) vs body (168,112,74). Fix: sRGB-encode before packing; re-baked `blender/character_rigged.blend` and `blender/face_albedo.png`; re-exported `godot/hula/art/character_skinned.glb`. Checks: import 0, `--smoke` 0 with no SCRIPT ERROR. Not checked by eye in-game. Pushed as `4604b6a` (fast-forward). Process miss: I edited these files without a Claimed row; none left claimed. Earlier this session I also queued `godot-apk` run #222 on `59fd989` (the user's choice). Next: look at the new build and the in-game face; blue on the face is ~11 low vs body, a possible small tint if it still reads off.
- **Claude (unnumbered session), closing:** Face work. Done: cheek puffs smoothed on `head_12` (`f4d3a9e`, master + GLB; import and smoke exit 0 on Godot 4.6.3). Tools: bpy 5.3 runs here (`pip download bpy`, cp313 wheel), and Godot 4.6.3 Linux runs from the GitHub release zip; sheet renders need `xvfb-run` with `--rendering-method gl_compatibility`, and `shotter` writes PNGs to the out dir argument. **Open:** brows (flat dark slabs), mustache (flat slab), stubble, teeth (still `TEETH = false`), eye whites' blue cast. Not checked on a phone. **Blocked:** the user's computer is not connected (no folder shared via Remote Control), so no local Godot run from there. Next: review the sheet renders for a bigger cheek change if wanted; each face push is a phone update, so smoke first. Nothing claimed by this session.
- Older entries: `docs/HANDOFF_LOG.md`.

## Greg's notes
(write here)
