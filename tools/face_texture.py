"""Paint the face: bake a real albedo for head_12 from the master.

The face used to be a 256 tile of skin noise with every feature done in geometry.
This pass gives it an authored skin map:

  - a clean Smart-UV unwrap of the head (the old UVs tile, so they cannot hold a face);
  - per-vertex shading from real ray-cast ambient occlusion, so the eye sockets,
    nostrils, lip line and the jaw shade themselves instead of reading flat;
  - painted features placed from the rig's own landmarks (the eye and brow bones,
    the lip polygons): socket shadow, brow shadow, cheek warmth, a lip rim, a
    forehead lift and a jaw fall-off;
  - smooth mottling.

The vertex colours are a MULTIPLIER, not a colour: the bake multiplies the head's
existing skin chain (tile x tint), so the face keeps exactly the body's tone and the
hands and neck never disagree with it.

Then bakes it to a 1024 albedo, puts it on a copy of the skin material (the body
keeps the tile) and packs the image into the blend. The gutters between UV islands
are inpainted with skin, so nothing samples black at a seam.

    blender --background --python tools/face_texture.py -- <in.blend> <out.blend> <png>

Run once: it rewrites the head's UVs and re-bakes. Back up the master first.
"""
import sys
import math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DST, PNG = argv[0], argv[1], argv[2]

bpy.ops.wm.open_mainfile(filepath=SRC)
head = bpy.data.objects["head_12"]
me = head.data
mw = head.matrix_world

# ------------------------------------------------------------------ 1. unwrap
bpy.ops.object.select_all(action="DESELECT")
head.select_set(True)
bpy.context.view_layer.objects.active = head
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.004)
bpy.ops.object.mode_set(mode="OBJECT")
print("FACE: unwrapped %d polys, uv layers %s" % (len(me.polygons), [l.name for l in me.uv_layers]))

# ------------------------------------------------------------------ 2. landmarks
def world(o):
    return o.matrix_world.translation.copy()

eL, eR = world(bpy.data.objects["white_l_1"]), world(bpy.data.objects["white_r_1"])
bL, bR = world(bpy.data.objects["brow_l_0"]), world(bpy.data.objects["brow_r_0"])

lip_pts = []
for p in me.polygons:
    if head.material_slots[p.material_index].material.name == "lip_mouth":
        for vi in p.vertices:
            lip_pts.append(mw @ me.vertices[vi].co)
mouth = sum(lip_pts, Vector()) / max(1, len(lip_pts))
print("FACE: eyes %s %s  mouth %s" % (tuple(round(c, 3) for c in eL), tuple(round(c, 3) for c in eR), tuple(round(c, 3) for c in mouth)))

# nose tip: the forward-most vertex between the eyes and the mouth
cand = [mw @ v.co for v in me.vertices]
cand = [p for p in cand if mouth.z < p.z < eL.z + 0.02]
nose_tip = min(cand, key=lambda p: p.y) if cand else mouth + Vector((0, -0.05, 0.06))
print("FACE: nose tip %s" % (tuple(round(c, 3) for c in nose_tip),))

# ------------------------------------------------------------------ 3. ray-cast AO
depsgraph = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(head, depsgraph)

NRAYS = 16
DIRS = []
for i in range(NRAYS):
    z = (i + 0.5) / NRAYS
    r = math.sqrt(max(0.0, 1.0 - z * z))
    phi = i * 2.399963229728653
    DIRS.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))

M3 = mw.to_3x3()
AO_MAX = 0.050          # local units: close contact shading, not the whole face
EPS = 0.0012

def smoothstep(e0, e1, x):
    t = (x - e0) / (e1 - e0)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t * (3.0 - 2.0 * t)

def falloff(d, r_in, r_out):
    return 1.0 - smoothstep(r_in, r_out, d)

cols = []
ao_sum = 0.0
for i, v in enumerate(me.vertices):
    nrm = v.normal
    if nrm.length < 1e-6:
        cols.append((1.0, 1.0, 1.0))
        continue
    n = nrm.normalized()
    t = n.orthogonal().normalized()
    b = n.cross(t)
    org = v.co + n * EPS
    occ = 0
    for d in DIRS:
        dq = t * d.x + b * d.y + n * d.z
        if bvh.ray_cast(org, dq, AO_MAX)[0] is not None:
            occ += 1
    ao = occ / NRAYS
    ao_sum += ao

    p = mw @ v.co
    nw = (M3 @ n).normalized()
    front = smoothstep(0.25, -0.15, nw.y)          # 1 on the face, 0 round the back

    shade = 1.0 - 0.30 * ao                        # cavity shading, mild

    sock = 0.0
    for e in (eL, eR):
        sock = max(sock, falloff((p - e).length, 0.026, 0.062))
    shade *= 1.0 - 0.30 * sock * front

    browsh = 0.0
    for bpt in (bL, bR):
        browsh = max(browsh, falloff((p - (bpt + Vector((0, 0, 0.012)))).length, 0.014, 0.050))
    shade *= 1.0 - 0.22 * browsh * front

    lipr = falloff((p - mouth).length, 0.030, 0.062)
    shade *= 1.0 - 0.16 * lipr * front

    jaw = smoothstep(mouth.z - 0.045, mouth.z - 0.105, p.z)
    shade *= 1.0 - 0.10 * jaw

    fore = smoothstep(mouth.z + 0.10, mouth.z + 0.20, p.z) * front
    shade *= 1.0 + 0.08 * fore

    # nose bridge: a lifted vertical plane between the eyes, and the ball catches the key light
    midx = (eL.x + eR.x) * 0.5
    bridge = falloff(abs(p.x - midx), 0.006, 0.024)
    bridge *= smoothstep(mouth.z + 0.03, mouth.z + 0.07, p.z) * smoothstep(eL.z + 0.06, eL.z, p.z) * front
    shade *= 1.0 + 0.07 * bridge

    r = shade
    g = shade
    bl = shade

    # cheeks: a little warmth (red up, blue down) - a multiplier, so it survives the tint
    cheek = 0.0
    for e in (eL, eR):
        c = e + Vector((0.030 if e.x > mouth.x else -0.030, -0.004, -0.052))
        cheek = max(cheek, falloff((p - c).length, 0.010, 0.048))
    cheek *= front
    r *= 1.0 + 0.16 * cheek
    g *= 1.0 + 0.04 * cheek
    bl *= 1.0 - 0.06 * cheek

    # nose ball: skin over cartilage is warmer and a touch lighter than the cheeks
    nosew = falloff((p - nose_tip).length, 0.012, 0.050) * front
    r *= 1.0 + 0.12 * nosew
    g *= 1.0 + 0.02 * nosew
    bl *= 1.0 - 0.02 * nosew

    mot = (0.55 * math.sin(p.x * 37.0 + p.z * 21.0) +
           0.30 * math.sin(p.y * 53.0 + p.x * 19.0 + 1.7) +
           0.15 * math.sin(p.z * 91.0 + p.y * 44.0 + 0.4))
    r *= 1.0 + 0.05 * mot
    g *= 1.0 + 0.05 * mot
    bl *= 1.0 + 0.05 * mot

    cols.append((min(1.0, r), min(1.0, g), min(1.0, bl)))
    if i % 5000 == 0:
        print("FACE: ao %d/%d" % (i, len(me.vertices)))

print("FACE: mean AO %.3f over %d verts" % (ao_sum / max(1, len(me.vertices)), len(me.vertices)))

# ------------------------------------------------------------------ 4. vertex colour layer
if "FaceCol" in me.color_attributes:
    me.color_attributes.remove(me.color_attributes["FaceCol"])
layer = me.color_attributes.new(name="FaceCol", type="FLOAT_COLOR", domain="POINT")
for i, c in enumerate(cols):
    layer.data[i].color = (c[0], c[1], c[2], 1.0)
print("FACE: vertex colours written")

# ------------------------------------------------------------------ 5. bake (tile x tint x FaceCol)
face_mat = bpy.data.materials["Material_0"].copy()
face_mat.name = "Face_Skin"
head.material_slots[0].material = face_mat

nt = face_mat.node_tree
principled = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
base_src = principled.inputs["Base Color"].links[0].from_socket

mul = nt.nodes.new("ShaderNodeMix")
mul.data_type = "RGBA"
mul.blend_type = "MULTIPLY"
mul.inputs["Factor"].default_value = 1.0
attr = nt.nodes.new("ShaderNodeAttribute")
attr.attribute_name = "FaceCol"
attr.attribute_type = "GEOMETRY"
nt.links.new(base_src, mul.inputs["A"])
nt.links.new(attr.outputs["Color"], mul.inputs["B"])
nt.links.new(mul.outputs["Result"], principled.inputs["Base Color"])

img = bpy.data.images.new("face_albedo", 1024, 1024, alpha=False)
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
nt.nodes.active = tex

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 1
sc.cycles.use_denoising = False
bake = sc.render.bake
bake.use_pass_direct = False
bake.use_pass_indirect = False
bake.use_pass_color = True
bake.margin = 8

bpy.ops.object.select_all(action="DESELECT")
head.select_set(True)
bpy.context.view_layer.objects.active = head
print("FACE: baking...")
bpy.ops.object.bake(type="DIFFUSE")
print("FACE: bake done")

# ------------------------------------------------------------------ 6. inpaint the gutters
# fill the gutters with the mean skin tone: flat is better than streaks at a seam
px = np.array(img.pixels[:], dtype=np.float32).reshape(1024, 1024, 4)
rgb = px[:, :, :3]
empty = rgb.sum(axis=2) < 1e-4
if empty.any():
    mean = rgb[~empty].mean(axis=0) if (~empty).any() else np.array([0.05, 0.02, 0.01], dtype=np.float32)
    rgb[empty] = mean
print("FACE: gutters filled flat, %d px" % int(empty.sum()))
px[:, :, :3] = np.clip(rgb, 0.0, 1.0)

# texel-level skin grain: the vertex grid is ~1.5 mm apart, too coarse for pores, so the
# fine variation has to come from the image. Multi-octave value noise, low amplitude.
def upsample(a, size):
    n = a.shape[0]
    ys = np.linspace(0.0, n - 1.0, size, dtype=np.float32)
    y0 = np.floor(ys).astype(np.int32)
    y1 = np.minimum(y0 + 1, n - 1)
    fy = (ys - y0)[:, None]
    tmp = a[y0] * (1.0 - fy) + a[y1] * fy
    x0 = np.floor(ys).astype(np.int32)
    x1 = np.minimum(x0 + 1, n - 1)
    fx = (ys - x0)[None, :]
    return tmp[:, x0] * (1.0 - fx) + tmp[:, x1] * fx

rng = np.random.default_rng(7)
grain = np.zeros((1024, 1024), dtype=np.float32)
weight = 0.0
for cell, wgt in ((6, 0.45), (12, 0.30), (24, 0.18), (48, 0.07)):
    grain += upsample(rng.random((cell, cell)).astype(np.float32), 1024) * wgt
    weight += wgt
grain /= weight
grain = 1.0 + (grain - 0.5) * 0.10          # +/- 5 %
rgb[:, :, 0] *= grain
rgb[:, :, 1] *= grain
rgb[:, :, 2] *= grain
px[:, :, :3] = np.clip(rgb, 0.0, 1.0)
# the bake is scene-linear, but an image holds display values: encode to sRGB so the
# texture reads as the same skin tone as the body (Godot decodes PNG albedo as sRGB)
lin = px[:, :, :3]
px[:, :, :3] = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1.0 / 2.4) - 0.055)
img.pixels = px.ravel()
print("FACE: grain applied, sRGB encoded")

# ------------------------------------------------------------------ 7. wire the bake into the material
for l in list(nt.links):
    if l.to_socket == principled.inputs["Base Color"]:
        nt.links.remove(l)
nt.links.new(tex.outputs["Color"], principled.inputs["Base Color"])
nt.nodes.remove(mul)
nt.nodes.remove(attr)
# the tile chain is no longer used: leave it, it documents where the tone came from

img.filepath_raw = PNG
img.file_format = "PNG"
img.save()
img.pack()
# the exporter writes a copy next to the glb whenever the image has a path; the glb embeds it anyway
img.filepath_raw = ""
img.filepath = ""
print("FACE: wrote", PNG)

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("FACE: saved", DST)
