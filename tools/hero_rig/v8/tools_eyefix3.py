import bpy,sys,json,mathutils as M
a=sys.argv[sys.argv.index('--')+1:]
rj=json.load(open(a[2]))
bpy.ops.wm.open_mainfile(filepath=a[0])
sk=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
def ctr(ob): vs=[ob.matrix_world@v.co for v in ob.data.vertices]; return sum(vs,M.Vector())/len(vs)
tg={}
for s in 'lr':
    for n in ('shine','shine2'):
        x,y,z=rj[f'{n}_{s}'][9:12]; tg[f'{n}_{s}']=M.Vector((x,-z,y))
        ob=bpy.data.objects[f'{n}_{s}_0']; d=tg[f'{n}_{s}']-ctr(ob)
        for v in ob.data.vertices: v.co+=ob.matrix_world.inverted().to_3x3()@d
        ob.data.update()
bpy.context.view_layer.objects.active=sk
bpy.ops.object.mode_set(mode='EDIT')
for k,p in tg.items():
    b=sk.data.edit_bones[k]; b.use_connect=False; b.head=p; b.tail=p+M.Vector((0,0,0.05)); b.roll=0
bpy.ops.object.mode_set(mode='OBJECT')
for k,p in tg.items(): print(k,tuple(round(x,4) for x in p))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
