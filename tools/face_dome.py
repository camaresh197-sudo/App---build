"""Tuck the scalp dome under the hair cap on the master face.

The skull dome (top z=0.147 local) pokes ~19 mm through the hair cap shell
(head_118, top z=0.128) as a skin horn at the crown's top-front. This lowers
verts above the cap by a smooth falloff so the dome sits ~5 mm under it, in the
basis AND every shape key (standard carried-delta practice).

    blender --background --factory-startup --python face_dome.py -- <in.blend> <out.blend>

One-off: running it twice keeps lowering the dome.
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)

CAP_TOP = 0.128
TARGET = 0.123   # dome rests this far below the cap shell
BAND = 0.018     # falloff width below the cap top

head = None
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("head"):
        if head is None or len(o.data.vertices) > len(head.data.vertices):
            head = o
me = head.data

moved = {}
for i, v in enumerate(me.vertices):
    z = v.co.z
    if z <= TARGET:
        continue
    w = 1.0 if z >= CAP_TOP else (CAP_TOP - z) / BAND   # full push above the cap, fading below it
    if w <= 0.0:
        continue
    dz = -(z - TARGET) * w
    if abs(dz) < 1e-5:
        continue
    moved[i] = dz

# Basis (key_blocks[0]) shares storage with the mesh verts, so iterating every
# key block lowers the basis and carries the same delta into all expressions.
if me.shape_keys:
    for kb in me.shape_keys.key_blocks:
        for i, dz in moved.items():
            kb.data[i].co.z += dz
else:
    for i, dz in moved.items():
        me.vertices[i].co.z += dz

me.update()
top = max(v.co.z for v in me.vertices)
print("DOME: %d verts lowered, new scalp top z %.3f (cap %.3f)" % (len(moved), top, CAP_TOP))
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("DOME: saved", DST)
