# W097: smooth shading across the cranium seam: set every polygon of head_low to smooth and recalc normals.
# python3 -I smooth_seam_v13.py -- in out
import bpy, bmesh, sys
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']
flat_before=sum(1 for p in lo.data.polygons if not p.use_smooth)
for p in lo.data.polygons: p.use_smooth=True
bm=bmesh.new(); bm.from_mesh(lo.data)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
print("flat polygons before:",flat_before,"now all smooth:",len(lo.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out)
