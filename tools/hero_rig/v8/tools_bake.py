import bpy
from mathutils import Matrix
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v13_root.blend")
n=0;cn=[]
for o in bpy.data.objects:
    if o.type!='MESH':continue
    M=o.matrix_world.copy()
    if all(abs(M[i][j]-(1 if i==j else 0))<1e-6 for i in range(4) for j in range(4)):continue
    me=o.data
    if me.has_custom_normals:cn.append(o.name)
    if me.users>1:me=o.data=me.copy()
    sk=me.shape_keys
    if sk:
        for kb in sk.key_blocks:
            for d in kb.data:d.co=M@d.co
    for v in me.vertices:v.co=M@v.co
    o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4)
    me.update();n+=1
bpy.context.view_layer.update()
bad=[o.name for o in bpy.data.objects if o.type=='MESH' and any(abs(o.matrix_world[i][j]-(1 if i==j else 0))>1e-5 for i in range(4) for j in range(4))]
print("baked",n,"still non-identity",bad,"custom normals",cn)
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/work/hero_v14_baked.blend")
