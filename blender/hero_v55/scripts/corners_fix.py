import bpy, sys, math, bmesh
import numpy as np
from collections import defaultdict, Counter
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
def components(me):
    parent = list(range(len(me.vertices)))
    def f(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for p in me.polygons:
        vs = p.vertices
        for a in vs[1:]: parent[f(a)] = f(vs[0])
    comp = defaultdict(list)
    for p in me.polygons: comp[f(p.vertices[0])].append(p.index)
    return comp
# ---- A) diagnose v45 (the version you saw)
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v45.blend")
me = bpy.data.objects["body_gnm"].data
comp = components(me)
small = sorted((len(f), k) for k, f in comp.items() if len(f) < 3000)
print("v45 islands total", len(comp), "| small islands (faces):", [n for n, _ in small][:14])
# ---- B) rebuild from v42 with corners kept connected
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v42.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
gi = {g.name: g.index for g in body.vertex_groups}; H, J = gi["head"], gi["jaw"]
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
N = len(me.vertices)
isU = [False]*N; isL = [False]*N; isTU = [False]*N; isTL = [False]*N
for v in me.vertices:
    p = v.co
    if p.z < 1.38 or p.z > 1.60: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012: continue
    isU[v.index] = has("upper_lip", idx); isL[v.index] = has("lower_lip", idx)
    isTU[v.index] = has("upper_teeth_and_gums", idx); isTL[v.index] = has("lower_teeth_and_gums", idx) or has("tongue", idx)
lipx = max(abs(me.vertices[i].co.x) for i in range(N) if isU[i] or isL[i])
CX = 0.78 * lipx
print("lip half-width mm", round(1000 * lipx, 1), "| seam cut only where |x| <", round(1000 * CX, 1), "mm; corners stay joined")
jw = [next((g.weight for g in me.vertices[i].groups if g.group == J), 0.0) for i in range(N)]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
bad = [f for f in bm.faces if any(isU[v.index] for v in f.verts) and any(isL[v.index] for v in f.verts) and abs(f.calc_center_median().x) < CX]
kept = sum(1 for f in bm.faces if any(isU[v.index] for v in f.verts) and any(isL[v.index] for v in f.verts)) - len(bad)
print("seam faces cut", len(bad), "| corner seam faces kept", kept)
cand = {v.index for f in bad for v in f.verts}
bmesh.ops.delete(bm, geom=bad, context='FACES_ONLY'); bm.edges.ensure_lookup_table()
bvs = {v for e in bm.edges if e.is_boundary for v in e.verts if v.index in cand}
up = [v for v in bvs if jw[v.index] < 0.5]; lo = [v for v in bvs if jw[v.index] >= 0.5]
def tree(vs):
    t = KDTree(len(vs))
    for i, v in enumerate(vs): t.insert(v.co, i)
    t.balance(); return t
tu, tl = tree(up), tree(lo); delta = {}; far = 0
for v in lo:
    _, i, d = tu.find(v.co)
    if d < 0.006: delta[v.index] = (up[i].co - v.co) * 0.5
    else: far += 1
for v in up:
    _, i, d = tl.find(v.co)
    if d < 0.006: delta[v.index] = (lo[i].co - v.co) * 0.5
    else: far += 1
for vi, dl in delta.items():
    v = bm.verts[vi]
    for layer in bm.verts.layers.shape.values(): v[layer] = v[layer] + dl
    v.co = v.co + dl
print("snapped", len(delta), "far (>6mm, left)", far, "| max move mm", round(1000 * max(d.length for d in delta.values()), 2))
bm.to_mesh(me); bm.free(); me.update()
# ---- weights: smooth jaw share; lip body + teeth + tongue fixed; corner lip verts free (-> ~half)
wh = [0.0]*N; wj = [0.0]*N
for v in me.vertices:
    for g in v.groups:
        if g.group == H: wh[v.index] = g.weight
        elif g.group == J: wj[v.index] = g.weight
tot = [wh[i] + wj[i] for i in range(N)]; j = [(wj[i] / tot[i]) if tot[i] > 1e-6 else 0.0 for i in range(N)]
fixed = [None]*N; region = [False]*N
for i, v in enumerate(me.vertices):
    p = v.co
    if 1.40 <= p.z <= 1.57 and abs(p.x) < 0.12 and tot[i] > 1e-6: region[i] = True
    corner = (isU[i] or isL[i]) and abs(p.x) >= CX
    if corner: continue
    if isU[i] or isTU[i]: fixed[i] = 0.0
    elif isL[i] or isTL[i]: fixed[i] = 1.0
nb = defaultdict(set)
for e in me.edges: nb[e.vertices[0]].add(e.vertices[1]); nb[e.vertices[1]].add(e.vertices[0])
free = [i for i in range(N) if region[i] and fixed[i] is None]
for it in range(40):
    new = j[:]
    for i in free:
        ns = nb[i]
        if ns: new[i] = 0.5 * j[i] + 0.5 * (sum(j[k] for k in ns) / len(ns))
    j = new
for i in range(N):
    if region[i] and tot[i] > 1e-6:
        body.vertex_groups[H].add([i], tot[i] * (1 - j[i]), 'REPLACE'); body.vertex_groups[J].add([i], tot[i] * j[i], 'REPLACE')
cw = [j[i] for i in range(N) if (isU[i] or isL[i]) and abs(me.vertices[i].co.x) >= CX]
print("corner lip verts", len(cw), "jaw share min", round(min(cw), 2), "mean", round(sum(cw)/len(cw), 2), "max", round(max(cw), 2))
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
comp = components(me); small = sorted(len(f) for f in comp.values() if len(f) < 3000)
print("v46 islands total", len(comp), "| small islands (faces):", small[:14])
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
V = {"front": ((0, -0.38, 1.49), (math.radians(90), 0, 0)), "close": ((0.0, -0.22, 1.50), (math.radians(90), 0, 0)), "side": ((0.38, -0.08, 1.48), (math.radians(90), 0, math.radians(90)))}
def shots(tag):
    for vn, (loc, rot) in V.items():
        cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = D + "/rig/face7_%s_%s.png" % (tag, vn); bpy.ops.render.render(write_still=True)
reset(); shots("rest"); reset(); rot_bone("jaw", 'X', 12); shots("jaw12"); reset(); rot_bone("jaw", 'X', 25); shots("jaw25"); reset()
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v46.blend"); print("saved v46")
