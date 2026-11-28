import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v71_remesh.blend")
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
gi = {g.name: g.index for g in body.vertex_groups}
N = len(me.vertices); R = [v.co.copy() for v in me.vertices]
CR, CL = gi["corner_r"], gi["corner_l"]
cornerset = {CR, CL}
# corner-zone vertices: within 7 mm of a corner bone head
cb = {"corner_r": arm.data.bones["corner_r"].head_local, "corner_l": arm.data.bones["corner_l"].head_local}
moved = 0
for i in range(N):
    p = R[i]
    dr = (p - cb["corner_r"]).length; dl = (p - cb["corner_l"]).length
    if min(dr, dl) > 0.009: continue
    cn = CR if dr < dl else CL
    wts = {g.group: g.weight for g in me.vertices[i].groups if g.weight > 0}
    tot = sum(wts.values())
    if tot <= 0: continue
    # give the corner bone all of the lip and jaw share in this zone
    for g in list(wts):
        if g in (gi.get("head"),): continue
        body.vertex_groups[g].remove([i])
    body.vertex_groups[cn].add([i], 1.0, 'REPLACE')
    moved += 1
print("corner-zone verts reassigned to one corner bone:", moved)
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v75_corner.blend")
