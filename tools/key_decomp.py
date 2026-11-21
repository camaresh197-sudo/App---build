"""Diagnose: compute face_shapes.py's displacement fields (stale frame) on the current
basis verts and check the residual current_key_delta - script_delta. If the residual
concentrates in the mouth/chin and the crown deltas cancel, subtraction is the repair.

    blender --background --factory-startup --python key_decomp.py -- <in.blend>
"""
import sys
import collections
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])


def fall(p, c, r):
    w = 1.0 - (p - c).length / r
    if w <= 0.0:
        return 0.0
    return w * w * (3.0 - 2.0 * w)


def smile_disp(p):
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        cheek = Vector((0.048 * s, -0.028, 0.056))
        d += Vector((0.041 * s, 0.026, 0.023)) * fall(p, cheek, 0.068)
        corner = Vector((0.034 * s, -0.068, 0.084))
        d += Vector((0.014 * s, 0.019, 0.004)) * fall(p, corner, 0.038)
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):
            c = Vector((0.017 * s, -0.030, 0.096)).lerp(Vector((0.035 * s, -0.066, 0.084)), t)
            d -= Vector((0.009 * s, 0.0, 0.009)) * fall(p, c, 0.021)
    return d


def squint_disp(p):
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        corner = Vector((0.066 * s, 0.022, 0.062))
        d += Vector((-0.014 * s, 0.0, -0.006)) * fall(p, corner, 0.044)
        lid = Vector((0.040 * s, 0.006, 0.088))
        d += Vector((0.0, 0.013, 0.007)) * fall(p, lid, 0.034)
    return d


def frown_disp(p):
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        corner = Vector((0.034 * s, -0.066, 0.084))
        d += Vector((0.005 * s, -0.016, -0.003)) * fall(p, corner, 0.038)
    d += Vector((0.0, 0.007, -0.005)) * fall(p, Vector((0.0, 0.050, 0.094)), 0.030)
    return d


def brow_disp(p):
    d = Vector((0.0, 0.0, 0.0))
    for s in (-1.0, 1.0):
        d += Vector((0.0, 0.015, 0.004)) * fall(p, Vector((0.043 * s, 0.062, 0.081)), 0.038)
    d += Vector((0.0, 0.009, 0.003)) * fall(p, Vector((0.0, 0.050, 0.094)), 0.032)
    return d


def snarl_disp(p):
    d = Vector((0.0, 0.0, 0.0))
    for yy in (0.018, 0.028, 0.038):
        d -= Vector((0.0, 0.0, 0.006)) * fall(p, Vector((0.0, yy, 0.100)), 0.017)
    for s in (-1.0, 1.0):
        d += Vector((0.006 * s, 0.0, 0.003)) * fall(p, Vector((0.015 * s, -0.022, 0.100)), 0.022)
    return d


def pucker_disp(p):
    d = Vector((0.0, 0.0, 0.0))
    d += Vector((0.0, 0.001, 0.011)) * fall(p, Vector((0.0, -0.064, 0.088)), 0.040)
    for s in (-1.0, 1.0):
        cheek = Vector((0.050 * s, -0.030, 0.056))
        d += Vector((-0.007 * s, 0.0, -0.002)) * fall(p, cheek, 0.052)
    return d


DISP = {"smile": smile_disp, "squint": squint_disp, "frown": frown_disp,
        "pucker": pucker_disp, "brow": brow_disp, "snarl": snarl_disp}

me = bpy.data.objects["head_12"].data
ks = me.shape_keys.key_blocks
for name, fn in DISP.items():
    kb = ks[name]
    res = []          # residual after subtracting the stale-frame script deltas
    corr = []         # how much the script deltas explain of the current deltas
    for i, v in enumerate(me.vertices):
        cur = kb.data[i].co - v.co
        sd = fn(v.co)
        r = cur - sd
        if cur.length > 0.002:
            res.append((v.co.y, v.co.z, r.length, cur.length))
            corr.append(1.0 - min(1.0, r.length / cur.length))
    n_res_big = sum(1 for _, _, rl, _ in res if rl > 0.004)
    print("KEY %-7s verts %4d  explained %.0f%%  residual>4mm: %d" % (
        name, len(res), 100.0 * sum(corr) / max(1, len(corr)), n_res_big))
    # where does the residual live?
    top = sorted(res, key=lambda t: -t[2])[:8]
    print("   top residuals (y, z, |res|, |cur|):", [(round(y, 3), round(z, 3), round(r, 3), round(c, 3)) for y, z, r, c in top])
    import statistics
    if res:
        zs = [z for _, z, _, _ in res]; ys = [y for y, _, _, _ in res]
        print("   residual y %.3f..%.3f  z %.3f..%.3f" % (min(ys), max(ys), min(zs), max(zs)))
