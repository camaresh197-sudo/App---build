import bpy, sys
import numpy as np
from collections import Counter
from mathutils import Vector
from mathutils.kdtree import KDTree
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v42.blend")
body = bpy.data.objects["body_gnm"]; me = body.data
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance()
DY = -0.0155; DZ = 1.27
jg = body.vertex_groups["jaw"].index
jw = [0.0] * len(me.vertices); cat = [""] * len(me.vertices); dist = [9.0] * len(me.vertices)
GR = ["upper_lip", "lower_lip", "upper_teeth_and_gums", "lower_teeth_and_gums", "tongue", "mouth_sock", "teeth", "gums"]
for v in me.vertices:
    jw[v.index] = next((g.weight for g in v.groups if g.group == jg), 0.0)
    p = v.co
    if p.z < 1.38 or p.z > 1.60: continue
    co, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY)))); dist[v.index] = d
    cat[v.index] = "+".join(n for n in GR if VG[gnames.index(n), idx] > 0.5) or "skin"
bad = []
for e in me.edges:
    a, b = e.vertices
    if abs(jw[a] - jw[b]) > 0.5 and cat[a] and cat[b]: bad.append((a, b))
print("EDGES with jaw-weight jump >0.5 in mouth zone:", len(bad))
c = Counter(tuple(sorted((cat[a], cat[b]))) for a, b in bad)
for k, n in c.most_common(12): print("PAIR", n, k)
zs = [ (me.vertices[a].co.z + me.vertices[b].co.z) / 2 for a, b in bad]
if zs: print("z of bad edges: min", round(min(zs), 4), "max", round(max(zs), 4))
lens = [(me.vertices[a].co - me.vertices[b].co).length for a, b in bad]
print("rest length of bad edges mm: median", round(1000 * sorted(lens)[len(lens)//2], 2), "max", round(1000 * max(lens), 2))
# vertices with intermediate jaw weight, by category
mid = Counter(cat[i] for i in range(len(jw)) if cat[i] and 0.15 < jw[i] < 0.85)
print("verts with jaw weight 0.15..0.85 by category:", dict(mid))
# teeth and gums: weights by category
for n in ("upper_teeth_and_gums", "lower_teeth_and_gums", "tongue", "mouth_sock", "teeth", "gums"):
    ws = [jw[i] for i in range(len(jw)) if n in cat[i].split("+")]
    if ws: print("CAT", n, "verts", len(ws), "jaw weight min", round(min(ws), 2), "mean", round(sum(ws)/len(ws), 2), "max", round(max(ws), 2))
