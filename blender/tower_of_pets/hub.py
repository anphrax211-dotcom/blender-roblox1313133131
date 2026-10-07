"""HUB: circular plaza, central paw fountain/spawn platform, spawn pad, the six facilities
(Pet Clinic, Shop, Eggs/Hatchery, Trading Plaza Portal, Pet Gym, Leaderboards monument) and the landscaping between them.

Layout follows the reference top-down hub plan (tower entrance north / +Y, spawn south):

                 TOWER ENTRANCE (90 deg)
  PET CLINIC (135)               SHOP (45)
   TRADING PORTAL (180)  FOUNTAIN   EGGS (0)
        LEADERBOARDS (225)       PET GYM (315)
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
SLOT = {'Eggs': 0, 'Shop': 45, 'Entrance': 90, 'PetClinic': 135, 'Trading': 180,
        'Leaderboards': 225, 'Spawn': 270, 'PetGym': 315}
SPAWN_POS = (0.0, -58.0, 0.0)
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
        for r in ((44.0,) if name in ('Spawn', 'Trading', 'Leaderboards') else (44.0, 78.0)):   # forecourts at r 78
            for s in (-1, 1):
                pos = Vector(polar(r, deg)) + side * s * (w / 2 + 2.2)
                inst('Lantern_Post', f'Lantern_{name}_{int(r)}_{"LR"[s > 0]}', c, pos, a)

    # outer gardens between facilities ---------------------------------------------------------
    rnd = random.Random(5)
    for k in range(8):
        mid = k * 45 + 22.5
        if mid in (22.5, 337.5, 202.5):   # beside the hatchery / between portal and monument: they bring their own
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
def build_shop():
    """the detailed shop (shop.py) on the hub's Shop slot, front facing the fountain"""
    import shop
    deg = SLOT['Shop']
    shop.build_shop(HUB, polar(R_BUILD - 2.0, deg), math.radians(deg - 90))


def build_pet_clinic():
    """the Pet Clinic (clinic.py) - replaces the old Pets area on the same slot, front facing the fountain"""
    import clinic
    deg = SLOT['PetClinic']
    clinic.build_clinic(HUB, polar(R_BUILD - 2.0, deg), math.radians(deg - 90))


def build_eggs():
    """the detailed hatchery (hatchery.py) on the hub's Eggs slot, front facing the fountain"""
    import hatchery
    deg = SLOT['Eggs']
    hatchery.build_hatchery(HUB, polar(R_BUILD + 2.0, deg), math.radians(deg - 90))


def build_trading_portal():
    """the Trading Plaza Portal (trading.py) - replaces the old Trading building on the same slot, facing the fountain"""
    import trading
    deg = SLOT['Trading']
    trading.build_trading_portal(HUB, polar(R_BUILD + 4.0, deg), math.radians(deg - 90))


def build_pet_gym():
    """the Pet Gym (gym.py) - replaces the old Upgrades area on the same slot, front facing the fountain"""
    import gym
    deg = SLOT['PetGym']
    gym.build_gym(HUB, polar(R_BUILD - 2.0, deg), math.radians(deg - 90))


def build_leaderboards():
    """the Leaderboards monument (leaderboard.py) - replaces the old Leaderboards stand on the same slot"""
    import leaderboard
    deg = SLOT['Leaderboards']
    leaderboard.build_leaderboards(HUB, polar(R_BUILD + 6.0, deg), math.radians(deg - 90))


def build_hub():
    coll(HUB, 'TOWER_OF_PETS')
    build_plaza()
    build_spawn_and_fountain()
    build_shop(); build_pet_clinic(); build_eggs(); build_trading_portal(); build_pet_gym(); build_leaderboards()
