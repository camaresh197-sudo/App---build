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
for src in ("body_rigged_v47.blend", "body_rigged_v49.blend"):
    bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + src)
    arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
    N = len(me.vertices); R = [v.co.copy() for v in me.vertices]; sock = [False]*N
    for v in me.vertices:
        p = v.co
        if p.z < 1.38 or p.z > 1.62: continue
        _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
        if d < 0.012: sock[v.index] = VG[gnames.index("mouth_sock"), idx] > 0.5
    SE = [(e.vertices[0], e.vertices[1]) for e in me.edges if sock[e.vertices[0]] and sock[e.vertices[1]]]
    for deg in (12, 25):
        for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
        pb = arm.pose.bones["jaw"]; h = pb.head.copy()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, 'X') @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
        ratios = sorted((P[a] - P[b]).length / max(1e-6, (R[a] - R[b]).length) for a, b in SE if (R[a] - R[b]).length > 0.0005)
        print(f"STRETCH {src[-9:-6]} jaw {deg}: sock edges {len(ratios)} | median {ratios[len(ratios)//2]:.2f} p95 {ratios[int(len(ratios)*0.95)]:.2f} p99 {ratios[int(len(ratios)*0.99)]:.2f} max {ratios[-1]:.2f}")
