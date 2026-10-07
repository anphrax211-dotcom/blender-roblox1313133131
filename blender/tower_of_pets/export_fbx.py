"""TOWER OF PETS - export the lobby to Roblox-ready FBX files (exports/TowerOfPets/).

    python3 blender/tower_of_pets/export_fbx.py            (after build.py; reads blender/TowerOfPets_Lobby.blend)

One FBX per building / area, all in the same world space, so with Studio's 3D Importer option
"Insert Using Scene Position" every file lands in the right place (1 Blender unit = 1 stud, Y up).

Per exported mesh:
- modifiers applied, collection instances (floating islands) realised, triangulated (concave n-gons safe)
- split by material: one MeshPart per material, named  <Object>__<Material>  so Roblox colours and
  materials can be applied by name (TowerOfPets_Materials.lua)
- anything still over 19,000 triangles is split into chunks (Roblox MeshPart limit 20k)
- buildings keep their <Name>_Root empty as the parent (= the Model pivot in Studio)

Also written: TowerOfPets_Materials.lua (material -> Color3 / Enum.Material / transparency + an apply()
helper), TowerOfPets_Lights.lua (every Blender lamp as a Roblox PointLight spec) and manifest.json.
"""
import os, sys, json, math, re
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
import bpy, bmesh
from mathutils import Matrix, Vector

ROOT_DIR = os.path.dirname(os.path.dirname(HERE))
BLEND = os.path.join(os.path.dirname(HERE), 'TowerOfPets_Lobby.blend')
OUT = os.path.join(ROOT_DIR, 'exports', 'TowerOfPets')
TRI_LIMIT = 19000

# file name -> (collections, root empty name or None)
GROUPS = (
    ('TowerOfPets_Plaza', ('Plaza', 'Spawn', 'Fountain'), None),
    ('TowerOfPets_TowerEntrance', ('Tower_Entrance',), None),
    ('TowerOfPets_Shop', ('TOWER_OF_PETS_SHOP',), 'Shop_Root'),
    ('TowerOfPets_Hatchery', ('TOWER_OF_PETS_HATCHERY',), 'Hatchery_Root'),
    ('TowerOfPets_PetClinic', ('PET_CLINIC',), 'PetClinic_Root'),
    ('TowerOfPets_PetGym', ('TOWER_OF_PETS_PET_GYM',), 'PetGym_Root'),
    ('TowerOfPets_TradingPortal', ('TOWER_OF_PETS_TRADING_PORTAL',), 'TradingPortal_Root'),
    ('TowerOfPets_Leaderboards', ('TOWER_OF_PETS_LEADERBOARDS',), 'Leaderboards_Root'),
    ('TowerOfPets_Tower_Lower', ('Hub_Base', 'Jungle', 'Desert', 'Ice', 'Lava'), None),
    ('TowerOfPets_Tower_Middle', ('Crystal', 'Shadow', 'Forest', 'Kingdom'), None),
    ('TowerOfPets_Tower_Upper', ('Cloud', 'Celestial', 'Divine'), None),
    ('TowerOfPets_FloatingIslands', ('FLOATING_ISLANDS', 'WATERFALLS'), None),
    ('TowerOfPets_Environment', ('ENVIRONMENT',), None),          # hub rock, arcades, mountains (no sky clouds)
    ('TowerOfPets_SkyClouds', ('Sky_Clouds',), None),
)
EXCLUDE_FROM = {'TowerOfPets_Environment': ('Sky_Clouds',)}
# current export settings (main() overrides them, e.g. build_floor1_export.py)
CFG = dict(blend=BLEND, groups=GROUPS, exclude=EXCLUDE_FROM, out=OUT, tri_limit=TRI_LIMIT, prefix='TowerOfPets',
           spawn=(0.0, -58.0, 0.0), precise=())

# Blender (x, y, z) -> Roblox (x, z, -y)  (FBX export axis_up='Y', axis_forward='-Z')
def to_roblox(v):
    return (round(v[0], 3), round(v[2], 3), round(-v[1], 3))


def lin2srgb(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


# ---------------------------------------------------------------- materials -
def rep_color(m):
    """representative flat colour of a (procedural) Blender material"""
    nt = m.node_tree if m.use_nodes else None
    if nt:
        b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b:
            inp = b.inputs['Base Color']
            if not inp.is_linked:
                return tuple(inp.default_value[:3])
            src = inp.links[0].from_node
            if src.type == 'VALTORGB':
                els = src.color_ramp.elements
                return tuple(sum(e.color[i] for e in els) / len(els) for i in range(3))
            if src.type == 'TEX_BRICK':
                a, b2 = src.inputs['Color1'].default_value, src.inputs['Color2'].default_value
                return tuple((a[i] + b2[i]) / 2 for i in range(3))
            if src.type == 'MIX' or src.type == 'MIX_RGB':
                cols = [i.default_value for i in src.inputs if i.type == 'RGBA' and not i.is_linked]
                if cols:
                    return tuple(sum(c_[i] for c_ in cols) / len(cols) for i in range(3))
    return tuple(m.diffuse_color[:3])


def roblox_material(m):
    name = m.name.lower()
    nt = m.node_tree if m.use_nodes else None
    emissive, metal, alpha = False, 0.0, m.diffuse_color[3]
    if nt:
        b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b:
            es = b.inputs['Emission Strength']
            emissive = es.is_linked or es.default_value > 0.3
            metal = b.inputs['Metallic'].default_value
            alpha = min(alpha, b.inputs['Alpha'].default_value)
        elif any(n.type == 'EMISSION' for n in nt.nodes):
            emissive = True
    if emissive:
        mat = 'Neon'
    elif alpha < 0.95 or 'glass' in name:
        mat = 'Glass'
    elif metal > 0.5:
        mat = 'Metal'
    elif any(k in name for k in ('wood', 'trunk', 'branch', 'plank', 'bark')):
        mat = 'Wood'
    else:
        mat = 'SmoothPlastic'
    return mat, (round(1.0 - alpha, 2) if alpha < 0.95 else 0.0)


def prepare_materials():
    """bake the representative colour into the Principled base colour default so FBX carries it"""
    info = {}
    for m in bpy.data.materials:
        if m.users == 0:
            continue
        col = rep_color(m)
        mat, tr = roblox_material(m)
        info[m.name] = dict(rgb=[int(round(lin2srgb(c_) * 255)) for c_ in col], material=mat, transparency=tr)
        if m.use_nodes:
            b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if b:
                b.inputs['Base Color'].default_value = (*col, 1)
        m.diffuse_color = (*col, m.diffuse_color[3])
    return info


# ---------------------------------------------------------------- meshes ----
def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def split_mesh(src_me, base_name):
    """triangulate, split per material and into <= TRI_LIMIT chunks -> [(name, mesh)]"""
    out = []
    for mi, mat in enumerate(src_me.materials):
        bm = bmesh.new()
        bm.from_mesh(src_me)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != mi], context='FACES')
        if not bm.faces:
            bm.free()
            continue
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
        for f in bm.faces:
            f.material_index = 0
        mname = mat.name if mat else 'None'
        faces = list(bm.faces)
        LIM = CFG['tri_limit']
        if len(faces) <= LIM:
            chunks = [None]
        else:                                               # pack connected pieces by x, slice big pieces
            bm.faces.ensure_lookup_table()
            seen, comps = set(), []
            for f in faces:
                if f.index in seen:
                    continue
                stack, comp = [f], []
                seen.add(f.index)
                while stack:
                    g = stack.pop()
                    comp.append(g)
                    for v in g.verts:
                        for h in v.link_faces:
                            if h.index not in seen:
                                seen.add(h.index); stack.append(h)
                comps.append(comp)
            pieces = []
            for comp in comps:
                if len(comp) > LIM:                         # big connected surface -> square-ish xy tiles
                    cs = [g.calc_center_median() for g in comp]
                    x0, x1 = min(c.x for c in cs), max(c.x for c in cs) + 1e-3
                    y0, y1 = min(c.y for c in cs), max(c.y for c in cs) + 1e-3
                    k = max(1, math.ceil(math.sqrt(len(comp) * 1.3 / LIM)))
                    tiles = {}
                    for g, c_ in zip(comp, cs):
                        key = (int((c_.x - x0) / (x1 - x0) * k), int((c_.y - y0) / (y1 - y0) * k))
                        tiles.setdefault(key, []).append(g)
                    for t in tiles.values():
                        t.sort(key=lambda g: g.calc_center_median().x)
                        pieces += [t[i:i + LIM] for i in range(0, len(t), LIM)]
                else:
                    pieces.append(comp)
            pieces.sort(key=lambda cp: sum(g.calc_center_median().x for g in cp) / len(cp))
            chunks, cur = [], []
            for cp in pieces:
                if len(cur) + len(cp) > LIM and cur:
                    chunks.append(cur); cur = []
                cur += cp
            if cur:
                chunks.append(cur)
            chunks = [set(g.index for g in ch) for ch in chunks]
        for k, keep in enumerate(chunks):
            if keep is None:
                b2 = bm
            else:
                b2 = bm.copy()
                b2.faces.ensure_lookup_table()
                bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in keep], context='FACES')
            me = bpy.data.meshes.new(f'{base_name}__{mname}' + (f'_{k + 1}' if keep is not None else ''))
            b2.to_mesh(me)
            if b2 is not bm:
                b2.free()
            me.materials.append(mat)
            out.append((me.name, me))
        bm.free()
    return out


def main(**cfg):
    CFG.update(cfg)
    GROUPS, EXCLUDE_FROM, OUT = CFG['groups'], CFG['exclude'], CFG['out']
    bpy.ops.wm.open_mainfile(filepath=CFG['blend'])
    os.makedirs(OUT, exist_ok=True)
    mats = prepare_materials()
    C = bpy.data.collections
    dg = bpy.context.evaluated_depsgraph_get()

    # which group does each object belong to
    owner = {}
    for fname, colls, _ in GROUPS:
        for cn in colls:
            for o in C[cn].all_objects:
                if any(o.name in C[x].all_objects for x in EXCLUDE_FROM.get(fname, ())):
                    continue
                owner.setdefault(o.name, fname)

    # every visible mesh instance (incl. realised collection instances) with its world matrix; the evaluated
    # meshes are copied right away (depsgraph references die once the scene changes)
    items = {g[0]: [] for g in GROUPS}
    cache = {}                       # (mesh name, has modifiers) -> split meshes (shared by linked duplicates)
    for inst in dg.object_instances:
        ob = inst.object
        src = inst.parent if inst.is_instance else inst.object
        if ob.type != 'MESH' or src is None:
            continue
        g = owner.get(src.original.name)
        if g is None:
            continue
        orig = ob.original
        if orig.hide_render and 'Trigger' not in orig.name or orig.name.startswith('SCALE_'):
            continue                                   # skip hidden helpers and the 5-stud scale avatars
        key = (orig.data.name, bool(orig.modifiers))
        if key not in cache:
            me = bpy.data.meshes.new_from_object(ob, preserve_all_data_layers=False, depsgraph=dg)
            cache[key] = split_mesh(me, orig.data.name.replace('ASSET_', ''))
            bpy.data.meshes.remove(me)
        nm = orig.name if not inst.is_instance else f'{src.original.name}_{orig.name}'
        nm = re.sub(r'\.\d{3}', '', nm)
        items[g].append((key, inst.matrix_world.copy(), nm))

    scene_coll = bpy.data.collections.new('_FBX_EXPORT')
    bpy.context.scene.collection.children.link(scene_coll)
    manifest = {}
    for fname, colls, root_name in GROUPS:
        made = []
        root = bpy.data.objects.new(root_name or fname, None)
        scene_coll.objects.link(root)
        if root_name and root_name in bpy.data.objects:
            root.matrix_world = bpy.data.objects[root_name].matrix_world.copy()
        rinv = root.matrix_world.inverted()
        tris = 0
        for key, mw, nm in items[fname]:
            for mname, me in cache[key]:
                part = mname.split('__', 1)[1]
                o = bpy.data.objects.new(f'{nm}__{part}', me)
                scene_coll.objects.link(o)
                o.parent = root
                o.matrix_parent_inverse = Matrix.Identity(4)
                o.matrix_basis = rinv @ mw
                made.append(o)
                tris += len(me.polygons)
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        root.select_set(True)
        for o in made:
            o.select_set(True)
        path = os.path.join(OUT, fname + '.fbx')
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'EMPTY', 'MESH'},
                                 apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
                                 axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=False,
                                 add_leaf_bones=False, bake_anim=False, path_mode='STRIP', use_custom_props=False)
        biggest = max((len(o.data.polygons) for o in made), default=0)
        manifest[fname] = dict(parts=len(made), triangles=tris, largest_part=biggest,
                               root=root.name, root_position_roblox=to_roblox(root.matrix_world.translation),
                               size_mb=round(os.path.getsize(path) / 1e6, 2))
        print(f'{fname}: {len(made)} parts, {tris:,} tris (largest {biggest:,}), '
              f'{manifest[fname]["size_mb"]} MB')
        for o in made:
            bpy.data.objects.remove(o)
        bpy.data.objects.remove(root)

    # lights -> PointLight specs (positions in Roblox studs, scene position import)
    lights = []
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or o.data.type != 'POINT':
            continue
        e = o.data.energy
        lights.append(dict(name=o.name, position=to_roblox(o.matrix_world.translation),
                           rgb=[int(round(lin2srgb(c_) * 255)) for c_ in o.data.color],
                           brightness=round(min(3.0, 0.8 + e / 1500), 2), range=round(min(60, max(12, math.sqrt(e) * 0.9)), 1)))
    write_lua(mats, lights)
    with open(os.path.join(OUT, 'manifest.json'), 'w') as f:
        json.dump(dict(files=manifest, materials=len(mats), lights=len(lights),
                       spawn_roblox=to_roblox(CFG['spawn'])), f, indent=2)
    print('materials', len(mats), 'lights', len(lights))


def write_lua(mats, lights):
    L = ['-- Tower of Pets: Blender material name -> Roblox appearance (generated by export_fbx.py).',
         '-- Every imported MeshPart is named "<Object>__<Material>"; apply(model) colours them all.',
         'local M = {}', '', 'M.Materials = {']
    for name in sorted(mats):
        d = mats[name]
        L.append(f'\t["{name}"] = {{Color = Color3.fromRGB({d["rgb"][0]}, {d["rgb"][1]}, {d["rgb"][2]}), '
                 f'Material = Enum.Material.{d["material"]}, Transparency = {d["transparency"]}}},')
    L += ['}', '',
          '-- decorative / effect pieces players should walk through',
          'M.NoCollide = {"Particles", "Energy", "EnergyRing", "Sparkle", "Cloud", "Leaf", "Leaves", "Vine", "Banner",',
          '\t"Waterfall", "Mist", "Glow", "Grass_Tuft", "Ground_Plant", "Flower", "Rivers", "Lakes"}', '',
          '-- walkable terrain: exact collision (needs Studio / command bar permission, ignored in game scripts)',
          'M.PreciseCollision = {' + ', '.join(f'"{p}"' for p in CFG['precise']) + '}', '',
          'function M.apply(root)',
          '\tfor _, part in ipairs(root:GetDescendants()) do',
          '\t\tif part:IsA("MeshPart") then',
          '\t\t\tlocal key = part.Name:match("__(.+)$")',
          '\t\t\tkey = key and key:gsub("%.%d+$", "")',
          '\t\t\tlocal spec = key and M.Materials[key]',
          '\t\t\tif key and not spec then  -- chunked parts end in _1, _2 ...',
          '\t\t\t\tspec = M.Materials[key:match("^(.-)_%d+$") or ""]',
          '\t\t\tend',
          '\t\t\tif spec then',
          '\t\t\t\tpart.Color = spec.Color',
          '\t\t\t\tpart.Material = spec.Material',
          '\t\t\t\tpart.Transparency = spec.Transparency',
          '\t\t\t\tpart.TextureID = ""',
          '\t\t\tend',
          '\t\t\tpart.Anchored = true',
          '\t\t\tfor _, pat in ipairs(M.PreciseCollision) do',
          '\t\t\t\tif part.Name:find(pat) then',
          '\t\t\t\t\tpcall(function() part.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end)',
          '\t\t\t\t\tbreak',
          '\t\t\t\tend',
          '\t\t\tend',
          '\t\t\tif part.Name:find("TeleportTrigger") then  -- invisible touch volumes',
          '\t\t\t\tpart.Transparency, part.CanCollide, part.CastShadow = 1, false, false',
          '\t\t\telse',
          '\t\t\t\tfor _, pat in ipairs(M.NoCollide) do',
          '\t\t\t\t\tif part.Name:find(pat) then part.CanCollide = false; part.CanQuery = false; break end',
          '\t\t\t\tend',
          '\t\t\tend',
          '\t\tend',
          '\tend',
          'end', '', 'return M', '']
    with open(os.path.join(CFG['out'], CFG['prefix'] + '_Materials.lua'), 'w') as f:
        f.write('\n'.join(L))
    L = ['-- Tower of Pets: lamps from the Blender lobby as PointLight specs (generated by export_fbx.py).',
         '-- Positions are world studs, valid when the FBX files were imported with "Insert Using Scene Position".',
         'local M = {}', '', 'M.Lights = {']
    for d in lights:
        x, y, z = d['position']
        L.append(f'\t{{Name = "{d["name"]}", Position = Vector3.new({x}, {y}, {z}), '
                 f'Color = Color3.fromRGB({d["rgb"][0]}, {d["rgb"][1]}, {d["rgb"][2]}), '
                 f'Brightness = {d["brightness"]}, Range = {d["range"]}}},')
    L += ['}', '',
          '-- creates an invisible anchored holder part per light inside `parent` (e.g. a "Lights" Folder)',
          'function M.build(parent)',
          '\tfor _, d in ipairs(M.Lights) do',
          '\t\tlocal p = Instance.new("Part")',
          '\t\tp.Name = d.Name',
          '\t\tp.Size = Vector3.new(0.5, 0.5, 0.5)',
          '\t\tp.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false',
          '\t\tp.Transparency = 1',
          '\t\tp.Position = d.Position',
          '\t\tlocal l = Instance.new("PointLight")',
          '\t\tl.Color, l.Brightness, l.Range, l.Shadows = d.Color, d.Brightness, d.Range, false',
          '\t\tl.Parent = p',
          '\t\tp.Parent = parent',
          '\tend',
          'end', '', 'return M', '']
    with open(os.path.join(CFG['out'], CFG['prefix'] + '_Lights.lua'), 'w') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    main()
