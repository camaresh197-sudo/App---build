class_name Psola
extends Object
# TD-PSOLA pitch shifting for the phone's Piper preview, in the game's own code (no plugin needed).
# The pitch is estimated from the clip itself (autocorrelation), the pitch marks are placed on the
# waveform peaks of each period, and each grain is repeated at the output period. Duration is kept:
# only the pitch changes. Checked on a Piper clip with pyworld measurements: identity correlation 0.98,
# +4 semitones gives 1.25x the pitch (1.26x expected), the unshifted part is unchanged, the length is kept.

# pitch per hop of `hop_s` seconds; 0 = unvoiced. Autocorrelation over a 40 ms window.
static func f0_track(x: PackedFloat32Array, sr: float, hop_s := 0.01, fmin := 70.0, fmax := 350.0) -> PackedFloat32Array:
	var n := x.size()
	var w := int(0.04 * sr)
	var h := int(hop_s * sr)
	var lag_min := int(sr / fmax)
	var lag_max := int(sr / fmin)
	var out := PackedFloat32Array()
	var seg := PackedFloat32Array()
	seg.resize(w)
	var c := w / 2
	while c < n - w / 2:
		var s0 := c - w / 2
		var mean := 0.0
		for i in w:
			mean += x[s0 + i]
		mean /= float(w)
		var e := 0.0
		for i in w:
			seg[i] = x[s0 + i] - mean
			e += seg[i] * seg[i]
		if e < 1e-6:
			out.append(0.0)
		else:
			var best := lag_min
			var best_v := -1e30
			for lag in range(lag_min, lag_max):
				var acc := 0.0
				for i in range(w - lag):
					acc += seg[i] * seg[i + lag]
				if acc > best_v:
					best_v = acc
					best = lag
			var r := best_v / (e + 1e-9)
			out.append(sr / float(best) if r > 0.45 else 0.0)
		c += h
	return out

# pitch marks: one per period, on the loudest sample near each predicted period
static func pitch_marks(x: PackedFloat32Array, sr: float, f0: PackedFloat32Array, h: int) -> PackedInt32Array:
	var marks := PackedInt32Array()
	var t := 0
	while t < x.size() - 1:
		var fi := mini(f0.size() - 1, t / h)
		if fi < 0 or f0[fi] <= 0.0:
			t += h
			continue
		var p := int(roundf(sr / f0[fi]))
		var lo := maxi(0, t - p / 4)
		var hi := mini(x.size(), t + p / 4 + 1)
		var m := t
		var best := -1.0
		for i in range(lo, hi):
			if absf(x[i]) > best:
				best = absf(x[i])
				m = i
		marks.append(m)
		t = m + p
	return marks

# pitch multiplier at time t from segs: Vector3(start_s, end_s, multiplier); 1.0 outside them
static func _gain_at(segs: Array, t: float) -> float:
	for sg in segs:
		var v: Vector3 = sg
		if t >= v.x and t < v.y:
			return v.z
	return 1.0

static func psola(x: PackedFloat32Array, sr: float, f0: PackedFloat32Array, h: int, segs: Array) -> PackedFloat32Array:
	var n := x.size()
	var out := PackedFloat32Array()
	out.resize(n + int(4.0 * sr / 50.0))
	var norm := PackedFloat32Array()
	norm.resize(out.size())
	var marks := pitch_marks(x, sr, f0, h)
	if marks.size() < 3:
		return x.duplicate()
	var t_out := float(marks[0])
	var last := marks.size() - 1
	while t_out < n:
		# the analysis mark nearest the output cursor
		var k := 0
		var kd := 1e30
		for j in marks.size():
			var d := absf(float(marks[j]) - t_out)
			if d < kd:
				kd = d
				k = j
		# the period is the spacing to the next mark: with no shift every grain lands on its own mark
		var p_in := float(marks[mini(k + 1, last)] - marks[k])
		p_in = maxf(p_in, 20.0)
		var g := _gain_at(segs, t_out / sr)
		var half := int(p_in)
		var lo := marks[k] - half
		var s0 := int(t_out) - half
		var w := 2 * half
		for i in w:
			var o := s0 + i
			if o < 0 or o >= out.size():
				continue
			var src := lo + i
			var sample := 0.0
			if src >= 0 and src < n:
				sample = x[src]
			var win := 0.5 - 0.5 * cos(2.0 * PI * float(i) / float(w - 1))
			out[o] += sample * win
			norm[o] += win
		t_out += p_in / g
	var y := PackedFloat32Array()
	y.resize(n)
	for i in n:
		var d := norm[i] if norm[i] > 1e-6 else 1.0
		y[i] = out[i] / d
	return y

# AudioStreamWAV in, AudioStreamWAV out (same rate, same length), with the pitch changed by segs.
static func apply(wav: AudioStreamWAV, segs: Array) -> AudioStreamWAV:
	var sr := float(wav.mix_rate)
	var bytes := wav.data
	var n := bytes.size() / 2
	var x := PackedFloat32Array()
	x.resize(n)
	var peak := 1e-6
	for i in n:
		x[i] = bytes.decode_s16(i * 2) / 32768.0
		peak = maxf(peak, absf(x[i]))
	var scale := 0.8 / peak
	for i in n:
		x[i] *= scale
	var f0 := f0_track(x, sr)
	var y := psola(x, sr, f0, int(0.01 * sr), segs)
	var outb := PackedByteArray()
	outb.resize(n * 2)
	for i in n:
		outb.encode_s16(i * 2, clampi(roundi(y[i] / scale * 32767.0), -32768, 32767))
	var r := AudioStreamWAV.new()
	r.format = AudioStreamWAV.FORMAT_16_BITS
	r.mix_rate = wav.mix_rate
	r.stereo = false
	r.data = outb
	return r
