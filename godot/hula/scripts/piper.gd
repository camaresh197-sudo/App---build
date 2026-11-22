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

# Seconds of audio in a plugin WAV (16-bit mono, 44-byte header).
static func _wav_len(raw: PackedByteArray, rate: float) -> float:
	return maxf(0.0, float(raw.size() - 44) / 2.0 / maxf(1.0, rate))

# One word: IPA in, an AudioStreamWAV out, fitted to `target` seconds when given. Piper's own
# length for a word is whatever it likes; the TIMING tab plays a word for its edited LEN, so a
# longer natural word lost its last phones (an edit there was never heard) and length edits did
# nothing. The word is rendered once to measure it, then again with length_scale = target / natural.
# null when the plugin or the model is missing. `info` gets the natural and final lengths.
static func sing_stream(ipa: String, target := 0.0, info := {}) -> AudioStreamWAV:
	if not available():
		return null
	var p = Engine.get_singleton("Piper")
	var rate: float = float(p.sampleRateHz())
	var raw: PackedByteArray = p.singIpa(ipa, 0.667, 1.0, 0.8)
	if raw.size() <= 44:
		return null
	var natural := _wav_len(raw, rate)
	info["natural"] = natural
	if target > 0.05 and natural > 0.05:
		var ls := clampf(target / natural, 0.4, 3.0)
		if absf(ls - 1.0) > 0.05:
			var fit: PackedByteArray = p.singIpa(ipa, 0.667, ls, 0.8)
			if fit.size() > 44:
				raw = fit
	info["final"] = _wav_len(raw, rate)
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = int(rate)
	wav.stereo = false
	wav.data = raw.slice(44)
	return wav
