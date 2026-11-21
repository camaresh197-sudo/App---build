"""Fix the eyes in the master, once.

  - the lids sit further over the ball, so the aperture reads as an almond instead of a
    full circle (the lower lid used to hide behind the eyeball);
  - the sclera is a warm off-white with a matte finish: the old 0.8 grey at roughness 0.45
    picked up the scene's blue sky as a sheen and read as a glass bead.

    blender --background --python tools/eye_fix.py -- <in.blend> <out.blend>

Safe to run once: it rotates the lids by a fixed amount, so running it twice compounds it.
"""
import sys
import math
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)

# --- lids: rotate the shells about the eye centre (their local origin) so they overlap the ball
DU = 0.14      # upper lid down (radians)
DL = -0.12     # lower lid up
for side in ("l", "r"):
    for name, a in (("lidu_%s_0" % side, DU), ("lidl_%s_0" % side, DL)):
        o = bpy.data.objects.get(name)
        if o is None:
            print("EYE: missing", name)
            continue
        c, s = math.cos(a), math.sin(a)
        for v in o.data.vertices:
            y, z = v.co.y, v.co.z
            v.co.y = y * c - z * s
            v.co.z = y * s + z * c
        print("EYE: rotated %s by %.2f" % (name, a))

# --- sclera: warm, matte
m = bpy.data.materials.get("Material_10")
if m and m.use_nodes:
    for n in m.node_tree.nodes:
        if n.type != "BSDF_PRINCIPLED":
            continue
        n.inputs["Base Color"].default_value = (0.72, 0.67, 0.60, 1.0)
        n.inputs["Roughness"].default_value = 0.72
        for spec in ("Specular IOR Level", "Specular"):
            if spec in n.inputs:
                n.inputs[spec].default_value = 0.22
        print("EYE: sclera material set")

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("EYE: saved", DST)
