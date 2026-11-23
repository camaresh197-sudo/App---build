import bpy, math
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath="/home/claude/out/character_rigged_armlimits.blend")
rig=bpy.data.objects["character_rig"]
for o in bpy.data.objects:
    if o.type=='MESH' and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks[1:]: kb.value=0.0
def setpose(spec):
    for pb in rig.pose.bones: pb.rotation_quaternion=(1,0,0,0)
    for (n,ax,deg) in spec:
        for s in ("l","r"):
            d=deg if (ax=="X" or s=="l") else -deg
            p=rig.pose.bones[f"{n}_{s}"]; p.rotation_mode="QUATERNION"
            p.rotation_quaternion=Quaternion({"X":Vector((1,0,0)),"Z":Vector((0,0,1)),"Y":Vector((0,1,0))}[ax],math.radians(d))
    bpy.context.view_layer.update()
def tree_of(name):
    dg=bpy.context.evaluated_depsgraph_get(); t=bpy.data.objects[name].evaluated_get(dg); tm=t.to_mesh()
    verts=[t.matrix_world@v.co for v in tm.vertices]; polys=[tuple(p.vertices) for p in tm.polygons]; t.to_mesh_clear()
    return BVHTree.FromPolygons(verts,polys)
def pts(name):
    dg=bpy.context.evaluated_depsgraph_get(); h=bpy.data.objects[name].evaluated_get(dg); hm=h.to_mesh()
    p=[h.matrix_world@v.co for v in hm.vertices]; h.to_mesh_clear(); return p
def inside_by_ray(tree,p):
    # parity test: count ray crossings along +z
    n=0; o=Vector(p); d=Vector((0.0001,0.0002,1.0)).normalized()
    while True:
        loc,nrm,idx,dist=tree.ray_cast(o,d)
        if loc is None: break
        n+=1; o=loc+d*1e-4
    return n%2==1
poses={"default":[],"elbow flex (pic4)":[("uarm","X",-60),("fore","X",-200)],"raise (pic5)":[("uarm","Z",200),("fore","X",-200)],"arms fwd 90":[("uarm","X",-90)],"hand to chest":[("uarm","X",-30),("fore","X",-200)]}
for name,spec in poses.items():
    setpose(spec)
    res={}
    for tn in ("head_12","neck_1","torso_cartoon","hair_l_0","hair_r_0","head_118"):
        tr=tree_of(tn)
        for side in ("l","r"):
            for part in (f"hand_new_{side}",f"fore_{side}_1",f"uarm_{side}_1"):
                c=sum(1 for p in pts(part) if inside_by_ray(tr,p))
                if c: res[f"{part} in {tn}"]=c
    print("PEN2",name,res if res else "no penetration")
