import bpy, bmesh, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_lids_rebuilt14.blend")
sc=bpy.context.scene; arm=bpy.data.objects['character_rig']
def lerp(a,b,t): return tuple(a[i]*(1-t)+b[i]*t for i in range(3))
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
# 1. iris: radial colour (light amber near the pupil, deep amber, dark limbal ring at the rim) via a vertex colour
for s in 'lr':
    o=bpy.data.objects['iris_%s_1'%s]; me=o.data
    ws=[o.matrix_world@v.co for v in me.vertices]; ctr=sum(ws,Vector())/len(ws)
    R=max((p-ctr).length for p in ws)
    ca=me.color_attributes.get('IrisCol') or me.color_attributes.new('IrisCol','FLOAT_COLOR','POINT')
    for v,p in zip(me.vertices,ws):
        t=(p-ctr).length/R
        inner=lerp((0.62,0.30,0.07),(0.30,0.12,0.02),smooth(0.25,0.75,t))
        col=lerp(inner,(0.07,0.035,0.02),smooth(0.80,0.97,t))
        ca.data[v.index].color=(*col,1.0)
    print("DF iris %s radius=%.4f"%(s,R))
m=bpy.data.materials['Material_9']; nt=m.node_tree
b=[n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'][0]
for l in list(nt.links):
    if l.to_node==b and l.to_socket.name=='Base Color': nt.links.remove(l)
an=nt.nodes.new('ShaderNodeAttribute'); an.attribute_name='IrisCol'; an.attribute_type='GEOMETRY'
nt.links.new(an.outputs['Color'],b.inputs['Base Color'])
b.inputs['Roughness'].default_value=0.6
if 'Specular IOR Level' in b.inputs: b.inputs['Specular IOR Level'].default_value=0.2
# 2. catchlight + tear ducts, skinned to the head bone
mat_cl=bpy.data.materials.new('EyeCatch'); mat_cl.use_nodes=True
bc=[n for n in mat_cl.node_tree.nodes if n.type=='BSDF_PRINCIPLED'][0]
bc.inputs['Base Color'].default_value=(1,1,1,1); bc.inputs['Emission Color'].default_value=(1,1,1,1); bc.inputs['Emission Strength'].default_value=2.0
mat_cl.diffuse_color=(1,1,1,1)
mat_td=bpy.data.materials.new('TearDuct'); mat_td.use_nodes=True
bt=[n for n in mat_td.node_tree.nodes if n.type=='BSDF_PRINCIPLED'][0]
bt.inputs['Base Color'].default_value=(0.80,0.30,0.28,1); bt.inputs['Roughness'].default_value=0.5
mat_td.diffuse_color=(0.80,0.30,0.28,1)
def dirv(th,ph): return Vector((math.sin(th)*math.cos(ph),-math.cos(th)*math.cos(ph),math.sin(ph)))
cs={}
for s in 'lr':
    w=bpy.data.objects['white_%s_1'%s]; ws=[w.matrix_world@v.co for v in w.data.vertices]; cs[s]=sum(ws,Vector())/len(ws)
mid=(cs['l'].x+cs['r'].x)/2
def blob(name,centre,ax,ay,az,rx,ry,rz,mat):
    bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=24,v_segments=12,radius=1.0)
    for v in bm.verts: v.co=centre+ax*(v.co.x*rx)+ay*(v.co.y*ry)+az*(v.co.z*rz)
    me=bpy.data.meshes.new(name+'_mesh'); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); o.data.materials.append(mat)
    vg=o.vertex_groups.new(name='head'); vg.add(list(range(len(me.vertices))),1.0,'REPLACE')
    md=o.modifiers.new('Armature','ARMATURE'); md.object=arm
for s in 'lr':
    c=cs[s]; outer=1.0 if c.x>mid else -1.0
    # catchlight: small bright dot on the upper side of the iris, nearer the outer edge
    io=bpy.data.objects['iris_%s_1'%s]; iws=[io.matrix_world@v.co for v in io.data.vertices]; ictr=sum(iws,Vector())/len(iws)
    front=min(p.y for p in iws)
    cl=Vector((ictr.x+outer*0.0042,front-0.0004,ictr.z+0.0045))
    blob('catch_%s'%s,cl,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)),0.0014,0.0006,0.0014,mat_cl)
    # tear duct at the inner corner (toward the nose), a small pink bump on the eyeball between the lids
    th=-outer*math.radians(34); ph=math.radians(-2)
    d=dirv(th,ph); tdir=Vector((math.cos(th),math.sin(th),0)); up=Vector((0,0,1))
    print("DF %s outer=%+d tearduct_theta=%.0f deg"%(s,outer,math.degrees(th)))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_a14.blend")
print("DFSAVED")
