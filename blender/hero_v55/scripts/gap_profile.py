import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v48_nosock.blend")
body = bpy.data.objects["body_gnm"]; me = body.data
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
N = len(me.vertices); R = [v.co.copy() for v in me.vertices]; interior = [False]*N; teeth = [False]*N
for v in me.vertices:
    p = v.co
    if p.z < 1.38 or p.z > 1.62: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d < 0.012 and any(has(n, idx) for n in ("teeth", "gums", "tongue", "upper_teeth_and_gums", "lower_teeth_and_gums")): interior[v.index] = True
    if d < 0.012 and has("teeth", idx): teeth[v.index] = True
tris = []
for p in me.polygons:
    if any(interior[v] for v in p.vertices): continue
    vs = list(p.vertices); tris.append(tuple(vs[:3]))
    if len(vs) == 4: tris.append((vs[0], vs[2], vs[3]))
bvh = BVHTree.FromPolygons(R, tris)
tv = [R[i] for i in range(N) if teeth[i]]
print("z(mm)   skin front y at x=0 / x=15 / x=-15   |  teeth front y (|x|<8 / |x| 12-18)   | gap at x=0")
for zmm in range(1460, 1556, 5):
    z = zmm / 1000.0; out = []
    for x in (0.0, 0.015, -0.015):
        hit, n, i, d = bvh.ray_cast(Vector((x, -0.03, z)), Vector((0, -1, 0)), 0.2)
        out.append(hit.y if hit else None)
    def tf(lo, hi):
        ys = [p.y for p in tv if lo <= abs(p.x) <= hi and abs(p.z - z) < 0.0025]; return min(ys) if ys else None
    t0 = tf(0, 0.008); t1 = tf(0.012, 0.018)
    f = lambda a: "  --  " if a is None else f"{1000*a:7.1f}"
    gap = "" if out[0] is None or t0 is None else f"{1000*(t0 - out[0]):6.1f}"
    print(f"{zmm}  {f(out[0])} {f(out[1])} {f(out[2])}   | {f(t0)} {f(t1)}   | {gap}")
