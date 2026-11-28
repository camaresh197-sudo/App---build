import bpy, sys, math
from mathutils import Vector
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v35.blend")
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
# ---- bones
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
spec = {}
for s in ("_l", "_r"):
    th = eb["thigh" + s]; d = (th.tail - th.head).normalized()
    hip = th.head.copy()
    h1 = eb.new("hipflex" + s); h1.head = hip; h1.tail = hip + d * 0.20; h1.roll = th.roll; h1.parent = eb["pelvis"]
    g_head = hip + Vector((0, 0.07, 0.0))
    g1 = eb.new("glute" + s); g1.head = g_head; g1.tail = g_head + d * 0.20; g1.roll = th.roll; g1.parent = eb["pelvis"]
    spec[s] = (hip.copy(), g_head.copy())
bpy.ops.object.mode_set(mode='OBJECT')
# ---- constraints: copy thigh rotation (local) at a fraction
for s in ("_l", "_r"):
    for name, infl in (("hipflex" + s, 0.5), ("glute" + s, 0.35)):
        c = arm.pose.bones[name].constraints.new('COPY_ROTATION')
        c.target = arm; c.subtarget = "thigh" + s; c.target_space = 'LOCAL'; c.owner_space = 'LOCAL'; c.influence = infl
# ---- weights
names = {g.name: g.index for g in body.vertex_groups}
for n in ("hipflex_l", "hipflex_r", "glute_l", "glute_r"):
    if n not in names: names[n] = body.vertex_groups.new(name=n).index
moved = 0
for v in me.vertices:
    p = v.co
    if p.z < 0.60 or p.z > 1.12 or abs(p.x) > 0.26: continue
    s = "_r" if p.x >= 0 else "_l"
    hip, gh = spec[s]
    W = {g.group: g.weight for g in v.groups}
    new = dict(W)
    # hip flexion helper: takes a share of the thigh weight near the hip joint
    d = (p - hip).length
    fh = 0.5 * (1 - ss(0.10, 0.26, d))
    tw = W.get(names["thigh" + s], 0.0)
    if fh > 0 and tw > 0:
        new[names["thigh" + s]] = tw * (1 - fh); new[names["hipflex" + s]] = new.get(names["hipflex" + s], 0.0) + tw * fh
    # glute helper: posterior verts near the buttock take a share of pelvis + hip + thigh weight
    dg = (p - gh).length
    fg = 0.4 * (1 - ss(0.08, 0.20, dg)) * ss(0.015, 0.06, p.y)
    if fg > 0:
        T = 0.0
        for n in ("pelvis", "hip" + s, "thigh" + s):
            w = new.get(names[n], 0.0); T += w * fg; new[names[n]] = w * (1 - fg)
        new[names["glute" + s]] = new.get(names["glute" + s], 0.0) + T
    if new != W:
        # cap at 4 influences, renormalise
        items = sorted(((k, w) for k, w in new.items() if w > 0.005), key=lambda kv: -kv[1])[:4]
        tot = sum(w for _, w in items); items = [(k, w / tot) for k, w in items]
        for g in body.vertex_groups:
            try: g.remove([v.index])
            except RuntimeError: pass
        for k, w in items: body.vertex_groups[k].add([v.index], w, 'REPLACE')
        moved += 1
print("reweighted verts", moved)
print("bones now", len(arm.data.bones), "helpers", [b.name for b in arm.data.bones if b.name.startswith(("hipflex", "glute"))])
unw = sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups))
print("unweighted verts", unw)
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v36.blend")
print("saved v36")
