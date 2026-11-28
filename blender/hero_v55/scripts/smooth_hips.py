import bpy, sys, math
from collections import defaultdict
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v34.blend")
body = bpy.data.objects["body_gnm"]; me = body.data
vg_names = [g.name for g in body.vertex_groups]
P = [(body.matrix_world @ v.co) for v in me.vertices]
nb = defaultdict(set)
for e in me.edges: nb[e.vertices[0]].add(e.vertices[1]); nb[e.vertices[1]].add(e.vertices[0])
# region: lower belly, pelvis, groin, upper thighs. Torso/legs only (exclude arms).
def region_w(p):
    if abs(p.x) > 0.24: return 0.0
    z = p.z
    if z < 0.55 or z > 1.12: return 0.0
    w = 1.0
    if z > 0.98: w = max(0.0, (1.12 - z) / 0.14)
    if z < 0.70: w = max(0.0, (z - 0.55) / 0.15)
    return w
R = {i: region_w(P[i]) for i in range(len(P))}
reg = [i for i, w in R.items() if w > 0]
print("region verts", len(reg))
# current weights
W = [dict() for _ in me.vertices]
for v in me.vertices:
    for g in v.groups:
        if g.weight > 0: W[v.index][g.group] = g.weight
def infl_stats(label):
    c = [len(d) for d in W]
    print(label, "max influences", max(c), "verts >4:", sum(1 for x in c if x > 4))
infl_stats("before")
# bones that take part in the smoothing (hip chain + lower spine)
use = {vg_names.index(n) for n in ["pelvis","spine","spine2","hip_l","hip_r","thigh_l","thigh_r","knee_l","knee_r","root"] if n in vg_names}
iL = vg_names.index("thigh_l"); iR = vg_names.index("thigh_r"); hL = vg_names.index("hip_l"); hR = vg_names.index("hip_r")
for it in range(14):
    newW = [d.copy() for d in W]
    for i in reg:
        wgt = 0.65 * R[i]
        ns = [j for j in nb[i] if R[j] > 0 or True]
        if not ns: continue
        keys = set(W[i].keys())
        for j in ns: keys |= set(W[j].keys())
        keys = {k for k in keys if k in use}
        for k in keys:
            mean = sum(W[j].get(k, 0.0) for j in ns) / len(ns)
            cur = W[i].get(k, 0.0)
            newW[i][k] = cur * (1 - wgt) + mean * wgt
    # keep each leg's thigh weights on its own side
    for i in reg:
        x = P[i].x
        if x > 0.02:
            for k in (iL, hL): newW[i].pop(k, None)
        if x < -0.02:
            for k in (iR, hR): newW[i].pop(k, None)
    # renormalise (non-smoothed groups keep their original share)
    for i in reg:
        tot = sum(newW[i].values())
        if tot > 0: newW[i] = {k: v / tot for k, v in newW[i].items() if v / tot > 0.005}
        tot = sum(newW[i].values()); newW[i] = {k: v / tot for k, v in newW[i].items()}
    W = newW
# cap region verts at 4 influences
for i in reg:
    if len(W[i]) > 4:
        top = sorted(W[i].items(), key=lambda kv: -kv[1])[:4]; tot = sum(v for _, v in top)
        W[i] = {k: v / tot for k, v in top}
infl_stats("after")
# write back
for i in reg:
    for g in body.vertex_groups:
        try: g.remove([i])
        except RuntimeError: pass
    for k, w in W[i].items(): body.vertex_groups[k].add([i], w, 'REPLACE')
unw = sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups))
print("unweighted verts", unw)
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v35.blend")
print("saved v35")
