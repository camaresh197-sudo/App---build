import bpy, sys, math
from mathutils import Matrix
D = sys.argv[-1]; SRC = sys.argv[sys.argv.index("--") - 2]; TAG = sys.argv[sys.argv.index("--") - 1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + SRC)
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; cam = sc.camera
cam.data.clip_start = 0.005; cam.data.lens = 50
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = 520; sc.render.resolution_y = 520
cam.location = (0.0, -0.30, 1.50); cam.rotation_euler = (math.radians(90), 0, 0)
for tag, deg in (("rest", 0), ("jaw12", 12), ("jaw25", 25)):
    reset()
    if deg: rot_bone("jaw", 'X', deg)
    sc.render.filepath = D + "/rig/%s_%s.png" % (TAG, tag); bpy.ops.render.render(write_still=True)
print("done")
