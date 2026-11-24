import bpy,sys,math
from mathutils import Vector
src,tag=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
a=bpy.data.objects['character_rig']
names=['spine','spine2','chest','clav_l','clav_r','shoulder_l','shoulder_r','uarm_l','uarm_r']
for n in names:
    b=a.data.bones.get(n)
    if not b: continue
    cu=bpy.data.curves.new('s_'+n,'CURVE');cu.dimensions='3D';cu.bevel_depth=0.007
    sp=cu.splines.new('POLY');sp.points.add(1)
    h=a.matrix_world@b.head_local;t=a.matrix_world@b.tail_local
    sp.points[0].co=(*h,1);sp.points[1].co=(*t,1)
    o=bpy.data.objects.new('stick_'+n,cu);bpy.context.scene.collection.objects.link(o)
    o.color=(1,0.1,0.1,1) if 'clav' in n else (0.1,0.3,1,1)
    o.show_in_front=True
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO';sc.display.shading.color_type='OBJECT'
sc.display.shading.show_xray=True;sc.display.shading.xray_alpha=0.35
sc.render.resolution_x=900;sc.render.resolution_y=700
sc.render.film_transparent=False
w=bpy.data.worlds.new('w');w.color=(1,1,1);sc.world=w
for o in bpy.data.objects:
    if o.type=='MESH' and not o.name.startswith('stick'): o.color=(0.8,0.75,0.7,1)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=1.1
ctr=Vector((0.09,0,1.2))
for view,loc,rot in(('front',(0.09,-3,1.2),(math.pi/2,0,0)),('back',(0.09,3,1.2),(math.pi/2,0,math.pi))):
    cam.location=loc;cam.rotation_euler=rot
    sc.render.filepath=f'/home/claude/out/{tag}_{view}.png';bpy.ops.render.render(write_still=True)
