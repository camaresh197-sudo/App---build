extends Node
# Real-time 3D vaquero, built from code (no imported model) and rendered into a transparent SubViewport that the 2D game draws as a sprite.
# Skeleton = a hierarchy of Node3D joints; the hula pose is procedural (pose()).
const VW := 280
const VH := 380
var vp: SubViewport
var cam: Camera3D
var root: Node3D
var j := {}          # joints by name
var mats := {}
var hoop_mat: StandardMaterial3D
var hoop_node: MeshInstance3D
var hat_mats: Array = []
var yaw := -0.18
var look := Vector2.ZERO

func _ready() -> void:
	vp = SubViewport.new()
	vp.size = Vector2i(VW, VH)
	vp.transparent_bg = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.world_3d = World3D.new()   # explicit, so the portrait camera can share it
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	_world(); _build(); _layer(j.hat, 2); _portrait(); _load_expr()

func tex() -> Texture2D: return vp.get_texture()

# ---------- world ----------
func _world() -> void:
	cam = Camera3D.new(); cam.fov = 26.0; vp.add_child(cam); cam.look_at_from_position(Vector3(0, 2.5, 5.6), Vector3(0, 0.82, 0))
	var sun := DirectionalLight3D.new(); sun.light_energy = 1.25; sun.rotation_degrees = Vector3(-38, 32, 0); sun.shadow_enabled = false; vp.add_child(sun)
	var fill := DirectionalLight3D.new(); fill.light_energy = 0.38; fill.light_color = Color("ffd7a8"); fill.rotation_degrees = Vector3(-10, -140, 0); vp.add_child(fill)
	var env := Environment.new(); env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color("9fb6e8"); env.ambient_light_energy = 0.55
	var we := WorldEnvironment.new(); we.environment = env; vp.add_child(we)

# ---------- materials / helpers ----------
func mat(col: Color, rough := 0.7, metal := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.albedo_color = col; m.roughness = rough; m.metallic = metal; return m

func put(parent: Node3D, mesh: Mesh, m: Material, pos := Vector3.ZERO, scl := Vector3.ONE, rot := Vector3.ZERO) -> MeshInstance3D:
	var n := MeshInstance3D.new(); n.mesh = mesh; n.material_override = m; n.position = pos; n.scale = scl; n.rotation = rot; parent.add_child(n); return n

func joint(name: String, parent: Node3D, pos: Vector3) -> Node3D:
	var n := Node3D.new(); n.name = name; n.position = pos; parent.add_child(n); j[name] = n; return n

func capsule(r: float, h: float) -> CapsuleMesh:
	var c := CapsuleMesh.new(); c.radius = r; c.height = h; c.radial_segments = 24; c.rings = 8; return c
func sphere(r: float, sx := 1.0, sy := 1.0, sz := 1.0) -> SphereMesh:
	var s := SphereMesh.new(); s.radius = r; s.height = r * 2.0; s.radial_segments = 28; s.rings = 14; return s

# surface of revolution from [radius, y] points
func lathe(prof: Array, seg := 40, smooth := true) -> ArrayMesh:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	if smooth: st.set_smooth_group(0)
	for i in prof.size() - 1:
		var a: Vector2 = prof[i]; var b: Vector2 = prof[i + 1]
		for k in seg:
			var t0 := TAU * k / seg; var t1 := TAU * (k + 1) / seg
			var p00 := Vector3(cos(t0) * a.x, a.y, sin(t0) * a.x); var p10 := Vector3(cos(t1) * a.x, a.y, sin(t1) * a.x)
			var p01 := Vector3(cos(t0) * b.x, b.y, sin(t0) * b.x); var p11 := Vector3(cos(t1) * b.x, b.y, sin(t1) * b.x)
			var u0 := float(k) / seg; var u1 := float(k + 1) / seg; var v0 := float(i) / (prof.size() - 1); var v1 := float(i + 1) / (prof.size() - 1)
			for tri in [[p00, p01, p11, Vector2(u0, v0), Vector2(u0, v1), Vector2(u1, v1)], [p00, p11, p10, Vector2(u0, v0), Vector2(u1, v1), Vector2(u1, v0)]]:
				for q in 3:
					st.set_uv(tri[3 + q]); st.add_vertex(tri[q])
	st.generate_normals()
	return st.commit()

func stripe_tex(c1: Color, c2: Color, n := 16) -> ImageTexture:
	var img := Image.create(128, 32, false, Image.FORMAT_RGBA8)
	for x in 128:
		var col := c1 if int(float(x) / 128.0 * n) % 2 == 0 else c2
		for y in 32: img.set_pixel(x, y, col)
	var t := ImageTexture.create_from_image(img); return t

# charro jacket cloth: red wool with gold vines
func jacket_tex() -> ImageTexture:
	var W := 256; var H := 256
	var img := Image.create(W, H, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new(); rng.seed = 7
	for y in H:
		for x in W:
			var n := 0.04 * sin(x * 1.7 + y * 0.9) * sin(y * 1.3 - x * 0.4)
			img.set_pixel(x, y, Color(0.62 + n, 0.07 + n * 0.3, 0.1 + n * 0.3))
	var gold := Color("e7b84a")
	for side in [0.2, 0.3, 0.7, 0.8]:
		for y in H:
			var cx := int((side + 0.04 * sin(y * 0.09)) * W)
			for dx in range(-2, 3): img.set_pixel(clampi(cx + dx, 0, W - 1), y, gold)
			if y % 20 == 0:
				for k in range(-7, 8):
					var lx := clampi(cx + k * (1 if side < 0.5 else -1) + 9, 0, W - 1)
					var ly := clampi(y - abs(k) / 2, 0, H - 1)
					img.set_pixel(lx, ly, gold)
	return ImageTexture.create_from_image(img)

# ---------- the model ----------
func _build() -> void:
	root = Node3D.new(); vp.add_child(root)
	var skin := mat(Color("a9714b"), 0.55)
	var cloth := mat(Color.WHITE, 0.85); cloth.albedo_texture = jacket_tex()
	var red := mat(Color("a3121c"), 0.85)
	var gold := mat(Color("e7b84a"), 0.35, 0.8)
	var silver := mat(Color("d8dde6"), 0.25, 0.9)
	var leather := mat(Color("8a5a2b"), 0.6)
	var boot := mat(Color("1b1412"), 0.35, 0.15)
	var black := mat(Color("120c09"), 0.5)
	var white := mat(Color("f4efe6"), 0.6)
	var felt := mat(Color("efe3c3"), 0.9)
	mats = {"felt": felt, "skin": skin}
	# pelvis & legs
	var pel := joint("pelvis", root, Vector3(0, 0.82, 0))
	put(pel, capsule(0.12, 0.34), red, Vector3(0, 0.02, 0), Vector3(1.25, 0.5, 0.9), Vector3(0, 0, PI / 2))
	for s in [-1, 1]:
		var side := "l" if s < 0 else "r"
		var hip := joint("hip_" + side, pel, Vector3(0.1 * s, -0.04, 0))
		put(hip, capsule(0.095, 0.4), red, Vector3(0, -0.17, 0))
		put(hip, sphere(0.097), red)
		var knee := joint("knee_" + side, hip, Vector3(0, -0.36, 0))
		put(knee, capsule(0.078, 0.38), red, Vector3(0, -0.16, 0))
		put(knee, sphere(0.08), red)
		var ank := joint("ankle_" + side, knee, Vector3(0, -0.34, 0))
		put(ank, capsule(0.075, 0.2), boot, Vector3(0, 0.03, 0))
		put(ank, capsule(0.065, 0.24), boot, Vector3(0, -0.05, 0.07), Vector3(1, 1, 1.2), Vector3(PI / 2, 0, 0))
		put(ank, sphere(0.04), gold, Vector3(0, -0.03, 0.17))
		# gold trouser stripe
		put(hip, BoxMesh.new(), gold, Vector3(0.093 * s, -0.2, 0), Vector3(0.008, 0.4, 0.02))
	# torso / jacket
	var spine := joint("spine", pel, Vector3(0, 0.07, 0))
	put(spine, capsule(0.18, 0.52), cloth, Vector3(0, 0.22, 0), Vector3(1.0, 1.0, 0.75))
	put(spine, capsule(0.2, 0.3), cloth, Vector3(0, 0.33, 0), Vector3(1.08, 0.8, 0.72))
	# collar & buttons
	put(spine, TorusMesh.new(), gold, Vector3(0, 0.5, 0), Vector3(0.1, 0.1, 0.1))
	for k in 4: put(spine, sphere(0.013), silver, Vector3(0, 0.4 - k * 0.07, 0.13))
	# belt + buckle
	var belt := put(spine, CylinderMesh.new(), leather, Vector3(0, 0.02, 0), Vector3(0.175, 0.045, 0.125))
	belt.mesh = (belt.mesh as CylinderMesh); (belt.mesh as CylinderMesh).radial_segments = 32
	put(spine, BoxMesh.new(), silver, Vector3(0, 0.02, 0.122), Vector3(0.07, 0.06, 0.02))
	put(spine, BoxMesh.new(), gold, Vector3(0, 0.02, 0.134), Vector3(0.04, 0.035, 0.012))
	# head
	var neck := joint("neck", spine, Vector3(0, 0.5, 0))
	put(neck, CylinderMesh.new(), skin, Vector3(0, 0.02, 0), Vector3(0.05, 0.07, 0.05))
	var head := joint("head", neck, Vector3(0, 0.15, 0)); head.scale = Vector3(1.22, 1.22, 1.22)
	put(head, sphere(0.105), skin, Vector3(0, 0.0, 0), Vector3(0.93, 1.1, 1.0))
	fr.jaw = put(head, sphere(0.06), skin, Vector3(0, -0.06, 0.02), Vector3(0.95, 0.75, 0.9))       # jaw
	_face(head, skin, white, black)
	put(head, sphere(0.02), skin, Vector3(-0.104, 0, 0.0), Vector3(0.5, 1.1, 0.8)); put(head, sphere(0.02), skin, Vector3(0.104, 0, 0.0), Vector3(0.5, 1.1, 0.8))
	# hair: long dark locks either side + back
	for s in [-1, 1]:
		put(head, capsule(0.04, 0.3), black, Vector3(0.1 * s, -0.1, -0.03), Vector3(0.9, 1, 0.9), Vector3(0, 0, 0.08 * s))
	put(head, sphere(0.108), black, Vector3(0, 0.02, -0.03), Vector3(0.95, 1.0, 0.95))
	# sombrero
	var hat := joint("hat", head, Vector3(0, 0.1, -0.01))
	var brim := lathe([Vector2(0.09, 0.0), Vector2(0.20, -0.005), Vector2(0.30, 0.0), Vector2(0.40, 0.03), Vector2(0.43, 0.065), Vector2(0.425, 0.07), Vector2(0.395, 0.04), Vector2(0.30, 0.012), Vector2(0.20, 0.005), Vector2(0.09, 0.012)])
	var crown := lathe([Vector2(0.1, 0.0), Vector2(0.098, 0.06), Vector2(0.088, 0.13), Vector2(0.074, 0.178), Vector2(0.05, 0.198), Vector2(0.0, 0.205)])
	var hm := mat(Color("efe3c3"), 0.9); hm.cull_mode = BaseMaterial3D.CULL_DISABLED
	var band := mat(Color("b3121f"), 0.6); band.cull_mode = BaseMaterial3D.CULL_DISABLED
	var hm2 := mat(Color("f3d27a"), 0.3, 0.6); hm2.cull_mode = BaseMaterial3D.CULL_DISABLED
	var b0 := put(hat, brim, hm, Vector3.ZERO, Vector3(0.98, 1.0, 0.98)); var c0 := put(hat, crown, hm)
	hat_mats = [hm, band, hm2]
	put(hat, lathe([Vector2(0.1, 0.012), Vector2(0.1005, 0.05), Vector2(0.1, 0.05)]), band, Vector3.ZERO, Vector3(1.02, 1, 1.02))
	put(hat, TorusMesh.new(), hm2, Vector3(0, 0.032, 0), Vector3(0.1, 0.1, 0.1)); (hat.get_child(hat.get_child_count() - 1).mesh as TorusMesh).inner_radius = 0.96; (hat.get_child(hat.get_child_count() - 1).mesh as TorusMesh).outer_radius = 1.0
	put(hat, TorusMesh.new(), hm2, Vector3(0, 0.0, 0), Vector3(0.43, 0.43, 0.43)).mesh = _thin_torus()
	# arms (raised, waving)
	for s in [-1, 1]:
		var side := "l" if s < 0 else "r"
		var sh := joint("shoulder_" + side, spine, Vector3(0.22 * s, 0.42, 0))
		put(sh, sphere(0.075), cloth)
		put(sh, capsule(0.062, 0.34), cloth, Vector3(0, -0.15, 0))
		var el := joint("elbow_" + side, sh, Vector3(0, -0.3, 0))
		put(el, sphere(0.058), cloth)
		put(el, capsule(0.052, 0.3), cloth, Vector3(0, -0.13, 0))
		put(el, CylinderMesh.new(), white, Vector3(0, -0.27, 0), Vector3(0.062, 0.04, 0.062))
		put(el, CylinderMesh.new(), gold, Vector3(0, -0.245, 0), Vector3(0.066, 0.012, 0.066))
		var hd := joint("hand_" + side, el, Vector3(0, -0.3, 0))
		put(hd, sphere(0.052), skin, Vector3(0, -0.04, 0), Vector3(1.0, 1.15, 0.7))
		for f in 4: put(hd, capsule(0.012, 0.07), skin, Vector3((-0.03 + f * 0.02), -0.1, 0), Vector3(1, 1, 1), Vector3(0, 0, (f - 1.5) * 0.12))
		put(hd, capsule(0.013, 0.06), skin, Vector3(0.045 * s, -0.05, 0.01), Vector3(1, 1, 1), Vector3(0, 0, -0.9 * s))
	# hoop
	hoop_mat = mat(Color.WHITE, 0.35, 0.05)
	hoop_mat.albedo_texture = stripe_tex(Color("1e8449"), Color("58d68d"))
	var tm := TorusMesh.new(); tm.inner_radius = 0.54; tm.outer_radius = 0.63; tm.rings = 48; tm.ring_segments = 16
	hoop_node = put(root, tm, hoop_mat, Vector3(0, 0.86, 0))

# ---------- portrait: a close-up of the face (no hat) drawn in the HUD so expressions are readable ----------
const PS := 160
var pvp: SubViewport
var pcam: Camera3D
var portrait_on := false:
	set(v):
		portrait_on = v
		if pvp: pvp.render_target_update_mode = SubViewport.UPDATE_ALWAYS if v else SubViewport.UPDATE_DISABLED

func _layer(n: Node, layer: int) -> void:
	if n is VisualInstance3D: (n as VisualInstance3D).layers = layer
	for c in n.get_children(): _layer(c, layer)

func _portrait() -> void:
	pvp = SubViewport.new(); pvp.size = Vector2i(PS, PS); pvp.transparent_bg = true; pvp.msaa_3d = Viewport.MSAA_4X
	pvp.world_3d = vp.world_3d; pvp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	add_child(pvp)
	pcam = Camera3D.new(); pcam.fov = 21.0; pcam.cull_mask = 1; pvp.add_child(pcam)
	pcam.look_at_from_position(Vector3(0.0, 1.56, 1.12), Vector3(0, 1.49, 0))
func ptex() -> Texture2D: return pvp.get_texture()

# ---------- life: moods, reactions, where he looks, talking ----------
var base_expr := "grin"       # the face he returns to
var react_n := ""
var react_t := 0.0
var gaze := Vector2.ZERO      # where the eyes look: x right, y up, -1..1 (the game sets this)
var talk := 0.0               # 0..1 while he speaks: the jaw and lips flap
var fo := {}                  # extra offsets on top of the blended expression (eye darts, brow flicks, breathing, talking)
var _gz := Vector2.ZERO
var _sac := Vector2.ZERO
var _sac_t := 1.0
var _brow_t := 2.0
var _brow_k := 0.0
const BLINK := {"joy": 3.2, "smug": 4.2, "anger": 5.2, "fear": 1.6, "sad": 2.6, "disgust": 2.8, "surprise": 6.5, "thought": 3.6, "fatigue": 2.4, "pain": 2.2, "calm": 3.4}

func mood(n: String) -> void:
	if n == base_expr: return
	base_expr = n
	if react_t <= 0.0: _set_target(n)

# a short reaction (pain, delight...) that falls back to the mood
func react(n: String, secs := 0.7) -> void:
	react_n = n; react_t = secs; _set_target(n)

# ---------- face ----------
# The face is a rig of named parts (fr) driven by blended parameters (fx), set with set_expr(name) and eased in pose().
# Parameter names match the HTML game's expression tables (data_expr.json): mo mw sm sk tt pu pf bo bi boL boR biL biR lid lidL lidR sq ew gx gy hr hp hy,
# plus te (tears), wet (glisten) and pd (pupil size) that only exist here.
var fr := {}           # face parts by name
var fx := {}           # current (blended) face parameters
var fx_t := {}         # target face parameters
var fx_def := {}
var expr_db := {}
var expr_fam := {}
var expr_name := "neutral"
var auto_blink := true
var _blink_t := 2.0
var _blink_k := 0.0
var _last_ms := 0
var fx_v := {}
const SPR := {"lid": [26.0, 1.0], "lidL": [26.0, 1.0], "lidR": [26.0, 1.0], "sq": [22.0, 1.0], "gx": [30.0, 1.0], "gy": [30.0, 1.0], "ew": [24.0, 0.9], "pd": [10.0, 1.0],
	"bo": [16.0, 0.75], "bi": [16.0, 0.75], "boL": [16.0, 0.75], "boR": [16.0, 0.75], "biL": [16.0, 0.75], "biR": [16.0, 0.75], "pf": [15.0, 0.8],
	"mo": [15.0, 0.6], "mw": [13.0, 0.7], "sm": [12.0, 0.75], "sk": [12.0, 0.8], "tt": [14.0, 0.9], "pu": [13.0, 0.8], "tg": [14.0, 0.7],
	"hp": [9.0, 0.8], "hr": [9.0, 0.8], "hy": [9.0, 0.8], "ns": [18.0, 0.9], "nf": [18.0, 0.9], "ch": [16.0, 0.8], "te": [3.0, 1.0], "wet": [4.0, 1.0], "fix": [10.0, 1.0]}
var _clock := 0.0
const LIP_N := 17

func _load_expr() -> void:
	var f := FileAccess.open("res://data_expr.json", FileAccess.READ)
	if f == null: return
	var d: Dictionary = JSON.parse_string(f.get_as_text())
	fx_def = d.def; expr_db = d.e; expr_fam = d.f
	fx_def["sm"] = 0.1    # the original static face had a lazy smile; the neutral table entry sets sm=0
	fx = fx_def.duplicate(); fx_t = fx_def.duplicate()
	set_expr("grin" if expr_db.has("grin") else "smile", true)

func expr_names() -> Array: return expr_db.keys()

func set_expr(name: String, snap := false) -> void:
	base_expr = name; react_t = 0.0
	_set_target(name, snap)

func _set_target(name: String, snap := false) -> void:
	if not expr_db.has(name): name = "neutral"
	expr_name = name
	fx_t = fx_def.duplicate()
	for k in expr_db[name]: fx_t[k] = expr_db[name][k]
	if snap: fx = fx_t.duplicate(); fx_v.clear()

# z of the head surface at (x, y) in head space (head sphere r 0.105 scaled 0.93, 1.1, 1)
func hz(x: float, y: float) -> float:
	return 0.105 * sqrt(maxf(0.02, 1.0 - pow(x / 0.0977, 2.0) - pow(y / 0.1155, 2.0)))

func _face(head: Node3D, skin: StandardMaterial3D, white: StandardMaterial3D, black: StandardMaterial3D) -> void:
	var skin_d := mat(skin.albedo_color.darkened(0.16), 0.7)
	var iris_m := mat(Color("4a2c17"), 0.35)
	var shine := mat(Color.WHITE, 0.1); shine.emission_enabled = true; shine.emission = Color.WHITE; shine.emission_energy_multiplier = 0.8
	var lip_m := mat(skin.albedo_color.darkened(0.3).lerp(Color("b5524a"), 0.45), 0.5)
	var mouth_m := mat(Color("4a1411"), 0.6)
	var teeth_m := mat(Color("fbf6ea"), 0.4)
	var wet_m := mat(Color(0.78, 0.9, 1.0, 0.5), 0.04); wet_m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	wet_m.emission_enabled = true; wet_m.emission = Color(0.55, 0.75, 1.0); wet_m.emission_energy_multiplier = 0.35
	var drop_m := mat(Color(0.85, 0.94, 1.0), 0.05); drop_m.emission_enabled = true; drop_m.emission = Color(0.7, 0.85, 1.0); drop_m.emission_energy_multiplier = 0.6
	fr.skin_d = skin_d
	for s: float in [-1.0, 1.0]:
		fr["cheek_" + ("l" if s < 0 else "r")] = put(head, sphere(0.03), skin, Vector3(0.05 * s, -0.034, 0.056), Vector3(1, 0.9, 0.7))
	# nose
	put(head, capsule(0.011, 0.05), skin, Vector3(0, 0.0, 0.103), Vector3(1, 1, 1), Vector3(-0.35, 0, 0))
	fr.tip = put(head, sphere(0.019), skin, Vector3(0, -0.02, 0.112), Vector3(1, 0.9, 0.95))
	for s: float in [-1.0, 1.0]:
		fr["wing_" + ("l" if s < 0 else "r")] = put(head, sphere(0.011), skin, Vector3(0.016 * s, -0.022, 0.104), Vector3(1, 0.9, 0.8))
		fr["nost_" + ("l" if s < 0 else "r")] = put(head, sphere(0.0055), skin_d, Vector3(0.0085 * s, -0.03, 0.111), Vector3(1, 0.7, 0.5))
	# eyes: white, iris + pupil + catchlight, upper lid (moves + stretches), lash line, lower lid, wet band, tear streak and drop
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		var ex: float = 0.04 * s
		fr["ex_" + sd] = ex
		fr["white_" + sd] = put(head, sphere(0.023), white, Vector3(ex, 0.025, 0.088), Vector3(1.05, 0.72, 0.5))
		var iris := put(head, sphere(0.0125), iris_m, Vector3(ex + 0.002 * s, 0.024, 0.0985), Vector3(1, 1, 0.5)); iris.name = "iris_" + sd
		fr["iris_" + sd] = iris
		fr["pupil_" + sd] = put(iris, sphere(0.006), black, Vector3(0, 0, 0.007), Vector3(1, 1, 0.6))
		fr["shine_" + sd] = put(head, sphere(0.003), shine, Vector3(ex + 0.006 * s, 0.03, 0.1075))
		fr["lid_" + sd] = put(head, sphere(0.0245), skin, Vector3(ex, 0.0365, 0.0905), Vector3(1.08, 0.46, 0.6))
		fr["lash_" + sd] = put(head, capsule(0.0035, 0.052), black, Vector3(ex, 0.0285, 0.0975), Vector3(1, 1, 0.6), Vector3(0, 0, PI / 2 - 0.12 * s))
		fr["low_" + sd] = put(head, sphere(0.02), skin_d, Vector3(ex, 0.0, 0.092), Vector3(1.1, 0.35, 0.5))
		fr["wet_" + sd] = put(head, sphere(0.02), wet_m, Vector3(ex, 0.006, 0.0975), Vector3(1.0, 0.2, 0.5))
		fr["streak_" + sd] = put(head, capsule(0.0024, 0.04), wet_m, Vector3(ex * 1.12, -0.025, hz(ex * 1.12, -0.025) + 0.0015), Vector3(1, 1, 0.7))
		fr["drop_" + sd] = put(head, sphere(0.0048), drop_m, Vector3(ex * 1.12, -0.03, hz(ex * 1.12, -0.03) + 0.003), Vector3(1, 1.5, 1))
	# brows: inner + outer piece per side
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		fr["bi_" + sd] = put(head, capsule(0.0085, 0.036), black, Vector3(0.028 * s, 0.063, 0.087), Vector3(1, 1, 0.6), Vector3(0, 0, PI / 2 + 0.1 * s))
		fr["bo_" + sd] = put(head, capsule(0.0075, 0.036), black, Vector3(0.058 * s, 0.059, 0.074), Vector3(1, 1, 0.6), Vector3(0, 0.45 * s, PI / 2 - 0.42 * s))
		fr["bm_" + sd] = put(head, capsule(0.008, 0.034), black, Vector3(0.043 * s, 0.062, 0.081), Vector3(1, 1, 0.6), Vector3(0, 0.25 * s, PI / 2 - 0.1 * s))
	# charro mustache: moves with the smile, the nose and the jaw
	var must: Array = []
	fr.must = must
	for s: float in [-1.0, 1.0]:
		var n := 18
		for i in n:
			var t := float(i) / (n - 1)
			var x := 0.004 + t * 0.064
			var y := -0.04 - sin(t * PI) * 0.006 + maxf(0.0, t - 0.55) * 0.05
			var z := 0.105 * 0.95 * sqrt(maxf(0.02, 1.0 - pow(x / 0.0977, 2.0))) + 0.007
			var r := lerpf(0.0165, 0.0065, pow(t, 0.8))
			var mn := put(head, sphere(r), black, Vector3(x * s, y, z), Vector3(1.15, 0.9, 0.9))
			must.append([mn, mn.position, t, s])
	# mouth: dark cavity, teeth, upper and lower lip rows (shaped every frame), smile-line dimples
	fr.cav = put(head, sphere(0.03), mouth_m, Vector3(0, -0.068, 0.083), Vector3(1.0, 0.46, 0.3))
	fr.teeth = put(head, BoxMesh.new(), teeth_m, Vector3(0, -0.0625, 0.0925), Vector3(0.046, 0.008, 0.004))
	fr.lipU = []; fr.lipL = []
	for i in LIP_N:
		fr.lipL.append(put(head, sphere(0.0042), lip_m, Vector3.ZERO, Vector3(1.2, 0.8, 0.8)))
		fr.lipU.append(put(head, sphere(0.0038), lip_m, Vector3.ZERO, Vector3(1.2, 0.7, 0.8)))
	for s: float in [-1.0, 1.0]:
		fr["dim_" + ("l" if s < 0 else "r")] = put(head, sphere(0.0055), skin_d, Vector3(0.042 * s, -0.056, 0.082), Vector3(1, 1.3, 0.6))
	fr.chin = put(head, sphere(0.024), skin, Vector3(0, -0.098, 0.062), Vector3(1.1, 0.8, 0.9))   # chin
	fr.tongue = put(head, sphere(0.014), mat(Color("c0525a"), 0.45), Vector3(0, -0.075, 0.08), Vector3(1.2, 0.5, 1.0))
	for s: float in [-1.0, 1.0]:
		fr["fold_" + ("l" if s < 0 else "r")] = put(head, sphere(0.007), skin_d, Vector3(0.042 * s, -0.05, 0.085), Vector3(0.6, 2.2, 0.5))   # smile line (nasolabial fold)

	# skin details that appear with expression: forehead lines, the furrow between the brows, crow's feet
	var line_m := mat(skin.albedo_color.darkened(0.3), 0.8)
	fr.fore = []
	for i in 3:
		var yy := 0.08 + i * 0.011
		fr.fore.append(put(head, capsule(0.0012, 0.05), line_m, Vector3(0, yy, hz(0, yy) + 0.001), Vector3(1, 1, 0.5), Vector3(0, 0, PI / 2)))
	fr.glab = []
	for s: float in [-1.0, 1.0]:
		fr.glab.append(put(head, capsule(0.0012, 0.02), line_m, Vector3(0.007 * s, 0.054, hz(0.007 * s, 0.054) + 0.001), Vector3(1, 1, 0.5), Vector3(0, 0, 0.12 * s)))
	fr.crow = []
	for s: float in [-1.0, 1.0]:
		for a in [-0.55, 0.0, 0.55]:
			var cx: float = 0.066 * s + 0.007 * s * cos(a); var cy: float = 0.022 + 0.008 * sin(a)
			var nd := put(head, capsule(0.0011, 0.014), line_m, Vector3(cx, cy, hz(cx, cy) + 0.001), Vector3(1, 1, 0.5), Vector3(0, 0, atan2(-s * cos(a), sin(a))))
			fr.crow.append(nd)

	# more muscles: brow bunch between the brows, cheek puffs, lip-corner knots, chin dimple, jaw (masseter) bulges, forehead vein
	var vein_m := mat(Color(0.55, 0.22, 0.2), 0.7)
	fr.bunch = put(head, sphere(0.009), skin_d, Vector3(0, 0.052, hz(0, 0.052) - 0.002), Vector3(1.0, 0.8, 0.5))
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		fr["puff_" + sd] = put(head, sphere(0.02), skin, Vector3(0.042 * s, -0.01, 0.088), Vector3(1.2, 0.28, 0.6))
		fr["corner_" + sd] = put(head, sphere(0.0055), skin_d, Vector3(0.04 * s, -0.07, 0.085), Vector3(1, 1, 0.6))
		fr["mass_" + sd] = put(head, sphere(0.02), skin, Vector3(0.078 * s, -0.052, 0.03), Vector3(0.5, 1.0, 0.8))
		fr["vein_" + sd] = put(head, capsule(0.0013, 0.03), vein_m, Vector3(0.06 * s, 0.092, hz(0.06 * s, 0.092) + 0.001), Vector3(1, 1, 0.5), Vector3(0, 0, 0.5 * s))
	fr.dimple = put(head, sphere(0.006), skin_d, Vector3(0, -0.092, 0.081), Vector3(1.4, 0.8, 0.5))
	_apply_face()

func _fp(k: String) -> float: return float(fx.get(k, 0.0)) + float(fo.get(k, 0.0))

# shapes every face part from the current parameters
func _apply_face() -> void:
	if fr.is_empty() or fx.is_empty(): return
	var blink := _blink_k
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		var ex: float = fr["ex_" + sd]
		# upper lid: its lower edge sits at 0.0084 (closed) .. 0.042 (wide); below half-open it grows taller so it can cover the eye
		var bis := _fp("bi") + _fp("biL" if s < 0 else "biR")
		var bos := _fp("bo") + _fp("boL" if s < 0 else "boR")
		var pf := _fp("pf")
		var glare := maxf(pf, maxf(0.0, -bis) * 0.8)
		var lid := clampf(_fp("lid") + _fp("lidL" if s < 0 else "lidR") - _fp("sq") * 0.08 - glare * 0.08 - maxf(0.0, _fp("sm") - 0.3) * 0.1, 0.0, 1.0)
		lid = maxf(lid, minf(_fp("lid") + _fp("lidL" if s < 0 else "lidR"), 0.1)) * (1.0 - blink)   # a glare narrows the eye but keeps the iris visible
		var tilt := clampf(glare * 0.4 - maxf(0.0, bis) * 0.3, -0.4, 0.45)
		var sy := 0.46 + maxf(0.0, 0.5 - lid) * 1.0
		var h := 0.0245 * sy
		var bottom := 0.0084 + lid * 0.0336
		var lidn: MeshInstance3D = fr["lid_" + sd]
		lidn.scale = Vector3(1.08, sy, 0.45); lidn.position = Vector3(ex, bottom + h, 0.089); lidn.rotation.z = s * tilt
		var lsh: Node3D = fr["lash_" + sd]
		lsh.position = Vector3(ex, bottom + 0.0035, 0.0975); lsh.rotation.z = PI / 2 - 0.12 * s + s * tilt
		var ew := _fp("ew")
		(fr["white_" + sd] as Node3D).scale = Vector3(1.05 + ew * 0.1, 0.72 + ew * 0.12, 0.5)
		# lower lid rises with squint, tears or a wet look
		var sq := clampf(_fp("sq") + _fp("wet") * 0.15 + maxf(0.0, _fp("sm")) * 0.2, 0.0, 1.0)
		var low: MeshInstance3D = fr["low_" + sd]
		low.position = Vector3(ex, sq * 0.013, 0.092); low.scale = Vector3(1.1, 0.35 + sq * 0.3, 0.5)
		# gaze and pupil
		var gx := _fp("gx"); var gy := _fp("gy")
		var ir: MeshInstance3D = fr["iris_" + sd]
		ir.position = Vector3(ex + 0.002 * s + gx * 0.008, 0.024 + gy * 0.0055, 0.0985 - absf(gx) * 0.002)
		var sh: Node3D = fr["shine_" + sd]
		var shy := minf(0.03 + gy * 0.0055, bottom - 0.003)   # the catchlight slides down under the lid edge
		sh.position = Vector3(ex + 0.006 * s + gx * 0.008, shy, 0.1075)
		sh.visible = shy > 0.016
		ir.visible = lid > 0.05
		ir.position.z -= clampf(0.5 - lid, 0.0, 0.5) * 0.01    # iris sinks behind a drooped lid
		var pd := 1.0 + _fp("pd") * 0.6 + _fp("ew") * 0.35
		(fr["pupil_" + sd] as Node3D).scale = Vector3(pd, pd, 0.6)
		ir.scale = Vector3(1.0 + _fp("ew") * 0.1, 1.0 + _fp("ew") * 0.1, 0.5)
		# tears: glistening band on the lower lid, a streak down the cheek and a drop that runs along it
		var wet := _fp("wet"); var te := _fp("te")
		var wn: MeshInstance3D = fr["wet_" + sd]
		wn.visible = wet > 0.04
		wn.position = Vector3(ex, 0.0075 + sq * 0.013, 0.0985); wn.scale = Vector3(1.0, 0.12 + wet * 0.16, 0.5)
		var st: MeshInstance3D = fr["streak_" + sd]
		var drop: MeshInstance3D = fr["drop_" + sd]
		st.visible = te > 0.08; drop.visible = te > 0.08
		if te > 0.08:
			var x := ex * (1.1 + 0.04 * te)
			var ln := 0.02 + te * 0.055
			var ym := 0.0 - ln * 0.5 - 0.004
			st.position = Vector3(x, ym, hz(x, ym) + 0.0015)
			st.scale = Vector3(1, ln / 0.04, 0.7)
			var ph := fmod(_clock * (0.35 + te * 0.4) + (0.0 if s < 0 else 0.45), 1.0)
			var dy := -0.004 - ln * ph
			drop.position = Vector3(x, dy, hz(x, dy) + 0.003)
			drop.scale = Vector3(1, 1.5, 1) * (0.7 + te * 0.5) * (1.0 - ph * 0.4)
		# brows: raise, lower and tilt (inner higher = sad/worried, inner lower = angry), pinch together, overhang the eye when scowling
		var bdrop := maxf(0.0, -bis)
		var bi: MeshInstance3D = fr["bi_" + sd]
		bi.position = Vector3(0.028 * s - 0.012 * pf * s - 0.006 * bdrop * s, 0.063 + 0.02 * bis - 0.012 * pf, 0.087 + 0.004 * glare)
		bi.rotation = Vector3(0, 0, PI / 2 + s * clampf(0.1 + 0.6 * (bos - bis) + 0.4 * pf, -0.85, 0.95))
		var bo: MeshInstance3D = fr["bo_" + sd]
		bo.position = Vector3(0.058 * s - 0.005 * pf * s, 0.059 + 0.016 * bos - 0.006 * pf - 0.006 * bdrop, 0.074 + 0.003 * glare)
		bo.rotation = Vector3(0, 0.45 * s, PI / 2 + s * clampf(-0.42 + 0.5 * (bos - bis) + 0.35 * pf, -0.9, 0.7))
		var bm: MeshInstance3D = fr["bm_" + sd]
		var arch := 0.003 + 0.004 * clampf((bos + bis) * 0.5, -0.5, 1.0) - 0.004 * glare       # the brow arches when raised and flattens when scowling
		bm.position = Vector3(0.043 * s - 0.008 * pf * s, (bi.position.y + bo.position.y) * 0.5 + arch, 0.081 + 0.004 * glare)
		bm.rotation = Vector3(0, 0.25 * s, PI / 2 + s * ((bi.rotation.z + bo.rotation.z) * 0.5 - PI / 2))
	# mouth: half-width w, smile sm lifts corners (frown drops them), mo opens the jaw, pu puckers, sk skews
	var sm := _fp("sm"); var mo := clampf(_fp("mo"), 0.0, 1.0)
	var w := 0.036 * (1.0 + 0.5 * _fp("mw")) * (1.0 - 0.45 * _fp("pu"))
	var A := 0.010 + sm * (0.016 if sm > 0.0 else 0.022)
	var sk := _fp("sk")
	for i in LIP_N:
		var t := float(i) / (LIP_N - 1) * 2.0 - 1.0
		var t2 := t * t
		var x := t * w
		var skw := sk * 0.008 * t
		var zz := 0.0895 - absf(t) * 0.006
		var yl := -0.0735 - mo * 0.03 * (1.0 - 0.5 * t2) + A * (t2 - 0.5) + skw - maxf(0.0, -sm) * 0.008 * t2
		var yu := -0.0635 + A * 0.5 * (t2 - 0.5) + skw + _fp("ns") * 0.004
		(fr.lipL[i] as Node3D).position = Vector3(x, yl + _fp("pu") * 0.003, zz + _fp("pu") * 0.006 * (1.0 - 0.5 * t2))
		(fr.lipU[i] as Node3D).position = Vector3(x, yu, zz)
	var cav: MeshInstance3D = fr.cav
	cav.position = Vector3(0, -0.0685 - mo * 0.012, 0.083)
	cav.scale = Vector3(w / 0.03 * 0.95, 0.25 + mo * 0.7, 0.3)
	var tn: MeshInstance3D = fr.teeth
	var show := maxf(_fp("tt") * 0.9, mo * 1.2)
	tn.visible = show > 0.18
	tn.position = Vector3(0, -0.0615 + _fp("ns") * 0.004, 0.0925); tn.scale = Vector3(w * 1.25, 0.008 + minf(1.0, show) * 0.004, 0.004)
	for s: float in [-1.0, 1.0]:
		var d: Node3D = fr["dim_" + ("l" if s < 0 else "r")]
		d.position = Vector3((w + 0.006) * s, -0.0735 - mo * 0.03 * 0.5 + A * 0.5 + 0.012 + sm * 0.01, 0.082)

	# facial muscles: cheeks lift with a smile or squint, the nose wrinkles and flares, the mustache rides the upper lip, the jaw drops, the tongue shows
	var sq2 := _fp("sq"); var ns := _fp("ns"); var nf := _fp("nf"); var ch := _fp("ch"); var tg := _fp("tg")
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		var ck: Node3D = fr["cheek_" + sd]
		var up := maxf(0.0, sm) * 0.7 + sq2 * 0.8
		ck.position = Vector3(0.05 * s, -0.034 + up * 0.011 - maxf(0.0, -sm) * 0.004, 0.056 + up * 0.004)
		ck.scale = Vector3(1.0 + up * 0.18, 0.9 + up * 0.25, 0.7 + up * 0.15)
		var wg: Node3D = fr["wing_" + sd]
		wg.position = Vector3(0.016 * s * (1.0 + nf * 0.35), -0.022 + ns * 0.005, 0.104)
		wg.scale = Vector3(1.0 + nf * 0.3, 0.9 - ns * 0.15, 0.8)
		var nt: Node3D = fr["nost_" + sd]
		nt.position = Vector3(0.0085 * s * (1.0 + nf * 0.5), -0.03 + ns * 0.005, 0.111)
		nt.scale = Vector3(1.0 + nf * 0.5, 0.7 + nf * 0.6, 0.5)
		var fd: Node3D = fr["fold_" + sd]
		fd.position = Vector3((w + 0.008) * s, -0.052 + maxf(0.0, sm) * 0.012 + ns * 0.004 - mo * 0.008, 0.085)
		fd.scale = Vector3(0.6, 1.6 + maxf(0.0, sm) * 1.5 + ns * 1.0, 0.5)
	(fr.tip as Node3D).position = Vector3(0, -0.02 + ns * 0.004 - maxf(0.0, _fp("pu")) * 0.002, 0.112 + nf * 0.002)
	for m in fr.must:
		var nd: Node3D = m[0]; var b: Vector3 = m[1]; var mt: float = m[2]; var ms: float = m[3]
		var dy := maxf(0.0, sm) * 0.007 * mt * mt + ns * 0.005 - maxf(0.0, -sm) * 0.006 * mt * mt - mo * 0.006 * (1.0 - mt) + sk * 0.003 * ms * mt
		var dx := _fp("mw") * 0.01 * mt * ms - _fp("pu") * 0.012 * mt * ms
		nd.position = b + Vector3(dx, dy, 0.0)
	var jaw: Node3D = fr.jaw
	jaw.position = Vector3(0, -0.06 - mo * 0.01, 0.02 + ch * 0.004)
	var chn: Node3D = fr.chin
	chn.position = Vector3(ch * 0.003, -0.098 - mo * 0.009 + maxf(0.0, -sm) * 0.004 - _fp("pu") * 0.002, 0.062 + ch * 0.004)
	chn.scale = Vector3(1.1 - ch * 0.1, 0.8 + maxf(0.0, -sm) * 0.15, 0.9)
	# deeper muscles: corrugator bunch, cheek puffs, zygomatic lip-corner knots, mentalis dimple, masseter, forehead vein
	var glr := maxf(_fp("pf"), maxf(0.0, -_fp("bi")) * 0.8)
	var bn: Node3D = fr.bunch
	bn.visible = glr > 0.35
	bn.scale = Vector3(0.45 + glr * 0.35, 1.0 + glr * 0.9, 0.35 + glr * 0.2)
	var twa := _fp("tw1"); var twb := _fp("tw2")
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		var up2 := maxf(0.0, sm) * 0.6 + sq2 * 0.7 + _fp("wet") * 0.3
		var pf2: Node3D = fr["puff_" + sd]
		pf2.position = Vector3(0.042 * s, -0.012 + up2 * 0.011, 0.088 + up2 * 0.002)
		pf2.scale = Vector3(1.2, 0.28 + up2 * 0.32, 0.6)
		var cn: Node3D = fr["corner_" + sd]
		var cy: float = (fr.lipL[LIP_N - 1 if s > 0.0 else 0] as Node3D).position.y
		cn.position = Vector3((w + 0.003) * s, cy + 0.002 + twa * 0.0008 * s, 0.085)
		cn.scale = Vector3(1.0 + absf(sm) * 0.5 + _fp("mw") * 0.3, 1.0 + absf(sm) * 0.5, 0.6)
		var ms: Node3D = fr["mass_" + sd]
		var cl := clampf(ch * 0.8 + glr * 0.4 + _fp("tt") * 0.15 - mo * 0.2, 0.0, 1.0)
		ms.position = Vector3(0.082 * s, -0.05 - mo * 0.006, 0.012)
		ms.scale = Vector3(0.32 + cl * 0.2, 1.0 + cl * 0.1, 0.7 + cl * 0.1)
		var vn: Node3D = fr["vein_" + sd]
		var rage := clampf(glr + sq2 * 0.5 + ns * 0.4 - 1.25, 0.0, 1.0) * 2.5
		vn.visible = rage > 0.1; vn.scale = Vector3(1, minf(1.4, rage), 0.5)
	var dm: Node3D = fr.dimple
	var mn := clampf(maxf(0.0, -sm) * 0.6 + _fp("pu") * 0.7 + ch * 0.4 - mo * 0.7, 0.0, 1.0)
	dm.visible = mn > 0.15
	dm.position = Vector3(0, -0.092 - mo * 0.009 + mn * 0.003, 0.081); dm.scale = Vector3(1.4 + mn * 0.6, 0.8 + mn * 0.5, 0.5)
	# skin details: forehead lines with raised brows, the furrow with a scowl, crow's feet with a big smile or squint
	var rz := (_fp("bo") + _fp("bi") + _fp("boL") + _fp("boR") + _fp("biL") + _fp("biR")) * 0.5
	for i in 3:
		var n3: Node3D = fr.fore[i]; var am := clampf((rz - 0.25 - i * 0.14) * 3.0, 0.0, 1.0)
		n3.visible = am > 0.05; n3.scale = Vector3(1, maxf(am, 0.01) * (1.3 - i * 0.15), 0.5)
	var gl := clampf((maxf(_fp("pf"), maxf(0.0, -_fp("bi")) * 0.8) - 0.2) * 1.6, 0.0, 1.0)
	for n3 in fr.glab:
		(n3 as Node3D).visible = gl > 0.05; (n3 as Node3D).scale = Vector3(1, maxf(gl, 0.01), 0.5)
	var cr := clampf((maxf(0.0, sm) * 0.6 + sq2 * 0.8 - 0.35) * 1.6, 0.0, 1.0)
	for n3 in fr.crow:
		(n3 as Node3D).visible = cr > 0.05; (n3 as Node3D).scale = Vector3(1, maxf(cr, 0.01), 0.5)
	var tn2: MeshInstance3D = fr.tongue
	tn2.visible = tg > 0.08 and mo > 0.12
	tn2.position = Vector3(0, -0.0715 - mo * 0.014, 0.082 + tg * 0.012)
	tn2.scale = Vector3(1.2, 0.5 + tg * 0.2, 1.0 + tg * 0.8)

# eases the face toward its target; called from pose() (uses real time, so no extra plumbing in main.gd)
func face_update() -> void:
	if fx.is_empty(): return
	var now := Time.get_ticks_msec()
	var dt := clampf((now - _last_ms) / 1000.0, 0.001, 0.1) if _last_ms > 0 else 0.016
	_last_ms = now; _clock += dt
	if react_t > 0.0:
		react_t -= dt
		if react_t <= 0.0: _set_target(base_expr)
	# every muscle group is a damped spring with its own speed: eyes snap, brows and mouth follow with a little overshoot, the jaw bounces, tears build slowly
	var steps := 2
	var hh := dt / steps
	for _i in steps:
		for key in fx_t:
			var pr: Array = SPR.get(key, [12.0, 1.0])
			var x: float = fx.get(key, 0.0); var v: float = fx_v.get(key, 0.0)
			v += ((float(fx_t[key]) - x) * pr[0] * pr[0] - 2.0 * pr[1] * pr[0] * v) * hh
			fx[key] = x + v * hh; fx_v[key] = v
	fo["tw1"] = sin(_clock * 3.1) * sin(_clock * 1.3 + 1.0); fo["tw2"] = sin(_clock * 2.3 + 2.0) * sin(_clock * 0.9)
	var fam: String = expr_fam.get(expr_name, "calm")
	# eyes: follow the gaze target, with small darting jumps (not while staring)
	var stare := clampf(_fp_raw("fix"), 0.0, 1.0)
	_sac_t -= dt
	if _sac_t < 0.0:
		_sac_t = randf_range(0.5, 2.2) * (1.8 if fam == "fatigue" else 1.0)
		_sac = Vector2(randf_range(-0.28, 0.28), randf_range(-0.2, 0.2)) * (1.0 - stare)
	_gz = _gz.lerp(gaze, 1.0 - exp(-dt * 14.0))
	fo["gx"] = clampf(_gz.x * 0.9 + _sac.x, -1.2, 1.2) * (1.0 - stare * 0.6)
	fo["gy"] = clampf(_gz.y * 0.8 + _sac.y, -1.2, 1.2) * (1.0 - stare * 0.6)
	# brows: now and then one lifts a little; breathing nudges the mouth and chest-driven head bob
	_brow_t -= dt
	if _brow_t < 0.0: _brow_t = randf_range(1.2, 3.5); _brow_k = randf_range(0.12, 0.3)
	_brow_k = maxf(0.0, _brow_k - dt * 0.5)
	fo["bo"] = _brow_k * (1.0 - stare); fo["bi"] = _brow_k * 0.4 * (1.0 - stare)
	var breath := 0.5 + 0.5 * sin(_clock * 1.7)
	fo["mo"] = breath * 0.018 + talk * (0.1 + 0.3 * absf(sin(_clock * 11.0)) * (0.6 + 0.4 * sin(_clock * 4.3)))
	fo["mw"] = talk * 0.3 * sin(_clock * 6.5); fo["pu"] = talk * 0.2 * maxf(0.0, sin(_clock * 6.5 + 2.0))
	# blinking: gap and length depend on the feeling (fear flutters, tiredness drags)
	if auto_blink:
		_blink_t -= dt
		var half := 0.14 if fam == "fatigue" else 0.075
		if _blink_t < 0.0: _blink_t = BLINK.get(fam, 3.4) * randf_range(0.7, 1.3)
		_blink_k = clampf(1.0 - absf(_blink_t + half) / half, 0.0, 1.0) if _blink_t > -2.0 * half and _blink_t < 0.0 else 0.0
	else: _blink_k = 0.0
	_apply_face()

func _fp_raw(k: String) -> float: return float(fx.get(k, 0.0))

func _thin_torus() -> TorusMesh:
	var t := TorusMesh.new(); t.inner_radius = 0.985; t.outer_radius = 1.0; t.rings = 48; t.ring_segments = 6; return t

# ---------- pose ----------
# phase: hula cycle in radians. wave: 0..1 arm waving. hurt: 0..1.
func pose(phase: float, bank := 0.0, wave := 1.0, hurt := 0.0) -> void:
	var c := cos(phase); var s := sin(phase)
	root.rotation.y = yaw + bank * 0.35
	var pel: Node3D = j.pelvis
	pel.position = Vector3(c * 0.06, 0.82 + sin(phase * 2.0) * 0.018, s * 0.05)
	pel.rotation = Vector3(0, s * 0.1, -c * 0.08)
	(j.spine as Node3D).rotation = Vector3(0.03, -s * 0.08, c * 0.075 + bank * 0.12)
	(j.neck as Node3D).rotation = Vector3(0, s * 0.05, -c * 0.04)
	(j.head as Node3D).rotation = Vector3(0.04 + sin(phase * 2.0) * 0.03 + _fp("hp") * 1.0, look.x * 0.4 + s * 0.05 + _fp("hy") * 0.6, c * 0.05 + _fp("hr") * 0.8)
	(j.hat as Node3D).rotation = Vector3(-0.16, 0, c * 0.05)
	for side in ["l", "r"]:
		var d := -1.0 if side == "l" else 1.0
		(j["hip_" + side] as Node3D).rotation = Vector3(sin(phase * 2.0 + (0.0 if side == "l" else 1.2)) * 0.07 - 0.04, 0, d * 0.03 - c * 0.04)
		(j["knee_" + side] as Node3D).rotation = Vector3(0.1 + sin(phase * 2.0 + (0.0 if side == "l" else 1.2)) * 0.1, 0, 0)
		(j["ankle_" + side] as Node3D).rotation = Vector3(-0.05, 0, 0)
		var w := sin(phase * 1.0 + (0.0 if side == "l" else PI)) * wave
		(j["shoulder_" + side] as Node3D).rotation = Vector3(0.0, 0, d * (2.45 + w * 0.2))
		(j["elbow_" + side] as Node3D).rotation = Vector3(0.25 * hurt, 0, d * (0.6 + (0.5 + 0.5 * w) * 0.4 * wave))
		(j["hand_" + side] as Node3D).rotation = Vector3(0, 0, d * w * 0.35)
	# hoop circles the waist
	hoop_node.position = Vector3(c * 0.13, 0.86 + sin(phase * 2.0) * 0.018, s * 0.13)
	hoop_node.rotation = Vector3(-s * 0.16, 0, c * 0.16)
	hoop_mat.uv1_offset.x = -phase / TAU * 3.0
	face_update()

func set_hoop(col_a: Color, col_b: Color) -> void:
	hoop_mat.albedo_texture = stripe_tex(col_a, col_b)

const HAT_COL := ["efe3c3", "2b2b30", "c0392b", "f7f7f7", "f1c40f", "ff6bd5"]
var _cos_key := ""
func set_cos(hat_i: int, hoop_i: int, defs: Dictionary) -> void:
	var k := "%d_%d" % [hat_i, hoop_i]
	if k == _cos_key: return
	_cos_key = k
	(hat_mats[0] as StandardMaterial3D).albedo_color = Color(HAT_COL[clampi(hat_i, 0, HAT_COL.size() - 1)])
	var h: Dictionary = defs.hoop[clampi(hoop_i, 0, defs.hoop.size() - 1)]
	if h.get("c") != null: set_hoop(Color(h.c[0]), Color(h.c[1]))
	else: set_hoop(Color("ff4fa3"), Color("48dbfb"))
