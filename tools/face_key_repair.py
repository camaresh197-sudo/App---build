"""Repair the expression shape keys on the merged master face.

History: face_shapes.py authored smile/squint/frown/pucker/brow/snarl in the OLD
pre-merge mesh's local frame. After the mesh moved/re-scaled, every displacement
ball landed off-target - the smile's cheek anchor sits on the skull top, so
grin/laugh erupt a scalp horn (and the keys are wrong elsewhere).

This pass, per key:
  1. current_delta - stale_script_delta  -> keeps the later correct additions
     (face_mouth2 lip-corner motion, face_chin delta) and cancels most of the
     stale field,
  2. masks the residual to the face region (smooth caps),
  3. re-adds the expression, re-authored with anchors measured in the CURRENT
     frame (from the control bones: mouth corners (±0.037,-0.075,-0.067), eyes
     (±0.040,-0.073,+0.025), brows (±0.038,-0.084,+0.063), nose wings
     (±0.009,-0.104,-0.029), cheek (±0.046,-0.054,-0.034), chin (0,-0.04,-0.100)).

    blender --background --factory-startup --python face_key_repair.py -- <in.blend> <out.blend>

One-off. Idempotence: not guaranteed - it subtracts the stale field, which is
only present once. Keep a backup of the input.
"""
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)


def fall(p, c, r):
    w = 1.0 - (p - c).length / r
    if w <= 0.0:
        return 0.0
    return w * w * (3.0 - 2.0 * w)


def clamp(x, a, b):
    return max(a, min(b, x))


def fade(v, lo, hi, f):
    # 0 outside [lo, hi], smooth 1 inside, fading over f at both edges
    return clamp(min((v - lo) / f, (hi - v) / f, 1.0), 0.0, 1.0)


# ---- the stale field, verbatim face_shapes.py anchors (old frame) ----
def smile_old(p):
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        d += Vector((0.041 * s, 0.026, 0.023)) * fall(p, Vector((0.048 * s, -0.028, 0.056)), 0.068)
        d += Vector((0.014 * s, 0.019, 0.004)) * fall(p, Vector((0.034 * s, -0.068, 0.084)), 0.038)
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):
            c = Vector((0.017 * s, -0.030, 0.096)).lerp(Vector((0.035 * s, -0.066, 0.084)), t)
            d -= Vector((0.009 * s, 0.0, 0.009)) * fall(p, c, 0.021)
    return d


def squint_old(p):
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        d += Vector((-0.014 * s, 0.0, -0.006)) * fall(p, Vector((0.066 * s, 0.022, 0.062)), 0.044)
        d += Vector((0.0, 0.013, 0.007)) * fall(p, Vector((0.040 * s, 0.006, 0.088)), 0.034)
    return d


def frown_old(p):
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        d += Vector((0.005 * s, -0.016, -0.003)) * fall(p, Vector((0.034 * s, -0.066, 0.084)), 0.038)
    d += Vector((0.0, 0.007, -0.005)) * fall(p, Vector((0.0, 0.050, 0.094)), 0.030)
    return d


def brow_old(p):
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        d += Vector((0.0, 0.015, 0.004)) * fall(p, Vector((0.043 * s, 0.062, 0.081)), 0.038)
    d += Vector((0.0, 0.009, 0.003)) * fall(p, Vector((0.0, 0.050, 0.094)), 0.032)
    return d


def snarl_old(p):
    d = Vector((0.0, 0.0, 0.0))
    for yy in (0.018, 0.028, 0.038):
        d -= Vector((0.0, 0.0, 0.006)) * fall(p, Vector((0.0, yy, 0.100)), 0.017)
    for s in (-1.0, 1.0):
        d += Vector((0.006 * s, 0.0, 0.003)) * fall(p, Vector((0.015 * s, -0.022, 0.100)), 0.022)
    return d


def pucker_old(p):
    d = Vector((0.0, 0.0, 0.0))
    d += Vector((0.0, 0.001, 0.011)) * fall(p, Vector((0.0, -0.064, 0.088)), 0.040)
    for s in (-1.0, 1.0):
        d += Vector((-0.007 * s, 0.0, -0.002)) * fall(p, Vector((0.050 * s, -0.030, 0.056)), 0.052)
    return d


OLD = {"smile": smile_old, "squint": squint_old, "frown": frown_old,
       "pucker": pucker_old, "brow": brow_old, "snarl": snarl_old}

# ---- the expressions, re-authored in the CURRENT frame ----
def smile_new(p):
    # cheek mounds up and forward, the corner lifts, a crease pulls in beside it
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        d += Vector((0.041 * s, -0.021, 0.027)) * fall(p, Vector((0.046 * s, -0.054, -0.034)), 0.072)
        d += Vector((0.014 * s, -0.004, 0.019)) * fall(p, Vector((0.037 * s, -0.075, -0.067)), 0.040)
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):
            c = Vector((0.016 * s, -0.100, -0.030)).lerp(Vector((0.035 * s, -0.075, -0.065)), t)
            d -= Vector((0.009 * s, -0.008, 0.0)) * fall(p, c, 0.023)
    return d


def squint_new(p):
    # outer eye corner pulls in and back, the lower lid pushes up
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        d += Vector((-0.014 * s, 0.006, 0.0)) * fall(p, Vector((0.058 * s, -0.072, 0.024)), 0.046)
        d += Vector((0.0, -0.007, 0.013)) * fall(p, Vector((0.040 * s, -0.075, 0.018)), 0.036)
    return d


def frown_new(p):
    # mouth corners drag down; a furrow pulls in between the brows
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        d += Vector((0.005 * s, 0.003, -0.016)) * fall(p, Vector((0.037 * s, -0.075, -0.067)), 0.040)
    d += Vector((0.0, 0.005, 0.007)) * fall(p, Vector((0.0, -0.086, 0.052)), 0.032)
    return d


def brow_new(p):
    # the brow ridge lifts and takes the forehead skin with it
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        d += Vector((0.0, -0.004, 0.015)) * fall(p, Vector((0.038 * s, -0.084, 0.063)), 0.042)
    d += Vector((0.0, -0.003, 0.009)) * fall(p, Vector((0.0, -0.086, 0.052)), 0.034)
    return d


def snarl_new(p):
    # the nose bridge wrinkles back and the wings flare
    d = Vector((0.0, 0.0, 0.0))
    for c in (Vector((0.0, -0.095, 0.010)), Vector((0.0, -0.092, 0.025)), Vector((0.0, -0.089, 0.040))):
        d -= Vector((0.0, -0.006, 0.0)) * fall(p, c, 0.019)
    for s in (-1.0, 1.0):
        d += Vector((0.006 * s, -0.003, 0.0)) * fall(p, Vector((0.014 * s, -0.102, -0.028)), 0.024)
    return d


def pucker_new(p):
    # the mouth pushes forward, the cheeks hollow in
    d = Vector((0.0, 0.0, 0.0))
    d += Vector((0.0, -0.010, 0.001)) * fall(p, Vector((0.0, -0.078, -0.068)), 0.044)
    for s in (-1.0, 1.0):
        d += Vector((-0.007 * s, 0.002, 0.0)) * fall(p, Vector((0.046 * s, -0.054, -0.034)), 0.056)
    return d


NEW = {"smile": smile_new, "squint": squint_new, "frown": frown_new,
       "pucker": pucker_new, "brow": brow_new, "snarl": snarl_new}

# per-key z ceilings for the residual mask (above the eye line only the brow may move)
ZCAP = {"smile": 0.050, "squint": 0.058, "frown": 0.056, "pucker": 0.030, "brow": 0.072, "snarl": 0.034}
FADE = 0.014

head = None
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("head"):
        if head is None or len(o.data.vertices) > len(head.data.vertices):
            head = o
if head is None:
    raise SystemExit("REPAIR: no head mesh")
me = head.data
ks = me.shape_keys.key_blocks

n = len(me.vertices)
report = []
for name, old_fn in OLD.items():
    kb = ks.get(name)
    if kb is None:
        print("REPAIR: no key", name)
        continue
    new_fn = NEW[name]
    zcap = ZCAP[name]
    moved = 0
    big = 0.0
    for i, v in enumerate(me.vertices):
        p = v.co
        cur = kb.data[i].co - p
        if cur.length < 1e-6 and fall(p, Vector((0.0, -0.08, -0.03)), 0.16) <= 0.0:
            continue
        # 1+2: keep the additions, drop the stale field, mask to the face
        resid = cur - old_fn(p)
        zc = fade(p.z, -0.118, zcap, FADE)
        yc = fade(p.y, -0.118, 0.012 + 0.043 * clamp((-0.045 - p.z) / 0.035, 0.0, 1.0), 0.010)
        d = resid * (zc * yc)
        # 3: the re-authored expression
        d += new_fn(p)
        if (kb.data[i].co - (p + d)).length > 1e-6:
            moved += 1
        big = max(big, d.length)
        kb.data[i].co = p + d
    report.append((name, moved, big))
    print("REPAIR: %-7s verts touched %d, max |delta| %.3f" % (name, moved, big))

print("REPAIR: keys ->", [k.name for k in ks])
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("REPAIR: saved", DST)
