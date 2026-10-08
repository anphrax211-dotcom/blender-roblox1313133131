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
- hub: plaza r=128, paw fountain/spawn platform, Pet Clinic / Shop / Hatchery / Trading Plaza Portal / Pet Gym /
  Leaderboards monument
  on a ring facing the fountain (each building parented to a `<Name>_Root` empty — move the empty to move it)
- entrance: 20-step stairs to z=20, stepped pointed arch, portal surface (`Entrance_Portal`) and an invisible
  `Portal_TeleportTrigger` box for the Roblox teleport
- tower: foundation + Jungle … Divine, ~2,200 studs to the spire; trees, bushes, lanterns, clouds, crystals,
  islands and mountains are linked duplicates of `_ASSET_LIBRARY` meshes
- all trees and foliage come from the foliage pack below (far tower/island placements use the low LODs)
- cameras `CAM_1_MainPlayerView` … `CAM_6_HeroFullTower`; previews in `previews/TowerOfPets_CAM_*.png`

Roblox export: `exports/TowerOfPets/` holds one FBX per building/area (same world space, 1 unit = 1 stud),
plus `TowerOfPets_Materials.lua` and `TowerOfPets_Lights.lua`. See `exports/TowerOfPets/IMPORT.md` for the
Studio import steps.

```
python3 blender/tower_of_pets/build.py                                   # rebuild the .blend
python3 blender/tower_of_pets/export_fbx.py                              # rebuild exports/TowerOfPets/*.fbx
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

## Tower of Pets floating islands pack (`blender/TowerOfPets_Islands.blend`)
Stylised Roblox floating islands built from the floating-islands reference sheet (`blender/tower_of_pets/islands.py`).
Layered faceted cliff blocks (light/mid/dark warm grey) tapering to a point, bright grass caps overhanging the rim,
moss drapes and vines, cyan waterfalls, rope bridges, lanterns, crystals — trees come from the foliage pack.

| Asset | Tris | Notes |
|---|---|---|
| Large_Island / Medium_Island / Small_Island | 2.9k / 2.0k / 1.4k | grass radius ~40 / 24 / 12 studs, walkable tops |
| Tall_Island / Rock_Formation / Crystal_Island | 1.5k / 0.7k / 1.7k | vertical variation, background rock, crystal cliff |
| Waterfall_Small / _Medium / _Large / _Wide | 0.3k–0.7k | origin at the lip, flows toward -Y into the clouds |
| Bridge_Short / _Medium / _Long | ~1.2k–4k | 20 / 40 / 70 studs along +Y |
| Rock_*, Grass_Patch/Tuft, Moss_Drape_A/B, Lantern_Wood, Crystal_*, Stone_Block, Stone_Pillar, Paw_Banner, Wood_Fence | small | modular decoration |

Variations `Island_A` … `Island_H` (collections; place with *Add > Collection Instance*): A large tree + waterfall +
bridge, B small trees + lantern, C crystals + waterfall, D tall + vines, E open grassy platform, F rock-only,
G big waterfall, H bridge connector. The lobby places them around the tower and hub the same way.

```
python3 blender/tower_of_pets/build_islands_pack.py
```

## Castle base / lower tower (in `blender/TowerOfPets_Lobby.blend`)
The main entrance rebuilt from the castle-base reference with real masonry (`blender/tower_of_pets/castle.py`):
walls are courses of individually chamfered blocks in running bond over a dark core, so the seams are true
recessed grooves; corners have quoins, arches are rings of voussoirs with keystones, pillars are stacked from
base / block shaft / gold band / capital / cap, and cornices, gold trim, balustrades, steps and flagstones are
separate bevelled pieces.

- gatehouse: stepped pointed arch (3 voussoir rings + 2 gold rings + glow rim) around the recessed portal,
  banner pillars, pediment with navy panel + gold paw + crown, pinnacles, windowed wings, cat statues
- block-built stairs with stepped cheek walls, newel posts, lanterns, topiary planters, flagstone landing
- tower-base front faces in masonry with voussoir windows, upper gate + balcony, two-tier arcades with
  banners, balustrades and waterfall spouts, masonry paw fountain with a flame finial
- modular kit in `_ASSET_LIBRARY/CASTLE_KIT`: `Stone_Block_Small/Medium/Large`, `Wall_Straight`, `Wall_Corner`,
  `Wall_Trim`, `Pillar_Base/Main/Top`, `Arch_Small/Large`, `Decorative_Trim`, `Gold_Trim`, `Stair_Straight`,
  `Balcony`, `Ledge`, `Banner`, `Castle_Lantern`, `Balustrade`, `Cat_Statue`, `Topiary_Cone`
  (the library collection is excluded from the view layer - enable it to see the masters at the origin)
- cameras: `CAM_7_Castle_Reference`, `CAM_8_Castle_Front`, `CAM_9_Castle_Close`, `CAM_10_Castle_Side`,
  `CAM_11_Castle_Player`
- each wall section is its own mesh (mostly < 20k triangles) so it can be imported into Roblox as MeshParts

## Tower of Pets shop (`blender/TowerOfPets_Shop.blend`, also placed in the lobby)
The hub shop rebuilt from the shop reference in the castle masonry language (`blender/tower_of_pets/shop.py`).
Wide stone building with an open front between dark stone pillars (wall lanterns), red lintel over a
segmental voussoir arch, raised arched gable carrying the big gold-framed SHOP sign with the cart icon and
gold scrolls, curved red gable roof with tile courses and gold fascia, masonry wings with red plank panels,
red paw banners and lantern pillars, lean-to red roofs; back wall with an arched door, barrels, crates, vines.
Interior: plank floor, panelled walls, red back panel with a glowing cart, six stocked shelves, curved
counter with a gold paw (room behind it for an NPC), red runner + round paw rug, beams, hanging lanterns.

- collections: `TOWER_OF_PETS_SHOP / BUILDING (Walls, Pillars, Arches, Trim, Roof), SIGNAGE (Main_Shop_Sign,
  Small_Shop_Signs), BANNERS, INTERIOR (Counter, Shelves, Carpet, Decorations), SHOP_ITEMS, LIGHTING (shop),
  LANDSCAPING`; everything is parented to `Shop_Root` (move that to move the shop)
- kit (`SHOP_KIT`): `Shop_Stone_Block`, `Shop_Stone_Wall`, `Shop_Stone_Corner`, `Shop_Stone_Pillar`,
  `Shop_Stone_Arch`, `Shop_Red_Wall_Panel`, `Shop_Roof_Piece`, `Shop_Gold_Trim`, `Shop_Sign`, `Shop_Banner`,
  `Shop_Lantern`, `Shop_Lantern_Wall`, `Shop_Counter`, `Shop_Shelf`, `Shop_Crate`, `Shop_Chest`,
  `Shop_Gift_Box(_Blue)`, `Shop_Potion_Pink/Blue/Green/Purple`, `Shop_Pet_Item`, `Shop_Pet_Food`, `Shop_Barrel`,
  `Shop_Carpet`, `Shop_Planter` ("Shop_" prefix because castle/island assets already use some plain names)
- cameras: `CAM_Shop_Front` (reference perspective), `_Interior`, `_Side`, `_Rear`, `_Player`; in the lobby
  `CAM_12_Shop_Front`
- scale: entrance ~21 x 16 studs, counter 3.4 studs high, 4+ stud walkways; ~100k triangles with landscaping

```
python3 blender/tower_of_pets/build_shop_pack.py
```

## Tower of Pets hatchery / eggs (`blender/TowerOfPets_Hatchery.blend`, also placed in the lobby)
The Eggs building rebuilt from the hatchery reference (`blender/tower_of_pets/hatchery.py`), in the castle
masonry language: block-built facade with corner quoins and a deep round arch (outer voussoirs, gold ring,
recessed purple inner arch), gold-framed purple band with the glowing EGGS lettering, raised purple parapet with
the egg emblem (glowing egg + paw in a stone/gold frame, fan of purple crystals), banner pillars with lanterns,
purple-panelled wings with lean-to purple roofs and lantern pillars, crystal planters; back wall with a raised
purple panel and two egg emblems. Interior: octagonal hall under a ribbed dome with a glowing oculus, arched niche
shelves of eggs, central tiered hatchery platform with the floating glowing egg, magic rings and sparkles,
crystal pedestals, egg pedestals, display stands, purple runner + paw medallion, bracket lanterns, banners.

- eggs: `Egg_Blue`, `Egg_Cyan`, `Egg_Pink`, `Egg_Purple`, `Egg_Gold`, `Egg_Green`, `Egg_Fire`, `Egg_Ice`,
  `Egg_Crystal`, `Egg_Dark` (one collection each under `EGGS`)
- kit (`HATCHERY_KIT`, "Hatch_" prefix): `Hatch_Stone_Block/Wall/Corner/Pillar/Arch`, `Hatch_Purple_Wall`,
  `Hatch_Roof_Piece`, `Hatch_Gold_Trim`, `Hatch_Egg_Sign`, `Hatch_Egg_Emblem`, `Hatch_Purple_Banner`,
  `Hatch_Crystal(_Cluster_Purple/_Blue)`, `Hatch_Lantern`, `Hatch_Egg_Pedestal_S/M/L`, `Hatch_Egg_Display`,
  `Hatch_Central_Hatchery_Platform`, `Hatch_Big_Egg`, `Hatch_Interior_Shelf`, `Hatch_Decorative_Paw`, `Hatch_Planter`
- collections: `TOWER_OF_PETS_HATCHERY / BUILDING (Walls, Pillars, Arches, Roof, Gold_Trim), SIGNAGE (Eggs_Sign,
  Egg_Emblem), BANNERS, INTERIOR (Central_Platform, Shelves, Pedestals, Decorations), EGGS, CRYSTALS, LANTERNS,
  LANDSCAPING, LIGHTING` - in the lobby, names already used by the shop/tower get a " (hatchery)" suffix
- cameras: `CAM_Hatchery_Front/_Interior/_Side/_Rear/_Player`; lobby `CAM_13_Hatchery_Front`
- scale: arch opening 13 x 17.5 studs, hall 30 studs across, ~108k triangles with landscaping

```
python3 blender/tower_of_pets/build_hatchery_pack.py
```

## Tower of Pets pet clinic (`blender/TowerOfPets_PetClinic.blend`, replaces the old Pets area in the lobby)
The old Pets building, its sign, props and green colours are gone; the Pet Clinic (`blender/tower_of_pets/clinic.py`)
stands on the same hub slot (135 deg, facing the fountain). Light masonry facade with a wide segmental voussoir arch
(gold ring, blue soffit), blue "PET CLINIC" sign band with gold frame and teal glow ends, round-topped stone frame
holding the glowing paw + medical-cross emblem, two banner pillars with lanterns, two pet statues with teal
bandanas, blue-flower planters, blue lean-to and gable roofs with gold fascia; back wall with a big paw-cross emblem.
Interior: stone floor, blue rug + paw medallion, curved reception desk (dark wood, blue panels, gold trim, emblem,
room for an NPC) with supply shelves and a glowing paw-cross panel behind it, waiting benches + plants + info
screen, treatment area (exam table, stool, monitor, IV stand, pet carrier, first-aid kit, info screen), bowls,
balls, bones, banners, lanterns.

- kit (`PETCLINIC_KIT`): `PetClinic_Wall`, `_Pillar`, `_Arch`, `_Roof`, `_GoldTrim`, `_Sign`, `_Emblem`, `_Banner`,
  `_Lantern`, `_Statue`, `_Reception`, `_TreatmentTable`, `_Stool`, `_Monitor`, `_MedicalStand`, `_PetCarrier`,
  `_FirstAid`, `_Shelf`, `_Bottle(_Blue)`, `_Bench`, `_InfoScreen`, `_PottedPlant`, `_FoodBowl`, `_Ball`, `_Bone`,
  `_Decorations`, `_Planter`
- lobby outliner: `TOWER_OF_PETS / TOWER_OF_PETS_HUB / PET_CLINIC (Exterior, Interior, Roof, Signage, Banners,
  Statues, Reception, Treatment, Decorations, Lighting)` and `EXISTING_HUB (TOWER_OF_PETS_SHOP,
  TOWER_OF_PETS_HATCHERY, Spawn, Fountain, Plaza, Tower_Entrance)`; the tower,
  islands, waterfalls, environment, lighting and cameras stay beside it under `TOWER_OF_PETS`
- cameras: `CAM_PetClinic_Front/_Interior/_Side/_Rear/_Player`; lobby `CAM_14_PetClinic_Front`
- scale: entrance 20 studs wide, desk 3.4 studs, exam table 3 studs; ~93k triangles with landscaping

```
python3 blender/tower_of_pets/build_clinic_pack.py
```

## Tower of Pets pet gym (`blender/TowerOfPets_PetGym.blend`, replaces the old Upgrades area in the lobby)
The old Upgrades building (arch gateway, glowing up arrow, upgrade platform, crystals, UPGRADES sign and its blue
materials) is gone; the Pet Gym (`blender/tower_of_pets/gym.py`) stands on the same hub slot (315 deg, facing the
fountain). Blue + gold training theme in the hub's masonry: deep round voussoir arch (gold ring, dark-blue inner
ring), "TRAIN • LEVEL • GET STRONGER" slogan band, gold-framed white-on-navy "PET GYM" sign, raised blue parapet
with the paw + barbell emblem, banner pillars with lanterns, blue banners with gold paws, two mascot dog statues
(red headbands, blue wristbands, dumbbell) on masonry pedestals, blue gable and lean-to roofs with gold fascia,
planters and vines; back wall with a big paw + barbell emblem.
Interior: wooden plank floor, circular dark-blue training floor (gold rings, glowing ticks, gold paw), dumbbell
racks, plate stacks, bench presses with barbells, punching bags on a frame, pull-up bar, wooden training post,
padded dummy, agility hurdles, stepped jump platforms, pet running wheel, paw targets, trophy shelf + trophies,
crates, banners, wall and ceiling lanterns.

- kit (`PETGYM_KIT`): `PetGym_Wall`, `_Pillar`, `_Arch`, `_Roof`, `_GoldTrim`, `_Sign`, `_Emblem`, `_Banner`,
  `_PetStatue`, `_Dumbbell`, `_Barbell`, `_Weight`, `_WeightRack`, `_Bench`, `_TrainingBag`, `_BagFrame`,
  `_PullUpBar`, `_TrainingPost`, `_Hurdle`, `_Platform`, `_RunningWheel`, `_Dummy`, `_PawTarget`, `_Trophy`,
  `_TrophyShelf`, `_CentralFloor`, `_Lantern`, `_Planter`
- outliner: `TOWER_OF_PETS_PET_GYM / BUILDING (Walls, Pillars, Arches, Roof, Gold_Trim), SIGNAGE (Pet_Gym,
  Training_Slogan, Paw_Barbell), BANNERS, STATUES, TRAINING_EQUIPMENT (Weights, Barbells, Dumbbells, Benches, Bags,
  Training_Posts, Agility), INTERIOR, TROPHIES, LANDSCAPING, LIGHTING`; in the lobby it sits under
  `TOWER_OF_PETS_HUB` next to `PET_CLINIC` (names already used elsewhere in the lobby get a ` (gym)` suffix)
- cameras: `CAM_PetGym_Front/_Interior/_Side/_Rear/_Player`; lobby `CAM_15_PetGym_Front`
- scale: entrance 14 studs wide, central training floor 15 studs across, bench 4.4 studs; ~100k triangles with
  landscaping, every mesh under Roblox's 20k-triangle limit

```
python3 blender/tower_of_pets/build_gym_pack.py
```

## Tower of Pets trading plaza portal (`blender/TowerOfPets_TradingPortal.blend`, replaces the old Trading building)
The old Trading pavilion (gold roof, booths, handshake plaque, TRADING sign and its gold/navy board materials) is
gone; the Trading Plaza Portal (`blender/tower_of_pets/trading.py`) stands on the same hub slot (180 deg, facing the
fountain). It is only the gateway: walking through `TradingPortal_TeleportTrigger` (invisible, not rendered) is
where the Roblox teleport to the separate Trading Plaza place goes - the plaza itself is not built here.
Masonry central block with a deep layered round arch (stone voussoirs front and back, gold ring, purple-stone
chamber lining, inner recessed arch), raised round-topped crest with the glowing trading emblem (cat + dog
silhouettes under circular trade arrows), purple "TRADING PLAZA" sign with gold frame and a navy "TRADE WITH OTHER
PLAYERS" ribbon, tall pillars and outer pillars with lanterns, crenellated side walls with navy gold-paw banners,
a cat and a dog statue on paw pedestals holding glowing trade cubes toward each other, a paved forecourt with
purple bands and the circular trading floor symbol, path lanterns, planters, purple crystals, trees and vines.

- portal effect pieces (separate objects, ready to animate in Roblox): `PORTAL/Core` (`TradingPortal_Core` vortex
  surface + the trigger), `PORTAL/Rings` (`TradingPortal_EnergyRing_0..2`, origin at the portal centre - spin them
  about local Y), `PORTAL/Energy` (swirl arms + glowing trade icon, origin at the centre), `PORTAL/Particles`
- kit (`TRADINGPORTAL_KIT`): `TradingPortal_Wall`, `_Pillar`, `_Arch`, `_Roof`, `_GoldTrim`, `_Sign`, `_Banner`,
  `_Statue` (cat), `_Statue_Dog`, `_Pedestal`, `_Core`, `_EnergyRing`, `_Particles`, `_Lantern`, `_Floor`,
  `_TradingSymbol`, `_Crystal`
- outliner: `TOWER_OF_PETS_TRADING_PORTAL / ARCHITECTURE (Walls, Pillars, Arch, Trim, Roof), SIGNAGE (Trading_Plaza,
  Trade_With_Other_Players), PORTAL (Core, Rings, Energy, Particles), STATUES (Pet_Left, Pet_Right), BANNERS,
  LANTERNS, FLOOR, LANDSCAPING, LIGHTING` (names already used in the lobby get a ` (trading)` suffix)
- cameras: `CAM_TradingPortal_Front/_Close/_Side/_Back/_Top/_Player`; lobby `CAM_16_TradingPortal_Front`
- scale: walk-through opening 14.8 studs wide x 19.4 high, statues ~10 studs on 6.8-stud pedestals; ~100k triangles

```
python3 blender/tower_of_pets/build_trading_pack.py
```

## Tower of Pets leaderboards monument (`blender/TowerOfPets_Leaderboards.blend`, replaces the old Leaderboards)
The old three-board stand (plinth, trophy, LEADERBOARDS board) is gone; the Leaderboards monument
(`blender/tower_of_pets/leaderboard.py`) stands on the same hub slot (225 deg, facing the fountain). It is an
open-air monument - no roof, no interior. Masonry foundation with three shallow steps, carved back wall, three
arched navy boards with gold frames and stone voussoir surrounds: TOP PET POWER (crossed swords), TOP PET
COLLECTORS (paw), TOP ROBUX SPENT (Robux hexagon), each with a title band, subtitle and ranks #1-#10 (avatar disc,
name, value). Above them a navy "SEE THE STRONGEST • TOP COLLECTORS • TOP SUPPORTERS" ribbon, the gold-framed
"LEADERBOARDS" sign and a gold crown on a raised arched crest; tall pillars with navy crown + paw banners and
lanterns, small lanterns and topiary planters between the boards, two crowned guardian cats (navy bandanas with
gold paws) facing the centre from pedestals with glowing paw panels, and a navy/gold paw medallion in the forecourt.

- Roblox: each board's screen is its own part (`Leaderboard_1_Screen` ... `_3_Screen`) for a SurfaceGui; the
  ranked rows are placeholder 3D text in `BOARDS/<board>/Placeholder_Entries_<n>` - delete them once the live
  boards are wired up
- kit (`LEADERBOARD_KIT`): `Leaderboard_Wall`, `_Pillar`, `_Arch`, `_Board`, `_Screen`, `_Sign`, `_Crown`, `_Banner`,
  `_CatStatue`, `_Pedestal`, `_Lantern`, `_Step`, `_FloorEmblem`, `_Planter`, `_Emblem_Swords`, `_Emblem_Paw`,
  `_Emblem_Robux`
- outliner: `TOWER_OF_PETS_LEADERBOARDS / MONUMENT (Foundation, Steps, Walls, Pillars, Arches, Gold_Trim), SIGNAGE
  (Leaderboards_Title, Leaderboards_Subtitle, Crown), BOARDS (Top_Pet_Power, Top_Pet_Collectors, Top_Robux_Spent),
  STATUES, BANNERS, LANTERNS, FLOOR, LANDSCAPING, LIGHTING` (` (leaderboards)` suffix where a name is taken)
- cameras: `CAM_Leaderboards_Front/_Boards/_Side/_Player/_Top`; lobby `CAM_17_Leaderboards_Front`
- scale: boards 14 studs wide, ~24 studs tall; steps 0.75 studs each; ~133k triangles with landscaping

```
python3 blender/tower_of_pets/build_leaderboards_pack.py
```

## Tower of Pets Floor 1: The Verdant Kingdom, greybox layout (`blender/TowerOfPets_Floor1.blend`)
Base terrain only, traced 1:1 from the Floor 1 map sheet (`blender/tower_of_pets/floor1.py`):
- **How it's traced:** every area's top surface is a polygon drawn over the sheet in pixels. One uniform scale
  (1.1 studs per pixel, north = +Y) keeps the sheet's proportions, about 1,600 × 1,100 studs of islands.
  `previews/TowerOfPets_F1_Trace_Overlay.png` shows the traced outlines (magenta), lakes (cyan) and paths (yellow)
  on top of the sheet.
- **Islands:** areas that touch form one island, with cliffs where heights differ, matching the sheet:
  - **the central island:** Ancient Ruins + Emerald Lake + World Tree, with Cloudridge Peaks on its north-west
    and the dark Beast Cave / Jungle Fortress mass fused to its east shore;
  - **the west continent:** Whispering Forest above Sunlit Meadows, Verdant Village and the Floor Entrance;
  - **separate islands:** Riverfall Valley, Mossy Caverns, Lotus Swamp and the Sky Temple, plus secret and
    decorative islets.
- **Heights:** exaggerated 1.3× for verticality, from the Lotus Swamp at about −5 to the Cloudridge summit at
  about 315.
- **Terrain:** deep rock undersides over a cloud sea, rivers, lakes and ponds where the sheet has them,
  waterfalls (into lower ground or into the clouds), a cavern hill, crags, fortress rim spires and peaks.
- **Not built yet:** buildings, trees, decorations and detailed assets.

- **Five biomes** (`TERRAIN/<BIOME>`), with one `_Top` / `_Cliffs` / `_Underside` mesh per area so each island can be
  refined on its own:
  - VERDANT_FOREST (Floor Entrance, Sunlit Meadows, Verdant Village, Whispering Forest)
  - WATERFALL_VALLEY (Riverfall Valley, Emerald Lake, Lotus Swamp)
  - ANCIENT_RUINS (Ancient Ruins, Cloudridge Peaks)
  - MYSTIC_WILDS (World Tree Grove, Mossy Caverns, Beast Cave)
  - JUNGLE_FORTRESS (the biggest and highest plateau, plus the Sky Temple)
  - Plus secret and decorative islets.
- **Path network:** 25 routes following the sheet's roads, 22–32 studs wide (12 for secret paths) and rideable.
  Most ramps are under 28°; the steepest climbs (Beast Climb, Sky Stair) are about 30°.
  Routes branch and loop, with shortcuts (Cloudridge Stair, West Cliff Trail, Lake Loop, Mossy–Swamp Descent,
  two routes into the fortress). Where a path crosses the void it becomes a natural rock bridge (`TERRAIN/NATURAL_BRIDGES`).
  Fortress approaches are carved canyon ramps.
- **Landmark blockouts:**
  - floor-entrance spawn ring on a large flat platform
  - 6 checkpoints, 3 mini-boss arenas, the main boss arena
  - 7 cave mouths, 6 world-egg pads, secret-area markers
  - flat pads reserved for the village, ruins plaza, World Tree, Sky Temple and fortress
- `GUIDES`: map labels (area plus level range, shown only on `CAM_F1_Map_TopDown`), reserved-footprint outlines
  and 5-stud scale figures. These are not exported.
- **Cameras:** `CAM_F1_Map_TopDown` (orthographic, matches the sheet), `_Overview`, `_Entrance_Player`,
  `_Valley_View`, `_Fortress_View`, `_Side_Elevation`.
- **Roblox:** `exports/TowerOfPets/Floor1/` holds one FBX per biome plus bridges, water, blockouts and clouds.
  Terrain chunks are 6k triangles or fewer, and `Floor1_Materials.lua` sets exact collision on the terrain.
  `floor1_layout.json` has every spawn, checkpoint, boss, egg, cave and path waypoint in Roblox coordinates.
  See `IMPORT.md` there.

```
python3 blender/tower_of_pets/build_floor1_pack.py      # terrain .blend + floor1_layout.json
python3 blender/tower_of_pets/build_floor1_export.py    # exports/TowerOfPets/Floor1/*.fbx
```

## Fire pets: Ashrat, Cinderkit, Flarecat, Smoulderat (`blender/FirePets.blend`)
Four stylised pets modelled to match the fire-pet turnaround sheet (`blender/fire_pets.py`). Proportions come
from the sheet's front, side and back views on one shared scale (Ashrat is about 1 m tall to the ear tips), so
the four keep the sheet's relative sizes. The tail silhouettes are traced from the sheet's side views.

| Pet | Look | Fire features (objects) |
|---|---|---|
| Ashrat | charcoal rat, big cupped orange-lined ears, orange paws and nose, buck teeth | `_Tail` (curled flame), `_CheekSwirls` (glowing swirls at the eyes), `_FlameMarkings` |
| Cinderkit | soot-black kitten, cheek fluff, amber paws, open smile | `_FlameTuft` (forehead crest), `_FaceFlames`, `_ChestRuff`, `_Tail` (layered flame), `_FlameMarkings` incl. flame "socks" |
| Flarecat | peach-gold cat, pink inner ears, orange paws, flush eyes | `_FlameMane` (broad leaf flames: crest, cheek flares, neck mane, lotus over the back of the head), `_ChestRuff` (two layers of leaves), `_Tail`, pale `_FlameMarkings` |
| Smoulderat | stout dome-backed charcoal rat, red paws | `_HeadCrystals` + `_BackCrystals`, `_LavaFissures` (cracked-rock network), `_Tail` (curled flame) |

- **Coordinates:** 1 unit = 1 m, Z up. Each pet faces −Y and stands on z = 0. Left to right: Ashrat x=−3.9,
  Cinderkit −1.3, Flarecat 1.3, Smoulderat 3.9.
- **How it's built:**
  - Heads and bodies are seamless smooth shells. Overlapping volumes are voxel-remeshed, smoothed and
    decimated.
  - Tails are layered "inflated" flames: a yellow shell with orange and red inner flames.
  - Markings, swirls and lava cracks are thin decals wrapped onto the surface.
  - Fire colours are red → orange → yellow gradients stored in the `Col` colour attribute (`Fire_Gradient`
    material). They are slightly emissive.
- **`PETS/<Pet>`:** one collection per pet. Every part is a separate editable mesh (`<Pet>_Body`, `_Head`,
  `_Ear_L/R`, `_Leg_FL/FR/BL/BR`, `_Paw_*`, `_Tail`, `_Eye_L/R`, `_Nose`, `_Mouth`, `_Teeth`, `_Whiskers`, plus
  the fire objects above), all parented to `<Pet>_Root`. Move the empty to move the pet. L/R are the pet's own
  sides (left = +X). Ashrat, Cinderkit and Smoulderat are about 32–38k triangles. Flarecat is built in a light
  game-budget format (`LOW` in `fire_pets.py`), about 22k triangles. Its eyes are thin shells wrapped onto the head,
  so they sit flush with the face (`eyes(..., flush=True)`).
- **`STUDIO`:** five soft area lights and a neutral grey world. The ground plane is a shadow catcher, so renders
  show an even grey backdrop with soft contact shadows.
- **`CAMERAS`:** orthographic `CAM_<Pet>_Front`, `_Side` and `_Back` cameras, all at the same scale and tilted
  5° down like the sheet. The side camera looks from +X, so the head is on the left as on the sheet, and it
  clips out the neighbouring pets. There are also two overview cameras: `CAM_Overview_ThreeQuarter` and
  `CAM_Lineup_Front`.
- **`LABELS`:** pet names and FRONT / SIDE / BACK markers on the ground. They show in the viewport only, not in
  renders.
- **Previews:** `previews/FirePets_Turnaround.png` is laid out like the reference sheet. Also
  `FirePets_<Pet>_<View>.png`, `FirePets_Overview_ThreeQuarter.png` and `FirePets_Lineup_Front.png`.

- **Roblox:** `exports/FirePets/<Pet>.fbx` has three MeshParts, `<Pet>_Body`, `<Pet>_Head` and `<Pet>_Fire`,
  each under 20k triangles and sharing one
  1024² colour texture that is baked from the materials and embedded. The pet faces −Z, Y is up, the pivot is at
  the feet, and the scale is 3 studs per metre. See `exports/FirePets/IMPORT.md`.

```
python3 blender/fire_pets.py                          # rebuild blender/FirePets.blend
python3 blender/fire_pets.py --render previews        # also render every turnaround camera + the sheet
python3 blender/export_fire_pets.py                   # rebuild exports/FirePets/*.fbx + textures
```

## Water pets: Bogtoad, Bubbletoad, Puddlepup, Rainhound (`blender/WaterPets.blend`)
Four Common water-type pets from the water-pet turnaround sheet (`blender/water_pets.py`). They're built in the
same style and pipeline as the fire pets, reusing `fire_pets.py`'s helpers, on the same shared scale. All four
use the light game-budget format (about 19–27k triangles each), and every eye is flush with the head.

| Pet | Look | Parts beyond the usual body / head / legs / paws / eyes |
|---|---|---|
| Bogtoad | squat olive-green toad, cream belly, amber eyes, wide open smile, brown toes | `_Belly`, `_Spots`, `_Cheeks`, `_Moss` (puffy clover clumps on the head and spine), `_Nostrils`, `_Mouth` |
| Bubbletoad | round teal toad, pale aqua belly, indigo eyes, webbed cyan feet | `_Belly`, `_Spots` (cyan bubble spots), `_Bubbles` (clear glossy bubbles on the head and down the back) |
| Puddlepup | chunky blue puppy, navy floppy ears, pale muzzle and chest fluff, tongue out | `_Muzzle`, `_ChestFluff`, `_WaterTopknot`, `_Tail` (clear water curl with a droplet), `_Spots` |
| Rainhound | taller dark-blue dog, long ears fading to aqua tips | `_Muzzle`, `_CloudTuft`, `_ChestFluff` (cloud puffs), `_Tail` (cloud swirl, blue inside → white outside), `_RainDrops` (aqua teardrops on body, legs and ears) |

- **Layout:** left to right, Bogtoad x=−3.9, Bubbletoad −1.3, Puddlepup 1.3, Rainhound 3.9. Each faces −Y on
  z = 0.
- **Collections:** one per pet under `PETS`, with every part a separate editable mesh parented to `<Pet>_Root`.
  `STUDIO`, `CAMERAS` (`CAM_<Pet>_Front/_Side/_Back`, orthographic) and `LABELS` work like the fire pets.
- **Previews:** `previews/WaterPets_Turnaround.png`, `WaterPets_<Pet>_<View>.png`,
  `WaterPets_Overview_ThreeQuarter.png` and `WaterPets_Lineup_Front.png`.

```
python3 blender/water_pets.py                        # rebuild blender/WaterPets.blend
python3 blender/water_pets.py --render previews      # also render every turnaround camera + the sheet
```
