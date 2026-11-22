package com.camaresh.piper

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.util.Log
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.nio.LongBuffer
import org.godotengine.godot.Godot
import org.godotengine.godot.plugin.GodotPlugin
import org.godotengine.godot.plugin.UsedByGodot
import org.json.JSONObject

/**
 * Embedded Piper (VITS) preview for the TIMING editor.
 *
 * The model ships in the APK's assets (android/build/src/main/assets/piper/, copied there
 * by CI). The editor passes one word's IPA; this class maps it to phoneme ids straight
 * from the model's own .onnx.json, runs ONNX Runtime, and returns 16-bit mono WAV bytes.
 */
class PiperPlugin(godot: Godot) : GodotPlugin(godot) {
    private val lock = Any()
    private var env: OrtEnvironment? = null
    private var session: OrtSession? = null
    private var idMap: Map<String, Long> = emptyMap()
    private var sampleRate = 22050

    override fun getPluginName(): String = "Piper"

    private fun loadModel(): Boolean = synchronized(lock) {
        if (session != null) return true
        try {
            // Godot 4.6 declares getActivity() nullable; a bare .assets access fails the Kotlin build.
            val activity = getActivity() ?: return false
            val assets = activity.assets
            val names = assets.list("piper") ?: return false
            val onnx = names.firstOrNull { it.endsWith(".onnx") } ?: return false
            val cfgName = names.firstOrNull { it.endsWith(".onnx.json") } ?: return false
            val model = assets.open("piper/$onnx").readBytes()
            val cfg = JSONObject(assets.open("piper/$cfgName").bufferedReader().use { it.readText() })
            sampleRate = cfg.optJSONObject("audio")?.optInt("sample_rate", 22050) ?: 22050
            val raw = cfg.getJSONObject("phoneme_id_map")
            val map = HashMap<String, Long>()
            val keys = raw.keys()
            while (keys.hasNext()) {
                val k = keys.next()
                val arr = raw.getJSONArray(k)
                if (arr.length() > 0) map[k] = arr.getLong(0)
            }
            idMap = map
            env = OrtEnvironment.getEnvironment()
            session = env!!.createSession(model)
            return true
        } catch (t: Throwable) {
            Log.e("PiperPlugin", "loadModel failed", t)
            return false
        }
    }

    /**
     * Piper's id layout is `^ _ p1 _ p2 _ ... pn _ $`: a pad after every phoneme, which is how the
     * voice was trained. Without the pads the model babbles at about half the length.
     * Stress (ˈ ˌ) and length (ː) marks are real ids and stay; symbols the voice does not know are
     * skipped, as Piper itself does; a space is the word-break token.
     */
    private fun idsFor(ipa: String): LongArray {
        val pad = idMap["_"] ?: 0L
        val ids = ArrayList<Long>(ipa.length * 2 + 4)
        idMap["^"]?.let { ids.add(it) }
        ids.add(pad)
        for (ch in ipa) {
            if (ch == '/' || ch == '.') continue
            val id = idMap[ch.toString()] ?: continue
            ids.add(id)
            ids.add(pad)
        }
        idMap["$"]?.let { ids.add(it) }
        return ids.toLongArray()
    }

    @UsedByGodot
    fun ready(): Boolean = loadModel()

    @UsedByGodot
    fun sampleRateHz(): Int { loadModel(); return sampleRate }

    /** One word: IPA in, 16-bit mono WAV bytes out. Empty on any failure. */
    @UsedByGodot
    fun singIpa(ipa: String, noiseScale: Float, lengthScale: Float, noiseW: Float): ByteArray {
        if (!loadModel()) return ByteArray(0)
        val ids = idsFor(ipa)
        if (ids.size < 5) return ByteArray(0)
        val e = env ?: return ByteArray(0)
        val s = session ?: return ByteArray(0)
        return try {
            OnnxTensor.createTensor(e, LongBuffer.wrap(ids), longArrayOf(1, ids.size.toLong())).use { input ->
                OnnxTensor.createTensor(e, LongBuffer.wrap(longArrayOf(ids.size.toLong())), longArrayOf(1)).use { lengths ->
                    OnnxTensor.createTensor(e, FloatBuffer.wrap(floatArrayOf(noiseScale, lengthScale, noiseW)), longArrayOf(3)).use { scales ->
                        s.run(mapOf("input" to input, "input_lengths" to lengths, "scales" to scales)).use { result ->
                            val list = ArrayList<Float>(4096)
                            collect(result.get(0).value, list)
                            val pcm = IntArray(list.size)
                            for (i in list.indices) {
                                val v = (list[i] * 0.89f).coerceIn(-1.0f, 1.0f)
                                pcm[i] = (v * 32767.0f).toInt()
                            }
                            return@use toWav(pcm)
                        }
                    }
                }
            }
        } catch (t: Throwable) {
            Log.e("PiperPlugin", "singIpa failed", t)
            ByteArray(0)
        }
    }

    private fun collect(v: Any?, list: ArrayList<Float>) {
        when (v) {
            is FloatArray -> for (f in v) list.add(f)
            is Array<*> -> for (x in v) collect(x, list)
            else -> {}
        }
    }

    private fun toWav(pcm: IntArray): ByteArray {
        val samples = ByteArray(pcm.size * 2)
        val b = ByteBuffer.wrap(samples).order(ByteOrder.LITTLE_ENDIAN)
        for (v in pcm) b.putShort(v.toShort())
        val header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN)
        header.put("RIFF".toByteArray())
        header.putInt(36 + samples.size)
        header.put("WAVE".toByteArray())
        header.put("fmt ".toByteArray())
        header.putInt(16)
        header.putShort(1)
        header.putShort(1)
        header.putInt(sampleRate)
        header.putInt(sampleRate * 2)
        header.putShort(2)
        header.putShort(16)
        header.put("data".toByteArray())
        header.putInt(samples.size)
        return header.array() + samples
    }
}
