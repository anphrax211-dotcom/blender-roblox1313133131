"""HUB: circular plaza, central paw fountain/spawn platform, spawn pad, the six facilities
(Pets, Shop, Eggs, Trading, Upgrades, Leaderboards) and the landscaping between them.

Layout follows the reference top-down hub plan (tower entrance north / +Y, spawn south):

                 TOWER ENTRANCE (90 deg)
        PETS (135)               SHOP (45)
   TRADING (180)     FOUNTAIN       EGGS (0)
        LEADERBOARDS (225)       UPGRADES (315)
                    SPAWN (270)

Every facility is built in local space (front = -Y, centred on its own Empty) and the Empty
is placed on the ring facing the fountain, so a building can be moved by moving its Empty.
"""
import math, random
from mathutils import Vector, Matrix, Euler
from common import (Part, coll, empty, inst, paw, M_front, text_mesh, pointed_arch, round_arch,
                    ellipse, canopy, avatar, TAU)
from foliage import tree_in_planter

R_PLAZA = 128.0          # paved plaza radius
R_ISLAND = 172.0         # grassy island rim
R_BUILD = 96.0           # facility ring
R_CORE = 34.0            # central spawn platform
SLOT = {'Eggs': 0, 'Shop': 45, 'Entrance': 90, 'Pets': 135, 'Trading': 180,
        'Leaderboards': 225, 'Spawn': 270, 'Upgrades': 315}
SPAWN_POS = (0.0, -58.0, 0.0)
FAC_SCALE = 1.2         # facilities are authored at 1:1 studs and shown 20% larger (simulator style)
HUB = 'HUB'


def polar(r, deg, z=0.0):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a), z)


# ---------------------------------------------------------------- plaza -----
def build_plaza():
    c = 'Plaza'
    coll(c, HUB)
    p = Part('Plaza_Floor', c)
    p.cyl((0, 0, -2.0), R_PLAZA, 4.0, 'Plaza_Tile', 96)
    p.ring_sector(R_PLAZA - 1.5, R_PLAZA + 1.0, 0, TAU, 0, 0.9, 'Stone_Trim', 96)           # kerb
    p.ring_sector(R_PLAZA, R_ISLAND, 0, TAU, -3.0, 0.3, 'Grass', 96)                         # lawn rim
    p.ring_sector(R_CORE + 1.5, R_CORE + 3.0, 0, TAU, 0, 0.08, 'Blue_Inlay', 64)
    p.ring_sector(R_CORE + 4.0, R_CORE + 4.8, 0, TAU, 0, 0.08, 'Gold', 64)
    p.ring_sector(78.0, 79.5, 0, TAU, 0, 0.06, 'Stone_Trim', 96)
    p.ring_sector(118.0, 119.5, 0, TAU, 0, 0.06, 'Stone_Trim', 96)
    p.finish()

    # radial paths (8 spokes) --------------------------------------------------------------------
    p = Part('Plaza_Paths', c)
    for name, deg in SLOT.items():
        a = math.radians(deg)
        r0, r1 = R_CORE + 5, R_PLAZA - 2
        w = 22 if name in ('Entrance', 'Spawn') else 14
        mid = Vector(polar((r0 + r1) / 2, deg, 0.05))
        p.box(mid, (r1 - r0, w, 0.1), 'Plaza_Path', Matrix.Rotation(a, 3, 'Z'))
        for s in (-1, 1):                                   # border lines
            off = Vector((-math.sin(a), math.cos(a), 0)) * s * (w / 2 + 0.4)
            p.box(mid + off + Vector((0, 0, 0.02)), (r1 - r0, 0.8, 0.12), 'Stone_Trim', Matrix.Rotation(a, 3, 'Z'))
    p.finish()

    # inner garden ring: 8 raised planter wedges between the spokes ------------------------------
    p = Part('Plaza_Gardens_Inner', c, 0.2)
    g = Part('Plaza_Gardens_Inner_Grass', c)
    rnd = random.Random(3)
    for k in range(8):
        deg0, deg1 = k * 45, (k + 1) * 45
        r0, r1 = 50.0, 74.0
        gap = math.degrees(9.0 / r0)
        a0, a1 = math.radians(deg0 + gap), math.radians(deg1 - gap)
        p.ring_sector(r0, r1, a0, a1, 0, 1.6, 'Hub_Stone', 12)
        g.ring_sector(r0 + 1, r1 - 1, a0 + 0.02, a1 - 0.02, 1.0, 1.75, 'Grass', 12)
        mid = (deg0 + deg1) / 2
        # landscaping in the wedge
        inst(('Tree_Medium_High', 'Tree_Small', 'Tree_Tall_Thin')[k % 3], f'Tree_Inner_{k}', c, polar(64, mid, 1.7),
             rnd.uniform(0, TAU), (0.85, 1.0, 0.85)[k % 3])
        for j, (rr, dd) in enumerate(((56, -11), (56, 11), (69, -14), (69, 14), (60, 0))):
            inst(('Bush_01', 'Ground_Plant_01', 'Bush_03', 'Bush_02', 'Ground_Plant_02')[j], f'Bush_Inner_{k}_{j}', c,
                 polar(rr, mid + dd, 1.7), rnd.uniform(0, TAU), rnd.uniform(0.8, 1.1))
    p.finish(); g.finish()

    # lanterns along each spoke -----------------------------------------------------------------
    for name, deg in SLOT.items():
        if name == 'Entrance':
            continue
        a = math.radians(deg)
        side = Vector((-math.sin(a), math.cos(a), 0))
        w = 22 if name == 'Spawn' else 14
        for r in ((44.0,) if name == 'Spawn' else (44.0, 78.0)):
            for s in (-1, 1):
                pos = Vector(polar(r, deg)) + side * s * (w / 2 + 2.2)
                inst('Lantern_Post', f'Lantern_{name}_{int(r)}_{"LR"[s > 0]}', c, pos, a)

    # outer gardens between facilities ---------------------------------------------------------
    rnd = random.Random(5)
    for k in range(8):
        mid = k * 45 + 22.5
        if mid in (22.5, 337.5):          # beside the hatchery: it brings its own landscaping
            continue
        if mid in (67.5, 112.5):          # beside the grand stairs: low planters only
            inst('Stone_Planter', f'Planter_Stairs_{k}', c, polar(84, mid), math.radians(mid - 90))
            inst('Lantern_Stone', f'LanternStone_Stairs_{k}', c, polar(96, mid + (6 if mid < 90 else -6)))
            continue
        tree_in_planter(f'LobbyTree_Outer_{k}', c, polar(108, mid), math.radians(mid - 90), 'Tree_Large_High', seed=300 + k)
        inst(('Tree_Tall_Thin', 'Tree_Medium_High')[k % 2], f'Tree_Outer_{k}b', c, polar(126, mid + 9),
             rnd.uniform(0, TAU), 0.9)
        inst('Stone_Planter', f'Planter_Outer_{k}', c, polar(86, mid), math.radians(mid - 90))
        for j in range(3):
            inst(('Bush_02', 'Bush_01', 'Ground_Plant_01')[j], f'Bush_Outer_{k}_{j}', c,
                 polar(97 + j * 10, mid + (-11 if j % 2 else 11)), rnd.uniform(0, TAU))
        inst('Lantern_Stone', f'LanternStone_{k}', c, polar(116, mid - 6))

    # lawn rim: trees, rocks and a low balustrade on the island edge ------------------------------
    rnd = random.Random(8)
    for k in range(34):
        deg = k * (360 / 34) + rnd.uniform(-3, 3)
        if 55 < deg < 125:                 # tower foundation side
            continue
        r = rnd.uniform(138, 160)
        inst(rnd.choice(('Tree_Medium_High', 'Tree_Large_High', 'Tree_Small', 'Tree_Tall_Thin')), f'Tree_Rim_{k}', c,
             polar(r, deg, 0.3), rnd.uniform(0, TAU), rnd.uniform(0.85, 1.15))
        inst(rnd.choice(('Bush_01', 'Bush_02', 'Bush_03', 'Ground_Plant_01')), f'Bush_Rim_{k}', c, polar(r - 7, deg + 3, 0.3),
             rnd.uniform(0, TAU), rnd.uniform(1.0, 1.5))
    p = Part('Island_Balustrade', c, 0.15)
    for k in range(72):
        deg0 = k * 5
        if 52 < deg0 < 128:
            continue
        if any(abs(((deg0 - SLOT[s]) + 180) % 360 - 180) < 6 for s in ('Spawn',)):
            continue                                                   # opening at the south lookout
        a0, a1 = math.radians(deg0), math.radians(deg0 + 5)
        p.ring_sector(R_ISLAND - 3, R_ISLAND - 1.5, a0, a1, 0.3, 3.4, 'Hub_Stone', 2)
        p.ring_sector(R_ISLAND - 3.4, R_ISLAND - 1.1, a0, a1, 3.4, 4.0, 'Stone_Trim', 2)
        x, y, _ = polar(R_ISLAND - 2.25, deg0)
        p.box((x, y, 2.3), (2.6, 2.6, 4.6), 'Stone_Trim')
    p.finish()


# ---------------------------------------------------------------- spawn -----
def build_spawn_and_fountain():
    cs, cf = 'Spawn', 'Fountain'
    coll(cs, HUB); coll(cf, HUB)
    # central circular spawn platform -----------------------------------------------------------
    p = Part('Spawn_Platform', cs, 0.15)
    p.cyl((0, 0, 0.4), R_CORE, 0.8, 'Hub_Stone_Warm', 64)
    p.cyl((0, 0, 1.0), R_CORE - 4, 0.4, 'Plaza_Tile', 64)
    p.ring_sector(R_CORE - 4.5, R_CORE - 3.5, 0, TAU, 1.2, 1.3, 'Gold', 64)
    p.ring_sector(R_CORE - 9, R_CORE - 8, 0, TAU, 1.2, 1.28, 'Blue_Inlay', 64)
    # low stone seat walls with planters on the platform rim (gaps on the 8 spokes)
    for k in range(8):
        a0, a1 = math.radians(k * 45 + 10), math.radians(k * 45 + 35)
        p.ring_sector(R_CORE - 2.8, R_CORE - 0.4, a0, a1, 0.8, 2.6, 'Hub_Stone', 8)
        p.ring_sector(R_CORE - 3.1, R_CORE - 0.1, a0, a1, 2.6, 3.0, 'Stone_Trim', 8)
    p.finish()
    rnd = random.Random(12)
    for k in range(8):
        for j, d in enumerate((16, 29)):
            inst(('Bush_01', 'Ground_Plant_01')[j], f'Spawn_Bush_{k}_{j}', cs,
                 polar(R_CORE - 1.6, k * 45 + d, 3.0), rnd.uniform(0, TAU), 0.7)
        if k % 2 == 0:
            inst('Lantern_Stone', f'Spawn_Lantern_{k}', cs, polar(R_CORE - 1.6, k * 45 + 22.5, 3.0))

    # paw fountain -------------------------------------------------------------------------------
    z0 = 1.2
    from castle import bevel_box
    p = Part('Fountain_Basin', cf)
    # masonry basin wall: two courses of chamfered blocks (staggered) + cap stones, all real geometry
    nb = 24
    for row in range(2):
        for k in range(nb):
            a = TAU * (k + 0.5 * row) / nb
            M = Matrix.Translation((math.cos(a) * 18.0, math.sin(a) * 18.0, 0)) @ Matrix.Rotation(a + math.pi / 2, 4, 'Z')
            bevel_box(p, M, (0, 0, z0 + 0.65 + row * 1.3), (2 * 18.0 * math.sin(math.pi / nb) * 1.04 - 0.16, 2.0, 1.22),
                      ('Castle_Stone', 'Castle_Stone_Light')[(k + row) % 2], 0.16)
    for k in range(nb):
        a = TAU * (k + 0.25) / nb
        M = Matrix.Translation((math.cos(a) * 18.1, math.sin(a) * 18.1, 0)) @ Matrix.Rotation(a + math.pi / 2, 4, 'Z')
        bevel_box(p, M, (0, 0, z0 + 2.9), (2 * 18.1 * math.sin(math.pi / nb) * 1.06 - 0.14, 3.0, 0.6), 'Castle_Trim', 0.15)
    p.ring_sector(16.6, 16.9, 0, TAU, z0 + 3.2, z0 + 3.35, 'Gold', 48)
    p.cyl((0, 0, z0 + 1.2), 6.0, 2.4, 'Hub_Stone', 24)                   # pedestal
    p.cone((0, 0, z0 + 2.4), 4.0, 2.4, 'Hub_Stone_Warm', 24, r_top=9.5)  # upper bowl
    p.ring_sector(9.0, 9.8, 0, TAU, z0 + 4.8, z0 + 5.4, 'Stone_Trim', 32)
    p.torus((0, 0, z0 + 5.45), 9.4, 0.25, 'Gold', 40, 4)
    p.cyl((0, 0, z0 + 6.0), 2.2, 1.6, 'Hub_Stone_Warm', 16, r2=3.0)      # orb cradle
    p.torus((0, 0, z0 + 6.8), 3.0, 0.45, 'Gold', 24, 6)
    p.finish()
    p = Part('Fountain_Water', cf)
    p.cyl((0, 0, z0 + 2.2), 17.0, 0.2, 'Water', 48)
    p.cyl((0, 0, z0 + 5.1), 9.0, 0.2, 'Water', 32)
    for k in range(12):                     # spill-over sheets from the upper bowl
        a = TAU * k / 12
        d = Vector((math.cos(a), math.sin(a), 0))
        p.beam(d * 9.6 + Vector((0, 0, z0 + 5.2)), d * 12.0 + Vector((0, 0, z0 + 2.3)), 1.6, 0.25, 'Waterfall')
    for k in range(6):                      # jets around the basin
        a = TAU * (k + 0.5) / 6
        d = Vector((math.cos(a), math.sin(a), 0))
        p.beam(d * 15.5 + Vector((0, 0, z0 + 2.3)), d * 13.0 + Vector((0, 0, z0 + 6.0)), 0.35, 0.35, 'Waterfall')
        p.beam(d * 13.0 + Vector((0, 0, z0 + 6.0)), d * 11.0 + Vector((0, 0, z0 + 5.3)), 0.3, 0.3, 'Waterfall')
    p.finish()
    # glowing paw orb with cat ears (the game's emblem)
    p = Part('Fountain_PawOrb', cf)
    oc = Vector((0, 0, z0 + 10.6))
    p.uvsphere(oc, 4.6, 'Fountain_Orb', 24, 12, (1.0, 0.92, 1.0))
    # flame / teardrop finial with small side spikes (castle-base reference)
    p.cone(oc + Vector((0, 0, 3.6)), 1.9, 4.2, 'Fountain_Orb', 10)
    for k in range(4):
        a = TAU * k / 4 + 0.4
        tilt = Euler((math.sin(a) * 0.9, -math.cos(a) * 0.9, 0)).to_matrix()
        base = oc + Vector((math.cos(a) * 3.6, math.sin(a) * 3.6, 2.0))
        p.cyl(base + tilt @ Vector((0, 0, 0.7)), 0.7, 1.4, 'Fountain_Orb', 6, r2=0.05, rot=tilt)
    for side, rz in ((-1, 0.0), (1, math.pi)):           # paw on the front (-Y) and back
        paw(p, M_front(0, oc.y + side * 4.15, oc.z - 0.3, rz), 5.2, 0.8, 'Paw_White_Glow')
    p.torus(oc - Vector((0, 0, 4.0)), 4.4, 0.35, 'Magic_Glow', 40, 6)
    p.finish()
    # little floating sparkles round the orb
    p = Part('Fountain_Sparkles', cf)
    for k in range(18):
        a = rnd.uniform(0, TAU); r = rnd.uniform(6, 11)
        p.ico((math.cos(a) * r, math.sin(a) * r, z0 + rnd.uniform(6, 16)), rnd.uniform(0.15, 0.3), 'Magic_Glow', 1)
    p.finish()

    # spawn pad (Roblox SpawnLocation stand-in) on the south spoke --------------------------------
    p = Part('SpawnLocation_Pad', cs, 0.1)
    x, y, _ = SPAWN_POS
    p.cyl((x, y, 0.35), 8.0, 0.7, 'Hub_Stone_Warm', 40)
    p.cyl((x, y, 0.75), 6.6, 0.1, 'Blue_Inlay', 40)
    p.torus((x, y, 0.8), 7.3, 0.18, 'Gold', 40, 4)
    paw(p, Matrix.Translation((x, y + 0.4, 0.8)), 8.5, 0.1, 'Paw_White_Glow')
    for k in range(8):
        a = TAU * k / 8
        p.cyl((x + math.cos(a) * 9.5, y + math.sin(a) * 9.5, 0.9), 0.5, 1.8, 'Magic_Glow', 8)
    p.finish()
    avatar('SCALE_Avatar_5studs_Spawn', cs, (x + 2.0, y + 1.5, 0.8), math.pi)
    avatar('SCALE_Avatar_5studs_Portal', cs, (7.0, 138.0, 20.0), math.pi * 0.9)


# ---------------------------------------------------------------- facilities -
def facility(name):
    coll(name, HUB)
    deg = SLOT[name]
    e = empty(f'{name}_Root', name, polar(R_BUILD, deg), math.radians(deg - 90), 6)
    e.scale = (FAC_SCALE,) * 3
    return e


def plinth(p, w, d, h=1.2, step_w=16):
    p.box((0, 0, h / 2), (w, d, h), 'Hub_Stone')
    p.box((0, 0, h + 0.1), (w - 1, d - 1, 0.2), 'Plaza_Tile')
    p.box((0, -d / 2 - 1.5, h / 4), (step_w, 3.0, h / 2), 'Hub_Stone')


def sign(name, text, coll_name, parent, z, y, color_mat, w=None, size=3.2, text_mat='Shop_White', h=5.5):
    """framed sign board with 3D lettering on the front"""
    w = w or max(12.0, len(text) * size * 0.78 + 4)
    p = Part(name + '_Board', coll_name, 0.12)
    p.box((0, y, z), (w, 1.0, h), color_mat)
    p.box((0, y - 0.1, z + h / 2), (w + 0.6, 1.3, 0.5), 'Gold')
    p.box((0, y - 0.1, z - h / 2), (w + 0.6, 1.3, 0.5), 'Gold')
    for s in (-1, 1):
        p.box((s * w / 2, y - 0.1, z), (0.5, 1.3, h + 0.5), 'Gold')
    p.finish(parent=parent)
    text_mesh(name + '_Text', text, coll_name, size, 0.5, text_mat, (0, y - 0.75, z - 0.1), 0, parent)


def build_shop():
    """the detailed shop (shop.py) on the hub's Shop slot, front facing the fountain"""
    import shop
    deg = SLOT['Shop']
    shop.build_shop(HUB, polar(R_BUILD - 2.0, deg), math.radians(deg - 90))


def build_pets():
    root = facility('Pets'); c = 'Pets'
    p = Part('Pets_Building', c, 0.15)
    plinth(p, 34, 28)
    p.box((0, 11, 9.0), (30, 2, 15.6), 'Hub_Stone_Warm')
    for s in (-1, 1):
        p.box((s * 14, 2, 9.0), (2, 18, 15.6), 'Hub_Stone_Warm')
        for yy in (-8.0, 4.0):
            p.box((s * 14.2, yy, 9.0), (2.8, 2.8, 15.6), 'Hub_Stone')
        p.box((s * 9, -8.0, 9.0), (2.4, 2.4, 15.6), 'Hub_Stone')
    p.box((0, -8, 17.4), (32, 4, 2), 'Pets_Green')
    # gabled green roof + front pediment with paw
    p.prism_xz([(-18, 18.2), (18, 18.2), (0, 28.5)], -11.5, 13, 'Pets_Green')
    p.prism_xz([(-15.5, 18.4), (15.5, 18.4), (0, 27.0)], -11.8, -11.4, 'Hub_Stone_Warm')
    p.box((0, -12.0, 18.4), (36.5, 1.0, 0.6), 'Gold')
    paw(p, M_front(0, -12.0, 22.3), 6.0, 0.6, 'Pets_Green_Glow')
    # pet beds & pedestals inside
    for i, x in enumerate((-8, 0, 8)):
        p.cyl((x, 4, 2.0), 3.0, 1.6, 'Hub_Stone', 20)
        p.torus((x, 4, 3.0), 2.4, 0.7, ('Shop_Red', 'Upgrade_Blue', 'Eggs_Purple')[i], 20, 6)
        p.cyl((x, 4, 2.9), 2.0, 0.3, 'Fabric_Cream', 16)
    # bowls
    for x in (-4, 4):
        p.cyl((x, -2, 1.9), 1.1, 0.9, 'Silver', 12, r2=1.4)
    p.finish(parent=root)
    # pool in front (as in the reference)
    p = Part('Pets_Pool', c, 0.1)
    p.ring_sector(4.5, 6.0, 0, TAU, 0.0, 1.8, 'Hub_Stone', 24, center=(0, -19))
    p.cyl((0, -19, 1.3), 4.6, 0.2, 'Water', 24)
    p.torus((0, -19, 1.85), 5.25, 0.2, 'Pets_Green_Glow', 24, 4)
    p.finish(parent=root)
    sign('Pets_Sign', 'PETS', c, root, 31.5, -10.5, 'Pets_Green', 16, 4.0)
    for s in (-1, 1):
        inst('Lantern_Post', f'Pets_Lantern_{s}', c, (s * 19, -12, 1.2), 0, 1.0, root)
        inst('Bush_02', f'Pets_Bush_{s}', c, (s * 16, 10, 1.2), 0, 1.0, root)
        inst('Ground_Plant_01', f'Pets_Flowers_{s}', c, (s * 11.5, -15.5, 1.2), 0, 0.7, root)


def build_eggs():
    """the detailed hatchery (hatchery.py) on the hub's Eggs slot, front facing the fountain"""
    import hatchery
    deg = SLOT['Eggs']
    hatchery.build_hatchery(HUB, polar(R_BUILD + 2.0, deg), math.radians(deg - 90))


def build_trading():
    root = facility('Trading'); c = 'Trading'
    p = Part('Trading_Pavilion', c, 0.15)
    plinth(p, 34, 28, step_w=20)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 13.5, sy * 10
            p.box((x, y, 1.9), (3.6, 3.6, 1.4), 'Stone_Trim')
            p.cyl((x, y, 9.0), 1.3, 13.0, 'Trade_Gold', 12)
            p.box((x, y, 16.0), (3.2, 3.2, 1.2), 'Gold')
    p.box((0, 0, 17.4), (31, 24, 1.6), 'Hub_Stone_Warm')
    p.box((0, 0, 18.4), (32, 25, 0.5), 'Gold')
    # pyramidal golden roof with lantern finial
    p.prism([(-16, -12.5), (16, -12.5), (16, 12.5), (-16, 12.5)], 18.6, 19.4, 'Trade_Gold')
    vs = p.prism([(-15, -11.5), (15, -11.5), (15, 11.5), (-15, 11.5)], 19.4, 26.0, 'Trade_Gold')
    for v in vs[4:]:
        v.co.x *= 0.25; v.co.y *= 0.25
    p.box((0, 0, 27.0), (3, 3, 2.0), 'Trade_Gold_Glow')
    p.cone((0, 0, 28.0), 2.4, 2.5, 'Gold', 4)
    # two facing trade booths + central exchange ring
    for s in (-1, 1):
        p.box((s * 7, 2, 3.2), (4, 10, 2.8), 'Wood')
        p.box((s * 7, 2, 4.8), (5, 11, 0.4), 'Trade_Gold')
        p.box((s * 10.5, 2, 3.0), (2.0, 4.0, 2.4), 'Shop_Red')         # seats
    p.cyl((0, 2, 1.6), 3.4, 0.4, 'Trade_Gold_Glow', 24)
    p.finish(parent=root)
    # handshake icon on a framed golden plaque (front)
    p = Part('Trading_HandshakeIcon', c, 0.05)
    y = -12.8
    p.box((0, y + 0.6, 21.8), (11, 0.6, 6.6), 'Board_Navy')
    M = M_front(0, y, 21.8)
    for s in (-1, 1):                                # two forearms meeting
        p.beam(M @ Vector((s * 4.4, -1.6, 0.3)), M @ Vector((s * 1.2, 0.2, 0.3)), 1.4, 0.6, 'Trade_Gold_Glow')
    p.box(M @ Vector((0, 0.3, 0.3)), (3.6, 0.6, 2.0), 'Trade_Gold_Glow')     # clasped hands
    for i in range(4):
        p.box(M @ Vector((-1.3 + i * 0.85, 1.5, 0.35)), (0.6, 0.6, 1.1), 'Trade_Gold_Glow')
    p.finish(parent=root)
    sign('Trading_Sign', 'TRADING', c, root, 29.5, -12.5, 'Board_Navy', 22, 3.4, 'Trade_Gold_Glow')
    for s in (-1, 1):
        inst('Lantern_Post', f'Trading_Lantern_{s}', c, (s * 19, -12, 1.2), 0, 1.0, root)
        inst('Bush_03', f'Trading_Bush_{s}', c, (s * 18.5, 6, 1.2), 0, 1.1, root)


def build_upgrades():
    root = facility('Upgrades'); c = 'Upgrades'
    p = Part('Upgrades_Gate', c, 0.15)
    plinth(p, 36, 28)
    # big round arch gateway (stone with blue inner frame)
    p.strip_xz(round_arch(32, 14, 14), round_arch(22, 14, 14), 4.0, 9.0, 'Hub_Stone_Warm')
    p.strip_xz(round_arch(22.4, 14, 14), round_arch(20.6, 14, 14), 3.6, 9.4, 'Upgrade_Blue')
    p.strip_xz(round_arch(32.6, 14, 14), round_arch(31.4, 14, 14), 3.5, 4.0, 'Gold')
    p.prism_xz(round_arch(21, 14, 14), 8.6, 9.0, 'Board_Navy')                     # dark backdrop
    p.box((0, 6.5, 2.0), (36, 5, 1.6), 'Hub_Stone')
    p.finish(parent=root)
    # glowing up arrow in the arch
    p = Part('Upgrades_Arrow', c)
    arrow = [(-2.2, 0), (2.2, 0), (2.2, 8), (5.5, 8), (0, 15), (-5.5, 8), (-2.2, 8)]
    p.prism(arrow, 0, 0.8, 'Upgrade_Blue_Glow', M_front(0, 8.5, 4.8))
    p.finish(parent=root)
    # circular upgrade platform in front + crystals
    p = Part('Upgrades_Platform', c, 0.1)
    p.cyl((0, -6, 1.8), 9.0, 1.2, 'Hub_Stone_Warm', 40)
    p.cyl((0, -6, 2.45), 7.4, 0.1, 'Upgrade_Blue_Glow', 40)
    p.torus((0, -6, 2.5), 8.2, 0.25, 'Gold', 40, 4)
    paw(p, Matrix.Translation((0, -5.6, 2.5)), 8, 0.12, 'Paw_White_Glow')
    for s in (-1, 1):
        p.cyl((s * 13, -8, 4.0), 1.6, 5.6, 'Hub_Stone', 8)
        p.cyl((s * 13, -8, 7.0), 2.1, 0.5, 'Gold', 8)
    p.finish(parent=root)
    for s in (-1, 1):
        inst('Crystals_B', f'Upgrades_Crystal_{s}', c, (s * 13, -8, 7.2), 0.3 * s, 1.8, root)
        inst('Crystals_B', f'Upgrades_CrystalBig_{s}', c, (s * 19, 2, 1.2), 1.2 * s, 3.2, root)
        inst('Lantern_Post', f'Upgrades_Lantern_{s}', c, (s * 19, -12, 1.2), 0, 1.0, root)
    sign('Upgrades_Sign', 'UPGRADES', c, root, 27.0, 3.0, 'Upgrade_Blue', 24, 3.2)


def build_leaderboards():
    root = facility('Leaderboards'); c = 'Leaderboards'
    p = Part('Leaderboards_Base', c, 0.15)
    plinth(p, 44, 22, step_w=24)
    p.finish(parent=root)
    boards = ((-14.5, 0, 22, 'MOST PETS'), (0, -2.5, 27, 'HIGHEST FLOOR'), (14.5, 0, 22, 'RICHEST'))
    for i, (x, y, h, title) in enumerate(boards):
        b = Part(f'Leaderboard_{i + 1}', c, 0.1)
        w = 12.5
        b.box((x, y + 1.0, 1.2 + h / 2), (w + 1.6, 1.6, h), 'Board_Navy')
        b.box((x, y + 0.1, 1.2 + h / 2 - 1.5), (w - 0.6, 0.4, h - 6.0), 'Board_Screen')
        for s in (-1, 1):
            b.box((x + s * (w / 2 + 0.8), y + 1.0, 1.2 + h / 2), (1.0, 2.2, h + 0.6), 'Gold')
        b.box((x, y + 1.0, 1.4 + h), (w + 2.6, 2.4, 0.8), 'Gold')
        top = 1.2 + h - 5.0
        for r in range(10):                                   # ranking rows
            z = top - 1.6 - r * ((h - 8.0) / 10)
            badge = ('Gold', 'Silver', 'Bronze')[r] if r < 3 else 'Board_Row'
            b.cyl((x - w / 2 + 1.6, y - 0.2, z), 0.55, 0.3, badge, 10, axis='Y')
            b.box((x + 0.6, y - 0.15, z), (w - 4.8 - (r % 3) * 0.8, 0.2, 0.55), 'Board_Row')
        b.finish(parent=root)
        text_mesh(f'Leaderboard_{i + 1}_Title', title, c, 1.25, 0.3, 'Trade_Gold_Glow',
                  (x, y - 0.25, 1.2 + h - 2.0), 0, root)
    # trophy on top of the centre board
    t = Part('Leaderboards_Trophy', c)
    zt = 1.2 + 27 + 1.8
    t.box((0, -1.5, zt + 0.6), (4, 3, 1.2), 'Board_Navy')
    t.cyl((0, -1.5, zt + 2.0), 0.5, 1.8, 'Gold', 10)
    t.cone((0, -1.5, zt + 2.9), 1.0, 4.0, 'Gold', 16, r_top=3.0)
    t.cyl((0, -1.5, zt + 6.9), 3.0, 0.3, 'Gold', 16)
    for s in (-1, 1):
        t.torus((s * 3.0, -1.5, zt + 5.0), 1.2, 0.25, 'Gold', 16, 6, rot=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    t.finish(parent=root)
    sign('Leaderboards_Sign', 'LEADERBOARDS', c, root, 38.5, -2.6, 'Board_Navy', 30, 2.9, 'Trade_Gold_Glow')
    for s in (-1, 1):
        inst('Lantern_Post', f'Leaderboards_Lantern_{s}', c, (s * 23.5, -10, 1.2), 0, 1.0, root)
        inst('Ground_Plant_02', f'Leaderboards_Bush_{s}', c, (s * 7.3, -9.5, 1.2), 0, 0.8, root)


def build_hub():
    coll(HUB, 'TOWER_OF_PETS')
    build_plaza()
    build_spawn_and_fountain()
    build_shop(); build_pets(); build_eggs(); build_trading(); build_upgrades(); build_leaderboards()
