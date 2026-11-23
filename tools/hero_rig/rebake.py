import bpy, math
from mathutils import Vector, Matrix
SRC="/home/claude/out/character_rigged_headback.blend"
OUT="/home/claude/out/character_rigged_armrolls.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
LIMB=[]
for s in ("l","r"):
    LIMB+=[f"uarm_{s}",f"elbow_{s}",f"fore_{s}",f"hand_{s}"]
    for f in ("fg0","fh0","fg1","fh1","fg2","fh2","fg3","fh3"): LIMB.append(f"{f}_{s}")
    LIMB.append(f"thumb_{s}")
def depth(n):
    d=0; b=rig.data.bones[n]
    while b.parent: d+=1; b=b.parent
    return d
LIMB.sort(key=depth)
dg=bpy.context.evaluated_depsgraph_get()
watch=["uarm_l_1","uarm_r_1","fore_l_1","fore_r_1","hand_new_l","hand_new_r","elbow_l_1","elbow_r_1","shoulder_l_1"]
def snapshot():
    dg=bpy.context.evaluated_depsgraph_get(); out={}
    for n in watch:
        o=bpy.data.objects[n].evaluated_get(dg); me=o.to_mesh()
        out[n]=[o.matrix_world@v.co for v in me.vertices]; o.to_mesh_clear()
    return out
before=snapshot()
# old deformation matrices D = pose_matrix * inverse(rest_matrix)
D={n: rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted() for n in LIMB}
# --- shared roll rule
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
for n in LIMB:
    b=eb[n]; d=(b.tail-b.head).normalized()
    z=Vector((1,0,0)).cross(d)
    if z.length<1e-6: z=Vector((0,1,0))
    z.normalize(); b.align_roll(z)
    if b.x_axis.x<0: b.align_roll(-z)
bpy.ops.object.mode_set(mode='OBJECT')
# --- re-bake poses so the deformation is unchanged
for n in LIMB:
    pb=rig.pose.bones[n]; pb.rotation_mode="QUATERNION"
    pb.matrix = D[n] @ rig.data.bones[n].matrix_local
    bpy.context.view_layer.update()
after=snapshot()
worst=0
for n in watch:
    m=max((a-b).length for a,b in zip(before[n],after[n])); worst=max(worst,m)
    print("RB mesh drift",n,round(m,5))
print("RB worst drift (m):",round(worst,6))
for n in ("uarm_l","uarm_r","fore_l","fore_r","hand_l","hand_r"):
    pb=rig.pose.bones[n]; print("RB pose",n,[round(math.degrees(a),1) for a in pb.rotation_quaternion.to_euler("XYZ")], "loc", [round(c,4) for c in pb.location], "x_axis", tuple(round(c,2) for c in rig.data.bones[n].x_axis))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
