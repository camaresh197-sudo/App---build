import bpy, sys, math
from mathutils import Vector
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v37.blend")
body = bpy.data.objects["body_gnm"]; arm = bpy.data.objects["character_rig"]
for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
bpy.context.view_layer.update()
P = [body.matrix_world @ v.co for v in body.data.vertices]
for n in ("clav_r","shoulder_r","uarm_r","elbow_r"):
    b = arm.data.bones[n]; print("BONE", n, "head", [round(c,3) for c in b.head_local], "tail", [round(c,3) for c in b.tail_local])
print("SHOULDER top z (x 0.15-0.40):", round(max(p.z for p in P if 0.15 < p.x < 0.40),3))
print("outer x at z 1.25-1.32:", round(max(p.x for p in P if 1.25 < p.z < 1.32),3))
for x0 in [0.16, 0.20, 0.24, 0.28, 0.32, 0.36]:
    sl = [p for p in P if x0 <= p.x < x0 + 0.02 and p.z > 1.0]
    # largest-z cluster = arm/deltoid lobe: take verts with z > (zmax - 0.22)
    zmax = max(p.z for p in sl); lobe = [p for p in sl if p.z > zmax - 0.22 and p.z < zmax]
    ys = [p.y for p in lobe]; zs = [p.z for p in lobe]
    print("X", x0, "n", len(sl), "z", round(min(p.z for p in sl),3), round(zmax,3), "lobe centre y,z", round((min(ys)+max(ys))/2,3), round((min(zs)+max(zs))/2,3), "lobe size y", round(max(ys)-min(ys),3))
# upper arm slices along z (arm hanging at ~A-pose): x extents of the arm lobe
for z0 in [1.30, 1.25, 1.20, 1.15, 1.10]:
    sl = [p for p in P if z0 <= p.z < z0 + 0.02 and p.x > 0.18]
    if sl:
        arm_l = [p for p in sl if p.x > 0.20]
        print("Z", z0, "x", round(min(p.x for p in arm_l),3), round(max(p.x for p in arm_l),3), "centre y", round(sum(p.y for p in arm_l)/len(arm_l),3))
