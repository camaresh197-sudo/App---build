import bpy, sys
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v71_remesh.blend")
body = bpy.data.objects["body_gnm"]; me = body.data
names = {g.index: g.name for g in body.vertex_groups}
for fi in (21951, 16585, 16248):
    p = me.polygons[fi]
    print("FACE", fi, "centre x mm", round(1000*p.center.x,1), "z", round(1000*p.center.z,1))
    for vi in p.vertices:
        ws = sorted(((names[g.group], round(g.weight,2)) for g in me.vertices[vi].groups if g.weight > 0.01), key=lambda t: -t[1])
        print("   v", vi, "xyz mm", [round(1000*c) for c in me.vertices[vi].co], ws)
