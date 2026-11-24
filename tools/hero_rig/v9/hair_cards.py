import bpy, sys, math, random, bmesh
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
out = sys.argv[sys.argv.index("--")+2]
random.seed(7)
arm = next(o for o in bpy.data.objects if o.type=='ARMATURE')
old = {n: bpy.data.objects[n] for n in ["hair_l_0","hair_r_0"]}
mat = old["hair_l_0"].data.materials[0] if old["hair_l_0"].data.materials else None
coll = old["hair_l_0"].users_collection[0]
C = Vector((0.10,-0.075,1.56)); RX,RY,RZ = 0.142,0.118,0.152
SEG = 14; CARDS_PER_SIDE = 84; WIDTH = 0.0055; END_Z = 1.18
def surf(lat, lon, off):
    return Vector((C.x+(RX+off)*math.cos(lat)*math.cos(lon),
                   C.y+(RY+off)*math.cos(lat)*math.sin(lon),
                   C.z+(RZ+off)*math.sin(lat)))
def strand(lat0, lon0, end_lat, phase, amp, dr=None):
    pts=[]
    for k in range(SEG+1):
        t = k/SEG
        lat = lat0 + (end_lat-lat0)*t
        s = max(0.0, -lat)/math.radians(52)          # 0 at equator, 1 at the ends
        drift = 0.12*math.sin(phase)
        L0 = lon0 % (2*math.pi)
        if 3.95 <= L0 < 4.25: drift = 0.30                 # one side of the part: sweep away from the gap
        elif 3.25 < L0 <= 3.55: drift = -0.30              # other side: sweep away from the gap
        lon = lon0 + drift*t
        base_off = 0.0025 + 0.009*t**1.5                # close to the scalp at the root, lifts toward the tips
        p = surf(max(lat,0.0), lon, base_off)
        if lat < 0: p.z = C.z + (RZ+base_off)*math.sin(lat)*0 - s*(C.z-END_Z) + 0.0
        radial = Vector((math.cos(lon), math.sin(lon), 0))
        wave = amp*t*math.sin(9*t + phase) + 0.002*math.sin(31*t + 4*phase)*t   # fine kinks along each strand
        p = p + radial*wave + Vector((0,0,0))
        pts.append(p)
    return pts
def front_root(lat, lon):
    # keep roots off the forehead and eyes: a wider front arc lower down, a narrow one over the crown
    d = abs(((lon + math.pi/2 + math.pi) % (2*math.pi)) - math.pi)
    limit = 75 if lat < math.radians(50) else 35
    return d < math.radians(limit)
def part_band(lat, lon):
    return math.degrees(lat) > 40 and 3.55 < lon % (2*math.pi) < 3.95   # left side part
def make_card(bm_faces_L, bm_faces_R, side):
    pass
cards = {"hair_l_0": [], "hair_r_0": []}
for side, lon_lo, lon_hi, key in [("L", math.pi*0.5, math.pi*1.5, "hair_l_0"), ("R", -math.pi*0.5, math.pi*0.5, "hair_r_0")]:
    n = 0
    tries = 0
    while n < CARDS_PER_SIDE and tries < 5000:
        tries += 1
        lat0 = math.radians(random.uniform(22, 78))
        lon0 = random.uniform(lon_lo, lon_hi)
        if front_root(lat0, lon0) or (key=="hair_l_0" and part_band(lat0, lon0)): continue
        end_lat = math.radians(random.uniform(-52, -36))
        phase = random.uniform(0, 2*math.pi)
        amp = random.uniform(0.012, 0.028)
        pts = strand(lat0, lon0, end_lat, phase, amp)
        if any(p.y < -0.09 and p.z < 1.62 for p in pts): continue   # keep strands off the face
        cards[key].append(pts); n += 1
    print("CARDS", key, n, "tries", tries)

crown_cards = {"hair_l_0": [], "hair_r_0": []}
for key, lo, hi in [("hair_l_0", math.pi*0.5, math.pi*1.5), ("hair_r_0", -math.pi*0.5, math.pi*0.5)]:
    n = 0; tries = 0
    while n < 40 and tries < 6000:
        tries += 1
        lat0 = math.radians(random.uniform(58, 80))
        lon0 = random.uniform(lo, hi)
        d = abs(((lon0 + math.pi/2 + math.pi) % (2*math.pi)) - math.pi)
        if d < math.radians(18): continue                  # keep only the hairline bare
        if key == "hair_l_0" and part_band(lat0, lon0): continue
        end_lat = math.radians(random.uniform(40, 50))     # short: stops at the upper back of the skull
        pts = strand(lat0, lon0, end_lat, random.uniform(0, 2*math.pi), 0.006)
        if any(p.y < -0.09 and p.z < 1.62 for p in pts): continue   # keep strands off the face
        crown_cards[key].append(pts); n += 1
    print("CROWN", key, n)

fringe_cards = []
FRONT = -math.pi/2 + 2*math.pi
nf = 0; tries = 0
PART_LON = FRONT - math.radians(36)                       # parting on the character's left                       # the parting runs through the fringe here
GAP = math.radians(3.5)
while nf < 30 and tries < 4000:
    tries += 1
    lon0 = FRONT + random.uniform(-math.radians(46), math.radians(30))
    if abs(lon0 - PART_LON) < GAP: continue                 # keep the parting clear
    lat0 = math.radians(random.uniform(60, 78))
    end_lat = math.radians(random.uniform(28, 34))         # falls forward over the forehead, stops above the brows
    # cards either side of the parting sweep away from it
    dr = -0.22 if lon0 < PART_LON else 0.22
    pts = strand(lat0, lon0, end_lat, 0.0, 0.003, dr)
    if any(p.y < -0.09 and p.z < 1.62 for p in pts): continue
    fringe_cards.append(pts); nf += 1
print("FRINGE", nf, "tries", tries)

def build(name, strands):
    m = bpy.data.meshes.new(name); b = bmesh.new()
    for pts in strands:
        verts_l=[]; verts_r=[]
        for k,p in enumerate(pts):
            radial = Vector((p.x-C.x, p.y-C.y, 0)).normalized()
            tang = (pts[min(k+1,len(pts)-1)] - pts[max(k-1,0)]).normalized()
            side_dir = tang.cross(radial).normalized()
            w = WIDTH*random.uniform(0.6, 1.4)*(1 - 0.8*k/len(pts))   # each strand its own width, tapering to a point
            verts_l.append(b.verts.new(p + side_dir*w*0.5))
            verts_r.append(b.verts.new(p - side_dir*w*0.5))
        for k in range(len(pts)-1):
            b.faces.new([verts_l[k], verts_r[k], verts_r[k+1], verts_l[k+1]])
    b.normal_update(); b.to_mesh(m); b.free()
    o = bpy.data.objects.new(name, m); coll.objects.link(o); o.parent = arm
    if mat: o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = False
    vg = o.vertex_groups.new(name="head"); vg.add(list(range(len(m.vertices))), 1.0, 'REPLACE')
    md = o.modifiers.new("Armature","ARMATURE"); md.object = arm
    return o
for n in old: bpy.data.objects.remove(old[n], do_unlink=True)
L = build("hair_l_0", cards["hair_l_0"] + crown_cards["hair_l_0"] + fringe_cards[::2]); R = build("hair_r_0", cards["hair_r_0"] + crown_cards["hair_r_0"] + fringe_cards[1::2])
print("CARDS faces", len(L.data.polygons), len(R.data.polygons), "verts", len(L.data.vertices), len(R.data.vertices))
bpy.ops.wm.save_mainfile(filepath=out); print("SAVED", out)
