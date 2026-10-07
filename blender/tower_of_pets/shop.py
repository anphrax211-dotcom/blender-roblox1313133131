"""TOWER OF PETS - SHOP, rebuilt from the shop reference sheet with the castle masonry language.

Layout (local space, studs, front = -Y, ground z = 0, origin = centre of the plinth front-back):
    central hall   x +-17, y -11..19, open front between two dark stone pillars, red lintel + stone arch,
                   raised arched gable with the big SHOP sign, curved red gable roof with gold fascia
    side wings     x +-17..25, y -8..14, masonry with red plank fronts, paw banners, lean-to red roofs,
                   corner pillars with lanterns
    interior       wood floor, panelled walls, back-wall red panel with glowing cart, shelves of items,
                   curved counter with a gold paw (room behind it for an NPC), red carpet runner + round paw rug,
                   ceiling beams, hanging lanterns, red banners
    back           masonry with an arched back door, barrels, crates, vines
A 5-stud Roblox avatar fits easily: entrance 21 x 16 studs, counter 3.4 studs high, 4+ studs walkways.

Collections: TOWER_OF_PETS_SHOP / BUILDING (Walls, Pillars, Arches, Trim, Roof), SIGNAGE (Main_Shop_Sign,
Small_Shop_Signs), BANNERS, INTERIOR (Counter, Shelves, Carpet, Decorations), SHOP_ITEMS, LIGHTING (shop),
LANDSCAPING.  Modular kit (SHOP_KIT in the asset library): Shop_Stone_Block, Shop_Stone_Wall,
Shop_Stone_Corner, Shop_Stone_Pillar, Shop_Stone_Arch, Shop_Red_Wall_Panel, Shop_Roof_Piece, Shop_Gold_Trim,
Shop_Sign, Shop_Banner, Shop_Lantern, Shop_Counter, Shop_Shelf, Shop_Crate, Shop_Chest, Shop_Gift_Box,
Shop_Potion_*, Shop_Pet_Item, Shop_Pet_Food, Shop_Barrel, Shop_Carpet, Shop_Planter
(prefixed 'Shop_' because castle / island assets already use some of the plain names).
"""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
from common import (Part, MATS, mat_plain, mat_noise, coll, inst, ASSETS, empty, paw, M_front, text_mesh,
                    round_arch, pointed_arch, TAU)
from castle import (bevel_box, masonry, quoins, voussoirs, pillar, trim_run, inside, lifted, frame_strip,
                    STONES)

ROOT = 'TOWER_OF_PETS_SHOP'
KIT = 'SHOP_KIT'
I4 = Matrix.Identity(4)
FLIP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))       # local XY drawing -> XZ plane


def RZ(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def T(x, y, z=0.0):
    return Matrix.Translation((x, y, z))


# ---------------------------------------------------------------- materials -
def build_shop_materials():
    P = mat_plain
    mat_noise('Shop_Stone_Dark', (0.34, 0.34, 0.39), (0.39, 0.39, 0.44), 0.8, 0.15, 0.1, 1.2)
    mat_noise('Red_Wood', (0.62, 0.06, 0.07), (0.70, 0.09, 0.09), 0.6, 0.3, 0.15, 2.0)
    P('Red_Wood_Dark', (0.42, 0.04, 0.05), 0.6)
    mat_noise('Shop_Roof', (0.56, 0.05, 0.07), (0.63, 0.08, 0.09), 0.55, 0.2, 0.1, 1.5)
    P('Shop_Roof_Dark', (0.38, 0.03, 0.04), 0.6)
    P('Red_Fabric', (0.82, 0.04, 0.08), 0.75)
    mat_noise('Carpet_Red', (0.62, 0.03, 0.05), (0.68, 0.05, 0.07), 0.9, 0.6, 0.05, 3.0)
    mat_noise('Interior_Wood', (0.34, 0.18, 0.08), (0.40, 0.22, 0.10), 0.7, 0.5, 0.2, 3.0)
    mat_noise('Shop_Wood', (0.55, 0.30, 0.12), (0.62, 0.35, 0.15), 0.7, 0.5, 0.2, 3.0)
    P('Sign_Emissive', (1.0, 0.97, 0.90), 0.4, emit=1.4)
    P('Potion_Pink', (1.0, 0.25, 0.65), 0.1, emit=0.6)
    P('Potion_Blue', (0.15, 0.55, 1.0), 0.1, emit=0.6)
    P('Potion_Green', (0.25, 0.95, 0.30), 0.1, emit=0.6)
    P('Potion_Purple', (0.60, 0.25, 1.0), 0.1, emit=0.6)
    P('Glass', (0.85, 0.95, 1.0), 0.05, alpha=0.45)
    P('Gift_Pink', (1.0, 0.35, 0.70), 0.5)
    P('Gift_Blue', (0.15, 0.55, 1.0), 0.5)
    P('Cart_Glow', (1.0, 0.96, 0.92), 0.4, emit=1.6)


# ---------------------------------------------------------------- kit -------
def shop_lantern(p, M=I4):
    """black iron lantern with warm glow (origin at its base)"""
    bevel_box(p, M, (0, 0, 0.25), (1.8, 1.8, 0.5), 'Lantern_Metal', 0.08)
    p.box(M @ Vector((0, 0, 1.7)), (1.4, 1.4, 2.4), 'Lantern_Glow')
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box(M @ Vector((sx * 0.75, sy * 0.75, 1.7)), (0.28, 0.28, 2.6), 'Lantern_Metal')
    bevel_box(p, M, (0, 0, 3.05), (2.3, 2.3, 0.4), 'Lantern_Metal', 0.06)
    p.cyl(M @ Vector((0, 0, 3.8)), 1.6, 1.3, 'Lantern_Metal', 4, r2=0.15, rot=Matrix.Rotation(math.pi / 4, 3, 'Z'))
    p.ico(M @ Vector((0, 0, 4.6)), 0.3, 'Gold', 1)


def shop_lantern_wall(p):
    """wall lantern on a curled iron bracket (mounts on a face at local y = 0, hangs toward -y)"""
    p.box((0, -0.3, 0), (1.0, 0.6, 1.6), 'Lantern_Metal')
    p.beam(Vector((0, -0.3, 0.4)), Vector((0, -2.6, 0.9)), 0.3, 0.3, 'Lantern_Metal')
    p.torus((0, -2.0, 1.2), 0.5, 0.12, 'Gold', 10, 4, rot=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    shop_lantern(p, T(0, -2.8, -3.2))


def red_banner(p, M=I4, w=3.6, length=9.0):
    """deep red fabric banner, gold trim, gold paw, small gold top bar (hangs from local origin, faces -y)"""
    Mb = M @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    o = [(-w / 2, 0), (w / 2, 0), (w / 2, -length), (0, -length - w * 0.55), (-w / 2, -length)]
    p.prism(o, -0.25, 0.0, 'Red_Fabric', Mb)
    edge = [(-w / 2, 0), (-w / 2, -length), (0, -length - w * 0.55), (w / 2, -length), (w / 2, 0)]
    inner = [(-w / 2 + 0.35, 0), (-w / 2 + 0.35, -length + 0.15), (0, -length - w * 0.55 + 0.5),
             (w / 2 - 0.35, -length + 0.15), (w / 2 - 0.35, 0)]
    for (a0, a1), (b0, b1) in zip(zip(edge, edge[1:]), zip(inner, inner[1:])):
        q = [a0, a1, b1, b0]
        p.hexa([Mb @ Vector((x, z, 0.0)) for x, z in q] + [Mb @ Vector((x, z, 0.18)) for x, z in q], 'Gold')
    paw(p, Mb @ Matrix.Translation((0, -length * 0.55, 0.0)), w * 0.72, 0.2, 'Gold')
    p.cyl(M @ Vector((0, -0.3, 0.35)), 0.25, w + 1.0, 'Gold', 8, axis='X')
    for s in (-1, 1):
        p.ico(M @ Vector((s * (w / 2 + 0.5), -0.3, 0.35)), 0.35, 'Gold', 1)
    p.cone(M @ Vector((0, -0.3, 0.6)), 0.45, 0.8, 'Gold', 4)


def shelf(p, rnd, w=6.0, d=1.6, h=9.0):
    """wooden display shelf unit (origin at the floor, front -y) - items are placed as separate instances"""
    for s in (-1, 1):
        bevel_box(p, I4, (s * (w / 2 - 0.25), 0, h / 2), (0.5, d, h), 'Interior_Wood', 0.1)
    bevel_box(p, I4, (0, d / 2 - 0.15, h / 2), (w, 0.3, h), 'Interior_Wood', 0.05)
    for z in (0.4, h * 0.36, h * 0.68):
        bevel_box(p, I4, (0, 0, z), (w - 0.5, d, 0.3), 'Shop_Wood', 0.06)
        bevel_box(p, I4, (0, -d / 2 + 0.05, z + 0.15), (w - 0.5, 0.12, 0.18), 'Gold', 0.03)
    bevel_box(p, I4, (0, -0.15, h + 0.3), (w + 0.6, d + 0.4, 0.6), 'Shop_Wood', 0.12)
    p.cone((0, -d / 2 + 0.05, h + 0.9), 0.6, 0.9, 'Gold', 4)


SHELF_LEVELS = (0.55, 9.0 * 0.36 + 0.15, 9.0 * 0.68 + 0.15)


def counter(p, rnd):
    """curved-front wooden counter with gold trim and a gold paw (origin floor, front -y); 3.4 studs high"""
    segs = [(-7.5, -5.0, 25), (-5.0, 5.0, 0), (5.0, 7.5, -25)]
    for x0, x1, ang in segs:
        cx = (x0 + x1) / 2
        M = T(cx, 0.4 if ang else 0, 0) @ RZ(ang)
        L = (x1 - x0) / math.cos(math.radians(ang))
        bevel_box(p, M, (0, 0, 1.6), (L, 2.0, 3.2), 'Interior_Wood', 0.12)
        for k in range(int(L / 1.6)):                                   # raised panel fronts
            x = -L / 2 + (k + 0.5) * L / int(L / 1.6)
            bevel_box(p, M, (x, -1.05, 1.6), (L / int(L / 1.6) - 0.4, 0.2, 2.2), 'Shop_Wood', 0.08)
        bevel_box(p, M, (0, -0.15, 3.35), (L + 0.4, 2.6, 0.3), 'Shop_Wood', 0.08)
        bevel_box(p, M, (0, -1.4, 3.35), (L + 0.4, 0.12, 0.36), 'Gold', 0.04)
        bevel_box(p, M, (0, -1.1, 0.2), (L, 0.3, 0.4), 'Gold', 0.04)
    paw(p, M_front(0, -1.25, 1.4), 1.8, 0.15, 'Gold')
    bevel_box(p, I4, (0, 2.6, 1.0), (14, 1.0, 2.0), 'Interior_Wood', 0.1)       # under-counter shelf (NPC side)


def crate(p, s=2.0):
    bevel_box(p, I4, (0, 0, s / 2), (s, s, s), 'Shop_Wood', 0.08)
    for sy in (-1, 1):
        for z in (0.15, s - 0.15):
            bevel_box(p, I4, (0, sy * (s / 2 + 0.02), z), (s + 0.04, 0.12, 0.3), 'Interior_Wood', 0.03)
        p.beam(Vector((-s / 2 + 0.2, sy * (s / 2 + 0.03), 0.2)), Vector((s / 2 - 0.2, sy * (s / 2 + 0.03), s - 0.2)),
               0.3, 0.1, 'Interior_Wood')


def chest(p):
    bevel_box(p, I4, (0, 0, 0.7), (2.8, 1.8, 1.4), 'Shop_Wood', 0.1)
    p.cyl((0, 0.1, 1.45), 0.92, 2.8, 'Shop_Wood', 10, axis='X')
    for x in (-1.0, 1.0):
        bevel_box(p, I4, (x, 0, 1.2), (0.3, 1.9, 2.0), 'Gold', 0.04)
    bevel_box(p, I4, (0, -0.95, 1.3), (0.6, 0.15, 0.7), 'Gold', 0.05)


def gift_box(p, mat='Gift_Pink', s=1.4):
    bevel_box(p, I4, (0, 0, s / 2), (s, s, s), mat, 0.06)
    p.box((0, 0, s / 2), (s + 0.04, 0.25, s + 0.04), 'Gold')
    p.box((0, 0, s / 2), (0.25, s + 0.04, s + 0.04), 'Gold')
    for a in (0.6, -0.6):
        p.ico((math.sin(a) * 0.3, 0, s + 0.2), 0.28, 'Gold', 1, (1.4, 0.6, 0.7))


def potion(p, mat):
    p.cyl((0, 0, 0.45), 0.45, 0.9, mat, 10, smooth=True)
    p.uvsphere((0, 0, 0.95), 0.5, mat, 10, 6)
    p.cyl((0, 0, 1.55), 0.18, 0.5, 'Glass', 8)
    p.cyl((0, 0, 1.9), 0.22, 0.25, 'Shop_Wood', 8)


def pet_item(p):
    """decorated pet egg on a gold stand"""
    p.cyl((0, 0, 0.15), 0.6, 0.3, 'Gold', 10)
    p.cyl((0, 0, 0.45), 0.25, 0.4, 'Gold', 8)
    p.uvsphere((0, 0, 1.25), 0.6, 'Egg_Shell', 12, 8, (1, 1, 1.3))
    for k in range(5):
        a = TAU * k / 5
        p.ico((math.cos(a) * 0.55, math.sin(a) * 0.55, 1.2), 0.14, 'Potion_Pink' if k % 2 else 'Potion_Blue', 1)


def pet_food(p):
    """pet food bag with a paw print"""
    p.box((0, 0, 0.9), (1.4, 0.8, 1.8), 'Gift_Blue')
    p.box((0, 0, 1.9), (1.2, 0.5, 0.25), 'Shop_Wood')
    paw(p, M_front(0, -0.41, 0.8), 0.9, 0.05, 'Sign_Emissive')


def barrel(p):
    p.cyl((0, 0, 1.2), 0.95, 2.4, 'Shop_Wood', 12, smooth=True)
    for z in (0.35, 1.2, 2.05):
        p.torus((0, 0, z), 1.0, 0.1, 'Lantern_Metal', 14, 4)
    p.cyl((0, 0, 2.42), 0.85, 0.06, 'Interior_Wood', 12)


def carpet(p, L=16.0, w=6.0):
    bevel_box(p, I4, (0, 0, 0.06), (w, L, 0.12), 'Carpet_Red', 0.03)
    for s in (-1, 1):
        bevel_box(p, I4, (s * (w / 2 - 0.4), 0, 0.13), (0.3, L - 0.6, 0.04), 'Gold', 0.01)


def planter(p, rnd, w=5.0):
    masonry(p, T(0, -w / 2), -w / 2, w / 2, 0, 2.2, rnd, 1.1, (1.6, 2.4), w - 0.4, backing=False)
    bevel_box(p, I4, (0, 0, 2.4), (w + 0.5, w + 0.5, 0.4), 'Castle_Trim', 0.1)
    p.box((0, 0, 2.5), (w - 0.6, w - 0.6, 0.2), 'Dirt')


def shop_sign(p, rnd, M=I4, small=False):
    """arched red board, gold frame, white SHOP + cart (cart part); text is a separate text object"""
    r = 7.5 if not small else 2.6
    zc = 0.0
    board = [(-r, -r * 0.7)] + [(r * math.cos(math.pi - math.pi * i / 16), zc + r * 0.55 * math.sin(math.pi * i / 16))
                                for i in range(17)] + [(r, -r * 0.7)]
    p.prism(board, 0.0, 0.8, 'Red_Wood', M @ FLIP)
    outer = [(-r - 0.6, -r * 0.7 - 0.6)] + [((r + 0.6) * math.cos(math.pi - math.pi * i / 16),
                                               zc + (r * 0.55 + 0.6) * math.sin(math.pi * i / 16)) for i in range(17)] + \
            [(r + 0.6, -r * 0.7 - 0.6)]
    frame_strip(p, M, outer, board, -0.35, 0.6, 'Gold')
    frame_strip(p, M, [(-r - 0.6, -r * 0.7 - 0.6), (r + 0.6, -r * 0.7 - 0.6)],
                [(-r, -r * 0.7), (r, -r * 0.7)], -0.35, 0.6, 'Gold')
    cart_icon(p, M @ T(0, -0.2, r * 0.2), r * 0.42)


def cart_icon(p, M, s):
    """glowing shopping-cart icon drawn on the local XZ plane (faces -y)"""
    for a, b in (((-0.9, 0.55), (-0.62, -0.15)), ((-0.62, -0.15), (0.7, -0.15)), ((0.7, -0.15), (0.92, 0.45)),
                 ((0.92, 0.45), (-0.78, 0.45)), ((-0.9, 0.55), (-1.2, 0.68)), ((-0.62, -0.15), (-0.7, -0.38)),
                 ((-0.7, -0.38), (0.75, -0.38))):
        p.beam(M @ Vector((a[0] * s, -0.15, a[1] * s)), M @ Vector((b[0] * s, -0.15, b[1] * s)),
               0.2 * s, 0.25, 'Cart_Glow')
    for x in (-0.45, 0.55):
        p.cyl(M @ Vector((x * s, -0.15, -0.6 * s)), 0.14 * s, 0.3, 'Cart_Glow', 10, axis='Y')
    for k in range(3):                                                      # basket grid
        x = -0.35 + k * 0.38
        p.beam(M @ Vector((x * s, -0.15, 0.42 * s)), M @ Vector(((x + 0.03) * s, -0.15, -0.12 * s)), 0.1 * s, 0.2,
               'Cart_Glow')


def _lib(name, sub, builder, *a, **kw):
    p = Part('ASSET_' + name, sub)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def build_shop_kit(parent):
    coll(KIT, parent)
    R = random.Random
    _lib('Shop_Stone_Block', KIT, lambda p: bevel_box(p, I4, (0, 0, 1.25), (4.0, 1.6, 2.5), 'Castle_Stone', 0.18))
    _lib('Shop_Stone_Wall', KIT, lambda p: masonry(p, I4, -6, 6, 0, 10, R(1), 2.5, (3, 5)))
    def corner(p):
        masonry(p, I4, 0, 6, 0, 10, R(2), 2.5, (3, 5))
        masonry(p, RZ(-90), -6, 0, 0, 10, R(3), 2.5, (3, 5))
        quoins(p, I4, 0, 10, R(4), 3.6, 2.0, 2.5, side=1)
    _lib('Shop_Stone_Corner', KIT, corner)
    _lib('Shop_Stone_Pillar', KIT, lambda p: pillar(p, I4, 4.6, 0, 19, R(5), cap=None,
                                                     mats=('Shop_Stone_Dark',), band=0.5))
    _lib('Shop_Stone_Arch', KIT, lambda p: voussoirs(p, I4, round_arch(9.4, 4, 12), round_arch(6, 4, 12), -0.4, 1.6, R(6),
                                                     2.2))
    def red_panel(p):
        for k in range(4):
            bevel_box(p, I4, (-3 + k * 2, 0, 5), (1.9, 0.6, 10), 'Red_Wood', 0.08)
        frame_strip(p, I4, [(-4.3, 0), (-4.3, 10.3), (4.3, 10.3), (4.3, 0)], [(-4, 0), (-4, 10), (4, 10), (4, 0)],
                    -0.45, 0.2, 'Gold')
    _lib('Shop_Red_Wall_Panel', KIT, red_panel)
    _lib('Shop_Roof_Piece', KIT, lambda p: roof_slope(p, I4, 0, 8, 0, 4.0, -4, 4, 0.5))
    _lib('Shop_Gold_Trim', KIT, lambda p: bevel_box(p, I4, (0, 0, 0.2), (8, 0.35, 0.4), 'Gold', 0.06))
    _lib('Shop_Sign', KIT, lambda p: shop_sign(p, R(7), T(0, 0, 3.0), small=True))
    _lib('Shop_Banner', KIT, red_banner)
    _lib('Shop_Lantern', KIT, shop_lantern)
    _lib('Shop_Lantern_Wall', KIT, shop_lantern_wall)
    _lib('Shop_Counter', KIT, counter, R(8))
    _lib('Shop_Shelf', KIT, shelf, R(9))
    _lib('Shop_Crate', KIT, crate)
    _lib('Shop_Chest', KIT, chest)
    _lib('Shop_Gift_Box', KIT, gift_box, 'Gift_Pink')
    _lib('Shop_Gift_Box_Blue', KIT, gift_box, 'Gift_Blue', 1.1)
    for c in ('Pink', 'Blue', 'Green', 'Purple'):
        _lib(f'Shop_Potion_{c}', KIT, potion, f'Potion_{c}')
    _lib('Shop_Pet_Item', KIT, pet_item)
    _lib('Shop_Pet_Food', KIT, pet_food)
    _lib('Shop_Barrel', KIT, barrel)
    _lib('Shop_Carpet', KIT, carpet)
    _lib('Shop_Planter', KIT, planter, R(10))


def roof_slope(p, M, x_eave, x_ridge, z_eave, z_ridge, y0, y1, t, mat='Shop_Roof', segs=3, sag=0.35,
               courses=True, course_mat='Shop_Roof_Dark'):
    """slightly concave (fantasy) roof slope between an eave line and a ridge line, extruded along y,
    with raised tile courses parallel to the eave"""
    pts = []
    for i in range(segs + 1):
        f = i / segs
        x = x_eave + (x_ridge - x_eave) * f
        z = z_eave + (z_ridge - z_eave) * f - sag * math.sin(math.pi * f)
        pts.append((x, z))
    for (xa, za), (xb, zb) in zip(pts, pts[1:]):
        q = [(xa, za), (xb, zb), (xb, zb + t), (xa, za + t)]
        p.hexa([M @ Vector((x, y0, z)) for x, z in q] + [M @ Vector((x, y1, z)) for x, z in q], mat)
    if courses:
        L = math.hypot(x_ridge - x_eave, z_ridge - z_eave)
        n = max(2, int(L / 1.6))
        for k in range(1, n):
            f = k / n
            x = x_eave + (x_ridge - x_eave) * f
            z = z_eave + (z_ridge - z_eave) * f - sag * math.sin(math.pi * f) + t
            p.hexa([M @ Vector((x - 0.35, y0, z)), M @ Vector((x + 0.35, y0, z + 0.0)), M @ Vector((x + 0.35, y0, z + 0.22)),
                    M @ Vector((x - 0.35, y0, z + 0.22)),
                    M @ Vector((x - 0.35, y1, z)), M @ Vector((x + 0.35, y1, z)), M @ Vector((x + 0.35, y1, z + 0.22)),
                    M @ Vector((x - 0.35, y1, z + 0.22))], course_mat)
    return pts


# ---------------------------------------------------------------- build -----
def subcolls():
    for c, par in (('BUILDING', ROOT), ('Walls', 'BUILDING'), ('Pillars', 'BUILDING'), ('Arches', 'BUILDING'),
                   ('Trim', 'BUILDING'), ('Roof', 'BUILDING'), ('SIGNAGE', ROOT), ('Main_Shop_Sign', 'SIGNAGE'),
                   ('Small_Shop_Signs', 'SIGNAGE'), ('BANNERS', ROOT), ('INTERIOR', ROOT), ('Counter', 'INTERIOR'),
                   ('Shelves', 'INTERIOR'), ('Carpet', 'INTERIOR'), ('Decorations', 'INTERIOR'), ('SHOP_ITEMS', ROOT),
                   ('LIGHTING (shop)', ROOT), ('LANDSCAPING', ROOT)):
        coll(c, par)


def build_shop(parent_coll, loc=(0, 0, 0), rot_z=0.0, cam_prefix=None):
    """build the whole shop under an Empty 'Shop_Root' (move/rotate the Empty to place it)"""
    coll(ROOT, parent_coll)
    subcolls()
    root = empty('Shop_Root', ROOT, loc, rot_z, 8)
    rnd = random.Random(4242)
    F = 1.0                                                      # floor height (top of the plinth)

    def fin(p):
        return p.finish(parent=root)

    # ---------------- floor / plinth --------------------------------------------------------------
    p = Part('Shop_Floor', 'Walls')
    bevel_box(p, I4, (0, 2, F / 2), (50, 34, F), 'Castle_Trim', 0.2)
    for i in range(2):                                           # front steps
        bevel_box(p, I4, (0, -15.2 - i * 1.4, (F - i * 0.5) / 2), (24 - i * 2, 1.4, F - i * 0.5), 'Castle_Stone_Light', 0.12)
    for k in range(16):                                          # wood planks inside the hall
        x = -14.6 + (k + 0.5) * 29.2 / 16
        bevel_box(p, I4, (x, 3.4, F + 0.12), (29.2 / 16 - 0.1, 25.2, 0.24), ('Interior_Wood', 'Shop_Wood')[k % 2], 0.04)
    for i in range(6):                                           # stone flags across the threshold
        bevel_box(p, I4, (-10.5 + (i + 0.5) * 21 / 6, -12.6, F + 0.1), (21 / 6 - 0.12, 4.6, 0.2), 'Castle_Stone_Light', 0.06)
    fin(p)

    # ---------------- walls (masonry over a dark core) ---------------------------------------------
    w = Part('Shop_Walls_Hall', 'Walls')
    # back wall with an arched back door
    door = lifted(round_arch(5.2, 6.5, 10), 0, F)
    w.box((0, 17.5, (F + 22) / 2), (34, 2.6, 22 - F), 'Castle_Seam')
    masonry(w, T(0, 19.1) @ RZ(180), -17, 17, F, 22, rnd, 2.4, (3, 5.5), 1.6,
            skip=lambda x, z, ww, h: inside(door, -x, z), backing=False)
    voussoirs(w, T(0, 19.1) @ RZ(180), lifted(round_arch(7.6, 6.5, 10), 0, F), door, -0.6, 1.2, rnd, 1.8)
    for k in range(4):                                           # plank door
        bevel_box(w, I4, (-1.95 + k * 1.3, 18.9, F + 3.6), (1.24, 0.3, 7.2), 'Shop_Wood', 0.06)
    w.cyl((1.4, 19.3, F + 3.4), 0.25, 0.4, 'Gold', 8, axis='Y')
    # hall side walls (the part above the wing roofs is visible outside)
    for s in (-1, 1):
        w.box((s * 16, 3.5, (F + 22) / 2), (2.2, 26, 22 - F), 'Castle_Seam')
        xr = (-9.5, 16.5) if s > 0 else (-16.5, 9.5)          # RZ(+-90): local x runs along +-y
        masonry(w, T(s * 17.1, 0) @ RZ(s * 90), xr[0], xr[1], 12.5, 22, rnd, 2.4, (3, 5.5), 1.6, backing=False)
        quoins(w, T(s * 17.1, 19.1) @ RZ(180), F, 22, rnd, 3.4, 2.0, 2.4, side=s,
               mat='Castle_Trim')
    # interior wood panelling + red back panel
    for k in range(17):
        x = -14.4 + (k + 0.5) * 28.8 / 17
        if abs(x) < 3.0:
            bevel_box(w, I4, (x, 16.05, F + 15.8), (28.8 / 17 - 0.08, 0.3, 10.4), 'Interior_Wood', 0.05)
            continue
        bevel_box(w, I4, (x, 16.05, F + 10.5), (28.8 / 17 - 0.08, 0.3, 21 - F - 0.2), 'Interior_Wood', 0.05)
    for s in (-1, 1):
        for k in range(14):
            y = -9.0 + (k + 0.5) * 25.0 / 14
            bevel_box(w, I4, (s * 14.85, y, F + 10.5), (0.3, 25.0 / 14 - 0.08, 21 - F - 0.2), 'Interior_Wood', 0.05)
        bevel_box(w, I4, (s * 14.7, 3.5, F + 0.5), (0.4, 25, 1.0), 'Shop_Wood', 0.06)          # skirting
        bevel_box(w, I4, (s * 14.7, 3.5, 20.6), (0.5, 25, 0.8), 'Shop_Wood', 0.06)            # cornice
    fin(w)

    # ---------------- wings --------------------------------------------------------------------------
    wg = Part('Shop_Walls_Wings', 'Walls')
    WT = 13.0
    for s in (-1, 1):
        x0, x1 = (17.2, 25.0) if s > 0 else (-25.0, -17.2)
        wg.box(((x0 + x1) / 2, 3, (F + WT) / 2), (x1 - x0, 22, WT - F), 'Castle_Seam')
        # outer side (masonry) + back (masonry)
        xr = (-8, 14) if s > 0 else (-14, 8)
        masonry(wg, T(s * 25.1, 0) @ RZ(s * 90), xr[0], xr[1], F, WT, rnd, 2.4, (3, 5.5), 1.6, backing=False)
        masonry(wg, T(0, 14.1) @ RZ(180), *((-x1, -x0)), F, WT, rnd, 2.4, (3, 5.5), 1.6, backing=False)
        quoins(wg, T(s * 25.1, -8.1), F, WT, rnd, 3.4, 2.0, 2.4, side=-s, mat='Castle_Trim')
        quoins(wg, T(s * 25.1, 14.1) @ RZ(180), F, WT, rnd, 3.4, 2.0, 2.4, side=s, mat='Castle_Trim')
        # front: red plank panel between stone frames, gold frame
        cx = s * 19.0                                       # red plank panel between the hall pillar and the corner pillar
        for k in range(3):
            bevel_box(wg, I4, (cx - 2.0 + k * 2.0, -8.0, F + 5.4), (1.9, 0.6, 9.8), 'Red_Wood', 0.08)
        frame_strip(wg, T(cx, -8.1), [(-3.3, F), (-3.3, F + 10.6), (3.3, F + 10.6), (3.3, F)],
                    [(-3.0, F), (-3.0, F + 10.3), (3.0, F + 10.3), (3.0, F)], -0.55, 0.1, 'Gold')
        trim_run(wg, T(0, -8.4), x0, x1, WT - 1.6, h=1.6, out=1.0)
        # corner pillar with a lantern on top
        pillar(wg, T(s * 24.0, -8.6), 3.4, 0, WT + 2.5, rnd, cap=None, band=0.45, panel=False)
    fin(wg)
    for s in (-1, 1):
        inst('Shop_Lantern', f'Shop_WingLantern_{"LR"[s > 0]}', 'Trim', (s * 24.0, -8.6, WT + 2.3), 0, 1.15, root)
        for k, x in enumerate((s * 17.6, s * 20.4)):
            inst('Shop_Banner', f'Shop_WingBanner_{"LR"[s > 0]}{k}', 'BANNERS', (x, -8.75, F + 10.2), 0, 1.0, root)

    # ---------------- entrance pillars, lintel, stone arch -------------------------------------------
    pl = Part('Shop_Pillars', 'Pillars')
    for s in (-1, 1):
        pillar(pl, T(s * 13.4, -11.0), 4.6, F, 19.0, rnd, cap=None, band=0.5, mats=('Shop_Stone_Dark',))
        bevel_box(pl, T(s * 13.4, -11.0), (0, -2.45, F + 12.5), (3.6, 0.3, 0.45), 'Gold', 0.05)
        bevel_box(pl, T(s * 13.4, -11.0), (0, 0, F + 21.4), (6.4, 6.4, 1.2), 'Castle_Trim', 0.2)
    fin(pl)
    ar = Part('Shop_Entrance_Arch', 'Arches')
    zs = F + 13.0                                                     # spring line of the shallow (segmental) arch
    seg_i = [(x, zs + 2.0 * (1 - (x / 10.8) ** 2)) for x in [-10.8 + 21.6 * i / 12 for i in range(13)]]
    seg_o = [(x, zs + 2.2 + 2.0 * (1 - (x / 11.6) ** 2)) for x in [-11.6 + 23.2 * i / 12 for i in range(13)]]
    voussoirs(ar, T(0, -11.0), seg_o, seg_i, -1.2, 1.4, rnd, 2.2, mat=None)
    # red timber spandrel between the arch and the lintel
    ar.prism([(-11.6, zs + 2.2)] + seg_o[1:-1] + [(11.6, zs + 2.2), (11.6, F + 17.8), (-11.6, F + 17.8)],
             -11.4, -10.2, 'Red_Wood', FLIP)
    # red wooden lintel beam with gold trim above the arch
    bevel_box(ar, I4, (0, -11.6, F + 19.0), (32.0, 2.6, 2.6), 'Red_Wood', 0.15)
    for z in (F + 17.8, F + 20.2):
        bevel_box(ar, I4, (0, -12.95, z), (32.0, 0.2, 0.3), 'Gold', 0.04)
    for x in range(-14, 15, 4):                                       # gold studs
        ar.ico((x, -13.0, F + 19.0), 0.28, 'Gold', 1)
    fin(ar)

    # ---------------- front gable with the raised arched sign section --------------------------------
    gb = Part('Shop_Front_Gable', 'Walls')
    yF = -10.6
    ze, zr = F + 20.3, F + 31.0                                       # roof eave / ridge heights
    tri = [(-17.5, ze), (17.5, ze), (0, zr)]
    gb.prism(tri, yF, yF + 1.0, 'Red_Wood', FLIP)
    for k in range(11):                                               # vertical planks on the gable
        x = -15 + k * 3
        top = ze + (zr - ze) * (1 - abs(x) / 17.5)
        bevel_box(gb, I4, (x, yF - 0.25, (ze + top) / 2), (0.3, 0.3, max(0.2, top - ze - 0.4)), 'Red_Wood_Dark', 0.04)
    # raised arched section behind the sign
    cz, rr = F + 27.0, 10.0
    arch_top = [(-rr, ze)] + [(rr * math.cos(math.pi - math.pi * i / 16), cz + rr * math.sin(math.pi * i / 16) * 0.75)
                              for i in range(17)] + [(rr, ze)]
    gb.prism(arch_top, yF - 1.6, yF + 1.2, 'Red_Wood', FLIP)
    frame_strip(gb, I4, [(x * 1.06, ze + (z - ze) * 1.05) for x, z in arch_top[:-1]][:],
                [(x, z) for x, z in arch_top[:-1]], yF - 1.9, yF - 1.4, 'Gold')
    # curved red cap roof following the arch
    for i in range(16):
        a0, a1 = math.pi - math.pi * i / 16, math.pi - math.pi * (i + 1) / 16
        pts = []
        for a in (a0, a1):
            for rad in (rr + 0.2, rr + 1.8):
                pts.append((rad * math.cos(a), cz + rad * math.sin(a) * 0.75))
        q = [pts[0], pts[2], pts[3], pts[1]]
        gb.hexa([Vector((x, yF - 2.4, z)) for x, z in q] + [Vector((x, yF + 4.0, z)) for x, z in q], 'Shop_Roof')
        gb.hexa([Vector((x, yF - 2.6, z)) for x, z in (pts[1], pts[3], (pts[3][0], pts[3][1] - 0.35), (pts[1][0], pts[1][1] - 0.35))] +
                [Vector((x, yF - 2.3, z)) for x, z in (pts[1], pts[3], (pts[3][0], pts[3][1] - 0.35), (pts[1][0], pts[1][1] - 0.35))],
                'Gold')
    # gold scroll ornaments and crown finials
    for s in (-1, 1):
        gb.torus((s * 10.6, yF - 2.0, ze + 4.5), 1.3, 0.3, 'Gold', 14, 6, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
        gb.torus((s * 10.9, yF - 2.0, ze + 2.2), 0.8, 0.25, 'Gold', 12, 6, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
        crown = Vector((s * 17.8, yF - 0.8, ze + 1.0))
        gb.cyl(crown + Vector((0, 0, 0.5)), 1.1, 1.0, 'Gold', 8)
        for k in range(5):
            a = TAU * k / 5
            gb.cone(crown + Vector((math.cos(a) * 0.85, math.sin(a) * 0.85, 1.0)), 0.3, 1.0, 'Gold', 4)
    gb.ico((0, yF - 1.0, cz + rr * 0.75 + 2.4), 0.9, 'Gold', 1)
    gb.cone((0, yF - 1.0, cz + rr * 0.75 + 1.6), 0.6, 1.0, 'Gold', 6)
    fin(gb)

    # ---------------- roofs ----------------------------------------------------------------------------
    rf = Part('Shop_Roof_Main', 'Roof')
    for s in (-1, 1):
        roof_slope(rf, RZ(0) if s > 0 else Matrix.Scale(-1, 4, Vector((1, 0, 0))), 18.6, 0.0, ze - 0.6, zr, yF - 0.6,
                   20.0, 0.8, sag=0.6)
    bevel_box(rf, I4, (0, 4.7, zr + 0.6), (1.6, 31.0, 1.2), 'Shop_Roof_Dark', 0.2)                 # ridge cap
    # back gable: red planks closing the roof triangle above the back wall
    rf.prism([(-17.0, 21.6), (17.0, 21.6), (0, zr - 0.2)], 18.0, 19.4, 'Red_Wood', FLIP)
    for k in range(9):
        x = -12 + k * 3
        top = 21.6 + (zr - 0.2 - 21.6) * (1 - abs(x) / 17.0)
        bevel_box(rf, I4, (x, 19.55, (21.8 + top) / 2), (0.3, 0.3, max(0.3, top - 22.0)), 'Red_Wood_Dark', 0.04)
    rf.cyl((0, 19.6, 25.5), 1.6, 0.4, 'Interior_Wood', 12, axis='Y')                             # round vent
    rf.torus((0, 19.85, 25.5), 1.6, 0.2, 'Gold', 16, 4, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
    for y in (yF - 0.8, 20.2):
        rf.ico((0, y, zr + 1.6), 0.8, 'Gold', 1)
    for s in (-1, 1):                                                     # gold fascia on eaves + rakes
        bevel_box(rf, I4, (s * 18.7, 4.7, ze - 0.7), (0.5, 31.2, 0.6), 'Gold', 0.06)
        ang = math.atan2(zr - ze, 18.6)
        L = math.hypot(18.6, zr - ze)
        Mr = T(s * 9.3, yF - 0.7, (ze + zr) / 2 - 0.1) @ Matrix.Rotation(s * ang, 4, 'Y')
        bevel_box(rf, Mr, (0, 0, 0), (L + 0.6, 0.5, 0.6), 'Gold', 0.06)
    # wing lean-to roofs
    for s in (-1, 1):
        Mw = I4 if s > 0 else Matrix.Scale(-1, 4, Vector((1, 0, 0)))
        roof_slope(rf, Mw, 27.0, 17.2, WT + 0.3, ze - 1.4, -10.2, 15.6, 0.7, sag=0.4)
        bevel_box(rf, I4, (s * 27.1, 2.7, WT + 0.25), (0.5, 25.8, 0.55), 'Gold', 0.06)
        ang = math.atan2(ze - 1.4 - WT, 9.8)
        Mr = T(s * 22.1, -10.3, (WT + ze - 1.4) / 2 + 0.25) @ Matrix.Rotation(s * ang, 4, 'Y')
        bevel_box(rf, Mr, (0, 0, 0), (math.hypot(9.8, ze - 1.4 - WT) + 0.4, 0.5, 0.55), 'Gold', 0.06)
    fin(rf)

    # ---------------- main sign + small signs ---------------------------------------------------------
    sg = Part('Shop_Main_Sign', 'Main_Shop_Sign')
    shop_sign(sg, rnd, T(0, yF - 2.0, cz - 1.0))
    fin(sg)
    text_mesh('Shop_Main_Sign_Text', 'SHOP', 'Main_Shop_Sign', 4.4, 0.7, 'Sign_Emissive',
              (0, yF - 2.9, cz - 4.7), 0, root)
    # free-standing sign on a post at the front-left (reference)
    ss = Part('Shop_Small_Sign_Front', 'Small_Shop_Signs')
    Ms = T(-21.5, -19.5) @ RZ(18)
    bevel_box(ss, Ms, (0, 0, 0.3), (2.4, 2.4, 0.6), 'Castle_Stone_Light', 0.12)
    for x in (-2.0, 2.0):
        bevel_box(ss, Ms, (x, 0, 2.6), (0.5, 0.5, 5.2), 'Shop_Wood', 0.06)
    bevel_box(ss, Ms, (0, 0, 5.4), (5.8, 0.6, 5.2), 'Red_Wood', 0.15)
    frame_strip(ss, Ms, [(-3.2, 2.6), (-3.2, 8.2), (3.2, 8.2), (3.2, 2.6), (-3.2, 2.6)],
                [(-2.9, 2.9), (-2.9, 7.9), (2.9, 7.9), (2.9, 2.9), (-2.9, 2.9)], -0.5, 0.35, 'Gold')
    cart_icon(ss, Ms @ T(0, -0.3, 6.6), 1.2)
    fin(ss)
    text_mesh('Shop_Small_Sign_Front_Text', 'SHOP', 'Small_Shop_Signs', 1.25, 0.2, 'Sign_Emissive',
                  Ms @ Vector((0, -0.5, 4.0)), math.radians(18), root)

    # ---------------- banners on the entrance pillars (inside faces) + interior ------------------------
    for s in (-1, 1):                                                 # lanterns on the pillar fronts
        inst('Shop_Lantern_Wall', f'Shop_EntranceLantern_{"LR"[s > 0]}', 'Trim', (s * 13.4, -13.35, F + 14.5), 0, 1.0,
             root)
    for s in (-1, 1):
        for k, y in enumerate((-4.0, 9.0)):
            inst('Shop_Banner', f'Shop_InteriorBanner_{"LR"[s > 0]}{k}', 'BANNERS', (s * 14.6, y, F + 17.5),
                 math.radians(-90 if s > 0 else 90), 1.1, root)

    # back-wall red panel with glowing cart
    bp = Part('Shop_BackPanel', 'Decorations')
    bevel_box(bp, I4, (0, 15.75, F + 11.5), (12, 0.3, 9), 'Red_Fabric', 0.06)
    frame_strip(bp, T(0, 15.55), [(-6.4, F + 6.6), (-6.4, F + 16.4), (6.4, F + 16.4), (6.4, F + 6.6), (-6.4, F + 6.6)],
                [(-6, F + 7), (-6, F + 16), (6, F + 16), (6, F + 7), (-6, F + 7)], -0.4, 0.2, 'Gold')
    cart_icon(bp, T(0, 15.4, F + 11.5), 3.4)
    # ceiling, beams, hanging lanterns
    bevel_box(bp, I4, (0, 3.5, ze - 0.4), (29.6, 25.4, 0.4), 'Interior_Wood', 0.05)
    for y in range(-8, 17, 5):
        bevel_box(bp, I4, (0, y, ze - 1.2), (29.6, 1.0, 1.2), 'Shop_Wood', 0.12)
    for x in (-6.0, 6.0):
        bp.box((x, 2.0, ze - 3.2), (0.15, 0.15, 3.0), 'Lantern_Metal')
        shop_lantern(bp, T(x, 2.0, ze - 8.6))
    fin(bp)

    # counter, shelves, carpet
    inst('Shop_Counter', 'Shop_Counter', 'Counter', (0, 8.0, F + 0.24), 0, 1.0, root)
    # shelf fronts (local -y) face the room: back wall 0 deg, left wall +90, right wall -90
    shelves = [((-10.5, 14.9, 0), 'Shop_Shelf'), ((10.5, 14.9, 0), 'Shop_Shelf'),
               ((-13.9, 3.0, 90), 'Shop_Shelf'), ((13.9, 3.0, -90), 'Shop_Shelf'),
               ((-13.9, -4.5, 90), 'Shop_Shelf'), ((13.9, -4.5, -90), 'Shop_Shelf')]
    for i, ((x, y, rz), nm) in enumerate(shelves):
        inst(nm, f'Shop_Shelf_{i}', 'Shelves', (x, y, F + 0.24), math.radians(rz), 1.0, root)
    items = ('Shop_Potion_Pink', 'Shop_Potion_Blue', 'Shop_Gift_Box', 'Shop_Potion_Green', 'Shop_Pet_Item',
             'Shop_Potion_Purple', 'Shop_Gift_Box_Blue', 'Crystals_B', 'Shop_Pet_Food')
    n = 0
    for i, ((x, y, rz), _) in enumerate(shelves):
        R = Matrix.Rotation(math.radians(rz), 3, 'Z')
        for lvl in SHELF_LEVELS:
            for k in range(3):
                off = R @ Vector((-1.8 + k * 1.8, 0.0, 0))
                nm = items[(i * 3 + k + int(lvl)) % len(items)]
                sc = 0.45 if nm.startswith('Crystals') else (0.7 if 'Food' in nm else 0.85)
                inst(nm, f'Shop_Item_{n:03d}', 'SHOP_ITEMS', (x + off.x, y + off.y, F + 0.24 + lvl + 0.15),
                     rnd.uniform(-0.3, 0.3), sc, root)
                n += 1
    for k, (x, nm) in enumerate(((-4.5, 'Shop_Gift_Box'), (-2.2, 'Shop_Potion_Blue'), (0.0, 'Shop_Pet_Item'),
                                 (2.2, 'Shop_Potion_Pink'), (4.5, 'Shop_Gift_Box_Blue'))):
        inst(nm, f'Shop_CounterItem_{k}', 'SHOP_ITEMS', (x, 7.9, F + 3.75), rnd.uniform(-0.4, 0.4), 0.9, root)
    for k, (x, y, nm, sc) in enumerate(((-11.0, -8.0, 'Shop_Crate', 1.0), (-11.0, -8.0, 'Shop_Gift_Box', 0.9),
                                        (11.0, -8.0, 'Shop_Chest', 1.0), (10.6, 11.0, 'Shop_Crate', 0.9),
                                        (-11.6, 10.0, 'Shop_Barrel', 1.0))):
        z = F + 0.24 + (2.0 if k == 1 else 0)
        inst(nm, f'Shop_Floor_{nm}_{k}', 'SHOP_ITEMS', (x, y, z), rnd.uniform(-0.3, 0.3), sc, root)
    cp = Part('Shop_Carpet_Runner', 'Carpet')
    carpet(cp, 18.0, 6.0)
    ob = fin(cp)
    ob.location = (0, -6.0, F + 0.24)
    rug = Part('Shop_Carpet_Rug', 'Carpet')
    rug.cyl((0, 0, 0.07), 5.6, 0.14, 'Carpet_Red', 32)
    rug.torus((0, 0, 0.15), 5.0, 0.18, 'Gold', 40, 4)
    paw(rug, T(0, 0.3, 0.14), 5.6, 0.04, 'Gold')
    ob = fin(rug)
    ob.location = (0, 0.5, F + 0.27)

    # ---------------- back yard ---------------------------------------------------------------------
    for k, (x, y, nm, rz) in enumerate(((-6.0, 21.0, 'Shop_Barrel', 0), (-4.0, 21.6, 'Shop_Barrel', 0.5),
                                        (5.0, 21.2, 'Shop_Crate', 0.3), (7.4, 21.0, 'Shop_Crate', -0.2),
                                        (6.2, 21.0, 'Shop_Crate', 0.1))):
        inst(nm, f'Shop_Back_{nm}_{k}', 'SHOP_ITEMS', (x, y, F + (2.0 if k == 4 else 0)), rz,
             0.8 if k == 4 else 1.0, root)
    from foliage import vine
    vv = Part('Shop_Back_Vines', 'LANDSCAPING')
    for x in (-14.0, -9.5, 9.0, 13.5, -22.0, 22.5):
        vine(vv, (x, 19.5 if abs(x) < 17 else 14.5, 21.0 if abs(x) < 17 else 12.5), rnd.uniform(6, 12), rnd, 1.1)
    fin(vv)

    # ---------------- landscaping -----------------------------------------------------------------------
    for k, (x, y, nm, sc, rz) in enumerate((
            (-16.5, -18.0, 'Shop_Planter', 1.0, 0), (16.5, -18.0, 'Shop_Planter', 1.0, 0),
            (-16.5, -18.0, 'Topiary_Cone', 0.9, 0), (16.5, -18.0, 'Topiary_Cone', 0.9, 0),
            (-27.5, -11.0, 'Bush_02', 1.1, 0.4), (27.5, -11.0, 'Bush_01', 1.2, 0.2),
            (-28.0, 4.0, 'Bush_03', 1.0, 0.0), (28.5, 6.0, 'Ground_Plant_01', 1.2, 0.0),
            (-29.0, 17.0, 'Tree_Medium_High', 0.9, 0.3), (29.0, 17.5, 'Tree_Small', 1.0, 1.0),
            (-8.0, -19.5, 'Ground_Plant_02', 1.0, 0.0), (8.0, -19.5, 'Ground_Plant_02', 1.0, 1.0),
            (26.0, -17.5, 'Rock_A', 1.2, 0.5), (-25.0, 12.0, 'Rock_B', 1.4, 0.0))):
        z = 2.7 if nm == 'Topiary_Cone' else 0.0
        inst(nm, f'Shop_Land_{nm}_{k}', 'LANDSCAPING', (x, y, z), rz, sc, root)

    # ---------------- lights ---------------------------------------------------------------------------
    for k, (x, y, z, e) in enumerate(((0, 2, 14, 9000), (-7, 10, 9, 3500), (7, 10, 9, 3500), (0, -10, 10, 3000),
                                      (-16, -15.5, 14, 1800), (16, -15.5, 14, 1800))):
        L = bpy.data.lights.new(f'Shop_Light_{k}', 'POINT')
        L.color = (1.0, 0.70, 0.38); L.energy = e; L.shadow_soft_size = 1.5
        o = bpy.data.objects.new(L.name, L)
        o.location = (x, y, z); o.parent = root
        coll('LIGHTING (shop)').objects.link(o)
    return root


def build_shop_cameras(root_loc=(0, 0, 0), rot_z=0.0, coll_name='CAMERAS', prefix='CAM_Shop', only=None):
    """front (reference perspective), interior, side, rear, player-height cameras relative to the shop"""
    M = Matrix.Translation(root_loc) @ Matrix.Rotation(rot_z, 4, 'Z')
    out = {}
    for name, loc, tgt, lens in (('Front', (-7, -74, 15), (0, 0, 16.5), 28), ('Interior', (-5, -11, 6.5), (2, 14, 7.5), 20),
                                 ('Side', (-58, -42, 26), (0, 2, 12), 30), ('Rear', (30, 50, 26), (0, 8, 11), 30),
                                 ('Player', (3, -36, 5.2), (0, 6, 9), 24)):
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
