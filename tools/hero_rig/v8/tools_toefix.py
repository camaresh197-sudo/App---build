import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/hero_v10_legs2.blend")
a=bpy.data.objects['character_rig']
def mv(name,d):
    o=bpy.data.objects[name];dl=o.matrix_world.inverted().to_3x3()@Vector(d)
    for v in o.data.vertices:v.co+=dl
    o.data.update()
mv('toe_l_0',(0,-0.004,-0.020));mv('toe_l_1',(0,-0.014,-0.033))
bpy.context.view_layer.objects.active=a
bpy.ops.object.mode_set(mode='EDIT')
t=a.data.edit_bones['toe_l'];t.tail=t.head+Vector((0,0,0.05))
bpy.ops.object.mode_set(mode='OBJECT')
for n in('toe_l_0','toe_l_1','toe_r_0','toe_r_1'):
    o=bpy.data.objects[n];ws=[o.matrix_world@v.co for v in o.data.vertices]
    print(n,"z",round(min(w.z for w in ws),3),round(max(w.z for w in ws),3),"y",round(min(w.y for w in ws),3),round(max(w.y for w in ws),3))
print([round(x,3) for x in a.data.bones['toe_l'].tail_local])
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/work/hero_v10_legs2.blend")
