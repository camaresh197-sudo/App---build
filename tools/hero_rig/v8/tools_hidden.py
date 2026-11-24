import bpy
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v14_baked.blend")
vl=bpy.context.view_layer
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH':continue
    h=(o.hide_viewport,o.hide_render,o.hide_get())
    if any(h):
        ws=[o.matrix_world@v.co for v in o.data.vertices]
        c=[round(sum(w[i] for w in ws)/len(ws),2) for i in range(3)]
        rows.append((o.name,h,len(o.data.polygons),c))
print(len(rows),"hidden meshes, faces",sum(r[2] for r in rows))
for r in rows:print(r)
