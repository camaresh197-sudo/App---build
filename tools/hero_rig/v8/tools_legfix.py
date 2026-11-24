import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v8_clav.blend")
a=bpy.data.objects['character_rig']
D=Vector((0,0.036,0.03))
names=[f'{n}_r' for n in('hip','thigh','knee','shin','ankle','foot','toe')]
def dom(o):
    cnt={}
    for v in o.data.vertices:
        if v.groups:
            g=max(v.groups,key=lambda x:x.weight).group
            n=o.vertex_groups[g].name;cnt[n]=cnt.get(n,0)+1
    return max(cnt,key=cnt.get) if cnt else None
moved=[];hoop=[]
for o in list(bpy.data.objects):
    if o.type!='MESH':continue
    d=dom(o)
    if 'hoop' in o.name.lower() or d=='hoop': hoop.append(o.name);continue
    if d in names:
        assert not o.data.shape_keys,o.name
        dl=o.matrix_world.inverted().to_3x3()@D
        for v in o.data.vertices:v.co+=dl
        o.data.update();moved.append(o.name)
for n in hoop:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
bpy.context.view_layer.objects.active=a
bpy.ops.object.mode_set(mode='EDIT')
eb=a.data.edit_bones
for n in names:eb[n].head+=D;eb[n].tail+=D
if 'hoop' in eb:eb.remove(eb['hoop'])
bpy.ops.object.mode_set(mode='OBJECT')
print("moved",moved);print("hoop meshes removed",hoop,"bones",len(a.data.bones))
for n in('hip','thigh','knee','shin','ankle'):
    l=a.data.bones[n+'_l'];r=a.data.bones[n+'_r']
    print(n,"L",[round(x,3) for x in l.head_local],"R",[round(x,3) for x in r.head_local])
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/work/hero_v9_legs.blend")
