import bpy, math, sys
from mathutils import Vector
SRC="/home/claude/out/character_rigged_bones.blend"
OUT="/home/claude/out/character_rigged_shoulders.blend"
PP={'1':dict(cap=0.98,up=0.92,down=2.0,ysq=0.90,slope=0.0,rep=0.08),'2':dict(cap=0.70,up=0.85,down=1.3,ysq=0.90,slope=0.02,rep=0.08)}
bpy.ops.wm.open_mainfile(filepath=SRC)
rig=bpy.data.objects["character_rig"]
def sm(x): x=max(0,min(1,x)); return x*x*(3-2*x)
for side,sg in (("l",-1),("r",1)):
    ub=rig.data.bones["uarm_"+side]; J=ub.head_local.copy(); a=(ub.tail_local-ub.head_local).normalized()
    for nm in ("shoulder_%s_1"%side,"shoulder_%s_2"%side):
        P=PP[nm[-1]]; o=bpy.data.objects[nm]; M=o.matrix_world; Mi=M.inverted(); me=o.data
        if "uarm_"+side not in o.vertex_groups: o.vertex_groups.new(name="uarm_"+side)
        gs=o.vertex_groups["shoulder_"+side]; gu=o.vertex_groups["uarm_"+side]
        for v in me.vertices:
            p=M@v.co; q=p-J; t=q.dot(a); rad=q-a*t
            if t>0: t2=t*P['down']
            else:   t2=t*P['up']
            rad=rad*P['cap']
            q2=a*t2+rad
            # tuck the tail of the deltoid inside the arm tube to avoid a jagged seam
            tt=q2.dot(a); rr=q2-a*tt; ln=rr.length
            if ln>0.046:
                k=1-sm((tt-0.05)/0.07)*(1-0.046/ln); rr=rr*k; q2=a*tt+rr
            q2.y*=P['ysq']
            # trapezius slope on inner top
            i=-sg*q2.x
            if i>0 and q2.z>0: q2.z-=P['slope']*sm(i/0.07)*sm(q2.z/0.03)
            v.co=Mi@(J+q2)
            # weights: blend into uarm below the joint
            wu=sm(t2/P['rep']) if t2>0 else 0.0
            gs.add([v.index],1.0-wu,'REPLACE')
            if wu>0: gu.add([v.index],wu,'REPLACE')
        me.update()
# trapezius: lift torso top toward the shoulders
o=bpy.data.objects["torso_cartoon"]; M=o.matrix_world; Mi=M.inverted()
for v in o.data.vertices:
    p=M@v.co; dx=abs(p.x-0.09)
    lift=0.045*sm((dx-0.02)/0.07)*sm((p.z-1.29)/0.06)
    if lift>0: v.co=Mi@Vector((p.x,p.y,p.z+lift))
o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT,compress=True)
print("SAVED")
