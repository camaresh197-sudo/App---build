extends RefCounted
# Save data (user://save.json) and the menu's static data (data_menu.json: skills, cosmetics, trophies).
const PATH := "user://save.json"
static var data: Dictionary = {}
static var defs: Dictionary = {}

static func load_all() -> void:
	var f := FileAccess.open("res://data/data_menu.json", FileAccess.READ)
	defs = JSON.parse_string(f.get_as_text())
	data = {"gold": 300, "skills": {}, "own": {"hat": [0], "hoop": [0], "trail": [0]}, "eq": {"hat": 0, "hoop": 0, "trail": 0},
		"ach": {}, "stats": {"runs": 0, "kills": 0, "hats": 0, "bosses": 0, "gold_all": 0, "time": 0, "best_run": 0, "best_level": 0, "best_combo": 0, "best_kills": 0},
		"opt": {"music": 8, "sfx": 8, "particles": 1, "shake": true, "fps": false, "vibe": true, "legacy": true}, "levels": {}}
	var g := FileAccess.open(PATH, FileAccess.READ)
	if g:
		var j = JSON.parse_string(g.get_as_text())
		if j is Dictionary: _merge(data, j)

static func _merge(a: Dictionary, b: Dictionary) -> void:
	for k in b:
		if a.has(k) and a[k] is Dictionary and b[k] is Dictionary: _merge(a[k], b[k])
		else: a[k] = b[k]

static func save() -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f: f.store_string(JSON.stringify(data))

static func rank(id: String) -> int: return int(data.skills.get(id, 0))
static func skill_cost(s: Dictionary) -> int: return int(round(s.base * pow(1.7, rank(s.id))))
