import bpy
from mathutils import Vector
SRC="/home/claude/out/character_rigged_abs.blend"
OUT="/home/claude/out/character_rigged_hipsbone.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
HIP=eb["pelvis"].head.copy()
hb=eb.new("hips")
hb.head=HIP.copy(); hb.tail=HIP+Vector((0,0,0.10))
hb.parent=eb["root"]; hb.use_connect=False
hb.use_deform=False
eb["pelvis"].parent=hb
bpy.ops.object.mode_set(mode='OBJECT')
print("CHK hips parent", rig.data.bones["hips"].parent.name, "pelvis parent", rig.data.bones["pelvis"].parent.name, "hips head", tuple(round(c,3) for c in rig.data.bones["hips"].head_local))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
