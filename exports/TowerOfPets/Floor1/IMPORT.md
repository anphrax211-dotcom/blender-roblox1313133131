# Floor 1: The Verdant Kingdom (greybox) in Roblox Studio

This is the base layout only: terrain, water and landmark markers. There are no buildings, trees or decorations
yet. It's generated from `blender/TowerOfPets_Floor1.blend` by `blender/tower_of_pets/build_floor1_export.py`.
1 unit = 1 stud, Y up. The playable area is about 1,500 × 1,500 studs, with heights from about −27 (Lotus Swamp)
to about 324 (Cloudridge summit).

Floor 1 should be its **own place** (the hub's tower entrance teleports to it). Import it into an empty
place, not the hub.

## Files

| File | Contents |
|---|---|
| `Floor1_Verdant_Forest.fbx` | Floor Entrance, Sunlit Meadows, Verdant Village, Whispering Forest, Guardian Grove, Mistfall secret isle |
| `Floor1_Waterfall_Valley.fbx` | Riverfall Valley, Emerald Lake, Lotus Swamp, Lotus Grotto secret |
| `Floor1_Ancient_Ruins.fbx` | Ancient Ruins plateau, Cloudridge Peaks, Cloud Perch secret |
| `Floor1_Mystic_Wilds.fbx` | World Tree Grove, Mossy Caverns, Beast Cave |
| `Floor1_Jungle_Fortress.fbx` | Jungle Fortress plateau, Sky Guardian ledge, Sky Temple island, Overlook secret |
| `Floor1_Natural_Bridges.fbx` | the rock bridges where paths cross the void |
| `Floor1_Water.fbx` | rivers, lakes, ponds, waterfalls |
| `Floor1_Landmark_Blockouts.fbx` | spawn ring, 6 checkpoints, 3 mini-boss rings, main boss ring, 6 world-egg pads, 7 cave mouths, secret markers |
| `Floor1_Clouds.fbx` | cloud sea far below the islands (optional) |
| `Floor1_Materials.lua` | ModuleScript: colours and materials, plus exact collision on the terrain (`apply(model)`) |
| `floor1_layout.json` | positions in Roblox coordinates: spawn, areas and level ranges, checkpoints, bosses, eggs, caves, secret areas, every path's waypoints, waterfalls |

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
5. Put a SpawnLocation at the spawn ring, about **(-550, 8, 546)**, facing the meadows (toward −Z).
6. **Kill plane:** the islands float above a void. Set Workspace.FallenPartsDestroyHeight to about −500, or add
   a respawn zone under the clouds.
7. **Scale check:** the spawn platform is about 180 studs across, and the main paths are 22–32 studs wide.

## Key positions (Roblox coordinates)

- Spawn (Floor Entrance): (-550, 8, 546)
- Main boss (Jungle Fortress arena): (417, 195, 12)
- All other positions are in `floor1_layout.json`: checkpoints, mini-bosses, eggs, caves, secrets, path
  waypoints.
