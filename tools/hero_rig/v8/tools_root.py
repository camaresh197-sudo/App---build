import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v12_uv.blend")
a=bpy.data.objects['character_rig'];bpy.context.view_layer.objects.active=a
bpy.ops.object.mode_set(mode='EDIT')
r=a.data.edit_bones['root'];r.head=Vector((0,0,0));r.tail=Vector((0,0,0.1))
bpy.ops.object.mode_set(mode='OBJECT')
print("root",[tuple(round(x,3) for x in a.data.bones['root'].head_local)],"bones",len(a.data.bones))
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/work/hero_v13_root.blend")
