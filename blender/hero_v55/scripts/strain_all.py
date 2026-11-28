import bpy, sys, math, json
from collections import Counter
from mathutils import Vector, Matrix
D = sys.argv[-1]; FN = sys.argv[sys.argv.index("--") - 1]
meta = json.load(open(D + "/rig/pipeline60_meta.json")); M = meta["M"]; NPOUCH = meta["NPOUCH"]; NNEW = meta["NNEW"]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + FN)
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
NP = len(me.polygons); N = len(me.vertices); N0 = N - NNEW
ring = [me.polygons[NP - NPOUCH + i].vertices[0] for i in range(M)]; ringset = set(ring)
# pouch ring index of each new vertex: ring k = (v-N0)//M (+1)
R = [v.co.copy() for v in me.vertices]
def where(i):
    if i >= N0: return "pouch r%d" % ((i - N0) // M + 1) if (i - N0) < M * 12 else "pouch cap"
    return "RING" if i in ringset else "skin"
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
reset(); rot_bone("jaw", 'X', 25)
dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
bad = []
for e in me.edges:
    a, b = e.vertices
    if abs(R[a].x) > 0.06 or not (1.43 < R[a].z < 1.60): continue
    L0 = (R[a] - R[b]).length
    if L0 < 0.0006: continue
    r = (P[a] - P[b]).length / L0
    if r > 4.0: bad.append((r, a, b, L0))
print("edges stretched >4x at jaw 25:", len(bad))
c = Counter(tuple(sorted((where(a).split()[0] + (" " + where(a).split()[1] if "pouch" in where(a) else ""), where(b).split()[0] + (" " + where(b).split()[1] if "pouch" in where(b) else "")))) for _, a, b, _ in bad)
for k, n in c.most_common(10): print("PAIR", n, k)
bad.sort(key=lambda t: -t[0])
for r, a, b, L0 in bad[:8]:
    mid = (R[a] + R[b]) / 2
    print(f"  ratio {r:5.1f} rest {1000*L0:4.1f} mm at x {1000*mid.x:6.1f} z {1000*mid.z:7.1f} y {1000*mid.y:7.1f} | {where(a)} - {where(b)}")
