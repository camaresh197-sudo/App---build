import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v33.blend")
body = bpy.data.objects["body_gnm"]; arm = bpy.data.objects["character_rig"]
Z0, Z1 = 1.40, 1.46
hg = body.vertex_groups["head"]
changed = 0
for v in body.data.vertices:
    z = (body.matrix_world @ v.co).z
    if z < Z0: continue
    t = 1.0 if z >= Z1 else (z - Z0) / (Z1 - Z0)
    t = t * t * (3 - 2 * t)
    cur = {g.group: g.weight for g in v.groups}
    head_old = cur.get(hg.index, 0.0)
    for gi, w in cur.items():
        if gi != hg.index: body.vertex_groups[gi].add([v.index], w * (1 - t), 'REPLACE')
    body.vertex_groups[hg.index].add([v.index], head_old * (1 - t) + t, 'REPLACE')
    changed += 1
# remove tiny weights at rigid head verts
for v in body.data.vertices:
    z = (body.matrix_world @ v.co).z
    if z >= Z1:
        for g in list(v.groups):
            if g.group != hg.index: body.vertex_groups[g.group].remove([v.index])
print("head weights changed on", changed, "verts")
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v34.blend")
print("saved v34")
