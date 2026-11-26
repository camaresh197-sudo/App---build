import bpy, sys
from mathutils import Vector
src,out=sys.argv[-9],sys.argv[-8]
CX,CY,CZ,TX,TY,TZ=[float(v) for v in sys.argv[-6:]]
bpy.ops.wm.open_mainfile(filepath=src)
_lo=bpy.data.objects.get('head_low')
if _lo is not None:
    _w=_lo.copy(); _w.data=_lo.data; _w.name='head_low_wire'
    bpy.context.scene.collection.objects.link(_w)
    _m=_w.modifiers.new('wire','WIREFRAME'); _m.thickness=0.00045; _m.offset=1.0; _m.use_replace=True
    _dm=bpy.data.materials.new('wiremat'); _dm.diffuse_color=(0.02,0.02,0.03,1)
    _w.data=_lo.data.copy(); _w.data.materials.clear(); _w.data.materials.append(_dm)
    _lo.data.materials.clear()
    _sm=bpy.data.materials.new('lowskin'); _sm.diffuse_color=(0.82,0.82,0.82,1); _lo.data.materials.append(_sm)
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
