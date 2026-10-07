"""TOWER OF PETS - TRADING PLAZA PORTAL (replaces the old Trading building), in the hub's castle masonry language.

Built from the Trading Plaza Portal reference sheet: a wide stone gateway, NOT the plaza itself - players walk
through the portal and are teleported to the separate Trading Plaza map.
Masonry central block with a deep layered round arch (stone voussoirs, gold ring, purple-stone chamber lining,
inner recessed arch), raised round-topped crest holding the glowing trading emblem (two pets + circular trade
arrows), purple "TRADING PLAZA" sign with gold frame and a navy "TRADE WITH OTHER PLAYERS" ribbon, tall side
pillars and outer pillars with lanterns, side walls with navy banners (gold border + paw), a cat and a dog statue
on paw pedestals exchanging glowing trade cubes, a paved forecourt with the circular trading floor emblem,
purple floor bands, lanterns, planters, crystals and trees.

The portal effect is split into separate, animatable pieces: Core (emissive vortex surface), Rings (three
energy rings, origin at the portal centre -> spin them), Energy (swirl arms + glowing icon), Particles
(sparkles / stars) plus an invisible TradingPortal_TeleportTrigger for the Roblox teleport.

Collections: TOWER_OF_PETS_TRADING_PORTAL / ARCHITECTURE (Walls, Pillars, Arch, Trim, Roof), SIGNAGE
(Trading_Plaza, Trade_With_Other_Players), PORTAL (Core, Rings, Energy, Particles), STATUES (Pet_Left,
Pet_Right), BANNERS, LANTERNS, FLOOR, LANDSCAPING, LIGHTING  (" (trading)" suffix where a name is taken).
Kit (TRADINGPORTAL_KIT): TradingPortal_Wall, _Pillar, _Arch, _Roof, _GoldTrim, _Sign, _Banner, _Statue,
_Statue_Dog, _Pedestal, _Core, _EnergyRing, _Particles, _Lantern, _Floor, _TradingSymbol, _Crystal.
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
from common import (Part, MATS, mat_plain, mat_noise, mat_portal, coll, inst, ASSETS, empty, paw, M_front,
                    text_mesh, round_arch, ellipse, TAU)
from castle import (bevel_box, masonry, quoins, voussoirs, pillar, trim_run, inside, lifted, frame_strip,
                    rect_minus_arch)

ROOT = 'TOWER_OF_PETS_TRADING_PORTAL'
KIT = 'TRADINGPORTAL_KIT'
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


# ---------------------------------------------------------------- shared helpers (also used by leaderboard.py) --
def make_subcolls(root, tree, parent, in_lobby, suffix, cn):
    """create root + sub-collections; a name already in the file (or reserved in the lobby) gets a suffix"""
    from hatchery import RESERVED
    cn.clear()
    coll(root, parent)
    for name, par in tree:
        taken = name in bpy.data.collections or (in_lobby and name in RESERVED)
        cn[name] = f'{name} ({suffix})' if taken else name
        coll(cn[name], cn.get(par, par))


def pennant(p, M=I4, w=4.4, length=12.0, fabric='Trade_Banner', icon=None):
    """hanging banner: fabric with a pointed tail, gold border, gold icon (paw by default), gold top bar.
    Hangs from the local origin, faces -y."""
    Mb = M @ DRAW
    o = [(-w / 2, 0), (w / 2, 0), (w / 2, -length), (0, -length - w * 0.55), (-w / 2, -length)]
    p.prism(o, -0.25, 0.0, fabric, Mb)
    edge = [(-w / 2, 0), (-w / 2, -length), (0, -length - w * 0.55), (w / 2, -length), (w / 2, 0)]
    inner = [(-w / 2 + 0.38, 0), (-w / 2 + 0.38, -length + 0.16), (0, -length - w * 0.55 + 0.55),
             (w / 2 - 0.38, -length + 0.16), (w / 2 - 0.38, 0)]
    for (a0, a1), (b0, b1) in zip(zip(edge, edge[1:]), zip(inner, inner[1:])):
        q = [a0, a1, b1, b0]
        p.hexa([Mb @ Vector((x, z, 0.0)) for x, z in q] + [Mb @ Vector((x, z, 0.18)) for x, z in q], 'Gold')
    if icon:
        icon(p, Mb, w, length)
    else:
        paw(p, Mb @ T(0, -length * 0.58, 0.0), w * 0.66, 0.25, 'Gold')
    bevel_box(p, M, (0, -0.3, 0.35), (w + 1.2, 0.5, 0.7), 'Gold', 0.1)
    for s in (-1, 1):
        p.ico(M @ Vector((s * (w / 2 + 0.7), -0.3, 0.35)), 0.42, 'Gold', 1)


def merge_objects(objs, name, collection, parent=None):
    """join text meshes etc. (all sharing one material) into one mesh object - fewer Roblox parts"""
    bm = bmesh.new()
    mat = objs[0].data.materials[0]
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_basis)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        old = o.data
        bpy.data.objects.remove(o)
        if old.users == 0:
            bpy.data.meshes.remove(old)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll(collection).objects.link(ob)
    ob.parent = parent
    return ob


def lantern_light(name, collection, parent, loc, energy=900, col=(1.0, 0.7, 0.4), size=1.2):
    L = bpy.data.lights.new(name, 'POINT')
    L.color = col; L.energy = energy; L.shadow_soft_size = size
    o = bpy.data.objects.new(name, L)
    o.location = loc; o.parent = parent
    coll(collection).objects.link(o)
    return o


# ---------------------------------------------------------------- materials -
def build_trading_materials():
    P = mat_plain
    mat_noise('Trade_Purple_Stone', (0.40, 0.27, 0.66), (0.46, 0.32, 0.72), 0.75, 0.15, 0.1, 1.2)
    P('Trade_Purple', (0.30, 0.08, 0.78), 0.5)
    P('Trade_Navy', (0.06, 0.05, 0.28), 0.6)
    P('Trade_Banner', (0.12, 0.07, 0.40), 0.85)
    P('Trade_Statue', (0.76, 0.68, 0.60), 0.6)
    P('Trade_White_Glow', (1.0, 0.98, 1.0), 0.4, emit=1.3)
    P('Trade_Icon_Glow', (0.98, 0.86, 1.0), 0.3, emit=1.05)
    P('Trade_Ring_Glow', (0.62, 0.30, 1.0), 0.3, emit=1.5)
    P('Trade_Ring_Pink', (1.0, 0.40, 0.92), 0.3, emit=1.0)
    P('Trade_Ring_Blue', (0.35, 0.40, 1.0), 0.3, emit=1.3)
    P('Trade_Spark', (0.90, 0.80, 1.0), 0.3, emit=1.5)
    P('Trade_Disc_Glow', (0.45, 0.16, 0.95), 0.4, emit=0.8)
    P('Trade_Crystal', (0.62, 0.32, 1.0), 0.15, emit=0.5)
    P('Trade_Water', (0.20, 0.55, 1.0), 0.05)
    m = mat_portal('Trade_Portal')                         # purple / violet / blue vortex
    ramp = next(n for n in m.node_tree.nodes if n.type == 'VALTORGB')
    for el, col in zip(ramp.color_ramp.elements, ((1.0, 0.86, 1.0, 1), (0.72, 0.30, 1.0, 1),
                                                    (0.38, 0.08, 0.86, 1), (0.10, 0.12, 0.62, 1))):
        el.color = col
    m.diffuse_color = (0.5, 0.2, 1.0, 1)


# ---------------------------------------------------------------- symbols ---
def arc_band(cx, cy, r, w, a0, a1, n=12):
    out = [(cx + (r + w / 2) * math.cos(a0 + (a1 - a0) * i / n), cy + (r + w / 2) * math.sin(a0 + (a1 - a0) * i / n))
           for i in range(n + 1)]
    inn = [(cx + (r - w / 2) * math.cos(a0 + (a1 - a0) * i / n), cy + (r - w / 2) * math.sin(a0 + (a1 - a0) * i / n))
           for i in range(n + 1)]
    return out + inn[::-1]


def trade_arrows(p, M, s, mat, depth=0.3, cx=0.0, cy=0.0, r=1.7, w=0.5):
    """two circular arrows chasing each other (drawn in local XY, extruded toward -y by M_front-style M)"""
    for a0, a1 in ((math.radians(25), math.radians(160)), (math.radians(205), math.radians(340))):
        pts = arc_band(cx * s, cy * s, r * s, w * s, a0, a1)
        p.prism(pts, 0, depth, mat, M)
        P = Vector((cx * s + r * s * math.cos(a1), cy * s + r * s * math.sin(a1)))
        n = Vector((math.cos(a1), math.sin(a1)))
        t = Vector((-math.sin(a1), math.cos(a1)))
        tri = [P + n * w * s * 1.5, P + t * w * s * 2.4, P - n * w * s * 1.5]
        p.prism([(v.x, v.y) for v in tri], 0, depth, mat, M)


def trade_symbol(p, M, s=1.0, pet_mat='Trade_Icon_Glow', arrow_mat='Trade_Icon_Glow', depth=0.3):
    """trading emblem: two pet silhouettes (cat left, dog right) facing each other under circular trade arrows"""
    S = lambda pts: [(x * s, y * s) for x, y in pts]
    for k in (-1, 1):                                       # k = -1 left pet, +1 right pet (mirrored)
        X = lambda pts: [(-k * x, y) for x, y in pts] if k > 0 else pts
        shapes = [ellipse(-3.0, -1.3, 1.9, 1.7, 16), ellipse(-1.4, -1.75, 0.95, 0.72, 12),
                  ellipse(-3.9, -3.3, 1.7, 1.1, 14)]
        if k < 0:                                           # cat: pointy ears
            shapes += [[(-4.6, -0.6), (-4.3, 1.5), (-3.2, 0.2)], [(-2.9, 0.25), (-1.9, 1.3), (-1.55, -0.4)]]
        else:                                               # dog: floppy ears
            shapes += [ellipse(-4.6, -1.3, 0.62, 1.25, 10), ellipse(-1.9, 0.35, 0.55, 0.85, 10)]
        for poly in shapes:
            q = S(X(poly))
            if k > 0:
                q = q[::-1]
            p.prism(q, 0, depth, pet_mat, M)
    trade_arrows(p, M, s, arrow_mat, depth, 0.0, 2.0, 1.65, 0.48)


def emblem(p, M, s=1.0):
    """crest emblem: stone + gold rings around a glowing purple disc carrying the trading symbol (faces -y)"""
    n = 32
    def ring(r):
        return [(math.cos(TAU * i / n) * r * s, math.sin(TAU * i / n) * r * s) for i in range(n + 1)]
    frame_strip(p, M, ring(7.4), ring(6.6), -0.9, 1.2, 'Castle_Stone_Light')
    frame_strip(p, M, ring(6.7), ring(6.1), -1.3, 0.6, 'Gold')
    p.prism(ring(6.2)[:-1], 0.0, 0.8, 'Trade_Disc_Glow', M @ FLIP)
    trade_symbol(p, M @ T(0, -0.05, 0.3 * s) @ DRAW, 0.95 * s, depth=0.4)


# ---------------------------------------------------------------- statues ---
def trade_pet(p, kind='cat'):
    """stylized sitting pet statue holding a glowing trade cube out in front (faces -y, origin at its base)"""
    S, z = 'Trade_Statue', 0.0
    p.uvsphere((0, 0.5, z + 2.6), 2.3, S, 16, 10, (1.0, 1.1, 1.2))                   # body
    for s_ in (-1, 1):
        p.uvsphere((s_ * 1.7, 1.1, z + 1.3), 1.35, S, 12, 8, (0.85, 1.3, 1.0))      # haunches
        p.uvsphere((s_ * 0.9, -1.6, z + 0.4), 0.7, S, 10, 6, (1, 1.3, 0.6))         # feet
        sh = Vector((s_ * 1.45, -0.6, z + 3.9))                                     # arms reaching forward
        hand = Vector((s_ * 0.9, -2.9, z + 3.6))
        p.beam(sh, hand, 0.95, 0.95, S)
        p.uvsphere(hand, 0.6, S, 10, 6)
    p.uvsphere((0, -0.4, z + 6.3), 2.0, S, 16, 10, (1.05, 1.0, 0.95))                # head
    p.uvsphere((0, -2.1, z + 5.8), 0.85, S, 12, 8, (1.0, 0.9, 0.7))                  # muzzle
    p.ico((0, -2.85, z + 6.1), 0.25, 'Castle_Seam', 1)
    for s_ in (-1, 1):                                                               # happy closed eyes
        p.torus((s_ * 0.75, -2.05, z + 6.75), 0.28, 0.07, 'Castle_Seam', 10, 4,
                rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
        if kind == 'cat':
            tilt = Euler((0, s_ * 0.35, 0)).to_matrix()
            p.cyl(Vector((s_ * 1.2, -0.3, z + 8.1)) + tilt @ Vector((0, 0, 0.8)), 0.85, 1.7, S, 4, r2=0.05, rot=tilt)
        else:
            p.uvsphere((s_ * 1.9, -0.2, z + 5.8), 0.7, S, 10, 6, (0.5, 0.85, 1.6))  # floppy ears
    p.torus((0, -0.3, z + 4.7), 1.55, 0.28, 'Gold', 18, 5, rot=Euler((0.3, 0, 0)).to_matrix())   # gold scarf
    p.cone((0.6, -1.7, z + 4.5), 0.45, -1.2, 'Gold', 4)
    from foliage import tube
    tail = ([Vector((1.6, 2.4, z + 0.6)), Vector((2.6, 1.0, z + 0.4)), Vector((2.5, -1.2, z + 0.4))] if kind == 'cat'
            else [Vector((0, 2.5, z + 1.2)), Vector((0.5, 3.4, z + 2.6)), Vector((0.2, 3.2, z + 3.8))])
    tube(p, tail, [0.55, 0.45, 0.3], S, 6)
    # the glowing trade cube held between the paws
    bevel_box(p, I4, (0, -3.4, z + 4.0), (1.8, 1.8, 1.8), 'Trade_Ring_Glow', 0.2)
    trade_arrows(p, M_front(0, -4.32, z + 4.0), 0.32, 'Trade_White_Glow', 0.08)


def pedestal(p, rnd=None):
    rnd = rnd or random.Random(11)
    bevel_box(p, I4, (0, 0, 0.6), (7.6, 7.6, 1.2), 'Castle_Trim', 0.2)
    masonry(p, T(0, -3.0), -3.0, 3.0, 1.2, 5.8, rnd, 1.55, (2.0, 3.0), 6.0, backing=False)
    bevel_box(p, I4, (0, -3.05, 3.5), (3.6, 0.3, 3.4), 'Trade_Navy', 0.08)
    frame_strip(p, T(0, -3.05), [(-1.9, 1.7), (-1.9, 5.3), (1.9, 5.3), (1.9, 1.7), (-1.9, 1.7)],
                [(-1.6, 2.0), (-1.6, 5.0), (1.6, 5.0), (1.6, 2.0), (-1.6, 2.0)], -0.35, 0.05, 'Gold')
    paw(p, M_front(0, -3.25, 3.4), 2.4, 0.15, 'Gold')
    bevel_box(p, I4, (0, 0, 6.3), (7.2, 7.2, 1.0), 'Castle_Trim', 0.18)
    bevel_box(p, I4, (0, -3.65, 6.3), (6.6, 0.3, 0.35), 'Gold', 0.05)


# ---------------------------------------------------------------- portal ----
def energy_ring(p, R=6.8, t=0.28, mat='Trade_Ring_Glow', beads=8, bead_mat='Trade_Spark'):
    """ring in the local XZ plane around the origin (faces -y) with glowing beads - spin about local Y"""
    rx = Matrix.Rotation(math.pi / 2, 3, 'X')
    p.torus((0, 0, 0), R, t, mat, 48, 6, rot=rx)
    for i in range(beads):
        a = TAU * i / beads
        p.ico((math.cos(a) * R, -0.1, math.sin(a) * R), t * 1.9, bead_mat, 1)


def swirl(p, R=6.6, arms=6, mats=('Trade_Ring_Pink', 'Trade_Ring_Glow', 'Trade_Ring_Blue')):
    """spiral energy arms in the local XZ plane (faces -y), origin at the centre"""
    from foliage import tube
    for k in range(arms):
        a0 = TAU * k / arms
        path, radii = [], []
        for i in range(10):
            f = i / 9
            a = a0 + f * 1.6
            r = 3.4 + f * (R - 3.4)
            path.append(Vector((math.cos(a) * r, -0.05 - 0.3 * (1 - f), math.sin(a) * r)))
            radii.append(0.05 + 0.16 * math.sin(math.pi * f))
        tube(p, path, radii, mats[k % len(mats)], 5)


def sparkles(p, rnd, n=70, box=((-9, 9), (-9, 1), (1, 22))):
    """small glowing orbs + four-point stars"""
    (x0, x1), (y0, y1), (z0, z1) = box
    for i in range(n):
        q = Vector((rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(z0, z1)))
        if i % 4 == 0:
            s = rnd.uniform(0.35, 0.6)
            star = [(0, s * 1.6), (s * 0.3, s * 0.3), (s * 1.6, 0), (s * 0.3, -s * 0.3), (0, -s * 1.6),
                    (-s * 0.3, -s * 0.3), (-s * 1.6, 0), (-s * 0.3, s * 0.3)]
            p.prism(star, -0.05, 0.05, 'Trade_Spark', M_front(q.x, q.y, q.z))
        else:
            p.ico(q, rnd.uniform(0.1, 0.28), rnd.choice(('Trade_Spark', 'Trade_Ring_Pink', 'Trade_Ring_Glow')), 1)


def floor_emblem(p, r=7.5):
    """circular trading floor symbol: stone ring, gold ring, purple centre, gold trade symbol (faces up)"""
    p.cyl((0, 0, 0.12), r + 1.4, 0.24, 'Castle_Trim', 48)
    p.cyl((0, 0, 0.18), r + 0.5, 0.26, 'Gold', 48)
    p.cyl((0, 0, 0.22), r, 0.3, 'Trade_Purple', 48)
    p.torus((0, 0, 0.37), r * 0.78, 0.12, 'Gold', 48, 4)
    for k in range(16):
        a = TAU * k / 16
        bevel_box(p, T(math.cos(a) * r * 0.9, math.sin(a) * r * 0.9) @ Matrix.Rotation(a, 4, 'Z'),
                  (0, 0, 0.38), (0.9, 0.3, 0.08), 'Trade_Ring_Glow', 0.02)
    trade_symbol(p, T(0, 0.3, 0.37), r * 0.12, 'Gold', 'Gold', 0.08)


def crystal_cluster(p, rnd):
    from islands import crystal
    crystal(p, (0, 0, 0), 4.2, 0.8, 'Trade_Crystal')
    for k in range(4):
        a = TAU * k / 4 + rnd.uniform(-0.3, 0.3)
        crystal(p, (math.cos(a) * 0.9, math.sin(a) * 0.9, 0), rnd.uniform(1.8, 2.8), 0.5, 'Trade_Crystal',
                axis=(math.cos(a) * 0.5, math.sin(a) * 0.5, 1))


def _lib(name, builder, *a, **kw):
    p = Part('ASSET_' + name, KIT)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def build_trading_kit(parent):
    from shop import shop_lantern
    coll(KIT, parent)
    R = random.Random
    _lib('TradingPortal_Wall', lambda p: masonry(p, I4, -6, 6, 0, 10, R(1), 2.5, (3, 5)))
    _lib('TradingPortal_Pillar', lambda p: pillar(p, I4, 6.0, 0, 36, R(2), cap=None, band=0.56))
    _lib('TradingPortal_Arch', lambda p: voussoirs(p, I4, round_arch(23, 12, 16), round_arch(18.8, 12, 16), -0.8, 1.2,
                                                   R(3), 2.6))
    _lib('TradingPortal_Roof', lambda p: (bevel_box(p, I4, (0, 0, 0.6), (12, 5, 1.2), 'Castle_Trim', 0.2),
                                          bevel_box(p, I4, (0, -2.55, 0.6), (12, 0.3, 0.35), 'Gold', 0.05)))
    _lib('TradingPortal_GoldTrim', lambda p: bevel_box(p, I4, (0, 0, 0.2), (8, 0.35, 0.4), 'Gold', 0.06))
    _lib('TradingPortal_Sign', lambda p: trading_sign(p, I4))
    _lib('TradingPortal_Banner', pennant)
    _lib('TradingPortal_Statue', trade_pet, 'cat')
    _lib('TradingPortal_Statue_Dog', trade_pet, 'dog')
    _lib('TradingPortal_Pedestal', pedestal)
    _lib('TradingPortal_Core', lambda p: p.prism(round_arch(15, 12, 20), -0.2, 0.2, 'Trade_Portal', FLIP))
    _lib('TradingPortal_EnergyRing', energy_ring)
    _lib('TradingPortal_Particles', lambda p: sparkles(p, R(4), 40))
    _lib('TradingPortal_Lantern', shop_lantern)
    _lib('TradingPortal_Floor', floor_emblem)
    _lib('TradingPortal_TradingSymbol', lambda p: emblem(p, I4, 1.0))
    _lib('TradingPortal_Crystal', crystal_cluster, R(5))


def trading_sign(p, M):
    """purple sign board with a gently arched top and gold frame (text added separately); origin bottom centre"""
    W, H, A = 16.2, 5.4, 1.3
    top = [(W * math.cos(math.pi * i / 12), H + A * math.sin(math.pi * i / 12)) for i in range(13)]
    poly = [(-W, 0.0), (W, 0.0)] + top
    p.prism(poly, -0.2, 1.2, 'Trade_Purple', M @ FLIP)
    Wo, Wi = W + 0.45, W - 0.05
    outer = [(-Wo, -0.45)] + [(Wo * math.cos(math.pi - math.pi * i / 12), H + 0.45 + A * math.sin(math.pi - math.pi * i / 12))
                              for i in range(13)] + [(Wo, -0.45), (-Wo, -0.45)]
    inner = [(-Wi, 0.0)] + [(Wi * math.cos(math.pi - math.pi * i / 12), H - 0.05 + A * math.sin(math.pi - math.pi * i / 12))
                            for i in range(13)] + [(Wi, 0.0), (-Wi, 0.0)]
    frame_strip(p, M, outer, inner, -0.6, 0.4, 'Gold')


# ---------------------------------------------------------------- build -----
TREE = (('ARCHITECTURE', ROOT), ('Walls', 'ARCHITECTURE'), ('Pillars', 'ARCHITECTURE'), ('Arch', 'ARCHITECTURE'),
        ('Trim', 'ARCHITECTURE'), ('Roof', 'ARCHITECTURE'), ('SIGNAGE', ROOT), ('Trading_Plaza', 'SIGNAGE'),
        ('Trade_With_Other_Players', 'SIGNAGE'), ('PORTAL', ROOT), ('Core', 'PORTAL'), ('Rings', 'PORTAL'),
        ('Energy', 'PORTAL'), ('Particles', 'PORTAL'), ('STATUES', ROOT), ('Pet_Left', 'STATUES'),
        ('Pet_Right', 'STATUES'), ('BANNERS', ROOT), ('LANTERNS', ROOT), ('FLOOR', ROOT), ('LANDSCAPING', ROOT),
        ('LIGHTING', ROOT))


def build_trading_portal(parent_coll, loc=(0, 0, 0), rot_z=0.0):
    make_subcolls(ROOT, TREE, parent_coll, parent_coll is not None, 'trading', CN)
    root = empty('TradingPortal_Root', ROOT, loc, rot_z, 8)
    rnd = random.Random(2468)
    Z0 = 1.5                          # top of the platform
    yF = -3.0                         # front face of the central block
    yB = 7.0                          # back face
    AW, AH = 17.0, 12.0               # arch opening (width, spring height above Z0)
    A = lambda w, hs=AH: lifted(round_arch(w, hs, 16), 0, Z0)

    def fin(p):
        return p.finish(parent=root)

    def I(asset, name, col, xyz, rz=0.0, s=1.0, tilt=(0.0, 0.0)):
        o = inst(asset, name, c(col), xyz, rz, s, root)
        o.rotation_euler = (tilt[0], tilt[1], rz)
        return o

    # ---------------- platform, steps, forecourt -----------------------------------------------------
    fl = Part('TradingPortal_Platform', c('FLOOR'))
    bevel_box(fl, I4, (0, 3.0, Z0 / 2), (70, 18, Z0), 'Castle_Trim', 0.2)
    masonry(fl, T(0, -6.0), -35, 35, 0, Z0, rnd, Z0, (3, 5), 1.0, backing=False)
    for i in range(2):                                         # two steps up to the portal
        bevel_box(fl, I4, (0, -6.9 - i * 1.6, (Z0 - i * 0.75) / 2), (26 - i * 2, 1.6, Z0 - i * 0.75),
                  'Castle_Stone_Light', 0.12)
    fl.cyl((0, -6.0, 0.08), 30.0, 0.16, 'Castle_Stone_Light', 64)                 # paved forecourt
    fl.box((0, -6.6, Z0 + 0.03), (15, 1.0, 0.06), 'Trade_Ring_Glow')            # glowing threshold
    fin(fl)
    I('TradingPortal_Floor', 'TradingPortal_FloorSymbol', 'FLOOR', (0, -19.5, 0.1), 0, 1.0)
    fb = Part('TradingPortal_Floor_Bands', c('FLOOR'))
    for k in range(9):
        a0 = math.radians(197 + k * 16.5); a1 = a0 + math.radians(11)
        for r0, r1, z1, mat in ((21.0, 25.0, 0.24, 'Trade_Purple_Stone'), (20.5, 21.0, 0.27, 'Gold'),
                                (25.0, 25.5, 0.27, 'Gold')):
            fb.ring_sector(r0, r1, a0, a1, 0.12, z1, mat, 4)
    fb.ring_sector(29.0, 30.6, math.radians(180), math.radians(360), 0.0, 0.5, 'Castle_Trim', 32)
    for v in fb.bm.verts:                                      # ring sectors are built around the origin
        v.co.y -= 6.0
    fin(fb)

    # ---------------- central block with the deep layered arch --------------------------------------------
    w = Part('TradingPortal_Central_Block', c('Walls'))
    ZT = Z0 + 31.0
    skipA = lambda x, z, ww, h: inside(A(AW + 6.0), x, z)
    masonry(w, T(0, yF), -13.0, 13.0, Z0, ZT, rnd, 2.6, (3.2, 5.5), 1.6, skip=skipA, backing=False)
    masonry(w, T(0, yB) @ RZ(180), -13.0, 13.0, Z0, ZT, rnd, 2.6, (3.2, 5.5), 1.6, skip=skipA, backing=False)
    rect_minus_arch(w, T(0, yF), -12.9, 12.9, Z0, ZT, A(AW + 1.0), 1.0, yB - yF - 1.0, 'Castle_Seam')
    for s in (-1, 1):
        masonry(w, T(s * 13.0, 2.0) @ RZ(s * 90), -5.0, 5.0, Z0, ZT, rnd, 2.6, (3.0, 5.0), 1.4, backing=False)
    quoins(w, T(-13.0, yF), Z0, ZT, rnd, 3.4, 2.0, 2.6, side=1, mat='Castle_Trim')
    quoins(w, T(13.0, yF), Z0, ZT, rnd, 3.4, 2.0, 2.6, side=-1, mat='Castle_Trim')
    fin(w)
    ar = Part('TradingPortal_Arch', c('Arch'))
    for y0, y1, Mf in ((-1.4, 1.2, T(0, yF)), (-1.4, 1.2, T(0, yB) @ RZ(180))):
        voussoirs(ar, Mf, A(AW + 6.0), A(AW + 1.8), y0, y1, rnd, 2.8)
        frame_strip(ar, Mf, A(AW + 1.8), A(AW + 1.0), -1.0, 1.4, 'Gold')
    frame_strip(ar, T(0, 0), A(AW + 1.0), A(AW), yF + 0.4, yB - 0.4, 'Trade_Purple_Stone')        # chamber lining
    voussoirs(ar, T(0, 1.4), A(AW), A(AW - 2.2), -0.6, 2.4, rnd, 2.2, mat='Trade_Purple_Stone')    # inner recessed arch
    frame_strip(ar, T(0, 1.2), A(AW - 0.1), A(AW - 0.5), -0.6, 0.0, 'Gold')
    fin(ar)
    tr = Part('TradingPortal_Trim', c('Trim'))
    trim_run(tr, T(0, yF), -13, 13, Z0, h=1.2, out=1.0)
    for s in (-1, 1):
        trim_run(tr, T(s * 25.5, -0.3), -5.5, 5.5, Z0, h=1.0, out=0.8)
    fin(tr)

    # ---------------- crest with the trading emblem ----------------------------------------------------
    cr = Part('TradingPortal_Crest', c('Walls'))
    zc = ZT - 1.0
    crest = lifted(round_arch(24.0, 7.0, 18), 0, zc)
    cr.prism(crest, -2.6, 5.0, 'Castle_Stone_Light', FLIP)
    voussoirs(cr, T(0, -2.6), lifted(round_arch(27.0, 7.0, 18), 0, zc), crest, -0.8, 0.8, rnd, 2.6, keystone=True,
              backing=False)
    frame_strip(cr, T(0, -2.6), lifted(round_arch(27.6, 7.0, 18), 0, zc), lifted(round_arch(27.0, 7.0, 18), 0, zc),
                -0.6, 6.6, 'Gold')
    emblem(cr, T(0, -2.7, zc + 8.6), 0.92)
    paw(cr, M_front(0, 5.1, zc + 9.0, math.pi), 7.0, 0.3, 'Gold')                  # back of the crest
    fin(cr)

    # ---------------- sign -------------------------------------------------------------------------------
    sg = Part('TradingPortal_Sign', c('Trading_Plaza'))
    trading_sign(sg, T(0, yF - 3.4, Z0 + 23.6))
    for s in (-1, 1):
        sg.cyl(Vector((s * 16.9, yF - 4.0, Z0 + 26.3)), 1.1, 0.6, 'Gold', 12, axis='Y')
        sg.cyl(Vector((s * 16.9, yF - 4.35, Z0 + 26.3)), 0.75, 0.2, 'Trade_Ring_Glow', 12, axis='Y')
    fin(sg)
    text_mesh('TradingPortal_Sign_Text', 'TRADING PLAZA', c('Trading_Plaza'), 3.5, 0.6, 'Trade_White_Glow',
              (0, yF - 4.1, Z0 + 26.6), 0, root)
    rb = Part('TradingPortal_Ribbon', c('Trade_With_Other_Players'))
    bevel_box(rb, I4, (0, yF - 4.6, Z0 + 22.9), (23.0, 0.8, 2.6), 'Trade_Navy', 0.1)
    frame_strip(rb, T(0, yF - 4.6), [(-11.8, Z0 + 21.4), (-11.8, Z0 + 24.4), (11.8, Z0 + 24.4), (11.8, Z0 + 21.4),
                                     (-11.8, Z0 + 21.4)],
                [(-11.45, Z0 + 21.75), (-11.45, Z0 + 24.05), (11.45, Z0 + 24.05), (11.45, Z0 + 21.75),
                 (-11.45, Z0 + 21.75)], -0.5, 0.3, 'Gold')
    for s in (-1, 1):                                        # ribbon tails
        rb.prism([(s * 11.8, Z0 + 21.6), (s * 14.4, Z0 + 21.0), (s * 13.4, Z0 + 22.8), (s * 14.4, Z0 + 24.4),
                  (s * 11.8, Z0 + 24.2)][::(1 if s > 0 else -1)], yF - 4.4, yF - 3.9, 'Trade_Navy', FLIP)
    fin(rb)
    text_mesh('TradingPortal_Ribbon_Text', 'TRADE WITH OTHER PLAYERS', c('Trade_With_Other_Players'), 1.4, 0.3,
              'Trade_White_Glow', (0, yF - 5.15, Z0 + 22.85), 0, root)

    # ---------------- pillars, side walls, outer pillars ------------------------------------------------------
    pl = Part('TradingPortal_Pillars', c('Pillars'))
    for s in (-1, 1):
        pillar(pl, T(s * 16.8, 1.0), 6.0, Z0, 34.0, rnd, cap=None, band=0.5)
        pillar(pl, T(s * 33.0, 1.0), 4.4, Z0, 25.0, rnd, cap=None, band=0.5, panel=False)
    fin(pl)
    sw = Part('TradingPortal_SideWalls', c('Walls'))
    for s in (-1, 1):
        xa, xb = (19.6, 31.0)
        sw.box((s * (xa + xb) / 2, 2.0, (Z0 + 23.0) / 2), (xb - xa, 3.6, 23.0 - Z0), 'Castle_Seam')
        masonry(sw, T(0, 0.0), *(sorted((s * xa, s * xb))), Z0, 23.0, rnd, 2.4, (3, 5.5), 1.4, backing=False)
        masonry(sw, T(0, 4.0) @ RZ(180), *(sorted((-s * xa, -s * xb))), Z0, 23.0, rnd, 2.4, (3, 5.5), 1.4, backing=False)
    fin(sw)
    rf = Part('TradingPortal_Roof', c('Roof'))
    bevel_box(rf, I4, (0, 2.0, ZT + 0.4), (27.6, 11.4, 1.0), 'Castle_Trim', 0.2)
    bevel_box(rf, I4, (0, yF - 0.75, ZT + 0.4), (26.4, 0.3, 0.35), 'Gold', 0.05)
    for s in (-1, 1):
        bevel_box(rf, I4, (s * 25.3, 2.0, 23.6), (12.4, 5.2, 1.2), 'Castle_Trim', 0.2)
        bevel_box(rf, I4, (s * 25.3, -0.65, 23.6), (11.6, 0.3, 0.35), 'Gold', 0.05)
        for k in range(4):                                     # little crenels on the side walls
            bevel_box(rf, I4, (s * (20.9 + k * 2.8), 2.0, 24.9), (1.6, 3.6, 1.4), 'Castle_Stone_Light', 0.15)
    fin(rf)
    for s in (-1, 1):
        LR = 'LR'[s > 0]
        I('TradingPortal_Banner', f'TradingPortal_Banner_{LR}', 'BANNERS', (s * 25.3, -1.1, 21.6), 0, 1.0)
        I('TradingPortal_Lantern', f'TradingPortal_PillarLantern_{LR}', 'LANTERNS', (s * 16.8, 1.0, Z0 + 34.2), 0, 1.4)
        I('TradingPortal_Lantern', f'TradingPortal_OuterLantern_{LR}', 'LANTERNS', (s * 33.0, 1.0, Z0 + 25.2), 0, 1.15)
        I('Shop_Lantern_Wall', f'TradingPortal_WallLantern_{LR}', 'LANTERNS', (s * 16.8, -2.0, Z0 + 13.0), 0, 0.9)
        lantern_light(f'TradingPortal_Light_Pillar_{LR}', c('LIGHTING'), root, (s * 16.8, -1.5, Z0 + 37.0), 900)
        lantern_light(f'TradingPortal_Light_Outer_{LR}', c('LIGHTING'), root, (s * 33.0, -1.5, Z0 + 27.5), 600)

    # ---------------- statues on pedestals ----------------------------------------------------------------
    for s, kind, col in ((-1, 'TradingPortal_Statue', 'Pet_Left'), (1, 'TradingPortal_Statue_Dog', 'Pet_Right')):
        x, y = s * 13.2, -12.5
        I('TradingPortal_Pedestal', f'TradingPortal_Pedestal_{col}', col, (x, y, 0), 0, 1.0)
        I(kind, f'TradingPortal_{col}', col, (x, y, 6.8), math.radians(-s * 62), 1.0)

    # ---------------- portal effect (separate, animatable pieces) ---------------------------------------------
    zc0 = Z0 + AH                                              # arch centre
    core = Part('TradingPortal_Core', c('Core'))
    core.prism(A(AW - 2.2), 2.2, 2.6, 'Trade_Portal', FLIP)
    fin(core)
    for k, (R, y, mat, sc) in enumerate(((6.9, 1.7, 'Trade_Ring_Glow', 1.0), (5.2, 1.4, 'Trade_Ring_Pink', 0.75),
                                         (3.4, 1.1, 'Trade_Ring_Blue', 0.5))):
        rg = Part(f'TradingPortal_EnergyRing_{k}', c('Rings'))
        energy_ring(rg, R, 0.28 if k == 0 else 0.22, mat, 8 + 2 * k)
        fin(rg).location = (0, y, zc0 - 1.0)
    en = Part('TradingPortal_Energy_Swirl', c('Energy'))
    swirl(en, 6.4)
    fin(en).location = (0, 2.0, zc0 - 1.0)
    ic = Part('TradingPortal_Energy_Icon', c('Energy'))
    trade_symbol(ic, M_front(0, 0, 0.6), 0.95, 'Trade_Icon_Glow', 'Trade_Icon_Glow', 0.3)
    fin(ic).location = (0, 0.9, zc0 - 1.0)
    sp = Part('TradingPortal_Particles', c('Particles'))
    sparkles(sp, random.Random(77), 70, ((-8, 8), (-12, 1.0), (Z0 + 1, Z0 + 21)))
    sparkles(sp, random.Random(78), 30, ((-22, 22), (-26, -8), (Z0 + 2, Z0 + 14)))
    fin(sp)
    tg = Part('TradingPortal_TeleportTrigger', c('Core'))
    tg.box((0, 2.4, Z0 + 9.0), (AW - 3.0, 4.0, 18.0), 'Trade_Ring_Glow')
    t = fin(tg)
    t.display_type = 'WIRE'
    t.hide_render = True
    for k, (x, y, z, e) in enumerate(((0, -3, Z0 + 10, 2600), (0, 4.5, Z0 + 10, 1800), (0, -14, Z0 + 4, 700))):
        lantern_light(f'TradingPortal_Light_Portal_{k}', c('LIGHTING'), root, (x, y, z), e, (0.62, 0.32, 1.0), 3.0)

    # ---------------- lanterns, landscaping ---------------------------------------------------------------------
    for k, (x, y) in enumerate(((-21.5, -24.0), (21.5, -24.0), (-28.5, -12.5), (28.5, -12.5))):
        I('Castle_Lantern', f'TradingPortal_PathLantern_{k}', 'LANTERNS', (x, y, 0), 0, 0.95)
        lantern_light(f'TradingPortal_Light_Path_{k}', c('LIGHTING'), root, (x, y - 1.5, 9.0), 500)
    for k, (x, y, nm, sc, rz) in enumerate((
            (-25.3, -4.6, 'Stone_Planter', 1.0, 0.0), (25.3, -4.6, 'Stone_Planter', 1.0, 0.0),
            (-18.0, -12.0, 'Bush_01', 1.1, 0.4), (18.0, -12.0, 'Bush_02', 1.1, 1.2),
            (-8.5, -13.5, 'Ground_Plant_02', 0.9, 0.0), (8.5, -13.5, 'Ground_Plant_02', 0.9, 1.0),
            (-38.0, -4.0, 'Bush_03', 1.3, 0.2), (38.0, -4.0, 'Bush_01', 1.3, 1.0),
            (-30.0, 14.0, 'Tree_Medium_High', 0.9, 0.3), (30.0, 14.0, 'Tree_Large_High', 0.75, 1.3),
            (-12.0, 13.0, 'Tree_Small', 1.0, 0.5), (12.0, 13.0, 'Tree_Small', 0.9, 2.0),
            (-38.5, 8.0, 'Ground_Plant_01', 1.3, 0.0), (38.5, 8.0, 'Ground_Plant_01', 1.3, 1.0))):
        I(nm, f'TradingPortal_Land_{nm}_{k}', 'LANDSCAPING', (x, y, 0), rz, sc)
    for k, (x, y, sc) in enumerate(((-16.5, -21.5, 1.0), (16.5, -21.5, 0.9), (-35.0, -10.0, 0.8), (35.0, -10.0, 0.8))):
        I('TradingPortal_Crystal', f'TradingPortal_Crystal_{k}', 'LANDSCAPING', (x, y, 0.1), k * 0.9, sc)
    from foliage import vine
    vv = Part('TradingPortal_Vines', c('LANDSCAPING'))
    for x, y, z in ((-13.2, yF - 0.4, ZT), (13.2, yF - 0.4, ZT), (-31.0, -0.4, 23.0), (31.0, -0.4, 23.0),
                    (-19.8, -0.4, 23.0), (19.8, -0.4, 23.0)):
        vine(vv, (x, y, z), rnd.uniform(6, 13), rnd, 1.1)
    fin(vv)
    return root


def build_trading_cameras(root_loc=(0, 0, 0), rot_z=0.0, coll_name='CAMERAS', prefix='CAM_TradingPortal', only=None):
    M = Matrix.Translation(root_loc) @ Matrix.Rotation(rot_z, 4, 'Z')
    out = {}
    for name, loc, tgt, lens in (('Front', (0, -82, 15), (0, 0, 22), 28), ('Close', (-5, -36, 26), (0, 0, 32), 32),
                                 ('Side', (-62, -48, 20), (0, -2, 18), 28), ('Back', (24, 64, 20), (0, 0, 18), 28),
                                 ('Top', (0, -14, 150), (0, -12, 0), 32), ('Player', (5, -42, 5.2), (0, 0, 15), 24)):
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
