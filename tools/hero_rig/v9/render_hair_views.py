import bpy, sys, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
tag = sys.argv[sys.argv.index("--")+2]; outdir = sys.argv[sys.argv.index("--")+3]
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.name.startswith("hat"): o.hide_render = True
sc.render.engine='BLENDER_WORKBENCH'; sc.render.resolution_x=700; sc.render.resolution_y=700
center = Vector((0.10,-0.07,1.56))
light=bpy.data.lights.new("s",'SUN'); light.energy=3; lo=bpy.data.objects.new("s",light); sc.collection.objects.link(lo); lo.rotation_euler=(0.6,0.2,0.6)
views = {"front": Vector((0,-0.75,0)), "left": Vector((-0.75,0,0)), "back": Vector((0,0.75,0))}
for name, off in views.items():
    cam=bpy.data.cameras.new("c"+name); cam.lens=85
    co=bpy.data.objects.new("c"+name,cam); sc.collection.objects.link(co)
    co.location=center+off
    d=center-co.location; co.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.camera=co; sc.render.filepath=f"{outdir}/hair_{tag}_{name}.png"
    bpy.ops.render.render(write_still=True); print("SAVED", name)
