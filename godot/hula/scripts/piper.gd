class_name PiperVoice
extends Object
# Wrapper for the embedded Piper Android plugin (android/piper/.../PiperPlugin.kt).
# Present only in a Piper build (Android + Gradle + the model in assets); on every other
# run `available()` is false and the TIMING tab falls back to the diphone preview.

static func available() -> bool:
	return OS.get_name() == "Android" and Engine.has_singleton("Piper")

# Why the exact preview is or is not running, in words the TIMING tab can show. Cached: the model
# load is expensive, so the plugin is asked once per launch.
static var _status := ""
static func status() -> String:
	if _status != "":
		return _status
	if OS.get_name() != "Android":
		_status = "Piper: not Android, no plugin"
	elif not Engine.has_singleton("Piper"):
		_status = "Piper: plugin missing from this APK (install HulaVaqueroPiper)"
	elif Engine.get_singleton("Piper").ready():
		_status = "Piper: plugin + model ready"
	else:
		var err := String(Engine.get_singleton("Piper").lastError())
		_status = "Piper: model failed: " + (err if err != "" else "unknown (no error recorded)")
	return _status

# One word: IPA in, an AudioStreamWAV out. null when the plugin or the model is missing.
static func sing_stream(ipa: String) -> AudioStreamWAV:
	if not available():
		return null
	var p = Engine.get_singleton("Piper")
	var raw: PackedByteArray = p.singIpa(ipa, 0.667, 1.0, 0.8)
	if raw.size() <= 44:
		return null
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = int(p.sampleRateHz())
	wav.stereo = false
	wav.data = raw.slice(44)
	return wav
