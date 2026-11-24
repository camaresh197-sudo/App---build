import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v8_clav.blend")
a=bpy.data.objects['character_rig']
want=['hip_','thigh_','knee_','shin_','ankle_','foot_','toe_']
def dom(o):
    # dominant group per mesh by vertex count
    cnt={}
    for v in o.data.vertices:
        if v.groups:
            g=max(v.groups,key=lambda x:x.weight).group
            n=o.vertex_groups[g].name;cnt[n]=cnt.get(n,0)+1
    return max(cnt,key=cnt.get) if cnt else None
rows={}
for o in bpy.data.objects:
    if o.type!='MESH':continue
    d=dom(o)
    if d and any(d.startswith(w) for w in want) and d[-1] in 'lr':
        ws=[o.matrix_world@v.co for v in o.data.vertices]
        mn=[min(w[i] for w in ws) for i in range(3)];mx=[max(w[i] for w in ws) for i in range(3)]
        rows.setdefault(d,[]).append((o.name,[round(x,3) for x in mn],[round(x,3) for x in mx],len(o.data.polygons)))
for k in sorted(rows):
    for r in rows[k]:print(k,r)
