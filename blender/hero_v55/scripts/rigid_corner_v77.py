import bpy, sys
from mathutils import Vector
D = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v71_remesh.blend")
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
gi = {g.name: g.index for g in body.vertex_groups}; H, J = gi["head"], gi["jaw"]
N = len(me.vertices); R = [v.co.copy() for v in me.vertices]
lip_c = [(R[i]) for i in range(N) if abs(R[i].x) > 0.0 and 1.49 < R[i].z < 1.51 and R[i].y < -0.13]
mid = sum(lip_c, Vector()) / len(lip_c)
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
changed = 0
for i in range(N):
    p = R[i]
    if abs(p.x) > 0.030 or not (1.46 < p.z < 1.55): continue
    # distance from the mouth-line midpoint in the lip plane
    d = ((p.x - mid.x) ** 2 + (p.z - mid.z) ** 2) ** 0.5
    if abs(p.x) < 0.024: continue           # lip body keeps its own lip bones
    f = ss(0.014, 0.022, abs(p.x))          # 0 inside 14 mm, 1 beyond 22 mm
    if f <= 0: continue
    cur = {g.group: g.weight for g in me.vertices[i].groups if g.weight > 0}
    jaw_share = cur.get(J, 0.0) + sum(w for g, w in cur.items() if g not in (H, J))
    head_share = cur.get(H, 0.0)
    new = {H: head_share * (1 - f), J: (jaw_share + head_share * f)}
    for g in list(cur):
        body.vertex_groups[g].remove([i])
    for g, w in new.items():
        if w > 1e-4: body.vertex_groups[g].add([i], w, 'REPLACE')
    changed += 1
print("rigidised verts", changed)
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v77_rigid.blend")
