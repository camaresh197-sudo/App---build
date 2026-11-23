import bpy, math
from mathutils import Vector, Matrix
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_d14.blend")
ALPHA=math.radians((62.0-24.0)/2.0)       # opening runs 29 deg (inner) .. 62 deg (outer): centre is 16.5 deg toward the outer side
cs={}
for s in 'lr':
    w=bpy.data.objects['white_%s_1'%s]; ws=[w.matrix_world@v.co for v in w.data.vertices]; cs[s]=sum(ws,Vector())/len(ws)
mid=(cs['l'].x+cs['r'].x)/2
for s in 'lr':
    c=cs[s]; outer=1.0 if c.x>mid else -1.0
    io=bpy.data.objects['iris_%s_1'%s]; iw=[io.matrix_world@v.co for v in io.data.vertices]; ic=sum(iw,Vector())/len(iw)-c
    cur=math.atan2(ic.x,-ic.y)                       # where the iris sits now (0 = straight ahead, + toward +x)
    target=outer*ALPHA
    R=Matrix.Rotation(target-cur,3,'Z')
    print("CT %s current_theta=%.1f target=%.1f rotate=%.1f deg"%(s,math.degrees(cur),math.degrees(target),math.degrees(target-cur)))
    for n in ['iris_%s_1'%s,'pupil_%s_0'%s,'catch_%s'%s]:
        o=bpy.data.objects[n]; M=o.matrix_world; Mi=M.inverted()
        for v in o.data.vertices:
            v.co=Mi@(c+R@((M@v.co)-c))
        o.data.update()
    # move the iris gradient centre with the iris
    o=bpy.data.objects['iris_%s_1'%s]; ws=[o.matrix_world@v.co for v in o.data.vertices]; ctr=sum(ws,Vector())/len(ws)
    m=bpy.data.materials['IrisMat_%s'%s]; mp=[n for n in m.node_tree.nodes if n.type=='MAPPING'][0]
    mp.inputs['Location'].default_value=ctr
    print("CT %s outer=%+d iris_centre_x_offset=%.4f (was ~0)"%(s,outer,ctr.x-c.x))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_e14.blend")
print("CTSAVED")
