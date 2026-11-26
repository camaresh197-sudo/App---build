# Open the closed mouth on the retopo head: remove the inner disc, rim the opening with the inner lip, recess a fan behind it.
# python3 -I open_mouth_v13.py -- in.blend out.blend
import bpy, bmesh, math, sys
from mathutils import Vector
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']
CZ=1.4777; RX=0.0255; UP=0.0040; DN=0.0048      # inner opening: 25.5 mm half-width, lip half-heights 4.0 up / 4.8 down
RECESS=0.012                                     # interior sits this far behind the lips
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
def inside(c):
    dz=c.z-CZ; k=UP if dz>0 else DN
    return (c.x/RX)**2+(dz/k)**2<1.0 and c.y<-0.06
dele=[f for f in bm.faces if inside(f.calc_center_median())]
print("inner faces removed:",len(dele))
bmesh.ops.delete(bm,geom=dele,context='FACES_ONLY')
bnd=[e for e in bm.edges if len(e.link_faces)==1]
adj={}
for e in bnd:
    a,b=e.verts; adj.setdefault(a,[]).append(b); adj.setdefault(b,[]).append(a)
start=bnd[0].verts[0]; loop=[start]; prev=None; cur=start
while True:
    nxt=[n for n in adj[cur] if n is not prev]
    n=nxt[0] if nxt else None
    if n is None or n is start or len(loop)>len(bnd)+2: break
    loop.append(n); prev,cur=cur,n
print("opening rim verts:",len(loop))
cy=sum(v.co.y for v in loop)/len(loop)-RECESS
c=bm.verts.new(Vector((0.0,cy,CZ)))
for i in range(len(loop)):
    a=loop[i]; b=loop[(i+1)%len(loop)]
    try: bm.faces.new((c,a,b))
    except ValueError: pass
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
print("head_low now: verts",len(lo.data.vertices),"faces",len(lo.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out)
