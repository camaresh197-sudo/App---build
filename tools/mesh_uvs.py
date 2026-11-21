"""Give the master's UV-less meshes a UV unwrap, so Godot's import stops failing
with 'UVs are required to generate tangents' (exit -1) on character_skinned.glb.

    blender --background --factory-startup --python mesh_uvs.py -- <in.blend> <out.blend>

Safe to re-run: meshes that already have a UV layer are skipped. Smart UV
Project on the shaded geometry - no material or vertex changes.
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=SRC)

bpy.context.view_layer.objects.active = None
fixed = []
for o in bpy.data.objects:
    if o.type != "MESH" or o.data.uv_layers:
        continue
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.01)   # 66 deg, ~1 px margin
    bpy.ops.object.mode_set(mode="OBJECT")
    fixed.append(o.name)
    print("UV: unwrapped", o.name)

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("UV: %d meshes unwrapped, saved %s" % (len(fixed), DST))
