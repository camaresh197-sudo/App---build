import bpy, sys
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/body2/body_gnm_v32_smoothed.blend")
ob = bpy.data.objects["body_gnm"]
P = [ob.matrix_world @ v.co for v in ob.data.vertices]
print("BOUNDS z", round(min(p.z for p in P),3), round(max(p.z for p in P),3), "x", round(min(p.x for p in P),3), round(max(p.x for p in P),3))
def clusters(xs, gap):
    xs = sorted(xs); cl = [[xs[0]]]
    for x in xs[1:]:
        if x - cl[-1][-1] > gap: cl.append([x])
        else: cl[-1].append(x)
    return cl
print("== right half (x>0): per-z slice, clusters (count, xmin, xmax) with y-centroid")
for zi in range(0, 146, 5):
    z0 = zi / 100.0
    sl = [p for p in P if z0 <= p.z < z0 + 0.02 and p.x > 0.0]
    if not sl: continue
    cl = clusters([p.x for p in sl], 0.012)
    out = []
    for c in cl:
        pts = [p for p in sl if c[0] - 1e-9 <= p.x <= c[-1] + 1e-9]
        out.append((len(c), round(c[0], 3), round(c[-1], 3), round(sum(p.y for p in pts)/len(pts), 3)))
    print("Z", z0, out)
