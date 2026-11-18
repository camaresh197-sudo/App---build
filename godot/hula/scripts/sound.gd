extends Node
# Audio: sample bank (real instrument + drum samples rendered from a soundfont), SFX, and the game's mariachi song played by a step sequencer.
# Samples live in res://audio (assets pack). Everything is guarded, so the game still runs silent if the pack hasn't arrived yet.
const E := 0.13               # seconds per eighth-note slot (6 per bar, 6/8 feel)
const SMP_MUS := 0.25
const TRIM := {"guitar": 0.8, "bass": 1.39, "trumpet": 0.37, "violin": 0.23, "accordion": 0.27, "pad": 0.11, "choir": 0.47, "bell": 0.4, "kick": 1.5, "snare": 0.36, "hat": 0.07, "shaker": 0.26, "clap": 0.07, "cymbal": 0.14, "tom": 1.27, "sfx_coin": 0.13, "sfx_buy": 0.1, "sfx_power": 0.09, "sfx_level": 0.16, "sfx_trophy": 0.15, "sfx_trumpet": 0.05, "sfx_beat": 0.11, "sfx_boss": 0.22, "sfx_click": 0.21, "sfx_shield": 0.05, "impact": 1.43, "riser": 0.5, "crowd": 0.69}
const SFX_REL := {"shoot": 0.35, "hit": 0.4, "pop": 0.5, "coin": 0.5, "click": 0.4, "beat": 0.8}
# melodic instruments: [lowest root, highest root], roots every 2 semitones; each root has a second take "_2"
const RANGE := {"guitar": [40, 88], "bass": [28, 64], "trumpet": [52, 88], "violin": [55, 99], "accordion": [48, 84], "pad": [40, 80], "choir": [48, 84], "bell": [60, 100]}
const NVOICE := 40

var voices: Array = []        # AudioStreamPlayer pool
var vstop: Array = []         # per voice: time to release (0 = none)
var vbase: Array = []         # per voice: base volume db
var cache := {}
var later: Array = []         # [time, Callable]
var now := 0.0
var last := {}
var song: Array = []
var playing := false
var step := 0
var next_t := 0.0
var loop_from := 0
var vol_music := 0.8
var vol_sfx := 0.8
var have := false

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_buses()
	for i in NVOICE:
		var p := AudioStreamPlayer.new(); add_child(p); voices.append(p); vstop.append(0.0); vbase.append(0.0)
	var f := FileAccess.open("res://data_song.json", FileAccess.READ)
	if f: song = JSON.parse_string(f.get_as_text())
	for i in song.size():
		if song[i][7] == 0: loop_from = i; break
	have = ResourceLoader.exists("res://audio/kick.ogg")

func _buses() -> void:
	for nm in ["Music", "SFX"]:
		if AudioServer.get_bus_index(nm) < 0:
			AudioServer.add_bus(); var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, nm); AudioServer.set_bus_send(i, "Master")
	var mb := AudioServer.get_bus_index("Music")
	if AudioServer.get_bus_effect_count(mb) == 0:
		var rv := AudioEffectReverb.new(); rv.room_size = 0.55; rv.damping = 0.5; rv.wet = 0.16; rv.dry = 0.9; rv.hipass = 0.1
		AudioServer.add_bus_effect(mb, rv)
		var comp := AudioEffectCompressor.new(); comp.threshold = -14.0; comp.ratio = 3.0; comp.gain = 2.0
		AudioServer.add_bus_effect(mb, comp)
	if AudioServer.get_bus_effect_count(0) == 0 and ClassDB.class_exists("AudioEffectHardLimiter"):
		var lim = ClassDB.instantiate("AudioEffectHardLimiter"); lim.pre_gain_db = 0.0; lim.ceiling_db = -0.5
		AudioServer.add_bus_effect(0, lim)

func set_volumes(music10: int, sfx10: int) -> void:
	vol_music = music10 / 10.0; vol_sfx = sfx10 / 10.0
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Music"), linear_to_db(maxf(0.0001, vol_music * 0.7)))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("SFX"), linear_to_db(maxf(0.0001, vol_sfx)))
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Music"), music10 <= 0)
	AudioServer.set_bus_mute(AudioServer.get_bus_index("SFX"), sfx10 <= 0)

# ---------- sample bank ----------
func _stream(key: String) -> AudioStream:
	if cache.has(key): return cache[key]
	var path := "res://audio/%s.ogg" % key
	var s: AudioStream = load(path) if ResourceLoader.exists(path) else null
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
	var v: float = o.get("v", 1.0) * TRIM.get(name, 1.0)
	p.bus = o.get("bus", "Music")
	vbase[oi] = linear_to_db(maxf(0.0001, v)); p.volume_db = vbase[oi]
	var dur: float = o.get("dur", 0.0)
	vstop[oi] = (now + dur) if dur > 0.0 else 0.0
	p.play()

func note(name: String, midi: int, dur: float, v: float, ref: float, dl := 0.0) -> void:
	play(name, {"midi": midi, "dur": dur, "v": v / ref * SMP_MUS, "dl": dl})
func hit(name: String, dl: float, v: float, ref: float) -> void:
	play(name, {"v": v / ref * SMP_MUS, "dl": dl})

# ---------- sfx ----------
func sfx(n: String, vol := 1.0) -> void:
	if not have: return
	var gap: float = {"shoot": 0.09, "hit": 0.05, "pop": 0.04, "coin": 0.05}.get(n, 0.03)
	if last.has(n) and now - last[n] < gap: return
	last[n] = now
	var nm := "sfx_" + n
	if n == "shoot" or n == "hit" or n == "pop" or n == "hurt":   # these have no sample of their own: use the closest one-shots
		nm = {"shoot": "hat", "hit": "sfx_click", "pop": "sfx_coin", "hurt": "impact"}[n]
		var r := 0.94 + randf() * 0.12
		if n == "shoot": play("hat", {"v": 0.9, "rate": 0.9 * r, "bus": "SFX"})
		elif n == "hit": play("tom", {"v": 0.22, "rate": 1.6 * r, "bus": "SFX"})
		elif n == "pop": play("snare", {"v": 0.3, "rate": 1.25 * r, "bus": "SFX"}); play("sfx_coin", {"v": 0.35, "rate": 1.5 * r, "bus": "SFX", "dl": 0.03})
		else: play("impact", {"v": 0.5 * vol, "rate": 1.2, "bus": "SFX"})
		return
	play(nm, {"v": SFX_REL.get(n, 0.7) * vol, "rate": 0.94 + randf() * 0.12, "bus": "SFX"})

# ---------- music ----------
func start_music() -> void:
	if song.is_empty() or not have: return
	if playing: return
	playing = true; step = 0; next_t = now + 0.05

func stop_music() -> void:
	playing = false
	for i in voices.size():
		if voices[i].bus == "Music": vstop[i] = now + 0.01

func _process(dt: float) -> void:
	now += dt
	var i := 0
	while i < later.size():
		if later[i][0] <= now: later[i][1].call(); later.remove_at(i)
		else: i += 1
	for k in voices.size():   # short release so held notes end without a click
		var p: AudioStreamPlayer = voices[k]
		if not p.playing or vstop[k] <= 0.0: continue
		var left: float = vstop[k] - now
		if left <= 0.0: p.stop(); vstop[k] = 0.0
		elif left < 0.08: p.volume_db = vbase[k] + linear_to_db(maxf(0.01, left / 0.08))
	if playing:
		var guard := 0
		while now >= next_t and guard < 4:
			_step(step, next_t - now); step += 1; next_t += E; guard += 1
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
	var nb := song.size()
	var bi := st / 6
	if bi >= nb: bi = loop_from + (bi - nb) % (nb - loop_from)
	var slot := st % 6
	var B: Array = song[bi]
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
			var nx: int = int(mel[idx]) if idx < 6 else (int(song[(bi + 1) % nb][3][idx - 6]) if (bi + 1) < nb else 0)
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
