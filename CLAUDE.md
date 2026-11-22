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
When compacting, keep: the read order (`HANDOFF.md`, `AGENTS.md`, `PERSONALITIES.md`, `git log origin/godot -5`); `godot` as the source of truth (no pushes to `main` or `ccr-*` without go-ahead); claimed files; every user override in exact wording; the current task, branch, and any unpushed or unverified work.
