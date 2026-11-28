import bpy, sys, math
import numpy as np
from collections import Counter
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v55_lips_smooth.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
NP = len(me.polygons); N = len(me.vertices); N0 = N - 649
ring = set(me.polygons[NP - 702 + i].vertices[0] for i in range(54))
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
R = [v.co.copy() for v in me.vertices]; cat = [""] * N
for i in range(N0):
    p = R[i]
    if p.z < 1.40 or p.z > 1.60: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012: continue
    for n in ("upper_lip", "lower_lip", "mouth_sock", "teeth", "gums", "tongue"):
        if has(n, idx): cat[i] = n; break
    else: cat[i] = "skin"
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def move(name, d):
    pb = arm.pose.bones[name]; pb.matrix = Matrix.Translation(d) @ pb.matrix; bpy.context.view_layer.update()
reset(); rot_bone("jaw", 'X', 12)
for k in range(17):
    prof = math.sin(math.pi * k / 16) ** 0.8
    move("lipU_%d" % k, Vector((0, 0, 0.008 * prof))); move("lipL_%d" % k, Vector((0, 0, -0.003 * prof)))
move("corner_r", Vector((0.008, 0, 0.005))); move("corner_l", Vector((-0.008, 0, 0.005)))
for k, s in ((0, 1), (16, -1)):
    move("lipU_%d" % k, Vector((s * 0.0064, 0, 0.004))); move("lipL_%d" % k, Vector((s * 0.0064, 0, 0.004)))
dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
bad = []
for e in me.edges:
    a, b = e.vertices
    if a >= N0 or b >= N0: continue
    if cat[a] in ("teeth", "gums", "tongue") or cat[b] in ("teeth", "gums", "tongue"): continue
    if abs(R[a].x) > 0.050 or not (1.44 < R[a].z < 1.58): continue
    L0 = (R[a] - R[b]).length
    if L0 < 0.0008: continue
    r = (P[a] - P[b]).length / L0
    if r > 3.0 or r < 0.3: bad.append((r, a, b, L0))
print("edges with strain >3x or <0.3x:", len(bad))
c = Counter(tuple(sorted((cat[a], cat[b]))) for _, a, b, _ in bad)
for k, n in c.most_common(8): print("PAIR", n, k)
bad.sort(key=lambda t: -t[0])
for r, a, b, L0 in bad[:8]:
    mid = (R[a] + R[b]) / 2
    print(f"  ratio {r:5.1f} rest len {1000*L0:4.1f} mm at x {1000*mid.x:6.1f} z {1000*mid.z:7.1f} y {1000*mid.y:7.1f} | {cat[a]}-{cat[b]} | ring ends: {a in ring}/{b in ring}")
xs = [abs((R[a].x + R[b].x) / 2) for _, a, b, _ in bad]
print("bad edges by |x| mm: <10:", sum(1 for x in xs if x < 0.010), " 10-20:", sum(1 for x in xs if 0.010 <= x < 0.020), " 20-30:", sum(1 for x in xs if 0.020 <= x < 0.030), " >30:", sum(1 for x in xs if x >= 0.030))
