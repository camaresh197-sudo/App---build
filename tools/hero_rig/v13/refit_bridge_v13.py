# Re-fit the bridge correction table (build_v13_chin.py) so the centre profile is a straight line from the brow (z 1.556)
# to the apex (z 1.500). python3 -I refit_bridge_v13.py -- feat_v13_chin.blend
import bpy, sys, re
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
h=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(h,bpy.context.evaluated_depsgraph_get())
Z=[1.500,1.508,1.516,1.524,1.532,1.540,1.548,1.556]
def meas(z):
    loc,n,i,d=bv.ray_cast(Vector((0.0,-0.4,z)),Vector((0,1,0)))
    return loc.y*1000
m=[meas(z) for z in Z]
brow,apex=m[-1],m[0]
target=[apex+(brow-apex)*(z-1.500)/(1.556-1.500) for z in Z]
old=[0.2,-1.5,-1.0,-3.2,-5.8,-4.0,-2.6,0.0]
new=[round(o+(t-mm),2) for o,t,mm in zip(old,target,m)]
for z,mm,t,nw in zip(Z,m,target,new): print("z %.3f  meas %8.2f  target %8.2f  corr %+.2f"%(z,mm,t,nw))
src=open('build_v13_chin.py').read()
pat=re.compile(r"_cc=\[[^\]]*\]")
assert len(pat.findall(src))==1
src=pat.sub("_cc=["+", ".join("%.2f"%v for v in new)+"]",src)
open('build_v13_chin.py','w').write(src)
print("table updated")
