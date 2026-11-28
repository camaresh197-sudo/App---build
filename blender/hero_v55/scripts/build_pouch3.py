import bpy, sys, math, bmesh
import numpy as np
from collections import defaultdict
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v48_nosock.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
gi = {g.name: g.index for g in body.vertex_groups}; H, J = gi["head"], gi["jaw"]
# ---- low jaw hinge (B)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones["jaw"]; tl = eb.tail.copy(); eb.head = Vector((0, -0.045, 1.505)); eb.tail = tl
bpy.ops.object.mode_set(mode='OBJECT')
# ---- categories of interior parts (teeth, gums, tongue) from GNM groups
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
N = len(me.vertices); R = [v.co.copy() for v in me.vertices]; interior = [False] * N
for v in me.vertices:
    p = v.co
    if p.z < 1.38 or p.z > 1.62: continue
    _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
    if d < 0.012 and has("teeth", idx): interior[v.index] = True
iv = [R[i] for i in range(N) if interior[i]]
ys = np.array([p.y for p in iv]); xs = np.array([abs(p.x) for p in iv]); zs = np.array([p.z for p in iv])
print("interior verts", len(iv), "| y range mm", round(1000 * ys.min(), 1), round(1000 * ys.max(), 1), "| |x| max mm", round(1000 * xs.max(), 1), "| z range mm", round(1000 * zs.min(), 1), round(1000 * zs.max(), 1))
bins = np.arange(-0.150, -0.040, 0.005); cen = bins + 0.0025
ax = []; atop = []; abot = []
for b in bins:
    m = (ys >= b) & (ys < b + 0.005)
    if m.any(): ax.append(xs[m].max()); atop.append(zs[m].max()); abot.append(zs[m].min())
    else: ax.append(np.nan); atop.append(np.nan); abot.append(np.nan)
def fillnan(a):
    a = np.array(a); idx = np.arange(len(a)); ok = ~np.isnan(a); return np.interp(idx, idx[ok], a[ok])
ax = fillnan(ax); atop = fillnan(atop); abot = fillnan(abot)
def smooth_max(a, w=1): return np.array([a[max(0, i - w):i + w + 1].max() for i in range(len(a))])
def smooth_min(a, w=1): return np.array([a[max(0, i - w):i + w + 1].min() for i in range(len(a))])
ax = smooth_max(ax); atop = smooth_max(atop); abot = smooth_min(abot)
MARG = 0.003; YB = -0.060
def env(y):  # half-width, top z, bottom z at depth y
    return (min(0.043, max(0.030, float(np.interp(y, cen, ax)) + MARG)) * (1.0 if y > YB - 0.0 else 1.0), max(1.530, float(np.interp(y, cen, atop)) + MARG), min(1.472, float(np.interp(y, cen, abot)) - MARG))
for y in (-0.140, -0.130, -0.120, -0.110, -0.100, -0.090, -0.080, -0.070): print("envelope at y", y, [round(1000 * c, 1) for c in env(y)])
# ---- main skin component and open loops
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
parent = list(range(len(bm.verts)))
def f(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for e in bm.edges: parent[f(e.verts[0].index)] = f(e.verts[1].index)
cnt = defaultdict(int)
for v in bm.verts: cnt[f(v.index)] += 1
main = max(cnt, key=cnt.get)
def zone(e): return 1.44 < (e.verts[0].co.z + e.verts[1].co.z) / 2 < 1.58 and abs((e.verts[0].co.x + e.verts[1].co.x) / 2) < 0.07
be = [e for e in bm.edges if e.is_boundary and zone(e) and f(e.verts[0].index) == main]
rs = set(be); seen = set(); loops = []
for e in be:
    if e in seen: continue
    st = [e]; comp = []
    while st:
        x = st.pop()
        if x in seen: continue
        seen.add(x); comp.append(x)
        for v in x.verts:
            for ee in v.link_edges:
                if ee in rs and ee not in seen: st.append(ee)
    loops.append(comp)
info = []
for c in loops:
    vv = {v for x in c for v in x.verts}; xs_ = [v.co.x for v in vv]; zs_ = [v.co.z for v in vv]
    info.append((len(c), round(1000 * min(xs_), 1), round(1000 * max(xs_), 1), round(1000 * min(zs_), 1), round(1000 * max(zs_), 1)))
print("skin open loops (edges, xmin, xmax, zmin, zmax mm):", info)
lip = max(loops, key=lambda c: len(c) if all(abs(v.co.z - 1.504) < 0.010 and abs(v.co.x) < 0.03 for x in c for v in x.verts) else 0)
fill = [c for c in loops if c is not lip and len(c) in (24, 8) and all(1.48 < v.co.z < 1.53 and abs(v.co.x) > 0.014 for x in c for v in x.verts)]
print("lip ring edges", len(lip), "| side loops to seal", [len(c) for c in fill])
res = bmesh.ops.holes_fill(bm, edges=[e for c in fill for e in c], sides=30)
tri = bmesh.ops.triangulate(bm, faces=list(res["faces"]))["faces"]
print("sealed side openings with", len(tri), "triangles")
# ---- order the lip ring starting at +x corner, heading over the top
adj = defaultdict(list)
for e in lip: a, b = e.verts; adj[a].append(b); adj[b].append(a)
start = max(adj, key=lambda v: v.co.x); order = [start]; prev = None; cur = start
nxt = max(adj[cur], key=lambda v: v.co.z); 
while True:
    order.append(nxt); prev, cur = cur, nxt
    cands = [v for v in adj[cur] if v is not prev]
    if not cands or cands[0] is start: break
    nxt = cands[0]
    if len(order) > len(lip) + 2: break
if order[-1] is start: order.pop()
M = len(order); print("ordered ring vertices", M, "of", len(lip))
# jaw share of ring vertices (lips: upper 0, lower 1, corners partial) from current weights
jw = []
for v in order:
    wh = wj = 0.0
    for g in me.vertices[v.index].groups:
        if g.group == H: wh = g.weight
        elif g.group == J: wj = g.weight
    jw.append(wj / (wh + wj) if wh + wj > 1e-6 else 0.0)
print("ring jaw share: upper half mean", round(sum(jw[1:M//2]) / max(1, M//2 - 1), 2), "lower half mean", round(sum(jw[M//2 + 1:]) / max(1, M - M//2 - 1), 2))
from mathutils.bvhtree import BVHTree
tris = []
for p in me.polygons:
    if any(interior[v] for v in p.vertices): continue
    vs = list(p.vertices); tris.append(tuple(vs[:3]))
    if len(vs) == 4: tris.append((vs[0], vs[2], vs[3]))
skin_bvh = BVHTree.FromPolygons(R, tris)
SKIN_MARGIN = 0.003; pushed = 0
# ---- loft
K = 12; ZC = 1.5035; NSUP = 2.8
def ss(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
dl = bm.verts.layers.deform.verify(); shp = list(bm.verts.layers.shape.values())
col = bm.verts.layers.float_color.get("Col")
DARK = (0.30, 0.06, 0.07, 1.0)
rings = [order]; new_verts = []
def make_vert(co, j):
    v = bm.verts.new(co)
    for l in shp: v[l] = co.copy()
    v[dl][H] = 1.0 - j; v[dl][J] = j
    if col is not None: v[col] = DARK
    new_verts.append(v); return v
for k in range(1, K + 1):
    s = ss(k / 3.0); u = ss(max(0, k - 2) / (K - 2)); ring = []
    for i, pv in enumerate(order):
        p = pv.co; th = 2 * math.pi * i / M
        yk = (p.y - 0.0015 * s) * (1 - u) + YB * u
        a, top, bot = env(yk); c, sn = math.cos(th), math.sin(th)
        ex = a * math.copysign(abs(c) ** (2 / NSUP), c)
        ez = ZC + ((top - ZC) if sn >= 0 else (ZC - bot)) * math.copysign(abs(sn) ** (2 / NSUP), sn)
        E = Vector((ex, yk, ez)); P = p.lerp(E, s); P.y = yk
        hit, _n, _i, _d = skin_bvh.ray_cast(Vector((P.x, -0.03, P.z)), Vector((0, -1, 0)), 0.25)
        if hit is not None and P.y < hit.y + SKIN_MARGIN: P.y = hit.y + SKIN_MARGIN; pushed += 1
        ring.append(make_vert(P, jw[i]))
    rings.append(ring)
centre = make_vert(Vector((0, YB - 0.004, ZC)), 0.5)
faces = []
for k in range(K):
    A = rings[k]; B = rings[k + 1]
    for i in range(M):
        j2 = (i + 1) % M
        faces.append(bm.faces.new((A[i], A[j2], B[j2], B[i])))
last = rings[K]
for i in range(M): faces.append(bm.faces.new((last[i], last[(i + 1) % M], centre)))
# face normals toward the pouch axis
fixed = 0
for fc in faces:
    cc = fc.calc_center_median(); axis = Vector((0, cc.y, ZC)); toward = axis - cc
    if fc.normal.dot(toward) < 0: fc.normal_flip(); fixed += 1
    fc.smooth = True
print("pouch vertices pushed back behind the skin:", pushed)
print("pouch faces", len(faces), "flipped", fixed, "| vertices added", len(new_verts))
bm.to_mesh(me); bm.free(); me.update()
print("unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v52_pouch.blend"); print("saved v52")
