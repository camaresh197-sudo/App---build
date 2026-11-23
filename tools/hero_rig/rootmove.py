import bpy
from mathutils import Vector
SRC="/home/claude/out/character_rigged_centerhips.blend"
OUT="/home/claude/out/character_rigged_hiproot.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
def snap(tag):
    m=bpy.data.objects["torso_cartoon"]; l=bpy.data.objects["thigh_l_1"]
    return [tuple(round(c,5) for c in (m.matrix_world@v.co)) for v in m.data.vertices[:200]]+[tuple(round(c,5) for c in (l.matrix_world@v.co)) for v in l.data.vertices[:200]]
before=snap("before")
HIP=Vector((0.0,-0.02,0.84))
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
root=eb["root"]; pel=eb["pelvis"]
# root now sits at the hips (short bone up from hip centre)
root.head=HIP.copy(); root.tail=HIP+Vector((0,0,0.10))
# pelvis hangs from the hips root, same centre
pel.head=HIP.copy(); pel.tail=HIP+Vector((0,0,0.06))
bpy.ops.object.mode_set(mode='OBJECT')
after=snap("after")
diff=sum(1 for a,b in zip(before,after) if a!=b)
print("rest mesh vertices changed:", diff, "of", len(before))
print("root parent:", rig.data.bones["root"].parent, "pelvis parent:", rig.data.bones["pelvis"].parent.name)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
