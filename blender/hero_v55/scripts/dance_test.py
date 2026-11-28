import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v34.blend")
sc = bpy.context.scene
arm = bpy.data.objects["character_rig"]
V = Vector
def wmat(): return arm.matrix_world
def rot_about(name, axis, deg, pivot=None):
    pb = arm.pose.bones[name]
    h = pivot if pivot is not None else (wmat() @ pb.head)
    R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h)
    pb.matrix = wmat().inverted() @ (R @ (wmat() @ pb.matrix)); bpy.context.view_layer.update()
def aim(name, target):
    pb = arm.pose.bones[name]
    h = wmat() @ pb.head; t = wmat() @ pb.tail
    rot = (t - h).normalized().rotation_difference(target.normalized()).to_matrix().to_4x4()
    pb.matrix = wmat().inverted() @ (Matrix.Translation(h) @ rot @ Matrix.Translation(-h) @ (wmat() @ pb.matrix)); bpy.context.view_layer.update()
def reset():
    for pb in arm.pose.bones: pb.location = (0,0,0); pb.rotation_quaternion = (1,0,0,0); pb.rotation_euler = (0,0,0); pb.scale = (1,1,1)
    bpy.context.view_layer.update()
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = 520; sc.render.resolution_y = 900
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -4.0, 0.95); cam.rotation_euler = (math.radians(90), 0, 0)
N = 6
for k in range(N):
    ph = 2 * math.pi * k / N
    reset()
    pel = arm.pose.bones["pelvis"]
    pw = wmat() @ pel.head
    # hip circle: pelvis yaw + side tilt (about world Y) + forward tilt (about world X)
    rot_about("pelvis", 'Z', 22 * math.sin(ph))
    rot_about("pelvis", 'Y', 12 * math.cos(ph), pw)
    rot_about("pelvis", 'X', 8 * math.sin(ph + 1.0), pw)
    # keep the legs pointing down (planted): aim thighs/shins back to vertical
    for s, x in (("_r", 0.14), ("_l", -0.14)):
        aim("thigh" + s, V((x - (0.09 if s == "_r" else -0.09), 0, -0.42)))
        aim("shin" + s, V((0.025 if s == "_r" else -0.025, 0, -0.39)))
    # counter-twist spine and chest
    rot_about("spine", 'Z', -12 * math.sin(ph)); rot_about("spine2", 'Z', -10 * math.sin(ph)); rot_about("chest", 'Z', -6 * math.sin(ph))
    # arm wave: right arm up and waving, left arm out and swinging
    aim("uarm_r", V((0.55, 0, 0.85))); aim("fore_r", V((0.30 + 0.5 * math.sin(2 * ph), -0.1, 0.9)))
    aim("uarm_l", V((-0.9, -0.2, 0.15 + 0.3 * math.sin(ph)))); aim("fore_l", V((-0.9, -0.3 - 0.2 * math.cos(ph), 0.1)))
    # head tilt
    rot_about("neck", 'Y', 8 * math.sin(ph)); rot_about("head", 'Z', -10 * math.sin(ph))
    sc.render.filepath = D + "/rig/dance_%d.png" % k; bpy.ops.render.render(write_still=True)
# close-up of the worst-case hip frame
reset()
ph = math.pi / 2; pel = arm.pose.bones["pelvis"]; pw = wmat() @ pel.head
rot_about("pelvis", 'Z', 22); rot_about("pelvis", 'Y', 0, pw)
rot_about("spine", 'Z', -12); rot_about("spine2", 'Z', -10); rot_about("chest", 'Z', -6)
cam.location = (0, -1.8, 1.05); cam.rotation_euler = (math.radians(90), 0, 0); sc.render.resolution_x = 700; sc.render.resolution_y = 700
sc.render.filepath = D + "/rig/dance_hips_close.png"; bpy.ops.render.render(write_still=True)
print("dance done")
