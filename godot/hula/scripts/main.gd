extends Node2D
# Hula Vaquero: Sky Ride (Godot port). Logical field 772x360 = 3088x1440 / 4.
const FW := 772.0
const FH := 360.0
enum S { MENU, PLAY, OVER }
var state := S.MENU
var t := 0.0
var frames: Array[Texture2D] = []
var player := Vector2(120, 180)
var target := Vector2(120, 180)
var hp := 100.0
var score := 0
var ships: Array = []
var shots: Array = []
var pops: Array = []
var fire_cd := 0.0
var spawn_cd := 1.0
var touch_id := -1
var buttons: Array = []   # [Rect2, Callable]
var shake := 0.0

func _ready() -> void:
	for i in 37:
		frames.append(load("res://art/ship_%03d.webp" % i))

var touch_start := Vector2.ZERO
var player_start := Vector2.ZERO

func _input(e: InputEvent) -> void:
	# touch only (the project turns mouse clicks into touches too). The hero moves by how far the finger has dragged,
	# so tapping a spot does nothing by itself and a drag moves him the same distance, like the HTML game.
	if e is InputEventScreenTouch:
		var pos := _to_field(e.position)
		if e.pressed:
			for b in buttons:
				if (b[0] as Rect2).has_point(pos):
					(b[1] as Callable).call(); return
			if state == S.PLAY and touch_id == -1:
				touch_id = e.index; touch_start = pos; player_start = player; target = player
		elif e.index == touch_id:
			touch_id = -1; target = player
	elif e is InputEventScreenDrag and state == S.PLAY and e.index == touch_id:
		target = player_start + (_to_field(e.position) - touch_start)

func _to_field(p: Vector2) -> Vector2:
	return get_canvas_transform().affine_inverse() * p

func start_run() -> void:
	state = S.PLAY; hp = 100.0; score = 0; ships.clear(); shots.clear(); pops.clear()
	player = Vector2(120, 180); target = player; t = 0.0; touch_id = -1

func _process(dt: float) -> void:
	t += dt
	if state == S.PLAY:
		player = player.lerp(target, 1.0 - pow(0.00001, dt))
		player = player.clamp(Vector2(24, 24), Vector2(_right() - 24, FH - 24))
		fire_cd -= dt
		if fire_cd <= 0.0:
			fire_cd = 0.22
			shots.append({"p": player + Vector2(18, -4), "v": Vector2(560, 0)})
		spawn_cd -= dt
		if spawn_cd <= 0.0:
			spawn_cd = max(0.45, 1.3 - t * 0.012)
			ships.append({"p": Vector2(_right() + 40, randf_range(40, FH - 40)), "v": Vector2(-randf_range(70, 130), 0), "hp": 3, "ph": randf() * 6.0})
		for s in shots: s.p += s.v * dt
		shots = shots.filter(func(s): return s.p.x < _right() + 20)
		for sh in ships:
			sh.ph += dt
			var to_p: Vector2 = (player - sh.p).normalized()
			sh.v = sh.v.lerp(to_p * 110.0, dt * 0.8) + Vector2(0, sin(sh.ph * 2.0) * 40.0 * dt)
			sh.p += sh.v * dt
			if sh.p.distance_to(player) < 26.0:
				sh.hp = 0; hp -= 12.0; shake = 0.25
			for s in shots:
				if s.p.distance_to(sh.p) < 22.0: sh.hp -= 1; s.p.x = 9999
		for sh in ships:
			if sh.hp <= 0:
				score += 10
				for k in 8: pops.append({"p": sh.p, "v": Vector2.from_angle(randf() * TAU) * randf_range(40, 190), "life": 0.5})
		ships = ships.filter(func(sh): return sh.hp > 0 and sh.p.x > -60)
		shots = shots.filter(func(s): return s.p.x < 9000)
		if hp <= 0: state = S.OVER
	for p in pops:
		p.p += p.v * dt; p.life -= dt
	pops = pops.filter(func(p): return p.life > 0)
	shake = max(0.0, shake - dt)
	queue_redraw()

func _right() -> float:
	var vs := get_viewport_rect().size
	return vs.x

func _draw() -> void:
	buttons.clear()
	var R := _right()
	var off := Vector2(randf_range(-1, 1), randf_range(-1, 1)) * shake * 10.0
	draw_set_transform(off)
	_sky(R)
	if state == S.MENU: _menu(R)
	else:
		for s in shots: draw_rect(Rect2(s.p - Vector2(8, 2), Vector2(16, 4)), Color(1, 0.9, 0.3))
		for sh in ships: _ship(sh)
		_hero(player, t)
		for p in pops: draw_circle(p.p, 3.0 * p.life * 2.0, Color(0.6, 0.9, 0.3, p.life * 2.0))
		_hud(R)
		if state == S.OVER: _over(R)

func _sky(R: float) -> void:
	var top := Color("3b8fd9"); var mid := Color("8fcdf5"); var bot := Color("ffc98a")
	for i in 36:
		var u := i / 35.0
		var c := top.lerp(mid, u / 0.55) if u < 0.55 else mid.lerp(bot, (u - 0.55) / 0.45)
		draw_rect(Rect2(0, i * 10, R, 10), c)
	for k in 7:
		var x := fmod(k * 190.0 - t * (8 + k * 2), R + 160) - 80
		draw_circle(Vector2(x, 60 + (k * 53) % 200), 26, Color(1, 1, 1, 0.55))
		draw_circle(Vector2(x + 24, 66 + (k * 53) % 200), 20, Color(1, 1, 1, 0.55))
	for k in 6:
		var x := k * 150.0 - fmod(t * 20, 150.0)
		draw_rect(Rect2(x, FH - 50 - (k * 17) % 40, 90, 120), Color("b5546e"))

func _hero(p: Vector2, tm: float) -> void:
	var bob := sin(tm * 4.0) * 3.0
	p += Vector2(0, bob)
	draw_circle(p + Vector2(0, 30), 14, Color(0, 0, 0, 0.18))
	draw_rect(Rect2(p + Vector2(-8, -4), Vector2(16, 26)), Color("c0392b"))
	draw_circle(p + Vector2(0, -12), 8, Color("a8744f"))
	draw_colored_polygon(PackedVector2Array([p + Vector2(-20, -16), p + Vector2(20, -16), p + Vector2(8, -24), p + Vector2(-8, -24)]), Color("f1e6c8"))
	draw_arc(p + Vector2(0, 8), 19, 0, TAU, 28, Color("2ecc71"), 3.0)

func _ship(sh: Dictionary) -> void:
	var d: Vector2 = sh.v.normalized()
	var ang := rad_to_deg(acos(clamp(d.y, -1.0, 1.0)))
	var fi := int(round(ang / 5.0))
	var tex := frames[clampi(fi, 0, 36)]
	var sz := 96.0
	var r := Rect2(sh.p - Vector2(sz, sz) / 2.0, Vector2(sz, sz))
	if d.x < 0.0:
		draw_texture_rect(tex, Rect2(r.position + Vector2(sz, 0), Vector2(-sz, sz)), false)
	else:
		draw_texture_rect(tex, r, false)

func _btn(r: Rect2, label: String, col: Color, fn: Callable, fs := 22) -> void:
	buttons.append([r, fn])
	draw_rect(Rect2(r.position + Vector2(0, 3), r.size), Color(0, 0, 0, 0.35))
	draw_rect(r, col)
	draw_rect(Rect2(r.position, Vector2(r.size.x, r.size.y * 0.45)), Color(1, 1, 1, 0.14))
	var f := ThemeDB.fallback_font
	var w := f.get_string_size(label, HORIZONTAL_ALIGNMENT_CENTER, -1, fs).x
	draw_string(f, r.position + Vector2((r.size.x - w) / 2.0, r.size.y / 2.0 + fs * 0.35), label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color.WHITE)

func _menu(R: float) -> void:
	var f := ThemeDB.fallback_font
	var cx := R / 2.0 - 140.0
	draw_string(f, Vector2(cx - 150, 90), "HULA VAQUERO", HORIZONTAL_ALIGNMENT_LEFT, -1, 52, Color("ffd32a"))
	draw_string(f, Vector2(cx - 40, 120), "SKY RIDE · GODOT", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
	_hero(Vector2(cx + 50, 230), t)
	_btn(Rect2(R - 300, 80, 240, 70), "RIDE!", Color("2ecc71"), start_run, 32)
	_btn(Rect2(R - 300, 168, 240, 50), "ENDLESS", Color("8e44ad"), start_run, 22)
	_btn(Rect2(R - 300, 232, 240, 50), "OPTIONS", Color("e67e22"), func(): pass, 22)

func _hud(R: float) -> void:
	var f := ThemeDB.fallback_font
	draw_rect(Rect2(10, 8, 160, 16), Color(0, 0, 0, 0.4))
	draw_rect(Rect2(10, 8, 160 * clamp(hp / 100.0, 0, 1), 16), Color("2ecc71"))
	draw_string(f, Vector2(14, 21), "HP %d/100" % int(max(hp, 0)), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
	draw_string(f, Vector2(R - 130, 24), "SCORE %d" % score, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color("ffd32a"))

func _over(R: float) -> void:
	draw_rect(Rect2(0, 0, R, FH), Color(0.03, 0.03, 0.08, 0.7))
	var f := ThemeDB.fallback_font
	draw_string(f, Vector2(R / 2 - 140, 150), "KNOCKED OUT!", HORIZONTAL_ALIGNMENT_LEFT, -1, 44, Color("ff4757"))
	draw_string(f, Vector2(R / 2 - 60, 185), "Score %d" % score, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
	_btn(Rect2(R / 2 - 110, 215, 220, 50), "AGAIN", Color("2ecc71"), start_run, 24)
	_btn(Rect2(R / 2 - 110, 275, 220, 40), "MENU", Color("636e72"), func(): state = S.MENU, 18)
