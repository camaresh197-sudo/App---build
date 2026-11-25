import bpy, sys
bpy.ops.wm.open_mainfile(filepath='/home/claude/newhead/feat_v129.blend')
ob=max([o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('eye_')],key=lambda o:len(o.data.vertices))
V=[v.co for v in ob.data.vertices]
crown=max(v.z for v in V); chin=min(v.z for v in V)
W=2*max(abs(v.x) for v in V); D=max(v.y for v in V)-min(v.y for v in V)
print('crown %.4f chin %.4f H %.4f W %.4f D %.4f W/H %.2f D/H %.2f'%(crown,chin,crown-chin,W,D,W/(crown-chin),D/(crown-chin)))
# centreline front profile
import collections
prof=collections.OrderedDict()
for v in V:
    if abs(v.x)<0.0035 and v.y<0:
        k=round(v.z/0.004)*0.004
        prof[k]=min(prof.get(k,9),v.y)
for z in sorted(prof,reverse=True):
    if 1.40<=z<=1.60: print('%.3f %.4f'%(z,prof[z]))
# widths at levels
for z in (1.60,1.537,1.50,1.46,1.43):
    xs=[abs(v.x) for v in V if abs(v.z-z)<0.003]
    print('width@%.3f %.3f'%(z,2*max(xs)))
