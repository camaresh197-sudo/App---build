import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v71_remesh.blend")
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
gi = {g.name: g.index for g in body.vertex_groups}
N = len(me.vertices); R = [v.co.copy() for v in me.vertices]
cr_h = arm.data.bones["corner_r"].head_local.copy(); cl_h = arm.data.bones["corner_l"].head_local.copy()
# add one jaw-parented bone per corner, placed slightly inside the corner
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones
for nm, h, sx in (("corner2_r", cr_h, -1), ("corner2_l", cl_h, 1)):
    b = eb.new(nm); b.head = h + Vector((sx * 0.004, 0, 0)); b.tail = b.head + Vector((sx * 0.008, 0, 0)); b.parent = eb["jaw"]
bpy.ops.object.mode_set(mode='OBJECT')
for nm in ("corner2_r", "corner2_l"): body.vertex_groups.new(name=nm)
gi = {g.name: g.index for g in body.vertex_groups}
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
# blend the corner-zone weights toward the jaw-parented corner family over a wider zone
blended = 0
for i in range(N):
    p = R[i]
    dr = (p - cr_h).length; dl = (p - cl_h).length
    d = min(dr, dl)
    if d > 0.016: continue
    side = "corner2_r" if dr < dl else "corner2_l"
    f = ss(0.016, 0.005, d)   # 1 close to the corner, 0 at 16 mm
    wts = {g.group: g.weight for g in me.vertices[i].groups if g.weight > 0}
    tot = sum(wts.values())
    if tot <= 0: continue
    for g in list(wts):
        if g == gi["head"]: continue
        body.vertex_groups[g].remove([i])
    keep_head = wts.get(gi["head"], 0.0)
    new = {gi["head"]: keep_head * (1 - f)}
    rest = 1.0 - new[gi["head"]]
    new[gi[side]] = rest * f + new.get(gi[side], 0.0)
    # remaining non-head share follows the original family proportions
    other = tot - keep_head
    for g, w in wts.items():
        if g == gi["head"]: continue
        new[g] = new.get(g, 0.0) + (rest * (1 - f)) * (w / other if other > 0 else 0)
    for g, w in new.items():
        if w > 1e-4: body.vertex_groups[g].add([i], w, 'REPLACE')
    blended += 1
print("blended verts", blended, "| unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v76_corner2.blend")
