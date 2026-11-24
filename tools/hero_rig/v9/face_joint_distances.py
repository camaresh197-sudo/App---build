import bpy, sys
from mathutils.kdtree import KDTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
arm = next(o for o in bpy.data.objects if o.type=='ARMATURE')
M = arm.matrix_world
def verts(o):
    # basis (rest) positions in world space
    if o.data.shape_keys: src = o.data.shape_keys.key_blocks[0].data
    else: src = o.data.vertices
    return [o.matrix_world @ v.co for v in src]
groups = {
 "head":  ["head_12","head_118","head_21","head_27","hair_l_0","hair_r_0","hat_0","hat_1","hat_2","hat_3","hat_4"],
 "must":  ["mustm_l","mustm_r"],
 "nose":  ["nose_nost_l_0","nose_nost_r_0"],
 "mouth": ["mouth_cav_0","teeth_u","teeth_l"],
 "eye":   ["lidl_l_0","lidl_r_0","lidu_l_0","lidu_r_0","iris_l_1","iris_r_1","pupil_l_0","pupil_r_0","white_l_1","white_r_1"],
 "neck":  ["neck_1","neck_2"],
}
def pts(names):
    out=[]
    for n in names:
        o=bpy.data.objects.get(n)
        if o: out += verts(o)
    return out
allface = pts(sum(groups.values(), []))
kd_all = KDTree(len(allface)); [kd_all.insert(p,i) for i,p in enumerate(allface)]; kd_all.balance()
kd = {}
for g,names in groups.items():
    p=pts(names)
    if not p: continue
    k=KDTree(len(p)); [k.insert(q,i) for i,q in enumerate(p)]; k.balance(); kd[g]=k
faceb=[b for b in arm.data.bones if any(b.name.startswith(s) for s in ["brow","cheek","fold","hair","hat","jaw","chin","corner","lip","lid","mass","mouth","nose","puff","must","shine","white","iris","pupil"])]
rows=[]
for b in faceb:
    w = M @ b.head_local
    _,_,d = kd_all.find(w)
    rows.append((d,b.name,tuple(round(c,3) for c in w)))
rows.sort(reverse=True)
print("FACE BONES:", len(rows))
for d,n,w in rows: print(f"{n:12s} dist_cm={d*100:6.2f} world={w}")
