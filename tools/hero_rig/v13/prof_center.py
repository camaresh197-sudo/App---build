# centre-line profile: forward-most y (mm, negative = forward) per height, x within 2 mm of the middle
import bpy,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
o=bpy.data.objects['head_quad']
pts=[v.co for v in o.data.vertices if abs(v.co.x)<0.002]
z=1.60
print("z      front_y(mm)")
while z>=1.40:
    ys=[p.y for p in pts if abs(p.z-z)<0.0025]
    if ys: print(f"{z:.3f} {min(ys)*1000:7.1f}")
    z-=0.01
