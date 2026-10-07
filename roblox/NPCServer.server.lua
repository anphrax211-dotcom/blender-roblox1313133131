-- NPCServer (Script in ServerScriptService)
-- Rigs the Tower of Pets NPCs and adds their Talk prompts. Keep NPCDirector next to this script.
local Director = require(script.Parent:WaitForChild("NPCDirector"))
Director.Start()
