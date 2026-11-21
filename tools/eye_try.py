"""Try lid rotations on the master's eye and render each, to find the one that closes the
aperture into an almond without swallowing the iris.

    blender --background --python tools/eye_try.py -- <in.blend> <out_dir>

Diagnostic only: never saves the blend.
"""
import sys
import os
import math
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUTDIR = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)
os.makedirs(OUTDIR, exist_ok=True)

COL = {
    "head_12": (0.35, 0.35, 0.35, 1),
    "white_l_1": (0.9, 0.1, 0.1, 1),
    "iris_l_1": (0.1, 0.2, 0.95, 1),
    "pupil_l_0": (0.0, 0.0, 0.0, 1),
    "lidu_l_0": (0.1, 0.8, 0.2, 1),
    "lidl_l_0": (0.8, 0.8, 0.1, 1),
}
for o in bpy.data.objects:
    o.color = COL.get(o.name, (0.45, 0.45, 0.45, 1))

LIDS = {"lidu_l_0": None, "lidl_l_0": None}
ORIG = {n: [tuple(v.co) for v in bpy.data.objects[n].data.vertices] for n in LIDS}


def set_rot(name, a):
    me = bpy.data.objects[name].data
    c, s = math.cos(a), math.sin(a)
    for v, o in zip(me.vertices, ORIG[name]):
        y, z = o[1], o[2]
        v.co = (o[0], y * c - z * s, y * s + z * c)


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
sc.render.resolution_x = 400
sc.render.resolution_y = 400

for du, dl in [(0.25, -0.25), (0.25, 0.25), (-0.25, 0.25), (-0.25, -0.25), (0.4, -0.35), (0.15, -0.35)]:
    set_rot("lidu_l_0", du)
    set_rot("lidl_l_0", dl)
    tag = ("p" if du > 0 else "n") + ("p" if dl > 0 else "n") + "_%.2f_%.2f" % (du, dl)
    sc.render.filepath = os.path.join(OUTDIR, "lid_%s.png" % tag)
    bpy.ops.render.render(write_still=True)
    print("TRY", tag)
