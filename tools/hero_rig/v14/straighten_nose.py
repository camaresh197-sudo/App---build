import sys, bpy, bmesh, json, math
src,dst=sys.argv[sys.argv.index('--')+1], sys.argv[sys.argv.index('--')+2]
S='/tmp/claude-0/-home-user-App---build/06e83864-e0ef-54c3-9ec4-508030560da5/scratchpad/hero/'
pr=json.load(open(S+'prof_v143_base_reverted.json'))
def p(z):
    zb=str(int(round(z/2)*2)); return -pr[zb]-105.0 if zb in pr else None
RZ,TZ=1536.0,1499.0; r=p(RZ); t=p(TZ)
def hump(z):
    if z>=RZ or z<=TZ: return 0.0
    line=r+(RZ-z)/(RZ-TZ)*(t-r); o=p(z)
    return max(0.0,(o-line)) if o is not None else 0.0
def sm(x): x=max(0.0,min(1.0,x)); return x*x*(3-2*x)
def hump_s(z):
    # smooth the correction along z (+-4 mm)
    v=[hump(z+k) for k in range(-4,5)]; return sum(v)/len(v)
def wx(x): return 1.0-sm((abs(x)-0.008)/0.014)      # full within 8 mm of the midline, 0 by 22 mm
def wy(y): return sm((-y-0.05)/0.03)                 # front skin only
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['head_quad']; M=o.matrix_world; Mi=M.inverted()
bm=bmesh.new(); bm.from_mesh(o.data)
moved=0; maxd=0.0
for v in bm.verts:
    q=M@v.co
    if 1.498<q.z<1.537:
        w=wx(q.x)*wy(q.y)
        if w>0:
            d=hump_s(q.z*1000)*w/1000.0
            if d>0: q.y+=d; v.co=Mi@q; moved+=1; maxd=max(maxd,d)
bm.normal_update()
flips=[e for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].normal.dot(e.link_faces[1].normal)<0]
print(f"STR moved {moved} max pull-back mm {maxd*1000:.1f} flips {len(flips)}")
bm.to_mesh(o.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst); print('saved')
