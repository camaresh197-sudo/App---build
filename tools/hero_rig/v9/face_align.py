import bpy, sys, json, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
mode = sys.argv[sys.argv.index("--")+2]          # "report" or "apply"
ref = json.load(open(sys.argv[sys.argv.index("--")+3]))
arm = next(o for o in bpy.data.objects if o.type=='ARMATURE')
EYE = ("lid","white","iris","pupil","shine")
todo = []
for b in arm.data.bones:
    if b.name not in ref or b.name.startswith(EYE): continue
    if b.name in ("head","neck","neck2","chest","spine","spine2","pelvis","root","hip_l","hip_r","clav_l","clav_r") : continue
    r = ref[b.name]; tgt = Vector((r[9], -r[11], r[10])); cur = b.head_local.copy()
    d = (tgt-cur).length
    if d > 0.005: todo.append((d, b.name, tgt-cur))
todo.sort(reverse=True)
print("MOVE", len(todo), "bones off >0.5 cm (excluding eyes, core spine/head):")
for d,n,v in todo: print(f"  {n:12s} {d*100:5.2f} cm")
if mode == "apply":
    bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones
    for d,n,v in todo:
        for c in eb[n].children: c.use_connect = False
    for d,n,v in todo:
        e = eb[n]; e.head += v; e.tail += v
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.save_mainfile(filepath=sys.argv[sys.argv.index("--")+4])
    print("SAVED", len(todo))
