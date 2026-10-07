"""TOWER OF PETS - PET GYM / TRAINING AREA (replaces the old Upgrades area), in the hub's castle masonry language.

Built from the written Pet Gym brief (blue + gold training theme): masonry facade with a deep round arch
(voussoirs, gold ring, recessed dark-blue inner ring), "TRAIN - LEVEL - GET STRONGER" slogan band, gold-framed
PET GYM sign, raised blue parapet carrying the paw + barbell emblem, banner pillars with lanterns, two dog mascot
statues (red headbands, blue wristbands, dumbbells) on pedestals, blue roofs with gold fascia, planters.
Interior: central dark-blue training floor (gold rings, paw), weight rack with dumbbells, bench press with a
barbell, plate stacks, punching bags on a frame, pull-up bar, wooden training posts, agility hurdles, jump
platforms, pet running wheel, training dummy, paw targets, trophy shelf, crates, banners, lanterns.

Collections: TOWER_OF_PETS_PET_GYM / BUILDING (Walls, Pillars, Arches, Roof, Gold_Trim), SIGNAGE (Pet_Gym,
Training_Slogan, Paw_Barbell), BANNERS, STATUES, TRAINING_EQUIPMENT (Weights, Barbells, Dumbbells, Benches,
Bags, Training_Posts, Agility), INTERIOR, TROPHIES, LANDSCAPING, LIGHTING  (" (gym)" suffix where taken).
Kit (PETGYM_KIT): PetGym_Wall, _Pillar, _Arch, _Roof, _GoldTrim, _Sign, _Emblem, _Banner, _PetStatue, _Dumbbell,
_Barbell, _Weight, _WeightRack, _Bench, _TrainingBag, _BagFrame, _PullUpBar, _TrainingPost, _Hurdle, _Platform,
_RunningWheel, _Dummy, _PawTarget, _Trophy, _TrophyShelf, _CentralFloor, _Lantern, _Planter.
"""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
from common import (Part, MATS, mat_plain, mat_noise, coll, inst, ASSETS, empty, paw, M_front, text_mesh,
                    round_arch, TAU)
from castle import (bevel_box, masonry, quoins, voussoirs, pillar, trim_run, inside, lifted, frame_strip,
                    rect_minus_arch)

ROOT = 'TOWER_OF_PETS_PET_GYM'
KIT = 'PETGYM_KIT'
I4 = Matrix.Identity(4)
FLIP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
DRAW = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
CN = {}


def RZ(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def T(x, y, z=0.0):
    return Matrix.Translation((x, y, z))


def c(name):
    return CN.get(name, name)


# ---------------------------------------------------------------- materials -
def build_gym_materials():
    P = mat_plain
    mat_noise('Gym_Blue', (0.05, 0.28, 0.86), (0.08, 0.33, 0.92), 0.6, 0.25, 0.08, 2.0)
    P('Gym_Blue_Dark', (0.03, 0.08, 0.34), 0.6)
    mat_noise('Gym_Floor_Dark', (0.03, 0.09, 0.36), (0.05, 0.12, 0.42), 0.7, 0.3, 0.05, 2.0)
    P('Gym_Mat', (0.05, 0.22, 0.66), 0.85)
    mat_noise('Gym_Roof', (0.04, 0.22, 0.72), (0.06, 0.27, 0.80), 0.5, 0.2, 0.1, 1.5)
    P('Gym_Roof_Dark', (0.02, 0.12, 0.48), 0.55)
    P('Gym_Rubber', (0.07, 0.07, 0.09), 0.7)
    P('Gym_Steel', (0.78, 0.80, 0.85), 0.25, metal=0.9)
    P('Gym_Red', (0.90, 0.08, 0.08), 0.5)
    P('Gym_Leather', (0.62, 0.10, 0.08), 0.6)
    P('Gym_Sign_Glow', (1.0, 1.0, 1.0), 0.4, emit=1.3)
    P('Gym_Glow_Blue', (0.15, 0.55, 1.0), 0.3, emit=1.0)
    P('Gym_Statue', (0.80, 0.72, 0.66), 0.6)
    P('Gym_White', (0.95, 0.96, 1.0), 0.5)
    P('Gym_Blue_Fabric', (0.04, 0.24, 0.80), 0.8)
    mat_noise('Gym_Wood_Floor', (0.55, 0.32, 0.15), (0.62, 0.38, 0.18), 0.6, 0.5, 0.15, 3.0)


# ---------------------------------------------------------------- symbols ---
def paw_barbell(p, M, s=1.0):
    """big gym emblem: stone + gold ring around a blue disc, white paw and a gold barbell across it
    (drawn on the local XZ plane, facing -y)"""
    n = 28
    def ring(r):
        return [(math.cos(TAU * i / n) * r * s, math.sin(TAU * i / n) * r * s) for i in range(n + 1)]
    frame_strip(p, M, ring(6.4), ring(5.6), -0.9, 1.0, 'Castle_Stone_Light')
    frame_strip(p, M, ring(5.7), ring(5.2), -1.3, 0.6, 'Gold')
    p.prism(ring(5.3)[:-1], 0.0, 0.8, 'Gym_Blue', M @ FLIP)
    paw(p, M @ T(0, 0, 0.9 * s) @ DRAW, 6.4 * s, 0.4, 'Gym_Sign_Glow')
    zb = -2.6 * s                                           # barbell across the lower half
    p.cyl(M @ Vector((0, -1.0, zb)), 0.28 * s, 15.0 * s, 'Gold', 10, axis='X')
    for sx in (-1, 1):
        for k, (x, r) in enumerate(((5.0, 1.9), (6.0, 1.5))):
            p.cyl(M @ Vector((sx * x * s, -1.0, zb)), r * s, 0.8 * s, ('Gym_Blue_Dark', 'Gold')[k], 16, axis='X')
        p.cyl(M @ Vector((sx * 4.3 * s, -1.0, zb)), 0.5 * s, 0.4 * s, 'Gold', 10, axis='X')


def gym_banner(p, M=I4, w=4.0, length=11.0):
    """bright blue banner, gold border, gold paw, gold top bar (hangs from local origin, faces -y)"""
    Mb = M @ DRAW
    o = [(-w / 2, 0), (w / 2, 0), (w / 2, -length), (0, -length - w * 0.55), (-w / 2, -length)]
    p.prism(o, -0.25, 0.0, 'Gym_Blue_Fabric', Mb)
    edge = [(-w / 2, 0), (-w / 2, -length), (0, -length - w * 0.55), (w / 2, -length), (w / 2, 0)]
    inner = [(-w / 2 + 0.35, 0), (-w / 2 + 0.35, -length + 0.15), (0, -length - w * 0.55 + 0.5),
             (w / 2 - 0.35, -length + 0.15), (w / 2 - 0.35, 0)]
    for (a0, a1), (b0, b1) in zip(zip(edge, edge[1:]), zip(inner, inner[1:])):
        q = [a0, a1, b1, b0]
        p.hexa([Mb @ Vector((x, z, 0.0)) for x, z in q] + [Mb @ Vector((x, z, 0.18)) for x, z in q], 'Gold')
    paw(p, Mb @ T(0, -length * 0.55, 0.0), w * 0.7, 0.25, 'Gold')
    bevel_box(p, M, (0, -0.3, 0.35), (w + 1.0, 0.5, 0.6), 'Gold', 0.08)
    for s in (-1, 1):
        p.ico(M @ Vector((s * (w / 2 + 0.6), -0.3, 0.35)), 0.38, 'Gold', 1)


# ---------------------------------------------------------------- equipment -
def dumbbell(p, M=I4, s=1.0):
    p.cyl(M @ Vector((0, 0, 0.5 * s)), 0.13 * s, 1.6 * s, 'Gym_Steel', 8, axis='X')
    for sx in (-1, 1):
        p.cyl(M @ Vector((sx * 0.7 * s, 0, 0.5 * s)), 0.5 * s, 0.35 * s, 'Gym_Blue_Dark', 6, axis='X')


def barbell(p, M=I4, L=8.0):
    p.cyl(M @ Vector((0, 0, 0)), 0.14, L, 'Gym_Steel', 8, axis='X')
    for sx in (-1, 1):
        for k, (x, r, mat) in enumerate(((L / 2 - 1.4, 1.2, 'Gym_Blue'), (L / 2 - 0.95, 0.95, 'Gym_Rubber'))):
            p.cyl(M @ Vector((sx * x, 0, 0)), r, 0.4, mat, 16, axis='X')
        p.cyl(M @ Vector((sx * (L / 2 - 1.8), 0, 0)), 0.3, 0.3, 'Gold', 8, axis='X')


def weight_plate(p, M=I4, r=1.2):
    p.cyl(M @ Vector((0, 0, 0.2)), r, 0.4, 'Gym_Rubber', 16)
    p.torus(M @ Vector((0, 0, 0.41)), r * 0.7, 0.08, 'Gold', 16, 4)
    p.cyl(M @ Vector((0, 0, 0.42)), 0.25, 0.05, 'Gym_Steel', 8)


def weight_rack(p):
    """two-level dumbbell rack (dumbbells built in so it reads at a distance); front -y"""
    for sx in (-1, 1):
        bevel_box(p, I4, (sx * 2.8, 0, 1.4), (0.4, 1.8, 2.8), 'Shop_Wood', 0.06)
    for z, y in ((1.1, -0.35), (2.4, 0.35)):
        bevel_box(p, I4, (0, y, z), (6.0, 1.0, 0.2), 'Shop_Wood', 0.05)
        for k in range(4):
            dumbbell(p, T(-2.1 + k * 1.4, y, z + 0.1) @ RZ(90), 0.7)
    bevel_box(p, I4, (0, 0.7, 3.0), (6.0, 0.25, 0.5), 'Gym_Blue', 0.05)
    p.ico((0, 0.55, 3.0), 0.3, 'Gold', 1)


def bench(p):
    """training bench (bench press) with uprights; barbell is a separate instance"""
    for y in (-1.8, 1.8):
        bevel_box(p, I4, (0, y, 0.7), (1.6, 0.4, 1.4), 'Gym_Steel', 0.05)
    bevel_box(p, I4, (0, 0, 1.55), (1.6, 4.4, 0.4), 'Shop_Wood', 0.08)
    bevel_box(p, I4, (0, 0, 1.95), (1.5, 4.2, 0.4), 'Gym_Mat', 0.18)
    for sx in (-1, 1):
        p.cyl((sx * 1.6, 2.0, 2.3), 0.15, 4.6, 'Gym_Steel', 8)
        p.box((sx * 1.6, 1.8, 4.3), (0.3, 0.5, 0.15), 'Gym_Steel')


def training_bag(p):
    """hanging punching bag (origin at the hook)"""
    p.cyl((0, 0, -0.6), 0.06, 1.2, 'Gym_Steel', 6)
    p.cyl((0, 0, -3.3), 1.1, 4.2, 'Gym_Leather', 14, smooth=True)
    p.cyl((0, 0, -1.25), 0.9, 0.3, 'Gym_Leather', 14, r2=1.1, smooth=True)
    for z in (-2.0, -4.6):
        p.torus((0, 0, z), 1.12, 0.08, 'Gold', 16, 4)
    paw(p, M_front(0, -1.12, -3.3), 1.3, 0.05, 'Gym_Sign_Glow')


def bag_frame(p, L=9.0, h=10.0):
    for sx in (-1, 1):
        bevel_box(p, I4, (sx * L / 2, 0, h / 2), (0.7, 0.7, h), 'Shop_Wood', 0.08)
        bevel_box(p, I4, (sx * L / 2, 0, 0.3), (1.6, 2.4, 0.6), 'Shop_Wood', 0.08)
    bevel_box(p, I4, (0, 0, h), (L + 1.0, 0.8, 0.8), 'Shop_Wood', 0.1)
    bevel_box(p, I4, (0, -0.42, h), (L, 0.06, 0.25), 'Gold', 0.02)


def pullup_bar(p):
    for sx in (-1, 1):
        p.cyl((sx * 3.2, 0, 4.5), 0.2, 9.0, 'Gym_Steel', 8)
        bevel_box(p, I4, (sx * 3.2, 0, 0.2), (1.2, 2.4, 0.4), 'Gym_Rubber', 0.06)
    p.cyl((0, 0, 8.4), 0.13, 6.8, 'Gym_Steel', 8, axis='X')
    for sx in (-1, 1):
        p.cyl((sx * 1.6, 0, 8.4), 0.2, 1.0, 'Gym_Rubber', 8, axis='X')


def training_post(p):
    """wooden training post / dummy with three striking arms and a padded target"""
    p.cyl((0, 0, 0.3), 1.2, 0.6, 'Shop_Wood', 10)
    p.cyl((0, 0, 3.4), 0.55, 5.6, 'Shop_Wood', 10)
    for z, ang in ((4.6, 25), (4.6, -25), (3.2, 0)):
        Mh = T(0, 0, z) @ RZ(ang)
        p.beam(Mh @ Vector((0, 0, 0)), Mh @ Vector((0, -1.8, 0.1)), 0.3, 0.3, 'Interior_Wood')
    p.cyl((0, -0.56, 2.2), 0.5, 0.2, 'Gym_Red', 12, axis='Y')
    p.cyl((0, -0.62, 2.2), 0.25, 0.1, 'Gym_Sign_Glow', 10, axis='Y')
    p.uvsphere((0, 0, 6.5), 0.65, 'Shop_Wood', 10, 6)


def hurdle(p, w=3.0, h=1.4):
    for sx in (-1, 1):
        bevel_box(p, I4, (sx * w / 2, 0, h / 2), (0.25, 0.25, h), 'Gym_Steel', 0.03)
        bevel_box(p, I4, (sx * w / 2, 0, 0.1), (0.4, 1.2, 0.2), 'Gym_Rubber', 0.04)
    for k in range(2):
        bevel_box(p, I4, (0, 0, h - 0.1 - k * 0.2), (w, 0.2, 0.2), ('Gym_Red', 'Gym_White')[k % 2], 0.04)


def platform(p):
    """three stepped jump platforms with paw tops"""
    for k, (x, h) in enumerate(((-2.4, 1.0), (0.0, 2.0), (2.4, 3.0))):
        bevel_box(p, I4, (x, 0, h / 2), (2.2, 2.2, h), ('Gym_Blue', 'Gym_Mat', 'Gym_Blue')[k], 0.15)
        bevel_box(p, I4, (x, 0, h + 0.05), (2.3, 2.3, 0.1), 'Gold', 0.03)
        paw(p, T(x, 0.1, h + 0.1), 1.4, 0.04, 'Gym_Sign_Glow')


def running_wheel(p):
    """big pet running wheel on an A-frame stand"""
    R = 3.4
    for x in (-1.0, 1.0):
        p.torus(Vector((x, 0, R + 0.6)), R, 0.18, 'Gym_Blue', 32, 6, rot=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    for i in range(16):
        a = TAU * i / 16
        q = Vector((0, math.cos(a) * R, R + 0.6 + math.sin(a) * R))
        p.beam(q + Vector((-1.0, 0, 0)), q + Vector((1.0, 0, 0)), 0.3, 0.3, 'Shop_Wood')
    for x in (-1.3, 1.3):
        for sy in (-1, 1):
            p.beam(Vector((x, sy * 2.2, 0)), Vector((x, 0, R + 0.6)), 0.3, 0.3, 'Gym_Steel')
    p.cyl((0, 0, R + 0.6), 0.25, 3.2, 'Gold', 8, axis='X')


def dummy(p):
    """padded training dummy on a spring base"""
    p.cyl((0, 0, 0.25), 1.2, 0.5, 'Gym_Rubber', 12)
    for k in range(4):
        p.torus((0, 0, 0.7 + k * 0.3), 0.35, 0.08, 'Gym_Steel', 10, 4)
    p.cyl((0, 0, 2.9), 0.9, 2.8, 'Gym_Red', 12, smooth=True)
    p.uvsphere((0, 0, 4.8), 0.8, 'Gym_Red', 12, 8)
    p.torus((0, 0, 2.2), 0.92, 0.1, 'Gold', 16, 4)
    paw(p, M_front(0, -0.92, 3.2), 1.0, 0.05, 'Gym_Sign_Glow')


def paw_target(p):
    """round wall target with a paw bullseye (faces -y)"""
    for k, (r, mat) in enumerate(((2.0, 'Gym_Blue_Dark'), (1.5, 'Gym_White'), (1.0, 'Gym_Red'))):
        p.cyl((0, -0.1 * k, 0), r, 0.2, mat, 24, axis='Y')
    p.torus((0, -0.05, 0), 2.0, 0.1, 'Gold', 24, 4, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
    paw(p, M_front(0, -0.3, 0.05), 1.3, 0.05, 'Gym_Sign_Glow')


def trophy(p, s=1.0):
    p.cyl((0, 0, 0.25 * s), 0.6 * s, 0.5 * s, 'Gym_Blue_Dark', 8)
    p.cyl((0, 0, 0.75 * s), 0.12 * s, 0.6 * s, 'Gold', 8)
    p.cone((0, 0, 1.0 * s), 0.25 * s, 1.0 * s, 'Gold', 12, r_top=0.6 * s)
    for sx in (-1, 1):
        p.torus((sx * 0.6 * s, 0, 1.6 * s), 0.25 * s, 0.06 * s, 'Gold', 10, 4, rot=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    p.ico((0, 0, 2.15 * s), 0.18 * s, 'Gold', 1)


def trophy_shelf(p):
    """achievement shelf: wooden unit with gold trophies and paw medals built in (front -y)"""
    w, h = 9.0, 7.0
    for sx in (-1, 1):
        bevel_box(p, I4, (sx * (w / 2 - 0.25), 0, h / 2), (0.5, 1.6, h), 'Shop_Wood', 0.08)
    bevel_box(p, I4, (0, 0.65, h / 2), (w, 0.3, h), 'Gym_Blue_Dark', 0.05)
    for k, z in enumerate((0.4, 2.6, 4.8)):
        bevel_box(p, I4, (0, 0, z), (w - 0.5, 1.6, 0.25), 'Shop_Wood', 0.05)
        bevel_box(p, I4, (0, -0.78, z + 0.12), (w - 0.5, 0.08, 0.2), 'Gold', 0.02)
        for j in range(3):
            x = -2.8 + j * 2.8
            if (k + j) % 2 == 0:
                trophy_at(p, x, z + 0.13, 0.9 + 0.2 * (j == 1))
            else:                                               # paw medal on a stand
                p.cyl((x, 0.2, z + 1.0), 0.7, 0.15, 'Gold', 16, axis='Y')
                paw(p, M_front(x, 0.1, z + 1.0), 0.8, 0.05, 'Gym_Blue_Dark')
                p.box((x, 0.3, z + 0.45), (0.15, 0.15, 0.9), 'Shop_Wood')
    bevel_box(p, I4, (0, -0.1, h + 0.3), (w + 0.6, 1.9, 0.6), 'Shop_Wood', 0.1)
    p.cone((0, -0.4, h + 0.6), 0.7, 1.0, 'Gold', 4)


def trophy_at(p, x, z, s):
    p.cyl((x, 0, z + 0.25 * s), 0.6 * s, 0.5 * s, 'Gym_Blue_Dark', 8)
    p.cyl((x, 0, z + 0.75 * s), 0.12 * s, 0.6 * s, 'Gold', 8)
    p.cone((x, 0, z + 1.0 * s), 0.25 * s, 1.0 * s, 'Gold', 12, r_top=0.6 * s)
    for sx in (-1, 1):
        p.torus((x + sx * 0.6 * s, 0, z + 1.6 * s), 0.25 * s, 0.06 * s, 'Gold', 10, 4,
                rot=Matrix.Rotation(math.pi / 2, 3, 'Y'))


def central_floor(p, r=7.5):
    """central circular training floor: dark blue disc, gold rings, tick marks and a big paw"""
    p.cyl((0, 0, 0.1), r, 0.2, 'Gym_Floor_Dark', 48)
    for rr, t in ((r - 0.3, 0.14), (r * 0.66, 0.1)):
        p.torus((0, 0, 0.22), rr, t, 'Gold', 48, 4)
    for k in range(12):
        a = TAU * k / 12
        Mk = T(math.cos(a) * (r * 0.83), math.sin(a) * (r * 0.83)) @ Matrix.Rotation(a, 4, 'Z')
        bevel_box(p, Mk, (0, 0, 0.22), (1.2, 0.25, 0.06), 'Gym_Glow_Blue', 0.02)
    paw(p, T(0, 0.3, 0.2), r * 0.8, 0.06, 'Gold')


def dog_statue(p, rnd=None):
    """friendly mascot dog statue: red headband, blue wristbands, little dumbbell; masonry pedestal"""
    rnd = rnd or random.Random(7)
    bevel_box(p, I4, (0, 0, 0.5), (6.6, 6.6, 1.0), 'Castle_Trim', 0.18)
    masonry(p, T(0, -2.7), -2.7, 2.7, 1.0, 5.0, rnd, 1.4, (1.8, 2.8), 5.4, backing=False)
    bevel_box(p, I4, (0, 0, 5.4), (6.4, 6.4, 0.8), 'Castle_Trim', 0.15)
    bevel_box(p, I4, (0, -3.25, 5.4), (5.6, 0.3, 0.3), 'Gold', 0.04)
    S, z = 'Gym_Statue', 5.8
    p.uvsphere((0, 0.6, z + 2.6), 2.2, S, 16, 10, (1.0, 1.15, 1.2))
    for s_ in (-1, 1):
        p.uvsphere((s_ * 1.6, 1.2, z + 1.4), 1.35, S, 12, 8, (0.85, 1.3, 1.0))
        p.cyl((s_ * 0.85, -1.1, z + 1.6), 0.55, 3.2, S, 10, smooth=True)
        p.uvsphere((s_ * 0.85, -1.6, z + 0.35), 0.7, S, 10, 6, (1, 1.35, 0.6))
        p.torus((s_ * 0.85, -1.1, z + 1.5), 0.6, 0.18, 'Gym_Blue', 12, 4)            # wristbands
    p.uvsphere((0, -0.5, z + 5.6), 1.7, S, 16, 10, (1.0, 1.0, 0.95))
    p.uvsphere((0, -2.1, z + 5.0), 0.95, S, 12, 8, (0.9, 1.1, 0.75))                # snout
    p.uvsphere((0, -3.0, z + 5.3), 0.32, 'Gym_Rubber', 8, 5)                        # nose
    for s_ in (-1, 1):
        p.uvsphere((s_ * 1.7, -0.3, z + 5.0), 0.7, S, 10, 6, (0.5, 0.8, 1.5))       # floppy ears
        p.ico((s_ * 0.65, -1.95, z + 6.0), 0.2, 'Gym_Rubber', 1)
    p.torus((0, -0.5, z + 6.4), 1.62, 0.25, 'Gym_Red', 20, 6, rot=Euler((0.15, 0, 0)).to_matrix())  # headband
    p.cone((1.5, 0.4, z + 6.4), 0.3, -1.4, 'Gym_Red', 4)
    dumbbell(p, T(0, -2.0, z), 1.0)
    from foliage import tube
    tube(p, [Vector((0, 2.6, z + 1.0)), Vector((0.4, 3.4, z + 2.4)), Vector((0.2, 3.2, z + 3.6))],
         [0.45, 0.35, 0.2], S, 6)


def planter(p, rnd, w=6.0, d=3.6):
    from foliage import leaf_cluster
    masonry(p, T(0, -d / 2), -w / 2, w / 2, 0, 2.0, rnd, 1.0, (1.6, 2.4), d - 0.4, backing=False)
    bevel_box(p, I4, (0, 0, 2.2), (w + 0.5, d + 0.5, 0.4), 'Castle_Trim', 0.1)
    p.box((0, 0, 2.3), (w - 0.6, d - 0.6, 0.2), 'Dirt')
    for k in range(3):
        x = -w / 2 + 1.2 + k * (w - 2.4) / 2
        leaf_cluster(p, (x, rnd.uniform(-0.4, 0.4), 3.2), 1.2, rnd, 14, squash=0.8)
        for j in range(4):
            a = TAU * j / 4 + k
            p.ico((x + math.cos(a) * 0.9, math.sin(a) * 0.9, 3.9 + rnd.uniform(-0.2, 0.3)), 0.32, 'Gym_Blue', 1)
            p.ico((x + math.cos(a) * 0.9, math.sin(a) * 0.9, 4.15), 0.12, 'Gym_White', 1)


def _lib(name, builder, *a, **kw):
    p = Part('ASSET_' + name, KIT)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def build_gym_kit(parent):
    from shop import shop_lantern, roof_slope
    coll(KIT, parent)
    R = random.Random
    _lib('PetGym_Wall', lambda p: masonry(p, I4, -6, 6, 0, 10, R(1), 2.5, (3, 5)))
    _lib('PetGym_Pillar', lambda p: pillar(p, I4, 5.4, 0, 23, R(2), cap=None, band=0.56))
    _lib('PetGym_Arch', lambda p: voussoirs(p, I4, round_arch(18, 4, 14), round_arch(14, 4, 14), -0.6, 1.6, R(3), 2.4))
    _lib('PetGym_Roof', lambda p: roof_slope(p, I4, 0, 8, 0, 4.0, -4, 4, 0.5, mat='Gym_Roof', course_mat='Gym_Roof_Dark'))
    _lib('PetGym_GoldTrim', lambda p: bevel_box(p, I4, (0, 0, 0.2), (8, 0.35, 0.4), 'Gold', 0.06))
    def sign(p):
        bevel_box(p, I4, (0, 0.4, 2.4), (14, 0.8, 4.2), 'Gym_Blue_Dark', 0.1)
        frame_strip(p, I4, [(-7.4, 0.0), (-7.4, 4.8), (7.4, 4.8), (7.4, 0.0), (-7.4, 0.0)],
                    [(-7.0, 0.4), (-7.0, 4.4), (7.0, 4.4), (7.0, 0.4), (-7.0, 0.4)], -0.5, 0.3, 'Gold')
    _lib('PetGym_Sign', sign)
    _lib('PetGym_Emblem', lambda p: paw_barbell(p, T(0, 0, 6.5), 1.0))
    _lib('PetGym_Banner', gym_banner)
    _lib('PetGym_PetStatue', dog_statue)
    _lib('PetGym_Dumbbell', dumbbell)
    _lib('PetGym_Barbell', barbell)
    _lib('PetGym_Weight', weight_plate)
    _lib('PetGym_WeightRack', weight_rack)
    _lib('PetGym_Bench', bench)
    _lib('PetGym_TrainingBag', training_bag)
    _lib('PetGym_BagFrame', bag_frame)
    _lib('PetGym_PullUpBar', pullup_bar)
    _lib('PetGym_TrainingPost', training_post)
    _lib('PetGym_Hurdle', hurdle)
    _lib('PetGym_Platform', platform)
    _lib('PetGym_RunningWheel', running_wheel)
    _lib('PetGym_Dummy', dummy)
    _lib('PetGym_PawTarget', paw_target)
    _lib('PetGym_Trophy', trophy)
    _lib('PetGym_TrophyShelf', trophy_shelf)
    _lib('PetGym_CentralFloor', central_floor)
    _lib('PetGym_Lantern', shop_lantern)
    _lib('PetGym_Planter', planter, R(5))


# ---------------------------------------------------------------- build -----
def subcolls(parent, in_lobby):
    from hatchery import RESERVED
    CN.clear()
    coll(ROOT, parent)
    tree = (('BUILDING', ROOT), ('Walls', 'BUILDING'), ('Pillars', 'BUILDING'), ('Arches', 'BUILDING'),
            ('Roof', 'BUILDING'), ('Gold_Trim', 'BUILDING'), ('SIGNAGE', ROOT), ('Pet_Gym', 'SIGNAGE'),
            ('Training_Slogan', 'SIGNAGE'), ('Paw_Barbell', 'SIGNAGE'), ('BANNERS', ROOT), ('STATUES', ROOT),
            ('TRAINING_EQUIPMENT', ROOT), ('Weights', 'TRAINING_EQUIPMENT'), ('Barbells', 'TRAINING_EQUIPMENT'),
            ('Dumbbells', 'TRAINING_EQUIPMENT'), ('Benches', 'TRAINING_EQUIPMENT'), ('Bags', 'TRAINING_EQUIPMENT'),
            ('Training_Posts', 'TRAINING_EQUIPMENT'), ('Agility', 'TRAINING_EQUIPMENT'), ('INTERIOR', ROOT),
            ('TROPHIES', ROOT), ('LANDSCAPING', ROOT), ('LIGHTING', ROOT))
    for name, par in tree:
        taken = name in bpy.data.collections or (in_lobby and name in RESERVED)
        CN[name] = f'{name} (gym)' if taken else name
        coll(CN[name], c(par))


def build_gym(parent_coll, loc=(0, 0, 0), rot_z=0.0):
    from shop import roof_slope
    subcolls(parent_coll, parent_coll is not None)
    root = empty('PetGym_Root', ROOT, loc, rot_z, 8)
    rnd = random.Random(1357)
    F = 1.0
    yF = -9.0

    def fin(p):
        return p.finish(parent=root)

    def I(asset, name, col, xyz, rz=0.0, s=1.0):
        return inst(asset, name, c(col), xyz, rz, s, root)

    # ---------------- plinth + floor ------------------------------------------------------------------
    p = Part('PetGym_Floor', c('Walls'))
    bevel_box(p, I4, (0, 4, F / 2), (56, 38, F), 'Castle_Trim', 0.2)
    for i in range(2):
        bevel_box(p, I4, (0, -15.7 - i * 1.4, (F - i * 0.5) / 2), (24 - i * 2, 1.4, F - i * 0.5), 'Castle_Stone_Light', 0.12)
    for k in range(16):                                          # wooden training floor (planks)
        x = -14.6 + (k + 0.5) * 29.2 / 16
        bevel_box(p, I4, (x, 6.5, F + 0.1), (29.2 / 16 - 0.1, 31.0, 0.2), 'Gym_Wood_Floor', 0.04)
    fin(p)
    I('PetGym_CentralFloor', 'PetGym_CentralFloor', 'INTERIOR', (0, 6.0, F + 0.2))

    # ---------------- hall walls ------------------------------------------------------------------------
    w = Part('PetGym_Hall_Walls', c('Walls'))
    w.box((0, 22.6, (F + 22) / 2), (34, 2.4, 22 - F), 'Castle_Seam')
    masonry(w, T(0, 24.0) @ RZ(180), -17, 17, F, 22.0, rnd, 2.4, (3, 5.5), 1.6,
            skip=lambda x, z, ww, h: (x * x) / 64 + ((z - 13.0) ** 2) / 64 < 1.0, backing=False)
    for s in (-1, 1):
        w.box((s * 16.0, 7.0, (F + 22) / 2), (2.0, 32, 22 - F), 'Castle_Seam')
        xr = (-9.0, 23.0) if s > 0 else (-23.0, 9.0)
        masonry(w, T(s * 17.1, 0) @ RZ(s * 90), xr[0], xr[1], 13.0, 22.0, rnd, 2.4, (3, 5.5), 1.6, backing=False)
        quoins(w, T(s * 17.1, 24.0) @ RZ(180), F, 22.0, rnd, 3.4, 2.0, 2.4, side=s, mat='Castle_Trim')
        # interior: stone-coloured plaster above a blue wainscot with a gold rail
        bevel_box(w, I4, (s * 14.9, 7.0, F + 10.5), (0.3, 32, 21), 'Castle_Stone_Light', 0.05)
        bevel_box(w, I4, (s * 14.7, 7.0, F + 2.4), (0.3, 32, 4.8), 'Gym_Blue', 0.05)
        bevel_box(w, I4, (s * 14.6, 7.0, F + 4.9), (0.3, 32, 0.25), 'Gold', 0.03)
        bevel_box(w, I4, (s * 14.6, 7.0, F + 20.4), (0.6, 32, 0.8), 'Castle_Trim', 0.08)
    bevel_box(w, I4, (0, 21.3, F + 10.5), (29.6, 0.3, 21), 'Castle_Stone_Light', 0.05)
    bevel_box(w, I4, (0, 21.1, F + 2.4), (29.6, 0.3, 4.8), 'Gym_Blue', 0.05)
    bevel_box(w, I4, (0, 21.0, F + 4.9), (29.6, 0.3, 0.25), 'Gold', 0.03)
    fin(w)
    be = Part('PetGym_Back_Emblem', c('Paw_Barbell'))
    paw_barbell(be, T(0, 24.6, F + 13.0) @ RZ(180), 1.15)
    fin(be)

    # ---------------- wings -----------------------------------------------------------------------------
    wg = Part('PetGym_Wings', c('Walls'))
    WT = 13.0
    for s in (-1, 1):
        x0, x1 = (17.2, 27.0) if s > 0 else (-27.0, -17.2)
        wg.box(((x0 + x1) / 2, 5.0, (F + WT) / 2), (x1 - x0, 24, WT - F), 'Castle_Seam')
        xr = (-7.0, 17.0) if s > 0 else (-17.0, 7.0)
        masonry(wg, T(s * 27.1, 0) @ RZ(s * 90), xr[0], xr[1], F, WT, rnd, 2.4, (3, 5.5), 1.6, backing=False)
        masonry(wg, T(0, 17.1) @ RZ(180), -x1, -x0, F, WT, rnd, 2.4, (3, 5.5), 1.6, backing=False)
        quoins(wg, T(s * 27.1, 17.1) @ RZ(180), F, WT, rnd, 3.4, 2.0, 2.4, side=s, mat='Castle_Trim')
        masonry(wg, T(0, -7.1), x0, x1, F, WT, rnd, 2.4, (3, 5.5), 1.6,
                skip=lambda x, z, ww, h, s=s: abs(x - s * 22.2) < 3.4 and z < F + 11.4, backing=False)
        bevel_box(wg, I4, (s * 22.2, -6.6, F + 5.7), (6.4, 0.6, 10.4), 'Gym_Blue', 0.08)
        frame_strip(wg, T(s * 22.2, -7.0), [(-3.5, F), (-3.5, F + 11.2), (3.5, F + 11.2), (3.5, F)],
                    [(-3.15, F), (-3.15, F + 10.85), (3.15, F + 10.85), (3.15, F)], -0.5, 0.3, 'Gold')
        quoins(wg, T(s * 27.1, -7.1), F, WT, rnd, 3.4, 2.0, 2.4, side=-s, mat='Castle_Trim')
        trim_run(wg, T(0, -7.4), x0, x1, WT - 1.6, h=1.6, out=1.0)
        pillar(wg, T(s * 27.0, -7.6), 3.4, 0, WT + 2.6, rnd, cap=None, band=0.5, panel=False)
    fin(wg)
    for s in (-1, 1):
        I('PetGym_Banner', f'PetGym_WingBanner_{"LR"[s > 0]}', 'BANNERS', (s * 22.2, -7.0, F + 10.6), 0, 0.8)
        I('PetGym_Lantern', f'PetGym_WingLantern_{"LR"[s > 0]}', 'LIGHTING', (s * 27.0, -7.6, WT + 2.4), 0, 1.1)

    # ---------------- facade: deep round arch, slogan, sign, emblem parapet ------------------------------
    fa = Part('PetGym_Facade', c('Walls'))
    AW, AH = 14.0, 10.0
    A = lambda wdt: lifted(round_arch(wdt, AH, 14), 0, F)
    masonry(fa, T(0, yF), -17.0, 17.0, F, 22.0, rnd, 2.6, (3.2, 5.5), 1.6,
            skip=lambda x, z, ww, h: inside(A(AW + 5.6), x, z), backing=False)
    rect_minus_arch(fa, T(0, yF), -17.0, 17.0, F, 22.0, A(AW), 1.0, 2.0, 'Castle_Seam')
    ar = Part('PetGym_Arch', c('Arches'))
    voussoirs(ar, T(0, yF), A(AW + 5.6), A(AW + 1.8), -1.6, 1.2, rnd, 2.6)
    frame_strip(ar, T(0, yF), A(AW + 1.8), A(AW + 1.0), -1.0, 1.6, 'Gold')
    frame_strip(ar, T(0, yF), A(AW + 1.0), A(AW), 0.4, 2.6, 'Gym_Blue_Dark')
    for s in (-1, 1):
        bevel_box(ar, I4, (s * (AW / 2 + 0.4), yF + 1.6, F + AH / 2), (0.8, 2.4, AH), 'Gym_Blue_Dark', 0.06)
    fin(ar)
    trim_run(fa, T(0, yF), -17, 17, F, h=1.2, out=1.0)
    quoins(fa, T(-17.0, yF), F, 22.0, rnd, 3.4, 2.0, 2.6, side=1, mat='Castle_Trim')
    quoins(fa, T(17.0, yF), F, 22.0, rnd, 3.4, 2.0, 2.6, side=-1, mat='Castle_Trim')
    # raised blue parapet carrying the emblem
    para = [(-12.5, 28.0), (12.5, 28.0), (12.5, 31.0), (7.5, 34.6), (-7.5, 34.6), (-12.5, 31.0)]
    fa.prism(para, yF - 2.2, yF + 1.2, 'Gym_Blue', FLIP)
    frame_strip(fa, T(0, yF - 2.2), para + [para[0]], [(x * 0.94, 28.0 + (z - 28.0) * 0.9) for x, z in para + [para[0]]],
                -0.5, 0.2, 'Gold')
    for s in (-1, 1):
        bevel_box(fa, I4, (s * 12.5, yF - 0.5, 29.5), (2.4, 3.4, 3.0), 'Castle_Stone_Light', 0.18)
        bevel_box(fa, I4, (s * 12.5, yF - 0.5, 31.2), (2.9, 3.9, 0.5), 'Castle_Trim', 0.12)
    fin(fa)
    sl = Part('PetGym_Slogan_Band', c('Training_Slogan'))
    bevel_box(sl, T(0, yF - 3.2, 19.75), (0, 0.4, 0), (25.0, 0.8, 3.1), 'Gym_Blue_Dark', 0.08)
    frame_strip(sl, T(0, yF - 3.2, 18.2), [(-12.8, 0.0), (-12.8, 3.1), (12.8, 3.1), (12.8, 0.0), (-12.8, 0.0)],
                [(-12.45, 0.3), (-12.45, 2.8), (12.45, 2.8), (12.45, 0.3), (-12.45, 0.3)], -0.4, 0.3, 'Gold')
    fin(sl)
    text_mesh('PetGym_Slogan_Text', 'TRAIN • LEVEL • GET STRONGER', c('Training_Slogan'), 1.75, 0.3,
              'Gym_Sign_Glow', (0, yF - 3.75, 19.7), 0, root)
    sg = Part('PetGym_Sign', c('Pet_Gym'))
    Ms = T(0, yF - 2.4, 21.6)
    bevel_box(sg, Ms, (0, 0.4, 3.0), (22.0, 0.8, 5.8), 'Gym_Blue_Dark', 0.1)
    frame_strip(sg, Ms, [(-11.4, 0.0), (-11.4, 6.2), (11.4, 6.2), (11.4, 0.0), (-11.4, 0.0)],
                [(-11.0, 0.4), (-11.0, 5.8), (11.0, 5.8), (11.0, 0.4), (-11.0, 0.4)], -0.5, 0.3, 'Gold')
    for s in (-1, 1):
        sg.cyl(Ms @ Vector((s * 11.6, -0.4, 3.0)), 1.2, 0.6, 'Gold', 12, axis='Y')
        sg.cyl(Ms @ Vector((s * 11.6, -0.75, 3.0)), 0.8, 0.2, 'Gym_Glow_Blue', 12, axis='Y')
    fin(sg)
    text_mesh('PetGym_Sign_Text', 'PET GYM', c('Pet_Gym'), 4.2, 0.6, 'Gym_Sign_Glow', (0, yF - 3.1, 24.5), 0, root)
    em = Part('PetGym_Paw_Barbell', c('Paw_Barbell'))
    paw_barbell(em, T(0, yF - 2.4, 36.2), 1.0)
    fin(em)

    # ---------------- roofs ---------------------------------------------------------------------------------
    rf = Part('PetGym_Roofs', c('Roof'))
    gt = Part('PetGym_Gold_Trim', c('Gold_Trim'))
    ze, zr = 22.6, 30.0
    for s in (-1, 1):
        roof_slope(rf, I4 if s > 0 else Matrix.Scale(-1, 4, Vector((1, 0, 0))), 18.4, 0.0, ze - 0.6, zr, yF + 1.0,
                   25.0, 0.8, mat='Gym_Roof', sag=0.5, course_mat='Gym_Roof_Dark')
        bevel_box(gt, I4, (s * 18.5, 8.0, ze - 0.7), (0.5, 24.0, 0.6), 'Gold', 0.06)
        Mw = I4 if s > 0 else Matrix.Scale(-1, 4, Vector((1, 0, 0)))
        roof_slope(rf, Mw, 28.6, 17.1, WT + 0.2, 19.6, -9.6, 18.6, 0.7, mat='Gym_Roof', sag=0.35, course_mat='Gym_Roof_Dark')
        bevel_box(gt, I4, (s * 28.7, 4.5, WT + 0.15), (0.5, 28.2, 0.55), 'Gold', 0.06)
        ang = math.atan2(19.6 - WT, 11.5)
        Mr = T(s * 22.85, -9.7, (WT + 19.6) / 2 + 0.2) @ Matrix.Rotation(s * ang, 4, 'Y')
        bevel_box(gt, Mr, (0, 0, 0), (math.hypot(11.5, 19.6 - WT) + 0.4, 0.5, 0.55), 'Gold', 0.06)
    bevel_box(rf, I4, (0, 8.0, zr + 0.6), (1.6, 24.0, 1.2), 'Gym_Roof_Dark', 0.2)
    rf.prism([(-17.0, 22.0), (17.0, 22.0), (0, zr - 0.2)], 23.0, 24.4, 'Gym_Blue', FLIP)
    fin(rf)
    fin(gt)

    # ---------------- pillars, banners, lanterns, statues --------------------------------------------------
    pl = Part('PetGym_Pillars', c('Pillars'))
    for s in (-1, 1):
        pillar(pl, T(s * 15.6, yF - 3.0), 5.4, F, 24.0, rnd, cap=None, band=0.56)
        bevel_box(pl, T(s * 15.6, yF - 3.0), (0, 0, F + 26.0), (7.0, 7.0, 1.0), 'Castle_Trim', 0.15)
        bevel_box(pl, T(s * 15.6, yF - 3.0), (0, -3.55, F + 26.0), (6.4, 0.3, 0.35), 'Gold', 0.05)
        dumbbell(pl, T(s * 15.6, yF - 5.9, F + 3.3) @ Matrix.Rotation(math.pi / 2, 4, 'X'), 1.1)   # wall plaque
    fin(pl)
    for s in (-1, 1):
        I('PetGym_Banner', f'PetGym_PillarBanner_{"LR"[s > 0]}', 'BANNERS', (s * 15.6, yF - 5.75, F + 21.5), 0, 1.0)
        I('PetGym_Lantern', f'PetGym_PillarLantern_{"LR"[s > 0]}', 'LIGHTING', (s * 15.6, yF - 3.0, F + 26.5), 0, 1.15)
        I('Shop_Lantern_Wall', f'PetGym_EntranceLantern_{"LR"[s > 0]}', 'LIGHTING', (s * 10.9, yF - 1.6, F + 9.0), 0, 0.9)
        I('PetGym_PetStatue', f'PetGym_Statue_{"LR"[s > 0]}', 'STATUES', (s * 19.4, -15.8, 0), -s * 0.25, 1.0)
        I('PetGym_Planter', f'PetGym_Planter_{"LR"[s > 0]}', 'LANDSCAPING', (s * 26.5, -13.2, 0), 0, 1.0)
        I('Castle_Lantern', f'PetGym_PathLantern_{"LR"[s > 0]}', 'LIGHTING', (s * 32.0, -11.0, 0), 0, 0.9)

    # ---------------- training equipment ----------------------------------------------------------------------
    Z = F + 0.2
    I('PetGym_WeightRack', 'PetGym_WeightRack_0', 'Weights', (-13.2, 2.0, Z), math.radians(90))
    I('PetGym_WeightRack', 'PetGym_WeightRack_1', 'Weights', (-13.2, 10.0, Z), math.radians(90))
    for k in range(4):                                      # plate stacks
        I('PetGym_Weight', f'PetGym_Plate_A{k}', 'Weights', (-12.4, -4.6, Z + k * 0.42), k * 0.3, 1.0 - k * 0.08)
        I('PetGym_Weight', f'PetGym_Plate_B{k}', 'Weights', (-10.0, -5.4, Z + k * 0.42), k * 0.5, 0.9 - k * 0.08)
    I('PetGym_Bench', 'PetGym_Bench_0', 'Benches', (-5.0, 16.0, Z), 0)
    I('PetGym_Barbell', 'PetGym_Barbell_0', 'Barbells', (-5.0, 17.8, Z + 4.45), 0)
    I('PetGym_Bench', 'PetGym_Bench_1', 'Benches', (-1.0, 16.0, Z), 0)
    I('PetGym_Barbell', 'PetGym_Barbell_Floor', 'Barbells', (5.2, -4.2, Z + 1.2), 0.25)
    for k, (x, y) in enumerate(((-6.6, 12.0), (-5.4, 12.6), (-12.0, 14.0))):
        I('PetGym_Dumbbell', f'PetGym_Dumbbell_{k}', 'Dumbbells', (x, y, Z), k * 0.8, 1.0)
    I('PetGym_BagFrame', 'PetGym_BagFrame', 'Bags', (12.4, 6.0, Z), math.radians(90))
    for k, y in enumerate((3.2, 8.8)):
        I('PetGym_TrainingBag', f'PetGym_TrainingBag_{k}', 'Bags', (12.4, y, Z + 9.6), k * 0.4)
    I('PetGym_PullUpBar', 'PetGym_PullUpBar', 'Training_Posts', (10.5, 16.8, Z), 0)
    I('PetGym_TrainingPost', 'PetGym_TrainingPost_0', 'Training_Posts', (12.6, -3.2, Z), math.radians(-60))
    I('PetGym_Dummy', 'PetGym_Dummy', 'Training_Posts', (8.4, -5.6, Z), math.radians(-20))
    for k, x in enumerate((-6.0, -2.5, 1.0)):              # agility: hurdles, platforms, running wheel
        I('PetGym_Hurdle', f'PetGym_Hurdle_{k}', 'Agility', (x, -5.6, Z), 0, 1.0 - 0.1 * k)
    I('PetGym_Platform', 'PetGym_Platform', 'Agility', (4.5, 15.6, Z), 0)
    I('PetGym_RunningWheel', 'PetGym_RunningWheel', 'Agility', (-11.0, 18.0, Z), math.radians(90))
    for k, (x, y, z, rz) in enumerate(((-6.0, 21.0, F + 13.0, 0), (6.0, 21.0, F + 13.0, 0),
                                       (14.6, 13.5, F + 12.0, -90), (-14.6, 6.0, F + 12.0, 90))):
        I('PetGym_PawTarget', f'PetGym_PawTarget_{k}', 'Training_Posts', (x, y, z), math.radians(rz), 1.0)
    I('PetGym_TrophyShelf', 'PetGym_TrophyShelf', 'TROPHIES', (0, 20.4, Z), 0)
    for k, x in enumerate((-1.6, 1.6)):
        I('PetGym_Trophy', f'PetGym_Trophy_{k}', 'TROPHIES', (x, 20.0, Z + 7.6), 0, 1.1)
    for k, (x, y, nm, rz, sc) in enumerate(((10.6, -7.4, 'Shop_Crate', 0.2, 1.0), (12.6, -7.4, 'Shop_Crate', -0.2, 0.9),
                                            (11.6, -7.4, 'Shop_Crate', 0.0, 0.8))):
        I(nm, f'PetGym_Crate_{k}', 'INTERIOR', (x, y, Z + (1.9 if k == 2 else 0)), rz, sc)
    for s in (-1, 1):                                       # banners + lanterns inside
        I('PetGym_Banner', f'PetGym_InteriorBanner_{"LR"[s > 0]}', 'BANNERS', (s * 14.45, 0.0, F + 19.5),
          math.radians(-90 if s > 0 else 90), 0.8)
        I('Shop_Lantern_Wall', f'PetGym_InteriorLantern_{"LR"[s > 0]}', 'LIGHTING', (s * 14.5, 16.0, F + 13.5),
          math.radians(-90 if s > 0 else 90), 0.8)
    cb = Part('PetGym_Ceiling', c('INTERIOR'))
    bevel_box(cb, I4, (0, 7.0, 21.6), (29.6, 32.0, 0.4), 'Castle_Stone_Light', 0.05)
    for y in range(-6, 22, 6):
        bevel_box(cb, I4, (0, y, 20.8), (29.6, 1.0, 1.2), 'Shop_Wood', 0.12)
    from shop import shop_lantern
    for x, y in ((-6.0, 6.0), (6.0, 6.0)):
        cb.box((x, y, 19.0), (0.15, 0.15, 2.8), 'Lantern_Metal')
        shop_lantern(cb, T(x, y, 13.4))
    fin(cb)

    # ---------------- landscaping ------------------------------------------------------------------------------
    for k, (x, y, nm, sc, rz) in enumerate((
            (-32.0, -3.0, 'Bush_02', 1.2, 0.3), (32.0, -3.0, 'Bush_01', 1.3, 0.2),
            (-31.0, 12.0, 'Tree_Medium_High', 0.85, 0.3), (31.0, 13.0, 'Tree_Small', 1.0, 1.0),
            (-30.0, 22.0, 'Bush_03', 1.1, 0.0), (30.0, 22.0, 'Ground_Plant_01', 1.3, 0.0),
            (-4.0, -19.5, 'Ground_Plant_02', 1.0, 0.0), (4.0, -19.5, 'Ground_Plant_02', 1.0, 1.0),
            (-8.0, 26.6, 'Shop_Crate', 1.0, 0.2), (8.0, 26.4, 'Shop_Barrel', 1.0, 0))):
        I(nm, f'PetGym_Land_{nm}_{k}', 'LANDSCAPING', (x, y, 0), rz, sc)
    from foliage import vine
    vv = Part('PetGym_Vines', c('LANDSCAPING'))
    for x, y, z in ((-17.1, -9.6, 21.6), (17.1, -9.6, 21.6), (-14.0, 24.5, 21.6), (13.0, 24.5, 21.6),
                    (-27.4, 17.4, 12.6), (27.4, 17.4, 12.6)):
        vine(vv, (x, y, z), rnd.uniform(6, 12), rnd, 1.1)
    fin(vv)

    # ---------------- lights --------------------------------------------------------------------------------
    for k, (x, y, z, e, col) in enumerate(((0, 6, 17, 3500, (0.85, 0.92, 1.0)), (0, 6, 6, 1200, (0.3, 0.6, 1.0)),
                                           (-9, 12, 11, 1100, (1.0, 0.72, 0.42)), (9, 12, 11, 1100, (1.0, 0.72, 0.42)),
                                           (0, -11, 12, 1500, (1.0, 0.72, 0.42)),
                                           (-15.6, -15.5, 28, 1200, (1.0, 0.7, 0.4)), (15.6, -15.5, 28, 1200, (1.0, 0.7, 0.4)))):
        L = bpy.data.lights.new(f'PetGym_Light_{k}', 'POINT')
        L.color = col; L.energy = e; L.shadow_soft_size = 1.5
        o = bpy.data.objects.new(L.name, L)
        o.location = (x, y, z); o.parent = root
        coll(c('LIGHTING')).objects.link(o)
    return root


def build_gym_cameras(root_loc=(0, 0, 0), rot_z=0.0, coll_name='CAMERAS', prefix='CAM_PetGym', only=None):
    M = Matrix.Translation(root_loc) @ Matrix.Rotation(rot_z, 4, 'Z')
    out = {}
    for name, loc, tgt, lens in (('Front', (-5, -84, 17), (0, 0, 20), 28), ('Interior', (-3, -8.5, 7.5), (1, 14, 5.5), 18),
                                 ('Side', (-64, -40, 26), (0, 4, 13), 30), ('Rear', (26, 72, 24), (0, 10, 12), 30),
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
