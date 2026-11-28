import bpy, sys, math, bmesh
from mathutils import Vector
D = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=D + "/rig/body_rigged_v71_remesh.blend")
sc = bpy.context.scene; arm = bpy.data.objects["character_rig"]; body = bpy.data.objects["body_gnm"]; me = body.data; cam = sc.camera
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.normal_update()
bm.to_mesh(me); bm.free(); me.update()
for p in me.polygons: p.use_smooth = True
me.update()
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v78_normals.blend")
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = 520; sc.render.resolution_y = 520
cam.data.clip_start = 0.005; cam.data.lens = 50
target = Vector((0, -0.12, 1.49))
for vn, (az, el, dist) in {"front": (0, 0, 0.26), "right40": (40, 5, 0.32), "close": (0, 0, 0.16)}.items():
    a = math.radians(az); e = math.radians(el)
    cam.location = target + Vector((dist * math.sin(a) * math.cos(e), -dist * math.cos(a) * math.cos(e), dist * math.sin(e)))
    cam.rotation_euler = (target - cam.location).normalized().to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = D + "/rig/n78_%s.png" % vn; bpy.ops.render.render(write_still=True)
print("done")
