"""Render the crown: hair + topknot visible, all shape keys zero, close camera.

    blender --background --factory-startup --python crown_check.py -- <in.blend> <out.png>
"""
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])

head = bpy.data.objects.get("head_12")
if head is not None and head.data.shape_keys:
    for kb in head.data.shape_keys.key_blocks:
        if kb.name != "Basis":
            kb.value = 0.0
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("hat"):
        o.hide_render = True

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
cam_data.lens = 70
tgt = Vector((0.0, 0.0, 1.66))
cam.location = Vector((0.35, -0.75, 2.02))
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
scn.render.filepath = argv[1]
bpy.ops.render.render(write_still=True)
print("CROWN: saved", argv[1])
