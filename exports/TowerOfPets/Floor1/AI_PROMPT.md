# Floor 1 into Roblox Studio: what you do, then what to tell the AI

## Part A: you, in Roblox Studio (about 15 minutes)

1. **New place:** File → New → **Baseplate**. Delete **Baseplate** in Explorer. File → **Publish to Roblox**
   (name it "Tower of Pets - Floor 1").
2. **Import the map, one file at a time.** Avatar tab → **Import 3D** → pick one `.fbx`. In the importer window,
   click the **top item in the left list**, then on the right set:
   - **Insert Using Scene Position: ON**
   - **Scale Unit: Stud**
   - **Merge Meshes: OFF**

   Click **Import**, then do the same for the next file:
   1. `Floor1_Verdant_Forest.fbx`
   2. `Floor1_Waterfall_Valley.fbx`
   3. `Floor1_Ancient_Ruins.fbx`
   4. `Floor1_Mystic_Wilds.fbx`
   5. `Floor1_Jungle_Fortress.fbx`
   6. `Floor1_Entrance.fbx`
   7. `Floor1_Shop.fbx`
   8. `Floor1_Hatchery.fbx`
   9. `Floor1_Village.fbx`
   10. `Floor1_Bridges.fbx`
   11. `Floor1_Natural_Bridges.fbx`
   12. `Floor1_Water.fbx`
   13. `Floor1_Landmark_Blockouts.fbx`
   14. `Floor1_Clouds.fbx` (optional, last)
3. **Import `Floor1_Assets.fbx`** the same way. It's the library of trees, rocks and props, and lands as a pile at
   the centre of the map; that's expected.
4. **Insert the scripts in one go:** in Explorer, right-click **ServerStorage** → **Insert from File…** → pick
   `Floor1_Scripts.rbxmx`. ServerStorage now has:
   - `Floor1_Materials`
   - `Floor1_Scatter`
   - `Floor1_Lighting`
   - `Floor1_Lights`
   - `Floor1_Village`
   - a folder `Floor1_ScatterData` with 11 modules
5. **Optional, only if the trees later look white or grey:** Home → **Asset Manager** → **Images** → upload
   `Floor1_Palette.png`. Right-click it → **Copy Asset ID** and give that ID to the AI.
6. Make sure **Game Settings → Security → Enable Studio Access to API Services** is on, then publish again.

Then open your Roblox Studio AI (the Assistant, or an AI connected to Studio through the Roblox Studio MCP) and
paste everything below the line. If the AI can't run code in Studio, it will give you code to paste into the
**command bar** (View → Command Bar) instead.

---

I'm building Floor 1 ("The Verdant Kingdom") of my Roblox pet game **Tower of Pets**. Players ride their pets
across a huge world of floating islands. The map was made in Blender and I've already imported it. Please finish
the setup in Studio.

If you are connected to my Studio, do each step yourself and check the Output window after each one. If you are
not, give me the exact code for the command bar and tell me exactly where to click. I'm a beginner: one step at a
time, and tell me what you found before moving on.

**Important rules**
- Do NOT edit, move, resize, re-colour or delete the imported map parts. They are generated in Blender and get
  replaced when I re-import. Fix things with settings and scripts only.
- Put any new scripts in ServerScriptService, StarterPlayerScripts or ReplicatedStorage, never inside the map
  folders.

**Facts about the map** (1 stud = 1 Blender unit, imported with scene positions)
- The world is about 17,400 × 11,600 studs, made of floating islands over a void. A cloud sea sits at about
  Y = −3,800.
- Imported terrain models: `Floor1_Verdant_Forest`, `Floor1_Waterfall_Valley`, `Floor1_Ancient_Ruins`,
  `Floor1_Mystic_Wilds`, `Floor1_Jungle_Fortress`, `Floor1_Entrance`, `Floor1_Shop`, `Floor1_Hatchery`,
  `Floor1_Village`, `Floor1_Bridges`,
  `Floor1_Natural_Bridges`, `Floor1_Water`,
  `Floor1_Landmark_Blockouts` and maybe `Floor1_Clouds`.
  - There are about 3,300 MeshParts in total (plus about 600 if I imported the clouds), each named
    `<Object>__<Material>`.
- `Floor1_Entrance` is the Floor 1 entrance: a big portal with stairs and a round plaza with a leaf emblem.
  Players spawn on the plaza. Beside the plaza stand the hub's Shop and Hatchery (Eggs) buildings, the same
  models as in my hub (`Shop_Root` and `Hatchery_Root`).
- `Floor1_Village` is a small village round the plaza: seven placeholder houses for quest NPCs
  (`Village_House_Elder`, `_Baker`, `_Smith`, `_Weaver`, `_Gardener`, `_Scholar`, `_Fisher`) and two market stalls
  (`Village_Market_Stalls`). A lake with two waterfalls lies to the right of the village.
- `Floor1_Assets` is the asset library: 87 MeshParts such as `Tree_Large_Low`, `Rock_Large` and `Lantern_Wood`.
- ServerStorage holds the ModuleScripts `Floor1_Materials`, `Floor1_Scatter`, `Floor1_Lighting`, `Floor1_Lights`,
  `Floor1_Village` and a folder
  `Floor1_ScatterData` with 11 data modules.
- **Check positions:**
  - Entrance plaza / spawn: about (-5225, 60, 3850).
  - Main boss arena on the fortress plateau: about (5500, 1200, 990).
  - A 5-stud character should look tiny next to the 56-stud-wide main road at the spawn.

**Step 1: check the import**
1. List the imported models and where they are. Compare them with the facts above (position and size).
2. If they look right, move all the terrain models into a Folder `workspace.Floor1`.
3. Move the `Floor1_Assets` model into ServerStorage and make sure it's named exactly `Floor1_Assets`.
4. If the models are in the wrong place or about 3.6× too big or small, don't fake a fix. Tell me to delete them
   and re-import with Insert Using Scene Position ON and Scale Unit = Stud.

**Step 2: materials and collision**

Run `require(game.ServerStorage.Floor1_Materials).apply(workspace.Floor1)`. It colours and anchors every part,
gives the walkable ground, cliffs and bridge decks exact collision, and makes water and clouds non-colliding.
Report any errors.

**Step 3: environment (trees, plants, rocks, props)**

Place the scatter one category at a time, so no single command takes too long:
```lua
local S = require(game.ServerStorage.Floor1_Scatter)
S.place({categories = {"Trees"}, lights = true})
```
Then do the same for "Foliage", "Rocks", "Props", "Ruins", "Water", "Cliffs", "Landmarks" and "Background".
- Everything goes into `workspace.Floor1_Environment`.
- Each call prints how many pieces it placed and warns about any missing asset. Tell me the counts. The total
  should be about 25,000.
- Look at a few trees. If they are white or grey instead of green and brown, the palette texture is missing. Ask
  me for the palette image ID, then run `S.setTexture("rbxassetid://<ID>")` and also set that TextureID on every
  MeshPart inside `ServerStorage.Floor1_Assets`.

**Step 4: lighting, spawn, safety**
1. Run `require(game.ServerStorage.Floor1_Lighting).apply()`. Then create a Folder `workspace.Floor1.Lights` and
   run `require(game.ServerStorage.Floor1_Lights).build(workspace.Floor1.Lights)` for the shop, hatchery, house and portal
   lamps. `Floor1_Lighting` sets bright fantasy daylight, haze, bloom and terrain clouds.
2. Add a SpawnLocation (Anchored, Transparency 1, CanCollide off, Neutral) on the plaza emblem at
   (-5225, 61, 3850), facing away from the portal toward the forest road.
3. Touching `Floor1_Portal_TeleportTrigger` (inside the entrance portal) should take the player back to the hub.
   Make it invisible and non-colliding, then add a server script that teleports to my hub place with
   TeleportService. Ask me for the hub PlaceId and use a placeholder until I give it. Add a debounce and a short
   "Returning to the hub..." fade.
4. Set `Workspace.FallenPartsDestroyHeight = -4000`.
5. Turn on `Workspace.StreamingEnabled`. The Landmarks and Background models are already set to Persistent so the
   World Tree and distant islands stay visible.

**Step 5: test**

Start a Play test (F5). Check that:
- I spawn on the plaza in front of the portal, and can walk into the Shop and the Hatchery;
- I can walk up onto every house porch and along the stepping-stone walks;
- I can walk up the portal stairs, along the paved road, and across the wooden and stone bridges without falling
  through;
- trees only block at their trunks;
- nothing important is missing.

Tell me the frame rate and anything that looks wrong, with its location. Don't change the map geometry; describe
the problem so I can have it fixed in Blender.

**Step 6: shop and hatchery (placeholders)**

Add a ProximityPrompt at the entrance of the Shop and of the Hatchery (the side facing the plaza). Each opens a
simple placeholder UI with the building's name and a close button: red/gold for the Shop, purple/gold for the
Hatchery. I'll hook my real shop and egg-hatching systems into these later.

**Step 7: village NPC placeholders (for quests later)**
1. Create a Folder `workspace.Floor1.NPCSpots` and run
   `require(game.ServerStorage.Floor1_Village).buildSpots(workspace.Floor1.NPCSpots)`. It makes one invisible
   marker part per house porch and market stall, facing the road, with `Role` and `House` attributes. It should
   report 9.
2. At each marker, put a simple placeholder NPC: a standard R15 rig, anchored, named after its role (Elder, Baker,
   Smith, Weaver, Gardener, Scholar, Fisher, Merchant), standing on the marker's position and facing the same way.
   Give each one a BillboardGui name tag and a ProximityPrompt "Talk".
3. Talking opens one shared placeholder dialog with the NPC's name, a line such as "I might have a quest for you
   soon!", and a close button.
4. Keep it data-driven: one ModuleScript in ReplicatedStorage maps each Role to its display name and dialog lines,
   so I can add real quests later without touching the map.

At the end, list everything you created and where it is.
