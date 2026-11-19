"""A Blender pass over the master character .blend.

blender/character_rigged.blend is the master for the character's mesh (see
blend_to_glb.py). This is the tidy-up to run after editing it: weld coincident
verts, fix normals, shade smooth, and take the sphericity out of the head so it
reads as a head rather than a ball.

    blender --background --factory-startup --python face_pass.py -- <in.blend> <out.blend>
"""
import sys
import bpy
import bmesh

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=SRC)


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def reshape_head(me):
    # the head is a pure ellipsoid: flatten the back and narrow the crown so the skull is not a sphere
    for v in me.vertices:
        x, y, z = v.co
        if z < 0.0:
            z *= 1.0 - 0.11 * smoothstep(0.0, 0.10, -z)
        t = smoothstep(0.04, 0.115, y)
        if t > 0.0:
            x *= 1.0 - 0.11 * t
            z *= 1.0 - 0.06 * t
        v.co = (x, y, z)


# the head is the biggest mesh on the head bone; its name carries a child index that can shift, so match by size
head = None
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("head"):
        if head is None or len(o.data.vertices) > len(head.data.vertices):
            head = o

names = []
for o in list(bpy.data.objects):
    if o.type != "MESH":
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(o.data)
    bm.free()
    if o is head:
        reshape_head(o.data)
    o.data.update()
    if len(o.data.vertices) > 64:      # smooth the round parts; leave hard-edged parts (teeth, boxes) faceted
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.shade_smooth()
    names.append(o.name)

print("FACE: tidied %d meshes; head reshaped: %s" % (len(names), head.name if head else "NOT FOUND"))
if head is None:
    print("FACE: mesh names -> %s" % ", ".join(names[:40]))

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("FACE: saved", DST)
