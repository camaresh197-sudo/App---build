# Concentric eye-loop patch into head_low (from retopo_v13.py): python3 -I patch_eye_v13.py -- <in.blend> <out.blend>
# Cuts a hole around the +x eye in the QuadriFlow mesh and fills it with rings: lid opening, lid rim, crease, then
# rings that blend out to the hole boundary (the boundary vertices are reused, so the patch is stitched). Every new
# point is projected onto the high-poly head (head_quad).
import bpy, bmesh, math, sys, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']; hi=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
SC=0.907                                   # the head was scaled by this about the crown (z 1.674)
EYE=os.environ.get('V13_EYE','eye_l')       # eye_l = +x (character's left, viewer's right); eye_r = -x
eye=bpy.data.objects[EYE]
NOSE=os.environ.get('V13_NOSE','0')=='1'   # nostril mode: rings around one nostril instead of an eye
SGN=1.0 if EYE in ('eye_l','nostril_l') else -1.0
vs=[v.co for v in eye.data.vertices]
cx=sum(v.x for v in vs)/len(vs); cz=sum(v.z for v in vs)/len(vs)
if NOSE:
    cx=0.0092*SGN; cz=1.5048   # nostril centre (nostril_l/r objects, location z 1.5048)
print("eye centre x %.4f z %.4f"%(cx,cz))
A=(0.0046 if NOSE else 0.0185)*SC; BU=(0.0023 if NOSE else 0.0095)*SC; BL=(0.0023 if NOSE else 0.0068)*SC   # almond opening (same numbers as the lid code), scaled
def opening(th):
    dx=math.cos(th)*1.0; up=math.sin(th)>=0
    b=BU if up else BL
    x=cx+A*dx
    z=cz+(0 if NOSE else 0.09*SGN*dx*0.0105*SC)+b*math.sin(th)  # outer corner lifted like the lid code (side-aware)
    return x,z
def onsurface(x,z,yref=None):
    """project (x,z) onto the high-poly skin along y. With yref (the depth of the neighbour ring at the same angle) a hit more
    than 2 mm away is a different sheet (lid wrap vs skin at the eye corners): stay on the neighbour's sheet by snapping to the
    nearest surface point from (x,yref,z) instead. That jump was folding thin back-facing slits at both corners."""
    loc,n,i,d=bv.ray_cast(Vector((x,-0.5,z)),Vector((0,1,0)))
    if loc is None: return None
    if yref is None or abs(loc.y-yref)<0.002: return Vector((x,loc.y,z))
    p,nn,ii,dd=bv.find_nearest(Vector((x,yref,z)))
    return Vector(p) if p is not None else Vector((x,loc.y,z))
# 1) hole: delete faces whose centre is inside an ellipse around the eye
RX,RZ=((float(os.environ.get('V13_NRX','0.0072')),float(os.environ.get('V13_NRZ','0.0065'))) if NOSE else (0.044,0.033))   # nostril hole: stops short of the midline (nostrils are 9.2 mm off-centre)
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
HX=cx+SGN*(float(os.environ.get('V13_NSHIFT','0.0014')) if NOSE else 0.0)   # hole centre pushed outward, away from the midline (wing)
dele=[f for f in bm.faces if f.calc_center_median().y<-0.04 and ((f.calc_center_median().x-HX)/RX)**2+((f.calc_center_median().z-cz)/RZ)**2<1.0]
print("faces removed:",len(dele))
bmesh.ops.delete(bm,geom=dele,context='FACES_ONLY')
# 2) order the boundary loop
bnd=[e for e in bm.edges if len(e.link_faces)==1]
print("boundary edges:",len(bnd))
adj={}
for e in bnd:
    a,b=e.verts; adj.setdefault(a,[]).append(b); adj.setdefault(b,[]).append(a)
start=bnd[0].verts[0]; loop=[start]; prev=None; cur=start
while True:
    nxt=[n for n in adj[cur] if n is not prev]
    n=nxt[0] if nxt else None
    if n is None or n is start: break
    loop.append(n); prev,cur=cur,n
    if len(loop)>len(bnd)+2: break
M=len(loop); print("loop verts:",M)
ang=lambda v: math.atan2((v.co.z-cz)/RZ,(v.co.x-cx)/RX)
# orientation: make angle increase along the loop
tot=0.0
for i in range(M):
    d=ang(loop[(i+1)%M])-ang(loop[i]); d=(d+math.pi)%(2*math.pi)-math.pi; tot+=d
if tot<0: loop.reverse()
# angle of every boundary vertex by normalised arc length (monotonic by construction): the staircase boundary runs almost
# vertically at the two ends of the long axis, where atan2 goes backwards and crossed radial lines fold thin slits
_u=[((v.co.x-cx)/RX,(v.co.z-cz)/RZ) for v in loop]
_cum=[0.0]
for i in range(M):
    a,b=_u[i],_u[(i+1)%M]; _cum.append(_cum[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
th=[math.atan2(_u[0][1],_u[0][0])+2*math.pi*_cum[i]/_cum[-1] for i in range(M)]
# 3) rings, from the opening (k=0) out to the boundary (k=K)
RING=[(1.00,0.0),(1.10,0.0),(1.25,0.0),(1.45,0.22),(1.70,0.45)] if NOSE else [(1.00,0.0),(1.14,0.0),(1.38,0.0),(1.70,0.18),(2.10,0.40),(2.60,0.62),(3.20,0.82)]     # (scale of the almond, blend toward the boundary)
rings=[]
for (s,w) in RING:
    row=[]
    for i in range(M):
        ox,oz=opening(th[i])
        px,pz=cx+s*(ox-cx),cz+s*(oz-cz)
        bx,bz_=loop[i].co.x,loop[i].co.z
        x=(1-w)*px+w*bx; z=(1-w)*pz+w*bz_
        p=onsurface(x,z,rings[-1][i].co.y if rings else None)
        row.append(bm.verts.new(p if p else Vector((x,loop[i].co.y,z))))
    rings.append(row)
rings.append(loop)
new=[]
for k in range(len(rings)-1):
    for i in range(M):
        j=(i+1)%M
        try: new.append(bm.faces.new((rings[k][i],rings[k][j],rings[k+1][j],rings[k+1][i])))
        except ValueError: pass
# relax the outer three rings (not the stitched boundary): average each vertex with its neighbours, then put it back on the high-poly surface,
# so the radial lines stop following the staircase of the old grid
_outer=set(v for row in rings[-4:-1] for v in row)
for _ in range(6):
    _pos={}
    for v in _outer:
        nb=[e.other_vert(v) for e in v.link_edges]
        if not nb: continue
        c=sum((n.co for n in nb),Vector())/len(nb)
        p=onsurface(0.5*v.co.x+0.5*c.x,0.5*v.co.z+0.5*c.z,v.co.y)
        _pos[v]=p if p else v.co.copy()
    for v,p in _pos.items(): v.co=p
# outward normals (front of the face is -y)
if sum(f.normal.y for f in new if f.normal.length>0) > 0:
    for f in new: f.normal_flip()
bm.normal_update(); bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free()
for p in lo.data.polygons: p.use_smooth=True
print("head_low now: verts",len(lo.data.vertices),"faces",len(lo.data.polygons),"new patch quads",len(new))
bpy.ops.wm.save_as_mainfile(filepath=out)
