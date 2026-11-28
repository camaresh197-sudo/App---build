import bpy, sys, math, json
from collections import Counter
from mathutils import Vector, Matrix
D = sys.argv[-1]
FILES = [("v55", "body_rigged_v55_lips_smooth.blend", None), ("v61", "body_rigged_v61_pipeline.blend", json.load(open(D + "/rig/pipeline60_meta.json")))]
for tag, fn, meta in FILES:
    bpy.ops.wm.open_mainfile(filepath=D + "/rig/" + fn)
    arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
    N = len(me.vertices); NNEW = meta["NNEW"] if meta else 649; N0 = N - NNEW
    R = [v.co.copy() for v in me.vertices]
    wire = sum(1 for e in me.edges if not any(True for _ in [0]) )  # placeholder
    facecount = [0] * len(me.edges)
    emap = {}
    for e in me.edges: emap[tuple(sorted(e.vertices))] = e.index
    for p in me.polygons:
        vs = list(p.vertices)
        for a in range(len(vs)): facecount[emap[tuple(sorted((vs[a], vs[(a + 1) % len(vs)])))]] += 1
    wires = sum(1 for c in facecount if c == 0)
    def reset():
        for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
        bpy.context.view_layer.update()
    def rot_bone(name, axis, deg):
        pb = arm.pose.bones[name]; h = pb.head.copy()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
    def move(name, d):
        pb = arm.pose.bones[name]; pb.matrix = Matrix.Translation(d) @ pb.matrix; bpy.context.view_layer.update()
    def lips(lu, out, up, ll):
        for k in range(17):
            prof = math.sin(math.pi * k / 16) ** 0.8
            move("lipU_%d" % k, Vector((0, 0, lu * prof))); move("lipL_%d" % k, Vector((0, 0, ll * prof)))
        move("corner_r", Vector((out, 0, up))); move("corner_l", Vector((-out, 0, up)))
        for k, s in ((0, 1), (16, -1)):
            move("lipU_%d" % k, Vector((s * out * 0.8, 0, up * 0.8))); move("lipL_%d" % k, Vector((s * out * 0.8, 0, up * 0.8)))
    print(f"{tag}: loose wire edges (no faces): {wires}")
    for pn, f in (("snarl", lambda: (rot_bone("jaw", 'X', 12), lips(0.008, 0.008, 0.005, -0.003))), ("jaw25", lambda: rot_bone("jaw", 'X', 25))):
        reset(); f()
        dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
        worst = []
        for p in me.polygons:
            vs = list(p.vertices); c = sum((R[v] for v in vs), Vector()) / len(vs)
            if abs(c.x) > 0.06 or not (1.43 < c.z < 1.60): continue
            mx = 0.0
            for a in range(len(vs)):
                L0 = (R[vs[a]] - R[vs[(a + 1) % len(vs)]]).length
                if L0 > 0.0006: mx = max(mx, (P[vs[a]] - P[vs[(a + 1) % len(vs)]]).length / L0)
            if mx > 4.0: worst.append((mx, p.index, c, any(v >= N0 for v in vs)))
        worst.sort(key=lambda t: -t[0])
        print(f"   {pn}: faces with an edge stretched >4x: {len(worst)} (skin {sum(1 for w in worst if not w[3])}, lining {sum(1 for w in worst if w[3])}) | worst {worst[0][0]:.1f}x" if worst else f"   {pn}: none")
        for mx, pi, c, lin in worst[:4]: print(f"      {mx:5.1f}x at x {1000*c.x:6.1f} z {1000*c.z:7.1f} y {1000*c.y:7.1f} {'(lining)' if lin else '(skin)'}")
