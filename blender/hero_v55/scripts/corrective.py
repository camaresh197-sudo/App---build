import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v38.blend")
sc = bpy.context.scene
arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data
assert arm.matrix_world == Matrix.Identity(4) and body.matrix_world == Matrix.Identity(4)
def aim(name, target):
    pb = arm.pose.bones[name]; h = pb.head.copy(); t = pb.tail.copy()
    rot = (t - h).normalized().rotation_difference(target.normalized()).to_matrix().to_4x4()
    pb.matrix = Matrix.Translation(h) @ rot @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
def reset():
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    bpy.context.view_layer.update()
def forward():
    reset(); aim("clav_r", Vector((0.18,-0.07,0.04))); aim("uarm_r", Vector((0.1,-1,0))); aim("fore_r", Vector((0.1,-1,0)))
def across():
    reset(); aim("clav_r", Vector((0.18,-0.09,0.04))); aim("uarm_r", Vector((-0.6,-1,-0.1))); aim("fore_r", Vector((-1,-0.4,-0.05)))
def evalv():
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh()
    pts = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear(); return pts
# basis shape key
if not me.shape_keys: body.shape_key_add(name="Basis", from_mix=False)
key = body.shape_key_add(name="corr_shoulder_r_fwd", from_mix=False); key.value = 0.0
R = [v.co.copy() for v in me.vertices]
forward(); bpy.context.view_layer.update()
P0 = evalv()
Jp = arm.pose.bones["uarm_r"].head.copy(); Jr = arm.data.bones["uarm_r"].head_local.copy()
def ss(a, b, t):
    u = max(0.0, min(1.0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
mask = [0.0] * len(R); tgt = list(P0)
for i, r in enumerate(R):
    if r.x < 0: continue
    d0 = (r - Jr).length
    m = (1 - ss(0.06, 0.16, d0)) * ss(-0.05, 0.0, r.z - Jr.z)
    if m <= 0: continue
    v = P0[i] - Jp; rl = v.length
    if rl < 1e-6: continue
    rt = max(rl, d0 * 0.97)
    tgt[i] = P0[i] + m * (Jp + v / rl * rt - P0[i]); mask[i] = m
cap = [i for i, m in enumerate(mask) if m > 0.05]
def ratio_stats(P, label):
    rr = [ (P[i] - Jp).length / max(1e-6, (R[i] - Jr).length) for i in cap]
    rr.sort(); print(label, "cap verts", len(cap), "radius ratio median", round(rr[len(rr)//2], 3), "p10", round(rr[len(rr)//10], 3), "min", round(rr[0], 3))
ratio_stats(P0, "LBS only  ")
# skin matrices -> rest-space delta
names = {g.index: g.name for g in body.vertex_groups}
SM = {}
for gi, n in names.items():
    if n in arm.pose.bones: SM[gi] = (arm.pose.bones[n].matrix @ arm.data.bones[n].matrix_local.inverted())
maxerr = 0.0
for i in cap:
    gs = [(g.group, g.weight) for g in me.vertices[i].groups if g.weight > 0 and g.group in SM]
    tot = sum(w for _, w in gs); M = Matrix(((0,0,0),(0,0,0),(0,0,0)))
    Mfull = Matrix([[0]*4 for _ in range(4)]); 
    for g, w in gs: Mfull = Mfull + SM[g] * (w / tot)
    L = Mfull.to_3x3()
    chk = (Mfull @ R[i].to_4d()).to_3d(); maxerr = max(maxerr, (chk - P0[i]).length)
    key.data[i].co = R[i] + L.inverted() @ (tgt[i] - P0[i])
print("skin matrix check vs evaluated: max err mm", round(maxerr * 1000, 4))
# apply key and verify
key.value = 1.0; bpy.context.view_layer.update(); P1 = evalv()
ratio_stats(P1, "with key 1 ")
err = [(P1[i] - tgt[i]).length for i in cap]
print("achieved vs target: mean mm", round(1000 * sum(err) / len(err), 3), "max mm", round(1000 * max(err), 3))
mv = [(P1[i] - P0[i]).length for i in cap]; print("key moves cap verts: mean mm", round(1000*sum(mv)/len(mv),2), "max mm", round(1000*max(mv),2))
# driver: strength from uarm_r local rotation angle (quaternion W), 0 below ~40 deg, 1 above ~85 deg
fc = key.driver_add("value"); d = fc.driver; d.type = 'SCRIPTED'
var = d.variables.new(); var.name = "w"; var.type = 'TRANSFORMS'
t = var.targets[0]; t.id = arm; t.bone_target = "uarm_r"; t.transform_type = 'ROT_W'; t.transform_space = 'LOCAL_SPACE'
d.expression = "min(max((2*acos(min(max(w,-1),1)) - 0.7) / 0.8, 0), 1)"
key.driver_remove("value") if False else None
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1)
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x = 520; sc.render.resolution_y = 520
views = {"front": ((0.15, -2.1, 1.3), (math.radians(90), 0, 0)), "back": ((0.15, 2.1, 1.3), (math.radians(90), 0, math.radians(180)))}
def shots(tag, posefn):
    posefn()
    for vn, (loc, rot) in views.items():
        cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = D + "/rig/corr_%s_%s.png" % (tag, vn); bpy.ops.render.render(write_still=True)
# drivers evaluate by pose; render with driver ON (as shipped) and with key forced off for comparison
fcurve = me.shape_keys.animation_data.drivers[0]
print("driver value forward:", end=" "); forward(); bpy.context.view_layer.update(); print(round(key.value, 3))
shots("fwd_on", forward)
across(); bpy.context.view_layer.update(); print("driver value across:", round(key.value, 3))
shots("across_on", across)
# key off: remove driver temporarily by muting
fcurve.mute = True; key.value = 0.0
shots("fwd_off", forward); shots("across_off", across)
fcurve.mute = False
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v39.blend"); print("saved v39")
