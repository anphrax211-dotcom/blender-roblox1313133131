-- NPCClient (LocalScript in StarterPlayer > StarterPlayerScripts)
-- Animates every rigged Tower of Pets NPC on this client: idle, look at nearby players,
-- wave when you walk up, talk (mouth + gestures + speech bubble) when the server says a line,
-- and play any clip the server asks for.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")

local Shared = ReplicatedStorage:WaitForChild("NPCAnimation")
local NPCAnimator = require(Shared:WaitForChild("NPCAnimator"))

local GREET_DISTANCE = 14 -- studs: wave when the local player walks this close
local GREET_COOLDOWN = 30 -- seconds between greetings per NPC
local LOOK_DISTANCE = 22 -- studs: turn the head towards the nearest player
local ANIMATE_DISTANCE = 160 -- studs: NPCs further away than this are not updated

local player = Players.LocalPlayer
local animators = {} -- model -> state

local function bubble(model, text)
	local head = model:FindFirstChild("Head", true)
	if not head then
		return
	end
	local ok = pcall(function()
		TextChatService:DisplayBubble(head, text)
	end)
	if not ok then
		pcall(function()
			game:GetService("Chat"):Chat(head, text)
		end)
	end
end

local function attach(model)
	if animators[model] or not model:GetAttribute("NPCRigged") then
		return
	end
	local motors = 0
	for _, d in model:GetDescendants() do
		if d:IsA("Motor6D") then
			motors += 1
		end
	end
	if motors < 15 or not model.PrimaryPart then
		return -- not fully replicated yet; the periodic scan tries again
	end
	local ok, anim = pcall(NPCAnimator.new, model)
	if not ok then
		warn("NPCClient: " .. tostring(anim))
		return
	end
	local state = { anim = anim, greetedAt = -math.huge, near = false }
	animators[model] = state
	model:GetAttributeChangedSignal("ActionId"):Connect(function()
		local clip = model:GetAttribute("Action")
		if clip then
			anim:Play(clip)
		end
	end)
	model:GetAttributeChangedSignal("SpeechId"):Connect(function()
		local text = model:GetAttribute("Speech") or ""
		anim:Speak(text, model:GetAttribute("SpeechGesture"), os.clock())
		bubble(model, text)
	end)
	model.Destroying:Connect(function()
		animators[model] = nil
	end)
end

local function scan()
	for _, d in workspace:GetDescendants() do
		if d:IsA("Model") and d:GetAttribute("NPCRigged") then
			attach(d)
		end
	end
end

local function watch(model)
	if model:IsA("Model") then
		model:GetAttributeChangedSignal("NPCRigged"):Connect(function()
			attach(model)
		end)
		attach(model)
	end
end

scan()
workspace.DescendantAdded:Connect(watch)

local function characterHeads()
	local heads = {}
	for _, p in Players:GetPlayers() do
		local head = p.Character and p.Character:FindFirstChild("Head")
		if head then
			heads[p] = head.Position
		end
	end
	return heads
end

local nextScan = 0
local step = RunService.PreSimulation or RunService.Stepped
step:Connect(function(a, b)
	local dt = if typeof(b) == "number" then b else a -- Stepped passes (time, dt)
	local now = os.clock()
	if now >= nextScan then -- pick up NPCs that streamed in or finished replicating
		nextScan = now + 2
		scan()
	end
	local heads = characterHeads()
	local myHead = heads[player]
	for model, state in animators do
		local hrp = model.PrimaryPart
		if not hrp then
			continue
		end
		local pos = hrp.Position
		if myHead and (myHead - pos).Magnitude > ANIMATE_DISTANCE then
			continue
		end
		-- look at the nearest player (prefer this player when tied)
		local best, bestDist = nil, LOOK_DISTANCE
		for p, h in heads do
			local dist = (h - pos).Magnitude - (if p == player then 1 else 0)
			if dist < bestDist then
				best, bestDist = h, dist
			end
		end
		state.anim:SetLookTarget(best)
		-- wave when this player walks up
		if myHead then
			local near = (myHead - pos).Magnitude < GREET_DISTANCE
			if near and not state.near and now - state.greetedAt > GREET_COOLDOWN then
				state.greetedAt = now
				if state.anim.speakingUntil == 0 then
					state.anim:Play("Wave")
				end
			end
			state.near = near
		end
		state.anim:Update(dt, now)
	end
end)
