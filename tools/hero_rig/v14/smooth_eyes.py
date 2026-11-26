import sys, bpy, bmesh, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,dst,its=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2], int(sys.argv[sys.argv.index('--')+3])
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['head_quad']; M=o.matrix_world
L=json.load(open('/tmp/claude-0/-home-user-App---build/06e83864-e0ef-54c3-9ec4-508030560da5/scratchpad/hero/v143_landmarks.json'))
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
RX2,RZ2=0.026,0.016
patch=set(); rim=set()
for name in ['eye_l','eye_r']:
    cx,_,cz=[v/1000 for v in L[name]]
    for v in bm.verts:
        p=M@v.co
        if p.y<-0.03:
            e=((p.x-cx)/RX2)**2+((p.z-cz)/RZ2)**2
            if e<=0.95**2 and not v.is_boundary: patch.add(v)
            elif e<=1.12**2: rim.add(v)
print('SE patch', len(patch))
def mirror_gap():
    # mean mirror gap in the eye band (skin only)
    sk=bmesh.new(); sk.from_mesh(o.data); sk.transform(M); tree=BVHTree.FromBMesh(sk); out=[]
    for v in patch:
        p=M@v.co; mp=Vector((-p.x,p.y,p.z)); out.append(tree.find_nearest(mp)[3])
    sk.free(); return sum(out)/len(out)*1000, max(out)*1000
orig={v:v.co.copy() for v in patch}
g0=mirror_gap(); print(f'SE mirror gap before mean {g0[0]:.2f} max {g0[1]:.2f} mm')
for it in range(its):
    new={}
    for v in patch:
        nb=[e.other_vert(v) for e in v.link_edges]
        new[v]=v.co.lerp(sum((n.co for n in nb),Vector())/len(nb),0.5)
    for v,p in new.items(): v.co=p
bm.to_mesh(o.data)   # so mirror_gap sees the result
g1=mirror_gap(); print(f'SE mirror gap after  mean {g1[0]:.2f} max {g1[1]:.2f} mm')
mv=max((v.co-orig[v]).length for v in patch)*1000
bm.normal_update()
h={}
for e in bm.edges:
    if len(e.link_faces)==2:
        d=max(-1.0,min(1.0,e.link_faces[0].normal.dot(e.link_faces[1].normal)))
        if d<0: k=int(math.degrees(math.acos(d))//15)*15; h[k]=h.get(k,0)+1
print('SE max move mm', round(mv,2), 'crease/fold histogram', dict(sorted(h.items())))
bm.to_mesh(o.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst); print('saved')
