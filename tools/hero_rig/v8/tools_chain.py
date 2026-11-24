import bpy
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v8_clav.blend")
a=bpy.data.objects['character_rig']
bones=a.data.bones
def p(b,d=0):
    print("  "*d+f"{b.name}  h={tuple(round(x,3) for x in b.head_local)} t={tuple(round(x,3) for x in b.tail_local)} len={b.length:.3f} conn={b.use_connect}")
    for c in b.children:p(c,d+1)
for r in [b for b in bones if not b.parent]:p(r)
print("bones",len(bones))
# vertex group usage per bone
use={b.name:0 for b in bones}
for o in bpy.data.objects:
    if o.type!='MESH':continue
    for g in o.vertex_groups:
        if g.name in use:use[g.name]+=1
print("UNWEIGHTED:",[k for k,v in use.items() if v==0])
# gaps: child head vs parent tail
for b in bones:
    if b.parent:
        d=(b.head_local-b.parent.tail_local).length
        if d>0.01:print("GAP",b.parent.name,"->",b.name,round(d,3))
