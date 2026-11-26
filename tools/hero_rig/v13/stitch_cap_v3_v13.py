# W101: join the cranium cap to the cut head with a 1:1 zip. The cap rim is resampled to the head rim count by splitting
# its longest edges one at a time (bmesh.utils.edge_split returns the new vertex), then the rims are zipped in loop order.
# python3 -I stitch_cap_v3_v13.py -- retopo.blend cap.blend out.blend
import bpy, bmesh, sys, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,capsrc,out=sys.argv[-3],sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
lo=bpy.data.objects['head_low']; hi=bpy.data.objects['head_quad']
skin=BVHTree.FromObject(hi,bpy.context.evaluated_depsgraph_get())
C=Vector((0.0,-0.02,1.58)); COS=math.cos(math.radians(82))
with bpy.data.libraries.load(capsrc, link=False) as (df,dt): dt.meshes=['cranium_cap']
capme=bpy.data.meshes['cranium_cap']
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
def cr(c):
    d=c-C; r=d.length; return r>0 and d.z/r>COS and d.z>0
cut=[f for f in bm.faces if cr(f.calc_center_median())]
cutset=set(cut)
RIM=set(e for f in cut for e in f.edges if any(g not in cutset for g in e.link_faces))
bmesh.ops.delete(bm,geom=cut,context='FACES_ONLY'); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
cb=bmesh.new(); cb.from_mesh(capme); cmap={}
for v in cb.verts: cmap[v]=bm.verts.new(v.co)
for f in cb.faces:
    try: bm.faces.new([cmap[v] for v in f.verts])
    except ValueError: pass
cb.free(); bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table()
capset=set(cmap.values())
def loop_of(edges):
    adj={}
    for e in edges:
        a,b=e.verts; adj.setdefault(a,[]).append(b); adj.setdefault(b,[]).append(a)
    seen=set(); out_=[]
    for s in adj:
        if s in seen: continue
        L=[s]; seen.add(s); prev=None; cur=s
        while True:
            nx=[n for n in adj[cur] if n is not prev and n not in seen]
            if not nx: break
            cur=nx[0]; seen.add(cur); L.append(cur); prev=L[-2]
        out_.append(L)
    return out_
headE=[e for e in RIM if not (e.verts[0] in capset or e.verts[1] in capset)]
H=max(loop_of(headE),key=len)
capE=[e for e in bm.edges if len(e.link_faces)==1 and e.verts[0] in capset and e.verts[1] in capset]
A=max(loop_of(capE),key=len)
print("head rim",len(H),"cap rim",len(A))
need=len(H)-len(A)
newv=set()
if need>0:
    # split one edge at a time: pick the longest rim edges, re-find the edge each time
    for _ in range(need):
        cands=[e for e in bm.edges if len(e.link_faces)==1 and e.verts[0] in capset|newv and e.verts[1] in capset|newv]
        e=max(cands,key=lambda x:x.calc_length())
        ne,nv=bmesh.utils.edge_split(e,e.verts[0],0.5)
        p,n,i,d=skin.find_nearest(nv.co)
        if p is not None: nv.co=Vector(p)
        newv.add(nv)
    A=max(loop_of([e for e in bm.edges if len(e.link_faces)==1 and e.verts[0] in capset|newv and e.verts[1] in capset|newv]),key=len)
print("cap rim now",len(A))
A=A if len(A)==len(H) else A
def az(v): return math.atan2(v.co.y-C.y,v.co.x-C.x)
def orient(L):
    t=0.0
    for i in range(len(L)):
        d=az(L[(i+1)%len(L)])-az(L[i]); d=(d+math.pi)%(2*math.pi)-math.pi; t+=d
    return L if t>0 else list(reversed(L))
A=orient(A); H=orient(H)
k0=min(range(len(H)),key=lambda k:(H[k].co-A[0].co).length); H=H[k0:]+H[:k0]
N1,N2=len(A),len(H); i=j=0; made=skip=0
for _ in range(N1+N2):
    a0,a1=A[i%N1],A[(i+1)%N1]; b0,b1=H[j%N2],H[(j+1)%N2]
    adv=(i<N1) and (j>=N2 or ((az(a1)-az(a0))%(2*math.pi) <= (az(b1)-az(b0))%(2*math.pi)))
    try:
        if adv: bm.faces.new((a0,a1,b0)); i+=1
        else:   bm.faces.new((a0,b0,b1)); j+=1
        made+=1
    except ValueError:
        skip+=1; i+=1 if adv else 0; j+=0 if adv else 1
print("zip triangles",made,"skipped",skip)
for p_ in bm.faces: p_.smooth=True
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(lo.data); bm.free(); lo.data.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print("head_low faces",len(lo.data.polygons))
