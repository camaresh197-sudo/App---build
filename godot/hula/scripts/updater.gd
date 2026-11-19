extends Node
# Self-updating pack loader (autoload "Updater"). This script is part of the app itself and is never replaced by an update.
#  - on start (before the game's own scripts load): mount every pack listed in user://packs/state.json
#  - in the background: fetch latest.json from the release page, download any new packs, verify their sha256, and apply them on the NEXT launch
#  - safety net: a new pack is marked "pending"; the game calls Updater.confirm_good() once it is running. If it never does (crash / black screen),
#    the next launch counts a failed start against that pack and drops the file after BAD_LIMIT of them, so one early close cannot write it off.
const MANIFEST_URL := "https://github.com/camaresh197-sudo/app---build/releases/download/godot-latest/latest.json"
const DIR := "user://packs"
const STATE := "user://packs/state.json"
const BAD_LIMIT := 2          # failed starts before a pack is written off for good

var build := 0                # the build number baked into this APK (res://build.txt)
var status := ""              # shown by the game as a small toast
var status_t := 0.0
var ready_to_apply := false   # packs are downloaded and waiting: the game closes itself when it is safe
# good/pending/trying map {name: sha}; bad maps {sha: failed starts}, so a pack can earn another chance and a wipe can clear it
var state := {"good": {}, "pending": {}, "trying": {}, "bad": {}, "build": 0, "engine": ""}
var _trying := {}
var _queue: Array = []
var _http: HTTPRequest
var _cur: Dictionary = {}
var _manifest: Dictionary = {}
var _test := false            # launched with "-- ..." (the shotter harness): leave the packs alone and run the code on disk

func _init() -> void:
	DirAccess.make_dir_recursive_absolute(DIR)
	_test = not OS.has_feature("mobile") and not OS.get_cmdline_user_args().is_empty()
	if _test: return                                     # a test run measures the code on disk: never mount, download or blacklist packs
	_read_build()
	_load_state()
	# a newer APK (or a newer engine) carries everything older packs had: forget them, or they would override the newer app's files
	if int(state.get("build", -1)) != build or str(state.get("engine", "")) != _engine():
		_wipe()
	# "trying" packs (mounted last launch, never confirmed) failed to start: count it and drop the file. BAD_LIMIT of these writes a pack off,
	# so a launch that ends early (closed at the title screen, or a test run) cannot kill a pack that is actually fine.
	var tr: Dictionary = state.get("trying", {})
	for n in tr:
		var sha: String = tr[n]
		(state.bad as Dictionary)[sha] = int((state.bad as Dictionary).get(sha, 0)) + 1
		DirAccess.remove_absolute("%s/%s" % [DIR, n])
	state["trying"] = {}
	var mounted := {}
	for n in state.good:
		var p := "%s/%s" % [DIR, n]
		if FileAccess.file_exists(p) and FileAccess.get_sha256(p) == state.good[n]:
			if ProjectSettings.load_resource_pack(p): mounted[n] = state.good[n]
	state.good = mounted
	# packs downloaded last session are tried now. They stay "pending" on disk until confirm_good() runs.
	_trying = {}
	for n in state.pending:
		var p2 := "%s/%s" % [DIR, n]
		if FileAccess.file_exists(p2) and FileAccess.get_sha256(p2) == state.pending[n] and ProjectSettings.load_resource_pack(p2): _trying[n] = state.pending[n]
	state["trying"] = _trying.duplicate()
	state.pending = {}
	state["build"] = build
	state["engine"] = _engine()
	_save_state()

func _ready() -> void:
	if _test: return
	_http = HTTPRequest.new(); add_child(_http)
	_http.use_threads = true
	_http.request_completed.connect(_on_done)
	await get_tree().create_timer(2.0).timeout   # let the game start first
	_fetch_manifest()

func confirm_good() -> void:
	if _test: return
	# the game is up and running: packs tried this launch are good. Drop older packs from the same slot (the part of the name before "-").
	for n in _trying:
		var slot: String = n.get_slice("-", 0)
		for old in state.good.keys():
			if old != n and old.get_slice("-", 0) == slot:
				state.good.erase(old); DirAccess.remove_absolute("%s/%s" % [DIR, old])
		state.good[n] = _trying[n]
	_trying = {}
	state["trying"] = {}
	_save_state()

func _read_build() -> void:
	var f := FileAccess.open("res://build.txt", FileAccess.READ)
	if f: build = int(f.get_as_text().strip_edges())

# the engine a pack was built for. packs are compiled by one engine build and only mount in an APK built with that same one.
# comparing major.minor.patch means the APK's own hash does not count as a change.
func _engine() -> String:
	var v := Engine.get_version_info()
	return "%d.%d.%d" % [int(v.get("major", 0)), int(v.get("minor", 0)), int(v.get("patch", 0))]

# forget every pack on disk: a new APK, or an engine change, makes all of them stale (and clears the bad list with them)
func _wipe() -> void:
	for n in (state.good as Dictionary).keys() + (state.pending as Dictionary).keys() + (state.get("trying", {}) as Dictionary).keys():
		DirAccess.remove_absolute("%s/%s" % [DIR, n])
	state = {"good": {}, "pending": {}, "trying": {}, "bad": {}, "build": build, "engine": _engine()}
	_save_state()

func _load_state() -> void:
	var f := FileAccess.open(STATE, FileAccess.READ)
	if not f: return
	var j = JSON.parse_string(f.get_as_text())
	if not (j is Dictionary): return
	for k in ["good", "pending", "trying"]:
		if j.get(k) is Dictionary: state[k] = j[k]
	if j.get("bad") is Dictionary: state["bad"] = j["bad"]
	elif j.get("bad") is Array:
		for sha in j["bad"]: (state.bad as Dictionary)[str(sha)] = BAD_LIMIT   # older builds kept a plain list of written-off shas
	if j.has("build"): state["build"] = j["build"]
	if j.has("engine"): state["engine"] = j["engine"]

func _save_state() -> void:
	var f := FileAccess.open(STATE, FileAccess.WRITE)
	if f: f.store_string(JSON.stringify(state))

func _say(t: String, secs := 6.0) -> void:
	status = t; status_t = secs

func _process(dt: float) -> void:
	if status_t > 0.0:
		status_t -= dt
		if status_t <= 0.0: status = ""

func _fetch_manifest() -> void:
	_cur = {"kind": "manifest"}
	if _http.request(MANIFEST_URL) != OK: _cur = {}

func _on_done(result: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
	if _cur.get("kind", "") == "manifest":
		_cur = {}
		if result != HTTPRequest.RESULT_SUCCESS or code != 200: return   # offline: nothing to do
		var j = JSON.parse_string(body.get_string_from_utf8())
		if not (j is Dictionary): return
		_manifest = j
		_plan()
	elif _cur.get("kind", "") == "pack":
		var c := _cur; _cur = {}
		var tmp: String = c.path + ".part"
		if result == HTTPRequest.RESULT_SUCCESS and code == 200 and FileAccess.file_exists(tmp) and FileAccess.get_sha256(tmp) == c.sha:
			DirAccess.rename_absolute(tmp, c.path)
			state.pending[c.name] = c.sha
			_save_state()
		else:
			DirAccess.remove_absolute(tmp)
			_say("Update download failed")
		_next()

func _plan() -> void:
	if int(_manifest.get("build", 0)) < build and build > 0:
		return   # this APK is newer than the published packs
	# packs are compiled by a specific engine build and only load in an APK built with that same one.
	# an older APK must ignore them and keep playing instead of downloading something it cannot mount.
	var want: String = str(_manifest.get("engine", ""))
	if want != "" and not _engine().begins_with(want):
		return
	_queue.clear()
	for p in _manifest.get("packs", []):
		var n: String = p.name; var sha: String = p.sha
		if state.good.get(n, "") == sha or state.pending.get(n, "") == sha or _trying.get(n, "") == sha: continue
		if int((state.bad as Dictionary).get(sha, 0)) >= BAD_LIMIT: continue   # this exact pack failed to start BAD_LIMIT times
		# an older version of the same pack slot is replaced when the new one becomes good
		_queue.append(p)
	if _queue.is_empty(): return
	_say("Downloading update...", 60.0)
	_next()

func _next() -> void:
	if _queue.is_empty():
		if not (state.pending as Dictionary).is_empty():
			ready_to_apply = true
			_say("Update ready — closing to apply", 600.0)
		return
	var p: Dictionary = _queue.pop_front()
	_cur = {"kind": "pack", "name": p.name, "sha": p.sha, "path": "%s/%s" % [DIR, p.name]}
	_http.download_file = _cur.path + ".part"
	if _http.request(p.url) != OK:
		_cur = {}; _next()

