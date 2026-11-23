import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_b14.blend")
for s in 'lr':
    o=bpy.data.objects['iris_%s_1'%s]
    ws=[o.matrix_world@v.co for v in o.data.vertices]; ctr=sum(ws,Vector())/len(ws); R=max((p-ctr).length for p in ws)
    m=bpy.data.materials.new('IrisMat_%s'%s); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes): 
        if n.type!='OUTPUT_MATERIAL': nt.nodes.remove(n)
    out=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'][0]
    bsdf=nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.inputs['Roughness'].default_value=0.5; bsdf.inputs['Specular IOR Level'].default_value=0.25
    tc=nt.nodes.new('ShaderNodeTexCoord'); mp=nt.nodes.new('ShaderNodeMapping'); mp.vector_type='TEXTURE'
    mp.inputs['Location'].default_value=ctr; mp.inputs['Scale'].default_value=(R,R,R)
    gr=nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type='SPHERICAL'
    cr=nt.nodes.new('ShaderNodeValToRGB')
    # gradient factor is 1 at the centre and 0 at the iris rim
    cr.color_ramp.elements[0].position=0.0; cr.color_ramp.elements[0].color=(0.04,0.02,0.01,1)      # dark limbal ring at the rim
    cr.color_ramp.elements[1].position=1.0; cr.color_ramp.elements[1].color=(0.55,0.26,0.06,1)      # lighter amber near the pupil
    e1=cr.color_ramp.elements.new(0.12); e1.color=(0.04,0.02,0.01,1)
    e2=cr.color_ramp.elements.new(0.32); e2.color=(0.20,0.08,0.015,1)                              # deep amber
    nt.links.new(tc.outputs['Object'],mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'],gr.inputs['Vector'])
    nt.links.new(gr.outputs['Fac'],cr.inputs['Fac']); nt.links.new(cr.outputs['Color'],bsdf.inputs['Base Color']); nt.links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    o.data.materials.clear(); o.data.materials.append(m)
    print("IG iris",s,"centre",tuple(round(x,4) for x in ctr),"R=%.4f"%R)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-App---build/ea27b49c-e36e-540f-ac13-37334bb2e73a/scratchpad/wip/hero_wip_defined_c14.blend")
print("IGSAVED")
