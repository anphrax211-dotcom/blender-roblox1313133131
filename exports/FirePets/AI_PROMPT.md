Attach these files from `exports/FirePets/` to the message: `IMPORT.md`, `manifest.json` and the four
`<Pet>_Texture.png` images. Then paste everything below the line.

---

I'm making a Roblox pet game. I imported 4 fire pet models (FBX, made in Blender) into Roblox Studio and I need
their colours and fire effects set up properly. I've attached IMPORT.md, manifest.json and the 4 texture PNGs.
If you are connected to my Roblox Studio (Roblox Studio MCP), do every step directly in Studio and check the
Output window for errors after each step. If you are NOT connected, walk me through each step: give exact clicks,
exact code, the script type, and exactly where it goes in Explorer. I'm a beginner, so keep instructions simple
and do one step at a time.

## Facts about the models
- I imported 4 files: `Ashrat.fbx`, `Cinderkit.fbx`, `Flarecat.fbx`, `Smoulderat.fbx`. Each should be a Model with
  exactly 3 MeshParts:
  - `<Pet>_Body`: body, legs, paws
  - `<Pet>_Head`: head, eyes, ears, nose, mouth, whiskers
  - `<Pet>_Fire`: tail, flames, flame markings, lava cracks, crystals
- **All the colour is in ONE texture per pet** (`<Pet>_Texture.png`, 1024×1024). It's embedded in the FBX and
  shared by ALL 3 MeshParts of that pet. The parts are meant to show this texture, not a flat Color. The texture
  holds everything: fire gradients (red → orange → yellow), flame markings, eyes, nose, lava cracks.
- Each pet faces −Z (its LookVector), with the pivot at the feet. Each is about 3–3.7 studs tall.
- Every MeshPart is under 20k triangles (each pet is about 22–38k in total).

## What I need you to do
1. **Find the models.** Find the 4 pet Models in Workspace (they may be named after the file or be inside a
   folder). Tell me what you found. If a pet came in as one merged MeshPart, or with different part names, tell
   me and help me re-import it with **Merge Meshes OFF** and **Scale Unit = Stud**.
2. **Check the textures.** For each of the 12 MeshParts, check `TextureID`. If it's empty, or the part looks
   plain grey or white:
   - help me upload that pet's `<Pet>_Texture.png` (Asset Manager / Bulk Import → Images, or the Creator Hub);
   - put the resulting `rbxassetid://` id into `TextureID` on ALL 3 parts of that pet.
3. **Make the texture show correctly.** On all 12 parts:
   - `Material = SmoothPlastic`. NOT Neon: Neon hides the texture.
   - `Color = white (255,255,255)`, so the texture isn't tinted.
   - `Transparency = 0`, `Reflectance = 0`, `DoubleSided = false`.
   - Do NOT replace the texture with a SurfaceAppearance or a flat colour unless I ask.
4. **Make the fire glow.** Add these to each pet's `<Pet>_Fire` part:
   - A `PointLight`: Brightness 1.2, Range 6, Shadows off. Colours:
     - Ashrat (255,140,40)
     - Cinderkit (255,150,40)
     - Flarecat (255,170,70)
     - Smoulderat (255,80,30)
   - A small ember `ParticleEmitter`, subtle, not a big fire:
     - Rate 4, Lifetime 0.6–1.2, Speed 0.5–1.5, SpreadAngle (30,30)
     - Size from 0.15 to 0, LightEmission 1
     - Color sequence orange (255,150,40) → red (255,60,20)
     - Acceleration (0,2,0)
     - The default sparkle texture is fine.
5. **Set each pet up as one movable model.**
   - Set `PrimaryPart = <Pet>_Body`.
   - Weld `<Pet>_Head` and `<Pet>_Fire` to `<Pet>_Body` with `WeldConstraint`s.
   - On all 3 parts: `CanCollide = false`, `CanTouch = false`, `CanQuery = false`, `Massless = true`,
     `CastShadow = true`.
   - Leave them unanchored if my pet-follow system moves them with physics. Anchor them if they're just for
     display. Ask me which.
6. **Store them for scripts.** Put the 4 finished Models into `ReplicatedStorage.Pets` (a Folder), named exactly
   `Ashrat`, `Cinderkit`, `Flarecat`, `Smoulderat`, so my pet scripts can clone them.
7. **Check your work.** Show me how each pet looks from the front and from the side (or tell me exactly what to
   look at). The pets should look like this:
   - **Ashrat:** charcoal rat, big orange-lined ears, orange paws, orange nose, buck teeth, glowing orange swirls by
     the eyes, flame markings, curled orange-to-yellow fire tail.
   - **Cinderkit:** black kitten, flame crest on the forehead, yellow flame chest ruff, amber paws, flame markings,
     big yellow flame tail with orange and red inside.
   - **Flarecat:** pale gold cat, pink inner ears, orange flame mane all around the head, yellow chest ruff,
     orange paws, big flame tail.
   - **Smoulderat:** stout dark charcoal rat, red paws, red-orange crystals on its head and back, glowing yellow
     lava cracks all over its body, curled fire tail.

## If something looks wrong
- **Whole pet grey or white:** the texture isn't applied (step 2).
- **Colours look washed out or tinted:** the part `Color` isn't white, or the material isn't SmoothPlastic
  (step 3).
- **Pet is huge, tiny, sideways or upside down:** re-import with Scale Unit = Stud. The pet's front should face
  −Z. Fix the rotation with the Model pivot, not by rotating parts separately.
- **Texture looks scrambled or stretched on the mesh:** tell me. It means the UVs didn't import and I'll need to
  re-export.

Please don't change the mesh shapes. Only fix the colours and textures and add the glow, particles and welds.
