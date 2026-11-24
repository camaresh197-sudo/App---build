import bpy,sys,math
from mathutils import Vector,Matrix
src,tag=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
sc=bpy.context.scene;a=bpy.data.objects['character_rig']
bpy.context.view_layer.objects.active=a;bpy.ops.object.mode_set(mode='POSE')
P=a.pose.bones
def rot(name,axis,deg):
    pb=P[name];M=pb.matrix.copy();h=M.translation.copy()
    R=Matrix.Translation(h)@Matrix.Rotation(math.radians(deg),4,axis)@Matrix.Translation(-h)
    pb.matrix=R@M;bpy.context.view_layer.update()
def reset():
    for pb in P:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0)
    bpy.context.view_layer.update()
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE'
sc.display.shading.single_color=(0.85,0.7,0.6);sc.display.shading.show_xray=False
sc.render.resolution_x=700;sc.render.resolution_y=800
w=bpy.data.worlds.new('w');w.color=(1,1,1);sc.world=w
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
def shot(name,loc,rot_,scale,z):
    cam.data.ortho_scale=scale;cam.location=loc;cam.rotation_euler=rot_
    sc.render.filepath=f'/home/claude/out/{tag}_{name}.png';bpy.ops.render.render(write_still=True)
FR=((math.pi/2,0,0));SD=((math.pi/2,0,math.pi/2))
# A: arms up with shrug
reset()
rot('clav_l','Y',18);rot('clav_r','Y',-18)
rot('uarm_l','Y',95);rot('uarm_r','Y',-95)
shot('A_armsup',(0.09,-3,1.2),FR,1.5,1.2)
# B: arms forward, elbows bent, spine and neck bend
reset()
for n,d in(('spine',10),('spine2',10),('chest',8),('neck',8),('neck2',10)):rot(n,'X',d)
rot('uarm_l','X',-80);rot('uarm_r','X',-80)
rot('fore_l','X',-80);rot('fore_r','X',-80)
shot('B_forward',(3,0,1.1),SD,1.9,1.1)
# C: leg swing
reset()
rot('thigh_r','X',-50);rot('shin_r','X',70);rot('thigh_l','X',15)
shot('C_legs',(3,0,0.6),SD,1.4,0.6)
