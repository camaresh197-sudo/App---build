import bpy, math
from mathutils import Vector, Quaternion
SRC="/home/claude/out/character_rigged_headback.blend"
OUT="/home/claude/out/character_rigged_armrest.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
def moved(pb):
    D=pb.matrix @ rig.data.bones[pb.name].matrix_local.inverted()
    return max(abs(D[i][j]-(1.0 if i==j else 0.0)) for i in range(4) for j in range(4))>1e-6
posed=[pb.name for pb in rig.pose.bones if moved(pb)]
print("AR posed bones:", len(posed))
watch=["uarm_l_1","uarm_r_1","fore_l_1","fore_r_1","hand_new_l","hand_new_r","elbow_l_1","elbow_r_1","shoulder_l_1","shoulder_r_1","head_12","torso_cartoon","thigh_l_1"]
def snap():
    dg=bpy.context.evaluated_depsgraph_get(); out={}
    for n in watch:
        o=bpy.data.objects[n].evaluated_get(dg); me=o.to_mesh()
        out[n]=[o.matrix_world@v.co for v in me.vertices]; o.to_mesh_clear()
    return out
before=snap()
# 1) bake the current (A-pose) deformation into the meshes that are weighted to posed bones
dg=bpy.context.evaluated_depsgraph_get()
baked=[]; skipped=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not any(m.type=='ARMATURE' for m in o.modifiers): continue
    gnames={g.index:g.name for g in o.vertex_groups}
    uses=any(gnames.get(g.group) in posed and g.weight>0 for v in o.data.vertices for g in v.groups)
    if not uses: continue
    if o.data.shape_keys:
        skipped.append(o.name); continue
    ev=o.evaluated_get(dg); me=ev.to_mesh()
    assert len(me.vertices)==len(o.data.vertices)
    for v,e in zip(o.data.vertices,me.vertices): v.co=e.co
    ev.to_mesh_clear(); o.data.update(); baked.append(o.name)
print("AR baked meshes:", len(baked), "skipped (shape keys, posed weights):", skipped)
# 2) pose -> rest
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
after=snap()
worst=0
for n in watch:
    m=max((a-b).length for a,b in zip(before[n],after[n])); worst=max(worst,m)
print("AR worst mesh drift (m):", round(worst,6))
still=[pb.name for pb in rig.pose.bones if pb.location.length>1e-6 or abs(pb.rotation_quaternion.w-1)>1e-6]
print("AR bones still posed:", still)
B=rig.data.bones
for n in ("uarm_l","uarm_r","fore_l","fore_r","hand_l","hand_r"):
    print("AR rest",n,"head",tuple(round(c,3) for c in B[n].head_local),"tail",tuple(round(c,3) for c in B[n].tail_local))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
