extends Node
# Voice audio playback for cutscenes
# Can use TTS or pre-recorded voice lines
class_name VoiceManager

var voices: Dictionary = {}  # speaker -> audio player
var tts_enabled := false
var voice_cache: Dictionary = {}  # cached audio files

func _ready() -> void:
	_setup_voice_players()

func _setup_voice_players() -> void:
	var speakers = ["hero", "baron", "abuela", "kid", "guitar", "chorus"]
	for speaker in speakers:
		var player = AudioStreamPlayer.new()
		player.bus = "Vox"
		add_child(player)
		voices[speaker] = player

func play_dialogue(speaker: String, text: String) -> void:
	if not voices.has(speaker):
		return

	var player: AudioStreamPlayer = voices[speaker]

	# Try to load pre-recorded line
	var cache_key = "%s_%s" % [speaker, text.hash()]
	if voice_cache.has(cache_key):
		player.stream = voice_cache[cache_key]
		player.play()
		return

	# Try pre-recorded file (name rule must mirror tools/piper_batch.py)
	var audio_path = "res://audio/voice/%s/%s.ogg" % [speaker, _safe_name(text)]
	if ResourceLoader.exists(audio_path):
		var audio = load(audio_path)
		if audio:
			voice_cache[cache_key] = audio
			player.stream = audio
			player.play()
		return

	# If TTS enabled, generate speech
	if tts_enabled:
		_tts_speak(speaker, text, player)

## Filename-safe version of a dialogue line: lowercase, spaces -> '_',
## minus characters Windows filenames cannot contain. Mirrors piper_batch.py.
func _safe_name(text: String) -> String:
	var n := text.to_lower().replace(" ", "_")
	for c in ["?", "*", ":", "\"", "<", ">", "|", "/", "\\"]:
		n = n.replace(c, "")
	return n.lstrip(".")   # a leading dot makes a hidden file Godot never imports ("...sorry" lines)

func _tts_speak(speaker: String, text: String, player: AudioStreamPlayer) -> void:	# Placeholder for TTS implementation
	# Could use Google Cloud TTS API, local espeak, or similar
	push_warning("TTS not implemented: %s says '%s'" % [speaker, text])

func stop_all_voices() -> void:
	for player in voices.values():
		player.stop()

func get_voice_duration(speaker: String, text: String) -> float:
	var cache_key = "%s_%s" % [speaker, text.hash()]
	if voice_cache.has(cache_key):
		var audio = voice_cache[cache_key]
		if audio and audio is AudioStream:
			return audio.get_length()

	# Estimate: ~150 words per minute = 2.5 chars per second
	return float(text.length()) / 2.5
