# Subdivide the large corner triangles once (W082): new vertices come from the subdivide result itself (geom_split),
# checked against the number of split edges before any re-projection. python3 -I subdivide_corners_v13.py -- in out
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']; hi=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
def corner(c): return 0.024<abs(c.x)<0.040 and 1.466<c.z<1.490 and c.y<-0.05
big=[f for f in bm.faces if corner(f.calc_center_median()) and f.calc_area()>(0.0012**2)]
edges=list({e for f in big for e in f.edges})
print("big corner faces:",len(big),"split edges:",len(edges))
res=bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=False)
new=[g for g in res['geom_split'] if isinstance(g,bmesh.types.BMVert)]
print("new verts from split:",len(new))
if len(new)!=len(edges):
    print("COUNT MISMATCH - not re-projecting"); bm.free(); sys.exit(1)
for _ in range(8):
    for v in new:
        nb=[e.other_vert(v) for e in v.link_edges]
        c=sum((n.co for n in nb),Vector())/len(nb)
        q=0.5*v.co+0.5*c
        loc,n,i,d=bv.ray_cast(Vector((q.x,-0.5,q.z)),Vector((0,1,0)))
        if loc: v.co=Vector((q.x,loc.y,q.z))
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print("head_low faces now",len(lo.data.polygons))
