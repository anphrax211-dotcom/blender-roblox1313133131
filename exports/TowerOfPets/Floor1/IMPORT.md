# Floor 1: The Verdant Kingdom (greybox) in Roblox Studio

This is the base terrain pass: terrain, water, landmark markers and greybox landmark massing (World Tree, fortress
keep, ruin pillars). There are no final buildings, trees or decorations yet. It's generated from
`blender/TowerOfPets_Floor1.blend` by `blender/tower_of_pets/build_floor1_export.py`. 1 unit = 1 stud, Y up.

The world is built at **10× scale**: about 17,400 × 11,600 studs. The regions sit where the map sheet puts them,
grouped into four landmasses with open sky between them, linked by natural rock bridges:
- **Verdant mainland:** Entrance, Meadows, Village and Whispering Forest.
- **Central highlands:** Ruins, Cloudridge, World Tree, Emerald Lake, Riverfall Valley and Mossy Caverns.
- **Lotus Swamp.**
- **Jungle Fortress:** with Beast Cave.

The Sky Temple, the four secret isles and two optional islets float on their own.

Heights run from about −280 (Lotus Swamp) to about 3,930 (Cloudridge summit). The Fortress Heights are at 2,400,
and the World Tree reaches about 5,800. Player-scale things are not scaled:
- path widths (main roads 56, trails 40, hidden paths 20);
- markers, and checkpoint and mini-boss pads;
- path climbs, which stay at 25° or less.

Floor 1 should be its **own place** (the hub's tower entrance teleports to it). Import it into an empty
place, not the hub.

## Files

| File | Contents |
|---|---|
| `Floor1_Verdant_Forest.fbx` | Floor Entrance, Sunlit Meadows, Verdant Village, Whispering Forest, Mistfall secret isle, treasure islet |
| `Floor1_Waterfall_Valley.fbx` | Riverfall Valley, Emerald Lake, Lotus Swamp, Lotus Grotto secret |
| `Floor1_Ancient_Ruins.fbx` | Ancient Ruins, Cloudridge Peaks, Cloud Perch secret |
| `Floor1_Mystic_Wilds.fbx` | World Tree Grove, Mossy Caverns, Beast Cave |
| `Floor1_Jungle_Fortress.fbx` | Jungle Fortress jungle ring, Fortress Heights (boss plateau), Sky Temple island (Mini-Boss 3), Overlook secret, rare-pet islet |
| `Floor1_Natural_Bridges.fbx` | the few rock bridges where paths still cross open sky |
| `Floor1_Water.fbx` | rivers, lakes, ponds, waterfalls |
| `Floor1_Landmark_Blockouts.fbx` | spawn ring, 6 checkpoints, 3 mini-boss rings, main boss ring, 6 world-egg pads, 8 cave mouths, secret markers, and the landmark massing (`Landmark_World_Tree`, `Landmark_Fortress_Keep`, `Landmark_Ruins_Pillars`) |
| `Floor1_Clouds.fbx` | cloud sea far below the islands, in tiles (optional) |
| `Floor1_Materials.lua` | ModuleScript: colours and materials, plus exact collision on the terrain (`apply(model)`) |
| `floor1_layout.json` | positions in Roblox coordinates: spawn, regions, areas and level ranges, checkpoints, bosses, eggs, caves, cave pairs for future tunnels, secret areas, every path's waypoints (with its kind: main / secondary / hidden), waterfalls |

Each area has `<Area>_Top` (walkable ground and paths), `<Area>_Cliffs` (cliff walls) and `<Area>_Underside`
(the floating rock below). Large surfaces are split into chunks of 6,000 triangles or fewer, and no part is
bigger than 1,900 studs on any side (Roblox MeshParts are limited to 2,048). There are about 2,000 parts and
1.32M triangles in total; `manifest.json` lists each file's part count, triangle count and widest part. Parts are
named `<Object>__<Material>`.

## Import

1. Create a new place: File → New → Baseplate. Delete the **Baseplate**, then publish the place.
2. Avatar tab → **Import 3D**, **one file at a time**. Click the top item in the importer's left list, then set:
   - **Insert Using Scene Position: ON**
   - **Scale Unit: Stud**
   - **Merge Meshes: OFF**
3. Put everything in a Folder `workspace.Floor1`.
4. Insert `Floor1_Materials.lua` as a ModuleScript in ServerStorage named `Floor1_Materials`, then run this
   in the command bar:
   ```lua
   require(game.ServerStorage.Floor1_Materials).apply(workspace.Floor1)
   ```
   This colours every part and anchors it. It also gives the terrain (`_Top`, `_Cliffs`, bridges) exact
   **PreciseConvexDecomposition** collision, so players and pets walk on the real ground. Water, waterfalls and
   clouds become non-colliding.
5. Put a SpawnLocation at the spawn ring, about **(-5225, 120, 3850)**, facing the meadows and village (toward −Z).
6. **Kill plane:** the kingdom floats above a void, with the cloud sea at about −3,800. Set
   Workspace.FallenPartsDestroyHeight to about −4,000, or add a respawn zone just above the clouds.
7. **Big world:** turn on Workspace.StreamingEnabled so players only load the nearby terrain.
8. **Scale check:** the Floor Entrance platform is about 3,000 × 1,700 studs. Main roads are 56 studs wide.

## Key positions (Roblox coordinates)

- Spawn (Floor Entrance): (-5225, 120, 3850)
- Main boss (Fortress Heights arena): (5500, 2400, 990)
- All other positions are in `floor1_layout.json`: checkpoints, mini-bosses, eggs, caves, secrets, path
  waypoints.
