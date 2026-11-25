import bpy, math
from mathutils import Vector

# ---- base head as rings, with the jaw loop designed in ----
import bmesh
EYE_Y=-0.082; EYE_Z=1.533; EYE_X=0.036
# (z, half-width rx, back depth ryb, front depth ryf); jaw loop at z~1.440, chin ring at z~1.424
RINGS=[
(1.6740,0.0040,0.0080,0.0080),
(1.6713,0.0225,0.0430,0.0190),
(1.6685,0.0318,0.0610,0.0270),
(1.6630,0.0437,0.0770,0.0380),
(1.6576,0.0545,0.0880,0.0460),
(1.6521,0.0625,0.0960,0.0530),
(1.6466,0.0690,0.1040,0.0600),
(1.6397,0.0735,0.1110,0.0670),
(1.6329,0.0760,0.1180,0.0740),
(1.6192,0.0814,0.1290,0.0840),
(1.6055,0.0852,0.1330,0.0910),
(1.5918,0.0880,0.1400,0.0965),
(1.5781,0.0905,0.1430,0.1000),
(1.5644,0.0912,0.1450,0.1026),
(1.5370,0.0930,0.1450,0.1040),
(1.500,0.090,0.130,0.102),
(1.482,0.086,0.122,0.099),
(1.458,0.082,0.092,0.097),
(1.440,0.078,0.074,0.100),
(1.426,0.068,0.054,0.114),
(1.416,0.058,0.040,0.113),
(1.406,0.046,0.030,0.100),
(1.396,0.032,0.020,0.078),
(1.387,0.018,0.012,0.050),
]
# densify with a smooth monotone spline (no linear creases between rings)
import numpy as _np
from scipy.interpolate import PchipInterpolator as _P
_z=_np.array([r[0] for r in RINGS])[::-1]
_f=[_P(_z,_np.array([r[i] for r in RINGS])[::-1]) for i in (1,2,3)]
_zs=_np.arange(RINGS[0][0],RINGS[-1][0]-1e-9,-0.004)
_dense=[(float(z),float(_f[0](z)),float(_f[1](z)),float(_f[2](z))) for z in _zs]
_dense.append(RINGS[-1])
RINGS=_dense
NSEG=144
bm=bmesh.new()
ring_verts=[]
for (z,rx,ryb,ryf) in RINGS:
    row=[]
    for j in range(NSEG):
        t=2*math.pi*j/NSEG
        s=math.sin(t); c=math.cos(t)
        ry = ryb*s if s>=0 else ryf*s
        row.append(bm.verts.new((rx*c, ry, z)))
    ring_verts.append(row)
top=bm.verts.new((0,0,RINGS[0][0]))
bot=bm.verts.new((0,0,RINGS[-1][0]-0.004))
for i in range(len(ring_verts)-1):
    a=ring_verts[i]; b=ring_verts[i+1]
    for j in range(NSEG):
        k=(j+1)%NSEG
        bm.faces.new((a[j],a[k],b[k],b[j]))
for j in range(NSEG):
    k=(j+1)%NSEG
    bm.faces.new((top,ring_verts[0][k],ring_verts[0][j]))
    bm.faces.new((bot,ring_verts[-1][j],ring_verts[-1][k]))
bm.normal_update()
me=bpy.data.meshes.new('head_quad_mesh')
bm.to_mesh(me); bm.free()
head=bpy.data.objects.new('head_quad', me)
bpy.context.scene.collection.objects.link(head)
bpy.context.view_layer.objects.active=head

# finer mesh over the nose and nostrils, two passes (about 1 mm quads) so small forms can be resolved
import bmesh as _bmn
for _rx,_rz in ((0.044,0.038),(0.036,0.030),(0.0115,0.028),(0.0080,0.022)):
    _b=_bmn.new(); _b.from_mesh(me)
    _reg=[e for e in _b.edges if all((((v.co.x)/_rx)**2+((v.co.z-(1.512 if _rx<0.02 else 1.495))/_rz)**2<1.0 and v.co.y<-0.08) for v in e.verts)]
    _bmn.ops.subdivide_edges(_b, edges=_reg, cuts=1, use_grid_fill=True)
    _b.to_mesh(me); _b.free(); me.update()
# features (same bumps as features.py)
def bump(p,c,rx,rz,amp):
    d=((p.x-c.x)/rx)**2+((p.z-c.z)/rz)**2
    return -amp*(1-d)**2 if d<1.0 else 0.0
def gbump(p,c,rx,rz,amp):
    d=((p.x-c.x)/rx)**2+((p.z-c.z)/rz)**2
    if d>=3.0: return 0.0
    return -amp*(math.exp(-d)-math.exp(-3.0))/(1-math.exp(-3.0))
for v in me.vertices:
    p=v.co.copy(); dy=0.0
    if p.y<-0.02:
        # nose (redone): one smooth Gaussian ridge with a tip, no steep walls
        dy+=gbump(p,Vector((0,0,1.508)),0.0100,0.023,0.017)
        dy+=gbump(p,Vector((0,0,1.498)),0.0070,0.007,0.008)
        # upper lip, blended into the nose base
        dy+=gbump(p,Vector((0,0,1.462)),0.026,0.012,0.009)
        # nostrils carved into the underside of the nose base: a soft, tilted dent per side (no rim)
        # nostril forms as separate soft shapes (no concentric rings): wing, opening, alar crease, columella
        for sx in (1,-1):
            dy+=gbump(p,Vector((0.0115*sx,0,1.494)),0.0068,0.0085,0.005)            # alar wing, a soft bulge beside the tip
            dy+=gbump(p,Vector((0.0092*sx,0,1.4875)),0.0052,0.0038,-0.0070)     # nostril opening, a small dent under the tip
            dy+=gbump(p,Vector((0.0180*sx,0,1.497)),0.0030,0.0090,-0.0022)      # alar crease, a short groove outside the wing
        dy+=gbump(p,Vector((0,0,1.488)),0.0040,0.0080,0.0025)
        # nasal bridge: a narrow raised ridge from between the eyes down to the tip, with a shadow line along each side
        dy+=gbump(p,Vector((0,0,1.518)),0.0070,0.018,0.0045)
        for sx in (1,-1):
            dy+=gbump(p,Vector((0.0125*sx,0,1.508)),0.0050,0.020,-0.0016)                    # columella between the nostrils
        dy-=0.0015*math.exp(-(((p.x)/0.005)**2+((p.z-1.474)/0.012)**2))   # philtrum ridge from nose base to lip
        dy+=bump(p,Vector((0,0,1.455)),0.024,0.012,0.010)
        dy+=bump(p,Vector((0.052,0,1.553)),0.025,0.016,0.004)
        dy+=bump(p,Vector((-0.052,0,1.553)),0.025,0.016,0.004)
    v.co.y+=dy
# eye sockets, applied after the features so the brow and cheek stay forward of the dish
for v in me.vertices:
    if v.co.y>-0.06: continue
    for sx in (1,-1):
        c=Vector((EYE_X*sx,EYE_Y,EYE_Z))
        d=((v.co.x-c.x)**2/0.042**2+(v.co.z-c.z)**2/0.028**2)**0.5
        if d<1.0:
            v.co.y+=0.024*(1-d)**2
# (removed: a hard 1 mm strip under the nose that showed as a ledge on the finer mesh)
# eyelid edge loops in the mesh itself: subdivide the eye region, then shape the rim and creases on it
import bmesh
bm=bmesh.new(); bm.from_mesh(me)
region=[]
for e in bm.edges:
    ok=True
    for v in e.verts:
        near=False
        for sx in (1,-1):
            c=(EYE_X*sx,EYE_Z)
            if ((v.co.x-c[0])/0.034)**2+((v.co.z-c[1])/0.024)**2<1.0 and v.co.y<-0.06:
                near=True
        if not near: ok=False
    if ok: region.append(e)
bmesh.ops.subdivide_edges(bm, edges=region, cuts=1, use_grid_fill=True)
bm.to_mesh(me); bm.free()
me.update()
# third pass: tightest ring, so the lid loops are finer where they matter most
bm=bmesh.new(); bm.from_mesh(me)
region3=[]
for e in bm.edges:
    ok=True
    for v in e.verts:
        near=any(((v.co.x-EYE_X*sx)/0.024)**2+((v.co.z-EYE_Z)/0.015)**2<1.0 and v.co.y<-0.06 for sx in (1,-1))
        if not near: ok=False
    if ok: region3.append(e)
bmesh.ops.subdivide_edges(bm, edges=region3, cuts=1, use_grid_fill=True)
bm.to_mesh(me); bm.free()
me.update()
# second pass: tighter ring around each eye for finer lid edges
bm=bmesh.new(); bm.from_mesh(me)
region2=[]
for e in bm.edges:
    ok=True
    for v in e.verts:
        near=any(((v.co.x-EYE_X*sx)/0.032)**2+((v.co.z-EYE_Z)/0.021)**2<1.0 and v.co.y<-0.06 for sx in (1,-1))
        if not near: ok=False
    if ok: region2.append(e)
bmesh.ops.subdivide_edges(bm, edges=region2, cuts=1, use_grid_fill=True)
bm.to_mesh(me); bm.free()
me.update()
for v in me.vertices:
    if v.co.y>-0.06: continue
    for sx in (1,-1):
        cx=EYE_X*sx
        dx=(v.co.x-cx)/0.0185
        # almond opening: upper lid higher than the lower lid, outer corner lifted
        outer=sx  # +1 on the right eye (outer = +x), -1 on the left
        lift=0.09*outer*dx
        dz_raw=v.co.z-(EYE_Z+lift*0.0105)
        bU=0.0095; bL=0.0068
        bz=bU if dz_raw>0 else bL
        r=((dx)**2+(dz_raw/bz)**2)**0.5
        if r<1.8:
            # upper lid drapes forward over the eyeball; lower lid stays flatter
            drape=0.0030*max(0.0,1-r) if dz_raw>0 else 0.0012*max(0.0,1-r)
            # lid margin: a soft edge at r~1, then a crease dip just outside
            rim=0.0010*max(0.0,1-abs(r-1.0)/0.2)
            crease=-0.0011*max(0.0,1-abs(r-1.35)/0.2)   # closed crease ring, all round
            v.co.y-=rim+crease
            # outer margin: extra forward lift on the side away from the nose, so the lid covers the eyeball edge
            if 0.9<r<1.3:
                side=0.0030 if dx*sx>0.5 else 0.0018
                v.co.y-=side*max(0.0,1-abs(r-1.1)/0.2)
            # eyebag crease: a closed ring further out
            v.co.y+=0.0006*max(0.0,1-abs(r-1.75)/0.25)
            # wrap the lid skin around the eyeball: pull the opening forward onto a shell just outside the eye
            R=0.0140
            ex=v.co.x-cx; ez=v.co.z-EYE_Z
            if ex*ex+ez*ez<R*R:
                y_surf=-0.062-(R*R-ex*ex-ez*ez)**0.5
                w=max(0.0,min(1.0,(r-0.85)/0.2))*max(0.0,min(1.0,(1.25-r)/0.1))  # margin ring only; the opening stays open
                if y_surf<v.co.y:
                    v.co.y=v.co.y*(1-w)+y_surf*w
# materials
def mat(name,col):
    m=bpy.data.materials.new(name); m.diffuse_color=col; return m
skin=mat('skin',(0.8,0.8,0.8,1)); head.data.materials.append(skin)
white=mat('sclera',(0.92,0.92,0.9,1)); dark=mat('iris',(0.85,0.52,0.12,1))
# eyeballs (sclera) recessed in sockets, irises flattened onto the front
for sx,nm in ((1,'l'),(-1,'r')):
    cx=EYE_X*sx
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=0.0135, location=(cx,-0.0685,EYE_Z))
    e=bpy.context.active_object; e.name='eye_'+nm; e.data.materials.append(white)
# nostril openings as separate small pieces: dark ellipsoids set into the dents so each reads as an opening
nost=mat('nostril',(0.07,0.04,0.04,1))
for sx in (1,-1):
    xs=0.0092*sx
    ys=[v.co.y for v in me.vertices if abs(v.co.x-xs)<0.003 and abs(v.co.z-1.4875)<0.002 and v.co.y<-0.05]
    sy=min(ys)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=1.0, location=(xs,sy+0.0035,1.4875))
    n=bpy.context.active_object; n.name='nostril_'+('l' if sx>0 else 'r')
    n.scale=(0.0046,0.0048,0.0023)
    n.rotation_euler=(0.0,math.radians(14*sx),math.radians(0))
    n.data.materials.append(nost)
    n.data.update()
bpy.ops.wm.save_as_mainfile(filepath="feat_v13_chin.blend")
print("saved feat_v143 verts", len(me.vertices))
