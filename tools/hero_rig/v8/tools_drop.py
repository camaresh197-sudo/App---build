import bpy
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v14_baked.blend")
d=[o.name for o in bpy.data.objects if o.type=='MESH' and (o.hide_viewport or o.hide_render)]
for n in d:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
print("dropped",len(d),"meshes left",sum(1 for o in bpy.data.objects if o.type=='MESH'),"faces",sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'))
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/work/hero_v15_clean.blend")
