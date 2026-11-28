import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v39.blend")
sc = bpy.context.scene
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
def center(o):
    pts = [o.matrix_world @ v.co for v in o.data.vertices]; return sum(pts, Vector()) / len(pts)
eyeobjs = {n: bpy.data.objects[n] for n in bpy.data.objects.keys() if n.startswith(("eyeball_", "iris_", "pupil_"))}
cL = center(eyeobjs["eyeball_right"]); cR = center(eyeobjs["eyeball_left"])   # GNM left = +x; this rig: _r = +x
print("eye centres (+x, -x):", [round(c, 4) for c in cR], [round(c, 4) for c in cL])
# ---- bones
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones
j = eb.new("jaw"); j.head = Vector((0, -0.012, 1.535)); j.tail = Vector((0, -0.095, 1.430)); j.parent = eb["head"]
for nm, c in (("eye_r", cR), ("eye_l", cL)):
    e = eb.new(nm); e.head = c; e.tail = c + Vector((0, -0.03, 0)); e.parent = eb["head"]
bpy.ops.object.mode_set(mode='OBJECT')
# ---- jaw weights: move a share of the HEAD weight on the lower front face to the jaw bone
gi = {g.name: g.index for g in body.vertex_groups}
jg = body.vertex_groups.new(name="jaw"); gi["jaw"] = jg.index
moved = 0; jsum = 0.0
for v in me.vertices:
    p = body.matrix_world @ v.co
    if p.z > 1.52 or p.z < 1.36: continue
    jm = ss(1.515, 1.490, p.z) * (1 - ss(0.055, 0.095, abs(p.x))) * ss(-0.005, -0.045, p.y)
    if jm <= 0.01: continue
    hw = next((g.weight for g in v.groups if g.group == gi["head"]), 0.0)
    if hw <= 0: continue
    take = hw * jm
    body.vertex_groups["head"].add([v.index], hw - take, 'REPLACE'); jg.add([v.index], take, 'REPLACE')
    moved += 1; jsum += take
print("jaw-weighted verts", moved, "mean jaw weight", round(jsum / max(1, moved), 3))
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)), "bones", len(arm.data.bones))
# ---- eyes follow the eye bones (keep world transforms)
bpy.context.view_layer.update()
for n, o in eyeobjs.items():
    w = o.matrix_world.copy(); bn = "eye_r" if o.matrix_world.translation.x >= 0 or center(o).x >= 0 else "eye_l"
    bn = "eye_r" if center(o).x >= 0 else "eye_l"
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = bn
    o.matrix_parent_inverse = (arm.matrix_world @ arm.pose.bones[bn].matrix).inverted(); o.matrix_world = w
bpy.context.view_layer.update()
# ---- test poses
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1)
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x = 520; sc.render.resolution_y = 520
V = {"front": ((0, -0.75, 1.53), (math.radians(90), 0, 0)), "side": ((0.75, -0.03, 1.50), (math.radians(90), 0, math.radians(90)))}
def shots(tag):
    for vn, (loc, rot) in V.items():
        cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = D + "/rig/face_%s_%s.png" % (tag, vn); bpy.ops.render.render(write_still=True)
reset(); shots("rest")
reset(); rot_bone("jaw", 'X', 12); shots("jaw12")
reset(); rot_bone("jaw", 'X', 25); shots("jaw25")
reset(); rot_bone("eye_r", 'Z', 25); rot_bone("eye_l", 'Z', 25); rot_bone("eye_r", 'X', -12); rot_bone("eye_l", 'X', -12); shots("eyes")
reset()
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v40.blend"); print("saved v40")
