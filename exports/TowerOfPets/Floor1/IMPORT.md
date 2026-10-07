# Floor 1: The Verdant Kingdom (greybox) in Roblox Studio

This is the base terrain pass: terrain, water, landmark markers and greybox landmark massing (World Tree, fortress
keep, ruin pillars). There are no final buildings, trees or decorations yet. It's generated from
`blender/TowerOfPets_Floor1.blend` by `blender/tower_of_pets/build_floor1_export.py`. 1 unit = 1 stud, Y up.
The regions sit where the map sheet puts them, but they now form one connected continent of about
1,740 × 1,150 studs. Only the Sky Temple, the four secret isles and two optional islets float apart.
Heights run from about −29 (Lotus Swamp) to about 390 (Cloudridge summit). The Fortress Heights are at 240,
and the World Tree canopy reaches about 590.

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
| `Floor1_Clouds.fbx` | cloud sea far below the islands (optional) |
| `Floor1_Materials.lua` | ModuleScript: colours and materials, plus exact collision on the terrain (`apply(model)`) |
| `floor1_layout.json` | positions in Roblox coordinates: spawn, regions, areas and level ranges, checkpoints, bosses, eggs, caves, cave pairs for future tunnels, secret areas, every path's waypoints (with its kind: main / secondary / hidden), waterfalls |

Each area has `<Area>_Top` (walkable ground and paths), `<Area>_Cliffs` (cliff walls) and `<Area>_Underside`
(the floating rock below). Large surfaces are split into chunks of 6,000 triangles or fewer. Parts are named
`<Object>__<Material>`.

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
5. Put a SpawnLocation at the spawn ring, about **(-522, 12, 385)**, facing the meadows and village (toward −Z).
6. **Kill plane:** the kingdom floats above a void. Set Workspace.FallenPartsDestroyHeight to about −550, or add
   a respawn zone under the clouds.
7. **Scale check:** the Floor Entrance platform is about 300 × 170 studs. Main roads are 36 studs wide,
   secondary trails 26 and hidden paths 14. Path climbs are at most about 25°.

## Key positions (Roblox coordinates)

- Spawn (Floor Entrance): (-522, 12, 385)
- Main boss (Fortress Heights arena): (550, 240, 99)
- All other positions are in `floor1_layout.json`: checkpoints, mini-bosses, eggs, caves, secrets, path
  waypoints.
