# CLAUDE.md — Claude Code project instructions

**Read `HANDOFF.md` first, every session, before acting.** Then `AGENTS.md`.

## Git workflow

**Always push to the `godot` branch** — not to feature branches or `main`.

When committing changes:
1. Create/work on feature branch as needed
2. Commit with detailed message
3. Push to `godot` branch: `git push origin <branch>:godot`

This keeps the workflow consistent with GitHub Actions and deploys.

## Project structure

See `AGENTS.md` for codebase overview, file locations, and task lookup table.

## Audio generation

Victory vocals are sung lines rendered from Piper (VITS, en_US-ryan-medium) speech:
WORLD re-pitches each syllable to the victory melody (-24 semitones) and stretches vowels
so syllables land on the beat. Lyrics live in `godot/hula/data/data_lyrics.json`
(clip id -> text); clips are in `godot/hula/audio/vox/`, lead-in 0.15 s in `data_vox.json`.
After pulling changes run `godot --headless --import` to generate `.import` files.

## Compact instructions

When compacting (`/compact` or automatic), keep these in the summary:
- The rule to read `HANDOFF.md` first, then `AGENTS.md`, `PERSONALITIES.md`, and `git log origin/godot -5`. Re-read `HANDOFF.md` after compacting if the summary doesn't include its Log and Claimed table.
- `godot` is the source of truth. Push finished work there with `git push origin <branch>:godot`. Do not push to `main` or `ccr-*` without the user's explicit go-ahead.
- Any files another agent has claimed in the `HANDOFF.md` Claimed table. Do not edit them.
- Any user override in `HANDOFF.md`, with the user's exact wording.
- The current task, its branch, and what is still unpushed or unverified.
- Doc-only commits (`*.md`) are safe on `godot`. Code and asset commits publish to the phone, so run the import and smoke test first.
