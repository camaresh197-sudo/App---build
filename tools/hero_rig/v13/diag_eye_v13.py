# counts bad faces in the eye patch: flipped, tiny, slivers  (python3 -I diag_eye_v13.py -- file.blend)
import bpy, bmesh, math, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
lo=bpy.data.objects['head_low']; eye=bpy.data.objects['eye_l']; vs=[v.co for v in eye.data.vertices]
cx=sum(v.x for v in vs)/len(vs); cz=sum(v.z for v in vs)/len(vs)
bm=bmesh.new(); bm.from_mesh(lo.data); bm.faces.ensure_lookup_table()
RX,RZ=0.044,0.033
fs=[f for f in bm.faces if ((f.calc_center_median().x-cx)/(RX*1.15))**2+((f.calc_center_median().z-cz)/(RZ*1.15))**2<1 and f.calc_center_median().y<-0.04]
sl=sorted(fs,key=lambda f:-(sum(e.calc_length() for e in f.edges)**2/max(f.calc_area(),1e-12)))
print("faces %d  flipped %d  tiny %d  worst sliver %.0f  3rd worst %.0f"%(len(fs),sum(1 for f in fs if f.normal.y>0.05),sum(1 for f in fs if f.calc_area()<2e-8),
      sum(e.calc_length() for e in sl[0].edges)**2/sl[0].calc_area(), sum(e.calc_length() for e in sl[2].edges)**2/sl[2].calc_area()))
