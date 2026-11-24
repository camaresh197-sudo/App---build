import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
out = sys.argv[sys.argv.index("--")+2]; png = sys.argv[sys.argv.index("--")+3]
old = bpy.data.images.get("iris_tex_v38.png")
img = bpy.data.images.load(png, check_existing=False)
img.name = "iris_tex_v59.png"; img.colorspace_settings.name = 'sRGB'; img.pack()
for mname in ["IrisMat_l","IrisMat_r"]:
    m = bpy.data.materials.get(mname)
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE': nd.image = img
if old: bpy.data.images.remove(old)
print("PACKED", img.name, img.size[:], img.packed_file is not None)
bpy.ops.wm.save_mainfile(filepath=out); print("SAVED", out)
