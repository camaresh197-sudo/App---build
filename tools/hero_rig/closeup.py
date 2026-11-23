import bpy, sys
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
src,tag=a[0],a[1]; tgt=Vector((float(a[2]),float(a[3]),float(a[4]))); scale=float(a[5]); views=a[6].split(',')
bpy.ops.wm.open_mainfile(filepath=src)
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.data is not None and hasattr(o.data,"shape_keys") and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks[1:]: kb.value=0.0
for n in ("sombrero","hat_0","hat_1","hat_2","hat_3","hat_4"):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render=True
cd=bpy.data.cameras.new("O"); cd.type='ORTHO'; cd.ortho_scale=scale
cam=bpy.data.objects.new("O",cd); sc.collection.objects.link(cam); sc.camera=cam
for name,loc,e in [("K",(1.5,-3,2.5),900),("F",(-2,-2,1.5),250),("B",(0,3,2),500)]:
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=e; ld.size=3
    lo=bpy.data.objects.new(name,ld); lo.location=loc; sc.collection.objects.link(lo)
sc.render.engine='BLENDER_WORKBENCH'; sc.render.resolution_x=700; sc.render.resolution_y=700
sc.display.shading.light='STUDIO'
D={"front":Vector((0,-4,0)),"back":Vector((0,4,0)),"left":Vector((-4,0,0)),"right":Vector((4,0,0)),"top":Vector((0,0,4)),"f34":Vector((-2.5,-3,0.5)),"b34":Vector((2.5,3,0.5))}
for v in views:
    loc=tgt+D[v]; cam.location=loc; cam.rotation_euler=(tgt-loc).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"/home/claude/render/{tag}_{v}.png"; bpy.ops.render.render(write_still=True)
print("WROTE")
