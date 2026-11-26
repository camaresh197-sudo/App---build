# Open the closed mouth on the retopo head: remove the inner disc, rim the opening with the inner lip, recess a fan behind it.
# python3 -I open_mouth_v13.py -- in.blend out.blend
import bpy, bmesh, math, sys
from mathutils import Vector
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']
CZ=1.4777; RX=0.0255; UP=0.0040; DN=0.0048      # inner opening: 25.5 mm half-width, lip half-heights 4.0 up / 4.8 down
RECESS=0.018                                     # interior sits this far behind the lips
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
def inside(c):
    dz=c.z-CZ; k=UP if dz>0 else DN
    return (c.x/RX)**2+(dz/k)**2<1.0 and c.y<-0.06
dele=[f for f in bm.faces if inside(f.calc_center_median())]
print("inner faces removed:",len(dele))
bmesh.ops.delete(bm,geom=dele,context='FACES_ONLY')
bnd=[e for e in bm.edges if len(e.link_faces)==1]
def mid(e): return sum((v.co for v in e.verts),type(e.verts[0].co)())/2
# pick the MOUTH rim component (W076): the first boundary found was an eye loop, which is why the fan was wrong
adj={}
for e in bnd:
    for v in e.verts: adj.setdefault(v,[]).append(e)
seen=set(); comps=[]
for e in bnd:
    if e in seen: continue
    st=[e]; comp=[]; seen.add(e)
    while st:
        x=st.pop(); comp.append(x)
        for v in x.verts:
            for y in adj[v]:
                if y not in seen: seen.add(y); st.append(y)
    comps.append(comp)
def is_mouth(c):
    zs=[mid(e).z for e in c]; xs=[mid(e).x for e in c]
    return abs(sum(zs)/len(zs)-CZ)<0.004 and max(xs)-min(xs)<0.07
mc=[c for c in comps if is_mouth(c)]
assert len(mc)==1, "mouth rim not found: %d candidates"%len(mc)
mouth_edges=mc[0]
# order the rim loop
ad={}
for e in mouth_edges:
    a_,b_=e.verts; ad.setdefault(a_,[]).append(b_); ad.setdefault(b_,[]).append(a_)
start=mouth_edges[0].verts[0]; loop=[start]; prev=None; cur=start
while True:
    nxt=[n for n in ad[cur] if n is not prev]
    n=nxt[0] if nxt else None
    if n is None or n is start or len(loop)>len(mouth_edges)+2: break
    loop.append(n); prev,cur=cur,n
print("mouth rim verts:",len(loop),"edges:",len(mouth_edges))
cy=sum(v.co.y for v in loop)/len(loop)-RECESS
c=bm.verts.new(Vector((0.0,cy,CZ)))
fan_start=len(bm.faces)
for i in range(len(loop)):
    a=loop[i]; b=loop[(i+1)%len(loop)]
    try: bm.faces.new((c,a,b))
    except ValueError: pass
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
mat=bpy.data.materials.get('mouth_interior') or bpy.data.materials.new('mouth_interior')
mat.diffuse_color=(0.12,0.06,0.06,1)
if 'mouth_interior' not in [m.name for m in lo.data.materials if m]: lo.data.materials.append(mat)
mi=[i for i,m in enumerate(lo.data.materials) if m and m.name=='mouth_interior'][0]
for f in bm.faces:
    if all(v.co.z<CZ+0.001 and v.co.z>CZ-0.003 and abs(v.co.x)<0.027 and v.co.y<-0.07 for v in f.verts) and any(v is c for v in f.verts): f.material_index=mi
bm.to_mesh(lo.data); bm.free(); lo.data.update()
print("head_low now: verts",len(lo.data.vertices),"faces",len(lo.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out)
