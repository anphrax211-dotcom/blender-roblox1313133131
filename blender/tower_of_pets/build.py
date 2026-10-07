"""TOWER OF PETS - lobby build (Blender 4.2+/5.x, or the `bpy` pip module).

Builds the playable hub/lobby, the tower entrance + portal, and the exterior-only visual template
of the giant tower, then saves TowerOfPets_Lobby.blend next to the blender/ folder.

    blender -b -P blender/tower_of_pets/build.py
    python3 blender/tower_of_pets/build.py               (with `pip install bpy`)
    (or open build.py in Blender's Scripting tab and press Run Script)

Units: 1 Blender unit = 1 Roblox stud, Z up. The spawn faces +Y toward the tower entrance.
Collections:
    TOWER_OF_PETS / HUB (Plaza, Spawn, Fountain, Shop, Pets, Eggs, Trading, Upgrades, Leaderboards)
                  / TOWER_ENTRANCE
                  / TOWER_TEMPLATE (Hub_Base, Jungle ... Divine)
                  / FLOATING_ISLANDS / WATERFALLS / ENVIRONMENT / LIGHTING / CAMERAS
    _ASSET_LIBRARY (excluded) - source meshes for every linked-duplicate tree, bush, lantern,
                                planter, rock, cloud, crystal, island and mountain
"""
import os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
import common, hub, entrance, tower, environment
for m in (common, hub, entrance, tower, environment):        # re-running inside Blender picks up edits
    importlib.reload(m)

OUT = os.path.join(os.path.dirname(HERE), 'TowerOfPets_Lobby.blend')


def main(path=OUT):
    common.reset_scene()
    common.build_materials()
    common.coll('TOWER_OF_PETS')
    for c in ('HUB', 'TOWER_ENTRANCE', 'TOWER_TEMPLATE', 'FLOATING_ISLANDS', 'WATERFALLS', 'ENVIRONMENT',
              'LIGHTING', 'CAMERAS'):
        common.coll(c, 'TOWER_OF_PETS')
    common.coll(common.ASSET_COLL)
    common.build_assets()
    hub.build_hub()
    entrance.build_entrance()
    tower.build_tower()
    environment.build_environment()
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
