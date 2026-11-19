"""Turn the exported character.glb (a node/empty hierarchy) into a real Blender
Armature with rigidly-skinned meshes, and save it as a .blend for authoring.

Each glTF node that carries a mesh becomes a bone (its rest pose is the node's
world transform); every mesh is bound weight-1 to its parent node's bone, so the
result poses exactly like the glTF file but is a normal armature you can select,
pose and animate in Blender.

    blender --background --factory-startup --python rig_to_armature.py -- <in.glb> <out.blend>
"""
import sys
import os
import json
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0]
DST = argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

empties = [o for o in bpy.data.objects if o.type == "EMPTY"]
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print("RIG: %d empties, %d meshes" % (len(empties), len(meshes)))

arm_data = bpy.data.armatures.new("character_rig")
arm = bpy.data.objects.new("character_rig", arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)

bone_of = {}


def make_bone(empty, parent_bone):
    eb = arm_data.edit_bones.new(empty.name[:60])
    eb.head = empty.matrix_world.translation
    tail = None
    for c in empty.children:
        if c.type == "EMPTY":
            tail = c.matrix_world.translation
            break
    if tail is None or (tail - eb.head).length < 1e-4:
        tail = eb.head + Vector((0.0, 0.0, 0.05))
    eb.tail = tail
    eb.roll = 0.0
    if parent_bone is not None:
        eb.parent = parent_bone
    bone_of[empty.name] = eb.name
    for c in empty.children:
        if c.type == "EMPTY":
            make_bone(c, eb)


bpy.ops.object.mode_set(mode="EDIT")
for root in [o for o in empties if o.parent is None or o.parent.type != "EMPTY"]:
    make_bone(root, None)

# The lip and mustache bead rows are hidden helpers, so the glb prunes them - but they are the rig the mouth tubes
# deform against. Recreate them from the reference rig the export wrote (Godot Y-up -> Blender Z-up).
ref_path = os.path.join(os.path.dirname(SRC), "character_rig.json")
beads = 0
if os.path.exists(ref_path):
    with open(ref_path) as fh:
        ref = json.load(fh)
    for name, a in ref.items():
        if name in bone_of:
            continue
        if name.startswith("lipU_") or name.startswith("must_"):
            parent = "head"
        elif name.startswith("lipL_"):
            parent = "jaw"
        else:
            continue
        if parent not in arm_data.edit_bones:
            continue
        eb = arm_data.edit_bones.new(name[:60])
        eb.head = Vector((a[9], -a[11], a[10]))
        eb.tail = eb.head + Vector((0.0, 0.0, 0.01))
        eb.roll = 0.0
        eb.parent = arm_data.edit_bones[parent]
        bone_of[name] = eb.name
        beads += 1
bpy.ops.object.mode_set(mode="OBJECT")
print("RIG: %d bones (%d mouth beads)" % (len(arm_data.bones), beads))

# bind each mesh rigidly to its parent node's bone
bound = 0
skipped = 0
for m in meshes:
    pe = m.parent
    bn = bone_of.get(pe.name) if pe is not None else None
    if bn is None:
        skipped += 1
        continue
    vg = m.vertex_groups.new(name=bn)
    vg.add([v.index for v in m.data.vertices], 1.0, "REPLACE")
    mw = m.matrix_world.copy()
    m.parent = arm
    m.matrix_parent_inverse = arm.matrix_world.inverted()
    m.matrix_world = mw
    mod = m.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    bound += 1
print("RIG: bound %d meshes, skipped %d" % (bound, skipped))

# Re-weight the mouth tubes: the code rebuilds them every frame from the bead rows, so in the file they belong to the
# bead bones instead. _tube writes ring by ring, so vertex i of a tube is ring i // ring_size - that ring was built
# from bead (i // ring_size), which is exactly the bone that should carry it.
TUBES = [("lipUm", 8, "lipU_", 0), ("lipLm", 8, "lipL_", 0), ("mustm_l", 10, "must_l_", 1), ("mustm_r", 10, "must_r_", 1)]
rew = 0
for nm, ring, prefix, off in TUBES:
    o = bpy.data.objects.get(nm)
    if o is None:
        continue
    for g in list(o.vertex_groups):
        o.vertex_groups.remove(g)
    groups = {}
    for i in range(len(o.data.vertices)):
        bn = prefix + str(max(0, i // ring - off))
        if bn not in groups:
            groups[bn] = o.vertex_groups.new(name=bn)
        groups[bn].add([i], 1.0, "REPLACE")
    rew += 1
print("RIG: re-weighted %d mouth tubes" % rew)

# the node hierarchy has become the armature; drop the empties so the file is clean
for e in empties:
    bpy.data.objects.remove(e, do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("RIG: saved", DST)
