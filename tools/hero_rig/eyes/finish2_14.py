import bpy, bmesh, math, statistics
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_f14.blend")
sc=bpy.context.scene; arm=bpy.data.objects['character_rig']
TCO=math.radians(62); TCI=math.radians(24); HU=math.radians(14); HL=math.radians(18)
OUTER={'l':-1.0,'r':1.0}
def rim(th,H,s):
    outer_side=th*OUTER[s]>0; tc=TCO if outer_side else TCI; a=abs(th)
    return 0.0 if a>=tc else H*(1.0 if outer_side else (1.0-0.25*(a/tc)))*math.sqrt(max(0.0,1.0-(a/tc)**2))
def dirv(th,ph): return Vector((math.sin(th)*math.cos(ph),-math.cos(th)*math.cos(ph),math.sin(ph)))
# 1. lids take the face's own skin tone (average of its texture, or its base colour), slightly deeper
head=bpy.data.objects['head_12']; hm=head.material_slots[0].material; col=(0.85,0.60,0.48)
for n in hm.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:
        px=list(n.image.pixels); k=len(px)//4
        col=tuple(sum(px[i*4+j] for i in range(0,k,max(1,k//4000)))/len(range(0,k,max(1,k//4000))) for j in range(3)); break
    if n.type=='BSDF_PRINCIPLED': col=tuple(n.inputs['Base Color'].default_value[:3])
lid=bpy.data.materials.new('LidSkin'); lid.use_nodes=True
b=[n for n in lid.node_tree.nodes if n.type=='BSDF_PRINCIPLED'][0]
b.inputs['Base Color'].default_value=(col[0]*0.93,col[1]*0.90,col[2]*0.88,1); b.inputs['Roughness'].default_value=0.55
lid.diffuse_color=(*[c*0.9 for c in col],1)
print("FN skin colour used",tuple(round(c,3) for c in col))
for n in ['lidu_l_0','lidl_l_0','lidu_r_0','lidl_r_0']:
    o=bpy.data.objects[n]; o.data.materials.clear(); o.data.materials.append(hm)
# 2. lash line (upper rim) and waterline (lower rim)
def mk(name,rgb,rough=0.7):
    m=bpy.data.materials.new(name); m.use_nodes=True
    bb=[x for x in m.node_tree.nodes if x.type=='BSDF_PRINCIPLED'][0]
    bb.inputs['Base Color'].default_value=(*rgb,1); bb.inputs['Roughness'].default_value=rough
    for k in ('Specular IOR Level','Coat Weight','Sheen Weight'):
        if k in bb.inputs: bb.inputs[k].default_value=0.0
    m.diffuse_color=(*rgb,1); return m
lash=mk('LashLine',(0.025,0.015,0.012)); water=mk('Waterline',(0.55,0.17,0.15))
cs={}
for s in 'lr':
    w=bpy.data.objects['white_%s_1'%s]; ws=[w.matrix_world@v.co for v in w.data.vertices]; cs[s]=sum(ws,Vector())/len(ws)
def strip(name,c,s,upper,mat,w_deg,R):
    bm=bmesh.new(); N=120
    th0=-OUTER[s]*TCI; th1=OUTER[s]*TCO
    rows=[]
    for i in range(N+1):
        th=th0+(th1-th0)*i/N
        r=rim(th,HU if upper else HL,s)
        if upper: pa,pb=r, r+math.radians(w_deg)          # on the lid skin just above the edge
        else:     pa,pb=-r-math.radians(w_deg), -r        # on the lid skin just below the edge
        rows.append([bm.verts.new(c+dirv(th,pa)*R), bm.verts.new(c+dirv(th,pb)*R)])
    for i in range(N):
        a,b2=rows[i]; c2,d=rows[i+1]
        try: bm.faces.new((a,b2,d,c2))
        except ValueError: pass
    bm.normal_update()
    flip=[f for f in bm.faces if (f.calc_center_median()-c).dot(f.normal)<0]
    if flip: bmesh.ops.reverse_faces(bm,faces=flip)
    me=bpy.data.meshes.new(name+'_mesh'); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); o.data.materials.append(mat)
    vg=o.vertex_groups.new(name='head'); vg.add(list(range(len(me.vertices))),1.0,'REPLACE')
    md=o.modifiers.new('Armature','ARMATURE'); md.object=arm
for s in 'lr':
    c=cs[s]
    strip('lashline_%s'%s,c,s,True,lash,2.4,0.0333)
    strip('waterline_%s'%s,c,s,False,water,1.5,0.0332)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined16.blend")
print("FNSAVED")
