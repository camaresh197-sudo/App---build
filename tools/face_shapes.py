"""Author the face's expression shape keys on the master .blend.

The face used to get its fleshy expressions by moving bone-attached blobs. The
better tool is blendshapes: a neutral face plus a sculpted "smile", "squint",
etc., that the game drives by name (set_blend_shape_value). This adds/updates
those keys on the head mesh. Re-run it after editing the mesh; it is idempotent.

    blender --background --factory-startup --python face_shapes.py -- <in.blend> <out.blend>
"""
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=SRC)


def fall(p, c, r):
    w = 1.0 - (p - c).length / r
    if w <= 0.0:
        return 0.0
    return w * w * (3.0 - 2.0 * w)


def smile_disp(p):
    # a real smile: the cheek mounds out and up, a nasolabial crease forms beside it, and the mouth corner lifts
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        cheek = Vector((0.048 * s, -0.028, 0.056))
        d += Vector((0.041 * s, 0.026, 0.023)) * fall(p, cheek, 0.068)
        corner = Vector((0.034 * s, -0.068, 0.084))
        d += Vector((0.014 * s, 0.019, 0.004)) * fall(p, corner, 0.038)
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):        # the crease, nose wing -> mouth corner: pull it in
            c = Vector((0.017 * s, -0.030, 0.096)).lerp(Vector((0.035 * s, -0.066, 0.084)), t)
            d -= Vector((0.009 * s, 0.0, 0.009)) * fall(p, c, 0.021)
    return d


def squint_disp(p):
    # a Duchenne squint: the outer eye corner pulls in and the lower lid pushes up
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        corner = Vector((0.066 * s, 0.022, 0.062))
        d += Vector((-0.014 * s, 0.0, -0.006)) * fall(p, corner, 0.044)
        lid = Vector((0.040 * s, 0.006, 0.088))
        d += Vector((0.0, 0.013, 0.007)) * fall(p, lid, 0.034)
    return d


# the head is the biggest mesh on the head bone (its name carries a child index that can shift)
head = None
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("head"):
        if head is None or len(o.data.vertices) > len(head.data.vertices):
            head = o
if head is None:
    raise SystemExit("FACE: no head mesh found")

me = head.data
if me.shape_keys is None:
    head.shape_key_add(name="Basis", from_mix=False)

SHAPES = {"smile": smile_disp, "squint": squint_disp}
for name, fn in SHAPES.items():
    old = me.shape_keys.key_blocks.get(name)
    if old is not None:
        head.shape_key_remove(old)
    sk = head.shape_key_add(name=name, from_mix=False)
    for i, v in enumerate(me.vertices):
        sk.data[i].co = v.co + fn(v.co)

print("FACE: head %s, shape keys -> %s" % (head.name, [k.name for k in me.shape_keys.key_blocks]))
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("FACE: saved", DST)
