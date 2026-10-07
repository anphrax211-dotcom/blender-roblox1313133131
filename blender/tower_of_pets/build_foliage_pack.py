"""TOWER OF PETS - Roblox trees & foliage asset pack as its own scene (TowerOfPets_Foliage.blend).

    python3 blender/tower_of_pets/build_foliage_pack.py        (or blender -b -P ...)

Same meshes the lobby instances (built by foliage.py), laid out for review / export:
    row 1  Large_Lobby_Tree, Medium_Tree, Small_Tree, Tall_Thin_Tree (high detail) + a planted lobby tree
    row 2  the low-LOD versions
    row 3  Bush_01-03, Ground_Plant_01-02, Vine
    row 4  tree parts (trunks, branches, roots, leaf clusters, vines) and the stone planters
Collections: TOWER_OF_PETS_FOLIAGE / TREES, FOLIAGE, TREE_PARTS (Trunks, Branches, Leaves, Roots, Vines), PLANTERS
"""
import os, sys, importlib, math
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import common, foliage
for m in (common, foliage):
    importlib.reload(m)

OUT = os.path.join(os.path.dirname(HERE), 'TowerOfPets_Foliage.blend')

LAYOUT = [
    (0, ['Tree_Large_High', 'Tree_Medium_High', 'Tree_Small', 'Tree_Tall_Thin'], 32),
    (-36, ['Tree_Large_Low', 'Tree_Medium_Low', 'Tree_Small_Low', 'Tree_Tall_Thin_Low'], 32),
    (34, ['Bush_01', 'Bush_02', 'Bush_03', 'Ground_Plant_01', 'Ground_Plant_02', 'Vine'], 10),
    (54, ['Trunk_Thick', 'Trunk_Thin', 'Branch_Curved', 'Branch_Small', 'Root_Set', 'Root_Single',
          'Leaf_Cluster_A', 'Leaf_Cluster_B', 'Leaf_Cluster_C', 'Leaf_Cluster_Low', 'Leaf_Single',
          'Vine_Short', 'Vine_Medium', 'Vine_Long'], 12),
    (80, ['Stone_Planter', 'Stone_Planter_Empty', 'Stone_Planter_Large', 'Planter_Wall_Block',
          'Planter_Corner_Post'], 20),
]


def main(path=OUT):
    common.reset_scene()
    common.build_materials()
    foliage.build_foliage_materials()
    foliage.build_foliage_assets(None)
    for y, names, step in LAYOUT:
        x0 = -step * (len(names) - 1) / 2
        for i, n in enumerate(names):
            ob = common.ASSETS[n]
            ob.location = (x0 + i * step, -y, 0)
            if n.startswith('Vine'):
                ob.location.z = 8.0
            if n.startswith('Leaf_Cluster'):
                ob.location.z = 5.0
    # a planted lobby tree, as in the reference close-up
    foliage.tree_in_planter('Showcase_LobbyTree', 'TREES', (78, 0, 0), 0.4, seed=3)
    # ground, sky, sun, cameras
    p = common.Part('Showcase_Ground', 'TOWER_OF_PETS_FOLIAGE')
    p.box((0, -20, -0.25), (260, 200, 0.5), 'Plaza_Tile')
    p.finish()
    sc = bpy.context.scene
    w = bpy.data.worlds.new('Sky'); sc.world = w
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.25, 0.60, 1.0, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 2.6; sun.data.color = (1.0, 0.96, 0.88); sun.data.angle = math.radians(3)
    sun.rotation_euler = Vector((0.5, 0.7, -0.6)).normalized().to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(sun)

    def cam(name, loc, tgt, lens):
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        c.data.lens = lens; c.location = loc
        c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(c)
        return c
    sc.camera = cam('CAM_Trees', (0, -66, 32), (0, 0, 10), 32)
    cam('CAM_LobbyTree_CloseUp', (58, -34, 9), (78, 0, 10), 30)
    cam('CAM_Foliage', (0, -47, 9), (0, -34, 1.5), 34)
    cam('CAM_Parts', (0, -76, 16), (0, -54, 4), 34)
    cam('CAM_Planters', (0, -112, 26), (0, -80, 1), 36)
    cam('CAM_Overview', (0, -190, 120), (0, -30, 0), 32)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    tris = {n: sum(len(f.vertices) - 2 for f in o.data.polygons) for n, o in common.ASSETS.items()}
    for n in sorted(tris):
        print(f'  {n:24s} {tris[n]:6d} tris')
    print('Saved:', path)


if __name__ == '__main__':
    main()
