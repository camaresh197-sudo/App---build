extends Node2D
# Hula Vaquero: Sky Ride (Godot port). Logical field 772x360 = 3088x1440 / 4.
const FW := 772.0
const FH := 360.0
enum S { MENU, PLAY, OVER, SECRET, PICK }
const Save = preload("res://scripts/save.gd")
const CardDeck = preload("res://scripts/card_deck.gd")
var deck: CardDeck = CardDeck.new()
var level := 1
var xp := 0.0
var pending_picks := 0      # level-ups waiting for the player to choose
var picks: Array = []       # the cards on screen right now
const Menu = preload("res://scripts/menu.gd")
const Map = preload("res://scripts/map.gd")
var menu
var map
var hero3d
var ship_tex: Array = []
var state := S.MENU
var t := 0.0
var frames: Array[Texture2D] = []
var player := Vector2(120, 180)
var target := Vector2(120, 180)
var hp := 100.0
var score := 0
var run_level := ""
var run_target := 0
var run_spawn := 1.0
var run_speed := 1.0
var won := false
var run_stars := 0
var ships: Array = []
var shots: Array = []
var pops: Array = []
var fire_cd := 0.0
var spawn_cd := 1.0
var touch_id := -1
var buttons: Array = []   # [Rect2, Callable]
var shake := 0.0
var _restart_t := 0.0         # seconds spent at the title screen while a downloaded update waits

func _ready() -> void:
	for i in 37:
		frames.append(load("res://art/ship_%03d.webp" % i))
	ship_tex = frames
	Save.load_all()
	menu = Menu.new(self)
	map = Map.new(self)
	hero3d = preload("res://scripts/hero3d.gd").new(); add_child(hero3d)
	snd = preload("res://scripts/sound.gd").new(); add_child(snd)
	cutscene = preload("res://scripts/cutscene.gd").new(); add_child(cutscene)

var snd: Node
var cutscene: Node
var _want := "?"
var _vm := -1
var touch_start := Vector2.ZERO
var player_start := Vector2.ZERO

func _input(e: InputEvent) -> void:
	# touch only (the project turns mouse clicks into touches too). The hero moves by how far the finger has dragged,
	# so tapping a spot does nothing by itself and a drag moves him the same distance, like the HTML game.
	if e is InputEventScreenTouch:
		var pos := _to_field(e.position)
		if e.pressed:
			# Skip cutscene on tap
			if cutscene and cutscene.is_active():
				cutscene.handle_tap(pos)
				get_tree().root.set_input_as_handled()
				return
			for b in buttons:
				if (b[0] as Rect2).has_point(pos):
					snd.sfx("click"); (b[1] as Callable).call(); return
			if state == S.PLAY and touch_id == -1:
				touch_id = e.index; touch_start = pos; player_start = player; target = player
		elif e.index == touch_id:
			touch_id = -1; target = player
	elif e is InputEventScreenDrag and state == S.PLAY and e.index == touch_id:
		target = player_start + (_to_field(e.position) - touch_start)

func _to_field(p: Vector2) -> Vector2:
	return get_canvas_transform().affine_inverse() * p

func start_run(level_id := "", goal := 0) -> void:
	run_level = level_id
	run_target = goal
	won = false
	run_stars = 0
	map.close()   # the RIDE! button launches from the map: PLAY draws first, but don't leave the map's state armed
	var nd: Dictionary = {}
	if level_id != "":
		nd = map.node_by_id(level_id)
	run_spawn = float(nd.get("spawn", 1.0))
	run_speed = float(nd.get("speed", 1.0))
	hero3d.arm_clear(); hero3d.mood("grin"); hero3d.gaze = Vector2.ZERO
	deck.reset(); level = 1; xp = 0.0; pending_picks = 0; picks = []
	state = S.PLAY; hp = deck.st.max_hp; score = 0; ships.clear(); shots.clear(); pops.clear()
	player = Vector2(120, 180); target = player; t = 0.0; touch_id = -1
	snd.start_music()

func open_map() -> void:
	menu.close_hub()
	map.open()
	state = S.MENU

var _confirmed := false
func _process(dt: float) -> void:
	t += dt
	hero3d.portrait_on = state == S.PLAY or state == S.OVER or state == S.SECRET or (state == S.MENU and not menu.in_hub and not map.in_map)
	hero3d.auto_dance = state == S.MENU or state == S.SECRET
	fps_s = lerpf(fps_s, 1.0 / maxf(dt, 0.0001), 0.08)
	var want: String = "menu" if state == S.MENU else ("game" if state == S.PLAY else (menu.song_test if state == S.SECRET else ""))
	if want != _want:
		_want = want
		if want == "": snd.stop_music()
		else: snd.start_music(want)
	# beat feed for the hero's dance, phase-locked to the music. after the track switch above, so is_playing() is
	# already true on the frame the music starts (the hero never sees a stale first frame). Object.set() on a
	# property hero3d.gd has not declared yet is a silent no-op; guard the nodes in case _process runs before _ready.
	if hero3d and snd:
		hero3d.set("beat", snd.beat_pos())
		hero3d.set("beat_on", snd.is_playing())
		hero3d.set("beat_bar", snd.bar_pos())
		hero3d.set("beat_bpm", 60.0 / snd.beat_secs())
	var vm: int = int(Save.data.opt.music) * 100 + int(Save.data.opt.sfx)
	if vm != _vm: _vm = vm; snd.set_volumes(int(Save.data.opt.music), int(Save.data.opt.sfx))
	if cutscene: cutscene.update(dt)
	# confirm as soon as the game is really up. a long wait turns "opened it for a second to check" into a failed start.
	if not _confirmed and Time.get_ticks_msec() > 2000:
		_confirmed = true; Updater.confirm_good()
	if state == S.PLAY:
		player = player.lerp(target, 1.0 - pow(0.00001, dt))
		player = player.clamp(Vector2(24, 24), Vector2(_right() - 24, FH - 24))
		hp = minf(hp + float(deck.st.regen) * dt, float(deck.st.max_hp))
		deck.tick_shield(dt)
		fire_cd -= dt
		if fire_cd <= 0.0:
			fire_cd = 0.22
			var n: int = 1 + int(deck.st.extra)
			for i in n:
				var off: float = (i - (n - 1) / 2.0) * 9.0
				shots.append({"p": player + Vector2(18, -4 + off), "v": Vector2(560, 0), "d": float(deck.st.dmg)})
			snd.sfx("shoot")
		spawn_cd -= dt
		if spawn_cd <= 0.0:
			spawn_cd = max(0.45, 1.3 - t * 0.012) / max(0.1, run_spawn)
			ships.append({"p": Vector2(_right() + 40, randf_range(40, FH - 40)), "v": Vector2(-randf_range(70, 130) * run_speed, 0), "hp": 3, "ph": randf() * 6.0})
		for s in shots: s.p += s.v * dt
		shots = shots.filter(func(s): return s.p.x < _right() + 20)
		for sh in ships:
			sh.ph += dt
			var to_p: Vector2 = (player - sh.p).normalized()
			sh.v = sh.v.lerp(to_p * 110.0 * run_speed, dt * 0.8) + Vector2(0, sin(sh.ph * 2.0) * 40.0 * dt)
			sh.p += sh.v * dt
			if sh.hp > 0.0 and sh.p.distance_to(player) < 26.0:
				var ram: int = int(deck.st.ram)
				if ram > 0:
					# Spiked Bumper: the ball is hurt by the ram and bounces off instead of dying
					sh.hp -= 1.5 * ram
					sh.p += (sh.p - player).normalized() * 30.0
				else:
					sh.hp = 0.0
				if int(deck.st.shield) > 0:
					deck.st.shield -= 1
				else:
					hp -= deck.hit_damage()
				shake = 0.25; snd.sfx("hurt"); hero3d.react("pain", 0.6); hero3d.arm_kick("flinch", 0.5)
			for s in shots:
				if s.p.distance_to(sh.p) < 22.0:
					var dmg: float = float(s.get("d", 1.0))
					if randf() < float(deck.st.crit): dmg *= 2.0
					sh.hp -= dmg; s.p.x = 9999; snd.sfx("hit")
		for sh in ships:
			if sh.hp <= 0:
				score += 10; snd.sfx("pop"); _combo += 1; _combo_t = 1.6
				xp += 1.0 * float(deck.st.xp_mult)
				if randf() < float(deck.st.heal_kill): hp = minf(hp + 5.0, float(deck.st.max_hp))
				if _combo % 5 == 0: hero3d.react("laugh", 1.1); hero3d.arm_kick("cheer", 1.1)
				for k in 8: pops.append({"p": sh.p, "v": Vector2.from_angle(randf() * TAU) * randf_range(40, 190), "life": 0.5})
		ships = ships.filter(func(sh): return sh.hp > 0 and sh.p.x > -60)
		shots = shots.filter(func(s): return s.p.x < 9000)
		_director(dt)
		if run_target > 0 and score >= run_target:
			_finish(true)
		elif hp <= 0:
			_finish(false)
		while state == S.PLAY and xp >= _xp_need():
			xp -= _xp_need(); level += 1; pending_picks += 1
		if state == S.PLAY and pending_picks > 0:
			_open_pick()
	for p in pops:
		p.p += p.v * dt; p.life -= dt
	pops = pops.filter(func(p): return p.life > 0)
	shake = max(0.0, shake - dt)
	# a downloaded update is waiting: close the app once the player is safely at the title screen, so the
	# packs are mounted on the next launch. one tap on the icon and the new build is running.
	# get() instead of a direct read: this script ships in packs, so it also runs inside APKs whose updater
	# predates the flag, and those must keep behaving exactly as before.
	if Updater.get("ready_to_apply") == true and OS.has_feature("mobile") and state == S.MENU and not menu.in_hub:
		_restart_t += dt
		if _restart_t > 2.5: get_tree().quit()
	else:
		_restart_t = 0.0
	queue_redraw()

# XP needed to reach the next level. Grows a little each level.
func _xp_need() -> float:
	return 10.0 + 4.0 * float(level)

# opens the card picker with three cards. Several queued level-ups show one picker after another.
func _open_pick() -> void:
	picks = deck.choices(3)
	if picks.is_empty():
		pending_picks = 0   # nothing left to offer: keep playing
		return
	state = S.PICK

func _take_pick(i: int) -> void:
	if i < 0 or i >= picks.size():
		return
	hp = deck.apply(str(picks[i].id), hp)
	pending_picks -= 1
	picks = []
	if pending_picks > 0:
		_open_pick()
	else:
		state = S.PLAY

# the hero's face reacts to the game: looks at the nearest ship, flinches when one gets close, worries when hurt, laughs on a streak
var _combo := 0
var _combo_t := 0.0
func _director(dt: float) -> void:
	_combo_t -= dt
	if _combo_t <= 0.0: _combo = 0
	var nearest := Vector2.ZERO; var nd := 1e9
	for sh in ships:
		var d: float = sh.p.distance_to(player)
		if sh.p.x > player.x - 40.0 and d < nd: nd = d; nearest = sh.p
	if nd < 1e8: hero3d.gaze = Vector2(clampf((nearest.x - player.x) / 220.0, -1.0, 1.0), clampf(-(nearest.y - player.y) / 120.0, -1.0, 1.0))
	else: hero3d.gaze = Vector2(0.6, 0.0)
	hero3d.look = Vector2(hero3d.gaze.x * 0.5, 0.0)
	if nd < 70.0 and hero3d.react_t <= 0.0: hero3d.react("startled", 0.35); hero3d.arm_kick("flinch", 0.3)
	var hp_pct := hp * 100.0 / maxf(1.0, float(deck.st.max_hp))
	hero3d.mood("afraid" if hp_pct <= 25.0 else ("worried" if hp_pct <= 50.0 else ("determined" if ships.size() >= 5 else "grin")))

func _finish(win: bool) -> void:
	state = S.OVER
	won = win
	run_stars = 0
	snd.stop_music()
	if win:
		run_stars = 1
		var th: Array = map.star_thresholds()
		if th.size() >= 2:
			if hp >= float(th[0]): run_stars = 3
			elif hp >= float(th[1]): run_stars = 2
		if run_level != "":
			var lv: Dictionary = Save.data.get("levels", {})
			lv[run_level] = max(int(lv.get(run_level, 0)), run_stars)
			Save.data.levels = lv
		hero3d.mood("grin"); hero3d.arm_kick("cheer", 2.0)
		snd.sfx("level")
	else:
		hero3d.mood("despair"); hero3d.arm_kick("limp", 999.0); hero3d.gaze = Vector2(0.0, -0.7)
	Save.data.stats.runs = int(Save.data.stats.runs) + 1
	Save.data.stats.best_run = max(int(Save.data.stats.best_run), score)
	Save.save()

func _back_to_map() -> void:
	map.open()
	state = S.MENU

func _right() -> float:
	var vs := get_viewport_rect().size
	return vs.x

var fps_s := 60.0
func _fps(R: float) -> void:
	var f := ThemeDB.fallback_font
	var txt := "%d FPS" % int(round(fps_s))
	var col := Color("2ecc71") if fps_s >= 50.0 else (Color("f1c40f") if fps_s >= 30.0 else Color("e74c3c"))
	draw_rect(Rect2(R / 2 - 34, 3, 68, 16), Color(0, 0, 0, 0.55))
	draw_string(f, Vector2(R / 2 - 28, 15), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, col)

func _draw() -> void:
	buttons.clear()
	var R := _right()
	var off := Vector2(randf_range(-1, 1), randf_range(-1, 1)) * shake * 10.0
	draw_set_transform(off)
	_sky(R)
	if state == S.SECRET:
		_hero(Vector2(FW / 2, 160), t)
		if not (cutscene and cutscene.is_active()):
			menu.secret(R, t)
		_below(R, Color(0.03, 0.03, 0.08, 0.85))
		if menu.song_test_tab != 0: _portrait_hud()   # the theater grid uses that corner
	elif state == S.MENU:
		if map.in_map:
			map.draw(R, t); _below(R, Color(0.03, 0.03, 0.08, 0.92))
		elif menu.in_hub:
			menu.hub(R, t, Callable(self, "_hero")); _below(R, Color(0.03, 0.03, 0.08, 0.8))
		else:
			menu.title(R, t, Callable(self, "_hero"), ship_tex); _below(R, Color("4a2a3e"))
		if not menu.in_hub and not map.in_map: _portrait_hud()
	else:
		for s in shots: draw_rect(Rect2(s.p - Vector2(8, 2), Vector2(16, 4)), Color(1, 0.9, 0.3))
		for sh in ships: _ship(sh)
		_hero(player, t)
		for p in pops: draw_circle(p.p, 3.0 * p.life * 2.0, Color(0.6, 0.9, 0.3, p.life * 2.0))
		if state == S.OVER: draw_rect(Rect2(0, 0, R, _vis_h()), Color(0.03, 0.03, 0.08, 0.7))   # dim the field, but the HUD below stays bright
		_hud(R)
		_portrait_hud()
		if state == S.OVER: _over(R)
		if state == S.PICK: _pick(R)
	if cutscene: cutscene.draw(self)
	_toast(R)
	draw_set_transform(Vector2.ZERO)
	if Save.data.opt.fps: _fps(R)

# visible logical height: 360 at the design aspect, more when the window is taller. never shift the composition
# (buttons/_to_field live in field coords); instead extend the background fills down to cover the extra space.
func _vis_h() -> float:
	return maxf(FH, get_viewport_rect().size.y)

func _below(R: float, col: Color) -> void:
	var h := _vis_h()
	if h > FH: draw_rect(Rect2(0, FH, R, h - FH), col)

func _sky(R: float) -> void:
	var top := Color("3b8fd9"); var mid := Color("8fcdf5"); var bot := Color("ffc98a")
	var h := _vis_h()
	for i in int(ceil(h / 10.0)):
		var u := clampf(i / 35.0, 0.0, 1.0)
		var c := top.lerp(mid, u / 0.55) if u < 0.55 else mid.lerp(bot, (u - 0.55) / 0.45)
		draw_rect(Rect2(0, i * 10, R, 10), c)
	for k in 7:
		var x := fmod(k * 190.0 - t * (8 + k * 2), R + 160) - 80
		draw_circle(Vector2(x, 60 + (k * 53) % 200), 26, Color(1, 1, 1, 0.55))
		draw_circle(Vector2(x + 24, 66 + (k * 53) % 200), 20, Color(1, 1, 1, 0.55))
	for k in 6:
		var x := k * 150.0 - fmod(t * 20, 150.0)
		var by := FH - 50 - (k * 17) % 40
		draw_rect(Rect2(x, by, 90, maxf(120.0, h - by)), Color("b5546e"))

func _hero(p: Vector2, tm: float, k := 1.0) -> void:
	# the 3D vaquero: posed, rendered in its own viewport, drawn here as a sprite (height ~ 76 field units)
	hero3d.set_cos(int(Save.data.eq.hat), int(Save.data.eq.hoop), Save.defs.cos)
	hero3d.pose(tm * 3.2)
	var th: Texture2D = hero3d.tex()
	var hh := 118.0 * k; var ww: float = hh * float(hero3d.VW) / float(hero3d.VH)
	draw_circle(p + Vector2(0, 38 * k), 15 * k, Color(0, 0, 0, 0.16))
	draw_texture_rect(th, Rect2(p - Vector2(ww / 2.0, hh * 0.52), Vector2(ww, hh)), false)

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

func _toast(R: float) -> void:
	if Updater.status != "":
		var f := ThemeDB.fallback_font
		var w := f.get_string_size(Updater.status, HORIZONTAL_ALIGNMENT_CENTER, -1, 13).x
		draw_rect(Rect2(R / 2 - w / 2 - 10, FH - 28, w + 20, 22), Color(0, 0, 0, 0.55))
		draw_string(f, Vector2(R / 2 - w / 2, FH - 12), Updater.status, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)

func _hud(R: float) -> void:
	var f := ThemeDB.fallback_font
	var mx := maxf(1.0, float(deck.st.max_hp))
	draw_rect(Rect2(10, 8, 160, 16), Color(0, 0, 0, 0.4))
	draw_rect(Rect2(10, 8, 160 * clamp(hp / mx, 0, 1), 16), Color("2ecc71"))
	draw_string(f, Vector2(14, 21), "HP %d/%d" % [int(max(hp, 0)), int(mx)], HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
	draw_rect(Rect2(10, 27, 160, 6), Color(0, 0, 0, 0.4))
	draw_rect(Rect2(10, 27, 160 * clamp(xp / _xp_need(), 0, 1), 6), Color("9b59b6"))
	draw_string(f, Vector2(176, 34), "LV %d" % level, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
	draw_string(f, Vector2(R - 130, 24), "SCORE %d" % score, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color("ffd32a"))
	if run_target > 0:
		draw_string(f, Vector2(R - 130, 42), "TARGET %d" % run_target, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("9aa3c7"))

func _portrait_hud() -> void:
	# close-up of his face, bottom-left, so the emotions can be read
	var pr := Rect2(12, FH - 124, 112, 112)
	draw_rect(pr.grow(4), Color(0.05, 0.05, 0.12, 0.6))
	draw_texture_rect(hero3d.ptex(), pr, false)
	draw_rect(pr.grow(4), Color("e7b84a"), false, 2.0)

func _pick(R: float) -> void:
	var f := ThemeDB.fallback_font
	draw_rect(Rect2(0, 0, R, _vis_h()), Color(0.03, 0.03, 0.08, 0.72))
	draw_string(f, Vector2(R / 2 - 150, 40), "LEVEL %d! CHOOSE A POWER" % level, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color("ffd32a"))
	for i in picks.size():
		var c: Dictionary = picks[i]
		var r := Rect2(R / 2 - 260, 54 + i * 96, 520, 86)
		var idx := i
		buttons.append([r, func(): _take_pick(idx)])
		var col := CardDeck.rarity_color(c)
		draw_rect(Rect2(r.position + Vector2(0, 3), r.size), Color(0, 0, 0, 0.35))
		draw_rect(r, Color(0.12, 0.12, 0.2, 0.96))
		draw_rect(r, col, false, 2.0)
		draw_string(f, r.position + Vector2(14, 28), String(c.name), HORIZONTAL_ALIGNMENT_LEFT, -1, 18, col)
		draw_string(f, r.position + Vector2(r.size.x - 90, 28), String(c.rarity).to_upper(), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(col, 0.7))
		var lines := _wrap(String(c.desc), f, 12, r.size.x - 28)
		for li in lines.size():
			draw_string(f, r.position + Vector2(14, 50 + li * 16), lines[li], HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)

# splits text into lines no wider than w pixels
func _wrap(text: String, f: Font, fs: int, w: float) -> Array:
	var out: Array = []
	var cur := ""
	for word in text.split(" "):
		var trial := word if cur == "" else cur + " " + word
		if f.get_string_size(trial, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > w and cur != "":
			out.append(cur); cur = word
		else:
			cur = trial
	if cur != "": out.append(cur)
	return out

func _over(R: float) -> void:
	var f := ThemeDB.fallback_font
	var title := "LEVEL CLEAR!" if won else "KNOCKED OUT!"
	var col := Color("2ecc71") if won else Color("ff4757")
	draw_string(f, Vector2(R / 2 - 150, 145), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 40, col)
	draw_string(f, Vector2(R / 2 - 60, 178), "Score %d" % score, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
	if won:
		for i in 3:
			draw_circle(Vector2(R / 2 - 24 + i * 24, 202), 8, Color("ffd32a") if i < run_stars else Color(1, 1, 1, 0.18))
	var nxt: Dictionary = {}
	if run_level != "" and won:
		nxt = map.next_node(run_level)
	if won and not nxt.is_empty():
		var nid := str(nxt.get("id", ""))
		var ntarget := int(nxt.get("target", 0))
		_btn(Rect2(R / 2 - 110, 224, 220, 44), "NEXT", Color("2ecc71"), func(): start_run(nid, ntarget), 22)
		_btn(Rect2(R / 2 - 110, 276, 106, 36), "AGAIN", Color("0984e3"), func(): start_run(run_level, run_target), 16)
		_btn(Rect2(R / 2 - 4, 276, 106, 36), "MAP", Color("636e72"), _back_to_map, 16)
	else:
		_btn(Rect2(R / 2 - 110, 236, 220, 48), "AGAIN", Color("2ecc71"), func(): start_run(run_level, run_target), 22)
		_btn(Rect2(R / 2 - 110, 292, 220, 34), "MAP", Color("636e72"), _back_to_map, 16)
