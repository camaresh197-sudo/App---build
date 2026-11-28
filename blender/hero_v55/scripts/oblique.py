import bpy, sys, math
from mathutils import Matrix, Vector
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v47.blend")
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
target = Vector((0, -0.12, 1.49)); dist = 0.34
def place(az, el):
    a = math.radians(az); e = math.radians(el)
    pos = target + Vector((dist * math.sin(a) * math.cos(e), -dist * math.cos(a) * math.cos(e), dist * math.sin(e)))
    cam.location = pos
    d = (target - pos).normalized(); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
views = {"right40": (40, 5), "left40": (-40, 5), "below": (0, -35)}
for tag, deg in (("rest", 0), ("jaw12", 12), ("jaw25", 25)):
    reset()
    if deg: rot_bone("jaw", 'X', deg)
    for vn, (az, el) in views.items():
        place(az, el); sc.render.filepath = D + "/rig/ob_%s_%s.png" % (tag, vn); bpy.ops.render.render(write_still=True)
print("done")
