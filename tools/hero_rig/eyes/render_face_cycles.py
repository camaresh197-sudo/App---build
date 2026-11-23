import bpy, math, sys
src=sys.argv[sys.argv.index('--')+1]; out=sys.argv[sys.argv.index('--')+2]
bpy.ops.wm.open_mainfile(filepath=src)
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=48; sc.cycles.use_denoising=False
sc.render.resolution_x=900; sc.render.resolution_y=900
w=bpy.data.worlds.new("W"); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.9,0.9,0.9,1); w.node_tree.nodes['Background'].inputs[1].default_value=1.2
sc.world=w
for o in bpy.data.objects:
    if o.type=='MESH' and o.data.shape_keys:
        for k in o.data.shape_keys.key_blocks[1:]: k.value=0.0
# hide hat so the eyes are visible
for o in bpy.data.objects:
    if o.name.startswith('hat'): o.hide_render=True
h=bpy.data.objects['head_12']
ws=[h.matrix_world@v.co for v in h.data.vertices]
cx=sum(p.x for p in ws)/len(ws); cz=sum(p.z for p in ws)/len(ws)
cam=bpy.data.cameras.new("C"); cam.lens=85
co=bpy.data.objects.new("C",cam); sc.collection.objects.link(co); sc.camera=co
co.rotation_euler=(math.radians(90),0,0); co.location=(cx,-1.5,cz+0.01)
sc.render.filepath=out; bpy.ops.render.render(write_still=True); print("CDONE")
