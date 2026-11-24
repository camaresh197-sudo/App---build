import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
o = bpy.data.objects.get("head_118")
print("DEL before:", bool(o), (len(o.data.polygons), o.data.shape_keys is not None) if o else None)
if o:
    m = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.meshes.remove(m)
bpy.ops.wm.save_mainfile(filepath=sys.argv[sys.argv.index("--")+2]); print("DELETED head_118; saved")
