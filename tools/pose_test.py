"""Prove the skin follows the bones: pose a couple of bones and re-render.

    blender --background --factory-startup --python pose_test.py -- <in.blend> <out.png>
"""
import sys
import bpy
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, OUT = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
for nm, eul in [("head", (0.0, 0.0, 0.5)), ("cheek_l", (0.0, 0.0, -0.3)), ("jaw", (0.4, 0.0, 0.0)), ("lip_u", (0.0, 0.0, 0.0))]:
    pb = arm.pose.bones.get(nm)
    if pb is None:
        print("POSE: no bone", nm)
        continue
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = Euler(eul)
    print("POSE: set", nm, eul)
bpy.ops.object.mode_set(mode="OBJECT")

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = Vector((0.0, -1.1, 1.62))
cam.rotation_euler = (1.5708, 0.0, 0.0)
cam_data.lens = 50
bpy.context.scene.camera = cam
sun_data = bpy.data.lights.new("sun", type="SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (0.6, 0.1, 0.4)
w = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
if bg is not None:
    bg.inputs[0].default_value = (0.55, 0.58, 0.62, 1.0)
    bg.inputs[1].default_value = 1.0
scn = bpy.context.scene
try:
    scn.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    scn.render.engine = "BLENDER_EEVEE"
scn.render.resolution_x = 400
scn.render.resolution_y = 400
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("POSE: rendered", OUT)
