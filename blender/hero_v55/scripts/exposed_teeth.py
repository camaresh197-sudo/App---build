import bpy, sys, math
import numpy as np
from collections import defaultdict
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
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
for src, hinge in (("body_rigged_v52_pouch.blend", None),):
    bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + src)
    arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
    N = len(me.vertices); R = [v.co.copy() for v in me.vertices]
    interior = [False]*N; teeth = [False]*N
    for v in me.vertices:
        p = v.co
        if p.z < 1.38 or p.z > 1.62: continue
        _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
        if d >= 0.012: continue
        if any(has(n, idx) for n in ("teeth", "gums", "tongue", "upper_teeth_and_gums", "lower_teeth_and_gums")): interior[v.index] = True
        if has("teeth", idx) and abs(p.x) < 0.040: teeth[v.index] = True
    NPOUCH = 702; NP = len(me.polygons); N0 = N - 649
    ringv = set()
    for pi in range(NP - NPOUCH, NP - NPOUCH + 54):
        for v in me.polygons[pi].vertices:
            if v < N0: ringv.add(v)
    ringv = list(ringv)
    def rot_bone(name, axis, deg):
        pb = arm.pose.bones[name]; h = pb.head.copy()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
    tv = [i for i in range(N) if teeth[i]]
    for deg in (0, 12, 25):
        for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
        if deg: rot_bone("jaw", 'X', deg)
        dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]
        tris = []
        for pl in m.polygons:
            vs = list(pl.vertices)
            if any(interior[v] for v in vs if v < N): continue
            tris.append(tuple(vs[:3]))
            if len(vs) == 4: tris.append((vs[0], vs[2], vs[3]))
        bvh = BVHTree.FromPolygons(P, tris)
        cx = sum(P[i].x for i in ringv) / len(ringv); cz = sum(P[i].z for i in ringv) / len(ringv)
        poly = sorted(((P[i].x, P[i].z) for i in ringv), key=lambda q: math.atan2(q[1] - cz, q[0] - cx))
        ext = 0; inop = 0
        for i in tv:
            q = (P[i].x, P[i].z)
            if pip(q, poly): inop += 1; continue
            hit, _n, _i, d = bvh.ray_cast(P[i], Vector((0, -1, 0)), 0.2)
            if hit is None: ext += 1
        oe.to_mesh_clear()
        print(f"{src[12:-6] if 'pouch' not in src else 'v52'} jaw {deg:2d}: teeth in front view {len(tv)} | inside the lip opening {inop} | OUTSIDE the opening with nothing in front: {ext}")
