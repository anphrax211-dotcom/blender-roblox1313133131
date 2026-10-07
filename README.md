# Blender → Roblox egg models

## Wild eggs (`exports/*Egg.fbx`)
Explorer, Wild, RareWild, EpicWild, LegendaryWild — `blender/wild_eggs.py`, colours in `exports/wild_palette.json`.

## Boss eggs (`exports/*BossEgg.fbx`)
Rainhound, Magmaw, Crystaltusk, Granitram, Pyrocrow, Volcanox, Abyssray, Bogtoad, Elderstag.

Built to match the existing Celestial/Ember/Meadow eggs:
- Z-up, sits on z=0, 1.68 wide × 1.96 tall body on a 0.07 voxel grid
- emblem on the front (−Y)
- one mesh per colour, named `<Egg>_<Part>__<Egg>_<Colour>`; colours in `exports/boss_palette.json`

Regenerate (Blender 4+/5, or `pip install bpy`):
```
cd blender
python3 boss_eggs.py --out ../exports            # all eggs
python3 boss_eggs.py --only Magmaw --blend       # one egg, also save .blend
python3 render_previews.py ../exports ../previews
```
Or open `blender/boss_eggs.py` in Blender's Scripting tab and run it.

## Tower of Pets lobby (`blender/TowerOfPets_Lobby.blend`)
Full 3D lobby scene built from the Tower of Pets reference sheets: playable hub, tower entrance + portal,
and the exterior-only visual template of the 11-floor tower (no playable floors yet).
Generator: `blender/tower_of_pets/` (`common`, `hub`, `entrance`, `tower`, `environment`, `build`).

- 1 unit = 1 Roblox stud, Z up; spawn at (0, -58) facing +Y toward the entrance
- hub: plaza r=128, paw fountain/spawn platform, Pets / Shop / Eggs / Trading / Upgrades / Leaderboards
  on a ring facing the fountain (each building parented to a `<Name>_Root` empty — move the empty to move it)
- entrance: 20-step stairs to z=20, stepped pointed arch, portal surface (`Entrance_Portal`) and an invisible
  `Portal_TeleportTrigger` box for the Roblox teleport
- tower: foundation + Jungle … Divine, ~2,200 studs to the spire; trees, bushes, lanterns, clouds, crystals,
  islands and mountains are linked duplicates of `_ASSET_LIBRARY` meshes
- all trees and foliage come from the foliage pack below (far tower/island placements use the low LODs)
- cameras `CAM_1_MainPlayerView` … `CAM_6_HeroFullTower`; previews in `previews/TowerOfPets_CAM_*.png`

```
python3 blender/tower_of_pets/build.py                                   # rebuild the .blend
python3 blender/tower_of_pets/render.py blender/TowerOfPets_Lobby.blend previews 48 100
```

## Tower of Pets trees & foliage pack (`blender/TowerOfPets_Foliage.blend`)
Stylised low-poly Roblox foliage built from the tree & foliage reference sheet (`blender/tower_of_pets/foliage.py`).
Faceted warm-brown trunks forking into curved limbs, chunky roots, crowns of shingled broad leaves over a dark
core, hanging leaf-pair vines, lavender-grey block planters. Same meshes are instanced in the lobby.

| Asset | Tris | Asset | Tris |
|---|---|---|---|
| Tree_Large_High / _Low | 6,204 / 1,944 | Bush_01 / 02 / 03 | 380 / 852 / 344 |
| Tree_Medium_High / _Low | 2,964 / 1,060 | Ground_Plant_01 / 02 | 308 / 236 |
| Tree_Small / _Low | 2,736 / 1,060 | Vine_Short / Medium / Long | 64 / 124 / 204 |
| Tree_Tall_Thin / _Low | 2,002 / 710 | Stone_Planter (filled) / _Large / _Empty | 2,764 / 3,076 / 2,036 |

Parts: `Trunk_Thick/Thin`, `Branch_Curved/Small`, `Root_Set/Single`, `Leaf_Cluster_A/B/C/Low`, `Leaf_Single`,
`Planter_Wall_Block`, `Planter_Corner_Post`. Collections: `TOWER_OF_PETS_FOLIAGE / TREES, FOLIAGE,
TREE_PARTS (Trunks, Branches, Leaves, Roots, Vines), PLANTERS`.

```
python3 blender/tower_of_pets/build_foliage_pack.py     # prints per-asset triangle counts
```
