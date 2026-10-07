"""TOWER OF PETS - floating islands asset pack as its own scene (TowerOfPets_Islands.blend).

    python3 blender/tower_of_pets/build_islands_pack.py        (or blender -b -P ...)

Lays out the eight island variations (Island_A .. Island_H, placed as collection instances) on a row above a
cloud floor, and every modular piece (island bases, rocks, grass, vines, waterfalls, bridges, lanterns,
crystals, decorations, trees from the foliage pack) in rows in front of them for review/export.
"""
import os, sys, importlib, math, random
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import common, foliage, islands
for m in (common, foliage, islands):
    importlib.reload(m)

OUT = os.path.join(os.path.dirname(HERE), 'TowerOfPets_Islands.blend')
MOD_X = 1600              # module rows sit in their own area, away from the showcase
VAR_X = {'Island_E': -420, 'Island_B': -300, 'Island_C': -185, 'Island_A': -40, 'Island_G': 115, 'Island_D': 225,
         'Island_H': 315, 'Island_F': 410}
VAR_Z = {'Island_E': -10, 'Island_B': 25, 'Island_C': 5, 'Island_A': 0, 'Island_G': 30, 'Island_D': 15,
         'Island_H': -5, 'Island_F': 45}
ROWS = [
    (-150, ['Large_Island', 'Medium_Island', 'Small_Island', 'Tall_Island', 'Rock_Formation', 'Crystal_Island'], 95),
    (-260, ['Waterfall_Small', 'Waterfall_Medium', 'Waterfall_Large', 'Waterfall_Wide', 'Bridge_Short',
            'Bridge_Medium', 'Bridge_Long'], 70),
    (-340, ['Rock_Large', 'Rock_Medium', 'Rock_Small', 'Grass_Patch', 'Grass_Tuft', 'Moss_Drape_A', 'Moss_Drape_B',
            'Lantern_Wood', 'Crystal_Small', 'Crystal_Medium', 'Crystal_Large', 'Crystal_Cluster', 'Stone_Block',
            'Stone_Pillar', 'Paw_Banner', 'Wood_Fence'], 20),
]


def main(path=OUT):
    common.reset_scene()
    common.build_materials()
    foliage.build_foliage_materials()
    islands.build_island_materials()
    common.coll(common.ASSET_COLL)
    common.build_assets()                                       # clouds, lanterns, rocks used by the scene
    islands.build_island_assets(None)
    foliage.build_foliage_assets('TREES (foliage pack)')
    islands.build_variations()
    bpy.context.view_layer.layer_collection.children[common.ASSET_COLL].exclude = True
    vl = bpy.context.view_layer.layer_collection.children[islands.ROOT]
    vl.children['ISLAND_VARIATIONS'].exclude = True             # shown through the instances below
    vl.children['TREES (foliage pack)'].exclude = True

    show = common.coll('ISLAND_SHOWCASE')
    for key, x in VAR_X.items():
        islands.place_variation(key, f'{key}_Placed', 'ISLAND_SHOWCASE', (x, 60, VAR_Z[key]))
        common.text_mesh(f'{key}_Label', key.replace('_', ' '), 'ISLAND_SHOWCASE', 7, 0.8, 'Shop_White',
                         (x, 60, VAR_Z[key] + 62))
    for y, names, step in ROWS:
        x0 = -step * (len(names) - 1) / 2
        for i, n in enumerate(names):
            ob = common.ASSETS[n]
            ob.location = (MOD_X + x0 + i * step, y, 0)
            if n.startswith(('Large_', 'Medium_', 'Small_', 'Tall_', 'Rock_Formation', 'Crystal_Island')):
                ob.location.z = 40
            if n.startswith('Waterfall'):
                ob.location.z = 125
    # cloud floor + scattered small floating rocks
    rnd = random.Random(4)
    for i in range(70):
        common.inst(f'Cloud_{"ABCD"[i % 4]}', f'CloudFloor_{i:02d}', 'ISLAND_SHOWCASE',
                    (rnd.uniform(-600, 600), rnd.uniform(-450, 300), rnd.uniform(-190, -150)), rnd.uniform(0, 6.28),
                    rnd.uniform(25, 50))
    for i in range(14):
        common.inst(rnd.choice(('Rock_Large', 'Rock_Medium', 'Rock_Small')), f'FloatingRock_{i:02d}', 'ISLAND_SHOWCASE',
                    (rnd.uniform(-480, 480), rnd.uniform(120, 260), rnd.uniform(40, 140)), rnd.uniform(0, 6.28),
                    rnd.uniform(0.8, 1.6))
    # sky, sun, cameras (same light as the lobby)
    sc = bpy.context.scene
    w = bpy.data.worlds.new('Sky'); sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.25, 0.60, 1.0, 1); bg.inputs['Strength'].default_value = 1.0
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 2.6; sun.data.color = (1.0, 0.96, 0.88); sun.data.angle = math.radians(3)
    sun.rotation_euler = Vector((0.45, 0.75, -0.55)).normalized().to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(sun)

    def cam(name, loc, tgt, lens):
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        c.data.lens = lens; c.data.clip_end = 20000; c.location = loc
        c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(c)
        return c
    sc.camera = cam('CAM_Islands_Overview', (-20, -330, 80), (-20, 60, 0), 22)
    cam('CAM_Island_A', (-40, -95, 45), (-40, 60, -10), 30)
    cam('CAM_Island_C_Crystal', (-185, -20, 25), (-185, 60, -5), 34)
    cam('CAM_Island_H_Bridge', (315, -10, 20), (315, 60, 0), 34)
    cam('CAM_Modules', (MOD_X, -560, 150), (MOD_X, -230, 20), 28)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    for n in ('Large_Island', 'Medium_Island', 'Small_Island', 'Tall_Island', 'Rock_Formation', 'Crystal_Island',
              'Rock_Large', 'Waterfall_Large', 'Bridge_Medium', 'Lantern_Wood', 'Crystal_Cluster'):
        o = common.ASSETS[n]
        print(f'  {n:18s} {sum(len(f.vertices) - 2 for f in o.data.polygons):6d} tris')
    print('Saved:', path)


if __name__ == '__main__':
    main()
