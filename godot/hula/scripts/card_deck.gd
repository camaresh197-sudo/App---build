extends RefCounted
class_name CardDeck
# Level-up card picker. Card data: data/data_upgrades.json (ported from the legacy HTML5 build).
# Only cards whose effect the Godot build implements are in IMPLEMENTED. Everything else in the
# catalog (new weapons, active skills, weapon levels, gold, pickups, burn, grip) is not offered yet.

const DATA := "res://data/data_upgrades.json"
const IMPLEMENTED := [
	"r_twin", "r_turbo", "r_plate", "r_shell", "r_bumper", "r_repair", "r_luck",
	"p_spurs", "p_poncho", "p_tequila", "p_eye", "p_rage",
	"c_study", "c_hp", "c_dmg",
]
const RARITY_W := {"common": 1.0, "rare": 0.45, "epic": 0.2}
const RARITY_COL := {"common": "bdc3c7", "rare": "3498db", "epic": "9b59b6"}
const SHIELD_RECHARGE := 15.0
const TAKE_HIT := 12.0

static var _catalog: Array = []

# run state for the current ride; reset() at the start of every run
var st: Dictionary = {}
var owned: Dictionary = {}

func reset() -> void:
	st = {
		"dmg": 1.0, "crit": 0.0, "extra": 0, "speed": 1.0,
		"max_hp": 100.0, "armor": 0, "regen": 0.0, "heal_kill": 0.0,
		"ram": 0, "xp_mult": 1.0, "luck": 0.0,
		"shield_max": 0, "shield": 0, "shield_t": 0.0,
	}
	owned = {}

static func catalog() -> Array:
	if _catalog.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		if parsed is Dictionary:
			for c in parsed.get("cards", []):
				if String(c.get("id", "")) in IMPLEMENTED:
					_catalog.append(c)
	return _catalog

# up to n distinct cards the player can still take. Rarer cards get more weight with Luck.
func choices(n: int) -> Array:
	var pool: Array = []
	for c in catalog():
		var mx = c.get("max")
		if mx != null and int(owned.get(c.id, 0)) >= int(mx):
			continue
		var w: float = RARITY_W.get(String(c.rarity), 1.0)
		if String(c.rarity) != "common":
			w *= 1.0 + float(st.luck) * 0.01
		pool.append([c, w])
	var out: Array = []
	for k in n:
		if pool.is_empty():
			break
		var total := 0.0
		for p in pool:
			total += float(p[1])
		var r := randf() * total
		var idx := pool.size() - 1
		for i in pool.size():
			r -= float(pool[i][1])
			if r <= 0.0:
				idx = i
				break
		out.append(pool[idx][0])
		pool.remove_at(idx)
	return out

# applies a card to the run. hp is the current HP; returns the new HP (Repair Kit heals).
func apply(id: String, hp: float) -> float:
	owned[id] = int(owned.get(id, 0)) + 1
	match id:
		"r_twin": st.extra += 1
		"r_turbo": st.speed *= 1.08
		"r_plate":
			st.max_hp += 20.0; st.armor += 1; hp += 20.0
		"r_shell":
			st.shield_max += 1; st.shield += 1
		"r_bumper": st.ram += 1
		"r_repair":
			hp += float(st.max_hp) * 0.4; st.regen += 0.3
		"r_luck": st.luck += 10.0
		"p_spurs": st.speed *= 1.1
		"p_poncho":
			st.max_hp += 10.0; st.armor += 2; hp += 10.0
		"p_tequila": st.heal_kill += 0.1
		"p_eye": st.crit += 0.08
		"p_rage": st.dmg *= 1.15
		"c_study": st.xp_mult *= 1.1
		"c_hp":
			st.max_hp += 15.0; hp += 15.0
		"c_dmg": st.dmg *= 1.12
	return minf(hp, float(st.max_hp))

# damage the hero takes from one ball contact, before shield. Armor and Ram reduce it.
func hit_damage() -> float:
	return TAKE_HIT / (1.0 + 0.15 * float(st.armor)) * pow(0.7, int(st.ram))

# shield recharges one point every SHIELD_RECHARGE seconds while below its max
func tick_shield(dt: float) -> void:
	if int(st.shield) < int(st.shield_max):
		st.shield_t += dt
		if st.shield_t >= SHIELD_RECHARGE:
			st.shield_t = 0.0
			st.shield += 1
	else:
		st.shield_t = 0.0

static func rarity_color(c: Dictionary) -> Color:
	return Color(RARITY_COL.get(String(c.get("rarity", "common")), "bdc3c7"))
