"""Hair pass v2 (v67 -> v68): layered wide clumps, skin-conformed, no plates.

What failed in the first attempt (render `preview/face_hair1_*`):
- a flat undercoat read as a grey helmet plate;
- 8.5 mm ribbons seen edge-on read as wires;
- side-front cards hung down over the cheek and mouth;
- hairline left a bald dome.

This version: wider clumps (18-28 mm) in layered rows, each card rotated
around its own tangent so the ribbons face different ways, no undercoat.
Hairline comes down to the top of the brows; side and back rows cover the
temples and occiput. One left-side list is mirrored.

Usage (Blender 5.3 standalone, repo root):
  blender --background --factory-startup --python tools/hero_rig/v9/hair_cards_v2.py \
      -- blender/wip/hero_v67_lids_light.blend blender/wip/hero_v68_hair.blend
"""
import bpy, sys, math, random, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=src)
random.seed(5)

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
old = {n: bpy.data.objects[n] for n in ("hair_l_0", "hair_r_0")}
mat = old["hair_l_0"].data.materials[0]
coll = old["hair_l_0"].users_collection[0]

C = Vector((0.10, -0.075, 1.56))
RX, RY, RZ = 0.142, 0.118, 0.152
SEG = 14
PART_LO, PART_HI = 3.55, 3.95          # character-left side part
FRONT = -math.pi / 2 + 2 * math.pi

dg = bpy.context.evaluated_depsgraph_get()
head_eval = bpy.data.objects["head_12"].evaluated_get(dg)
skin = BVHTree.FromObject(head_eval, dg)


def dir_of(lat, lon):
    return Vector((math.cos(lat) * math.cos(lon) * RX,
                   math.cos(lat) * math.sin(lon) * RY,
                   math.sin(lat) * RZ)).normalized()


def skin_point(lat, lon, off):
    d = dir_of(lat, lon)
    hit, normal, index, dist = skin.ray_cast(C + d * 0.6, -d)
    if hit is not None:
        return hit + normal * off
    return Vector((C.x + RX * math.cos(lat) * math.cos(lon),
                   C.y + RY * math.cos(lat) * math.sin(lon),
                   C.z + RZ * math.sin(lat)))


def eye_band(p):
    return p.y < -0.115 and 1.44 < p.z < 1.655 and 0.0 < p.x < 0.20


def clump(lat0, lon0, end_lat, sweep, width_conf, off0, off1, amp, phase, front_row=False):
    pts = []
    for k in range(SEG + 1):
        t = k / SEG
        lat = lat0 + (end_lat - lat0) * t
        lon = lon0 + sweep * t
        off = off0 + (off1 - off0) * t
        if front_row:
            off = min(off, 0.004)                     # fringe lies on the forehead
        p = skin_point(lat, lon, off)
        if lat < 0:
            anchor = pts[-1].z if pts else p.z
            p.z = anchor - math.sin(-lat) * 0.10       # hang below the jaw, no face crossing
        radial = Vector((math.cos(lon), math.sin(lon), 0))
        p = p + radial * (amp * t * math.sin(8 * t + phase))
        pts.append(p)
    return pts


def ok(pts):
    """Reject cards crossing the eye/brow band."""
    return not any(eye_band(p) for p in pts)


left = []
PART_LON = FRONT - math.radians(36)

# 1. fringe row: hairline at the brow top, swept away from the part
for i in range(14):
    lon0 = FRONT + math.radians(-52 + 7.0 * i) + random.uniform(-1.5, 1.5)
    if abs(lon0 - PART_LON) < math.radians(4):
        continue
    lat0 = math.radians(random.uniform(56, 66))
    end = math.radians(random.uniform(38, 43))
    sweep = -0.35 if lon0 < PART_LON else 0.35
    pts = clump(lat0, lon0, end, sweep, 1, 0.0035, 0.0045,
                random.uniform(0.004, 0.008), random.uniform(0, 6.28), front_row=True)
    if ok(pts):
        left.append((pts, 0.020))

# 2. temple rows: cover the sides down past the ears
for row, lat0_deg in enumerate((48, 34, 20, 6)):
    for i in range(7):
        lon0 = FRONT + math.radians(62 + (i / 6.0) * 88)   # side to back
        lat0 = math.radians(lat0_deg + random.uniform(-4, 4))
        pts = clump(lat0, lon0, lat0 - math.radians(random.uniform(22, 32)),
                    random.uniform(-0.10, 0.10), 1, 0.004, 0.016,
                    random.uniform(0.010, 0.020), random.uniform(0, 6.28))
        if ok(pts):
            left.append((pts, 0.024))

# 3. back rows: occiput to nape
for row, lat0_deg in enumerate((40, 24, 8, -8)):
    for i in range(6):
        lon0 = FRONT + math.radians(150 + (i / 5.0) * 80)  # back arc
        lat0 = math.radians(lat0_deg + random.uniform(-4, 4))
        pts = clump(lat0, lon0, lat0 - math.radians(random.uniform(22, 34)),
                    random.uniform(-0.10, 0.10), 1, 0.004, 0.018,
                    random.uniform(0.010, 0.022), random.uniform(0, 6.28))
        if ok(pts):
            left.append((pts, 0.026))

# 4. crown: short lifted clumps, leave the part gap
while sum(1 for _ in []) == 0 and len([1 for _, w in left if w == 0.021]) < 12:
    lon0 = random.uniform(math.pi * 1.5, math.pi * 2.5)
    if PART_LO < lon0 % (2 * math.pi) < PART_HI:
        continue
    lat0 = math.radians(random.uniform(72, 86))
    pts = clump(lat0, lon0, math.radians(random.uniform(46, 58)),
                random.uniform(-0.15, 0.15), 1, 0.004, 0.014,
                random.uniform(0.006, 0.012), random.uniform(0, 6.28))
    if ok(pts):
        left.append((pts, 0.021))

print("CLUMPS left", len(left))


def mirrored(pts):
    return [Vector((2 * C.x - p.x, p.y, p.z)) for p in pts]


right = []
for pts, w in left:
    m = mirrored(pts)
    lon = math.atan2(m[0].y - C.y, m[0].x - C.x) % (2 * math.pi)
    if PART_LO < lon < PART_HI:
        continue
    right.append((m, w))
print("CLUMPS right", len(right))


def build(name, items):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for pts, width in items:
        rot = Matrix.Rotation(random.uniform(-0.55, 0.55), 3, (pts[-1] - pts[0]).normalized())
        vl, vr = [], []
        for k, p in enumerate(pts):
            radial = Vector((p.x - C.x, p.y - C.y, 0)).normalized()
            tang = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
            side = rot @ tang.cross(radial).normalized()
            w = width * (1.0 - 0.92 * k / len(pts)) * random.uniform(0.9, 1.1)
            vl.append(bm.verts.new(p + side * w * 0.5))
            vr.append(bm.verts.new(p - side * w * 0.5))
        for k in range(len(pts) - 1):
            bm.faces.new([vl[k], vr[k], vr[k + 1], vl[k + 1]])
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
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


for n in old:
    bpy.data.objects.remove(old[n], do_unlink=True)
L = build("hair_l_0", left)
R = build("hair_r_0", right)
print("FACES", len(L.data.polygons), len(R.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
