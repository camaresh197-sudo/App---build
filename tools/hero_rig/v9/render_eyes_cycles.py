import bpy, sys, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
tag = sys.argv[sys.argv.index("--")+2]; outdir = sys.argv[sys.argv.index("--")+3]
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.name.startswith("hat") or o.name.startswith("hair"): o.hide_render = True
for o in list(bpy.data.objects):
    if o.type == 'LIGHT': o.hide_render = True        # the file carries 14 old lights; render with mine only
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.resolution_x = 900; sc.render.resolution_y = 520
sc.render.image_settings.file_format = 'PNG'
eyes = Vector((0.085, -0.08, 1.587))
# key light and fill so the eyes read
for name, loc, e in [("key", (0.25,-0.9,1.9), 60), ("fill", (-0.2,-0.8,1.5), 15)]:
    L = bpy.data.lights.new(name, 'AREA'); L.energy = e; L.size = 0.4
    lo = bpy.data.objects.new(name, L); sc.collection.objects.link(lo); lo.location = loc
    lo.rotation_euler = (eyes - Vector(loc)).to_track_quat('-Z','Y').to_euler()
cam = bpy.data.cameras.new("c"); cam.lens = 85
co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co)
co.location = eyes + Vector((0.0, -0.55, 0.075))
co.rotation_euler = (eyes + Vector((0,0,0.04)) - co.location).to_track_quat('-Z','Y').to_euler()
sc.camera = co
sc.render.filepath = f"{outdir}/eyes_cycles_{tag}.png"
bpy.ops.render.render(write_still=True); print("SAVED", sc.render.filepath)
