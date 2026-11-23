import bpy, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_corners6.blend")
RL=0.0330; MARGIN=0.0004
OUTER={'l':-1.0,'r':1.0}
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
def dirv(th,ph): return Vector((math.sin(th)*math.cos(ph),-math.cos(th)*math.cos(ph),math.sin(ph)))
cs={}
for s in 'lr':
    w=bpy.data.objects['white_%s_1'%s]; ws=[w.matrix_world@v.co for v in w.data.vertices]; cs[s]=sum(ws,Vector())/len(ws)
h=bpy.data.objects['head_12']; M=h.matrix_world; Mi=M.inverted().to_3x3()
kb=h.data.shape_keys.key_blocks if h.data.shape_keys else None
moved=0; maxd=0.0
for i,v in enumerate(h.data.vertices):
    p=M@v.co
    best=Vector((0,0,0)); 
    for s in 'lr':
        c=cs[s]; u=p-c; r=u.length
        if r<1e-6 or u.y>0.005: continue                      # only the front of the face
        d=u/r; cen=dirv(OUTER[s]*math.radians(19),0.0)
        rho=math.acos(max(-1.0,min(1.0,d.dot(cen))))
        w=1.0-smooth(math.radians(40),math.radians(90),rho)
        tgt=RL-MARGIN
        if r<tgt and w>0:
            delta=d*((tgt-r)*w)
            if delta.length>best.length: best=delta
    if best.length>0:
        dl=Mi@best; v.co=v.co+dl
        if kb:
            for k in kb: k.data[i].co=k.data[i].co+dl
        moved+=1; maxd=max(maxd,best.length)
h.data.update()
print("PH raised_verts=%d max_raise=%.4f m"%(moved,maxd))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_corners6h.blend")
