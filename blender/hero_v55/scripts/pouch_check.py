import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v52_pouch.blend")
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
NPOUCH = 702; NP = len(me.polygons); first = NP - NPOUCH
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
N0 = len(me.vertices) - 649
up = []; lo = []
for i in range(N0):
    p = me.vertices[i].co
    if p.z < 1.38 or p.z > 1.62 or abs(p.x) > 0.032: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012 or not has("teeth", idx): continue
    (up if has("upper_teeth_and_gums", idx) else lo).append(i)
print("front teeth verts (|x|<32mm): upper", len(up), "lower", len(lo))
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
for deg in (0, 12, 25):
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    if deg: rot_bone("jaw", 'X', deg)
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]
    tris = []
    for pi in range(first, NP):
        vs = list(m.polygons[pi].vertices); tris.append(tuple(vs[:3]))
        if len(vs) == 4: tris.append((vs[0], vs[2], vs[3]))
    bvh = BVHTree.FromPolygons(P, tris)
    def outside(sel):
        n = 0
        for i in sel:
            hit, _n, _i, d = bvh.ray_cast(P[i], Vector((0, -1, 0)), 0.2)
            if hit is None: n += 1
        return n
    # also the pouch's own clearance behind the skin: any pouch vertex in front of skin?
    oe.to_mesh_clear()
    print(f"JAW {deg:2d}: front teeth with NO lining in front of them: upper {outside(up)}/{len(up)}  lower {outside(lo)}/{len(lo)}")
