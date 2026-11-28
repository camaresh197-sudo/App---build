import bpy, sys, bmesh
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v46.blend")
me = bpy.data.objects["body_gnm"].data
bm = bmesh.new(); bm.from_mesh(me)
be = [e for e in bm.edges if e.is_boundary and 1.46 < (e.verts[0].co.z + e.verts[1].co.z) / 2 < 1.56 and abs((e.verts[0].co.x + e.verts[1].co.x) / 2) < 0.06]
rs = set(be); seen = set(); k = 0
for e in sorted(be, key=lambda e: e.verts[0].co.x):
    if e in seen: continue
    st = [e]; comp = []
    while st:
        x = st.pop()
        if x in seen: continue
        seen.add(x); comp.append(x)
        for v in x.verts:
            for ee in v.link_edges:
                if ee in rs and ee not in seen: st.append(ee)
    vv = {v for x in comp for v in x.verts}
    xs = [v.co.x for v in vv]; zs = [v.co.z for v in vv]; ys = [v.co.y for v in vv]
    ln = sum((x.verts[0].co - x.verts[1].co).length for x in comp)
    k += 1; print("LOOP", k, "edges", len(comp), "length mm", round(1000 * ln, 1), "x", round(1000 * min(xs), 1), round(1000 * max(xs), 1), "z", round(1000 * min(zs), 1), round(1000 * max(zs), 1), "y", round(1000 * min(ys), 1), round(1000 * max(ys), 1))
