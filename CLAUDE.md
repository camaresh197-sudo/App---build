# CLAUDE.md

**Read `HANDOFF.md` first, every session, before acting.** Then `AGENTS.md`, `PERSONALITIES.md`, and your own findings bank (Wren `docs/findings/WREN.md`, Greg `docs/FINDINGS.md`).

## Hard rules (the ones that keep getting skipped)
1. **Findings bank:** the moment you learn something major, append one record to your own bank (Wren `docs/findings/WREN.md`, Greg `docs/FINDINGS.md`) BEFORE your next reply. Do not wait for the end.
2. **Claim before the first edit** of code, data or assets: Claimed row in `HANDOFF.md`, push, then edit. Remove it when pushed.
3. **End of session:** when the user ends it or asks for the handoff, run `python3 tools/session_check.py` and do every item in `docs/AGENT_PROTOCOL.md` > End of session. Tick each step in the reply; name any skipped one.
4. **Never push without the user's go-ahead.** `.md`-only pushes to `godot` build nothing; say "no build triggered".
5. A Stop hook (`.claude/settings.json`) runs the same checker and blocks "done" while it fails; Greg runs it by hand with `--agent greg`.

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
When compacting, keep: the read order (`HANDOFF.md`, `AGENTS.md`, `PERSONALITIES.md`, your own findings bank, `git log origin/godot -5`); `godot` as the source of truth (no pushes to `main` or `ccr-*` without go-ahead); claimed files; every user override in exact wording; the current task, branch, and any unpushed or unverified work.
