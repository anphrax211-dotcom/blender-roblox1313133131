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

## Tower of Pets Floor 1: The Verdant Kingdom (`blender/TowerOfPets_Floor1.blend`)
Floor 1 with its global environment detail pass: every biome is at a 60–70% baseline, ready for per-biome passes.
The terrain comes from `blender/tower_of_pets/floor1.py`, the environment dressing from `floor1_detail.py`, and the
Roblox scatter and lighting scripts from `floor1_roblox.py`.

**Layout and scale**
- **Placement:** every area is a polygon traced over the map sheet (`previews/TowerOfPets_F1_Trace_Overlay.png`),
  scaled 10× (`WORLD = 10`) to about 17,400 × 11,600 studs. These stay at player scale:
  - path widths (main 56, trails 40, hidden 20);
  - markers, and checkpoint and mini-boss pads;
  - climbs, at 25° or less.
- **Heights:** region base heights are flattened by `LEVEL = 0.5`, so the islands sit closer in height. They run
  from about −120 (Lotus Swamp) to 1,200 (Fortress Heights). Peaks, crags and spires keep 75% of their height
  (`FEATURE_LEVEL`), with the Cloudridge summit at about 2,650. Inside a landmass, neighbours within 460 studs of
  each other slope into each other and can be ridden; larger differences become cliffs.
- **Four landmasses:** inside a landmass the regions are merged; between landmasses there's a channel of open sky,
  roughly 300–620 studs wide. Change `LANDMASS` to join or split regions.
  - **Verdant mainland:** Floor Entrance, Sunlit Meadows, Verdant Village and Whispering Forest.
  - **Central highlands:** Ancient Ruins, Cloudridge Peaks, World Tree Grove, Emerald Lake, Riverfall Valley and
    Mossy Caverns.
  - **Lotus Swamp.**
  - **Jungle Fortress:** the jungle ring, Fortress Heights and Beast Cave.

  The Sky Temple, four secret isles and two optional islets (treasure, rare pet) float on their own.
- **Paths:** 28 organic routes (12 main, 11 secondary, 5 hidden). They follow the ground with a grade limit, cutting
  canyons or raising causeways where they must.

**Detail pass**
- **Terrain:** subtle small-scale relief (hummocks, dips, shelves) on every area, and exposed rock on steeper
  hillsides.
  - Cliff walls are cut into roughly 60-stud strata bands. Each band juts out or steps back and alternates rock
    tones, giving layered, irregular cliffs.
  - Undersides are rougher and banded, and decimated to 20% with their rims kept exact.
- **Vegetation:** about 4,500 trees from the hub's own foliage pack (`Tree_*_Low`), scaled 2–6×. Mystic Wilds uses a
  darker re-colour of the same meshes (`*_Mystic`). There are also about 13,500 bushes, plants, ferns, flowers,
  grass and mushrooms. Densities are set per area (`DRESS` in `floor1_detail.py`); noise makes groves and clearings.
  - Kept clear: roads (with a wide margin for riders), pads, reserved footprints, water, steep ground and island rims.
- **Water:** smoother rivers, river-bank rocks, reeds along shores and banks, and lily pads on the ponds (dense in
  the swamp, which also has mud banks). Waterfalls that land on ground get mist, foam and rocks. About 16 small
  cascades spill over island rims.
- **Paths:** dirt colour variation, with stone sections in the ruins, fortress, entrance and village. There are
  pebbles along the edges, lanterns along the main roads, signposts at junctions, benches at checkpoints, and
  fences or rope barriers near the entrance and village.
- **Bridges:** 11 built bridges where paths cross open sky (`Floor1_Bridges.fbx`), all in one style family:
  - wood truss bridges with railings, stringers and keel braces;
  - stone bridges with parapets and corbels;
  - rope-railed plank bridges on the hidden paths.

  All have stone abutments and lanterns at both ends. The Sky Stair, the Fortress Grand Ramp and the Cloud Perch
  path stay natural rock spans.
- **Landmark hints:**
  - **World Tree:** a hub-style trunk and limbs, a canopy of about 40 giant hub leaf clusters, and giant roots.
  - **Jungle Fortress:** a silhouette of curtain walls, corner towers with red roofs, and a stepped keep with glowing
    windows.
  - **Ruins:** broken columns and walls, ruin arches and fragments.
  - **Cloudridge:** boulders, alpine trees and snow patches.
  - **Sky Temple:** temple platforms, columns, floating rocks and clouds.
  - **Swamp:** reeds and lily pads.
  - **Mystic Wilds:** glowing mushrooms.
- **Cliffs and background:**
  - moss drapes, vines and roots on island rims and inner cliffs, with boulders set into the walls;
  - floating debris below the islands;
  - 34 distant islands with trees and waterfalls;
  - mountain spires rising from the cloud sea;
  - cloud banks.
- **Lighting:** warm, soft sun with light haze in the previews. `Floor1_Lighting.lua` sets ShadowMap, Atmosphere,
  Bloom, ColorCorrection and Terrain clouds in Roblox.
- **Old or wrong assets:** none. Floor 1 is generated from scratch and contains no hub buildings or training props.
  Its only placeholder geometry (the greybox fortress boxes and the ico-sphere tree canopy) was replaced.

**Floor 1 entrance** (`floor1_entrance.py`, `Floor1_Entrance.fbx`)

The entrance is built into the south-west of the Verdant mainland, where the map puts it: same landmass, no gap.

- **Terrain** (shaped in `floor1.py`):
  - a flat plaza pad at the spawn and a portal pad cut into a new rocky, tree-topped ridge;
  - small knolls;
  - a spring pool with a shallow meandering brook that drops off the west cliff as a small waterfall.
- **Portal:** hub masonry (`castle.py` helpers): chamfered block courses, a voussoir arch with a gold inner ring
  and glowing runes, banded pillars with gold trim, a stone pediment with the gold-framed Verdant leaf medallion,
  and wing walls.
  - Green Verdant leaf banners, vines and moss.
  - A swirling cyan portal: dark blue rim, cyan layers, spiral arms, a bright core and sparkles.
  - `Floor1_Portal_TeleportTrigger`, an invisible touch box inside the portal for the return-to-hub teleport.
  - It stands on a dais with a 56-stud-wide staircase (10 shallow steps, stepped cheek walls, newels).
- **Plaza:** about 100 studs across, centred on the spawn. Flagstone rings with gold inlays surround the Verdant
  emblem. A low stone border is open toward the stairs, the forest road and the hidden brook path.
- **Road:** paved stone pavers with curb stones leave the plaza and thin out into the dirt forest trail over about
  600 studs.
- **Dressing, all existing hub assets:**
  - hub trees framing the portal and lining the road (high-detail versions near the entrance);
  - hub `Castle_Lantern`s on the stairs and around the plaza, hub `Lantern_Post`s and `Lantern_Wood`s down the road;
  - Verdant banner poles at the road mouth and the first junction, and wooden fences on the road's outer curve;
  - stone planters, bushes, flowers, ferns, and boulders and moss on the ridge;
  - the hub rope bridge over the brook.
- **Placeholders for later:**
  - `Cave_Entrance_Hollow` in the ridge;
  - a hidden brook path behind the bushes, crossing the rope bridge to a waterfall overlook;
  - `Secret_Cliff_Path`, a cliffside shortcut.
- **Shop and Hatchery:** the hub's own Shop and Hatchery (Eggs), built by `shop.py` and `hatchery.py`, stand either
  side of the plaza, fronts facing it. Each has its own flat pad and a paved walkway through the plaza border.
  They export as `Floor1_Shop.fbx` and `Floor1_Hatchery.fbx`, and their lamps go to `Floor1_Lights.lua`.
- **Built floors stay clean:** the plaza, portal, Shop and Hatchery pads (`HARD_PADS`) are flattened again after
  every path and river carve and set just under the floor meshes, so no terrain pokes through. Road pavers sit
  0.35 studs above the ground.
- **Portal upgrade:** a second, proud ring of pale voussoirs with its own cyan runes and rune columns down the
  jambs, a swirl ring and orbiting particles in the opening, stone fire braziers at the front of the dais, and
  warm brazier lights plus a cyan portal glow light (in `Floor1_Lights.lua`).
- **Cameras:** `CAM_F1_Entrance_Front`, `_Aerial`, `_Plaza`, `_Player` and `_Brook`.

**Verdant Village** (`floor1_village.py`, `Floor1_Village.fbx`)

Placeholder houses round the entrance for quest NPCs later. The portal, plaza, road, Shop and Hatchery stay where
they were. The village is compact: the houses line both sides of the road right after the plaza, about 50 studs
apart with their porches about 6 studs from the road edge. The Elder's house stands beside the portal stairs and
the lake directly behind the Hatchery.
- **Greenery (hub trees, bushes and flowers):** front gardens either side of every porch, plants round the walls,
  small trees between neighbouring houses, a dense tree-and-bush backdrop behind both rows, flowers and grass along
  the road edges, and flower meadows on the open grass. All of it is non-colliding foliage (trees only at their
  trunks), so pets can still ride across.

- **Eight houses, every one different.** Each has:
  - a stone masonry foundation, plaster walls and a dark timber frame (posts, rails, X / chevron / diagonal braces);
  - glowing windows with open shutters and flower boxes;
  - an arched plank door in a stone frame, a hanging sign, a door lamp and a timber porch with stone steps;
  - a masonry chimney.

  Roofs are straight gables, bell-cast curves or thatch, in red, brown, blue, teal, green, purple or straw.

  | House | Look | Extra |
  |---|---|---|
  | Elder | two storeys, jettied | balcony and a roof dormer |
  | Baker | bell-cast roof | domed bread oven |
  | Smith | stone ground floor | open forge shed |
  | Weaver | tall, jettied | balcony and a firewood lean-to |
  | Gardener | | vine pergola |
  | Scholar | | round stone tower with a spire |
  | Herbalist | small, steep orange gable | herb planter beds |
  | Fisher | thatched cottage by the lake | net rack |
- **NPC spots:** each house has an NPC spot on its porch, facing the road, and each market stall has one behind its
  counter (10 spots in all). They are in `floor1_layout.json` (`village`) and in the ModuleScript `Floor1_Village.lua`;
  `buildSpots(folder)` makes invisible marker parts with `Role` / `House` attributes.
- **Market:** two stalls with striped awnings and produce beside the road.
- **Props:** barrels, crates, firewood, flower pots, a cart, baskets, hay bales, clotheslines, garden patches,
  benches, fences and a well. They sit beside and behind the houses, never on the road or the riding routes.
- **Walks:** stepping-stone walks run from each porch to the road.
- **Lamps:** a warm lamp on every house, exported to `Floor1_Lights.lua`.
- **Lake on the right of the village:** an irregular shore with grass to the water's edge, rocks, reeds, flowers,
  bushes, small trees, lily pads and a fishing jetty. Two waterfalls drop into it from a new mossy cliff behind it,
  with foam, mist and splash rocks. It's a lake, not a river.
- **Plaza and road:**
  - benches and flower beds round the plaza rim; the centre and the walk-ins stay open;
  - grass tufts, flowers and occasional Verdant banners along the road edges.
- **Hillside:** layered rocks, moss drapes, vines, bushes, flowers and hub trees at different heights on the portal
  ridge and the cliff.
- **Clean floors:** every house and stall has its own flat pad.
- **Collision:** porches, steps and walks (`Village_Walk_*`) get exact collision.
- **Cameras:** `CAM_F1_Village_Aerial`, `_Street`, `_Lakeside` and `_Lake`.

**Roblox delivery** (`exports/TowerOfPets/Floor1/`, see `IMPORT.md` there)
- Terrain, water, bridges and landmarks are one FBX per group, about 2,900 MeshParts and 1.56M triangles. Each part
  has at most 6,000 triangles and is no wider than 1,900 studs.
- The scatter isn't baked into FBX. `Floor1_Assets.fbx` holds the 69 assets once each, as a single palette-textured
  MeshPart (`Floor1_Palette.png`). `Floor1_Scatter.lua` clones them from the `Scatter/` data modules (about 25,000
  placements) with per-category collision: tree trunk colliders, non-colliding foliage, Hull rocks, Box props, and
  persistent landmarks and background.
- Cameras: `CAM_F1_Map_TopDown`, `_Overview`, `_Entrance_Player`, `_Valley_View`, `_World_Tree_View`,
  `_Fortress_View`, `_Side_Elevation`, `_Bridge_Stone` and `_Bridge_Wood`.

```
python3 blender/tower_of_pets/build_floor1_pack.py      # .blend + floor1_layout.json + scatter / lighting scripts
python3 blender/tower_of_pets/build_floor1_export.py    # exports/TowerOfPets/Floor1/*.fbx + asset library
python3 blender/tower_of_pets/render.py blender/TowerOfPets_Floor1.blend previews 48 100   # previews
```
