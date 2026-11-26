# Triangulate the n-gons in the mouth corner bands (W079) and re-run the opening fan so the interior depth returns.
# python3 -I triangulate_corners_v13.py -- in.blend out.blend
import bpy, bmesh, sys
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
def corner(c): return 0.024<abs(c.x)<0.040 and 1.466<c.z<1.490 and c.y<-0.05
ngons=[f for f in bm.faces if len(f.verts)>4 and corner(f.calc_center_median())]
print("ngons in corner bands:",len(ngons),"sizes:",[len(f.verts) for f in ngons])
bmesh.ops.triangulate(bm,faces=ngons,quad_method='BEAUTY',ngon_method='BEAUTY')
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print("triangulated; head_low faces now",len(lo.data.polygons))
