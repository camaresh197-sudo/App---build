"""One-off chin pass for the merged master face.

`face_sculpt.py` grew a chin/teeth step after the master was already built, and the
master's jaw is joined by `face_rebuild.py` (no separate `jaw_0` to move). This shifts
the chin region forward/up on the merged mesh and carries the same delta into every
shape key, so expressions keep the new chin.

    blender --background --factory-startup --python face_chin.py -- <in.blend> <out.blend>

One-off: running it twice compounds the move.
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


head = None
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("head"):
        if head is None or len(o.data.vertices) > len(head.data.vertices):
            head = o
if head is None:
    raise SystemExit("CHIN: no head mesh found")

me = head.data
gi = head.vertex_groups.get("jaw")
if gi is None:
    raise SystemExit("CHIN: no jaw vertex group")

jw = {}
for v in me.vertices:
    w = 0.0
    for g in v.groups:
        if g.group == gi.index and g.weight > w:
            w = g.weight
    jw[v.index] = w

lip = set()
for p in me.polygons:
    m = me.materials[p.material_index] if p.material_index < len(me.materials) else None
    if m is not None and m.name == "lip_mouth":
        lip.update(p.vertices)

CENTER = Vector((0.0, -0.070, -0.095))
RADIUS = 0.045
DELTA = Vector((0.0, -0.007, 0.004))   # forward (-Y) and up a little

moved = {}
for v in me.vertices:
    if v.index in lip or jw.get(v.index, 0.0) < 0.2:
        continue
    if v.co.z > -0.070 or v.co.y > -0.02:
        continue
    w = fall(v.co, CENTER, RADIUS)
    if w <= 0.0:
        continue
    d = DELTA * w
    v.co = v.co + d
    moved[v.index] = d

if me.shape_keys is not None:
    for kb in me.shape_keys.key_blocks[1:]:
        for i, d in moved.items():
            kb.data[i].co = kb.data[i].co + d

me.update()
print("CHIN: %s moved %d verts, keys %d" % (head.name, len(moved), (len(me.shape_keys.key_blocks) - 1) if me.shape_keys else 0))
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("CHIN: saved", DST)
