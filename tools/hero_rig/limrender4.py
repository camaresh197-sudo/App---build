import bpy, math
from mathutils import Vector, Quaternion
bpy.ops.wm.open_mainfile(filepath="/home/claude/out/character_rigged_armlimits3.blend")
rig=bpy.data.objects["character_rig"]; sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks[1:]: kb.value=0.0
    if o.name.startswith(("hat_","sombrero")): o.hide_render=True
cd=bpy.data.cameras.new("O"); cd.type='ORTHO'; cd.ortho_scale=2.2
cam=bpy.data.objects.new("O",cd); sc.collection.objects.link(cam); sc.camera=cam
ld=bpy.data.lights.new("K",'AREA'); ld.energy=900; ld.size=3
lo=bpy.data.objects.new("K",ld); lo.location=(1.5,-3,2.5); sc.collection.objects.link(lo)
sc.render.engine='BLENDER_WORKBENCH'; sc.render.resolution_x=600; sc.render.resolution_y=600
# each pose = list of (bone, axis, left_deg); right side mirrors Y/Z sign
POSES={"default":[],
 "armsback90":[("uarm","X",90)],
 "armsin90":[("uarm","Z",-90)],
 "elbow150":[("uarm","X",-60),("fore","X",-200)],
 "raise":[("uarm","Z",200),("fore","X",-200)],
 "wristfwd":[("hand","X",-170),("hand","Z",90)]}
tgt=Vector((0.1,0,1.1)); ax3={"X":Vector((1,0,0)),"Y":Vector((0,1,0)),"Z":Vector((0,0,1))}
def apply(spec):
    for pb in rig.pose.bones: pb.rotation_quaternion=(1,0,0,0)
    for bone,ax,deg in spec:
        for s in ("l","r"):
            d=deg if (s=="l" or ax=="X") else -deg
            pb=rig.pose.bones[f"{bone}_{s}"]; pb.rotation_mode="QUATERNION"; pb.rotation_quaternion=Quaternion(ax3[ax],math.radians(d))
    bpy.context.view_layer.update()
for name,spec in POSES.items():
    apply(spec)
    for vn,loc in (("front",Vector((0.1,-4,1.1))),("side",Vector((-4,0,1.1)))):
        cam.location=loc; cam.rotation_euler=(tgt-loc).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=f"/home/claude/render/am_{name}_{vn}.png"; bpy.ops.render.render(write_still=True)
print("WROTE")
