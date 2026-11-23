import bpy
from mathutils import Vector
SRC="/home/claude/out/character_rigged_straight2.blend"
OUT="/home/claude/out/character_rigged_straight3.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
B=rig.data.bones
hl=B["thigh_l"].head_local; hr=B["thigh_r"].head_local
mid=(hl.x+hr.x)/2
DX=0.09-mid                     # centre the leg pair on the pelvis/torso line x = 0.09
print("leg mid before", round(mid,4), "shift", round(DX,4))
LEG=("hip_","thigh_","knee_","shin_","ankle_","foot_","toe_")
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for eb in rig.data.edit_bones:
    if eb.name.startswith(LEG):
        eb.head=eb.head+Vector((DX,0,0)); eb.tail=eb.tail+Vector((DX,0,0))
bpy.ops.object.mode_set(mode='OBJECT')
n=0
for o in bpy.data.objects:
    if o.type!='MESH': continue
    if not (o.name.startswith(LEG)): continue
    d=o.matrix_world.inverted().to_3x3()@Vector((DX,0,0))
    for v in o.data.vertices: v.co+=d
    o.data.update(); n+=1
print("legs moved meshes", n)
print("CHK hips", tuple(round(c,3) for c in B["thigh_l"].head_local), tuple(round(c,3) for c in B["thigh_r"].head_local))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
