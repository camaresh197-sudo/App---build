import bpy, sys, math, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
out = sys.argv[sys.argv.index("--")+2]
arm = next(o for o in bpy.data.objects if o.type=='ARMATURE')
mat = bpy.data.materials["BrowHairMat"]
coll = bpy.data.objects["brow_l_0"].users_collection[0]
for o in [o for o in bpy.data.objects if o.name.startswith("brow_")]:
    m = o.data; bpy.data.objects.remove(o, do_unlink=True)
    if m.users == 0: bpy.data.meshes.remove(m)
# skin to ray-cast against (rest shape)
head = bpy.data.objects["head_12"]
src = head.data.shape_keys.key_blocks[0].data if head.data.shape_keys else head.data.vertices
bm0 = bmesh.new(); bm0.from_mesh(head.data)
for i, v in enumerate(bm0.verts): v.co = head.matrix_world @ src[i].co
bvh = BVHTree.FromBMesh(bm0)
MID = 0.085
# brow centre line (left brow), inner to tail, in x,z; y comes from the skin
arc = [(0.078,1.637), (0.062,1.642), (0.044,1.645), (0.026,1.641), (0.010,1.631), (-0.002,1.619)]
def pt(u):
    n = len(arc)-1; i = min(int(u*n), n-1); f = u*n - i
    return (arc[i][0]+(arc[i+1][0]-arc[i][0])*f, arc[i][1]+(arc[i+1][1]-arc[i][1])*f)
def half_h(u):                      # soft taper: full at the inner end, thin at the tail
    return 0.0075*(1-u)**0.9 + 0.0012
def build(side):
    NU, NV = 28, 7
    bm = bmesh.new(); grid = []
    for i in range(NU+1):
        u = i/NU; x, z = pt(u); h = half_h(u)
        # direction across the brow (perpendicular to the arc in x,z)
        x2, z2 = pt(min(u+0.02,1)); x1, z1 = pt(max(u-0.02,0))
        tx, tz = x2-x1, z2-z1; L = math.hypot(tx, tz) or 1
        nx, nz = -tz/L, tx/L
        row = []
        for j in range(NV+1):
            v = -1 + 2*j/NV
            px, pz = x + nx*h*v, z + nz*h*v
            if side == "r": px = 2*MID - px
            hit = bvh.ray_cast(Vector((px, -0.6, pz)), Vector((0,1,0)))
            y = hit[0].y if hit[0] else -0.14
            y -= 0.0015 + 0.0025*(1-v*v)*(1-0.6*u)      # slightly proud, rounded across its height
            row.append(bm.verts.new((px, y, pz)))
        grid.append(row)
    for i in range(NU):
        for j in range(NV):
            bm.faces.new([grid[i][j], grid[i+1][j], grid[i+1][j+1], grid[i][j+1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("brow_%s" % side); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("brow_%s_0" % side, me); coll.objects.link(o); o.parent = arm
    o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    vg = o.vertex_groups.new(name="head"); vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    sd = o.modifiers.new("Subsurf", "SUBSURF"); sd.levels = 1; sd.render_levels = 1
    md = o.modifiers.new("Armature", "ARMATURE"); md.object = arm
    return o
l = build("l"); r = build("r")
print("BROW faces", len(l.data.polygons), len(r.data.polygons))
bpy.ops.wm.save_mainfile(filepath=out); print("SAVED", out)
