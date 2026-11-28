import bpy, sys, math, bmesh
import numpy as np
from collections import defaultdict
from mathutils import Vector
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v42.blend")
body = bpy.data.objects["body_gnm"]; me = body.data
gi = {g.name: g.index for g in body.vertex_groups}; H, J = gi["head"], gi["jaw"]
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
N = len(me.vertices); R = [v.co.copy() for v in me.vertices]
lab = [""] * N
for v in me.vertices:
    p = v.co
    if p.z < 1.38 or p.z > 1.62: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012: lab[v.index] = "far"; continue
    for n, tag in (("upper_lip", "U"), ("lower_lip", "L"), ("mouth_sock", "S"), ("teeth", "T"), ("gums", "G"), ("tongue", "N")):
        if has(n, idx): lab[v.index] = tag; break
    else: lab[v.index] = "skin"
jw = [next((g.weight for g in me.vertices[i].groups if g.group == J), 0.0) for i in range(N)]
CX = 0.0228
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
def inzone(f): c = f.calc_center_median(); return abs(c.x) < CX and 1.485 < c.z < 1.520
bad = [f for f in bm.faces if inzone(f) and ((max(jw[v.index] for v in f.verts) >= 0.9 and min(jw[v.index] for v in f.verts) <= 0.1) or ("U" in [lab[v.index] for v in f.verts] and "L" in [lab[v.index] for v in f.verts]))]
bmesh.ops.delete(bm, geom=bad, context='FACES_ONLY'); bm.edges.ensure_lookup_table()
be = [e for e in bm.edges if e.is_boundary and 1.48 < (e.verts[0].co.z + e.verts[1].co.z) / 2 < 1.52 and abs((e.verts[0].co.x + e.verts[1].co.x) / 2) < 0.03 and any(lab[v.index] in ("U", "L", "skin") for v in e.verts)]
rs = set(be); seen = set(); loops = []
for e in be:
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
loops.sort(key=len)
print("loops (edges):", [len(c) for c in loops])
for c in loops[:3]:
    print("--- loop with", len(c), "edges")
    fs = set()
    for e in c:
        for f in e.link_faces: fs.add(f)
    for f in list(fs)[:6]:
        cc = f.calc_center_median()
        print("   adjacent face at x %6.1f z %7.1f y %7.1f | verts:" % (1000 * cc.x, 1000 * cc.z, 1000 * cc.y), [(lab[v.index], round(jw[v.index], 2)) for v in f.verts])
