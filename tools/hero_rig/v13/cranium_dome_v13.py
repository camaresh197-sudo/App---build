# Step 2 (W087, fixed in W088): cut the cranium faces above the 82-degree line on the retopo head, and fill the hole with rings that
# shrink toward the crown pole (same vertex count as the boundary, so every ring joins), then project onto the skin.
# python3 -I cranium_dome_v13.py -- in.blend out.blend
import bpy, bmesh, math, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']; hi=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
C=Vector((0.0,-0.02,1.58)); COS=math.cos(math.radians(82))
def cr(c):
    d=c-C; r=d.length
    return r>0 and d.z/r>COS and d.z>0
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
dele=[f for f in bm.faces if cr(f.calc_center_median())]
print("cranium faces removed:",len(dele))
bmesh.ops.delete(bm,geom=dele,context='FACES_ONLY')
bnd=[e for e in bm.edges if len(e.link_faces)==1]
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
def dirz(c):
    d=(c-C); return d.z/max(d.length,1e-9)
cands=[c for c in comps if len(c)>20 and all(dirz(v.co)>COS-0.15 for e in c for v in e.verts)]
print("boundary components:",[len(c) for c in comps],"candidates:",[len(c) for c in cands])
if len(cands)!=1:
    print("NOT ONE CRANIUM LOOP - stopping"); bm.free(); sys.exit(1)
comp=cands[0]
ad={}
for e in comp:
    a,b=e.verts; ad.setdefault(a,[]).append(b); ad.setdefault(b,[]).append(a)
start=comp[0].verts[0]; loop=[start]; prev=None; cur=start
while True:
    nxt=[n for n in ad[cur] if n is not prev]
    n=nxt[0] if nxt else None
    if n is None or n is start or len(loop)>len(comp)+2: break
    loop.append(n); prev,cur=cur,n
M=len(loop); print("loop verts:",M,"of",len(comp))
KR=8; rings=[loop]
# W088: rings step the POLAR angle from the boundary (82 deg) toward the crown, keeping each boundary azimuth, and cast
# the rays along those directions. (The earlier version shrank distance, so rings fell back onto the boundary's rays.)
TH0=math.radians(82)
for k in range(1,KR+1):
    th=TH0*(1.0-k/(KR+1))
    row=[]
    for v in loop:
        az=math.atan2(v.co.y-C.y, v.co.x-C.x)
        d=Vector((math.sin(th)*math.cos(az), math.sin(th)*math.sin(az), math.cos(th)))
        loc,n,i,dd=bv.ray_cast(C,d)
        row.append(bm.verts.new(loc if loc else C+d*0.07))
    rings.append(row)
pole=bm.verts.new(C+Vector((0,0,0.02)))
loc,n,i,dd=bv.ray_cast(C,Vector((0,0,1)))
if loc: pole.co=loc
for i in range(M):
    j=(i+1)%M
    for k in range(len(rings)-1):
        try: bm.faces.new((rings[k][i],rings[k][j],rings[k+1][j],rings[k+1][i]))
        except ValueError: print("skip quad",k,i)
for i in range(M):
    j=(i+1)%M
    try: bm.faces.new((rings[-1][i],rings[-1][j],pole))
    except ValueError: print("skip fan",i)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print("head_low now faces",len(lo.data.polygons))
