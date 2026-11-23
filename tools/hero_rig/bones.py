import bpy, math, sys
from mathutils import Vector
SRC="/home/claude/out/character_rigged_twist.blend"
OUT="/home/claude/out/character_rigged_bones.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
CX=0.09
import bmesh
def subdiv(name,cuts=1):
    o=bpy.data.objects[name]; bm=bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=cuts,use_grid_fill=True)
    bm.to_mesh(o.data); bm.free(); o.data.update(); print(name,len(o.data.vertices))
subdiv("torso_cartoon"); subdiv("pelvis_new"); subdiv("neck_2"); subdiv("shoulder_l_1"); subdiv("shoulder_r_1")
def seg_d(p,a,b):
    ab=b-a; t=max(0,min(1,(p-a).dot(ab)/ab.dot(ab))); return (p-(a+ab*t)).length
def apply(objname, feats):
    """feats: list of (kind, a, b, r, amt, mode) world coords. kind 'seg' ridge a->b, 'pt' bump at a.
       mode: direction filter vec n (world, unit) - only verts whose normal.n>0.35 move, along vertex normal*amt"""
    o=bpy.data.objects[objname]; M=o.matrix_world; Mi=M.inverted(); Mn=M.to_3x3().inverted().transposed()
    me=o.data; assert not me.shape_keys, objname
    me.calc_normals() if hasattr(me,'calc_normals') else None
    disp={}
    for v in me.vertices:
        p=M@v.co; n=(Mn@v.normal).normalized(); dsum=Vector((0,0,0))
        for f in feats:
            kind,a,b,r,amt,nf=f
            d=seg_d(p,a,b) if kind=='seg' else (p-a).length
            if d>r*2.2: continue
            if nf is not None and n.dot(nf)<0.3: continue
            w=math.exp(-(d/r)**2)
            dsum+=n*amt*w
        if dsum.length>0: disp[v.index]=dsum
    for i,dv in disp.items():
        v=me.vertices[i]; v.co=v.co+Mi.to_3x3()@dv
    me.update(); print(objname,"moved",len(disp))
F=Vector((0,-1,0)); B=Vector((0,1,0))
# ---- torso (front = -y). collarbones: sternum notch -> shoulder tip, both sides
y_f=-0.105
for s in (-1,1):
    a=Vector((CX+s*0.02,-0.095,1.325)); b=Vector((CX+s*0.125,-0.075,1.345))
    apply("torso_cartoon",[('seg',a,b,0.018,0.016,F)])
apply("torso_cartoon",[('pt',Vector((CX,-0.095,1.335)),Vector((CX,-0.095,1.335)),0.022,-0.014,F)])   # suprasternal notch
# scapulae (back): triangle ridges: spine of scapula diagonal + medial edge
for s in (-1,1):
    apply("torso_cartoon",[('seg',Vector((CX+s*0.03,0.055,1.27)),Vector((CX+s*0.115,0.050,1.315)),0.016,0.010,B),   # scapular spine
                           ('seg',Vector((CX+s*0.03,0.060,1.27)),Vector((CX+s*0.045,0.065,1.15)),0.014,0.008,B)])  # medial border
# spine ridge of vertebrae (back midline) with bumps
for z in [1.30,1.25,1.20,1.15,1.10,1.05,1.00,0.95,0.90]:
    apply("torso_cartoon",[('pt',Vector((CX,0.07,z)),Vector((CX,0.07,z)),0.011,0.005,B)])
# ---- pelvis: iliac crest / ASIS (front hip points) and PSIS dimples
pa=bpy.data.objects["pelvis_new"]
for s in (-1,1):
    apply("pelvis_new",[('pt',Vector((CX+s*0.115,-0.09,0.885)),Vector((0,0,0)),0.022,0.012,F),
                        ('seg',Vector((CX+s*0.10,-0.085,0.88)),Vector((CX+s*0.12,0.0,0.89)),0.016,0.007,None)])
# ---- neck: adam's apple + SCM tendons
apply("neck_2",[('pt',Vector((0.095,-0.085,1.385)),Vector((0,0,0)),0.016,0.010,F)])
for s in (-1,1):
    apply("neck_2",[('seg',Vector((0.095+s*0.05,-0.035,1.40)),Vector((0.095+s*0.022,-0.078,1.30)),0.014,0.006,F)])
# ---- arms
rig=bpy.data.objects["character_rig"]
def bh(n): return rig.data.bones[n].head_local.copy()
for side,sg in (("l",-1),("r",1)):
    el=bh("fore_"+side); wr=bh("hand_"+side); sh=bh("uarm_"+side)
    # acromion: top/back of shoulder ball
    for nm in ("shoulder_%s_1"%side,"shoulder_%s_2"%side):
        apply(nm,[('seg',sh+Vector((sg*-0.04,0.01,0.065)),sh+Vector((sg*0.05,0.035,0.045)),0.02,0.010,Vector((0,0,1)))])
    # forearm taper toward wrist
    ax=(wr-el); L=ax.length; ax.normalize()
    for nm in ("fore_%s_1"%side,"fore_%s_2"%side,"fore_%s_3"%side):
        o=bpy.data.objects[nm]; M=o.matrix_world; Mi=M.inverted()
        for v in o.data.vertices:
            p=M@v.co; q=p-el; proj=q.dot(ax); t=max(0,min(1,proj/L))
            u=max(0,(t-0.45)/0.55); k=1-0.16*(u*u*(3-2*u))
            rad=q-ax*proj; newp=el+ax*proj+rad*k
            v.co=Mi@newp
        o.data.update()
    # elbow: olecranon point (back), epicondyles (sides)
    for nm in ("uarm_%s_1"%side,"fore_%s_1"%side):
        apply(nm,[('pt',el+Vector((0,0.045,-0.012)),Vector((0,0,0)),0.03,0.028,B),
                  ('pt',el+Vector((0.04,0.0,0)),Vector((0,0,0)),0.022,0.012,Vector((1,0,0))),
                  ('pt',el+Vector((-0.04,0.0,0)),Vector((0,0,0)),0.022,0.012,Vector((-1,0,0)))])
    # wrist: ulnar styloid + radial bump
    for nm in ("fore_%s_1"%side,"fore_%s_2"%side,"fore_%s_3"%side):
        apply(nm,[('pt',wr+Vector((sg*0.02,0.025,0.012)),Vector((0,0,0)),0.018,0.016,B),
                  ('pt',wr+Vector((-sg*0.02,-0.02,0.012)),Vector((0,0,0)),0.016,0.010,F)])
bpy.ops.wm.save_as_mainfile(filepath=OUT,compress=True)
