"""Verify a rigged .blend: report the armature, confirm every mesh is bound, and
render a front view so the skinning can be eyeballed.

    blender --background --factory-startup --python verify_rig.py -- <in.blend> <out.png>
"""
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, OUT = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=SRC)

arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print("VERIFY: armatures %d, meshes %d" % (len(arms), len(meshes)))
if arms:
    a = arms[0]
    print("VERIFY: bones", len(a.data.bones))
    print("VERIFY: sample bones", sorted(b.name for b in a.data.bones)[:12])
    unbound = [m.name for m in meshes if not any(md.type == "ARMATURE" for md in m.modifiers)]
    print("VERIFY: meshes without armature modifier:", len(unbound), unbound[:5])
    nogroup = [m.name for m in meshes if len(m.vertex_groups) == 0]
    print("VERIFY: meshes with no vertex group:", len(nogroup), nogroup[:5])

# a quick front render
cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = Vector((0.0, -3.2, 1.1))
cam.rotation_euler = (1.5708, 0.0, 0.0)
cam_data.lens = 55
bpy.context.scene.camera = cam

sun_data = bpy.data.lights.new("sun", type="SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (0.7, 0.2, 0.5)

# ambient so the face under the wide brim is not pure black
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
scn.render.resolution_y = 620
scn.render.film_transparent = False
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("VERIFY: rendered", OUT)
