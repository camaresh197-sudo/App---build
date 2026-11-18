extends Node
# test helper: args after "--": out.png frames [play]
func _ready() -> void:
	await get_tree().process_frame
	var a := OS.get_cmdline_user_args()
	var m = get_parent()
	if a.size() > 2 and a[2] == "play": m.start_run()
	if a.size() > 2 and a[2] == "secret":
		m.state = m.S.SECRET
		if a.size() > 3:
			m.menu.song_test = a[3]; m.snd.vox_only = a.size() > 4 and a[4] == "voxonly"; m.snd.start_music(a[3])
	if a.size() > 3 and a[2] == "hub": m.menu.open_hub(int(a[3]))
	var n := int(a[1])
	if a.size() > 2 and a[2] == "anim":
		# record the face: a[0]=out dir, a[3]=fps. Timeline of expressions below; one png per frame.
		var h3 = m.hero3d
		m.set_process(false)
		var fps := int(a[3])
		h3.fixed_dt = 1.0 / fps
		h3.pvp.size = Vector2i(360, 360)
		h3.portrait_on = true
		var tl := [[0.0, "grin"], [1.2, "laugh"], [2.6, "worried"], [3.8, "sob"], [5.6, "rage"], [7.0, "smug"], [8.2, "surprise"], [9.2, "grin"]]
		var total := 10.4
		var idx := 0
		for f in int(total * fps):
			var tt: float = float(f) / fps
			while idx < tl.size() and tl[idx][0] <= tt:
				h3.set_expr(tl[idx][1]); idx += 1
			h3.gaze = Vector2(sin(tt * 0.9) * 0.7, sin(tt * 0.6) * 0.3)
			h3.talk = 1.0 if tt > 9.3 else 0.0
			h3.pose(tt * 3.2)
			await get_tree().process_frame
			await get_tree().process_frame
			h3.ptex().get_image().save_png("%s/f%04d.png" % [a[0], f])
		get_tree().quit()
		return
	if a.size() > 2 and a[2] == "legs":
		var hl = m.hero3d
		m.set_process(false)
		hl.fixed_dt = 1.0 / 30.0
		var lg := FileAccess.open("/tmp/legs.log", FileAccess.WRITE)
		for mode in ["hula", "dance"]:
			hl.gesture(mode); hl.gest_cur = mode; hl.gk = 1.0 if mode != "hula" else 0.0
			var mn := Vector3(9, 9, 9); var mx := Vector3(-9, -9, -9)
			for f in 90:
				hl._clock = f / 30.0
				hl.pose(f / 30.0 * 3.2)
				var p1: Vector3 = (hl.j["ankle_l"] as Node3D).global_position
				mn = mn.min(p1); mx = mx.max(p1)
			lg.store_line("%s left ankle range: x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f" % [mode, mn.x, mx.x, mn.y, mx.y, mn.z, mx.z])
		lg.close()
		get_tree().quit()
		return
	if a.size() > 4 and a[2] == "seq":
		# continuous clip with the springs running: a[3]=gesture, a[4]=seconds; one png per frame at 24 fps
		var hs = m.hero3d
		m.set_process(false)
		hs.fixed_dt = 1.0 / 24.0
		hs.vp.size = Vector2i(420, 570)
		hs.gesture(a[3])
		var nf := int(float(a[4]) * 24.0)
		for f in nf:
			hs.pose(f / 24.0 * 3.2)
			await get_tree().process_frame
			hs.tex().get_image().save_png("%s/f%04d.png" % [a[0], f])
		get_tree().quit()
		return
	if a.size() > 3 and a[2] == "views":
		# a[3] = gesture; renders front / side / back / three-quarter at time a[4]
		var hv = m.hero3d
		m.set_process(false)
		hv.fixed_dt = 1.0 / 30.0
		hv.vp.size = Vector2i(600, 800)
		hv.gesture(a[3]); hv.gest_cur = a[3]; hv.gk = 1.0 if a[3] != "hula" else 0.0
		var k := 0
		for yw in [0.0, 1.57, 3.14, -0.8]:
			hv.yaw = yw
			hv._clock = float(a[4]) if a.size() > 4 else 2.4
			hv.snap = true; hv.pose(float(a[4]) * 3.2 if a.size() > 4 else 1.0)
			await get_tree().process_frame
			await get_tree().process_frame
			hv.tex().get_image().save_png("%s/v%d.png" % [a[0], k]); k += 1
		get_tree().quit()
		return
	if a.size() > 2 and a[2] == "auto":
		# menu auto-dance test: simulate the title screen for 12 s, log gesture state
		var ha = m.hero3d
		m.set_process(false)
		ha.fixed_dt = 1.0 / 30.0; ha.auto_dance = true
		var lg := FileAccess.open("/tmp/auto.log", FileAccess.WRITE)
		for f in 360:
			ha.pose(f / 30.0 * 3.2)
			if f % 15 == 0: lg.store_line("t=%.1f clock=%.2f want=%s cur=%s gk=%.2f" % [f / 30.0, ha._clock, ha.gest, ha.gest_cur, ha.gk])
		lg.close()
		get_tree().quit()
		return
	if a.size() > 3 and a[2] == "gest":
		# gesture test: a[0]=out dir, a[3]=gesture names; 6 frames across 1.3 s each, one png per frame
		var hg = m.hero3d
		m.set_process(false)
		hg.fixed_dt = 1.0 / 30.0
		for nm in String(a[3]).split(","):
			hg.gesture(nm); hg.gest_cur = nm; hg.gk = 1.0
			for fi in 6:
				hg._clock = 2.0 + fi * 0.25
				hg.snap = true; hg.pose(0.0)
				await get_tree().process_frame
				await get_tree().process_frame
				hg.tex().get_image().save_png("%s/%s_%d.png" % [a[0], nm, fi])
		get_tree().quit()
		return
	if a.size() > 2 and a[2] == "arms":
		# arm test: a[0]=out dir. Four phases of the hula sweep, then each reaction held, one png (whole body) per pose.
		var h4 = m.hero3d
		m.set_process(false)
		h4.fixed_dt = 1.0 / 30.0
		h4.vp.size = Vector2i(420, 570)
		var poses := [["w0", "", 0.0], ["w1", "", 1.57], ["w2", "", 3.14], ["w3", "", 4.71], ["flinch", "flinch", 0.0], ["cheer", "cheer", 0.0], ["limp", "limp", 0.0]]
		for ps in poses:
			h4.arm_kick(ps[1], 999.0 if ps[1] != "" else 0.0)
			for i in 40:
				h4.pose(ps[2])
			await get_tree().process_frame
			await get_tree().process_frame
			h4.tex().get_image().save_png("%s/%s.png" % [a[0], ps[0]])
		get_tree().quit()
		return
	if a.size() > 2 and a[2] == "portrait":
		var h2 = m.hero3d
		m.start_run()
		if a.size() > 3: h2.set_expr(a[3], true)
		for i in n:
			await get_tree().process_frame
		h2.ptex().get_image().save_png(a[0])
		get_tree().quit()
		return
	if a.size() > 3 and a[2] == "sheet":
		# face sheet: a[0]=out dir, a[3]=comma-separated expression names; one png per expression (hat hidden, face close-up)
		var h = m.hero3d
		m.set_process(false)   # the game loop would keep setting the menu mood
		h.auto_blink = false
		h.vp.size = Vector2i(400, 400)
		h.cam.look_at_from_position(Vector3(0.0, 1.57, 1.1), Vector3(0, 1.5, 0))
		h.j.hat.visible = false
		for nm in a[3].split(","):
			h.set_expr(nm, true)
			h.pose(0.0)
			h.set_expr(nm, true)
			h.pose(0.0)
			await get_tree().process_frame
			await get_tree().process_frame
			h.tex().get_image().save_png(a[0] + "/" + nm + ".png")
		get_tree().quit()
		return
	for i in n: await get_tree().process_frame
	if a.size() > 2 and a[2] == "face":
		var h = m.hero3d
		h.vp.size = Vector2i(600, 600)
		h.cam.look_at_from_position(Vector3(0.0, 1.56, 1.25), Vector3(0, 1.5, 0))
		h.j.hat.visible = false if a.size() > 4 else true
		h.pose(float(a[3]))
		await get_tree().process_frame
		await get_tree().process_frame
		h.tex().get_image().save_png(a[0])
	elif a.size() > 2 and a[2] == "herotex":
		m.hero3d.pose(float(a[3]))
		await get_tree().process_frame
		await get_tree().process_frame
		m.hero3d.tex().get_image().save_png(a[0])
	else:
		get_viewport().get_texture().get_image().save_png(a[0])
	get_tree().quit()
