"""Shared helpers for the Tower of Pets lobby: scene, collections, materials, the
bmesh `Part` builder, 2D shape helpers (paw, pointed arch, text) and the reusable
asset library (trees, bushes, lanterns, rocks, clouds, islands) that the rest of
the scene places as linked duplicates (instancing).

Units: 1 Blender unit = 1 Roblox stud.  Z is up.  The tower lies to +Y of the
hub; the player spawns south of the fountain looking north (+Y).
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

TAU = 2 * math.pi


# ---------------------------------------------------------------- scene -----
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.name = 'TowerOfPets_Lobby'
    sc.unit_settings.system = 'NONE'          # plain units = studs
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.sample_clamp_indirect = 8.0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.view_settings.view_transform = 'Standard'      # saturated cartoon colours (AgX desaturates)
    sc.view_settings.look = 'Medium High Contrast'
    sc.view_settings.exposure = -0.35
    sc.render.resolution_x, sc.render.resolution_y = 1536, 1024
    sc.render.compositor_device = 'CPU'
    COLL.clear(); MATS.clear(); ASSETS.clear()
    return sc


# ---------------------------------------------------------------- collections
COLL = {}


def coll(name, parent=None):
    """get/create a collection; `parent` is another collection name (None = scene root)"""
    if name not in COLL:
        c = bpy.data.collections.new(name)
        (COLL[parent] if parent else bpy.context.scene.collection).children.link(c)
        COLL[name] = c
    return COLL[name]


def empty(name, collection, loc=(0, 0, 0), rot_z=0.0, size=4.0):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = size
    e.location = loc
    e.rotation_euler = (0, 0, rot_z)
    coll(collection).objects.link(e)
    return e


# ---------------------------------------------------------------- materials -
MATS = {}


def _bsdf(m):
    return m.node_tree, m.node_tree.nodes['Principled BSDF']


def mat_plain(name, rgb, rough=0.6, emit=0.0, metal=0.0, alpha=1.0, emit_rgb=None, coat=0.0):
    m = bpy.data.materials.new(name)
    nt, b = _bsdf(m)
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = (*(emit_rgb or rgb), 1)
        b.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*rgb, alpha)
    MATS[name] = m
    return m


def mat_noise(name, a, b_, rough=0.75, scale=0.12, bump=0.25, bump_scale=0.9, detail=3.0, emit=0.0):
    """mottled stylised stone / sand / grass: two-colour noise + soft bump (object space, studs)"""
    m = mat_plain(name, a, rough, emit=emit)
    nt, b = _bsdf(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = scale
    n1.inputs['Detail'].default_value = detail
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[0].color = (*a, 1)
    ramp.color_ramp.elements[1].color = (*b_, 1)
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = bump_scale
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    L = nt.links.new
    L(tc.outputs['Object'], n1.inputs['Vector']); L(tc.outputs['Object'], n2.inputs['Vector'])
    L(n1.outputs['Fac'], ramp.inputs['Fac']); L(ramp.outputs['Color'], b.inputs['Base Color'])
    if emit:
        L(ramp.outputs['Color'], b.inputs['Emission Color'])
    L(n2.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_blocks(name, c1, c2, mortar, rough=0.8, w=4.0, h=2.0, scale=1.0, bump=0.35):
    """stylised stone-block masonry (brick texture in object space, studs)"""
    m = mat_plain(name, c1, rough)
    nt, b = _bsdf(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = (*c1, 1)
    br.inputs['Color2'].default_value = (*c2, 1)
    br.inputs['Mortar'].default_value = (*mortar, 1)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.12
    br.inputs['Brick Width'].default_value = w
    br.inputs['Row Height'].default_value = h
    br.offset = 0.5
    # brick texture is 2D: drive it with X+Y (wraps round towers) and Z
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    bp.invert = True
    L = nt.links.new
    L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs['Vector'], sep.inputs['Vector'])
    L(sep.outputs['X'], add.inputs[0]); L(sep.outputs['Y'], add.inputs[1])
    L(add.outputs['Value'], comb.inputs['X']); L(sep.outputs['Z'], comb.inputs['Y'])
    L(comb.outputs['Vector'], br.inputs['Vector'])
    L(br.outputs['Color'], b.inputs['Base Color'])
    L(br.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_emit_gradient(name, c_lo, c_hi, strength, axis='Z', lo=0.0, hi=1.0, noise=0.0, noise_scale=0.3):
    """emissive gradient along a generated axis (portal energy, waterfalls, lava falls)"""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = lo
    mr.inputs['From Max'].default_value = hi
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c_lo, 1)
    ramp.color_ramp.elements[1].color = (*c_hi, 1)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = strength
    L = nt.links.new
    L(tc.outputs['Generated'], sep.inputs['Vector'])
    val = sep.outputs[axis]
    if noise:
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = noise_scale
        nz.inputs['Detail'].default_value = 2.0
        L(tc.outputs['Object'], nz.inputs['Vector'])
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MULTIPLY_ADD'
        mx.inputs[1].default_value = noise
        L(nz.outputs['Fac'], mx.inputs[0]); L(val, mx.inputs[2])
        val = mx.outputs['Value']
    L(val, mr.inputs['Value']); L(mr.outputs['Result'], ramp.inputs['Fac'])
    L(ramp.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    m.diffuse_color = (*c_hi, 1)
    MATS[name] = m
    return m


def mat_waterfall(name, c_deep, c_light, strength=1.2, streak_scale=0.25):
    """stylised falling water: vertical streaks (stretched noise) light/deep blue, semi-emissive"""
    m = mat_plain(name, c_light, 0.15)
    nt, b = _bsdf(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (streak_scale, streak_scale, streak_scale * 0.06)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0
    nz.inputs['Detail'].default_value = 4.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[0].color = (*c_deep, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (*c_light, 1)
    b.inputs['Emission Strength'].default_value = strength
    L = nt.links.new
    L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs['Vector'], nz.inputs['Vector'])
    L(nz.outputs['Fac'], ramp.inputs['Fac'])
    L(ramp.outputs['Color'], b.inputs['Base Color']); L(ramp.outputs['Color'], b.inputs['Emission Color'])
    return m


def mat_stars(name, base, star_rgb, density=0.06, scale=1.2, strength=6.0):
    """dark cosmic stone sprinkled with emissive star specks (celestial floor)"""
    m = mat_plain(name, base, 0.4)
    nt, b = _bsdf(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = scale
    vo.feature = 'F1'
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = density
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = strength
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.05
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*base, 1)
    ramp.color_ramp.elements[1].color = (base[0] * 2.2, base[1] * 1.4, base[2] * 2.4, 1)
    b.inputs['Emission Color'].default_value = (*star_rgb, 1)
    L = nt.links.new
    L(tc.outputs['Object'], vo.inputs['Vector']); L(vo.outputs['Distance'], lt.inputs[0])
    L(lt.outputs['Value'], mul.inputs[0]); L(mul.outputs['Value'], b.inputs['Emission Strength'])
    L(tc.outputs['Object'], nz.inputs['Vector']); L(nz.outputs['Fac'], ramp.inputs['Fac'])
    L(ramp.outputs['Color'], b.inputs['Base Color'])
    return m


def mat_portal(name):
    """swirling blue/purple portal energy: radial gradient + twisted noise, strongly emissive"""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    # radial distance from portal centre (generated coords 0..1 on X and Z)
    sx = nt.nodes.new('ShaderNodeMath'); sx.operation = 'SUBTRACT'; sx.inputs[1].default_value = 0.5
    sz = nt.nodes.new('ShaderNodeMath'); sz.operation = 'SUBTRACT'; sz.inputs[1].default_value = 0.42
    cmb = nt.nodes.new('ShaderNodeCombineXYZ')
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0
    nz.inputs['Detail'].default_value = 6.0; nz.inputs['Distortion'].default_value = 2.5
    mix = nt.nodes.new('ShaderNodeMath'); mix.operation = 'MULTIPLY_ADD'; mix.inputs[1].default_value = 0.35
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    el = ramp.color_ramp.elements
    el[0].position = 0.05; el[0].color = (0.55, 0.85, 1.0, 1)
    el[1].position = 0.75; el[1].color = (0.30, 0.10, 0.85, 1)
    e2 = el.new(0.30); e2.color = (0.05, 0.50, 1.0, 1)
    e3 = el.new(0.55); e3.color = (0.03, 0.15, 0.85, 1)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.25
    L = nt.links.new
    L(tc.outputs['Generated'], sep.inputs['Vector'])
    L(sep.outputs['X'], sx.inputs[0]); L(sep.outputs['Z'], sz.inputs[0])
    L(sx.outputs['Value'], cmb.inputs['X']); L(sz.outputs['Value'], cmb.inputs['Y'])
    L(cmb.outputs['Vector'], ln.inputs[0])
    L(tc.outputs['Generated'], nz.inputs['Vector'])
    L(nz.outputs['Fac'], mix.inputs[0]); L(ln.outputs['Value'], mix.inputs[2])
    L(mix.outputs['Value'], ramp.inputs['Fac'])
    L(ramp.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    m.diffuse_color = (0.2, 0.5, 1.0, 1)
    MATS[name] = m
    return m


def build_materials():
    N, P, B = mat_noise, mat_plain, mat_blocks
    # --- hub / entrance ---------------------------------------------------------------------------
    B('Hub_Stone', (0.80, 0.66, 0.46), (0.72, 0.58, 0.40), (0.55, 0.43, 0.30), w=6, h=3, bump=0.2)
    B('Hub_Stone_Warm', (0.90, 0.66, 0.38), (0.82, 0.58, 0.32), (0.62, 0.45, 0.28), w=5, h=2.5, bump=0.2)
    N('Plaza_Tile', (0.84, 0.76, 0.62), (0.78, 0.70, 0.56), 0.7, 0.05, 0.08, 0.5)
    N('Plaza_Path', (0.95, 0.82, 0.58), (0.90, 0.76, 0.52), 0.7, 0.06, 0.08, 0.5)
    P('Stone_Trim', (0.74, 0.66, 0.56), 0.75)
    P('Stone_Dark', (0.42, 0.36, 0.34), 0.8)
    P('Blue_Inlay', (0.05, 0.45, 1.0), 0.3, emit=1.0)
    N('Grass', (0.24, 0.72, 0.08), (0.42, 0.85, 0.12), 0.85, 0.08, 0.1, 1.5)
    N('Grass_Dark', (0.12, 0.52, 0.06), (0.24, 0.66, 0.08), 0.85, 0.08, 0.1, 1.5)
    N('Leaf_Green', (0.14, 0.58, 0.06), (0.32, 0.78, 0.08), 0.7, 0.35, 0.3, 2.0)
    N('Leaf_Light', (0.36, 0.80, 0.08), (0.56, 0.90, 0.15), 0.7, 0.35, 0.3, 2.0)
    N('Leaf_Dark', (0.06, 0.38, 0.05), (0.14, 0.52, 0.06), 0.7, 0.35, 0.3, 2.0)
    N('Wood', (0.55, 0.28, 0.10), (0.68, 0.38, 0.15), 0.7, 0.4, 0.3, 3.0)
    P('Gold', (1.0, 0.76, 0.15), 0.3, metal=0.85)
    P('Gold_Glow', (1.0, 0.78, 0.10), 0.3, emit=0.8, metal=0.5)
    P('Banner_Navy', (0.04, 0.14, 0.60), 0.6)
    P('Lantern_Glow', (1.0, 0.62, 0.22), 0.4, emit=2.75)
    P('Lantern_Metal', (0.14, 0.11, 0.12), 0.5, metal=0.6)
    P('Paw_White_Glow', (0.90, 0.97, 1.0), 0.3, emit=1.65)
    P('Magic_Glow', (0.20, 0.62, 1.0), 0.3, emit=1.93)
    P('Magic_Purple', (0.55, 0.20, 1.0), 0.3, emit=1.93)
    mat_portal('Portal_Energy')
    P('Water', (0.05, 0.68, 1.0), 0.05, emit=0.35, emit_rgb=(0.1, 0.75, 1.0), coat=1.0)
    mat_waterfall('Waterfall', (0.10, 0.62, 1.0), (0.80, 0.96, 1.0), 0.45)
    P('Foam', (0.92, 0.97, 1.0), 0.6, emit=0.6)
    P('Fountain_Orb', (0.10, 0.50, 1.0), 0.15, emit=1.21, emit_rgb=(0.10, 0.45, 1.0))
    # facility colours ----------------------------------------------------------------------------
    P('Shop_Red', (1.0, 0.10, 0.08), 0.45); P('Shop_Red_Glow', (1.0, 0.18, 0.12), 0.4, emit=1.38)
    P('Shop_White', (1.0, 0.98, 0.94), 0.55)
    P('Eggs_Purple', (0.60, 0.18, 0.95), 0.45); P('Eggs_Purple_Glow', (0.75, 0.30, 1.0), 0.4, emit=1.54)
    P('Crystal_Blue', (0.15, 0.55, 1.0), 0.1, emit=1.1)
    P('Crystal_Purple', (0.55, 0.15, 1.0), 0.1, emit=1.1)
    P('Crystal_Pink', (1.0, 0.25, 0.75), 0.1, emit=1.1)
    P('Egg_Shell', (0.95, 0.90, 0.80), 0.4)
    P('Egg_Glow', (0.75, 0.40, 1.0), 0.3, emit=0.99)
    P('Fabric_Cream', (0.92, 0.85, 0.70), 0.8)
    P('Avatar_Yellow', (0.96, 0.80, 0.25), 0.6); P('Avatar_Blue', (0.05, 0.35, 0.80), 0.6)
    P('Avatar_Green', (0.35, 0.75, 0.25), 0.6); P('Avatar_Face', (0.05, 0.05, 0.05), 0.5)
    # tower themes --------------------------------------------------------------------------------
    B('Jungle_Stone', (0.72, 0.68, 0.50), (0.62, 0.60, 0.42), (0.38, 0.42, 0.24), w=8, h=4, scale=0.5)
    N('Mossy_Stone', (0.34, 0.62, 0.16), (0.62, 0.66, 0.42), 0.85, 0.06, 0.15, 0.4)
    B('Desert_Sandstone', (1.0, 0.76, 0.38), (0.94, 0.66, 0.30), (0.70, 0.46, 0.20), w=8, h=4, scale=0.5)
    P('Desert_Gold', (1.0, 0.80, 0.20), 0.35, metal=0.4, emit=0.5)
    B('Ice', (0.62, 0.88, 1.0), (0.50, 0.80, 1.0), (0.30, 0.60, 0.95), w=8, h=4, scale=0.5, bump=0.12)
    P('Ice_Clear', (0.45, 0.80, 1.0), 0.08, emit=0.8)
    P('Snow', (0.95, 0.97, 1.0), 0.8)
    N('Lava_Rock', (0.20, 0.10, 0.10), (0.36, 0.16, 0.12), 0.9, 0.08, 0.3, 0.5)
    mat_noise('Lava', (1.0, 0.20, 0.02), (1.0, 0.65, 0.10), 0.5, 0.15, 0.0, 1.0, 2.0, emit=2.2)
    P('Iron', (0.10, 0.08, 0.08), 0.5, metal=0.8)
    N('Crystal_Rock', (0.30, 0.12, 0.55), (0.48, 0.20, 0.75), 0.8, 0.07, 0.2, 0.5)
    B('Shadow_Stone', (0.30, 0.20, 0.45), (0.24, 0.16, 0.38), (0.12, 0.08, 0.20), w=8, h=4, scale=0.5)
    P('Shadow_Glow', (0.60, 0.15, 1.0), 0.4, emit=1.93)
    N('Forest_Wood', (0.50, 0.26, 0.10), (0.66, 0.38, 0.15), 0.8, 0.1, 0.4, 0.8)
    P('Forest_Glow', (0.35, 1.0, 0.30), 0.4, emit=1.38)
    B('Kingdom_Stone', (0.74, 0.72, 0.70), (0.66, 0.64, 0.62), (0.42, 0.40, 0.40), w=8, h=4, scale=0.5)
    P('Roof_Blue', (0.08, 0.35, 1.0), 0.5)
    P('Roof_Red', (0.95, 0.15, 0.10), 0.5)
    N('Cloud_Marble', (0.94, 0.95, 0.98), (0.84, 0.88, 0.95), 0.4, 0.05, 0.1, 0.5)
    mat_stars('Celestial_Stone', (0.10, 0.06, 0.40), (0.9, 0.9, 1.0))
    P('Celestial_Ring', (0.55, 0.30, 1.0), 0.2, emit=2.48)
    N('Divine_Marble', (0.98, 0.96, 0.90), (0.92, 0.88, 0.80), 0.35, 0.05, 0.1, 0.5)
    P('Divine_Ring', (1.0, 0.80, 0.40), 0.2, emit=2.48)
    P('Window_Warm', (1.0, 0.62, 0.22), 0.4, emit=1.65)
    P('Window_Blue', (0.20, 0.60, 1.0), 0.4, emit=1.65)
    # environment ---------------------------------------------------------------------------------
    N('Cliff_Rock', (0.62, 0.44, 0.28), (0.78, 0.60, 0.40), 0.9, 0.05, 0.3, 0.3)
    N('Cliff_Rock_Dark', (0.44, 0.30, 0.20), (0.58, 0.42, 0.28), 0.9, 0.05, 0.3, 0.3)
    N('Mountain', (0.30, 0.62, 0.22), (0.66, 0.58, 0.44), 0.9, 0.012, 0.3, 0.08)
    P('Cloud', (0.95, 0.97, 1.0), 0.9, emit=0.15, emit_rgb=(0.85, 0.90, 1.0))
    P('Sea', (0.02, 0.45, 0.90), 0.15, coat=1.0)
    P('Rope', (0.72, 0.52, 0.28), 0.9)


# ---------------------------------------------------------------- mesh part -
class Part:
    """bmesh accumulator -> one named, editable mesh object (one material slot per material)"""

    def __init__(self, name, collection, bevel=0.0):
        self.name, self.coll, self.bevel = name, collection, bevel
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _tag(self, verts, mat, smooth=False):
        i = self.mi(mat)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = i
            f.smooth = smooth
        return verts

    def _faces(self, faces, mat, smooth=False):
        i = self.mi(mat)
        for f in faces:
            f.material_index = i
            f.smooth = smooth

    # -- primitives (all return the created verts) --
    def box(self, c, s, mat, rot=None):
        m = Matrix.Translation(Vector(c)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4)) \
            @ Matrix.Diagonal((*s, 1))
        return self._tag(bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)['verts'], mat)

    def cyl(self, c, r, depth, mat, segs=12, axis='Z', r2=None, rot=None, smooth=False, caps=True):
        R = {'Z': Matrix.Identity(4), 'X': Matrix.Rotation(math.pi / 2, 4, 'Y'),
             'Y': Matrix.Rotation(math.pi / 2, 4, 'X')}[axis]
        if rot is not None:
            R = rot.to_4x4() @ R
        m = Matrix.Translation(Vector(c)) @ R
        res = bmesh.ops.create_cone(self.bm, cap_ends=caps, segments=segs, radius1=r,
                                    radius2=r if r2 is None else r2, depth=depth, matrix=m)
        return self._tag(res['verts'], mat, smooth)

    def cone(self, base_c, r, h, mat, segs=8, r_top=0.0, smooth=False):
        """cone/frustum standing on base_c (h may be negative -> hangs down)"""
        c = Vector(base_c) + Vector((0, 0, h / 2))
        if h >= 0:
            return self.cyl(c, r, h, mat, segs, r2=r_top, smooth=smooth)
        return self.cyl(c, r_top, -h, mat, segs, r2=r, smooth=smooth)

    def ico(self, c, r, mat, sub=1, scale=(1, 1, 1), smooth=True):
        m = Matrix.Translation(Vector(c)) @ Matrix.Diagonal((*scale, 1))
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=m)
        return self._tag(res['verts'], mat, smooth)

    def uvsphere(self, c, r, mat, segs=16, rings=8, scale=(1, 1, 1), smooth=True, rot=None):
        m = Matrix.Translation(Vector(c)) @ (rot.to_4x4() if rot else Matrix.Identity(4)) \
            @ Matrix.Diagonal((*scale, 1))
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=rings, radius=r, matrix=m)
        return self._tag(res['verts'], mat, smooth)

    def torus(self, c, R, r, mat, segs=32, sides=6, rot=None, smooth=True):
        """ring in the local XY plane"""
        M = Matrix.Translation(Vector(c)) @ (rot.to_4x4() if rot else Matrix.Identity(4))
        bm = self.bm
        rings = []
        for i in range(segs):
            a = TAU * i / segs
            ring = []
            for k in range(sides):
                b = TAU * k / sides
                p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a),
                            r * math.sin(b)))
                ring.append(bm.verts.new(M @ p))
            rings.append(ring)
        faces = []
        for i in range(segs):
            A, Bv = rings[i], rings[(i + 1) % segs]
            for k in range(sides):
                faces.append(bm.faces.new((A[k], Bv[k], Bv[(k + 1) % sides], A[(k + 1) % sides])))
        self._faces(faces, mat, smooth)

    def beam(self, a, b, w, h, mat, pad=0.0, up=(0, 0, 1)):
        a, b = Vector(a), Vector(b)
        d = b - a
        q = d.to_track_quat('Z', 'Y').to_matrix()
        return self.box((a + b) / 2, (w, h, d.length + 2 * pad), mat, q)

    def hexa(self, pts, mat, smooth=False):
        """closed hexahedron from 8 corners: bottom quad 0-3, top quad 4-7 (same winding)"""
        v = [self.bm.verts.new(p) for p in pts]
        F = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
        faces = [self.bm.faces.new([v[i] for i in f]) for f in F]
        self._faces(faces, mat, smooth)

    def prism(self, pts, z0, z1, mat, M=None, smooth=False):
        """convex/concave polygon in local XY extruded z0..z1, then transformed by M"""
        M = M or Matrix.Identity(4)
        bm = self.bm
        lo = [bm.verts.new(M @ Vector((x, y, z0))) for x, y in pts]
        hi = [bm.verts.new(M @ Vector((x, y, z1))) for x, y in pts]
        n = len(pts)
        faces = [bm.faces.new(lo[::-1]), bm.faces.new(hi)]
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((lo[i], lo[j], hi[j], hi[i])))
        self._faces(faces, mat, smooth)
        return lo + hi

    def prism_xz(self, pts, y0, y1, mat):
        """polygon drawn in the XZ plane (front elevation) extruded along Y from y0 to y1"""
        M = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # (x,y,z)->(x,z,y)
        return self.prism(pts, y0, y1, mat, M)

    def strip_xz(self, outer, inner, y0, y1, mat):
        """frame between two open polylines in the XZ plane (e.g. an arch moulding), extruded along Y"""
        for i in range(len(outer) - 1):
            a, b, c, d = outer[i], outer[i + 1], inner[i + 1], inner[i]
            q = [(a[0], y0, a[1]), (b[0], y0, b[1]), (c[0], y0, c[1]), (d[0], y0, d[1])]
            self.hexa(q + [(x, y1, z) for x, _, z in q], mat)

    def ring_sector(self, r0, r1, a0, a1, z0, z1, mat, segs=None, center=(0, 0)):
        """annular sector (angles in radians) as a closed mesh"""
        segs = segs or max(2, int(abs(a1 - a0) / TAU * 64))
        cx, cy = center
        bm = self.bm
        rows = []
        for i in range(segs + 1):
            a = a0 + (a1 - a0) * i / segs
            ca, sa = math.cos(a), math.sin(a)
            rows.append([bm.verts.new((cx + r * ca, cy + r * sa, z)) for r, z in
                         ((r0, z0), (r1, z0), (r1, z1), (r0, z1))])
        faces = []
        for i in range(segs):
            A, Bv = rows[i], rows[i + 1]
            for k in range(4):
                faces.append(bm.faces.new((A[k], Bv[k], Bv[(k + 1) % 4], A[(k + 1) % 4])))
        faces.append(bm.faces.new(rows[0][::-1]))
        faces.append(bm.faces.new(rows[-1]))
        self._faces(faces, mat)

    def loft(self, rings, mat, cap_bottom=True, cap_top=True, smooth=False):
        """skin a list of equal-length closed point rings (bottom -> top)"""
        bm = self.bm
        V = [[bm.verts.new(p) for p in r] for r in rings]
        n = len(rings[0])
        faces = []
        for A, Bv in zip(V, V[1:]):
            for i in range(n):
                j = (i + 1) % n
                faces.append(bm.faces.new((A[i], A[j], Bv[j], Bv[i])))
        if cap_bottom:
            faces.append(bm.faces.new(V[0][::-1]))
        if cap_top:
            faces.append(bm.faces.new(V[-1]))
        self._faces(faces, mat, smooth)

    def finish(self, smooth_all=False, parent=None, loc=None, rot_z=None):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(MATS[m])
        if smooth_all:
            me.shade_smooth()
        ob = bpy.data.objects.new(self.name, me)
        coll(self.coll).objects.link(ob)
        if parent is not None:
            ob.parent = parent
        if loc is not None:
            ob.location = loc
        if rot_z is not None:
            ob.rotation_euler = (0, 0, rot_z)
        if self.bevel:
            bv = ob.modifiers.new('Bevel', 'BEVEL')
            bv.width = self.bevel
            bv.segments = 1
            bv.limit_method = 'ANGLE'
            bv.angle_limit = math.radians(40)
        return ob


# ---------------------------------------------------------------- 2D shapes -
def ellipse(cx, cy, rx, ry, n=16, a0=0.0):
    return [(cx + rx * math.cos(a0 + TAU * i / n), cy + ry * math.sin(a0 + TAU * i / n)) for i in range(n)]


def paw_shapes(size=1.0):
    """paw print in the XY plane (toes up = +Y), ~size wide: [(polygon points), ...]"""
    s = size
    pad = []
    for i in range(20):                          # rounded-triangle main pad
        a = TAU * i / 20
        r = 1.0 - 0.10 * math.cos(3 * a + math.pi / 2)
        pad.append((0.30 * s * r * math.cos(a) * 1.15, -0.16 * s + 0.24 * s * r * math.sin(a)))
    toes = [ellipse(x * s, y * s, 0.105 * s, 0.135 * s, 14, 0.0) for x, y in
            ((-0.36, 0.13), (-0.13, 0.32), (0.13, 0.32), (0.36, 0.13))]
    # tilt the outer toes outward
    def rot(poly, cx, cy, ang):
        c, sn = math.cos(ang), math.sin(ang)
        return [(cx + (x - cx) * c - (y - cy) * sn, cy + (x - cx) * sn + (y - cy) * c) for x, y in poly]
    toes[0] = rot(toes[0], -0.36 * s, 0.13 * s, 0.45)
    toes[1] = rot(toes[1], -0.13 * s, 0.32 * s, 0.15)
    toes[2] = rot(toes[2], 0.13 * s, 0.32 * s, -0.15)
    toes[3] = rot(toes[3], 0.36 * s, 0.13 * s, -0.45)
    return [pad] + toes


def paw(p, M, size, depth, mat):
    """extruded paw print; M maps local XY (toes +Y, face +Z) into the part's space"""
    for poly in paw_shapes(size):
        p.prism(poly, 0, depth, mat, M)


def M_front(x, y, z, rot_z=0.0):
    """matrix mapping a local XY drawing (Y up) onto a vertical plane facing -Y at (x,y,z)"""
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot_z, 4, 'Z') @ \
        Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def pointed_arch(w, hs, ht, chamfer=0.0, n_side=1):
    """open outline (bottom-left -> top -> bottom-right) of the gabled 'pointed' arch used on
    the tower entrance: vertical sides of height hs, straight-sided point of height ht"""
    x = w / 2
    pts = [(-x, 0.0)]
    pts += [(-x, hs * i / n_side) for i in range(1, n_side)]
    if chamfer:
        pts += [(-x, hs - chamfer), (-x + chamfer * 0.6, hs + chamfer * 0.5)]
    else:
        pts += [(-x, hs)]
    pts += [(0.0, hs + ht)]
    if chamfer:
        pts += [(x - chamfer * 0.6, hs + chamfer * 0.5), (x, hs - chamfer)]
    else:
        pts += [(x, hs)]
    pts += [(x, hs * i / n_side) for i in range(n_side - 1, 0, -1)]
    pts += [(x, 0.0)]
    return pts


def round_arch(w, hs, n=8):
    """open outline of a round-topped arch, bottom-left -> bottom-right"""
    r = w / 2
    pts = [(-r, 0.0)]
    for i in range(n + 1):
        a = math.pi - math.pi * i / n
        pts.append((r * math.cos(a), hs + r * math.sin(a)))
    pts.append((r, 0.0))
    return pts


FONT = None


def find_font():
    global FONT
    if FONT is None:
        for f in ('/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf',
                  '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf',
                  r'C:\Windows\Fonts\ariblk.ttf', r'C:\Windows\Fonts\arialbd.ttf',
                  '/System/Library/Fonts/Supplemental/Arial Black.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
            if os.path.exists(f):
                FONT = bpy.data.fonts.load(f)
                break
    return FONT


def text_mesh(name, text, collection, size, depth, mat, loc=(0, 0, 0), rot_z=0.0, parent=None,
              align='CENTER'):
    """3D text converted to a real mesh (Roblox-friendly). Faces -Y, stands upright."""
    cu = bpy.data.curves.new(name + '_curve', 'FONT')
    cu.body = text
    f = find_font()
    if f:
        cu.font = f
    cu.size = size
    cu.extrude = depth / 2
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.resolution_u = 3
    tmp = bpy.data.objects.new(name + '_tmp', cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.name = name
    me.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))        # XY text -> XZ, readable from -Y
    me.materials.clear()
    me.materials.append(MATS[mat])
    ob = bpy.data.objects.new(name, me)
    coll(collection).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    if parent is not None:
        ob.parent = parent
    return ob


# ---------------------------------------------------------------- assets ----
ASSETS = {}
ASSET_COLL = '_ASSET_LIBRARY'


def asset(name):
    return ASSETS[name]


def inst(asset_name, name, collection, loc, rot_z=0.0, scale=1.0, parent=None, tilt=(0.0, 0.0)):
    """linked duplicate of a library asset (shares mesh data -> cheap, edit once)"""
    src = ASSETS[asset_name]
    ob = bpy.data.objects.new(name, src.data)
    coll(collection).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (tilt[0], tilt[1], rot_z)
    ob.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    if parent is not None:
        ob.parent = parent
    return ob


def _asset_part(name):
    return Part('ASSET_' + name, ASSET_COLL)


def _register(name, p, smooth=False):
    ob = p.finish(smooth)
    ob.data.name = 'ASSET_' + name
    ASSETS[name] = ob
    return ob


def rock_blob(p, c, r, mat, rnd, sub=1, squash=(1, 1, 0.7), jitter=0.22):
    vs = p.ico(c, r, mat, sub, squash, smooth=False)
    for v in vs:
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * r * jitter
    return vs


def canopy(p, c, r, mats, rnd, n=6, flat=0.8, low=True):
    """crown mass made of the foliage pack's faceted leaf clusters (mats kept for API compatibility)"""
    from foliage import leaf_cluster
    c = Vector(c)
    leaf_cluster(p, c, r, rnd, squash=flat, low=low)
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.3, 0.3)
        off = Vector((math.cos(a) * r * 0.7, math.sin(a) * r * 0.7, rnd.uniform(-0.3, 0.35) * r))
        leaf_cluster(p, c + off, r * rnd.uniform(0.55, 0.8), rnd, squash=flat, low=low)


def build_assets():
    lib = coll(ASSET_COLL)
    rnd = random.Random(11)
    # lantern post (hub) ---------------------------------------------------------------------------
    p = _asset_part('Lantern_Post')
    p.box((0, 0, 0.5), (1.6, 1.6, 1.0), 'Stone_Dark')
    p.cyl((0, 0, 4.5), 0.32, 7, 'Lantern_Metal', 8)
    p.box((0, 0, 8.4), (1.4, 1.4, 0.3), 'Lantern_Metal')
    p.box((0, 0, 9.5), (1.0, 1.0, 1.9), 'Lantern_Glow')
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box((sx * 0.62, sy * 0.62, 9.5), (0.18, 0.18, 2.1), 'Lantern_Metal')
    p.cone((0, 0, 10.5), 1.05, 1.0, 'Lantern_Metal', 4)
    p.ico((0, 0, 11.6), 0.25, 'Gold', 1)
    _register('Lantern_Post', p)
    # stone pedestal lantern (low, Japanese-style, for plazas)
    p = _asset_part('Lantern_Stone')
    p.box((0, 0, 0.6), (2.2, 2.2, 1.2), 'Stone_Trim')
    p.box((0, 0, 2.2), (1.2, 1.2, 2.0), 'Stone_Trim')
    p.box((0, 0, 3.8), (1.6, 1.6, 1.2), 'Lantern_Glow')
    p.cone((0, 0, 4.4), 1.6, 1.2, 'Stone_Dark', 4)
    _register('Lantern_Stone', p)
    # rocks ---------------------------------------------------------------------------------------
    for k in range(3):
        p = _asset_part(f'Rock_{"ABC"[k]}')
        rr = random.Random(60 + k)
        rock_blob(p, (0, 0, 0), 1.0, 'Cliff_Rock', rr, 1, (1.2, 1.0, 0.8))
        _register(f'Rock_{"ABC"[k]}', p)
    # clouds --------------------------------------------------------------------------------------
    for k in range(4):
        p = _asset_part(f'Cloud_{"ABCD"[k]}')
        rr = random.Random(80 + k)
        n = 7 + k * 2
        for i in range(n):
            x = rr.uniform(-1, 1) * (1.6 + k * 0.3)
            y = rr.uniform(-0.6, 0.6)
            r = rr.uniform(0.6, 1.1) * (1.0 - abs(x) / (3.5 + k * 0.4))
            p.ico((x, y, r * 0.35), r, 'Cloud', 2, (1, 1, 0.75))
        _register(f'Cloud_{"ABCD"[k]}', p)
    # crystal cluster ----------------------------------------------------------------------------
    for k, mats in enumerate((('Crystal_Purple', 'Crystal_Pink'), ('Crystal_Blue', 'Crystal_Purple'))):
        p = _asset_part(f'Crystals_{"AB"[k]}')
        rr = random.Random(90 + k)
        for i in range(7):
            a = rr.uniform(0, TAU); d = 0 if i == 0 else rr.uniform(0.4, 1.0)
            h = (3.0 if i == 0 else rr.uniform(1.2, 2.2))
            tilt = Euler((rr.uniform(-0.45, 0.45) * (i > 0), rr.uniform(-0.45, 0.45) * (i > 0), a)).to_matrix()
            base = Vector((math.cos(a) * d, math.sin(a) * d, 0))
            r = 0.35 if i == 0 else rr.uniform(0.2, 0.3)
            p.cyl(base + tilt @ Vector((0, 0, h * 0.4)), r, h * 0.8, mats[i % 2], 6, rot=tilt)
            p.cyl(base + tilt @ Vector((0, 0, h * 0.9)), 0, h * 0.2, mats[i % 2], 6, r2=r, rot=tilt)
        _register(f'Crystals_{"AB"[k]}', p)
    for o in lib.objects:
        o.hide_render = True
    lib.hide_render = True


# ---------------------------------------------------------------- avatar ----
def avatar(name, collection, loc, rot_z=0.0):
    """placeholder R6-proportioned Roblox avatar, 5 studs tall (scale reference only)"""
    p = Part(name, collection, 0.05)
    p.box((-0.5, 0, 1.0), (1, 1, 2), 'Avatar_Green'); p.box((0.5, 0, 1.0), (1, 1, 2), 'Avatar_Green')
    p.box((0, 0, 3.0), (2, 1, 2), 'Avatar_Blue')
    p.box((-1.5, 0, 3.0), (1, 1, 2), 'Avatar_Yellow'); p.box((1.5, 0, 3.0), (1, 1, 2), 'Avatar_Yellow')
    p.cyl((0, 0, 4.6), 0.6, 1.2, 'Avatar_Yellow', 12)
    p.box((-0.22, -0.58, 4.75), (0.14, 0.05, 0.22), 'Avatar_Face')
    p.box((0.22, -0.58, 4.75), (0.14, 0.05, 0.22), 'Avatar_Face')
    return p.finish(loc=loc, rot_z=rot_z)


# ---------------------------------------------------------------- waterfalls -
def waterfall(name, collection, lip, out_dir, drop, width, mat='Waterfall', foam=True, thick=0.8,
              curve=6.0, seed=0, foam_mat='Foam'):
    """stylised waterfall sheet: pours over a lip along out_dir (horizontal), curves and drops `drop`
    studs; optional foam blobs where it lands. One object per fall."""
    rnd = random.Random(seed)
    lip = Vector(lip)
    d = Vector((out_dir[0], out_dir[1], 0)).normalized()
    side = Vector((-d.y, d.x, 0))
    cl = [lip - d * 2.0, lip, lip + d * curve * 0.45 - Vector((0, 0, curve * 0.25)),
          lip + d * curve * 0.8 - Vector((0, 0, curve * 0.8))]
    n_lo = max(2, int(drop / 40))
    for k in range(1, n_lo + 1):
        cl.append(lip + d * (curve + k * drop * 0.02) - Vector((0, 0, curve + (drop - curve) * k / n_lo)))
    p = Part(name, collection)
    for i in range(len(cl) - 1):
        a, b = cl[i], cl[i + 1]
        wa = width * (1 + 0.15 * i / len(cl)); wb = width * (1 + 0.15 * (i + 1) / len(cl))
        na = (b - a).cross(side).normalized() * thick / 2
        q = [a - side * wa / 2 - na, a + side * wa / 2 - na, a + side * wa / 2 + na, a - side * wa / 2 + na]
        r = [b - side * wb / 2 - na, b + side * wb / 2 - na, b + side * wb / 2 + na, b - side * wb / 2 + na]
        p.hexa(q + r, mat)
    if foam:
        end = cl[-1]
        for k in range(7):
            o = side * rnd.uniform(-0.6, 0.6) * width + d * rnd.uniform(-0.3, 0.6) * width * 0.4
            p.ico(end + o, rnd.uniform(0.25, 0.42) * width, foam_mat, 2, (1, 1, 0.55))
    return p.finish()
