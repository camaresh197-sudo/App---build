# Quad-remesh the high-poly head (feat_v13_ears.blend) to a game-ready head_low: python3 -I retopo_v13.py -- <target_faces> <out.blend>
# Keeps the original as head_quad (high) and adds head_low; then reports how far head_low is from head_quad.
import bpy, sys, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
T=int(sys.argv[-2]); out=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath="feat_v13_ears.blend")
hi=bpy.data.objects['head_quad']
lo=hi.copy(); lo.data=hi.data.copy(); lo.name='head_low'
bpy.context.scene.collection.objects.link(lo)
for o in bpy.context.view_layer.objects: o.select_set(False)
bpy.context.view_layer.objects.active=lo; lo.select_set(True)
import bmesh, os
# clean the copy: merge doubles, triangulate ngons, recalc normals (QuadriFlow rejects messy input)
_bm=bmesh.new(); _bm.from_mesh(lo.data)
bmesh.ops.remove_doubles(_bm,verts=_bm.verts[:],dist=1e-6)
bmesh.ops.triangulate(_bm,faces=[f for f in _bm.faces if len(f.verts)>3])
bmesh.ops.recalc_face_normals(_bm,faces=_bm.faces[:])
_bm.to_mesh(lo.data); _bm.free()
SYM=os.environ.get('V13_SYM','0')=='1'
r=bpy.ops.object.quadriflow_remesh(mode='FACES', target_faces=T, use_mesh_symmetry=SYM, use_preserve_sharp=False,
                                   use_preserve_boundary=False, smooth_normals=True, seed=1)
print("quadriflow:",r,"symmetry",SYM)
me=lo.data
for p in me.polygons: p.use_smooth=True
quads=sum(1 for p in me.polygons if len(p.vertices)==4); tris=sum(1 for p in me.polygons if len(p.vertices)==3)
print("head_low: verts",len(me.vertices),"faces",len(me.polygons),"quads",quads,"tris",tris,"other",len(me.polygons)-quads-tris)
# surface deviation: distance from every head_low vertex to the high-poly surface (mm)
dg=bpy.context.evaluated_depsgraph_get()
bv=BVHTree.FromObject(hi,dg)
ds=[]
for v in me.vertices:
    loc,n,i,d=bv.find_nearest(lo.matrix_world@v.co)
    ds.append(d*1000)
ds.sort()
print("deviation mm: mean %.2f  p95 %.2f  max %.2f"%(sum(ds)/len(ds),ds[int(len(ds)*.95)],ds[-1]))
hi.hide_set(True); hi.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=out)
