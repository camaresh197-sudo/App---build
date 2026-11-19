"""Rebuild the lower face: join the jaw ball into the head, add a skin muzzle
under the lip tubes, and blend the jaw weights across the seam.

Run on the master (or a copy) after face_jaw.py:

    blender --background --factory-startup --python face_rebuild.py -- <in.blend> <out.blend>

Why: the head is an egg, the lips are separate tubes, and the jaw is a separate
ball. Joining the jaw makes one mesh (all seven shape keys expand correctly).
The muzzle is a skin ellipsoid joined into the same mesh, sitting just behind
the lip tubes, so they have a surface to attach to instead of floating.
"""
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=SRC)


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


head = bpy.data.objects.get("head_12")
jaw = bpy.data.objects.get("jaw_0")
if head is None or jaw is None:
    raise SystemExit("REBUILD: need head_12 and jaw_0")

# mouth centre in head-local space, taken from the lower lip mesh
lip = bpy.data.objects["lipLm"]
world_c = Vector((0, 0, 0))
for v in lip.data.vertices:
    world_c += lip.matrix_world @ v.co
world_c /= len(lip.data.vertices)
c = head.matrix_world.inverted() @ world_c
print("REBUILD: mouth centre (head local) %.3f %.3f %.3f" % (c.x, c.y, c.z))

# join the jaw into the head (Blender expands the shape keys to the joined verts)
bpy.ops.object.select_all(action="DESELECT")
head.select_set(True)
jaw.select_set(True)
bpy.context.view_layer.objects.active = head
bpy.ops.object.join()
head = bpy.context.view_layer.objects.active

# add a skin muzzle just behind the lip tubes and join it too
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.030,
                                    location=(c.x, c.y + 0.006, c.z))
muz = bpy.context.active_object
muz.scale = (1.35, 0.75, 0.60)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
if head.data.materials:
    muz.data.materials.append(head.data.materials[0])
bpy.ops.object.select_all(action="DESELECT")
head.select_set(True)
muz.select_set(True)
bpy.context.view_layer.objects.active = head
bpy.ops.object.join()
head = bpy.context.view_layer.objects.active
print("REBUILD: joined with muzzle -> %d verts" % len(head.data.vertices))

me = head.data
gj = head.vertex_groups.get("jaw")
gh = head.vertex_groups.get("head")
if gj is None or gh is None:
    raise SystemExit("REBUILD: missing head/jaw groups")
jaw_idx = gj.index

# weight everything below the lower lip to the jaw with a short blend band
seam = c.z - 0.012
blended = 0
for v in me.vertices:
    jw = 0.0
    for g in v.groups:
        if g.group == jaw_idx:
            jw = g.weight
            break
    if jw > 0.5:
        continue
    w = 1.0 - smoothstep(seam - 0.012, seam + 0.014, v.co.z)
    front = 1.0 - smoothstep(-0.020, 0.050, v.co.y)
    wj = 0.85 * w * front
    if wj > 0.001:
        gj.add([v.index], wj, "REPLACE")
        gh.add([v.index], 1.0 - wj, "REPLACE")
        blended += 1
print("REBUILD: blended %d verts into the jaw group" % blended)

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("REBUILD: saved", DST)
