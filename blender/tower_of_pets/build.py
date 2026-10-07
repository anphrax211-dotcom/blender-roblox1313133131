"""TOWER OF PETS - lobby build (Blender 4.2+/5.x, or the `bpy` pip module).

Builds the playable hub/lobby, the tower entrance + portal, and the exterior-only visual template
of the giant tower, then saves TowerOfPets_Lobby.blend next to the blender/ folder.

    blender -b -P blender/tower_of_pets/build.py
    python3 blender/tower_of_pets/build.py               (with `pip install bpy`)
    (or open build.py in Blender's Scripting tab and press Run Script)

Units: 1 Blender unit = 1 Roblox stud, Z up. The spawn faces +Y toward the tower entrance.
Collections:
    TOWER_OF_PETS / TOWER_OF_PETS_HUB / PET_CLINIC (Exterior, Interior, Roof, Signage, Banners, Statues,
                                                    Reception, Treatment, Decorations, Lighting)
                                      / EXISTING_HUB (TOWER_OF_PETS_SHOP, TOWER_OF_PETS_HATCHERY, Trading,
                                                      Leaderboards, Upgrades, Spawn, Fountain, Plaza, Tower_Entrance)
                  / TOWER_TEMPLATE (Hub_Base, Jungle ... Divine)
                  / FLOATING_ISLANDS / WATERFALLS / ENVIRONMENT / LIGHTING / CAMERAS
    _ASSET_LIBRARY (excluded) - source meshes for every linked duplicate: lanterns, rocks, clouds,
                                crystals, islands, mountains and the TOWER_OF_PETS_FOLIAGE pack
                                (trees, bushes, plants, vines, planters - see foliage.py) and the
                                TOWER_OF_PETS_FLOATING_ISLANDS pack (islands.py; Island_A..H variations
                                are placed in FLOATING_ISLANDS as collection instances)
"""
import os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
import common, foliage, islands, castle, shop, hatchery, clinic, hub, entrance, tower, environment
for m in (common, foliage, islands, castle, shop, hatchery, clinic, hub, entrance, tower, environment):        # re-running inside Blender picks up edits
    importlib.reload(m)

OUT = os.path.join(os.path.dirname(HERE), 'TowerOfPets_Lobby.blend')


def organize_hub():
    """final outliner layout: TOWER_OF_PETS / TOWER_OF_PETS_HUB / PET_CLINIC + EXISTING_HUB (Shop, Hatchery,
    Trading, Leaderboards, Upgrades, Spawn, Fountain, Plaza, Tower_Entrance)"""
    C = bpy.data.collections
    hub = C['HUB']
    hub.name = 'TOWER_OF_PETS_HUB'
    ex = bpy.data.collections.new('EXISTING_HUB')
    hub.children.link(ex)
    for name in ('TOWER_OF_PETS_SHOP', 'TOWER_OF_PETS_HATCHERY', 'Trading', 'Leaderboards', 'Upgrades', 'Spawn',
                 'Fountain', 'Plaza'):
        col = C[name]
        hub.children.unlink(col)
        ex.children.link(col)
    ent = C['TOWER_ENTRANCE']
    C['TOWER_OF_PETS'].children.unlink(ent)
    ex.children.link(ent)
    ent.name = 'Tower_Entrance'


def main(path=OUT):
    common.reset_scene()
    common.build_materials()
    foliage.build_foliage_materials()
    islands.build_island_materials()
    castle.build_castle_materials()
    shop.build_shop_materials()
    hatchery.build_hatchery_materials()
    clinic.build_clinic_materials()
    common.coll('TOWER_OF_PETS')
    for c in ('HUB', 'TOWER_ENTRANCE', 'TOWER_TEMPLATE', 'FLOATING_ISLANDS', 'WATERFALLS', 'ENVIRONMENT',
              'LIGHTING', 'CAMERAS'):
        common.coll(c, 'TOWER_OF_PETS')
    common.coll(common.ASSET_COLL)
    common.build_assets()
    foliage.build_foliage_assets(common.ASSET_COLL)
    islands.build_island_assets(common.ASSET_COLL)
    islands.build_variations()
    castle.build_castle_kit(common.ASSET_COLL)
    shop.build_shop_kit(common.ASSET_COLL)
    hatchery.build_hatchery_kit(common.ASSET_COLL)
    clinic.build_clinic_kit(common.ASSET_COLL)
    hub.build_hub()
    entrance.build_entrance()
    tower.build_tower()
    environment.build_environment()
    organize_hub()
    # keep the asset library out of the way (instances still render)
    vl = bpy.context.view_layer
    vl.layer_collection.children[common.ASSET_COLL].exclude = True
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.users_collection[0].name == common.ASSET_COLL]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    print(f'Tower of Pets lobby: {len(bpy.data.objects)} objects, {len(bpy.data.meshes)} unique meshes, '
          f'~{tris:,} triangles placed')
    print('Saved:', path)


if __name__ == '__main__':
    main()
