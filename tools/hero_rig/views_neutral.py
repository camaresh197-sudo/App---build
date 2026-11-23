import bpy, sys
from mathutils import Vector
src=sys.argv[sys.argv.index('--')+1]; tag=sys.argv[sys.argv.index('--')+2]
bpy.ops.wm.open_mainfile(filepath=src)
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.data is not None and hasattr(o.data,"shape_keys") and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks[1:]: kb.value=0.0
for n in ("sombrero","hat_0","hat_1","hat_2","hat_3","hat_4"):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render=True
cam_data=bpy.data.cameras.new("O"); cam_data.type='ORTHO'; cam_data.ortho_scale=1.7
cam=bpy.data.objects.new("O",cam_data); sc.collection.objects.link(cam); sc.camera=cam
for name,loc,e in [("K",(1.5,-3,2.5),900),("F",(-2,-2,1.5),250)]:
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=e; ld.size=3
    lo=bpy.data.objects.new(name,ld); lo.location=loc; sc.collection.objects.link(lo)
sc.render.engine='BLENDER_WORKBENCH'; sc.render.resolution_x=700; sc.render.resolution_y=700
tgt=Vector((0.1,0,1.0))
for name,loc in (("front",Vector((0.1,-4,1.0))),("left",Vector((-4,0,1.0))),("right",Vector((4.2,0,1.0))),("top",Vector((0.1,0,5)))):
    cam.location=loc; cam.rotation_euler=(tgt-loc if name!="top" else Vector((0,0,-1))).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"/home/claude/render/{tag}_{name}.png"; bpy.ops.render.render(write_still=True)
print("WROTE")
