import bpy, bmesh, sys
from mathutils import Vector
src=sys.argv[sys.argv.index('--')+1]; out=sys.argv[sys.argv.index('--')+2]
bpy.ops.wm.open_mainfile(filepath=src)
sc=bpy.context.scene; rig=bpy.data.objects["character_rig"]
for o in bpy.data.objects:
    if o.data is not None and hasattr(o.data,"shape_keys") and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks[1:]: kb.value=0.0
    if o.type=='MESH' and (o.name.startswith("hat") or o.name.startswith("hair")): o.hide_render=True
COL={"chest":(1,0.1,0.1,1),"clav":(1,0.8,0,1),"shoulder":(0.1,0.8,0.1,1),"uarm":(0.1,0.4,1,1),"spine2":(0.8,0.2,0.8,1),"neck":(0,0.9,0.9,1),"fore":(1,0.5,0,1)}
def mk(name,a,b,col,r=0.008):
    bm=bmesh.new(); d=b-a
    bmesh.ops.create_cone(bm,cap_ends=True,segments=10,radius1=r,radius2=r*0.2,depth=d.length)
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); sc.collection.objects.link(o)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(d.normalized())
    o.location=(a+b)/2; o.color=col; o.show_in_front=True
    return o
def sph(name,p,col,r=0.014):
    bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=12,v_segments=8,radius=r)
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); o.location=p; o.color=col; o.show_in_front=True
for b in rig.data.bones:
    n=b.name
    key=None
    for k in COL:
        if n.startswith(k): key=k
    if key is None or n in ("chest",) and False: continue
    mk("v_"+n,b.head_local,b.tail_local,COL[key]); sph("j_"+n,b.head_local,COL[key])
cd=bpy.data.cameras.new("O"); cd.type='ORTHO'; cd.ortho_scale=0.75
cam=bpy.data.objects.new("O",cd); sc.collection.objects.link(cam); sc.camera=cam
sc.render.engine='BLENDER_WORKBENCH'; sc.render.resolution_x=800; sc.render.resolution_y=800
sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='OBJECT'; sh.show_xray=True; sh.xray_alpha=0.25
tgt=Vector((0.09,0,1.27)); loc=tgt+Vector((0,-4,0)); cam.location=loc; cam.rotation_euler=(tgt-loc).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=out; bpy.ops.render.render(write_still=True)
