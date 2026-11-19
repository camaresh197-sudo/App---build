"""Export the rigged .blend back out as a skinned glTF (.glb).

    blender --background --factory-startup --python blend_to_glb.py -- <in.blend> <out.glb>
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=SRC)

# select everything (armature + meshes) and export the whole scene
for o in bpy.data.objects:
    o.select_set(True)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
bpy.context.view_layer.objects.active = arm

bpy.ops.export_scene.gltf(
    filepath=DST,
    export_format="GLB",
    use_selection=False,
    export_apply=False,
    export_skins=True,
    export_yup=True,
    export_animations=False,
)
print("GLB: wrote", DST)
