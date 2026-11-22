class_name PiperVoice
extends Object
# Wrapper for the embedded Piper Android plugin (android/piper/.../PiperPlugin.kt).
# Present only in a Piper build (Android + Gradle + the model in assets); on every other
# run `available()` is false and the TIMING tab falls back to the diphone preview.

static func available() -> bool:
	return OS.get_name() == "Android" and Engine.has_singleton("Piper")

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
