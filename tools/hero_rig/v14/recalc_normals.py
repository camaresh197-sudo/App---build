import sys, bpy, bmesh
src,dst=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2]
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['head_quad']
bm=bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.normal_update()
flips=[e for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].normal.dot(e.link_faces[1].normal)<0]
print('EFIX flips', len(flips))
M=o.matrix_world
import collections
zs=[ (M@((e.verts[0].co+e.verts[1].co)/2)) for e in flips]
if zs: print('EFIX flip extent x', min(p.x for p in zs)*1000, max(p.x for p in zs)*1000, 'z', min(p.z for p in zs)*1000, max(p.z for p in zs)*1000)
asp=[]
for f in bm.faces:
    L=[e.calc_length() for e in f.edges]; asp.append(max(L)/max(min(L),1e-9))
asp.sort(); n=len(asp)
print(f"EFIX aspect median {asp[n//2]:.2f} p90 {asp[int(n*0.9)]:.2f} max {asp[-1]:.1f}")
bm.to_mesh(o.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst); print('saved')
