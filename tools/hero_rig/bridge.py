import bpy, math
from mathutils import Vector
SRC="/home/claude/out/character_rigged_shoulders.blend"
OUT="/home/claude/out/character_rigged_bridge.blend"
W=float(__import__('sys').argv[-1]) if __import__('sys').argv[-1].replace('.','').isdigit() else 0.42
bpy.ops.wm.open_mainfile(filepath=SRC)
def sm(x): x=max(0,min(1,x)); return x*x*(3-2*x)
o=bpy.data.objects["torso_cartoon"]; M=o.matrix_world; Mi=M.inverted()
CX=0.09
for v in o.data.vertices:
    p=M@v.co
    f=1+W*sm((p.z-1.20)/0.15)
    v.co=Mi@Vector((CX+(p.x-CX)*f,p.y,p.z))
o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT,compress=True)
print("SAVED")
