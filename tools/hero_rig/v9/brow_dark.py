import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
b = bpy.data.materials["BrowHairMat"].node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.018, 0.010, 0.006, 1.0)
bpy.ops.wm.save_mainfile(filepath=sys.argv[sys.argv.index("--")+2]); print("SAVED")
