"""TOWER OF PETS - PET CLINIC (replaces the old Pets area), rebuilt from the Pet Clinic reference.

Layout (local space, studs, front = -Y, ground z = 0, origin = plinth centre line):
    front     light masonry facade with a wide segmental entrance arch (voussoirs, gold ring, recessed blue
              soffit), blue "PET CLINIC" sign band with gold frame and teal glow ends, tall round-topped stone
              frame above it holding the glowing paw + medical-cross emblem; two tall banner pillars with
              lanterns, two pet statues (teal bandanas) on pedestals, blue-flower planters, lantern posts
    wings     masonry with blue panels + banners, blue lean-to roofs with gold fascia
    interior  stone floor with a blue rug and paw medallion; curved reception desk (dark wood, blue panels,
              gold trim, paw-cross emblem) with supply shelves behind and room for an NPC; waiting benches and
              potted plants on the left; treatment area on the right (exam table, stool, monitor, IV stand, pet
              carrier, first-aid kit); glowing pet info screens, banners, lanterns, bowls / balls / bones
    back      masonry with a big glowing paw-cross emblem, vines, crates
Scale: entrance 20 x ~14 studs, reception desk 3.4 studs high, exam table 3 studs, walkways 4+ studs.

Collections (under the hub): PET_CLINIC / Exterior, Interior, Roof, Signage, Banners, Statues, Reception,
Treatment, Decorations, Lighting  (" (clinic)" suffix only where a name is already taken).
Kit (PETCLINIC_KIT): PetClinic_Wall, _Pillar, _Arch, _Roof, _GoldTrim, _Sign, _Emblem, _Banner, _Lantern, _Statue,
_Reception, _TreatmentTable, _Stool, _Monitor, _MedicalStand, _PetCarrier, _FirstAid, _Shelf, _Bottle, _Bench,
_InfoScreen, _PottedPlant, _FoodBowl, _Ball, _Bone, _Decorations, _Planter.
"""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
from common import (Part, MATS, mat_plain, mat_noise, coll, inst, ASSETS, empty, paw, M_front, text_mesh,
                    round_arch, pointed_arch, TAU)
from castle import (bevel_box, masonry, quoins, voussoirs, pillar, trim_run, inside, lifted, frame_strip,
                    rect_minus_arch, STONES)

ROOT = 'PET_CLINIC'
KIT = 'PETCLINIC_KIT'
I4 = Matrix.Identity(4)
FLIP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
DRAW = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))    # XY drawing -> XZ, extrude toward -y
CN = {}


def RZ(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def T(x, y, z=0.0):
    return Matrix.Translation((x, y, z))


def c(name):
    return CN.get(name, name)


# ---------------------------------------------------------------- materials -
def build_clinic_materials():
    P = mat_plain
    mat_noise('Clinic_Blue', (0.05, 0.30, 0.88), (0.08, 0.35, 0.94), 0.6, 0.25, 0.08, 2.0)
    P('Clinic_Blue_Dark', (0.03, 0.12, 0.50), 0.6)
    P('Clinic_Blue_Fabric', (0.04, 0.16, 0.62), 0.75)
    mat_noise('Clinic_Roof', (0.06, 0.30, 0.86), (0.09, 0.36, 0.92), 0.5, 0.2, 0.1, 1.5)
    P('Clinic_Roof_Dark', (0.03, 0.18, 0.60), 0.55)
    P('Clinic_White', (0.95, 0.93, 0.88), 0.5)
    P('Clinic_Teal', (0.08, 0.80, 0.72), 0.4, emit=0.8)
    P('Clinic_Teal_Cloth', (0.06, 0.72, 0.66), 0.7)
    P('Clinic_Sign_Glow', (1.0, 1.0, 1.0), 0.4, emit=1.3)
    P('Clinic_Cross', (0.15, 0.85, 1.0), 0.3, emit=1.1)
    P('Clinic_Screen', (0.10, 0.50, 1.0), 0.3, emit=0.8)
    P('Clinic_Metal', (0.76, 0.79, 0.84), 0.25, metal=0.9)
    P('Clinic_Cushion', (0.10, 0.40, 0.95), 0.7)
    P('Clinic_Red', (0.92, 0.08, 0.08), 0.5)
    mat_noise('Clinic_Floor', (0.86, 0.82, 0.76), (0.90, 0.86, 0.80), 0.6, 0.3, 0.05, 2.0)
    mat_noise('Clinic_Rug', (0.08, 0.34, 0.86), (0.10, 0.38, 0.90), 0.9, 0.6, 0.05, 3.0)
    P('Clinic_Statue', (0.80, 0.72, 0.66), 0.6)
    P('Clinic_Glass', (0.75, 0.92, 1.0), 0.05, alpha=0.5)


# ---------------------------------------------------------------- symbols ---
def paw_cross(p, M, s, depth=0.3, paw_mat='Clinic_Sign_Glow', cross_mat='Clinic_Cross'):
    """white paw with a cyan medical cross on its main pad, drawn on the local XZ plane (faces -y)"""
    paw(p, M @ DRAW, s, depth, paw_mat)
    cy = -0.16 * s
    for w, h in ((0.30 * s, 0.10 * s), (0.10 * s, 0.30 * s)):
        bevel_box(p, M, (0, -depth - 0.05, cy), (w, 0.2, h), cross_mat, 0.02)


def clinic_banner(p, M=I4, w=4.0, length=11.0):
    """deep blue banner, gold border, white paw + cyan cross, gold top bar (hangs from local origin)"""
    Mb = M @ DRAW
    o = [(-w / 2, 0), (w / 2, 0), (w / 2, -length), (0, -length - w * 0.55), (-w / 2, -length)]
    p.prism(o, -0.25, 0.0, 'Clinic_Blue_Fabric', Mb)
    edge = [(-w / 2, 0), (-w / 2, -length), (0, -length - w * 0.55), (w / 2, -length), (w / 2, 0)]
    inner = [(-w / 2 + 0.35, 0), (-w / 2 + 0.35, -length + 0.15), (0, -length - w * 0.55 + 0.5),
             (w / 2 - 0.35, -length + 0.15), (w / 2 - 0.35, 0)]
    for (a0, a1), (b0, b1) in zip(zip(edge, edge[1:]), zip(inner, inner[1:])):
        q = [a0, a1, b1, b0]
        p.hexa([Mb @ Vector((x, z, 0.0)) for x, z in q] + [Mb @ Vector((x, z, 0.18)) for x, z in q], 'Gold')
    paw_cross(p, M @ T(0, -0.0, -length * 0.5), w * 0.72, 0.25, 'Clinic_White', 'Clinic_Teal')
    bevel_box(p, M, (0, -0.3, 0.35), (w + 1.0, 0.5, 0.6), 'Gold', 0.08)
    for s in (-1, 1):
        p.ico(M @ Vector((s * (w / 2 + 0.6), -0.3, 0.35)), 0.38, 'Gold', 1)


def emblem(p, M=I4, s=1.0):
    """big medical paw emblem: rounded blue panel in a gold ring + stone frame, glowing paw + cyan cross"""
    n = 28
    def ring(r):
        return [(math.cos(TAU * i / n) * r * s, math.sin(TAU * i / n) * r * s) for i in range(n + 1)]
    frame_strip(p, M, ring(6.4), ring(5.6), -0.9, 1.0, 'Castle_Stone_Light')
    frame_strip(p, M, ring(5.7), ring(5.2), -1.3, 0.6, 'Gold')
    p.prism(ring(5.3)[:-1], 0.0, 0.8, 'Clinic_Blue', M @ FLIP)
    paw_cross(p, M @ T(0, 0.0, 0.6 * s), 7.0 * s, 0.4)


def statue(p, rnd=None):
    """friendly sitting pet statue (smooth stylised cat) with a teal bandana on a masonry pedestal"""
    rnd = rnd or random.Random(5)
    bevel_box(p, I4, (0, 0, 0.5), (6.6, 6.6, 1.0), 'Castle_Trim', 0.18)
    masonry(p, T(0, -2.7), -2.7, 2.7, 1.0, 5.0, rnd, 1.4, (1.8, 2.8), 5.4, backing=False)
    bevel_box(p, I4, (0, 0, 5.4), (6.4, 6.4, 0.8), 'Castle_Trim', 0.15)
    bevel_box(p, I4, (0, -3.25, 5.4), (5.6, 0.3, 0.3), 'Gold', 0.04)
    S, z = 'Clinic_Statue', 5.8
    p.uvsphere((0, 0.6, z + 2.6), 2.1, S, 16, 10, (1.0, 1.15, 1.25))
    for s_ in (-1, 1):
        p.uvsphere((s_ * 1.5, 1.2, z + 1.4), 1.3, S, 12, 8, (0.85, 1.3, 1.0))
        p.cyl((s_ * 0.75, -1.1, z + 1.6), 0.45, 3.2, S, 10, smooth=True)
        p.uvsphere((s_ * 0.75, -1.5, z + 0.35), 0.62, S, 10, 6, (1, 1.35, 0.6))
    p.uvsphere((0, -0.6, z + 5.7), 1.65, S, 16, 10, (1.08, 1.0, 0.95))
    p.uvsphere((0, -1.9, z + 5.2), 0.75, S, 12, 8, (1.25, 0.8, 0.72))
    p.ico((0, -2.55, z + 5.4), 0.18, 'Clinic_Blue_Dark', 1)
    for s_ in (-1, 1):
        tilt = Euler((0, s_ * 0.35, 0)).to_matrix()
        p.cyl(Vector((s_ * 1.0, -0.5, z + 7.2)) + tilt @ Vector((0, 0, 0.75)), 0.75, 1.5, S, 6, r2=0.05, rot=tilt,
              smooth=True)
        p.ico((s_ * 0.6, -2.05, z + 6.0), 0.2, 'Clinic_Blue_Dark', 1)
    # teal bandana: band + triangle flap
    p.torus((0, -0.45, z + 4.1), 1.25, 0.28, 'Clinic_Teal_Cloth', 18, 6, rot=Euler((0.3, 0, 0)).to_matrix())
    p.prism([(-1.1, 0.0), (1.1, 0.0), (0, -1.5)], 0.0, 0.25, 'Clinic_Teal_Cloth',
            T(0, -1.6, z + 4.0) @ Matrix.Rotation(-0.35, 4, 'X') @ DRAW)
    from foliage import tube
    tube(p, [Vector((1.4, 2.0, z + 0.6)), Vector((2.4, 0.6, z + 0.4)), Vector((2.2, -1.2, z + 0.5)),
             Vector((1.4, -2.0, z + 0.6))], [0.5, 0.45, 0.38, 0.25], S, 6)


# ---------------------------------------------------------------- props -----
def reception(p):
    """curved reception desk: dark wood, blue panels, gold trim, paw-cross emblem; 3.4 studs high"""
    for x0, x1, ang in ((-8.0, -5.0, 22), (-5.0, 5.0, 0), (5.0, 8.0, -22)):
        cx = (x0 + x1) / 2
        M = T(cx, 0.5 if ang else 0) @ RZ(ang)
        L = (x1 - x0) / math.cos(math.radians(ang))
        bevel_box(p, M, (0, 0, 1.6), (L, 2.2, 3.2), 'Interior_Wood', 0.12)
        nseg = max(1, int(L / 2.0))
        for k in range(nseg):
            x = -L / 2 + (k + 0.5) * L / nseg
            bevel_box(p, M, (x, -1.15, 1.6), (L / nseg - 0.45, 0.2, 2.0), 'Clinic_Blue', 0.08)
        bevel_box(p, M, (0, -0.2, 3.35), (L + 0.4, 2.8, 0.3), 'Shop_Wood', 0.08)
        bevel_box(p, M, (0, -1.55, 3.35), (L + 0.4, 0.12, 0.36), 'Gold', 0.04)
        bevel_box(p, M, (0, -1.2, 0.2), (L, 0.3, 0.4), 'Gold', 0.04)
    p.cyl((0, -1.4, 1.7), 1.0, 0.2, 'Clinic_Blue_Dark', 20, axis='Y')
    p.torus((0, -1.5, 1.7), 1.0, 0.08, 'Gold', 20, 4, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
    paw_cross(p, T(0, -1.55, 1.75), 1.4, 0.08)
    bevel_box(p, I4, (0, 2.8, 1.0), (15, 1.0, 2.0), 'Interior_Wood', 0.1)          # NPC-side under-shelf
    # little bell + computer screen on top
    p.cyl((4.2, 0.0, 3.6), 0.35, 0.2, 'Gold', 10)
    p.uvsphere((4.2, 0.0, 3.75), 0.3, 'Gold', 10, 5, (1, 1, 0.7))
    bevel_box(p, I4, (-3.0, 0.4, 4.6), (2.4, 0.2, 1.6), 'Clinic_Blue_Dark', 0.05)
    bevel_box(p, I4, (-3.0, 0.28, 4.6), (2.1, 0.05, 1.3), 'Clinic_Screen', 0.02)
    p.box((-3.0, 0.5, 3.8), (0.3, 0.3, 0.6), 'Clinic_Metal')


def treatment_table(p):
    """padded pet exam table on steel legs (top at 3 studs)"""
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.cyl((sx * 2.2, sy * 1.1, 1.3), 0.15, 2.6, 'Clinic_Metal', 8)
    bevel_box(p, I4, (0, 0, 2.7), (5.2, 2.8, 0.3), 'Clinic_Metal', 0.06)
    bevel_box(p, I4, (0, 0, 3.05), (5.0, 2.6, 0.45), 'Clinic_Cushion', 0.2)
    bevel_box(p, I4, (-1.9, 0, 3.35), (1.2, 2.2, 0.3), 'Clinic_White', 0.12)          # pillow
    bevel_box(p, I4, (0, 0, 0.6), (4.6, 2.4, 0.15), 'Clinic_Metal', 0.03)          # lower shelf
    bevel_box(p, I4, (1.2, 0.2, 0.9), (1.6, 1.0, 0.5), 'Clinic_White', 0.08)          # folded towel


def stool(p):
    p.cyl((0, 0, 0.1), 0.9, 0.2, 'Clinic_Metal', 12)
    p.cyl((0, 0, 1.0), 0.15, 1.8, 'Clinic_Metal', 8)
    p.cyl((0, 0, 2.0), 0.95, 0.35, 'Clinic_Cushion', 16, smooth=True)


def monitor(p):
    """medical monitor on a rolling stand with a paw on the screen"""
    p.cyl((0, 0, 0.1), 1.0, 0.2, 'Clinic_Metal', 5)
    p.cyl((0, 0, 2.4), 0.12, 4.4, 'Clinic_Metal', 8)
    bevel_box(p, I4, (0, 0, 4.9), (2.6, 0.4, 1.9), 'Clinic_White', 0.12)
    bevel_box(p, I4, (0, -0.22, 4.9), (2.2, 0.05, 1.5), 'Clinic_Screen', 0.02)
    paw(p, M_front(0, -0.26, 4.95), 0.9, 0.04, 'Clinic_Sign_Glow')
    for k in range(5):                                         # heartbeat line
        p.box((-0.9 + k * 0.45, -0.27, 4.4 + (0.2 if k % 2 else 0.0)), (0.4, 0.04, 0.06), 'Clinic_Teal')


def medical_stand(p):
    """IV / drip stand with a bag and tube"""
    for k in range(5):
        a = TAU * k / 5
        p.beam(Vector((0, 0, 0.3)), Vector((math.cos(a) * 0.9, math.sin(a) * 0.9, 0.05)), 0.12, 0.12, 'Clinic_Metal')
    p.cyl((0, 0, 3.2), 0.08, 6.2, 'Clinic_Metal', 8)
    p.beam(Vector((-0.6, 0, 6.2)), Vector((0.6, 0, 6.2)), 0.08, 0.08, 'Clinic_Metal')
    bevel_box(p, I4, (0.5, 0, 5.4), (0.7, 0.3, 1.1), 'Clinic_Glass', 0.12)
    p.box((0.5, 0, 5.2), (0.5, 0.25, 0.6), 'Clinic_Teal')
    p.beam(Vector((0.5, 0, 4.8)), Vector((0.9, -0.3, 2.6)), 0.05, 0.05, 'Clinic_Glass')


def pet_carrier(p):
    bevel_box(p, I4, (0, 0, 1.1), (3.0, 2.0, 2.2), 'Clinic_White', 0.25)
    bevel_box(p, I4, (0, 0, 1.8), (3.1, 2.1, 0.25), 'Clinic_Blue', 0.06)
    for k in range(5):                                         # grille door
        p.box((-0.8 + k * 0.4, -1.03, 1.0), (0.1, 0.1, 1.4), 'Clinic_Metal')
    p.box((0, -1.03, 1.72), (1.8, 0.1, 0.12), 'Clinic_Metal')
    p.box((0, -1.03, 0.3), (1.8, 0.1, 0.12), 'Clinic_Metal')
    p.torus((0, 0, 2.45), 0.6, 0.12, 'Clinic_Blue_Dark', 12, 4, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))


def first_aid(p):
    bevel_box(p, I4, (0, 0, 0.6), (1.8, 0.9, 1.2), 'Clinic_Red', 0.12)
    for w, h in ((0.8, 0.25), (0.25, 0.8)):
        p.box((0, -0.47, 0.6), (w, 0.05, h), 'Clinic_White')
    p.torus((0, 0, 1.3), 0.4, 0.08, 'Clinic_White', 10, 4, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))


def shelf(p):
    """white/wood supply shelf with blue doors at the bottom (bottles are separate instances)"""
    w, d, h = 5.6, 1.6, 8.0
    for s in (-1, 1):
        bevel_box(p, I4, (s * (w / 2 - 0.25), 0, h / 2), (0.5, d, h), 'Shop_Wood', 0.1)
    bevel_box(p, I4, (0, d / 2 - 0.15, h / 2), (w, 0.3, h), 'Clinic_White', 0.05)
    for z in (0.4, 3.2, 5.2, 7.2):
        bevel_box(p, I4, (0, 0, z), (w - 0.5, d, 0.25), 'Shop_Wood', 0.05)
    for s in (-1, 1):
        bevel_box(p, I4, (s * 1.2, -0.75, 1.8), (2.3, 0.15, 2.4), 'Clinic_Blue', 0.06)
        p.ico((s * 0.3, -0.85, 1.8), 0.12, 'Gold', 1)
    bevel_box(p, I4, (0, -0.1, h + 0.25), (w + 0.4, d + 0.3, 0.5), 'Shop_Wood', 0.1)
    bevel_box(p, I4, (0, -0.85, h + 0.25), (w + 0.2, 0.08, 0.2), 'Gold', 0.02)


SHELF_Z = (3.35, 5.35, 7.35)


def bottle(p, mat='Clinic_Teal'):
    p.cyl((0, 0, 0.4), 0.32, 0.8, 'Clinic_White', 10)
    p.box((0, -0.3, 0.45), (0.4, 0.04, 0.3), mat)
    p.cyl((0, 0, 0.95), 0.18, 0.3, mat, 8)


def bench(p):
    for x in (-2.4, 2.4):
        bevel_box(p, I4, (x, 0, 0.8), (0.5, 2.0, 1.6), 'Shop_Wood', 0.08)
    bevel_box(p, I4, (0, 0, 1.75), (5.6, 2.2, 0.3), 'Shop_Wood', 0.08)
    bevel_box(p, I4, (0, -0.1, 2.1), (5.2, 1.9, 0.45), 'Clinic_Cushion', 0.18)
    bevel_box(p, I4, (0, 0.95, 3.1), (5.6, 0.3, 2.4), 'Shop_Wood', 0.08)
    bevel_box(p, I4, (0, 0.75, 3.1), (5.2, 0.35, 1.9), 'Clinic_Cushion', 0.15)


def info_screen(p):
    """glowing pet information screen (cat + dog silhouettes, cross) in a white frame (faces -y)"""
    bevel_box(p, I4, (0, 0.15, 0), (5.2, 0.3, 3.6), 'Clinic_White', 0.12)
    bevel_box(p, I4, (0, -0.05, 0), (4.7, 0.1, 3.1), 'Clinic_Screen', 0.03)
    S = 'Clinic_Sign_Glow'
    for cx, big in ((-1.0, True), (1.2, False)):               # simple pet silhouettes
        r = 0.55 if big else 0.42
        p.uvsphere((cx, -0.15, -0.4), r * 1.3, S, 10, 6, (1, 0.25, 0.8))
        p.uvsphere((cx + r * 0.9, -0.15, 0.25), r * 0.75, S, 10, 6, (1, 0.25, 1))
        for s in (-1, 1):
            p.cone((cx + r * 0.9 + s * r * 0.4, -0.15, 0.25 + r * 0.5), r * 0.25, r * 0.6, S, 4)
    for w, h in ((0.9, 0.3), (0.3, 0.9)):
        p.box((1.7, -0.15, 1.0), (w, 0.08, h), 'Clinic_Teal')


def potted_plant(p, rnd=None):
    from foliage import leaf_cluster
    rnd = rnd or random.Random(4)
    p.cyl((0, 0, 0.7), 0.9, 1.4, 'Clinic_White', 12, r2=1.15)
    p.torus((0, 0, 1.35), 1.12, 0.1, 'Clinic_Blue', 16, 4)
    p.cyl((0, 0, 2.6), 0.15, 2.4, 'Trunk', 6)
    leaf_cluster(p, (0, 0, 4.2), 1.4, rnd, 18, squash=0.9)


def food_bowl(p, mat='Clinic_Red'):
    p.cyl((0, 0, 0.25), 0.8, 0.5, mat, 14, r2=1.0)
    p.cyl((0, 0, 0.45), 0.75, 0.1, 'Shop_Wood', 14)


def ball(p, mat='Clinic_Blue'):
    p.uvsphere((0, 0, 0.45), 0.45, mat, 12, 8)
    p.torus((0, 0, 0.45), 0.45, 0.06, 'Clinic_White', 14, 4, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))


def bone(p):
    p.cyl((0, 0, 0.25), 0.18, 1.6, 'Clinic_White', 8, axis='X')
    for s in (-1, 1):
        for d in (-0.18, 0.18):
            p.ico((s * 0.85, d, 0.25), 0.26, 'Clinic_White', 1)


def decorations(p):
    """grouped small pet props (bowl, balls, bone, brush) - also available individually"""
    food_bowl(p)
    for dx, m in ((1.6, 'Clinic_Blue'), (2.6, 'Clinic_Teal')):
        p.uvsphere((dx, 0.4, 0.45), 0.45, m, 12, 8)
    p.cyl((-1.6, 0.6, 0.25), 0.18, 1.6, 'Clinic_White', 8, axis='X')
    bevel_box(p, I4, (0.4, -1.4, 0.2), (1.6, 0.6, 0.3), 'Shop_Wood', 0.08)              # brush
    for k in range(6):
        p.box((-0.2 + k * 0.25, -1.4, 0.45), (0.08, 0.4, 0.2), 'Clinic_White')


def planter(p, rnd, w=6.0, d=3.6):
    from foliage import leaf_cluster
    masonry(p, T(0, -d / 2), -w / 2, w / 2, 0, 2.0, rnd, 1.0, (1.6, 2.4), d - 0.4, backing=False)
    bevel_box(p, I4, (0, 0, 2.2), (w + 0.5, d + 0.5, 0.4), 'Castle_Trim', 0.1)
    p.box((0, 0, 2.3), (w - 0.6, d - 0.6, 0.2), 'Dirt')
    for k in range(3):
        x = -w / 2 + 1.2 + k * (w - 2.4) / 2
        leaf_cluster(p, (x, rnd.uniform(-0.4, 0.4), 3.2), 1.2, rnd, 14, squash=0.8)
        for j in range(4):                                     # blue flowers
            a = TAU * j / 4 + k
            p.ico((x + math.cos(a) * 0.9, math.sin(a) * 0.9, 3.9 + rnd.uniform(-0.2, 0.3)), 0.32, 'Clinic_Cushion', 1)
            p.ico((x + math.cos(a) * 0.9, math.sin(a) * 0.9, 4.15), 0.12, 'Clinic_White', 1)


def _lib(name, builder, *a, **kw):
    p = Part('ASSET_' + name, KIT)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def build_clinic_kit(parent):
    from shop import shop_lantern, roof_slope
    coll(KIT, parent)
    R = random.Random
    _lib('PetClinic_Wall', lambda p: masonry(p, I4, -6, 6, 0, 10, R(1), 2.5, (3, 5)))
    _lib('PetClinic_Pillar', lambda p: pillar(p, I4, 5.0, 0, 22, R(2), cap=None, band=0.55))
    _lib('PetClinic_Arch', lambda p: voussoirs(p, I4, lifted(round_arch(16, 3, 14), 0, 0), lifted(round_arch(12, 3, 14), 0, 0),
                                               -0.6, 1.6, R(3), 2.4))
    _lib('PetClinic_Roof', lambda p: roof_slope(p, I4, 0, 8, 0, 4.0, -4, 4, 0.5, mat='Clinic_Roof',
                                                course_mat='Clinic_Roof_Dark'))
    _lib('PetClinic_GoldTrim', lambda p: bevel_box(p, I4, (0, 0, 0.2), (8, 0.35, 0.4), 'Gold', 0.06))
    def sign(p):
        bevel_box(p, I4, (0, 0.4, 2.4), (14, 0.8, 4.2), 'Clinic_Blue_Dark', 0.1)
        frame_strip(p, I4, [(-7.4, 0.0), (-7.4, 4.8), (7.4, 4.8), (7.4, 0.0), (-7.4, 0.0)],
                    [(-7.0, 0.4), (-7.0, 4.4), (7.0, 4.4), (7.0, 0.4), (-7.0, 0.4)], -0.5, 0.3, 'Gold')
    _lib('PetClinic_Sign', sign)
    _lib('PetClinic_Emblem', lambda p: emblem(p, T(0, 0, 6.5), 1.0))
    _lib('PetClinic_Banner', clinic_banner)
    _lib('PetClinic_Lantern', shop_lantern)
    _lib('PetClinic_Statue', statue)
    _lib('PetClinic_Reception', reception)
    _lib('PetClinic_TreatmentTable', treatment_table)
    _lib('PetClinic_Stool', stool)
    _lib('PetClinic_Monitor', monitor)
    _lib('PetClinic_MedicalStand', medical_stand)
    _lib('PetClinic_PetCarrier', pet_carrier)
    _lib('PetClinic_FirstAid', first_aid)
    _lib('PetClinic_Shelf', shelf)
    _lib('PetClinic_Bottle', bottle, 'Clinic_Teal')
    _lib('PetClinic_Bottle_Blue', bottle, 'Clinic_Cushion')
    _lib('PetClinic_Bench', bench)
    _lib('PetClinic_InfoScreen', info_screen)
    _lib('PetClinic_PottedPlant', potted_plant)
    _lib('PetClinic_FoodBowl', food_bowl)
    _lib('PetClinic_Ball', ball)
    _lib('PetClinic_Bone', bone)
    _lib('PetClinic_Decorations', decorations)
    _lib('PetClinic_Planter', planter, R(5))


# ---------------------------------------------------------------- build -----
def subcolls(parent):
    CN.clear()
    coll(ROOT, parent)
    for name in ('Exterior', 'Interior', 'Roof', 'Signage', 'Banners', 'Statues', 'Reception', 'Treatment',
                 'Decorations', 'Lighting'):
        from hatchery import RESERVED
        taken = name in bpy.data.collections or name in RESERVED
        actual = f'{name} (clinic)' if taken else name
        CN[name] = actual
        coll(actual, ROOT)


def build_clinic(parent_coll, loc=(0, 0, 0), rot_z=0.0):
    from shop import roof_slope
    subcolls(parent_coll)
    root = empty('PetClinic_Root', ROOT, loc, rot_z, 8)
    rnd = random.Random(2468)
    F = 1.0

    def fin(p):
        return p.finish(parent=root)

    def I(asset, name, col, xyz, rz=0.0, s=1.0):
        return inst(asset, name, c(col), xyz, rz, s, root)

    # ---------------- plinth + floor ------------------------------------------------------------------
    p = Part('PetClinic_Floor', c('Exterior'))
    bevel_box(p, I4, (0, 3, F / 2), (54, 34, F), 'Castle_Trim', 0.2)
    for i in range(2):
        bevel_box(p, I4, (0, -14.7 - i * 1.4, (F - i * 0.5) / 2), (24 - i * 2, 1.4, F - i * 0.5), 'Castle_Stone_Light', 0.12)
    for i in range(8):
        for j in range(7):
            x = -14.5 + (i + 0.5) * 29 / 8
            y = -8.8 + (j + 0.5) * 26 / 7
            bevel_box(p, I4, (x, y, F + 0.1), (29 / 8 - 0.12, 26 / 7 - 0.12, 0.2),
                      ('Clinic_Floor', 'Castle_Stone_Light')[(i + j) % 2], 0.05)
    # blue rug with the paw medallion (cyan glowing ring)
    bevel_box(p, I4, (0, -2.0, F + 0.25), (14, 9.0, 0.12), 'Clinic_Rug', 0.05)
    for s in (-1, 1):
        bevel_box(p, I4, (s * 6.6, -2.0, F + 0.33), (0.3, 8.4, 0.05), 'Clinic_White', 0.01)
        bevel_box(p, I4, (0, -2.0 + s * 4.1, F + 0.33), (13.2, 0.3, 0.05), 'Clinic_White', 0.01)
    p.cyl((0, -2.0, F + 0.33), 3.2, 0.06, 'Clinic_White', 28)
    p.torus((0, -2.0, F + 0.37), 3.0, 0.1, 'Clinic_Teal', 32, 4)
    paw(p, T(0, -1.7, F + 0.36), 3.6, 0.05, 'Clinic_Blue')
    fin(p)

    # ---------------- hall walls ---------------------------------------------------------------------
    w = Part('PetClinic_Hall_Walls', c('Exterior'))
    yF = -9.0
    w.box((0, 17.6, (F + 21) / 2), (33, 2.4, 21 - F), 'Castle_Seam')
    masonry(w, T(0, 19.0) @ RZ(180), -16.5, 16.5, F, 21.0, rnd, 2.4, (3, 5.5), 1.6,
            skip=lambda x, z, ww, h: (x * x) / 64 + ((z - 12.5) ** 2) / 64 < 1.0, backing=False)
    for s in (-1, 1):
        w.box((s * 15.8, 4.5, (F + 21) / 2), (2.0, 27, 21 - F), 'Castle_Seam')
        xr = (-9.0, 18.0) if s > 0 else (-18.0, 9.0)
        masonry(w, T(s * 16.9, 0) @ RZ(s * 90), xr[0], xr[1], 12.0, 21.0, rnd, 2.4, (3, 5.5), 1.6, backing=False)
        quoins(w, T(s * 16.9, 19.0) @ RZ(180), F, 21.0, rnd, 3.4, 2.0, 2.4, side=s, mat='Castle_Trim')
    # interior: light plaster with blue wainscot, gold rail, white cornice
    for s in (-1, 1):
        bevel_box(w, I4, (s * 14.7, 4.5, F + 10), (0.3, 27, 20), 'Clinic_White', 0.05)
        bevel_box(w, I4, (s * 14.5, 4.5, F + 2.0), (0.3, 27, 4.0), 'Clinic_Blue', 0.05)
        bevel_box(w, I4, (s * 14.4, 4.5, F + 4.1), (0.3, 27, 0.25), 'Gold', 0.03)
        bevel_box(w, I4, (s * 14.4, 4.5, F + 19.4), (0.6, 27, 0.8), 'Castle_Trim', 0.08)
    bevel_box(w, I4, (0, 16.3, F + 10), (29, 0.3, 20), 'Clinic_White', 0.05)
    bevel_box(w, I4, (0, 16.1, F + 2.0), (29, 0.3, 4.0), 'Clinic_Blue', 0.05)
    bevel_box(w, I4, (0, 16.0, F + 4.1), (29, 0.3, 0.25), 'Gold', 0.03)
    # back-wall feature: big glowing paw-cross panel behind the desk (inside)
    w.cyl((0, 16.0, F + 12.0), 4.4, 0.3, 'Clinic_Blue', 28, axis='Y')
    w.torus((0, 15.8, F + 12.0), 4.4, 0.25, 'Gold', 32, 6, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
    paw_cross(w, T(0, 15.8, F + 12.3), 5.4, 0.25)
    fin(w)
    # back exterior emblem (big glowing paw-cross in a round stone frame)
    be = Part('PetClinic_Back_Emblem', c('Signage'))
    emblem(be, T(0, 19.6, F + 12.0) @ RZ(180), 1.15)
    fin(be)

    # ---------------- wings -----------------------------------------------------------------------------
    wg = Part('PetClinic_Wings', c('Exterior'))
    WT = 13.0
    for s in (-1, 1):
        x0, x1 = (17.0, 26.0) if s > 0 else (-26.0, -17.0)
        wg.box(((x0 + x1) / 2, 4.0, (F + WT) / 2), (x1 - x0, 22, WT - F), 'Castle_Seam')
        xr = (-7.0, 15.0) if s > 0 else (-15.0, 7.0)
        masonry(wg, T(s * 26.1, 0) @ RZ(s * 90), xr[0], xr[1], F, WT, rnd, 2.4, (3, 5.5), 1.6, backing=False)
        masonry(wg, T(0, 15.1) @ RZ(180), -x1, -x0, F, WT, rnd, 2.4, (3, 5.5), 1.6, backing=False)
        quoins(wg, T(s * 26.1, 15.1) @ RZ(180), F, WT, rnd, 3.4, 2.0, 2.4, side=s, mat='Castle_Trim')
        # front: masonry with a blue panel + banner
        masonry(wg, T(0, -7.1), x0, x1, F, WT, rnd, 2.4, (3, 5.5), 1.6,
                skip=lambda x, z, ww, h, s=s: abs(x - s * 21.6) < 3.4 and z < F + 11.4, backing=False)
        bevel_box(wg, I4, (s * 21.6, -6.6, F + 5.7), (6.4, 0.6, 10.4), 'Clinic_Blue', 0.08)
        frame_strip(wg, T(s * 21.6, -7.0), [(-3.5, F), (-3.5, F + 11.2), (3.5, F + 11.2), (3.5, F)],
                    [(-3.15, F), (-3.15, F + 10.85), (3.15, F + 10.85), (3.15, F)], -0.5, 0.3, 'Gold')
        quoins(wg, T(s * 26.1, -7.1), F, WT, rnd, 3.4, 2.0, 2.4, side=-s, mat='Castle_Trim')
        trim_run(wg, T(0, -7.4), x0, x1, WT - 1.6, h=1.6, out=1.0)
        pillar(wg, T(s * 26.0, -7.6), 3.4, 0, WT + 2.6, rnd, cap=None, band=0.5, panel=False)
    fin(wg)
    for s in (-1, 1):
        I('PetClinic_Banner', f'PetClinic_WingBanner_{"LR"[s > 0]}', 'Banners', (s * 21.6, -7.0, F + 10.4), 0, 0.85)
        I('PetClinic_Lantern', f'PetClinic_WingLantern_{"LR"[s > 0]}', 'Exterior', (s * 26.0, -7.6, WT + 2.4), 0, 1.1)

    # ---------------- front facade, arch, sign, emblem tower ----------------------------------------
    fa = Part('PetClinic_Facade', c('Exterior'))
    AW, AS = 20.0, 9.0                                    # opening width, spring height above the floor
    seg_i = [(x, F + AS + 3.2 * (1 - (x / (AW / 2)) ** 2)) for x in [-AW / 2 + AW * i / 14 for i in range(15)]]
    seg_o = [(x, F + AS + 2.8 + 3.6 * (1 - (x / (AW / 2 + 2.6)) ** 2)) for x in
             [-(AW / 2 + 2.6) + (AW + 5.2) * i / 14 for i in range(15)]]
    opening = [(-AW / 2, F)] + seg_i + [(AW / 2, F)]
    outer_poly = [(-AW / 2 - 2.6, F)] + seg_o + [(AW / 2 + 2.6, F)]
    masonry(fa, T(0, yF), -17.0, 17.0, F, 21.0, rnd, 2.6, (3.2, 5.5), 1.6,
            skip=lambda x, z, ww, h: inside(outer_poly, x, z), backing=False)
    rect_minus_arch(fa, T(0, yF), -17.0, 17.0, F, 21.0, opening, 1.0, 2.0, 'Castle_Seam')
    voussoirs(fa, T(0, yF), [(-AW / 2 - 2.6, F + AS + 2.8)] + seg_o[1:-1] + [(AW / 2 + 2.6, F + AS + 2.8)],
              [(-AW / 2, F + AS)] + seg_i[1:-1] + [(AW / 2, F + AS)], -1.4, 1.2, rnd, 2.4)
    for s in (-1, 1):                                     # jambs below the arch springing
        for k in range(3):
            bevel_box(fa, T(0, yF), (s * (AW / 2 + 1.3), 0.0, F + k * 3.0 + 1.5), (2.6, 2.6, 2.9), 'Castle_Stone_Light', 0.2)
    frame_strip(fa, T(0, yF), seg_i, [(x, z - 0.6) for x, z in seg_i], -0.6, 1.2, 'Gold')
    # blue soffit / canopy just inside the arch
    fa.box((0, yF + 3.0, F + AS + 3.0), (AW, 4.0, 0.6), 'Clinic_Blue')
    trim_run(fa, T(0, yF), -17, 17, F, h=1.2, out=1.0)
    quoins(fa, T(-17.0, yF), F, 21.0, rnd, 3.4, 2.0, 2.6, side=1, mat='Castle_Trim')
    quoins(fa, T(17.0, yF), F, 21.0, rnd, 3.4, 2.0, 2.6, side=-1, mat='Castle_Trim')
    # emblem tower above the sign: round-topped masonry frame
    tower = [(-10.0, 21.0)] + [(10.0 * math.cos(math.pi - math.pi * i / 16), 31.0 + 6.0 * math.sin(math.pi * i / 16))
                               for i in range(17)] + [(10.0, 21.0)]
    masonry(fa, T(0, yF - 0.8), -10.0, 10.0, 21.0, 37.2, rnd, 2.4, (3, 5), 2.2,
            skip=lambda x, z, ww, h: not inside(tower, x, z), backing=False)
    fa.prism(tower, 0.0, 2.0, 'Castle_Seam', T(0, yF - 0.5) @ FLIP)
    fa.prism(tower, 2.0, 2.6, 'Castle_Stone_Light', T(0, yF - 0.5) @ FLIP)          # finished back face
    frame_strip(fa, T(0, yF - 1.4), tower[1:-1], [(x * 0.9, 31.0 + (z - 31.0) * 0.9) for x, z in tower[1:-1]],
                -0.8, 0.6, 'Castle_Trim')
    frame_strip(fa, T(0, yF - 1.9), [(x * 0.9, 31.0 + (z - 31.0) * 0.9) for x, z in tower[1:-1]],
                [(x * 0.86, 31.0 + (z - 31.0) * 0.86) for x, z in tower[1:-1]], -0.4, 0.4, 'Gold')
    fa.ico((0, yF - 1.4, 38.0), 0.8, 'Gold', 1)
    fa.cone((0, yF - 1.4, 37.0), 0.7, 1.4, 'Gold', 6)
    for s in (-1, 1):                                     # gold scroll brackets
        fa.torus((s * 10.6, yF - 1.6, 23.5), 1.2, 0.3, 'Gold', 14, 6, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
    fin(fa)
    sg = Part('PetClinic_Sign', c('Signage'))
    Ms = T(0, yF - 2.4, 16.8)
    bevel_box(sg, Ms, (0, 0.4, 2.4), (20.4, 0.8, 4.6), 'Clinic_Blue_Dark', 0.1)
    frame_strip(sg, Ms, [(-10.6, 0.0), (-10.6, 5.0), (10.6, 5.0), (10.6, 0.0), (-10.6, 0.0)],
                [(-10.2, 0.4), (-10.2, 4.6), (10.2, 4.6), (10.2, 0.4), (-10.2, 0.4)], -0.5, 0.3, 'Gold')
    for s in (-1, 1):                                     # teal glow end panels
        bevel_box(sg, Ms, (s * 11.5, 0.2, 2.5), (1.4, 0.8, 5.6), 'Clinic_Teal', 0.15)
        bevel_box(sg, Ms, (s * 11.5, -0.3, 2.5), (1.8, 0.3, 6.2), 'Gold', 0.08)
    fin(sg)
    text_mesh('PetClinic_Sign_Text', 'PET CLINIC', c('Signage'), 2.9, 0.5, 'Clinic_Sign_Glow', (0, yF - 3.1, 19.15), 0, root)
    em = Part('PetClinic_Emblem', c('Signage'))
    emblem(em, T(0, yF - 2.2, 29.6), 1.05)
    fin(em)

    # ---------------- roofs -------------------------------------------------------------------------------
    rf = Part('PetClinic_Roofs', c('Roof'))
    ze, zr = 21.6, 29.0
    for s in (-1, 1):                                     # hall gable roof (behind the emblem tower)
        roof_slope(rf, I4 if s > 0 else Matrix.Scale(-1, 4, Vector((1, 0, 0))), 18.2, 0.0, ze - 0.6, zr, yF + 0.6,
                   20.0, 0.8, mat='Clinic_Roof', sag=0.5, course_mat='Clinic_Roof_Dark')
        bevel_box(rf, I4, (s * 18.3, 5.3, ze - 0.7), (0.5, 19.6, 0.6), 'Gold', 0.06)
    bevel_box(rf, I4, (0, 5.3, zr + 0.6), (1.6, 19.6, 1.2), 'Clinic_Roof_Dark', 0.2)
    rf.prism([(-16.5, 21.0), (16.5, 21.0), (0, zr - 0.2)], 18.0, 19.4, 'Clinic_Blue', FLIP)   # back gable
    for s in (-1, 1):                                     # wing lean-to roofs + front canopy roofs
        Mw = I4 if s > 0 else Matrix.Scale(-1, 4, Vector((1, 0, 0)))
        roof_slope(rf, Mw, 27.6, 16.9, WT + 0.2, 19.2, -9.6, 16.6, 0.7, mat='Clinic_Roof', sag=0.35,
                   course_mat='Clinic_Roof_Dark')
        bevel_box(rf, I4, (s * 27.7, 3.5, WT + 0.15), (0.5, 26.2, 0.55), 'Gold', 0.06)
        ang = math.atan2(19.2 - WT, 10.7)
        Mr = T(s * 22.25, -9.7, (WT + 19.2) / 2 + 0.2) @ Matrix.Rotation(s * ang, 4, 'Y')
        bevel_box(rf, Mr, (0, 0, 0), (math.hypot(10.7, 19.2 - WT) + 0.4, 0.5, 0.55), 'Gold', 0.06)
    fin(rf)

    # ---------------- big pillars, banners, lanterns, statues ---------------------------------------
    pl = Part('PetClinic_Pillars', c('Exterior'))
    for s in (-1, 1):
        pillar(pl, T(s * 15.4, yF - 3.0), 5.4, F, 23.0, rnd, cap=None, band=0.56)
        bevel_box(pl, T(s * 15.4, yF - 3.0), (0, 0, F + 25.0), (7.0, 7.0, 1.0), 'Castle_Trim', 0.15)
        bevel_box(pl, T(s * 15.4, yF - 3.0), (0, -3.55, F + 25.0), (6.4, 0.3, 0.35), 'Gold', 0.05)
        bevel_box(pl, T(s * 15.4, yF - 3.0), (0, -2.75, F + 4.0), (2.4, 0.3, 2.4), 'Gold', 0.05)
        paw(pl, M_front(s * 15.4, yF - 5.9, F + 3.8), 1.6, 0.1, 'Clinic_Blue_Dark')
    fin(pl)
    for s in (-1, 1):
        I('PetClinic_Banner', f'PetClinic_PillarBanner_{"LR"[s > 0]}', 'Banners', (s * 15.4, yF - 5.75, F + 20.5), 0, 1.1)
        I('PetClinic_Lantern', f'PetClinic_PillarLantern_{"LR"[s > 0]}', 'Exterior', (s * 15.4, yF - 3.0, F + 25.5), 0, 1.15)
        I('Shop_Lantern_Wall', f'PetClinic_EntranceLantern_{"LR"[s > 0]}', 'Exterior', (s * 11.0, yF - 1.4, F + 9.4), 0, 0.9)
        I('PetClinic_Statue', f'PetClinic_Statue_{"LR"[s > 0]}', 'Statues', (s * 18.8, -15.6, 0), -s * 0.25, 1.0)
        I('PetClinic_Planter', f'PetClinic_Planter_{"LR"[s > 0]}', 'Exterior', (s * 26.0, -13.2, 0), 0, 1.0)
        I('Castle_Lantern', f'PetClinic_PathLantern_{"LR"[s > 0]}', 'Exterior', (s * 31.5, -11.0, 0), 0, 0.9)

    # ---------------- interior: reception, shelves, waiting, treatment ---------------------------------
    I('PetClinic_Reception', 'PetClinic_Reception', 'Reception', (0, 8.0, F + 0.2))
    for k, x in enumerate((-9.0, 9.0)):
        I('PetClinic_Shelf', f'PetClinic_Shelf_{k}', 'Reception', (x, 15.2, F + 0.2))
        for lv, z in enumerate(SHELF_Z):
            for j in range(4):
                nm = ('PetClinic_Bottle', 'PetClinic_Bottle_Blue', 'PetClinic_FirstAid', 'PetClinic_Bottle')[(j + lv + k) % 4]
                sc = 0.45 if 'FirstAid' in nm else 0.9
                I(nm, f'PetClinic_ShelfItem_{k}{lv}{j}', 'Reception', (x - 1.8 + j * 1.2, 15.0, F + 0.2 + z + 0.15), 0, sc)
    # waiting area (left): benches facing the room, plants, info screen
    for k, y in enumerate((-4.5, 3.5)):
        I('PetClinic_Bench', f'PetClinic_Bench_{k}', 'Decorations', (-12.6, y, F + 0.2), math.radians(90), 1.0)
    I('PetClinic_PottedPlant', 'PetClinic_Plant_0', 'Decorations', (-13.2, -0.5, F + 0.2), 0, 1.0)
    I('PetClinic_PottedPlant', 'PetClinic_Plant_1', 'Decorations', (-13.2, 9.5, F + 0.2), 0.7, 1.1)
    I('PetClinic_InfoScreen', 'PetClinic_InfoScreen_L', 'Decorations', (-14.3, 0.0, F + 9.5), math.radians(90), 1.1)
    # treatment area (right)
    I('PetClinic_TreatmentTable', 'PetClinic_TreatmentTable', 'Treatment', (10.6, 0.5, F + 0.2), math.radians(90))
    I('PetClinic_Stool', 'PetClinic_Stool', 'Treatment', (7.6, 0.0, F + 0.2))
    I('PetClinic_Monitor', 'PetClinic_Monitor', 'Treatment', (12.8, -3.6, F + 0.2), math.radians(-110))
    I('PetClinic_MedicalStand', 'PetClinic_MedicalStand', 'Treatment', (12.8, 4.2, F + 0.2), math.radians(-90))
    I('PetClinic_PetCarrier', 'PetClinic_PetCarrier', 'Treatment', (11.6, -6.6, F + 0.2), math.radians(-70))
    I('PetClinic_FirstAid', 'PetClinic_FirstAid_Table', 'Treatment', (11.6, 2.4, F + 0.2 + 3.3), math.radians(-90), 0.5)
    I('PetClinic_InfoScreen', 'PetClinic_InfoScreen_R', 'Treatment', (14.3, 0.5, F + 9.5), math.radians(-90), 1.1)
    for k, (x, y, nm, rz) in enumerate(((-6.0, -6.5, 'PetClinic_Decorations', 0.4), (5.5, 12.0, 'PetClinic_FoodBowl', 0),
                                        (6.8, 12.4, 'PetClinic_Ball', 0), (-5.4, 12.2, 'PetClinic_Bone', 0.6),
                                        (-7.6, 12.6, 'PetClinic_PetCarrier', 0.0))):
        I(nm, f'PetClinic_Prop_{k}', 'Decorations', (x, y, F + 0.2), rz, 0.8 if 'Carrier' in nm else 1.0)
    for s in (-1, 1):                                     # banners + lanterns inside
        I('PetClinic_Banner', f'PetClinic_InteriorBanner_{"LR"[s > 0]}', 'Banners', (s * 14.25, 9.5, F + 18.0),
          math.radians(-90 if s > 0 else 90), 0.9)
        I('Shop_Lantern_Wall', f'PetClinic_InteriorLantern_{"LR"[s > 0]}', 'Lighting', (s * 14.3, -5.5, F + 12.5),
          math.radians(-90 if s > 0 else 90), 0.8)
    # ceiling beams
    cb = Part('PetClinic_Ceiling', c('Interior'))
    bevel_box(cb, I4, (0, 4.5, 20.6), (29.6, 27.0, 0.4), 'Clinic_White', 0.05)
    for y in range(-6, 18, 6):
        bevel_box(cb, I4, (0, y, 19.8), (29.6, 1.0, 1.2), 'Shop_Wood', 0.12)
    for x in (-6.0, 6.0):
        cb.box((x, 3.0, 18.0), (0.15, 0.15, 2.8), 'Lantern_Metal')
        from shop import shop_lantern
        shop_lantern(cb, T(x, 3.0, 12.4))
    fin(cb)

    # ---------------- landscaping + back yard ---------------------------------------------------------
    for k, (x, y, nm, sc, rz) in enumerate((
            (-31.0, -3.0, 'Bush_02', 1.2, 0.3), (31.0, -3.0, 'Bush_01', 1.3, 0.2), (-30.0, 10.0, 'Tree_Medium_High', 0.85, 0.3),
            (30.0, 11.0, 'Tree_Small', 1.0, 1.0), (-29.0, 20.0, 'Bush_03', 1.1, 0.0), (29.0, 20.0, 'Ground_Plant_01', 1.3, 0.0),
            (-4.0, -19.0, 'Ground_Plant_02', 1.0, 0.0), (4.0, -19.0, 'Ground_Plant_02', 1.0, 1.0),
            (-8.0, 21.6, 'Shop_Crate', 1.0, 0.2), (-6.0, 21.4, 'Shop_Crate', 0.8, -0.3), (8.0, 21.4, 'Shop_Barrel', 1.0, 0))):
        I(nm, f'PetClinic_Land_{nm}_{k}', 'Exterior', (x, y, 0), rz, sc)
    from foliage import vine
    vv = Part('PetClinic_Vines', c('Exterior'))
    for x, y, z in ((-16.9, -9.6, 20.6), (16.9, -9.6, 20.6), (-14.0, 19.5, 20.6), (13.0, 19.5, 20.6),
                    (-26.4, 15.4, 12.6), (26.4, 15.4, 12.6)):
        vine(vv, (x, y, z), rnd.uniform(6, 12), rnd, 1.1)
    fin(vv)

    # ---------------- lights ---------------------------------------------------------------------------
    for k, (x, y, z, e, col) in enumerate(((0, 4, 16, 3500, (0.85, 0.92, 1.0)), (0, 12, 10, 1200, (0.4, 0.75, 1.0)),
                                           (-8, -2, 10, 1100, (1.0, 0.72, 0.42)), (8, -2, 10, 1100, (1.0, 0.72, 0.42)),
                                           (0, -11, 12, 1500, (1.0, 0.72, 0.42)),
                                           (-14.6, -15.5, 27, 1200, (1.0, 0.7, 0.4)), (14.6, -15.5, 27, 1200, (1.0, 0.7, 0.4)))):
        L = bpy.data.lights.new(f'PetClinic_Light_{k}', 'POINT')
        L.color = col; L.energy = e; L.shadow_soft_size = 1.5
        o = bpy.data.objects.new(L.name, L)
        o.location = (x, y, z); o.parent = root
        coll(c('Lighting')).objects.link(o)
    return root


def build_clinic_cameras(root_loc=(0, 0, 0), rot_z=0.0, coll_name='CAMERAS', prefix='CAM_PetClinic', only=None):
    M = Matrix.Translation(root_loc) @ Matrix.Rotation(rot_z, 4, 'Z')
    out = {}
    for name, loc, tgt, lens in (('Front', (-5, -80, 16), (0, 0, 19), 28), ('Interior', (-4, -9.5, 6.5), (2, 12, 6.5), 20),
                                 ('Side', (-62, -40, 26), (0, 3, 13), 30), ('Rear', (26, 66, 24), (0, 8, 12), 30),
                                 ('Player', (4, -36, 5.2), (0, 6, 9), 24)):
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
