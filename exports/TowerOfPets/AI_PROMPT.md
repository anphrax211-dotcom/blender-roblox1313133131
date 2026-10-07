Attach these 4 files from `exports/TowerOfPets/` to the message: `TowerOfPets_Materials.lua`, `TowerOfPets_Lights.lua`,
`IMPORT.md`, `manifest.json`. Then paste everything below the line.

---

I'm building the main hub/lobby for my Roblox game **"Tower of Pets"** (a pet simulator). The 3D models were made in
Blender and exported as FBX files. I've attached IMPORT.md, manifest.json, TowerOfPets_Materials.lua and
TowerOfPets_Lights.lua. If you are connected to my Roblox Studio (Roblox Studio MCP), do every step directly in
Studio and check the Output window for errors after each step. If you are NOT connected, walk me through each step:
give exact clicks, exact code, the script type, and exactly where it goes in Explorer.
I'm a beginner, so keep instructions simple and do one step at a time.

## What I've done so far
I selected ALL the FBX files at once and clicked Import 3D. No settings window appeared, so the importer options
were probably NOT applied: "Insert Using Scene Position", "Scale Unit = Stud" and "Merge Meshes = off".
The models may be in the wrong place, at the wrong size, merged, or not in Workspace at all.

## Facts about the files (all from the same Blender scene, 1 Blender unit = 1 stud, Y up)
FBX files (each one is a Model):
- **TowerOfPets_Plaza:** plaza floor, paths, gardens, lanterns, fountain, spawn pad
- **TowerOfPets_TowerEntrance:** stairs, castle gate, entrance portal, Portal_TeleportTrigger
- **TowerOfPets_Shop, _Hatchery, _PetClinic, _PetGym, _TradingPortal, _Leaderboards:** the six buildings
- **TowerOfPets_Tower_Lower, _Middle, _Upper:** the giant visual-only tower behind the hub (no playable floors)
- **TowerOfPets_Environment:** rock underside of the hub island, side arcades, mountains
- **TowerOfPets_FloatingIslands, TowerOfPets_SkyClouds:** decoration only. These two are the heaviest
  (FloatingIslands is about 2,900 parts), so skip them at first and add them last if performance is fine.

Correct world positions (in studs) when imported with scene position. Use these to check the import:
- Fountain / hub centre: (0, 0, 0). Plaza radius is about 128 studs, the grass rim reaches about 172.
- Building roots (centre of each building, front facing the fountain):
  - Hatchery (98, 0, 0)
  - Shop (66.5, 0, -66.5)
  - Pet Clinic (-66.5, 0, -66.5)
  - Trading Plaza Portal (-100, 0, 0)
  - Leaderboards (-72.1, 0, 72.1)
  - Pet Gym (66.5, 0, 66.5)
- The Tower Entrance stairs start about 100 studs from the centre toward -Z, and the tower rises behind them.
- Spawn pad top: (0, 0.8, 58), facing -Z toward the tower entrance.
- **Size check:** the Pet Gym is about 56 studs wide. A default character (about 5 studs) should be about as
  tall as a lantern post.
- Every mesh is one MeshPart named `<Object>__<Material>`, e.g. `PetGym_Facade__Castle_Stone_Light`.

## Step 1: Check the import and fix it if needed
1. Find everything that was imported (Workspace, or wherever Studio put it). Tell me what you find.
2. Compare the positions and sizes with the facts above.
3. If the models are at the right size and position, move them all into a Folder `workspace.TowerOfPets`.
4. If they are wrong (piled up, about 3.6x too big or small, merged into one mesh, or missing), don't try to fake
   a fix. Tell me to delete them and re-import ONE file at a time:
   - Avatar tab → Import 3D → select one file.
   - In the 3D Importer window, click the top item in the left list to show the settings on the right
     (section "File General").
   - Insert Using Scene Position = ON, Scale Unit = Stud, Merge Meshes = OFF, then Import.
   - Import order: Plaza, TowerEntrance, Shop, Hatchery, PetClinic, PetGym, TradingPortal, Leaderboards,
     Tower_Lower, Tower_Middle, Tower_Upper, Environment (FloatingIslands and SkyClouds last or not at all).
5. Delete the default Baseplate (it would flicker with the plaza floor) and the default SpawnLocation.

## Step 2: Colours, materials and lights
1. Create two ModuleScripts in ServerStorage from the attached files: `TowerOfPets_Materials` and
   `TowerOfPets_Lights` (exact content).
2. Run once:
   ```lua
   local root = workspace.TowerOfPets
   require(game.ServerStorage.TowerOfPets_Materials).apply(root)
   local f = Instance.new("Folder"); f.Name = "Lights"; f.Parent = root
   require(game.ServerStorage.TowerOfPets_Lights).build(f)
   ```
   This colours every part by material name (glow becomes Neon, wood becomes Wood, metal becomes Metal, the rest
   SmoothPlastic). It also anchors everything, makes the TeleportTrigger parts invisible and non-colliding, turns
   off collision on foliage, banners and effects, and adds 89 PointLights.
3. Lighting: Technology = Future. Add an Atmosphere (soft blue haze, Density about 0.25), Bloom (Intensity about
   0.5) and a bright sunny sky. The look is bright, colourful and cartoony.

## Step 3: Spawn
Add a SpawnLocation (Transparency 1, CanCollide off or a thin part) on the spawn pad at about (0, 0.8, 58),
facing -Z toward the tower entrance.

## Step 4: Trading Plaza Portal (at -100, 0, 0)
- Touching `TradingPortal_TeleportTrigger__*` teleports the player with TeleportService to my separate Trading
  Plaza place. Ask me for the PlaceId and use a placeholder until I give it. Add a debounce and a short fade or
  "Teleporting..." screen.
- Animate the portal with TweenService or RunService, client-side where it makes sense:
  - spin `TradingPortal_EnergyRing_0/1/2__*` around the portal's facing axis, at different speeds and directions;
  - slowly rotate `TradingPortal_Energy_Swirl__*`;
  - pulse `TradingPortal_Energy_Icon__*`;
  - drift `TradingPortal_Particles__*`.
- Add a purple ParticleEmitter and a purple PointLight in the portal.

## Step 5: Tower entrance portal
`Portal_TeleportTrigger__*` in the TowerEntrance model is a placeholder teleport into the tower. For now, show a
"Coming soon" message.

## Step 6: Leaderboards monument (at -72.1, 0, 72.1)
- Three boards with SurfaceGuis on the front face (the face toward the fountain):
  - `Leaderboard_1_Screen__Lb_Screen`: TOP PET POWER (strongest pet teams)
  - `Leaderboard_2_Screen__Lb_Screen`: TOP PET COLLECTORS (most pets discovered)
  - `Leaderboard_3_Screen__Lb_Screen`: TOP ROBUX SPENT (biggest supporters)
- Each board shows the top 10 from an OrderedDataStore: rank #1-#10, player avatar headshot thumbnail, display
  name, value (abbreviate big numbers like 12.4M). Use a navy/gold style that matches the monument. Refresh every
  few minutes.
- Use leaderstats-style values I can hook my game into later. Robux spent is updated from
  MarketplaceService.ProcessReceipt.
- Delete the placeholder text parts `Leaderboard_*_Ranks__*` and `Leaderboard_*_Entries__*`.
- Remind me to publish the place and enable "Studio Access to API Services" so DataStores work.

## Step 7: Buildings
Add a ProximityPrompt at each entrance of the Shop, Hatchery (Eggs), Pet Clinic and Pet Gym. Each one opens a
simple placeholder UI with the building's name and a close button, matching the building colours:
- Shop: red/gold
- Hatchery: purple/gold
- Pet Clinic: blue/teal
- Pet Gym: blue/gold

## Step 8: Test and tidy
Playtest (F5): walk around the whole hub, through the portal arch and up the tower stairs. Fix anything that
blocks movement (CanCollide) or that players fall through (CollisionFidelity). Then add FloatingIslands and
SkyClouds if performance is OK.
Finally, list every script you created and where it is.

Organise scripts cleanly:
- server Scripts in ServerScriptService
- LocalScripts in StarterPlayerScripts / StarterGui
- shared ModuleScripts in ReplicatedStorage

Start with Step 1 and tell me what you found before moving on.
