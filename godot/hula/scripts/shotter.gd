extends Node
# test helper: args after "--": out.png frames [play]
# Every harness run starts from the same RNG state, so clip/hat logs and face renders are reproducible.
# Pass seed=<n> anywhere in the args to use a different one; normal launches are untouched.
const SEED := 20261118
func _ready() -> void:
	await get_tree().process_frame
	var a := OS.get_cmdline_user_args()
	if a.size() < 2:
		queue_free()   # normal launch (no "-- out.png frames ..." args): this is only a test helper
		return
	var sd := SEED
	for arg in a:
		if arg.begins_with("seed="): sd = int(arg.substr(5))
	seed(sd)   # shotter is a child, so this runs before main/_ready builds the hero: even its first randf is repeatable
	print("shotter: rng seed %d" % sd)
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
	if a.size() > 3 and a[2] == "face":
		# a[0]=out dir, a[3]=comma list of expressions: each is held 1 s (24 fps, springs and couplings running), portrait saved at the end
		var hf = m.hero3d
		m.set_process(false)
		hf.fixed_dt = 1.0 / 24.0
		hf.portrait_on = true
		hf.pvp.size = Vector2i(640, 640)
		hf.auto_blink = false
		hf.gesture("hula")
		for nm in a[3].split(","):
			hf.set_expr(nm, false)
			for f in 24:
				hf.pose(f / 24.0)
				await get_tree().process_frame
			hf.ptex().get_image().save_png("%s/%s.png" % [a[0], nm])
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
		h.fixed_dt = 1.0 / 24.0   # no wall-clock dt: the face's breathing/twitch channels must be repeatable too
		h.vp.size = Vector2i(400, 400)
		var fyaw := float(a[4]) if a.size() > 4 else 0.0     # orbit the face camera so the profile can be checked too
		var fc := Vector3(0.0, 1.585, 0.09)                  # orbit around the face, not the body axis
		h.cam.look_at_from_position(fc + Vector3(sin(fyaw), 0.0, cos(fyaw)) * 0.82, fc)
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
	if a.size() > 5 and a[2] == "beat":
		# coordinator harness: drive the dance from a synthetic musical beat and log the motion, so beat-lock can be measured.
		# args: a[0]=out dir, a[3]=gesture, a[4]=beats to run, a[5]=steps per beat,
		#       a[6]=beat at which the gesture is triggered (default 0), a[7]=="fallback" to use the internal clock instead
		var hb = m.hero3d
		m.set_process(false)
		var spb := int(a[5])
		var start_beat := float(a[6]) if a.size() > 6 else 0.0
		hb.fixed_dt = 1.0 / (float(spb) * 2.0)   # one commanded beat == 1/BPS seconds of internal clock
		hb.set("beat_bpm", 120.0)
		hb.set("beat_on", not (a.size() > 7 and a[7] == "fallback"))
		var lg := FileAccess.open("%s/beat_%s_%.2f.csv" % [a[0], a[3], start_beat], FileAccess.WRITE)
		lg.store_line("beat,yaw,handdist,hand_l_y,hand_r_y,ankle_l_y,ankle_r_y,gest_cur,gk")
		var trigger := true
		for s in int(float(a[4]) * spb):
			var bt := start_beat + float(s) / float(spb)
			if trigger:
				# trigger the gesture at start_beat, exactly like the game does (blend out of hula first)
				hb.gesture(a[3]); hb.gest_cur = "hula"; hb.gk = 0.0; trigger = false
			hb.set("beat", bt)
			if a.size() > 9 and a[9] == "barfeed": hb.set("beat_bar", fmod(bt, 4.0))   # mimic the producer: beats into the 4/4 bar
			hb._clock = bt * 0.5
			hb.snap = not (a.size() > 8 and a[8] == "nosnap")
			hb.pose(0.0)
			var hl: Vector3 = (hb.j["hand_l"] as Node3D).global_position
			var hr: Vector3 = (hb.j["hand_r"] as Node3D).global_position
			var al: Vector3 = (hb.j["ankle_l"] as Node3D).global_position
			var ar: Vector3 = (hb.j["ankle_r"] as Node3D).global_position
			lg.store_line("%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%s,%.3f" % [bt, (hb.root as Node3D).rotation.y, hl.distance_to(hr), hl.y, hr.y, al.y, ar.y, hb.gest_cur, hb.gk])
		lg.close()
		get_tree().quit()
		return
	if a.size() > 5 and a[2] == "clip":
		# coordinator: log the arm joints and the hat in world space, so sombrero clipping can be measured numerically
		# args: a[0]=out dir, a[3]=gesture, a[4]=beats, a[5]=steps/beat, a[6]=optional arm_kick to hold ("cheer"/"flinch"/"limp")
		var hc = m.hero3d
		m.set_process(false)
		var cspb := int(a[5])
		hc.fixed_dt = 1.0 / (float(cspb) * 2.0)
		hc.set("beat_on", true)
		hc.gesture(a[3]); hc.gest_cur = a[3]; hc.gk = 1.0 if a[3] != "hula" else 0.0
		if a.size() > 6 and a[6] != "": hc.arm_kick(a[6], 999.0)
		var cg := FileAccess.open("%s/clip_%s.csv" % [a[0], a[3]], FileAccess.WRITE)
		cg.store_line("beat,hatx,haty,hatz,shlx,shly,shlz,ellx,elly,ellz,halx,haly,halz,shrx,shry,shrz,elrx,elry,elrz,harx,hary,harz")
		for s in int(float(a[4]) * cspb):
			var bt2 := float(s) / float(cspb)
			hc.set("beat", bt2)
			hc._clock = bt2 * 0.5
			hc.snap = true
			hc.pose(0.0)
			var hp: Vector3 = (hc.j.hat as Node3D).global_position
			var shl: Vector3 = (hc.j.shoulder_l as Node3D).global_position
			var ell: Vector3 = (hc.j.elbow_l as Node3D).global_position
			var hal: Vector3 = (hc.j.hand_l as Node3D).global_position
			var shr: Vector3 = (hc.j.shoulder_r as Node3D).global_position
			var elr: Vector3 = (hc.j.elbow_r as Node3D).global_position
			var har: Vector3 = (hc.j.hand_r as Node3D).global_position
			var line := "%.4f" % bt2
			for v in [hp, shl, ell, hal, shr, elr, har]:
				line += ",%.4f,%.4f,%.4f" % [v.x, v.y, v.z]
			cg.store_line(line)
		cg.close()
		get_tree().quit()
		return
	if a.size() > 2 and a[2] == "live":
		# end-to-end: main._process is NOT disabled, so the real music feeds hero3d.beat; log the hero's clock and body every frame
		var hl = m.hero3d
		var lg := FileAccess.open("%s/live.csv" % a[0], FileAccess.WRITE)
		lg.store_line("t,beat,beat_on,phrase0,gest,gk,talk,handdist,yaw")
		for f in n:
			await get_tree().process_frame
			var hd2: Vector3 = (hl.j["hand_l"] as Node3D).global_position
			var hr2: Vector3 = (hl.j["hand_r"] as Node3D).global_position
			lg.store_line("%.4f,%.4f,%s,%.4f,%s,%.3f,%.3f,%.4f,%.4f" % [m.t, hl.beat, str(hl.beat_on), hl._phrase0, hl.gest_cur, hl.gk, hl.talk, hd2.distance_to(hr2), (hl.root as Node3D).rotation.y])
		lg.close()
		get_tree().quit()
		return
	if a.size() > 2 and a[2] == "glb":
		# authoring export: build the hero, settle it into one expression, then write the whole rig out as glTF
		# (.glb) so it can be opened and edited in Blender. args: a[0]=res:// path, a[3]=expression (default neutral)
		# The mesh is now authored in Blender (blender/character_rigged.blend is the master), so this generator is
		# frozen: it will not overwrite an existing export unless you pass "force" (it would clobber the sculpt).
		var hx = m.hero3d
		if FileAccess.file_exists(a[0]) and not a.has("force"):
			print("glb: %s exists - the .blend is the master now; pass 'force' to regenerate from code" % a[0])
			get_tree().quit()
			return
		m.set_process(false)
		hx.rig_skel = null       # export the control rig itself, so the procedural parts (the mouth tubes) get built
		hx.fixed_dt = 1.0 / 24.0
		hx.set_expr(a[3] if a.size() > 3 else "neutral", true)
		for i in 4:
			hx.pose(0.0)
			await get_tree().process_frame
		# Write the reference rig: the control joints' world transforms at the exported pose. The game needs these to
		# map its joint transforms onto the file's bones (Blender's bone rests are not the empty transforms), and this
		# way it reads them from the file instead of trying to reproduce the export pose. Done before the prune, which
		# frees hidden joints that are still listed in the rig.
		var ref := {}
		for name in hx.j:
			var nd: Node3D = hx.j[name]
			if not is_instance_valid(nd): continue
			var gt: Transform3D = nd.global_transform
			ref[name] = [gt.basis.x.x, gt.basis.x.y, gt.basis.x.z, gt.basis.y.x, gt.basis.y.y, gt.basis.y.z, gt.basis.z.x, gt.basis.z.y, gt.basis.z.z, gt.origin.x, gt.origin.y, gt.origin.z]
		var jf := FileAccess.open("res://art/character_rig.json", FileAccess.WRITE)
		jf.store_string(JSON.stringify(ref)); jf.close()
		print("glb: wrote reference rig (%d joints)" % ref.size())
		# Drop the hidden parts before exporting. A hidden node is a part's on/off switch, so prune its whole subtree.
		# They carry no visible geometry, but a hidden node makes Godot write KHR_node_visibility into
		# extensionsRequired, and Blender does not implement that extension, so it refuses the file.
		var doomed: Array = []
		var stack: Array = [hx.root]
		while not stack.is_empty():
			var nd: Node = stack.pop_back()
			if nd is Node3D and not (nd as Node3D).visible:
				doomed.append(nd)
				continue                     # its children are hidden with it
			for c in nd.get_children(): stack.append(c)
		for nd in doomed:
			nd.get_parent().remove_child(nd)
			nd.free()
		print("glb: pruned %d hidden parts" % doomed.size())
		var doc := GLTFDocument.new()
		var st := GLTFState.new()
		var ae := doc.append_from_scene(hx.root, st)
		var we := doc.write_to_filesystem(st, a[0])
		print("glb: append=%d write=%d nodes=%d -> %s" % [ae, we, st.get_nodes().size(), a[0]])
		get_tree().quit()
		return
	for i in n: await get_tree().process_frame
	if a.size() > 2 and a[2] == "face":
		var h = m.hero3d
		h.fixed_dt = 1.0 / 24.0
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
