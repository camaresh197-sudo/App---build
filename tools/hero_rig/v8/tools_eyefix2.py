import bpy,sys,bmesh,mathutils as M
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sk=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
o=bpy.data.objects['head_12']
print('det',o.matrix_world.determinant())
bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm,faces=bm.faces[:]); bm.to_mesh(o.data); bm.free(); o.data.update()
c=M.Vector((0.085,-0.01,1.58)); out=sum(1 for p in o.data.polygons if (o.matrix_world.to_3x3()@p.normal).dot(o.matrix_world@p.center-c)>0)
print('head_12 outward now',out,'of',len(o.data.polygons))
# catchlights: mesh centre -> ball centre (the code moves the joint onto the cornea every frame)
def ctr(n):
    ob=bpy.data.objects[n]; vs=[ob.matrix_world@v.co for v in ob.data.vertices]; return sum(vs,M.Vector())/len(vs)
ball={'l':ctr('white_l_1'),'r':ctr('white_r_1')}
for s in 'lr':
    for n in ('shine','shine2'):
        ob=bpy.data.objects[f'{n}_{s}_0']
        d=ball[s]-ctr(f'{n}_{s}_0')
        for v in ob.data.vertices: v.co+= ob.matrix_world.inverted().to_3x3()@d
        ob.data.update()
bpy.context.view_layer.objects.active=sk
bpy.ops.object.mode_set(mode='EDIT')
for s in 'lr':
    for n in ('shine','shine2'):
        b=sk.data.edit_bones[f'{n}_{s}']; b.use_connect=False; b.head=ball[s]; b.tail=ball[s]+M.Vector((0,0,0.05)); b.roll=0
bpy.ops.object.mode_set(mode='OBJECT')
for s in 'lr':
    for n in ('shine','shine2'): print(n,s,tuple(round(x,3) for x in ctr(f'{n}_{s}_0')))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
