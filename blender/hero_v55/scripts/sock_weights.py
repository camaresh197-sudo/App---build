import bpy, sys, math
import numpy as np
from collections import defaultdict
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v47.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
gi = {g.name: g.index for g in body.vertex_groups}; H, J = gi["head"], gi["jaw"]
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
N = len(me.vertices); R = [v.co.copy() for v in me.vertices]
sock = [False]*N; upper = [False]*N; lower = [False]*N
for v in me.vertices:
    p = v.co
    if p.z < 1.38 or p.z > 1.62: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d >= 0.012: continue
    sock[v.index] = has("mouth_sock", idx)
    upper[v.index] = has("upper_teeth_and_gums", idx)
    lower[v.index] = has("lower_teeth_and_gums", idx) or has("tongue", idx)
wh = [0.0]*N; wj = [0.0]*N
for v in me.vertices:
    for g in v.groups:
        if g.group == H: wh[v.index] = g.weight
        elif g.group == J: wj[v.index] = g.weight
tot = [wh[i] + wj[i] for i in range(N)]; j = [(wj[i] / tot[i]) if tot[i] > 1e-6 else 0.0 for i in range(N)]
nb = defaultdict(set)
for e in me.edges: nb[e.vertices[0]].add(e.vertices[1]); nb[e.vertices[1]].add(e.vertices[0])
# sock-only vertices are the unknowns; contacts with gums/teeth are fixed 0 / 1
ku = KDTree(sum(1 for i in range(N) if upper[i] and not sock[i])); kl = KDTree(sum(1 for i in range(N) if lower[i] and not sock[i]))
for i in range(N):
    if upper[i] and not sock[i]: ku.insert(R[i], i)
    if lower[i] and not sock[i]: kl.insert(R[i], i)
ku.balance(); kl.balance()
unknown = []; fixedv = {}
for i in range(N):
    if not sock[i]: continue
    if upper[i] or lower[i]: continue
    _, _, du = ku.find(R[i]); _, _, dl = kl.find(R[i])
    if min(du, dl) < 0.0025: fixedv[i] = 0.0 if du < dl else 1.0; continue
    unknown.append(i)
# sock vertices that touch a non-sock vertex keep that neighbour's weight as a boundary value (average)
bound = {}
for i in unknown:
    ext = [j[k] for k in nb[i] if not sock[k]]
    if ext: bound[i] = sum(ext) / len(ext)
print("sock verts", sum(sock), "unknown", len(unknown), "touching skin/lips", len(bound), "fixed by gum contact", len(fixedv))
def sock_edges(): return [(a, b) for a, b in ((e.vertices[0], e.vertices[1]) for e in me.edges) if sock[a] and sock[b]]
SE = sock_edges()
def jumps(jj): return sum(1 for a, b in SE if abs(jj[a] - jj[b]) > 0.5)
print("sock edges", len(SE), "| jaw-share jumps >0.5 BEFORE", jumps(j))
jn = j[:]
for i, v in fixedv.items(): jn[i] = v
for i, v in bound.items(): jn[i] = v          # initial guess at the attachment
for it in range(400):
    new = jn[:]
    for i in unknown:
        ns = [k for k in nb[i] if sock[k] or True]
        vals = [jn[k] for k in nb[i] if sock[k]]
        if i in bound: vals += [bound[i]] * 2
        if vals: new[i] = 0.5 * jn[i] + 0.5 * (sum(vals) / len(vals))
    jn = new
print("sock edges   | jaw-share jumps >0.5 AFTER ", jumps(jn))
for i in unknown + list(fixedv):
    if tot[i] > 1e-6:
        body.vertex_groups[H].add([i], tot[i] * (1 - jn[i]), 'REPLACE'); body.vertex_groups[J].add([i], tot[i] * jn[i], 'REPLACE')
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v49.blend"); print("saved v49")
