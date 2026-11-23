import bpy, math
from mathutils import Vector, Quaternion
SRC="/home/claude/out/character_rigged_armrest.blend"
OUT="/home/claude/out/character_rigged_armrolls2.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
LIMB=[]
for s in ("l","r"):
    LIMB+=["clav_"+s,"shoulder_"+s,f"uarm_{s}",f"elbow_{s}",f"fore_{s}",f"hand_{s}"]
    for f in ("fg0","fh0","fg1","fh1","fg2","fh2","fg3","fh3"): LIMB.append(f"{f}_{s}")
    LIMB.append(f"thumb_{s}")
watch=["uarm_l_1","uarm_r_1","fore_l_1","fore_r_1","hand_new_l","hand_new_r","shoulder_l_1","shoulder_r_1","elbow_l_1","elbow_r_1"]
def snap():
    dg=bpy.context.evaluated_depsgraph_get(); out={}
    for n in watch:
        o=bpy.data.objects[n].evaluated_get(dg); me=o.to_mesh()
        out[n]=[o.matrix_world@v.co for v in me.vertices]; o.to_mesh_clear()
    return out
before=snap()
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
for n in LIMB:
    b=eb[n]; d=(b.tail-b.head).normalized()
    z=Vector((1,0,0)).cross(d)
    if z.length<1e-6: z=Vector((0,1,0))
    z.normalize(); b.align_roll(z)
    if b.x_axis.x<0: b.align_roll(-z)
bpy.ops.object.mode_set(mode='OBJECT'); bpy.context.view_layer.update()
after=snap()
print("R2 worst mesh drift:", round(max(max((a-b).length for a,b in zip(before[n],after[n])) for n in watch),6))
B=rig.data.bones
for pair in (("uarm_l","uarm_r"),("fore_l","fore_r"),("hand_l","hand_r")):
    for n in pair: print("R2 axes",n,"x",tuple(round(c,2) for c in B[n].x_axis),"z",tuple(round(c,2) for c in B[n].z_axis))
def sweep(bone, tip, degs):
    pb=rig.pose.bones[bone]; tb=rig.pose.bones[tip]; out=[]
    for d in degs:
        pb.rotation_mode="QUATERNION"; pb.rotation_quaternion=Quaternion(Vector((1,0,0)), math.radians(d)); bpy.context.view_layer.update()
        t=rig.matrix_world@tb.tail; out.append((d,round(t.x-0.09,2),round(t.y,2),round(t.z,2)))
    pb.rotation_quaternion=(1,0,0,0); bpy.context.view_layer.update(); return out
print("R2 elbow L:", sweep("fore_l","hand_l",(-90,0,90)))
print("R2 elbow R:", sweep("fore_r","hand_r",(-90,0,90)))
print("R2 shoulder L:", sweep("uarm_l","fore_l",(-90,-30,0,30,90)))
print("R2 shoulder R:", sweep("uarm_r","fore_r",(-90,-30,0,30,90)))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
