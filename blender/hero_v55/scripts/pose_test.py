import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v34.blend")
sc = bpy.context.scene
arm = bpy.data.objects["character_rig"]
V = Vector
def world_dir(pb):
    h = arm.matrix_world @ pb.head; t = arm.matrix_world @ pb.tail
    return (t - h).normalized(), h
def aim(name, target):
    pb = arm.pose.bones[name]; cur, h = world_dir(pb)
    rot = cur.rotation_difference(target.normalized()).to_matrix().to_4x4()
    pb.matrix = arm.matrix_world.inverted() @ (Matrix.Translation(h) @ rot @ Matrix.Translation(-h) @ (arm.matrix_world @ pb.matrix))
    bpy.context.view_layer.update()
def rotz(name, deg):
    pb = arm.pose.bones[name]; h = arm.matrix_world @ pb.head
    R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, 'Z') @ Matrix.Translation(-h)
    pb.matrix = arm.matrix_world.inverted() @ (R @ (arm.matrix_world @ pb.matrix)); bpy.context.view_layer.update()
def reset():
    for pb in arm.pose.bones: pb.location = (0,0,0); pb.rotation_quaternion = (1,0,0,0); pb.rotation_euler = (0,0,0); pb.scale = (1,1,1)
    bpy.context.view_layer.update()
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = 700; sc.render.resolution_y = 1000
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
def shot(name, loc, rot):
    cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = D + "/rig/pose34_%s.png" % name; bpy.ops.render.render(write_still=True)
front = ((0, -4.2, 0.85), (math.radians(90), 0, 0)); side = ((4.2, 0, 0.85), (math.radians(90), 0, math.radians(90)))
# A: arms out horizontal
reset()
aim("uarm_r", V((1, 0, 0.1))); aim("fore_r", V((1, 0, 0.1))); aim("uarm_l", V((-1, 0, 0.1))); aim("fore_l", V((-1, 0, 0.1)))
shot("A_armsout", *front)
# B: elbows bent 90 forward, right knee raised
reset()
aim("fore_r", V((0.1, -1, 0.1))); aim("fore_l", V((-0.1, -1, 0.1)))
aim("thigh_r", V((0.1, -1, -0.3))); aim("shin_r", V((0.1, -0.2, -1)))
shot("B_bent", *side); shot("B_bent_front", *front)
# C: head turn + spine bend
reset()
rotz("head", 40); rotz("neck", 20); rotz("spine2", 15)
shot("C_headturn", (0, -1.6, 1.35), (math.radians(90), 0, 0))
print("poses done")
