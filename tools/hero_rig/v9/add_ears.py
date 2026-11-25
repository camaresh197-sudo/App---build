"""Add ears (v68): procedural pinna left + right, skin material.

The head never had ears (hair covered the spot). This builds an ear shell per
side: elliptical pinna with raised helix rim and a concha bowl, tilted back
~10 deg, rooted at the widest point of the skull at eye/ear-line height.
Mirrored across the sagittal plane. Rigged to the 'head' vertex group like
the other code-created meshes.

Usage:
  blender --background --factory-startup --python tools/hero_rig/v9/add_ears.py \
      -- blender/wip/hero_v68_bald.blend
"""
import bpy, sys, math, bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
path = argv[0]
bpy.ops.wm.open_mainfile(filepath=path)

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
head = bpy.data.objects["head_12"]
mat = head.data.materials[0]
coll = head.users_collection[0]

HC = Vector((0.085, -0.017, 1.58))

# remove previous attempt
for o in [o for o in bpy.data.objects if o.name.startswith("ear_")]:
    bpy.data.objects.remove(o, do_unlink=True)

# skull radius at ear height, per side, from the mesh itself
mw = head.matrix_world
verts = [mw @ v.co for v in head.data.vertices]
zs = 1.565


def skull_x(sign, z, y):
    cand = [p.x for p in verts
            if abs(p.y - y) < 0.008 and abs(p.z - z) < 0.012
            and (p.x - HC.x) * sign > 0]
    return (max(cand) if sign > 0 else min(cand)) if cand else None


EAR_CZ = 1.562          # ear centre height
A = 0.034               # half height of the pinna
B = 0.019               # half width (front-back)
PROTRUDE = 0.018        # helix stands off the skull
NU, NV = 18, 12


def ear_mesh(sign):
    me = bpy.data.meshes.new("ear")
    bm = bmesh.new()
    grid = [[None] * NV for _ in range(NU + 1)]
    for i in range(NU + 1):
        u = i / NU                      # 0 = top, 1 = bottom of pinna
        z = EAR_CZ + A * math.cos(u * math.pi) * 1.0
        for j in range(NV):
            v = j / (NV - 1)            # 0 = back, 1 = front edge
            # ellipse half-width at this height, front edge thins out
            hw = B * math.sin(u * math.pi) ** 0.7
            y = HC.y - hw + 2 * hw * v
            # radial parameter for the shell profile
            du = abs(u - 0.5) * 2       # 0 centre, 1 rim
            dv = abs(v - 0.5) * 2
            rad = max(du, dv)           # square-ish ring param 0..1
            # helix rim raised at rad~0.75, concha bowl at centre
            if rad < 0.62:
                out = 0.007 + 0.004 * (1.0 - rad / 0.62)
            elif rad < 0.88:
                t = (rad - 0.62) / 0.26
                out = 0.011 + 0.009 * math.sin(t * math.pi)
            else:
                t = (rad - 0.88) / 0.12
                out = 0.020 - 0.012 * t
            # root at the skull surface at this vertex's own (y, z)
            rx = skull_x(sign, z, y)
            if rx is None:
                # fall back: nearest neighbour rows already known
                rx = HC.x + sign * 0.098
            x = rx + sign * out
            p = Vector((x, y, z))
            # tilt the top slightly back, lobe slightly forward
            p.y += 0.010 * math.cos(u * math.pi)
            grid[i][j] = bm.verts.new(p)
    for i in range(NU):
        for j in range(NV - 1):
            try:
                bm.faces.new([grid[i][j], grid[i][j + 1],
                              grid[i + 1][j + 1], grid[i + 1][j]])
            except ValueError:
                pass
    # close the rim with a fan to the root plate so the ear is solid-ish
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    return me


def finish(name, me):
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.parent = arm
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    vg = o.vertex_groups.new(name="head")
    vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    md = o.modifiers.new("Armature", 'ARMATURE')
    md.object = arm
    return o


finish("ear_l_0", ear_mesh(1))
finish("ear_r_0", ear_mesh(-1))
print("EARS added")
bpy.ops.wm.save_as_mainfile(filepath=path)
print("SAVED", path)
