import bpy, sys, math, bmesh
from collections import defaultdict
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v71_remesh.blend")
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
N = len(me.vertices)
R = [v.co.copy() for v in me.vertices]
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
def rot_bone(name, axis, deg):
    pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def strain_faces(thresh=4.0):
    reset(); rot_bone("jaw", 'X', 25)
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
    out = []
    for p in me.polygons:
        vs = list(p.vertices); c = sum((R[v] for v in vs), Vector()) / len(vs)
        if abs(c.x) > 0.06 or not (1.43 < c.z < 1.60): continue
        mx = 0.0
        for a in range(len(vs)):
            L0 = (R[vs[a]] - R[vs[(a+1) % len(vs)]]).length
            if L0 > 0.0006: mx = max(mx, (P[vs[a]] - P[vs[(a+1) % len(vs)]]).length / L0)
        if mx > thresh: out.append(p.index)
    return out
before = strain_faces()
print("BEFORE faces >4x:", len(before))
# 1) remove the stretched faces at the corners (x beyond 15 mm, near lip line) and re-fill the holes
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bad = set(before)
dead = [f for f in bm.faces if f.index in bad and abs(f.calc_center_median().x) > 0.012]
bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.edges.ensure_lookup_table()
bnd = [e for e in bm.edges if e.is_boundary]
loops = []; seen = set(); rs = set(bnd)
for e in bnd:
    if e in seen: continue
    st = [e]; comp = []
    while st:
        x = st.pop()
        if x in seen: continue
        seen.add(x); comp.append(x)
        for v in x.verts:
            for ee in v.link_edges:
                if ee in rs and ee not in seen: st.append(ee)
    loops.append(comp)
small = [c for c in loops if len(c) <= 12]
print("deleted", len(dead), "faces; small holes to fill:", [len(c) for c in small])
if small:
    res = bmesh.ops.holes_fill(bm, edges=[e for c in small for e in c], sides=12)
    bmesh.ops.triangulate(bm, faces=list(res["faces"]))
bm.normal_update()
bm.to_mesh(me); bm.free(); me.update()
# 2) smooth the corner vertices that now sit on the sliver edges
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v73_rips.blend")
after = strain_faces()
print("AFTER faces >4x:", len(after))
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
