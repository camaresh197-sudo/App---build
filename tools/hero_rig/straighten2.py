import bpy
from mathutils import Vector
SRC="/home/claude/out/character_rigged_legsmove2.blend"
OUT="/home/claude/out/character_rigged_straight2.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
bones=rig.data.bones
# capture old joint positions (armature space; rig is identity)
old={}
for n in ["thigh_l","shin_l","knee_l","ankle_l","foot_l","toe_l","thigh_r","shin_r","knee_r","ankle_r","foot_r","toe_r"]:
    b=bones[n]; old[n]=(b.head_local.copy(), b.tail_local.copy())
newpos={}   # bone -> (head, tail) new
dels={}     # bone -> (dh, dt) for mesh skinning
for s in ("l","r"):
    H=old["thigh_"+s][0]                       # hip joint: unchanged
    Kn=Vector((H.x,H.y,old["thigh_"+s][1].z))  # knee: straight under hip
    An=Vector((H.x,H.y,old["shin_"+s][1].z))   # ankle: straight under hip
    dK=Kn-old["thigh_"+s][1]; dA=An-old["shin_"+s][1]
    # thigh: head fixed, tail to knee
    newpos["thigh_"+s]=(old["thigh_"+s][0], Kn)
    dels["thigh_"+s]=(Vector(),dK)
    # knee helper and shin: head at knee, tail at ankle
    newpos["knee_"+s]=(old["knee_"+s][0]+dK, old["knee_"+s][1]+dK); dels["knee_"+s]=(dK,dK)
    newpos["shin_"+s]=(Kn, An); dels["shin_"+s]=(dK,dA)
    for n in ("ankle_"+s,"foot_"+s,"toe_"+s):
        h,t=old[n]; newpos[n]=(h+dA,t+dA); dels[n]=(dA,dA)
# write bones
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
for n,(h,t) in newpos.items():
    eb[n].head=h; eb[n].tail=t
bpy.ops.object.mode_set(mode='OBJECT')
# skin the meshes with the same bone deltas (linear blend along each bone)
def seg_t(p,h,t):
    d=t-h; L=d.length_squared
    return 0.0 if L<1e-9 else max(0.0,min(1.0,(p-h).dot(d)/L))
done=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.data.vertices: continue
    if not any(o.name.startswith(p) for p in ("thigh_","knee_","shin_","ankle_","foot_","toe_","hip_","pelvis_new")): continue
    M=o.matrix_world; Mi=M.inverted()
    for v in o.data.vertices:
        p=M@v.co
        tot=0.0; disp=Vector()
        for g in v.groups:
            name=o.vertex_groups[g.group].name
            if name not in bones: continue
            w=g.weight; tot+=w
            if name in dels:
                if name in old: h,t=old[name]
                else: h,t=bones[name].head_local, bones[name].tail_local
                tt=seg_t(p,h,t)
                dh,dt=dels[name]
                disp+= w*((1-tt)*dh+tt*dt)
        if tot>0:
            v.co = Mi@(p+disp/tot)
    if o.data.shape_keys:
        pass
    o.data.update(); done.append(o.name)
print("skinned:", len(done))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
