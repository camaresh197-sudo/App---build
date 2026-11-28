import bpy, sys, bmesh
from mathutils import Vector
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v46.blend")
body = bpy.data.objects["body_gnm"]; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()
def zone(e): return 1.46 < (e.verts[0].co.z + e.verts[1].co.z) / 2 < 1.56 and abs((e.verts[0].co.x + e.verts[1].co.x) / 2) < 0.06
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
small = [c for c in loops if len(c) <= 12]
print("open loops in mouth zone", [len(c) for c in loops], "-> filling", [len(c) for c in small])
edges = [e for c in small for e in c]
res = bmesh.ops.holes_fill(bm, edges=edges, sides=12)
newf = list(res["faces"])
tri = bmesh.ops.triangulate(bm, faces=newf)["faces"]
flipped = 0
for f in tri:
    nbrs = [of for e in f.edges for of in e.link_faces if of not in tri and of.is_valid]
    if nbrs:
        ref = sum((of.normal for of in nbrs), Vector())
        if f.normal.dot(ref) < 0: f.normal_flip(); flipped += 1
    f.smooth = True
print("faces added", len(tri), "flipped to match neighbours", flipped)
rem = [e for e in bm.edges if e.is_boundary and zone(e)]
print("boundary edges left in zone", len(rem))
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v47.blend"); print("saved v47")
