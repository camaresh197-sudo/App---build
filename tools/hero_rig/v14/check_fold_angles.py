import sys, bpy, bmesh, math, collections
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
o=bpy.data.objects['head_quad']; M=o.matrix_world
bm=bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
hist=collections.Counter(); worst=[]
for e in bm.edges:
    if len(e.link_faces)==2:
        f0,f1=e.link_faces
        if f0.material_index>=1 or f1.material_index>=1: continue
        d=max(-1.0,min(1.0,f0.normal.dot(f1.normal)))
        if d<0:
            c=M@((e.verts[0].co+e.verts[1].co)/2)
            if 1.515<c.z<1.55 and abs(c.x)>0.02: continue
            a=math.degrees(math.acos(d)); hist[int(a//15)*15]+=1; worst.append(a)
print('ANG histogram (deg between neighbouring normals)', dict(sorted(hist.items())))
print('ANG max', round(max(worst),1) if worst else None, 'count>150', sum(1 for a in worst if a>150), 'count 90-135', sum(1 for a in worst if 90<=a<135))
