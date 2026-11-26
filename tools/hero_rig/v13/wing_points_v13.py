# Place the alar rim points for one nostril and mark them on the retopo head (check before building).
# python3 -I wing_points_v13.py -- in.blend out.blend   (SIDE env: nostril_l = +x, nostril_r = -x)
import bpy, bmesh, math, sys, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
SIDE=os.environ.get('V13_SIDE','nostril_l'); SGN=1.0 if SIDE=='nostril_l' else -1.0
CX,CZ=0.0083*SGN,1.5089                 # nostril centre (measured world centre, W065)
SHIFT=0.0040*SGN                        # the wing sits outboard of the opening
A,B=0.0070,0.0060                       # alar rim half-axes (x outward, z)
N=24
pts=[]
for k in range(N):
    t=2*math.pi*k/N
    x=CX+SHIFT+A*math.cos(t)*SGN
    z=CZ+B*math.sin(t)
    if abs(x)<0.0045: continue          # keep the wing clear of the midline
    loc,n,i,d=bv.ray_cast(Vector((x,-0.5,z)),Vector((0,1,0)))
    if loc is None: continue
    pts.append(Vector((x,loc.y,z)))
print("alar points:",len(pts))
mat=bpy.data.materials.new('wingmark'); mat.diffuse_color=(1.0,0.2,0.2,1)
for p in pts:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=6,radius=0.00045,location=p)
    o=bpy.context.active_object; o.name='wingpt'; o.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=out)
