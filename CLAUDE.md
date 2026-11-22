# CLAUDE.md

**Read `HANDOFF.md` first, every session, before acting.** Then `AGENTS.md`.

## Git
Push finished work to `godot`, not feature branches or `main`:
1. Work on a feature branch if needed
2. Commit with a detailed message
3. `git push origin <branch>:godot`

GitHub Actions and deploys watch `godot`.

## Project
Structure, file locations and task lookup: `AGENTS.md`.

## Audio
Victory vocals are Piper (VITS, en_US-ryan-medium) speech. WORLD re-pitches each syllable to the melody (-24 semitones) and stretches vowels onto the beat. Lyrics: `godot/hula/data/data_lyrics.json` (clip id → text). Clips: `godot/hula/audio/vox/`; lead-in 0.15 s in `data_vox.json`. After pulling, run `godot --headless --import`.

## Compact instructions
When compacting (`/compact` or automatic), keep:
- Read `HANDOFF.md` first, then `AGENTS.md`, `PERSONALITIES.md`, and `git log origin/godot -5`. Re-read `HANDOFF.md` after compacting if the summary lacks its Log and Claimed table.
- `godot` is the source of truth. Don't push to `main` or `ccr-*` without the user's explicit go-ahead.
- Files another agent has claimed in `HANDOFF.md`. Don't edit them.
- Every user override in `HANDOFF.md`, in the user's exact wording.
- The current task, its branch, and what is unpushed or unverified.
- Doc-only (`*.md`) commits are safe on `godot`. Code and asset commits reach the phone: run import and smoke first.
