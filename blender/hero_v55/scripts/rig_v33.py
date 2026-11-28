import bpy, sys, math
from mathutils import Vector, Matrix
D = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=D + "/body2/body_gnm_v32_smoothed.blend")
sc = bpy.context.scene
body = bpy.data.objects["body_gnm"]
V = Vector
def mir(v): return V((-v.x, v.y, v.z))
# ---- landmarks (right side, +x). Left = mirrored, named *_l (as in the master rig).
B = {}  # name -> (head, tail, parent)
B["root"] = (V((0,0,0)), V((0,0,0.2)), None)
B["pelvis"] = (V((0,0,0.93)), V((0,0,0.98)), "root")
B["spine"]  = (V((0,0,0.95)), V((0,0,1.09)), "pelvis")
B["spine2"] = (V((0,0,1.09)), V((0,0,1.22)), "spine")
B["chest"]  = (V((0,0,1.22)), V((0,0,1.33)), "spine2")
B["neck"]   = (V((0,-0.012,1.33)), V((0,-0.012,1.43)), "chest")
B["neck2"]  = (V((0,-0.012,1.43)), V((0,-0.010,1.49)), "neck")
B["head"]   = (V((0,-0.010,1.49)), V((0,-0.010,1.68)), "neck2")
side = {
 "hip":   (V((0.085,0,0.90)), V((0.085,0,0.95)), "pelvis"),
 "thigh": (V((0.09,0,0.90)),  V((0.14,-0.005,0.48)), "hip"),
 "knee":  (V((0.14,-0.005,0.48)), V((0.14,-0.005,0.53)), "thigh"),
 "shin":  (V((0.14,-0.005,0.48)), V((0.165,0,0.09)), "knee"),
 "ankle": (V((0.165,0,0.09)), V((0.18,-0.05,0.05)), "shin"),
 "foot":  (V((0.18,-0.05,0.05)), V((0.235,-0.17,0.02)), "ankle"),
 "toe":   (V((0.235,-0.17,0.02)), V((0.25,-0.20,0.02)), "foot"),
 "clav":  (V((0.02,-0.01,1.30)), V((0.20,-0.005,1.34)), "chest"),
 "shoulder": (V((0.20,-0.005,1.34)), V((0.20,-0.005,1.39)), "clav"),
 "uarm":  (V((0.20,-0.005,1.335)), V((0.282,0,1.105)), "shoulder"),
 "elbow": (V((0.282,0,1.105)), V((0.282,0,1.155)), "uarm"),
 "fore":  (V((0.282,0,1.105)), V((0.36,-0.07,0.88)), "elbow"),
 "hand":  (V((0.36,-0.07,0.88)), V((0.395,-0.10,0.79)), "fore"),
}
for n, (h, t, p) in side.items():
    for sfx, f in (("_r", lambda x: x), ("_l", mir)):
        B[n + sfx] = (f(h), f(t), (p + sfx) if p not in ("pelvis", "chest") else p)
# fingers
K = V((0.395,-0.10,0.79)); Dd = (V((0.43,-0.12,0.69)) - K).normalized(); S = Dd.cross(V((0,0,1))).normalized()
for i in range(4):
    h = K + S * ((i - 1.5) * 0.022); t = h + Dd * 0.04
    B[f"fg{i}_r"] = (h, t, "hand_r"); B[f"fh{i}_r"] = (t, t + Dd * 0.035, f"fg{i}_r")
B["thumb_r"] = (V((0.375,-0.115,0.85)), V((0.395,-0.16,0.78)), "hand_r")
for i in range(4):
    for k in ("fg", "fh"):
        h, t, p = B[f"{k}{i}_r"]; B[f"{k}{i}_l"] = (mir(h), mir(t), p[:-2] + "_l")
h, t, p = B["thumb_r"]; B["thumb_l"] = (mir(h), mir(t), "hand_l")
print("bones to create", len(B))
# ---- build armature
ad = bpy.data.armatures.new("character_rig"); arm = bpy.data.objects.new("character_rig", ad)
sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for n, (h, t, p) in B.items():
    eb = ad.edit_bones.new(n); eb.head = h; eb.tail = t
for n, (h, t, p) in B.items():
    if p: ad.edit_bones[n].parent = ad.edit_bones[p]
bpy.ops.object.mode_set(mode='OBJECT')
# ---- auto weights
for o in bpy.data.objects: o.select_set(False)
body.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
with bpy.context.temp_override(active_object=arm, selected_objects=[body, arm], selected_editable_objects=[body, arm]):
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
print("body parent", body.parent.name if body.parent else None, "vgroups", len(body.vertex_groups), "modifiers", [m.type for m in body.modifiers])
# eyes rigid on head bone
hb = arm.pose.bones["head"]
for n in [o.name for o in bpy.data.objects if o.name.startswith(("eyeball_", "iris_", "pupil_"))]:
    o = bpy.data.objects[n]; w = o.matrix_world.copy()
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = "head"
    o.matrix_parent_inverse = (arm.matrix_world @ hb.matrix).inverted(); o.matrix_world = w
bpy.context.view_layer.update()
# weight sanity: unweighted verts
unw = sum(1 for v in body.data.vertices if not any(g.weight > 0.001 for g in v.groups))
print("unweighted verts", unw, "of", len(body.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=D + "/rig/body_rigged_v33.blend")
print("saved v33")
