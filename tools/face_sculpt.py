"""Sculpt the merged face mesh on the master .blend.

The merge gave one clean surface but rounded the thin features - the nose most of
all. This puts the definition back by displacing the merged mesh: a raised nose
bridge, a tip and wings. Run it after face_merge.py and before face_shapes.py
(it clears the shape keys, which are re-authored afterwards).

    blender --background --factory-startup --python face_sculpt.py -- <in.blend> <out.blend>
"""
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=SRC)


def fall(p, c, r):
    w = 1.0 - (p - c).length / r
    return 0.0 if w <= 0.0 else w * w * (3.0 - 2.0 * w)


def nose_disp(p):
    d = Vector((0.0, 0.0, 0.0))
    # the bridge: a raised ridge from between the brows down to the tip
    for t in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        c = Vector((0.0, 0.026 - t * 0.048, 0.092 + t * 0.016))
        d += Vector((0.0, 0.0, 0.020 * (1.0 - 0.3 * t))) * fall(p, c, 0.019)
    # the tip: pushed forward and a little down, so it reads as a nose rather than a bump
    d += Vector((0.0, -0.008, 0.026)) * fall(p, Vector((0.0, -0.021, 0.107)), 0.019)
    # the wings: flare either side of the tip
    for s in (-1.0, 1.0):
        d += Vector((0.009 * s, 0.0, 0.008)) * fall(p, Vector((0.016 * s, -0.023, 0.101)), 0.017)
    return d


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def crown_disp(p):
    # KNOWN ISSUE: a small skin spike pokes above the hairline at the crown. This mild flatten helps but does not
    # remove it; the real fix is to round the head's crown (or match the hair cap) - see the note in the commit.
    if p.y <= 0.03:
        return Vector((0.0, 0.0, 0.0))
    return Vector((0.0, -(p.y - 0.03) * 0.30, 0.0))


head = None
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("head"):
        if head is None or len(o.data.vertices) > len(head.data.vertices):
            head = o
if head is None:
    raise SystemExit("SCULPT: no head mesh found")

me = head.data
if me.shape_keys is not None:                 # cleared here; face_shapes.py re-authors them on the sculpted mesh
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.shape_key_remove(all=True)

moved = 0
for v in me.vertices:
    d = nose_disp(v.co) + crown_disp(v.co)
    if d.length > 1e-6:
        v.co = v.co + d
        moved += 1
me.update()

print("SCULPT: %s - nose on %d/%d verts" % (head.name, moved, len(me.vertices)))
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("SCULPT: saved", DST)
