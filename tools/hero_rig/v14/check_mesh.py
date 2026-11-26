import sys, bpy, bmesh, collections, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
o=bpy.data.objects['head_quad']; M=o.matrix_world
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
E=collections.Counter(len(e.link_faces) for e in bm.edges)
print('V143 edge face-counts', dict(sorted(E.items())))
print('V143 boundary edges', sum(1 for e in bm.edges if e.is_boundary))
print('V143 loose verts', sum(1 for v in bm.verts if not v.link_faces), 'loose edges', sum(1 for e in bm.edges if not e.link_faces))
tris=sum(1 for f in bm.faces if len(f.verts)==3); quads=sum(1 for f in bm.faces if len(f.verts)==4); ng=sum(1 for f in bm.faces if len(f.verts)>4)
print(f"V143 faces {len(bm.faces)} tris {tris} quads {quads} ngons {ng}")
flip=sum(1 for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].normal.dot(e.link_faces[1].normal)<0)
print('V143 neighbour flips', flip)
asp=[]
for f in bm.faces:
    L=[e.calc_length() for e in f.edges]
    asp.append(max(L)/max(min(L),1e-9))
asp.sort(); n=len(asp)
print(f"V143 aspect median {asp[n//2]:.2f} p90 {asp[int(n*0.9)]:.2f} max {asp[-1]:.1f} over3 {sum(1 for a in asp if a>3)}")
poles=sum(1 for v in bm.verts if len([e for e in v.link_edges if e.link_faces])>4)
print('V143 poles(valence>4)', poles)
# profile tear: front surface vs centreline
prof=collections.defaultdict(lambda:9)
for v in bm.verts:
    p=M@v.co
    if abs(p.x)>0.006: continue
    b=round(p.z*1000/4)*4
    prof[b]=min(prof[b],p.y)
big=[(b,round(y*1000,1)) for b,y in sorted(prof.items()) if 1450<=b<=1510]
print('V143 profile mm', big)
bm.free()
