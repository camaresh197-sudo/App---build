import sys, bpy
from mathutils import Vector
src,outdir=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2]
bpy.ops.wm.open_mainfile(filepath=src)
scn=bpy.context.scene; scn.render.engine='BLENDER_WORKBENCH'; scn.display.shading.color_type='MATERIAL'; scn.render.resolution_x=scn.render.resolution_y=800
for o in bpy.data.objects: o.hide_render = o.name not in ('head_quad','eye_l','eye_r','nostril_l','nostril_r')
c=bpy.data.cameras.new('c'); c.lens=70; ob=bpy.data.objects.new('c',c); scn.collection.objects.link(ob); scn.camera=ob
T=Vector((0,-0.03,1.52))
for name,loc in [('front',Vector((0,-1.0,1.52))),('threeq',Vector((0.65,-0.8,1.58))),('side',Vector((1.0,-0.03,1.52)))]:
    ob.location=loc; ob.rotation_euler=(T-loc).normalized().to_track_quat('-Z','Y').to_euler()
    scn.render.filepath=f"{outdir}/final_{name}.png"; bpy.ops.render.render(write_still=True)
print('rendered')
