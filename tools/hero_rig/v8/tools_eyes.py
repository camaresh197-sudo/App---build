import bpy,sys,mathutils
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
sk=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
for o in bpy.data.objects:
    n=o.name.lower()
    if o.type=='MESH' and any(k in n for k in ('eye','iris','pupil','lid','white','lash','sclera','head','socket','brow')):
        vs=[o.matrix_world@v.co for v in o.data.vertices]
        if not vs: continue
        c=sum(vs,mathutils.Vector())/len(vs)
        mn=[min(v[i] for v in vs) for i in range(3)];mx=[max(v[i] for v in vs) for i in range(3)]
        vg=max(o.vertex_groups,key=lambda g:sum(1 for v in o.data.vertices for x in v.groups if x.group==g.index),default=None)
        print(f"{o.name:22s} c=({c.x:.3f},{c.y:.3f},{c.z:.3f}) size=({mx[0]-mn[0]:.3f},{mx[1]-mn[1]:.3f},{mx[2]-mn[2]:.3f}) n={len(vs)} g={vg.name if vg else None} vis={not o.hide_viewport}")
for b in sk.pose.bones:
    if any(k in b.name for k in ('eye','head','iris','pupil','lid','white')):
        h=sk.matrix_world@b.head;t=sk.matrix_world@b.tail
        print('BONE',b.name,tuple(round(x,3) for x in h),tuple(round(x,3) for x in t))
