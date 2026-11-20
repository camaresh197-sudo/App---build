extends Node
# Cutscene player: displays dialogue synced to music + background
class_name CutscenePlayer

var snd: Node
var hero3d: Node
var main: Node2D

var active := false
var cur_cutscene := ""
var cur_scene := ""
var cur_event_idx := 0
var events: Array = []
var current_event: Dictionary = {}
var event_time := 0.0
var display_text := ""
var display_speaker := ""
var display_expr := ""
var current_audio_length := 0.0  # Duration of current audio line in seconds

var cutscene_data: Dictionary = {}
var config_data: Dictionary = {}
var audio_durations: Dictionary = {}  # Cache of audio file durations

# Playlist: scenes play back to back. Each item is {title, text, cs?}. text is the narration caption; cs picks the
# music + dialogue set (looked up by title in the dialogue data when omitted).
const EXIT_RECT := Rect2(772.0 - 86.0, 8.0, 78.0, 26.0)
var playlist: Array = []
var playlist_idx := 0
var caption_title := ""
var caption_text := ""
var caption_left := 0.0
var title_cs: Dictionary = {}   # scene title -> cutscene id
var act_intros: Array = []      # data_theater.json "acts": 4 lists of {title, text, cs?}

func _ready() -> void:
	_load_data()

func _load_data() -> void:
	# Load cutscene dialogue data
	var f = FileAccess.open("res://data/data_cutscenes.json", FileAccess.READ)
	if f:
		var data = JSON.parse_string(f.get_as_text())
		if data and data.has("data"):
			cutscene_data = data["data"]
			for cs_id in cutscene_data:
				for scene_title in cutscene_data[cs_id]:
					title_cs[scene_title] = cs_id

	f = FileAccess.open("res://data/data_theater.json", FileAccess.READ)
	if f:
		var th = JSON.parse_string(f.get_as_text())
		if th is Dictionary and th.has("acts"):
			act_intros = th["acts"]

	# Load cutscene config
	f = FileAccess.open("res://data/cutscene_config.json", FileAccess.READ)
	if f:
		var data = JSON.parse_string(f.get_as_text())
		if data and data.has("cutscenes"):
			config_data = data["cutscenes"]

func start(snd_node: Node, hero3d_node: Node, main_node: Node2D, cutscene_id: String, scene_name: String) -> void:
	snd = snd_node
	hero3d = hero3d_node
	main = main_node

	cur_cutscene = cutscene_id
	cur_scene = scene_name
	cur_event_idx = 0
	event_time = 0.0
	active = false
	events = []
	current_event = {}
	display_text = ""
	display_speaker = ""

	# Try to start cutscene audio if file exists
	if snd and config_data.has(cutscene_id):
		var cs_config = config_data[cutscene_id]
		for scene_cfg in cs_config.get("scenes", []):
			if scene_cfg.has("id") and scene_cfg["id"] == scene_name:
				if scene_cfg.has("audio_file"):
					var audio_path = scene_cfg["audio_file"]
					if ResourceLoader.exists(audio_path):
						snd.play_cutscene_audio(audio_path)
					else:
						print("Cutscene audio not found: ", audio_path)
				break

	# Load events for this scene
	if cutscene_data.has(cutscene_id):
		var cutscene = cutscene_data[cutscene_id]
		if cutscene.has(scene_name) and cutscene[scene_name] is Array:
			events = cutscene[scene_name]
			if events.size() > 0:
				active = true
				_advance_event()

func _advance_event() -> void:
	if not events or events.is_empty() or cur_event_idx >= events.size():
		active = false
		display_text = ""
		display_speaker = ""
		current_event = {}
		if snd:
			snd.stop_cutscene_audio()
		return

	current_event = events[cur_event_idx]
	if not current_event or current_event.is_empty():
		active = false
		return

	event_time = 0.0
	cur_event_idx += 1

	display_speaker = current_event.get("who", "")
	display_text = current_event.get("say", "")
	display_expr = current_event.get("ex", current_event.get("hx", ""))

	# Calculate audio duration for this dialogue line
	# Use gap if specified (in beats), otherwise estimate from text length
	if current_event.has("gap"):
		var beat_sec = snd.beat_secs() if snd else 0.3
		current_audio_length = float(current_event.get("gap", 0)) * beat_sec
	else:
		# Estimate: ~12 characters per second for speech
		var text_len = display_text.length()
		current_audio_length = maxf(1.0, text_len / 12.0)

	# Apply expression to hero
	if display_speaker == "hero" and display_expr != "" and hero3d:
		hero3d.set_expr(display_expr)

func update(dt: float) -> void:
	if caption_left > 0.0:
		caption_left -= dt
	if active and snd:
		event_time += dt
		# Wait for the current line to finish; the estimated length plus a 300ms buffer keeps the pacing even.
		if event_time >= current_audio_length + 0.3:
			_advance_event()
	if not active and caption_left <= 0.0 and not playlist.is_empty():
		playlist_idx += 1
		_play_item()

func play_list(snd_node: Node, hero3d_node: Node, main_node: Node2D, items: Array, from := 0) -> void:
	snd = snd_node
	hero3d = hero3d_node
	main = main_node
	playlist = items
	playlist_idx = from
	_play_item()

# Play the intro scenes for act 0-3 (skippable: tap = next scene, EXIT = stop). No-op for an unknown act.
func play_act(snd_node: Node, hero3d_node: Node, main_node: Node2D, act: int) -> void:
	if act < 0 or act >= act_intros.size():
		return
	play_list(snd_node, hero3d_node, main_node, act_intros[act], 0)

func _play_item() -> void:
	if playlist_idx >= playlist.size():
		stop_all()
		return
	var item: Dictionary = playlist[playlist_idx]
	var title: String = item.get("title", "")
	var cs: String = item.get("cs", title_cs.get(title, ""))
	if snd:
		snd.stop_music()
		if cs != "":
			snd.start_music(cs)
	start(snd, hero3d, main, cs, title)
	caption_title = title
	caption_text = item.get("text", "")
	caption_left = maxf(3.5, caption_text.length() / 14.0)

func stop_all() -> void:
	playlist = []
	playlist_idx = 0
	active = false
	caption_title = ""
	caption_text = ""
	caption_left = 0.0
	display_text = ""
	display_speaker = ""
	current_event = {}
	if snd:
		snd.stop_cutscene_audio()
		snd.stop_music()

func handle_tap(pos: Vector2) -> void:
	if not playlist.is_empty() and EXIT_RECT.has_point(pos):
		stop_all()
	else:
		skip()

func skip() -> void:
	active = false
	display_text = ""
	display_speaker = ""
	current_event = {}
	current_audio_length = 0.0
	caption_left = 0.0
	if snd:
		snd.stop_cutscene_audio()
	if not playlist.is_empty():
		playlist_idx += 1
		_play_item()

func draw(canvas: CanvasItem) -> void:
	var has_line := active and display_text != ""
	var has_caption := caption_left > 0.0 and caption_title != ""
	if not has_line and not has_caption:
		return

	# Background overlay with gradient
	# Top part darker, bottom part lighter so dialogue box stands out
	var top_color = Color(0.1, 0.05, 0.15, 0.8)
	var bot_color = Color(0.05, 0.03, 0.1, 0.9)
	canvas.draw_set_transform(Vector2.ZERO)
	canvas.draw_polygon(
		PackedVector2Array([Vector2(0, 0), Vector2(772, 0), Vector2(772, 360), Vector2(0, 360)]),
		PackedColorArray([top_color, top_color, bot_color, bot_color]))

	var speaker_colors = {
		"baron": Color("#ff6a5a"),
		"hero": Color("#ffd32a"),
		"abuela": Color("#ff9ecb"),
		"kid": Color("#7fe3ff"),
		"guitar": Color("#9be37a"),
		"chorus": Color("#e8d4b8")
	}

	var font = ThemeDB.fallback_font
	var speaker_color = speaker_colors.get(display_speaker, Color.WHITE)

	if has_line:
		_draw_speaker(canvas, font, speaker_color)

	if has_caption:
		canvas.draw_rect(Rect2(40, 44, 692, 112), Color(0, 0, 0, 0.55))
		canvas.draw_string(font, Vector2(40, 72), caption_title, HORIZONTAL_ALIGNMENT_CENTER, 692, 22, Color("ffd32a"))
		canvas.draw_multiline_string(font, Vector2(56, 98), caption_text, HORIZONTAL_ALIGNMENT_CENTER, 660, 15, 4, Color.WHITE)

	if has_line:
		var box_height := 80.0
		var box_y := 360.0 - box_height
		var box_rect := Rect2(10, box_y, 752, box_height)
		canvas.draw_rect(box_rect, Color(0, 0, 0, 0.9))
		canvas.draw_rect(box_rect, speaker_color, false, 2.0)
		canvas.draw_string(font, Vector2(20, box_y + 20), display_speaker.to_upper(), -1, -1, 14, speaker_color)
		canvas.draw_string(font, Vector2(20, box_y + 45), display_text, -1, 720, 16, Color.WHITE)

	var skip_text := "TAP: NEXT SCENE" if not playlist.is_empty() else "[TAP TO SKIP]"
	var skip_size := font.get_string_size(skip_text, HORIZONTAL_ALIGNMENT_RIGHT, -1, 11)
	canvas.draw_string(font, Vector2(752 - skip_size.x, 350), skip_text, -1, -1, 11, Color(1, 1, 1, 0.5))

	if not playlist.is_empty():
		canvas.draw_rect(EXIT_RECT, Color(0.75, 0.22, 0.17, 0.9))
		canvas.draw_rect(EXIT_RECT, Color(1, 1, 1, 0.5), false, 1.5)
		canvas.draw_string(font, EXIT_RECT.position + Vector2(0, 18), "EXIT", HORIZONTAL_ALIGNMENT_CENTER, EXIT_RECT.size.x, 13, Color.WHITE)
		canvas.draw_string(font, Vector2(16, 24), "SCENE %d / %d" % [playlist_idx + 1, playlist.size()], -1, -1, 12, Color(1, 1, 1, 0.7))

func _draw_speaker(canvas: CanvasItem, font: Font, col: Color) -> void:
	var x = current_event.get("x", 180)
	var y = current_event.get("y", 150)
	var scale_x = 772.0 / 320.0
	x = int(x * scale_x)

	var radius := 32.0
	# Outer glow
	canvas.draw_circle(Vector2(x, y), radius + 6, Color(col.r, col.g, col.b, 0.3))
	# Main circle
	canvas.draw_circle(Vector2(x, y), radius, col)
	# Inner dark circle
	canvas.draw_circle(Vector2(x, y), radius - 3, Color(0, 0, 0, 0.9))
	var label = display_speaker.substr(0, 3).to_upper()
	var text_size = font.get_string_size(label, -1, -1, 14)
	canvas.draw_string(font, Vector2(x - text_size.x / 2, y - 7), label, -1, -1, 14, col)

func is_active() -> bool:
	return active or caption_left > 0.0 or not playlist.is_empty()
