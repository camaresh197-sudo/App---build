import bpy, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_a14.blend")
K=1.10
cs={}
for s in 'lr':
    w=bpy.data.objects['white_%s_1'%s]; ws=[w.matrix_world@v.co for v in w.data.vertices]; cs[s]=sum(ws,Vector())/len(ws)
def sscale(p,c,a,k):
    u=p-c; r=u.length; ud=u/r; ca=max(-1,min(1,ud.dot(a))); al=math.acos(ca)
    perp=ud-a*ca
    if perp.length<1e-9: return p
    pd=perp.normalized(); na=min(al*k,2.6)
    return c+(a*math.cos(na)+pd*math.sin(na))*r
for s in 'lr':
    c=cs[s]
    io=bpy.data.objects['iris_%s_1'%s]; iw=[io.matrix_world@v.co for v in io.data.vertices]; ic=sum(iw,Vector())/len(iw)
    a=(ic-c).normalized()
    for n in ['iris_%s_1'%s,'pupil_%s_0'%s]:
        o=bpy.data.objects[n]; M=o.matrix_world; Mi=M.inverted()
        rr=0.0319 if n.startswith('iris') else 0.0321
        for v in o.data.vertices:
            p=sscale(M@v.co,c,a,K); v.co=Mi@(c+(p-c).normalized()*rr)
        o.data.update()
    cl=bpy.data.objects['catch_%s'%s]; M=cl.matrix_world; Mi=M.inverted()
    cw=[M@v.co for v in cl.data.vertices]; cc=sum(cw,Vector())/len(cw); newc=sscale(cc,c,a,K)
    for v in cl.data.vertices: v.co=Mi@((M@v.co)+(newc-cc))
    cl.data.update()
    iw=[io.matrix_world@v.co for v in io.data.vertices]; print("IS %s iris half_width now %.4f"%(s,(max(p.x for p in iw)-min(p.x for p in iw))/2))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_b14.blend")
print("ISSAVED")
