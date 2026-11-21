"""Colour-code the eye parts and render them flat, to see which piece occludes which.

    blender --background --python tools/eye_debug.py -- <in.blend> <out.png>

Only a diagnostic: it never saves the blend.
"""
import sys
import math
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)

COL = {
    "head_12": (0.35, 0.35, 0.35, 1),
    "white_l_1": (0.9, 0.1, 0.1, 1),
    "iris_l_1": (0.1, 0.2, 0.95, 1),
    "pupil_l_0": (0.0, 0.0, 0.0, 1),
    "lidu_l_0": (0.1, 0.8, 0.2, 1),
    "lidl_l_0": (0.8, 0.8, 0.1, 1),
    "brow_l_0": (0.55, 0.1, 0.6, 1),
    "brow_l_1": (0.55, 0.1, 0.6, 1),
    "brow_l_2": (0.55, 0.1, 0.6, 1),
}
for o in bpy.data.objects:
    if o.name in COL:
        o.color = COL[o.name]
    elif o.type == "MESH":
        o.color = (0.45, 0.45, 0.45, 1)

cam_d = bpy.data.cameras.new("dbgcam")
cam_d.type = "ORTHO"
cam_d.ortho_scale = 0.13
cam = bpy.data.objects.new("dbgcam", cam_d)
bpy.context.scene.collection.objects.link(cam)
cam.location = (0.0365, -0.6, 1.5872)
cam.rotation_euler = (math.pi / 2, 0, 0)
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "FLAT"
sc.display.shading.color_type = "OBJECT"
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.film_transparent = False
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("DBG render wrote", OUT)
