import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
def W(arm): return arm.matrix_world
def aim(arm, name, target):
    pb = arm.pose.bones[name]; h = arm.matrix_world @ pb.head; t = arm.matrix_world @ pb.tail
    rot = (t - h).normalized().rotation_difference(target.normalized()).to_matrix().to_4x4()
    pb.matrix = arm.matrix_world.inverted() @ (Matrix.Translation(h) @ rot @ Matrix.Translation(-h) @ (arm.matrix_world @ pb.matrix)); bpy.context.view_layer.update()
def pose_forward(arm):
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
    aim(arm, "clav_r", Vector((0.18,-0.07,0.04))); aim(arm, "uarm_r", Vector((0.1,-1,0))); aim(arm, "fore_r", Vector((0.1,-1,0)))
def eval_verts(body):
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); me = oe.to_mesh()
    pts = [oe.matrix_world @ v.co for v in me.vertices]; oe.to_mesh_clear(); return pts
res = {}
for tag, f in (("v37", "body_rigged_v37.blend"), ("v38", "body_rigged_v38.blend")):
    bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + f)
    arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]
    pose_forward(arm)
    res[tag] = eval_verts(body)
    if tag == "v38":
        for n in ("uarm_r", "deltoid_r"):
            pb = arm.pose.bones[n]; q = pb.rotation_quaternion if pb.rotation_mode == 'QUATERNION' else pb.rotation_euler.to_quaternion()
            m = arm.convert_space(pose_bone=pb, matrix=pb.matrix, from_space='POSE', to_space='LOCAL')
            ang = math.degrees(m.to_quaternion().angle)
            print("BONE", n, "local rest-relative rotation deg", round(ang, 2), "constraints", [(c.type, c.subtarget, c.influence) for c in pb.constraints])
        arm38 = arm; body38 = body
        # which verts carry deltoid weight
        gi = body.vertex_groups["deltoid_r"].index
        dv = [v.index for v in body.data.vertices if any(g.group == gi and g.weight > 0.01 for g in v.groups)]
        wsum = sum(g.weight for i in dv for g in body.data.vertices[i].groups if g.group == gi) / max(1, len(dv))
        print("deltoid_r verts", len(dv), "mean weight", round(wsum, 3))
a, b = res["v37"], res["v38"]
dv = [(b[i] - a[i]).length for i in range(len(a))]
print("MOVE v37->v38 forward pose: max mm", round(max(dv) * 1000, 2), "mean over verts >0.1mm", round(1000 * sum(x for x in dv if x > 1e-4) / max(1, sum(1 for x in dv if x > 1e-4)), 2), "verts moved >1mm", sum(1 for x in dv if x > 1e-3), ">5mm", sum(1 for x in dv if x > 5e-3))
