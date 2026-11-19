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
		var hx = m.hero3d
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
	if a.size() > 3 and a[2] == "mix":
		# audio QA: play one track in real time and capture the Master bus in front of and behind the limiter.
		# args: a[0]=out .wav ("-" to skip), a[3]=track, a[4]=seconds (default 12). Levels are printed as one line each.
		var track: String = a[3]
		var secs: float = float(a[4]) if a.size() > 4 else 12.0
		var pre_cap := AudioEffectCapture.new(); pre_cap.buffer_length = 4.0
		var post_cap := AudioEffectCapture.new(); post_cap.buffer_length = 4.0
		AudioServer.add_bus_effect(0, pre_cap, 0)   # before the limiter: the raw sum the limiter has to tame
		AudioServer.add_bus_effect(0, post_cap)     # after it: what actually reaches the speakers
		var mb := AudioServer.get_bus_index("Music")
		var mpre_cap := AudioEffectCapture.new(); mpre_cap.buffer_length = 4.0
		var mpost_cap := AudioEffectCapture.new(); mpost_cap.buffer_length = 4.0
		AudioServer.add_bus_effect(mb, mpre_cap, 0)   # the Music bus in front of its reverb
		AudioServer.add_bus_effect(mb, mpost_cap)     # and behind it, to see how much the reverb adds
		m.set_process(false)
		m.snd.set_volumes(8, 8)                     # pin the mix buses so runs stay comparable
		m.snd.start_music(track)
		if a.size() > 5 and a[5] == "play":         # end-to-end: let the real game run so music and SFX overlap
			m.set_process(true)
			m.start_run()
		Engine.max_fps = 60                         # steady dt keeps the sequencer timing repeatable
		var pre := PackedVector2Array(); var post := PackedVector2Array()
		var mpre := PackedVector2Array(); var mpost := PackedVector2Array()
		var t0 := Time.get_ticks_msec()
		while Time.get_ticks_msec() - t0 < int(secs * 1000.0):
			await get_tree().process_frame
			var n1 := pre_cap.get_frames_available()
			if n1 > 0: pre.append_array(pre_cap.get_buffer(n1))
			var n2 := post_cap.get_frames_available()
			if n2 > 0: post.append_array(post_cap.get_buffer(n2))
			var n3 := mpre_cap.get_frames_available()
			if n3 > 0: mpre.append_array(mpre_cap.get_buffer(n3))
			var n4 := mpost_cap.get_frames_available()
			if n4 > 0: mpost.append_array(mpost_cap.get_buffer(n4))
		var sr := AudioServer.get_mix_rate()
		_audio_report("PRE ", pre, sr)
		_audio_report("POST", post, sr)
		_audio_report("Mpre", mpre, sr)
		_audio_report("Mpst", mpost, sr)
		if a[0] != "-": _audio_wav(a[0], post, sr)
		print("mix: track=%s secs=%.1f sr=%d frames=%d" % [track, secs, sr, post.size()])
		get_tree().quit()
		return
	if a.size() > 2 and a[2] == "sfx":
		# audio QA: fire each one-shot once with the music muted and report its level, so SFX loudness can be
		# compared against the music bed. args: a[0]=out .wav ("-" to skip), a[3]=comma list (default: all)
		var cap := AudioEffectCapture.new(); cap.buffer_length = 4.0
		AudioServer.add_bus_effect(0, cap, 0)
		m.set_process(false)
		m.snd.set_volumes(8, 8)
		Engine.max_fps = 60
		AudioServer.set_bus_mute(AudioServer.get_bus_index("Music"), true)
		AudioServer.set_bus_mute(AudioServer.get_bus_index("Vox"), true)
		var sr := AudioServer.get_mix_rate()
		var all := ["shoot", "hit", "pop", "coin", "click", "hurt", "beat", "buy", "power", "level", "trophy", "trumpet", "shield", "boss"]
		var names: Array = String(a[3]).split(",") if a.size() > 3 else all
		var mix := PackedVector2Array()
		for nm in names:
			cap.clear_buffer()
			m.snd.sfx(nm)
			var acc := PackedVector2Array()
			var t0 := Time.get_ticks_msec()
			while Time.get_ticks_msec() - t0 < 700:
				await get_tree().process_frame
				var nf := cap.get_frames_available()
				if nf > 0: acc.append_array(cap.get_buffer(nf))
			_audio_report("sfx %-8s" % nm, acc, sr)
			mix.append_array(acc)
		if a[0] != "-": _audio_wav(a[0], mix, sr)
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

# ---------- audio QA helpers (used by the "mix" mode) ----------
func _db(x: float) -> float:
	return linear_to_db(maxf(1e-9, x))

# Level summary of a stereo capture: peak, RMS, crest factor, hard-clip count, DC and a 3-band split.
# The bands use one-pole filters (cheap, order-1), enough to spot a mix that is bottom-heavy or top-heavy.
func _audio_report(tag: String, x: PackedVector2Array, sr: int) -> void:
	var n := x.size()
	if n == 0:
		print("%s: no frames" % tag); return
	var a_lo := 1.0 - exp(-TAU * 200.0 / sr)
	var a_hi := 1.0 - exp(-TAU * 2000.0 / sr)
	var peak := 0.0; var sumsq := 0.0; var clip := 0; var dc := 0.0
	var lo := 0.0; var hi := 0.0; var lsq := 0.0; var msq := 0.0; var hsq := 0.0
	for i in n:
		var s := (x[i].x + x[i].y) * 0.5
		var ab := absf(s)
		if ab > peak: peak = ab
		if ab >= 0.999: clip += 1
		sumsq += s * s; dc += s
		lo += a_lo * (s - lo)
		hi += a_hi * (s - hi)
		var mid := s - lo - hi
		lsq += lo * lo; msq += mid * mid; hsq += hi * hi
	var rms := sqrt(sumsq / n)
	print("%s peak=%.1f dBFS  rms=%.1f dBFS  crest=%.1f dB  clip=%d  dc=%.4f  lo/mid/hi=%.1f/%.1f/%.1f dB" % [tag, _db(peak), _db(rms), _db(peak) - _db(rms), clip, dc / n, _db(sqrt(lsq / n)), _db(sqrt(msq / n)), _db(sqrt(hsq / n))])

func _audio_wav(path: String, x: PackedVector2Array, sr: int) -> void:
	var b := PackedByteArray(); b.resize(x.size() * 4)
	var j := 0
	for i in x.size():
		b.encode_s16(j, int(clampf(x[i].x, -1.0, 1.0) * 32767.0))
		b.encode_s16(j + 2, int(clampf(x[i].y, -1.0, 1.0) * 32767.0))
		j += 4
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = sr
	w.stereo = true
	w.data = b
	print("wav: %s err=%d frames=%d" % [path, w.save_to_wav(path), x.size()])
