extends Node2D
# Procedurally generate cutscene backgrounds
class_name SceneGenerator

var canvas: CanvasItem

func generate_background(scene_id: String) -> void:
	canvas = self

	match scene_id:
		"c_fiesta":
			_scene_fiesta()
		"c_theft":
			_scene_theft()
		"c_fall":
			_scene_fall()
		"c_hero":
			_scene_hero()
		"c_climb":
			_scene_climb()
		"c_mission":
			_scene_mission()
		"c_pursuit1":
			_scene_pursuit1()
		"c_pursuit2":
			_scene_pursuit2()
		"c_reckon":
			_scene_reckon()
		"c_armada":
			_scene_armada()
		"c_showdown":
			_scene_showdown()

func _scene_fiesta() -> void:
	# Vibrant plaza with buildings, lights, celebration
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.2, 0.1, 0.25))  # Night sky

	# Buildings silhouette
	canvas.draw_rect(Rect2(0, 240, 150, 120), Color(0.3, 0.1, 0.2))
	canvas.draw_rect(Rect2(622, 240, 150, 120), Color(0.3, 0.1, 0.2))

	# Lights
	for i in 10:
		var x = 50 + i * 70
		canvas.draw_circle(Vector2(x, 200), 8, Color(1, 0.8, 0.2, 0.6))

func _scene_theft() -> void:
	# Dark, shadowy town at night
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.05, 0.08, 0.15))

	# Roof silhouettes
	for i in 5:
		var points = PackedVector2Array([
			Vector2(i * 160, 240),
			Vector2(i * 160 + 80, 180),
			Vector2(i * 160 + 160, 240)
		])
		canvas.draw_colored_polygon(points, Color(0.1, 0.12, 0.2))

	# Moon
	canvas.draw_circle(Vector2(650, 80), 40, Color(0.95, 0.9, 0.8, 0.8))

func _scene_fall() -> void:
	# Dark, dramatic
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.1, 0.05, 0.1))

	# Large shadow shapes
	canvas.draw_rect(Rect2(0, 200, 772, 160), Color(0, 0, 0, 0.3))

func _scene_hero() -> void:
	# Golden, triumphant
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.3, 0.2, 0.1))

	# Golden glow
	canvas.draw_circle(Vector2(386, 180), 150, Color(1, 0.8, 0.2, 0.2))

func _scene_climb() -> void:
	# Mountain/cliff scene
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.2, 0.3, 0.4))

	# Mountain silhouette
	var mountain = PackedVector2Array([
		Vector2(0, 360),
		Vector2(200, 150),
		Vector2(400, 200),
		Vector2(600, 100),
		Vector2(772, 200),
		Vector2(772, 360)
	])
	canvas.draw_colored_polygon(mountain, Color(0.1, 0.2, 0.3))

func _scene_mission() -> void:
	# Interior/indoor setting
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.25, 0.2, 0.15))

	# Walls
	canvas.draw_rect(Rect2(0, 0, 772, 80), Color(0.3, 0.25, 0.2))
	canvas.draw_rect(Rect2(0, 280, 772, 80), Color(0.2, 0.15, 0.1))

func _scene_pursuit1() -> void:
	# Fast action - speed lines
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.15, 0.1, 0.2))

	for i in 15:
		canvas.draw_line(Vector2(0, i * 24), Vector2(772, i * 24), Color(1, 1, 1, 0.1), 2)

func _scene_pursuit2() -> void:
	# Continuation of pursuit
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.1, 0.15, 0.2))

	# Motion blur effect
	for i in 8:
		canvas.draw_rect(Rect2(0, 0, 772, 360), Color(1, 1, 1, 0.02 * (8 - i)))

func _scene_reckon() -> void:
	# Confrontation - stark
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.2, 0.15, 0.25))

	# Spotlight
	canvas.draw_circle(Vector2(386, 180), 200, Color(1, 0.9, 0.7, 0.15))

func _scene_armada() -> void:
	# Epic, grand
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.3, 0.25, 0.4))

	# Multiple suns/lights
	canvas.draw_circle(Vector2(200, 100), 30, Color(1, 0.5, 0.2, 0.4))
	canvas.draw_circle(Vector2(600, 100), 30, Color(1, 0.5, 0.2, 0.3))

func _scene_showdown() -> void:
	# Final confrontation - dramatic
	canvas.draw_rect(Rect2(0, 0, 772, 360), Color(0.1, 0.05, 0.15))

	# Dramatic lighting
	canvas.draw_circle(Vector2(386, 180), 250, Color(1, 0.3, 0.2, 0.2))
