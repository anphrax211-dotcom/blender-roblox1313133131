-- Minimal Roblox API mock for testing the NPC scripts with the standalone Luau CLI.
-- Only what the NPC scripts use: Vector3, CFrame, Color3, Enum, Instance (Part/MeshPart/Model/
-- Folder/ModuleScript/Motor6D/Weld/WeldConstraint/Attachment/ProximityPrompt/BindableEvent),
-- attributes, signals, game services and a joint solver to place parts like Roblox would.

local M = {}

-- ---------------------------------------------------------------- Vector3
local V = {}
V.__index = function(v, k)
	if k == "Magnitude" then
		return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
	elseif k == "Unit" then
		local m = math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
		return M.v3(v.X / m, v.Y / m, v.Z / m)
	end
	return V[k]
end
function M.v3(x, y, z)
	return setmetatable({ X = x or 0, Y = y or 0, Z = z or 0, __type = "Vector3" }, V)
end
V.__add = function(a, b) return M.v3(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
V.__sub = function(a, b) return M.v3(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
V.__unm = function(a) return M.v3(-a.X, -a.Y, -a.Z) end
V.__mul = function(a, b)
	if type(a) == "number" then a, b = b, a end
	if type(b) == "number" then return M.v3(a.X * b, a.Y * b, a.Z * b) end
	return M.v3(a.X * b.X, a.Y * b.Y, a.Z * b.Z)
end
V.__div = function(a, b) return M.v3(a.X / b, a.Y / b, a.Z / b) end
function V.Dot(a, b) return a.X * b.X + a.Y * b.Y + a.Z * b.Z end
function V.Cross(a, b)
	return M.v3(a.Y * b.Z - a.Z * b.Y, a.Z * b.X - a.X * b.Z, a.X * b.Y - a.Y * b.X)
end
M.Vector3 = { new = M.v3, zero = M.v3(0, 0, 0), xAxis = M.v3(1, 0, 0), yAxis = M.v3(0, 1, 0), zAxis = M.v3(0, 0, 1) }

-- ---------------------------------------------------------------- CFrame (rotation columns + position)
local C = {}
local function cf(p, x, y, z)
	return setmetatable({ p = p, x = x, y = y, z = z, __type = "CFrame" }, C)
end
C.__index = function(c, k)
	if k == "Position" then return c.p
	elseif k == "RightVector" or k == "XVector" then return c.x
	elseif k == "UpVector" or k == "YVector" then return c.y
	elseif k == "LookVector" then return -c.z
	elseif k == "ZVector" then return c.z end
	return C[k]
end
local function rotv(c, v) return c.x * v.X + c.y * v.Y + c.z * v.Z end
C.__mul = function(a, b)
	if b.__type == "Vector3" then return a.p + rotv(a, b) end
	return cf(a.p + rotv(a, b.p), rotv(a, b.x), rotv(a, b.y), rotv(a, b.z))
end
function C.Inverse(c)
	-- transpose rotation
	local x = M.v3(c.x.X, c.y.X, c.z.X)
	local y = M.v3(c.x.Y, c.y.Y, c.z.Y)
	local z = M.v3(c.x.Z, c.y.Z, c.z.Z)
	local inv = cf(M.v3(0, 0, 0), x, y, z)
	return cf(-rotv(inv, c.p), x, y, z)
end
function C.ToObjectSpace(a, b) return a:Inverse() * b end
function C.PointToObjectSpace(a, v) return a:Inverse() * v end
function C.VectorToObjectSpace(a, v) return M.v3(a.x:Dot(v), a.y:Dot(v), a.z:Dot(v)) end
local I = { M.v3(1, 0, 0), M.v3(0, 1, 0), M.v3(0, 0, 1) }
M.CFrame = {
	identity = cf(M.v3(0, 0, 0), I[1], I[2], I[3]),
	new = function(x, y, z)
		if type(x) == "table" then return cf(x, I[1], I[2], I[3]) end
		return cf(M.v3(x or 0, y or 0, z or 0), I[1], I[2], I[3])
	end,
	fromMatrix = function(p, x, y, z) return cf(p, x, y, z or x:Cross(y)) end,
	fromAxisAngle = function(axis, a)
		local u = axis.Unit
		local c, s = math.cos(a), math.sin(a)
		local function r(v) -- Rodrigues
			return v * c + u:Cross(v) * s + u * (u:Dot(v) * (1 - c))
		end
		return cf(M.v3(0, 0, 0), r(I[1]), r(I[2]), r(I[3]))
	end,
}
M.CFrame.Angles = function(rx, ry, rz) -- Roblox: Rx * Ry * Rz
	return M.CFrame.fromAxisAngle(I[1], rx) * M.CFrame.fromAxisAngle(I[2], ry) * M.CFrame.fromAxisAngle(I[3], rz)
end

-- ---------------------------------------------------------------- Color3 / Enum
local Col = {}
Col.__index = Col
function M.c3(r, g, b) return setmetatable({ R = r, G = g, B = b, __type = "Color3" }, Col) end
function Col.Lerp(a, b, t) return M.c3(a.R + (b.R - a.R) * t, a.G + (b.G - a.G) * t, a.B + (b.B - a.B) * t) end
M.Color3 = { new = M.c3 }
M.Enum = { Material = { Neon = "Neon", SmoothPlastic = "SmoothPlastic" } }

-- ---------------------------------------------------------------- signals / instances
local function signal()
	local s = { handlers = {} }
	function s:Connect(fn) table.insert(self.handlers, fn); return { Disconnect = function() end } end
	function s:Fire(...) for _, h in self.handlers do h(...) end end
	return s
end
M.signal = signal

local CLASS_BASE = {
	Part = { "BasePart" }, MeshPart = { "BasePart" }, Motor6D = { "JointInstance" }, Weld = { "JointInstance" },
}
local Inst = {}
Inst.__index = function(o, k)
	if k == "Position" and rawget(o, "CFrame") then return rawget(o, "CFrame").Position end
	if k == "Parent" then return rawget(o, "_parent") end
	if Inst[k] ~= nil then return Inst[k] end
	for _, c in rawget(o, "_children") do -- Roblox-style child access: folder.ChildName
		if rawget(c, "Name") == k then return c end
	end
	return nil
end
Inst.__newindex = function(o, k, v)
	if k == "Parent" then
		if o.ClassName == "WeldConstraint" and v and o.Part0 and o.Part1 then
			rawset(o, "_offset", o.Part0.CFrame:ToObjectSpace(o.Part1.CFrame))
		end
		local old = rawget(o, "_parent")
		if old then
			for i, c in old._children do
				if c == o then table.remove(old._children, i) break end
			end
		end
		rawset(o, "_parent", v)
		if v then
			table.insert(v._children, o)
			local root = v
			while root do
				local ev = rawget(root, "DescendantAdded")
				if ev then ev:Fire(o) end
				root = rawget(root, "_parent")
			end
		end
	elseif k == "Position" and rawget(o, "CFrame") then
		local c = o.CFrame
		rawset(o, "CFrame", M.CFrame.fromMatrix(v, c.x, c.y, c.z))
	else
		rawset(o, k, v)
	end
end
function M.new(className, props)
	local o = setmetatable({ ClassName = className, Name = className, _children = {}, _attrs = {}, _attrSignals = {},
		__isInstance = true, Destroying = signal() }, Inst)
	if className == "Part" or className == "MeshPart" then
		rawset(o, "CFrame", M.CFrame.identity)
		rawset(o, "Size", M.v3(1, 1, 1))
		rawset(o, "Material", M.Enum.Material.SmoothPlastic)
		rawset(o, "Color", M.c3(0.6, 0.6, 0.6))
		rawset(o, "Anchored", false)
	elseif className == "Motor6D" or className == "Weld" then
		rawset(o, "C0", M.CFrame.identity)
		rawset(o, "C1", M.CFrame.identity)
		if className == "Motor6D" then rawset(o, "Transform", M.CFrame.identity) end
	elseif className == "ProximityPrompt" then
		rawset(o, "Triggered", signal())
	elseif className == "BindableEvent" then
		rawset(o, "Event", signal())
		function o:Fire(...) self.Event:Fire(...) end
	elseif className == "Attachment" then
		rawset(o, "Position", nil)
	end
	for k, v in props or {} do o[k] = v end
	return o
end
function Inst.IsA(o, cls)
	if o.ClassName == cls then return true end
	for _, b in CLASS_BASE[o.ClassName] or {} do
		if b == cls then return true end
	end
	return false
end
function Inst.GetChildren(o) return table.clone(o._children) end
function Inst.GetDescendants(o)
	local out = {}
	local function walk(x)
		for _, c in x._children do
			table.insert(out, c)
			walk(c)
		end
	end
	walk(o)
	return out
end
function Inst.FindFirstChild(o, name, recursive)
	for _, c in (if recursive then o:GetDescendants() else o._children) do
		if c.Name == name then return c end
	end
	return nil
end
function Inst.WaitForChild(o, name)
	local c = o:FindFirstChild(name)
	assert(c, "WaitForChild would hang: " .. name)
	return c
end
function Inst.Destroy(o)
	o.Destroying:Fire()
	o.Parent = nil
end
function Inst.SetAttribute(o, k, v)
	o._attrs[k] = v
	local s = o._attrSignals[k]
	if s then s:Fire() end
end
function Inst.GetAttribute(o, k) return o._attrs[k] end
function Inst.GetAttributeChangedSignal(o, k)
	o._attrSignals[k] = o._attrSignals[k] or signal()
	return o._attrSignals[k]
end

M.Instance = { new = M.new }
function M.typeof(x)
	if type(x) == "table" then
		if rawget(x, "__isInstance") then return "Instance" end
		if rawget(x, "__type") then return rawget(x, "__type") end
	end
	return type(x)
end

-- ---------------------------------------------------------------- joint solver
-- places every part from the anchored root through Motor6Ds and welds (like Roblox does)
function M.solve(model)
	local joints = {}
	for _, d in model:GetDescendants() do
		if d.ClassName == "Motor6D" or d.ClassName == "Weld" or d.ClassName == "WeldConstraint" then
			table.insert(joints, d)
		end
	end
	local placed = {}
	for _, d in model:GetDescendants() do
		if d.ClassName == "Part" or d.ClassName == "MeshPart" then
			if d.Anchored then placed[d] = true end
		end
	end
	local progress = true
	while progress do
		progress = false
		for _, j in joints do
			if placed[j.Part0] and not placed[j.Part1] then
				if j.ClassName == "Motor6D" then
					j.Part1.CFrame = j.Part0.CFrame * j.C0 * j.Transform * j.C1:Inverse()
				elseif j.ClassName == "Weld" then
					j.Part1.CFrame = j.Part0.CFrame * j.C0 * j.C1:Inverse()
				else
					j.Part1.CFrame = j.Part0.CFrame * j._offset
				end
				placed[j.Part1] = true
				progress = true
			end
		end
	end
	return placed
end

return M
