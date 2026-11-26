import sys, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
orig=sys.argv[sys.argv.index('--')+1]; new=sys.argv[sys.argv.index('--')+2]
bpy.ops.wm.open_mainfile(filepath=orig)
o=bpy.data.objects['head_quad']; bm=bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
tree=BVHTree.FromBMesh(bm)
bpy.ops.wm.open_mainfile(filepath=new)
n=bpy.data.objects['head_quad']
P=[n.matrix_world@v.co for v in n.data.vertices]
d=[tree.find_nearest(p)[3] for p in P]
d.sort()
print(f"DEV retopo verts {len(P)} mean_mm {sum(d)/len(d)*1000:.2f} p95_mm {d[int(len(d)*0.95)]*1000:.2f} max_mm {d[-1]*1000:.2f}")
bm.free()
