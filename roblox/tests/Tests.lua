-- NPC animation test-suite (run with: python3 roblox/tests/run_tests.py)
-- Uses the real modules + Mock.lua. Every NPC is rebuilt from the Blender fixture, rotated and
-- moved in the world, rigged, solved through its joints and animated.

local Core = require(NPCFolder.NPCAnimationCore)
local Data = require(NPCFolder.NPCAnimationData)
local Rig = require(NPCFolder.NPCRig)
local Animator = require(NPCFolder.NPCAnimator)

local pass, fail = 0, 0
local function check(cond, msg)
	if cond then
		pass += 1
	else
		fail += 1
		print("FAIL: " .. msg)
	end
end
local function near(a, b, eps)
	return math.abs(a - b) <= (eps or 1e-4)
end

-- ---------------------------------------------------------------- core maths
local out = { 0, 0, 0, 0, 0, 0 }
local keys = { { 0, 0, 0, 0, 0, 0, 0 }, { 1, 10, 0, 0, 0, 2, 0 } }
Core.sampleKeys(keys, 0.5, out)
check(near(out[1], 5) and near(out[5], 1), "sampleKeys midpoint")
Core.sampleKeys(keys, 0.25, out)
check(out[1] < 2.5 and out[1] > 0, "sampleKeys eases in")
Core.sampleKeys(keys, -1, out)
check(out[1] == 0, "sampleKeys clamps before start")
Core.sampleKeys(keys, 3, out)
check(out[1] == 10, "sampleKeys clamps after end")
check(near(Core.clipTime({ length = 4, loop = true } :: any, 5), 1), "loop wraps")
check(near(Core.clipTime({ length = 4, loop = false } :: any, 5), 4), "one-shot clamps")
check(Core.mirrorName("RightUpperArm") == "LeftUpperArm" and Core.mirrorName("LeftFoot") == "RightFoot"
	and Core.mirrorName("Head") == "Head", "mirrorName")
local wl = Core.mirrorClip(Data.Clips.Wave)
check(wl.joints.LeftUpperArm ~= nil and wl.joints.LeftLowerArm ~= nil and wl.joints.LeftHand ~= nil,
	"mirrored wave animates the left arm")
check(near(wl.joints.LeftUpperArm[2][4], -Data.Clips.Wave.joints.RightUpperArm[2][4]), "mirror negates rz")
local yaw, pitch, ok = Core.lookAngles(1, 0, 0, 60, 25)
check(ok and near(yaw, -60), "look right = negative yaw (clamped)")
yaw, pitch, ok = Core.lookAngles(0, 1, -1, 60, 25)
check(ok and near(yaw, 0) and near(pitch, 25), "look up = positive pitch (clamped)")
_, _, ok = Core.lookAngles(0, 0, 1, 60, 25)
check(not ok, "target behind is ignored")
check(near(Core.overlayWeight(Data.Clips.Wave, 0.1, 0.2, 0.25), 0.5), "fade in")
check(near(Core.overlayWeight(Data.Clips.Talk, 1.0, 0.2, 0.25, 0.9), 0.6), "fade out after stop")

local VALID = {}
for _, n in Rig.BODY do
	VALID[n] = true
end
for name, clip in Data.Clips do
	for j, ks in clip.joints do
		check(VALID[j] == true, name .. ": unknown joint " .. j)
		for i = 2, #ks do
			check(ks[i][1] > ks[i - 1][1], name .. "." .. j .. ": keys not sorted")
		end
		if clip.loop then
			local a, b = ks[1], ks[#ks]
			local same = true
			for c = 2, 7 do
				same = same and near(a[c], b[c], 1e-3)
			end
			check(same and near(b[1], clip.length), name .. "." .. j .. ": loop does not close")
		else
			for c = 2, 7 do
				check(near(ks[1][c], 0, 1e-3) and near(ks[#ks][c], 0, 1e-3), name .. "." .. j .. ": one-shot must start/end at rest")
			end
		end
	end
end

-- ---------------------------------------------------------------- rig + animate every NPC
local ROT = CFrame.fromAxisAngle(Vector3.yAxis, math.rad(90)) -- model turned after import
local MOVE = Vector3.new(50, 3, -20)
local TURN = ROT * CFrame.fromAxisAngle(Vector3.yAxis, 0)

local function buildModel(key, parts)
	local model = Instance.new("Model")
	model.Name = key .. "_NPC"
	for name, p in parts do
		local mp = Instance.new("MeshPart")
		mp.Name = name
		mp.Size = Vector3.new(p.s[1], p.s[2], p.s[3])
		mp.CFrame = CFrame.new(MOVE) * TURN * CFrame.new(Vector3.new(p.c[1], p.c[2], p.c[3]))
		mp.Anchored = true
		if string.find(name, "Glow") or string.find(name, "Crystal") then
			mp.Material = Enum.Material.Neon
		end
		mp.Parent = model
	end
	model.Parent = workspace
	return model
end

local function snapshot(model)
	local s = {}
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			s[d] = d.CFrame
		end
	end
	return s
end

local function maxError(model, snap, skip)
	local worst = 0
	for part, c in snap do
		if skip and skip[part.Name] then
			continue
		end
		local d = (part.CFrame.Position - c.Position).Magnitude
		d += (part.CFrame.RightVector - c.RightVector).Magnitude + (part.CFrame.UpVector - c.UpVector).Magnitude
		worst = math.max(worst, d)
	end
	return worst
end

local function run(anim, model, seconds, t0)
	local steps = math.floor(seconds * 60 + 0.5)
	for i = 1, steps do
		anim:Update(1 / 60, t0 + i / 60)
	end
	Mock.solve(model)
	return t0 + steps / 60
end

local frontWorld = TURN * Vector3.zAxis -- fixture faces +Z, as the FBX importer brings it in
local rightWorld = TURN * -Vector3.xAxis

for key, parts in Fixture do
	local cfg = Data.NPCs[key]
	check(cfg ~= nil, key .. ": no animation data")
	local model = buildModel(key, parts)
	local snap = snapshot(model)
	local hrp = Rig.build(model, key, cfg)
	check(model.PrimaryPart == hrp and hrp.Anchored, key .. ": anchored HumanoidRootPart is PrimaryPart")
	local motors, welds, floats = 0, 0, 0
	for _, d in model:GetDescendants() do
		if d.ClassName == "Motor6D" then motors += 1 end
		if d.ClassName == "WeldConstraint" then welds += 1 end
		if d.ClassName == "Weld" then floats += 1 end
	end
	local nparts = 0
	for _ in parts do
		nparts += 1
	end
	check(motors == 15, key .. ": 15 Motor6Ds, got " .. motors)
	check(welds + floats == nparts - 15, key .. ": every non-body part welded")
	local floatParts = 0
	for _, g in cfg.floats or {} do
		floatParts += #g.parts
	end
	check(floats == floatParts, key .. ": float props use Welds")
	check(near(model:GetAttribute("NPCScale"), 1 / 0.28, 1e-3), key .. ": scale measured as 3.571 studs/m")
	check(hrp.CFrame.UpVector:Dot(Vector3.yAxis) > 0.999, key .. ": frame up")
	check(hrp.CFrame.LookVector:Dot(frontWorld) > 0.999, key .. ": frame faces the front")
	local placed = Mock.solve(model)
	local count = 0
	for _ in placed do
		count += 1
	end
	check(count == nparts + 1, key .. ": every part reachable through joints")
	local err = maxError(model, snap)
	check(err < 1e-3, string.format("%s: rest pose drifts by %.5f", key, err))

	-- idle only: small motion
	local anim = Animator.new(model)
	local t = run(anim, model, 1.0, 0)
	local floating = {}
	for _, g in cfg.floats or {} do
		for _, n in g.parts do
			floating[n] = true
		end
	end
	check(maxError(model, snap, floating) < 1.0, key .. ": idle stays subtle (floating props excluded)")

	local P = Rig.partsByName(model)
	local side = cfg.gesture
	local other = if side == "Right" then "Left" else "Right"
	local shoulderY = MOVE.Y + cfg.pivots.RightUpperArm[2] / 0.28
	local otherHandRest = snap[P[other .. "Hand"]].Position

	-- Wave: gesture hand up above the shoulder, other hand stays down
	anim:Play("Wave")
	t = run(anim, model, 1.0, t)
	check(P[side .. "Hand"].Position.Y > shoulderY, key .. ": Wave raises the " .. side .. " hand")
	check((P[other .. "Hand"].Position - otherHandRest).Magnitude < 1.2, key .. ": Wave leaves the other hand")
	t = run(anim, model, 2.0, t)
	check(#anim.overlays == 0, key .. ": Wave finishes and is removed")

	-- Point: gesture hand reaches forward
	anim:Play("Point")
	t = run(anim, model, 0.9, t)
	local o = hrp.CFrame:PointToObjectSpace(P[side .. "Hand"].Position) -- x right, y up, z back
	check(o.Z < -1.0 and o.Y > 1.2, string.format("%s: Point holds the hand out in front at shoulder height (z %.2f, y %.2f)",
		key, o.Z, o.Y))
	t = run(anim, model, 1.5, t)

	-- Celebrate: whole body hops, both hands up
	anim:Play("Celebrate")
	t = run(anim, model, 0.45, t)
	check(P.LowerTorso.Position.Y > snap[P.LowerTorso].Position.Y + 0.3, key .. ": Celebrate hops")
	check(P.RightHand.Position.Y > shoulderY - 0.3 and P.LeftHand.Position.Y > shoulderY - 0.3,
		key .. ": Celebrate raises both hands")
	t = run(anim, model, 1.5, t)

	-- Bow: head goes forward and down
	local headRest = snap[P.Head].Position - snap[P.LowerTorso].Position -- relative to the hips (Entrance hovers)
	anim:Play("Bow")
	t = run(anim, model, 0.8, t)
	local headNow = P.Head.Position - P.LowerTorso.Position
	check((headNow - headRest):Dot(frontWorld) > 0.4 and headNow.Y < headRest.Y, key .. ": Bow leans forward")
	t = run(anim, model, 1.5, t)

	-- Speak: talk loop + mouth while speaking, then stops by itself
	local mouth = P.Head_Smile
	local mouthSize = mouth and mouth.Size
	local dur = anim:Speak("Hello there, welcome to the tower!", cfg.talkGesture, t)
	check(anim:IsPlaying("Talk"), key .. ": Speak starts Talk")
	local moved = false
	for _ = 1, 30 do
		t = run(anim, model, 1 / 60, t)
		if mouth and (mouth.Size - mouthSize).Magnitude > 1e-3 then
			moved = true
		end
	end
	check(moved or mouth == nil, key .. ": mouth moves while talking")
	t = run(anim, model, dur + 0.5, t)
	check(not anim:IsPlaying("Talk"), key .. ": Talk stops after the line")
	t = run(anim, model, 3.0, t)
	if mouth then
		check((mouth.Size - mouthSize).Magnitude < 1e-6, key .. ": mouth closes again")
	end

	-- floating props move relative to the hand
	for _, g in cfg.floats or {} do
		local p = P[g.parts[1]]
		local weld = p:FindFirstChild("PropFloat")
		check(weld ~= nil and weld.C0 ~= nil, key .. ": float weld for " .. g.parts[1])
	end

	-- look-at: target to the character's right turns the face right
	anim:SetLookTarget(P.Head.Position + rightWorld * 10)
	t = run(anim, model, 2.0, t)
	local faceDir = P.Head.CFrame:VectorToObjectSpace(frontWorld)
	local headFront = P.Head.CFrame * faceDir - P.Head.Position
	local restFront = snap[P.Head] * faceDir - snap[P.Head].Position
	check(headFront:Dot(rightWorld) > restFront:Dot(rightWorld) + 0.4, key .. ": head turns towards a player on its right")
	anim:SetLookTarget(nil)

	anim:Destroy()
	Mock.solve(model)
	check(maxError(model, snap) < 1e-3, key .. ": Destroy restores the rest pose")
end

-- ---------------------------------------------------------------- server director + client glue
local Director = require(ServerFolder.NPCDirector)
Director.Start() -- re-rigs the already-rigged models (must be idempotent)
local talked = nil
Director.Talked.Event:Connect(function(player, key)
	talked = key
end)
local n = 0
for key, model in Director.Models do
	n += 1
	local prompt = model:FindFirstChild("TalkPrompt", true)
	check(prompt ~= nil, key .. ": has a Talk prompt")
	prompt.Triggered:Fire({ Name = "Tester" })
	check(model:GetAttribute("SpeechId") == 1 and model:GetAttribute("Speech") == Data.NPCs[key].lines[1],
		key .. ": prompt says the first line")
	check(talked == key, key .. ": Talked event fired")
	local motors = 0
	for _, d in model:GetDescendants() do
		if d.ClassName == "Motor6D" then motors += 1 end
	end
	check(motors == 15, key .. ": rebuild keeps exactly 15 Motor6Ds")
end
check(n == 12, "Director rigged all 12 NPCs, got " .. n)

-- client: attach animators, react to attributes, greet, show bubbles
RunClient()
local shop = Director.Models.Shop
local localHead = LocalCharacter.Head
localHead.CFrame = shop.PrimaryPart.CFrame * CFrame.new(0, 1, -30)
for i = 1, 10 do
	PreSimulation:Fire(1 / 60)
end
localHead.CFrame = shop.PrimaryPart.CFrame * CFrame.new(0, 1, -8) -- walk up to the shop NPC
for i = 1, 30 do
	PreSimulation:Fire(1 / 60)
end
Mock.solve(shop)
local P = Rig.partsByName(shop)
check(P.RightHand.Position.Y > shop.PrimaryPart.Position.Y + 2, "client: Shop NPC waves when you walk up")
Director.Say("Shop", "Thanks for buying!", "Celebrate")
PreSimulation:Fire(1 / 60)
check(Bubbles[#Bubbles] == "Thanks for buying!", "client: speech bubble shown")
Director.Play("Egg", "Nod")
for i = 1, 20 do
	PreSimulation:Fire(1 / 60)
end
Mock.solve(Director.Models.Egg)
check(true, "client: Play runs without errors")

print(string.format("%d passed, %d failed", pass, fail))
if fail > 0 then
	error("tests failed")
end
