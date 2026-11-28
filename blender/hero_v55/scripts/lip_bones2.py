import bpy, sys, math
from collections import defaultdict
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v53_lips.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
NPOUCH = 702; NP = len(me.polygons); N = len(me.vertices); N0 = N - 649; M = 54
ring = [me.polygons[NP - NPOUCH + i].vertices[0] for i in range(M)]
R = [v.co.copy() for v in me.vertices]
order = [ring[i % M] for i in range(M, M // 2 - 1, -1)]      # +x corner -> -x corner along the lower half
pts = [R[i] for i in order]; seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]; L = sum(seg)
def at(s):
    acc = 0.0
    for i, d in enumerate(seg):
        if acc + d >= s or i == len(seg) - 1: t = (s - acc) / d if d > 0 else 0; return pts[i].lerp(pts[i + 1], max(0, min(1, t)))
        acc += d
lipL = [at(L * k / 16) for k in range(17)]
print("lower lip arc length mm", round(1000 * L, 1), "| ends x mm", round(1000 * lipL[0].x, 1), round(1000 * lipL[16].x, 1))
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones
for k, p in enumerate(lipL):
    b = eb.new("lipL_%d" % k); b.head = p; b.tail = p + Vector((0, -0.008, 0)); b.parent = eb["jaw"]
bpy.ops.object.mode_set(mode='OBJECT')
for k in range(17): body.vertex_groups.new(name="lipL_%d" % k)
gi = {g.name: g.index for g in body.vertex_groups}; J = gi["jaw"]
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
RAD = 0.014; moved = 0
for v in me.vertices:
    if v.index >= N0: continue
    p = R[v.index]
    if abs(p.x) > 0.040 or p.z < 1.44 or p.z > 1.55: continue
    jcur = next((g.weight for g in v.groups if g.group == J), 0.0)
    if jcur < 0.01: continue
    best = None
    for k in range(16):
        a, b = lipL[k], lipL[k + 1]; ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab)))); d = (p - (a + ab * t)).length
        if best is None or d < best[0]: best = (d, k, t)
    d, k, t = best
    W = min(1.0 - ss(0.004, RAD, d), jcur)
    if W > 0.01:
        body.vertex_groups["jaw"].add([v.index], jcur - W, 'REPLACE')
        body.vertex_groups["lipL_%d" % k].add([v.index], W * (1 - t), 'ADD'); body.vertex_groups["lipL_%d" % (k + 1)].add([v.index], W * t, 'ADD'); moved += 1
print("lower-lip weighted verts", moved, "| bones", len(arm.data.bones), "| unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v54_lower.blend"); print("saved v54")
# ---- smoothing of lip-bone weights over skin neighbours
LIPG = [gi[n] for n in gi if n.startswith(("lipU_", "lipL_", "corner_"))]
HEADI, JAWI = gi["head"], gi["jaw"]
nb = defaultdict(set)
for e in me.edges:
    a, b = e.vertices
    if a < N0 and b < N0: nb[a].add(b); nb[b].add(a)
region = [i for i in range(N0) if abs(R[i].x) < 0.050 and 1.44 < R[i].z < 1.56]
Wt = {i: {g.group: g.weight for g in me.vertices[i].groups if g.weight > 0} for i in range(N0)}
for it in range(3):
    new = {}
    for i in region:
        ns = [k for k in nb[i] if k in Wt]
        if not ns: continue
        d = dict(Wt[i])
        for g in LIPG:
            mean = sum(Wt[k].get(g, 0.0) for k in ns) / len(ns); cur = Wt[i].get(g, 0.0); d[g] = 0.5 * cur + 0.5 * mean
        lip_total = sum(d.get(g, 0.0) for g in LIPG); rest_old = sum(w for g, w in Wt[i].items() if g not in LIPG)
        rest_new = max(0.0, 1.0 - lip_total)
        if rest_old > 1e-6:
            for g in list(d):
                if g not in LIPG: d[g] = Wt[i][g] * rest_new / rest_old
        elif rest_new > 1e-6:
            d[HEADI] = d.get(HEADI, 0.0) + rest_new
        new[i] = d
    for i, d in new.items(): Wt[i] = d
for i in region:
    for g in body.vertex_groups:
        try: g.remove([i])
        except RuntimeError: pass
    tot = sum(Wt[i].values())
    for gidx, w in Wt[i].items():
        if w > 0.002: body.vertex_groups[gidx].add([i], w / tot, 'REPLACE')
print("smoothed lip weights on", len(region), "verts | unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v55_lips_smooth.blend"); print("saved v55")
