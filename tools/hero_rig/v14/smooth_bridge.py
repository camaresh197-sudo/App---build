import sys, bpy, bmesh
from mathutils import Vector
src,dst=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2]
its=int(sys.argv[sys.argv.index('--')+3])
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['head_quad']; M=o.matrix_world
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
patch=[v for v in bm.verts if 1.512<(M@v.co).z<1.537 and abs((M@v.co).x)<0.024 and (M@v.co).y<-0.05]
print('SB patch', len(patch))
for it in range(its):
    new={}
    for v in patch:
        nb=[e.other_vert(v) for e in v.link_edges]
        new[v]=v.co.lerp(sum((n.co for n in nb),Vector())/len(nb),0.5)
    for v,p in new.items(): v.co=p
bm.normal_update()
import math, collections
h=collections.Counter()
for e in bm.edges:
    if len(e.link_faces)==2:
        d=max(-1.0,min(1.0,e.link_faces[0].normal.dot(e.link_faces[1].normal)))
        if d<0: h[int(math.degrees(math.acos(d))//15)*15]+=1
print('SB crease/fold histogram', dict(sorted(h.items())))
bm.to_mesh(o.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst); print('saved')
