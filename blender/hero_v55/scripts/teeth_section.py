import bpy, sys, math, bmesh
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]; SRC = sys.argv[sys.argv.index("--") - 2]; TAG = sys.argv[sys.argv.index("--") - 1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + SRC)
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me0 = body.data; cam = sc.camera
cam.data.clip_start = 0.005
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
    elif has("teeth", idx) and (has("upper_teeth_and_gums", idx)): cat[v.index] = "uteeth"
    elif has("teeth", idx) and (has("lower_teeth_and_gums", idx)): cat[v.index] = "lteeth"
    elif has("gums", idx) and has("upper_teeth_and_gums", idx): cat[v.index] = "ugum"
    elif has("gums", idx) and has("lower_teeth_and_gums", idx): cat[v.index] = "lgum"
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = 520; sc.render.resolution_y = 520
for o in bpy.data.objects:
    if o.name.startswith(("eyeball_", "iris_", "pupil_")): o.hide_render = True
for tag, deg in (("rest", 0), ("jaw12", 12), ("jaw25", 25)):
    reset()
    if deg: rot_bone("jaw", 'X', deg)
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); me = oe.to_mesh()
    P = [v.co.copy() for v in me.vertices]
    def stat(c, f):
        vs = [P[i] for i in range(N) if cat[i] == c]
        return (min(f(p) for p in vs), max(f(p) for p in vs)) if vs else (None, None)
    uy = stat("uteeth", lambda p: p.y); ly = stat("lteeth", lambda p: p.y); lipU = stat("ulip", lambda p: p.y); lipL = stat("llip", lambda p: p.y)
    uz = stat("uteeth", lambda p: p.z); lz = stat("lteeth", lambda p: p.z)
    print(f"POSE {tag}: front-most y (mm)  upper teeth {1000*uy[0]:.1f}  upper lip {1000*lipU[0]:.1f}  | lower teeth {1000*ly[0]:.1f}  lower lip {1000*lipL[0]:.1f}")
    print(f"        teeth z (mm): upper teeth bottom {1000*uz[0]:.1f}, lower teeth top {1000*lz[1]:.1f}  | gap {1000*(uz[0]-lz[1]):.1f}")
    # sagittal section
    bm = bmesh.new(); bm.from_mesh(me)
    for e in list(bm.edges): pass
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces), plane_co=(0.0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    sm = bpy.data.meshes.new("sect"); bm.to_mesh(sm); bm.free()
    so = bpy.data.objects.new("sect", sm); sc.collection.objects.link(so)
    body.hide_render = True
    cam.location = (0.45, -0.08, 1.50); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    sc.render.filepath = D + "/rig/%s_sect_%s.png" % (TAG, tag); bpy.ops.render.render(write_still=True)
    body.hide_render = False; bpy.data.objects.remove(so, do_unlink=True); oe.to_mesh_clear()
reset(); print("done")
