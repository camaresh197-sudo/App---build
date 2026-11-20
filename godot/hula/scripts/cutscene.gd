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
	active = true

	# Load events for this scene
	if snd.cutscenes.has(cutscene_id) and snd.cutscenes[cutscene_id].has(scene_name):
		events = snd.cutscenes[cutscene_id][scene_name]
		_advance_event()
	else:
		active = false

func _advance_event() -> void:
	if cur_event_idx >= events.size():
		active = false
		display_text = ""
		display_speaker = ""
		return

	current_event = events[cur_event_idx]
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
	if not active:
		return

	event_time += dt

	# Check if it's time to advance (gap or duration-based)
	var should_advance := false

	# If there's a gap, use it as the event duration
	if current_event.has("gap"):
		var gap_beats = float(current_event.get("gap", 0))
		var gap_secs = gap_beats * snd.beat_secs()
		if event_time >= gap_secs:
			should_advance = true
	else:
		# Default: show for 2 beats
		var default_secs = 2.0 * snd.beat_secs()
		if event_time >= default_secs:
			should_advance = true

	if should_advance:
		_advance_event()

func draw(canvas: CanvasItem) -> void:
	if not active or display_text == "":
		return

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
	var font = ThemeDB.fallback_font
	var speaker_color = Color.WHITE
	if display_speaker == "baron":
		speaker_color = Color("#ff6a5a")
	elif display_speaker == "hero":
		speaker_color = Color("#ffd32a")
	elif display_speaker == "abuela":
		speaker_color = Color("#ff9ecb")

	canvas.draw_string(font, Vector2(20, box_y + 25), display_speaker.to_upper(), -1, -1, 14, speaker_color)

	# Dialogue text (wrapped)
	canvas.draw_string(font, Vector2(20, box_y + 50), display_text, -1, 720, 16, Color.WHITE)

func is_active() -> bool:
	return active
