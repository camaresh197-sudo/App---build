"""Hair clumps v2 (v67 -> v68): skin-true radius, many narrow locks.

Failure log (preview/face_hair1..7):
- cards read as wires or leave bald gaps; one shell reads as a hood;
- v1 locks were too few/too wide and used the head ellipsoid for the front
  radius, so they floated 3-6 cm in front of the forehead and read as planks.

This version:
- radius per (z, lon) comes from the head mesh's own vertices: kd-tree lookup
  around the ellipsoid point, take the max radius of nearby skin vertices, so
  hair hugs the real forehead, temples and skull;
- ~60 narrow locks (20-28 mm) as tapered 6-sided tubes, overlapping;
- a small skull cap only at the top/back, fully covered by locks;
- fringe sweeps across the forehead away from a left part.

Usage (Blender 5.3 standalone, repo root):
  blender --background --factory-startup --python tools/hero_rig/v9/hair_locks.py \
      -- blender/wip/hero_v67_lids_light.blend blender/wip/hero_v68_hair.blend
"""
import bpy, sys, math, random, bmesh
from mathutils import Vector, kdtree

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=src)
random.seed(21)

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
old = {n: bpy.data.objects[n] for n in ("hair_l_0", "hair_r_0") if n in bpy.data.objects}
mat = old["hair_l_0"].data.materials[0]
coll = old["hair_l_0"].users_collection[0]

HC = Vector((0.085, -0.017, 1.58))
HRX, HRY, HRZ = 0.110, 0.130, 0.160
FRONT = -math.pi / 2 + 2 * math.pi
PART_LON = FRONT - math.radians(34)

# ---- skin radius from the head mesh vertices (kd-tree) -----------------------
head = bpy.data.objects["head_12"]
mw = head.matrix_world
verts = [mw @ v.co for v in head.data.vertices]
kd = kdtree.KDTree(len(verts))
for i, p in enumerate(verts):
    kd.insert(p, i)
kd.balance()

_r_cache = {}


def base_r(lon):
    return math.hypot(HRX * math.cos(lon), HRY * math.sin(lon))


def ell_z(z):
    q = (z - HC.z) / HRZ
    q = max(-1.0, min(1.0, q))
    return math.sqrt(max(0.0, 1.0 - q * q))


def skin_r(z, lon):
    """Max horizontal radius of nearby head vertices, never inside the ellipsoid."""
    key = (round(z, 3), round(lon, 3))
    if key in _r_cache:
        return _r_cache[key]
    p0 = Vector((HC.x + base_r(lon) * ell_z(z) * math.cos(lon),
                 HC.y + base_r(lon) * ell_z(z) * math.sin(lon), z))
    best = 0.0
    for (co, idx, dist) in kd.find_range(p0, 0.055):
        dv = co - Vector((HC.x, HC.y, z))
        if dv.length < 0.005:
            continue
        a = abs(((math.atan2(dv.y, dv.x) - lon + math.pi) % (2 * math.pi)) - math.pi)
        if a > math.radians(35):
            continue
        best = max(best, math.hypot(dv.x, dv.y))
    if best <= 0.0:
        best = base_r(lon) * ell_z(z)
    _r_cache[key] = best
    return best


def path(root_z, root_lon, tip_z, tip_lon, lift0, lift1, wave, phase, n=12, wobble=0.0):
    pts = []
    for k in range(n + 1):
        t = k / n
        z = root_z + (tip_z - root_z) * (t ** 1.25)
        lon = root_lon + (tip_lon - root_lon) * t + wobble * math.sin(3.0 * t + phase) * t
        r = skin_r(max(z, 1.41), lon)
        if z < 1.41:
            r = max(r, skin_r(1.41, lon)) * (1.0 + 0.06 * (1.41 - z))
        lift = lift0 + (lift1 - lift0) * (t ** 1.5) + wave * math.sin(2.6 * t + phase) * t
        pts.append(Vector((HC.x + (r + lift) * math.cos(lon),
                           HC.y + (r + lift) * math.sin(lon), z)))
    return pts


def cap():
    NLON, NROW = 64, 12
    rows = []
    for j in range(NROW + 1):
        s = j / NROW
        ring = []
        for i in range(NLON):
            lon = 2 * math.pi * i / NLON
            d = abs(((lon - FRONT + math.pi) % (2 * math.pi)) - math.pi)
            tz = 1.700 - 0.30 * (d / math.pi) ** 1.4
            z = 1.746 - (1.746 - tz) * (s ** 1.2)
            r = skin_r(max(z, 1.50), lon) + 0.0022
            ring.append(Vector((HC.x + r * math.cos(lon), HC.y + r * math.sin(lon), z)))
        rows.append(ring)
    return rows


def build_mesh(rows):
    me = bpy.data.meshes.new("cap")
    bm = bmesh.new()
    vg_ = [[bm.verts.new(p) for p in ring] for ring in rows]
    for j in range(len(rows) - 1):
        n = len(rows[0])
        for i in range(n):
            k = (i + 1) % n
            try:
                bm.faces.new([vg_[j][i], vg_[j][k], vg_[j + 1][k], vg_[j + 1][i]])
            except ValueError:
                pass
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    return me


def tube(pts, width, thick, sides=6, taper=0.92, twist=0.0):
    me = bpy.data.meshes.new("lock")
    bm = bmesh.new()
    rings = []
    for k, p in enumerate(pts):
        t = k / (len(pts) - 1)
        tang = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        radial = Vector((p.x - HC.x, p.y - HC.y, 0)).normalized()
        side = tang.cross(radial).normalized()
        up = side.cross(tang).normalized()
        w = width * (1.0 - taper * t) * 0.5
        th = thick * (1.0 - taper * t) * 0.5
        ring = []
        for i in range(sides):
            a = 2 * math.pi * i / sides + twist
            ring.append(bm.verts.new(p + side * (w * math.cos(a)) + up * (th * math.sin(a))))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new([rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]])
    bm.faces.new(list(reversed(rings[-1])))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    return me


locks = []
W = 0.024

# fringe: 10 locks, roots at the hairline, sweep away from the part
for i in range(10):
    lon0 = FRONT + math.radians(-50 + 10 * i) + random.uniform(-1.5, 1.5)
    if abs(lon0 - PART_LON) < math.radians(4):
        continue
    sweep = -1.0 if lon0 > PART_LON else 1.0
    pts = path(1.662, lon0, 1.645, lon0 + math.radians(14) * sweep,
               0.003, 0.006, 0.003, random.uniform(0, 6.28), 9, 0.02)
    locks.append((pts, W, 0.012))

# sides: three layers, temple to shoulder
for row, (root_z, cnt, tipz) in enumerate(((1.640, 5, 1.330), (1.575, 5, 1.255), (1.515, 5, 1.210))):
    for i in range(cnt):
        lon0 = FRONT + math.radians(64 + 18 * i + row * 5) + random.uniform(-1.5, 1.5)
        pts = path(root_z, lon0, tipz, lon0 + random.uniform(-0.04, 0.04),
                   0.003, 0.016, 0.008, random.uniform(0, 6.28), 11, 0.025)
        locks.append((pts, W + 0.004, 0.014))

# back: occiput to nape
for i in range(9):
    lon0 = FRONT + math.radians(140 + 9 * i) + random.uniform(-1.5, 1.5)
    pts = path(1.660, lon0 % (2 * math.pi), 1.180, lon0 % (2 * math.pi) + random.uniform(-0.03, 0.03),
               0.003, 0.018, 0.010, random.uniform(0, 6.28), 12, 0.025)
    locks.append((pts, W + 0.006, 0.016))

# crown: short locks fanning over the cap
for i in range(12):
    lon0 = random.uniform(0, 2 * math.pi)
    if abs(((lon0 - PART_LON + math.pi) % (2 * math.pi)) - math.pi) < math.radians(8):
        continue
    pts = path(1.730, lon0, 1.640, lon0 + random.uniform(-0.10, 0.10),
               0.003, 0.012, 0.005, random.uniform(0, 6.28), 7, 0.02)
    locks.append((pts, W, 0.012))

print("LOCKS", len(locks))

for o_old in list(bpy.data.objects):
    if o_old.name.startswith("hair_"):
        bpy.data.objects.remove(o_old, do_unlink=True)


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


me_cap = build_mesh(cap())
o_cap = finish("hair_cap", me_cap)

bm_all = bmesh.new()
for idx, (pts, w, th) in enumerate(locks):
    tmp = tube(pts, w, th, twist=random.uniform(0, 1.0))
    bm_all.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
bm_all.normal_update()
me_locks = bpy.data.meshes.new("locks")
bm_all.to_mesh(me_locks)
bm_all.free()
o_locks = finish("hair_l_0", me_locks)

print("FACES cap", len(me_cap.polygons), "locks", len(me_locks.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
