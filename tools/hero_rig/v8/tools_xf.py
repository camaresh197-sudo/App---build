import bpy
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v13_root.blend")
bad=[]
for o in bpy.data.objects:
    if o.type!='MESH':continue
    s=o.scale;r=o.rotation_euler;l=o.location
    nonid=any(abs(x-1)>1e-4 for x in s) or any(abs(x)>1e-4 for x in r) or any(abs(x)>1e-4 for x in l)
    mw=o.matrix_world;ident=all(abs(mw[i][j]-(1 if i==j else 0))<1e-4 for i in range(4) for j in range(4))
    if not ident:bad.append((o.name,tuple(round(x,3) for x in s),tuple(round(x,3) for x in l),o.parent.name if o.parent else None,o.parent_type,bool(o.data.shape_keys),o.data.users))
print(len(bad),"meshes with non-identity matrix_world of",sum(1 for o in bpy.data.objects if o.type=='MESH'))
for b in bad[:30]:print(b)
print("armature matrix_world identity:",all(abs(a-b)<1e-6 for a,b in zip([x for r in bpy.data.objects['character_rig'].matrix_world for x in r],[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])))
