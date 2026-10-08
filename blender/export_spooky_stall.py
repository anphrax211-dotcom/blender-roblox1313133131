"""Export the Spooky Harvest stall (spooky_stall.py's part list) as a Roblox FBX.

The 1,000-odd parts are merged into named MeshParts, one per (section, Roblox material, colour, transparency,
collision), plus the sign board and each light-holder kept on their own. The names carry everything the FBX
can't, and SpookyHarvest_Setup.lua restores it inside Studio:

    <Section>__<Material>__<RRGGBB>[__T<transparency %>][__NC][__L<n>]      e.g. Canopy__Fabric__7034A0
    Sign__SignBoard__WoodPlanks__422A1B                                     gets the "SPOOKY HARVEST" SurfaceGui

Output (exports/SpookyHarvestStall/):
    SpookyHarvestStall.fbx       1 unit = 1 stud, Y up, stall front facing -Z, ground at y = 0
    SpookyHarvest_Setup.lua      materials, colours, transparency, collisions, sign, lights, folders
    fbx_manifest.json            MeshPart names and triangle counts

    python3 export_spooky_stall.py
"""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Matrix, Vector
import spooky_stall as ss

OUT = os.path.join(HERE, '..', 'exports', 'SpookyHarvestStall')
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # Roblox (Y up, -Z front) -> Blender


def part_bmesh(p):
    """the part's geometry in Roblox local space"""
    bm = bmesh.new()
    sx, sy, sz = p['size']
    smooth = True
    if p['shape'] == 'Ball':
        bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=min(sx, sy, sz) / 2)
    elif p['shape'] == 'Cylinder':
        d = min(sy, sz)
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16 if d > 0.25 else 8, radius1=d / 2, radius2=d / 2,
                              depth=sx)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    elif p['shape'] == 'Wedge':
        vs = [bm.verts.new((x * sx / 2, y * sy / 2, z * sz / 2)) for x in (-1, 1)
              for y, z in ((-1, -1), (-1, 1), (1, 1))]
        for f in ((0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)):
            bm.faces.new([vs[i] for i in f])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        smooth = False
    elif p['mesh'] == 'Sphere':
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.5)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    else:
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
        smooth = False
    for f in bm.faces:
        f.smooth = smooth
    return bm


def group_name(p, light_ids):
    section = p['path'].split('/')[0] or 'Stall'
    hexcol = '%02X%02X%02X' % tuple(int(v) for v in p['color'])
    name = f'{section}__{p["material"]}__{hexcol}'
    if p['transparency'] > 0.001:
        name += f'__T{int(round(p["transparency"] * 100))}'
    if not p['collide']:
        name += '__NC'
    if p['sign']:
        name = f'Sign__SignBoard__{p["material"]}__{hexcol}'
    if p['light']:
        light_ids.append(p)
        name += f'__L{len(light_ids)}'
    return name


def main():
    s = ss.build()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    groups, light_ids = {}, []
    for p in s.parts:
        if p['transparency'] >= 0.99:          # the invisible ShopInteractZone is recreated by the setup script
            continue
        groups.setdefault(group_name(p, light_ids), []).append(p)
    objs, manifest = [], {}
    for name, parts in sorted(groups.items()):
        bm = bmesh.new()
        for p in parts:
            pb = part_bmesh(p)
            pb.transform(C @ Matrix.Translation(p['pos']) @ p['R'].to_4x4())
            me = bpy.data.meshes.new('_t')
            pb.to_mesh(me)
            pb.free()
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        mat = bpy.data.materials.get(name.split('__')[1]) or bpy.data.materials.new(name.split('__')[1])
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        objs.append(ob)
        tris = sum(len(f.vertices) - 2 for f in me.polygons)
        manifest[name] = dict(parts=len(parts), triangles=tris)
        assert tris < 20000, name
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'SpookyHarvestStall.fbx')
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_NONE', global_scale=1.0, axis_forward='-Z', axis_up='Y',
                             mesh_smooth_type='FACE', use_mesh_modifiers=False, add_leaf_bones=False, bake_anim=False,
                             path_mode='STRIP', use_custom_props=False)
    with open(os.path.join(OUT, 'fbx_manifest.json'), 'w') as f:
        json.dump(dict(meshparts=len(objs), triangles=sum(v['triangles'] for v in manifest.values()),
                       lights=len(light_ids), parts=manifest), f, indent=1)
    write_setup(light_ids)
    print(f'{len(objs)} MeshParts, {sum(v["triangles"] for v in manifest.values()):,} tris, {len(light_ids)} lights, '
          f'{os.path.getsize(path) / 1e6:.2f} MB -> {path}')


SETUP = r'''--[[ SPOOKY HARVEST stall: setup after importing SpookyHarvestStall.fbx
     Generated by blender/export_spooky_stall.py.

     1. Import SpookyHarvestStall.fbx (Avatar or Home tab > Import 3D) with Scale Unit = Stud,
        Merge Meshes = OFF and Insert Using Scene Position = ON.
     2. Rename the imported model to SpookyHarvestStall (or select it), paste this whole file into the
        Command Bar and press Enter.

     Every MeshPart name is <Section>__<Material>__<RRGGBB>[__T<transparency %>][__NC][__L<n>]. This script
     turns that back into Material, Color, Transparency and CanCollide, anchors everything, sorts the parts
     into folders per section, adds the "SPOOKY HARVEST" sign text, the soft PointLights and an invisible
     ShopInteractZone in front of the counter. It is safe to run again. ]]

local SIGN_TEXT = "SPOOKY HARVEST"
local LIGHTS = { -- n = { r, g, b, brightness, range }
%LIGHTS%
}

local model = workspace:FindFirstChild("SpookyHarvestStall")
if not model then
	local sel = game:GetService("Selection"):Get()
	model = sel[1]
end
assert(model, "Select the imported stall model (or name it SpookyHarvestStall) and run again")
model.Name = "SpookyHarvestStall"

local function folder(name)
	local f = model:FindFirstChild(name)
	if not f then
		f = Instance.new("Folder")
		f.Name = name
		f.Parent = model
	end
	return f
end

local function addSign(part)
	local old = part:FindFirstChild("SignGui")
	if old then old:Destroy() end
	local gui = Instance.new("SurfaceGui")
	gui.Name = "SignGui"
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 60
	gui.LightInfluence = 0.35
	gui.Parent = part
	local label = Instance.new("TextLabel")
	label.Name = "Title"
	label.BackgroundTransparency = 1
	label.AnchorPoint = Vector2.new(0.5, 0.5)
	label.Position = UDim2.fromScale(0.5, 0.52)
	label.Size = UDim2.fromScale(0.7, 0.78)
	label.Font = Enum.Font.LuckiestGuy
	label.Text = SIGN_TEXT
	label.TextScaled = true
	label.TextColor3 = Color3.fromRGB(255, 196, 70)
	label.Parent = gui
	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.fromRGB(58, 30, 12)
	stroke.Thickness = 4
	stroke.Parent = label
	local grad = Instance.new("UIGradient")
	grad.Color = ColorSequence.new(Color3.fromRGB(255, 214, 96), Color3.fromRGB(240, 150, 40))
	grad.Rotation = 90
	grad.Parent = label
end

local count, base = 0, nil
for _, p in ipairs(model:GetDescendants()) do
	if p:IsA("MeshPart") or p:IsA("Part") then
		local bits = string.split(p.Name, "__")
		local section, matName, hex = bits[1], bits[2], bits[3]
		local isSign = section == "Sign" and bits[2] == "SignBoard"
		if isSign then matName, hex = bits[3], bits[4] end
		if matName and Enum.Material[matName] and hex then
			p.Material = Enum.Material[matName]
			p.Color = Color3.fromHex(hex)
			p.Transparency = 0
			p.CanCollide = true
			for i = 4, #bits do
				local flag = bits[i]
				if string.sub(flag, 1, 1) == "T" and tonumber(string.sub(flag, 2)) then
					p.Transparency = tonumber(string.sub(flag, 2)) / 100
				elseif flag == "NC" then
					p.CanCollide = false
				elseif string.sub(flag, 1, 1) == "L" and tonumber(string.sub(flag, 2)) then
					local l = LIGHTS[tonumber(string.sub(flag, 2))]
					local old = p:FindFirstChild("Glow")
					if old then old:Destroy() end
					local light = Instance.new("PointLight")
					light.Name = "Glow"
					light.Color = Color3.fromRGB(l[1], l[2], l[3])
					light.Brightness = l[4]
					light.Range = l[5]
					light.Shadows = false
					light.Parent = p
				end
			end
			p.CanTouch = p.CanCollide
			p.CastShadow = p.Transparency < 0.2
			p.Anchored = true
			if p:IsA("MeshPart") and not p.CanCollide then
				p.CollisionFidelity = Enum.CollisionFidelity.Box
			end
			if isSign then addSign(p) end
			p.Parent = folder(section)
			if section == "Structure" and (not base or p.Size.X * p.Size.Z > base.Size.X * base.Size.Z) then base = p end
			count = count + 1
		end
	end
end

local zone = model:FindFirstChild("ShopInteractZone") or Instance.new("Part")
zone.Name = "ShopInteractZone"
zone.Size = Vector3.new(5, 4, 3)
zone.Transparency = 1
zone.CanCollide = false
zone.CanTouch = true
zone.CastShadow = false
zone.Anchored = true
-- 0.6 studs to the player's right of the stall centre, in front of the free counter space
local cf, size = model:GetBoundingBox()
zone.CFrame = cf * CFrame.new(-0.6, 2 - size.Y / 2, -size.Z / 2 - 1.2)
zone.Parent = model
if base then model.PrimaryPart = base end
print(("SpookyHarvestStall set up: %d parts styled"):format(count))
'''


def write_setup(light_ids):
    rows = []
    for i, p in enumerate(light_ids):
        (r, g, b), br, rg = p['light']
        rows.append(f'\t[{i + 1}] = {{ {r}, {g}, {b}, {br:g}, {rg:g} }},')
    with open(os.path.join(OUT, 'SpookyHarvest_Setup.lua'), 'w') as f:
        f.write(SETUP.replace('%LIGHTS%', '\n'.join(rows)))


if __name__ == '__main__':
    main()
