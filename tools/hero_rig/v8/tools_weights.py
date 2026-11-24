import bpy,math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v10_legs2.blend")
a=bpy.data.objects['character_rig'];B=a.data.bones
CX=0.09
cl=lambda x,lo=0,hi=1:max(lo,min(hi,x))
sm=lambda t:t*t*(3-2*t)
def get(o):
    W=[]
    for v in o.data.vertices:
        W.append({o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-4})
    return W
def put(o,W):
    names=set(k for w in W for k in w)|{g.name for g in o.vertex_groups}
    for n in names:
        if n not in o.vertex_groups:o.vertex_groups.new(name=n)
    for g in o.vertex_groups:
        g.remove(list(range(len(o.data.vertices))))
    for n in names:
        g=o.vertex_groups[n]
        for i,w in enumerate(W):
            if w.get(n,0)>1e-4:g.add([i],w[n],'REPLACE')
def norm(w):
    s=sum(w.values())
    if s>0:
        for k in w:w[k]/=s
def take(w,name,share):  # give `share` of total weight to name
    for k in list(w):w[k]*=(1-share)
    w[name]=w.get(name,0)+share
obj=lambda n:bpy.data.objects[n]
# 1 torso: spine/spine2/chest by height, then clav share on upper trap
o=obj('torso_cartoon');W=get(o);M=o.matrix_world
for i,v in enumerate(o.data.vertices):
    w=W[i];p=M@v.co
    S=w.pop('spine',0)+w.pop('chest',0)+w.pop('spine2',0)
    if S>0:
        z=p.z
        ts=sm(cl((z-0.95)/0.09));tc=sm(cl((z-1.15)/0.07))
        sp=1-ts;c=tc;s2=1-sp-c
        for n,x in(('spine',sp),('spine2',s2),('chest',c)):
            if x>1e-4:w[n]=w.get(n,0)+S*x
    if p.z>1.24:
        dx=abs(p.x-CX);t=sm(cl((dx-0.05)/0.12))
        take(w,'clav_l' if p.x<CX else 'clav_r',0.8*t)
    norm(w)
put(o,W)
# 2 shoulder parts: inner edge shares with clav
for s,side in(('l','clav_l'),('r','clav_r')):
    for n in(f'shoulder_{s}_1',f'shoulder_{s}_2'):
        o=obj(n);W=get(o);M=o.matrix_world
        for i,v in enumerate(o.data.vertices):
            p=M@v.co;dx=abs(p.x-CX)
            take(W[i],side,0.5*(1-sm(cl((dx-0.14)/0.10))));norm(W[i])
        put(o,W)
# 3 neck / neck2
for n in('neck_1',):
    o=obj(n);W=get(o);M=o.matrix_world
    for i,v in enumerate(o.data.vertices):
        z=(M@v.co).z;s=sm(cl((z-1.40)/0.10));W[i]={'neck':1-s,'neck2':s}
    put(o,W)
# 4 thumbs
for s in 'lr':
    hand=obj(f'hand_new_{s}');W=get(hand);M=hand.matrix_world
    hb=B[f'hand_{s}'];tb=B[f'thumb_{s}']
    def segd(p,h,t):
        d=t-h;u=cl((p-h).dot(d)/d.length_squared);return (p-(h+d*u)).length
    cands={'current':(tb.head_local.copy(),tb.tail_local.copy())}
    if s=='r':
        lh=B['hand_l'];lt=B['thumb_l']
        oh=lt.head_local-lh.head_local;ot=lt.tail_local-lt.head_local
        cands['mirrored']=(hb.head_local+Vector((-oh.x,oh.y,oh.z)),hb.head_local+Vector((-oh.x,oh.y,oh.z))+Vector((-ot.x,ot.y,ot.z)))
    best=None
    for k,(h,t) in cands.items():
        n=sum(1 for v in hand.data.vertices if segd(M@v.co,h,t)<0.02)
        print("hand",s,k,[round(x,3) for x in h],[round(x,3) for x in t],"verts<20mm:",n)
        if k==('mirrored' if s=='r' else 'current'):best=(n,k,h,t)
    n,k,h,t=best;print("hand",s,"use",k)
    if k!='current':
        bpy.context.view_layer.objects.active=a;bpy.ops.object.mode_set(mode='EDIT')
        e=a.data.edit_bones[f'thumb_{s}'];e.head=h;e.tail=t;bpy.ops.object.mode_set(mode='OBJECT')
    for i,v in enumerate(hand.data.vertices):
        d=segd(M@v.co,h,t);x=cl(1-(d-0.012)/0.02)
        if x>0:take(W[i],f'thumb_{s}',x);norm(W[i])
    put(hand,W)
# report
use={}
for o in bpy.data.objects:
    if o.type=='MESH':
        for g in o.vertex_groups:use[g.name]=use.get(g.name,0)+1
print("still unweighted among body bones:",[n for n in('spine2','neck2','clav_l','clav_r','thumb_l','thumb_r') if n not in use])
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/work/hero_v11_weighted.blend")
