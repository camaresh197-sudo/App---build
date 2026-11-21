extends RefCounted
class_name Legacy
const Save = preload("res://scripts/save.gd")
# The "legacy version": features ported from the archived HTML5 build (see docs/legacy.md and
# docs/legacy_checklist.md). Everything legacy checks Legacy.on(). Turn it off under Options to play
# without the ported features. When the checklist is finished and the final review is done, this file
# and every Legacy.on() check get removed together.

static func on() -> bool:
	return bool(Save.data.opt.get("legacy", true))
