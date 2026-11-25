# Scale every mesh in feat_v13_chin.blend about the chin base: python3 -I scale_v13.py -- <scale> <out.blend>
# 6.5-heads-tall hero: scale 0.907 (user decision 2026-11-25; 1.674 m / 0.284 m = 5.9 heads before).
import bpy, sys
from mathutils import Vector
S=float(sys.argv[-2]); out=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath="feat_v13_chin.blend")
pivot=Vector((0.0,-0.02,1.674))      # crown: standing height stays 1.674 m, so the figure is exactly 1.674/head heads tall
for o in bpy.data.objects:
    if o.type!='MESH': continue
    M=o.matrix_world.copy()
    for v in o.data.vertices:
        v.co=pivot+S*((M@v.co)-pivot)
    o.matrix_world.identity()
    o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
o=bpy.data.objects['head_quad']; vs=[v.co for v in o.data.vertices]
zs=[p.z for p in vs]; xs=[abs(p.x) for p in vs]
print("crown-chin", round(max(zs)-min(zs),3), "width", round(2*max(xs),3), "crown z", round(max(zs),3), "chin z", round(min(zs),3))
