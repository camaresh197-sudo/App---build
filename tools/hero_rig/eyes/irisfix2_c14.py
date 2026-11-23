import bpy
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_c14.blend")
for s in 'lr':
    m=bpy.data.materials['IrisMat_%s'%s]; nt=m.node_tree
    cr=[n for n in nt.nodes if n.type=='VALTORGB'][0]; b=[n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'][0]
    b.inputs['Roughness'].default_value=0.75; b.inputs['Specular IOR Level'].default_value=0.03
    el=cr.color_ramp.elements
    # rebuild the ramp: dark ring at the rim, bright saturated amber toward the pupil
    while len(el)>2: el.remove(el[-1])
    el[0].position=0.0; el[0].color=(0.03,0.012,0.004,1)
    el[1].position=1.0; el[1].color=(0.95,0.50,0.08,1)
    for pos,col in ((0.10,(0.05,0.02,0.005,1)),(0.30,(0.55,0.22,0.03,1)),(0.60,(0.80,0.38,0.06,1))):
        e=el.new(pos); e.color=col
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_d14.blend")
