import bpy, sys, math, bmesh, json
import numpy as np
from collections import defaultdict
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
D = sys.argv[-1]
CORNER_FRAC = 0.93; TAPER0 = 0.014
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v42.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
NEWSET = set()
def cats(mesh):
    n = len(mesh.vertices); c = {k: [False] * n for k in ("U", "L", "TU", "TL", "sock", "interior", "teeth")}
    for v in mesh.vertices:
        p = v.co
        if p.z < 1.38 or p.z > 1.62: continue
        if v.index in NEWSET: continue
        _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
        if d >= 0.012: continue
        i = v.index
        if i in NEWSET: continue
        c["U"][i] = has("upper_lip", idx); c["L"][i] = has("lower_lip", idx)
        c["TU"][i] = has("upper_teeth_and_gums", idx); c["TL"][i] = has("lower_teeth_and_gums", idx) or has("tongue", idx)
        c["sock"][i] = has("mouth_sock", idx); c["teeth"][i] = has("teeth", idx)
        c["interior"][i] = any(has(nm, idx) for nm in ("teeth", "gums", "tongue", "upper_teeth_and_gums", "lower_teeth_and_gums"))
    return c
def jshare(mesh, H, J):
    n = len(mesh.vertices); wh = [0.0] * n; wj = [0.0] * n
    for v in mesh.vertices:
        for g in v.groups:
            if g.group == H: wh[v.index] = g.weight
            elif g.group == J: wj[v.index] = g.weight
    tot = [wh[i] + wj[i] for i in range(n)]
    return tot, [(wj[i] / tot[i]) if tot[i] > 1e-6 else 0.0 for i in range(n)]
gi = {g.name: g.index for g in body.vertex_groups}; H, J = gi["head"], gi["jaw"]
# ================= A') re-mesh the mouth region
C = cats(me); N = len(me.vertices); R = [v.co.copy() for v in me.vertices]
tot, j = jshare(me, H, J)
tris = []
for p in me.polygons:
    vs = list(p.vertices)
    if any(C["interior"][v] or C["sock"][v] for v in vs): continue
    tris.append(tuple(vs[:3]))
    if len(vs) == 4: tris.append((vs[0], vs[2], vs[3]))
hf = BVHTree.FromPolygons(R, tris)
def hfy(x, z, default):
    hit = hf.ray_cast(Vector((x, -0.03, z)), Vector((0, -1, 0)), 0.25)[0]
    return hit.y if hit is not None else default
sx = []; sz = []
for p in me.polygons:
    vs = list(p.vertices)
    if any(C["U"][v] for v in vs) and any(C["L"][v] for v in vs):
        c = sum((R[v] for v in vs), Vector()) / len(vs)
        if abs(c.x) < 0.027: sx.append(c.x); sz.append(c.z)
coef = np.polyfit(sx, sz, 2)
def zseam(x): return float(np.polyval(coef, x))
print("A') seam fit from", len(sx), "seam faces: z at x=0", round(1000 * zseam(0), 2), "mm, at x=0.025", round(1000 * zseam(0.025), 2), "mm")
ZC = 1.505; BX = 0.038; BZ = 0.036; X0 = 0.0265; KR = 14
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
interior_v = {v for v in bm.verts if C["interior"][v.index]}
jold = {v: j[v.index] for v in bm.verts}
def in_ell(c): return (c.x / BX) ** 2 + ((c.z - ZC) / BZ) ** 2 < 1.0 and c.y < -0.09
dead = [f for f in bm.faces if not any(v in interior_v for v in f.verts) and (all(C["sock"][v.index] for v in f.verts) or in_ell(f.calc_center_median()))]
bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.edges.ensure_lookup_table()
def nearish(e):
    mx = (e.verts[0].co.x + e.verts[1].co.x) / 2; mz = (e.verts[0].co.z + e.verts[1].co.z) / 2; my = (e.verts[0].co.y + e.verts[1].co.y) / 2
    r = (mx / BX) ** 2 + ((mz - ZC) / BZ) ** 2
    return 0.6 < r < 1.8 and my < -0.09
be = [e for e in bm.edges if e.is_boundary and nearish(e) and e.verts[0] not in interior_v and e.verts[1] not in interior_v]
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
loop = max(loops, key=len)
print("A') faces deleted", len(dead), "| boundary loops", sorted(len(c) for c in loops), "-> using", len(loop))
bverts = list({v for e in loop for v in e.verts})
phi = lambda v: math.atan2((v.co.z - ZC) / BZ, v.co.x / BX) % (2 * math.pi)
bverts.sort(key=phi); Nb = len(bverts)
ekeys = {tuple(sorted((e.verts[0].index, e.verts[1].index))) for e in loop}
adjok = sum(1 for i in range(Nb) if tuple(sorted((bverts[i].index, bverts[(i + 1) % Nb].index))) in ekeys)
print("A') boundary vertices", Nb, "| consecutive pairs that are real edges", adjok, "of", Nb)
i0 = min(range(Nb), key=lambda i: min(phi(bverts[i]), 2 * math.pi - phi(bverts[i])))
order_b = bverts[i0:] + bverts[:i0]
ic = min(range(Nb), key=lambda i: abs(phi(order_b[i]) - math.pi) if phi(order_b[i]) > 0.5 else 9)
if phi(order_b[1]) > math.pi:   # ensure increasing angle
    order_b = [order_b[0]] + order_b[:0:-1]; ic = min(range(Nb), key=lambda i: abs(phi(order_b[i]) - math.pi) if phi(order_b[i]) > 0.5 else 9)
dl_ = bm.verts.layers.deform.verify(); shp = list(bm.verts.layers.shape.values()); col = bm.verts.layers.float_color.get("Col")
PINK = (0.72, 0.52, 0.52, 1.0); GREY = (0.62, 0.62, 0.62, 1.0)
newv = []
def mk(co, jv, cc):
    v = bm.verts.new(co)
    for l in shp: v[l] = co.copy()
    v[dl_][H] = 1.0 - jv; v[dl_][J] = jv
    if col is not None: v[col] = cc
    newv.append(v); return v
ring0 = []; xz0 = []
for i in range(Nb):
    if i <= ic: x = X0 * (1 - 2 * i / ic)
    else: x = -X0 + 2 * X0 * (i - ic) / (Nb - ic)
    z = zseam(x); y = hfy(x, z, -0.143); xz0.append((x, z))
    if i == 0 or i == ic:
        ring0.append(mk(Vector((x, y, z)), 0.5, PINK))
    else:
        ring0.append(mk(Vector((x, y, z)), 0.0 if i < ic else 1.0, PINK))
rings = [ring0]
for k in range(1, KR):
    t = (k / KR) ** 1.5; ring = []
    for i in range(Nb):
        b = order_b[i]; x0, z0 = xz0[i]
        x = x0 + (b.co.x - x0) * t; z = z0 + (b.co.z - z0) * t
        y = hfy(x, z, ring0[i].co.y + (b.co.y - ring0[i].co.y) * t)
        j0 = 0.5 if i in (0, ic) else (0.0 if i < ic else 1.0)
        jv = j0 + (jold[b] - j0) * t
        sc_ = ss(0.0, 0.35, t)
        cc = tuple(PINK[m_] * (1 - sc_) + GREY[m_] * sc_ for m_ in range(4))
        ring.append(mk(Vector((x, y, z)), jv, cc))
    rings.append(ring)
rings.append(order_b)
pf = []
for k in range(KR):
    A_ = rings[k]; B_ = rings[k + 1]
    for i in range(Nb):
        f_ = bm.faces.new((A_[i], A_[(i + 1) % Nb], B_[(i + 1) % Nb], B_[i]))
        if f_.normal.y > 0: f_.normal_flip()
        f_.smooth = True; pf.append(f_)
bm.verts.index_update()
RING0_IDX = [v.index for v in ring0]; NEWSET = {v.index for v in newv}
print("A') patch: ring0 vertices", Nb, "corner index", ic, "| new verts", len(newv), "| new faces", len(pf), "| rings", KR)
bm.to_mesh(me); bm.free(); me.update()
# ================= B) remove the old lining sheet
C = cats(me); bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
dead = [f for f in bm.faces if all(C["sock"][v.index] for v in f.verts)]
bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(me); bm.free(); me.update()
print("B) old lining faces removed", len(dead), "| mesh verts now", len(me.vertices))
# ================= C) jaw hinge (low) and the new lining pouch
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones["jaw"]; tl_ = eb.tail.copy(); eb.head = Vector((0, -0.045, 1.505)); eb.tail = tl_
bpy.ops.object.mode_set(mode='OBJECT')
C = cats(me); N = len(me.vertices); R = [v.co.copy() for v in me.vertices]
iv = [R[i] for i in range(N) if C["teeth"][i] and abs(R[i].x) < 0.1]
ys = np.array([p.y for p in iv]); xs = np.array([abs(p.x) for p in iv]); zs = np.array([p.z for p in iv])
bins = np.arange(-0.150, -0.040, 0.005); cen = bins + 0.0025; ax = []; atop = []; abot = []
for b in bins:
    m = (ys >= b) & (ys < b + 0.005)
    if m.any(): ax.append(xs[m].max()); atop.append(zs[m].max()); abot.append(zs[m].min())
    else: ax.append(np.nan); atop.append(np.nan); abot.append(np.nan)
def fillnan(a):
    a = np.array(a); idx = np.arange(len(a)); ok = ~np.isnan(a); return np.interp(idx, idx[ok], a[ok])
ax = fillnan(ax); atop = fillnan(atop); abot = fillnan(abot)
smx = lambda a, w=1: np.array([a[max(0, i - w):i + w + 1].max() for i in range(len(a))]); smn = lambda a, w=1: np.array([a[max(0, i - w):i + w + 1].min() for i in range(len(a))])
ax = smx(ax); atop = smx(atop); abot = smn(abot); MARG = 0.003; YB = -0.060
def env(y): return (min(0.043, max(0.030, float(np.interp(y, cen, ax)) + MARG)), max(1.530, float(np.interp(y, cen, atop)) + MARG), min(1.472, float(np.interp(y, cen, abot)) - MARG))
tris = []
for p in me.polygons:
    if any(C["interior"][v] for v in p.vertices): continue
    vs = list(p.vertices); tris.append(tuple(vs[:3]))
    if len(vs) == 4: tris.append((vs[0], vs[2], vs[3]))
skin_bvh = BVHTree.FromPolygons(R, tris)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
bm.verts.ensure_lookup_table(); order = [bm.verts[i] for i in RING0_IDX]; M = len(order); print("C) ring0 vertices", M)
tot, jj = jshare(me, H, J); jw = [jj[v.index] for v in order]
K = 12; ZC = 1.5035; NSUP = 2.8
def smooth_t(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
dl_ = bm.verts.layers.deform.verify(); shp = list(bm.verts.layers.shape.values()); col = bm.verts.layers.float_color.get("Col"); DARK = (0.30, 0.06, 0.07, 1.0)
rings = [order]; new_verts = []
def make_vert(co, jv):
    v = bm.verts.new(co)
    for l in shp: v[l] = co.copy()
    v[dl_][H] = 1.0 - jv; v[dl_][J] = jv
    if col is not None: v[col] = DARK
    new_verts.append(v); return v
pushed = 0
for k in range(1, K + 1):
    s = smooth_t(k / 3.0); u = smooth_t(max(0, k - 2) / (K - 2)); ring = []
    for i, pv in enumerate(order):
        p = pv.co; th = 2 * math.pi * i / M
        yk = (p.y - 0.0015 * s) * (1 - u) + YB * u
        a, top, bot = env(yk); c_, sn = math.cos(th), math.sin(th)
        ex = a * math.copysign(abs(c_) ** (2 / NSUP), c_)
        ez = ZC + ((top - ZC) if sn >= 0 else (ZC - bot)) * math.copysign(abs(sn) ** (2 / NSUP), sn)
        P = p.lerp(Vector((ex, yk, ez)), s); P.y = yk
        hit, _n, _i, _d = skin_bvh.ray_cast(Vector((P.x, -0.03, P.z)), Vector((0, -1, 0)), 0.25)
        if hit is not None and P.y < hit.y + 0.003: P.y = hit.y + 0.003; pushed += 1
        ring.append(make_vert(P, jw[i]))
    rings.append(ring)
centre = make_vert(Vector((0, YB - 0.004, ZC)), 0.5)
faces = []
for k in range(K):
    A = rings[k]; B = rings[k + 1]
    for i in range(M): faces.append(bm.faces.new((A[i], A[(i + 1) % M], B[(i + 1) % M], B[i])))
last = rings[K]
for i in range(M): faces.append(bm.faces.new((last[i], last[(i + 1) % M], centre)))
flipped = 0
for fc in faces:
    cc = fc.calc_center_median()
    if fc.normal.dot(Vector((0, cc.y, ZC)) - cc) < 0: fc.normal_flip(); flipped += 1
    fc.smooth = True
NPOUCH = len(faces); NNEW = len(new_verts)
bm.to_mesh(me); bm.free(); me.update()
N = len(me.vertices); N0 = N - NNEW; NP = len(me.polygons)
print("C) pouch faces", NPOUCH, "new verts", NNEW, "pushed behind skin", pushed, "flipped", flipped)
# ================= D) lip bones: 17 upper, 17 lower, 2 corners
R = [v.co.copy() for v in me.vertices]
ringi = [me.polygons[NP - NPOUCH + i].vertices[0] for i in range(M)]
assert len(set(ringi)) == M and all(v < N0 for v in ringi)
ic = min(range(M), key=lambda i: R[ringi[i]].x)
def chain(idx_list):
    pts = [R[i] for i in idx_list]; seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]; Ltot = sum(seg)
    def at(s):
        acc = 0.0
        for i, d in enumerate(seg):
            if acc + d >= s or i == len(seg) - 1: t = (s - acc) / d if d > 0 else 0; return pts[i].lerp(pts[i + 1], max(0, min(1, t)))
            acc += d
    return [at(Ltot * k / 16) for k in range(17)], Ltot
lipU, LU = chain([ringi[i] for i in range(0, ic + 1)])
lipL, LL = chain([ringi[i % M] for i in range(M, ic - 1, -1)])
cr = R[ringi[0]].copy(); cl = R[ringi[ic]].copy()
print("D) ring corner index", ic, "of", M, "| upper chain mm", round(1000 * LU, 1), "lower chain mm", round(1000 * LL, 1), "| corners x mm", round(1000 * cr.x, 1), round(1000 * cl.x, 1))
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones
for k in range(17):
    b = eb.new("lipU_%d" % k); b.head = lipU[k]; b.tail = lipU[k] + Vector((0, -0.008, 0)); b.parent = eb["head"]
    b = eb.new("lipL_%d" % k); b.head = lipL[k]; b.tail = lipL[k] + Vector((0, -0.008, 0)); b.parent = eb["jaw"]
for nm, p, sx in (("corner_r", cr, 1), ("corner_l", cl, -1)):
    b = eb.new(nm); b.head = p; b.tail = p + Vector((sx * 0.008, 0, 0)); b.parent = eb["jaw"]
bpy.ops.object.mode_set(mode='OBJECT')
for nm in ["lipU_%d" % k for k in range(17)] + ["lipL_%d" % k for k in range(17)] + ["corner_r", "corner_l"]: body.vertex_groups.new(name=nm)
gi = {g.name: g.index for g in body.vertex_groups}
RAD = 0.014; mu = ml = mc = 0
for v in me.vertices:
    if v.index >= N0: continue
    p = R[v.index]
    if abs(p.x) > 0.040 or p.z < 1.44 or p.z > 1.58: continue
    h = jw_ = 0.0
    for g in v.groups:
        if g.group == H: h = g.weight
        elif g.group == J: jw_ = g.weight
    if h + jw_ < 0.5: continue
    def nearest(chainp):
        best = None
        for k in range(16):
            a, b = chainp[k], chainp[k + 1]; ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab)))); d = (p - (a + ab * t)).length
            if best is None or d < best[0]: best = (d, k, t)
        return best
    d, k, t = nearest(lipU)
    W = min(1.0 - ss(0.004, RAD, d), h) * (1.0 - jw_)
    if W > 0.01:
        body.vertex_groups["head"].add([v.index], h - W, 'REPLACE')
        body.vertex_groups["lipU_%d" % k].add([v.index], W * (1 - t), 'ADD'); body.vertex_groups["lipU_%d" % (k + 1)].add([v.index], W * t, 'ADD'); mu += 1
    for nm, cp in (("corner_r", cr), ("corner_l", cl)):
        dc = (p - cp).length; cw = min((1.0 - ss(0.004, 0.013, dc)) * 0.9, jw_)
        if cw > 0.01:
            jcur = next((g.weight for g in me.vertices[v.index].groups if g.group == J), 0.0)
            body.vertex_groups["jaw"].add([v.index], max(0.0, jcur - cw), 'REPLACE'); body.vertex_groups[nm].add([v.index], cw, 'REPLACE'); mc += 1
    jcur = next((g.weight for g in me.vertices[v.index].groups if g.group == J), 0.0)
    if jcur >= 0.01:
        d, k, t = nearest(lipL); W = min(1.0 - ss(0.004, RAD, d), jcur)
        if W > 0.01:
            body.vertex_groups["jaw"].add([v.index], jcur - W, 'REPLACE')
            body.vertex_groups["lipL_%d" % k].add([v.index], W * (1 - t), 'ADD'); body.vertex_groups["lipL_%d" % (k + 1)].add([v.index], W * t, 'ADD'); ml += 1
print("D) weighted verts: upper", mu, "lower", ml, "corners", mc, "| bones", len(arm.data.bones))
# smoothing of lip-bone weights (lighter on the upper lip so the lift is kept)
LIPG = {gi[n]: (0.2 if n.startswith("lipU_") else 0.5) for n in gi if n.startswith(("lipU_", "lipL_", "corner_"))}
nb = defaultdict(set)
for e in me.edges:
    a, b = e.vertices
    if a < N0 and b < N0: nb[a].add(b); nb[b].add(a)
regionv = [i for i in range(N0) if abs(R[i].x) < 0.050 and 1.44 < R[i].z < 1.56]
Wt = {i: {g.group: g.weight for g in me.vertices[i].groups if g.weight > 0} for i in range(N0)}
for it in range(3):
    new = {}
    for i in regionv:
        ns = [k for k in nb[i] if k in Wt]
        if not ns: continue
        d = dict(Wt[i])
        for g, fac in LIPG.items():
            mean = sum(Wt[k].get(g, 0.0) for k in ns) / len(ns); cur = Wt[i].get(g, 0.0); d[g] = (1 - fac) * cur + fac * mean
        lt = sum(d.get(g, 0.0) for g in LIPG); ro = sum(w for g, w in Wt[i].items() if g not in LIPG); rn = max(0.0, 1.0 - lt)
        if ro > 1e-6:
            for g in list(d):
                if g not in LIPG: d[g] = Wt[i][g] * rn / ro
        elif rn > 1e-6: d[H] = d.get(H, 0.0) + rn
        new[i] = d
    for i, d in new.items(): Wt[i] = d
for i in regionv:
    for g in body.vertex_groups:
        try: g.remove([i])
        except RuntimeError: pass
    tt = sum(Wt[i].values())
    for gidx, w in Wt[i].items():
        if w > 0.002: body.vertex_groups[gidx].add([i], w / tt, 'REPLACE')
print("D) unweighted", sum(1 for v in me.vertices if not any(g.weight > 0.001 for g in v.groups)))
json.dump({"M": M, "NPOUCH": NPOUCH, "NNEW": NNEW, "ic": ic}, open(D + "/rig/meta70.json", "w"))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v70_remesh.blend"); print("saved v70")
