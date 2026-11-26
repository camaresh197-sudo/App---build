# W091: stitch the cranium cap (cranium_cap.blend, mesh 'cranium_cap') to the retopo head's cranium boundary by a zipper:
# both boundary loops are sorted by azimuth about the cranium centre and joined triangle by triangle.
# python3 -I stitch_cap_v13.py -- retopo.blend cap.blend out.blend
import bpy, bmesh, sys, math
from mathutils import Vector
src,capsrc,out=sys.argv[-3],sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']
with bpy.data.libraries.load(capsrc, link=False) as (df,dt):
    dt.meshes=['cranium_cap']
capme=dt.meshes and bpy.data.meshes['cranium_cap']
C=Vector((0.0,-0.02,1.58)); COS=math.cos(math.radians(82))
bm=bmesh.new(); bm.from_mesh(lo.data); bm.verts.ensure_lookup_table()
cb=bmesh.new(); cb.from_mesh(capme)
cmap={}
for v in cb.verts:
    cmap[v]=bm.verts.new(v.co)
for f in cb.faces:
    try: bm.faces.new([cmap[v] for v in f.verts])
    except ValueError: pass
cb.free()
bm.faces.ensure_lookup_table()
def bnd_edges(verts_ok):
    return [e for e in bm.edges if len(e.link_faces)==1 and all(verts_ok(v.co) for v in e.verts)]
def dirz_ok(p):
    d=p-C; return d.length>0 and d.z/d.length>COS-0.15 and d.z>0
def loop_of(edges):
    adj={}
    for e in edges:
        a,b=e.verts; adj.setdefault(a,[]).append(b); adj.setdefault(b,[]).append(a)
    seen=set(); loops=[]
    for s in adj:
        if s in seen: continue
        loop=[s]; seen.add(s); prev=None; cur=s
        while True:
            nx=[n for n in adj[cur] if n is not prev and n not in seen]
            if not nx: break
            cur=nx[0]; seen.add(cur); loop.append(cur); prev=loop[-2]
        loops.append(loop)
    return loops
hb=loop_of(bnd_edges(dirz_ok))
hb=[l for l in hb if len(l)>100]
cap_v=set(cmap.values())
capedges=[e for e in bm.edges if len(e.link_faces)==1 and e.verts[0] in cap_v and e.verts[1] in cap_v]
cl=loop_of(capedges)
cl=[l for l in cl if len(l)>50]
print("head loop:",[len(l) for l in hb],"cap loop:",[len(l) for l in cl])
if len(hb)!=1 or len(cl)!=1:
    print("LOOP COUNT MISMATCH - not stitching"); sys.exit(1)
def az(v): return math.atan2(v.co.y-C.y, v.co.x-C.x)
A=sorted(cl[0],key=az); B=sorted(hb[0],key=az)
N1,N2=len(A),len(B)
i=j=0; made=0; skipped=0
for _ in range(N1+N2):
    a0,a1=A[i%N1],A[(i+1)%N1]; b0,b1=B[j%N2],B[(j+1)%N2]
    adv_a = (az(a1)<=az(b1)) if (i<N1) else False
    if j>=N2: adv_a=True
    if i>=N1: adv_a=False
    try:
        if adv_a: bm.faces.new((a0,a1,b0)); i+=1
        else:     bm.faces.new((a0,b0,b1)); j+=1
        made+=1
    except ValueError:
        skipped+=1
        if adv_a: i+=1
        else: j+=1
    if i>=N1 and j>=N2: break
print("zipper triangles:",made,"skipped:",skipped)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print("head_low faces now",len(lo.data.polygons))
