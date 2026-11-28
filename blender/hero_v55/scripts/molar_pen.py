import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
D = sys.argv[-1]; SRC = sys.argv[sys.argv.index("--") - 1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + SRC)
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me0 = body.data
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
N = len(me0.vertices); inner = [False] * N; lteeth = [False] * N
for v in me0.vertices:
    p = v.co
    if p.z < 1.38 or p.z > 1.62: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012: continue
    if any(has(n, idx) for n in ("teeth", "gums", "tongue", "mouth_sock", "upper_teeth_and_gums", "lower_teeth_and_gums")): inner[v.index] = True
    if has("lower_teeth_and_gums", idx) and (has("teeth", idx) or has("gums", idx)): lteeth[v.index] = True
R = [v.co.copy() for v in me0.vertices]
mol = [i for i in range(N) if lteeth[i] and abs(R[i].x) > 0.020]
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
polys = [list(p.vertices) for p in me0.polygons]
skin_faces = [[v for v in f] for f in polys if not any(inner[v] for v in f)]
for deg in (0, 12, 25):
    reset()
    if deg: rot_bone("jaw", 'X', deg)
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
    tris = []
    for f in skin_faces:
        tris.append(tuple(f[:3]))
        if len(f) == 4: tris.append((f[0], f[2], f[3]))
    bvh = BVHTree.FromPolygons(P, tris)
    out = 0; dist = []
    for i in mol:
        s = 1.0 if P[i].x > 0 else -1.0
        hit, n, idx, d = bvh.ray_cast(P[i], Vector((s, 0, 0)), 0.2)
        if hit is None: out += 1
        else: dist.append(d)
    dist.sort()
    print(f"JAW {deg:2d}: lower molar verts {len(mol)} | NO cheek skin outside them: {out} | cheek thickness mm: min {1000*dist[0]:.1f} median {1000*dist[len(dist)//2]:.1f}" if dist else f"JAW {deg}: no hits, all {len(mol)} outside")
