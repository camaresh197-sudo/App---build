---
name: fast-godot
description: Fast, low-token Godot 4 coding and debugging rules for rapid iterations.
---

# Fast Godot 4 Rules
- **Engine:** Godot 4.x only (`@export`, `@onready`, `await`, `CharacterBody3D`/`2D`, `Tween`, static types).
- **Edits:** Output ONLY changed functions or minimal unified diffs. Never rewrite untouched code.
- **No Fluff:** Zero explanations, zero summaries, zero intros/outros. Just apply the edit.
- **Debug:** Read the exact error line first. Check `@onready` paths in `.tscn` before editing logic.
- **Scope:** Touch `.gd` files only unless `.tscn` changes are explicitly requested.
