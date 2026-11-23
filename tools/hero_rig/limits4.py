import bpy, math
from mathutils import Vector, Quaternion
SRC="/home/claude/out/character_rigged_armrolls2.blend"
OUT="/home/claude/out/character_rigged_armlimits3.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
R=math.radians
# (bone, (xmin,xmax),(ymin,ymax),(zmin,zmax)) in degrees for the LEFT side; Y and Z are negated for the right side
LIM=[("uarm",(-110,30),(-60,60),(-25,100)),
     ("fore",(-110,5),(-70,70),(-5,5)),
     ("hand",(-70,70),(-10,10),(-20,20))]
for name,(x0,x1),(y0,y1),(z0,z1) in LIM:
    for s in ("l","r"):
        pb=rig.pose.bones[f"{name}_{s}"]; pb.rotation_mode="QUATERNION"
        for c in list(pb.constraints):
            if c.name in("back_swing_limit","joint_limits"): pb.constraints.remove(c)
        c=pb.constraints.new('LIMIT_ROTATION'); c.name="joint_limits"; c.owner_space='LOCAL'
        c.use_limit_x=c.use_limit_y=c.use_limit_z=True
        c.min_x,c.max_x=R(x0),R(x1)
        if s=="l": c.min_y,c.max_y,c.min_z,c.max_z=R(y0),R(y1),R(z0),R(z1)
        else:      c.min_y,c.max_y,c.min_z,c.max_z=R(-y1),R(-y0),R(-z1),R(-z0)
def tip(bone,t,axis,deg):
    pb=rig.pose.bones[bone]; tb=rig.pose.bones[t]
    ax={"X":Vector((1,0,0)),"Y":Vector((0,1,0)),"Z":Vector((0,0,1))}[axis]
    pb.rotation_quaternion=Quaternion(ax,math.radians(deg)); bpy.context.view_layer.update()
    p=rig.matrix_world@tb.tail; out=(round(p.x-0.09,2),round(p.y,2),round(p.z,2))
    pb.rotation_quaternion=(1,0,0,0); bpy.context.view_layer.update(); return out
for bone,t in (("uarm","fore"),("fore","hand")):
    for ax,degs in (("X",(-200,-170,-90,0,30,90)),("Z",(-90,-40,0,150,200))):
        L=[tip(f"{bone}_l",f"{t}_l",ax,d) for d in degs]
        Rr=[tip(f"{bone}_r",f"{t}_r",ax,d if ax=="X" else -d) for d in degs]
        mirror=all(abs(l[0]+r[0])<0.03 and abs(l[1]-r[1])<0.03 and abs(l[2]-r[2])<0.03 for l,r in zip(L,Rr))
        print("LM",bone,ax,"L",list(zip(degs,L)),"mirrors R:",mirror)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED")
