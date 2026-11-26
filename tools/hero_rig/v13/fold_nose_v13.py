# folded faces in the nose region (python3 -I fold_nose_v13.py -- file.blend): normal against the average of neighbours
import bpy, bmesh, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
bm=bmesh.new(); bm.from_mesh(bpy.data.objects['head_low'].data); bm.faces.ensure_lookup_table()
bad=0; n=0
for f in bm.faces:
    c=f.calc_center_median()
    if c.y<-0.07 and abs(c.x)<0.03 and 1.46<c.z<1.56:
        n+=1
        nb=[g for e in f.edges for g in e.link_faces if g is not f]
        avg=sum((g.normal for g in nb),type(f.normal)())
        if avg.length>0 and f.normal.dot(avg.normalized())<-0.2: bad+=1
print("nose faces",n,"folded",bad)
