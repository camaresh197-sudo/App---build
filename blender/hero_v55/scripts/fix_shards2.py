import bpy, sys, math, bmesh
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v42.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
jg = body.vertex_groups["jaw"].index
jw = [next((g.weight for g in v.groups if g.group == jg), 0.0) for v in me.vertices]
print("shape keys:", [k.name for k in me.shape_keys.key_blocks], "verts", len(me.vertices), "faces", len(me.polygons))
import numpy as np
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd0 = KDTree(len(T))
for i, t in enumerate(T): kd0.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd0.balance()
DY = -0.0155; DZ = 1.27
iU = gnames.index("upper_lip"); iL = gnames.index("lower_lip")
isU = [False] * len(me.vertices); isL = [False] * len(me.vertices)
for v in me.vertices:
    p = v.co
    if p.z < 1.46 or p.z > 1.56: continue
    _, idx, d = kd0.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d < 0.012: isU[v.index] = VG[iU, idx] > 0.5; isL[v.index] = VG[iL, idx] > 0.5
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
bad = [f for f in bm.faces if any(isU[v.index] for v in f.verts) and any(isL[v.index] for v in f.verts)]
print("seam faces (upper_lip vertex + lower_lip vertex) to delete", len(bad))
cand = {v.index for f in bad for v in f.verts}
bmesh.ops.delete(bm, geom=bad, context='FACES_ONLY')
bm.edges.ensure_lookup_table()
bvs = {v for e in bm.edges if e.is_boundary for v in e.verts if v.index in cand}
up = [v for v in bvs if jw[v.index] < 0.5]; lo = [v for v in bvs if jw[v.index] >= 0.5]
print("seam boundary verts upper", len(up), "lower", len(lo))
def tree(vs):
    t = KDTree(len(vs))
    for i, v in enumerate(vs): t.insert(v.co, i)
    t.balance(); return t
tu, tl = tree(up), tree(lo)
delta = {}; gaps = []; skipped = 0
for v in lo:
    _, i, d = tu.find(v.co); gaps.append(d)
    if d < 0.005: delta[v.index] = (up[i].co - v.co) * 0.5
    else: skipped += 1
for v in up:
    _, i, d = tl.find(v.co)
    if d < 0.005: delta[v.index] = (lo[i].co - v.co) * 0.5
    else: skipped += 1
gaps.sort(); print("seam gap mm: median", round(1000 * gaps[len(gaps)//2], 2), "p90", round(1000 * gaps[int(len(gaps) * 0.9)], 2), "max", round(1000 * gaps[-1], 2), "| snapped", len(delta), "skipped (gap >5mm)", skipped)
mv = [dl.length for dl in delta.values()]; print("max snap move mm", round(1000 * max(mv), 2) if mv else 0)
for vi, dl in delta.items():
    v = bm.verts[vi]
    for layer in bm.verts.layers.shape.values(): v[layer] = v[layer] + dl
    v.co = v.co + dl
bm.to_mesh(me); bm.free(); me.update()
print("faces", len(me.polygons))
# ---- tests
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
sc.render.resolution_x = 520; sc.render.resolution_y = 520
cam = sc.camera
V = {"front": ((0, -0.38, 1.49), (math.radians(90), 0, 0)), "side": ((0.38, -0.08, 1.48), (math.radians(90), 0, math.radians(90)))}
def shots(tag):
    for vn, (loc, rot) in V.items():
        cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = D + "/rig/face5_%s_%s.png" % (tag, vn); bpy.ops.render.render(write_still=True)
reset(); shots("rest")
reset(); rot_bone("jaw", 'X', 12); shots("jaw12")
reset(); rot_bone("jaw", 'X', 25); shots("jaw25")
reset()
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v44.blend"); print("saved v44")
