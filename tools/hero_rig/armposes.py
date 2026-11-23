import bpy, sys, math
argv=sys.argv[sys.argv.index('--')+1:]
src, tag, spec = argv[0], argv[1], argv[2]
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects["character_rig"]
# zero expression keys so only the arm pose shows
for o in bpy.data.objects:
    if o.type=='MESH' and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks[1:]: kb.value=0.0
for part in spec.split(";"):
    if not part: continue
    bone,axis,deg=part.split(":")
    pb=rig.pose.bones[bone]; pb.rotation_mode="XYZ"
    e=list(pb.rotation_euler); e["XYZ".index(axis)]=math.radians(float(deg)); pb.rotation_euler=e
bpy.context.view_layer.update()
cam_data=bpy.data.cameras.new("O"); cam_data.type='ORTHO'; cam_data.ortho_scale=2.2
cam=bpy.data.objects.new("O",cam_data); bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera=cam
from mathutils import Vector
cam.location=Vector((0.1,-4,1.2)); tgt=Vector((0.1,0,1.1))
cam.rotation_euler=(tgt-cam.location).to_track_quat('-Z','Y').to_euler()
for o in bpy.data.objects:
    if o.name.startswith("hat_") or o.name.startswith("sombrero"): o.hide_render=True
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.render.resolution_x=600; sc.render.resolution_y=600
sc.render.filepath=f"/home/claude/render/{tag}.png"; bpy.ops.render.render(write_still=True)
print("WROTE")
