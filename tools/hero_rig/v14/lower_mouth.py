import sys, bpy, bmesh, math
src,dst=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2]
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['head_quad']; M=o.matrix_world; Mi=M.inverted()
NOSE=1.4875; MOUTH=1.476; MOUTH_NEW=1.467; CHIN=1.391
def remap(z):
    if z>=NOSE or z<=CHIN: return z
    if z>=MOUTH: return NOSE-(NOSE-z)*(NOSE-MOUTH_NEW)/(NOSE-MOUTH)
    return CHIN+(z-CHIN)*(MOUTH_NEW-CHIN)/(MOUTH-CHIN)
def smooth(t): t=max(0.0,min(1.0,t)); return t*t*(3-2*t)
def weight(p):
    wy=smooth((-p.y-0.00)/0.06)          # front only: 0 at y>=0, 1 by y<=-0.06
    wx=1.0-smooth((abs(p.x)-0.045)/0.045) # full inside |x|<45mm, fades by 90 mm
    return wy*wx
bm=bmesh.new(); bm.from_mesh(o.data)
n=0
for v in bm.verts:
    p=M@v.co; w=weight(p)
    if w>0 and CHIN<p.z<NOSE:
        p.z=p.z+w*(remap(p.z)-p.z); v.co=Mi@p; n+=1
bm.normal_update()
flip=sum(1 for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].normal.dot(e.link_faces[1].normal)<0)
# new mouth groove: min |y| front protrusion on the centreline between lips
prof={}
for v in bm.verts:
    p=M@v.co
    if abs(p.x)<0.006 and 1.43<p.z<1.50:
        b=round(p.z*1000/2)*2
        if b not in prof or p.y<prof[b]: prof[b]=p.y
groove=max(prof.items(), key=lambda kv: kv[1])  # least forward point
print(f"MOUTH moved {n} flips {flip} groove z {groove[0]} y {groove[1]*1000:.1f}")
bm.to_mesh(o.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst)
print('saved')
