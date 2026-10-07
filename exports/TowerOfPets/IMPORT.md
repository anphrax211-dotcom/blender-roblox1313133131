# Tower of Pets hub: importing into Roblox Studio

These files are generated from `blender/TowerOfPets_Lobby.blend` by `blender/tower_of_pets/export_fbx.py`
(re-run it after any Blender change). Everything shares one world space: **1 Blender unit = 1 stud, Y up**.

## Files

| File | What it is | Pivot (Model root) |
|---|---|---|
| `TowerOfPets_Plaza.fbx` | plaza floor, paths, gardens, lanterns, fountain, spawn pad, island balustrade | world origin |
| `TowerOfPets_TowerEntrance.fbx` | grand stairs, castle gatehouse, entrance portal + `Portal_TeleportTrigger` | world origin |
| `TowerOfPets_Shop.fbx` | Shop (45°) | `Shop_Root` |
| `TowerOfPets_Hatchery.fbx` | Hatchery / Eggs (0°) | `Hatchery_Root` |
| `TowerOfPets_PetClinic.fbx` | Pet Clinic (135°) | `PetClinic_Root` |
| `TowerOfPets_PetGym.fbx` | Pet Gym (315°) | `PetGym_Root` |
| `TowerOfPets_TradingPortal.fbx` | Trading Plaza Portal (180°) + `TradingPortal_TeleportTrigger` | `TradingPortal_Root` |
| `TowerOfPets_Leaderboards.fbx` | Leaderboards monument (225°), screens `Leaderboard_1..3_Screen` | `Leaderboards_Root` |
| `TowerOfPets_Tower_Lower/_Middle/_Upper.fbx` | the giant visual-only tower (foundation + 11 themed tiers) | world origin |
| `TowerOfPets_FloatingIslands.fbx` | floating islands, bridges, waterfalls | world origin |
| `TowerOfPets_Environment.fbx` | hub rock underside, side arcades, mountains | world origin |
| `TowerOfPets_SkyClouds.fbx` | big decorative clouds (optional, Roblox has its own clouds) | world origin |
| `TowerOfPets_Materials.lua` | ModuleScript: colours + Roblox materials for every part, `apply(model)` | |
| `TowerOfPets_Lights.lua` | ModuleScript: the Blender lamps as PointLights, `build(folder)` | |
| `manifest.json` | part / triangle counts per file, root positions, spawn position | |

Each mesh is split by material, so one MeshPart has one material. Parts are named `<Object>__<Material>`
(for example `PetGym_Facade__Castle_Stone_Light`). Every part is under 19,000 triangles.

## Import (Studio → Avatar tab → Import 3D), one file at a time

1. Pick the `.fbx` file.
2. Set these importer options:
   - **Insert Using Scene Position: ON**. Each file then lands where it belongs, with no manual moving.
   - **Scale Unit: Stud**. Check the size: the Pet Gym is about 56 studs wide and a default character is about
     5 studs tall. If everything is about 3.6× too big or too small, the unit setting is wrong.
   - **Merge Meshes: OFF**. This keeps the named parts: triggers, screens, portal rings.
   - **Anchored: ON**, if the option is shown. `TowerOfPets_Materials.apply` also anchors every part.
3. Import. Put every model in a Folder, e.g. `Workspace.TowerOfPets`.

Recommended order: Plaza → TowerEntrance → the six facilities → Tower_* → FloatingIslands → Environment →
SkyClouds. The FloatingIslands file is the heaviest (about 2,900 parts, about 680k triangles). If Studio struggles,
skip it or the SkyClouds file at first.

## Colours, materials and lights

FBX carries only flat material colours, because the Blender materials are procedural. Do this instead:

1. Insert both `.lua` files as **ModuleScripts** in `ServerStorage`, named `TowerOfPets_Materials` and
   `TowerOfPets_Lights`.
2. Run this once in the Studio command bar:

```lua
local root = workspace.TowerOfPets
require(game.ServerStorage.TowerOfPets_Materials).apply(root)
local lights = Instance.new("Folder"); lights.Name = "Lights"; lights.Parent = root
require(game.ServerStorage.TowerOfPets_Lights).build(lights)
```

`apply` does the following:
- sets Color, Material (glowing Blender materials become **Neon**, wood becomes Wood, metal becomes Metal,
  everything else SmoothPlastic for the cartoony look) and Transparency;
- anchors every part;
- makes `*TeleportTrigger*` parts invisible and non-colliding;
- turns off collision on effects and foliage: particles, portal energy, rings, leaves, vines, banners,
  waterfalls, glow pieces.

## Key objects for scripting

- **Spawn:** the spawn pad is at Roblox position about `(0, 0.8, 58)` (top of the pad), facing −Z, toward the
  tower entrance. Put the `SpawnLocation` there.
- **Tower entrance portal:** `Portal_TeleportTrigger__*` (Tower_Entrance file).
- **Trading Plaza Portal:**
  - `TradingPortal_TeleportTrigger__*` is the teleport to the separate Trading Plaza place.
  - The animated pieces are `TradingPortal_EnergyRing_0/1/2__*` (spin around the axis pointing out of the portal),
    `TradingPortal_Energy_Swirl__*`, `TradingPortal_Energy_Icon__*` and `TradingPortal_Particles__*`.
- **Leaderboards:**
  - `Leaderboard_1_Screen__Lb_Screen` (Top Pet Power), `_2_` (Top Pet Collectors) and `_3_` (Top Robux Spent)
    are the SurfaceGui faces. Use the front face, the one pointing toward the fountain.
  - Delete the `Leaderboard_*_Ranks__*` and `Leaderboard_*_Entries__*` placeholder text parts once the live
    boards work.
- **Facility roots:** the Model roots (`Shop_Root`, `Hatchery_Root`, `PetClinic_Root`, `PetGym_Root`,
  `TradingPortal_Root`, `Leaderboards_Root`) sit at each building's centre, with the front facing the fountain.
  Their positions are in `manifest.json`.

Hub slots (degrees around the fountain, 0° = +X, counter-clockwise seen from above in Blender):
Eggs 0, Shop 45, Tower Entrance 90, Pet Clinic 135, Trading Portal 180, Leaderboards 225, Spawn 270,
Pet Gym 315.
