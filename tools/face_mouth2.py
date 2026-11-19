"""Replace the bead-driven lip tubes with lip geometry that is part of the head.

The old lips were two skinned tube objects. Joining them directly broke their bind.
This pass rebuilds them as head geometry with fresh weights:

* upper lip  -> head bone
* lower lip  -> jaw bone (so the jaw still opens the mouth)
* lip material renamed "lip_mouth" so the runtime can colour just that surface
* the existing smile / frown / pucker shape keys get lip-corner motion
* a new "lip_up" key lifts the upper lip for the talk animation

The mustache, cavity, teeth and tongue stay as they are. Run after face_lips.py:

    blender --background --factory-startup --python face_mouth2.py -- <in.blend> <out.blend>
"""
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=SRC)
head = bpy.data.objects.get("head_12")
if head is None:
    raise SystemExit("MOUTH2: no head_12")

counts = {}
for name, group in (("lipUm", "head"), ("lipLm", "jaw")):
    o = bpy.data.objects.get(name)
    if o is None:
        raise SystemExit("MOUTH2: missing " + name)
    counts[name] = len(o.data.vertices)
    # give the flattened lip band some depth back so it reads as a lip, not a painted strip
    mw = o.matrix_world
    inv = mw.inverted()
    pts = [mw @ v.co for v in o.data.vertices]
    ymean = sum(p.y for p in pts) / len(pts)
    for v, p in zip(o.data.vertices, pts):
        p.y = ymean + (p.y - ymean) * 1.25
        v.co = inv @ p
    o.data.update()
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    o.vertex_groups.clear()
    vg = o.vertex_groups.new(name=group)
    vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
    if o.material_slots and o.material_slots[0].material:
        o.material_slots[0].material.name = "lip_mouth"

bpy.ops.object.select_all(action="DESELECT")
head.select_set(True)
for name in counts:
    bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active = head
bpy.ops.object.join()
head = bpy.context.view_layer.objects.active
me = head.data

n = len(me.vertices)
lo = n - sum(counts.values())
up_hi = lo + counts["lipUm"]
pts = [me.vertices[i].co for i in range(lo, n)]
xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
cx = (min(xs) + max(xs)) * 0.5
half = max(abs(min(xs) - cx), abs(max(xs) - cx), 1e-6)
print("MOUTH2: %d verts, lip block %d..%d, upper ends %d" % (n, lo, n - 1, up_hi))

# match the code's MOUTH_DY: the mustache/teeth/cavity are lifted 10 mm at runtime,
# so the static lips must start at the same height in the file.
DY = 0.010
for i in range(lo, n):
    me.vertices[i].co.z += DY
for kb in me.shape_keys.key_blocks:
    for i in range(lo, n):
        kb.data[i].co.z += DY
print("MOUTH2: lip bbox x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f] centre x %.3f"
      % (min(xs), max(xs), min(ys), max(ys), min(zs) + DY, max(zs) + DY, cx))

for kb in me.shape_keys.key_blocks:
    kn = kb.name.lower()
    if kn == "basis":
        continue
    for i in range(lo, n):
        p = me.vertices[i].co
        t = max(-1.0, min(1.0, (p.x - cx) / half))
        if kn == "smile":
            kb.data[i].co.z += 0.0095 * t * t
            kb.data[i].co.x += 0.0030 * t * abs(t)
        elif kn == "frown":
            kb.data[i].co.z -= 0.0055 * t * t
            kb.data[i].co.x -= 0.0015 * t * abs(t)
        elif kn == "pucker":
            kb.data[i].co.x -= 0.0055 * t
            kb.data[i].co.y -= 0.0025 * (1.0 - abs(t))

lk = head.shape_key_add(name="lip_up", from_mix=False)
for i in range(lo, up_hi):
    lk.data[i].co.z += 0.0050

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("MOUTH2: saved", DST)
