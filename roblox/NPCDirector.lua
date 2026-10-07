-- NPCDirector (ModuleScript in ServerScriptService)
-- Server side of the Tower of Pets NPCs:
--   * finds the 12 NPC models in Workspace and rigs them (NPCRig)
--   * gives each a "Talk" ProximityPrompt that speaks the next line from NPCAnimationData
--   * lets your own game code make NPCs speak or play an animation:
--
--       local Director = require(game.ServerScriptService.NPCDirector)
--       Director.Say("Shop", "Thanks for buying!", "Celebrate")   -- line + optional gesture
--       Director.Play("Egg", "Wave")                              -- just an animation
--       Director.Talked.Event:Connect(function(player, npcKey) ... end)  -- open your shop UI etc.
--
-- Animations themselves run on every client (NPCClient), driven by attributes on the model:
--   Action / ActionId    -> play a clip;   Speech / SpeechGesture / SpeechId -> say a line

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("NPCAnimation")
local Data = require(Shared:WaitForChild("NPCAnimationData"))
local Rig = require(Shared:WaitForChild("NPCRig"))

local Director = {}
Director.Models = {} -- npcKey -> Model
Director.Talked = Instance.new("BindableEvent") -- (player, npcKey) after a player talks to an NPC

local lineIndex = {}

local function findModel(key)
	local want = string.lower(key .. "_NPC")
	for _, d in workspace:GetDescendants() do
		if d:IsA("Model") and string.lower(d.Name) == want then
			return d
		end
	end
	return nil
end

local function resolve(target)
	if typeof(target) == "Instance" then
		return target
	end
	return Director.Models[target]
end

function Director.Play(target, clipName)
	local model = resolve(target)
	if not model then
		warn("NPCDirector.Play: no NPC " .. tostring(target))
		return
	end
	model:SetAttribute("Action", clipName)
	model:SetAttribute("ActionId", (model:GetAttribute("ActionId") or 0) + 1)
end

function Director.Say(target, text, gesture)
	local model = resolve(target)
	if not model then
		warn("NPCDirector.Say: no NPC " .. tostring(target))
		return
	end
	model:SetAttribute("Speech", text)
	model:SetAttribute("SpeechGesture", gesture or "")
	model:SetAttribute("SpeechId", (model:GetAttribute("SpeechId") or 0) + 1)
end

local function addPrompt(model, key, cfg)
	local hrp = model.PrimaryPart
	local att = Instance.new("Attachment")
	att.Name = "TalkPromptAttachment"
	att.Position = Vector3.new(0, 1.5 * (model:GetAttribute("NPCScale") or 3.57) * 0.28, 0)
	att.Parent = hrp
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "TalkPrompt"
	prompt.ActionText = "Talk"
	prompt.ObjectText = cfg.display or key
	prompt.MaxActivationDistance = 10
	prompt.RequiresLineOfSight = false
	prompt.Parent = att
	prompt.Triggered:Connect(function(player)
		local lines = cfg.lines or {}
		if #lines > 0 then
			lineIndex[key] = (lineIndex[key] or 0) % #lines + 1
			Director.Say(model, lines[lineIndex[key]], cfg.talkGesture)
		end
		Director.Talked:Fire(player, key)
	end)
end

function Director.Start()
	for key, cfg in Data.NPCs do
		local model = findModel(key)
		if not model then
			warn(string.format("NPCDirector: model %s_NPC not found in Workspace - skipped", key))
			continue
		end
		local ok, err = pcall(Rig.build, model, key, cfg)
		if not ok then
			warn(string.format("NPCDirector: could not rig %s: %s", model.Name, tostring(err)))
			continue
		end
		Director.Models[key] = model
		addPrompt(model, key, cfg)
	end
end

return Director
