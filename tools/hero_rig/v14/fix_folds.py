import sys, bpy, bmesh
from mathutils import Vector
src,dst=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2]
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['head_quad']
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
def folds():
    return [e for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].normal.dot(e.link_faces[1].normal)<0]
bad=folds()
print('FIX before', len(bad))
# patch = verts of folded faces, plus one ring
seed=set()
for e in bad:
    for f in e.link_faces:
        for v in f.verts: seed.add(v)
ring=set(seed)
for v in seed:
    for e in v.link_edges:
        ring.add(e.other_vert(v))
inner=set(seed)  # move seed verts; keep the outer ring fixed
fixed=ring-inner
orig={v:v.co.copy() for v in inner}
for it in range(40):
    new={}
    for v in inner:
        nb=[e.other_vert(v) for e in v.link_edges]
        new[v]=sum((n.co for n in nb), Vector())/len(nb)
    for v,p in new.items(): v.co=p
bm.normal_update()
disp=max((v.co-orig[v]).length for v in inner)
left=folds()
print(f"FIX after {len(left)} folds, patch verts {len(inner)}, max move mm {disp*1000:.2f}")
bm.to_mesh(o.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst)
print('saved')
