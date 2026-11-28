import bpy, sys, math
from collections import defaultdict
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v71_remesh.blend")
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
N = len(me.vertices)
R = [v.co.copy() for v in me.vertices]
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def strain(thresh=4.0):
    reset(); rot_bone("jaw", 'X', 25)
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
    n = 0; worst = 0
    for p in me.polygons:
        vs = list(p.vertices); c = sum((R[v] for v in vs), Vector()) / len(vs)
        if abs(c.x) > 0.06 or not (1.43 < c.z < 1.60): continue
        for a in range(len(vs)):
            L0 = (R[vs[a]] - R[vs[(a+1) % len(vs)]]).length
            if L0 > 0.0006:
                r = (P[vs[a]] - P[vs[(a+1) % len(vs)]]).length / L0; worst = max(worst, r)
                if r > thresh: n += 1; break
    return n, worst
print("START faces >4x:", strain())
# corner vertices: x beyond 18 mm near the lip line, moved back toward their rest position on the head
nb = defaultdict(set)
for e in me.edges: nb[e.vertices[0]].add(e.vertices[1]); nb[e.vertices[1]].add(e.vertices[0])
corner = [i for i in range(N) if abs(R[i].x) > 0.018 and 1.49 < R[i].z < 1.51 and abs(R[i].y) < 0.150]
print("corner verts", len(corner))
for it in range(30):
    new = {}
    for i in corner:
        ns = nb[i]
        new[i] = R[i].lerp(sum((me.vertices[k].co for k in ns), Vector()) / len(ns), 0.4)
    for i, p in new.items(): me.vertices[i].co = p
    me.update()
    R_now = [v.co.copy() for v in me.vertices]
print("AFTER relax faces >4x:", strain())
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v74_relax.blend")
