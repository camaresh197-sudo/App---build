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

var cutscene_data: Dictionary = {}
var config_data: Dictionary = {}

func _ready() -> void:
	_load_data()

func _load_data() -> void:
	# Load cutscene dialogue data
	var f = FileAccess.open("res://data/data_cutscenes.json", FileAccess.READ)
	if f:
		var data = JSON.parse_string(f.get_as_text())
		if data and data.has("data"):
			cutscene_data = data["data"]

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

	# Apply expression to hero
	if display_speaker == "hero" and display_expr != "" and hero3d:
		hero3d.set_expr(display_expr)

func update(dt: float) -> void:
	if not active or not snd:
		return

	event_time += dt

	var beat_sec = snd.beat_secs()
	if beat_sec <= 0:
		beat_sec = 0.3  # Fallback timing

	var should_advance := false

	# Use gap if specified, otherwise default duration
	if current_event.has("gap"):
		var gap_beats = float(current_event.get("gap", 0))
		var gap_secs = maxf(0.1, gap_beats * beat_sec)
		if event_time >= gap_secs:
			should_advance = true
	else:
		var default_secs = maxf(0.5, 2.0 * beat_sec)
		if event_time >= default_secs:
			should_advance = true

	if should_advance:
		_advance_event()

func skip() -> void:
	if active:
		active = false
		display_text = ""
		display_speaker = ""
		current_event = {}
		if snd:
			snd.stop_cutscene_audio()

func draw(canvas: CanvasItem) -> void:
	if not active or display_text == "":
		return

	# Background overlay - darker for visibility
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0, 0, 0, 0.65))

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

	# Draw speaker bubble
	_draw_speaker(canvas, font, speaker_color)

	# Draw dialogue box at bottom
	var box_height := 80.0
	var box_y := 360.0 - box_height
	var box_rect := Rect2(10, box_y, 752, box_height)

	# Draw box background
	canvas.draw_rect(box_rect, Color(0, 0, 0, 0.9))
	canvas.draw_rect(box_rect, speaker_color, false, 2.0)

	# Speaker name
	canvas.draw_string(font, Vector2(20, box_y + 20), display_speaker.to_upper(), -1, -1, 14, speaker_color)

	# Dialogue text
	canvas.draw_string(font, Vector2(20, box_y + 45), display_text, -1, 720, 16, Color.WHITE)

	# Skip hint
	var skip_text = "[TAP TO SKIP]"
	var skip_size = font.get_string_size(skip_text, HORIZONTAL_ALIGNMENT_RIGHT, -1, 11)
	canvas.draw_string(font, Vector2(752 - 20 - skip_size.x, box_y + 65), skip_text, -1, -1, 11, Color(1, 1, 1, 0.5))

func _draw_speaker(canvas: CanvasItem, font: Font, col: Color) -> void:
	var x = current_event.get("x", 180)
	var y = current_event.get("y", 150)
	var scale_x = 772.0 / 320.0
	x = int(x * scale_x)

	var radius := 32.0
	canvas.draw_circle(Vector2(x, y), radius, col)
	canvas.draw_circle(Vector2(x, y), radius - 3, Color(0, 0, 0, 0.8))
	var label = display_speaker.substr(0, 3).to_upper()
	var text_size = font.get_string_size(label, -1, -1, 14)
	canvas.draw_string(font, Vector2(x - text_size.x / 2, y - 7), label, -1, -1, 14, col)

func is_active() -> bool:
	return active
