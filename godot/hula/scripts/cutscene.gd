extends Node
# Cutscene player: displays dialogue synced to music
class_name CutscenePlayer

var snd: Node
var hero3d: Node
var main: Node2D

var active := false
var cur_cutscene := ""      # e.g. "c_fiesta"
var cur_scene := ""         # e.g. "THE LAST POP"
var cur_event_idx := 0
var events: Array = []
var current_event: Dictionary = {}
var event_time := 0.0       # time within current event
var display_text := ""
var display_speaker := ""
var display_expr := ""

func _ready() -> void:
	pass

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

	# Load events for this scene
	if snd and snd.cutscenes.has(cutscene_id):
		if snd.cutscenes[cutscene_id] is Dictionary and snd.cutscenes[cutscene_id].has(scene_name):
			events = snd.cutscenes[cutscene_id][scene_name]
			if events is Array and events.size() > 0:
				active = true
				_advance_event()
			else:
				events = []
		else:
			events = []
	else:
		events = []

func _advance_event() -> void:
	if not events or events.is_empty() or cur_event_idx >= events.size():
		active = false
		display_text = ""
		display_speaker = ""
		current_event = {}
		return

	current_event = events[cur_event_idx]
	if not current_event or current_event.is_empty():
		active = false
		return

	event_time = 0.0
	cur_event_idx += 1

	# Extract dialogue info
	display_speaker = current_event.get("who", "")
	display_text = current_event.get("say", "")
	display_expr = current_event.get("ex", current_event.get("hx", ""))

	# Apply expression to hero if it's a hero line
	if display_speaker == "hero" and display_expr != "" and hero3d:
		hero3d.expr(display_expr)

func update(dt: float) -> void:
	if not active or not snd:
		return

	event_time += dt

	var beat_sec = snd.beat_secs()
	if beat_sec <= 0:
		return  # Music not ready, skip timing

	# Check if it's time to advance (gap or duration-based)
	var should_advance := false

	# If there's a gap, use it as the event duration
	if current_event.has("gap"):
		var gap_beats = float(current_event.get("gap", 0))
		var gap_secs = maxf(0.1, gap_beats * beat_sec)
		if event_time >= gap_secs:
			should_advance = true
	else:
		# Default: show for 2 beats (min 0.5s)
		var default_secs = maxf(0.5, 2.0 * beat_sec)
		if event_time >= default_secs:
			should_advance = true

	if should_advance:
		_advance_event()

func draw(canvas: CanvasItem) -> void:
	if not active or display_text == "":
		return

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

	# Draw speaker character bubble
	_draw_speaker(canvas, font, speaker_color)

	# Draw dialogue box at bottom
	var box_height := 80.0
	var box_y := 360.0 - box_height
	var box_rect := Rect2(10, box_y, 752, box_height)

	# Background
	var bg = StyleBoxFlat.new()
	bg.bg_color = Color(0, 0, 0, 0.8)
	bg.set_corner_radius_all(8)
	canvas.draw_style_box(bg, box_rect)

	# Speaker name (left)
	canvas.draw_string(font, Vector2(20, box_y + 25), display_speaker.to_upper(), -1, -1, 14, speaker_color)

	# Dialogue text (wrapped)
	canvas.draw_string(font, Vector2(20, box_y + 50), display_text, -1, 720, 16, Color.WHITE)

func _draw_speaker(canvas: CanvasItem, font: Font, col: Color) -> void:
	var x = current_event.get("x", 180)
	var y = current_event.get("y", 150)
	var scale_x = 772.0 / 320.0
	x = int(x * scale_x)
	var radius := 20.0
	canvas.draw_circle(Vector2(x, y), radius, col)
	canvas.draw_circle(Vector2(x, y), radius - 2, Color(0, 0, 0, 0.5))
	var label = display_speaker.substr(0, 3).to_upper()
	var text_size = font.get_string_size(label, -1, -1, 10)
	canvas.draw_string(font, Vector2(x - text_size.x / 2, y + radius + 10), label, -1, -1, 10, col)

func is_active() -> bool:
	return active
