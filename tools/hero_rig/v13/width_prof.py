import bpy,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
o=[x for x in bpy.data.objects if x.type=='MESH' and x.name.startswith('head')][0]
vs=[v.co for v in o.data.vertices]
print("z   maxhalfwidth(mm)  diff")
prev=None
z=1.52
while z>=1.385:
    w=[abs(p.x) for p in vs if abs(p.z-z)<0.0035]
    if w:
        m=max(w)*1000
        print(f"{z:.3f} {m:6.1f} {'' if prev is None else f'{m-prev:+.1f}'}")
        prev=m
    z-=0.01
