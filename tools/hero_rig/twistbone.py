import bpy, math
from mathutils import Vector, Quaternion
SRC="/home/claude/out/character_rigged_armlimits3.blend"
OUT="/home/claude/out/character_rigged_twist.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
R=math.radians
watch=[f"{n}_{s}" for s in ("l","r") for n in ("fore","hand_new")]
watch=["fore_l_1","fore_l_2","fore_l_3","fore_r_1","fore_r_2","fore_r_3","hand_new_l","hand_new_r","elbow_l_1","elbow_r_1"]
def snap():
    dg=bpy.context.evaluated_depsgraph_get(); out={}
    for n in watch:
        o=bpy.data.objects[n].evaluated_get(dg); me=o.to_mesh(); out[n]=[o.matrix_world@v.co for v in me.vertices]; o.to_mesh_clear()
    return out
before=snap()
# 1) twist bones: wrist half of each forearm, same roll as the forearm
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
info={}
for s in ("l","r"):
    f=eb[f"fore_{s}"]
    t=eb.new(f"foretw_{s}")
    t.head=f.head+(f.tail-f.head)*0.5; t.tail=f.tail.copy(); t.roll=f.roll
    t.parent=f; t.use_connect=False; t.use_deform=True
    info[s]=(f.head.copy(), f.tail.copy())
bpy.ops.object.mode_set(mode='OBJECT')
# 2) weights: 0 up to 40% of the forearm, ramping to 1 at the wrist
def smooth(x): x=max(0.0,min(1.0,x)); return x*x*(3-2*x)
for s in ("l","r"):
    h,tl=info[s]; d=tl-h; L2=d.length_squared
    for i in (1,2,3):
        o=bpy.data.objects[f"fore_{s}_{i}"]; M=o.matrix_world
        vf=o.vertex_groups[f"fore_{s}"]; vt=o.vertex_groups.new(name=f"foretw_{s}")
        for v in o.data.vertices:
            p=M@v.co; t=(p-h).dot(d)/L2
            w=smooth((t-0.40)/0.60)
            base=1.0
            for g in v.groups:
                if g.group==vf.index: base=g.weight
            vf.add([v.index],base*(1-w),'REPLACE'); vt.add([v.index],base*w,'REPLACE')
# 3) twist follows the hand's twist about its own axis
for s in ("l","r"):
    pb=rig.pose.bones[f"foretw_{s}"]; pb.rotation_mode="QUATERNION"
    c=pb.constraints.new('COPY_ROTATION'); c.name="follow_wrist_twist"
    c.target=rig; c.subtarget=f"hand_{s}"
    c.use_x=False; c.use_z=False; c.use_y=True
    c.euler_order='YZX'; c.target_space='LOCAL'; c.owner_space='LOCAL'; c.mix_mode='REPLACE'; c.influence=1.0
# 4) twist now lives in the wrist: forearm bone stays near-neutral, hand takes the twist
for s in ("l","r"):
    for bone,(y0,y1) in ((f"fore_{s}",(-20,20)),(f"hand_{s}",(-80,80))):
        for c in rig.pose.bones[bone].constraints:
            if c.name=="joint_limits": c.min_y,c.max_y=R(y0),R(y1)
bpy.context.view_layer.update()
after=snap()
print("TW rest drift:",round(max(max((a-b).length for a,b in zip(before[n],after[n])) for n in watch),6))
# 5) test: twist the left hand 60 deg about its axis and look at the forearm skin
hl=rig.pose.bones["hand_l"]; hl.rotation_mode="QUATERNION"; hl.rotation_quaternion=Quaternion(Vector((0,1,0)),R(60)); bpy.context.view_layer.update()
print("TW twist bone local quat euler Y deg:", round(math.degrees(rig.pose.bones["foretw_l"].rotation_quaternion.to_euler("YZX").y),1) if False else round(math.degrees(rig.pose.bones["foretw_l"].matrix_basis.to_euler("YZX").y),1))
dg=bpy.context.evaluated_depsgraph_get(); o=bpy.data.objects["fore_l_1"].evaluated_get(dg); me=o.to_mesh()
h,tl=info["l"]; d=tl-h; L2=d.length_squared
base=[v.co.copy() for v in bpy.data.objects["fore_l_1"].data.vertices]
rows={}
for v,b0 in zip(me.vertices,base):
    p=o.matrix_world@b0; t=(p-h).dot(d)/L2
    axis=d.normalized()
    r0=(p-h)-axis*((p-h).dot(axis)); r1=((o.matrix_world@v.co)-h); r1=r1-axis*(r1.dot(axis))
    if r0.length<1e-4 or r1.length<1e-4: continue
    ang=math.degrees(r0.angle(r1)); k=int(t*10)
    rows.setdefault(k,[]).append(ang)
o.to_mesh_clear()
print("TW skin twist by position along forearm (0=elbow, 1=wrist):",[(k/10,round(sum(a)/len(a),1)) for k,a in sorted(rows.items())])
hl.rotation_quaternion=(1,0,0,0); bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
