"""TOWER OF PETS - export Floor 1 (blender/TowerOfPets_Floor1.blend) to Roblox-ready FBX files.

    python3 blender/tower_of_pets/build_floor1_export.py      (after build_floor1_pack.py)

Writes exports/TowerOfPets/Floor1/: one FBX per biome + natural bridges, built bridges, water, landmark blockouts and
clouds, all in one world space (1 unit = 1 stud), Floor1_Materials.lua, Floor1_Lights.lua (empty: sun only) and
manifest.json, then Floor1_Assets.fbx + Floor1_Palette.png (the scatter's asset library, see floor1_roblox.py). Terrain is chunked into <= 6,000-triangle MeshParts so PreciseConvexDecomposition collision
follows the ground closely. GUIDES (labels, reserved footprints, scale figures) are not exported.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import export_fbx, floor1, floor1_roblox

ROOT_DIR = os.path.dirname(os.path.dirname(HERE))
GROUPS = (
    ('Floor1_Verdant_Forest', ('VERDANT_FOREST',), None),
    ('Floor1_Waterfall_Valley', ('WATERFALL_VALLEY',), None),
    ('Floor1_Ancient_Ruins', ('ANCIENT_RUINS',), None),
    ('Floor1_Mystic_Wilds', ('MYSTIC_WILDS',), None),
    ('Floor1_Jungle_Fortress', ('JUNGLE_FORTRESS',), None),
    ('Floor1_Natural_Bridges', ('NATURAL_BRIDGES',), None),
    ('Floor1_Bridges', ('F1_BRIDGES',), None),
    ('Floor1_Entrance', ('F1_ENTRANCE',), None),
    ('Floor1_Shop', ('TOWER_OF_PETS_SHOP',), 'Shop_Root'),
    ('Floor1_Hatchery', ('TOWER_OF_PETS_HATCHERY',), 'Hatchery_Root'),
    ('Floor1_Village', ('F1_VILLAGE',), None),
    ('Floor1_Fortress', ('F1_FORTRESS',), None),
    ('Floor1_Water', ('WATER',), None),
    ('Floor1_Landmark_Blockouts', ('LANDMARK_BLOCKOUTS',), None),
    ('Floor1_Clouds', ('CLOUDS',), None),
)

if __name__ == '__main__':
    sx, sy = floor1.px(*floor1.SPAWN)
    export_fbx.main(blend=os.path.join(os.path.dirname(HERE), 'TowerOfPets_Floor1.blend'), groups=GROUPS, exclude={},
                    out=os.path.join(ROOT_DIR, 'exports', 'TowerOfPets', 'Floor1'), tri_limit=6000, prefix='Floor1', max_extent=1900,
                    spawn=(sx, sy, 12.0 * floor1.ZL), precise=('_Top__', '_Cliffs__', 'Natural_Bridges', '_Deck__', 'Entrance_Walk', 'Village_Walk', 'Fortress_Walk'))
    out = os.path.join(ROOT_DIR, 'exports', 'TowerOfPets', 'Floor1')
    floor1_roblox.export_assets(os.path.join(os.path.dirname(HERE), 'TowerOfPets_Floor1.blend'), out)
    floor1_roblox.write_rbxmx(out)                  # every Floor 1 ModuleScript in one Studio file
