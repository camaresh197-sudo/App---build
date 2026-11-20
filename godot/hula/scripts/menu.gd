extends RefCounted
# Title screen and the options hub (Skills / Wardrobe / Trophies / Stats / Settings). Draws onto the main node `c`.
const Save = preload("res://scripts/save.gd")
const TABS := ["SKILLS", "WARDROBE", "TROPHIES", "STATS", "SETTINGS"]
const TAB_COL := [Color("e67e22"), Color("e84393"), Color("f39c12"), Color("0984e3"), Color("6c5ce7")]
var c: Node2D
var tab := 0
var page := 0
var in_hub := false
var set_flash := 0.0
var song_test := ""
var sec_taps := 0
var sec_t := 0.0
var sec_msg := ""

func _init(main: Node2D) -> void:
	c = main

func open_hub(t := 4) -> void:
	in_hub = true; tab = t; page = 0
func close_hub() -> void:
	in_hub = false

# ---------- helpers ----------
func font() -> Font: return ThemeDB.fallback_font
func txt(p: Vector2, s: String, size: int, col: Color, w := -1.0, align := HORIZONTAL_ALIGNMENT_LEFT) -> void:
	c.draw_string(font(), p, s, align, w, size, col)
func ctxt(cx: float, y: float, s: String, size: int, col: Color) -> void:
	var w := font().get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	c.draw_string(font(), Vector2(cx - w / 2.0, y), s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)
func otxt(p: Vector2, s: String, size: int, col: Color, ol: Color, olw := 4) -> void:
	c.draw_string_outline(font(), p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, olw, ol)
	c.draw_string(font(), p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)
func rrect(r: Rect2, col: Color, rad := 8.0) -> void:
	var sb := StyleBoxFlat.new(); sb.bg_color = col
	sb.set_corner_radius_all(int(rad)); c.draw_style_box(sb, r)
func rframe(r: Rect2, col: Color, wd := 1.5, rad := 8.0) -> void:
	var sb := StyleBoxFlat.new(); sb.bg_color = Color(0, 0, 0, 0); sb.border_color = col
	sb.set_border_width_all(int(max(1, round(wd)))); sb.set_corner_radius_all(int(rad)); c.draw_style_box(sb, r)
func button(r: Rect2, label: String, col: Color, fn: Callable, fs := 20, sub := "") -> void:
	c.buttons.append([r, fn])
	rrect(Rect2(r.position + Vector2(0, 3), r.size), Color(0, 0, 0, 0.35), 10)
	rrect(r, col, 10)
	rrect(Rect2(r.position + Vector2(2, 2), Vector2(r.size.x - 4, r.size.y * 0.42)), Color(1, 1, 1, 0.16), 8)
	rframe(r, Color(1, 1, 1, 0.35), 1.5, 10)
	if sub == "":
		ctxt(r.position.x + r.size.x / 2, r.position.y + r.size.y / 2 + fs * 0.35, label, fs, Color.WHITE)
	else:
		ctxt(r.position.x + r.size.x / 2, r.position.y + r.size.y / 2 - 1, label, fs, Color.WHITE)
		ctxt(r.position.x + r.size.x / 2, r.position.y + r.size.y / 2 + 14, sub, 11, Color(1, 1, 1, 0.8))
func pill(r: Rect2, border := Color(1, 0.83, 0.16, 0.55)) -> void:
	rrect(Rect2(r.position + Vector2(0, 2), r.size), Color(0, 0, 0, 0.3), r.size.y / 2)
	rrect(r, Color(0.09, 0.05, 0.16, 0.85), r.size.y / 2)
	rframe(r, border, 1.2, r.size.y / 2)
func coin(p: Vector2, r := 7.0) -> void:
	c.draw_circle(p, r, Color("1e8449")); c.draw_circle(p, r * 0.77, Color("58d68d"))

# ---------- title screen ----------
func title(R: float, t: float, hero: Callable, ship_tex: Array) -> void:
	var ox := (R - 640.0) / 2.0
	var hx := ox + 190.0
	# sun + rays + town
	c.draw_circle(Vector2(hx, 190), 88, Color(1, 0.8, 0.4, 0.35))
	c.draw_circle(Vector2(hx, 190), 66, Color(1, 0.85, 0.5, 0.55))
	for k in 14:
		var a := t * 0.12 + k * TAU / 14.0
		c.draw_colored_polygon(PackedVector2Array([Vector2(hx, 52), Vector2(hx, 52) + Vector2.from_angle(a - 0.05) * 330, Vector2(hx, 52) + Vector2.from_angle(a + 0.05) * 330]), Color(1, 0.92, 0.6, 0.07))
	for k in 14:
		var bx := k * 62.0 - 30.0; var bh := 40.0 + float((k * 37) % 50)
		c.draw_rect(Rect2(bx, 300 - bh, 52, bh + 60), Color("3a2147"))
		for w in 3: c.draw_rect(Rect2(bx + 8 + w * 14, 300 - bh + 10 + (k % 2) * 8, 7, 9), Color("ffcf6b") if (k + w) % 3 != 0 else Color("5b3a66"))
	c.draw_rect(Rect2(0, 300, R, 60), Color("4a2a3e")); c.draw_rect(Rect2(0, 300, R, 3), Color("ff9a5c"))
	# ring
	c.draw_set_transform(Vector2(hx, 322), 0.0, Vector2(1, 0.22)); c.draw_arc(Vector2.ZERO, 92, 0, TAU, 48, Color(1, 0.83, 0.16, 0.8), 3.0); c.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# bunting
	for row in 2:
		var y0 := 8.0 + row * 20.0
		for k in 22:
			var x := k * (R / 21.0); var y := y0 + sin(k * 0.5 + row) * 4.0 + 6.0
			var col := Color.from_hsv(fmod(k * 0.13 + row * 0.3, 1.0), 0.6, 1.0)
			c.draw_colored_polygon(PackedVector2Array([Vector2(x - 8, y), Vector2(x + 8, y), Vector2(x, y + 15)]), col)
	# title letters
	var word := "HULA VAQUERO"
	var tw := 0.0
	for ch in word: tw += font().get_string_size(ch, HORIZONTAL_ALIGNMENT_LEFT, -1, 44).x
	var lx := hx - tw / 2.0
	for i in word.length():
		var ch := word[i]
		var w := font().get_string_size(ch, HORIZONTAL_ALIGNMENT_LEFT, -1, 44).x
		var dy := sin(t * 3.0 + i * 0.55) * 2.5
		if ch != " ":
			otxt(Vector2(lx, 80 + dy), ch, 44, Color("ffd32a"), Color(0.31, 0.1, 0.0, 0.95), 7)
		lx += w
	# ribbon
	var rx := hx - 112.0
	c.draw_colored_polygon(PackedVector2Array([Vector2(rx - 24, 100), Vector2(rx + 10, 100), Vector2(rx + 10, 128), Vector2(rx - 24, 128), Vector2(rx - 12, 114)]), Color("7d1020"))
	c.draw_colored_polygon(PackedVector2Array([Vector2(rx + 214, 100), Vector2(rx + 248, 100), Vector2(rx + 236, 114), Vector2(rx + 248, 128), Vector2(rx + 214, 128)]), Color("7d1020"))
	rrect(Rect2(rx, 92, 224, 30), Color("c0182f"), 4); rframe(Rect2(rx, 92, 224, 30), Color("ffd32a"), 1.5, 4)
	ctxt(hx, 112, "SKY RIDE · DELUXE", 15, Color.WHITE)
	# hero and orbiting ships
	hero.call(Vector2(hx, 214), t, 1.75)
	for k in 6:
		var a := t * 0.5 + k * TAU / 6.0
		var p := Vector2(hx + cos(a) * 130, 230 + sin(a) * 38)
		var d := Vector2(-sin(a), cos(a) * 0.3).normalized() * (1 if k % 2 == 0 else 1)
		var fi := clampi(int(round(rad_to_deg(acos(clamp(d.y, -1.0, 1.0))) / 5.0)), 0, 36)
		var sz := 56.0 + sin(a) * 10.0
		var mod := Color.from_hsv(fmod(0.0 + k * 0.17, 1.0), 0.0 if k == 0 else 0.55, 1.0)
		var r := Rect2(p - Vector2(sz, sz) / 2.0, Vector2(sz, sz))
		if d.x < 0.0: r = Rect2(r.position + Vector2(sz, 0), Vector2(-sz, sz))
		c.draw_texture_rect(ship_tex[fi], r, false, mod)
	# buttons column
	var bxr := R - 250.0
	button(Rect2(bxr, 64, 224, 60), "RIDE!", Color("2ecc71"), c.start_run, 30, "world map · 4 acts")
	button(Rect2(bxr, 136, 224, 50), "ENDLESS", Color("8e44ad"), c.start_run, 22, "no map, just fly")
	button(Rect2(bxr, 198, 224, 50), "OPTIONS", Color("e67e22"), func(): open_hub(0), 22, "skills · wardrobe · more")
	pill(Rect2(bxr, 262, 104, 26)); coin(Vector2(bxr + 14, 275)); txt(Vector2(bxr + 28, 280), "$ %d" % Save.data.gold, 13, Color("58d68d"))
	c.buttons.append([Rect2(bxr + 112, 262, 112, 26), _secret_tap])
	pill(Rect2(bxr + 112, 262, 112, 26)); ctxt(bxr + 168, 280, "NO RUNS YET" if Save.data.stats.runs == 0 else "RUNS %d" % Save.data.stats.runs, 11, Color.WHITE)
	ctxt(bxr + 112, 312, "Drag to fly. Your weapons fire by themselves.", 11, Color(1, 1, 1, 0.8))
	ctxt(bxr + 112, 332, "Normal difficulty", 12, Color(1, 1, 1, 0.85))
	var vf := FileAccess.open("res://version.txt", FileAccess.READ)
	txt(Vector2(8, 352), "update " + (vf.get_as_text() if vf else "dev"), 11, Color(1, 1, 1, 0.55))

# ---------- hub ----------
func hub(R: float, t: float, hero: Callable) -> void:
	var ox := (R - 640.0) / 2.0
	c.draw_rect(Rect2(0, 0, R, 360), Color(0.03, 0.03, 0.08, 0.8))
	# tabs
	for i in 5:
		var r := Rect2(ox + 8 + i * 69.5, 8, 66, 36)
		var on := i == tab
		c.buttons.append([r, func(): tab = i; page = 0])
		rrect(Rect2(r.position + Vector2(0, 2), r.size), Color(0, 0, 0, 0.3), 9)
		rrect(r, TAB_COL[i] if on else Color(0.15, 0.16, 0.27, 0.95), 9)
		rframe(r, Color.WHITE if on else Color(1, 1, 1, 0.12), 1.6 if on else 1.0, 9)
		ctxt(r.position.x + 33, r.position.y + 23, TABS[i], 10, Color.WHITE if on else Color("9aa3c7"))
	button(Rect2(ox + 358, 8, 80, 36), "BACK", Color("6c5ce7"), close_hub, 16)
	pill(Rect2(ox + 446, 12, 96, 28)); coin(Vector2(ox + 462, 26)); txt(Vector2(ox + 475, 31), "$ %d" % Save.data.gold, 13, Color("58d68d"))
	button(Rect2(ox + 550, 8, 82, 36), "RIDE!", Color("2ecc71"), func(): close_hub(); c.start_run(), 16)
	match tab:
		0: skills(ox)
		1: wardrobe(ox, t, hero)
		2: trophies(ox)
		3: stats(ox)
		4: settings(ox)

func skills(ox: float) -> void:
	var list: Array = Save.defs.skills
	var per := 8; var pages := int(ceil(list.size() / float(per)))
	page = clampi(page, 0, pages - 1)
	for i in per:
		var idx := page * per + i
		if idx >= list.size(): break
		var s: Dictionary = list[idx]
		var r := Rect2(ox + 14 + (i >> 2) * 310.0, 68 + (i & 3) * 60.0, 302, 55)
		var rk := Save.rank(s.id); var maxed := rk >= int(s.max); var cost := Save.skill_cost(s); var aff: bool = Save.data.gold >= cost
		c.buttons.append([r, func():
			if not maxed and Save.data.gold >= cost:
				Save.data.gold -= cost; Save.data.skills[s.id] = rk + 1; Save.save()])
		rrect(r, Color(0.12, 0.125, 0.22, 0.95), 10)
		rframe(r, Color("2ecc71") if maxed else (Color("f1c40f") if aff else Color("444444")), 1.5, 10)
		txt(r.position + Vector2(10, 19), s.name, 13, Color.WHITE)
		for k in int(s.max): c.draw_rect(Rect2(r.position.x + 10 + k * 12, r.position.y + 25, 9, 5), Color("2ecc71") if k < rk else Color(1, 1, 1, 0.2))
		txt(r.position + Vector2(10, 44), s.desc, 10, Color("b2bec3"), 280)
		var pr := "MAX" if maxed else "$ %d" % cost
		txt(r.position + Vector2(r.size.x - 70, 19), pr, 13, Color("2ecc71") if maxed else (Color("f1c40f") if aff else Color("777777")), 60, HORIZONTAL_ALIGNMENT_RIGHT)
	pager(ox, pages)
	ctxt(ox + 320, 339, "Page %d/%d · tap a skill to buy" % [page + 1, pages], 12, Color("dfe6e9"))

func pager(ox: float, pages: int) -> void:
	if pages <= 1: return
	button(Rect2(ox + 14, 318, 80, 34), "◄", Color("636e72"), func(): page = (page + pages - 1) % pages, 18)
	button(Rect2(ox + 546, 318, 80, 34), "►", Color("636e72"), func(): page = (page + 1) % pages, 18)

func wardrobe(ox: float, t: float, hero: Callable) -> void:
	c.draw_circle(Vector2(ox + 120, 170), 90, Color(1, 0.7, 0.28, 0.28))
	hero.call(Vector2(ox + 120, 190), t, 1.7)
	var secs := [["hat", "SOMBREROS", 74], ["hoop", "HOOPS", 160], ["trail", "TRAILS", 246]]
	for sc in secs:
		var kind: String = sc[0]
		txt(Vector2(ox + 240, sc[2] + 8), sc[1], 12, Color("ffd32a"))
		var items: Array = Save.defs.cos[kind]
		var n := items.size(); var gap := 5.0; var cw := (382.0 - gap * (n - 1)) / n
		for i in n:
			var it: Dictionary = items[i]
			var r := Rect2(ox + 240 + i * (cw + gap), sc[2] + 14, cw, 64)
			var owned: bool = (Save.data.own[kind] as Array).has(i); var eq: bool = int(Save.data.eq[kind]) == i; var aff: bool = Save.data.gold >= int(it.cost)
			c.buttons.append([r, func():
				if owned: Save.data.eq[kind] = i
				elif Save.data.gold >= int(it.cost):
					Save.data.gold -= int(it.cost); (Save.data.own[kind] as Array).append(i); Save.data.eq[kind] = i
				Save.save()])
			rrect(r, Color(0.12, 0.125, 0.22, 0.95), 9)
			rframe(r, Color("2ecc71") if eq else (Color("74b9ff") if owned else (Color("f1c40f") if aff else Color("444444"))), 2.5 if eq else 1.4, 9)
			var cx := r.position.x + cw / 2
			if kind == "hat":
				var hc: Color = [Color("f1e6c8"), Color("2b2b30"), Color("c0392b"), Color.WHITE, Color("f1c40f"), Color.from_hsv(fmod(t * 0.3, 1.0), 0.6, 1.0)][i]
				c.draw_colored_polygon(PackedVector2Array([Vector2(cx - cw * 0.36, r.position.y + 30), Vector2(cx + cw * 0.36, r.position.y + 30), Vector2(cx + cw * 0.15, r.position.y + 18), Vector2(cx - cw * 0.15, r.position.y + 18)]), hc)
			elif kind == "hoop":
				var col := Color.from_hsv(fmod(t * 0.3, 1.0), 0.7, 1.0) if not it.get("c") else Color(it.c[1])
				c.draw_arc(Vector2(cx, r.position.y + 22), min(cw * 0.26, 17.0), 0, TAU, 24, col, 3.0)
			else:
				var gl: String = ["×", "✦", "♨", "✺", "♥"][i]
				ctxt(cx, r.position.y + 32, gl, 20, [Color("777777"), Color("fff3a0"), Color("ff7a1a"), Color("48dbfb"), Color("ff6b81")][i])
			ctxt(cx, r.position.y + 47, it.name, 9, Color.WHITE)
			ctxt(cx, r.position.y + 59, "WORN" if eq else ("OWNED" if owned else "● %d" % int(it.cost)), 9, Color("2ecc71") if eq else (Color("74b9ff") if owned else (Color("f1c40f") if aff else Color("777777"))))

func trophies(ox: float) -> void:
	var list: Array = Save.defs.achs
	var per := 14; var pages := int(ceil(list.size() / float(per)))
	page = clampi(page, 0, pages - 1)
	var have := 0
	for a in list: if Save.data.ach.get(a.id, false): have += 1
	ctxt(ox + 320, 338, "%d / %d earned  ·  page %d/%d" % [have, list.size(), page + 1, pages], 13, Color("f1c40f"))
	for i in per:
		var idx := page * per + i
		if idx >= list.size(): break
		var a: Dictionary = list[idx]; var got: bool = Save.data.ach.get(a.id, false)
		var r := Rect2(ox + 14 + (i / 7) * 310.0, 68 + (i % 7) * 35.0, 302, 32)
		rrect(r, Color(0.18, 0.31, 0.22, 0.95) if got else Color(0.12, 0.125, 0.22, 0.95), 7)
		rframe(r, Color("2ecc71") if got else Color("3d4160"), 1.2, 7)
		txt(r.position + Vector2(8, 22), "★", 15, Color("f9ca24") if got else Color("555555"))
		txt(r.position + Vector2(30, 14), a.name, 11, Color.WHITE if got else Color("9aa3c7"), 200)
		txt(r.position + Vector2(30, 26), a.desc, 9, Color("9aa3c7"), 210)
		txt(r.position + Vector2(r.size.x - 70, 20), "DONE" if got else "● %d" % int(a.gold), 11, Color("2ecc71") if got else Color("f1c40f"), 60, HORIZONTAL_ALIGNMENT_RIGHT)
	pager(ox, pages)

func stats(ox: float) -> void:
	var st: Dictionary = Save.data.stats
	var rows := [["Runs played", st.runs], ["Balls popped", st.kills], ["Sombreros knocked off", st.hats], ["Bosses defeated", st.bosses],
		["Gold earned (all time)", st.gold_all], ["Time in the sky", "%d:%02d" % [int(st.time) / 60, int(st.time) % 60]], ["Best run", "-" if st.best_run == 0 else "%d:%02d" % [int(st.best_run) / 60, int(st.best_run) % 60]],
		["Best level", "-" if st.best_level == 0 else st.best_level], ["Best combo", "×%d" % st.best_combo], ["Most balls in a run", st.best_kills],
		["Trophies", "%d / %d" % [(Save.data.ach as Dictionary).size(), (Save.defs.achs as Array).size()]], ["Skill ranks bought", _sum(Save.data.skills)]]
	for i in rows.size():
		var r := Rect2(ox + 14 + (i / 6) * 310.0, 72 + (i % 6) * 43.0, 302, 38)
		rrect(r, Color(0.16, 0.17, 0.28, 0.8) if i % 2 == 0 else Color(0.12, 0.125, 0.22, 0.8), 8)
		txt(r.position + Vector2(12, 24), rows[i][0], 13, Color("c8d6e5"))
		txt(r.position + Vector2(r.size.x - 112, 24), str(rows[i][1]), 14, Color("ffd32a"), 100, HORIZONTAL_ALIGNMENT_RIGHT)

func _sum(d: Dictionary) -> int:
	var n := 0
	for k in d: n += int(d[k])
	return n

func settings(ox: float) -> void:
	var defs := [
		["music", "Music volume", "How loud the music is", "vol"], ["sfx", "Sound effects volume", "Shots, pops, pickups", "vol"],
		["particles", "Particles", "Sparks, confetti and cosmetic trails", "q"], ["shake", "Screen shake", "Shake on hits and booms", "bool"],
		["fps", "FPS counter", "Shows the frame rate in a corner", "bool"], ["vibe", "Vibration", "Buzz on hits", "bool"]]
	for i in defs.size():
		var d: Array = defs[i]
		var r := Rect2(ox + 14 + (i / 3) * 310.0, 70 + (i % 3) * 62.0, 302, 56)
		var key: String = d[0]
		rrect(r, Color(0.12, 0.125, 0.22, 0.95), 10); rframe(r, Color(1, 1, 1, 0.14), 1.2, 10)
		txt(r.position + Vector2(10, 22), d[1], 13, Color.WHITE)
		txt(r.position + Vector2(10, 40), d[2], 10, Color("9aa3c7"), 180)
		var kind: String = d[3]
		if kind == "bool":
			var on: bool = Save.data.opt[key]
			c.buttons.append([r, func(): Save.data.opt[key] = not on; Save.save()])
			var sw := Rect2(r.position.x + r.size.x - 54, r.position.y + 18, 42, 20)
			rrect(sw, Color("2ecc71") if on else Color("4a4f6e"), 10)
			c.draw_circle(Vector2(sw.position.x + (32 if on else 10), sw.position.y + 10), 7.5, Color.WHITE)
		else:
			var mx := 10 if kind == "vol" else 2
			var v: int = int(Save.data.opt[key])
			c.buttons.append([Rect2(r.position.x + r.size.x - 120, r.position.y, 40, r.size.y), func(): Save.data.opt[key] = max(0, v - 1); Save.save()])
			c.buttons.append([Rect2(r.position.x + r.size.x - 40, r.position.y, 40, r.size.y), func(): Save.data.opt[key] = min(mx, v + 1); Save.save()])
			txt(Vector2(r.position.x + r.size.x - 108, r.position.y + 34), "‹", 22, Color("7d86ad"))
			txt(Vector2(r.position.x + r.size.x - 26, r.position.y + 34), "›", 22, Color("7d86ad"))
			var lab: String = ("%d%%" % (v * 10)) if kind == "vol" else ["Low", "Normal", "High"][v]
			ctxt(r.position.x + r.size.x - 62, r.position.y + 33, lab, 13, Color("ffd32a"))

# ---------- secret song test (tap the RUNS pill on the title three times) ----------
const TRACKS := ["menu", "game", "victory", "map", "race", "rpg", "boss", "finale", "unease", "dirge", "wrath", "vigil", "omen", "c_fiesta", "c_theft", "c_fall", "c_hero", "c_climb", "c_mission", "c_pursuit1", "c_pursuit2", "c_reckon", "c_armada", "c_showdown"]
const SONGS := ["menu", "game", "victory"]
const CUTSCENES := ["c_fiesta", "c_theft", "c_fall", "c_hero", "c_climb", "c_mission", "c_pursuit1", "c_pursuit2", "c_reckon", "c_armada", "c_showdown"]
const READY := SONGS + CUTSCENES
const TNAME := {"menu": "TITLE THEME", "game": "SHOOTER SONG", "victory": "VICTORY FANFARE"}
var cutscene_data: Dictionary = {}
var song_test_tab := 0  # 0 = songs, 1 = cutscenes

func _secret_tap() -> void:
	var now := Time.get_ticks_msec() / 1000.0
	sec_taps = sec_taps + 1 if now - sec_t < 1.5 else 1
	sec_t = now
	if sec_taps >= 3:
		sec_taps = 0; song_test = ""; sec_msg = ""; song_test_tab = 0; c.state = c.S.SECRET; c.snd.sfx("level")
		_load_cutscene_data()

func _load_cutscene_data() -> void:
	var f := FileAccess.open("res://data/data_cutscenes.json", FileAccess.READ)
	if f:
		var j = JSON.parse_string(f.get_as_text())
		if j and j.get("cutscenes") is Array:
			for cs in j["cutscenes"]:
				if cs.get("id"):
					cutscene_data[cs["id"]] = cs

func secret(R: float, t: float) -> void:
	var ox := (R - 640.0) / 2.0
	c.draw_rect(Rect2(0, 0, R, 360), Color(0.03, 0.03, 0.08, 0.85))
	txt(Vector2(ox + 16, 28), "SONG TEST", 18, Color("16a085"))
	var msg: String = ("now playing: " + TNAME.get(song_test, song_test)) if song_test != "" else (sec_msg if sec_msg != "" else "pick a track to hear it")
	txt(Vector2(ox + 150, 27), msg, 12, Color("ffd32a"))

	# tabs
	var tab_names := ["SONGS", "CUTSCENES"]
	for ti in 2:
		var tr := Rect2(ox + 14 + ti * 310, 10, 150, 20)
		var is_on := ti == song_test_tab
		c.buttons.append([tr, func(): song_test_tab = ti; song_test = ""; sec_msg = ""])
		rframe(tr, Color("ffd32a") if is_on else Color(1, 1, 1, 0.3), 1.5 if is_on else 1.0, 4)
		ctxt(tr.position.x + tr.size.x / 2.0, tr.position.y + 10, tab_names[ti], 11, Color("ffd32a") if is_on else Color(1, 1, 1, 0.6))

	var tracks_to_show := SONGS if song_test_tab == 0 else CUTSCENES
	for i in tracks_to_show.size():
		var k: String = tracks_to_show[i]
		var r := Rect2(ox + 14 + (i % 4) * 153, 44 + (i / 4) * 40, 150, 36)
		var ready := READY.has(k)
		var on := k == song_test
		var col := Color("16a085") if on else (Color("2d3a6b") if ready else Color(0.18, 0.2, 0.3, 0.7))
		c.buttons.append([r, func():
			if ready:
				song_test = k; c.snd.stop_music(); c.snd.start_music(k); c.snd.sfx("click")
			else:
				sec_msg = k + " isn't in the new version yet"])
		rrect(r, col, 7); rframe(r, Color("ffd32a") if on else Color(1, 1, 1, 0.3 if ready else 0.15), 2.0 if on else 1.2, 7)
		var label := TNAME.get(k, cutscene_data.get(k, {}).get("name", k.to_upper()))
		ctxt(r.position.x + r.size.x / 2.0, r.position.y + (21 if not ready else 16), label, 11, Color.WHITE if ready else Color(1, 1, 1, 0.4))
		if ready:
			var sub_text := "with vocals" if k == "victory" else (cutscene_data.get(k, {}).get("desc", "ready") if k.begins_with("c_") else "ready")
			ctxt(r.position.x + r.size.x / 2.0, r.position.y + 30, sub_text, 9, Color(1, 1, 1, 0.55))
	button(Rect2(ox + 14, 314, 164, 38), "STOP", Color("c0392b"), func(): song_test = ""; c.snd.stop_music(), 16)
	button(Rect2(ox + 190, 314, 164, 38), "BACK", Color("6c5ce7"), func(): song_test = ""; c.snd.stop_music(); c.state = c.S.MENU, 16)
