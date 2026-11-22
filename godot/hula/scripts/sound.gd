extends Node
# Audio: sample bank (real instrument + drum samples rendered from a soundfont), SFX, and the game's mariachi song played by a step sequencer.
# Samples live in res://audio (assets pack). Everything is guarded, so the game still runs silent if the pack hasn't arrived yet.
const E := 0.13               # seconds per eighth-note slot (6 per bar, 6/8 feel)
const SMP_MUS := 0.25
const TRIM := {"guitar": 1.0, "bass": 1.0, "trumpet": 1.0, "violin": 1.0, "accordion": 1.0, "pad": 1.0, "choir": 1.0, "bell": 1.0, "kick": 1.25, "snare": 0.62, "hat": 0.3, "shaker": 0.38, "clap": 0.18, "cymbal": 0.26, "tom": 1.15, "impact": 1.43, "riser": 0.5, "crowd": 0.69}
# one-shot output gain (linear), independent of the instrument TRIM so the drums the SFX borrow do not set their level.
# Measured so every SFX lands near the same peak; the old per-sample TRIM values spanned ~27 dB, which buried
# shoot/coin/click under the music while hurt blared.
const SFX_LVL := {"shoot": 0.5, "hit": 0.43, "pop": 0.25, "coin": 0.38, "click": 0.37, "hurt": 0.38, "beat": 0.35, "buy": 0.42, "power": 0.39, "level": 0.4, "trophy": 0.42, "trumpet": 0.4, "shield": 0.41, "boss": 0.4}
# melodic instruments: [lowest root, highest root], roots every 2 semitones; each root has a second take "_2"
const RANGE := {"guitar": [40, 88], "bass": [28, 64], "trumpet": [52, 88], "violin": [55, 99], "accordion": [48, 84], "pad": [40, 80], "choir": [48, 84], "bell": [60, 100], "grunt": [40, 50]}
const NVOICE := 40

var voices: Array = []        # AudioStreamPlayer pool
var vstop: Array = []         # per voice: time to release (0 = none)
var vbase: Array = []         # per voice: base volume db
var vstart: Array = []        # per voice: start time
var vatt: Array = []          # per voice: attack (fade-in) seconds
var cache := {}
var later: Array = []         # [time, Callable]
var now := 0.0
var last := {}
var song: Array = []
var title: Array = []
var vic: Array = []
var vox: Dictionary = {}
var cutscenes: Dictionary = {}  # cutscene id -> data array
var vox_only := false         # test switch: only the sung clips play
var solo_grunt := false       # test switch: only the grunt ad-libs play
var mute_grunt := false       # test switch: mute the grunt ad-libs (vocal-ducking QA)
var cur := "game"
var boost := 1.0              # per-track gain, set in start_music() so the three songs are equally loud
var playing := false
var step := 0
var next_t := 0.0
var beat_t := 0.0            # sequencer time of beat 0 for the current track (the first audible downbeat, next_t)
var bar_t := 0.0             # sequencer time the current bar's step 0 fired (the bar boundary; victory hold bars are half-length)
var loop_from := 0
var vol_music := 0.8
var vol_sfx := 0.8
var have := false

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	process_priority = -1   # run our clock before main reads beat_pos()
	_buses()
	for i in NVOICE:
		var p := AudioStreamPlayer.new(); add_child(p); voices.append(p); vstop.append(0.0); vbase.append(0.0); vstart.append(0.0); vatt.append(0.0)
	var f := FileAccess.open("res://data/data_song.json", FileAccess.READ)
	if f: song = JSON.parse_string(f.get_as_text())
	var f4 := FileAccess.open("res://data/data_vox.json", FileAccess.READ)
	if f4: vox = JSON.parse_string(f4.get_as_text())
	var f3 := FileAccess.open("res://data/data_victory.json", FileAccess.READ)
	if f3: vic = JSON.parse_string(f3.get_as_text())
	var f2 := FileAccess.open("res://data/data_title.json", FileAccess.READ)
	if f2: title = JSON.parse_string(f2.get_as_text())
	var fcs := FileAccess.open("res://data/data_cutscenes.json", FileAccess.READ)
	if fcs:
		var cs_data = JSON.parse_string(fcs.get_as_text())
		if cs_data and cs_data.has("data"):
			cutscenes = cs_data["data"]
	for i in song.size():
		if song[i][7] == 0: loop_from = i; break
	have = ResourceLoader.exists("res://audio/kick.ogg")

func _buses() -> void:
	# Create all buses if they don't exist
	var bus_names = ["Music", "SFX", "Vox", "VoxGrunt", "Cutscene", "Ambient", "UI"]
	for nm in bus_names:
		if AudioServer.get_bus_index(nm) < 0:
			AudioServer.add_bus(); var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, nm); AudioServer.set_bus_send(i, "Master")

	# MASTER BUS - Limiting and metering
	if AudioServer.get_bus_effect_count(0) == 0:
		if ClassDB.class_exists("AudioEffectHardLimiter"):
			var lim = ClassDB.instantiate("AudioEffectHardLimiter")
			lim.pre_gain_db = 0.0
			lim.ceiling_db = -0.5
			AudioServer.add_bus_effect(0, lim)

	# MUSIC BUS - Warm room with musical reverb
	var mb := AudioServer.get_bus_index("Music")
	if AudioServer.get_bus_effect_count(mb) == 0:
		# Compression for consistent levels
		var mc := AudioEffectCompressor.new()
		mc.threshold = -20.0; mc.ratio = 2.0; mc.attack_us = 50000.0; mc.release_ms = 300.0; mc.gain = 0.0
		AudioServer.add_bus_effect(mb, mc)
		# Warm reverb for musical ambience
		var mr := AudioEffectReverb.new()
		mr.room_size = 0.55; mr.damping = 0.5; mr.wet = 0.16; mr.dry = 0.9; mr.hipass = 0.1
		AudioServer.add_bus_effect(mb, mr)

	# SFX BUS - Punchy compression, dry
	var sb := AudioServer.get_bus_index("SFX")
	if AudioServer.get_bus_effect_count(sb) == 0:
		# Heavy compression to tame transients
		var sc := AudioEffectCompressor.new()
		sc.threshold = -15.0; sc.ratio = 4.0; sc.attack_us = 10000.0; sc.release_ms = 200.0; sc.gain = 2.0
		AudioServer.add_bus_effect(sb, sc)

	# VOICE/VOX BUS - Clean dialogue with controlled room
	var vb := AudioServer.get_bus_index("Vox")
	if AudioServer.get_bus_effect_count(vb) == 0:
		# Tight compression for consistent vocal levels
		var vc := AudioEffectCompressor.new()
		vc.threshold = -10.0; vc.ratio = 1.5; vc.attack_us = 12000.0; vc.release_ms = 180.0; vc.gain = 0.0
		AudioServer.add_bus_effect(vb, vc)
		# Near-dry room: the vocals are already a multi-take render, and any
		# more wet reads as a slap/echo behind the words.
		var vr := AudioEffectReverb.new()
		vr.room_size = 0.3; vr.damping = 0.75; vr.wet = 0.05; vr.dry = 1.0
		AudioServer.add_bus_effect(vb, vr)

	# VOCAL GRUNT BUS - Separate compression for ad-libs
	var gb := AudioServer.get_bus_index("VoxGrunt")
	if AudioServer.get_bus_effect_count(gb) == 0:
		# Keep grunts from hitting limiter
		var gc := AudioEffectCompressor.new()
		gc.threshold = -4.0; gc.ratio = 2.5; gc.attack_us = 5000.0; gc.release_ms = 120.0; gc.gain = 0.0
		AudioServer.add_bus_effect(gb, gc)
		# Matching room as Vox (near-dry)
		var gr := AudioEffectReverb.new()
		gr.room_size = 0.3; gr.damping = 0.75; gr.wet = 0.04; gr.dry = 1.0
		AudioServer.add_bus_effect(gb, gr)

	# CUTSCENE BUS - Clean, tight, minimal effects
	var csb := AudioServer.get_bus_index("Cutscene")
	if AudioServer.get_bus_effect_count(csb) == 0:
		# Compression for consistent dialogue levels
		var csc := AudioEffectCompressor.new()
		csc.threshold = -18.0; csc.ratio = 3.0; csc.attack_us = 15000.0; csc.release_ms = 200.0; csc.gain = 1.0
		AudioServer.add_bus_effect(csb, csc)
		# Minimal reverb for clarity
		var cr := AudioEffectReverb.new()
		cr.room_size = 0.2; cr.damping = 0.8; cr.wet = 0.05; cr.dry = 0.95; cr.hipass = 0.3
		AudioServer.add_bus_effect(csb, cr)

	# AMBIENT BUS - Warm, wide atmosphere
	var ab := AudioServer.get_bus_index("Ambient")
	if AudioServer.get_bus_effect_count(ab) == 0:
		# Light compression
		var ac := AudioEffectCompressor.new()
		ac.threshold = -25.0; ac.ratio = 1.2; ac.attack_us = 100000.0; ac.release_ms = 500.0; ac.gain = 0.0
		AudioServer.add_bus_effect(ab, ac)
		# Large room for ambient
		var ar := AudioEffectReverb.new()
		ar.room_size = 0.8; ar.damping = 0.3; ar.wet = 0.25; ar.dry = 0.85; ar.hipass = 0.05
		AudioServer.add_bus_effect(ab, ar)

	# UI BUS - Tight, dry, punchy
	var ub := AudioServer.get_bus_index("UI")
	if AudioServer.get_bus_effect_count(ub) == 0:
		# Heavy compression for consistent UI feedback
		var uc := AudioEffectCompressor.new()
		uc.threshold = -12.0; uc.ratio = 5.0; uc.attack_us = 5000.0; uc.release_ms = 100.0; uc.gain = 2.0
		AudioServer.add_bus_effect(ub, uc)

func set_volumes(music10: int, sfx10: int) -> void:
	vol_music = music10 / 10.0; vol_sfx = sfx10 / 10.0
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Music"), linear_to_db(maxf(0.0001, vol_music * 0.7)))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("SFX"), linear_to_db(maxf(0.0001, vol_sfx)))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Vox"), linear_to_db(maxf(0.0001, vol_music * 0.7)))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("VoxGrunt"), linear_to_db(maxf(0.0001, vol_music * 0.7)))
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Vox"), music10 <= 0)
	AudioServer.set_bus_mute(AudioServer.get_bus_index("VoxGrunt"), music10 <= 0)
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Music"), music10 <= 0)
	AudioServer.set_bus_mute(AudioServer.get_bus_index("SFX"), sfx10 <= 0)

# ---------- sample bank ----------
func _stream(key: String) -> AudioStream:
	if cache.has(key): return cache[key]
	var path := "res://audio/%s.ogg" % key
	var s: AudioStream = load(path) if ResourceLoader.exists(path) else null
	if s == null:
		var wav := "res://audio/%s.wav" % key
		s = load(wav) if ResourceLoader.exists(wav) else null
	cache[key] = s; return s

func _pick(name: String, midi: int) -> Array:   # -> [stream, root] or []
	var variant := "" if randf() < 0.5 else "_2"
	if RANGE.has(name):
		var r: Array = RANGE[name]
		var root := clampi(int(round((midi - r[0]) / 2.0)) * 2 + r[0], r[0], r[1])
		if root > r[1]: root -= 2
		var s := _stream("%s_r%d%s" % [name, root, variant])
		if s == null: s = _stream("%s_r%d" % [name, root])
		return [s, root] if s else []
	var key := name
	if name in ["kick", "snare", "hat", "tom", "shaker", "clap", "cymbal"]:
		key = name + ["", "_2", "_3"][randi() % 3]
	var s2 := _stream(key)
	return [s2, 0] if s2 else []

# one voice: v = linear gain already scaled; delay in s; dur = hold time (0 = play whole sample)
func play(name: String, o := {}) -> void:
	if not have: return
	if vox_only and not name.begins_with("vox/"): return
	if solo_grunt and name != "grunt": return
	if mute_grunt and name == "grunt": return
	# capture the duck when the note is queued: a delayed note must keep the gain of its own bar
	if duck_gain != 1.0 and not o.has("duck") and (name == "bass" or name == "guitar" or name == "bell"):
		o = o.merged({"duck": duck_gain}, true)
	var dl: float = o.get("dl", 0.0)
	if dl > 0.0:
		later.append([now + dl, play.bind(name, o.merged({"dl": 0.0}, true))]); return
	var midi: int = o.get("midi", -1)
	var pk := _pick(name, midi if midi >= 0 else 60)
	if pk.is_empty(): return
	var p: AudioStreamPlayer = null; var oldest := 1e9; var oi := 0
	for i in voices.size():
		if not voices[i].playing: p = voices[i]; oi = i; break
		if vstop[i] < oldest: oldest = vstop[i]; oi = i
	if p == null: p = voices[oi]
	p.stream = pk[0]
	p.pitch_scale = pow(2.0, (midi - pk[1]) / 12.0) * o.get("rate", 1.0) if midi >= 0 and pk[1] > 0 else o.get("rate", 1.0)
	var v: float = o.get("v", 1.0) * o.get("trim", TRIM.get(name, 1.0))
	v *= o.get("duck", 1.0)
	p.bus = o.get("bus", "Music")
	if name.begins_with("vox/"): p.bus = "Vox"
	if p.bus == "Music" or p.bus == "Vox" or p.bus == "VoxGrunt": v *= boost
	vbase[oi] = linear_to_db(maxf(0.0001, v)); p.volume_db = vbase[oi]
	var dur: float = o.get("dur", 0.0)
	vstop[oi] = (now + dur) if dur > 0.0 else 0.0
	vstart[oi] = now; vatt[oi] = o.get("att", 0.0)
	if vatt[oi] > 0.0: p.volume_db = vbase[oi] - 40.0
	p.play(float(o.get("from", 0.0)))   # "from": start offset into the clip (word-level playback)

# like play(), but the caller supplies the stream (the embedded Piper's render)
func play_stream(stream: AudioStream, o := {}) -> void:
	if not have or stream == null: return
	var dl: float = o.get("dl", 0.0)
	if dl > 0.0:
		later.append([now + dl, play_stream.bind(stream, o.merged({"dl": 0.0}, true))]); return
	var p: AudioStreamPlayer = null; var oldest := 1e9; var oi := 0
	for i in voices.size():
		if not voices[i].playing: p = voices[i]; oi = i; break
		if vstop[i] < oldest: oldest = vstop[i]; oi = i
	if p == null: p = voices[oi]
	p.stream = stream
	p.pitch_scale = o.get("rate", 1.0)
	var v: float = o.get("v", 1.0)
	p.bus = o.get("bus", "Vox")
	if p.bus == "Music" or p.bus == "Vox" or p.bus == "VoxGrunt": v *= boost
	vbase[oi] = linear_to_db(maxf(0.0001, v)); p.volume_db = vbase[oi]
	var dur: float = o.get("dur", 0.0)
	vstop[oi] = (now + dur) if dur > 0.0 else 0.0
	vstart[oi] = now; vatt[oi] = 0.0
	p.play(float(o.get("from", 0.0)))

# stop word-timing previews: drop queued Vox chunks and silence the Vox voices
func stop_vox() -> void:
	later = later.filter(_keep_after_stop)
	for i in voices.size():
		if voices[i].bus == "Vox":
			voices[i].stop(); vstop[i] = 0.0

func _keep_after_stop(e) -> bool:
	var c = e[1]
	var m := str(c.get_method())
	if m == "play_stream": return false   # the embedded Piper's preview
	if m != "play": return true
	var n: int = c.get_bound_arguments_count()
	if n == 0: return true
	var name := str(c.get_bound_arguments()[0])
	return not (name.begins_with("vox/") or name.begins_with("phon/") or name == "di_bank")

func note(name: String, midi: int, dur: float, v: float, ref: float, dl := 0.0, att := 0.0) -> void:	play(name, {"midi": midi, "dur": dur, "v": v / ref * SMP_MUS, "dl": dl, "att": att})
func hit(name: String, dl: float, v: float, ref: float) -> void:
	play(name, {"v": v / ref * SMP_MUS, "dl": dl})

# ---------- sfx ----------
func sfx(n: String, vol := 1.0) -> void:
	if not have: return
	var gap: float = {"shoot": 0.09, "hit": 0.05, "pop": 0.04, "coin": 0.05}.get(n, 0.03)
	if last.has(n) and now - last[n] < gap: return
	last[n] = now
	# shoot/hit/pop/hurt have no sample of their own, so they borrow the closest one-shots. SFX_LVL sets the level
	# for every one-shot and trim:1.0 keeps the borrowed drum's TRIM out, so SFX do not inherit the music's drum balance.
	var g: float = SFX_LVL.get(n, 0.4) * vol
	var r := 0.94 + randf() * 0.12
	if n == "shoot": play("hat", {"v": g, "trim": 1.0, "rate": 0.9 * r, "bus": "SFX"})
	elif n == "hit": play("tom", {"v": g, "trim": 1.0, "rate": 1.6 * r, "bus": "SFX"})
	elif n == "pop":
		play("snare", {"v": g, "trim": 1.0, "rate": 1.25 * r, "bus": "SFX"})
		play("sfx_coin", {"v": g, "trim": 1.0, "rate": 1.5 * r, "bus": "SFX", "dl": 0.03})
	elif n == "hurt": play("impact", {"v": g, "trim": 1.0, "rate": 1.2, "bus": "SFX"})
	else: play("sfx_" + n, {"v": g, "trim": 1.0, "rate": 0.94 + randf() * 0.12, "bus": "SFX"})

# ---------- cutscene audio ----------
var cutscene_player: AudioStreamPlayer = null

func play_cutscene_audio(audio_path: String) -> void:
	if not have:
		print("Audio not available (have=false)")
		return
	if not ResourceLoader.exists(audio_path):
		print("Cutscene audio file not found: ", audio_path)
		return
	if cutscene_player == null:
		cutscene_player = AudioStreamPlayer.new()
		add_child(cutscene_player)
		cutscene_player.bus = "Cutscene"
	var stream = load(audio_path)
	if stream == null:
		print("Failed to load audio stream: ", audio_path)
		return
	cutscene_player.stream = stream
	cutscene_player.play()
	print("Playing cutscene audio: ", audio_path)

func stop_cutscene_audio() -> void:
	if cutscene_player and cutscene_player.playing:
		cutscene_player.stop()

# ---------- music ----------
# the musical beat, so the dance can lock to the tune. tempo table derived from the step constants above:
# a bar is steps-per-bar slots; a beat is the musical pulse, bar / beats-per-bar.
#   menu:    TE 0.125 s/step x 16 steps/bar = 2.000 s/bar, 4 beats/bar -> 0.500 s/beat (120 bpm)
#   game:    E  0.130 s/step x  6 steps/bar = 0.780 s/bar, 2 beats/bar -> 0.390 s/beat (6/8 feel)
#   victory: VE 0.105 s/step x 16 steps/bar = 1.680 s/bar, 4 beats/bar -> 0.420 s/beat
const BEAT_SECS := {"menu": TE * 4.0, "game": E * 3.0, "victory": VE * 4.0, "c_fiesta": E * 3.0, "c_theft": E * 3.0, "c_fall": E * 3.0, "c_hero": E * 3.0, "c_climb": E * 3.0, "c_mission": E * 3.0, "c_pursuit1": E * 3.0, "c_pursuit2": E * 3.0, "c_reckon": E * 3.0, "c_armada": E * 3.0, "c_showdown": E * 3.0}
const BEATS_BAR := {"menu": 4, "game": 2, "victory": 4, "c_fiesta": 2, "c_theft": 2, "c_fall": 2, "c_hero": 2, "c_climb": 2, "c_mission": 2, "c_pursuit1": 2, "c_pursuit2": 2, "c_reckon": 2, "c_armada": 2, "c_showdown": 2}
func start_music(track := "game") -> void:
	if not have: return
	if track == "menu" and title.is_empty(): return
	if track == "victory" and vic.is_empty(): return
	if track == "game" and song.is_empty(): return
	if track.begins_with("c_") and not cutscenes.has(track): return
	if playing and cur == track: return
	if playing: stop_music()
	duck_gain = 1.0
	cur = track; boost = 1.8 if track == "menu" else (0.6 if track == "victory" else 1.15); playing = true; step = 0; next_t = now + 0.08; beat_t = next_t; bar_t = beat_t

# word-timing preview: the victory track starts at a row of vic (its bar starts at next_t)
func victory_row_of(sec: String, bar: int) -> int:
	for r in vic.size():
		if String(vic[r][6]) == sec and int(vic[r][7]) == bar: return r
	return -1

# steps before a row: a half-bar row (index 17 = 1) plays 8 steps, the others 16 (see _process)
func victory_row_step(row: int) -> int:
	var st := 0
	for i in range(mini(row, vic.size())):
		st += 8 if int(vic[i][17]) == 1 else 16
	return st

func start_victory_at(row: int, step_off: int = 0) -> void:
	stop_music()
	start_music("victory")
	step = victory_row_step(row) + maxi(0, step_off)
	next_t = now + 0.08; beat_t = next_t; bar_t = beat_t

func stop_music() -> void:
	playing = false
	for i in voices.size():
		if voices[i].bus == "Music": vstop[i] = now + 0.01

# beats elapsed in the current track since beat 0, from the wall clock so it stays continuous and monotonic
# even when the sequencer skips (victory step += 8) or the lag guard resets next_t.
# beat 0 is the first audible downbeat: the first step start_music schedules (next_t = now + 0.08), so the
# 0.08 s lead-in is beat 0 and the dance's downbeat lands exactly on the music's.
func beat_pos() -> float:
	if not playing: return 0.0
	return maxf(0.0, (now - beat_t) / beat_secs())

# beats into the current bar, measured from the bar's step 0 (bar_t). returns 0.0 at a bar boundary and grows
# to the bar's length, then snaps back to 0 when the next bar's step 0 fires. normal bars are beats_per_bar()
# long; a victory hold bar (field17 == 1) is only half a bar, so there it wraps at beats_per_bar() / 2.
func bar_pos() -> float:
	if not playing: return 0.0
	return maxf(0.0, (now - bar_t) / beat_secs())

func beat_secs() -> float:
	return float(BEAT_SECS.get(cur, E * 3.0))

func beats_per_bar() -> int:
	return int(BEATS_BAR.get(cur, 2))

func is_playing() -> bool:
	return playing

func _process(dt: float) -> void:
	now += dt
	var i := 0
	while i < later.size():
		if later[i][0] <= now: later[i][1].call(); later.remove_at(i)
		else: i += 1
	for k in voices.size():   # short release so held notes end without a click
		var p: AudioStreamPlayer = voices[k]
		if not p.playing: continue
		var db: float = vbase[k]
		if vatt[k] > 0.0 and now - vstart[k] < vatt[k]:
			db += linear_to_db(maxf(0.01, (now - vstart[k]) / vatt[k]))
		if vstop[k] > 0.0:
			var left: float = vstop[k] - now
			if left <= 0.0: p.stop(); vstop[k] = 0.0; continue
			elif left < 0.08: db += linear_to_db(maxf(0.01, left / 0.08))
		p.volume_db = db
	if playing:
		var guard := 0
		# schedule steps LOOK_AHEAD early: the audio is queued to the exact beat (dl > 0). Firing a step only
		# once its time had passed made dl <= 0, so every sung clip started on the beat and its vowel landed
		# about 0.15 s late, after its lead-in was clamped to zero.
		while now >= next_t - LOOK_AHEAD and guard < 4:
			if step % (6 if cur == "game" else 16) == 0: bar_t = next_t   # a bar's step 0 sounds at next_t: mark the boundary
			if cur == "menu": _tstep(step, next_t - now)
			elif cur == "victory": _vstep(step, next_t - now)
			else: _step(step, next_t - now)
			step += 1; next_t += (TE if cur == "menu" else (VE if cur == "victory" else E)); guard += 1
			if cur == "victory" and step % 16 == 8 and int(vic[(step / 16) % vic.size()][17]) == 1: step += 8   # a half bar (a held word's ring-out) plays 8 steps, then the next section starts on the beat
		if guard >= 4: next_t = now

func _harmony(m: int, v: Array, r: int) -> int:
	var pcs: Array = []
	for n in v: pcs.append(int(n) % 12)
	pcs.append(r % 12)
	for d in range(3, 6):
		if pcs.has(((m - d) % 12 + 12) % 12): return m - d
	return m - 3

func _strum(v: Array, dl: float, down: bool, vol: float) -> void:
	var notes: Array = v.duplicate()
	if not down: notes.reverse()
	for i in notes.size():
		note("guitar", notes[i], 0.24 if down else 0.15, vol * (1.0 if down else 0.8), 0.05 * sqrt(notes.size()), dl + i * 0.011)

const ARP := [[0,1,2,3,2,1], [0,2,1,3,2,1], [3,2,1,0,1,2], [0,1,2,1,2,3], [0,2,3,2,1,0]]
const STRUMV := [[1,2,4,5], [1,2,3,5], [1,3,4,5]]
func _step(st: int, dl: float) -> void:
	# Cutscenes use choreography data, not sequencer data - skip audio generation
	if cur.begins_with("c_"): return

	var data_array := song
	var nb := data_array.size()
	if nb == 0: return
	var bi := st / 6
	if bi >= nb: bi = loop_from + (bi - nb) % (nb - loop_from)
	var slot := st % 6
	var B: Array = data_array[bi]
	var r: int = B[0]; var f: int = B[1]; var cv: Array = B[2]; var mel: Array = B[3]; var inst: String = B[4]; var bar: int = B[5]
	var odd := bi % 2 == 1
	var hv := 0.9 + randf() * 0.2
	var dd := maxf(0.0, dl)
	var bass_slots: Array = [0] if inst == "break" else ([0, 3] if inst == "ballad" else ([0, 2, 4] if odd else [0, 3]))
	if bar == 0 and slot == 0: hit("cymbal", dd, 0.045, 0.05)
	if bass_slots.has(slot): note("bass", r if slot == 0 else f, 0.3, 0.2 * hv, 0.17, dd)
	# vihuela strums
	if inst == "solo":
		if slot == 2 or slot == 5: _strum(cv, dd, slot == 2, 0.03)
	elif inst == "break":
		if bar >= 6: _strum(cv, dd, slot % 2 == 1, 0.03 + 0.012 * (bar - 6))
		elif slot == 2 or slot == 5: _strum(cv, dd, slot == 2, 0.035)
	else:
		var ss: Array = [1, 3, 5] if odd else STRUMV[(bi * 7 + 3) % 3]
		if ss.has(slot): _strum(cv, dd, slot % 2 == 1, 0.05 * hv)
	# shaker + claps
	hit("shaker", dd, (0.06 if bass_slots.has(slot) else 0.032) * (1.4 if inst == "break" else 1.0), 0.05)
	if inst == "break" and bar >= 2 and (slot == 2 or slot == 5): hit("clap", dd, 0.06, 0.05)
	# kick on the downbeat + snare on the 3, light hat
	if slot == 0 and inst != "break": hit("kick", dd, 0.1, 0.17)
	if slot == 3 and inst != "break": hit("snare", dd, 0.035, 0.07)
	if slot % 2 == 1 and inst != "break": hit("hat", dd, 0.018, 0.04)
	# string pad under the violin sections
	if (inst == "violin" or inst == "duet") and slot == 0:
		for n in cv: play("pad", {"midi": int(n) - 12, "dur": E * 6.0, "v": 0.035 / 0.03 * SMP_MUS, "dl": dd})
	# guitar solo arpeggios, trumpet answers
	if inst == "solo":
		var ct: Array = cv.duplicate(); ct.append(int(cv[0]) + 12)
		var pat: Array = ARP[(bi * 3 + 1) % 5]
		var n: int = int(ct[pat[slot] % ct.size()]) + (12 if slot == 5 and bar % 4 == 3 else 0)
		note("guitar", n, 0.4, 0.1 * hv, 0.11, dd)
		if bar % 4 == 3 and slot == 4:
			for x in cv: note("trumpet", int(x), 0.22, 0.035, 0.05, dd)
	# melody
	var m: int = int(mel[slot])
	if m > 0 and inst != "solo" and inst != "break":
		var holds := 0
		while true:
			var idx := slot + 1 + holds
			var nx: int = int(mel[idx]) if idx < 6 else (int(data_array[(bi + 1) % nb][3][idx - 6]) if (bi + 1) < nb else 0)
			if nx == -1: holds += 1
			else: break
			if holds > 5: break
		var dur := (1 + holds) * E * 0.97
		if inst == "trumpet" or inst == "duet":
			var k := 0.8 if inst == "duet" else 1.0
			var d2 := dur if inst == "duet" else minf(dur, maxf(0.16, dur * 0.62))
			note("trumpet", m, d2, 0.05 * k, 0.05, dd)
			note("trumpet", _harmony(m, cv, r), d2, 0.038 * k, 0.05, dd)
		if inst == "violin" or inst == "duet":
			var k2 := 0.85 if inst == "duet" else 1.0
			play("violin", {"midi": m, "dur": dur, "v": 0.045 * k2 / 0.048 * SMP_MUS, "dl": dd})
	# end-of-section run
	if B[6] == 1 and inst != "break" and slot >= 3:
		var ct2: Array = cv.duplicate(); ct2.append(int(cv[0]) + 12)
		for j in 2:
			var rn: int = int(ct2[maxi(0, ct2.size() - 1 - ((slot - 3) * 2 + j))]) + 12
			note("guitar", rn, 0.2, 0.07, 0.11, dd + j * 0.5 * E)

# ---------- title song (ranchera polka, 16 sixteenth-steps per bar) ----------
const TE := 0.125
func _lead(kind: String, m: int, dur: float, dl: float, v: Array) -> void:
	if kind == "horn" or kind == "trump":
		note("trumpet", m, dur, 0.05, 0.05, dl); note("trumpet", _harmony(m, v, 0), dur, 0.03, 0.05, dl)
	elif kind == "violin": play("violin", {"midi": m, "dur": dur, "v": 0.048 / 0.048 * SMP_MUS, "dl": dl, "att": 0.04})
	elif kind == "duet":
		note("trumpet", m, dur, 0.04, 0.05, dl); play("violin", {"midi": m, "dur": dur, "v": 0.035 / 0.048 * SMP_MUS, "dl": dl, "att": 0.04}); note("trumpet", _harmony(m, v, 0), dur, 0.024, 0.05, dl)
	elif kind == "gtr":
		note("guitar", m, maxf(0.1, dur), 0.11, 0.11, dl); note("guitar", m + 12, 0.1, 0.03, 0.11, dl)

func _tstep(st: int, dl: float) -> void:
	var nb := title.size()
	var bi := (st / 16) % nb
	var s := st % 16
	var B: Array = title[bi]
	var r: int = B[0]; var f: int = B[1]; var cv: Array = B[2]; var mel: Array = B[3]; var lead: String = B[4]
	var hy: int = B[5]; var sec: String = B[6]; var bar: int = B[7]; var n: int = B[8]; var first: bool = B[9] == 1; var is_end: bool = B[10] == 1; var nxr: int = B[11]
	var hv := 0.9 + randf() * 0.2
	var dd := maxf(0.0, dl)
	if s == 0 and first: hit("cymbal", dd, 0.05, 0.05)
	var quiet := lead == "gtr" or (lead == "violin" and sec.ends_with("break"))
	if hy == 0 and sec == "t-intro":
		if s == 0 and bar >= 2: hit("kick", dd, 0.15, 0.17)
		if s == 8 and bar >= 2: play("tom", {"v": 0.1 / 0.14 * SMP_MUS, "rate": 100.0 / 110.0, "dl": dd})
		if bar == 3 and s >= 12: hit("snare", dd, 0.03 + (s - 12) * 0.012, 0.07)
		if s == 0:
			for x in cv: note("trumpet", int(x) + 12, TE * 5, 0.03, 0.05, dd)
	elif sec == "t-break":
		if s % 4 == 0: hit("kick", dd, 0.07, 0.17)
		if s % 4 == 2: _strum(cv, dd, (s >> 2) % 2 == 0, 0.035 * hv)
		if bar == 3 and s >= 8: hit("snare", dd, 0.025 + (s - 8) * 0.008, 0.07)
	else:
		if s % 8 == 0: hit("kick", dd, 0.15 + 0.02 * hy, 0.17)
		if s == 4 or s == 12:
			hit("snare", dd, 0.05 + 0.01 * hy, 0.07); hit("clap", dd, 0.04, 0.05)
		hit("hat", dd, 0.02 if s % 2 == 1 else 0.034, 0.04)
	if not (hy == 0 or sec == "t-break") or (sec == "t-intro" and bar >= 2):
		if s % 4 == 0: note("bass", r if s % 8 == 0 else f, TE * 2.3, (0.19 if hy >= 1 else 0.14) * hv, 0.17, dd)
		if hy >= 1 and s % 4 == 2: _strum(cv, dd, (s >> 2) % 2 == 0, 0.052 * hv)
	if hy >= 2 and (s == 0 or s == 8):
		for x in cv: note("trumpet", int(x) + 12, TE * 2.4, 0.024, 0.05, dd)
	if hy >= 3 and s % 2 == 0: play("violin", {"midi": int(cv[(s >> 1) % cv.size()]) + 24, "dur": TE * 1.6, "v": 0.012 / 0.048 * SMP_MUS, "dl": dd, "att": 0.04})
	if hy >= 2 and s % 4 == 3 and randf() < 0.5: note("bell", int(cv[(s >> 2) % cv.size()]) + 24, TE * 2, 0.016, 0.02, dd)
	if is_end and s >= 12 and hy >= 1: hit("snare", dd, 0.04 + (s - 12) * 0.012, 0.07)
	if is_end and sec == "t-C" and s == 0:
		_strum(cv, dd, true, 0.09)
		for x in cv: note("trumpet", int(x), 1.4, 0.04, 0.05, dd)
	# melody lead (the guitar / violin leads keep playing through the quiet sections)
	var m: int = int(mel[s])
	if m > 0 and (not quiet or lead == "gtr" or lead == "violin"):
		var holds := 0
		while s + 1 + holds < 16 and (int(mel[s + 1 + holds]) == -1 or (int(mel[s + 1 + holds]) == 0 and holds < 3)): holds += 1
		_lead(lead, m, (1 + holds) * TE * 0.9, dd, cv)
	# arrangement layer: string pad, bell sparkle, bass approach into the next chord, section hit
	if s == 0:
		for x in cv: note("pad", int(x), TE * 16, (0.009 + 0.004 * hy) * (1.6 if (sec.ends_with("break") or sec.ends_with("intro")) else 1.0), 0.009, dd, TE * 16 * 0.28)
	if hy >= 1 and s % 4 == 1 and not (m > 0) and randf() < 0.6:
		note("bell", int(cv[((s >> 1) + bar * 2) % cv.size()]) + (24 if hy >= 2 else 12), TE * 2.2, 0.02 * (0.85 + hy * 0.1), 0.02, dd)
	if s == 15 and not is_end and nxr != r: note("bass", nxr + (-1 if nxr > r else 1), TE * 0.9, 0.1 * hv, 0.17, dd)
	if first and s == 0 and hy >= 2: play("impact", {"v": 0.1 / 0.1 * SMP_MUS, "dl": dd})

# ---------- victory fanfare (instrumental: the tune is carried by the lead instruments) ----------
const VE := 0.105
const VOX_GAIN := 2.4
var have_vox := true
# option 1: while a sung line is on, the bass, strums, bell and chord stabs step back so the voice sits clear.
# The lines are two bars each, so a bar is "sung" when its own bar or the bar before starts a line.
const DUCK_SUNG := 0.4
var duck_gain := 1.0
const LOOK_AHEAD := 0.2     # seconds a step is scheduled before its beat
func _vox_key(sec: String, bar: int) -> String:
	if sec == "v-A": return "A%d" % bar
	if sec == "v-B": return "B%d" % (bar >> 1) if bar % 2 == 0 else ""
	if sec == "v-C": return "C%d" % bar
	if sec == "v-tag": return "tag%d" % bar
	if sec == "v-F": return "F%d" % bar
	return ""
const VFILL := {"v-intro": 0.6, "v-A": 1.0, "v-B": 0.55, "v-F": 0.25, "v-C": 1.0, "v-tag": 0.0}
# Vocal ad-libs for the chorus singer: a deep, in-character grunt on the bar's chord root (r),
# two per section on the strong steps (12/14) and the section-final bar, with an "unh-unh"
# double when the phrase needs it. Never on a held bar or the final ring-out.
# [section, bar, step]; the grunt is pitched to r so it sits on a chord tone.
const VGRUNT := [["v-A", 3, 14], ["v-A", 7, 12], ["v-A", 7, 14],
	["v-B", 1, 14], ["v-B", 3, 12], ["v-B", 5, 14], ["v-B", 7, 14],
	["v-C", 3, 14], ["v-C", 5, 12], ["v-C", 5, 14], ["v-C", 7, 14],
	["v-tag", 1, 14], ["v-tag", 3, 14],
	["v-F", 1, 12], ["v-F", 3, 14]]
const VGRUNT_V := 4.2   # grunt level (linear, before the Vox bus); the body is pre-normalized in the sample bank
func _vtrp(cv: Array, add: int, dur: float, v: float, dl: float) -> void:
	for x in cv: note("trumpet", int(x) + add, dur, v * duck_gain, 0.05, dl)

func _vstep(st: int, dl: float) -> void:
	var nb := vic.size()
	var bi := (st / 16) % nb
	var s := st % 16
	var B: Array = vic[bi]
	var r: int = B[0]; var f: int = B[1]; var cv: Array = B[2]; var mel: Array = B[3]; var lead: String = B[4]
	var hy: int = B[5]; var sec: String = B[6]; var bar: int = B[7]; var n: int = B[8]
	var first: bool = B[9] == 1; var is_end: bool = B[10] == 1; var hold: bool = B[11] == 1; var of: String = B[12]
	var fin: bool = B[13] == 1; var last: bool = B[14] == 1; var nxr: int = B[15]; var pre: bool = B[16] == 1
	var sung := have_vox and (_vox_key(sec, bar) != "" or (bar > 0 and _vox_key(sec, bar - 1) != ""))
	duck_gain = DUCK_SUNG if sung else 1.0
	var hv := 0.9 + randf() * 0.2
	var dd := maxf(0.0, dl)
	var thin := last
	var gd := not (thin and s > 0)
	if s == 0 and first and not hold: hit("cymbal", dd, 0.05, 0.05)
	if hy == 0:
		if s == 0: hit("kick", dd, 0.17, 0.17)
		if s == 8: play("tom", {"v": 0.12 / 0.14 * SMP_MUS, "rate": 95.0 / 110.0, "dl": dd})
		if s == 12 or s == 14: play("tom", {"v": 0.09 / 0.14 * SMP_MUS, "rate": 120.0 / 110.0, "dl": dd})
	elif s % 4 == 0 and gd: hit("kick", dd, 0.14 + 0.02 * hy, 0.17)
	if hy >= 1 and (s == 4 or s == 12) and gd:
		hit("snare", dd, 0.05 + 0.01 * hy, 0.07)
		if hy >= 2: hit("clap", dd, 0.05, 0.05)
	if gd:
		if hy >= 1: hit("hat", dd, 0.026 if s % 2 == 1 else 0.04, 0.04)
		elif s % 4 == 2: hit("shaker", dd, 0.04, 0.05)
	if hy >= 3 and s % 2 == 1 and gd: hit("hat", dd, 0.022, 0.04)
	if s % 4 == 0 and (hy >= 1 or s == 0) and not (thin and s % 8 != 0): note("bass", r if s % 8 == 0 else f, VE * 3.0, (0.15 if hy == 0 else 0.19) * hv, 0.17, dd)
	if s % 4 == 2 and hy >= 1 and not thin: _strum(cv, dd, (s >> 2) % 2 == 0, 0.055 * hv)
	if hy == 0 and s == 0: _strum(cv, dd, true, 0.07 * hv)
	if s == 0 or (s == 8 and hy >= 1): _vtrp(cv, 12, VE * (7.0 if hy == 0 else 2.6), 0.04 if hy == 0 else 0.03, dd)
	if hy >= 2 and s % 2 == 0: note("bell", int(cv[(s >> 1) % cv.size()]) + 24, VE * 1.5, 0.012, 0.02, dd)
	if hy >= 3 and s == 4: _vtrp(cv, 24, VE * 2.0, 0.02, dd)
	if sec == "v-tag" and bar == 0 and s == 4: hit("clap", dd, 0.06, 0.05)
	# --- how sections join: fills, pickups, arrivals, held chords, final ring-out ---
	var sc := of if hold else sec
	var fs: float = VFILL.get(sc, 0.0)
	var sx := s + 8 if hold else s
	var half := n >= 8 and bar == n / 2 - 1 and not hold
	if (hold or (is_end and not pre)) and fs > 0.0 and not last:
		if sx == 6 or sx == 8: play("tom", {"v": (0.07 + 0.02 * fs) * minf(1.0, fs + 0.3) / 0.14 * SMP_MUS, "rate": (130.0 - (sx - 6) * 10.0) / 110.0, "dl": dd})
		if sx == 10 and fs >= 0.8: play("tom", {"v": 0.08 * fs / 0.14 * SMP_MUS, "rate": 112.0 / 110.0, "dl": dd})
		if sx >= 12:
			hit("snare", dd, (0.03 + (sx - 12) * 0.014) * fs, 0.07)
			if fs >= 1.0 and sx % 2 == 1: play("tom", {"v": 0.07 * fs / 0.14 * SMP_MUS, "rate": (100.0 - (sx - 12) * 6.0) / 110.0, "dl": dd})
		if sx == 14 and fs >= 1.2: hit("snare", dd + VE * 0.5, 0.075, 0.07)
	elif half and s >= 14: hit("snare", dd, 0.03 + (s - 14) * 0.015, 0.07)
	if ((hold and s == 6) or (is_end and not pre and s == 14)) and not last and nxr != r: note("bass", nxr, VE * 1.6, 0.15, 0.17, dd)
	if first and s == 0 and sc != "v-intro" and not hold:
		var big := 0.3
		if sc == "v-B" or sc == "v-F": big = 1.0 if fin else 0.8
		elif sc == "v-C": big = 0.7
		elif sc == "v-A": big = 0.4
		if big >= 0.7:
			hit("cymbal", dd, 0.03 * big, 0.05); hit("clap", dd, 0.05 * big, 0.05); _vtrp(cv, 12, VE * 4.0, 0.03 * big, dd)
		if sc == "v-B" or sc == "v-F" or sc == "v-C" or sc == "v-tag": play("impact", {"v": (0.12 if fin else 0.09) / 0.1 * SMP_MUS, "dl": dd})
	if hy >= 1 and bar % 2 == 1 and s == 10 and not is_end and not hold: hit("kick", dd, 0.1, 0.17)
	if hy >= 2 and bar % 4 == 3 and s == 6 and not is_end and not hold:
		hit("hat", dd, 0.05, 0.04); hit("hat", dd + VE * 0.5, 0.04, 0.04)
	if hold and s == 0 and not last:
		_vtrp(cv, 0, VE * 7.0, 0.028, dd); _vtrp(cv, 12, VE * 6.0, 0.018, dd)
		if sc != "v-tag": hit("cymbal", dd, 0.03, 0.05)
	if last:
		if s == 0:
			play("impact", {"v": 0.12 / 0.1 * SMP_MUS, "dl": dd}); hit("cymbal", dd, 0.07, 0.05); hit("clap", dd, 0.07, 0.05); hit("kick", dd, 0.18, 0.17)
			_strum(cv, dd, true, 0.1); _vtrp(cv, 12, VE * 38.0, 0.05, dd); _vtrp(cv, 0, VE * 34.0, 0.04, dd); note("bass", r, VE * 28.0, 0.2, 0.17, dd)
		if s == 4: _strum(cv, dd, false, 0.05)
	# --- the sung line (one clip per lyric line, starting on the line's first bar) ---
	if s == 0 and not hold and have_vox:
		var vk := _vox_key(sec, bar)
		if vk != "" and vox.has(vk):
			# one clip per line: each clip is pre-rendered as a small detuned ensemble (choir), so a separate
			# unison double is no longer played here (two takes at the same pitch comb-filtered into a metallic edge).
			play("vox/" + str(vox[vk][0]), {"v": VOX_GAIN, "dl": maxf(0.0, dd - float(vox[vk][1]) + 0.01)})
	# --- sparse vocal ad-libs: a deep grunt from the same singer, on the bar's chord root (r) ---
	if not hold and not last:
		for g in VGRUNT:
			if sec == g[0] and bar == g[1] and s == g[2]:
				play("grunt", {"midi": r, "dur": 0.34, "v": VGRUNT_V, "bus": "VoxGrunt", "dl": dd})
				break
	# --- the tune ---
	var m: int = int(mel[s])
	if m > 0:
		var holds := 0
		while s + 1 + holds < 16 and (int(mel[s + 1 + holds]) == -1 or (int(mel[s + 1 + holds]) == 0 and holds < 3)): holds += 1
		_lead(lead, m, (1 + holds) * VE * 0.9, dd, cv)
	# --- arrangement layer: pad + bell sparkle + bass approach ---
	var brk := sec.ends_with("intro")
	if s == 0 and not hold: for x in cv: note("pad", int(x), VE * 16, (0.009 + 0.004 * hy) * (1.6 if brk else 1.0), 0.009, dd, VE * 16 * 0.28)
	if hy >= 1 and s % 4 == 1 and not (m > 0) and not hold and randf() < 0.6:
		note("bell", int(cv[((s >> 1) + bar * 2) % cv.size()]) + (24 if hy >= 2 else 12), VE * 2.2, 0.02 * (0.85 + hy * 0.1), 0.02, dd)
	if s == 15 and not is_end and nxr != r: note("bass", nxr + (-1 if nxr > r else 1), VE * 0.9, 0.1 * hv, 0.17, dd)
