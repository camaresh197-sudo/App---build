# W090: remesh the cranium cap on its own (not joined): extract the high-poly faces above 82 deg from the crown, clean them,
# run QuadriFlow to an even quad cap, and mark it as a separate object for review. Nothing is stitched into head_low.
# python3 -I remesh_cranium_v13.py -- in.blend out.blend TARGET_FACES
import bpy, bmesh, sys, math
from mathutils import Vector
src,out=sys.argv[-3],sys.argv[-2]; T=int(sys.argv[-1])
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['head_quad']
C=Vector((0.0,-0.02,1.58)); COS=math.cos(math.radians(82))
bm=bmesh.new(); bm.from_mesh(hi.data); bm.faces.ensure_lookup_table()
def cr(c):
    d=c-C; r=d.length
    return r>0 and d.z/r>COS and d.z>0
keep=[f for f in bm.faces if not cr(f.calc_center_median())]
cap=[f for f in bm.faces if cr(f.calc_center_median())]
cut=bmesh.new()
mp={}
for f in cap:
    vs=[]
    for v in f.verts:
        if v not in mp: mp[v]=cut.verts.new(v.co)
        vs.append(mp[v])
    try: cut.faces.new(vs)
    except ValueError: pass
bmesh.ops.remove_doubles(cut,verts=cut.verts[:],dist=1e-6)
bmesh.ops.triangulate(cut,faces=[f for f in cut.faces if len(f.verts)>3])
bmesh.ops.recalc_face_normals(cut,faces=cut.faces[:])
me=bpy.data.meshes.new('cranium_cap'); cut.to_mesh(me); cut.free()
ob=bpy.data.objects.new('cranium_cap',me); bpy.context.scene.collection.objects.link(ob)
print("cap faces from skull:",len(cap),"cap verts:",len(me.vertices))
for o in bpy.context.view_layer.objects: o.select_set(False)
bpy.context.view_layer.objects.active=ob; ob.select_set(True)
r=bpy.ops.object.quadriflow_remesh(mode='FACES',target_faces=T,use_mesh_symmetry=False,use_preserve_sharp=False,use_preserve_boundary=True,smooth_normals=True,seed=1)
print("quadriflow:",r,"faces:",len(ob.data.polygons))
qu=sum(1 for p in ob.data.polygons if len(p.vertices)==4)
print("quads:",qu,"of",len(ob.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out)
