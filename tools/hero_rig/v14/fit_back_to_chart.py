import sys, bpy, bmesh, json, math
from mathutils import Vector
src,dst=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2]
S='/tmp/claude-0/-home-user-App---build/06e83864-e0ef-54c3-9ec4-508030560da5/scratchpad/hero/'
rows={int(k):v for k,v in json.load(open(S+'chart_rows.json')).items()}
CROWN_ROW=4; CHIN_ROW=410; XF=415.0; HPX=CHIN_ROW-CROWN_ROW
def chart_r(t):
    row=int(round(CROWN_ROW+t*HPX))
    for d in range(0,6):
        for rr in (row-d,row+d):
            if rr in rows: return (rows[rr][1]-XF)/HPX
    return None
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['head_quad']; M=o.matrix_world; Mi=M.inverted()
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
CROWN=1.674; CHIN=1.391; HMM=(CROWN-CHIN)*1000; YF=-0.105
# current back extent per 4mm z-bin
cur={}
for v in bm.verts:
    p=M@v.co; b=round(p.z*1000/4)
    if b not in cur or p.y>cur[b]: cur[b]=p.y
def cur_back(z):
    b=round(z*1000/4)
    for d in range(0,6):
        for bb in (b-d,b+d):
            if bb in cur and cur[bb]>0.02: return cur[bb]
    return None
def scale(z):
    t=(CROWN-z)/(CROWN-CHIN); r=chart_r(min(max(t,0.0),1.0))
    cb=cur_back(z)
    if r is None or cb is None: return 1.0
    target=YF+r*(HMM/1000.0)
    return max(0.85,min(1.15,target/cb))
# smooth the scale curve over z
zs=[CHIN+i*0.004 for i in range(int((CROWN-CHIN)/0.004)+1)]
sc=[scale(z) for z in zs]
k=10; sm=[sum(sc[max(0,i-k):i+k+1])/len(sc[max(0,i-k):i+k+1]) for i in range(len(sc))]
def s_of(z):
    i=int(round((z-CHIN)/0.004)); i=max(0,min(len(sm)-1,i)); return sm[i]
print('FIT scale samples', [(round(z*1000), round(s_of(z),2)) for z in zs[::12]])
for v in bm.verts:
    p=M@v.co
    if p.y>0.0:
        blend=min(1.0,p.y/0.02)
        p.y=p.y*(1+(s_of(p.z)-1)*blend)
        v.co=Mi@p
bm.normal_update()
flip=sum(1 for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].normal.dot(e.link_faces[1].normal)<0)
ys=[(M@v.co).y for v in bm.verts]
print(f"FIT flips {flip} y {min(ys)*1000:.1f}..{max(ys)*1000:.1f} depth {(max(ys)-min(ys))*1000:.1f}")
bm.to_mesh(o.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst)
print('saved')
