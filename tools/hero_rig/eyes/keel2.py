import bpy, math, collections
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_corners6.blend")
h=bpy.data.objects['head_12']; M=h.matrix_world; Mi=M.inverted().to_3x3()
ws=[M@v.co for v in h.data.vertices]
xs=[p.x for p in ws]; MID=(max(xs)+min(xs))/2
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
HW=0.045; BIN=0.004; Z0=1.545; Z1=1.600; DOME=0.006
bins=collections.defaultdict(list)
for p in ws:
    if p.y<-0.03 and 0.040<=abs(p.x-MID)<=0.050: bins[round(p.z/BIN)].append(p.y)
def ys_at(z):
    k=round(z/BIN)
    for d in range(0,6):
        for kk in (k-d,k+d):
            if bins.get(kk): return sum(bins[kk])/len(bins[kk])
    return None
dg0=bpy.context.evaluated_depsgraph_get(); hev0=h.evaluated_get(dg0); HMi0=M.inverted()
def surf_y(hev,x,z):
    ok,loc,n,i=hev.ray_cast(HMi0@Vector((x,-1.0,z)),(HMi0.to_3x3()@Vector((0,1,0))))
    return (M@loc).y if ok else None
brows=[o for o in bpy.data.objects if o.name.startswith('brow_') and o.type=='MESH']
old_y={}
for o in brows:
    bw=[o.matrix_world@v.co for v in o.data.vertices]; cx=sum(p.x for p in bw)/len(bw); cz=sum(p.z for p in bw)/len(bw)
    old_y[o.name]=(cx,cz,surf_y(hev0,cx,cz))
kb=h.data.shape_keys.key_blocks if h.data.shape_keys else None
moved=0; maxmove=0.0; mid_before={}; mid_after={}
for i,v in enumerate(h.data.vertices):
    p=M@v.co
    dx=p.x-MID
    if p.y>-0.03 or abs(dx)>=HW or p.z<Z0: continue
    wz=smooth(Z0,Z1,p.z)*(1.0-smooth(1.640,1.700,p.z))
    ys=ys_at(p.z)
    if ys is None: continue
    ym=ys-DOME
    yt=ym+(ys-ym)*(dx/HW)**2                    # gentle dome: highest at the middle, meets the side surface at +-45 mm
    if p.y<yt:                                   # only pull the front surface back, never push it out
        dy=(yt-p.y)*wz
        dl=Mi@Vector((0,dy,0)); v.co=v.co+dl
        if kb:
            for k in kb: k.data[i].co=k.data[i].co+dl
        moved+=1; maxmove=max(maxmove,dy)
h.data.update()
bpy.context.view_layer.update()
dg1=bpy.context.evaluated_depsgraph_get(); hev1=h.evaluated_get(dg1)
for o in brows:
    cx,cz,y0=old_y[o.name]; y1=surf_y(hev1,cx,cz)
    if y0 is not None and y1 is not None and y1>y0:
        sh=y1-y0; Mo=o.matrix_world.inverted().to_3x3()
        for v in o.data.vertices: v.co=v.co+Mo@Vector((0,sh,0))
        o.data.update(); print("KL brow %s moved back %.4f m"%(o.name,sh))
print("KL mid_x=%.4f moved_verts=%d max_recede=%.4f m"%(MID,moved,maxmove))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_corners6k2.blend")
print("KLSAVED")
