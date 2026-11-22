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
	button(Rect2(bxr, 64, 224, 60), "RIDE!", Color("2ecc71"), c.open_map, 30, "world map · 4 acts")
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
		["Gold earned (all time)", st.gold_all], ["Time in the sky", "%d:%02d" % [int(st.time) / 60, int(st.time) % 60]], ["Best run", "-" if st.best_run == 0 else str(int(st.best_run))],
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
	# legacy version switch (see scripts/legacy.gd and docs/legacy_checklist.md)
	var lr := Rect2(ox + 324, 260, 302, 48)
	var lon: bool = Legacy.on()
	c.buttons.append([lr, func(): Save.data.opt["legacy"] = not lon; Save.save()])
	rrect(lr, Color(0.12, 0.125, 0.22, 0.95), 10); rframe(lr, Color(1, 1, 1, 0.14), 1.2, 10)
	txt(lr.position + Vector2(10, 20), "Legacy version", 13, Color.WHITE)
	txt(lr.position + Vector2(10, 38), "Features ported from the HTML build", 10, Color("9aa3c7"), 180)
	var lsw := Rect2(lr.position.x + lr.size.x - 54, lr.position.y + 14, 42, 20)
	rrect(lsw, Color("2ecc71") if lon else Color("4a4f6e"), 10)
	c.draw_circle(Vector2(lsw.position.x + (32 if lon else 10), lsw.position.y + 10), 7.5, Color.WHITE)
	button(Rect2(ox + 14, 260, 302, 48), "CHECK FOR UPDATES", Color("3498db"), func(): c.snd.sfx("click"); Updater.check_for_updates(), 14)

# ---------- secret theater / song test (tap the RUNS pill on the title three times) ----------
const SONGS := ["menu", "game", "victory"]
const CUTSCENES := ["c_fiesta", "c_theft", "c_fall", "c_hero", "c_climb", "c_mission", "c_pursuit1", "c_pursuit2", "c_reckon", "c_armada", "c_showdown"]
const READY := SONGS + CUTSCENES
const TNAME := {"menu": "TITLE THEME", "game": "SHOOTER SONG", "victory": "VICTORY FANFARE"}
const STORY_LABELS := ["ACT 1 INTRO", "ACT 2 INTRO", "ACT 3 INTRO", "ACT 4 INTRO"]
var theater: Dictionary = {}       # data_theater.json: "acts" (4 intro lists) + "end" (28 ending scenes)
var scene_text: Dictionary = {}    # scene title -> narration caption
var cutscene_data: Dictionary = {}
var song_test_tab := 0  # 0=THEATER, 1=SONGS, 2=MUSICAL, 3=TIMING
# ---- word timing editor (TIMING tab). Onsets are seconds into each sung line; edits are saved
# on the phone and copied to the PC with tools/retime.py, which re-sings the changed lines.
# IPA and per-phone lengths are edited here too; until a re-sing, PLAY sketches them with the
# phoneme bank (audio/phon + data_phon_bank.json) instead of the shipped line clip.
const TIMING_GAP := 0.02
var timing: Dictionary = {}       # line id -> {words, onsets, ipa, phones, ...}
var timing_base: Dictionary = {}  # the shipped defaults, for RESET
var timing_order: Array = []
var timing_sel := "B0"
var timing_msg := ""
var phonics: Dictionary = {}      # data_phonics.json "words"
var phon_bank: Dictionary = {}    # data_phon_bank.json "phones" (palette + natural lengths)
var di_bank: Dictionary = {}      # data_diphone_bank.json "pairs": p1|p2 -> start/dur
var timing_word := -1             # selected word for the detail editor, -1 = graph
var timing_phone := 0             # selected phone inside that word
var timing_playhead := 0.0        # seconds into the selected line (graph click)
var timing_show_vox := true
var timing_show_inst := true
var timing_show_notes := true

func _secret_tap() -> void:
	var now := Time.get_ticks_msec() / 1000.0
	sec_taps = sec_taps + 1 if now - sec_t < 1.5 else 1
	sec_t = now
	if sec_taps >= 3:
		sec_taps = 0; song_test = ""; sec_msg = ""; song_test_tab = 0; c.state = c.S.SECRET; c.snd.sfx("level")
		_load_theater_data()

func _read_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null: return {}
	var j = JSON.parse_string(f.get_as_text())
	return j if j is Dictionary else {}

func _load_theater_data() -> void:
	theater = _read_json("res://data/data_theater.json")
	scene_text.clear()
	for list in theater.get("acts", []) + [theater.get("end", [])]:
		for item in list:
			scene_text[item["title"]] = item.get("text", "")
	var cs: Dictionary = _read_json("res://data/data_cutscenes.json").get("data", {})
	cutscene_data.clear()
	for cs_id in cs:
		var names: Array = (cs[cs_id] as Dictionary).keys()
		cutscene_data[cs_id] = {"id": cs_id, "scenes": names, "first_scene": names[0] if names.size() > 0 else ""}

func _play_list(items: Array, from := 0) -> void:
	if items.is_empty() or not c.cutscene: return
	song_test = ""; sec_msg = ""
	c.snd.sfx("click")
	c.cutscene.play_list(c.snd, c.hero3d, c, items, from)

func _play_cutscene_id(cs_id: String) -> void:
	var items: Array = []
	for scene_name in cutscene_data.get(cs_id, {}).get("scenes", []):
		items.append({"title": scene_name, "text": scene_text.get(scene_name, ""), "cs": cs_id})
	_play_list(items, 0)

func _timing_load() -> void:
	phonics = _read_json("res://data/data_phonics.json").get("words", {})
	var bank: Dictionary = _read_json("res://data/data_phon_bank.json")
	phon_bank = bank.get("phones", {})
	di_bank = _read_json("res://data/data_diphone_bank.json").get("pairs", {})
	var base: Dictionary = _read_json("res://data/data_word_timing.json")
	timing_order = base.get("order", [])
	timing_base = base.get("lines", {}).duplicate(true)
	for lid in timing_base:
		_timing_defaults(lid, timing_base[lid])
	timing = timing_base.duplicate(true)
	var saved: Dictionary = _read_json("user://word_timing.json").get("lines", {})
	for lid in saved:
		if timing.has(lid):
			for k in ["onsets", "ipa", "phones"]:
				if saved[lid].get(k) is Array:
					timing[lid][k] = (saved[lid][k] as Array).duplicate(true)
	for lid in timing:
		_timing_clamp_onsets(lid)

# IPA for one word: data_phonics.json when it has the word, else the written word.
func _timing_word_ipa(w: String) -> String:
	var key := w.strip_edges().to_lower().replace(",", "").replace(".", "").replace("'", "'")
	var e: Dictionary = phonics.get(key, {})
	var ipa := String(e.get("ipa", ""))
	return ipa if ipa != "" else key

# Split IPA into editable phones. Stress marks ride on the phone after them ("m") and length marks on
# the phone before them ("x"), so the IPA string and the Piper input keep them: dropping stress makes
# the singer mumble. A length mark also stretches the phone's default length.
func _timing_split_ipa(ipa: String) -> Array:
	var out: Array = []
	var mark := ""
	for ch in ipa:
		if ch in [".", "/", " "]:
			continue
		if ch == "ˈ" or ch == "ˌ":
			mark += ch
			continue
		if ch == "ː" or ch == "ˑ":
			if out.size() > 0:
				var last: Dictionary = out[out.size() - 1]
				last["d"] = minf(1.5, float(last.get("d", 0.12)) * 1.6)
				last["x"] = String(last.get("x", "")) + ch
			continue
		var natural := 0.12
		if phon_bank.has(ch):
			natural = float((phon_bank[ch] as Dictionary).get("dur", 0.12))
		var ph := {"p": ch, "d": clampf(natural, 0.03, 0.45)}
		if mark != "":
			ph["m"] = mark
			mark = ""
		out.append(ph)
	if out.is_empty():
		out.append({"p": "ə", "d": 0.12})
	return out

func _timing_defaults(lid: String, line: Dictionary) -> void:
	var words: Array = line.get("words", [])
	var ipa: Array = line.get("ipa", [])
	if ipa.size() != words.size():
		ipa = []
		for w in words:
			ipa.append(_timing_word_ipa(String(w)))
		line["ipa"] = ipa
	var phones: Array = line.get("phones", [])
	if phones.size() != words.size():
		phones = []
		var onsets: Array = line.get("onsets", [])
		var vein := 0.105
		var line_len := float(line.get("bars", 2)) * 16.0 * vein
		for i in ipa.size():
			var ph := _timing_split_ipa(String(ipa[i]))
			# default word length: the gap to the next word, capped; the last word is short
			var target := 0.5
			if i + 1 < onsets.size():
				target = clampf(float(onsets[i + 1]) - float(onsets[i]), 0.12, 0.7)
			elif i < onsets.size():
				target = clampf(line_len - float(onsets[i]), 0.2, 0.5)
			var total := 0.0
			for p in ph:
				total += float(p.get("d", 0.12))
			if total > 0.0:
				for p in ph:
					p["d"] = maxf(0.03, float(p.get("d", 0.12)) / total * target)
			phones.append(ph)
		line["phones"] = phones

func _timing_word_len(lid: String, i: int) -> float:
	var line: Dictionary = timing.get(lid, {})
	var phones_all: Array = line.get("phones", [])
	if i < 0 or i >= phones_all.size():
		return 0.0
	var total := 0.0
	for ph in phones_all[i]:
		total += float(ph.get("d", 0.0))
	return total

func _timing_nudge(lid: String, i: int, d: float) -> void:
	var on: Array = timing[lid]["onsets"]
	var b := _timing_onset_bounds(lid, i)
	on[i] = snappedf(clampf(float(on[i]) + d, b.x, b.y), 0.01)
	timing_msg = ""

# The line's span on the graph and in PLAY: the shipped line is bars * 16 steps. A word past it
# is drawn off the graph and PLAY stops before it, so onsets stay inside the line.
func _timing_line_len(lid: String) -> float:
	return float((timing.get(lid, {}) as Dictionary).get("bars", 2)) * 16.0 * c.snd.VE

# allowed [min, max] for word i's onset: after the previous word, and early enough that the word
# still starts inside the line (its last 0.1 s may fall off the end, its start may not)
func _timing_onset_bounds(lid: String, i: int) -> Vector2:
	var on: Array = timing[lid]["onsets"]
	var lo := 0.0 if i == 0 else float(on[i - 1]) + TIMING_GAP
	var hi := (_timing_line_len(lid) - 0.1) if i + 1 >= on.size() else float(on[i + 1]) - TIMING_GAP
	return Vector2(lo, maxf(lo, hi))

func _timing_clamp_onsets(lid: String) -> void:
	var on: Array = timing[lid].get("onsets", [])
	for i in on.size():
		var b := _timing_onset_bounds(lid, i)
		on[i] = clampf(float(on[i]), b.x, b.y)

func _timing_payload() -> Dictionary:
	var out := {}
	for lid in timing:
		out[lid] = timing[lid].duplicate(true)
	return {"lines": out}

func _timing_save() -> void:
	var f := FileAccess.open("user://word_timing.json", FileAccess.WRITE)
	if f == null:
		timing_msg = "could not save on this phone"; return
	f.store_string(JSON.stringify(_timing_payload(), "  "))
	timing_msg = "saved on this phone"

func _timing_copy() -> void:
	DisplayServer.clipboard_set(JSON.stringify(_timing_payload(), "  "))
	timing_msg = "copied: paste it into the chat"

func _timing_reset(lid: String) -> void:
	if timing_base.has(lid):
		timing[lid] = (timing_base[lid] as Dictionary).duplicate(true)
		timing_word = -1
		timing_phone = 0
		timing_playhead = 0.0
		timing_msg = "reset %s (press SAVE to keep it on this phone)" % lid

# ---- per-word IPA and phone-length editing
func _timing_sync_ipa() -> void:
	if timing_word < 0: return
	var line: Dictionary = timing.get(timing_sel, {})
	var ipa: Array = line.get("ipa", [])
	var phones_all: Array = line.get("phones", [])
	if timing_word >= ipa.size() or timing_word >= phones_all.size(): return
	var s := ""
	for ph in phones_all[timing_word]:
		s += String(ph.get("m", "")) + String(ph.get("p", "")) + String(ph.get("x", ""))
	ipa[timing_word] = s

func _timing_word_reset() -> void:
	if timing_word < 0: return
	var line: Dictionary = timing[timing_sel]
	var base: Dictionary = timing_base.get(timing_sel, {})
	var ipa: Array = line.get("ipa", [])
	var phones: Array = line.get("phones", [])
	var bipa: Array = base.get("ipa", [])
	var bphones: Array = base.get("phones", [])
	if timing_word < bipa.size():
		ipa[timing_word] = String(bipa[timing_word])
	if timing_word < bphones.size():
		phones[timing_word] = (bphones[timing_word] as Array).duplicate(true)
	timing_msg = "word reset"

func _timing_phone_set(p: String) -> void:
	if timing_word < 0: return
	var line: Dictionary = timing[timing_sel]
	var phones_all: Array = line.get("phones", [])
	if timing_word >= phones_all.size(): return
	var phones: Array = phones_all[timing_word]
	if phones.is_empty() or timing_phone < 0 or timing_phone >= phones.size():
		phones.append({"p": p, "d": 0.12})
		timing_phone = phones.size() - 1
	else:
		(phones[timing_phone] as Dictionary)["p"] = p
	_timing_sync_ipa()
	timing_msg = ""

func _timing_phone_dur(d: float) -> void:
	if timing_word < 0: return
	var line: Dictionary = timing[timing_sel]
	var phones_all: Array = line.get("phones", [])
	if timing_word >= phones_all.size(): return
	var phones: Array = phones_all[timing_word]
	if timing_phone < 0 or timing_phone >= phones.size(): return
	var ph: Dictionary = phones[timing_phone]
	ph["d"] = snappedf(clampf(float(ph.get("d", 0.12)) + d, 0.03, 1.5), 0.01)
	timing_msg = ""

func _timing_phone_del() -> void:
	if timing_word < 0: return
	var line: Dictionary = timing[timing_sel]
	var phones_all: Array = line.get("phones", [])
	if timing_word >= phones_all.size(): return
	var phones: Array = phones_all[timing_word]
	if timing_phone >= 0 and timing_phone < phones.size():
		phones.remove_at(timing_phone)
	timing_phone = clampi(timing_phone, 0, maxi(0, phones.size() - 1))
	_timing_sync_ipa()
	timing_msg = ""

func _timing_phone_add() -> void:
	if timing_word < 0: return
	var line: Dictionary = timing[timing_sel]
	var phones_all: Array = line.get("phones", [])
	if timing_word >= phones_all.size(): return
	var phones: Array = phones_all[timing_word]
	phones.append({"p": "ə", "d": 0.1})
	timing_phone = phones.size() - 1
	_timing_sync_ipa()
	timing_msg = "tap a symbol to replace it"

func _timing_is_sketch(lid: String) -> bool:
	var b: Dictionary = timing_base.get(lid, {})
	var t: Dictionary = timing.get(lid, {})
	return (JSON.stringify(t.get("ipa", [])) != JSON.stringify(b.get("ipa", []))
		or JSON.stringify(t.get("phones", [])) != JSON.stringify(b.get("phones", []))
		or JSON.stringify(t.get("onsets", [])) != JSON.stringify(b.get("onsets", [])))

# Preview with the edited timing. Unedited lines play the shipped clip; once the IPA, phone
# lengths or onsets differ, PLAY uses the phoneme bank so the edit is heard immediately (sketch
# voice). Retiming is relative to timing_playhead, set by tapping the graph. The clip starts
# 0.15 s before its first word (data_vox.json lead-in).
const VOX_LEAD := 0.15

func _timing_play(lid: String) -> void:
	var line: Dictionary = timing.get(lid, {})
	var onsets: Array = line.get("onsets", [])
	var sec := String(line.get("section", "v-B"))
	var bar := int(line.get("bar", 0))
	var row: int = c.snd.victory_row_of(sec, bar)
	if row < 0:
		timing_msg = "no chorus bar for %s" % lid; return
	var vein: float = c.snd.VE
	var line_len: float = float(line.get("bars", 2)) * 16.0 * vein
	var head := clampf(timing_playhead, 0.0, maxf(0.0, line_len - 0.05))
	# the track starts at this line's bar (and the playhead's step); the sequencer's own vocals are off
	c.snd.have_vox = false
	c.snd.start_victory_at(row, int(head / vein))
	var to_downbeat: float = c.snd.next_t - c.snd.now
	timing_play_t0 = c.snd.now + to_downbeat - head
	timing_play_len = line_len
	timing_play_id += 1
	var my_id := timing_play_id
	c.snd.later.append([c.snd.now + to_downbeat + (line_len - head), func(): if timing_play_id == my_id: _timing_stop()])
	if not _timing_is_sketch(lid):
		c.snd.play("vox/" + lid, {"v": 2.4, "dl": to_downbeat, "from": VOX_LEAD + head,
			"dur": maxf(0.05, line_len - head + VOX_LEAD)})
		return
	# Edited line: exact preview with the embedded Piper when present; diphone bank otherwise;
	# real-clip word slices last. The shipped lines play the shipped clip.
	var w_ph: Array = line.get("phones", [])
	if PiperVoice.available():
		_timing_play_piper(lid, head, to_downbeat, line_len)
		return
	# The diphone bank stitches 2-phone renders and still reads as gibberish (a speech recogniser
	# hears nothing in it), so it is off. Without the Piper build, an edited line plays the real
	# clip at the edited onsets; IPA and phone lengths are heard after a re-sing (COPY, retime.py).
	timing_msg = "real clip at your onsets; IPA/length: COPY + retime.py, or the Piper build"
	if not DIPHONE_PREVIEW or di_bank.is_empty():
		var shipped: Array = timing_base.get(lid, {}).get("onsets", [])
		for i in shipped.size():
			if i >= onsets.size(): break
			var at := float(onsets[i])
			if at < head - 0.001: continue
			var dur := float(onsets[i + 1]) - at if i + 1 < onsets.size() else maxf(0.05, line_len - at)
			c.snd.play("vox/" + lid, {"v": 2.4, "dl": to_downbeat + at - head,
				"from": VOX_LEAD + maxf(float(shipped[i]), head), "dur": maxf(0.05, dur)})
		return
	for i in onsets.size():
		if i >= w_ph.size(): break
		var t := float(onsets[i]) - head
		var phs: Array = w_ph[i]
		for j in phs.size():
			var p := String((phs[j] as Dictionary).get("p", "ə"))
			var nx := String((phs[j + 1] as Dictionary).get("p", p)) if j + 1 < phs.size() else p
			var d := float((phs[j] as Dictionary).get("d", 0.12))
			if t >= -0.001 and di_bank.has(p + "|" + nx):
				var e: Dictionary = di_bank[p + "|" + nx]
				c.snd.play("di_bank", {"v": 1.8, "dl": to_downbeat + maxf(0.0, t),
					"from": float(e.get("start", 0.0)), "dur": maxf(0.04, d) + 0.02, "bus": "Vox"})
			t += d

const DIPHONE_PREVIEW := false   # see _timing_play: the stitched preview is unintelligible
var timing_play_id := 0   # bumped by PLAY and STOP, so a stale end-of-line stop does nothing

var piper_cache := {}   # "lid_i_<ipa>" -> AudioStreamWAV from the embedded Piper

# Exact on-device preview: edited words are rendered by the embedded Piper, unchanged words
# play the shipped clip, so the line keeps the real voice where the user did not edit.
func _timing_play_piper(lid: String, head: float, to_downbeat: float, line_len: float) -> void:
	timing_msg = PiperVoice.status()   # shows whether Piper is really running, not just present
	var base: Dictionary = timing_base.get(lid, {})
	var shipped: Array = base.get("onsets", [])
	var bipa: Array = base.get("ipa", [])
	var bph: Array = base.get("phones", [])
	var line: Dictionary = timing.get(lid, {})
	var ipa: Array = line.get("ipa", [])
	var w_ph: Array = line.get("phones", [])
	var onsets: Array = line.get("onsets", [])
	for i in onsets.size():
		var at := float(onsets[i])
		if at < head - 0.001: continue
		var dur: float = float(onsets[i + 1]) - at if i + 1 < onsets.size() else maxf(0.05, line_len - at)
		var edited: bool = i < w_ph.size() and (i >= bipa.size() or String(ipa[i]) != String(bipa[i])
			or JSON.stringify(w_ph[i]) != JSON.stringify(bph[i]))
		var st: AudioStreamWAV = _piper_word(lid, i) if edited else null
		if edited and st == null:
			timing_msg = "%s  Piper gave no audio for '%s': real clip used" % [PiperVoice.status(), ipa[i]]
		if st != null:
			dur = maxf(0.05, _timing_word_len(lid, i))
			c.snd.play_stream(st, {"v": 2.4, "dl": to_downbeat + at - head, "dur": dur, "bus": "Vox"})
		elif i < shipped.size():
			c.snd.play("vox/" + lid, {"v": 2.4, "dl": to_downbeat + at - head,
				"from": VOX_LEAD + maxf(float(shipped[i]), head), "dur": maxf(0.05, dur)})

func _piper_word(lid: String, i: int) -> AudioStreamWAV:
	var ipa := String((timing[lid].get("ipa", []) as Array)[i]) if i < (timing[lid].get("ipa", []) as Array).size() else ""
	if ipa.is_empty(): return null
	var key := "%s_%d_%s" % [lid, i, ipa]
	if piper_cache.has(key):
		return piper_cache[key]
	var st := PiperVoice.sing_stream(ipa)
	if st != null:
		piper_cache[key] = st
	return st

# A/B: play the shipped line exactly as it is today, ignoring every edit.
func _timing_play_before(lid: String) -> void:
	var base: Dictionary = timing_base.get(lid, {})
	var sec := String(base.get("section", "v-B"))
	var bar := int(base.get("bar", 0))
	var row: int = c.snd.victory_row_of(sec, bar)
	if row < 0:
		timing_msg = "no chorus bar for %s" % lid; return
	var line_len: float = float(base.get("bars", 2)) * 16.0 * c.snd.VE
	c.snd.have_vox = false
	c.snd.start_victory_at(row)
	var to_downbeat: float = c.snd.next_t - c.snd.now
	timing_play_t0 = c.snd.now + to_downbeat
	timing_play_len = line_len
	timing_play_id += 1
	var my_id := timing_play_id
	c.snd.later.append([c.snd.now + to_downbeat + line_len, func(): if timing_play_id == my_id: _timing_stop()])
	c.snd.play("vox/" + lid, {"v": 2.4, "dl": to_downbeat, "from": VOX_LEAD, "dur": line_len + VOX_LEAD})
	timing_msg = "BEFORE: shipped %s" % lid

func _timing_stop() -> void:
	timing_play_id += 1
	timing_play_t0 = -1.0
	c.snd.stop_vox(); c.snd.stop_music(); c.snd.have_vox = true

# Sound graph under the word rows: the sung clip (yellow) over the instruments (blue) for the same
# stretch of the track, from data/data_line_env.json (tools/line_env.py). White ticks are the shipped
# word onsets; green ticks are the edited ones, so a move shows against the instruments before PLAY.
var line_env: Dictionary = {}
# graph markers (drag the green onset ticks): [Rect2, lid, word index], rebuilt every draw
var timing_markers: Array = []
var timing_graph_rect := Rect2()
var timing_graph_dur := 1.0
var timing_drag_index := -1   # touch index of the finger dragging a marker, -1 = none
var timing_drag_lid := ""
var timing_drag_word := -1
var timing_drag_x := 0.0
# playhead: sound time at which the clip starts (-1 = not playing), and the clip length in seconds
var timing_play_t0 := -1.0
var timing_play_len := 0.0

func timing_grab(pos: Vector2, idx: int) -> bool:
	if timing_menu_open or timing_word >= 0: return false
	for m in timing_markers:
		if (m[0] as Rect2).has_point(pos):
			timing_drag_index = idx; timing_drag_lid = m[1]; timing_drag_word = m[2]; timing_drag_x = pos.x
			return true
	if timing_graph_rect.size.x > 0.0 and timing_graph_rect.has_point(pos):
		var frac := (pos.x - timing_graph_rect.position.x) / timing_graph_rect.size.x
		timing_playhead = clampf(frac, 0.0, 1.0) * timing_graph_dur
		timing_msg = "start %.2f s" % timing_playhead
		return true
	return false

# move the grabbed onset by the finger's travel, kept between its neighbours (no rounding while dragging)
func timing_move(x: float) -> void:
	if timing_drag_index < 0 or timing_graph_rect.size.x <= 0.0: return
	var on: Array = timing[timing_drag_lid]["onsets"]
	var i := timing_drag_word
	var b := _timing_onset_bounds(timing_drag_lid, i)
	on[i] = clampf(float(on[i]) + (x - timing_drag_x) / timing_graph_rect.size.x * timing_graph_dur, b.x, b.y)
	timing_drag_x = x
	timing_msg = "at the end of the line" if float(on[i]) >= b.y - 0.001 and i + 1 >= on.size() else ""

func timing_release() -> void:
	if timing_drag_index >= 0 and timing.has(timing_drag_lid):
		var on: Array = timing[timing_drag_lid]["onsets"]
		on[timing_drag_word] = snappedf(float(on[timing_drag_word]), 0.01)
	timing_drag_index = -1
func _timing_notes(lid: String) -> Array:
	var line: Dictionary = timing.get(lid, {})
	var sec := String(line.get("section", "v-B"))
	var bar := int(line.get("bar", 0))
	var row: int = c.snd.victory_row_of(sec, bar)
	if row < 0 or row >= c.snd.vic.size():
		return []
	var notes = c.snd.vic[row][3]
	return notes if notes is Array else []

func _draw_timing_graph(ox: float, lid: String) -> void:
	if line_env.is_empty(): line_env = _read_json("res://data/data_line_env.json").get("lines", {})
	var r := Rect2(ox + 14, 220, 612, 76)
	rrect(r, Color(0, 0, 0, 0.3), 6)
	var e: Dictionary = line_env.get(lid, {})
	var line: Dictionary = timing.get(lid, {})
	var dur := maxf(0.5, float(line.get("bars", 2)) * 16.0 * c.snd.VE)
	var vy := r.position.y + 20
	if timing_show_notes:
		var lane := Rect2(r.position.x, r.position.y + 1, r.size.x, 17)
		c.draw_rect(lane, Color(0.06, 0.06, 0.12, 0.6))
		var notes: Array = _timing_notes(lid)
		if not notes.is_empty():
			var lo := 127
			var hi := 0
			for n in notes:
				if int(n) >= 0:
					lo = mini(lo, int(n)); hi = maxi(hi, int(n))
			if hi <= lo: hi = lo + 1
			var bw := lane.size.x / float(notes.size())
			for k in notes.size():
				if int(notes[k]) < 0: continue
				var ny := lane.position.y + lane.size.y - 2.0 - (int(notes[k]) - lo) / float(hi - lo) * (lane.size.y - 5.0)
				c.draw_rect(Rect2(lane.position.x + k * bw + 1, ny, maxf(1.0, bw - 2), 3), Color("f5f5f5"))
		ctxt(lane.position.x + 30, lane.position.y + 12, "NOTES", 9, Color(1, 1, 1, 0.35))
	if timing_show_vox:
		_draw_env_strip(e, "vox", Color("ffd32a"), Rect2(r.position.x, vy, r.size.x, 26), dur)
	if timing_show_inst:
		_draw_env_strip(e, "inst", Color("3498db"), Rect2(r.position.x, vy + 28, r.size.x, 26), dur)
	# word blocks over the vocal strip, using the edited onsets and phone lengths
	var onsets: Array = line.get("onsets", [])
	var ipa: Array = line.get("ipa", [])
	for i in onsets.size():
		var x0 := r.position.x + float(onsets[i]) / dur * r.size.x
		var x1 := r.position.x + (float(onsets[i]) + _timing_word_len(lid, i)) / dur * r.size.x
		var wbox := Rect2(x0, vy + 1, maxf(2.0, x1 - x0), 24)
		c.draw_rect(wbox, Color(1, 1, 1, 0.10))
		c.draw_rect(Rect2(wbox.position, Vector2(2, wbox.size.y)), Color("ffd32a"))
		if i < ipa.size() and wbox.size.x > 26:
			txt(Vector2(wbox.position.x + 3, wbox.position.y + 16), String(ipa[i]), 10, Color(1, 1, 1, 0.8))
	# playhead from the graph click, and the moving one while PLAY runs
	var hx := r.position.x + timing_playhead / dur * r.size.x
	c.draw_line(Vector2(hx, r.position.y), Vector2(hx, r.position.y + r.size.y), Color(1, 1, 1, 0.85), 1.5)
	if timing_play_t0 >= 0.0 and c.snd.now >= timing_play_t0 and c.snd.now <= timing_play_t0 + dur:
		var px := r.position.x + clampf((c.snd.now - timing_play_t0) / dur, 0.0, 1.0) * r.size.x
		c.draw_line(Vector2(px, r.position.y), Vector2(px, r.position.y + r.size.y), Color("e74c3c"), 2.0)
	var base: Array = timing_base.get(lid, {}).get("onsets", [])
	var edited: Array = line.get("onsets", [])
	# shipped onsets as faint ghosts, so BEFORE and NOW line up visually
	for i in base.size():
		var bx := r.position.x + float(base[i]) / dur * r.size.x
		c.draw_line(Vector2(bx, r.position.y), Vector2(bx, r.position.y + r.size.y), Color(1, 1, 1, 0.28), 1.0)
	for i in base.size():
		if i >= edited.size(): break
		var x := r.position.x + float(edited[i]) / dur * r.size.x
		c.draw_line(Vector2(x, r.position.y), Vector2(x, r.position.y + r.size.y), Color("2ecc71"), 2.0)
		timing_markers.append([Rect2(x - 14, r.position.y, 28, r.size.y), lid, i])
	timing_graph_rect = r; timing_graph_dur = dur

func _draw_env_strip(e: Dictionary, key: String, col: Color, rr: Rect2, dur: float) -> void:
	c.draw_rect(rr, Color(0, 0, 0, 0.25))
	if e.is_empty(): return
	var vals: Array = e.get(key, [])
	if vals.is_empty(): return
	var bw := rr.size.x / maxf(1.0, float(vals.size()))
	for k in vals.size():
		var h := float(vals[k]) * rr.size.y
		c.draw_rect(Rect2(rr.position.x + k * bw, rr.position.y + rr.size.y - h, maxf(1.0, bw), h), col)
	var env_dur := maxf(0.01, float(e.get("dur", 1.0)))
	var x := rr.position.x + clampf(dur / env_dur, 0.0, 1.0) * rr.size.x
	if dur < env_dur:
		c.draw_rect(Rect2(x, rr.position.y, rr.size.x - (x - rr.position.x), rr.size.y), Color(0, 0, 0, 0.55))

var timing_menu_open := false   # line picker (drop-down) is showing
func _timing_pick(lid: String) -> void:
	timing_sel = lid; timing_msg = ""; timing_menu_open = false
	timing_word = -1; timing_phone = 0; timing_playhead = 0.0

func _timing_next() -> void:
	var n := timing_order.size()
	if n == 0: return
	_timing_pick(timing_order[(timing_order.find(timing_sel) + 1) % n])

func _draw_toggle(r: Rect2, label: String, on: bool, fn: Callable) -> void:
	c.buttons.append([r, fn])
	rrect(r, Color("16a085") if on else Color("2d3a6b"), 5)
	ctxt(r.position.x + r.size.x / 2.0, r.position.y + 12, label, 9, Color.WHITE)

func _draw_timing(ox: float) -> void:
	if timing.is_empty(): _timing_load()
	timing_markers.clear()
	if timing_msg != "": txt(Vector2(ox + 14, 50), timing_msg, 11, Color("ffd32a"))   # status (saved, copied, reset) only
	var bld := int(Updater.build)
	txt(Vector2(ox + 552, 50), ("BUILD %d" % bld) if bld > 0 else "DEV BUILD", 10, Color(1, 1, 1, 0.45))
	# line box, left of the first word: tap to open the line picker
	var box := Rect2(ox + 14, 96, 110, 54)
	c.buttons.append([box, func(): timing_menu_open = not timing_menu_open])
	rrect(box, Color("2d3a6b"), 8); rframe(box, Color("ffd32a"), 1.5, 8)
	ctxt(box.position.x + box.size.x / 2.0, box.position.y + 20, "LINE", 10, Color(1, 1, 1, 0.6))
	ctxt(box.position.x + box.size.x / 2.0, box.position.y + 42, "%s  v" % timing_sel, 16, Color.WHITE)
	if not timing_menu_open:
		var nx := Rect2(ox + 14, 156, 110, 26)
		c.buttons.append([nx, func(): _timing_next()])
		rrect(nx, Color("16a085"), 8); rframe(nx, Color(1, 1, 1, 0.3), 1.0, 8)
		ctxt(nx.position.x + nx.size.x / 2.0, nx.position.y + 18, "NEXT LINE >", 12, Color.WHITE)
	var line: Dictionary = timing.get(timing_sel, {})
	var words: Array = line.get("words", [])
	var onsets: Array = line.get("onsets", [])
	var ipa: Array = line.get("ipa", [])
	if timing_word >= 0 and timing_word < words.size():
		_draw_timing_word(ox, line)
		_draw_timing_palette(ox)
	else:
		timing_word = -1
		# words, to the right of the box: five per row; tap one to edit its IPA and lengths
		for i in mini(words.size(), onsets.size()):
			var x := ox + 134 + (i % 5) * 100
			var y := 96 + (i / 5) * 50
			var idx := i
			var wbox := Rect2(x, y, 96, 46)
			c.buttons.append([wbox, func(): timing_word = idx; timing_phone = 0; timing_playhead = float(onsets[idx])])
			rrect(wbox, Color(0.12, 0.16, 0.3, 0.85), 6)
			rframe(wbox, Color("ffd32a"), 1.0, 6)
			txt(Vector2(x + 4, y + 15), "%s  %.2f" % [words[i], float(onsets[i])], 12, Color.WHITE)
			if i < ipa.size():
				txt(Vector2(x + 4, y + 33), String(ipa[i]), 11, Color(1, 1, 1, 0.7))
		_draw_toggle(Rect2(ox + 14, 200, 54, 16), "VOX", timing_show_vox, func(): timing_show_vox = not timing_show_vox)
		_draw_toggle(Rect2(ox + 72, 200, 54, 16), "INST", timing_show_inst, func(): timing_show_inst = not timing_show_inst)
		_draw_toggle(Rect2(ox + 130, 200, 60, 16), "NOTES", timing_show_notes, func(): timing_show_notes = not timing_show_notes)
		_draw_timing_graph(ox, timing_sel)
	var play_lid := timing_sel
	button(Rect2(ox + 14, 300, 140, 36), "PLAY", Color("e67e22"), func(): _timing_play(play_lid), 14)
	button(Rect2(ox + 164, 300, 140, 36), "STOP", Color("c0392b"), func(): _timing_stop(), 14)
	button(Rect2(ox + 314, 300, 140, 36), "COPY", Color("16a085"), func(): _timing_copy(), 14)
	button(Rect2(ox + 464, 300, 140, 36), "SAVE", Color("6c5ce7"), func(): _timing_save(), 14)
	# A/B and reset line
	var ab_lid := timing_sel
	button(Rect2(ox + 14, 340, 140, 16), "BEFORE", Color("7f8c8d"), func(): _timing_play_before(ab_lid), 10)
	button(Rect2(ox + 164, 340, 140, 16), "CURRENT", Color("e67e22"), func(): _timing_play(ab_lid), 10)
	button(Rect2(ox + 314, 340, 140, 16), "RESET LINE", Color("c0392b"), func(): _timing_reset(ab_lid), 10)

	# line picker: 3 columns so 16 lines fit above the buttons; drawn last over everything
	if timing_menu_open:
		var rows := int(ceil(timing_order.size() / 3.0))
		var panel := Rect2(ox + 14, 100, 612, 30 * rows + 6)
		rrect(panel, Color(0.05, 0.05, 0.12, 0.97), 8); rframe(panel, Color("ffd32a"), 1.5, 8)
		for k in timing_order.size():
			var lid: String = timing_order[k]
			var lw: Array = timing.get(lid, {}).get("words", [])
			var col := k / rows
			var rowi := k % rows
			var r := Rect2(ox + 20 + col * 202, 104 + rowi * 30, 194, 26)
			var on := lid == timing_sel
			c.buttons.append([r, func(): _timing_pick(lid)])
			rrect(r, Color("16a085") if on else Color("2d3a6b"), 6); rframe(r, Color(1, 1, 1, 0.3), 1.0, 6)
			txt(Vector2(r.position.x + 6, r.position.y + 17), "%s  %s" % [lid, " ".join(PackedStringArray(lw))], 11, Color.WHITE)

# word detail: IPA phones as tappable chips; length buttons under them
func _draw_timing_word(ox: float, line: Dictionary) -> void:
	var words: Array = line.get("words", [])
	var ipa: Array = line.get("ipa", [])
	var phones_all: Array = line.get("phones", [])
	if timing_word < 0 or timing_word >= phones_all.size(): return
	var phones: Array = phones_all[timing_word]
	timing_phone = clampi(timing_phone, 0, maxi(0, phones.size() - 1))
	var panel := Rect2(ox + 134, 96, 492, 100)
	rrect(panel, Color(0.08, 0.1, 0.2, 0.95), 8); rframe(panel, Color("e67e22"), 1.2, 8)
	var ipa_now := String(ipa[timing_word]) if timing_word < ipa.size() else ""
	txt(Vector2(panel.position.x + 8, panel.position.y + 16),
		"%s  IPA %s   LEN %.2f s" % [String(words[timing_word]), ipa_now, _timing_word_len(timing_sel, timing_word)],
		12, Color.WHITE)
	var x := panel.position.x + 8
	for k in phones.size():
		var ph: Dictionary = phones[k]
		var label := "%s %d" % [String(ph.get("p", "ə")), int(round(float(ph.get("d", 0.12)) * 1000.0))]
		var w := maxf(40, 12.0 + label.length() * 7.0)
		if x + w > panel.position.x + panel.size.x - 8: break
		var idx := k
		var cr := Rect2(x, panel.position.y + 24, w, 26)
		c.buttons.append([cr, func(): timing_phone = idx])
		rrect(cr, Color("16a085") if k == timing_phone else Color("2d3a6b"), 5)
		rframe(cr, Color("ffd32a") if k == timing_phone else Color(1, 1, 1, 0.25), 1.0, 5)
		ctxt(cr.position.x + cr.size.x / 2.0, cr.position.y + 17, label, 10, Color.WHITE)
		x += w + 4
	var by := panel.position.y + 58
	var bw := 74.0
	button(Rect2(panel.position.x + 8, by, bw, 26), "-20 ms", Color("c0392b"), func(): _timing_phone_dur(-0.02), 11)
	button(Rect2(panel.position.x + 8 + bw + 4, by, bw, 26), "+20 ms", Color("16a085"), func(): _timing_phone_dur(0.02), 11)
	button(Rect2(panel.position.x + 8 + (bw + 4) * 2, by, bw, 26), "DEL", Color("7f8c8d"), func(): _timing_phone_del(), 11)
	button(Rect2(panel.position.x + 8 + (bw + 4) * 3, by, bw, 26), "ADD", Color("2980b9"), func(): _timing_phone_add(), 11)
	button(Rect2(panel.position.x + 8 + (bw + 4) * 4, by, bw, 26), "RESET", Color("8e44ad"), func(): _timing_word_reset(), 11)
	button(Rect2(panel.position.x + 8 + (bw + 4) * 5, by, bw, 26), "DONE", Color("6c5ce7"), func(): timing_word = -1, 11)

# IPA palette: every phoneme in the bank, two rows; tap replaces the selected phone
func _draw_timing_palette(ox: float) -> void:
	var keys: Array = phon_bank.keys()
	var panel := Rect2(ox + 14, 220, 612, 74)
	rrect(panel, Color(0.05, 0.05, 0.12, 0.9), 6)
	txt(Vector2(panel.position.x + 6, panel.position.y + 12), "TAP A SYMBOL TO REPLACE THE SELECTED PHONE", 9, Color(1, 1, 1, 0.5))
	for k in keys.size():
		var col := k % 20
		var rowi := k / 20
		var r := Rect2(panel.position.x + 6 + col * 30, panel.position.y + 18 + rowi * 27, 28, 24)
		var key := String(keys[k])
		c.buttons.append([r, func(): _timing_phone_set(key)])
		rrect(r, Color("2d3a6b"), 4)
		rframe(r, Color(1, 1, 1, 0.2), 1.0, 4)
		ctxt(r.position.x + r.size.x / 2.0, r.position.y + 17, key, 13, Color.WHITE)

func secret(R: float, t: float) -> void:
	var ox := (R - 640.0) / 2.0
	c.draw_rect(Rect2(0, 0, R, 360), Color(0.03, 0.03, 0.08, 0.85))
	if theater.is_empty(): _load_theater_data()

	txt(Vector2(ox + 80, 26), "CUTSCENE THEATER", 18, Color.WHITE)
	for tab_idx in 4:
		var tr := Rect2(ox + 262 + tab_idx * 90, 8, 86, 24)
		var is_on := tab_idx == song_test_tab
		var idx := tab_idx
		c.buttons.append([tr, func(): song_test_tab = idx; song_test = ""; sec_msg = ""; c.snd.have_vox = true])
		rrect(tr, Color("16a085") if is_on else Color("2d3a6b"), 7)
		rframe(tr, Color("ffd32a") if is_on else Color(1, 1, 1, 0.4), 2.0 if is_on else 1.0, 7)
		ctxt(tr.position.x + tr.size.x / 2.0, tr.position.y + 17, ["THEATER", "SONGS", "MUSICAL", "TIMING"][tab_idx], 11, Color.WHITE)

	if song_test_tab == 0:
		txt(Vector2(ox + 14, 50), "pick a scene to watch", 12, Color("ffd32a"))
		txt(Vector2(ox + 14, 70), "STORY", 11, Color("ffd32a"))
		var acts: Array = theater.get("acts", [])
		var end_list: Array = theater.get("end", [])
		for i in 5:
			var r := Rect2(ox + 14 + i * 124, 76, 120, 26)
			var is_end := i == 4
			var list: Array = end_list if is_end else (acts[i] if i < acts.size() else [])
			c.buttons.append([r, func(): _play_list(list, 0)])
			rrect(r, Color("c0392b") if is_end else Color("6c5ce7"), 7); rframe(r, Color(1, 1, 1, 0.35), 1.2, 7)
			ctxt(r.position.x + r.size.x / 2.0, r.position.y + 17, "FULL ENDING" if is_end else STORY_LABELS[i], 11, Color.WHITE)
		txt(Vector2(ox + 14, 120), "ENDING SCENES (plays on from there)", 11, Color("ffd32a"))
		for i in end_list.size():
			var r := Rect2(ox + 14 + (i % 4) * 156, 126 + (i / 4) * 26, 152, 23)
			var from := i
			c.buttons.append([r, func(): _play_list(end_list, from)])
			rrect(r, Color("2d3a6b"), 6); rframe(r, Color(1, 1, 1, 0.3), 1.2, 6)
			ctxt(r.position.x + r.size.x / 2.0, r.position.y + 16, "%d. %s" % [i + 1, end_list[i]["title"]], 9, Color.WHITE)
	elif song_test_tab == 3:
		_draw_timing(ox)
	else:
		var msg: String = ("now playing: " + TNAME.get(song_test, song_test)) if song_test != "" else (sec_msg if sec_msg != "" else "pick a track to hear it")
		txt(Vector2(ox + 14, 50), msg, 12, Color("ffd32a"))
		var tracks_to_show: Array = SONGS if song_test_tab == 1 else CUTSCENES
		for i in tracks_to_show.size():
			var track: String = tracks_to_show[i]
			var r := Rect2(ox + 14 + (i % 4) * 153, 70 + (i / 4) * 40, 150, 36)
			var on := track == song_test
			c.buttons.append([r, func():
				if song_test_tab == 1:
					song_test = track; c.snd.stop_music(); c.snd.start_music(track); c.snd.sfx("click")
				else:
					_play_cutscene_id(track)])
			rrect(r, Color("16a085") if on else Color("2d3a6b"), 7); rframe(r, Color("ffd32a") if on else Color(1, 1, 1, 0.3), 2.0 if on else 1.2, 7)
			ctxt(r.position.x + r.size.x / 2.0, r.position.y + 16, TNAME.get(track, track.to_upper()), 11, Color.WHITE)
			ctxt(r.position.x + r.size.x / 2.0, r.position.y + 30, "with vocals" if track == "victory" else "ready", 9, Color(1, 1, 1, 0.55))

	if song_test_tab != 3:
		button(Rect2(ox + 14, 314, 164, 38), "STOP", Color("c0392b"), func(): song_test = ""; c.snd.stop_music(), 16)
	button(Rect2(ox + 14, 8, 56, 22), "BACK", Color("6c5ce7"), func(): song_test = ""; c.snd.stop_music(); c.snd.have_vox = true; c.state = c.S.MENU, 11)
