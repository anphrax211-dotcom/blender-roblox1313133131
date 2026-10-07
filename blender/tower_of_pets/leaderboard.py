"""TOWER OF PETS - LEADERBOARDS MONUMENT (replaces the old Leaderboards stand), in the hub's castle masonry language.

A freestanding outdoor monument - no interior, no roof - that players walk up to and read from the front:
wide masonry foundation with three shallow steps, carved light-stone back wall, three arched navy leaderboard
panels with gold frames and stone voussoir surrounds (TOP PET POWER - crossed swords, TOP PET COLLECTORS - paw,
TOP ROBUX SPENT - Robux hexagon; ranks #1-#10 with avatar disc, player name and value), a navy
"SEE THE STRONGEST - TOP COLLECTORS - TOP SUPPORTERS" ribbon, the big gold-framed "LEADERBOARDS" sign on a
raised arched crest with a gold crown, tall side pillars with navy crown + paw banners and lanterns, two crowned
guardian cat statues (navy/gold bandanas) facing the centre from pedestals with glowing paw panels, topiary
planters, small lanterns between the boards and a navy/gold paw medallion in the forecourt paving.

Each board's screen is its own object (Leaderboard_<n>_Screen) so a Roblox SurfaceGui can be placed on it; the
ranked rows are placeholder 3D text in BOARDS/<board>/Placeholder_Entries (delete them once the live board is wired).

Collections: TOWER_OF_PETS_LEADERBOARDS / MONUMENT (Foundation, Steps, Walls, Pillars, Arches, Gold_Trim), SIGNAGE
(Leaderboards_Title, Leaderboards_Subtitle, Crown), BOARDS (Top_Pet_Power, Top_Pet_Collectors, Top_Robux_Spent),
STATUES, BANNERS, LANTERNS, FLOOR, LANDSCAPING, LIGHTING  (" (leaderboards)" suffix where a name is taken).
Kit (LEADERBOARD_KIT): Leaderboard_Wall, _Pillar, _Arch, _Board, _Screen, _Sign, _Crown, _Banner, _CatStatue,
_Pedestal, _Lantern, _Step, _FloorEmblem, _Planter, _Emblem_Swords, _Emblem_Paw, _Emblem_Robux.
"""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
from common import Part, mat_plain, coll, inst, ASSETS, empty, paw, M_front, text_mesh, round_arch, TAU
from castle import bevel_box, masonry, quoins, voussoirs, pillar, trim_run, frame_strip, lifted
from trading import make_subcolls, pennant, merge_objects, lantern_light

ROOT = 'TOWER_OF_PETS_LEADERBOARDS'
KIT = 'LEADERBOARD_KIT'
I4 = Matrix.Identity(4)
FLIP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
CN = {}

BW, BH = 14.0, 16.0            # board frame width, height of the straight sides (arched top above)
BOARDS = (
    ('Top_Pet_Power', 'TOP PET POWER', 'STRONGEST PET TEAMS', 'swords',
     (('ShadowRex', '12.4M'), ('LunaPaws', '10.8M'), ('BlazeKing', '9.6M'), ('FrostyNova', '8.1M'),
      ('VoidHunter', '7.9M'), ('MysticCat', '7.2M'), ('PixelAlex', '6.1M'), ('AmyPetLuv', '5.9M'),
      ('DragonSoul', '5.6M'), ('NekoStar', '5.1M'))),
    ('Top_Pet_Collectors', 'TOP PET COLLECTORS', 'MOST PETS DISCOVERED', 'paw',
     (('NekoStar', '482'), ('PetMaster', '471'), ('LunaPaws', '468'), ('ShadowRex', '459'), ('CuddleKing', '443'),
      ('MysticCat', '438'), ('AmyPetLuv', '412'), ('PixelAlex', '405'), ('DragonSoul', '398'),
      ('FrostyNova', '387'))),
    ('Top_Robux_Spent', 'TOP ROBUX SPENT', 'BIGGEST SUPPORTERS', 'robux',
     (('RoyalDev', '125,430'), ('NightAura', '98,620'), ('ShadowRex', '76,510'), ('LunaPaws', '68,900'),
      ('MysticCat', '54,320'), ('BlazeKing', '48,600'), ('PixelAlex', '41,250'), ('CuddleKing', '39,120'),
      ('ThunderZ', '35,780'), ('NekoStar', '32,410'))),
)


def RZ(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def T(x, y, z=0.0):
    return Matrix.Translation((x, y, z))


def c(name):
    return CN.get(name, name)


# ---------------------------------------------------------------- materials -
def build_leaderboard_materials():
    P = mat_plain
    P('Lb_Navy', (0.03, 0.06, 0.28), 0.55)
    P('Lb_Navy_Light', (0.06, 0.13, 0.46), 0.5)
    P('Lb_Screen', (0.02, 0.04, 0.17), 0.45, emit=0.25)
    P('Lb_Row', (0.05, 0.09, 0.32), 0.5, emit=0.2)
    P('Lb_Text', (1.0, 1.0, 1.0), 0.4, emit=1.1)
    P('Lb_Text_Gold', (1.0, 0.76, 0.18), 0.4, emit=1.0)
    P('Lb_Text_Sub', (0.72, 0.80, 1.0), 0.4, emit=0.8)
    P('Lb_Paw_Glow', (1.0, 0.66, 0.16), 0.4, emit=1.5)
    P('Lb_Banner', (0.05, 0.10, 0.44), 0.85)
    P('Lb_Statue', (0.82, 0.80, 0.82), 0.6)
    P('Lb_Bandana', (0.08, 0.22, 0.78), 0.6)
    P('Lb_Gem_Red', (0.95, 0.08, 0.12), 0.2, emit=0.4)
    P('Lb_Gem_Blue', (0.10, 0.35, 1.0), 0.2, emit=0.4)
    P('Lb_Flower_Blue', (0.25, 0.42, 1.0), 0.6)
    for k, col in enumerate(((1.0, 0.50, 0.12), (0.12, 0.55, 1.0), (1.0, 0.22, 0.30), (0.25, 0.80, 0.25),
                             (0.60, 0.30, 1.0))):
        P(f'Lb_Avatar_{k}', col, 0.5, emit=0.15)


# ---------------------------------------------------------------- symbols ---
CROWN = [(-3.0, 0.0), (3.0, 0.0), (3.0, 1.1), (3.6, 4.0), (1.7, 2.2), (0.0, 4.8), (-1.7, 2.2), (-3.6, 4.0),
         (-3.0, 1.1)]


def crown_flat(p, M, s=1.0, depth=0.4, mat='Gold', gems=True):
    """flat crown emblem drawn in local XY (y up), extruded toward the viewer by M"""
    p.prism([(x * s, y * s) for x, y in CROWN], 0, depth, mat, M)
    for x, y in ((-3.6, 4.0), (0.0, 4.8), (3.6, 4.0)):
        p.ico(M @ Vector((x * s, y * s, depth * 0.5)), 0.42 * s, mat, 1)
    if gems:
        for k, x in enumerate((-1.8, 0.0, 1.8)):
            p.cyl(M @ Vector((x * s, 0.55 * s, depth + 0.05 * s)), 0.32 * s, 0.15 * s,
                  ('Lb_Gem_Blue', 'Lb_Gem_Red', 'Lb_Gem_Blue')[k], 8, rot=M.to_3x3().normalized())


def crown_3d(p, base, r=1.2, h=1.0, mat='Gold'):
    """small round crown (for statues): band + five points + balls"""
    base = Vector(base)
    p.cyl(base + Vector((0, 0, h * 0.3)), r, h * 0.6, mat, 14)
    for k in range(5):
        a = TAU * k / 5 + math.pi / 2
        q = base + Vector((math.cos(a) * r * 0.9, math.sin(a) * r * 0.9, h * 0.6))
        p.cone(q, 0.35 * r, h * 0.8, mat, 4)
        p.ico(q + Vector((0, 0, h * 0.85)), 0.14 * r, mat, 1)
    p.ico(base + Vector((0, -r, h * 0.3)), 0.22 * r, 'Lb_Gem_Red', 1)


def swords(p, M, s=1.0, mat='Gold', depth=0.4):
    """two crossed swords (local XY drawing)"""
    for k in (-1, 1):
        R = Matrix.Rotation(k * math.radians(40), 4, 'Z')
        blade = [(-0.32, -1.6), (0.32, -1.6), (0.32, 2.6), (0.0, 3.3), (-0.32, 2.6)]
        p.prism([(x * s, y * s) for x, y in blade], 0, depth, mat, M @ R)
        p.prism([(x * s, y * s) for x, y in ((-1.2, -1.95), (1.2, -1.95), (1.2, -1.55), (-1.2, -1.55))], 0,
                depth * 1.4, mat, M @ R)
        p.prism([(x * s, y * s) for x, y in ((-0.22, -3.1), (0.22, -3.1), (0.22, -1.95), (-0.22, -1.95))], 0,
                depth, 'Shop_Wood', M @ R)
        q = M @ R @ Vector((0, -3.35 * s, depth * 0.5))
        p.ico(q, 0.38 * s, mat, 1)


def robux(p, M, s=1.0, mat='Gold', depth=0.4):
    """Robux-style currency emblem: hexagon ring around a smaller hexagon ring"""
    def hexa(r, rot=math.pi / 2):
        return [(math.cos(rot + TAU * i / 6) * r * s, math.sin(rot + TAU * i / 6) * r * s) for i in range(7)]
    MX = M @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))   # drawing XY -> frame_strip XZ
    frame_strip(p, MX, hexa(2.8), hexa(2.0), 0, depth, mat)
    frame_strip(p, MX, hexa(1.25), hexa(0.6), 0, depth, mat)


def cat_statue(p):
    """crowned guardian cat statue (sitting, faces -y, origin at its base), navy bandana with a gold paw"""
    S = 'Lb_Statue'
    p.uvsphere((0, 0.6, 3.0), 2.6, S, 16, 10, (1.0, 1.1, 1.25))
    for s_ in (-1, 1):
        p.uvsphere((s_ * 1.9, 1.2, 1.5), 1.55, S, 12, 8, (0.85, 1.3, 1.0))          # haunches
        p.cyl((s_ * 0.95, -1.35, 2.2), 0.6, 4.2, S, 10, smooth=True)                # front legs
        p.uvsphere((s_ * 0.95, -1.75, 0.45), 0.8, S, 10, 6, (1, 1.35, 0.6))         # paws
    p.uvsphere((0, -0.6, 7.2), 2.2, S, 16, 10, (1.05, 1.0, 0.95))                    # head
    p.uvsphere((0, -2.3, 6.6), 0.9, S, 12, 8, (1.15, 0.8, 0.7))                      # muzzle
    p.ico((0, -3.0, 6.95), 0.25, 'Castle_Seam', 1)
    for s_ in (-1, 1):
        tilt = Euler((0, s_ * 0.38, 0)).to_matrix()
        p.cyl(Vector((s_ * 1.35, -0.5, 9.0)) + tilt @ Vector((0, 0, 0.9)), 1.0, 1.9, S, 4, r2=0.05, rot=tilt)
        p.torus((s_ * 0.8, -2.15, 7.6), 0.3, 0.08, 'Castle_Seam', 10, 4, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
    crown_3d(p, (0, -0.5, 9.0), 1.15, 1.1)
    # bandana: collar + triangle flap with a gold paw
    p.torus((0, -0.4, 5.2), 1.75, 0.3, 'Lb_Bandana', 18, 5, rot=Euler((0.3, 0, 0)).to_matrix())
    Mf = M_front(0, -2.05, 4.6) @ Matrix.Rotation(-0.25, 4, 'X')
    p.prism([(-1.9, 0.5), (1.9, 0.5), (0.0, -2.2)], 0, 0.3, 'Lb_Bandana', Mf)
    paw(p, Mf @ T(0, -0.35, 0.3), 1.1, 0.08, 'Gold')
    from foliage import tube
    tube(p, [Vector((1.9, 2.6, 0.6)), Vector((3.1, 1.0, 0.5)), Vector((2.9, -1.4, 0.5)), Vector((1.9, -2.3, 0.6))],
         [0.6, 0.55, 0.45, 0.3], S, 6)


def pedestal(p, rnd=None):
    """masonry pedestal with glowing paw panels on the front and both sides"""
    rnd = rnd or random.Random(13)
    bevel_box(p, I4, (0, 0, 0.6), (8.0, 8.0, 1.2), 'Castle_Trim', 0.2)
    masonry(p, T(0, -3.2), -3.2, 3.2, 1.2, 6.6, rnd, 1.8, (2.0, 3.2), 6.4, backing=False)
    for rz in (0, 90, -90):
        Mr = RZ(rz)
        bevel_box(p, Mr, (0, -3.3, 3.9), (3.4, 0.3, 3.4), 'Castle_Trim', 0.1)
        bevel_box(p, Mr, (0, -3.42, 3.9), (2.8, 0.2, 2.8), 'Lb_Paw_Glow', 0.05)
        paw(p, Mr @ M_front(0, -3.55, 3.75), 2.1, 0.12, 'Castle_Seam')
    bevel_box(p, I4, (0, 0, 7.1), (7.6, 7.6, 1.0), 'Castle_Trim', 0.18)
    bevel_box(p, I4, (0, -3.85, 7.1), (7.0, 0.3, 0.35), 'Gold', 0.05)


def planter(p, rnd=None):
    """square stone planter with a clipped topiary ball and blue flowers"""
    from foliage import leaf_cluster
    rnd = rnd or random.Random(17)
    bevel_box(p, I4, (0, 0, 1.0), (3.6, 3.6, 2.0), 'Castle_Stone_Light', 0.2)
    bevel_box(p, I4, (0, 0, 2.1), (4.0, 4.0, 0.4), 'Castle_Trim', 0.12)
    bevel_box(p, I4, (0, -2.0, 1.0), (2.6, 0.15, 0.3), 'Gold', 0.04)
    p.cyl((0, 0, 2.6), 0.25, 1.4, 'Trunk', 5)
    leaf_cluster(p, (0, 0, 4.4), 1.6, rnd, 18, squash=0.95, droop=0.1)
    for k in range(7):
        a = TAU * k / 7
        p.ico((math.cos(a) * 1.4, math.sin(a) * 1.4, 2.5), 0.3, 'Lb_Flower_Blue', 1)


def board_frame(p, rnd):
    """arched navy board slab with gold frame and a stone voussoir surround (front face y = -0.6, base z = 0)"""
    arch = round_arch(BW, BH, 16)
    p.prism(arch, -0.6, 1.6, 'Lb_Navy', FLIP)
    frame_strip(p, I4, round_arch(BW + 0.9, BH, 16), arch, -0.95, 1.2, 'Gold')
    voussoirs(p, I4, round_arch(BW + 3.4, BH, 16), round_arch(BW + 0.9, BH, 16), -0.5, 1.8, rnd, 2.3, backing=False)
    bevel_box(p, I4, (0, -0.2, -0.3), (BW + 3.6, 2.6, 0.6), 'Castle_Trim', 0.12)
    bevel_box(p, I4, (0, -1.0, 0.25), (BW + 0.9, 0.5, 0.5), 'Gold', 0.06)


def screen(p):
    bevel_box(p, I4, (0, -0.7, 8.05), (BW - 1.6, 0.2, 14.5), 'Lb_Screen', 0.05)


def _lib(name, builder, *a, **kw):
    p = Part('ASSET_' + name, KIT)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def crown_paw_icon(p, Mb, w, length):
    crown_flat(p, Mb @ T(0, -length * 0.36, 0.0), w * 0.12, 0.22, 'Gold', gems=False)
    paw(p, Mb @ T(0, -length * 0.7, 0.0), w * 0.62, 0.25, 'Gold')


def lb_banner(p):
    pennant(p, I4, 4.4, 13.0, 'Lb_Banner', crown_paw_icon)


def sign_board(p, M=I4, W=17.0, H=6.4):
    """navy sign slab with a gently arched top and gold frame (origin bottom centre, front y = -0.2)"""
    top = [(W * math.cos(math.pi * i / 14), H + 1.2 * math.sin(math.pi * i / 14)) for i in range(15)]
    p.prism([(-W, 0.0), (W, 0.0)] + top, -0.2, 1.2, 'Lb_Navy', M @ FLIP)
    Wo, Wi = W + 0.5, W - 0.05
    outer = [(-Wo, -0.5)] + [(Wo * math.cos(math.pi - math.pi * i / 14), H + 0.5 + 1.2 * math.sin(math.pi - math.pi * i / 14))
                             for i in range(15)] + [(Wo, -0.5), (-Wo, -0.5)]
    inner = [(-Wi, 0.0)] + [(Wi * math.cos(math.pi - math.pi * i / 14), H - 0.05 + 1.2 * math.sin(math.pi - math.pi * i / 14))
                            for i in range(15)] + [(Wi, 0.0), (-Wi, 0.0)]
    frame_strip(p, M, outer, inner, -0.6, 0.4, 'Gold')


def build_leaderboard_kit(parent):
    from shop import shop_lantern
    coll(KIT, parent)
    R = random.Random
    _lib('Leaderboard_Wall', lambda p: masonry(p, I4, -6, 6, 0, 10, R(1), 2.5, (3, 5)))
    _lib('Leaderboard_Pillar', lambda p: pillar(p, I4, 4.6, 0, 42, R(2), cap=None, band=0.5))
    _lib('Leaderboard_Arch', lambda p: voussoirs(p, I4, round_arch(BW + 3.4, BH, 16), round_arch(BW + 0.9, BH, 16),
                                                 -0.5, 1.8, R(3), 2.3))
    _lib('Leaderboard_Board', board_frame, R(4))
    _lib('Leaderboard_Screen', screen)
    _lib('Leaderboard_Sign', sign_board)
    _lib('Leaderboard_Crown', lambda p: crown_flat(p, M_front(0, 0, 0), 1.0, 0.8))
    _lib('Leaderboard_Banner', lb_banner)
    _lib('Leaderboard_CatStatue', cat_statue)
    _lib('Leaderboard_Pedestal', pedestal)
    _lib('Leaderboard_Lantern', shop_lantern)
    _lib('Leaderboard_Step', lambda p: bevel_box(p, I4, (0, 0, 0.375), (12, 2, 0.75), 'Castle_Stone_Light', 0.12))
    _lib('Leaderboard_FloorEmblem', floor_emblem)
    _lib('Leaderboard_Planter', planter)
    _lib('Leaderboard_Emblem_Swords', lambda p: swords(p, M_front(0, 0, 0)))
    _lib('Leaderboard_Emblem_Paw', lambda p: paw(p, M_front(0, 0, 0), 5.0, 0.4, 'Gold'))
    _lib('Leaderboard_Emblem_Robux', lambda p: robux(p, M_front(0, 0, 0)))


def floor_emblem(p, r=10.0):
    """navy medallion with gold rings and a gold paw (faces up)"""
    p.cyl((0, 0, 0.12), r + 1.6, 0.24, 'Castle_Trim', 56)
    p.cyl((0, 0, 0.18), r + 0.6, 0.26, 'Gold', 56)
    p.cyl((0, 0, 0.22), r, 0.3, 'Lb_Navy_Light', 56)
    p.torus((0, 0, 0.37), r * 0.8, 0.14, 'Gold', 56, 4)
    paw(p, T(0, 0.4, 0.37), r * 1.05, 0.08, 'Gold')


# ---------------------------------------------------------------- build -----
TREE = (('MONUMENT', ROOT), ('Foundation', 'MONUMENT'), ('Steps', 'MONUMENT'), ('Walls', 'MONUMENT'),
        ('Pillars', 'MONUMENT'), ('Arches', 'MONUMENT'), ('Gold_Trim', 'MONUMENT'), ('SIGNAGE', ROOT),
        ('Leaderboards_Title', 'SIGNAGE'), ('Leaderboards_Subtitle', 'SIGNAGE'), ('Crown', 'SIGNAGE'),
        ('BOARDS', ROOT), ('Top_Pet_Power', 'BOARDS'), ('Top_Pet_Collectors', 'BOARDS'),
        ('Top_Robux_Spent', 'BOARDS'), ('STATUES', ROOT), ('BANNERS', ROOT), ('LANTERNS', ROOT), ('FLOOR', ROOT),
        ('LANDSCAPING', ROOT), ('LIGHTING', ROOT))


def build_board(root, k, x, z0, data):
    key, title, sub, icon, rows = data
    col = c(key)
    ph = f'Placeholder_Entries_{k + 1}'
    coll(ph, col)
    inst('Leaderboard_Board', f'Leaderboard_{k + 1}_{key}_Frame', col, (x, 0, z0), 0, 1.0, root)
    inst('Leaderboard_Screen', f'Leaderboard_{k + 1}_Screen', col, (x, 0, z0), 0, 1.0, root)
    e = Part(f'Leaderboard_{k + 1}_Emblem', col)
    ze = z0 + BH + 3.0
    if icon == 'swords':
        swords(e, M_front(x, -0.7, ze), 0.95, 'Gold', 0.5)
    elif icon == 'paw':
        paw(e, M_front(x, -0.7, ze - 0.2), 4.8, 0.5, 'Gold')
    else:
        robux(e, M_front(x, -0.7, ze), 1.0, 'Gold', 0.5)
    yf = -0.85
    bevel_box(e, I4, (x, yf + 0.05, z0 + 13.9), (BW - 2.0, 0.2, 2.1), 'Lb_Navy_Light', 0.05)
    bevel_box(e, I4, (x, yf - 0.02, z0 + 12.75), (BW - 2.4, 0.15, 0.14), 'Gold', 0.02)
    for r in range(10):
        if r % 2 == 0:
            bevel_box(e, I4, (x, yf + 0.1, z0 + 10.9 - r * 1.05), (BW - 2.2, 0.1, 0.92), 'Lb_Row', 0.02)
        zr = z0 + 10.9 - r * 1.05
        e.cyl((x - 4.35, yf, zr), 0.42, 0.15, 'Lb_Text', 14, axis='Y')
        e.cyl((x - 4.35, yf - 0.08, zr), 0.33, 0.15, f'Lb_Avatar_{r % 5}', 14, axis='Y')
    e.finish(parent=root)
    text_mesh(f'Leaderboard_{k + 1}_Title', title, col, 1.0, 0.25, 'Lb_Text', (x, yf - 0.2, z0 + 13.9), 0, root)
    text_mesh(f'Leaderboard_{k + 1}_Subtitle', sub, col, 0.6, 0.15, 'Lb_Text_Sub', (x, yf - 0.1, z0 + 12.2), 0, root)
    gold, white = [], []
    for r, (name, val) in enumerate(rows):
        zr = z0 + 10.9 - r * 1.05
        gold.append(text_mesh(f'_r{k}{r}', f'#{r + 1}', ph, 0.74, 0.12, 'Lb_Text_Gold', (x - 6.2, yf - 0.05, zr), 0,
                              None, 'LEFT'))
        white.append(text_mesh(f'_n{k}{r}', name, ph, 0.72, 0.12, 'Lb_Text', (x - 3.65, yf - 0.05, zr), 0, None,
                               'LEFT'))
        white.append(text_mesh(f'_v{k}{r}', val, ph, 0.72, 0.12, 'Lb_Text' if r > 2 else 'Lb_Text_Gold',
                               (x + 6.0, yf - 0.05, zr), 0, None, 'RIGHT'))
    gold += [o for o in white if o.data.materials[0].name == 'Lb_Text_Gold']
    white = [o for o in white if o.data.materials[0].name == 'Lb_Text']
    merge_objects(gold, f'Leaderboard_{k + 1}_Ranks', ph, root)
    merge_objects(white, f'Leaderboard_{k + 1}_Entries', ph, root)


def build_leaderboards(parent_coll, loc=(0, 0, 0), rot_z=0.0):
    make_subcolls(ROOT, TREE, parent_coll, parent_coll is not None, 'leaderboards', CN)
    root = empty('Leaderboards_Root', ROOT, loc, rot_z, 8)
    rnd = random.Random(9753)
    Z0 = 3.0
    XB = BW + 2.2                         # board spacing

    def fin(p):
        return p.finish(parent=root)

    def I(asset, name, col, xyz, rz=0.0, s=1.0):
        return inst(asset, name, c(col), xyz, rz, s, root)

    # ---------------- foundation + steps --------------------------------------------------------------
    f = Part('Leaderboards_Foundation', c('Foundation'))
    bevel_box(f, I4, (0, 2.5, Z0 / 2), (66, 13, Z0), 'Castle_Trim', 0.2)
    masonry(f, T(0, -4.0), -33, 33, 0, Z0, rnd, 1.5, (3, 5), 1.0, backing=False)
    for s in (-1, 1):
        masonry(f, T(s * 33, 2.5) @ RZ(s * 90), -6.5, 6.5, 0, Z0, rnd, 1.5, (3, 5), 1.0, backing=False)
    fin(f)
    st = Part('Leaderboards_Steps', c('Steps'))
    for i in range(3):
        h = Z0 * (3 - i) / 4
        bevel_box(st, I4, (0, -5.0 - i * 2.0, h / 2), (56 - i * 3, 2.0, h), 'Castle_Stone_Light', 0.12)
        bevel_box(st, I4, (0, -6.02 - i * 2.0, h - 0.12), (56 - i * 3, 0.06, 0.12), 'Castle_Seam', 0.0)
    fin(st)
    pv = Part('Leaderboards_Paving', c('FLOOR'))
    pv.cyl((0, -14.0, 0.08), 30.0, 0.16, 'Castle_Stone_Light', 64)
    pv.ring_sector(14.2, 17.0, 0, TAU, 0.12, 0.24, 'Lb_Navy_Light', 64, center=(0, -26.0))
    pv.ring_sector(13.8, 14.2, 0, TAU, 0.12, 0.27, 'Gold', 64, center=(0, -26.0))
    pv.ring_sector(17.0, 17.4, 0, TAU, 0.12, 0.27, 'Gold', 64, center=(0, -26.0))
    for k in range(8):
        a = TAU * k / 8 + TAU / 16
        bevel_box(pv, T(0, -26.0) @ Matrix.Rotation(a, 4, 'Z'), (15.6, 0, 0.27), (2.8, 0.3, 0.08), 'Gold', 0.02)
    fin(pv)
    I('Leaderboard_FloorEmblem', 'Leaderboards_FloorEmblem', 'FLOOR', (0, -26.0, 0.12), 0, 1.0)

    # ---------------- back wall --------------------------------------------------------------------------
    w = Part('Leaderboards_Back_Wall', c('Walls'))
    ZW = Z0 + 26.0
    w.box((0, 3.2, (Z0 + ZW) / 2), (54, 4.0, ZW - Z0), 'Castle_Seam')
    masonry(w, T(0, 1.2), -27.0, 27.0, Z0, ZW, rnd, 2.5, (3.2, 5.5), 1.4, backing=False)
    masonry(w, T(0, 5.2) @ RZ(180), -27.0, 27.0, Z0, ZW, rnd, 2.5, (3.2, 5.5), 1.4, backing=False)
    for s in (-1, 1):
        quoins(w, T(s * 27.0, 5.2) @ RZ(180), Z0, ZW, rnd, 3.4, 2.0, 2.5, side=s, mat='Castle_Trim')
    # raised crest behind the sign: rectangle + elliptic top
    zc = ZW - 2.0
    crest = [(-19.0, zc)] + [(19.0 * math.cos(math.pi - math.pi * i / 18), zc + 10.0 + 10.0 * math.sin(math.pi - math.pi * i / 18))
                             for i in range(19)] + [(19.0, zc)]
    w.prism(crest, 1.4, 4.8, 'Castle_Stone_Light', FLIP)
    voussoirs(w, T(0, 1.4), [(x * 1.12, zc + (z - zc) * 1.06) for x, z in crest], crest, -0.9, 0.6, rnd, 2.6,
              backing=False)
    fin(w)
    gt = Part('Leaderboards_Gold_Trim', c('Gold_Trim'))
    bevel_box(gt, I4, (0, 0.3, ZW + 0.5), (55.0, 0.4, 0.4), 'Gold', 0.05)
    frame_strip(gt, T(0, 0.3), [(x * 1.16, zc + (z - zc) * 1.08) for x, z in crest],
                [(x * 1.12, zc + (z - zc) * 1.06) for x, z in crest], -0.3, 0.3, 'Gold')
    trim_run(gt, T(0, -4.0), -33, 33, Z0, h=1.0, out=0.8, gold=True)
    fin(gt)
    cn = Part('Leaderboards_Cornice', c('Walls'))
    bevel_box(cn, I4, (0, 3.2, ZW + 0.5), (55.4, 5.4, 1.0), 'Castle_Trim', 0.2)
    fin(cn)

    # ---------------- boards -------------------------------------------------------------------------------
    for k, data in enumerate(BOARDS):
        build_board(root, k, (k - 1) * XB, Z0 + 1.2, data)
    ar = Part('Leaderboards_Pilasters', c('Arches'))
    for s in (-1, 1):
        x = s * XB / 2
        bevel_box(ar, I4, (x, -0.3, Z0 + 10.0), (1.8, 2.2, 20.0), 'Castle_Stone_Light', 0.2)
        bevel_box(ar, I4, (x, -0.3, Z0 + 20.3), (2.6, 2.8, 0.6), 'Castle_Trim', 0.12)
        bevel_box(ar, I4, (x, -1.45, Z0 + 10.0), (0.5, 0.15, 17.0), 'Gold', 0.04)
    fin(ar)
    for s in (-1, 1):
        I('Leaderboard_Lantern', f'Leaderboards_BoardLantern_{"LR"[s > 0]}', 'LANTERNS', (s * XB / 2, -0.3, Z0 + 20.6), 0, 0.7)
        I('Leaderboard_Planter', f'Leaderboards_BoardPlanter_{"LR"[s > 0]}', 'LANDSCAPING', (s * XB / 2, -2.6, Z0), 0, 0.9)

    # ---------------- sign, ribbon, crown --------------------------------------------------------------------
    rb = Part('Leaderboards_Subtitle_Ribbon', c('Leaderboards_Subtitle'))
    zr = ZW + 0.2
    bevel_box(rb, I4, (0, -1.6, zr + 1.2), (37.0, 0.8, 2.4), 'Lb_Navy', 0.1)
    frame_strip(rb, T(0, -1.6), [(-18.8, zr - 0.15), (-18.8, zr + 2.55), (18.8, zr + 2.55), (18.8, zr - 0.15),
                                 (-18.8, zr - 0.15)],
                [(-18.45, zr + 0.2), (-18.45, zr + 2.2), (18.45, zr + 2.2), (18.45, zr + 0.2), (-18.45, zr + 0.2)],
                -0.5, 0.3, 'Gold')
    for s in (-1, 1):
        rb.prism([(s * 18.8, zr), (s * 21.6, zr - 0.6), (s * 20.6, zr + 1.2), (s * 21.6, zr + 2.6),
                  (s * 18.8, zr + 2.4)][::(1 if s > 0 else -1)], -1.4, -0.9, 'Lb_Navy', FLIP)
    fin(rb)
    text_mesh('Leaderboards_Subtitle_Text', 'SEE THE STRONGEST • TOP COLLECTORS • TOP SUPPORTERS',
              c('Leaderboards_Subtitle'), 1.0, 0.25, 'Lb_Text', (0, -2.15, zr + 1.15), 0, root)
    sg = Part('Leaderboards_Sign', c('Leaderboards_Title'))
    sign_board(sg, T(0, -1.4, zr + 2.8))
    for s in (-1, 1):
        sg.cyl(Vector((s * 17.8, -2.0, zr + 6.0)), 1.1, 0.6, 'Gold', 12, axis='Y')
        sg.cyl(Vector((s * 17.8, -2.35, zr + 6.0)), 0.7, 0.2, 'Lb_Paw_Glow', 12, axis='Y')
    fin(sg)
    text_mesh('Leaderboards_Title_Text', 'LEADERBOARDS', c('Leaderboards_Title'), 3.9, 0.6, 'Lb_Text',
              (0, -2.1, zr + 6.1), 0, root)
    I('Leaderboard_Crown', 'Leaderboards_Crown', 'Crown', (0, 0.9, zr + 10.6), 0, 1.25)

    # ---------------- pillars, banners, lanterns ------------------------------------------------------------------
    pl = Part('Leaderboards_Pillars', c('Pillars'))
    for s in (-1, 1):
        pillar(pl, T(s * 29.6, 1.6), 4.6, Z0, 40.0, rnd, cap=None, band=0.5)
    fin(pl)
    for s in (-1, 1):
        LR = 'LR'[s > 0]
        I('Leaderboard_Banner', f'Leaderboards_Banner_{LR}', 'BANNERS', (s * 29.6, -1.6, Z0 + 33.0), 0, 1.0)
        I('Leaderboard_Lantern', f'Leaderboards_PillarLantern_{LR}', 'LANTERNS', (s * 29.6, 1.6, Z0 + 40.2), 0, 1.3)
        I('Shop_Lantern_Wall', f'Leaderboards_WallLantern_{LR}', 'LANTERNS', (s * 29.6, -1.3, Z0 + 12.0), 0, 0.9)
        lantern_light(f'Leaderboards_Light_Pillar_{LR}', c('LIGHTING'), root, (s * 29.6, -1.0, Z0 + 43.0), 900)
        lantern_light(f'Leaderboards_Light_Board_{LR}', c('LIGHTING'), root, (s * XB / 2, -3.0, Z0 + 22.0), 450)
        # guardian cat statues facing the centre
        I('Leaderboard_Pedestal', f'Leaderboards_Pedestal_{LR}', 'STATUES', (s * 37.0, -1.0, 0), 0, 1.0)
        I('Leaderboard_CatStatue', f'Leaderboards_CatStatue_{LR}', 'STATUES', (s * 37.0, -1.0, 7.6),
          math.radians(-s * 52), 1.05)
        lantern_light(f'Leaderboards_Light_Pedestal_{LR}', c('LIGHTING'), root, (s * 37.0, -7.0, 4.0), 350)
    for k, (x, y, e) in enumerate(((0, -14, 2600), (-17, -10, 900), (17, -10, 900))):
        lantern_light(f'Leaderboards_Light_Front_{k}', c('LIGHTING'), root, (x, y, 18.0), e, (1.0, 0.86, 0.66), 4.0)
    for k, (x, y) in enumerate(((-23.0, -18.5), (23.0, -18.5), (-32.0, -10.0), (32.0, -10.0))):
        I('Castle_Lantern', f'Leaderboards_PathLantern_{k}', 'LANTERNS', (x, y, 0), 0, 0.95)
        lantern_light(f'Leaderboards_Light_Path_{k}', c('LIGHTING'), root, (x, y - 1.5, 9.0), 500)

    # ---------------- landscaping ---------------------------------------------------------------------------------
    for k, (x, y, nm, sc, rz) in enumerate((
            (-29.0, -6.4, 'Leaderboard_Planter', 1.0, 0.0), (29.0, -6.4, 'Leaderboard_Planter', 1.0, 0.0),
            (-37.0, -8.0, 'Bush_01', 1.1, 0.3), (37.0, -8.0, 'Bush_02', 1.1, 1.0),
            (-41.0, 4.0, 'Topiary_Cone', 1.2, 0.0), (41.0, 4.0, 'Topiary_Cone', 1.2, 0.0),
            (-34.0, 11.0, 'Tree_Medium_High', 0.85, 0.4), (34.0, 11.0, 'Tree_Tall_Thin', 0.9, 1.4),
            (-14.0, 11.0, 'Tree_Small', 0.9, 0.2), (14.0, 11.0, 'Tree_Small', 1.0, 2.2),
            (-27.0, -12.0, 'Ground_Plant_02', 1.0, 0.0), (27.0, -12.0, 'Ground_Plant_02', 1.0, 1.0),
            (-12.0, -10.8, 'Ground_Plant_01', 0.9, 0.0), (12.0, -10.8, 'Ground_Plant_01', 0.9, 1.0))):
        I(nm, f'Leaderboards_Land_{nm}_{k}', 'LANDSCAPING', (x, y, 0), rz, sc)
    from foliage import vine
    vv = Part('Leaderboards_Vines', c('LANDSCAPING'))
    for x in (-26.8, 26.8, -20.0, 20.0):
        vine(vv, (x, 0.8, ZW), rnd.uniform(6, 11), rnd, 1.0)
    fin(vv)
    return root


def build_leaderboard_cameras(root_loc=(0, 0, 0), rot_z=0.0, coll_name='CAMERAS', prefix='CAM_Leaderboards', only=None):
    M = Matrix.Translation(root_loc) @ Matrix.Rotation(rot_z, 4, 'Z')
    out = {}
    for name, loc, tgt, lens in (('Front', (0, -84, 16), (0, 0, 22), 28), ('Boards', (0, -34, 12.5), (0, 0, 13.5), 30),
                                 ('Side', (-64, -46, 22), (0, -2, 18), 28), ('Player', (5, -40, 5.2), (0, 0, 17), 22),
                                 ('Top', (0, -12, 150), (0, -10, 0), 32)):
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
