import bpy,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE']
print("armatures",[a.name for a in arm])
a=arm[0]
for b in a.data.bones:
    if any(k in b.name for k in('clav','chest','shoulder','uarm','spine')):
        print(b.name,b.parent.name if b.parent else None,tuple(round(x,3) for x in b.head_local),tuple(round(x,3) for x in b.tail_local))
vg=set()
for o in bpy.data.objects:
    if o.type=='MESH':
        for g in o.vertex_groups:
            if 'clav' in g.name: print("clav group on",o.name,g.name)
old=[(o.name,len(o.data.polygons),o.hide_viewport,o.hide_get() if hasattr(o,'hide_get') else None) for o in bpy.data.objects if o.type=='MESH' and 'OLD' in o.name]
print("OLD",old)
print("meshes",sum(1 for o in bpy.data.objects if o.type=='MESH'),"faces",sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'))
