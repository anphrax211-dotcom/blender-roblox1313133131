# Tower of Pets NPC animations (Roblox)

Animates the 12 lobby NPCs (`exports/NPCs/*_NPC.fbx`) with **no animation uploads**:
the scripts rig each imported model with Motor6D joints and play the clips from
`NPCAnimationData` on every client.

## What the NPCs do

| When | Animation |
|---|---|
| Always | **Idle** breathing / sway / glancing around (Tower Entrance **hovers**), blinking, Neon glow pulse, floating props (egg, crystals, gift, calendar, holo panels, paw) |
| A player is within 22 studs | head + torso turn to **look at** the nearest player |
| You walk up (14 studs) | **Wave** (once every 30 s per NPC) |
| A player presses the **Talk** prompt (E) | speaks its next line: speech bubble + **Talk** loop (head nods, hand gestures, moving mouth) + its own gesture |
| Your game code asks | any clip: `Talk`, `Wave`, `Point`, `Nod`, `Shake`, `Celebrate`, `Think`, `Bow` |

Each NPC's talk gesture: Shop / Upgrades / Tower Guide **Point**, Egg / Codes **Celebrate**,
Trading / Pets **Nod**, Leaderboards / Tower Entrance **Bow**, Daily Rewards **Wave**,
Index / Settings **Think**. Gestures use the NPC's free hand; prop-holding forearms straighten
while gesturing.

## Install (Roblox Studio)

1. Import the NPC FBX files with the 3D Importer (keep the model names `Shop_NPC`, `Egg_NPC`, ...)
   and colour them with `prompts/TowerOfPets_NPCs_Studio_Prompt.md`. Skip that prompt's
   welding/anchoring step if you like: the rig script below replaces those welds.
2. **ReplicatedStorage** -> new **Folder** named `NPCAnimation`, containing four **ModuleScripts**
   (name each after its file, paste the file's contents):
   `NPCAnimationData`, `NPCAnimationCore`, `NPCRig`, `NPCAnimator`.
3. **ServerScriptService** -> **ModuleScript** `NPCDirector` (from `NPCDirector.lua`) and a
   **Script** `NPCServer` (from `NPCServer.server.lua`).
4. **StarterPlayer > StarterPlayerScripts** -> **LocalScript** `NPCClient` (from `NPCClient.client.lua`).
5. Play. The Output window warns about any NPC model it can't find.

Speech bubbles use `TextChatService:DisplayBubble`; keep bubble chat enabled
(TextChatService > BubbleChatConfiguration > Enabled).

## Use it from your game code (server)

```lua
local Director = require(game.ServerScriptService.NPCDirector)

Director.Talked.Event:Connect(function(player, npcKey)   -- "Shop", "Egg", "Daily_Rewards", ...
	if npcKey == "Shop" then
		-- open your shop UI for this player here
	end
end)

Director.Say("Shop", "Thanks for buying!", "Celebrate")  -- line + optional gesture
Director.Play("Tower_Entrance", "Bow")                   -- just an animation
```

Edit the dialogue lines, talk gestures, gesture hand and floating props in
`blender/npc_animations.py` (`NPC_CONFIG`) and re-run it to regenerate `NPCAnimationData.lua`
(or edit `NPCAnimationData.lua` directly). Tunables (greet distance, look distance, cooldown)
are at the top of `NPCClient`.

## Editing the animations

The clips are keyframes in `blender/npc_animations.py` (`CLIPS`). Running it
(`python3 blender/npc_animations.py` with the `bpy` module, or `blender -b -P npc_animations.py`)
rebuilds `blender/TowerOfPets_NPCs_Animated.blend` (R15 armatures, every clip as an action,
a demo reel on each NPC's NLA track) **and** `roblox/NPCAnimationData.lua`, so Blender and Roblox
always play the same motion.

## Tests

`python3 roblox/tests/run_tests.py` (needs the standalone `luau` CLI; set `LUAU=/path/to/luau`)
syntax-checks every script and runs them against a small Roblox API mock: every NPC is rebuilt
from the Blender data, turned and moved, rigged and solved through its joints, then checked
clip by clip (rest pose kept, wave raises the right hand, point reaches forward, hop, bow,
mouth, look-at, prompt -> speech -> bubble, rebuilding twice).
