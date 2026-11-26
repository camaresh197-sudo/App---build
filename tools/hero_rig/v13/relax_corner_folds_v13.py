# Relax the vertices of folded faces in the mouth corner band and re-project them to the skin (W077).
# python3 -I relax_corner_folds_v13.py -- in.blend out.blend
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']; hi=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
def band(c): return 0.026<abs(c.x)<0.042 and abs(c.z-1.4777)<0.025 and c.y<-0.05
folded=[]
for f in bm.faces:
    c=f.calc_center_median()
    if not band(c): continue
    nb=[g for e in f.edges for g in e.link_faces if g is not f]
    avg=sum((g.normal for g in nb),Vector())
    if avg.length>0 and f.normal.dot(avg.normalized())<-0.2: folded.append(f)
verts=set(v for f in folded for v in f.verts)
# include one ring of neighbours so the fix is not a single point
ring=set(verts)
for v in verts:
    for e in v.link_edges: ring.add(e.other_vert(v))
print("folded faces:",len(folded),"verts to relax:",len(verts),"with ring:",len(ring))
for _ in range(12):
    new={}
    for v in ring:
        nb=[e.other_vert(v) for e in v.link_edges]
        if not nb: continue
        c=sum((n.co for n in nb),Vector())/len(nb)
        q=0.5*v.co+0.5*c
        loc,n,i,d=bv.ray_cast(Vector((q.x,-0.5,q.z)),Vector((0,1,0)))
        new[v]=Vector((q.x,loc.y,q.z)) if loc else v.co.copy()
    for v,p in new.items(): v.co=p
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
