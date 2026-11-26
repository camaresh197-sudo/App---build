import sys, bpy, json
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
o=bpy.data.objects['head_quad']; M=o.matrix_world
prof={}
for v in o.data.vertices:
    p=M@v.co
    if abs(p.x)<0.0015 and p.y<-0.05 and 1.40<p.z<1.66:
        b=round(p.z*1000/2)*2
        if b not in prof or p.y<prof[b]: prof[b]=p.y
json.dump({str(k):v*1000 for k,v in prof.items()}, open('/tmp/claude-0/-home-user-App---build/06e83864-e0ef-54c3-9ec4-508030560da5/scratchpad/hero/prof_ours.json','w')); print('PROF',len(prof))
