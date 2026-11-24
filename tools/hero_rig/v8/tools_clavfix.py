import bpy,sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v6.blend")
a=bpy.data.objects['character_rig']
bpy.context.view_layer.objects.active=a
bpy.ops.object.mode_set(mode='EDIT')
eb=a.data.edit_bones
ch=eb['chest']
ch.tail=Vector((ch.head.x,-0.023,ch.tail.z))
for s in 'lr':
    c=eb['clav_'+s]; sh=eb['shoulder_'+s]
    c.use_connect=False
    c.head=ch.tail.copy()
    c.tail=sh.head.copy()
    sh.use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
for o in [o for o in bpy.data.objects if o.type=='MESH' and '_OLD' in o.name]:
    bpy.data.objects.remove(o,do_unlink=True)
for b in a.data.bones:
    if b.name in('chest','clav_l','clav_r'):print(b.name,[round(x,3) for x in b.head_local],[round(x,3) for x in b.tail_local])
print("bones",len(a.data.bones),"meshes",sum(1 for o in bpy.data.objects if o.type=='MESH'),"faces",sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'))
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/work/hero_v8_clav.blend")
