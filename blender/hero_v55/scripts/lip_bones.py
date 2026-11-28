import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v52_pouch.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
gi = {g.name: g.index for g in body.vertex_groups}; H, J = gi["head"], gi["jaw"]
NPOUCH = 702; NP = len(me.polygons); N = len(me.vertices); N0 = N - 649; M = 54
ring = []
for i in range(M):
    ring.append(me.polygons[NP - NPOUCH + i].vertices[0])
assert len(set(ring)) == M and all(v < N0 for v in ring), "ring order check failed"
R = [v.co.copy() for v in me.vertices]
print("ring +x corner x mm", round(1000 * R[ring[0]].x, 1), "| index 27 x mm", round(1000 * R[ring[27]].x, 1))
# ---- 17 upper-lip points by arc length along ring indices 0..27 (over the top)
pts = [R[ring[i]] for i in range(0, 28)]
seg = [(pts[i + 1] - pts[i]).length for i in range(27)]; L = sum(seg)
def at(s):
    acc = 0.0
    for i, d in enumerate(seg):
        if acc + d >= s or i == 26: t = (s - acc) / d if d > 0 else 0; return pts[i].lerp(pts[i + 1], max(0, min(1, t)))
        acc += d
lipU = [at(L * k / 16) for k in range(17)]
cr = R[ring[0]].copy(); cl = R[ring[27]].copy()
print("upper lip arc length mm", round(1000 * L, 1), "| corner x", round(1000 * cr.x, 1), round(1000 * cl.x, 1))
# ---- bones
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones
for k, p in enumerate(lipU):
    b = eb.new("lipU_%d" % k); b.head = p; b.tail = p + Vector((0, -0.008, 0)); b.parent = eb["head"]
for nm, p, sx in (("corner_r", cr, 1), ("corner_l", cl, -1)):
    b = eb.new(nm); b.head = p; b.tail = p + Vector((sx * 0.008, 0, 0)); b.parent = eb["jaw"]
bpy.ops.object.mode_set(mode='OBJECT')
for nm in ["lipU_%d" % k for k in range(17)] + ["corner_r", "corner_l"]: body.vertex_groups.new(name=nm)
gi = {g.name: g.index for g in body.vertex_groups}
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
# ---- weights
RAD = 0.014; moved = 0; cmoved = 0
for v in me.vertices:
    p = R[v.index]
    if abs(p.x) > 0.040 or p.z < 1.47 or p.z > 1.58: continue
    h = j = 0.0
    for g in v.groups:
        if g.group == H: h = g.weight
        elif g.group == J: j = g.weight
    if h + j < 0.5: continue
    # nearest segment of the upper-lip chain
    best = None
    for k in range(16):
        a, b = lipU[k], lipU[k + 1]; ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab)))); d = (p - (a + ab * t)).length
        if best is None or d < best[0]: best = (d, k, t)
    d, k, t = best
    W = min(1.0 - ss(0.004, RAD, d), h)
    W = W * (1.0 - j)
    if W > 0.01:
        body.vertex_groups["head"].add([v.index], h - W, 'REPLACE')
        body.vertex_groups["lipU_%d" % k].add([v.index], W * (1 - t), 'ADD'); body.vertex_groups["lipU_%d" % (k + 1)].add([v.index], W * t, 'ADD'); moved += 1
    # corners (children of the jaw): take from the jaw share so total jaw-motion stays the same
    for nm, cp in (("corner_r", cr), ("corner_l", cl)):
        dc = (p - cp).length
        Wc = (1.0 - ss(0.004, 0.013, dc)) * 0.9
        cw = min(Wc, j)
        if cw > 0.01:
            jcur = next((g.weight for g in me.vertices[v.index].groups if g.group == J), 0.0)
            body.vertex_groups["jaw"].add([v.index], max(0.0, jcur - cw), 'REPLACE'); body.vertex_groups[nm].add([v.index], cw, 'REPLACE'); cmoved += 1
print("upper-lip weighted verts", moved, "| corner weighted verts", cmoved)
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)), "bones", len(arm.data.bones))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v53_lips.blend"); print("saved v53")
