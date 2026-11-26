# W096: smooth the brow seam step: relax the head vertices in a band around the cap rim at the brow, re-projected onto the
# high-poly skin each pass (the rim itself is fixed). python3 -I brow_step_v13.py -- in out
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['head_quad']; lo=bpy.data.objects['head_low']
bv=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
C=Vector((0.0,-0.02,1.58))
bm=bmesh.new(); bm.from_mesh(lo.data); bm.verts.ensure_lookup_table()
band=set(v for v in bm.verts if v.co.y<-0.04 and 1.56<v.co.z<1.63 and (v.co-C).length>0.06)
rim=set()
print("brow band verts:",len(band))
orig={v:v.co.copy() for v in band}
for _ in range(6):
    new={}
    for v in band:
        nb=[e.other_vert(v) for e in v.link_edges]
        c=sum((n.co for n in nb),Vector())/len(nb)
        q=0.5*v.co+0.5*c
        loc,n,i,d=bv.ray_cast(C,(q-C).normalized())
        new[v]=loc if loc else v.co.copy()
    for v,p in new.items(): v.co=p
mx=max((v.co-orig[v]).length for v in band) if band else 0
print("max move mm: %.2f"%(mx*1000))
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
