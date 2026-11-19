"""Flatten the victory... no, the face's lip and mustache tubes along the face normal.

The lips are swept tubes with a round cross-section, so they read as sausages
sitting in front of the face even when their centreline is on the skin. This pass
squashes each tube's cross-section in world Y (the face's front axis) toward its
nearest bead-bone centre and tucks the whole tube a little way back. Width and
height are untouched.

    blender --background --factory-startup --python face_lips.py -- <in.blend> <out.blend>
"""
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

FLAT = 0.50        # keep 50% of the depth around the bead centre
TUCK = 0.0018      # move the whole tube back towards the face (world +Y)

bpy.ops.wm.open_mainfile(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
bones = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}

parts = {
    "lipUm": "lipU_",
    "lipLm": "lipL_",
    "mustm_l": "must_l_",
    "mustm_r": "must_r_",
}
for obj_name, prefix in parts.items():
    o = bpy.data.objects.get(obj_name)
    if o is None:
        continue
    centres = [p for n, p in bones.items() if n.startswith(prefix)]
    if not centres:
        print("LIPS: no bones for", obj_name)
        continue
    mw = o.matrix_world
    inv = mw.inverted()
    moved = 0
    for v in o.data.vertices:
        p = mw @ v.co
        c = min(centres, key=lambda q: (q - p).length_squared)
        p.y = c.y + (p.y - c.y) * FLAT + TUCK
        v.co = inv @ p
        moved += 1
    o.data.update()
    print("LIPS: %s - %d verts, %d beads" % (obj_name, moved, len(centres)))

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("LIPS: saved", DST)
