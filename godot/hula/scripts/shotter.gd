extends Node
# test helper: args after "--": out.png frames [play]
func _ready() -> void:
	var a := OS.get_cmdline_user_args()
	var m = get_parent()
	if a.size() > 2 and a[2] == "play": m.start_run()
	var n := int(a[1])
	for i in n: await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(a[0])
	get_tree().quit()
