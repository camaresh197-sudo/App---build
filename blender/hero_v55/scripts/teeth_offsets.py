import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v47.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me0 = body.data
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
N = len(me0.vertices); cat = [""] * N
for v in me0.vertices:
    p = v.co
    if p.z < 1.40 or p.z > 1.60: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012: continue
    if has("upper_lip", idx): cat[v.index] = "ulip"
    elif has("lower_lip", idx): cat[v.index] = "llip"
    elif has("teeth", idx) and has("upper_teeth_and_gums", idx): cat[v.index] = "uteeth"
    elif has("teeth", idx) and has("lower_teeth_and_gums", idx): cat[v.index] = "lteeth"
    elif has("mouth_sock", idx): cat[v.index] = "sock"
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
R = [v.co.copy() for v in me0.vertices]
def evalv():
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear(); return P
def mean(P, sel): 
    vs = [P[i] for i in sel]; return sum(vs, Vector()) / len(vs)
front = lambda c: [i for i in range(N) if cat[i] == c and abs(R[i].x) < 0.012]
sel = {c: front(c) for c in ("llip", "ulip", "lteeth", "uteeth")}
print("front selections:", {k: len(v) for k, v in sel.items()})
# molars vs cheek wall: lower teeth outermost x, and the sock (cheek-wall) outermost x at the same height
molar = [i for i in range(N) if cat[i] == "lteeth" and abs(R[i].x) > 0.020]
sockw = [i for i in range(N) if cat[i] == "sock" and abs(R[i].x) > 0.020]
res = {}
for deg in (0, 12, 25):
    reset()
    if deg: rot_bone("jaw", 'X', deg)
    P = evalv(); res[deg] = P
    ll = mean(P, sel["llip"]); lt = mean(P, sel["lteeth"]); ul = mean(P, sel["ulip"]); ut = mean(P, sel["uteeth"])
    print(f"JAW {deg:2d}: lower teeth - lower lip (mm): dy {1000*(lt.y-ll.y):6.1f} dz {1000*(lt.z-ll.z):6.1f} | upper teeth - upper lip: dy {1000*(ut.y-ul.y):6.1f} dz {1000*(ut.z-ul.z):6.1f}")
    mx = max(abs(P[i].x) for i in molar); sx = max(abs(P[i].x) for i in sockw)
    print(f"        outermost |x| mm: lower molars {1000*mx:.1f}  cheek wall (sock) {1000*sx:.1f}")
# how far each lower-teeth vertex is from the nearest skin/lip surface point (front)
