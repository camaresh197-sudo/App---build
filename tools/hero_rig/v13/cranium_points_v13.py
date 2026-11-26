# Step 1 of the cranium retopo (W085): place a radial dome of rings over the cranium on the high-poly skin and mark them.
# Rings: polar angle from the crown pole down to the brow/temple; spokes around. Nothing is built into the mesh.
# python3 -I cranium_points_v13.py -- in.blend out.blend
import bpy, math, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
C=Vector((0.0,-0.02,1.58))                  # cranium centre (post-scale)
A,B,Cz=0.088,0.112,0.115                     # half-axes: width, depth, height of the cranium ellipsoid
RINGS=[12,22,32,42,52,62]                    # polar angles (deg) from the crown pole
SPOKES=16
mat=bpy.data.materials.new('craniummark'); mat.diffuse_color=(0.2,0.8,1.0,1)
pts=[]
for th_deg in RINGS:
    th=math.radians(th_deg)
    row=[]
    for k in range(SPOKES):
        ph=2*math.pi*k/SPOKES
        d=Vector((A*math.sin(th)*math.cos(ph), B*math.sin(th)*math.sin(ph), Cz*math.cos(th))).normalized()
        loc,n,i,dd=bv.ray_cast(C,d)
        row.append(loc if loc else None)
    pts.append(row)
n_ok=sum(1 for r in pts for p in r if p is not None)
print("ring points on skin:",n_ok,"of",len(RINGS)*SPOKES)
for r in pts:
    for p in r:
        if p is None: continue
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=6,radius=0.0009,location=p)
        o=bpy.context.active_object; o.name='craniumpt'; o.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=out)
