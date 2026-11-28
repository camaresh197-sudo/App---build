import bpy, sys, math
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v71_remesh.blend")
body = bpy.data.objects["body_gnm"]; me = body.data
R = [v.co.copy() for v in me.vertices]
ec = defaultdict(int)
for p in me.polygons:
    vs = list(p.vertices)
    for a in range(len(vs)): ec[tuple(sorted((vs[a], vs[(a+1) % len(vs)])))] += 1
bnd = [k for k, c in ec.items() if c == 1]
bv = sorted({v for k in bnd for v in k})
print("boundary edges", len(bnd), "boundary verts", len(bv))
# distance of each boundary vertex to the nearest face that is NOT on the patch (skin reference)
nonpatch = [p for p in me.polygons if p.index < len(me.polygons) - 1131]
tris = []
for p in nonpatch:
    vs = list(p.vertices); tris.append(tuple(vs[:3]))
    if len(vs) == 4: tris.append((vs[0], vs[2], vs[3]))
bvh = BVHTree.FromPolygons(R, tris)
gaps = []
for v in bv:
    hit = bvh.find_nearest(R[v])
    if hit[0] is not None: gaps.append(hit[3] * 1000)
gaps.sort()
print("border-to-skin gap mm: median", round(gaps[len(gaps)//2], 2), "p90", round(gaps[int(len(gaps)*0.9)], 2), "max", round(gaps[-1], 2))
