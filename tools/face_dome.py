"""Tuck the scalp dome under the hair cap on the master face.

The skull dome (top z=0.147 local) pokes ~19 mm through the hair cap shell
(head_118, top z=0.128) as a skin horn at the crown's top-front. This compresses
the crown verts toward an interior line by a smooth proportional squeeze (not a
hard flatten - a plateau at the cap height z-fights against the cap shell),
in the basis AND every shape key (standard carried-delta practice).

    blender --background --factory-startup --python face_dome.py -- <in.blend> <out.blend>

One-off: running it twice keeps compressing the crown.

Scope note (2026-11-21): written for the 03c3011-era master, whose scalp dome
poked through the hair cap at 3/4 angles. The godot-branch master (teeth
commits) no longer shows the poke - VERIFY with tools/crown_check.py before
running this on a newer master.
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)

T = 0.105    # the crown compresses toward this line - well under the cap shell (0.128)
K = 0.24     # fraction of the height above T that survives: smooth, no plateau
XMAX, YLO, YHI = 0.10, -0.10, 0.10

head = None
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("head"):
        if head is None or len(o.data.vertices) > len(head.data.vertices):
            head = o
me = head.data

moved = 0
# Basis (key_blocks[0]) and the mesh verts are separate storage in Blender 5.x;
# iterating every key block covers both.
for kb in me.shape_keys.key_blocks:
    for co in kb.data:
        p = co.co
        if p.z > T and abs(p.x) < XMAX and YLO < p.y < YHI:
            co.co.z = T + K * (p.z - T)
            moved += 1

me.update()
print("DOME: compressed %d coords, crown tops now <= %.3f (cap 0.128)" % (moved, T + K * 0.042))
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("DOME: saved", DST)
