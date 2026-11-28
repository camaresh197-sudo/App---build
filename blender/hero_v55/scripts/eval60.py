import bpy, sys, math, json
import numpy as np
from collections import Counter
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]; FN = sys.argv[sys.argv.index("--") - 2]; TAG = sys.argv[sys.argv.index("--") - 1]
meta = json.load(open(D + "/rig/pipeline60_meta.json")); M = meta["M"]; NPOUCH = meta["NPOUCH"]; NNEW = meta["NNEW"]
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
def pip(pt, poly):
    x, z = pt; inside = False; n = len(poly)
    for i in range(n):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1 + 1e-12) + x1: inside = not inside
    return inside
bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + FN)
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data; cam = sc.camera
cam.data.clip_start = 0.005; cam.data.lens = 50
NP = len(me.polygons); N = len(me.vertices); N0 = N - NNEW
ring = [me.polygons[NP - NPOUCH + i].vertices[0] for i in range(M)]
R = [v.co.copy() for v in me.vertices]; interior = [False] * N; cat = [""] * N; upT = []; loT = []
for i in range(N0):
    p = R[i]
    if p.z < 1.38 or p.z > 1.62: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012: continue
    if any(has(n, idx) for n in ("teeth", "gums", "tongue", "upper_teeth_and_gums", "lower_teeth_and_gums")): interior[i] = True
    if has("teeth", idx): (upT if has("upper_teeth_and_gums", idx) else loT).append(i)
    cat[i] = "upper_lip" if has("upper_lip", idx) else ("lower_lip" if has("lower_lip", idx) else "skin")
sedges = [(e.vertices[0], e.vertices[1]) for e in me.edges if e.vertices[0] < N0 and e.vertices[1] < N0 and not interior[e.vertices[0]] and not interior[e.vertices[1]]
          and abs(R[e.vertices[0]].x) < 0.045 and 1.45 < R[e.vertices[0]].z < 1.56 and (R[e.vertices[0]] - R[e.vertices[1]]).length > 0.0008]
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
        move("lipU_%d" % k, Vector((0, 0, lu * prof))); move("lipL_%d" % k, Vector((0, 0, ll * prof)))
    move("corner_r", Vector((out, 0, up))); move("corner_l", Vector((-out, 0, up)))
    for k, s in ((0, 1), (16, -1)):
        move("lipU_%d" % k, Vector((s * out * 0.8, 0, up * 0.8))); move("lipL_%d" % k, Vector((s * out * 0.8, 0, up * 0.8)))
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = 520; sc.render.resolution_y = 520
target = Vector((0, -0.12, 1.49))
poses = [("rest", lambda: None), ("snarl", lambda: (rot_bone("jaw", 'X', 12), lips(0.008, 0.008, 0.005, -0.003))),
         ("cover", lambda: (rot_bone("jaw", 'X', 12), lips(0.0, 0.0, 0.0, 0.006))), ("jaw25", lambda: rot_bone("jaw", 'X', 25))]
for pn, f in poses:
    reset(); f()
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
    rx = [P[i].x for i in ring]; rz = [P[i].z for i in ring]; cx = sum(rx) / M; cz = sum(rz) / M
    poly = sorted(((P[i].x, P[i].z) for i in ring), key=lambda q: math.atan2(q[1] - cz, q[0] - cx))
    ut = sum(1 for i in upT if pip((P[i].x, P[i].z), poly)); lt = sum(1 for i in loT if pip((P[i].x, P[i].z), poly))
    ratios = sorted((P[a] - P[b]).length / (R[a] - R[b]).length for a, b in sedges); n = len(ratios)
    badn = sum(1 for r in ratios if r > 3.0 or r < 0.3)
    print(f"RESULT {pn:6s}: opening {1000*(max(rx)-min(rx)):5.1f} x {1000*(max(rz)-min(rz)):5.1f} mm | teeth shown up {ut:4d} low {lt:4d} | edge ratio p1 {ratios[n//100]:.2f} p99 {ratios[-n//100]:.2f} min {ratios[0]:.2f} max {ratios[-1]:.2f} | edges >3x or <0.3x: {badn}")
    for vn, (az, el, dist) in {"front": (0, 0, 0.26), "right40": (40, 5, 0.32)}.items():
        a = math.radians(az); e = math.radians(el)
        cam.location = target + Vector((dist * math.sin(a) * math.cos(e), -dist * math.cos(a) * math.cos(e), dist * math.sin(e)))
        cam.rotation_euler = (target - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = D + "/rig/%s_%s_%s.png" % (TAG, pn, vn); bpy.ops.render.render(write_still=True)
print("done")
