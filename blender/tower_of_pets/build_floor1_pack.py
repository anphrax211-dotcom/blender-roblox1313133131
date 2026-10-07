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
import common, castle, floor1
for m in (common, castle, floor1):
    importlib.reload(m)

OUT = os.path.join(os.path.dirname(HERE), 'TowerOfPets_Floor1.blend')
JSON_DIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'exports', 'TowerOfPets', 'Floor1')


def main(path=OUT):
    common.reset_scene()
    common.build_materials()
    castle.build_castle_materials()
    floor1.build_floor1_materials()
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
    sun.data.energy = 2.6; sun.data.color = (1.0, 0.96, 0.88); sun.data.angle = math.radians(2.5)
    sun.rotation_euler = Vector((0.45, 0.75, -0.55)).normalized().to_track_quat('-Z', 'Y').to_euler()
    common.coll('LIGHTING', floor1.ROOT).objects.link(sun)
    cams = floor1.build_floor1_cameras()
    sc.camera = cams['CAM_F1_Overview']
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    os.makedirs(JSON_DIR, exist_ok=True)
    with open(os.path.join(JSON_DIR, 'floor1_layout.json'), 'w') as f:
        json.dump(layout, f, indent=1)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects
               if o.type == 'MESH' and o.name not in common.ASSETS)
    print('stats', stats)
    print(f'Floor 1: ~{tris:,} triangles, {len(bpy.data.objects)} objects')
    print('Saved:', path)


if __name__ == '__main__':
    main()
