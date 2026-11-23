import bpy, bmesh, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_corners6k2.blend")
dg=bpy.context.evaluated_depsgraph_get()
head=bpy.data.objects['head_12']; hev=head.evaluated_get(dg); HM=head.matrix_world; HMi=HM.inverted()
TCO=math.radians(62); TCI=math.radians(24); TC=TCO; HU=math.radians(14); HL=math.radians(18)
TMAX=math.radians(95); PMAX=math.radians(55); SNAP=math.radians(1.6)
RL_U=0.0330; RL_L=0.0327
OUTER={'l':-1.0,'r':1.0}
CUR=['l']
def eyeshape(th,H):
    outer_side = th*OUTER[CUR[0]]>0
    tc = TCO if outer_side else TCI
    a=abs(th); return 0.0 if a>=tc else H*(1.0 if outer_side else (1.0-0.25*(a/tc)))*math.sqrt(max(0.0,1.0-(a/tc)**2))      # elliptical arch, outer corner 62 deg, inner corner 40 deg
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
def dirv(th,ph): return Vector((math.sin(th)*math.cos(ph),-math.cos(th)*math.cos(ph),math.sin(ph)))
for s in 'lr':
    CUR[0]=s
    w=bpy.data.objects['white_%s_1'%s]; ws=[w.matrix_world@v.co for v in w.data.vertices]; c=sum(ws,Vector())/len(ws)
    for n,upper in [('lidu_%s_0',True),('lidl_%s_0',False)]:
        o=bpy.data.objects[n%s]; Mi=o.matrix_world.inverted()
        RL=RL_U if upper else RL_L
        rimf=(lambda th: eyeshape(th,HU)) if upper else (lambda th: -eyeshape(th,HL))
        bm=bmesh.new()
        bmesh.ops.create_uvsphere(bm,u_segments=128,v_segments=64,radius=1.0,calc_uvs=True)
        def tp(co):
            r=co.length; return math.atan2(co.x,-co.y), math.asin(max(-1,min(1,co.z/r)))
        keep=[]
        for f in bm.faces:
            cen=sum((v.co for v in f.verts),Vector())/len(f.verts)
            th,ph=tp(cen)
            rim=rimf(th)
            if (upper and ph>rim) or ((not upper) and ph<rim): keep.append(f)
        drop=[f for f in bm.faces if f not in set(keep)]
        bmesh.ops.delete(bm,geom=drop,context='FACES')
        loose=[v for v in bm.verts if not v.link_faces]
        if loose: bmesh.ops.delete(bm,geom=loose,context='VERTS')
        # place vertices: exact rim curve, shell radius, sink the outer edge into the skin
        bset={v.index for v in bm.verts if any(e.is_boundary for e in v.link_edges)}
        miss=0
        for v in bm.verts:
            th,ph=tp(v.co)
            rim=rimf(th)
            if v.index in bset: ph=rim            # every vertex on the opening edge sits exactly on the curve
            d=dirv(th,ph)
            cen=dirv(OUTER[s]*math.radians(19),0.0)
            rho=math.acos(max(-1.0,min(1.0,d.dot(cen))))
            soft=smooth(math.radians(45),math.radians(80),rho)
            rad=RL
            if soft>0:
                ok2,loc2,n2,i2=hev.ray_cast(HMi@c,(HMi.to_3x3()@d).normalized())
                if ok2:
                    dsk=(HM@loc2-c).length
                    rad=RL+(max(0.0320,min(RL,dsk-0.0003))-RL)*soft      # sink the outer shell toward the skin so no hard ring shows
            sp=c+d*rad
            wgt=0.0
            if wgt>0:
                ok,loc,nn,i=hev.ray_cast(HMi@c,(HMi.to_3x3()@d).normalized())
                if ok: sp=sp.lerp(HM@loc-d*0.0004,wgt)
                else: miss+=1
            v.co=Mi@sp
        nf=len(bm.faces); nv=len(bm.verts)
        bm.to_mesh(o.data); bm.free(); o.data.update()
        vg=o.vertex_groups[0]; vg.add(list(range(len(o.data.vertices))),1.0,'REPLACE')
        print("RB boundary=%d"%len(bset)); print("RB %-10s faces=%d verts=%d no_skin_hit=%d groups=%s mods=%s"%(n%s,nf,nv,miss,[g.name for g in o.vertex_groups],[m.type for m in o.modifiers]))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_lids_rebuilt14.blend")
print("RBSAVED")
