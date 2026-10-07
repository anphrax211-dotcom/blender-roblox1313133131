--!strict
-- NPCAnimationCore (ModuleScript)
-- Pure maths for the NPC animations: keyframe sampling, left/right mirroring and blending.
-- No Roblox APIs here, so it is unit-tested outside Studio (see roblox/tests).
--
-- A pose is { [jointName] = {rx, ry, rz, tx, ty, tz} } in character space
-- (X = character right, Y = up, Z = character back; degrees and model metres).

local Core = {}

export type Keys = { { number } }
export type Clip = { length: number, loop: boolean, sided: boolean, joints: { [string]: Keys } }
export type Pose = { [string]: { number } }

function Core.smooth(u: number): number
	return u * u * (3 - 2 * u)
end

-- ease-in-out interpolation between keys; writes 6 channels into `out`
function Core.sampleKeys(keys: Keys, t: number, out: { number }): { number }
	local n = #keys
	if t <= keys[1][1] then
		for c = 1, 6 do
			out[c] = keys[1][c + 1]
		end
		return out
	end
	for i = 1, n - 1 do
		local a, b = keys[i], keys[i + 1]
		if t <= b[1] then
			local span = math.max(b[1] - a[1], 1e-6)
			local u = Core.smooth((t - a[1]) / span)
			for c = 1, 6 do
				out[c] = a[c + 1] + (b[c + 1] - a[c + 1]) * u
			end
			return out
		end
	end
	for c = 1, 6 do
		out[c] = keys[n][c + 1]
	end
	return out
end

function Core.mirrorName(name: string): string
	if string.sub(name, 1, 5) == "Right" then
		return "Left" .. string.sub(name, 6)
	elseif string.sub(name, 1, 4) == "Left" then
		return "Right" .. string.sub(name, 5)
	end
	return name
end

-- copy of a clip mirrored across the character's centre plane (right arm -> left arm)
function Core.mirrorClip(clip: Clip): Clip
	local joints: { [string]: Keys } = {}
	for name, keys in clip.joints do
		local mk: Keys = {}
		for i, k in keys do
			mk[i] = { k[1], k[2], -k[3], -k[4], -k[5], k[6], k[7] }
		end
		joints[Core.mirrorName(name)] = mk
	end
	return { length = clip.length, loop = clip.loop, sided = clip.sided, joints = joints }
end

-- clip time for an elapsed time (wraps looping clips, clamps one-shots)
function Core.clipTime(clip: Clip, elapsed: number): number
	if clip.loop then
		return elapsed % clip.length
	end
	return math.clamp(elapsed, 0, clip.length)
end

local scratch = { 0, 0, 0, 0, 0, 0 }

-- blend a clip into `pose` with weight w (0..1). Joints the clip does not animate are untouched.
function Core.blendClip(pose: Pose, clip: Clip, elapsed: number, w: number)
	local t = Core.clipTime(clip, elapsed)
	for name, keys in clip.joints do
		local p = pose[name]
		if p == nil then
			p = { 0, 0, 0, 0, 0, 0 }
			pose[name] = p
		end
		Core.sampleKeys(keys, t, scratch)
		for c = 1, 6 do
			p[c] = p[c] + (scratch[c] - p[c]) * w
		end
	end
end

-- reset every joint of a pose to rest
function Core.clearPose(pose: Pose, joints: { string })
	for _, name in joints do
		local p = pose[name]
		if p == nil then
			pose[name] = { 0, 0, 0, 0, 0, 0 }
		else
			for c = 1, 6 do
				p[c] = 0
			end
		end
	end
end

-- weight of a one-shot / looping overlay at `elapsed`, with fades (seconds)
function Core.overlayWeight(clip: Clip, elapsed: number, fadeIn: number, fadeOut: number, stoppedAt: number?): number
	local w = if fadeIn > 0 then math.min(1, elapsed / fadeIn) else 1
	if stoppedAt then
		w = math.min(w, 1 - math.clamp((elapsed - stoppedAt) / math.max(fadeOut, 1e-3), 0, 1))
	elseif not clip.loop then
		w = math.min(w, math.clamp((clip.length - elapsed) / math.max(fadeOut, 1e-3), 0, 1))
	end
	return w
end

-- head look-at angles (degrees) from a target offset in character space
function Core.lookAngles(dx: number, dy: number, dz: number, maxYaw: number, maxPitch: number): (number, number, boolean)
	local yaw = math.deg(math.atan2(-dx, -dz))
	if math.abs(yaw) > 110 then
		return 0, 0, false -- target is behind: don't break the neck
	end
	local pitch = math.deg(math.atan2(dy, math.sqrt(dx * dx + dz * dz)))
	return math.clamp(yaw, -maxYaw, maxYaw), math.clamp(pitch, -maxPitch, maxPitch), true
end

-- "talking" mouth opening 0..1 from time: syllable-like flaps
function Core.mouthOpen(t: number): number
	local syl = math.max(0, math.sin(t * 15.7))
	local env = 0.6 + 0.4 * math.sin(t * 4.3 + 1.1)
	return syl * env
end

return Core
