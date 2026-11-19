"""Turn the exported character.glb (a node/empty hierarchy) into a real Blender
Armature with rigidly-skinned meshes, and save it as a .blend for authoring.

Each glTF node that carries a mesh becomes a bone (its rest pose is the node's
world transform); every mesh is bound weight-1 to its parent node's bone, so the
result poses exactly like the glTF file but is a normal armature you can select,
pose and animate in Blender.

    blender --background --factory-startup --python rig_to_armature.py -- <in.glb> <out.blend>
"""
import sys
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
bpy.ops.object.mode_set(mode="OBJECT")
print("RIG: %d bones" % len(arm_data.bones))

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

# the node hierarchy has become the armature; drop the empties so the file is clean
for e in empties:
    bpy.data.objects.remove(e, do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("RIG: saved", DST)
