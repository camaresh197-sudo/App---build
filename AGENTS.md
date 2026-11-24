# AGENTS.md

Guide for AI agents working in this repository. Read `handoff.md` first, then this file.

## What this repo is

- The Godot app ("Hula Vaquero") ships as an Android APK built by GitHub Actions.
- The Godot project lives on the `godot` branch (`godot/hula/` inside it). It is not checked out on `main`.
- `main` holds only CI and the handoff docs.

## Build pipeline

| Workflow | Trigger | What it does |
|---|---|---|
| `.github/workflows/release.yml` ("Release") | push to `main`, manual | Checks out `godot`, installs Godot 4.6.3 and export templates, stamps build numbers, exports a debug APK, uploads artifact `HulaVaquero-apk`. |
| `.github/workflows/blank.yml` ("CI") | push and PR to `main`, manual | Placeholder "Hello, world" job. Does not test the game. |
| `godot-apk` | push to `main`, `godot`, `ccr-*` | Builds the APK and publishes an update pack to the `godot-latest` release. The installed Android app downloads it automatically. |

**A push to `godot` or `ccr-*` reaches users' phones.** Run the import and smoke check before pushing code or assets.

## Checks before pushing Godot code

```
godot --headless --path godot/hula --import
godot --headless --path godot/hula --quit-after 120 -- --smoke
```

Look for `SCRIPT ERROR` in the output. Use Godot 4.6.3.

Known traps (also in `handoff.md`):
- `var x := SOME_CONST_ARRAY[i]` does not compile on untyped arrays. Use `var x: String = ...`.
- A compile error in `menu.gd` stops `main.gd` from loading, so Android shows only the background.
- The updater mounts packs from `user://.../packs` over `res://`. Delete that folder when testing locally, or you test old code.

## Branches

- Finished work goes to `godot`. Doc-only commits are safe there (`**/*.md` is ignored by the build).
- Work on your own branch (`ccr-<id>` or `<agent>-<topic>`) and say so in the handoff log.
- Never commit generated files: `*.import`, `*.uid`, `.godot/`, `build/`.

## Rules

1. Claim files in the "Claimed" table of `handoff.md` before editing them. Release the claim when pushed.
2. Do not edit files another agent has claimed. Leave a note in the Log instead.
3. Log each handoff in `handoff.md`, newest first, and keep the entry short. Detail goes in `docs/`.
4. Small commits, one topic each.
5. Do not claim something works until you have run it.
6. Do not open a pull request unless the user asks.

## Session start

1. Read `handoff.md` (Log, Claimed table, Open items).
2. Run `git log origin/godot -5` if you need the Godot state.
3. Work from what the Log and commits show. If an entry about you cannot be confirmed, say so in the Log.
