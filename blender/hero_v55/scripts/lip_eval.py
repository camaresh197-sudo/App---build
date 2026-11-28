import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
def pip(pt, poly):
    x, z = pt; inside = False; n = len(poly)
    for i in range(n):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1 + 1e-12) + x1: inside = not inside
    return inside
FILES = [("v53", "body_rigged_v53_lips.blend", False), ("v54", "body_rigged_v54_lower.blend", True), ("v55", "body_rigged_v55_lips_smooth.blend", True)]
for tag, fn, has_lower in FILES:
    bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + fn)
    sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
    NP = len(me.polygons); N = len(me.vertices); N0 = N - 649
    ring = [me.polygons[NP - 702 + i].vertices[0] for i in range(54)]
    upT = []; loT = []; interior = [False] * N
    for i in range(N0):
        p = me.vertices[i].co
        if p.z < 1.38 or p.z > 1.62: continue
        _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
        if d >= 0.012: continue
        if any(has(n, idx) for n in ("teeth", "gums", "tongue", "upper_teeth_and_gums", "lower_teeth_and_gums")): interior[i] = True
        if has("teeth", idx): (upT if has("upper_teeth_and_gums", idx) else loT).append(i)
    R = [v.co.copy() for v in me.vertices]
    sedges = [(e.vertices[0], e.vertices[1]) for e in me.edges if e.vertices[0] < N0 and e.vertices[1] < N0 and not interior[e.vertices[0]] and not interior[e.vertices[1]]
              and abs(R[e.vertices[0]].x) < 0.045 and 1.45 < R[e.vertices[0]].z < 1.56 and (R[e.vertices[0]] - R[e.vertices[1]]).length > 0.0008]
    def reset():
        for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
        bpy.context.view_layer.update()
    def rot_bone(name, axis, deg):
        pb = arm.pose.bones[name]; h = pb.head.copy()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
    def move(name, d):
        pb = arm.pose.bones[name]; pb.matrix = Matrix.Translation(d) @ pb.matrix; bpy.context.view_layer.update()
    def lips(lu, out, up, ll):
        for k in range(17):
            prof = math.sin(math.pi * k / 16) ** 0.8
            move("lipU_%d" % k, Vector((0, 0, lu * prof)))
            if has_lower: move("lipL_%d" % k, Vector((0, 0, ll * prof)))
        move("corner_r", Vector((out, 0, up))); move("corner_l", Vector((-out, 0, up)))
        for k, s in ((0, 1), (16, -1)):
            move("lipU_%d" % k, Vector((s * out * 0.8, 0, up * 0.8)))
            if has_lower: move("lipL_%d" % k, Vector((s * out * 0.8, 0, up * 0.8)))
    poses = [("snarl", lambda: (rot_bone("jaw", 'X', 12), lips(0.008, 0.008, 0.005, -0.003))),
             ("cover", lambda: (rot_bone("jaw", 'X', 12), lips(0.0, 0.0, 0.0, 0.006)))]
    for pn, f in poses:
        reset(); f()
        dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
        rx = [P[i].x for i in ring]; rz = [P[i].z for i in ring]; cx = sum(rx) / 54; cz = sum(rz) / 54
        poly = sorted(((P[i].x, P[i].z) for i in ring), key=lambda q: math.atan2(q[1] - cz, q[0] - cx))
        ut = sum(1 for i in upT if pip((P[i].x, P[i].z), poly)); lt = sum(1 for i in loT if pip((P[i].x, P[i].z), poly))
        ratios = sorted((P[a] - P[b]).length / (R[a] - R[b]).length for a, b in sedges)
        n = len(ratios)
        print(f"{tag} {pn:6s}: opening {1000*(max(rx)-min(rx)):5.1f} x {1000*(max(rz)-min(rz)):5.1f} mm | teeth shown up {ut:4d} low {lt:4d} | skin edge ratio p1 {ratios[n//100]:.2f} p99 {ratios[-n//100]:.2f} min {ratios[0]:.2f} max {ratios[-1]:.2f}")
