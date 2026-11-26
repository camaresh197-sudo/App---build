# Re-mesh the mouth corner bands (W078): delete the faces in each corner band, refill the openings with a
# fresh triangulated patch, re-project the new vertices onto the skin, and relax them.
# python3 -I remesh_corners_v13.py -- in.blend out.blend
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']; hi=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
def corner(c):
    return 0.024<abs(c.x)<0.040 and 1.466<c.z<1.490 and c.y<-0.05
dele=[f for f in bm.faces if corner(f.calc_center_median())]
print("corner faces removed:",len(dele))
bmesh.ops.delete(bm,geom=dele,context='FACES_ONLY')
bnd=[e for e in bm.edges if len(e.link_faces)==1]
print("open edges to refill:",len(bnd))
res=bmesh.ops.holes_fill(bm,edges=bnd,sides=0)
print("refill faces:",len(res['faces']))
new=set()
for f in res['faces']:
    for v in f.verts: new.add(v)
for v in new:
    loc,n,i,d=bv.ray_cast(Vector((v.co.x,-0.5,v.co.z)),Vector((0,1,0)))
    if loc: v.co=Vector((v.co.x,loc.y,v.co.z))
for _ in range(6):
    for v in new:
        nb=[e.other_vert(v) for e in v.link_edges]
        if not nb: continue
        c=sum((n.co for n in nb),Vector())/len(nb)
        q=0.5*v.co+0.5*c
        loc,n,i,d=bv.ray_cast(Vector((q.x,-0.5,q.z)),Vector((0,1,0)))
        if loc: v.co=Vector((q.x,loc.y,q.z))
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
