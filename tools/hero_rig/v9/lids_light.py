"""Lighten the hero's four eyelid meshes (v66 -> v67).

Each lid is a sphere section, ~4k quads, weighted 100% to one lid bone, no shape
keys. Un-subdivide keeps the quad grid and the silhouette: 15,860 -> 4,318
faces with a rim shift of <= 1.35 mm (2 iterations). A third iteration reaches
2,440 faces but shifts the upper rim 2.43 mm and reads faceted at 2x zoom.

Usage (Blender 5.3 standalone, from the repo root):
  blender --background --factory-startup --python tools/hero_rig/v9/lids_light.py \
      -- blender/wip/hero_v66_brows_flat.blend blender/wip/hero_v67_lids_light.blend 2

Prints per-lid faces, boundary-rim deviation (mm) and bbox deviation (mm).
Never run twice on the same file; always start from v66.
"""
import bpy, sys, bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, dst = argv[0], argv[1]
iters = int(argv[2]) if len(argv) > 2 else 2

bpy.ops.wm.open_mainfile(filepath=src)
names = ["lidu_r_0", "lidu_l_0", "lidl_r_0", "lidl_l_0"]
report = []


def rim_pts(o):
    """Midpoints of boundary edges: the lid opening rim."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    pts = [(e.verts[0].co.copy() + e.verts[1].co.copy()) / 2 for e in bm.edges if e.is_boundary]
    bm.free()
    return pts


for name in names:
    o = bpy.data.objects[name]
    before_f = len(o.data.polygons)
    rim_before = rim_pts(o)
    bb_before = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mod = o.modifiers.new("light", 'DECIMATE')
    mod.decimate_type = 'UNSUBDIV'
    mod.iterations = iters
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=mod.name)
    after_f = len(o.data.polygons)
    rim_after = rim_pts(o)
    worst = 0.0
    for p in rim_before:
        d = min((p - q).length for q in rim_after) if rim_after else 99
        worst = max(worst, d)
    bb_after = [o.matrix_world @ Vector(c) for c in o.bound_box]
    bb_delta = max((a - b).length for a, b in zip(bb_before, bb_after))
    report.append((name, before_f, after_f, len(rim_before), len(rim_after),
                   round(worst * 1000, 3), round(bb_delta * 1000, 3)))

tot_b = sum(r[1] for r in report)
tot_a = sum(r[2] for r in report)
for r in report:
    print("LID", r[0], "faces", r[1], "->", r[2], "rimverts", r[3], "->", r[4],
          "rim_dev_mm", r[5], "bbox_dev_mm", r[6])
print("TOTAL", tot_b, "->", tot_a, "saved", tot_b - tot_a)
bpy.ops.wm.save_as_mainfile(filepath=dst)
print("SAVED_BLEND", dst)
