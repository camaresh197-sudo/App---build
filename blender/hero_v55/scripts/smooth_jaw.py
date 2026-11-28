import bpy, sys, math
import numpy as np
from collections import defaultdict
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v44.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
gi = {g.name: g.index for g in body.vertex_groups}; H, J = gi["head"], gi["jaw"]
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
N = len(me.vertices)
wh = [0.0] * N; wj = [0.0] * N
for v in me.vertices:
    for g in v.groups:
        if g.group == H: wh[v.index] = g.weight
        elif g.group == J: wj[v.index] = g.weight
tot = [wh[i] + wj[i] for i in range(N)]
j = [(wj[i] / tot[i]) if tot[i] > 1e-6 else 0.0 for i in range(N)]
fixed = [None] * N; region = [False] * N
for v in me.vertices:
    p = v.co
    if 1.40 <= p.z <= 1.57 and abs(p.x) < 0.12 and tot[v.index] > 1e-6: region[v.index] = True
    if not (1.38 <= p.z <= 1.60): continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012: continue
    if has("upper_lip", idx) or has("upper_teeth_and_gums", idx): fixed[v.index] = 0.0
    elif has("lower_lip", idx) or has("lower_teeth_and_gums", idx) or has("tongue", idx): fixed[v.index] = 1.0
nb = defaultdict(set)
for e in me.edges: nb[e.vertices[0]].add(e.vertices[1]); nb[e.vertices[1]].add(e.vertices[0])
def jumps(jj):
    n = 0
    for e in me.edges:
        a, b = e.vertices
        if region[a] and region[b] and 1.46 < (me.vertices[a].co.z + me.vertices[b].co.z) / 2 < 1.56 and abs(jj[a] - jj[b]) > 0.5: n += 1
    return n
print("region verts", sum(region), "fixed lip/teeth/tongue", sum(1 for f in fixed if f is not None))
print("edges with jaw-share jump >0.5 BEFORE:", jumps(j))
free = [i for i in range(N) if region[i] and fixed[i] is None]
for it in range(40):
    new = j[:]
    for i in free:
        ns = [k for k in nb[i] if region[k] or True]
        if ns: new[i] = 0.5 * j[i] + 0.5 * (sum(j[k] for k in ns) / len(ns))
    j = new
print("edges with jaw-share jump >0.5 AFTER :", jumps(j))
for i in range(N):
    if region[i] and tot[i] > 1e-6:
        body.vertex_groups[H].add([i], tot[i] * (1 - j[i]), 'REPLACE'); body.vertex_groups[J].add([i], tot[i] * j[i], 'REPLACE')
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
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
V = {"front": ((0, -0.38, 1.49), (math.radians(90), 0, 0)), "side": ((0.38, -0.08, 1.48), (math.radians(90), 0, math.radians(90))), "close": ((0.02, -0.22, 1.49), (math.radians(90), 0, 0))}
def shots(tag):
    for vn, (loc, rot) in V.items():
        cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = D + "/rig/face6_%s_%s.png" % (tag, vn); bpy.ops.render.render(write_still=True)
reset(); shots("rest")
reset(); rot_bone("jaw", 'X', 12); shots("jaw12")
reset(); rot_bone("jaw", 'X', 25); shots("jaw25")
reset()
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v45.blend"); print("saved v45")
