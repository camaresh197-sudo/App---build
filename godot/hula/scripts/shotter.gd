extends Node
# test helper: args after "--": out.png frames [play]
func _ready() -> void:
	await get_tree().process_frame
	var a := OS.get_cmdline_user_args()
	var m = get_parent()
	if a.size() > 2 and a[2] == "play": m.start_run()
	if a.size() > 3 and a[2] == "hub": m.menu.open_hub(int(a[3]))
	var n := int(a[1])
	for i in n: await get_tree().process_frame
	if a.size() > 2 and a[2] == "herotex":
		m.hero3d.pose(float(a[3]))
		await get_tree().process_frame
		await get_tree().process_frame
		m.hero3d.tex().get_image().save_png(a[0])
	else:
		get_viewport().get_texture().get_image().save_png(a[0])
	get_tree().quit()
