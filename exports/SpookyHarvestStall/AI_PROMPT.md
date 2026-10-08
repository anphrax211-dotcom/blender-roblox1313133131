Attach these files from `exports/SpookyHarvestStall/` to the message: `SpookyHarvestStall.fbx`,
`SpookyHarvest_Setup.lua` and `fbx_manifest.json`. Then paste everything below the line.

---

I'm adding a Halloween event market stall called **"Spooky Harvest"** to my Roblox game. It was modelled in
Blender and exported as an FBX. I've attached `SpookyHarvestStall.fbx`, `SpookyHarvest_Setup.lua` (a script that
styles the stall after import) and `fbx_manifest.json` (every part name). If you are connected to my Roblox Studio
(Roblox Studio MCP), do every step directly in Studio and check the Output window for errors after each step. If
you are NOT connected, walk me through each step with exact clicks and exact code. I'm a beginner, so keep it
simple and do one step at a time.

## Facts about the file
- **Scale and orientation:** 1 unit = 1 stud, Y is up, and the ground is at y = 0. The front of the stall (where
  players stand) faces **−Z**. It's about 20 studs wide including the side lanterns, 8 deep and 15.5 tall, and
  the counter top is 3.4 studs high.
- **Parts:** it contains **111 MeshParts**, about 45,000 triangles in total, each part under 20,000.
- **Naming:** every MeshPart is named `<Section>__<Material>__<RRGGBB>`, sometimes with extra flags:
  - `__T<number>` = transparency in percent (e.g. `__T55` = 0.55);
  - `__NC` = no collision;
  - `__L<n>` = this part gets soft PointLight number n.
  - Examples: `Canopy__Fabric__703496`, `Structure__WoodPlanks__4A2F1E`,
    `CounterProps__Glass__D6E8EC__T55__NC`, `Lanterns__Neon__EC8028__T15__NC__L2`.
- **Sign:** the part `Sign__SignBoard__WoodPlanks__422A1B` is the sign board. The text "SPOOKY HARVEST" is NOT in
  the FBX. The setup script adds it as a SurfaceGui on the board's Front face (font LuckiestGuy, gold, centred).
- **Colours:** the FBX has no colours or Roblox materials. That's why `SpookyHarvest_Setup.lua` exists: it reads
  each name and sets Material, Color, Transparency, CanCollide and Anchored. It also adds 5 soft orange
  PointLights, the sign text, an invisible `ShopInteractZone` part in front of the counter, and sorts the parts
  into Folders (Structure, Counter, Canopy, Sign, Lanterns, CounterProps, Decor).

## What I need you to do
1. **Import.** Import `SpookyHarvestStall.fbx` with the 3D Importer (Home or Avatar tab → Import 3D). Use
   these settings:
   - **Scale Unit: Stud**
   - **Merge Meshes: OFF**: important, the part names must survive
   - **Insert Using Scene Position: ON**
   - **Anchored: ON**, if the option is shown

   After importing, check: is it a Model with about 111 MeshParts? Are the names like `Canopy__Fabric__703496`
   intact? Is it about 15.5 studs tall? If it's huge or tiny, re-import with Scale Unit = Stud. If the parts were
   merged or renamed, re-import with Merge Meshes OFF.
2. **Run the setup script.** Name the imported model `SpookyHarvestStall`, open View → Command Bar, paste the
   whole of `SpookyHarvest_Setup.lua` and press Enter. The Output should say
   `SpookyHarvestStall set up: 111 parts styled`. If the count is lower, tell me which part names were skipped.
3. **Check it looks right:**
   - a dark brown wooden booth with WoodPlanks wood grain;
   - an orange-and-purple striped Fabric canopy with pointed flaps;
   - a sign that reads **SPOOKY HARVEST** in gold letters, centred, with a purple bat on each side;
   - glowing carved jack-o'-lanterns: two hanging from iron brackets on the sides, one big and two small on the
     left of the counter, one on top of the sign, one carved into the counter front;
   - two warm iron lanterns hanging under the canopy;
   - two glass candy jars on the right of the counter;
   - autumn leaves, green vines and two small white cobwebs.

   The glow should be subtle, so the stall stays easy to see. If the sign text is mirrored, on the wrong face or
   missing, change `SignGui.Face` on `Sign__SignBoard...` (try Front, then Back).
4. **Place it.** Move the stall where I want it with `workspace.SpookyHarvestStall:PivotTo(CFrame.new(x, y, z))`
   or the Move tool. Keep the front (−Z side) facing where players walk.
5. **Hook up the shop (optional, ask me first).** The invisible `ShopInteractZone` part sits in front of the free
   middle of the counter. If I want, add a `ProximityPrompt` to it ("Open Shop", HoldDuration 0) and connect it to
   my shop UI, but ask me how my shop opens before writing that code.

## Please don't
- Don't change the mesh shapes or merge parts.
- Don't make the lights brighter or add effects that hide the stall.
- Don't add extra decorations, characters or UI beyond what's listed.

## If something looks wrong
- **Everything grey or plastic:** the setup script didn't run or didn't find the model. Name the model
  `SpookyHarvestStall`, or select it, and run the script again (it's safe to re-run).
- **Glass jars solid:** the transparency flag in the name was lost. Check the name still ends with `__T55__NC`.
- **Sign text missing:** check the sign part is still named `Sign__SignBoard__WoodPlanks__422A1B`.
