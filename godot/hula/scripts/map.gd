extends RefCounted
# World map screen: 4 acts x 5 nodes laid over the endless run. Reads data_map.json and
# Save.data.levels (id -> stars). Milestone 2 is read-only: it shows the chain and launches
# a run, but does not award stars yet (that is the run-goal slice).
const Save = preload("res://scripts/save.gd")
const DATA := "res://data/data_map.json"
var c: Node2D
var data: Dictionary = {}
var act := 0
var sel := 0
var in_map := false
var loaded := false

func _init(main: Node2D) -> void:
	c = main

func open() -> void:
	if not loaded:
		var f := FileAccess.open(DATA, FileAccess.READ)
		if f:
			var j = JSON.parse_string(f.get_as_text())
			if j is Dictionary:
				data = j
		loaded = true
	in_map = true
	act = 0
	sel = 0
	if acts().is_empty():
		return
	# land on the first open, unfinished node; otherwise the last one
	for a in acts().size():
		var ns := node_list(a)
		for i in ns.size():
			if is_unlocked(a, i) and stars(str(ns[i].get("id", ""))) < 3:
				act = a
				sel = i
				return
	act = acts().size() - 1
	sel = max(0, node_list(act).size() - 1)

func close() -> void:
	in_map = false

# ---------- data ----------
func acts() -> Array:
	return data.get("acts", [])

func node_list(a: int) -> Array:
	if a < 0 or a >= acts().size():
		return []
	return acts()[a].get("nodes", [])

func node(a: int, i: int) -> Dictionary:
	var ns := node_list(a)
	if i < 0 or i >= ns.size():
		return {}
	return ns[i]

func node_by_id(id: String) -> Dictionary:
	if id == "":
		return {}
	for a in acts().size():
		for nd in node_list(a):
			if str(nd.get("id", "")) == id:
				return nd
	return {}

func star_thresholds() -> Array:
	return data.get("stars", [70, 40])

func next_node(id: String) -> Dictionary:
	if id == "":
		return {}
	var k := -1
	var n := 0
	for a in acts().size():
		var ns := node_list(a)
		for i in ns.size():
			if str(ns[i].get("id", "")) == id:
				k = n + i
				break
		n += ns.size()
		if k >= 0:
			break
	if k < 0:
		return {}
	return node_by_flat(k + 1)

func stars(id: String) -> int:
	var lv: Dictionary = Save.data.get("levels", {})
	return int(lv.get(id, 0))

func flat_count() -> int:
	var n := 0
	for a in acts().size():
		n += node_list(a).size()
	return n

func flat_index(a: int, i: int) -> int:
	var n := 0
	for aa in acts().size():
		if aa == a:
			return n + i
		n += node_list(aa).size()
	return -1

func node_by_flat(k: int) -> Dictionary:
	var n := 0
	for a in acts().size():
		var ns := node_list(a)
		if k < n + ns.size():
			return ns[k - n]
		n += ns.size()
	return {}

func is_unlocked(a: int, i: int) -> bool:
	var k := flat_index(a, i)
	if k <= 0:
		return true
	var p := node_by_flat(k - 1)
	return stars(str(p.get("id", ""))) >= 1

func total_stars() -> int:
	var n := 0
	for a in acts().size():
		for nd in node_list(a):
			n += stars(str(nd.get("id", "")))
	return n

# ---------- drawing ----------
func draw(R: float, _t: float) -> void:
	if not in_map:
		return
	c.draw_rect(Rect2(0, 0, R, 360), Color(0.03, 0.03, 0.08, 0.92))
	var ox := (R - 640.0) / 2.0
	text(Vector2(ox + 16, 30), "WORLD MAP", 20, Color("ffd32a"))
	text(Vector2(ox + 430, 28), "%d / %d STARS" % [total_stars(), flat_count() * 3], 12, Color("ffd32a"))
	button(Rect2(ox + 552, 8, 82, 26), "BACK", Color("6c5ce7"), close, 12)

	# act tabs
	for a in acts().size():
		var ai := a
		var r := Rect2(ox + 14 + a * 86, 44, 80, 26)
		var on := a == act
		c.buttons.append([r, func(): act = ai; sel = clampi(sel, 0, max(0, node_list(ai).size() - 1))])
		panel(r, Color("e67e22") if on else Color(0.14, 0.15, 0.26, 0.95), 8.0)
		frame(r, Color(1, 1, 1, 0.4 if on else 0.12), 1.2)
		ctext(r.position.x + r.size.x / 2.0, r.position.y + 18, str(acts()[a].get("name", "ACT %d" % (a + 1))), 10, Color.WHITE if on else Color("9aa3c7"))

	var ns := node_list(act)
	var n := ns.size()
	if n == 0:
		ctext(R / 2.0, 190, "no map data", 14, Color(1, 1, 1, 0.5))
		return
	var y0 := 205.0
	var step: float = 500.0 / float(max(1, n - 1))
	for i in n:
		var idx := i
		var x: float = ox + 78.0 + i * step
		var y := y0 + sin(float(i) * 1.1 + act) * 26.0
		if i < n - 1:
			var x2: float = ox + 78.0 + (i + 1) * step
			var y2 := y0 + sin(float(i + 1) * 1.1 + act) * 26.0
			c.draw_line(Vector2(x, y), Vector2(x2, y2), Color(1, 1, 1, 0.16), 3.0)
		var nd: Dictionary = ns[i]
		var id := str(nd.get("id", ""))
		var open := is_unlocked(act, i)
		var st := stars(id)
		var rad := 18.0 if i == sel else 15.0
		var col := Color("ffd32a") if i == sel else (Color("2ecc71") if open else Color(0.25, 0.27, 0.36, 0.95))
		c.buttons.append([Rect2(x - 20, y - 20, 40, 40), func(): sel = idx])
		c.draw_circle(Vector2(x, y), rad + 3.0, Color(0, 0, 0, 0.35))
		c.draw_circle(Vector2(x, y), rad, col)
		if not open:
			c.draw_circle(Vector2(x, y), rad * 0.55, Color(0, 0, 0, 0.5))
		for s in 3:
			c.draw_circle(Vector2(x - 12.0 + s * 12.0, y + 27.0), 3.5, Color("ffd32a") if s < st else Color(1, 1, 1, 0.18))
		ctext(x, y + 44.0, "LOCKED" if not open else ("%d" % int(nd.get("target", 0))), 9, Color(1, 1, 1, 0.45 if not open else 0.75))

	# selected node panel
	var cur := node(act, sel)
	if cur.is_empty():
		return
	var pr := Rect2(ox + 14, 284, 612, 66)
	panel(pr, Color(0.06, 0.07, 0.14, 0.96), 10.0)
	frame(pr, Color("ffd32a"), 1.4)
	var cid := str(cur.get("id", ""))
	var ctarget := int(cur.get("target", 0))
	var open2 := is_unlocked(act, sel)
	text(Vector2(pr.position.x + 14, pr.position.y + 24), str(cur.get("name", "?")), 16, Color.WHITE)
	text(Vector2(pr.position.x + 14, pr.position.y + 46), "TARGET %d" % ctarget, 12, Color("9aa3c7"))
	var st2 := stars(cid)
	for s in 3:
		c.draw_circle(Vector2(pr.position.x + 300 + s * 18, pr.position.y + 30), 5.0, Color("ffd32a") if s < st2 else Color(1, 1, 1, 0.18))
	if open2:
		button(Rect2(pr.position.x + 470, pr.position.y + 14, 128, 38), "RIDE!", Color("2ecc71"), func(): c.start_run(cid, ctarget), 18)
	else:
		ctext(pr.position.x + 534, pr.position.y + 36, "CLEAR PREVIOUS", 11, Color("e74c3c"))
	text(Vector2(pr.position.x + 14, pr.position.y + 60), "stars: 3 at %d HP, 2 at %d" % [int(data.get("stars", [70, 40])[0]), int(data.get("stars", [70, 40])[1])], 9, Color(1, 1, 1, 0.45))

# ---------- small helpers ----------
func font() -> Font:
	return ThemeDB.fallback_font

func text(p: Vector2, s: String, size: int, col: Color) -> void:
	c.draw_string(font(), p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)

func ctext(cx: float, y: float, s: String, size: int, col: Color) -> void:
	var w := font().get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	c.draw_string(font(), Vector2(cx - w / 2.0, y), s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)

func panel(r: Rect2, col: Color, rad := 8.0) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = col
	sb.set_corner_radius_all(int(rad))
	c.draw_style_box(sb, r)

func frame(r: Rect2, col: Color, wd := 1.5, rad := 8.0) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	sb.border_color = col
	sb.set_border_width_all(int(max(1, round(wd))))
	sb.set_corner_radius_all(int(rad))
	c.draw_style_box(sb, r)

func button(r: Rect2, label: String, col: Color, fn: Callable, fs := 14) -> void:
	c.buttons.append([r, fn])
	panel(Rect2(r.position + Vector2(0, 2), r.size), Color(0, 0, 0, 0.35), 9.0)
	panel(r, col, 9.0)
	frame(r, Color(1, 1, 1, 0.35), 1.2, 9.0)
	ctext(r.position.x + r.size.x / 2.0, r.position.y + r.size.y / 2.0 + fs * 0.35, label, fs, Color.WHITE)
