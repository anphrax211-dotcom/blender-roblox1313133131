# Blender → Roblox egg models

## Wild eggs (`exports/*Egg.fbx`)
Explorer, Wild, RareWild, EpicWild, LegendaryWild — `blender/wild_eggs.py`, colours in `exports/wild_palette.json`.

## Boss eggs (`exports/*BossEgg.fbx`)
Rainhound, Magmaw, Crystaltusk, Granitram, Pyrocrow, Volcanox, Abyssray, Bogtoad, Elderstag.

Built to match the existing Celestial/Ember/Meadow eggs:
- Z-up, sits on z=0, 1.68 wide × 1.96 tall body on a 0.07 voxel grid
- emblem on the front (−Y)
- one mesh per colour, named `<Egg>_<Part>__<Egg>_<Colour>`; colours in `exports/boss_palette.json`

Regenerate (Blender 4+/5, or `pip install bpy`):
```
cd blender
python3 boss_eggs.py --out ../exports            # all eggs
python3 boss_eggs.py --only Magmaw --blend       # one egg, also save .blend
python3 render_previews.py ../exports ../previews
```
Or open `blender/boss_eggs.py` in Blender's Scripting tab and run it.

## Tower of Pets NPCs (`exports/NPCs/*_NPC.fbx`)
12 redesigned lobby NPCs (Shop, Egg, Trading, Upgrades, Pets, Leaderboards, Tower Guide,
Tower Entrance, Codes, Daily Rewards, Index, Settings) — `blender/tower_npcs.py` →
`blender/TowerOfPets_NPCs.blend`. Roblox R15-proportioned blocky bodies (~1.49 m / 5.3 studs),
R15 part names with joint-pivot origins; every other part is `<Bone>_<Item>` with a `bone`
custom property. Previews: `previews/NPCs_Lineup.png`, `previews/NPCs_Turnarounds.png`.

## NPC animations (`roblox/`, `blender/npc_animations.py`)
Idle / IdleHover / Talk / Wave / Point / Nod / Shake / Celebrate / Think / Bow, defined once in
`blender/npc_animations.py`: baked to Blender actions on R15 armatures
(`blender/TowerOfPets_NPCs_Animated.blend`, demo reel on each NPC's NLA track) and exported to
`roblox/NPCAnimationData.lua`. The Roblox scripts in `roblox/` rig the imported NPCs with Motor6Ds
and play the clips plus blinking, talking mouth, look-at, floating props, speech bubbles and a
Talk prompt — no animation uploads. Install steps: `roblox/README.md`. Tests:
`python3 roblox/tests/run_tests.py`.
