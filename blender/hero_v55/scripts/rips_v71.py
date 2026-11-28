import bpy, sys, math
from collections import Counter
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v71_remesh.blend")
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
N = len(me.vertices); NNEW = 649 + 0
R = [v.co.copy() for v in me.vertices]
emap = {}
for p in me.polygons:
    vs = list(p.vertices)
    for a in range(len(vs)):
        emap.setdefault(tuple(sorted((vs[a], vs[(a+1) % len(vs)]))), []).append(p.index)
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
reset(); rot_bone("jaw", 'X', 25)
dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
rips = []
for p in me.polygons:
    vs = list(p.vertices); c = sum((R[v] for v in vs), Vector()) / len(vs)
    if abs(c.x) > 0.06 or not (1.43 < c.z < 1.60): continue
    mx = 0.0
    for a in range(len(vs)):
        L0 = (R[vs[a]] - R[vs[(a+1) % len(vs)]]).length
        if L0 > 0.0006: mx = max(mx, (P[vs[a]] - P[vs[(a+1) % len(vs)]]).length / L0)
    if mx > 4.0: rips.append((mx, p.index, c))
rips.sort(key=lambda t: -t[0])
print("RIPS faces >4x at jaw25:", len(rips))
for mx, pi, c in rips[:12]: print(f"  {mx:5.1f}x face {pi} at x {1000*c.x:6.1f} z {1000*c.z:7.1f} y {1000*c.y:7.1f}")
