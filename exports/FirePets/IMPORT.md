# Fire pets: importing into Roblox Studio

`Ashrat.fbx`, `Cinderkit.fbx`, `Flarecat.fbx` and `Smoulderat.fbx` are generated from `blender/FirePets.blend` by
`blender/export_fire_pets.py`. Re-run that script after any Blender change.

## What each file contains

- **Two MeshParts:** `<Pet>_Body` (fur, face, ears, legs, paws) and `<Pet>_Fire` (tail, flames, markings, lava,
  crystals).
- **Colours:** both parts share one 1024×1024 colour texture, `<Pet>_Texture.png`. It's embedded in the FBX and
  also saved next to it. The texture holds the whole look: fire gradients, flame markings, eyes, lava cracks and
  crystals.
- **Orientation and pivot:** each pet faces Roblox −Z (the default front, `LookVector`), Y is up, and the pivot
  is between the feet on the ground.
- **Size:** 3 studs per Blender metre.

| Pet | Tall × long × wide (studs) | Triangles (Body + Fire) |
|---|---|---|
| Ashrat | 3.1 × 4.9 × 4.0 | 12.3k + 2.8k |
| Cinderkit | 3.6 × 4.4 × 3.3 | 12.4k + 6.2k |
| Flarecat | 3.7 × 4.5 × 3.4 | 11.5k + 9.8k |
| Smoulderat | 3.6 × 6.0 × 4.6 | 12.3k + 5.5k |

The length and width include the tail, which sweeps out to the pet's left. Every part is under Roblox's 20k
triangle limit.

## Import (Studio → Home or Avatar tab → Import 3D), one pet at a time

1. Pick the `.fbx` file.
2. Importer options:
   - **Scale Unit: Stud**
   - **Merge Meshes: OFF**, so Body and Fire stay separate parts
   - **Import Textures / Upload textures: ON**
3. Import. You get a Model with `<Pet>_Body` and `<Pet>_Fire`. Each MeshPart's `TextureID` is the uploaded
   texture.
4. If a part comes in grey (texture not picked up), upload `<Pet>_Texture.png` (Asset Manager → Images) and paste
   its id into **TextureID** on both MeshParts.

## Setting it up as a pet

- **Model:** set the Model's `PrimaryPart` to `<Pet>_Body` and weld `<Pet>_Fire` to it (WeldConstraint).
- **Physics:** turn off `CanCollide` on both parts, and turn on `Massless` if the pet follows a character.
- **Material:** keep `Material = SmoothPlastic`. `Neon` ignores the texture.
- **Glow (optional):** for the fire glow in-game, add a `PointLight` to `<Pet>_Fire`, e.g. colour (255,140,40),
  Brightness 1, Range 6. A `ParticleEmitter` of embers on the tail also works.
- **Size:** to make a pet bigger or smaller, use `Model:ScaleTo(n)` (e.g. `ScaleTo(0.8)`). Or change `PET_STUDS`
  in `export_fire_pets.py` and re-export.
