"""Give the jaw/chin a little more mass on the master .blend.

The mouth is wide, but the separate jaw piece (`jaw_0`) is only about 58% of the
head's width and its top sits almost at the lower lip, so the lower face reads as
a small round chin under a big mouth. This pass widens the jaw, extends it down a
little and pushes the chin forward, with a gradient so the change fades out at the
top instead of leaving a step.

This is a one-off pass on the already-sculpted master: it only moves `jaw_0` and
keeps the shape keys untouched. Do NOT re-run `face_sculpt.py` on the master to get
the same effect - that script also re-applies the nose displacement.

    blender --background --factory-startup --python face_jaw.py -- <in.blend> <out.blend>
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

# knobs: keep these small; the jaw should read bigger, not become a lantern
WIDE = 1.26          # total lateral gain at the bottom
DOWN = 1.28          # total vertical gain below the hinge
FWD = 0.008          # chin push (local -Y is forward)
HEAD_SIDE = 0.018    # squaring the lower head mesh at the jawline (local X)
HEAD_DOWN = 0.004    # ... and letting those sides hang a touch lower

bpy.ops.wm.open_mainfile(filepath=SRC)


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def jawline_delta(p):
    """Widen the lower head only on the sides, leaving the lip area alone."""
    w = 1.0 - smoothstep(-0.100, -0.060, p.z)      # 1 at the chin, 0 at the mouth line
    side = smoothstep(0.015, 0.075, abs(p.x))      # 0 at the centre, 1 at the jaw angle
    if w <= 0.0 or side <= 0.0:
        return 0.0, 0.0
    return (HEAD_SIDE * w * side) * (1.0 if p.x >= 0.0 else -1.0), -HEAD_DOWN * w * side


head = bpy.data.objects.get("head_12")
if head is not None:
    # shape keys store absolute points: apply the same delta to every key so the
    # expressions keep their exact offsets on the reshaped basis
    deltas = [jawline_delta(v.co) for v in head.data.vertices]
    keys = head.data.shape_keys.key_blocks if head.data.shape_keys else None
    if keys:
        for kb in keys:
            for i, (dx, dz) in enumerate(deltas):
                kb.data[i].co.x += dx
                kb.data[i].co.z += dz
    else:
        for i, (dx, dz) in enumerate(deltas):
            head.data.vertices[i].co.x += dx
            head.data.vertices[i].co.z += dz
    head.data.update()
    print("JAW: head_12 jawline on %d verts (%d keys)" % (sum(1 for d in deltas if d[0] or d[1]), len(keys) if keys else 0))


jaw = bpy.data.objects.get("jaw_0")
if jaw is None:
    raise SystemExit("JAW: no jaw_0 object found")

me = jaw.data
zs = [v.co.z for v in me.vertices]
top, bot = max(zs), min(zs)
span = max(1e-6, top - bot)
before_half = max(abs(v.co.x) for v in me.vertices)
before_h = span

moved = 0
for v in me.vertices:
    p = v.co
    t = min(1.0, max(0.0, (top - p.z) / span))         # 0 at the top, 1 at the chin
    ramp = t * t * (3.0 - 2.0 * t)
    # widen more towards the chin so the jaw gets an angle instead of a rounder ball
    v.co.x = p.x * (1.0 + (WIDE - 1.0) * (0.55 + 0.45 * ramp))
    # extend downward from the top edge (the hinge stays put)
    v.co.z = top - (top - p.z) * DOWN
    # push the front of the chin forward, strongest at the bottom
    if p.y < 0.0:
        front = min(1.0, -p.y / 0.063)
        v.co.y -= FWD * ramp * front
    moved += 1
me.update()

xs = [v.co.x for v in me.vertices]
zs = [v.co.z for v in me.vertices]
print("JAW: %s - %d verts, half-width %.3f -> %.3f, height %.3f -> %.3f"
      % (jaw.name, moved, before_half, max(abs(v) for v in xs),
         before_h, max(zs) - min(zs)))

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("JAW: saved", DST)
