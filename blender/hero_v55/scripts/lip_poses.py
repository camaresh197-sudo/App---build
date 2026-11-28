import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]; SRC = sys.argv[sys.argv.index("--") - 2]; TAG = sys.argv[sys.argv.index("--") - 1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + SRC)
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data; cam = sc.camera
cam.data.clip_start = 0.005; cam.data.lens = 50
NPOUCH = 702; NP = len(me.polygons); N = len(me.vertices); N0 = N - 649
ring = [me.polygons[NP - NPOUCH + i].vertices[0] for i in range(54)]
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
upT = []; loT = []
for i in range(N0):
    p = me.vertices[i].co
    if p.z < 1.38 or p.z > 1.62: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012 or not has("teeth", idx): continue
    (upT if has("upper_teeth_and_gums", idx) else loT).append(i)
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def move(name, d):
    pb = arm.pose.bones[name]; pb.matrix = Matrix.Translation(d) @ pb.matrix; bpy.context.view_layer.update()
def lips(lift, out, up):
    for k in range(17):
        prof = math.sin(math.pi * k / 16) ** 0.8
        move("lipU_%d" % k, Vector((0, 0, lift * prof)))
    move("corner_r", Vector((out, 0, up))); move("corner_l", Vector((-out, 0, up)))
    for k, s in ((0, 1), (16, -1)): move("lipU_%d" % k, Vector((s * out * 0.8, 0, up * 0.8)))
def pip(pt, poly):
    x, z = pt; inside = False; n = len(poly)
    for i in range(n):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1 + 1e-12) + x1: inside = not inside
    return inside
def measure(tag):
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
    rx = [P[i].x for i in ring]; rz = [P[i].z for i in ring]; cx = sum(rx) / 54; cz = sum(rz) / 54
    poly = sorted(((P[i].x, P[i].z) for i in ring), key=lambda q: math.atan2(q[1] - cz, q[0] - cx))
    ut = sum(1 for i in upT if pip((P[i].x, P[i].z), poly)); lt = sum(1 for i in loT if pip((P[i].x, P[i].z), poly))
    print(f"POSE {tag:12s}: opening width {1000*(max(rx)-min(rx)):5.1f} mm, height {1000*(max(rz)-min(rz)):5.1f} mm | tooth verts in opening: upper {ut:4d} lower {lt:4d}")
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = 520; sc.render.resolution_y = 520
target = Vector((0, -0.12, 1.49)); views = {"front": (0, 0, 0.26), "right40": (40, 5, 0.32)}
poses = [("jaw12", lambda: rot_bone("jaw", 'X', 12)),
         ("jaw12+snarl", lambda: (rot_bone("jaw", 'X', 12), lips(0.008, 0.008, 0.005))),
         ("jaw25+snarl", lambda: (rot_bone("jaw", 'X', 25), lips(0.008, 0.008, 0.005)))]
for tag, f in poses:
    reset(); f(); measure(tag)
    for vn, (az, el, dist) in views.items():
        a = math.radians(az); e = math.radians(el)
        cam.location = target + Vector((dist * math.sin(a) * math.cos(e), -dist * math.cos(a) * math.cos(e), dist * math.sin(e)))
        cam.rotation_euler = (target - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = D + "/rig/%s_%s_%s.png" % (TAG, tag.replace('+', '_'), vn); bpy.ops.render.render(write_still=True)
print("done")
