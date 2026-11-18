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
	vp.own_world_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	_world(); _build()

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
	put(head, sphere(0.06), skin, Vector3(0, -0.06, 0.02), Vector3(0.95, 0.75, 0.9))       # jaw
	put(head, sphere(0.02), skin, Vector3(0, -0.01, 0.105))                                    # nose
	put(head, sphere(0.02), skin, Vector3(-0.104, 0, 0.0), Vector3(0.5, 1.1, 0.8)); put(head, sphere(0.02), skin, Vector3(0.104, 0, 0.0), Vector3(0.5, 1.1, 0.8))
	for s in [-1, 1]:
		put(head, sphere(0.022), white, Vector3(0.04 * s, 0.025, 0.088), Vector3(1, 0.8, 0.5))
		var iris := put(head, sphere(0.012), black, Vector3(0.04 * s, 0.024, 0.099), Vector3(1, 1, 0.5)); iris.name = "iris_" + ("l" if s < 0 else "r")
		put(head, capsule(0.008, 0.07), black, Vector3(0.043 * s, 0.058, 0.093), Vector3(1, 1, 0.6), Vector3(0, 0, PI / 2 + 0.12 * s))   # brow
	# mustache + smile
	for s in [-1, 1]:
		put(head, capsule(0.014, 0.075), black, Vector3(0.036 * s, -0.04, 0.1), Vector3(1, 1, 0.7), Vector3(0, 0, PI / 2 + 0.35 * s))
	var smile := put(head, TorusMesh.new(), mat(Color("5a1f1a"), 0.6), Vector3(0, -0.066, 0.092), Vector3(0.05, 0.03, 0.02), Vector3(PI / 2, 0, 0))
	(smile.mesh as TorusMesh).inner_radius = 0.7; (smile.mesh as TorusMesh).outer_radius = 1.0
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
	(j.head as Node3D).rotation = Vector3(0.04 + sin(phase * 2.0) * 0.03, look.x * 0.4 + s * 0.05, c * 0.05)
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
	var m := Color.WHITE.lerp(Color(1, 0.45, 0.45), hurt)
	for n in root.get_children(): pass

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
