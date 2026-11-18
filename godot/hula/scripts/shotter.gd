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
