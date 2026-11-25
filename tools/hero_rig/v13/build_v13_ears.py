# Adds two ears to feat_v13_65.blend -> feat_v13_ears.blend   (python3 -I build_v13_ears.py)
# Each ear is a closed shell: a top surface (helix rim, concha, antihelix, tragus, lobe) over a thinner back
# surface, joined at the outline. Skin position comes from a ray cast on the head, so it sits on the surface.
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath="feat_v13_65.blend")
head=bpy.data.objects['head_quad']
bv=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
YC,ZC=0.015,1.538           # ear centre (behind the head's middle; top at the brow, bottom at the nose base z 1.505)
A,B=0.021,0.034             # half width (front to back), half height
TILT=math.radians(12)       # top leans back
NR,NS=26,72
def sst(a,b,x):
    t=min(1.0,max(0.0,(x-a)/(b-a))); return t*t*(3-2*t)
def g(x,c,w): return math.exp(-((x-c)/w)**2)
def height(u,v,r):
    """outward height (m) of the ear top surface over the skin at ear coords u (back +), v (up +), radius r in 0..1"""
    wf=sst(-1.0,0.25,u)                                   # 0 at the front edge (attached), 1 toward the back
    lobe=1.0-0.65*sst(-0.35,-0.95,v)                      # lobe hangs closer to the head
    h=0.004+0.013*wf**1.2*lobe
    h+=0.0065*g(r,0.88,0.10)*(0.35+0.65*wf)               # helix rim
    h-=0.0030*g(r,0.68,0.09)*wf                           # scapha, the groove inside the rim
    h+=0.0040*g(r,0.50,0.09)*sst(-0.1,0.3,u)*sst(-0.3,0.2,v)   # antihelix ridge
    h-=0.0095*math.exp(-((u+0.25)**2/0.12+(v+0.15)**2/0.10))   # concha bowl
    h+=0.0060*math.exp(-((u+0.85)**2/0.02+(v+0.05)**2/0.03))   # tragus
    h+=0.0030*math.exp(-(u**2/0.30+(v+0.78)**2/0.05))          # lobe fullness
    return max(h,0.0)
def skin_x(y,z):
    loc,n,i,d=bv.ray_cast(Vector((0.3,y,z)),Vector((-1,0,0)))
    return loc.x if loc else 0.08
def make_ear(sx):
    bm=bmesh.new(); top=[]; back=[]
    def place(r,th):
        u=r*math.cos(th); v=r*math.sin(th)
        a=A*(1.0+0.12*v)                                   # a little wider at the top than the bottom
        lu=a*u/ max(r,1e-9) * r if r>0 else 0.0
        lv=B*v
        y=YC+lu*math.cos(TILT)+lv*math.sin(TILT)
        z=ZC-lu*math.sin(TILT)+lv*math.cos(TILT)
        h=height(u,v,r)
        x=skin_x(y,z)
        return y,z,x,h
    ring_t=[]; ring_b=[]
    for i in range(NR+1):
        r=i/NR; rt=[]; rb=[]
        for j in range(NS if i>0 else 1):
            th=2*math.pi*j/NS
            y,z,x,h=place(r,th)
            rt.append(bm.verts.new((x+h,y,z)))
            rb.append(bm.verts.new((x+max(h-0.0045,-0.003),y,z)))
        ring_t.append(rt); ring_b.append(rb)
    for j in range(NS):                                    # centre fans
        k=(j+1)%NS
        bm.faces.new((ring_t[0][0],ring_t[1][j],ring_t[1][k]))
        bm.faces.new((ring_b[0][0],ring_b[1][k],ring_b[1][j]))
    for i in range(1,NR):
        for j in range(NS):
            k=(j+1)%NS
            bm.faces.new((ring_t[i][j],ring_t[i+1][j],ring_t[i+1][k],ring_t[i][k]))
            bm.faces.new((ring_b[i][j],ring_b[i][k],ring_b[i+1][k],ring_b[i+1][j]))
    for j in range(NS):                                    # outline wall
        k=(j+1)%NS
        bm.faces.new((ring_t[NR][j],ring_t[NR][k],ring_b[NR][k],ring_b[NR][j]))
    if sx<0:
        for v in bm.verts: v.co.x=-v.co.x
        bmesh.ops.reverse_faces(bm,faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    me=bpy.data.meshes.new('ear_mesh_'+('r' if sx>0 else 'l'))
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth=True
    o=bpy.data.objects.new('ear_'+('r' if sx>0 else 'l'),me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(head.data.materials[0])
    return o
for sx in (1,-1): make_ear(sx)
bpy.ops.wm.save_as_mainfile(filepath="feat_v13_ears.blend")
print("saved ears")
