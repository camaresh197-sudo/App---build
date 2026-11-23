# Embedded Piper (offline, exact)

The TIMING editor's exact preview: a Piper VITS model runs **inside the APK**, so an edited
word's IPA is heard in the real singer's voice with no PC. Unchanged words play the shipped
clip, so a line keeps its original voice except where edited.

## What it is

- `android/piper/src/main/java/com/camaresh/piper/PiperPlugin.kt` — Godot plugin v2 init
  class. Reads the model from the app's `assets/piper/`, maps IPA to phoneme ids from the
  model's own `.onnx.json`, runs ONNX Runtime, returns 16-bit WAV bytes.
- `godot/hula/scripts/piper.gd` (`PiperVoice`) — GDScript wrapper.
- `menu.gd` (`_timing_play_piper`) — edited words via the plugin, the rest from the clip.
- `sound.gd` `play_stream` — plays a caller-supplied stream on the Vox bus.
- `export_presets.cfg` preset **AndroidPiper** — the only preset with Gradle build on.

## How it is built

`.github/workflows/piper-apk.yml` (runs on `android/**`, the preset, `piper.gd` or itself):

1. `--install-android-build-template` (creates `android/build/`).
2. Downloads `en_US-bryce-medium.onnx` (+ `.onnx.json`) into `android/build/src/main/assets/piper/`.
3. Copies the Kotlin sources into `android/build/src/main/java/com/camaresh/`.
4. Injects the plugin meta-data into the manifest and the ONNX Runtime maven dependency
   into `build.gradle`.
5. Exports `AndroidPiper` and uploads the APK as an artifact.

The model and `android/build/` are never committed. Install the artifact APK on the phone
once; after that, pack updates keep working as before.

## Rules

- The main `godot-apk` build ignores `android/**` and `godot/hula/addons/**`, so plugin-only
  pushes do not rebuild the packs, and a broken plugin cannot block game updates.
- On every other run `PiperVoice.available()` is false; the chain is
  Piper → diphone bank → real-clip word slices.
- Per-phone lengths are not yet fed to the plugin (IPA only); the renderer's
  `render_phones` still owns lengths on re-sing.
- Voice licence: confirm `bryce`'s terms before shipping outside this project.
