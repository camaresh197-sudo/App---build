extends Node2D
# Cutscene scene: background, lighting, particles, audio for one cutscene
class_name CutsceneScene

@export var cutscene_id: String = "c_fiesta"
@export var scene_name: String = "THE FIESTA NEVER ENDS"

var audio_player: AudioStreamPlayer
var particles: GPUParticles2D
var background: ColorRect
var lighting: CanvasModulate

func _ready() -> void:
	_setup_background()
	_setup_lighting()
	_setup_particles()
	_setup_audio()

func _setup_background() -> void:
	background = ColorRect.new()
	background.color = Color(0.1, 0.05, 0.15)  # Dark purple
	background.anchor_left = 0
	background.anchor_top = 0
	background.anchor_right = 1
	background.anchor_bottom = 1
	add_child(background)
	move_child(background, 0)

func _setup_lighting() -> void:
	lighting = CanvasModulate.new()
	lighting.color = Color(1, 1, 1, 1)
	add_child(lighting)

func _setup_particles() -> void:
	particles = GPUParticles2D.new()
	particles.position = Vector2(400, 180)
	particles.amount = 50
	particles.lifetime = 3.0
	particles.emitting = true

	var process_mat = ParticleProcessMaterial.new()
	process_mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_CIRCLE
	process_mat.emission_radius = 100
	process_mat.initial_velocity_min = 50
	process_mat.initial_velocity_max = 150
	process_mat.gravity = Vector3(0, 0, 0)

	particles.process_material = process_mat
	add_child(particles)

func _setup_audio() -> void:
	audio_player = AudioStreamPlayer.new()
	audio_player.bus = "Music"
	add_child(audio_player)

func load_cutscene_audio(audio_path: String) -> void:
	var stream = load(audio_path)
	if stream:
		audio_player.stream = stream
		audio_player.play()
	else:
		push_error("Could not load audio: " + audio_path)

func set_scene_theme(bg_color: Color, light_color: Color) -> void:
	background.color = bg_color
	lighting.color = light_color

func set_particle_effect(emission_shape: int, emission_range: float, velocity_min: float, velocity_max: float, gravity: Vector3) -> void:
	var mat = particles.process_material as ParticleProcessMaterial
	if mat:
		mat.emission_shape = emission_shape
		mat.emission_radius = emission_range
		mat.initial_velocity_min = velocity_min
		mat.initial_velocity_max = velocity_max
		mat.gravity = gravity

func stop() -> void:
	audio_player.stop()
	particles.emitting = false
