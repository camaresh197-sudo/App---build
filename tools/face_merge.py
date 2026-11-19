"""Merge the face flesh into coherent meshes on the master .blend.

The face was dozens of separate primitives that intersect each other, so a
blendshape could only ever deform one of them. This fuses the head-bone skin
(head, nose, wings, ears, cheeks, puffs, folds, masseters) into ONE face mesh
bound to the head bone, and the jaw-bone flesh (jaw, chin, corners) into ONE
mesh bound to the jaw bone.

The shells are voxel-remeshed into a single continuous surface (clean topology
for blendshapes), then shrink-wrapped back onto the original shells so the
shapes - the nose, the ears - survive the merge instead of melting away.

    blender --background --factory-startup --python face_merge.py -- <in.blend> <out.blend>
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=SRC)

# Explicit groups: the head mesh, nose capsule and ears are all direct children of the head node (so they share the
# "head_" prefix), plus the cheek/puff/fold/masseter muscle blobs. The eye-socket liners (head_21/27), the nostrils
# and the dark cavity (head_118) are deliberately left out - they are dark detail that would fill the eye hollow.
HEAD = ["head_12", "head_15", "head_116", "head_117", "nose_tip_0", "nose_wing_l_0", "nose_wing_r_0",
        "cheek_l_0", "cheek_r_0", "puff_l_0", "puff_r_0", "fold_l_0", "fold_r_0", "mass_l_0", "mass_r_0"]
JAW = ["jaw_0", "chin_0", "corner_l_0", "corner_r_0", "tongue_0", "dimple_0"]


def pick(names):
    out = []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is not None and o.type == "MESH":
            out.append(o)
        else:
            print("MERGE: (missing) %s" % n)
    return out


def fuse(objs, name, bone, voxel, ratio, shrink=()):
    arm = [a for a in bpy.data.objects if a.type == "ARMATURE"][0]
    head = max(objs, key=lambda o: len(o.data.vertices))
    bone_group = head.vertex_groups[0].name if len(head.vertex_groups) else bone
    # the muscle blobs used to be alpha-soft; as solid geometry they would puff the face out, so scale them in
    for o in objs:
        if any(o.name.startswith(p) for p in shrink):
            o.scale = o.scale * 0.6
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = head
    if len(objs) > 1:
        bpy.ops.object.join()
    src = bpy.context.view_layer.objects.active
    if src.data.shape_keys is not None:        # a modifier cannot be applied over shape keys; re-authored after
        bpy.ops.object.shape_key_remove(all=True)
    # a clean, unified surface: remesh the shells into one, then shrink it back onto the shells so the shapes survive
    bpy.ops.object.duplicate()
    low = bpy.context.view_layer.objects.active
    for md in list(low.modifiers):
        low.modifiers.remove(md)
    m = low.modifiers.new("Remesh", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    bpy.ops.object.modifier_apply(modifier=m.name)
    d = low.modifiers.new("Decimate", "DECIMATE")
    d.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=d.name)
    s = low.modifiers.new("Shrink", "SHRINKWRAP")
    s.target = src
    s.wrap_method = "NEAREST_SURFACEPOINT"
    s.wrap_mode = "OUTSIDE_SURFACE"
    bpy.ops.object.modifier_apply(modifier=s.name)
    bpy.data.objects.remove(src, do_unlink=True)      # the shells were only a shape reference
    o = low
    o.name = name
    o.data.name = name
    am = o.modifiers.new("Armature", "ARMATURE")
    am.object = arm
    for g in list(o.vertex_groups):
        o.vertex_groups.remove(g)
    vg = o.vertex_groups.new(name=bone_group)
    vg.add([v.index for v in o.data.vertices], 1.0, "REPLACE")
    bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.sphere_project(direction="ALIGN_TO_OBJECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    print("MERGE: %s <- %d parts, bone %s, %d verts" % (name, len(objs), bone_group, len(o.data.vertices)))


h = pick(HEAD)
print("MERGE: head group = %s" % ", ".join(sorted(o.name for o in h)))
fuse(h, "head_12", "head", 0.0019, 0.32)

j = pick(JAW)
print("MERGE: jaw group = %s" % ", ".join(sorted(o.name for o in j)))
fuse(j, "jaw_0", "jaw", 0.0019, 0.38)

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("MERGE: saved", DST)
