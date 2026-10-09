# Floor 1: The Verdant Kingdom in Roblox Studio

Floor 1 after the global environment detail pass. It has:
- terrain with strata cliffs;
- water;
- built bridges;
- landmark silhouettes (World Tree, Jungle Fortress, ruins);
- about 25,000 placed trees, plants, rocks, props, ruin pieces, water and cliff dressing and background pieces.

Every biome is at a 60–70% baseline and is meant to get its own detail pass later. Everything is generated from
`blender/TowerOfPets_Floor1.blend` (`build_floor1_pack.py`, then `build_floor1_export.py`). 1 unit = 1 stud, Y up.

**Scale and layout.** The world is about 17,400 × 11,600 studs (10× the map sheet). There are four landmasses
with open sky between them, crossed by bridges:
- **Verdant mainland:** Entrance, Meadows, Village and Whispering Forest.
- **Central highlands:** Ruins, Cloudridge, World Tree, Emerald Lake, Riverfall Valley and Mossy Caverns.
- **Lotus Swamp.**
- **Jungle Fortress:** with Beast Cave.

The Sky Temple, four secret isles and two optional islets float on their own.

**Heights.** Region base heights run from about −120 (Lotus Swamp) to 1,200 (Fortress Heights, the boss plateau).
The Cloudridge summit is about 2,650 and the World Tree canopy about 4,800. Height differences between regions
are deliberately moderate, set by `LEVEL` in `floor1.py`.

**Player-scale sizes.** Main roads are 56 studs wide, trails 40 and hidden paths 20. Climbs stay at 25° or less.

Floor 1 should be its **own place** (the hub's tower entrance teleports to it). Import it into an empty place.

**Quickest route:** follow `AI_PROMPT.md`. You import the FBX files and insert `Floor1_Scripts.rbxmx`, which holds
every ModuleScript below (`Floor1_Materials`, `Floor1_Scatter`, `Floor1_Lighting` and the `Floor1_ScatterData`
folder). In Studio: right-click ServerStorage → Insert from File. Then paste the prompt into your Studio AI.

## Files

| File | Contents |
|---|---|
| `Floor1_Verdant_Forest.fbx` | Floor Entrance, Sunlit Meadows, Verdant Village, Whispering Forest, Mistfall secret isle, treasure islet |
| `Floor1_Waterfall_Valley.fbx` | Riverfall Valley, Emerald Lake, Lotus Swamp, Lotus Grotto secret |
| `Floor1_Ancient_Ruins.fbx` | Ancient Ruins, Cloudridge Peaks, Cloud Perch secret |
| `Floor1_Mystic_Wilds.fbx` | World Tree Grove, Mossy Caverns, Beast Cave |
| `Floor1_Jungle_Fortress.fbx` | jungle ring, Fortress Heights (boss plateau), Sky Temple island, Overlook secret, rare-pet islet |
| `Floor1_Entrance.fbx` | the Floor 1 entrance:<br>• the portal: masonry arch, pillars, Verdant banners, vines and the swirling portal<br>• `Floor1_Portal_TeleportTrigger`, an invisible touch box inside the portal for the return-to-hub teleport<br>• the dais and wide staircase<br>• the emblem plaza (the spawn)<br>• the paved start of the forest road<br><br>Walkable parts (`Entrance_Walk_*`) get exact collision. |
| `Floor1_Shop.fbx`, `Floor1_Hatchery.fbx` | the hub's Shop and Hatchery (Eggs), copied 1:1 and set either side of the entrance plaza, facing it, with paved walkways. Each is a Model with its `Shop_Root` / `Hatchery_Root` pivot. Their lamps are in `Floor1_Lights.lua` |
| `Floor1_Village.fbx` | the Verdant Village round the entrance: eight different timber-frame placeholder houses (Elder, Baker, Smith, Weaver, Gardener, Scholar, Herbalist, Fisher), two market stalls and stepping-stone walks. Porches, steps and walks (`Village_Walk_*`) get exact collision. The house lamps are in `Floor1_Lights.lua` |
| `Floor1_Fortress.fbx` | the Jungle Fortress castle on the Fortress Heights plateau (replaces the old massing blockout):<br>• a masonry podium with a monumental staircase and a paved approach with carved pillars and braziers<br>• curtain walls with battlements and wall walks, ten towers of different heights with tall tiered copper roofs, and an arched gatehouse<br>• a courtyard with statues and planters, an inner terrace with its own stairs<br>• the three-level keep with corner turrets, arcaded windows, a balcony, side wings and the monumental entrance<br>• red and gold banners, torches, vines<br><br>Walkable floors (`Fortress_Walk_*`) get exact collision; the torch and brazier lamps are in `Floor1_Lights.lua` |
| `Floor1_Village.lua` | ModuleScript: house, stall and NPC-spot positions (Roblox coordinates) for quest NPCs; `buildSpots(folder)` makes invisible marker parts |
| `Floor1_Bridges.fbx` | 11 built bridges where paths cross open sky: wood truss, stone and rope (decks get exact collision) |
| `Floor1_Natural_Bridges.fbx` | the rock spans of the Sky Stair, the Fortress Grand Ramp and the Cloud Perch path |
| `Floor1_Water.fbx` | rivers, lakes, ponds, waterfalls (including small cliff cascades) |
| `Floor1_Landmark_Blockouts.fbx` | the markers below, plus the landmark pieces (`Landmark_World_Tree_Trunk/Limbs`, `Landmark_Ruins_Pillars`) |
| `Floor1_Clouds.fbx` | flat cloud sea far below the islands (optional; Studio's Terrain clouds can replace it) |
| `Floor1_Materials.lua` | ModuleScript: colours and materials for the terrain FBX files, exact collision on the walkable surfaces (`apply(model)`) |
| `Floor1_Assets.fbx` + `Floor1_Palette.png` | the environment asset library: 89 assets (hub trees, hub stone lanterns and lantern posts, Verdant banner poles, Mystic Wilds trees, bushes, plants, flowers, rocks, lanterns, props, ruin pieces, reeds, lily pads, jungle palms and tropical plants, village props such as carts, hay bales, clotheslines, garden patches, a well and a fishing jetty, clouds, background islands ...). Each asset is **one MeshPart** coloured by the small palette texture |
| `Floor1_Scatter.lua` | ModuleScript that places every scattered piece by cloning `Floor1_Assets` |
| `Scatter/Floor1_Scatter_*.lua` | placement data ModuleScripts (position, yaw and scale per piece), one or more per category |
| `Floor1_Lighting.lua` | ModuleScript: bright fantasy daylight, soft shadows, haze, subtle bloom, terrain clouds |
| `Floor1_Lights.lua` | ModuleScript: the Shop, Hatchery, village house, portal brazier and portal glow lamps as PointLights (`build(folder)`) |
| `Floor1_Scripts.rbxmx` | all of the ModuleScripts above (including `Floor1_Village`) plus the `Floor1_ScatterData` folder, ready for Insert from File |
| `AI_PROMPT.md` | the manual Studio steps and a ready-to-paste prompt for a Studio AI |
| `floor1_layout.json` | positions in Roblox coordinates: spawn, regions, areas and level ranges, checkpoints, bosses, eggs, caves, cave pairs, secret areas, path waypoints, waterfalls, bridges |

The markers in `Floor1_Landmark_Blockouts.fbx` are:
- 6 checkpoints, 3 mini-boss rings and the main boss ring;
- 6 world-egg pads;
- 8 cave mouths;
- the secret markers.

Each terrain area has `<Area>_Top` (walkable ground and paths), `<Area>_Cliffs` (layered cliff walls) and
`<Area>_Underside` (the floating rock below, thinned out because it's only seen from afar). Parts are named
`<Object>__<Material>`. Every part has at most 6,000 triangles and is no bigger than 1,900 studs on any side
(Roblox's MeshPart limit is 2,048). The terrain, water, bridges and landmark files together come to about 2,900
parts and 1.56M triangles; the entrance, Shop, Hatchery, village and fortress add about 1,300 parts.

## 1. Terrain, water, bridges and landmarks

1. Create a new place: File → New → Baseplate. Delete the **Baseplate**, then publish the place.
2. Avatar tab → **Import 3D**, **one file at a time**. Click the top item in the importer's left list, then set:
   - **Insert Using Scene Position: ON**
   - **Scale Unit: Stud**
   - **Merge Meshes: OFF**
3. Import every `Floor1_*.fbx` (including `Floor1_Entrance.fbx`) **except `Floor1_Assets.fbx`**, and put them in a Folder `workspace.Floor1`.
4. Add `Floor1_Materials.lua` as a ModuleScript in ServerStorage named `Floor1_Materials`, then run this in the
   command bar:
   ```lua
   require(game.ServerStorage.Floor1_Materials).apply(workspace.Floor1)
   ```
   It does three things:
   - colours and anchors every part;
   - gives the walkable surfaces exact collision (**PreciseConvexDecomposition**): terrain `_Top` and `_Cliffs`,
     natural bridges, and bridge decks;
   - makes water, waterfalls and clouds non-colliding.

## 2. Environment scatter (trees, plants, rocks, props ...)

1. Import `Floor1_Assets.fbx` with the same settings. Rename the imported model **`Floor1_Assets`** and move it
   to **ServerStorage**. The 89 assets all sit at the origin; that's expected.
2. In ServerStorage, create a Folder **`Floor1_ScatterData`**. Add every `Scatter/Floor1_Scatter_*.lua` to it as
   a ModuleScript, keeping the file names.
3. Add `Floor1_Scatter.lua` as a ModuleScript in ServerStorage named `Floor1_Scatter`, then run:
   ```lua
   require(game.ServerStorage.Floor1_Scatter).place({lights = true})
   ```
   This creates `workspace.Floor1_Environment` with one Model per category. It takes a little while (about
   25,000 pieces).
4. **Palette texture:** if the assets show up white or grey, the importer didn't bring the palette in.
   1. Upload `Floor1_Palette.png` (Asset Manager → Images).
   2. Run `require(game.ServerStorage.Floor1_Scatter).setTexture("rbxassetid://<id>")`.
   3. Also set the same TextureID on the parts inside `ServerStorage.Floor1_Assets`.

**Options for `place`:**
- `categories = {"Trees", "Rocks"}` places only those categories.
- `texture = "rbxassetid://<id>"` sets the palette on every placed piece.
- `lights = true` adds warm PointLights to the lanterns.

**How each category behaves** (set in `Floor1_Scatter.lua`):

| Category | What | Collision |
|---|---|---|
| Trees | hub-style trees (Mystic Wilds re-coloured) | canopy non-colliding; an invisible cylinder trunk collider per tree, so riders can pass under canopies |
| Foliage | bushes, ground plants, ferns, flowers, grass, mushrooms | none, no shadows |
| Rocks | boulders, rock formations, river rocks, pebbles | Hull; small pebbles non-colliding |
| Props | lanterns, signposts, benches, fences, rope barriers, barrels, crates, logs, stumps | Box |
| Ruins | broken columns and walls, ruin arches, stone fragments, temple platforms | Hull |
| Water | reeds, lily pads, waterfall mist and foam | none |
| Cliffs | moss drapes, vines, roots, boulders set into cliff walls | none |
| Landmarks | World Tree canopy (hub leaf clusters) and giant roots | none; **streams persistently** |
| Background | distant islands with trees and falls, mountain spires, cloud banks, floating rocks | none; **streams persistently** |

## 3. Lighting, spawn, streaming

1. Add `Floor1_Lighting.lua` as a ModuleScript in ServerStorage, then run
   `require(game.ServerStorage.Floor1_Lighting).apply()`. It sets:
   - bright fantasy daylight with ShadowMap soft shadows;
   - a soft blue Atmosphere haze;
   - subtle Bloom;
   - vibrant ColorCorrection;
   - Terrain clouds.
2. Put a SpawnLocation on the entrance plaza emblem, about **(-5225, 61, 3850)**, facing away from the portal
   toward the forest road (toward +X / −Z).
3. **Kill plane:** the cloud sea is at about −3,800. Set Workspace.FallenPartsDestroyHeight to about −4,000, or
   add a respawn zone just above the clouds.
4. Turn on **Workspace.StreamingEnabled**. Nearby terrain and scatter stream in. The Landmarks and Background
   models are Persistent, so the World Tree, distant islands and mountains stay visible.
5. **Scale check:** the Floor Entrance platform is about 3,000 × 1,700 studs, and main roads are 56 studs wide.

## Key positions (Roblox coordinates)

- Spawn (Floor Entrance): (-5225, 60, 3850)
- Main boss (Fortress Heights arena): (5500, 1200, 990)
- Everything else is in `floor1_layout.json`.
