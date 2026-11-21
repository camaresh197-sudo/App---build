# CLAUDE.md — Claude Code project instructions

**Read `HANDOFF.md` first, every session, before acting** (user rule). Then `AGENTS.md`.

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
