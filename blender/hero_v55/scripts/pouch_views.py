import bpy, sys, math
from mathutils import Matrix, Vector
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
target = Vector((0, -0.12, 1.49))
views = {"front": (0, 0, 0.30), "right40": (40, 5, 0.34), "left40": (-40, 5, 0.34)}
for tag, deg in (("rest", 0), ("jaw12", 12), ("jaw25", 25)):
    reset()
    if deg: rot_bone("jaw", 'X', deg)
    for vn, (az, el, dist) in views.items():
        a = math.radians(az); e = math.radians(el)
        cam.location = target + Vector((dist * math.sin(a) * math.cos(e), -dist * math.cos(a) * math.cos(e), dist * math.sin(e)))
        cam.rotation_euler = (target - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = D + "/rig/%s_%s_%s.png" % (TAG, tag, vn); bpy.ops.render.render(write_still=True)
print("done")
