import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1] + "/body/master.blend")
arm = bpy.data.objects["character_rig"]
print("NBONES", len(arm.data.bones))
def depth(b):
    d = 0
    while b.parent: b = b.parent; d += 1
    return d
for b in arm.data.bones:
    print("B", depth(b), b.name, "<-", b.parent.name if b.parent else None, "head", [round(c, 3) for c in b.head_local], "tail", [round(c, 3) for c in b.tail_local], "deform", b.use_deform)
