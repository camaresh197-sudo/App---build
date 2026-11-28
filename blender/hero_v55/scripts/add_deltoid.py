import bpy, sys
from mathutils import Vector
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v37.blend")
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
cap = {}
for s in ("_r", "_l"):
    ua = eb["uarm" + s]; d = (ua.tail - ua.head).normalized()
    b = eb.new("deltoid" + s); b.head = ua.head.copy(); b.tail = ua.head + d * 0.15; b.roll = ua.roll; b.parent = eb["shoulder" + s]
    cap[s] = ua.head + Vector((0.03 if s == "_r" else -0.03, 0.0, 0.0))
bpy.ops.object.mode_set(mode='OBJECT')
for s in ("_r", "_l"):
    c = arm.pose.bones["deltoid" + s].constraints.new('COPY_ROTATION')
    c.target = arm; c.subtarget = "uarm" + s; c.target_space = 'LOCAL'; c.owner_space = 'LOCAL'; c.influence = 0.4
names = {g.name: g.index for g in body.vertex_groups}
for s in ("_r", "_l"):
    if "deltoid" + s not in names: names["deltoid" + s] = body.vertex_groups.new(name="deltoid" + s).index
moved = 0
for v in me.vertices:
    p = body.matrix_world @ v.co
    s = "_r" if p.x >= 0 else "_l"
    if p.z < 1.10 or p.z > 1.45 or abs(p.x) < 0.10: continue
    d = (p - cap[s]).length
    f = 0.55 * (1 - ss(0.05, 0.13, d))
    if f <= 0: continue
    W = {g.group: g.weight for g in v.groups if g.weight > 0}
    new = dict(W); T = 0.0
    for n in ("uarm", "shoulder", "clav"):
        w = new.get(names[n + s], 0.0); T += w * f; new[names[n + s]] = w * (1 - f)
    if T <= 0: continue
    new[names["deltoid" + s]] = new.get(names["deltoid" + s], 0.0) + T
    items = sorted(((k, w) for k, w in new.items() if w > 0.005), key=lambda kv: -kv[1])[:4]
    tot = sum(w for _, w in items)
    for g in body.vertex_groups:
        try: g.remove([v.index])
        except RuntimeError: pass
    for k, w in items: body.vertex_groups[k].add([v.index], w / tot, 'REPLACE')
    moved += 1
print("reweighted", moved, "bones", len(arm.data.bones))
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v38.blend")
print("saved v38")
