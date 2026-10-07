"""TOWER OF PETS - HATCHERY / EGGS building, rebuilt from the hatchery reference with the castle masonry.

Layout (local space, studs, front = -Y, ground z = 0, origin = plinth centre line):
    front     masonry facade with a deep round arch (outer voussoirs, gold ring, recessed purple inner arch),
              gold-framed purple band with the glowing EGGS sign, raised purple parapet carrying the egg emblem
              (glowing egg + paw in a gold/stone frame, fan of purple crystals), two big banner pillars
    wings     purple panelled walls between stone pillars, purple lean-to roofs, lantern pillars, crystal planters
    interior  octagonal hall (apothem 15) under a dome with a glowing oculus; arched niches with egg shelves,
              central tiered hatchery platform with a floating glowing egg, magic rings, crystals; egg
              pedestals, purple runner + paw medallion, lanterns, banners
    back      masonry with a raised purple panel carrying two egg emblems, banner pillars, a small door
Ten display eggs: Blue, Cyan, Pink, Purple, Gold, Green, Fire, Ice, Crystal, Dark.

Collections: TOWER_OF_PETS_HATCHERY / BUILDING (Walls, Pillars, Arches, Roof, Gold_Trim), SIGNAGE (Eggs_Sign,
Egg_Emblem), BANNERS, INTERIOR (Central_Platform, Shelves, Pedestals, Decorations), EGGS (one per egg type),
CRYSTALS, LANTERNS, LANDSCAPING, LIGHTING.  In the lobby, names already used by the shop / tower get a
" (hatchery)" suffix (Blender collection names must be unique).
Kit (HATCHERY_KIT, prefixed "Hatch_"): Hatch_Stone_Block, Hatch_Stone_Wall, Hatch_Stone_Corner, Hatch_Stone_Pillar,
Hatch_Stone_Arch, Hatch_Purple_Wall, Hatch_Roof_Piece, Hatch_Gold_Trim, Hatch_Egg_Sign, Hatch_Egg_Emblem,
Hatch_Purple_Banner, Hatch_Crystal(_Cluster_Purple/_Blue), Hatch_Lantern, Hatch_Egg_Pedestal_S/M/L,
Hatch_Egg_Display, Hatch_Central_Hatchery_Platform, Hatch_Interior_Shelf, Hatch_Decorative_Paw, Hatch_Planter;
eggs Egg_Blue ... Egg_Dark.
"""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
from common import (Part, MATS, mat_plain, mat_noise, coll, inst, ASSETS, empty, paw, M_front, text_mesh,
                    round_arch, pointed_arch, TAU)
from castle import (bevel_box, masonry, quoins, voussoirs, pillar, trim_run, inside, lifted, frame_strip,
                    rect_minus_arch, STONES)

ROOT = 'TOWER_OF_PETS_HATCHERY'
KIT = 'HATCHERY_KIT'
I4 = Matrix.Identity(4)
FLIP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
EGG_TYPES = ('Blue', 'Cyan', 'Pink', 'Purple', 'Gold', 'Green', 'Fire', 'Ice', 'Crystal', 'Dark')
CN = {}                                   # requested collection name -> actual (unique) name


def RZ(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def T(x, y, z=0.0):
    return Matrix.Translation((x, y, z))


def c(name):
    return CN.get(name, name)


# ---------------------------------------------------------------- materials -
def build_hatchery_materials():
    P = mat_plain
    mat_noise('Hatch_Purple', (0.34, 0.13, 0.72), (0.39, 0.16, 0.78), 0.6, 0.25, 0.08, 2.0)
    P('Hatch_Purple_Dark', (0.20, 0.07, 0.48), 0.6)
    P('Hatch_Purple_Fabric', (0.42, 0.10, 0.84), 0.75)
    mat_noise('Hatch_Roof', (0.28, 0.10, 0.60), (0.33, 0.13, 0.66), 0.55, 0.2, 0.1, 1.5)
    P('Hatch_Roof_Dark', (0.18, 0.06, 0.42), 0.6)
    mat_noise('Hatch_Floor', (0.80, 0.74, 0.70), (0.86, 0.80, 0.76), 0.7, 0.3, 0.05, 2.0)
    mat_noise('Hatch_Carpet', (0.38, 0.10, 0.74), (0.42, 0.13, 0.80), 0.9, 0.6, 0.05, 3.0)
    P('Hatch_Sign_Glow', (1.0, 0.95, 1.0), 0.4, emit=1.5)
    P('Hatch_Egg_Glow', (1.0, 0.30, 0.88), 0.25, emit=0.55, emit_rgb=(1.0, 0.35, 0.9))
    P('Hatch_Magic_Cyan', (0.08, 0.78, 1.0), 0.2, emit=1.1)
    P('Hatch_Magic_Pink', (1.0, 0.25, 0.85), 0.2, emit=1.0)
    P('Hatch_Magic_Blue', (0.20, 0.45, 1.0), 0.2, emit=1.4)
    P('Hatch_Oculus', (0.20, 0.62, 1.0), 0.3, emit=0.8)
    P('Crystal_Pink_Soft', (1.0, 0.35, 0.85), 0.08, emit=0.5)
    # eggs
    P('Egg_Mat_Blue', (0.10, 0.40, 1.0), 0.25, emit=0.25)
    P('Egg_Mat_Cyan', (0.15, 0.88, 1.0), 0.25, emit=0.45)
    P('Egg_Mat_Pink', (1.0, 0.42, 0.75), 0.3, emit=0.2)
    P('Egg_Mat_Purple', (0.55, 0.22, 1.0), 0.3, emit=0.25)
    P('Egg_Mat_Gold', (1.0, 0.74, 0.15), 0.22, metal=0.85)
    P('Egg_Mat_Green', (0.25, 0.85, 0.22), 0.3)
    P('Egg_Mat_Fire', (1.0, 0.28, 0.04), 0.35, emit=0.45)
    P('Egg_Mat_Ice', (0.70, 0.90, 1.0), 0.15, emit=0.2)
    P('Egg_Mat_Crystal', (0.62, 0.40, 1.0), 0.05, emit=0.7)
    P('Egg_Mat_Dark', (0.07, 0.04, 0.12), 0.35)
    P('Egg_Spot_White', (1.0, 1.0, 1.0), 0.4)
    P('Egg_Spot_Flame', (1.0, 0.80, 0.10), 0.4, emit=1.2)
    P('Egg_Spot_Dark', (0.05, 0.30, 0.05), 0.4)
    P('Egg_Crack_Magenta', (1.0, 0.20, 0.85), 0.4, emit=1.6)


# ---------------------------------------------------------------- eggs ------
EGG_STYLE = {   # type: (shell, spot material, spot count, faceted)
    'Blue': ('Egg_Mat_Blue', 'Egg_Spot_White', 7, False), 'Cyan': ('Egg_Mat_Cyan', 'Egg_Spot_White', 6, False),
    'Pink': ('Egg_Mat_Pink', 'Egg_Spot_White', 7, False), 'Purple': ('Egg_Mat_Purple', 'Crystal_Pink_Soft', 6, False),
    'Gold': ('Egg_Mat_Gold', 'Crystal_Cyan', 5, False), 'Green': ('Egg_Mat_Green', 'Egg_Spot_Dark', 8, False),
    'Fire': ('Egg_Mat_Fire', 'Egg_Spot_Flame', 9, False), 'Ice': ('Egg_Mat_Ice', 'Egg_Spot_White', 9, False),
    'Crystal': ('Egg_Mat_Crystal', 'Crystal_Pink_Soft', 0, True), 'Dark': ('Egg_Mat_Dark', 'Egg_Crack_Magenta', 0, False),
}


def egg(p, kind, r=1.0, base=(0, 0, 0), rnd=None):
    """display egg standing on base (height ~2.6 r)"""
    rnd = rnd or random.Random(hash(kind) & 0xffff)
    shell, spot, n, faceted = EGG_STYLE[kind]
    c0 = Vector(base) + Vector((0, 0, r * 1.3))
    if faceted:
        vs = p.ico(c0, r, shell, 1, (1, 1, 1.3), smooth=False)
        p.ico(c0, r * 0.55, 'Crystal_Pink_Soft', 1, (1, 1, 1.3), smooth=False)
    else:
        p.uvsphere(c0, r, shell, 14, 9, (1, 1, 1.3))
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 0.75 - 1.4 * (i + 0.5) / n
        rr = math.sqrt(max(0, 1 - z * z))
        a = golden * i * 3 + rnd.uniform(-0.3, 0.3)
        u = Vector((math.cos(a) * rr, math.sin(a) * rr, z * 1.3))
        if kind == 'Fire':                                   # flame tongues licking up the shell
            p.cyl(c0 + u * r * 0.98 + Vector((0, 0, r * 0.15)), r * 0.16, r * 0.45, spot, 5, r2=0.0)
        else:
            p.ico(c0 + u * r * 0.97, r * rnd.uniform(0.12, 0.2), spot, 1, (1, 1, 0.45))
    if kind == 'Dark':                                       # glowing cracks
        for k in range(5):
            a = TAU * k / 5
            z0, z1 = rnd.uniform(-0.6, 0.0), rnd.uniform(0.3, 0.9)
            pts = []
            for j in range(4):
                t = j / 3
                zz = z0 + (z1 - z0) * t
                aa = a + (0.25 if j % 2 else -0.25)
                ring = math.sqrt(max(0.05, 1 - zz * zz))
                pts.append(c0 + Vector((math.cos(aa) * ring * r * 1.01, math.sin(aa) * ring * r * 1.01, zz * r * 1.3)))
            for q0, q1 in zip(pts, pts[1:]):
                p.beam(q0, q1, r * 0.08, r * 0.06, spot)
    if kind == 'Gold':
        p.torus(c0, r * 1.0, r * 0.06, 'Gold', 24, 4)


# ---------------------------------------------------------------- kit -------
def purple_banner(p, M=I4, w=4.0, length=11.0):
    """deep purple banner with gold border, gold egg + paw symbol, gold top bar (hangs from local origin)"""
    Mb = M @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    o = [(-w / 2, 0), (w / 2, 0), (w / 2, -length), (0, -length - w * 0.55), (-w / 2, -length)]
    p.prism(o, -0.25, 0.0, 'Hatch_Purple_Fabric', Mb)
    edge = [(-w / 2, 0), (-w / 2, -length), (0, -length - w * 0.55), (w / 2, -length), (w / 2, 0)]
    inner = [(-w / 2 + 0.35, 0), (-w / 2 + 0.35, -length + 0.15), (0, -length - w * 0.55 + 0.5),
             (w / 2 - 0.35, -length + 0.15), (w / 2 - 0.35, 0)]
    for (a0, a1), (b0, b1) in zip(zip(edge, edge[1:]), zip(inner, inner[1:])):
        q = [a0, a1, b1, b0]
        p.hexa([Mb @ Vector((x, z, 0.0)) for x, z in q] + [Mb @ Vector((x, z, 0.18)) for x, z in q], 'Gold')
    # gold egg outline with a paw inside
    ec = Vector((0, -length * 0.5, 0.0))
    ring_o = [(math.cos(TAU * i / 20) * w * 0.32, ec.y + math.sin(TAU * i / 20) * w * 0.42) for i in range(21)]
    ring_i = [(math.cos(TAU * i / 20) * w * 0.25, ec.y + math.sin(TAU * i / 20) * w * 0.34) for i in range(21)]
    frame_strip(p, Mb @ FLIP, ring_o, ring_i, 0.0, 0.2, 'Gold')
    paw(p, Mb @ Matrix.Translation((0, ec.y - w * 0.03, 0.0)), w * 0.36, 0.2, 'Gold')
    bevel_box(p, M, (0, -0.3, 0.35), (w + 1.0, 0.5, 0.6), 'Gold', 0.08)
    for s in (-1, 1):
        p.ico(M @ Vector((s * (w / 2 + 0.6), -0.3, 0.35)), 0.38, 'Gold', 1)


def hatch_lantern(p, M=I4):
    """same lantern family as the shop / castle: black iron with a warm glow (origin at its base)"""
    from shop import shop_lantern
    shop_lantern(p, M)


def egg_pedestal(p, r=1.6, h=2.2):
    p.cyl((0, 0, 0.3), r + 0.4, 0.6, 'Castle_Trim', 16)
    p.cyl((0, 0, 0.6 + (h - 1.2) / 2), r * 0.7, h - 1.2, 'Castle_Stone_Light', 12)
    p.cyl((0, 0, h - 0.6), r * 0.85, 0.4, 'Hatch_Purple', 16)
    p.cyl((0, 0, h - 0.2), r, 0.4, 'Castle_Trim', 16)
    p.torus((0, 0, h - 0.2), r + 0.02, 0.1, 'Gold', 20, 4)
    p.torus((0, 0, h + 0.05), r * 0.6, 0.09, 'Hatch_Magic_Cyan', 20, 4)


def egg_display(p):
    """three-tier round display stand (eggs are placed on it as separate instances)"""
    for k, (r, z) in enumerate(((3.2, 0.0), (2.3, 1.0), (1.4, 2.0))):
        p.cyl((0, 0, z + 0.5), r, 1.0, ('Castle_Trim', 'Hatch_Purple', 'Castle_Trim')[k], 20)
        p.torus((0, 0, z + 1.0), r, 0.1, 'Gold', 24, 4)


def interior_shelf(p, w=6.0, h=7.0):
    """arched-niche egg shelf: stone surround, purple back, gold arch frame, two wooden shelves"""
    bevel_box(p, I4, (0, 0.6, h / 2), (w, 0.4, h), 'Hatch_Purple', 0.06)
    for s in (-1, 1):
        bevel_box(p, I4, (s * (w / 2 + 0.4), 0.0, h / 2), (0.8, 1.6, h), 'Castle_Stone_Light', 0.12)
    outer = lifted(round_arch(w + 1.6, h - w / 2, 10), 0, 0)
    inner = lifted(round_arch(w, h - w / 2, 10), 0, 0)
    frame_strip(p, I4, outer[3:-3], inner[3:-3], -0.7, 0.9, 'Castle_Stone_Light')
    frame_strip(p, I4, lifted(round_arch(w + 0.3, h - w / 2, 10), 0, 0)[2:-2], inner[2:-2], -0.85, -0.6, 'Gold')
    for z in (0.3, h * 0.42):
        bevel_box(p, I4, (0, 0.0, z), (w, 1.4, 0.3), 'Shop_Wood', 0.06)
        bevel_box(p, I4, (0, -0.68, z + 0.12), (w, 0.1, 0.2), 'Gold', 0.03)


SHELF_Z = (0.45, 7.0 * 0.42 + 0.15)


def central_platform(p):
    """central hatchery platform (without the egg): stone tiers, purple band, glowing rings, pedestal"""
    p.cyl((0, 0, 0.4), 7.0, 0.8, 'Castle_Trim', 32)
    p.cyl((0, 0, 1.2), 6.0, 0.8, 'Castle_Stone_Light', 32)
    p.torus((0, 0, 1.6), 6.0, 0.12, 'Gold', 40, 4)
    p.cyl((0, 0, 1.75), 5.2, 0.3, 'Hatch_Purple', 32)
    p.torus((0, 0, 1.95), 4.6, 0.22, 'Hatch_Magic_Cyan', 40, 6)
    p.torus((0, 0, 1.95), 3.4, 0.12, 'Gold', 32, 4)
    p.cyl((0, 0, 2.6), 1.9, 1.3, 'Castle_Stone_Light', 16, r2=1.4)
    p.cyl((0, 0, 3.35), 2.2, 0.3, 'Gold', 16)
    p.torus((0, 0, 3.55), 1.8, 0.14, 'Hatch_Magic_Pink', 24, 4)
    for k in range(8):                                  # rune stones round the rim
        a = TAU * (k + 0.5) / 8
        bevel_box(p, Matrix.Translation((math.cos(a) * 6.4, math.sin(a) * 6.4, 0)) @ Matrix.Rotation(a, 4, 'Z'),
                  (0, 0, 1.7), (0.6, 1.2, 0.5), 'Hatch_Magic_Blue', 0.08)


def big_egg(p):
    """the floating glowing hatchery egg with the white paw and two magic rings (origin at platform top)"""
    c0 = Vector((0, 0, 6.6))
    p.uvsphere(c0, 2.6, 'Hatch_Egg_Glow', 20, 12, (1, 1, 1.3))
    paw(p, M_front(0, -2.55, 6.4), 2.8, 0.3, 'Hatch_Sign_Glow')
    p.torus(c0, 3.6, 0.12, 'Hatch_Magic_Cyan', 40, 4, rot=Euler((0.35, 0.15, 0)).to_matrix())
    p.torus(c0 + Vector((0, 0, 0.6)), 3.3, 0.1, 'Hatch_Magic_Pink', 40, 4, rot=Euler((-0.3, -0.2, 0)).to_matrix())
    rnd = random.Random(8)
    for k in range(26):                                  # sparkles
        a = rnd.uniform(0, TAU); rr = rnd.uniform(3.0, 5.0)
        p.ico(c0 + Vector((math.cos(a) * rr, math.sin(a) * rr, rnd.uniform(-3, 4))), rnd.uniform(0.08, 0.16),
              rnd.choice(('Hatch_Magic_Cyan', 'Hatch_Magic_Pink', 'Hatch_Sign_Glow')), 1)


def egg_emblem(p, M=I4, s=1.0):
    """big egg-shaped emblem: gold + stone frame, glowing pink egg with white paw, fan of purple crystals"""
    from islands import crystal
    n = 28
    def ring(rx, rz):
        return [(math.cos(TAU * i / n) * rx * s, math.sin(TAU * i / n) * rz * s * (1.12 if i < n / 2 else 0.95))
                for i in range(n + 1)]
    frame_strip(p, M, ring(5.6, 6.4), ring(4.7, 5.5), -0.8, 1.0, 'Castle_Stone_Light')
    frame_strip(p, M, ring(4.8, 5.6), ring(4.3, 5.1), -1.2, 0.6, 'Gold')
    pts = ring(4.4, 5.2)[:-1]
    p.prism(pts, 0.0, 0.8, 'Hatch_Egg_Glow', M @ FLIP)
    paw(p, M @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1))) @ Matrix.Translation((0, -0.3 * s, 0.05)),
        5.0 * s, 0.4, 'Hatch_Sign_Glow')
    for k, (ang, h, mat) in enumerate(((-55, 5.0, 'Crystal_Violet'), (-28, 6.5, 'Crystal_Purple'), (0, 8.0, 'Crystal_Violet'),
                                       (28, 6.5, 'Crystal_Purple'), (55, 5.0, 'Crystal_Violet'))):
        a = math.radians(ang)
        d = Vector((math.sin(a), 0, math.cos(a)))
        base = M @ (Vector((math.sin(a) * 4.6 * s, 0.4, 5.4 * s + math.cos(a) * 0.6)))
        axis = (M.to_3x3() @ d).normalized()
        crystal(p, base, h * s, 0.9 * s, mat, axis=axis)


def eggs_sign_frame(p, M=I4, w=24.0, h=6.4):
    """gold-framed purple band for the EGGS lettering (text is a separate text object)"""
    bevel_box(p, M, (0, 0.4, 0), (w, 0.8, h), 'Hatch_Purple_Dark', 0.1)
    for z in (-h / 2, h / 2):
        bevel_box(p, M, (0, -0.15, z), (w + 0.8, 1.2, 0.6), 'Gold', 0.08)
    for x in (-w / 2, w / 2):
        bevel_box(p, M, (x, -0.15, 0), (0.6, 1.2, h + 0.6), 'Gold', 0.08)


def planter(p, rnd, w=6.0, d=3.6):
    masonry(p, T(0, -d / 2), -w / 2, w / 2, 0, 2.0, rnd, 1.0, (1.6, 2.4), d - 0.4, backing=False)
    bevel_box(p, I4, (0, 0, 2.2), (w + 0.5, d + 0.5, 0.4), 'Castle_Trim', 0.1)
    p.box((0, 0, 2.3), (w - 0.6, d - 0.6, 0.2), 'Dirt')


def _lib(name, sub, builder, *a, **kw):
    p = Part('ASSET_' + name, sub)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def build_hatchery_kit(parent):
    from islands import crystal, crystal_cluster
    coll(KIT, parent)
    R = random.Random
    _lib('Hatch_Stone_Block', KIT, lambda p: bevel_box(p, I4, (0, 0, 1.25), (4.0, 1.6, 2.5), 'Castle_Stone', 0.18))
    _lib('Hatch_Stone_Wall', KIT, lambda p: masonry(p, I4, -6, 6, 0, 10, R(1), 2.5, (3, 5)))
    def corner(p):
        masonry(p, I4, 0, 6, 0, 10, R(2), 2.5, (3, 5))
        masonry(p, RZ(-90), -6, 0, 0, 10, R(3), 2.5, (3, 5))
        quoins(p, I4, 0, 10, R(4), 3.6, 2.0, 2.5, side=1)
    _lib('Hatch_Stone_Corner', KIT, corner)
    _lib('Hatch_Stone_Pillar', KIT, lambda p: pillar(p, I4, 5.0, 0, 22, R(5), cap=None, band=0.55))
    _lib('Hatch_Stone_Arch', KIT, lambda p: voussoirs(p, I4, round_arch(14, 6, 14), round_arch(10, 6, 14), -0.6, 1.6,
                                                      R(6), 2.4))
    def purple_wall(p):
        bevel_box(p, I4, (0, 0.2, 5), (8, 0.6, 10), 'Hatch_Purple', 0.08)
        frame_strip(p, I4, [(-4.3, 0), (-4.3, 10.3), (4.3, 10.3), (4.3, 0)], [(-4, 0), (-4, 10), (4, 10), (4, 0)],
                    -0.45, 0.3, 'Gold')
    _lib('Hatch_Purple_Wall', KIT, purple_wall)
    from shop import roof_slope
    _lib('Hatch_Roof_Piece', KIT, lambda p: roof_slope(p, I4, 0, 8, 0, 4.0, -4, 4, 0.5, mat='Hatch_Roof',
                                                                 course_mat='Hatch_Roof_Dark'))
    _lib('Hatch_Gold_Trim', KIT, lambda p: bevel_box(p, I4, (0, 0, 0.2), (8, 0.35, 0.4), 'Gold', 0.06))
    _lib('Hatch_Egg_Sign', KIT, lambda p: eggs_sign_frame(p, T(0, 0, 3.2), 12, 3.4))
    _lib('Hatch_Egg_Emblem', KIT, lambda p: egg_emblem(p, T(0, 0, 7.0), 0.8))
    _lib('Hatch_Purple_Banner', KIT, purple_banner)
    _lib('Hatch_Crystal', KIT, crystal, (0, 0, 0), 5.0, 0.9, 'Crystal_Violet')
    _lib('Hatch_Crystal_Cluster_Purple', KIT, crystal_cluster, (0, 0, 0), 5.5, R(7),
         ('Crystal_Violet', 'Crystal_Pink_Soft', 'Crystal_Violet'))
    _lib('Hatch_Crystal_Cluster_Blue', KIT, crystal_cluster, (0, 0, 0), 5.5, R(8),
         ('Crystal_Cyan', 'Crystal_Deep', 'Crystal_Cyan'))
    _lib('Hatch_Lantern', KIT, hatch_lantern)
    for nm, r, h in (('S', 1.0, 1.8), ('M', 1.5, 2.4), ('L', 2.1, 3.0)):
        _lib(f'Hatch_Egg_Pedestal_{nm}', KIT, egg_pedestal, r, h)
    _lib('Hatch_Egg_Display', KIT, egg_display)
    _lib('Hatch_Central_Hatchery_Platform', KIT, central_platform)
    _lib('Hatch_Big_Egg', KIT, big_egg)
    _lib('Hatch_Interior_Shelf', KIT, interior_shelf)
    _lib('Hatch_Decorative_Paw', KIT, lambda p: (p.cyl((0, 0, 0.15), 1.6, 0.3, 'Gold', 20, axis='Y'),
                                                 paw(p, M_front(0, -0.16, 0), 2.2, 0.15, 'Hatch_Purple_Dark')))
    _lib('Hatch_Planter', KIT, planter, R(9))
    for k in EGG_TYPES:
        _lib(f'Egg_{k}', KIT, egg, k, 1.0)


# ---------------------------------------------------------------- build -----
# collection names the lobby creates later (tower floors etc.) - suffixed when building inside the lobby
RESERVED = {'Jungle', 'Desert', 'Ice', 'Lava', 'Crystal', 'Shadow', 'Forest', 'Kingdom', 'Cloud', 'Celestial',
            'Divine', 'Hub_Base', 'LIGHTING', 'CAMERAS', 'ENVIRONMENT', 'WATERFALLS', 'FLOATING_ISLANDS'}


def subcolls(in_lobby=False):
    CN.clear()
    tree = (('BUILDING', ROOT), ('Walls', 'BUILDING'), ('Pillars', 'BUILDING'), ('Arches', 'BUILDING'),
            ('Roof', 'BUILDING'), ('Gold_Trim', 'BUILDING'), ('SIGNAGE', ROOT), ('Eggs_Sign', 'SIGNAGE'),
            ('Egg_Emblem', 'SIGNAGE'), ('BANNERS', ROOT), ('INTERIOR', ROOT), ('Central_Platform', 'INTERIOR'),
            ('Shelves', 'INTERIOR'), ('Pedestals', 'INTERIOR'), ('Decorations', 'INTERIOR'), ('EGGS', ROOT)) + \
        tuple((k, 'EGGS') for k in EGG_TYPES) + \
        (('CRYSTALS', ROOT), ('LANTERNS', ROOT), ('LANDSCAPING', ROOT), ('LIGHTING', ROOT))
    for name, par in tree:
        taken = name in bpy.data.collections or (in_lobby and name in RESERVED)
        actual = f'{name} (hatchery)' if taken else name
        CN[name] = actual
        coll(actual, c(par))


def build_hatchery(parent_coll, loc=(0, 0, 0), rot_z=0.0):
    coll(ROOT, parent_coll)
    subcolls(parent_coll is not None)
    root = empty('Hatchery_Root', ROOT, loc, rot_z, 8)
    rnd = random.Random(5150)
    F = 1.0
    HC = Vector((0, 9.0, 0))                   # centre of the octagonal hall
    AP = 15.0                                  # hall apothem

    def fin(p):
        return p.finish(parent=root)

    def I(asset, name, col, xyz, rz=0.0, s=1.0):
        return inst(asset, name, c(col), xyz, rz, s, root)

    # ---------------- plinth + floor ----------------------------------------------------------------
    p = Part('Hatchery_Floor', c('Walls'))
    bevel_box(p, I4, (0, 6, F / 2), (58, 42, F), 'Castle_Trim', 0.2)
    for i in range(2):
        bevel_box(p, I4, (0, -15.7 - i * 1.4, (F - i * 0.5) / 2), (22 - i * 2, 1.4, F - i * 0.5), 'Castle_Stone_Light', 0.12)
    # hall floor: concentric stone rings + purple carpet ring
    for ring, (r0, r1, n, mat) in enumerate(((8.0, 11.0, 16, 'Hatch_Floor'), (11.0, 14.6, 20, 'Hatch_Floor'))):
        for k in range(n):
            a0, a1 = TAU * k / n, TAU * (k + 1) / n
            p.ring_sector(r0 + 0.06, r1 - 0.06, a0 + 0.012, a1 - 0.012, F, F + 0.22, mat, 3, center=(HC.x, HC.y))
    p.ring_sector(7.0, 8.0, 0, TAU, F, F + 0.24, 'Hatch_Carpet', 32, center=(HC.x, HC.y))
    p.ring_sector(7.9, 8.15, 0, TAU, F, F + 0.27, 'Gold', 32, center=(HC.x, HC.y))
    p.cyl((HC.x, HC.y, F + 0.11), 7.2, 0.22, 'Hatch_Floor', 32)
    # purple runner from the doors to the platform with a paw medallion
    bevel_box(p, I4, (0, -6.0, F + 0.14), (6.0, 14.0, 0.28), 'Hatch_Carpet', 0.04)
    for s in (-1, 1):
        bevel_box(p, I4, (s * 2.6, -6.0, F + 0.3), (0.3, 13.6, 0.06), 'Gold', 0.01)
    p.cyl((0, -6.0, F + 0.32), 2.2, 0.06, 'Gold', 24)
    paw(p, T(0, -5.8, F + 0.35), 2.6, 0.04, 'Hatch_Purple_Dark')
    fin(p)

    # ---------------- hall walls: square exterior (masonry) around an octagonal interior ------------
    w = Part('Hatchery_Hall_Core', c('Walls'))
    oct_out = [(HC.x + 17.2 * math.cos(math.radians(22.5 + 45 * i)) / math.cos(math.radians(22.5)),
                HC.y + 17.2 * math.sin(math.radians(22.5 + 45 * i)) / math.cos(math.radians(22.5))) for i in range(8)]
    # solid core filling the square shell minus the octagonal room (corner triangles + wall bands)
    for (x0, y0, x1, y1) in ((-17, 25.8, 17, 26.2), (-17.2, -8, -16.8, 26.2), (16.8, -8, 17.2, 26.2)):
        w.box(((x0 + x1) / 2, (y0 + y1) / 2, 12), (x1 - x0, y1 - y0, 22), 'Castle_Seam')
    for sx in (-1, 1):
        for sy, yc in ((-1, -8.0), (1, 26.0)):
            tri = [(sx * 17.0, yc), (sx * 17.0, yc - sy * 7.4), (sx * 9.6, yc)]
            w.prism(tri, F, 23.0, 'Castle_Seam')
    fin(w)

    # interior octagon faces: purple plaster with arched niches (shelves) + stone pilasters
    iw = Part('Hatchery_Interior_Walls', c('Walls'))
    for i in range(8):
        deg = 90 + 45 * i                                     # face directions (0: back wall, 4: front)
        a = math.radians(deg)
        centre = HC + Vector((math.cos(a), math.sin(a), 0)) * AP
        M = T(centre.x, centre.y) @ RZ(deg - 90)              # local -y faces the room centre
        side = 2 * AP * math.tan(math.pi / 8)
        if i == 4:                                            # front face: doorway (the arch passage)
            continue
        bevel_box(iw, M, (0, 0.5, (F + 21) / 2), (side - 0.2, 1.0, 20), 'Hatch_Purple', 0.06)
        bevel_box(iw, M, (0, -0.1, F + 0.6), (side, 0.6, 1.2), 'Castle_Trim', 0.1)     # skirting
        bevel_box(iw, M, (0, -0.2, 20.4), (side, 1.0, 1.0), 'Castle_Trim', 0.12)        # cornice
        bevel_box(iw, M, (0, -0.75, 19.8), (side, 0.15, 0.25), 'Gold', 0.03)
        # stone pilaster on each corner (between faces)
        pc = HC + Vector((math.cos(a + math.pi / 8), math.sin(a + math.pi / 8), 0)) * (AP / math.cos(math.pi / 8) - 0.6)
        for kk in range(7):
            bevel_box(iw, T(pc.x, pc.y) @ RZ(deg - 90 + 22.5), (0, 0, F + kk * 2.85 + 1.42), (1.8, 1.8, 2.75),
                      'Castle_Stone_Light', 0.16)
    fin(iw)
    for i in (1, 2, 6, 7):                                   # egg shelves in the side / back-diagonal niches
        deg = 90 + 45 * i
        a = math.radians(deg)
        centre = HC + Vector((math.cos(a), math.sin(a), 0)) * (AP - 0.4)
        I('Hatch_Interior_Shelf', f'Hatchery_Shelf_{i}', 'Shelves', (centre.x, centre.y, F + 2.0), math.radians(deg - 90))
        for lv, z in enumerate(SHELF_Z):
            for k in range(3):
                off = Matrix.Rotation(math.radians(deg - 90), 3, 'Z') @ Vector((-1.9 + k * 1.9, 0, 0))
                kind = EGG_TYPES[(i * 3 + k + lv * 5) % 10]
                I(f'Egg_{kind}', f'Hatchery_ShelfEgg_{i}_{lv}{k}', kind, (centre.x + off.x, centre.y + off.y,
                                                                           F + 2.0 + z + 0.15), rnd.uniform(0, TAU), 0.55)
    # back face: glowing blue arched window above a decorative paw
    deg = 90
    centre = HC + Vector((0, AP - 0.2, 0))
    bw = Part('Hatchery_Back_Window', c('Decorations'))
    Mw = T(centre.x, centre.y)
    bw.prism(lifted(round_arch(7, 8, 12), 0, F + 8), -0.1, 0.2, 'Hatch_Oculus', Mw @ FLIP)
    voussoirs(bw, Mw, lifted(round_arch(9.6, 8, 12), 0, F + 8), lifted(round_arch(7, 8, 12), 0, F + 8), -0.9, 0.2, rnd, 1.8)
    fin(bw)
    I('Hatch_Decorative_Paw', 'Hatchery_BackPaw', 'Decorations', (centre.x, centre.y - 0.5, F + 4.5))

    # dome + oculus
    dm = Part('Hatchery_Dome', c('Roof'))
    rings = []
    for k, (r, z) in enumerate(((AP / math.cos(math.pi / 8), 21.0), (14.5, 24.0), (12.0, 26.6), (8.5, 28.4), (4.6, 29.4))):
        rings.append([Vector((HC.x + r * math.cos(math.radians(22.5 + 45 * i)), HC.y + r * math.sin(math.radians(22.5 + 45 * i)), z))
                      for i in range(8)])
    dm.loft(rings, 'Hatch_Purple_Dark', cap_bottom=False, cap_top=False)
    for k in range(8):                                    # gold ribs
        a = math.radians(22.5 + 45 * k)
        pts = [Vector((HC.x + r * math.cos(a) * 0.98, HC.y + r * math.sin(a) * 0.98, z - 0.3)) for r, z in
               ((16.0, 21.0), (14.5, 24.0), (12.0, 26.6), (8.5, 28.4), (4.6, 29.4))]
        for q0, q1 in zip(pts, pts[1:]):
            dm.beam(q0, q1, 0.5, 0.5, 'Gold')
    dm.torus((HC.x, HC.y, 29.3), 4.6, 0.45, 'Gold', 24, 6)
    dm.cyl((HC.x, HC.y, 29.6), 4.4, 0.2, 'Hatch_Oculus', 24)
    fin(dm)

    # ---------------- exterior masonry ---------------------------------------------------------------
    ex = Part('Hatchery_Facade', c('Walls'))
    yF = -8.0
    ARCH_W, ARCH_HS = 13.0, 11.0
    opening = lifted(round_arch(ARCH_W, ARCH_HS, 14), 0, F)
    masonry(ex, T(0, yF - 0.6), -17, 17, F, 22.0, rnd, 2.6, (3.2, 5.5), 1.6,
            skip=lambda x, z, ww, h: inside(lifted(round_arch(ARCH_W + 5.4, ARCH_HS, 14), 0, F), x, z), backing=False)
    rect_minus_arch(ex, T(0, yF - 0.6), -17, 17, F, 22.0, lifted(round_arch(ARCH_W, ARCH_HS, 14), 0, F), 1.0, 2.0,
                    'Castle_Seam')
    # arch: outer voussoirs, gold ring, recessed purple inner arch with its own stones
    voussoirs(ex, T(0, yF - 0.6), lifted(round_arch(ARCH_W + 5.4, ARCH_HS, 14), 0, F),
              lifted(round_arch(ARCH_W + 1.6, ARCH_HS, 14), 0, F), -1.6, 1.2, rnd, 2.6)
    frame_strip(ex, T(0, yF - 0.6), lifted(round_arch(ARCH_W + 1.6, ARCH_HS, 14), 0, F),
                lifted(round_arch(ARCH_W + 0.8, ARCH_HS, 14), 0, F), -1.0, 1.6, 'Gold')
    frame_strip(ex, T(0, yF - 0.6), lifted(round_arch(ARCH_W + 0.8, ARCH_HS, 14), 0, F), opening, 0.4, 2.6,
                'Hatch_Purple')
    # reveal / passage through the wall
    for s in (-1, 1):
        bevel_box(ex, I4, (s * (ARCH_W / 2 + 0.4), yF + 0.6, F + ARCH_HS / 2), (0.8, 2.4, ARCH_HS), 'Hatch_Purple', 0.06)
    trim_run(ex, T(0, yF - 0.6), -17, 17, F, h=1.2, out=1.0)
    quoins(ex, T(-17.2, yF - 0.6), F, 22.0, rnd, 3.6, 2.0, 2.6, side=1, mat='Castle_Trim')
    quoins(ex, T(17.2, yF - 0.6), F, 22.0, rnd, 3.6, 2.0, 2.6, side=-1, mat='Castle_Trim')
    fin(ex)
    sd = Part('Hatchery_Sides_Back', c('Walls'))
    for s in (-1, 1):                                        # hall side walls above the wing roofs
        xr = (-8.0, 26.0) if s > 0 else (-26.0, 8.0)
        masonry(sd, T(s * 17.4, 0) @ RZ(s * 90), xr[0], xr[1], 14.0, 22.0, rnd, 2.6, (3.2, 5.5), 1.6, backing=False)
    # back wall (exterior) with a raised purple panel, two egg emblems and a small door
    door = lifted(round_arch(4.4, 5.5, 10), 0, F)
    masonry(sd, T(0, 26.6) @ RZ(180), -17.2, 17.2, F, 22.0, rnd, 2.6, (3.2, 5.5), 1.6,
            skip=lambda x, z, ww, h: abs(x) < 5.4 and z > F + 6.4 or inside(door, -x, z), backing=False)
    voussoirs(sd, T(0, 26.6) @ RZ(180), lifted(round_arch(6.6, 5.5, 10), 0, F), door, -0.6, 1.0, rnd, 1.6)
    for k in range(3):
        bevel_box(sd, I4, (-1.45 + k * 1.45, 26.5, F + 3.2), (1.4, 0.3, 6.4), 'Shop_Wood', 0.06)
    bevel_box(sd, I4, (0, 27.0, F + 15.5), (10.0, 0.8, 18.0), 'Hatch_Purple', 0.08)
    frame_strip(sd, T(0, 27.4) @ RZ(180), [(-5.4, F + 6.4), (-5.4, F + 24.8), (5.4, F + 24.8), (5.4, F + 6.4)],
                [(-5.0, F + 6.4), (-5.0, F + 24.4), (5.0, F + 24.4), (5.0, F + 6.4)], -0.4, 0.3, 'Gold')
    sd.prism([(-5.4, F + 24.8), (5.4, F + 24.8), (0, F + 30)], 26.6, 27.6, 'Hatch_Purple', FLIP)   # pointed gable
    for zz in (F + 11.0, F + 18.5):
        sd.cyl((0, 27.5, zz), 2.6, 0.4, 'Gold', 24, axis='Y')
        sd.cyl((0, 27.75, zz), 2.2, 0.2, 'Hatch_Egg_Glow', 24, axis='Y')
        paw(sd, M_front(0, 27.95, zz - 0.2, math.pi), 2.6, 0.12, 'Hatch_Sign_Glow')
    quoins(sd, T(-17.2, 26.6) @ RZ(180), F, 22.0, rnd, 3.6, 2.0, 2.6, side=-1, mat='Castle_Trim')
    quoins(sd, T(17.2, 26.6) @ RZ(180), F, 22.0, rnd, 3.6, 2.0, 2.6, side=1, mat='Castle_Trim')
    fin(sd)

    # ---------------- sign band, parapet and the egg emblem -----------------------------------------
    sg = Part('Hatchery_Eggs_Sign', c('Eggs_Sign'))
    eggs_sign_frame(sg, T(0, yF - 2.4, 24.6), 26.0, 5.6)
    fin(sg)
    text_mesh('Hatchery_Eggs_Sign_Text', 'EGGS', c('Eggs_Sign'), 5.0, 0.6, 'Hatch_Sign_Glow', (0, yF - 3.0, 24.4), 0, root)
    pp = Part('Hatchery_Parapet', c('Roof'))
    para = [(-13.5, 27.4), (13.5, 27.4), (13.5, 30.4), (8.0, 33.6), (-8.0, 33.6), (-13.5, 30.4)]
    pp.prism(para, yF - 2.4, yF + 1.0, 'Hatch_Purple', FLIP)
    frame_strip(pp, T(0, yF - 2.4), para + [para[0]], [(x * 0.94, 27.4 + (z - 27.4) * 0.9) for x, z in para + [para[0]]],
                -0.5, 0.2, 'Gold')
    for s in (-1, 1):                                        # stone corner blocks on the parapet shoulders
        bevel_box(pp, I4, (s * 13.5, yF - 0.7, 28.9), (2.4, 3.4, 3.0), 'Castle_Stone_Light', 0.18)
        bevel_box(pp, I4, (s * 13.5, yF - 0.7, 30.6), (2.9, 3.9, 0.5), 'Castle_Trim', 0.12)
    fin(pp)
    em = Part('Hatchery_Egg_Emblem', c('Egg_Emblem'))
    egg_emblem(em, T(0, yF - 3.4, 37.4), 1.12)
    fin(em)

    # ---------------- entrance pillars with banners ---------------------------------------------------
    pl = Part('Hatchery_Pillars', c('Pillars'))
    for s in (-1, 1):
        pillar(pl, T(s * 14.0, yF - 3.4), 5.4, F, 25.0, rnd, cap=None, band=0.58)
        bevel_box(pl, T(s * 14.0, yF - 3.4), (0, 0, F + 27.2), (7.0, 7.0, 1.0), 'Castle_Trim', 0.15)
        bevel_box(pl, T(s * 14.0, yF - 3.4), (0, -3.55, F + 27.2), (6.4, 0.3, 0.35), 'Gold', 0.05)
    fin(pl)
    for s in (-1, 1):
        I('Hatch_Purple_Banner', f'Hatchery_PillarBanner_{"LR"[s > 0]}', 'BANNERS', (s * 14.0, yF - 6.15, F + 21.0), 0, 1.1)
        I('Hatch_Lantern', f'Hatchery_PillarLantern_{"LR"[s > 0]}', 'LANTERNS', (s * 14.0, yF - 3.4, F + 27.7), 0, 1.15)

    # ---------------- wings ----------------------------------------------------------------------------
    wg = Part('Hatchery_Wings', c('Walls'))
    WT = 14.0
    for s in (-1, 1):
        x0, x1 = (17.4, 28.0) if s > 0 else (-28.0, -17.4)
        wg.box(((x0 + x1) / 2, 7.0, (F + WT) / 2), (x1 - x0, 26.0, WT - F), 'Castle_Seam')
        xr = (-6.0, 20.0) if s > 0 else (-20.0, 6.0)
        masonry(wg, T(s * 28.1, 0) @ RZ(s * 90), xr[0], xr[1], F, WT, rnd, 2.6, (3.2, 5.5), 1.6, backing=False)
        masonry(wg, T(0, 20.1) @ RZ(180), -x1, -x0, F, WT, rnd, 2.6, (3.2, 5.5), 1.6, backing=False)
        quoins(wg, T(s * 28.1, 20.1) @ RZ(180), F, WT, rnd, 3.6, 2.0, 2.6, side=s, mat='Castle_Trim')
        # front: purple panel between the hall pillar and the corner pillar
        cx = s * 22.4
        bevel_box(wg, I4, (cx, -6.0, F + 6.2), (8.2, 0.8, 11.2), 'Hatch_Purple', 0.08)
        frame_strip(wg, T(cx, -6.5), [(-4.5, F), (-4.5, F + 12.2), (4.5, F + 12.2), (4.5, F)],
                    [(-4.1, F), (-4.1, F + 11.8), (4.1, F + 11.8), (4.1, F)], -0.4, 0.2, 'Gold')
        bevel_box(wg, I4, (cx, -6.4, F + 0.7), (8.6, 1.4, 1.4), 'Castle_Trim', 0.12)
        trim_run(wg, T(0, -6.5), x0, x1 + s * 0.0, WT - 1.6, h=1.6, out=1.0)
        pillar(wg, T(s * 27.6, -6.6), 3.6, 0, WT + 2.4, rnd, cap=None, band=0.5, panel=False)
        # side purple panel with a banner
        bevel_box(wg, T(s * 28.3, 7.0) @ RZ(s * 90), (0, 0, F + 6.0), (7.0, 0.6, 9.0), 'Hatch_Purple', 0.06)
    fin(wg)
    for s in (-1, 1):
        I('Hatch_Purple_Banner', f'Hatchery_WingBanner_{"LR"[s > 0]}', 'BANNERS', (s * 22.4, -6.55, F + 11.6), 0, 0.95)
        I('Hatch_Purple_Banner', f'Hatchery_SideBanner_{"LR"[s > 0]}', 'BANNERS', (s * 28.75, 7.0, F + 10.4),
          math.radians(90 if s > 0 else -90), 0.8)
        I('Hatch_Lantern', f'Hatchery_WingLantern_{"LR"[s > 0]}', 'LANTERNS', (s * 27.6, -6.6, WT + 2.2), 0, 1.1)

    # ---------------- roofs ----------------------------------------------------------------------------
    from shop import roof_slope
    rf = Part('Hatchery_Roof', c('Roof'))
    for s in (-1, 1):                                          # wing lean-to roofs (purple, gold fascia)
        Mw = I4 if s > 0 else Matrix.Scale(-1, 4, Vector((1, 0, 0)))
        roof_slope(rf, Mw, 29.8, 17.3, WT + 0.2, 19.6, -8.4, 21.6, 0.7, mat='Hatch_Roof', sag=0.35,
                   course_mat='Hatch_Roof_Dark')
        bevel_box(rf, I4, (s * 29.9, 6.6, WT + 0.15), (0.5, 30.2, 0.55), 'Gold', 0.06)
        ang = math.atan2(19.6 - WT, 12.5)
        Mr = T(s * 23.55, -8.5, (WT + 19.6) / 2 + 0.2) @ Matrix.Rotation(s * ang, 4, 'Y')
        bevel_box(rf, Mr, (0, 0, 0), (math.hypot(12.5, 19.6 - WT) + 0.4, 0.5, 0.55), 'Gold', 0.06)
    # hall roof: low purple hip roof around the dome drum, gold edge
    for k in range(4):
        deg = 90 * k
        Mk = T(HC.x, HC.y) @ RZ(deg)
        pts = [(-18.6, -18.6, 22.4), (18.6, -18.6, 22.4), (12.0, -12.0, 26.0), (-12.0, -12.0, 26.0)]
        q = [Mk @ Vector(v) for v in pts]
        rf.hexa(q + [v + Vector((0, 0, 0.8)) for v in q], 'Hatch_Roof')
        bevel_box(rf, Mk, (0, -18.7, 22.6), (37.6, 0.5, 0.6), 'Gold', 0.06)
    rf.cyl((HC.x, HC.y, 27.3), 12.4, 2.6, 'Hatch_Purple', 8)                 # dome drum (outside)
    rf.loft([[Vector((HC.x + r * math.cos(math.radians(22.5 + 45 * i)), HC.y + r * math.sin(math.radians(22.5 + 45 * i)), z))
              for i in range(8)] for r, z in ((13.0, 28.6), (10.5, 31.2), (6.6, 32.8), (5.0, 33.2))],
            'Hatch_Roof', cap_bottom=False, cap_top=False)
    rf.torus((HC.x, HC.y, 33.2), 5.0, 0.4, 'Gold', 24, 6)
    rf.cyl((HC.x, HC.y, 33.2), 4.8, 0.25, 'Hatch_Oculus', 24)
    fin(rf)

    # ---------------- interior pieces ---------------------------------------------------------------------
    I('Hatch_Central_Hatchery_Platform', 'Hatchery_Central_Platform', 'Central_Platform', (HC.x, HC.y, F + 0.22))
    I('Hatch_Big_Egg', 'Hatchery_Big_Egg', 'Central_Platform', (HC.x, HC.y, F + 0.22))
    for k in range(2):                                         # crystal pedestals behind the platform
        a = math.radians(45 + 90 * k)
        pos = HC + Vector((math.cos(a), math.sin(a), 0)) * 10.0
        I('Hatch_Egg_Pedestal_M', f'Hatchery_CrystalPedestal_{k}', 'Pedestals', (pos.x, pos.y, F + 0.22))
        I(('Hatch_Crystal_Cluster_Blue', 'Hatch_Crystal_Cluster_Purple')[k % 2], f'Hatchery_PedestalCrystal_{k}',
          'CRYSTALS', (pos.x, pos.y, F + 2.62), rnd.uniform(0, TAU), 0.5)
    for k, (deg, kind) in enumerate(((165, 'Fire'), (195, 'Ice'), (15, 'Gold'), (345, 'Dark'))):
        a = math.radians(deg)
        pos = HC + Vector((math.cos(a), math.sin(a), 0)) * 11.4
        I('Hatch_Egg_Pedestal_S', f'Hatchery_EggPedestal_{k}', 'Pedestals', (pos.x, pos.y, F + 0.22))
        I(f'Egg_{kind}', f'Hatchery_PedestalEgg_{k}', kind, (pos.x, pos.y, F + 2.1), rnd.uniform(0, TAU), 0.8)
    for k, (x, y) in enumerate(((-7.4, HC.y - 7.4), (7.4, HC.y - 7.4))):   # front-corner display stands
        I('Hatch_Egg_Display', f'Hatchery_Display_{k}', 'Pedestals', (x, y, F + 0.22))
        for j, (dx, dz, kind) in enumerate(((0, 3.0, 'Crystal'), (1.8, 2.0, 'Pink'), (-1.8, 2.0, 'Cyan'),
                                            (2.6, 1.0, 'Green'), (-2.6, 1.0, 'Blue'))):
            I(f'Egg_{kind}', f'Hatchery_DisplayEgg_{k}{j}', kind, (x + dx, y - abs(dx) * 0.2, F + 0.22 + dz),
              rnd.uniform(0, TAU), 0.55)
    for k, deg in enumerate((157.5, 202.5, 22.5, 337.5)):      # bracket lanterns on the pilasters
        a = math.radians(deg)
        pos = HC + Vector((math.cos(a), math.sin(a), 0)) * (AP / math.cos(math.pi / 8) - 1.6)
        I('Shop_Lantern_Wall', f'Hatchery_WallLantern_{k}', 'LANTERNS', (pos.x, pos.y, F + 13.0), a - math.pi / 2, 0.8)
    for k, deg in enumerate((225, 315)):                       # banners on the front diagonal walls
        a = math.radians(deg)
        pos = HC + Vector((math.cos(a), math.sin(a), 0)) * (AP - 0.15)
        I('Hatch_Purple_Banner', f'Hatchery_InteriorBanner_{k}', 'BANNERS', (pos.x, pos.y, F + 18.0), math.radians(deg - 90),
          1.0)

    # ---------------- landscaping + crystals outside ------------------------------------------------------
    for k, (x, y, nm, sc, rz, z) in enumerate((
            (-14.0, -14.5, 'Hatch_Planter', 1.0, 0, 0), (14.0, -14.5, 'Hatch_Planter', 1.0, 0, 0),
            (-15.5, -14.5, 'Hatch_Crystal_Cluster_Purple', 0.55, 0.3, 2.4), (15.5, -14.5, 'Hatch_Crystal_Cluster_Blue', 0.55, 1.0, 2.4),
            (-12.4, -14.6, 'Bush_02', 0.7, 0, 2.4),
            (12.4, -14.6, 'Bush_01', 0.7, 0, 2.4),
            (-24.0, -11.0, 'Hatch_Planter', 1.2, 0, 0), (24.0, -11.0, 'Hatch_Planter', 1.2, 0, 0),
            (-24.0, -11.0, 'Bush_02', 1.0, 0.4, 2.4), (24.0, -11.0, 'Bush_03', 1.0, 0.2, 2.4),
            (-25.6, -11.0, 'Hatch_Crystal_Cluster_Blue', 0.45, 0, 2.4), (25.6, -11.0, 'Hatch_Crystal_Cluster_Purple', 0.45, 0, 2.4),
            (-31.5, -2.0, 'Hatch_Crystal_Cluster_Purple', 0.8, 0.5, 0), (31.5, 0.0, 'Hatch_Crystal_Cluster_Blue', 0.8, 0.2, 0),
            (-32.0, 22.0, 'Tree_Medium_High', 0.9, 0.3, 0), (32.0, 23.0, 'Tree_Large_High', 0.8, 1.0, 0),
            (-6.0, 30.0, 'Bush_02', 1.1, 0, 0), (7.0, 30.0, 'Ground_Plant_01', 1.2, 0, 0),
            (-31.0, 10.0, 'Bush_01', 1.2, 0, 0), (31.0, 12.0, 'Ground_Plant_02', 1.2, 0, 0))):
        I(nm, f'Hatchery_Land_{nm}_{k}', 'CRYSTALS' if 'Crystal' in nm else 'LANDSCAPING', (x, y, z), rz, sc)
    for s in (-1, 1):
        I('Castle_Lantern', f'Hatchery_PathLantern_{"LR"[s > 0]}', 'LANTERNS', (s * 9.0, -19.0, 0), 0, 0.85)
    from foliage import vine
    vv = Part('Hatchery_Vines', c('LANDSCAPING'))
    for x, y, z in ((-17.4, -10.5, 21.0), (17.4, -10.5, 21.0), (-28.4, 20.4, 13.5), (28.4, 20.4, 13.5),
                    (-12.0, 27.0, 21.5), (12.0, 27.0, 21.5)):
        vine(vv, (x, y, z), rnd.uniform(6, 12), rnd, 1.1)
    fin(vv)

    # ---------------- lights ---------------------------------------------------------------------------
    for k, (x, y, z, e, col) in enumerate(((HC.x, HC.y, F + 14, 3200, (0.8, 0.45, 1.0)),
                                           (HC.x, HC.y - 5, F + 5, 1200, (1.0, 0.45, 0.95)),
                                           (HC.x - 8, HC.y + 4, F + 9, 900, (0.3, 0.8, 1.0)),
                                           (HC.x + 8, HC.y + 4, F + 9, 900, (0.3, 0.8, 1.0)),
                                           (0, -9.5, F + 14, 3000, (1.0, 0.7, 0.4)),
                                           (-14, -13, F + 26, 1500, (1.0, 0.7, 0.4)), (14, -13, F + 26, 1500, (1.0, 0.7, 0.4)))):
        L = bpy.data.lights.new(f'Hatchery_Light_{k}', 'POINT')
        L.color = col; L.energy = e; L.shadow_soft_size = 1.5
        o = bpy.data.objects.new(L.name, L)
        o.location = (x, y, z); o.parent = root
        coll(c('LIGHTING')).objects.link(o)
    return root


def build_hatchery_cameras(root_loc=(0, 0, 0), rot_z=0.0, coll_name='CAMERAS', prefix='CAM_Hatchery', only=None):
    M = Matrix.Translation(root_loc) @ Matrix.Rotation(rot_z, 4, 'Z')
    out = {}
    for name, loc, tgt, lens in (('Front', (-4, -88, 17), (0, 2, 22), 28), ('Interior', (-2.5, -6.5, 6.5), (0, 12, 7.5), 20),
                                 ('Side', (-62, -40, 26), (0, 6, 14), 30), ('Rear', (26, 70, 24), (0, 12, 14), 30),
                                 ('Player', (4, -36, 5.2), (0, 6, 10), 24)):
        if only and name not in only:
            continue
        cam = bpy.data.cameras.new(f'{prefix}_{name}')
        cam.lens = lens; cam.clip_start = 0.3; cam.clip_end = 40000
        o = bpy.data.objects.new(f'{prefix}_{name}', cam)
        L, Tt = M @ Vector(loc), M @ Vector(tgt)
        o.location = L
        o.rotation_euler = (Tt - L).to_track_quat('-Z', 'Y').to_euler()
        coll(coll_name).objects.link(o)
        out[name] = o
    return out
