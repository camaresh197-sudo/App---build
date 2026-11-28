import bpy, sys
from collections import defaultdict
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v36.blend")
body = bpy.data.objects["body_gnm"]; me = body.data
names = {g.name: g.index for g in body.vertex_groups}
P = [body.matrix_world @ v.co for v in me.vertices]
nb = defaultdict(set)
for e in me.edges: nb[e.vertices[0]].add(e.vertices[1]); nb[e.vertices[1]].add(e.vertices[0])
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
SH = {"_r": Vector if False else None}
from mathutils import Vector
shoulder = {"_r": Vector((0.20, -0.005, 1.335)), "_l": Vector((-0.20, -0.005, 1.335))}
RAD = 0.20
use = {}
for s in ("_r", "_l"):
    use[s] = {names[n + s] for n in ("clav", "shoulder", "uarm", "chest") if n + s in names} | {names["spine2"], names["neck"]}
region = {}
for i, p in enumerate(P):
    s = "_r" if p.x >= 0 else "_l"
    if p.z < 1.0 or p.z > 1.50: continue
    d = (p - shoulder[s]).length
    if d < RAD:
        region[i] = (s, 1.0 - ss(0.10, RAD, d) * 0.6)
print("region verts", len(region))
W = [{g.group: g.weight for g in v.groups if g.weight > 0} for v in me.vertices]
def stats(label): 
    c = [len(d) for d in W]; print(label, "verts >4:", sum(1 for x in c if x > 4), "max", max(c))
stats("before")
for it in range(16):
    new = {}
    for i, (s, k) in region.items():
        ns = list(nb[i]); 
        keys = {kk for kk in set(W[i]) | {kk for j in ns for kk in W[j]} if kk in use[s]}
        d = dict(W[i]); f = 0.6 * k
        for kk in keys:
            mean = sum(W[j].get(kk, 0.0) for j in ns) / len(ns)
            d[kk] = W[i].get(kk, 0.0) * (1 - f) + mean * f
        t = sum(d.values()); new[i] = {kk: v / t for kk, v in d.items() if v / t > 0.005}
    for i, d in new.items():
        t = sum(d.values()); W[i] = {kk: v / t for kk, v in d.items()}
for i in region:
    if len(W[i]) > 4:
        top = sorted(W[i].items(), key=lambda kv: -kv[1])[:4]; t = sum(v for _, v in top); W[i] = {k: v / t for k, v in top}
stats("after")
for i in region:
    for g in body.vertex_groups:
        try: g.remove([i])
        except RuntimeError: pass
    for k, w in W[i].items(): body.vertex_groups[k].add([i], w, 'REPLACE')
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v37.blend")
print("saved v37")
