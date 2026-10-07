-- NPCAnimator (ModuleScript, used by the NPCClient LocalScript)
-- Plays the Tower of Pets NPC animations on a rigged NPC model (see NPCRig) by driving the
-- Motor6D.Transform of every joint each frame, plus the small "alive" details:
--   idle loop, layered clips (Talk / Wave / Point / Nod / Shake / Celebrate / Think / Bow),
--   blinking, a talking mouth, head/torso look-at, floating props and a glow pulse on Neon parts.

local Core = require(script.Parent.NPCAnimationCore)
local Data = require(script.Parent.NPCAnimationData)

local Animator = {}
Animator.__index = Animator

local JOINT_OF = { -- Motor6D name -> animated part (pose key)
	Root = "LowerTorso", Waist = "UpperTorso", Neck = "Head",
	RightShoulder = "RightUpperArm", RightElbow = "RightLowerArm", RightWrist = "RightHand",
	LeftShoulder = "LeftUpperArm", LeftElbow = "LeftLowerArm", LeftWrist = "LeftHand",
	RightHip = "RightUpperLeg", RightKnee = "RightLowerLeg", RightAnkle = "RightFoot",
	LeftHip = "LeftUpperLeg", LeftKnee = "LeftLowerLeg", LeftAnkle = "LeftFoot",
}
local POSE_JOINTS = {}
for _, part in JOINT_OF do
	table.insert(POSE_JOINTS, part)
end

local FADE_IN, FADE_OUT = 0.2, 0.25
local rad = math.rad

-- prepared (and mirrored where needed) clips per gesture side, shared by all animators
local prepared = { Right = {}, Left = {} }
for name, clip in Data.Clips do
	prepared.Right[name] = clip
	prepared.Left[name] = if clip.sided then Core.mirrorClip(clip) else clip
end

-- which local axis of a part points along the character's up / right
local function axisAlong(part, dir)
	local cf = part.CFrame
	local best, bestDot = "Y", -1
	for axis, v in { X = cf.RightVector, Y = cf.UpVector, Z = cf.LookVector } do
		local d = math.abs(v:Dot(dir))
		if d > bestDot then
			best, bestDot = axis, d
		end
	end
	return best
end

local function scaledSize(base, axisUp, axisWide, upMul, wideMul)
	local x, y, z = base.X, base.Y, base.Z
	local function mul(axis, m)
		if axis == "X" then x *= m elseif axis == "Y" then y *= m else z *= m end
	end
	mul(axisUp, upMul)
	if axisWide ~= axisUp then
		mul(axisWide, wideMul)
	end
	return Vector3.new(x, y, z)
end

function Animator.new(model)
	local key = model:GetAttribute("NPCKey")
	local cfg = Data.NPCs[key]
	assert(cfg, "no animation data for NPC " .. tostring(key))
	local self = setmetatable({}, Animator)
	self.model = model
	self.key = key
	self.cfg = cfg
	self.scale = model:GetAttribute("NPCScale") or 3.5714
	self.hrp = model:WaitForChild("HumanoidRootPart")
	self.gesture = cfg.gesture or "Right"
	self.clips = prepared[self.gesture]
	-- forearm of the gesture hand bent in the rest pose (holding a prop): gesture clips are
	-- authored with a straight arm, so they unbend it while they play
	self.bend = if cfg.bend and (cfg.bend[self.gesture] or 0) > 1 then cfg.bend[self.gesture] else 0
	self.idle = self.clips[cfg.idle or "Idle"]
	self.t = math.random() * 4 -- desync the idles
	self.pose = {}
	self.overlays = {}
	self.motors = {}
	self.look = { yaw = 0, pitch = 0 }
	self.lookTarget = nil
	self.speakingUntil = 0
	self.nextBlink = 1 + math.random() * 3
	self.blinkUntil = 0
	self.eyesClosed = false
	self.mouthOpen = 0

	for _, d in model:GetDescendants() do
		if d:IsA("Motor6D") and JOINT_OF[d.Name] then
			self.motors[JOINT_OF[d.Name]] = d
		end
	end

	local up, right = self.hrp.CFrame.UpVector, self.hrp.CFrame.RightVector
	local function face(part)
		return { part = part, base = part.Size, up = axisAlong(part, up), wide = axisAlong(part, right) }
	end
	self.eyes, self.mouth, self.glow, self.floats = {}, nil, {}, {}
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			if string.sub(d.Name, 1, 8) == "Head_Eye" then
				table.insert(self.eyes, face(d))
			elseif d.Name == "Head_Smile" then
				self.mouth = face(d)
			end
			if d.Material == Enum.Material.Neon then
				table.insert(self.glow, { part = d, base = d.Color, phase = #self.glow * 0.7 })
			end
		end
	end
	-- floating props: weld groups whose C0 we bob / spin around the group's centre
	for gi, group in cfg.floats or {} do
		local welds = {}
		for _, name in group.parts do
			local p = model:FindFirstChild(name, true)
			local w = p and p:FindFirstChild("PropFloat")
			if w then
				table.insert(welds, { weld = w, base = w.C0 })
			end
		end
		if #welds > 0 then
			local p0 = welds[1].weld.Part0
			local centre = Vector3.zero
			for _, w in welds do
				centre += w.base.Position
			end
			table.insert(self.floats, {
				welds = welds,
				centre = centre / #welds,
				up = p0.CFrame:VectorToObjectSpace(up),
				bob = (group.bob or 0) * self.scale,
				spin = rad(group.spin or 0),
				sway = rad(group.sway or 0),
				phase = group.phase or gi * 0.9,
			})
		end
	end
	return self
end

-- play a clip on top of the idle. Looping clips run until :Stop(name).
function Animator:Play(name)
	local clip = self.clips[name]
	if not clip then
		warn("NPCAnimator: unknown clip " .. tostring(name))
		return
	end
	for i = #self.overlays, 1, -1 do
		if self.overlays[i].name == name then
			table.remove(self.overlays, i)
		end
	end
	table.insert(self.overlays, { name = name, clip = clip, time = 0, stoppedAt = nil })
end

function Animator:Stop(name)
	for _, ov in self.overlays do
		if ov.name == name and not ov.stoppedAt then
			ov.stoppedAt = ov.time
		end
	end
end

function Animator:IsPlaying(name)
	for _, ov in self.overlays do
		if ov.name == name and not ov.stoppedAt then
			return true
		end
	end
	return false
end

-- talk for about as long as it takes to read `text` (with an optional gesture first)
function Animator:Speak(text, gesture, now)
	local duration = 1.0 + 0.055 * #(text or "")
	if gesture and gesture ~= "" and gesture ~= "Talk" then
		self:Play(gesture)
	end
	self:Play("Talk")
	self.speakingUntil = now + duration
	return duration
end

-- world position the NPC should look at (or nil)
function Animator:SetLookTarget(pos)
	self.lookTarget = pos
end

function Animator:Update(dt, now)
	self.t += dt
	local pose = self.pose
	Core.clearPose(pose, POSE_JOINTS)
	Core.blendClip(pose, self.idle, self.t, 1)

	-- stop talking when the line is done
	if self.speakingUntil > 0 and now >= self.speakingUntil then
		self.speakingUntil = 0
		self:Stop("Talk")
	end
	local i = 1
	while i <= #self.overlays do
		local ov = self.overlays[i]
		ov.time += dt
		local w = Core.overlayWeight(ov.clip, ov.time, FADE_IN, FADE_OUT, ov.stoppedAt)
		local done = (ov.stoppedAt and ov.time - ov.stoppedAt >= FADE_OUT) or (not ov.clip.loop and ov.time >= ov.clip.length)
		if done then
			table.remove(self.overlays, i)
		else
			Core.blendClip(pose, ov.clip, ov.time, w)
			if ov.clip.sided and self.bend > 0 then
				local elbow = pose[self.gesture .. "LowerArm"]
				elbow[1] -= self.bend * w
			end
			i += 1
		end
	end

	-- look at the target (head 70 % / torso 30 % of the turn)
	local yaw, pitch = 0, 0
	if self.lookTarget then
		local head = self.motors.Head and self.motors.Head.Part1
		local from = head and head.Position or self.hrp.Position
		local d = self.hrp.CFrame:VectorToObjectSpace(self.lookTarget - from)
		local y, p, ok = Core.lookAngles(d.X, d.Y, d.Z, 60, 25)
		if ok then
			yaw, pitch = y, p
		end
	end
	local k = 1 - math.exp(-dt * 5)
	self.look.yaw += (yaw - self.look.yaw) * k
	self.look.pitch += (pitch - self.look.pitch) * k
	pose.Head[2] += self.look.yaw * 0.7
	pose.Head[1] += self.look.pitch * 0.8
	pose.UpperTorso[2] += self.look.yaw * 0.3

	local s = self.scale
	for part, motor in self.motors do
		local p = pose[part]
		motor.Transform = CFrame.new(p[4] * s, p[5] * s, p[6] * s)
			* CFrame.Angles(0, rad(p[2]), 0) * CFrame.Angles(rad(p[1]), 0, 0) * CFrame.Angles(0, 0, rad(p[3]))
	end

	-- blink
	if self.t >= self.nextBlink then
		self.blinkUntil = self.t + 0.12
		self.nextBlink = self.t + 2.5 + math.random() * 3
	end
	local closed = self.t < self.blinkUntil
	if closed ~= self.eyesClosed then -- only touch Size when the state changes
		self.eyesClosed = closed
		for _, e in self.eyes do
			e.part.Size = if closed then scaledSize(e.base, e.up, e.wide, 0.12, 1.1) else e.base
		end
	end
	-- talking mouth
	if self.mouth then
		local open = if self.speakingUntil > 0 then Core.mouthOpen(self.t) else 0
		if open > 0 or self.mouthOpen ~= 0 then
			self.mouthOpen = open
			self.mouth.part.Size = scaledSize(self.mouth.base, self.mouth.up, self.mouth.wide, 1 + 2.6 * open, 1 - 0.25 * open)
		end
	end
	-- floating props
	for _, f in self.floats do
		local bob = f.up * (f.bob * math.sin(self.t * 2.1 + f.phase))
		local angle = if f.spin ~= 0 then f.spin * self.t else f.sway * math.sin(self.t * 1.3 + f.phase)
		local about = CFrame.new(f.centre + bob) * CFrame.fromAxisAngle(f.up, angle) * CFrame.new(-f.centre)
		for _, w in f.welds do
			w.weld.C0 = about * w.base
		end
	end
	-- gentle glow pulse on Neon parts
	for _, g in self.glow do
		g.part.Color = g.base:Lerp(Color3.new(1, 1, 1), 0.08 + 0.08 * math.sin(self.t * 3 + g.phase))
	end
end

-- put everything back to rest (used when the animator is destroyed)
function Animator:Destroy()
	for _, motor in self.motors do
		motor.Transform = CFrame.identity
	end
	for _, e in self.eyes do
		e.part.Size = e.base
	end
	if self.mouth then
		self.mouth.part.Size = self.mouth.base
	end
	for _, f in self.floats do
		for _, w in f.welds do
			w.weld.C0 = w.base
		end
	end
	for _, g in self.glow do
		g.part.Color = g.base
	end
end

return Animator
