# Handoff: Claude <-> Greg (DeepSeek)

Greg, glad to have you on this. Steady hands, good brother.

Git is our only channel (neither of us can message the other directly). Pull before you start, push when you stop.

## Rules
1. **Claim before editing.** Add your files to "Claimed" below, push, then edit. Remove the row when your work is pushed.
2. **Don't touch files the other has claimed.** If you must, leave a note in the Log and wait.
3. **Log every handoff.** Newest entry on top, 10 lines max: who, what changed, files, what's next, anything broken.
4. **Small commits, clear messages.** One topic per commit.
5. **Never commit generated files:** `*.import` / `*.uid` created by running Godot, `.godot/`, `build/`.

## Branches and builds
- Claude works on `ccr-74f83a2e-94v7jl`. Greg: use your own branch, e.g. `greg-<topic>`, and say so in the Log.
- The `godot-apk` workflow builds only `main`, `godot` and `ccr-*`. **A push to those publishes an update pack to the `godot-latest` release, which the installed Android app downloads automatically.** A broken push reaches the phone. Test first.

## Claimed
| Who | Files | Since |
|---|---|---|
| (none) | | |

## Gotchas we already hit
- `var x := SOME_CONST_ARRAY[i]` does not compile (untyped array). Write `var x: String = ...`. A compile error in `menu.gd` makes `main.gd` fail to load, so Android shows only the background.
- Check before pushing: `godot --headless --path godot/hula --quit-after 120 -- --smoke` and look for `SCRIPT ERROR` (Godot 4.6.3).
- The updater mounts packs from `user://.../packs` over `res://`. When testing locally, delete that `packs` folder or you test old code.
- Narration-only cutscene scenes have no entry in `data_cutscenes.json`; their text lives in `data_theater.json`.

## Current state
- Note: the theater code below is on branch `ccr-74f83a2e-94v7jl` and is not on `godot` or `main` until merged. Read it there: `git fetch origin ccr-74f83a2e-94v7jl`.
- Done: Cutscene Theater (secret menu: tap the RUNS pill 3 times). 28 scenes, act intros, playlist playback. Code in `scripts/cutscene.gd`, `scripts/menu.gd`, data in `data/data_theater.json`.
- Open: **world map between levels.** Not started and waiting on a scope decision. The Godot game is one endless run with no levels or acts. The HTTP version (`git show 93e7731:index.html`, search `WORLDS`, `NODES`, `drawMap`) has 4 acts of timed levels, bosses, a shop and a node map. A level system has to exist before a map makes sense.

## Log (newest first)
- **Claude:** Theater finished and pushed (`e87f0f9`). Created this file. Next: waiting on world map scope. Greg, you're up whenever you want a piece; claim it above first.

## Greg's notes
(write here)
