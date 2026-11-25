# Adds a neck tube to feat_v13_chin.blend -> feat_v13_neck.blend (run: python3 -I build_v13_neck.py)
import bpy, bmesh, math
bpy.ops.wm.open_mainfile(filepath="feat_v13_chin.blend")
head=bpy.data.objects['head_quad']
# (z, rx half-width, ryb back depth, ryf front depth, yc centre offset); the neck leans back going down
NECK=[
(1.470,0.058,0.058,0.056,0.012),
(1.420,0.058,0.058,0.055,0.016),
(1.380,0.057,0.057,0.055,0.024),
(1.340,0.057,0.058,0.056,0.034),
(1.300,0.060,0.062,0.058,0.042),
(1.270,0.068,0.068,0.062,0.046),
]
NSEG=72
from scipy.interpolate import PchipInterpolator as P
import numpy as np
zs=np.array([r[0] for r in NECK])[::-1]
f=[P(zs,np.array([r[i] for r in NECK])[::-1]) for i in (1,2,3,4)]
bm=bmesh.new(); rows=[]
z=NECK[0][0]
while z>=NECK[-1][0]-1e-9:
    rx,rb,rf,yc=[float(g(z)) for g in f]
    row=[]
    for j in range(NSEG):
        t=2*math.pi*j/NSEG; s=math.sin(t); c=math.cos(t)
        row.append(bm.verts.new((rx*c,(rb*s if s>=0 else rf*s)+yc,z)))
    rows.append(row); z-=0.01
for i in range(len(rows)-1):
    for j in range(NSEG):
        k=(j+1)%NSEG
        bm.faces.new((rows[i][j],rows[i][k],rows[i+1][k],rows[i+1][j]))
zb=rows and NECK[-1][0]
cap=bm.verts.new((0,float(f[3](NECK[-1][0])),NECK[-1][0]-0.004))
for j in range(NSEG):
    bm.faces.new((cap,rows[-1][j],rows[-1][(j+1)%NSEG]))
bm.normal_update()
me=bpy.data.meshes.new('neck_mesh'); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth=True
neck=bpy.data.objects.new('neck',me); bpy.context.scene.collection.objects.link(neck)
neck.data.materials.append(head.data.materials[0])
bpy.ops.wm.save_as_mainfile(filepath="feat_v13_neck.blend")
print("saved neck", len(me.vertices))
