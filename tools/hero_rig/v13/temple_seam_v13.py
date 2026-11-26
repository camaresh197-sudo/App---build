# W098: fix the temple sawtooth: move only head vertices in the temple band (side and back of the cranium seam) onto the
# nearest point of the high-poly skin, capped at 3 mm per vertex. Eye and brow vertices (front) are excluded.
# python3 -I temple_seam_v13.py -- in out
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['head_quad']; lo=bpy.data.objects['head_low']
bv=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
C=Vector((0.0,-0.02,1.58))
bm=bmesh.new(); bm.from_mesh(lo.data); bm.verts.ensure_lookup_table()
band=[v for v in bm.verts if abs(v.co.x)>0.045 and 1.56<v.co.z<1.64 and v.co.y>-0.03 and (v.co-C).length>0.06]
print("temple band verts:",len(band))
moves=[]
for v in band:
    p,n,i,d=bv.find_nearest(v.co)
    if p is None: continue
    dv=(Vector(p)-v.co)
    if dv.length>0.003: dv=dv.normalized()*0.003
    moves.append((v,v.co+dv))
for v,p in moves: v.co=p
print("moved:",len(moves),"  max move mm: %.2f"%(max((p-v.co).length for v,p in moves)*1000 if moves else 0))
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
