"""TOWER OF PETS - Floor 1 (The Verdant Kingdom) greybox layout scene (TowerOfPets_Floor1.blend).

    python3 blender/tower_of_pets/build_floor1_pack.py         (or blender -b -P ...)

Builds floor1.py's terrain, water, landmark blockouts, cloud sea, guide labels and cameras, saves the .blend and
writes exports/TowerOfPets/Floor1/floor1_layout.json (spawn, checkpoints, bosses, eggs, caves, path waypoints in
Roblox coordinates).
"""
import os, sys, importlib, math, json
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import common, castle, foliage, islands, floor1, floor1_detail, floor1_roblox
for m in (common, castle, foliage, islands, floor1, floor1_detail, floor1_roblox):
    importlib.reload(m)

OUT = os.path.join(os.path.dirname(HERE), 'TowerOfPets_Floor1.blend')
JSON_DIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'exports', 'TowerOfPets', 'Floor1')


def haze(sc):
    """slight atmospheric haze for the previews (the Roblox side uses Atmosphere, see Floor1_Lighting.lua)"""
    try:
        sc.view_layers[0].use_pass_mist = True
        ms = sc.world.mist_settings
        ms.start, ms.depth, ms.falloff = 1500.0, 26000.0, 'QUADRATIC'
        ng = bpy.data.node_groups.new('F1_Haze', 'CompositorNodeTree')
        ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = ng.nodes.new('CompositorNodeRLayers')
        mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.5
        mix = ng.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
        out = ng.nodes.new('NodeGroupOutput')
        A = next(i for i in mix.inputs if i.name == 'A' and i.type == 'RGBA')
        B = next(i for i in mix.inputs if i.name == 'B' and i.type == 'RGBA')
        R = next(o for o in mix.outputs if o.type == 'RGBA')
        B.default_value = (0.70, 0.84, 1.0, 1.0)
        L = ng.links.new
        L(rl.outputs['Mist'], mul.inputs[0]); L(mul.outputs[0], mix.inputs['Factor'])
        L(rl.outputs['Image'], A); L(R, out.inputs['Image'])
        sc.compositing_node_group = ng
    except Exception as e:                               # older / newer compositor API: render without haze
        print('haze skipped:', e)


def main(path=OUT):
    common.reset_scene()
    common.build_materials()
    castle.build_castle_materials()
    floor1.build_floor1_materials()
    floor1_detail.build_detail_assets()
    layout, stats = floor1.build_floor1()
    sc = bpy.context.scene
    w = bpy.data.worlds.new('Sky'); sc.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.62, 0.86, 1.0, 1); ramp.color_ramp.elements[1].color = (0.06, 0.38, 1.0, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector']); nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    sun = bpy.data.objects.new('Sun_Key', bpy.data.lights.new('Sun_Key', 'SUN'))
    sun.data.energy = 3.0; sun.data.color = (1.0, 0.93, 0.80); sun.data.angle = math.radians(3.5)   # warm, soft
    sun.rotation_euler = Vector((0.45, 0.75, -0.55)).normalized().to_track_quat('-Z', 'Y').to_euler()
    common.coll('LIGHTING', floor1.ROOT).objects.link(sun)
    haze(sc)
    cams = floor1.build_floor1_cameras()
    sc.camera = cams['CAM_F1_Overview']
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    os.makedirs(JSON_DIR, exist_ok=True)
    with open(os.path.join(JSON_DIR, 'floor1_layout.json'), 'w') as f:
        json.dump(layout, f, indent=1)
    # environment scatter -> Roblox placement data + placer + lighting scripts
    offsets = {}
    for name in {p[1] for p in floor1_detail.PLACED}:
        co = [v.co for v in common.ASSETS[name].data.vertices]
        c = [(max(v[a] for v in co) + min(v[a] for v in co)) / 2 for a in range(3)]
        offsets[name] = floor1_roblox.to_roblox(*c)
    files, per_cat = floor1_roblox.write_scatter(floor1_detail.PLACED, offsets, JSON_DIR)
    print('scatter modules', len(files), per_cat)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects
               if o.type == 'MESH' and o.name not in common.ASSETS)
    print('stats', stats)
    print(f'Floor 1: ~{tris:,} triangles, {len(bpy.data.objects)} objects')
    print('Saved:', path)


if __name__ == '__main__':
    main()
