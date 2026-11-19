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
var hoop_bone: Node3D          # the hoop rides this bone, so the mesh can live in the file like the rest
var hoop_glb: MeshInstance3D   # the file's hoop, which takes the code's fade
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
	_world(); _rig(); _build(); _layer(j.hat, 2); _load_rig(); _portrait(); _load_expr()

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
	var n := MeshInstance3D.new(); n.mesh = mesh; n.material_override = m; n.position = pos; n.scale = scl; n.rotation = rot
	n.name = "%s_%d" % [parent.name, parent.get_child_count()]   # stable id: the same code path names the same part the same way, so the Blender round-trip can match it
	parent.add_child(n); return n

# ---------- the skeleton ----------
# The rig is declared once, here: [name, parent, rest position, rest rotation]. _rig() builds every bone from this list
# before a single mesh is added, so a bone's parent, its rest pose and its length live in exactly one place and every mesh
# then hangs off a bone. Nothing about the shape is declared here, and the choreography never names a mesh.
# Poses are deltas from this rest (see _muscle): the bones carry the pose, the muscles trail it.
# The two sides and the fingers are mirrored, so the list is built instead of written out twice.
func _declare_bones() -> Array:
	var out: Array = [
		["root", "", Vector3.ZERO],
		["pelvis", "root", Vector3(0, 0.82, 0)],
		["spine", "pelvis", Vector3(0, 0.07, 0)],
		["spine2", "spine", Vector3(0, 0.15, 0)],           # mid-spine: the back curves through three joints instead of two
		["chest", "spine2", Vector3(0, 0.15, 0)],           # upper body twists on this, above the waist joint
		["neck", "chest", Vector3(0, 0.2, 0)],
		["neck2", "neck", Vector3(0, 0.1, 0)],              # upper neck: the head turns on this, the neck bends in two places
		["head", "neck2", Vector3(0, 0.1, 0)],
		["jaw", "head", Vector3(0, -0.05, -0.045)],         # the jaw hinge: the mouth opens by turning this bone, not by moving the lips
		["hat", "head", Vector3(0, 0.07, -0.012)],
	]
	for s in [-1, 1]:
		var side := "l" if s < 0 else "r"
		out.append_array([
			["hip_" + side, "pelvis", Vector3(0.1 * s, -0.04, 0)],
			["thigh_" + side, "hip_" + side, Vector3.ZERO],          # thigh twist: knees and toes turn out / in
			["knee_" + side, "thigh_" + side, Vector3(0, -0.36, 0)],
			["shin_" + side, "knee_" + side, Vector3.ZERO],          # shin twist
			["ankle_" + side, "shin_" + side, Vector3(0, -0.34, 0)],
			["foot_" + side, "ankle_" + side, Vector3(0, -0.06, -0.04)],   # pivots on the heel: toe taps and flicks
			["toe_" + side, "foot_" + side, Vector3(0, 0.01, 0.13)],       # ball of the foot: heel lifts, toe taps
			["clav_" + side, "chest", Vector3(0.08 * s, 0.12, 0)],   # collarbone: shrugs and rolls the shoulder
			["shoulder_" + side, "clav_" + side, Vector3(0.14 * s, 0, 0)],
			["uarm_" + side, "shoulder_" + side, Vector3.ZERO],      # upper-arm twist
			["elbow_" + side, "uarm_" + side, Vector3(0, -0.3, 0)],
			["fore_" + side, "elbow_" + side, Vector3.ZERO],         # forearm twist (palm turns)
			["hand_" + side, "fore_" + side, Vector3(0, -0.3, 0)],   # wrist
			["thumb_" + side, "hand_" + side, Vector3(0.04 * s, -0.045, 0.012), Vector3(0, 0, -0.9 * s)],
			["hair_" + side, "head", Vector3(0.068 * s, 0.03, -0.055), Vector3(0, 0, 0.08 * s)],   # pivots at the top so the lock can swing
			# eyes: a real ball that turns inside two lids, so the iris can never slide off the eye
			["white_" + side, "head", Vector3(0.04 * s, 0.025, 0.0725)],
			["iris_" + side, "white_" + side, Vector3.ZERO],
			["pupil_" + side, "iris_" + side, Vector3.ZERO],
			["lidu_" + side, "head", Vector3(0.04 * s, 0.025, 0.0725)],     # upper lid
			["lidl_" + side, "head", Vector3(0.04 * s, 0.025, 0.0725)],     # lower lid
			["brow_" + side, "head", Vector3(0.043 * s, 0.062, 0.081)],     # brow ridge: raise and tilt live on this bone; the three brow pieces are local detail
		])
		for f in 4:            # four fingers, two joints each
			out.append(["fg%d_%s" % [f, side], "hand_" + side, Vector3(-0.03 + f * 0.02, -0.075, 0)])
			out.append(["fh%d_%s" % [f, side], "fg%d_%s" % [f, side], Vector3(0, -0.048, 0)])
	return out

var rig := {}                 # name -> {parent, rest, rot}: what _declare_bones() asked for
func _rig() -> void:
	for e in _declare_bones():
		var n := String(e[0]); var p := String(e[1])
		var nd := Node3D.new(); nd.name = n; nd.position = e[2]
		if e.size() > 3: nd.rotation = e[3]
		if p == "": root = nd; vp.add_child(nd)
		else: (j[p] as Node3D).add_child(nd)
		j[n] = nd
		rig[n] = {"parent": p, "rest": nd.position, "rot": nd.rotation}

# the bone a mesh hangs off, by name. The rig is the only thing that knows where a bone sits.
func b(name: String) -> Node3D:
	var n: Node3D = j.get(name)
	if n == null: push_error("rig: no bone named " + name)
	return n

# a face control bone: a plain Node3D the face code poses instead of posing the mesh directly. The mesh sits at local
# zero under it, so the same transform math the code already used now drives a bone - and the whole face rig is a set
# of named nodes that shows up in Blender and can be edited there.
func _fb(nm: String, parent: Node3D, pos: Vector3, rot := Vector3.ZERO) -> Node3D:
	var nd := Node3D.new(); nd.name = nm; nd.position = pos; nd.rotation = rot; parent.add_child(nd); j[nm] = nd
	rig[nm] = {"parent": parent.name, "rest": pos, "rot": rot}
	return nd

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
	# the skeleton is already standing (see _rig): this only hangs meshes off it
	var skin := mat(Color("a9714b"), 0.55); skin.albedo_texture = _skin_tex(); skin.uv1_scale = Vector3(2.2, 2.2, 1.0)
	var cloth := mat(Color.WHITE, 0.85); cloth.albedo_texture = jacket_tex()
	var red := mat(Color("a3121c"), 0.85)
	var red_nc := mat(Color("a3121c"), 0.85); red_nc.cull_mode = BaseMaterial3D.CULL_DISABLED
	var gold := mat(Color("e7b84a"), 0.35, 0.8)
	var silver := mat(Color("d8dde6"), 0.25, 0.9)
	var leather := mat(Color("8a5a2b"), 0.6)
	var boot := mat(Color("1b1412"), 0.35, 0.15)
	var black := mat(Color("120c09"), 0.72)
	var white := mat(Color("f4efe6"), 0.6)
	var felt := mat(Color("efe3c3"), 0.9)
	mats = {"felt": felt, "skin": skin}
	# pelvis & legs
	var pel := b("pelvis")
	put(pel, capsule(0.12, 0.34), red, Vector3(0, 0.02, 0), Vector3(1.25, 0.5, 0.9), Vector3(0, 0, PI / 2))
	for s in [-1, 1]:
		var side := "l" if s < 0 else "r"
		var hip := b("hip_" + side)
		var thigh := b("thigh_" + side)          # thigh twist: knees and toes turn out / in
		put(thigh, lathe([Vector2(0.095, 0.05), Vector2(0.104, -0.02), Vector2(0.101, -0.1), Vector2(0.09, -0.21), Vector2(0.079, -0.31), Vector2(0.076, -0.37)], 32), red_nc)
		put(hip, sphere(0.097), red)
		var knee := b("knee_" + side)
		put(knee, sphere(0.08), red)
		var shin := b("shin_" + side)          # shin twist
		put(shin, lathe([Vector2(0.076, 0.02), Vector2(0.084, -0.05), Vector2(0.086, -0.11), Vector2(0.074, -0.2), Vector2(0.06, -0.29), Vector2(0.056, -0.34)], 32), red_nc)
		var ank := b("ankle_" + side)
		put(ank, capsule(0.075, 0.2), boot, Vector3(0, 0.03, 0))
		var foot := b("foot_" + side)       # pivots on the heel: toe taps and flicks
		put(foot, capsule(0.065, 0.14), boot, Vector3(0, 0.01, 0.07), Vector3(1, 1, 1.2), Vector3(PI / 2, 0, 0))
		var toe := b("toe_" + side)       # ball of the foot: heel lifts, toe taps
		put(toe, capsule(0.06, 0.12), boot, Vector3(0, 0, 0.05), Vector3(1, 1, 1.1), Vector3(PI / 2, 0, 0))
		put(toe, sphere(0.04), gold, Vector3(0, 0.02, 0.1))
		# gold trouser stripe
		put(thigh, BoxMesh.new(), gold, Vector3(0.088 * s, -0.19, 0), Vector3(0.008, 0.34, 0.02), Vector3(0, 0, -s * 0.045))
	# torso / jacket
	var spine := b("spine")
	put(spine, capsule(0.18, 0.52), cloth, Vector3(0, 0.22, 0), Vector3(1.0, 1.0, 0.75))
	var spine2 := b("spine2")      # mid-spine: the back curves through three joints instead of two
	var chest := b("chest")        # upper body twists on this, above the waist joint
	put(chest, capsule(0.2, 0.3), cloth, Vector3(0, 0.03, 0), Vector3(1.08, 0.8, 0.72))
	# collar & buttons
	put(chest, TorusMesh.new(), gold, Vector3(0, 0.2, 0), Vector3(0.1, 0.1, 0.1))
	for k in 4: put(spine, sphere(0.013), silver, Vector3(0, 0.4 - k * 0.07, 0.13))
	# belt + buckle
	var belt := put(spine, CylinderMesh.new(), leather, Vector3(0, 0.02, 0), Vector3(0.175, 0.045, 0.125))
	belt.mesh = (belt.mesh as CylinderMesh); (belt.mesh as CylinderMesh).radial_segments = 32
	put(spine, BoxMesh.new(), silver, Vector3(0, 0.02, 0.122), Vector3(0.07, 0.06, 0.02))
	put(spine, BoxMesh.new(), gold, Vector3(0, 0.02, 0.134), Vector3(0.04, 0.035, 0.012))
	# head
	var neck := b("neck")
	put(neck, CylinderMesh.new(), skin, Vector3(0, 0.07, 0), Vector3(0.125, 0.14, 0.125))      # the neck: runs from inside the collar up under the jaw
	put(neck, sphere(0.085), skin, Vector3(0, -0.02, 0.0), Vector3(1.0, 0.6, 0.85))      # wide base: neck flares into the shoulders
	var neck2 := b("neck2")       # upper neck: the head turns on this, the neck bends in two places
	var head := b("head"); head.scale = Vector3(1.22, 1.22, 1.22)
	fr.head = put(head, _head_mesh(), skin)
	fr.jaw = put(b("jaw"), sphere(0.058), skin, Vector3(0, -0.06, 0.016) - JAW_P, Vector3(0.86, 0.72, 0.88))       # jaw, on the jaw bone
	_face(head, skin, white, black)
	put(head, sphere(0.018), skin, Vector3(-0.100, -0.042, -0.008), Vector3(0.40, 1.05, 0.80)); put(head, sphere(0.018), skin, Vector3(0.100, -0.042, -0.008), Vector3(0.40, 1.05, 0.80))
	# hair: a shell that hugs the skull - high above the brows at the front, down over the nape at the back - with a long
	# flat lock falling behind each side. The old pair of rounded blobs beside the head read as ears; this reads as hair.
	var black_nc := mat(Color("120c09"), 0.78); black_nc.cull_mode = BaseMaterial3D.CULL_DISABLED
	put(head, _hair_cap(0.0977, 0.1155, 0.105, 0.088, -0.012, -0.10), black_nc)
	for s in [-1, 1]:
		var lock := b("hair_" + ("l" if s < 0 else "r"))      # pivots at the top so the lock can swing
		put(lock, lathe([Vector2(0.010, 0.04), Vector2(0.030, 0.0), Vector2(0.040, -0.08), Vector2(0.042, -0.16), Vector2(0.036, -0.24), Vector2(0.024, -0.31), Vector2(0.010, -0.36), Vector2(0.001, -0.385)], 24), black_nc, Vector3.ZERO, Vector3(0.88, 1.0, 1.15))
	# sombrero
	var hat := b("hat")
	var brim := lathe([Vector2(0.09, 0.0), Vector2(0.20, -0.005), Vector2(0.30, 0.0), Vector2(0.40, 0.03), Vector2(0.43, 0.065), Vector2(0.425, 0.07), Vector2(0.395, 0.04), Vector2(0.30, 0.012), Vector2(0.20, 0.005), Vector2(0.09, 0.012)])
	var crown := lathe([Vector2(0.1, 0.0), Vector2(0.098, 0.06), Vector2(0.088, 0.13), Vector2(0.074, 0.178), Vector2(0.05, 0.198), Vector2(0.0, 0.205)])
	var hm := mat(Color("efe3c3"), 0.9); hm.cull_mode = BaseMaterial3D.CULL_DISABLED
	var band := mat(Color("b3121f"), 0.6); band.cull_mode = BaseMaterial3D.CULL_DISABLED
	var hm2 := mat(Color("f3d27a"), 0.3, 0.6); hm2.cull_mode = BaseMaterial3D.CULL_DISABLED
	var b0 := put(hat, brim, hm, Vector3.ZERO, Vector3(0.68, 1.0, 0.68)); var c0 := put(hat, crown, hm, Vector3.ZERO, Vector3(0.88, 1.0, 0.88))
	hat_mats = [hm, band, hm2]
	put(hat, lathe([Vector2(0.1, 0.012), Vector2(0.1005, 0.05), Vector2(0.1, 0.05)]), band, Vector3.ZERO, Vector3(0.9, 1, 0.9))
	put(hat, TorusMesh.new(), hm2, Vector3(0, 0.032, 0), Vector3(0.089, 0.1, 0.089)); (hat.get_child(hat.get_child_count() - 1).mesh as TorusMesh).inner_radius = 0.96; (hat.get_child(hat.get_child_count() - 1).mesh as TorusMesh).outer_radius = 1.0
	put(hat, TorusMesh.new(), hm2, Vector3(0, 0.055, 0), Vector3(0.286, 0.43, 0.286)).mesh = _thin_torus()
	# arms (raised, waving)
	for s in [-1, 1]:
		var side := "l" if s < 0 else "r"
		var clav := b("clav_" + side)       # collarbone: shrugs and rolls the shoulder
		var sh := b("shoulder_" + side)
		put(sh, sphere(0.075), cloth)
		put(sh, sphere(0.085), cloth, Vector3(0.012 * s, 0.01, 0.0), Vector3(1.0, 1.05, 1.1))                       # deltoid cap
		put(chest, sphere(0.1), cloth, Vector3(0.095 * s, 0.185, -0.005), Vector3(1.5, 0.55, 0.95), Vector3(0, 0, -0.32 * s))   # trapezius slope from neck to shoulder
		var ua := b("uarm_" + side)             # upper-arm twist
		put(ua, capsule(0.062, 0.34), cloth, Vector3(0, -0.15, 0))
		var el := b("elbow_" + side)
		put(el, sphere(0.058), cloth)
		var fo_ := b("fore_" + side)             # forearm twist (palm turns)
		put(fo_, capsule(0.052, 0.3), cloth, Vector3(0, -0.13, 0))
		put(fo_, CylinderMesh.new(), white, Vector3(0, -0.27, 0), Vector3(0.062, 0.04, 0.062))
		put(fo_, CylinderMesh.new(), gold, Vector3(0, -0.245, 0), Vector3(0.066, 0.012, 0.066))
		var hd := b("hand_" + side)      # wrist
		put(hd, sphere(0.052), skin, Vector3(0, -0.04, 0), Vector3(1.0, 1.15, 0.7))
		for f in 4:            # four fingers, two joints each
			var f1 := b("fg%d_%s" % [f, side])
			f1.rotation = Vector3(0, 0, (f - 1.5) * 0.12)
			put(f1, capsule(0.012, 0.045 + (0.008 if f == 1 or f == 2 else 0.0)), skin, Vector3(0, -0.024, 0))
			var f2 := b("fh%d_%s" % [f, side])
			put(f2, capsule(0.011, 0.04), skin, Vector3(0, -0.02, 0))
		var tb := b("thumb_" + side)   # thumb
		tb.rotation = Vector3(0, 0, -0.9 * s)
		put(tb, capsule(0.013, 0.05), skin, Vector3(0, -0.026, 0))
	# hoop
	hoop_mat = mat(Color.WHITE, 0.35, 0.05)
	hoop_mat.albedo_texture = stripe_tex(Color("1e8449"), Color("58d68d"))
	hoop_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA       # faded by gk so it never pops when a gesture takes over
	var tm := TorusMesh.new(); tm.inner_radius = 0.54; tm.outer_radius = 0.63; tm.rings = 48; tm.ring_segments = 16
	hoop_bone = _fb("hoop", root, Vector3(0, 0.86, 0))
	hoop_node = put(hoop_bone, tm, hoop_mat, Vector3.ZERO)
	_apply_glb()

# Option B: the geometry can come from a .glb authored in Blender. The code still builds the rig and every part
# (so all the posing, springs and face logic keep working), then each part's mesh is swapped for the one with the
# same name in character.glb. Parts the Blender file does not name are left procedural, so a partial edit is safe.
const GLB_PATH := "res://art/character.glb"
var glb_parts := 0            # how many part meshes came from the .glb (0 = procedural build)
func _apply_glb() -> void:
	if FileAccess.file_exists(RIG_GLB): return   # the whole rig comes from the file instead
	if not FileAccess.file_exists(GLB_PATH): return
	var doc := GLTFDocument.new(); var st := GLTFState.new()
	if doc.append_from_file(GLB_PATH, st) != OK: return
	var src := doc.generate_scene(st)
	if src == null: return
	var by := {}
	var stack: Array = [src]
	while not stack.is_empty():
		var nd: Node = stack.pop_back()
		if nd is MeshInstance3D and (nd as MeshInstance3D).mesh != null: by[String(nd.name)] = (nd as MeshInstance3D).mesh
		for c in nd.get_children(): stack.append(c)
	var walk: Array = [root]
	while not walk.is_empty():
		var nd: Node = walk.pop_back()
		if nd is MeshInstance3D and by.has(String(nd.name)):
			(nd as MeshInstance3D).mesh = by[String(nd.name)]
			glb_parts += 1
		for c in nd.get_children(): walk.append(c)
	src.free()
	print("hero3d: %d part meshes from %s" % [glb_parts, GLB_PATH])

# ---------- the rig comes from the file ----------
# When character_skinned.glb is present the character is drawn from it: its skeleton is driven by the same control rig
# the pose code already moves, so the mesh AND the rig can be authored in Blender and the game picks them up. The parts
# the code rebuilds or moves every frame (the hoop, the lip and mustache tubes) stay procedural and keep drawing from
# the control rig, because a loaded skinned mesh is static geometry.
const RIG_GLB := "res://art/character_skinned.glb"
const RIG_REF := "res://art/character_rig.json"   # the joint transforms the .glb was exported from
var rig_scene: Node3D
var rig_skel: Skeleton3D
var rig_bone := {}            # bone name -> skeleton bone index
var rig_mesh := {}            # control mesh -> the glb mesh that replaces it
var rig_c := {}               # bone name -> rest frame mapping (bone rest into the joint's rest)
var rig_cinv := {}            # bone name -> inverse of rig_c
var rig_pre := {}             # bone name -> parent's rig_c inverse
var rig_parts := 0

func _load_rig() -> void:
	if not FileAccess.file_exists(RIG_GLB): return
	var doc := GLTFDocument.new(); var st := GLTFState.new()
	if doc.append_from_file(RIG_GLB, st) != OK: return
	rig_scene = doc.generate_scene(st)
	if rig_scene == null: return
	root.get_parent().add_child(rig_scene)
	var by := {}
	var stack: Array = [rig_scene]
	while not stack.is_empty():
		var nd: Node = stack.pop_back()
		if nd is Skeleton3D:
			rig_skel = nd
			for i in rig_skel.get_bone_count(): rig_bone[rig_skel.get_bone_name(i)] = i
		elif nd is MeshInstance3D: by[String(nd.name)] = nd
		for c in nd.get_children(): stack.append(c)
	if rig_skel == null: return
	# The file is exported from a settled expression, so the rig it was built from is that pose, not the build-time
	# rest. The export writes those joint transforms to character_rig.json, and the game reads them here - no guessing.
	if not FileAccess.file_exists(RIG_REF): return
	var jf := FileAccess.open(RIG_REF, FileAccess.READ)
	var refd = JSON.parse_string(jf.get_as_text()); jf.close()
	var rest := {}
	if refd is Dictionary:
		for name in refd:
			var a: Array = refd[name]
			rest[name] = Transform3D(Basis(Vector3(a[0], a[1], a[2]), Vector3(a[3], a[4], a[5]), Vector3(a[6], a[7], a[8])), Vector3(a[9], a[10], a[11]))
	for name in rig_bone:
		if not rest.has(name): continue
		var i: int = rig_bone[name]
		var rj: Transform3D = rest[name]
		var c: Transform3D = rj.affine_inverse() * rig_skel.get_bone_global_rest(i)
		rig_c[name] = c
		rig_cinv[name] = c.affine_inverse()
		var pb := rig_skel.get_bone_parent(i)
		if pb >= 0 and rig_cinv.has(rig_skel.get_bone_name(pb)): rig_pre[name] = rig_cinv[rig_skel.get_bone_name(pb)]
	var walk: Array = [root]
	while not walk.is_empty():
		var nd: Node = walk.pop_back()
		if nd is MeshInstance3D:
			var cm := nd as MeshInstance3D
			var g := by.get(String(cm.name)) as MeshInstance3D
			if g != null:
				if cm == hoop_node:
					hoop_glb = g                 # the file's hoop takes the code's fade instead of drawing the control mesh
					cm.layers = 0
				else:
					g.layers = cm.layers         # the glb mesh inherits the control mesh's render layer (e.g. the hat)
					g.material_override = cm.material_override   # the file carries geometry; the code keeps its materials
					cm.layers = 0                # ...and the control mesh stops drawing
					rig_mesh[cm] = g
					rig_parts += 1
		for c in nd.get_children(): walk.append(c)
	print("hero3d: rig from %s: %d bones, %d parts" % [RIG_GLB, rig_skel.get_bone_count(), rig_parts])

# copy the control rig onto the loaded skeleton, and carry each part's visibility across
func _rig_sync() -> void:
	if rig_skel == null or rig_c.is_empty(): return
	for name in rig_bone:
		var nd: Node3D = j.get(name)
		if nd == null: continue
		var i: int = rig_bone[name]
		var pose: Transform3D = (rig_pre.get(name, Transform3D.IDENTITY) as Transform3D) * nd.transform * (rig_c.get(name, Transform3D.IDENTITY) as Transform3D)
		rig_skel.set_bone_pose_position(i, pose.origin)
		rig_skel.set_bone_pose_rotation(i, pose.basis.get_rotation_quaternion())
		rig_skel.set_bone_pose_scale(i, pose.basis.get_scale())
	for cm in rig_mesh:
		var vis: bool = (cm as MeshInstance3D).visible
		var p: Node = (cm as Node3D).get_parent()
		while vis and p is Node3D:
			if not (p as Node3D).visible: vis = false
			p = p.get_parent()
		(rig_mesh[cm] as MeshInstance3D).visible = vis
	if hoop_glb != null:
		hoop_glb.visible = hoop_node.visible
		hoop_glb.transparency = hoop_node.transparency

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
	pcam.look_at_from_position(Vector3(0.0, 1.61, 1.12), Vector3(0, 1.54, 0))
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
var fixed_dt := 0.0
const SPR := {"lid": [26.0, 1.0], "lidL": [26.0, 1.0], "lidR": [26.0, 1.0], "sq": [22.0, 1.0], "gx": [30.0, 1.0], "gy": [30.0, 1.0], "ew": [24.0, 0.9], "pd": [10.0, 1.0],
	"bo": [16.0, 0.75], "bi": [16.0, 0.75], "boL": [16.0, 0.75], "boR": [16.0, 0.75], "biL": [16.0, 0.75], "biR": [16.0, 0.75], "pf": [15.0, 0.8],
	"mo": [15.0, 0.6], "mw": [13.0, 0.7], "sm": [12.0, 0.75], "sk": [12.0, 0.8], "tt": [14.0, 0.9], "pu": [13.0, 0.8], "tg": [14.0, 0.7],
	"hp": [9.0, 0.8], "hr": [9.0, 0.8], "hy": [9.0, 0.8], "ns": [18.0, 0.9], "nf": [18.0, 0.9], "ch": [16.0, 0.8], "te": [3.0, 1.0], "wet": [4.0, 1.0], "fix": [10.0, 1.0]}
var _clock := 0.0
const LIP_N := 17
# the head is an ellipsoid (these are its semi-axes in head space) and the eyes sit in a socket carved out of it, so
# EYE_R is the ball and EYE_X/Y/Z its centre: the ball is set back into the hollow instead of riding on a bump.
const HEAD_A := 0.09765
const HEAD_B := 0.1155
const HEAD_C := 0.105
const EYE_X := 0.04
const EYE_Y := 0.025
const EYE_Z := 0.0725
const EYE_R := 0.0235
const TOOTH_U := 6            # upper teeth in the visible row
const TOOTH_L := 6            # lower teeth (only shown when the mouth is really open)
const TOOTH_H := 0.0105       # tooth height
const TOOTH_D := 0.005        # tooth depth (front to back)
# The mouth is posed, not drawn: the jaw is a bone, and the parts that belong to it (lower lip, chin, tongue, its corner
# knots) hang off it. JAW_P is the hinge in head space and JAW_OPEN the angle at mo = 1, picked so the lower lip drops the
# same 0.03 the old per-part translation used to, so the mouth reads the same but the opening now comes from one bone.
const JAW_P := Vector3(0, -0.05, -0.045)
const JAW_OPEN := 0.23

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
	if snap:
		fx = fx_t.duplicate(); fx_v.clear()
		_cp.clear(); _fcs.clear(); fc.clear()   # snap means no trailing flesh either

# z of the head surface at (x, y) in head space (head sphere r 0.105 scaled 0.93, 1.1, 1)
func hz(x: float, y: float) -> float:
	return HEAD_C * sqrt(maxf(0.02, 1.0 - pow(x / HEAD_A, 2.0) - pow(y / HEAD_B, 2.0)))

# the head: an ellipsoid with a shallow dish carved around each eye. The dish is pushed back along the surface normal so
# its rim stays smooth and reads as a socket, which is what stops the eyeball from looking like a ball stuck on the face.
# Built as a UV sphere with shared vertices (no UVs needed - the skin has no texture) so the exported mesh stays small.
# The triangle order matches Godot's own primitives (lathe/SphereMesh) and the normals are the negated face cross
# product, which is the outward direction under that winding - the one convention that survives the glTF round-trip.
func _head_mesh() -> ArrayMesh:
	var seg := 48; var rings := 24
	var pts := PackedVector3Array(); var idx := PackedInt32Array()
	pts.append(_face_pt(_socket_pt(Vector3(0, HEAD_B, 0))))             # north pole
	for r in range(1, rings):
		var phi := PI * float(r) / rings
		var yy := cos(phi) * HEAD_B; var rr := sin(phi)
		for i in seg:
			var th := TAU * float(i) / seg
			pts.append(_face_pt(_socket_pt(Vector3(cos(th) * rr * HEAD_A, yy, sin(th) * rr * HEAD_C))))
	var south := pts.size()
	pts.append(_face_pt(_socket_pt(Vector3(0, -HEAD_B, 0))))
	var uvs := PackedVector2Array(); uvs.resize(pts.size())             # spherical UVs so the skin can carry a texture
	uvs[0] = Vector2(0.5, 0.0)
	for r in range(1, rings):
		for i in seg:
			uvs[1 + (r - 1) * seg + i] = Vector2(float(i) / seg, float(r) / rings)
	uvs[south] = Vector2(0.5, 1.0)
	for i in seg:
		var j := (i + 1) % seg
		idx.append(0); idx.append(1 + i); idx.append(1 + j)             # north cap
	for r in range(1, rings - 1):
		var a := 1 + (r - 1) * seg; var b := 1 + r * seg
		for i in seg:
			var j := (i + 1) % seg
			idx.append(a + i); idx.append(b + i); idx.append(b + j)
			idx.append(a + i); idx.append(b + j); idx.append(a + j)
	var last := 1 + (rings - 2) * seg
	for i in seg:
		var j := (i + 1) % seg
		idx.append(last + i); idx.append(south); idx.append(last + j)   # south cap
	var ns := PackedVector3Array(); ns.resize(pts.size())
	for i in ns.size(): ns[i] = Vector3.ZERO
	var t := 0
	while t + 2 < idx.size():
		var a: int = idx[t]; var b: int = idx[t + 1]; var c: int = idx[t + 2]
		var n := (pts[c] - pts[a]).cross(pts[b] - pts[a])
		ns[a] += n; ns[b] += n; ns[c] += n
		t += 3
	for i in ns.size():
		var L := ns[i].length()
		ns[i] = ns[i] / L if L > 0.000001 else Vector3.UP
	var arr := []; arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = pts; arr[Mesh.ARRAY_NORMAL] = ns; arr[Mesh.ARRAY_TEX_UV] = uvs; arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new(); am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return am

# The head is not a pure ellipsoid: below the mouth line it narrows and recedes into a jaw and a chin, so the lower
# face cannot read as a ball. Everything that sits on the lower face (chin, jaw, cheeks) is placed against this, so
# the jaw tucks under the face instead of bulging past it.
func _face_pt(p: Vector3) -> Vector3:
	var t := smoothstep(0.06, 0.125, -p.y)
	if t > 0.0:
		p.x *= 1.0 - 0.34 * t * t
		p.z *= 1.0 - 0.28 * t * t
		p.y -= 0.006 * t * t
	return p

func _socket_pt(p: Vector3) -> Vector3:
	if p.z <= 0.0: return p
	var dep := 0.0
	for s: float in [-1.0, 1.0]:
		var dx := (p.x - EYE_X * s) / 0.038
		var dy := (p.y - EYE_Y) / 0.030
		dep = maxf(dep, 1.0 - smoothstep(0.25, 1.0, sqrt(dx * dx + dy * dy)))
	if dep <= 0.0: return p
	var n := Vector3(p.x / (HEAD_A * HEAD_A), p.y / (HEAD_B * HEAD_B), p.z / (HEAD_C * HEAD_C)).normalized()
	return p - n * (0.0125 * dep * dep)

func _face(head: Node3D, skin: StandardMaterial3D, white: StandardMaterial3D, black: StandardMaterial3D) -> void:
	var J := b("jaw")       # the lower jaw: everything below the mouth line hangs off this bone
	var skin_d := mat(skin.albedo_color.darkened(0.16), 0.7)
	var iris_m := mat(Color.WHITE, 0.3); iris_m.albedo_texture = _iris_tex(); iris_m.emission_enabled = true; iris_m.emission_texture = iris_m.albedo_texture; iris_m.emission_energy_multiplier = 0.45
	iris_m.cull_mode = BaseMaterial3D.CULL_DISABLED
	var black_nc2 := mat(Color("050303"), 0.25); black_nc2.cull_mode = BaseMaterial3D.CULL_DISABLED
	var lid_base := skin.albedo_color.lightened(0.04)
	var lidv_m := mat(Color.WHITE, 0.85); lidv_m.vertex_color_use_as_albedo = true; lidv_m.cull_mode = BaseMaterial3D.CULL_DISABLED; lidv_m.metallic_specular = 0.08
	var sclera_m := mat(Color("e8e3d8"), 0.45); sclera_m.metallic_specular = 0.06
	var lid_m := mat(skin.albedo_color.lightened(0.04), 0.9); lid_m.metallic_specular = 0.05
	var shine := mat(Color.WHITE, 0.1); shine.emission_enabled = true; shine.emission = Color.WHITE; shine.emission_energy_multiplier = 0.8
	var lip_m := mat(skin.albedo_color.darkened(0.34).lerp(Color("b5524a"), 0.58), 0.5)
	var mouth_m := mat(Color("64211a"), 0.6)
	# soft-edged skin for the cheeks, chin and jaw muscles: the shape fades out where it meets the head, so it reads as a swelling of the same skin and not a separate lump
	var soft_sh := Shader.new()
	soft_sh.code = "shader_type spatial;\nrender_mode blend_mix, depth_draw_always, cull_back;\nuniform vec4 col : source_color;\nvoid fragment() {\n\tALBEDO = col.rgb;\n\tROUGHNESS = 0.55;\n\tfloat f = clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0);\n\tALPHA = smoothstep(0.3, 1.0, f) * 0.9;\n}\n"
	var soft_m := ShaderMaterial.new(); soft_m.shader = soft_sh; soft_m.set_shader_parameter("col", skin.albedo_color)
	# the muscle blobs (cheeks, puffs, masseters) are swelling, not lumps: they fade out much more than the chin does, so
	# a smile reads as the skin filling rather than as a separate blob laid on the face
	var muscle_sh := Shader.new()
	muscle_sh.code = "shader_type spatial;\nrender_mode blend_mix, depth_draw_opaque, cull_back;\nuniform vec4 col : source_color;\nvoid fragment() {\n\tALBEDO = col.rgb;\n\tROUGHNESS = 0.6;\n\tfloat f = clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0);\n\tALPHA = smoothstep(0.0, 1.0, f) * 0.38;\n}\n"
	var muscle_m := ShaderMaterial.new(); muscle_m.shader = muscle_sh; muscle_m.set_shader_parameter("col", skin.albedo_color)
	var teeth_m := mat(Color.WHITE, 0.32); teeth_m.albedo_texture = _tooth_tex(); teeth_m.uv1_scale = Vector3(3.0, 2.0, 1.0)
	var wet_m := mat(Color(0.78, 0.9, 1.0, 0.5), 0.04); wet_m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	wet_m.emission_enabled = true; wet_m.emission = Color(0.55, 0.75, 1.0); wet_m.emission_energy_multiplier = 0.35
	var drop_m := mat(Color(0.85, 0.94, 1.0), 0.05); drop_m.emission_enabled = true; drop_m.emission = Color(0.7, 0.85, 1.0); drop_m.emission_energy_multiplier = 0.6
	fr.skin_d = skin_d
	for s: float in [-1.0, 1.0]:
		var csd := "l" if s < 0 else "r"
		put(_fb("cheek_" + csd, head, Vector3(0.046 * s, -0.034, 0.054)), sphere(0.026), muscle_m); fr["cheek_" + csd] = b("cheek_" + csd)
	# nose
	put(head, capsule(0.010, 0.05), skin, Vector3(0, 0.0, 0.101), Vector3(1, 1, 1), Vector3(-0.35, 0, 0))
	put(_fb("nose_tip", head, Vector3(0, -0.019, 0.107)), sphere(0.016), skin, Vector3.ZERO, Vector3(1.05, 0.92, 0.95)); fr.tip = b("nose_tip")
	for s: float in [-1.0, 1.0]:
		var nsd := "l" if s < 0 else "r"
		put(_fb("nose_wing_" + nsd, head, Vector3(0.015 * s, -0.022, 0.100)), sphere(0.010), skin); fr["wing_" + nsd] = b("nose_wing_" + nsd)
		put(_fb("nose_nost_" + nsd, head, Vector3(0.0085 * s, -0.029, 0.104)), sphere(0.0052), skin_d); fr["nost_" + nsd] = b("nose_nost_" + nsd)
	# eyes: white, iris + pupil + catchlight, upper lid (moves + stretches), lash line, lower lid, wet band, tear streak and drop
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		var ex: float = EYE_X * s
		fr["ex_" + sd] = ex
		var ec := Vector3(ex, EYE_Y, EYE_Z)         # eyeball centre: a real ball that turns inside two lids, so the iris can never slide off the eye
		fr["ec_" + sd] = ec
		# a dark liner filling the dish behind the ball, so the socket reads as shadow instead of more skin
		fr["soc_" + sd] = put(head, sphere(0.025), skin_d, Vector3(ex, EYE_Y, EYE_Z - 0.005), Vector3(1.05, 0.82, 0.60))
		var ball := b("white_" + sd)
		fr["white_" + sd] = ball
		put(ball, sphere(EYE_R), sclera_m)
		var iris := b("iris_" + sd)
		fr["iris_" + sd] = iris
		put(iris, _cap(EYE_R * 1.002, asin(0.0138 / EYE_R), true), iris_m)
		var pup := b("pupil_" + sd)
		fr["pupil_" + sd] = pup
		put(pup, _cap(EYE_R * 1.004, asin(0.0050 / EYE_R), false), black_nc2)
		fr["shine_" + sd] = put(_fb("shine_" + sd, head, ec), sphere(0.0026), shine, Vector3.ZERO, Vector3(1, 1, 0.35))
		fr["shine2_" + sd] = put(_fb("shine2_" + sd, head, ec), sphere(0.0011), shine, Vector3.ZERO, Vector3(1, 1, 0.35))
		var lu := b("lidu_" + sd); fr["lid_" + sd] = lu
		put(lu, _lidmesh(EYE_R + 0.0022, true, lid_base, skin_d.albedo_color), lidv_m)
		var ll := b("lidl_" + sd); fr["low_" + sd] = ll
		put(ll, _lidmesh(EYE_R + 0.0022, false, lid_base, skin_d.albedo_color), lidv_m)
		put(_fb("wet_" + sd, head, Vector3(ex, 0.006, 0.0945)), sphere(0.02), wet_m); fr["wet_" + sd] = b("wet_" + sd)
		put(_fb("streak_" + sd, head, Vector3(ex * 1.12, -0.025, hz(ex * 1.12, -0.025) + 0.0015)), capsule(0.0024, 0.04), wet_m); fr["streak_" + sd] = b("streak_" + sd)
		put(_fb("drop_" + sd, head, Vector3(ex * 1.12, -0.03, hz(ex * 1.12, -0.03) + 0.003)), sphere(0.0048), drop_m); fr["drop_" + sd] = b("drop_" + sd)
	# brows: the ridge is a bone; inner / middle / outer pieces are small local offsets on it
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		var br := b("brow_" + sd)
		fr["brow_" + sd] = br
		fr["bi_" + sd] = put(br, capsule(0.0085, 0.036), black, Vector3(-0.015 * s, 0.001, 0.006), Vector3(1, 1, 0.6), Vector3(0, 0, PI / 2 + 0.26 * s))
		fr["bo_" + sd] = put(br, capsule(0.0075, 0.036), black, Vector3(0.015 * s, -0.003, -0.007), Vector3(1, 1, 0.6), Vector3(0, 0.45 * s, PI / 2 - 0.26 * s))
		fr["bm_" + sd] = put(br, capsule(0.008, 0.034), black, Vector3.ZERO, Vector3(1, 1, 0.6), Vector3(0, 0.25 * s, PI / 2))
	# charro mustache: moves with the smile, the nose and the jaw
	var must: Array = []
	fr.must = must
	for s: float in [-1.0, 1.0]:
		var n := 18
		var msd := "l" if s < 0 else "r"
		for i in n:
			var t := float(i) / (n - 1)
			var x := 0.003 + t * 0.048
			var y := -0.043 - sin(t * PI) * 0.004 + maxf(0.0, t - 0.6) * 0.019
			var z := hz(x, y) + 0.002
			var r := lerpf(0.0130, 0.0050, pow(t, 0.85))
			var mn := _fb("must_%s_%d" % [msd, i], head, Vector3(x * s, y, z))
			put(mn, sphere(r), black, Vector3.ZERO, Vector3(1.2, 0.9, 0.9))
			mn.visible = false
			must.append([mn, mn.position, t, s])
	# mouth: dark cavity, two rows of separate teeth (laid along the mouth arc every frame), upper and lower lip
	# rows (shaped every frame), smile-line dimples
	put(_fb("mouth_cav", head, Vector3(0, -0.068, 0.083)), sphere(0.03), mouth_m); fr.cav = b("mouth_cav")
	var tbox := BoxMesh.new(); tbox.size = Vector3.ONE
	fr.tooth_u = []; fr.tooth_l = []
	for i in TOOTH_U:
		put(_fb("tooth_u_%d" % i, head, Vector3(0, -0.0625, 0.0925)), tbox, teeth_m)
		var tu := b("tooth_u_%d" % i); tu.visible = false; fr.tooth_u.append(tu)
	for i in TOOTH_L:
		put(_fb("tooth_l_%d" % i, J, Vector3(0, -0.0735, 0.0895) - JAW_P), tbox, teeth_m)
		var tl := b("tooth_l_%d" % i); tl.visible = false; fr.tooth_l.append(tl)
	var tube_m := lip_m.duplicate(); tube_m.cull_mode = BaseMaterial3D.CULL_DISABLED
	var must_m := mat(Color("0d0908"), 0.75); must_m.cull_mode = BaseMaterial3D.CULL_DISABLED; must_m.rim_enabled = true; must_m.rim = 0.25; must_m.rim_tint = 0.0
	for nm in ["lipUm", "lipLm", "mustm_l", "mustm_r"]:
		var mi := MeshInstance3D.new(); mi.mesh = ArrayMesh.new(); mi.name = nm; mi.material_override = (must_m if nm.begins_with("must") else tube_m)
		(J if nm == "lipLm" else head).add_child(mi); fr[nm] = mi
	fr.lipU = []; fr.lipL = []
	for i in LIP_N:
		var bl := _fb("lipL_%d" % i, J, Vector3.ZERO); put(bl, sphere(0.0042), lip_m, Vector3.ZERO, Vector3(1.2, 0.8, 0.8)); bl.visible = false; fr.lipL.append(bl)
		var bu := _fb("lipU_%d" % i, head, Vector3.ZERO); put(bu, sphere(0.0038), lip_m, Vector3.ZERO, Vector3(1.2, 0.7, 0.8)); bu.visible = false; fr.lipU.append(bu)
	put(_fb("chin", J, Vector3(0, -0.100, 0.036) - JAW_P), sphere(0.025), soft_m); fr.chin = b("chin")   # chin, on the jaw bone
	put(_fb("tongue", J, Vector3(0, -0.075, 0.08) - JAW_P), sphere(0.014), mat(Color("c0525a"), 0.45)); fr.tongue = b("tongue")
	for s: float in [-1.0, 1.0]:
		var fsd := "l" if s < 0 else "r"
		put(_fb("fold_" + fsd, head, Vector3(0.042 * s, -0.05, 0.085)), sphere(0.005), skin_d); fr["fold_" + fsd] = b("fold_" + fsd)   # smile line (nasolabial fold)

	# skin details that appear with expression: forehead lines, the furrow between the brows, crow's feet
	var line_m := mat(skin.albedo_color.darkened(0.3), 0.8)
	fr.fore = []
	for i in 3:
		var yy := 0.08 + i * 0.011
		put(_fb("fore_%d" % i, head, Vector3(0, yy, hz(0, yy) + 0.001), Vector3(0, 0, PI / 2)), capsule(0.0012, 0.05), line_m)
		fr.fore.append(b("fore_%d" % i))
	fr.glab = []
	for s: float in [-1.0, 1.0]:
		var gsd := "l" if s < 0 else "r"
		put(_fb("glab_" + gsd, head, Vector3(0.007 * s, 0.054, hz(0.007 * s, 0.054) + 0.001), Vector3(0, 0, 0.12 * s)), capsule(0.0012, 0.02), line_m)
		fr.glab.append(b("glab_" + gsd))
	fr.crow = []
	for s: float in [-1.0, 1.0]:
		var csd := "l" if s < 0 else "r"
		var ci := 0
		for a in [-0.55, 0.0, 0.55]:
			var cx: float = 0.066 * s + 0.007 * s * cos(a); var cy: float = 0.022 + 0.008 * sin(a)
			var cnm := "crow_%s_%d" % [csd, ci]
			put(_fb(cnm, head, Vector3(cx, cy, hz(cx, cy) + 0.001), Vector3(0, 0, atan2(-s * cos(a), sin(a)))), capsule(0.0011, 0.014), line_m)
			fr.crow.append(b(cnm)); ci += 1

	# more muscles: brow bunch between the brows, cheek puffs, lip-corner knots, chin dimple, jaw (masseter) bulges, forehead vein
	var vein_m := mat(Color(0.55, 0.22, 0.2), 0.7)
	put(_fb("bunch", head, Vector3(0, 0.052, hz(0, 0.052) - 0.002)), sphere(0.009), skin_d); fr.bunch = b("bunch")
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		put(_fb("puff_" + sd, head, Vector3(0.042 * s, -0.01, 0.088)), sphere(0.017), muscle_m); fr["puff_" + sd] = b("puff_" + sd)
		put(_fb("corner_" + sd, J, Vector3(0.04 * s, -0.07, 0.085) - JAW_P), sphere(0.0016), skin_d); fr["corner_" + sd] = b("corner_" + sd)
		put(_fb("mass_" + sd, head, Vector3(0.073 * s, -0.052, 0.03)), sphere(0.02), muscle_m); fr["mass_" + sd] = b("mass_" + sd)
		put(_fb("vein_" + sd, head, Vector3(0.06 * s, 0.092, hz(0.06 * s, 0.092) + 0.001), Vector3(0, 0, 0.5 * s)), capsule(0.0013, 0.03), vein_m); fr["vein_" + sd] = b("vein_" + sd)
	put(_fb("dimple", J, Vector3(0, -0.092, 0.066) - JAW_P), sphere(0.006), skin_d); fr.dimple = b("dimple")
	_apply_face()

# a spherical cap facing +Z (the iris and pupil): polar-disc UVs so a round texture fits it
func _cap(r: float, ang: float, with_uv: bool, rings := 10, seg := 32) -> ArrayMesh:
	var vs := PackedVector3Array(); var ns := PackedVector3Array(); var uvs := PackedVector2Array(); var idx := PackedInt32Array()
	vs.append(Vector3(0, 0, r)); ns.append(Vector3(0, 0, 1)); uvs.append(Vector2(0.5, 0.5))
	for ri in range(1, rings + 1):
		var t := ang * ri / rings
		for si in seg:
			var f := TAU * si / seg
			var p := Vector3(sin(t) * cos(f), sin(t) * sin(f), cos(t))
			vs.append(p * r); ns.append(p)
			var rho := float(ri) / rings * 0.5
			uvs.append(Vector2(0.5 + rho * cos(f), 0.5 + rho * sin(f)))
	for si in seg:
		idx.append(0); idx.append(1 + si); idx.append(1 + (si + 1) % seg)
	for ri in range(1, rings):
		for si in seg:
			var a := 1 + (ri - 1) * seg + si; var b := 1 + (ri - 1) * seg + (si + 1) % seg
			idx.append(a); idx.append(a + seg); idx.append(b); idx.append(b); idx.append(a + seg); idx.append(b + seg)
	var arr := []; arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = vs; arr[Mesh.ARRAY_NORMAL] = ns; arr[Mesh.ARRAY_TEX_UV] = uvs; arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new(); am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return am

# a hair shell that hugs the skull: it follows the head ellipsoid (A, B, C), growing a little thicker towards the crown,
# and its lower edge sits high above the brows at the front, sweeps down at the sides and runs furthest down the nape.
# Because the edge is flush with the skin at t = 0 the hairline reads as a clean line and never floats off the face.
func _hair_cap(A: float, B: float, C: float, y_front: float, y_side: float, y_back: float, thick := 0.1, seg := 48, rows := 16) -> ArrayMesh:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES); st.set_smooth_group(0)
	for r in rows:
		var t0 := float(r) / rows; var t1 := float(r + 1) / rows
		for i in seg:
			var f0 := TAU * i / seg; var f1 := TAU * (i + 1) / seg
			var a := _hair_pt(A, B, C, y_front, y_side, y_back, thick, f0, t0)
			var b2 := _hair_pt(A, B, C, y_front, y_side, y_back, thick, f1, t0)
			var c2 := _hair_pt(A, B, C, y_front, y_side, y_back, thick, f0, t1)
			var d := _hair_pt(A, B, C, y_front, y_side, y_back, thick, f1, t1)
			st.add_vertex(a); st.add_vertex(c2); st.add_vertex(d)
			st.add_vertex(a); st.add_vertex(d); st.add_vertex(b2)
	st.generate_normals()
	return st.commit()

func _hair_pt(A: float, B: float, C: float, y_front: float, y_side: float, y_back: float, thick: float, f: float, t: float) -> Vector3:
	var sf := sin(f)                                             # +1 towards the front (+Z), -1 towards the back
	var ye := lerpf(y_side, y_front if sf >= 0.0 else y_back, absf(sf))
	var y := lerpf(ye, B, pow(t, 0.8))
	var rr := sqrt(maxf(0.0, 1.0 - (y / B) * (y / B)))
	var k := 1.006 + thick * pow(t, 0.7)                         # flush at the hairline, fullest over the crown
	return Vector3(A * k * rr * cos(f), y * k, C * k * rr * sin(f))

# an eyelid: a shell round the eyeball from its rim (the equator) up (upper) or down (lower). The rim is a great circle, so when the lid turns about the
# eye's x axis the opening becomes a natural almond. Vertex colours paint the lash line, the lid crease and the pink waterline.
func _lidmesh(r: float, upper: bool, base: Color, shade: Color) -> ArrayMesh:
	var nth := 28; var nla := 16
	var lmax := 1.3 if upper else 1.0
	var tmax := 1.4
	var vs := PackedVector3Array(); var ns := PackedVector3Array(); var cs := PackedColorArray(); var idx := PackedInt32Array()
	for li in nla + 1:
		var lam := lmax * li / nla * (1.0 if upper else -1.0)
		var al := absf(lam)
		for ti in nth + 1:
			var th := -tmax + 2.0 * tmax * ti / nth
			var p := Vector3(cos(lam) * sin(th), sin(lam), cos(lam) * cos(th))
			vs.append(p * r); ns.append(p)
			var c := base
			if upper:
				c = base.lerp(Color("140b07"), 1.0 - smoothstep(0.05, 0.115, al))               # lash line
				c = c.lerp(shade, smoothstep(0.4, 0.46, al) * (1.0 - smoothstep(0.5, 0.58, al)) * 0.8)        # lid crease
			else:
				c = base.lerp(Color("d98d88"), 1.0 - smoothstep(0.03, 0.075, al))              # waterline
			c = c.lerp(shade, smoothstep(1.0, 1.4, absf(th)) * 0.5)                           # darker towards the eye corners
			cs.append(c)
	for li in nla:
		for ti in nth:
			var a := li * (nth + 1) + ti; var b := a + 1; var c2 := a + nth + 1; var d := c2 + 1
			idx.append(a); idx.append(c2); idx.append(b); idx.append(b); idx.append(c2); idx.append(d)
	var arr := []; arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = vs; arr[Mesh.ARRAY_NORMAL] = ns; arr[Mesh.ARRAY_COLOR] = cs; arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new(); am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return am

# a smooth tube through a list of points, radius per point (elliptical: ry scales the radius in the up direction). Replaces the old chains of beads.
func _tube(mi: MeshInstance3D, pts: Array, rad: Array, ry := 1.0, ring := 8) -> void:
	var n := pts.size()
	var vs := PackedVector3Array(); var ns := PackedVector3Array(); var idx := PackedInt32Array()
	for i in n:
		var tg: Vector3 = (pts[mini(i + 1, n - 1)] - pts[maxi(i - 1, 0)]).normalized()
		var u := Vector3(0, 0, 1).cross(tg).normalized()
		if u.length() < 0.01: u = Vector3.UP
		var v := tg.cross(u).normalized()
		for k in ring:
			var a := TAU * k / ring
			var d := u * cos(a) * 0.85 + v * sin(a) * ry
			vs.append(pts[i] + d * float(rad[i])); ns.append((u * cos(a) + v * sin(a) / maxf(ry, 0.01)).normalized())
	for i in n - 1:
		for k in ring:
			var a := i * ring + k; var b := i * ring + (k + 1) % ring
			idx.append(a); idx.append(a + ring); idx.append(b); idx.append(b); idx.append(a + ring); idx.append(b + ring)
	var arr := []; arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = vs; arr[Mesh.ARRAY_NORMAL] = ns; arr[Mesh.ARRAY_INDEX] = idx
	var am: ArrayMesh = mi.mesh
	am.clear_surfaces(); am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)

# skin: faint mottling and grain so the face is not a flat plastic colour. Deliberately low contrast - it only has to
# break the surface up, not read as a pattern.
func _skin_tex() -> ImageTexture:
	var n := 256
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new(); rng.seed = 11
	for y in n:
		for x in n:
			var u := float(x) / n; var v := float(y) / n
			var blotch := 0.5 + 0.5 * sin(u * TAU * 2.0 + sin(v * TAU * 3.0) * 1.4) * sin(v * TAU * 2.0 + sin(u * TAU * 3.0) * 1.1)
			var pore := rng.randf() - 0.5
			# a near-white modulation: the material multiplies this by albedo_color, so the mean must stay ~1.0
			var g := clampf(1.0 + (blotch - 0.5) * 0.07 + pore * 0.03, 0.88, 1.0)
			img.set_pixel(x, y, Color(g, g, g, 1.0))
	return ImageTexture.create_from_image(img)

func _tooth_tex() -> ImageTexture:         # a single tooth: ivory, a warmer gum end at the top, a shaded incisal edge at the bottom
	var w := 12; var h := 24
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		for x in w:
			var vy := float(y) / (h - 1)
			var c := Color("fffdf5")
			c = c.lerp(Color("d8c39a"), smoothstep(0.0, 0.30, 1.0 - vy) * 0.6)          # gum end
			c = c.lerp(Color("e7dac1"), smoothstep(0.78, 1.0, vy) * 0.5)                 # incisal edge
			var sx := absf(float(x) / (w - 1) * 2.0 - 1.0)
			c = c.lerp(Color("cebc99"), smoothstep(0.62, 1.0, sx) * 0.45)               # round the sides
			img.set_pixel(x, y, c)
	return ImageTexture.create_from_image(img)

func _iris_tex() -> ImageTexture:
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var dark := Color("4a2810"); var mid := Color("96592a"); var light := Color("dba24a"); var amber := Color("f2c570"); var limb := Color("2a1508")
	for y in n:
		for x in n:
			var u := (x + 0.5) / n * 2.0 - 1.0; var v := (y + 0.5) / n * 2.0 - 1.0
			var r := sqrt(u * u + v * v); var a := atan2(v, u)
			var fib := 0.5 + 0.5 * sin(a * 31.0 + sin(a * 9.0) * 1.7) * (0.55 + 0.45 * sin(a * 13.0 + r * 5.0))        # radial fibres
			var col := mid.lerp(light, clampf(fib * (1.0 - r) * 1.6, 0.0, 1.0))
			col = col.lerp(dark, smoothstep(0.6, 0.92, r) * 0.45)
			col = col.lerp(amber, (1.0 - smoothstep(0.32, 0.55, r)) * 0.75)         # amber collar round the pupil
			col = col.lerp(limb, smoothstep(0.86, 0.98, r) * 0.8)                         # dark limbal ring
			if r < 0.34: col = Color("0b0604")
			img.set_pixel(x, y, Color(col.r, col.g, col.b, 1.0))
	return ImageTexture.create_from_image(img)

var fc := {}                  # soft tissue: only a fraction of how far a coupling spring is behind its pose
var _fcs := {}                # the coupling springs' lagged values
var _cp := {}                 # exact coupling targets: part of the skeleton's pose, never a driver of it
# Soft tissue gains, per coupling: 0 would be pure bone/tendon, 1 the old full-lag pull. Cheeks (ns/nf) and the chin (ch)
# are the fleshiest and keep the most trail; the eyes and the brow bone keep very little.
const FSOFT := {"bo": 0.14, "bi": 0.14, "lid": 0.18, "sq": 0.25, "ns": 0.35, "nf": 0.3, "ch": 0.3, "mw": 0.16, "sm": 0.16, "hp": 0.1, "tt": 0.25}

# The face has the same two layers as the body. _raw() is the expression the choreography asked for; _pose_v() adds the
# exact couplings, and it is all the structural parts read: jaw, lids, eye bones, brow bones, lip row, head. _fp() adds
# the muscles on top - a small share of the lag of a spring chasing that pose. A muscle can never move a bone off the
# expression, so a blink lands on the frame it was asked for and the flesh catches up afterwards.
func _raw(k: String) -> float: return float(fx.get(k, 0.0)) + float(fo.get(k, 0.0))
func _pose_v(k: String) -> float: return _raw(k) + float(_cp.get(k, 0.0))
func _fp(k: String) -> float: return _pose_v(k) + float(fc.get(k, 0.0))

# Muscles never work alone. A smile pulls the cheeks into the eyes and drops the outer brow, an open jaw lifts the brows and flares the nose,
# a scowl wrinkles the nose, tightens the lips and pushes the chin up, sadness bunches the chin and lifts the inner brows. Those relationships
# are now part of the pose (t below); what lags is only the soft tissue riding on it.
func _couple(dt: float) -> void:
	var sm := float(fx.get("sm", 0.0)); var mo := clampf(_raw("mo"), 0.0, 1.0)
	var bi := float(fx.get("bi", 0.0)); var bo := float(fx.get("bo", 0.0)); var lid := float(fx.get("lid", 0.5))
	var pf := float(fx.get("pf", 0.0)); var pu := float(fx.get("pu", 0.0)); var sq := float(fx.get("sq", 0.0))
	var glare := maxf(pf, maxf(0.0, -bi) * 0.8)
	var up := maxf(0.0, sm); var dn := maxf(0.0, -sm)
	var brow_up := clampf((bi + bo) * 0.5, 0.0, 1.0)
	var t := {
		"bo": -up * 0.14 + mo * 0.12 + dn * 0.05,                 # smile pulls the outer brow down; a shout lifts it
		"bi": mo * 0.1 + dn * 0.3 + glare * -0.1,                 # sadness lifts the inner brow
		"lid": brow_up * 0.28 - glare * 0.1 - dn * 0.06 + mo * 0.06,    # raised brows open the eyes, scowls and sadness narrow them
		"sq": glare * 0.15,
		"ns": glare * 0.35 + dn * 0.05 + sq * 0.1,                # snarl wrinkles the nose
		"nf": mo * 0.4 + glare * 0.2 + pu * -0.1,                 # the nostrils flare when he shouts or snarls
		"ch": glare * 0.4 + dn * 0.55 + pu * 0.3 - mo * 0.2,      # chin pushes up under a scowl, a frown or a pucker
		"mw": -glare * 0.15 + up * 0.12 - pu * 0.1,
		"sm": -glare * 0.12 + mo * 0.04,
		"hp": mo * 0.025 - dn * 0.03 + brow_up * 0.015,           # the head tips back a touch when the jaw drops, forward when sad
		"tt": glare * 0.3 * (1.0 if mo > 0.1 else 0.0),
	}
	var lag := {"bo": 18.0, "bi": 18.0, "lid": 14.0, "sq": 12.0, "ns": 10.0, "nf": 10.0, "ch": 8.0, "mw": 12.0, "sm": 9.0, "hp": 6.0, "tt": 10.0}
	_cp = t
	for k in t:
		var target := float(t[k]); var rate: float = float(lag[k])
		var cur: float = _fcs.get(k, target)
		cur = lerpf(cur, target, 1.0 - exp(-dt * rate))
		_fcs[k] = cur
		fc[k] = (cur - target) * float(FSOFT.get(k, 0.2))       # trailing flesh, never the pose itself

# shapes every face part from the current parameters
func _apply_face() -> void:
	if fr.is_empty() or fx.is_empty(): return
	var blink := _blink_k
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		var ex: float = fr["ex_" + sd]
		# upper lid: its lower edge sits at 0.0084 (closed) .. 0.042 (wide); below half-open it grows taller so it can cover the eye
		var bis := _pose_v("bi") + _pose_v("biL" if s < 0 else "biR")
		var bos := _pose_v("bo") + _pose_v("boL" if s < 0 else "boR")
		var pf := _pose_v("pf")
		var glare := maxf(pf, maxf(0.0, -bis) * 0.8)
		var Ls := "lidL" if s < 0 else "lidR"
		var sq := clampf(_pose_v("sq") + _pose_v("wet") * 0.15 + maxf(0.0, _pose_v("sm")) * 0.2, 0.0, 1.0)
		var lidv := clampf(_pose_v("lid") + _pose_v(Ls) - _pose_v("sq") * 0.04 - glare * 0.05 - maxf(0.0, _pose_v("sm") - 0.3) * 0.04, 0.0, 1.0)
		lidv = maxf(lidv, minf(_pose_v("lid") + _pose_v(Ls), 0.1))
		if lidv >= 0.12: lidv = maxf(lidv, 0.34)        # a half-lidded look still shows most of the iris
		lidv *= (1.0 - blink)
		var tilt := clampf(glare * 0.55 - maxf(0.0, bis) * 0.5 - maxf(0.0, -_pose_v("sm")) * 0.25, -0.6, 0.6)
		var ew := _pose_v("ew")
		var gxv := clampf(_pose_v("gx"), -1.2, 1.2); var gyv := clampf(_pose_v("gy"), -1.2, 1.2)
		# upper lid edge: elevation above the middle of the eye (radians). The lid rides down a little when he looks down.
		var au := lerpf(-0.16, 0.82, pow(lidv, 0.8)) + gyv * 0.15 + ew * 0.14
		var al := -0.45 + sq * 0.42 + _pose_v("wet") * 0.08 + blink * 0.55 - maxf(0.0, gyv) * 0.06
		var ec: Vector3 = fr["ec_" + sd]
		(fr["lid_" + sd] as Node3D).rotation = Vector3(-au, 0, s * tilt)
		(fr["low_" + sd] as Node3D).rotation = Vector3(-al, 0, s * tilt * 0.35)
		var ball: Node3D = fr["white_" + sd]
		ball.rotation = Vector3(-clampf(gyv * 0.4, -0.5, 0.5), clampf(gxv * 0.5, -0.65, 0.65) + s * 0.02, 0)
		ball.scale = Vector3.ONE * (1.0 + ew * 0.05)
		var pd := 1.0 + _fp("pd") * 0.6 + ew * 0.35
		(fr["pupil_" + sd] as Node3D).scale = Vector3(pd, pd, 1.0)
		# catchlights sit on the cornea in front of the iris, only while the eye is open enough to show them
		var ic := Basis.from_euler(ball.rotation) * Vector3(0, 0, EYE_R)
		var rs := EYE_R + 0.0012
		var p1 := (ic + Vector3(0.0055 * s, 0.0062, 0.0)).normalized() * rs
		var p2 := (ic + Vector3(-0.005 * s, -0.005, 0.0)).normalized() * rs
		var sh: Node3D = fr["shine_" + sd]; sh.position = ec + p1
		sh.visible = asin(clampf(p1.y / rs, -1.0, 1.0)) < au - 0.07 and p1.z > 0.0
		var sh2: Node3D = fr["shine2_" + sd]; sh2.position = ec + p2
		sh2.visible = asin(clampf(p2.y / rs, -1.0, 1.0)) > al + 0.06 and p2.z > 0.0 and sh.visible
		var lwy := (EYE_R + 0.0022) * sin(al)
		var lwz := (EYE_R + 0.0022) * cos(al)
		# tears: glistening band on the lower lid, a streak down the cheek and a drop that runs along it
		var wet := _fp("wet"); var te := _fp("te")
		var wn: Node3D = fr["wet_" + sd]
		wn.visible = wet > 0.04
		wn.position = ec + Vector3(0, lwy + 0.0014, lwz - 0.0012); wn.scale = Vector3(1.0, 0.12 + wet * 0.16, 0.5)
		var st: Node3D = fr["streak_" + sd]
		var drop: Node3D = fr["drop_" + sd]
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
		# brows: the ridge bone carries the raise and the tilt - those are the pose. The three pieces keep only their
		# shape, pinch (pf) and scowl overhang: small local offsets riding on the bone, never the thing that moves it.
		var bdrop := maxf(0.0, -bis)
		var bz := s * (-0.16 + 0.5 * (bos - bis) + 0.375 * pf)
		var bry := 0.062 + 0.018 * bis + 0.014 * bos
		var brp := Vector3(0.043 * s, bry, 0.081 + 0.004 * glare)
		var br: Node3D = fr["brow_" + sd]
		br.rotation.z = bz; br.position = brp
		var biw := Vector3(0.028 * s - 0.012 * pf * s - 0.006 * bdrop * s, 0.063 + 0.02 * bis - 0.012 * pf, 0.087 + 0.004 * glare)
		var bo_w := Vector3(0.058 * s - 0.005 * pf * s, 0.059 + 0.016 * bos - 0.006 * pf - 0.006 * bdrop, 0.074 + 0.003 * glare)
		var arch := 0.003 + 0.004 * clampf((bos + bis) * 0.5, -0.5, 1.0) - 0.004 * glare       # the brow arches when raised and flattens when scowling
		var bi_z := PI / 2 + s * clampf(0.1 + 0.6 * (bos - bis) + 0.4 * pf, -0.85, 0.95)
		var bo_z := PI / 2 + s * clampf(-0.42 + 0.5 * (bos - bis) + 0.35 * pf, -0.9, 0.7)
		var bm_w := Vector3(0.043 * s - 0.008 * pf * s, (biw.y + bo_w.y) * 0.5 + arch, 0.081 + 0.004 * glare)
		var bm_z := (bi_z + bo_z) * 0.5
		# map the wanted world transforms back into bone space: the bone supplies the pose, these locals only keep the brow's shape
		var inv := Basis.from_euler(Vector3(0, 0, -bz))
		var bi: MeshInstance3D = fr["bi_" + sd]
		bi.position = inv * (biw - brp); bi.rotation = (inv * Basis.from_euler(Vector3(0, 0, bi_z))).get_euler()
		var bo: MeshInstance3D = fr["bo_" + sd]
		bo.position = inv * (bo_w - brp); bo.rotation = (inv * Basis.from_euler(Vector3(0, 0.45 * s, bo_z))).get_euler()
		var bm: MeshInstance3D = fr["bm_" + sd]
		bm.position = inv * (bm_w - brp); bm.rotation = (inv * Basis.from_euler(Vector3(0, 0.25 * s, bm_z))).get_euler()
	# mouth: half-width w, smile sm lifts corners (frown drops them), pu puckers, sk skews. The jaw bone does the opening
	# (mo), so the lower lip only carries its own shape here and the corner knots ride the jaw with it.
	var sm := _pose_v("sm"); var mo := clampf(_pose_v("mo"), 0.0, 1.0)
	var jb: Node3D = b("jaw")
	jb.rotation = Vector3(JAW_OPEN * mo, 0, 0)
	var w := 0.036 * (1.0 + 0.5 * _pose_v("mw")) * (1.0 - 0.45 * _pose_v("pu"))
	var A := 0.010 + sm * (0.016 if sm > 0.0 else 0.022)
	var sk := _pose_v("sk")
	for i in LIP_N:
		var t := float(i) / (LIP_N - 1) * 2.0 - 1.0
		var t2 := t * t
		var x := t * w
		var skw := sk * 0.008 * t
		var yl := -0.0735 + A * (t2 - 0.5) + skw - maxf(0.0, -sm) * 0.008 * t2
		var yu := -0.0635 + A * 0.5 * (t2 - 0.5) + skw + _pose_v("ns") * 0.004 + _pose_v("ul") * 0.008
		# the lips sit on the face: their depth follows the head surface, so they curve back at the corners instead of
		# hanging in the air, and the jaw's drop keeps the lower lip on the receding chin
		var zl := hz(x, yl) + 0.0022 + _pose_v("pu") * 0.006 * (1.0 - 0.5 * t2)
		var zu := hz(x, yu) + 0.0022
		(fr.lipL[i] as Node3D).position = Vector3(x, yl + _pose_v("pu") * 0.003, zl) - JAW_P
		(fr.lipU[i] as Node3D).position = Vector3(x, yu, zu)
	var cav: Node3D = fr.cav
	# The mouth is the gap between the two lip tubes, and its edges are those tubes' inner edges (the jaw swing drops
	# the lower one). The dark interior, the teeth and the tongue are all sized to that gap, so nothing can spill out
	# around a lip and the lips stay the thing you read the expression from.
	var th := JAW_OPEN * mo
	var zu_c := hz(0.0, -0.0635 - 0.25 * A) + 0.0022
	var zl_c := hz(0.0, -0.0735 - 0.5 * A) + 0.0022
	var rl_c := 0.0034 + 0.0042
	var y_top := (-0.0635 - 0.25 * A) - 0.0062 + _pose_v("ul") * 0.008                                    # upper lip's lower edge
	var y_bot := -0.05 + (-0.0735 - 0.5 * A + 0.05) * cos(th) - (zl_c + 0.045) * sin(th) + rl_c     # lower lip's upper edge, after the jaw swing
	var h_win := maxf(0.004, y_top - y_bot)
	var zt := minf(zu_c, zl_c) + 0.0035
	cav.position = Vector3(0, (y_top + y_bot) * 0.5, minf(zu_c, zl_c))
	cav.scale = Vector3(w * 0.94 / 0.03, h_win * 0.55 / 0.03, 0.10)
	# teeth: two rows of separate teeth laid along the mouth arc, the upper row hanging from the upper lip and the
	# lower row standing on the lower lip. The gaps between them (and the per-tooth texture) are what make them read
	# as teeth instead of one white plate.
	var show := maxf(_pose_v("tt") * 0.9, mo * 1.2)
	var showk := clampf(show, 0.0, 1.0)
	var t_on := show > 0.18
	var spanw := w * 0.70
	var tth := minf(TOOTH_H * (0.88 + 0.12 * showk), h_win * 0.75)      # the upper row fills most of the opening
	var tth_l := minf(TOOTH_H * (0.88 + 0.12 * showk), h_win * 0.5)     # the lower row takes the rest, just behind it
	for k in TOOTH_U:
		var tu: Node3D = fr.tooth_u[k]
		tu.visible = t_on
		if t_on:
			var ft := (float(k) + 0.5) / TOOTH_U * 2.0 - 1.0
			var yu := -0.0635 + A * 0.5 * (ft * ft - 0.5) + sk * 0.008 * ft + _pose_v("ns") * 0.004
			# hang the row off the upper lip's lower edge (its tube radius tapers towards the corners), so a wide open
			# mouth shows the teeth instead of tucking them up behind the lip
			var bt := absf(ft) * 0.7
			var ru := 0.0030 + 0.0020 * (1.0 - bt) + 0.0012 * (1.0 - smoothstep(0.0, 0.35, bt))
			tu.position = Vector3(ft * spanw, yu - ru - tth * 0.5 - 0.0004, zt)
			tu.scale = Vector3(2.0 * spanw / TOOTH_U * 0.88, tth, TOOTH_D)
			tu.rotation.y = ft * 0.10
	var l_on := t_on and mo > 0.45
	for k in TOOTH_L:
		var tl: Node3D = fr.tooth_l[k]
		tl.visible = l_on
		if l_on:
			var ft := (float(k) + 0.5) / TOOTH_L * 2.0 - 1.0
			var yl := -0.0735 + A * (ft * ft - 0.5) + sk * 0.008 * ft - maxf(0.0, -sm) * 0.008 * ft * ft
			var rl := 0.0034 + 0.0042 * (1.0 - ft * ft)
			tl.position = Vector3(ft * spanw, yl + rl + tth_l * 0.5 + 0.0004, zt - 0.001) - JAW_P
			tl.scale = Vector3(2.0 * spanw / TOOTH_L * 0.88, tth_l, TOOTH_D)
			tl.rotation.y = ft * 0.10

	# facial muscles: cheeks lift with a smile or squint, the nose wrinkles and flares, the mustache rides the upper lip, the jaw drops, the tongue shows
	var sq2 := _fp("sq"); var ns := _fp("ns"); var nf := _fp("nf"); var ch := _fp("ch"); var tg := _fp("tg")
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		var ck: Node3D = fr["cheek_" + sd]
		var up := sq2 * 0.5      # the cheek shape now comes from the smile/squint blendshape, not a blob
		ck.position = Vector3(0.046 * s, -0.034 + up * 0.006 - maxf(0.0, -sm) * 0.004, 0.054 + up * 0.004)
		ck.scale = Vector3(1.0 + up * 0.18, 0.9 + up * 0.25, 0.7 + up * 0.15)
		var wg: Node3D = fr["wing_" + sd]
		wg.position = Vector3(0.015 * s * (1.0 + nf * 0.35), -0.022 + ns * 0.005, 0.100)
		wg.scale = Vector3(1.0 + nf * 0.3, 0.9 - ns * 0.15, 0.8)
		var nt: Node3D = fr["nost_" + sd]
		nt.position = Vector3(0.0085 * s * (1.0 + nf * 0.5), -0.029 + ns * 0.005, 0.104)
		nt.scale = Vector3(1.0 + nf * 0.5, 0.7 + nf * 0.6, 0.5)
		var fd: Node3D = fr["fold_" + sd]
		var fy := -0.052 + maxf(0.0, sm) * 0.012 + ns * 0.004 - mo * 0.008
		fd.position = Vector3((w + 0.008) * s, fy, hz((w + 0.008) * s, fy) + 0.0015)
		fd.scale = Vector3(0.5, 1.2 + maxf(0.0, sm) * 1.1 + ns * 0.8, 0.4)
	(fr.tip as Node3D).position = Vector3(0, -0.019 + ns * 0.004 - maxf(0.0, _fp("pu")) * 0.002, 0.107 + nf * 0.002)
	for m in fr.must:
		var nd: Node3D = m[0]; var b: Vector3 = m[1]; var mt: float = m[2]; var ms: float = m[3]
		var dy := maxf(0.0, sm) * 0.004 * mt * mt + ns * 0.004 - maxf(0.0, -sm) * 0.005 * mt * mt - mo * 0.005 * (1.0 - mt) + sk * 0.003 * ms * mt + _pose_v("ul") * 0.005 * (1.0 - mt)
		var dx := _fp("mw") * 0.006 * mt * ms - _fp("pu") * 0.008 * mt * ms
		nd.position = b + Vector3(dx, dy, 0.0)
	_mouth_meshes()
	var jaw: Node3D = fr.jaw
	jaw.position = Vector3(0, -0.06 + ch * 0.004, 0.02) - JAW_P
	var chn: Node3D = fr.chin
	chn.position = Vector3(sk * 0.004, -0.100 + ch * 0.004 + maxf(0.0, -sm) * 0.003 - _fp("pu") * 0.002, 0.036 + ch * 0.005) - JAW_P
	chn.scale = Vector3(1.02 - ch * 0.12 + mo * 0.04, 0.5 + ch * 0.16 + maxf(0.0, -sm) * 0.1 - mo * 0.05, 0.62 + ch * 0.1)
	chn.rotation.z = sk * 0.12
	# deeper muscles: corrugator bunch, cheek puffs, zygomatic lip-corner knots, mentalis dimple, masseter, forehead vein
	var glr := maxf(_fp("pf"), maxf(0.0, -_fp("bi")) * 0.8)
	var bn: Node3D = fr.bunch
	bn.visible = glr > 0.35
	bn.scale = Vector3(0.45 + glr * 0.35, 1.0 + glr * 0.9, 0.35 + glr * 0.2)
	var twa := _fp("tw1"); var twb := _fp("tw2")
	for s: float in [-1.0, 1.0]:
		var sd := "l" if s < 0 else "r"
		var up2 := sq2 * 0.45 + _fp("wet") * 0.3
		var pf2: Node3D = fr["puff_" + sd]
		pf2.position = Vector3(0.042 * s, -0.012 + up2 * 0.011, 0.088 + up2 * 0.002)
		pf2.scale = Vector3(1.2, 0.28 + up2 * 0.32, 0.6)
		var cn: Node3D = fr["corner_" + sd]
		var cy: float = (fr.lipL[LIP_N - 1 if s > 0.0 else 0] as Node3D).position.y
		cn.position = Vector3((w + 0.003) * s, cy + 0.002 + twa * 0.0008 * s, hz((w + 0.003) * s, cy - 0.05) + 0.0015 - JAW_P.z)
		cn.scale = Vector3(1.0 + absf(sm) * 0.5 + _fp("mw") * 0.3, 1.0 + absf(sm) * 0.5, 0.6)
		var ms: Node3D = fr["mass_" + sd]
		var cl := clampf(ch * 0.8 + glr * 0.4 + _fp("tt") * 0.15 - mo * 0.2, 0.0, 1.0)
		ms.position = Vector3(0.076 * s, -0.05 - mo * 0.006, 0.012)
		ms.scale = Vector3(0.32 + cl * 0.2, 1.0 + cl * 0.1, 0.7 + cl * 0.1)
		var vn: Node3D = fr["vein_" + sd]
		var rage := clampf(glr + sq2 * 0.5 + ns * 0.4 - 1.25, 0.0, 1.0) * 2.5
		vn.visible = rage > 0.1; vn.scale = Vector3(1, maxf(0.01, minf(1.4, rage)), 0.5)
	var dm: Node3D = fr.dimple
	var mn := clampf(maxf(0.0, -sm) * 0.6 + _fp("pu") * 0.7 + ch * 0.4 - mo * 0.7, 0.0, 1.0)
	dm.visible = mn > 0.15
	dm.position = Vector3(0, -0.092 + mn * 0.003, 0.066) - JAW_P; dm.scale = Vector3(1.4 + mn * 0.6, 0.8 + mn * 0.5, 0.3)
	# skin details: forehead lines with raised brows, the furrow with a scowl, crow's feet with a big smile or squint
	var rz := (_pose_v("bo") + _pose_v("bi") + _pose_v("boL") + _pose_v("boR") + _pose_v("biL") + _pose_v("biR")) * 0.5
	for i in 3:
		var n3: Node3D = fr.fore[i]; var am := clampf((rz - 0.25 - i * 0.14) * 3.0, 0.0, 1.0)
		n3.visible = am > 0.05; n3.scale = Vector3(1, maxf(am, 0.01) * (1.3 - i * 0.15), 0.5)
	var gl := clampf((maxf(_pose_v("pf"), maxf(0.0, -_pose_v("bi")) * 0.8) - 0.2) * 1.6, 0.0, 1.0)
	for n3 in fr.glab:
		(n3 as Node3D).visible = gl > 0.05; (n3 as Node3D).scale = Vector3(1, maxf(gl, 0.01), 0.5)
	var cr := clampf((maxf(0.0, sm) * 0.6 + sq2 * 0.8 - 0.35) * 1.6, 0.0, 1.0)
	for n3 in fr.crow:
		(n3 as Node3D).visible = cr > 0.05; (n3 as Node3D).scale = Vector3(1, maxf(cr, 0.01), 0.5)
	var tn2: Node3D = fr.tongue
	tn2.visible = tg > 0.08 and mo > 0.12
	tn2.position = Vector3(0, -0.0715, minf(zu_c, zl_c) - 0.001) - JAW_P
	tn2.scale = Vector3(1.2, 0.5 + tg * 0.2, 0.45 + tg * 0.25)
	# The fleshy expressions come from the file's blendshapes (sculpted in Blender), riding on top of the bones. This
	# is the shape-key path: a real smile/squint sculpt instead of bone-rotated blobs.
	var hg := rig_mesh.get(fr.get("head")) as MeshInstance3D
	if hg != null:
		var si := hg.find_blend_shape_by_name("smile")
		if si >= 0: hg.set_blend_shape_value(si, clampf(sm, 0.0, 1.0))
		var qi := hg.find_blend_shape_by_name("squint")
		if qi >= 0: hg.set_blend_shape_value(qi, clampf(sq2, 0.0, 1.0))

# eases the face toward its target; called from pose() (uses real time, so no extra plumbing in main.gd)
func face_update() -> void:
	if fx.is_empty(): return
	var now := Time.get_ticks_msec()
	var dt := clampf((now - _last_ms) / 1000.0, 0.001, 0.1) if _last_ms > 0 else 0.016
	if fixed_dt > 0.0: dt = fixed_dt     # recording: fixed time step
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
	fo["boL"] = sin(_clock * 0.8) * 0.03; fo["boR"] = sin(_clock * 0.8 + 2.1) * 0.03     # the two brows never quite match
	var breath := 0.5 + 0.5 * sin(_clock * 1.7)
	fo["mo"] = breath * 0.018 + talk * (0.1 + 0.3 * absf(sin(_clock * 11.0)) * (0.6 + 0.4 * sin(_clock * 4.3)))
	fo["mw"] = talk * 0.3 * sin(_clock * 6.5); fo["pu"] = talk * 0.2 * maxf(0.0, sin(_clock * 6.5 + 2.0))
	# the upper lip has to move too, or the mouth only flaps its jaw: it lifts on the open vowels and drops back onto the
	# lower lip for the closed ones (which is what makes speech read as speech and not as a hinged jaw)
	fo["ul"] = talk * (0.55 * absf(sin(_clock * 8.5)) - 0.15 + 0.2 * sin(_clock * 3.9))
	fo["bo"] += talk * 0.12 * maxf(0.0, sin(_clock * 5.0)); fo["bi"] += talk * 0.08 * maxf(0.0, sin(_clock * 5.0 + 0.6))   # speech punctuates with the brows
	fo["ch"] = talk * 0.25 * absf(sin(_clock * 11.0 + 0.5))                                                                  # and the chin bobs behind the jaw
	fo["bo"] -= _blink_k * 0.05; fo["bi"] -= _blink_k * 0.04          # brows dip with each blink
	_couple(dt)
	# blinking: gap and length depend on the feeling (fear flutters, tiredness drags)
	if auto_blink:
		_blink_t -= dt
		var half := 0.14 if fam == "fatigue" else 0.08
		if _blink_t < 0.0: _blink_t = BLINK.get(fam, 3.4) * randf_range(0.7, 1.3)
		if _blink_t < 0.0 and _blink_t > -2.0 * half:
			var p := (_blink_t + 2.0 * half) / (2.0 * half)      # 0 at the start of the blink, 1 at the end
			# a real blink is not a symmetric ramp: the lid snaps shut in the first third and lifts back more slowly
			_blink_k = smoothstep(0.0, 0.30, p) if p < 0.30 else 1.0 - smoothstep(0.30, 1.0, p)
		else:
			_blink_k = 0.0
	else: _blink_k = 0.0
	_apply_face()

func _mouth_meshes() -> void:
	if rig_skel != null: return          # the mouth tubes come from the file, skinned to the bead bones
	var up: Array = []; var lo: Array = []; var ru: Array = []; var rl: Array = []
	var mo := clampf(_pose_v("mo"), 0.0, 1.0)
	for i in LIP_N:
		var t := float(i) / (LIP_N - 1) * 2.0 - 1.0
		var u: Vector3 = (fr.lipU[i] as Node3D).position; var l: Vector3 = (fr.lipL[i] as Node3D).position
		var bow := 1.0 - smoothstep(0.0, 0.35, absf(t))               # the upper lip has a centre bow and tapers to the corners
		up.append(u + Vector3(0, 0.0008 * bow, 0.0004 * bow)); lo.append(l - Vector3(0, 0.0005, 0))
		ru.append(0.0030 + 0.0020 * (1.0 - absf(t)) + 0.0012 * bow); rl.append(0.0034 + 0.0042 * (1.0 - t * t))
	_tube(fr.lipUm, up, ru, 0.85); _tube(fr.lipLm, lo, rl, 0.95)
	for side in 2:
		var pts: Array = []; var rr: Array = []
		for m in fr.must:
			if (m[3] < 0.0) == (side == 0):
				var mp: Vector3 = (m[0] as Node3D).position
				if pts.is_empty(): pts.append(Vector3(-mp.x * 0.8, mp.y, mp.z)); rr.append(0.0125)        # carry on past the middle so the two halves join
				pts.append(mp); rr.append(lerpf(0.0130, 0.0050, pow(m[2], 0.85)) * 0.95)
		_tube(fr["mustm_l" if side == 0 else "mustm_r"], pts, rr, 1.0, 10)

func _fp_raw(k: String) -> float: return float(fx.get(k, 0.0))

func _thin_torus() -> TorusMesh:
	var t := TorusMesh.new(); t.inner_radius = 0.985; t.outer_radius = 1.0; t.rings = 48; t.ring_segments = 6; return t

# ---------- pose ----------
# Two layers, and only two.
#
# BONES carry the pose. A move is a "target" (pelvis, spine, chest, neck, head, shoulders, where each foot should be) and
# the bone does exactly that: a hand lands on the beat, a foot lands where it was put, and the pose he holds at the end of
# a move is the target, not something the springs drifted to. The legs are solved with two-bone IK from the pelvis down to
# the foot targets: feet stay planted on the floor, knees and hips bend around them, and steps, taps and hops are just foot
# targets that move.
#
# MUSCLES are the layer on top: flesh that trails the bone it hangs on. _muscle() springs toward the bone's exact value and
# gives back that value plus a fraction of how far the spring is behind, so the flesh only shows while he is moving and the
# bone's pose is never moved by it. That is why the dance no longer needs leads like the old CLAP_LEAD (0.1094 beat) to
# compensate for springs arriving late: the target *is* the pose. Gains are the knob, and they are per bone: 0 means the
# part is all bone and tendon (hands, feet), and anything above it is how much soft tissue shows.
const MUSCLE := {           # bone family -> [stiffness, gain]
	"pelvis": [15.0, 0.12], "spine": [16.0, 0.08], "chest": [17.0, 0.14],
	"neck": [18.0, 0.10], "head": [19.0, 0.16],
	"clav": [20.0, 0.08], "shoulder": [22.0, 0.08], "elbow": [26.0, 0.04], "hand": [30.0, 0.0],
	"ankle": [34.0, 0.0],   # the foot target the legs are solved to: a foot is put down, it does not drift
}
const L1 := 0.36            # thigh length
const L2 := 0.34            # shin length
const FOOT_Y := 0.1         # ankle height of a planted foot
const FOOT_X := 0.125       # half stance width
const BPS := 2.0            # dance tempo: beats per second (120 bpm). The fallback beat grid when no external source drives the dance
const BAR := 4.0            # beats per bar (the menu theme is 4/4): gesture phrases lock to this grid when the music gives no bar feed
const SALSA_BEATS := 16.0   # the salsa phrase: 16 beats (4 bars of 4/4), with the turn at beats 12.15-14.9 of it
const FLEX_BEATS := 8.0     # flex: one full left/right show-off cycle every 8 beats (2 bars)
const POWER_BEATS := 6.0    # power: swell, then the shout, every 6 beats
var snap := false           # tests: no muscle trail at all (the bones' pose, nothing on top)
var _snap := false
var _sm := {}
var _pdt := 0.016
var _pms := 0

func _muscle(key: String, fam: String, exact: Vector3) -> Vector3:
	var pr: Array = MUSCLE.get(fam, [16.0, 0.0])
	if _snap or float(pr[1]) <= 0.0:
		_sm.erase(key)
		return exact
	var w: float = pr[0]
	var st: Array = _sm.get(key, [])
	if st.is_empty():
		_sm[key] = [exact, exact * 0.0]
		return exact
	var x = st[0]; var v = st[1]
	var n := 4; var h := _pdt / n
	for _i in n:
		var a = (exact - x) * (w * w) - v * (2.0 * 0.9 * w)
		v += a * h; x += v * h
	st[0] = x; st[1] = v
	return exact + (x - exact) * float(pr[1])

func _neutral() -> Dictionary:
	return {"pel": Vector3(0, 0.82, 0), "pr": Vector3.ZERO, "sp": Vector3(0.03, 0, 0), "ch": Vector3.ZERO, "nk": Vector3.ZERO, "hd": Vector3.ZERO, "shl": 0.0, "shr": 0.0,
		"fl": Vector3(-FOOT_X, FOOT_Y, 0), "fr": Vector3(FOOT_X, FOOT_Y, 0), "fyl": 0.08, "fyr": 0.08, "fpl": 0.0, "fpr": 0.0, "spin": 0.0}

const MKEYS := ["pel", "pr", "sp", "ch", "nk", "hd", "shl", "shr", "fl", "fr", "fyl", "fyr", "fpl", "fpr", "spin"]
func _mix(a: Dictionary, b: Dictionary, k: float) -> Dictionary:
	var o := {}
	for key in MKEYS: o[key] = lerp(a[key], b[key], k)
	return o

func _move_hula(phase: float, bank: float) -> Dictionary:
	var c := cos(phase); var s := sin(phase)
	var M := _neutral()
	M.pel = Vector3(c * 0.07, 0.79 + 0.02 * sin(phase * 2.0 + 0.5), s * 0.05)      # the hip circle, with the knees kept soft under it
	M.pr = Vector3(0, s * 0.15, -c * 0.11)
	M.sp = Vector3(0.03, -s * 0.08, c * 0.09 + bank * 0.12)
	M.ch = Vector3(0, -s * 0.1, 0)
	M.nk = Vector3(0.05 * sin(phase * 2.0 + 0.8), s * 0.08, -c * 0.06)          # the neck nods with the hips and leans against the sway; the head follows a beat later
	M.hd = Vector3(0.04 * sin(phase * 2.0 + 1.5), s * 0.07, c * 0.05)
	var fl := smoothstep(0.05, 0.85, maxf(0.0, c)); var fr := smoothstep(0.05, 0.85, maxf(0.0, -c))       # the foot opposite the hip's shift unweights: the heel peels, then the foot steps out and touches back down
	M.fl = Vector3(-FOOT_X - 0.035 * fl, FOOT_Y + 0.04 * fl, 0.02 * fl); M.fpl = 0.55 * fl
	M.fr = Vector3(FOOT_X + 0.035 * fr, FOOT_Y + 0.04 * fr, 0.02 * fr); M.fpr = 0.55 * fr
	return M

func _sd(i: int) -> float:       # alternating side per beat
	return 1.0 if posmod(i, 2) == 0 else -1.0

func _al(a: Array, b: Array, m: float) -> Array:
	var o := []
	for i in a.size(): o.append(lerpf(a[i], b[i], m))
	return o

func _ft(d: float, lift := 0.0, out := 0.0, wide := 0.0, fwd := 0.0) -> Vector3:      # a foot target: lift = height, out = sideways, fwd = forward
	return Vector3(d * (FOOT_X + wide + out), FOOT_Y + lift, fwd)

# ---------- gestures: dance moves ----------
# gesture("dance"|"hips"|"clap"|"flex"|"power"|"hula"). The move is blended over the hula (out, then in). auto_dance cycles them like the title screen.
var gest := "hula"          # what we want
var gest_cur := "hula"      # what is on screen
var gest_t := 0.0           # local time of the current move, in seconds: the fallback clock when no external beat drives the dance
var beat := 0.0             # musical beat position, in beats; set externally each frame
var beat_bpm := 120.0       # the external source's tempo (informational: the offline fallback uses BPS)
var beat_bar := 0.0         # beats into the current bar from the music (0.0 at a bar line); fed by the producer
var beat_on := false        # true when an external beat source is driving the dance
var _phrase0 := 0.0         # beat where the current gesture's phrase is anchored (snapped to a bar line when beat_on)
var gk := 0.0               # blend 0..1
var auto_dance := false
const GMOOD := {"hula": "grin", "dance": "joy", "hips": "smug", "clap": "delight", "flex": "proud", "power": "battle_cry"}
var _G := {}
var _cyclic := false
var _cyc_i := 0
var _cyc_t := 0.0
# [move, arm kick, seconds to hold]: each move is held for its whole phrase, so the title screen sees complete choreography
const CYC := [["dance", "", 8.2], ["hips", "", 3.2], ["clap", "", 3.2], ["flex", "", 3.8], ["hula", "cheer", 3.2], ["power", "", 3.0], ["dance", "", 8.2], ["hula", "", 3.2]]
func gesture(n: String) -> void:
	gest = n

# Where the current gesture's phrase is anchored, in beats. Prefers the music's bar feed, so the phrase lands on the
# real bar line even when a bar is not 4 beats (the 6/8 game song has 2-beat bars); else the fallback 4/4 grid. The
# salsa also locks to its own 16-beat hypermeasure, so its turn lands on the music's 4-bar phrase rather than mid-phrase.
func _phrase_origin() -> float:
	var bar := maxf(0.0, beat_bar)                        # the producer may leave the feed at 0: clamp it
	var o := (beat - bar) if (beat_on and bar > 0.0) else floorf(beat / BAR) * BAR
	return o - fmod(o, SALSA_BEATS) if gest_cur == "dance" else o

func _gstep() -> void:
	var now := Time.get_ticks_msec()
	_pdt = fixed_dt if fixed_dt > 0.0 else clampf((now - _pms) / 1000.0, 0.001, 0.05)
	_pms = now
	var dt := _pdt
	if not beat_on: beat += dt * BPS      # no music: synthesize the beat grid at the fallback tempo (BPS == beat_bpm / 60 at the default 120 bpm)
	if auto_dance:
		if not _cyclic:                     # (re)start the cycle from the top whenever auto-dance comes on
			_cyclic = true; _cyc_i = 0; _cyc_t = 0.0; gest = CYC[0][0]
			if CYC[0][1] != "": arm_kick(CYC[0][1], 2.2)
		_cyc_t += dt
		while _cyc_t >= float(CYC[_cyc_i][2]):
			_cyc_t -= float(CYC[_cyc_i][2])
			_cyc_i = (_cyc_i + 1) % CYC.size()
			gest = CYC[_cyc_i][0]
			if CYC[_cyc_i][1] != "": arm_kick(CYC[_cyc_i][1], 2.2)
	elif _cyclic:
		_cyclic = false; gest = "hula"      # back to the plain hula when auto-dance stops
	_life(dt)
	if auto_dance: mood("joy" if (arm_t > 0.0 and arm_n == "cheer") else GMOOD.get(gest, "grin"))      # title screen: face matches the move
	if gest_cur != gest:
		gk -= dt * 5.0
		if gk <= 0.0:
			gk = 0.0; gest_cur = gest; gest_t = 0.0
			# phrase lock: anchor the new phrase to the bar (the salsa to its 16-beat hypermeasure), so its beats land on the
			# music instead of mid-bar. The move clock is beat - _phrase0 (see pose).
			_phrase0 = _phrase_origin()
	elif gest_cur != "hula": gk = minf(1.0, gk + dt * 5.0)
	else: gk = 0.0
	if gest_cur != "hula": gest_t += dt

var _micro_t := 2.5
const MICRO := ["wink", "cheeky", "playful", "big_grin", "laugh", "smirk", "tongue_out", "charming", "flirt", "mischief"]
func _life(dt: float) -> void:
	if auto_dance:                  # title screen: the eyes roam, he shouts on the accents, and little expressions flash across his face
		gaze = Vector2(sin(_clock * 0.9) * 0.7 + sin(_clock * 2.3) * 0.15, 0.2 * sin(_clock * 1.3))
		var bb := beat
		var accent := (int(floorf(bb)) % 4 == 0) and (bb - floorf(bb) < 0.6) and gest_cur != "hula"
		talk = lerpf(talk, 0.85 if accent else 0.0, 1.0 - exp(-dt * 14.0))
	_micro_t -= dt
	if _micro_t < 0.0:
		_micro_t = randf_range(2.2, 5.0)
		if react_t <= 0.0 and (auto_dance or base_expr == "grin"): react(MICRO[randi() % MICRO.size()], randf_range(0.6, 1.1))

func _move(n: String, b: float) -> Dictionary:       # b = the move's local beat position, off the shared beat grid
	var M := _neutral()
	M.arm_l = [0, 0, -2.0, 0, -0.85, 0, 0]; M.arm_r = [0, 0, 2.0, 0, 0.85, 0, 0]
	M.fing_l = 0.25; M.fing_r = 0.25
	var bi := int(floorf(b)); var bf := b - bi
	var up := sin(PI * bf)
	match n:
		"dance":       # salsa. Basic: weight rocks side to side on the beat with hip action (hips and chest counter-rotate), the free foot taps out between beats,
			           # one arm styles high while the other holds low, swapping every two beats. Every 16 beats: a full right turn with both arms up.
			var bp := fmod(b, 16.0)
			var hit := 1.0 - pow(1.0 - bf, 3.0)
			var spk := smoothstep(11.0, 12.0, bp) * (1.0 - smoothstep(15.0, 15.8, bp))
			var prep := smoothstep(10.4, 11.8, bp) * (1.0 - smoothstep(12.0, 12.6, bp))       # wind-up: the chest coils against the turn
			var land := smoothstep(15.1, 15.5, bp) * (1.0 - smoothstep(15.5, 16.0, bp))       # the last beat sinks into the knees
			var te := smoothstep(12.0, 12.3, bp) * (1.0 - smoothstep(15.0, 15.4, bp))         # the feet only leave the floor while the turn is moving
			var wp := lerpf(_sd(bi - 1), _sd(bi), hit) * (1.0 - spk)
			M.spin = smoothstep(12.15, 14.9, bp) * TAU
			var pv := sin((bp - 12.0) * PI * 3.0) * te                                        # three quick pivot steps through the turn
			var nl := 0.05 * maxf(0.0, pv); var nr := 0.05 * maxf(0.0, -pv)
			var pi_ := int(floorf(b / 2.0)); var af := b / 2.0 - pi_
			var ap := lerpf(_sd(pi_ - 1), _sd(pi_), smoothstep(0.65, 1.0, af))       # the styling arm leads the beat: it arrives as the beat lands
			var pump := pow(1.0 - bf, 2.0)
			M.pel = Vector3(wp * 0.07, 0.775 + 0.032 * up - 0.02 * spk - 0.02 * prep - 0.03 * land, 0)
			M.pr = Vector3(0, -wp * 0.14, wp * 0.1)
			M.sp = Vector3(0.05, wp * 0.08, -wp * 0.04)
			M.ch = Vector3(0, wp * 0.26 - 0.18 * prep, wp * 0.03)
			M.nk = Vector3(0.04 * pump, wp * 0.1, -wp * 0.06)
			var hy := -wp * 0.2 + 0.35 * (1.0 - spk) * sin(b * 0.45) - 0.35 * prep
			if spk > 0.001: hy += clampf(wrapf(-M.spin, -PI, PI), -1.15, 1.15) * spk       # spotting: the face holds to the front, then whips round with the body
			M.hd = Vector3(0.07 * pump + 0.05 * up + 0.05 * land, hy, -wp * 0.08)       # chin leads the beat, the head tilts into the shift and scans the room
			M.shr = maxf(0.0, wp) * 0.15; M.shl = maxf(0.0, -wp) * 0.15
			M.fyl = 0.08 + 0.34 * te; M.fyr = M.fyl                                            # the feet turn out onto the balls for the turn
			var fL := maxf(0.0, wp); var fR := maxf(0.0, -wp)
			M.fl = _ft(-1.0, 0.05 * fL * up + nl, 0.12 * fL * up, -0.01 * te, 0.035 * te + 0.03 * fL * up); M.fpl = 0.45 * fL * up + nl * 6.0
			M.fr = _ft(1.0, 0.05 * fR * up + nr, 0.12 * fR * up, -0.01 * te, -0.035 * te + 0.03 * fR * up); M.fpr = 0.45 * fR * up + nr * 6.0
			var mr0 := 0.5 + 0.5 * ap
			for sd in ["l", "r"]:
				var d := -1.0 if sd == "l" else 1.0
				var m := lerpf(mr0 if sd == "r" else 1.0 - mr0, 1.0, spk)
				M["arm_" + sd] = _al([-0.5 + 0.12 * pump, 0, d * 0.5, 0, -d * 0.95, 0.2, 0], [-0.15, 0, d * (2.3 + 0.12 * pump), 0, d * 0.55, 0, d * 0.5 * (1.0 - bf)], m)
			M.fing_l = 0.12 + 0.1 * sin(4.5 * b); M.fing_r = 0.12 + 0.1 * sin(4.5 * b + 1.5)
		"hips":        # sassy: the hip pops out on every two beats (one slow beat) and holds, the free foot touches out, hands on hips
			var bh := b * 0.5; var bj := int(floorf(bh)); var fh := bh - bj       # half the beat rate: the pop lasts a half-note
			var hit := 1.0 - pow(1.0 - fh, 4.0)
			var wp := lerpf(_sd(bj - 1), _sd(bj), hit)
			var tap := sin(PI * minf(1.0, fh * 2.0))
			M.pel = Vector3(wp * 0.06, 0.785 - 0.014 * hit, 0); M.pr = Vector3(0, wp * 0.06, wp * 0.13)       # sink into the pop, then settle
			M.sp = Vector3(0.03, 0, -wp * 0.06); M.ch = Vector3(0, -wp * 0.1, -wp * 0.05); M.hd = Vector3(0, -wp * 0.22, -wp * 0.08)
			M.fl = _ft(-1.0, 0.03 * maxf(0.0, wp) * tap, 0.1 * maxf(0.0, wp) * tap); M.fr = _ft(1.0, 0.03 * maxf(0.0, -wp) * tap, 0.1 * maxf(0.0, -wp) * tap)
			for sd in ["l", "r"]:
				var d := -1.0 if sd == "l" else 1.0
				M["arm_" + sd] = [0.1, 0, d * (0.75 + 0.1 * maxf(0.0, d * wp)), 0, -d * 1.3, 0, 0]
			M.fing_l = 0.3; M.fing_r = 0.3
		"clap":        # front claps on the beat with little hops, head nods along
			var c1 := absf(sin(PI * b)); var hop := 1.0 - c1     # the hands are the pose now, so the contact is the beat with no lead
			M.pel = Vector3(0, 0.765 + 0.035 * hop, 0)
			M.sp = Vector3(0.08 + 0.1 * hop, 0, 0); M.hd = Vector3(0.05 + 0.1 * hop, sin(1.5 * b) * 0.3, 0)
			M.shl = 0.06 + 0.1 * hop; M.shr = M.shl
			M.fl = _ft(-1.0, 0.07 * hop); M.fr = _ft(1.0, 0.07 * hop)
			for sd in ["l", "r"]:
				var d := -1.0 if sd == "l" else 1.0
				M["arm_" + sd] = [-0.9 - 0.2 * hop, 0, d * (0.9 - 0.3 * hop), 0, -d * (1.6 + 0.2 * hop), 0, 0]       # hands open shoulder-width, elbows flared, then snap together in front of the sternum
			M.fing_l = 0.0; M.fing_r = 0.0
		"flex":        # alternates showing each bicep in a wide squat, torso turns into it, head turns to admire: one side per 4 beats
			var u := sin(TAU * b / FLEX_BEATS)
			var mr := smoothstep(0.05, 0.4, u); var ml := smoothstep(0.05, 0.4, -u); var dd := mr - ml
			M.pel = Vector3(0, 0.765, 0); M.pr = Vector3(0, -dd * 0.08, 0)
			M.sp = Vector3(0.0, -dd * 0.1, dd * 0.03); M.ch = Vector3(0, -dd * 0.25, dd * 0.04); M.hd = Vector3(-0.05, dd * 0.5, -dd * 0.1)
			M.shr = mr * 0.25; M.shl = ml * 0.25
			M.fl = _ft(-1.0, 0.0, 0.0, 0.09); M.fr = _ft(1.0, 0.0, 0.0, 0.09); M.fyl = 0.35; M.fyr = 0.35
			for sd in ["l", "r"]:
				var d := -1.0 if sd == "l" else 1.0
				var m := mr if sd == "r" else ml
				M["arm_" + sd] = _al([0.1, 0, d * 0.5, 0, -d * 0.5, 0, 0], [-0.1, 0, d * 1.57, 0, d * 1.75, 0, 0], m)
			M.fing_r = lerpf(0.3, 1.0, mr); M.fing_l = lerpf(0.3, 1.0, ml)
		"power":       # wide squat, chest swells, then fists tight at the chest and shaking: one swell+shout every 6 beats
			var u := fmod(b / POWER_BEATS, 1.0)
			var ex := clampf((u - 0.6) / 0.1, 0.0, 1.0) * (1.0 - clampf((u - 0.9) / 0.1, 0.0, 1.0)); var sw := 0.5 - 0.5 * cos(u * TAU)
			var shk := sin(19.0 * b) * 0.04 * ex
			M.pel = Vector3(0, 0.755 - 0.03 * ex, 0); M.sp = Vector3(-0.1 - 0.05 * sw + shk * 0.4, 0, 0)       # the shout drives him down into the stance
			M.shl = 0.1 + 0.15 * sw + 0.12 * ex; M.shr = M.shl; M.hd = Vector3(-0.15, 0, 0)
			M.fl = _ft(-1.0, 0.0, 0.0, 0.1); M.fr = _ft(1.0, 0.0, 0.0, 0.1); M.fyl = 0.4; M.fyr = 0.4
			for sd in ["l", "r"]:
				var d := -1.0 if sd == "l" else 1.0
				M["arm_" + sd] = [-0.7 + shk, 0, d * (0.85 + 0.1 * ex), 0, d * (1.9 + 0.1 * ex), 0, shk]
			M.fing_l = 1.0; M.fing_r = 1.0
		_:
			pass
	return M

func _spine_set(r: Vector3) -> void:       # the bend is shared between the lumbar and the mid-spine
	(j.spine as Node3D).rotation = r * 0.5
	(j.spine2 as Node3D).rotation = r * 0.5

# two-bone leg IK: hip -> knee -> ankle reaches the foot target (in root space). Knee points forward (turned out by `out`), the foot is kept flat (pitch = toe down).
func _leg_ik(side: String, d: float, tgt: Vector3, out: float, pitch: float) -> void:
	var hip := j["hip_" + side] as Node3D
	var kn := j["knee_" + side] as Node3D
	var ank := j["ankle_" + side] as Node3D
	var hp := hip.global_position
	var v := root.to_global(tgt) - hp
	var dist := clampf(v.length(), 0.2, L1 + L2 - 0.002)
	var vh := v.normalized()
	var ang := acos(clampf((L1 * L1 + dist * dist - L2 * L2) / (2.0 * L1 * dist), -1.0, 1.0))
	var pole := (root.global_basis * Vector3(0, 0, 1)).rotated(vh, -d * out)
	pole = (pole - vh * pole.dot(vh)).normalized()
	var dir := (vh * cos(ang) + pole * sin(ang)).normalized()
	var yv := -dir
	var zv := (pole - dir * pole.dot(dir)).normalized()
	var xv := yv.cross(zv).normalized()
	hip.global_basis = Basis(xv, yv, zv)
	var shin := ((hp + vh * dist) - (hp + dir * L1)).normalized()
	kn.rotation = Vector3(acos(clampf(dir.dot(shin), -1.0, 1.0)), 0, 0)
	ank.global_basis = root.global_basis * Basis(Vector3.UP, d * out) * Basis(Vector3.RIGHT, pitch)

func pose(phase: float, bank := 0.0, wave := 1.0, hurt := 0.0) -> void:
	var c := cos(phase); var s := sin(phase)
	_gstep()
	_snap = snap; snap = false
	var M := _move_hula(phase, bank)
	if gk > 0.001:
		# the move runs on the shared beat grid: with an external beat, the phrase clock is beat - _phrase0 (bar-locked);
		# without one, it is the exact legacy gesture clock (gest_t seconds at BPS), so offline renders are unchanged.
		if beat_on and beat < _phrase0: _phrase0 = _phrase_origin()       # the beat jumped back (a track change): re-anchor so gb stays >= 0
		var gb := (beat - _phrase0) if beat_on else gest_t * BPS
		_G = _move(gest_cur, gb)
		M = _mix(M, _G, gk)
	else: _G = {}
	root.rotation.y = yaw + bank * 0.35 + float(M.spin)
	var pel: Node3D = j.pelvis
	var pp: Vector3 = _muscle("pel", "pelvis", M.pel)
	pel.position = pp
	pel.rotation = _muscle("pr", "pelvis", M.pr)
	_spine_set(_muscle("sp", "spine", M.sp))
	(j.chest as Node3D).rotation = _muscle("ch", "chest", M.ch)
	(j.neck as Node3D).rotation = _muscle("nk", "neck", M.nk)
	var hd: Vector3 = _muscle("hd", "head", M.hd + Vector3(sin(_clock * 0.7) * 0.05, sin(_clock * 0.45) * 0.1, sin(_clock * 0.6) * 0.03) * (1.0 - gk * 0.5))       # idle: the head is never quite still
	var tors: Vector3 = (j.chest as Node3D).rotation + pel.rotation * 0.5
	var stab := Vector3(-tors.x * 0.35, -tors.y * 0.4, -tors.z * 0.45) * (0.6 + 0.4 * gk)       # the head fights to stay level while the torso sways under it
	hd += stab
	(j.chest as Node3D).scale = Vector3.ONE * (1.0 + 0.012 * sin(_clock * 1.7)) + Vector3(0.0, 0.01 * sin(_clock * 1.7), 0.01 * sin(_clock * 1.7))
	(j.neck2 as Node3D).rotation = hd * 0.4
	(j.head as Node3D).rotation = Vector3(0.04 + _pose_v("hp") * 1.0 + hd.x * 0.6, look.x * 0.4 + _pose_v("hy") * 0.6 + hd.y * 0.6, _pose_v("hr") * 0.8 + hd.z * 0.6)
	_secondary(phase, c)
	for side in ["l", "r"]:
		var d := -1.0 if side == "l" else 1.0
		var ft: Vector3 = _muscle("f" + side, "ankle", M["f" + side])
		_leg_ik(side, d, ft, float(M["fy" + side]), float(M["fp" + side]))
		(j["thigh_" + side] as Node3D).rotation = Vector3.ZERO
		(j["shin_" + side] as Node3D).rotation = Vector3.ZERO
		(j["foot_" + side] as Node3D).rotation = Vector3.ZERO
		(j["toe_" + side] as Node3D).rotation = Vector3(-float(M["fp" + side]) * 0.6, 0, 0)
		_shb[side] = float(M["sh" + side])
		_arm(side, d, phase, bank, wave, hurt)
	hoop_node.visible = gk < 0.999
	hoop_node.transparency = gk
	hoop_bone.position = Vector3(pp.x + c * 0.06, pp.y + 0.04, pp.z + s * 0.08)
	hoop_bone.rotation = Vector3(-s * 0.16, 0, c * 0.16)
	hoop_mat.uv1_offset.x = -phase / TAU * 3.0
	face_update()
	_rig_sync()


# upper-arm / forearm twist and the fingers. Fingers ripple in the hula (a wave runs across them); gestures set a curl (0 open .. 1 fist).
func _hand_joints(side: String, d: float, ph: float, wave: float) -> void:
	var tw := wave * (1.0 - gk)
	(j["uarm_" + side] as Node3D).rotation = Vector3(0, d * 0.35 * sin(ph - 0.3) * tw, 0)
	(j["fore_" + side] as Node3D).rotation = Vector3(0, d * 0.7 * sin(ph - 1.0) * tw, 0)
	var curl := 0.25
	if gk > 0.001 and _G.has("fing_" + side): curl = lerpf(curl, _G["fing_" + side], gk)
	if arm_k > 0.001 and arm_n == "cheer": curl = lerpf(curl, 0.0, arm_k)        # cheering: hands wide open
	elif arm_k > 0.001 and arm_n == "flinch": curl = lerpf(curl, 0.7, arm_k)
	for f in 4:
		var rip := (sin(ph * 2.0 - f * 0.55) * 0.5 + 0.5) * (1.0 - curl) * 0.5 * (1.0 - gk * 0.5) if wave > 0.01 else 0.0
		var a := -(curl * 1.45 + rip)       # negative x curls toward the front
		(j["fg%d_%s" % [f, side]] as Node3D).rotation = Vector3(a, 0, (f - 1.5) * 0.12 * (1.0 + (1.0 - curl) * 0.8))
		(j["fh%d_%s" % [f, side]] as Node3D).rotation = Vector3(a * 1.15, 0, 0)
	(j["thumb_" + side] as Node3D).rotation = Vector3(-curl * 0.6, 0, -0.9 * d * (1.0 - curl * 0.4))

# ---------- arms ----------
# Flowing hula arms: a wave travels shoulder -> elbow -> wrist (each joint lags the one before), arms in counter-phase, with fore/aft swing and a little twist.
# arm_kick(name, secs) layers a reaction on top: "flinch" (guard up), "cheer" (arms high, pumping), "limp" (arms drop). secs >= 99 holds it until arm_kick("", 0).
var _shb := {"l": 0.0, "r": 0.0}
var arm_n := ""
var arm_t := 0.0
var arm_k := 0.0
func arm_kick(n: String, secs := 0.6) -> void:
	arm_n = n; arm_t = secs
func arm_clear() -> void:
	arm_t = 0.0

# reaction targets: [shoulder z, shoulder x, shoulder y, elbow z, elbow x, hand z, hand x, sway amount]
const ARM_K := {
	"flinch": [0.75, -0.5, 0.0, 2.3, 0.0, 0.0, 0.0, 0.0],
	"cheer": [2.55, 0.0, 0.0, 0.3, 0.0, 0.2, 0.0, 1.0],
	"limp": [0.28, 0.1, 0.0, 0.12, 0.1, 0.0, 0.1, 0.25],
}
func _arm(side: String, d: float, phase: float, bank: float, wave: float, hurt: float) -> void:
	var ph := phase + (0.0 if side == "l" else PI)
	var a_sw := sin(ph); var a_el := sin(ph - 0.7); var a_hd := sin(ph - 1.4)
	var sz_a := 2.0 + 0.4 * a_sw * wave - bank * 0.25 * d
	var sx := 0.55 * sin(ph - 0.5) * wave + 0.04 * sin(_clock * 1.6 + (0.0 if side == "l" else 1.0))
	var sy := d * 0.45 * cos(ph) * wave
	var ez_a := 0.5 + 0.35 * (0.5 + 0.5 * a_el) * wave + 0.3 * wave
	ez_a = minf(ez_a, (PI - sz_a) - 0.1)       # forearm never leans in past vertical: keeps the hands outside the hat brim
	var sz := d * sz_a
	var ez := d * ez_a
	var ex := 0.25 * hurt + 0.4 * a_el * wave
	var hz := d * 0.8 * a_hd * wave
	var hx := 0.6 * sin(ph - 2.0) * wave
	if gk > 0.001 and _G.has("arm_" + side):       # gesture arms
		var ga: Array = _G["arm_" + side]       # [shoulder x, y, z, elbow x, z, hand x, z]
		sx = lerpf(sx, ga[0], gk); sy = lerpf(sy, ga[1], gk); sz = lerpf(sz, ga[2], gk); ex = lerpf(ex, ga[3], gk); ez = lerpf(ez, ga[4], gk); hx = lerpf(hx, ga[5], gk); hz = lerpf(hz, ga[6], gk)
	_hand_joints(side, d, ph, wave)
	# reaction blend
	var dt := clampf(fixed_dt if fixed_dt > 0.0 else 0.016, 0.001, 0.1)
	if side == "l":                     # advance once per frame
		if arm_t > 0.0: arm_t -= dt if arm_t < 99.0 else 0.0
		var tgt := 1.0 if arm_t > 0.0 and ARM_K.has(arm_n) else 0.0
		arm_k = move_toward(arm_k, tgt, dt * (9.0 if tgt > arm_k else 3.5))
	if arm_k > 0.001 and ARM_K.has(arm_n):
		var k: Array = ARM_K[arm_n]
		var sway: float = k[7]
		var pump := sin(_clock * 11.0 + (0.0 if side == "l" else PI)) * 0.18 if arm_n == "cheer" else sin(_clock * 1.4 + (0.0 if side == "l" else PI)) * 0.06
		var kz: float = d * (k[0] + pump)
		sz = lerpf(sz, kz, arm_k); sx = lerpf(sx, k[1] + sx * sway, arm_k); sy = lerpf(sy, d * k[2] + sy * sway, arm_k)
		ez = lerpf(ez, d * k[3], arm_k); ex = lerpf(ex, k[4] + ex * sway, arm_k)
		hz = lerpf(hz, d * k[5] + hz * sway, arm_k); hx = lerpf(hx, k[6] + hx * sway, arm_k)
	# scapulohumeral rhythm: the collarbone rises with the arm (about a third of the lift past 30 degrees), swings forward when the arm reaches ahead and back when it pulls behind,
	# and the whole girdle breathes. The shoulder joint rides on it, so arm and shoulder blade move as one chain.
	var elev := clampf(absf(sz) - 0.5, 0.0, 2.4)
	var cl := Vector3(clampf(-absf(sx) * 0.0 - sx * 0.0, -1.0, 1.0), -d * clampf(-sx * 0.28 - absf(sy) * 0.08, -0.25, 0.3), d * (_shb[side] * 2.0 + elev * 0.27 + sin(_clock * 1.7) * 0.012))
	cl.x = clampf(-sx * 0.06, -0.08, 0.08)
	(j["clav_" + side] as Node3D).rotation = _muscle("cl" + side, "clav", cl)
	(j["shoulder_" + side] as Node3D).rotation = _muscle("as" + side, "shoulder", Vector3(sx, sy, sz))
	(j["elbow_" + side] as Node3D).rotation = _muscle("ae" + side, "elbow", Vector3(ex, 0, ez))
	(j["hand_" + side] as Node3D).rotation = _muscle("ah" + side, "hand", Vector3(hx, 0, hz))

# ---------- secondary motion: the hat and the hair lag behind the body and get thrown by the arms ----------
var _hs := [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]    # spring positions: hat x, hat z, hair l, hair r, hat lift, (spare)
var _hv := [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
func _secondary(phase: float, c: float) -> void:
	var dt := clampf(fixed_dt if fixed_dt > 0.0 else 0.016, 0.001, 0.05)
	var sway := sin(phase)
	var tx := -0.16 - 0.05 * sin(phase * 2.0 - 0.8)       # nods with the hips
	var tz := c * 0.05 - 0.13 * sway                         # leans against the sway
	var hl := 0.0; var hr := 0.0; var lift := 0.0
	hl = 0.08 * -1.0 + 0.16 * sway + 0.06 * sin(phase * 2.0)
	hr = 0.08 * 1.0 + 0.16 * sway - 0.06 * sin(phase * 2.0)
	var kk := arm_k
	if kk > 0.001:
		match arm_n:
			"flinch": tx += -0.2 * kk; lift += 0.03 * kk; hl += -0.35 * kk; hr += 0.35 * kk          # hat tips back and pops up, hair flares
			"cheer": tx += -0.12 * kk; tz += 0.1 * sin(_clock * 11.0) * kk; lift += 0.015 * kk; hl += -0.2 * kk; hr += 0.2 * kk
			"limp": tx += 0.22 * kk; hl += 0.1 * kk; hr += -0.1 * kk
	var tg := [tx, tz, hl, hr, lift, 0.0]
	var K := [34.0, 34.0, 20.0, 20.0, 60.0, 1.0]
	var Z := [0.45, 0.45, 0.35, 0.35, 0.4, 1.0]
	var sub := 6
	for _s in sub:
		for i in 5:
			var w: float = K[i]
			var a: float = w * w * (tg[i] - _hs[i]) - 2.0 * Z[i] * w * _hv[i]
			_hv[i] += a * dt / sub; _hs[i] += _hv[i] * dt / sub
	(j.hat as Node3D).rotation = Vector3(_hs[0], 0, _hs[1])
	(j.hat as Node3D).position = Vector3(0, 0.07 + _hs[4], -0.012)
	(j.hair_l as Node3D).rotation = Vector3(0, 0, _hs[2])
	(j.hair_r as Node3D).rotation = Vector3(0, 0, _hs[3])

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
