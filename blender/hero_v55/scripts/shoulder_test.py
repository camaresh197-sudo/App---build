import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v36.blend")
sc = bpy.context.scene
arm = bpy.data.objects["character_rig"]
def V(*a): return Vector(a[0]) if len(a) == 1 else Vector(a)
def W(): return arm.matrix_world
def reset():
    for pb in arm.pose.bones: pb.location = (0,0,0); pb.rotation_quaternion = (1,0,0,0); pb.rotation_euler = (0,0,0); pb.scale = (1,1,1)
    bpy.context.view_layer.update()
def aim(name, target):
    pb = arm.pose.bones[name]; h = W() @ pb.head; t = W() @ pb.tail
    rot = (t - h).normalized().rotation_difference(target.normalized()).to_matrix().to_4x4()
    pb.matrix = W().inverted() @ (Matrix.Translation(h) @ rot @ Matrix.Translation(-h) @ (W() @ pb.matrix)); bpy.context.view_layer.update()
def arm_r(d, d2=None, clav=None):
    if clav is not None: aim("clav_r", clav)
    aim("uarm_r", d); aim("fore_r", d2 if d2 is not None else d)
poses = {
 "T_out":   lambda: arm_r(V(1, 0, 0.05)),
 "overhead": lambda: arm_r(V(0.25, 0, 1), clav=V(1, 0, 0.35)),
 "forward": lambda: arm_r(V(0.1, -1, 0.0)),
 "across":  lambda: arm_r(V(-0.6, -1, -0.1), V(-1, -0.4, -0.05)),
 "back":    lambda: arm_r(V(0.35, 1, -0.15)),
}
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1)
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x = 520; sc.render.resolution_y = 520
views = {"front": ((0.15, -2.1, 1.3), (math.radians(90), 0, 0)),
         "side": ((2.1, -0.0, 1.3), (math.radians(90), 0, math.radians(90))),
         "back": ((0.15, 2.1, 1.3), (math.radians(90), 0, math.radians(180)))}
for n, f in poses.items():
    reset(); f()
    for vn, (loc, rot) in views.items():
        cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = D + "/rig/sh_%s_%s.png" % (n, vn); bpy.ops.render.render(write_still=True)
print("shoulder test done")
