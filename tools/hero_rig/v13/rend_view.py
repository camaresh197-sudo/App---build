import bpy, sys
from mathutils import Vector
src,out=sys.argv[-9],sys.argv[-8]
CX,CY,CZ,TX,TY,TZ=[float(v) for v in sys.argv[-6:]]
bpy.ops.wm.open_mainfile(filepath=src)
sc=bpy.context.scene; r=sc.render
r.engine='BLENDER_WORKBENCH'; r.resolution_x=800; r.resolution_y=800; r.image_settings.file_format='PNG'
sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'; sh.show_cavity=True
sh.background_type='WORLD'; sc.world=sc.world or bpy.data.worlds.new('w'); sc.world.color=(0.18,0.18,0.2)
target=bpy.data.objects.new('target', None); target.location=Vector((TX,TY,TZ)); sc.collection.objects.link(target)
cam=bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam)
cam.data.type='PERSP'; cam.data.lens=85
cam.location=Vector((CX,CY,CZ))       # 3/4 view from the front-right
c=cam.constraints.new('TRACK_TO'); c.target=target; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'
sc.camera=cam; r.filepath=out
bpy.ops.render.render(write_still=True); print("rendered", out)
