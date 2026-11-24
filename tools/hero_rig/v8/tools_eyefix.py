import bpy,sys,mathutils as M
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sk=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
def ctr(n):
    o=bpy.data.objects[n]; vs=[o.matrix_world@v.co for v in o.data.vertices]
    return sum(vs,M.Vector())/len(vs)
cl,cr=ctr('white_l_1'),ctr('white_r_1')
mx=(cl.x+cr.x)/2; y=(cl.y+cr.y)/2; z=(cl.z+cr.z)/2
half=(cr.x-cl.x)/2
print('centre x',mx,'half gap',half,'y',y,'z',z)
bpy.context.view_layer.objects.active=sk
bpy.ops.object.mode_set(mode='EDIT')
eb=sk.data.edit_bones
h=eb['head']
print('head children',[(c.name,c.use_connect) for c in h.children])
for c in h.children: c.use_connect=False
old=(h.head.copy(),h.tail.copy())
h.head=M.Vector((mx,h.head.y,h.head.z)); h.tail=M.Vector((mx,h.head.y,h.head.z+0.08))
print('head',old,'->',h.head,h.tail)
for s,sx in (('l',-1),('r',1)):
    p=M.Vector((mx+sx*half,y,z))
    for n in ('white','iris','pupil','lidu','lidl'):
        b=eb[f'{n}_{s}']; b.use_connect=False
        b.head=p; b.tail=p+M.Vector((0,0,0.05)); b.roll=0
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=a[1])
