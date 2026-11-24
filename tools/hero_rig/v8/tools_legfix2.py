import bpy,math
from mathutils import Vector,Matrix
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v9_legs.blend")
a=bpy.data.objects['character_rig']
B=a.data.bones
def dom(o):
    cnt={}
    for v in o.data.vertices:
        if v.groups:
            g=max(v.groups,key=lambda x:x.weight).group
            n=o.vertex_groups[g].name;cnt[n]=cnt.get(n,0)+1
    return max(cnt,key=cnt.get) if cnt else None
meshes={}
for o in bpy.data.objects:
    if o.type=='MESH':
        d=dom(o)
        if d:meshes.setdefault(d,[]).append(o)
def vmap(o,fn):
    M=o.matrix_world;Mi=M.inverted()
    for v in o.data.vertices:v.co=Mi@fn(M@v.co)
    o.data.update()
bones0={n:(B[n].head_local.copy(),B[n].tail_local.copy()) for n in B.keys()}
# ---- right leg: hip level and thigh length equal to left
hipL=B['hip_l'].head_local.z; kneeL=B['knee_l'].head_local.z
hipR=bones0['hip_r'][0].z; kneeR=bones0['knee_r'][0].z
s=(hipL-kneeL)/(hipR-kneeR)
dz_all=hipL-hipR            # whole leg
dz_low=(kneeL-kneeR)-dz_all  # extra for knee and below
R_all=['hip_r','thigh_r'];R_low=['knee_r','shin_r','ankle_r','foot_r','toe_r']
def right_fn(isthigh):
    def f(p):
        p=p+Vector((0,0,dz_all))
        if isthigh and p.z<hipL:p.z=hipL-(hipL-p.z)*s
        return p
    return f
for n in R_all:
    for o in meshes.get(n,[]):vmap(o,right_fn(n=='thigh_r'))
for n in R_low:
    for o in meshes.get(n,[]):vmap(o,lambda p:p+Vector((0,0,dz_all+dz_low)))
# ---- left foot pitch
P=bones0['ankle_l'][0]
fh,ft=bones0['foot_l']
vL=ft-fh
fr=B['foot_r'];vR=fr.tail_local-fr.head_local
ang=lambda v:math.atan2(v.z,-v.y)
th=ang(vR)-ang(vL)   # rotate about X so left foot slope equals right
Rot=Matrix.Rotation(-th,3,'X')  # sign checked below
def lf(p):return P+Rot@(p-P)
test=P+Rot@(fh-P);print("foot_l pitch before",math.degrees(ang(vL)),"right",math.degrees(ang(vR)),"rot",math.degrees(th))
for n in['ankle_l','foot_l','toe_l']:
    for o in meshes.get(n,[]):vmap(o,lf)
bpy.context.view_layer.objects.active=a
bpy.ops.object.mode_set(mode='EDIT')
eb=a.data.edit_bones
for n in R_all:
    eb[n].head=bones0[n][0]+Vector((0,0,dz_all));eb[n].tail=bones0[n][1]+Vector((0,0,dz_all))
eb['thigh_r'].tail=bones0['thigh_r'][1]+Vector((0,0,dz_all+dz_low))
for n in R_low:
    eb[n].head=bones0[n][0]+Vector((0,0,dz_all+dz_low));eb[n].tail=bones0[n][1]+Vector((0,0,dz_all+dz_low))
for n in['ankle_l','foot_l','toe_l']:
    h,t=bones0[n]
    eb[n].head=h if n=='ankle_l' else lf(h);eb[n].tail=lf(t)
bpy.ops.object.mode_set(mode='OBJECT')
r=lambda v:[round(x,3) for x in v]
for n in('hip','thigh','knee','shin','ankle','foot','toe'):
    print(n,"L",r(B[n+'_l'].head_local),r(B[n+'_l'].tail_local),"R",r(B[n+'_r'].head_local),r(B[n+'_r'].tail_local))
for n in('ankle','foot','toe','shin','thigh'):
    for s_ in 'lr':
        for o in meshes.get(f'{n}_{s_}',[]):
            ws=[o.matrix_world@v.co for v in o.data.vertices]
            print(o.name,"z",round(min(w.z for w in ws),3),round(max(w.z for w in ws),3),"y",round(min(w.y for w in ws),3),round(max(w.y for w in ws),3))
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/work/hero_v10_legs2.blend")
