"""Second jaw pass on the merged master face: re-shape the hanging chin lobe.

`face_rebuild.py` joined a separate jaw shell whose lower part bulges below the
head as a ball on a short neck. This pass shrink-wraps the lobe's *silhouette*
(width and height) onto the head shell's smooth chin, but keeps the lobe's
existing forward projection, so the chin does not recede. It then adds a little
forward push and squares the jaw angle.

Every delta is carried into the Basis and every shape key, so expressions keep
their offsets. Lip faces (`lip_mouth`) are left alone.

Note: once a mesh has shape keys, `mesh.vertices[i].co` is not the Basis key
block. This pass writes both, or the change never reaches a rest-pose render.

    blender --background --factory-startup --python face_jaw2.py -- <in.blend> <out.blend>

One-off: running it twice compounds the move.
"""
import sys
import bpy
from mathutils import bvhtree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)

RIM_Z = -0.088     # lobe starts here (do not touch above it)
FULL_Z = -0.110    # full reshape below this
PROUD = 0.004      # stand this far outside the head shell (local units)
RADIUS = 0.050     # ignore wrap targets farther than this
KEEP_Y = 0.15      # how much of the head shell's receded front to accept
WIDE = 0.008       # extra lateral mass at the jaw angle
CHIN_FWD = 0.014   # forward push at the chin point


def sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


head = None
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("head"):
        if head is None or len(o.data.vertices) > len(head.data.vertices):
            head = o
if head is None:
    raise SystemExit("JAW2: no head mesh found")

me = head.data
n = len(me.vertices)
keys = me.shape_keys.key_blocks if me.shape_keys else None

# connected components: the joined jaw shell is the big one that reaches lowest
parent = list(range(n))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def union(a, b):
    a, b = find(a), find(b)
    if a != b:
        parent[b] = a


for e in me.edges:
    union(e.vertices[0], e.vertices[1])
groups = {}
for i in range(n):
    groups.setdefault(find(i), []).append(i)
big = [g for g in groups.values() if len(g) > 500]
jaw = set(min(big, key=lambda g: min(me.vertices[i].co.z for i in g)))
shell = set(max(big, key=len))
print("JAW2: jaw component %d verts, z %.3f..%.3f" % (
    len(jaw), min(me.vertices[i].co.z for i in jaw),
    max(me.vertices[i].co.z for i in jaw)))

# BVH of the head shell only: the smooth chin whose width we copy
shell_faces = [list(p.vertices) for p in me.polygons
               if all(v in shell for v in p.vertices)]
bvh = bvhtree.BVHTree.FromPolygons([v.co.copy() for v in me.vertices],
                                   shell_faces, all_triangles=False)
print("JAW2: head shell %d verts, %d faces" % (len(shell), len(shell_faces)))

lip = set()
for p in me.polygons:
    m = me.materials[p.material_index] if p.material_index < len(me.materials) else None
    if m is not None and m.name == "lip_mouth":
        lip.update(p.vertices)

moved = {}
for i in jaw:
    if i in lip:
        continue
    co = me.vertices[i].co
    if co.z > RIM_Z:
        continue
    w = sstep(RIM_Z, FULL_Z, co.z)          # 0 at the rim, 1 low on the lobe
    if w <= 0.0:
        continue
    loc, nor, idx, dist = bvh.find_nearest(co, RADIUS)
    if loc is None or nor is None:
        continue
    target = loc + nor * PROUD
    new = co.lerp(target, w)
    new.y = co.y + (target.y - co.y) * (KEEP_Y * w)   # keep the projection

    # give the lower face a bit more mass: square the gonion and lead with the chin
    wz = sstep(-0.078, -0.102, co.z)
    side = sstep(0.020, 0.048, abs(co.x))
    new.x += WIDE * wz * side * (1.0 if co.x >= 0.0 else -1.0)
    cf = sstep(-0.092, -0.112, co.z) * (1.0 - sstep(0.018, 0.042, abs(co.x)))
    new.y -= CHIN_FWD * cf

    d = new - co
    if d.length_squared < 1e-12:
        continue
    me.vertices[i].co = new
    if keys is not None:
        keys[0].data[i].co = new            # Basis is separate from me.vertices
        for kb in keys[1:]:
            kb.data[i].co = kb.data[i].co + d
    moved[i] = d

me.update()
ys = [me.vertices[i].co.y for i in moved]
zs = [me.vertices[i].co.z for i in moved]
print("JAW2: reshaped %d verts, %d keys; y %.3f..%.3f z %.3f..%.3f" % (
    len(moved), (len(keys) - 1) if keys else 0,
    min(ys) if ys else 0.0, max(ys) if ys else 0.0,
    min(zs) if zs else 0.0, max(zs) if zs else 0.0))
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("JAW2: saved", DST)
