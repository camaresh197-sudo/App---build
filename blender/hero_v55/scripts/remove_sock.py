import bpy, sys, bmesh, math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v47.blend")
body = bpy.data.objects["body_gnm"]; me = body.data
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
N = len(me.vertices); sock = [False] * N; lip = [False] * N
for v in me.vertices:
    p = v.co
    if p.z < 1.38 or p.z > 1.62: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012: continue
    sock[v.index] = VG[gnames.index("mouth_sock"), idx] > 0.5
    lip[v.index] = VG[gnames.index("upper_lip"), idx] > 0.5 or VG[gnames.index("lower_lip"), idx] > 0.5
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
dead = [f for f in bm.faces if all(sock[v.index] for v in f.verts)]
mixed = [f for f in bm.faces if any(sock[v.index] for v in f.verts) and not all(sock[v.index] for v in f.verts)]
print("sock-only faces", len(dead), "| faces mixing sock and other verts (lip/skin joins)", len(mixed))
bmesh.ops.delete(bm, geom=dead, context='FACES')
bm.edges.ensure_lookup_table()
def zone(e): return 1.44 < (e.verts[0].co.z + e.verts[1].co.z) / 2 < 1.58 and abs((e.verts[0].co.x + e.verts[1].co.x) / 2) < 0.07
be = [e for e in bm.edges if e.is_boundary and zone(e)]
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
for k, c in enumerate(sorted(loops, key=len, reverse=True)):
    vv = {v for x in c for v in x.verts}
    xs = [v.co.x for v in vv]; zs = [v.co.z for v in vv]; ys = [v.co.y for v in vv]
    print("LOOP", k + 1, "edges", len(c), "x mm", round(1000 * min(xs), 1), round(1000 * max(xs), 1), "z mm", round(1000 * min(zs), 1), round(1000 * max(zs), 1), "y mm", round(1000 * min(ys), 1), round(1000 * max(ys), 1))
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v48_nosock.blend"); print("saved v48")
