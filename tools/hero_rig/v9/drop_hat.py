"""Remove the hat entirely (per user, 2026-11-24): redo later.

Deletes every object whose name starts with 'hat' from the given blend and
saves it back. Usage:
  blender --background --factory-startup --python tools/hero_rig/v9/drop_hat.py \
      -- blender/wip/hero_v68_bald.blend
"""
import bpy, sys

path = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=path)
n = 0
for o in [o for o in bpy.data.objects if o.name.lower().startswith("hat")]:
    print("REMOVED", o.name, o.type, len(o.data.polygons) if o.type == "MESH" else "")
    bpy.data.objects.remove(o, do_unlink=True)
    n += 1
bpy.ops.wm.save_as_mainfile(filepath=path)
print("REMOVED_COUNT", n, "SAVED", path)
