import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[sys.argv.index("--") + 1]; FN = sys.argv[sys.argv.index("--") + 2]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + FN)
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
R = [v.co.copy() for v in me.vertices]
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
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
            if r > 4.0: n += 1; break
print("STRAIN", FN, "faces >4x at jaw25:", n, "worst", round(worst, 1))
