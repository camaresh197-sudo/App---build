import bpy
from mathutils import Vector
SRC="/home/claude/out/character_rigged_hipsbone.blend"
OUT="/home/claude/out/character_rigged_headback.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
bones=rig.data.bones
DY=0.046
old={b.name:(b.head_local.copy(), b.tail_local.copy()) for b in bones}
dels={}
for n,(h,t) in old.items():
    if n=="neck": dels[n]=(Vector(),Vector((0,DY*0.5,0)))
    elif n=="neck2": dels[n]=(Vector((0,DY*0.5,0)),Vector((0,DY,0)))
    elif h.z>=1.46 and not n.startswith(("elbow","fore","hand","fg","fh","thumb","uarm","shoulder","clav","hoop")): dels[n]=(Vector((0,DY,0)),Vector((0,DY,0)))
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
for n,(dh,dt) in dels.items():
    eb[n].head=old[n][0]+dh; eb[n].tail=old[n][1]+dt
bpy.ops.object.mode_set(mode='OBJECT')
def seg_t(p,h,t):
    d=t-h; L=d.length_squared
    return 0.0 if L<1e-9 else max(0.0,min(1.0,(p-h).dot(d)/L))
n_obj=0
for o in bpy.data.objects:
    if o.type!='MESH' or not o.data.vertices: continue
    M=o.matrix_world; Mi=M.inverted()
    touched=False
    disps={}
    for v in o.data.vertices:
        p=M@v.co; tot=0.0; disp=Vector()
        for g in v.groups:
            name=o.vertex_groups[g.group].name
            if name not in old: continue
            w=g.weight; tot+=w
            if name in dels:
                h,t=old[name]; tt=seg_t(p,h,t); dh,dt=dels[name]
                disp+=w*((1-tt)*dh+tt*dt)
        if tot>0 and disp.length>1e-9:
            d_local=Mi.to_3x3()@(disp/tot)
            disps[v.index]=d_local; touched=True
    if not touched: continue
    for idx,d_local in disps.items():
        o.data.vertices[idx].co+=d_local
    if o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks:
            for idx,d_local in disps.items(): kb.data[idx].co+=d_local
    o.data.update(); n_obj+=1
print("CHK bones moved", len(dels), "meshes moved", n_obj)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
