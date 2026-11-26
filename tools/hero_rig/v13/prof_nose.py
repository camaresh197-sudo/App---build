# nose centre-line profile: forward y per 4 mm of height, with the slope; a straight bridge has d rising smoothly to the tip
import bpy,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
h=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(h,bpy.context.evaluated_depsgraph_get())
prev=None
for k in range(0,21):
    z=1.560-0.004*k
    loc,n,i,d=bv.ray_cast(Vector((0.0,-0.4,z)),Vector((0,1,0)))
    y=loc.y*1000
    print(f"z={z:.3f} y={y:7.2f}"+(f"  d={y-prev:+.2f}" if prev is not None else "")); prev=y
