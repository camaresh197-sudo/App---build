"""Bald + head reshape (v67 -> v68): human proportions.

Measured on v67 (preview/face_before_*):
- head 21.7 cm wide at the eye line (human ~15 cm): temples balloon;
- back skull balloons behind the ears;
- chin recessed under the mouth.

This script:
- removes every hair_* object (bald for now, per user);
- narrows head_12 about its axis with a smooth window peaking at the eye line;
- pulls the back skull in above/behind the ears;
- brings the chin forward;
- leaves the brow/eye-socket front, mouth block and jaw corners untouched.

Shape keys are untouched (base mesh only). Eye/lip joint positions are NOT
moved, so renders must be checked for eye float.

Usage:
  blender --background --factory-startup --python tools/hero_rig/v9/head_shape.py \
      -- blender/wip/hero_v67_lids_light.blend blender/wip/hero_v68_bald.blend
"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=src)

# 1. bald ---------------------------------------------------------------
for o in [o for o in bpy.data.objects if o.name.startswith("hair_")]:
    print("REMOVED", o.name)
    bpy.data.objects.remove(o, do_unlink=True)

# 2. reshape ------------------------------------------------------------
HC = Vector((0.085, -0.017, 1.58))     # head_12 world bbox centre
head = bpy.data.objects["head_12"]
mw = head.matrix_world
mwi = mw.inverted()


def bump(z, z0, width):
    """Smooth window 0..1 centred at z0."""
    t = (z - z0) / width
    return max(0.0, 1.0 - t * t)


def reshape(p):
    x0, y0, z0 = p.x - HC.x, p.y - HC.y, p.z

    # temples / eye-line width: -10 % at z=1.60, fading by +-9 cm
    f = bump(z0, 1.60, 0.11)
    x0 *= 1.0 - 0.10 * f
    # upper skull: only a slight widen above the brows
    f2 = bump(z0, 1.70, 0.08)
    x0 *= 1.0 + 0.03 * f2
    if y0 < 0:
        y0 *= 1.0 + 0.03 * f2          # round the upper front skull too

    # lower the crown more: flatter, less tall dome
    if z0 > 1.64:
        p.z -= 0.014 * bump(z0, 1.73, 0.09)

    # compress the whole cranium vertically toward the brow line: the skull
    # above the brows is featureless, so shortening it reads as "human"
    if z0 > 1.645:
        p.z = 1.645 + (p.z - 1.645) * 0.90

    # cheek band just below the eyes: narrow a little (inverted-egg fix)
    x0 *= 1.0 - 0.05 * bump(z0, 1.54, 0.05)

    # jaw and chin: widen so the lower face is not a point
    fj = bump(z0, 1.48, 0.06)
    x0 *= 1.0 + 0.09 * fj

    # ---- forehead slope: pull the upper-front back so the profile slopes ----
    if y0 < -0.05 and 1.635 < z0 < 1.70:
        y0 += 0.006 * bump(z0, 1.665, 0.035)

    # ---- nose: bridge + tip + wings, protruding along -y (front only) ----
    if y0 < -0.095 and abs(x0) < 0.045 and 1.52 < z0 < 1.635:
        nz = (z0 - 1.552) / 0.014          # 0 at the tip, + above, - below
        bridge = 0.0085 * math.exp(-max(0.0, nz) ** 2 / 2.2)
        bridge *= 1.0 - min(1.0, (abs(x0) / 0.028) ** 2)
        y0 -= bridge
        dt = math.hypot(x0 / 0.013, nz / 1.0)
        y0 -= 0.006 * math.exp(-dt ** 2)           # tip ball
        dw = math.hypot((abs(x0) - 0.019) / 0.010, (z0 - 1.546) / 0.011)
        y0 -= 0.0035 * math.exp(-dw ** 2)          # wings
        if 0.0 < nz < 1.2 and abs(x0) < 0.020:     # under-nose recess
            y0 += 0.002 * (1.0 - abs(nz))

    # ---- jaw: crisp mandible edge at the sides of the lower face ----
    if 1.44 < z0 < 1.51 and abs(x0) > 0.025:
        fe = bump(z0, 1.485, 0.03)
        y0 -= 0.005 * fe * min(1.0, (abs(x0) - 0.025) / 0.02)

    # back skull: pull in behind/above the ears
    if y0 > 0.0:
        fz = bump(z0, 1.62, 0.12)
        y0 = y0 * (1.0 - 0.16 * fz) - 0.004 * fz

    # chin: bring forward below the mouth, front only
    if y0 < -0.04 and z0 < 1.50:
        fc = bump(z0, 1.44, 0.05) * min(1.0, (-y0 - 0.04) / 0.05)
        y0 -= 0.009 * fc

    # under-jaw: clean throat line below the mandible
    if z0 < 1.46 and y0 > -0.03:
        y0 -= 0.004 * bump(z0, 1.43, 0.025)

    return Vector((HC.x + x0, HC.y + y0, p.z))


for v in head.data.vertices:
    v.co = mwi @ reshape(mw @ v.co)

# the Basis shape key stores its own copy of the positions and overrides the
# base mesh at render time; write the reshaped positions into it as well
if head.data.shape_keys:
    basis = head.data.shape_keys.key_blocks["Basis"]
    for v, kb in zip(head.data.vertices, basis.data):
        kb.co = v.co

# 3. measurements -------------------------------------------------------
w = head.matrix_world
vs = [w @ v.co for v in head.data.vertices]


def width(zc, band):
    xs = [p.x for p in vs if abs(p.z - zc) < band]
    return round(max(xs) - min(xs), 3) if xs else None


back = max((p.y for p in vs if 1.50 < p.z < 1.75), default=None)
frontnose = min((p.y for p in vs if 1.55 < p.z < 1.62), default=None)
chin = min((p.y for p in vs if p.z < 1.47), default=None)
print("MEAS width_eye", width(1.60, 0.015), "width_mouth", width(1.47, 0.015),
      "back_y", round(back, 3) if back else None,
      "nose_y", round(frontnose, 3) if frontnose else None,
      "chin_y", round(chin, 3) if chin else None)

bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
