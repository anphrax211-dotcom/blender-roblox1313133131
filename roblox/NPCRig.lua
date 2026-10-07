-- NPCRig (ModuleScript)
-- Turns an imported Tower of Pets NPC model (loose MeshParts from the FBX) into an animatable
-- R15-style rig: an anchored HumanoidRootPart, Motor6D joints between the R15 body parts at the
-- pivots measured in Blender, and welds that attach every other part to its body part.
-- Runs on the server so the joints replicate; the client animates the joints (NPCAnimator).
-- Works whatever way the model was rotated or scaled after import: the character frame is
-- measured from the parts themselves.

local Rig = {}

Rig.BODY = {
	"LowerTorso", "UpperTorso", "Head",
	"RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperArm", "LeftLowerArm", "LeftHand",
	"RightUpperLeg", "RightLowerLeg", "RightFoot", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
}

-- Roblox R15 joint names: { joint, Part0, Part1 }
Rig.JOINTS = {
	{ "Root", "HumanoidRootPart", "LowerTorso" },
	{ "Waist", "LowerTorso", "UpperTorso" },
	{ "Neck", "UpperTorso", "Head" },
	{ "RightShoulder", "UpperTorso", "RightUpperArm" },
	{ "RightElbow", "RightUpperArm", "RightLowerArm" },
	{ "RightWrist", "RightLowerArm", "RightHand" },
	{ "LeftShoulder", "UpperTorso", "LeftUpperArm" },
	{ "LeftElbow", "LeftUpperArm", "LeftLowerArm" },
	{ "LeftWrist", "LeftLowerArm", "LeftHand" },
	{ "RightHip", "LowerTorso", "RightUpperLeg" },
	{ "RightKnee", "RightUpperLeg", "RightLowerLeg" },
	{ "RightAnkle", "RightLowerLeg", "RightFoot" },
	{ "LeftHip", "LowerTorso", "LeftUpperLeg" },
	{ "LeftKnee", "LeftUpperLeg", "LeftLowerLeg" },
	{ "LeftAnkle", "LeftLowerLeg", "LeftFoot" },
}

local function v3(t)
	return Vector3.new(t[1], t[2], t[3])
end

-- every BasePart in the model by name (first match wins)
function Rig.partsByName(model)
	local parts = {}
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and d.Name ~= "HumanoidRootPart" and parts[d.Name] == nil then
			parts[d.Name] = d
		end
	end
	return parts
end

-- character frame (right, up, back unit vectors) + studs-per-metre scale, measured from the parts
function Rig.measure(parts, npcData)
	local lt, head = parts.LowerTorso, parts.Head
	assert(lt and head, "NPC model needs LowerTorso and Head parts")
	local cLT, cHead = v3(npcData.centers.LowerTorso), v3(npcData.centers.Head)
	local span = head.Position - lt.Position
	local scale = span.Magnitude / (cHead - cLT).Magnitude
	local up = span.Unit
	-- the eyes sit on the front of the face
	local sum, count = Vector3.zero, 0
	for name, p in parts do
		if string.sub(name, 1, 8) == "Head_Eye" then
			sum += p.Position
			count += 1
		end
	end
	local front
	if count > 0 then
		front = sum / count - head.Position
	elseif parts.Head_Smile then
		front = parts.Head_Smile.Position - head.Position
	else
		front = -head.CFrame.LookVector
	end
	front = (front - up * front:Dot(up)).Unit
	local back = -front
	local right = up:Cross(back)
	local origin = lt.Position
	local function toWorld(p) -- character-space metres -> world position
		local d = p - cLT
		return origin + (right * d.X + up * d.Y + back * d.Z) * scale
	end
	return { right = right, up = up, back = back, scale = scale, toWorld = toWorld }
end

local function isFloatProp(name, npcData)
	for _, group in npcData.floats or {} do
		for _, n in group.parts do
			if n == name then
				return true
			end
		end
	end
	return false
end

-- build (or rebuild) the rig. Returns the HumanoidRootPart.
function Rig.build(model, key, npcData)
	local parts = Rig.partsByName(model)
	for _, name in Rig.BODY do
		assert(parts[name], string.format("%s is missing body part %s", model.Name, name))
	end
	-- keep everything still while we rebuild
	for _, p in parts do
		p.Anchored = true
	end
	for _, d in model:GetDescendants() do
		if d:IsA("JointInstance") or d:IsA("WeldConstraint") then
			d:Destroy()
		end
	end
	local old = model:FindFirstChild("HumanoidRootPart")
	if old then
		old:Destroy()
	end

	local f = Rig.measure(parts, npcData)
	local function frameAt(pivotMetres)
		return CFrame.fromMatrix(f.toWorld(v3(pivotMetres)), f.right, f.up, f.back)
	end

	local hrp = Instance.new("Part")
	hrp.Name = "HumanoidRootPart"
	hrp.Size = Vector3.new(0.56, 0.56, 0.28) * f.scale -- 2 x 2 x 1 studs at Roblox scale
	hrp.CFrame = frameAt(npcData.pivots.LowerTorso)
	hrp.Transparency = 1
	hrp.Anchored = true
	hrp.CanCollide = false
	hrp.CanTouch = false
	hrp.CanQuery = false
	hrp.Parent = model
	model.PrimaryPart = hrp
	parts.HumanoidRootPart = hrp

	for _, j in Rig.JOINTS do
		local name, p0, p1 = j[1], parts[j[2]], parts[j[3]]
		local cf = frameAt(npcData.pivots[j[3]])
		local m = Instance.new("Motor6D")
		m.Name = name
		m.Part0 = p0
		m.Part1 = p1
		m.C0 = p0.CFrame:ToObjectSpace(cf)
		m.C1 = p1.CFrame:ToObjectSpace(cf)
		m.Parent = p1
	end

	local body = {}
	for _, name in Rig.BODY do
		body[name] = true
	end
	for name, p in parts do
		if body[name] or name == "HumanoidRootPart" then
			continue
		end
		local bone = string.match(name, "^([^_]+)_") or "UpperTorso"
		local p0 = parts[bone] or parts.UpperTorso
		if isFloatProp(name, npcData) then
			local w = Instance.new("Weld") -- the client moves C0 to make the prop float
			w.Name = "PropFloat"
			w.Part0 = p0
			w.Part1 = p
			w.C0 = p0.CFrame:ToObjectSpace(p.CFrame)
			w.Parent = p
		else
			local w = Instance.new("WeldConstraint")
			w.Name = "NPCWeld"
			w.Part0 = p0
			w.Part1 = p
			w.Parent = p
		end
	end

	for name, p in parts do
		if name ~= "HumanoidRootPart" then
			p.Anchored = false
			p.Massless = true
			p.CanTouch = false
			p.CanCollide = (name == "UpperTorso" or name == "LowerTorso")
			if p.Material == Enum.Material.Neon then
				p.CastShadow = false
			end
		end
	end

	-- stream each NPC to clients as one piece, so the client never sees half a rig
	pcall(function()
		model.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
	end)
	model:SetAttribute("NPCKey", key)
	model:SetAttribute("NPCScale", f.scale)
	model:SetAttribute("NPCRigged", true)
	return hrp
end

return Rig
