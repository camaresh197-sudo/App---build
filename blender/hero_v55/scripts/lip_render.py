import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
def run(fn, tag, has_lower):
    bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + fn)
    sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; cam = sc.camera
    cam.data.clip_start = 0.005; cam.data.lens = 50
    def reset():
        for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
        bpy.context.view_layer.update()
    def rot_bone(name, axis, deg):
        pb = arm.pose.bones[name]; h = pb.head.copy()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
    def move(name, d):
        pb = arm.pose.bones[name]; pb.matrix = Matrix.Translation(d) @ pb.matrix; bpy.context.view_layer.update()
    def lips(lu, out, up, ll):
        for k in range(17):
            prof = math.sin(math.pi * k / 16) ** 0.8
            move("lipU_%d" % k, Vector((0, 0, lu * prof)))
            if has_lower: move("lipL_%d" % k, Vector((0, 0, ll * prof)))
        move("corner_r", Vector((out, 0, up))); move("corner_l", Vector((-out, 0, up)))
        for k, s in ((0, 1), (16, -1)):
            move("lipU_%d" % k, Vector((s * out * 0.8, 0, up * 0.8)))
            if has_lower: move("lipL_%d" % k, Vector((s * out * 0.8, 0, up * 0.8)))
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
    sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = 520; sc.render.resolution_y = 520
    target = Vector((0, -0.12, 1.49))
    poses = [("snarl", lambda: (rot_bone("jaw", 'X', 12), lips(0.008, 0.008, 0.005, -0.003))),
             ("cover", lambda: (rot_bone("jaw", 'X', 12), lips(0.0, 0.0, 0.0, 0.006)))]
    for pn, f in poses:
        reset(); f()
        for vn, (az, el, dist) in {"front": (0, 0, 0.26), "right40": (40, 5, 0.32)}.items():
            a = math.radians(az); e = math.radians(el)
            cam.location = target + Vector((dist * math.sin(a) * math.cos(e), -dist * math.cos(a) * math.cos(e), dist * math.sin(e)))
            cam.rotation_euler = (target - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = D + "/rig/lr_%s_%s_%s.png" % (tag, pn, vn); bpy.ops.render.render(write_still=True)
run("body_rigged_v53_lips.blend", "v53", False)
run("body_rigged_v55_lips_smooth.blend", "v55", True)
print("done")
