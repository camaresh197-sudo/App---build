"""Hair shell (v67 -> v68): sculpted wig surface fitted to the head ellipsoid.

Why: two card passes failed (preview/face_hair1_*, face_hair2_*): ribbons read as
wires, wide cards leave bald gaps, an undercoat reads as a helmet plate. Two
ray/hull attempts failed too: horizontal ray-casts hit inner skull faces and
holes at the crown, and a per-bin vertex hull was too sparse (0.015-0.047 m
radii at the forehead).

The head's own bounds give a stable ellipsoid: centre (0.085, -0.017, 1.58),
radii (0.108, 0.127, 0.158) from head_12's world bbox. The shell follows that
surface, then adds:
- a hairline at the brow top in front, dropping past the ears to the shoulders;
- a side part groove on the character's left;
- wavy ridges and an uneven tip edge, so it does not read as a cap;
- a crown pole above the skull top.

Usage (Blender 5.3 standalone, repo root):
  blender --background --factory-startup --python tools/hero_rig/v9/hair_shell.py \
      -- blender/wip/hero_v67_lids_light.blend blender/wip/hero_v68_hair.blend
"""
import bpy, sys, math, bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=src)

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
old = {n: bpy.data.objects[n] for n in ("hair_l_0", "hair_r_0") if n in bpy.data.objects}
mat = old["hair_l_0"].data.materials[0]
coll = old["hair_l_0"].users_collection[0]

# head_12 world bbox centre/radii (measured 2026-11-24)
HC = Vector((0.085, -0.017, 1.58))
HRX, HRY, HRZ = 0.113, 0.134, 0.165   # 5-6 mm outside the mesh: no skin poke-through
FRONT = -math.pi / 2 + 2 * math.pi
PART_LON = FRONT - math.radians(36)


def head_r(z, lon):
    q = (z - HC.z) / HRZ
    q = max(-1.0, min(1.0, q))
    base = math.hypot(HRX * math.cos(lon), HRY * math.sin(lon))
    return max(0.012, base * math.sqrt(max(0.0, 1.0 - q * q)))


TIP_Z_TOP = 1.748

TIPS = [(0, 1.660), (30, 1.652), (50, 1.628), (65, 1.585), (80, 1.500),
        (95, 1.380), (115, 1.280), (140, 1.205), (180, 1.170)]


def angle_from_front(lon):
    return abs(((lon - FRONT + math.pi) % (2 * math.pi)) - math.pi)


def tip_z(lon):
    d = math.degrees(angle_from_front(lon))
    for (d0, z0), (d1, z1) in zip(TIPS, TIPS[1:]):
        if d0 <= d <= d1:
            t = (d - d0) / (d1 - d0)
            z = z0 + (z1 - z0) * (t * t * (3 - 2 * t))
            break
    else:
        z = TIPS[-1][1]
    return z + 0.012 * math.sin(7.0 * lon + 0.6) + 0.008 * math.sin(13.0 * lon)


def edge_noise(lon):
    return 0.014 * math.sin(17.0 * lon + 2.1) + 0.010 * math.sin(29.0 * lon + 0.3)


def part_weight(lon):
    d = abs(((lon - PART_LON + math.pi) % (2 * math.pi)) - math.pi)
    return math.exp(-(d / math.radians(2.6)) ** 2)


NLON, NROW = 128, 30
rows = []
for j in range(NROW + 1):
    s = j / NROW
    ring = []
    for i in range(NLON):
        lon = 2 * math.pi * i / NLON
        front_d = angle_from_front(lon)
        tz = tip_z(lon) + edge_noise(lon) * (1.0 if front_d > math.radians(20) else 0.25)
        z = TIP_Z_TOP - (TIP_Z_TOP - tz) * (s ** 1.25)
        base = head_r(max(z, 1.44), lon)
        if z < 1.44:
            base = max(base, head_r(1.44, lon)) * (1.0 + 0.12 * (1.44 - z))
        off = 0.005 + 0.020 * s ** 1.6
        off -= 0.005 * part_weight(lon) * min(1.0, s * 4)
        off = max(off, 0.0016)
        wave = (0.0060 * math.sin(6.0 * lon + 0.4) * math.sin(2.3 * math.pi * s)
                + (0.0040 + 0.0100 * s) * math.sin(13.0 * lon + 1.3))
        taper = 0.012 * max(0.0, (s - 0.85) / 0.15) * (0.5 + 0.5 * math.sin(13.0 * lon + 1.3))
        rr = base + off + wave - taper
        x = HC.x + rr * math.cos(lon)
        y = HC.y + rr * math.sin(lon)
        z2 = z + 0.004 * math.sin(5.0 * lon + 1.1) * s
        ring.append(Vector((x, y, z2)))
    rows.append(ring)

for o_old in list(bpy.data.objects):
    if o_old.name.startswith("hair_"):
        bpy.data.objects.remove(o_old, do_unlink=True)

me = bpy.data.meshes.new("hair")
bm = bmesh.new()
vgrid = [[bm.verts.new(p) for p in ring] for ring in rows]
for j in range(NROW):
    for i in range(NLON):
        k = (i + 1) % NLON
        try:
            bm.faces.new([vgrid[j][i], vgrid[j][k], vgrid[j + 1][k], vgrid[j + 1][i]])
        except ValueError:
            pass
pole = bm.verts.new(Vector((HC.x, HC.y, TIP_Z_TOP)))
for i in range(NLON):
    k = (i + 1) % NLON
    try:
        bm.faces.new([pole, vgrid[0][k], vgrid[0][i]])
    except ValueError:
        pass
bm.normal_update()
bm.to_mesh(me)
bm.free()
o = bpy.data.objects.new("hair_l_0", me)
coll.objects.link(o)
o.parent = arm
o.data.materials.append(mat)
for p in o.data.polygons:
    p.use_smooth = True
vg = o.vertex_groups.new(name="head")
vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
md = o.modifiers.new("Armature", 'ARMATURE')
md.object = arm

print("FACES", len(me.polygons), "VERTS", len(me.vertices))
print("RAD", [round(head_r(z, FRONT) + 0.005, 3) for z in (1.70, 1.66, 1.60, 1.50)])
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
