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
			m.menu.song_test = a[3]; m.snd.start_music(a[3])
	if a.size() > 3 and a[2] == "hub": m.menu.open_hub(int(a[3]))
	var n := int(a[1])
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
