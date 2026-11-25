"""Real modelled nose (v68): lofted shell with bridge, tip, wings, underside.

The falloff-sculpted nose read flat. This builds actual geometry: a grid lofted
down the nose axis, each vertex rooted at the face skin at its own (x, z) so
the shell hugs the face, protruding by a modelled profile:
- bridge: narrow at the root between the brows, widening downward;
- tip: a ball, protruding ~16 mm from the face plane;
- wings: flare at the bottom sides, with an under-nose recess between them;
- the seam edge is pushed inside the face skin so no join line shows.
Skin material, rigged to 'head', mirrored by construction (symmetric grid).

Usage:
  blender --background --factory-startup --python tools/hero_rig/v9/add_nose_geo.py \
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
mw = head.matrix_world

for o in [o for o in bpy.data.objects if o.name.startswith("nose_geo")]:
    bpy.data.objects.remove(o, do_unlink=True)

verts_world = [mw @ v.co for v in head.data.vertices]
_cache = {}

# ---- smooth quadratic fit of the face plane y(x, z) around the nose --------
import numpy as np
samp = [p for p in verts_world
        if p.y < -0.09 and abs(p.x - HC.x) < 0.065 and 1.50 < p.z < 1.63]
A = np.array([[1.0, p.x - HC.x, p.z - 1.56, (p.x - HC.x) ** 2,
               (p.z - 1.56) ** 2, (p.x - HC.x) * (p.z - 1.56)] for p in samp])
b = np.array([p.y for p in samp])
coef, *_ = np.linalg.lstsq(A, b, rcond=None)


def face_y(x, z):
    """Smooth fitted face-surface y at (x, z)."""
    dx, dz = x - HC.x, z - 1.56
    return coef[0] + coef[1] * dx + coef[2] * dz + coef[3] * dx * dx \
        + coef[4] * dz * dz + coef[5] * dx * dz


NU, NV = 20, 18          # u: root->under nose, v: left wing -> right wing
Z_ROOT = 1.588           # bridge root
Z_TIP = 1.548            # tip centre
Z_SUB = 1.536            # under-nose

bm = bmesh.new()
grid = [[None] * NV for _ in range(NU + 1)]
for i in range(NU + 1):
    u = i / NU
    z = Z_ROOT + (Z_SUB - Z_ROOT) * (u ** 0.92)
    for j in range(NV):
        v = j / (NV - 1)
        s = 2 * v - 1                       # -1 left .. +1 right
        arch = 1.0 - s * s                  # arch across the nose width
        # half width profile: root narrow, wings flare at u~0.85
        if u < 0.7:
            hw = 0.010 + 0.006 * u
        else:
            hw = 0.014 + 0.008 * ((u - 0.7) / 0.3) ** 1.4
        x = HC.x + s * hw
        # protrusion profile beyond the face plane
        if u < 0.72:                        # bridge: concave dip then rise
            out = 0.010 * (u / 0.72) ** 1.6
            out *= 1.0 - 0.22 * math.exp(-((u - 0.38) / 0.20) ** 2)
        elif u < 0.88:                      # tip ball
            t = (u - 0.72) / 0.16
            out = 0.011 + 0.006 * math.sin(t * math.pi)
        else:                               # wings + under-nose recess
            t = (u - 0.88) / 0.12
            out = 0.017 - 0.013 * t
        # edges land flush on the skin: no flange, no seam gap
        out *= arch ** 0.5
        fy = face_y(x, z)
        # ride proud of the skin to avoid z-fighting, but flush at the rim
        y = fy - out + 0.0015 * min(1.0, out / 0.004)
        p = Vector((x, y, z))
        grid[i][j] = bm.verts.new(p)

for i in range(NU):
    for j in range(NV - 1):
        try:
            bm.faces.new([grid[i][j], grid[i][j + 1],
                          grid[i + 1][j + 1], grid[i + 1][j]])
        except ValueError:
            pass

# no rim tuck: the outer column is already flush with the skin (out -> 0)

bm.normal_update()
me = bpy.data.meshes.new("nose_geo")
bm.to_mesh(me)
bm.free()

o = bpy.data.objects.new("nose_geo", me)
coll.objects.link(o)
o.parent = arm
o.data.materials.append(mat)
for pg in o.data.polygons:
    pg.use_smooth = True
vg = o.vertex_groups.new(name="head")
vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
md = o.modifiers.new("Armature", 'ARMATURE')
md.object = arm

print("NOSE faces", len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=path)
print("SAVED", path)
