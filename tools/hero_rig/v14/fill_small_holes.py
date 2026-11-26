import sys, bpy, bmesh, collections
src,dst=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2]
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['head_quad']
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
adj=collections.defaultdict(list)
be=[e for e in bm.edges if e.is_boundary]
for e in be:
    a,b=e.verts; adj[a.index].append(e); adj[b.index].append(e)
seen=set(); small=[]
for e in be:
    if e in seen: continue
    st=[e]; comp=[]; seen.add(e)
    while st:
        x=st.pop(); comp.append(x)
        for v in x.verts:
            for y in adj[v.index]:
                if y not in seen: seen.add(y); st.append(y)
    if len(comp)<=8: small.append(comp)
print('FILL small loops', len(small))
for comp in small:
    bmesh.ops.holes_fill(bm, edges=comp, sides=len(comp))
bm.normal_update()
flip=sum(1 for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].normal.dot(e.link_faces[1].normal)<0)
print('FILL flips', flip, 'boundary', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(o.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst); print('saved')
