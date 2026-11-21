"""Render neutral front/quarter views of a .blend or .glb (imported) for quick visual QA.

    blender --background --factory-startup --python render_check.py -- <in.blend|in.glb> <out_dir>
"""
import os
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)

if SRC.lower().endswith(".glb"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
else:
    bpy.ops.wm.open_mainfile(filepath=SRC)

print("RENDER_CHECK: objects ---")
for o in bpy.data.objects:
    if o.type == "MESH":
        print("RC-MESH:", o.name, len(o.data.vertices), "mat:", [m.material.name if m.material else "?" for m in o.material_slots])

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
sun_data = bpy.data.lights.new("sun", type="SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (0.6, 0.1, 0.4)

# head sits around z=1.55, faces -Y: camera in front, slightly high
views = {
    "front": (Vector((0.0, -1.35, 1.62)), (1.5708, 0.0, 0.0)),
    "q34":   (Vector((0.55, -1.05, 1.62)), (1.5708, 0.0, -0.48)),
}
cam_data.lens = 50
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
for nm, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = rot
    scn.render.filepath = os.path.join(OUT, nm + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDER_CHECK: saved", scn.render.filepath)
