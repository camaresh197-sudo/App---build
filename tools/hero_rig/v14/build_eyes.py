import sys, bpy, bmesh, math, json, collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,dst=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2]
ROWS=int(sys.argv[sys.argv.index('--')+3]) if len(sys.argv)>sys.argv.index('--')+3 else 10
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['head_quad']; M=o.matrix_world; Mi=M.inverted()
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
skin=bmesh.new(); skin.from_mesh(o.data); skin.transform(M); tree=BVHTree.FromBMesh(skin)
L=json.load(open('/tmp/claude-0/-home-user-App---build/06e83864-e0ef-54c3-9ec4-508030560da5/scratchpad/hero/v143_landmarks.json'))
def front_hit(x,z):
    loc,n,i,d=tree.ray_cast(Vector((x,-0.4,z)),Vector((0,1,0)),0.6)
    return loc
RX2,RZ2=0.026,0.016; RX0,RZ0=0.0104,0.0064
total_new=0; report=[]
for name in ['eye_l','eye_r']:
    cx,_,cz=[v/1000 for v in L[name]]
    def inside(p):
        return ((p.x-cx)/RX2)**2+((p.z-cz)/RZ2)**2<=1.0 and p.y<-0.03
    bm.faces.ensure_lookup_table()
    cut=[f for f in bm.faces if inside(M@f.calc_center_median())]
    bmesh.ops.delete(bm, geom=cut, context='FACES')
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.verts.index_update()
    bnd=[e for e in bm.edges if e.is_boundary]
    # keep only boundary edges near this eye
    near=[e for e in bnd if inside_near((M@e.verts[0].co)) ] if False else bnd
    adj=collections.defaultdict(list)
    for e in near:
        a,b=e.verts; adj[a].append(b); adj[b].append(a)
    # pick the loop whose centre is near this eye
    seen=set(); loops=[]
    for s in list(adj):
        if s in seen: continue
        loop=[s]; seen.add(s); prev=None; v=s
        while True:
            nxt=[w for w in adj[v] if w is not prev]
            if not nxt: break
            w=nxt[0]
            if w is s or w in seen: break
            loop.append(w); seen.add(w); prev,v=v,w
        loops.append(loop)
    def lc(loop):
        c=sum(((M@v.co) for v in loop),Vector())/len(loop); return (c.x-cx)**2+(c.z-cz)**2
    loop=min([l for l in loops if len(l)>6], key=lc)
    N=len(loop)
    # order loop by angle around the eye centre so rows are consistent
    def ang(v):
        p=M@v.co; return math.atan2((p.z-cz)/RZ2,(p.x-cx)/RX2)
    loop.sort(key=ang)
    rim=[M@v.co for v in loop]
    rows=[[v for v in loop]]
    for r in range(1,ROWS+1):
        t=r/ROWS; row=[]
        for p,v in zip(rim,loop):
            th=ang(v)
            x0=cx+RX0*math.cos(th); z0=cz+RZ0*math.sin(th)
            x=p.x+(x0-p.x)*t; z=p.z+(z0-p.z)*t
            hit=front_hit(x,z)
            if hit is None: hit=Vector((x,p.y,z))
            row.append(bm.verts.new(Mi@hit))
        rows.append(row)
    nf=0
    for a,b in zip(rows,rows[1:]):
        for i in range(N):
            j=(i+1)%N
            try: bm.faces.new([a[i],a[j],b[j],b[i]]); nf+=1
            except ValueError: pass
    total_new+=nf; report.append((name,N,len(cut),nf))
bm.normal_update()
flip=sum(1 for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].normal.dot(e.link_faces[1].normal)<0)
bnd=[e for e in bm.edges if e.is_boundary]
print('EYES', report, 'new faces', total_new, 'flips', flip, 'boundary edges', len(bnd))
bm.to_mesh(o.data); bm.free(); skin.free()
bpy.ops.wm.save_as_mainfile(filepath=dst)
print('saved')
