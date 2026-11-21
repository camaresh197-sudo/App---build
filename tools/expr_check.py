"""Render the master's head close-up with selected shape keys driven and the hat hidden.

    blender --background --factory-startup --python expr_check.py -- <in.blend> <out.png> [key=value ...]
"""
import os
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)

head = bpy.data.objects.get("head_12")
if head is None:
    raise SystemExit("EXPR: no head_12")
if head.data.shape_keys:
    for kv in argv[2:]:
        k, v = kv.split("=")
        kb = head.data.shape_keys.key_blocks.get(k)
        if kb is not None:
            kb.value = float(v)
            print("EXPR: set", k, v)
        else:
            print("EXPR: no key", k)
    # isolate: every other key to 0 unless the args name it
    for kb in head.data.shape_keys.key_blocks:
        if kb.name == "Basis":
            continue
        if not any(kv.startswith(kb.name + "=") for kv in argv[2:]):
            kb.value = 0.0

# hide hat + hair locks so the crown is visible
for o in bpy.data.objects:
    if o.type == "MESH" and (o.name.startswith("hat") or o.name.startswith("hair") or o.name == "head_118"):
        o.hide_render = True
        print("EXPR: hidden", o.name)

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
cam_data.lens = 65
tgt = Vector((0.0, 0.0, 1.58))
cam.location = Vector((0.0, -0.95, 1.60))
d = tgt - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
sun_data = bpy.data.lights.new("sun", type="SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (0.6, 0.1, 0.4)
scn = bpy.context.scene
scn.camera = cam
try:
    scn.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    scn.render.engine = "BLENDER_EEVEE"
scn.render.resolution_x = 500
scn.render.resolution_y = 500
w = scn.world or bpy.data.worlds.new("World")
scn.world = w
if w.use_nodes:
    bg = w.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs[0].default_value = (0.55, 0.58, 0.62, 1.0)
        bg.inputs[1].default_value = 1.0
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("EXPR: saved", OUT)
