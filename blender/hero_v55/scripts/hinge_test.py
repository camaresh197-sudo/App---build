import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
D = sys.argv[-1]
HINGES = {"A_old": Vector((0, -0.012, 1.535)), "B_low": Vector((0, -0.045, 1.505)), "C_mid": Vector((0, -0.030, 1.520))}
zz = np.load(D + "/gnm_head/weights/gnm_head.npz")
T = zz["template_vertex_positions"]; gnames = [str(n) for n in zz["vertex_group_names"]]; VG = zz["vertex_groups"]
kd = KDTree(len(T))
for i, t in enumerate(T): kd.insert(Vector((float(t[0]), float(t[1]), float(t[2]))), i)
kd.balance(); DY = -0.0155; DZ = 1.27
def has(n, idx): return VG[gnames.index(n), idx] > 0.5
for name, hp in HINGES.items():
    bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v47.blend")
    sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data; cam = sc.camera
    cam.data.clip_start = 0.005; cam.data.lens = 50
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones["jaw"]; tail = eb.tail.copy(); eb.head = hp; eb.tail = tail if (tail - hp).length > 0.01 else hp + Vector((0, -0.05, -0.05))
    bpy.ops.object.mode_set(mode='OBJECT')
    R = [v.co.copy() for v in me.vertices]; N = len(R); ll = []
    for v in me.vertices:
        p = v.co
        if abs(p.x) < 0.010 and 1.46 < p.z < 1.52:
            _, idx, d = kd.find(Vector((p.x, p.z - DZ, -(p.y - DY))))
            if d < 0.012 and has("lower_lip", idx): ll.append(v.index)
    for pb in arm.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    pb = arm.pose.bones["jaw"]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(25), 4, 'X') @ Matrix.Translation(-h) @ pb.matrix; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); m = oe.to_mesh(); P = [v.co.copy() for v in m.vertices]; oe.to_mesh_clear()
    dl = sum((P[i] - R[i] for i in ll), Vector()) / len(ll)
    print(f"HINGE {name} {tuple(hp)}: lower-lip centre at 25 deg moves down {-1000*dl.z:.1f} mm, back {1000*dl.y:.1f} mm (verts {len(ll)})")
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
    sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = 520; sc.render.resolution_y = 520
    target = Vector((0, -0.12, 1.47)); dist = 0.36
    for vn, (az, el) in (("right40", (40, 5)), ("front", (0, 0))):
        a = math.radians(az); e = math.radians(el)
        cam.location = target + Vector((dist * math.sin(a) * math.cos(e), -dist * math.cos(a) * math.cos(e), dist * math.sin(e)))
        cam.rotation_euler = (target - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = D + "/rig/hinge_%s_%s.png" % (name, vn); bpy.ops.render.render(write_still=True)
print("done")
