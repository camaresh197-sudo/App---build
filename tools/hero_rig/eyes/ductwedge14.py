import bpy, bmesh, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_e14.blend")
sc=bpy.context.scene; arm=bpy.data.objects['character_rig']
TCI=math.radians(24); HU=math.radians(14); HL=math.radians(18); INNER=0.75
LEN=math.radians(12.0); NS=28; NV=18; RP=0.0313
def dirv(th,ph): return Vector((math.sin(th)*math.cos(ph),-math.cos(th)*math.cos(ph),math.sin(ph)))
mat=bpy.data.materials.new('TearDuct'); mat.use_nodes=True
b=[n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'][0]
b.inputs['Base Color'].default_value=(0.30,0.03,0.03,1); b.inputs['Roughness'].default_value=0.8
for k in ('Specular IOR Level','Coat Weight','Sheen Weight'):
    if k in b.inputs: b.inputs[k].default_value=0.0
mat.diffuse_color=(0.30,0.03,0.03,1)
cs={}
for s in 'lr':
    w=bpy.data.objects['white_%s_1'%s]; ws=[w.matrix_world@v.co for v in w.data.vertices]; cs[s]=sum(ws,Vector())/len(ws)
mid=(cs['l'].x+cs['r'].x)/2
for s in 'lr':
    c=cs[s]; outer=1.0 if c.x>mid else -1.0; inner=-outer
    a_end=TCI-math.radians(0.25)
    bm=bmesh.new(); grid=[]
    for i in range(NS+1):
        sp=i/NS                                    # 0 = rounded end toward the iris, 1 = the pointed tip in the corner
        a=a_end-LEN*(1.0-sp)
        g=math.sqrt(max(0.0,1.0-(1.0-sp)**2))      # round at the iris end, full rim height at the tip
        base=math.sqrt(max(0.0,1.0-(a/TCI)**2))
        fac=1.0-0.25*(a/TCI); hu=HU*fac*base*g; hl=HL*fac*base*g
        row=[]
        for j in range(NV+1):
            v=j/NV; ph=-hl+(hu+hl)*v
            bulge=0.0007*(1.0-(2*v-1.0)**2)*g
            row.append(bm.verts.new(c+dirv(inner*a,ph)*(RP+bulge)))
        grid.append(row)
    for i in range(NS):
        for j in range(NV):
            f=bm.faces.new((grid[i][j],grid[i+1][j],grid[i+1][j+1],grid[i][j+1]))
    bm.normal_update()
    flip=[f for f in bm.faces if (f.calc_center_median()-c).dot(f.normal)<0]
    if flip: bmesh.ops.reverse_faces(bm,faces=flip)
    me=bpy.data.meshes.new('tearduct_%s_mesh'%s); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new('tearduct_%s'%s,me); sc.collection.objects.link(o); o.data.materials.append(mat)
    vg=o.vertex_groups.new(name='head'); vg.add(list(range(len(me.vertices))),1.0,'REPLACE')
    md=o.modifiers.new('Armature','ARMATURE'); md.object=arm
    print("DW %s inner_sign=%+d faces=%d flipped=%d"%(s,inner,len(me.polygons),len(flip)))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_f14.blend")
print("DWSAVED")
