import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v35.blend")
sc = bpy.context.scene
arm = bpy.data.objects["character_rig"]
def V(*a): return Vector(a[0]) if len(a) == 1 else Vector(a)
def W(): return arm.matrix_world
def hw(n): return W() @ arm.pose.bones[n].head
def reset():
    for pb in arm.pose.bones: pb.location = (0,0,0); pb.rotation_quaternion = (1,0,0,0); pb.rotation_euler = (0,0,0); pb.scale = (1,1,1)
    bpy.context.view_layer.update()
def aim(name, target):
    pb = arm.pose.bones[name]; h = W() @ pb.head; t = W() @ pb.tail
    rot = (t - h).normalized().rotation_difference(target.normalized()).to_matrix().to_4x4()
    pb.matrix = W().inverted() @ (Matrix.Translation(h) @ rot @ Matrix.Translation(-h) @ (W() @ pb.matrix)); bpy.context.view_layer.update()
def rot_about(name, axis, deg, pivot=None):
    pb = arm.pose.bones[name]; h = pivot if pivot is not None else (W() @ pb.head)
    R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h)
    pb.matrix = W().inverted() @ (R @ (W() @ pb.matrix)); bpy.context.view_layer.update()
def move(name, d):
    pb = arm.pose.bones[name]
    pb.matrix = W().inverted() @ (Matrix.Translation(d) @ (W() @ pb.matrix)); bpy.context.view_layer.update()
L1 = (V((0.14,-0.005,0.48)) - V((0.09,0,0.90))).length; L2 = (V((0.165,0,0.09)) - V((0.14,-0.005,0.48))).length
ANK = {"_r": V((0.165,0,0.09)), "_l": V((-0.165,0,0.09))}
def ik(s, ankle, pole):
    hip = hw("thigh" + s); v = ankle - hip; d = min(max(v.length, abs(L1 - L2) + 1e-3), L1 + L2 - 1e-3); u = v.normalized()
    a = math.acos((L1*L1 + d*d - L2*L2) / (2*L1*d))
    pp = (pole - pole.dot(u) * u).normalized()
    knee = hip + L1 * (math.cos(a) * u + math.sin(a) * pp)
    aim("thigh" + s, knee - hip); aim("shin" + s, ankle - hw("shin" + s))
    aim("foot" + s, V((0.055 if s == "_r" else -0.055, -0.12, -0.03)))
def plant(pole_x=0.15):
    ik("_r", ANK["_r"], V((pole_x, -1, 0))); ik("_l", ANK["_l"], V((-pole_x, -1, 0)))
def pose(name):
    reset()
    if name == "sway_L":
        move("pelvis", V(0.09, 0, 0)); rot_about("pelvis", 'Y', 10); plant(); rot_about("spine", 'Y', -6); rot_about("spine2", 'Y', -5)
    elif name == "sway_R":
        move("pelvis", V(-0.09, 0, 0)); rot_about("pelvis", 'Y', -10); plant(); rot_about("spine", 'Y', 6); rot_about("spine2", 'Y', 5)
    elif name == "squat":
        move("pelvis", V(0, 0.05, -0.36)); rot_about("pelvis", 'X', 12); plant(0.6); rot_about("spine", 'X', -10); rot_about("spine2", 'X', -8)
    elif name == "kick":
        aim("thigh_r", V(0.05, -1, 0.45)); aim("shin_r", V(0.05, -1, 0.15)); aim("foot_r", V(0.05, -1, -0.3)); rot_about("spine", 'X', 6)
    elif name == "side_raise":
        aim("thigh_l", V(-1, 0, 0.55)); aim("shin_l", V(-1, 0, 0.3)); rot_about("spine", 'Y', 8); rot_about("spine2", 'Y', 6)
    elif name == "thrust":
        move("pelvis", V(0, -0.08, 0)); rot_about("pelvis", 'X', -15); plant(); rot_about("spine", 'X', 10); rot_about("spine2", 'X', 8)
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1)
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x = 520; sc.render.resolution_y = 900
names = ["squat", "kick", "side_raise"]
for n in names:
    pose(n)
    cam.location = (0, -4.0, 0.95); cam.rotation_euler = (math.radians(90), 0, 0); sc.render.filepath = D + "/rig/hip35_%s_front.png" % n; bpy.ops.render.render(write_still=True)
    cam.location = (4.0, 0, 0.95); cam.rotation_euler = (math.radians(90), 0, math.radians(90)); sc.render.filepath = D + "/rig/hip35_%s_side.png" % n; bpy.ops.render.render(write_still=True)
sc.render.resolution_x = 700; sc.render.resolution_y = 700
for n in ["squat", "kick", "side_raise"]:
    pose(n)
    cam.location = (0, -1.9, 0.85); cam.rotation_euler = (math.radians(90), 0, 0); sc.render.filepath = D + "/rig/hip35_%s_close.png" % n; bpy.ops.render.render(write_still=True)
print("hip test done")
