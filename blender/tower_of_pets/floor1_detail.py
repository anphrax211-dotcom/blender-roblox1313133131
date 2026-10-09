"""TOWER OF PETS - FLOOR 1 global environment detail pass (on top of floor1.py's base terrain).

Keeps the layout exactly as floor1.py builds it and dresses every landmass to a ~60-70 % baseline:
  * a reusable asset library: the hub's own trees (Tree_*_Low, plus a darker Mystic Wilds re-colour of the same
    meshes), bushes, ground plants, vines, moss drapes, rocks, grass and lanterns from the foliage / islands packs, and
    a small set of new Floor 1 props in the same low-poly style (flowers, ferns, reeds, lily pads, mushrooms, stumps,
    logs, signposts, benches, barrels, crates, rope barriers, broken columns / walls, ruin arches, temple platforms,
    mist puffs, foam rings);
  * scatter: every placement is a linked duplicate of a library mesh (SCATTER/<category>), chosen per area by density
    tables and kept off paths, pads, reserved footprints, water, steep ground and island rims, with noise-driven
    groves and clearings so riders always have open ground;
  * routes: lanterns along main roads, signposts at junctions, benches at checkpoints, path-edge pebbles and fences;
  * bridges: wood / stone / rope bridges built along the paths where they cross open sky (rock spans stay terrain);
  * water: waterfall mist + foam + rocks, river-bank rocks and reeds, lily pads, small cliff cascades (floor1.py);
  * cliffs: moss drapes, vines and roots hanging from the rims, floating debris under the islands;
  * background: distant islands with trees and falls, mountain spires rising from the cloud sea, cloud banks.
Every placement is also recorded (PLACED) so build_floor1_pack.py can write the Roblox scatter scripts.
"""
import math, random
import numpy as np
import bpy
from mathutils import Vector, Matrix
from common import Part, MATS, mat_plain, mat_noise, coll, ASSETS, TAU
import common, foliage, islands
import floor1 as F

LIB = 'F1_ASSET_LIBRARY'
SCATTER = 'SCATTER'
PLACED = []                    # (category, asset, x, y, z, rot_z, scale)
W = F.WORLD

# category -> how Roblox treats it (see Floor1_Scatter.lua)
CATEGORIES = ('Trees', 'Foliage', 'Rocks', 'Props', 'Ruins', 'Water', 'Cliffs', 'Landmarks', 'Background')


# ---------------------------------------------------------------- materials -
def build_detail_materials():
    P, N = mat_plain, mat_noise
    foliage.build_foliage_materials()
    islands.build_island_materials()
    P('Leaves_Mystic_Light', (0.06, 0.52, 0.30), 0.65)
    P('Leaves_Mystic_Mid', (0.03, 0.36, 0.20), 0.7)
    P('Leaves_Mystic_Dark', (0.01, 0.17, 0.10), 0.8)
    P('Leaves_Mystic_Highlight', (0.10, 0.70, 0.52), 0.6)
    P('Flower_Pink', (1.0, 0.30, 0.62), 0.6)
    P('Flower_Yellow', (1.0, 0.82, 0.10), 0.6)
    P('Flower_White', (0.95, 0.95, 1.0), 0.6)
    P('Flower_Purple', (0.62, 0.30, 1.0), 0.6)
    P('Flower_Center', (1.0, 0.70, 0.08), 0.6)
    P('Fern_Green', (0.10, 0.55, 0.12), 0.7)
    P('Reed_Green', (0.30, 0.55, 0.12), 0.8)
    P('Reed_Brown', (0.40, 0.24, 0.10), 0.85)
    P('Lily_Pad', (0.16, 0.58, 0.14), 0.6)
    P('Mushroom_Red', (0.92, 0.16, 0.12), 0.6)
    P('Mushroom_Stem', (0.95, 0.90, 0.80), 0.7)
    P('Mushroom_Glow', (0.10, 0.85, 1.0), 0.4, emit=1.2)
    P('Sign_Wood', (0.62, 0.38, 0.18), 0.8)
    P('Barrel_Wood', (0.50, 0.28, 0.12), 0.8)
    P('Iron_Band', (0.25, 0.25, 0.28), 0.5, metal=0.6)
    N('Ruin_Stone', (0.70, 0.66, 0.56), (0.78, 0.74, 0.64), 0.85, 0.08, 0.12, 0.6)
    N('Ruin_Stone_Mossy', (0.46, 0.56, 0.32), (0.56, 0.64, 0.38), 0.85, 0.08, 0.12, 0.6)
    N('Temple_Stone', (0.86, 0.84, 0.80), (0.93, 0.92, 0.88), 0.8, 0.08, 0.1, 0.6)
    P('Temple_Gold', (1.0, 0.72, 0.22), 0.35, metal=0.6)
    N('Bridge_Stone', (0.72, 0.70, 0.66), (0.80, 0.78, 0.74), 0.85, 0.08, 0.12, 0.6)
    N('Fortress_Stone', (0.48, 0.24, 0.16), (0.56, 0.30, 0.20), 0.85, 0.08, 0.12, 0.6)
    P('Fortress_Roof', (0.80, 0.30, 0.10), 0.6)
    P('Fortress_Glow', (1.0, 0.45, 0.08), 0.4, emit=1.5)
    P('Mist', (0.95, 0.98, 1.0), 0.9, emit=0.3, alpha=0.45)
    P('Foam', (0.95, 0.99, 1.0), 0.6, emit=0.4)


# ---------------------------------------------------------------- new assets (same low-poly language as the hub)
def _lib(name, builder, *a, **kw):
    p = Part('ASSET_' + name, LIB)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def flower_cluster(p, rnd, mat):
    for k in range(7):
        a = rnd.uniform(0, TAU); r = rnd.uniform(0, 0.9)
        h = rnd.uniform(0.7, 1.5)
        b = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        p.cyl(b + Vector((0, 0, h / 2)), 0.06, h, 'Leaves_Mid', 4)
        c = b + Vector((0, 0, h))
        for j in range(5):
            aa = TAU * j / 5
            p.ico(c + Vector((math.cos(aa) * 0.22, math.sin(aa) * 0.22, 0)), 0.17, mat, 1, (1, 1, 0.5), smooth=False)
        p.ico(c + Vector((0, 0, 0.05)), 0.12, 'Flower_Center', 1, smooth=False)
    foliage.broad_plant(p, rnd, 4, 0.9, 0.35, 0.25, mats=('Leaves_Mid', 'Leaves_Light'))


def fern(p, rnd):
    foliage.broad_plant(p, rnd, 9, 2.6, 0.55, 0.55, mats=('Fern_Green', 'Leaves_Mid', 'Leaves_Dark'))


def reeds(p, rnd):
    for k in range(11):
        a = rnd.uniform(0, TAU); r = rnd.uniform(0, 1.2)
        h = rnd.uniform(3.0, 5.5)
        b = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        tilt = Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), 1)).normalized()
        p.beam(b, b + tilt * h, 0.12, 0.12, 'Reed_Green')
        if k % 3 == 0:
            c = b + tilt * (h * 0.82)
            p.beam(c, c + tilt * 0.9, 0.32, 0.32, 'Reed_Brown')


def lily_pad(p, rnd, flower=False):
    for k in range(3):
        a = rnd.uniform(0, TAU); r = rnd.uniform(0.6, 2.2) if k else 0
        p.cyl((math.cos(a) * r, math.sin(a) * r, 0.05), rnd.uniform(0.8, 1.4), 0.1, 'Lily_Pad', 10)
    if flower:
        for j in range(6):
            aa = TAU * j / 6
            p.ico((math.cos(aa) * 0.3, math.sin(aa) * 0.3, 0.3), 0.28, 'Flower_Pink', 1, (1, 0.5, 0.8), smooth=False)
        p.ico((0, 0, 0.35), 0.18, 'Flower_Yellow', 1, smooth=False)


def mushrooms(p, rnd, cap='Mushroom_Red'):
    for k in range(3):
        a = rnd.uniform(0, TAU); r = rnd.uniform(0, 0.8) if k else 0
        h = rnd.uniform(0.6, 1.4) * (1.4 if k == 0 else 1)
        b = (math.cos(a) * r, math.sin(a) * r)
        p.cyl((b[0], b[1], h / 2), 0.16 * h + 0.1, h, 'Mushroom_Stem', 8)
        p.uvsphere((b[0], b[1], h), 0.45 * h + 0.25, cap, 10, 5, (1, 1, 0.55))


def stump(p, rnd):
    foliage.tube(p, [Vector((0, 0, -0.3)), Vector((0, 0, 0.8)), Vector((0, 0, 1.5))], [1.6, 1.25, 1.2], 'Trunk', 8)
    p.cyl((0, 0, 1.52), 1.1, 0.06, 'Sign_Wood', 8)
    foliage.roots(p, 1.2, 4, rnd, 2.0, 0.8)


def log(p, rnd):
    p.cyl((0, 0, 0.85), 0.85, 7.5, 'Trunk', 8, axis='X')
    for s in (-1, 1):
        p.cyl((s * 3.77, 0, 0.85), 0.75, 0.06, 'Sign_Wood', 8, axis='X')
    foliage.tube(p, foliage.curve((1.0, 0.4, 1.4), (2.5, 1.8, 3.0), (0.5, 0, 0.8), 3), [0.3, 0.2, 0.1], 'Trunk', 5)
    p.ico((-1.5, 0, 1.6), 0.6, 'Moss', 1, (1.6, 1, 0.35), smooth=False)


def signpost(p, rnd):
    p.box((0, 0, 3.0), (0.5, 0.5, 6.0), 'Sign_Wood')
    p.cone((0, 0, 6.0), 0.45, 0.4, 'Sign_Wood', 4)
    for z, a in ((4.9, 0.25), (3.9, -0.35), (2.9, 0.9)):
        R = Matrix.Rotation(a, 3, 'Z')
        p.box(R @ Vector((1.3, 0, z)), (2.8, 0.18, 0.7), 'Wood_Plank', R)
        p.box(R @ Vector((2.85, 0, z)), (0.45, 0.18, 0.45), 'Wood_Plank', R @ Matrix.Rotation(math.pi / 4, 3, 'Y'))


def bench(p, rnd):
    for x in (-2.0, 2.0):
        p.box((x, 0, 0.55), (0.4, 1.4, 1.1), 'Wood_Dark')
    for y in (-0.38, 0.0, 0.38):
        p.box((0, y, 1.15), (5.2, 0.34, 0.16), 'Wood_Plank')
    p.box((0, 0.72, 1.9), (5.2, 0.16, 0.9), 'Wood_Plank')


def barrel(p, rnd):
    p.cyl((0, 0, 1.2), 0.95, 2.4, 'Barrel_Wood', 12, smooth=True)
    for z in (0.35, 1.2, 2.05):
        p.torus((0, 0, z), 1.0, 0.09, 'Iron_Band', 14, 4)


def crate(p, rnd):
    p.box((0, 0, 1.0), (2.0, 2.0, 2.0), 'Wood_Plank')
    for s in (-1, 1):
        p.beam(Vector((-0.8, s * 1.02, 0.2)), Vector((0.8, s * 1.02, 1.8)), 0.3, 0.08, 'Wood_Dark')
        p.box((0, s * 1.02, 0.15), (2.04, 0.08, 0.3), 'Wood_Dark')
        p.box((0, s * 1.02, 1.85), (2.04, 0.08, 0.3), 'Wood_Dark')


def rope_barrier(p, rnd):
    for x in (-5.0, 0.0, 5.0):
        p.cyl((x, 0, 1.6), 0.25, 3.2, 'Wood_Dark', 6)
    for z in (2.6, 1.6):
        for a, b in ((-5, 0), (0, 5)):
            p.beam(Vector((a, 0, z)), Vector((b, 0, z - 0.25)), 0.12, 0.12, 'Rope_Tan')


def broken_column(p, rnd, h):
    p.box((0, 0, 0.5), (3.4, 3.4, 1.0), 'Ruin_Stone')
    p.cyl((0, 0, 1.2), 1.4, 0.4, 'Ruin_Stone', 10)
    p.cyl((0, 0, 1.4 + h / 2), 1.15, h, 'Ruin_Stone', 10)
    for k in range(3):                                         # jagged broken top
        a = TAU * k / 3 + rnd.uniform(0, 1)
        p.box((math.cos(a) * 0.5, math.sin(a) * 0.5, 1.4 + h + 0.3), (1.0, 0.9, rnd.uniform(0.4, 1.2)), 'Ruin_Stone',
              Matrix.Rotation(a, 3, 'Z'))
    p.ico((1.0, 0, 1.4 + h * 0.5), 0.6, 'Ruin_Stone_Mossy', 1, (0.5, 1.3, 1.6), smooth=False)
    p.box((2.8, 1.2, 0.5), (1.6, 1.4, 1.0), 'Ruin_Stone', Matrix.Rotation(0.4, 3, 'Z'))     # fallen drum


def broken_wall(p, rnd):
    L = 14.0
    for row in range(5):
        x = -L / 2 + (0.9 if row % 2 else 0)
        top = 5 - abs(row - 1)
        while x < L / 2 - 1:
            w = rnd.uniform(1.6, 2.6)
            if row < 2 or rnd.random() < 0.82 - row * 0.08:
                p.box((x + w / 2, 0, 0.6 + row * 1.15), (w - 0.12, 1.4, 1.05),
                      'Ruin_Stone_Mossy' if rnd.random() < 0.18 else 'Ruin_Stone')
            x += w
        if top < 0:
            break
    for k in range(3):
        p.box((rnd.uniform(-6, 6), rnd.uniform(1.4, 3.0), 0.4), (1.8, 1.2, 0.8), 'Ruin_Stone',
              Matrix.Rotation(rnd.uniform(0, 3), 3, 'Z'))


def ruin_arch(p, rnd):
    for x in (-4.5, 4.5):
        p.box((x, 0, 0.5), (3.0, 3.0, 1.0), 'Ruin_Stone')
        p.box((x, 0, 5.0), (2.2, 2.2, 8.0), 'Ruin_Stone')
    arch = common.round_arch(11.2, 0.1, 10)
    inner = common.round_arch(6.8, 0.1, 10)
    from castle import frame_strip
    frame_strip(p, Matrix.Translation((0, 1.1, 9.0)), arch, inner, -2.2, 0.0, 'Ruin_Stone')
    p.box((3.6, 0, 13.2), (2.6, 2.2, 1.6), 'Ruin_Stone_Mossy')


def stone_fragment(p, rnd):
    for k in range(4):
        c = (rnd.uniform(-2.5, 2.5), rnd.uniform(-2.5, 2.5), 0.4)
        p.box(c, (rnd.uniform(1.0, 2.4), rnd.uniform(0.8, 1.8), rnd.uniform(0.6, 1.2)),
              'Ruin_Stone' if k % 3 else 'Ruin_Stone_Mossy', Matrix.Rotation(rnd.uniform(0, 3), 3, 'Z'))


def temple_platform(p, rnd):
    pts = [(math.cos(TAU * k / 8 + TAU / 16) * 9, math.sin(TAU * k / 8 + TAU / 16) * 9) for k in range(8)]
    p.prism(pts, 0, 1.2, 'Temple_Stone')
    p.prism([(x * 0.8, y * 0.8) for x, y in pts], 1.2, 1.6, 'Temple_Stone')
    p.cyl((0, 0, 1.65), 2.4, 0.1, 'Temple_Gold', 16)
    p.cone((0, 0, -3.0), 8.0, -0.01, 'Island_Rock', 8, r_top=0.5)          # a rough rock root below it


def mist_puff(p, rnd):
    for k in range(4):
        p.ico((rnd.uniform(-3, 3), rnd.uniform(-3, 3), rnd.uniform(0, 2)), rnd.uniform(2.5, 4.0), 'Mist', 2,
              (1, 1, 0.6))


def foam_ring(p, rnd):
    p.torus((0, 0, 0.15), 4.0, 0.7, 'Foam', 20, 5, smooth=False)
    for k in range(7):
        a = TAU * k / 7
        p.ico((math.cos(a) * 4.2, math.sin(a) * 4.2, 0.3), 0.9, 'Foam', 1, (1, 1, 0.5), smooth=False)


def recolour(src, name, swap):
    """same mesh as `src` with other materials (e.g. the hub tree in Mystic Wilds greens)"""
    me = ASSETS[src].data.copy()
    me.name = 'ASSET_' + name
    for i, m in enumerate(me.materials):
        if m and m.name in swap:
            me.materials[i] = MATS[swap[m.name]]
    ob = bpy.data.objects.new(name, me)
    coll(LIB).objects.link(ob)
    ASSETS[name] = ob
    return ob


def build_detail_assets():
    """the hub asset packs + the new Floor 1 props, in one hidden library collection"""
    build_detail_materials()
    common.build_assets()                                          # lantern posts, clouds, small rocks ...
    foliage.build_foliage_assets(None)
    islands.build_island_assets(None)
    R = random.Random
    for c in ('Pink', 'Yellow', 'White', 'Purple'):
        _lib(f'Flower_Cluster_{c}', flower_cluster, R(len(c)), f'Flower_{c}')
    _lib('Fern', fern, R(5))
    _lib('Reeds', reeds, R(6))
    _lib('Lily_Pads', lily_pad, R(7))
    _lib('Lily_Pads_Flower', lily_pad, R(8), True)
    _lib('Mushrooms', mushrooms, R(9))
    _lib('Mushrooms_Glow', mushrooms, R(10), 'Mushroom_Glow')
    _lib('Stump', stump, R(11))
    _lib('Log', log, R(12))
    _lib('Signpost', signpost, R(13))
    _lib('Bench', bench, R(14))
    _lib('Barrel', barrel, R(15))
    _lib('Crate', crate, R(16))
    _lib('Rope_Barrier', rope_barrier, R(17))
    _lib('Broken_Column_A', broken_column, R(18), 6.0)
    _lib('Broken_Column_B', broken_column, R(19), 11.0)
    _lib('Broken_Wall', broken_wall, R(20))
    _lib('Ruin_Arch', ruin_arch, R(21))
    _lib('Stone_Fragments', stone_fragment, R(22))
    _lib('Temple_Platform', temple_platform, R(23))
    _lib('Mist_Puff', mist_puff, R(24))
    _lib('Foam_Ring', foam_ring, R(25))
    import castle, floor1_entrance, shop, hatchery
    castle.build_castle_kit(None)                                  # hub stone lanterns, banners, blocks ...
    shop.build_shop_materials(); hatchery.build_hatchery_materials()
    shop.build_shop_kit(None); hatchery.build_hatchery_kit(None)   # the hub Shop / Hatchery kits (entrance)
    floor1_entrance.build_entrance_assets()
    import floor1_village, floor1_fortress
    floor1_village.build_village_assets()
    floor1_fortress.build_fortress_assets()
    import floor1_jungle
    floor1_jungle.build_jungle_assets()
    mystic = {'Leaves_Light': 'Leaves_Mystic_Light', 'Leaves_Mid': 'Leaves_Mystic_Mid',
              'Leaves_Dark': 'Leaves_Mystic_Dark', 'Leaves_Highlight': 'Leaves_Mystic_Highlight'}
    for t in ('Tree_Large_Low', 'Tree_Medium_Low', 'Tree_Small_Low', 'Tree_Tall_Thin_Low', 'Bush_01', 'Bush_03'):
        recolour(t, t.replace('_Low', '') + '_Mystic' if 'Tree' in t else t + '_Mystic', mystic)
    # the library is only the source of the linked duplicates: keep it out of renders and exports
    for name in (LIB, common.ASSET_COLL, foliage.FOLIAGE_ROOT, islands.ROOT, castle.KIT, shop.KIT,
                 hatchery.CN.get(hatchery.KIT, hatchery.KIT)):
        c = bpy.data.collections.get(name)
        if c is None:
            continue
        c.hide_render = True
        c.hide_viewport = True


# ---------------------------------------------------------------- placement helpers
def place(cat, asset, x, y, z, rot=0.0, s=1.0):
    asset = str(asset)
    ob = bpy.data.objects.new(f'{asset}', ASSETS[asset].data)
    coll(f'Scatter_{cat}', SCATTER).objects.link(ob)        # (prefixed: the hub packs own 'TREES', 'Landmarks'...)
    ob.location = (x, y, z)
    ob.rotation_euler = (0, 0, rot)
    ob.scale = (s, s, s)
    PLACED.append((cat, asset, x, y, z, rot, s))
    return ob


def grid_index(T, x, y):
    i = np.clip(np.rint((np.asarray(x) + F.EXT) / F.S).astype(int), 0, T.n - 1)
    j = np.clip(np.rint((np.asarray(y) + F.EXT) / F.S).astype(int), 0, T.n - 1)
    return i, j


def ground_z(T, x, y):
    """bilinear terrain height at many points"""
    fx = (np.asarray(x) + F.EXT) / F.S; fy = (np.asarray(y) + F.EXT) / F.S
    i = np.clip(fx.astype(int), 0, T.n - 2); j = np.clip(fy.astype(int), 0, T.n - 2)
    u, v = fx - i, fy - j
    H = T.H
    return (H[i, j] * (1 - u) * (1 - v) + H[i + 1, j] * u * (1 - v) + H[i, j + 1] * (1 - u) * v
            + H[i + 1, j + 1] * u * v)


def candidates(T, spacing, seed):
    """jittered grid over the land's bounding box"""
    rng = np.random.default_rng(seed)
    land = T.land
    x0, x1 = T.X[land].min(), T.X[land].max(); y0, y1 = T.Y[land].min(), T.Y[land].max()
    gx, gy = np.meshgrid(np.arange(x0, x1, spacing), np.arange(y0, y1, spacing), indexing='ij')
    x = gx.ravel() + rng.uniform(-0.45, 0.45, gx.size) * spacing
    y = gy.ravel() + rng.uniform(-0.45, 0.45, gy.size) * spacing
    return x, y, rng


def keepout_mask(T):
    """cells kept clear for gameplay: pads, reserved footprints, spawn (True = keep clear)"""
    X, Y = T.X, T.Y
    m = np.zeros(X.shape, dtype=bool)
    for name, cx, cy, r, z in F.PADS:
        if name in ('Meadow_Riding_Field', 'Jungle_Clearing', 'Lake_Islet', 'World_Tree_Pad'):
            r = r * 0.8 if name != 'World_Tree_Pad' else r * 1.05
        if name.startswith(('House_', 'Stall_')):                # village: no big wild trees over the roofs
            r = r * 2.0
        wx, wy = F.px(cx, cy)
        m |= np.hypot(X - wx, Y - wy) < r + 12
    for name, cx, cy, kind, a, b in F.RESERVED:
        wx, wy = F.px(cx, cy)
        if kind == 'circle':
            m |= np.hypot(X - wx, Y - wy) < a + 10
        else:
            m |= (np.abs(X - wx) < a / 2 + 10) & (np.abs(Y - wy) < b / 2 + 10)
    return m


# per-area dressing: trees / bushes / plants / flowers / rocks / grass (per million sq studs), tree scale range,
# tree mix, extras
DRESS = {
    'Floor_Entrance':     dict(trees=19, bushes=60, plants=28, flowers=72, rocks=12, grass=48, scale=(2.0, 3.2)),
    'Sunlit_Meadows':     dict(trees=42, bushes=40, plants=22, flowers=96, rocks=14, grass=66, scale=(2.2, 4.0)),
    'Verdant_Village':    dict(trees=27, bushes=50, plants=22, flowers=66, rocks=8, grass=48, scale=(2.0, 3.4)),
    'Whispering_Forest':  dict(trees=200, bushes=110, plants=66, flowers=24, rocks=26, grass=36, scale=(2.6, 5.0),
                               logs=12),
    'Riverfall_Valley':   dict(trees=104, bushes=120, plants=77, flowers=42, rocks=40, grass=54, scale=(2.4, 4.4),
                               logs=6),
    'Emerald_Lake':       dict(trees=76, bushes=70, plants=33, flowers=36, rocks=20, grass=42, scale=(2.4, 4.0)),
    'Lotus_Swamp':        dict(trees=30, bushes=100, plants=61, flowers=24, rocks=10, grass=30, scale=(2.0, 3.4),
                               reeds=170, mushrooms=20),
    'Ancient_Ruins':      dict(trees=27, bushes=50, plants=22, flowers=18, rocks=26, grass=36, scale=(2.2, 3.6),
                               ruins=55),
    'Cloudridge_Peaks':   dict(trees=23, bushes=12, plants=6, flowers=5, rocks=55, grass=12, scale=(2.2, 4.0),
                               alpine=True),
    'World_Tree_Grove':   dict(trees=152, bushes=100, plants=61, flowers=24, rocks=18, grass=24, scale=(3.0, 5.6),
                               mystic=True, mushrooms=30),
    'Mossy_Caverns':      dict(trees=171, bushes=120, plants=77, flowers=12, rocks=40, grass=24, scale=(2.8, 5.4),
                               mystic=True, mushrooms=40, logs=10),
    'Beast_Cave':         dict(trees=65, bushes=60, plants=33, flowers=4, rocks=60, grass=12, scale=(2.4, 4.4),
                               mystic=True, mushrooms=20),
    'Jungle_Fortress':    dict(trees=170, bushes=150, plants=110, flowers=30, rocks=30, grass=40, scale=(3.0, 5.6),
                               jungle=True, logs=10),
    'Fortress_Heights':   dict(trees=40, bushes=90, plants=70, flowers=24, rocks=16, grass=40, scale=(2.4, 4.0),
                               jungle=True, ruins=10),
    'Sky_Temple':         dict(trees=19, bushes=50, plants=22, flowers=36, rocks=10, grass=36, scale=(2.0, 3.2),
                               temple=True),
}
SECRET_DRESS = dict(trees=114, bushes=120, plants=55, flowers=96, rocks=20, grass=48, scale=(2.0, 3.6))


def dress_of(a):
    return DRESS.get(a.name, SECRET_DRESS)


def tree_kind(rng, d):
    r = rng.random()
    if d.get('alpine'):
        return 'Tree_Tall_Thin_Low' if r < 0.8 else 'Tree_Medium_Low'
    if d.get('jungle'):                                        # the jungle set: canopy, ancient, palm, banana ...
        import floor1_jungle
        return floor1_jungle.pick_weighted(rng, floor1_jungle.JUNGLE_TREES)
    if d.get('mystic'):
        return ('Tree_Large_Mystic', 'Tree_Medium_Mystic', 'Tree_Tall_Thin_Mystic', 'Tree_Large_Low')[
            0 if r < 0.45 else 1 if r < 0.75 else 2 if r < 0.92 else 3]
    return ('Tree_Large_Low', 'Tree_Medium_Low', 'Tree_Small_Low', 'Tree_Tall_Thin_Low')[
        0 if r < 0.42 else 1 if r < 0.72 else 2 if r < 0.88 else 3]


def scatter(T):
    from floor1_jungle import JUNGLE_BUSHES, JUNGLE_GROUND
    X, Y = T.X, T.Y
    keep = keepout_mask(T)
    grove = F.field_noise(X, Y, 321, 90 * W, 3)            # groves (high) and clearings (low)
    detail_n = F.field_noise(X, Y, 322, 14 * W, 2)
    n_areas = len(F.AREAS)

    def pick(spacing, seed, per_m, need, max_slope=0.55, path_gap=14.0, edge_gap=24.0, water_gap=10.0,
             clear_keep=True, use_grove=0.0):
        """accepted candidate points for one layer: (x, y, area index); per_m(area) -> density / 1M sq studs"""
        x, y, rng = candidates(T, spacing, seed)
        i, j = grid_index(T, x, y)
        ok = T.land[i, j] & (T.own[i, j] < n_areas)
        ok &= T.slope[i, j] < max_slope
        ok &= T.path_e[i, j] > path_gap
        ok &= T.edge_d[i, j] > edge_gap
        ok &= (T.lake_f[i, j] > 1.15) & (T.river_d[i, j] > water_gap)
        if clear_keep:
            ok &= ~keep[i, j]
        dens = np.array([per_m(a) for a in F.AREAS] + [0.0])
        p = dens[np.minimum(T.own[i, j], n_areas)] * spacing * spacing / 1e6
        if use_grove:
            g = grove[i, j]
            p = p * np.clip(1.0 + use_grove * g * 1.6, 0.05, 2.4)
        ok &= rng.random(x.size) < p
        return x[ok], y[ok], T.own[i[ok], j[ok]], rng

    counts = {}

    def put(cat, asset, xs, ys, scales, rng, z_off=0.0):
        zs = ground_z(T, xs, ys)
        for x, y, z, s in zip(xs, ys, zs, scales):
            place(cat, asset, float(x), float(y), float(z) + z_off, rng.uniform(0, TAU), float(s))
        counts[asset] = counts.get(asset, 0) + len(xs)

    # trees: groves and clearings, kept off the roads by a wide margin so riders pass freely
    xs, ys, own, rng = pick(52.0, 1, lambda a: dress_of(a)['trees'], 'trees', 0.5, 46.0, 40.0, 30.0, use_grove=1.0)
    for x, y, o in zip(xs, ys, own):
        a = F.AREAS[o]; d = dress_of(a)
        k = tree_kind(rng, d)
        s = rng.uniform(*d['scale']) * (1.15 if d.get('jungle') else 1.0)
        place('Trees', k, float(x), float(y), float(ground_z(T, x, y)) - 0.4 * s, rng.uniform(0, TAU), s)
        counts[k] = counts.get(k, 0) + 1
    # bushes (closer to paths; jungle and mystic get their own mixes)
    xs, ys, own, rng = pick(40.0, 2, lambda a: dress_of(a)['bushes'], 'bushes', 0.6, 8.0, 14.0, 8.0, use_grove=0.6)
    for x, y, o in zip(xs, ys, own):
        d = dress_of(F.AREAS[o])
        k = rng.choice(('Bush_01_Mystic', 'Bush_03_Mystic', 'Bush_02') if d.get('mystic') else
                       JUNGLE_BUSHES if d.get('jungle') else
                       ('Bush_01', 'Bush_02', 'Bush_03'))
        s = rng.uniform(1.6, 3.2) * (1.3 if d.get('jungle') else 1.0)
        place('Foliage', k, float(x), float(y), float(ground_z(T, x, y)) - 0.2, rng.uniform(0, TAU), s)
        counts[k] = counts.get(k, 0) + 1
    # ground plants / ferns / flowers / grass / mushrooms
    xs, ys, own, rng = pick(30.0, 3, lambda a: dress_of(a)['plants'], 'plants', 0.7, 4.0, 10.0, 4.0)
    for x, y, o in zip(xs, ys, own):
        d = dress_of(F.AREAS[o])
        k = rng.choice(JUNGLE_GROUND if d.get('jungle') else
                       ('Fern', 'Fern', 'Ground_Plant_01', 'Ground_Plant_02') if d.get('mystic') else ('Ground_Plant_01', 'Ground_Plant_02', 'Fern'))
        place('Foliage', k, float(x), float(y), float(ground_z(T, x, y)), rng.uniform(0, TAU), rng.uniform(1.4, 2.6))
        counts[k] = counts.get(k, 0) + 1
    xs, ys, own, rng = pick(26.0, 4, lambda a: dress_of(a)['flowers'], 'flowers', 0.6, 3.0, 10.0, 4.0, use_grove=-0.6)
    for x, y, o in zip(xs, ys, own):
        k = rng.choice(('Pink_Jungle_Plant', 'Red_Jungle_Plant', 'Flower_Cluster_Pink', 'Purple_Accent_Plant',
                        'Pink_Jungle_Plant') if dress_of(F.AREAS[o]).get('jungle') else
                       ('Flower_Cluster_Pink', 'Flower_Cluster_Yellow', 'Flower_Cluster_White', 'Flower_Cluster_Purple',
                        'Flower_Cluster_Pink'))
        place('Foliage', k, float(x), float(y), float(ground_z(T, x, y)), rng.uniform(0, TAU), rng.uniform(1.6, 3.0))
        counts[k] = counts.get(k, 0) + 1
    xs, ys, own, rng = pick(30.0, 5, lambda a: dress_of(a)['grass'], 'grass', 0.6, 2.0, 8.0, 3.0)
    for x, y, o in zip(xs, ys, own):
        k = 'Grass_Patch' if rng.random() < 0.6 else 'Grass_Tuft'
        place('Foliage', k, float(x), float(y), float(ground_z(T, x, y)) - 0.1, rng.uniform(0, TAU),
              rng.uniform(2.0, 3.6) if k == 'Grass_Patch' else rng.uniform(2.5, 4.5))
        counts[k] = counts.get(k, 0) + 1
    xs, ys, own, rng = pick(60.0, 6, lambda a: dress_of(a).get('mushrooms', 0), 'mushrooms', 0.6, 10.0, 16.0, 6.0)
    for x, y, o in zip(xs, ys, own):
        d = dress_of(F.AREAS[o])
        k = 'Mushrooms_Glow' if d.get('mystic') and rng.random() < 0.6 else 'Mushrooms'
        place('Foliage', k, float(x), float(y), float(ground_z(T, x, y)), rng.uniform(0, TAU), rng.uniform(1.8, 3.6))
        counts[k] = counts.get(k, 0) + 1
    # rocks and boulders (also on steeper ground); big formations as landmarks in the peaks and crags
    xs, ys, own, rng = pick(60.0, 7, lambda a: dress_of(a)['rocks'], 'rocks', 1.2, 12.0, 20.0, 6.0)
    for x, y, o in zip(xs, ys, own):
        a = F.AREAS[o]
        r = rng.random()
        k, s = (('Rock_Large', rng.uniform(1.5, 4.0)) if r < 0.25 else ('Rock_Medium', rng.uniform(1.2, 3.0))
                if r < 0.6 else ('Rock_Small', rng.uniform(1.0, 2.6)))
        if a.name in ('Cloudridge_Peaks', 'Beast_Cave') and rng.random() < 0.25:
            k, s = 'Rock_Formation', rng.uniform(1.5, 3.5)
        if dress_of(a).get('jungle'):                         # mossy jungle rocks
            k = {'Rock_Large': 'Jungle_Rock_Large', 'Rock_Medium': 'Mossy_Boulder', 'Rock_Small': 'Flat_Rock',
                 'Rock_Formation': 'Jungle_Rock_Formation'}[k] if rng.random() < 0.8 else 'Root_Rock'
            s = s * 0.8
        place('Rocks', k, float(x), float(y), float(ground_z(T, x, y)) - 0.2 * s * 5, rng.uniform(0, TAU), s)
        counts[k] = counts.get(k, 0) + 1
    # fallen logs and stumps in the forests
    xs, ys, own, rng = pick(80.0, 8, lambda a: dress_of(a).get('logs', 0), 'logs', 0.4, 16.0, 30.0, 10.0)
    for x, y, o in zip(xs, ys, own):
        k = rng.choice(('Log', 'Stump', 'Stump'))
        place('Props', k, float(x), float(y), float(ground_z(T, x, y)) - 0.2, rng.uniform(0, TAU), rng.uniform(1.8, 3.2))
        counts[k] = counts.get(k, 0) + 1
    # ruins hints: columns, broken walls, arches, fragments (kept out of the reserved ruin footprints)
    xs, ys, own, rng = pick(80.0, 9, lambda a: dress_of(a).get('ruins', 0), 'ruins', 0.45, 18.0, 30.0, 10.0)
    for x, y, o in zip(xs, ys, own):
        r = rng.random()
        k = 'Broken_Column_B' if r < 0.25 else 'Broken_Column_A' if r < 0.45 else 'Broken_Wall' if r < 0.72 \
            else 'Ruin_Arch' if r < 0.8 else 'Stone_Fragments'
        place('Ruins', k, float(x), float(y), float(ground_z(T, x, y)) - 0.5, rng.uniform(0, TAU), rng.uniform(2.2, 3.6))
        counts[k] = counts.get(k, 0) + 1
    # swamp reeds + lily pads on the ponds; reeds along every shore and river bank
    xs, ys, own, rng = pick(28.0, 10, lambda a: dress_of(a).get('reeds', 0) + 30, 'reeds', 0.6, 6.0, 8.0, -1e9,
                            clear_keep=True)
    i, j = grid_index(T, xs, ys)
    near_water = ((T.lake_f[i, j] > 1.0) & (T.lake_f[i, j] < 1.45)) | ((T.river_d[i, j] > 0) & (T.river_d[i, j] < 26))
    swamp = np.array([F.AREAS[o].name == 'Lotus_Swamp' for o in own], dtype=bool)
    sel = near_water | (swamp & (rng.random(len(xs)) < 0.25))
    put('Water', 'Reeds', xs[sel], ys[sel], rng.uniform(2.0, 3.6, sel.sum()), rng)
    x, y, rng = candidates(T, 34.0, 11)
    i, j = grid_index(T, x, y)
    pond = (T.lake_f[i, j] < 0.85) & T.land[i, j]
    lotus = np.array([F.LAKES[li][0].startswith('Lotus') for li in T.lake_i[i, j]], dtype=bool)
    sel = pond & ((lotus & (rng.random(x.size) < 0.55)) | (~lotus & (rng.random(x.size) < 0.05)))
    for xx, yy, li in zip(x[sel], y[sel], T.lake_i[i[sel], j[sel]]):
        k = 'Lily_Pads_Flower' if rng.random() < 0.3 else 'Lily_Pads'
        place('Water', k, float(xx), float(yy), F.LAKES[li][2] + 0.05, rng.uniform(0, TAU), rng.uniform(2.0, 4.0))
        counts[k] = counts.get(k, 0) + 1
    # river-bank rocks
    xs, ys, own, rng = pick(36.0, 12, lambda a: 70.0, 'riverrocks', 1.5, 6.0, 8.0, -1e9)
    i, j = grid_index(T, xs, ys)
    sel = (T.river_d[i, j] > -2) & (T.river_d[i, j] < 16)
    put('Rocks', 'Rock_Small', xs[sel], ys[sel], rng.uniform(1.0, 2.4, sel.sum()), rng, -0.6)
    return counts


# ---------------------------------------------------------------- routes ----
def dress_routes(T):
    counts = dict(lanterns=0, signposts=0, benches=0, pebbles=0, fences=0)
    keep = keepout_mask(T)
    ends = {}
    for name, kind, w, pts in T.paths:
        for p in (pts[0], pts[-1]):
            key = (round(p[0] / 40), round(p[1] / 40))
            ends.setdefault(key, []).append((p, pts, name))
    # lanterns along main roads (both sides, staggered), skipping bridges and open sky
    for name, kind, w, pts in T.paths:
        if kind != 'main' or name == 'Entrance_Road':          # (the entrance road has its own lanterns)
            continue
        acc, side = 0.0, 1
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            acc += L
            if acc < 260:
                continue
            acc = 0.0
            d = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
            n = Vector((-d.y, d.x, 0)) * side
            side = -side
            x, y = b[0] + n.x * (w / 2 + 7), b[1] + n.y * (w / 2 + 7)
            i, j = grid_index(T, x, y)
            if not T.land[i, j] or T.edge_d[i, j] < 10 or T.own[i, j] >= len(F.AREAS) or keep[i, j]:
                continue
            place('Props', 'Lantern_Wood', x, y, float(ground_z(T, x, y)) - 0.3, math.atan2(d.y, d.x), 1.6)
            counts['lanterns'] += 1
    # signposts where several routes meet; benches by the checkpoints
    for key, lst in ends.items():
        if len(lst) < 2:
            continue
        p = lst[0][0]
        x, y = p[0] + 40, p[1] + 34
        i, j = grid_index(T, x, y)
        if T.land[i, j] and T.path_e[i, j] > 4:
            place('Props', 'Signpost', x, y, float(ground_z(T, x, y)), random.Random(len(ends)).uniform(0, TAU), 1.6)
            counts['signposts'] += 1
    for name, cx, cy in F.CHECKPOINTS:
        wx, wy = F.px(cx, cy)
        for k, a in enumerate((0.6, 2.4)):
            x, y = wx + math.cos(a) * 26, wy + math.sin(a) * 26
            place('Props', 'Bench', x, y, float(ground_z(T, x, y)), a + math.pi / 2, 1.4)
            counts['benches'] += 1
    # pebbles along the path edges
    x, y, rng = candidates(T, 22.0, 31)
    i, j = grid_index(T, x, y)
    sel = T.land[i, j] & (T.path_e[i, j] > -3) & (T.path_e[i, j] < 7) & (rng.random(x.size) < 0.12)
    for xx, yy in zip(x[sel], y[sel]):
        place('Rocks', rng.choice(('Rock_A', 'Rock_B', 'Rock_C')), float(xx), float(yy),
              float(ground_z(T, xx, yy)) - 0.3, rng.uniform(0, TAU), rng.uniform(1.2, 2.6))
        counts['pebbles'] += 1
    # wooden fences / rope barriers along the roads near the entrance and the village, and at sheer path edges
    for name, kind, w, pts in T.paths:
        if name not in ('Village_Road', 'Meadow_Road', 'Village_Swamp_Road'):
            continue
        for k in range(4, len(pts) - 4, 9):
            a, b = pts[k], pts[k + 1]
            d = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
            n = Vector((-d.y, d.x, 0))
            for s in (-1, 1):
                if (k // 9 + (s > 0)) % 3 == 0:
                    continue
                x, y = a[0] + n.x * s * (w / 2 + 3), a[1] + n.y * s * (w / 2 + 3)
                i, j = grid_index(T, x, y)
                if not T.land[i, j] or keep[i, j]:
                    continue
                place('Props', 'Wood_Fence' if name != 'Village_Swamp_Road' else 'Rope_Barrier', x, y,
                      float(ground_z(T, x, y)), math.atan2(d.y, d.x), 1.4)
                counts['fences'] += 1
    # a few barrels and crates by the village and the entrance (future stalls / camps)
    rng = random.Random(41)
    for (cx, cy), n in (((520, 690), 6), ((1150, 745), 4)):
        wx, wy = F.px(cx, cy)
        for k in range(n):
            x, y = wx + rng.uniform(-60, 60), wy + rng.uniform(-40, 40)
            i, j = grid_index(T, x, y)
            if T.land[i, j] and T.path_e[i, j] > 3 and not keep[i, j]:
                place('Props', rng.choice(('Barrel', 'Crate', 'Crate')), x, y, float(ground_z(T, x, y)),
                      rng.uniform(0, TAU), 1.6)
    return counts


# ---------------------------------------------------------------- cliffs, debris, cascades extras
def dress_cliffs(T):
    """moss drapes, vines and roots hanging from the island rims; floating debris below the edges"""
    rng = np.random.default_rng(51)
    rim = T.land & (T.edge_d <= F.S * 1.01) & (T.own < len(F.AREAS))
    ii, jj = np.nonzero(rim)
    sel = rng.random(ii.size) < 0.10
    n = 0
    for i, j in zip(ii[sel], jj[sel]):
        nx, ny = T.NX[i, j], T.NY[i, j]
        if nx == 0 and ny == 0:
            continue
        x, y, z = T.VX[i, j], T.VY[i, j], T.H[i, j]
        rot = math.atan2(ny, nx) + math.pi / 2
        r = rng.random()
        k, s, dz = (('Moss_Drape_B', rng.uniform(5, 9), -6 * 1) if r < 0.4 else
                    ('Moss_Drape_A', rng.uniform(5, 9), -4) if r < 0.65 else
                    ('Vine_Long', rng.uniform(6, 12), -2) if r < 0.9 else ('Root_Single', rng.uniform(6, 10), -10))
        place('Cliffs', k, float(x + nx * 1.5), float(y + ny * 1.5), float(z + dz), float(rot), float(s))
        n += 1
    # inner cliffs (between regions): boulders and outcrops set into the walls, moss hanging from their top edges
    gx, gy = np.gradient(T.H, F.S)
    g = np.hypot(gx, gy) + 1e-9
    steep = T.land & (T.slope > 2.2) & (T.own < len(F.AREAS)) & (T.path_e > 30)
    ii, jj = np.nonzero(steep)
    sel = rng.permutation(ii.size)[:min(900, ii.size)]
    Hm = T.H
    for t in sel:
        i, j = ii[t], jj[t]
        win = Hm[max(i - 2, 0):i + 3, max(j - 2, 0):j + 3]
        lo, hi = float(win.min()), float(win.max())
        if hi - lo < 4 * W:
            continue
        dx, dy = -gx[i, j] / g[i, j], -gy[i, j] / g[i, j]              # downhill = out of the wall
        x, y = float(T.X[i, j]) + dx * 6, float(T.Y[i, j]) + dy * 6
        if rng.random() < 0.6:
            z = rng.uniform(lo + 0.1 * (hi - lo), hi - 0.15 * (hi - lo))
            k = 'Rock_Large' if rng.random() < 0.6 else 'Rock_Formation'
            s = rng.uniform(3, 7) if k == 'Rock_Large' else rng.uniform(1.2, 2.4)
            place('Cliffs', k, x, y, z, float(rng.uniform(0, TAU)), float(s))
        else:
            k = 'Moss_Drape_B' if rng.random() < 0.6 else 'Vine_Long'
            place('Cliffs', k, x, y, hi - 2, math.atan2(dy, dx) + math.pi / 2, float(rng.uniform(6, 11)))
        n += 1
    # floating debris beneath the islands (out of the riding space)
    ii, jj = np.nonzero(T.land & (T.edge_d <= F.S * 1.01))
    pick = rng.choice(ii.size, size=min(110, ii.size), replace=False)
    for t in pick:
        i, j = ii[t], jj[t]
        nx, ny = T.NX[i, j], T.NY[i, j]
        d = rng.uniform(60, 420)
        x, y = T.VX[i, j] + nx * d, T.VY[i, j] + ny * d
        z = T.H[i, j] - rng.uniform(200, 1100)
        k = 'Rock_Large' if rng.random() < 0.5 else 'Rock_Medium'
        place('Background', k, float(x), float(y), float(z), float(rng.uniform(0, TAU)), float(rng.uniform(2.5, 6)))
    return n


def dress_falls(T, falls):
    """mist, foam and rocks where a waterfall lands on ground"""
    rng = random.Random(61)
    n = 0
    for f in falls:
        if f['bottom'] <= F.CLOUD_Z + 20:
            continue
        x, y, zb, w = f['x'], f['y'], f['bottom'], f.get('width', 60.0)
        d = Vector(f.get('dir', (0.0, 0.0)))
        c = Vector((x, y)) + d * (w * 0.4)
        place('Water', 'Foam_Ring', c.x, c.y, zb + 0.2, rng.uniform(0, TAU), w / 9)
        for k in range(3):
            o = Vector((rng.uniform(-0.4, 0.4) * w, rng.uniform(-0.4, 0.4) * w))
            place('Water', 'Mist_Puff', c.x + o.x, c.y + o.y, zb + rng.uniform(2, 10), rng.uniform(0, TAU),
                  w / rng.uniform(5, 8))
        for k in range(6):
            a = rng.uniform(0, TAU)
            r = w * rng.uniform(0.5, 0.9)
            place('Rocks', rng.choice(('Rock_Medium', 'Rock_Small')), c.x + math.cos(a) * r, c.y + math.sin(a) * r,
                  zb - 1.0, rng.uniform(0, TAU), rng.uniform(1.4, 3.0))
        n += 1
    return n


# ---------------------------------------------------------------- landmark hints
def dress_landmarks(T):
    rng = random.Random(71)
    # World Tree: hub-style canopy of leaf clusters and giant roots round the trunk (trunk + limbs in floor1.py)
    tx, ty = F.px(*F.WORLD_TREE)
    z0 = T.sample(tx, ty)[0]
    top = z0 + 300 * W
    for k in range(44):
        a = TAU * k / 13 + rng.uniform(-0.2, 0.2) if k < 39 else rng.uniform(0, TAU)
        r = (155, 110, 60)[min(k // 13, 2)] * W * rng.uniform(0.85, 1.1) if k < 39 else rng.uniform(0, 40) * W
        z = top + (55 - (r / W / 155) ** 2 * 70) * W + rng.uniform(-12, 12) * W
        kind = rng.choice(('Leaf_Cluster_Low', 'Leaf_Cluster_A', 'Leaf_Cluster_B', 'Leaf_Cluster_C'))
        place('Landmarks', kind, tx + math.cos(a) * r, ty + math.sin(a) * r, z, rng.uniform(0, TAU),
              rng.uniform(80, 115) * W / 10)
    for k in range(14):
        a = TAU * k / 14 + rng.uniform(-0.1, 0.1)
        x, y = tx + math.cos(a) * 52 * W, ty + math.sin(a) * 52 * W
        place('Landmarks', 'Root_Single', x, y, float(T.sample(x, y)[0]) - 2 * W, a, rng.uniform(120, 170) * W / 10)
    # Sky Temple: ancient platforms and broken columns round the reserved temple footprint, small clouds alongside
    cx, cy = F.px(1240, 130)
    zt = T.sample(cx, cy)[0]
    for k in range(9):
        a = TAU * k / 9 + rng.uniform(-0.15, 0.15)
        r = rng.uniform(95, 125) * W
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.55
        h, land = T.sample(x, y)
        if land:
            place('Ruins', rng.choice(('Temple_Platform', 'Broken_Column_B', 'Broken_Column_A')), x, y, h - 0.4,
                  rng.uniform(0, TAU), rng.uniform(2.6, 4.2))
    for k in range(10):
        a = rng.uniform(0, TAU); r = rng.uniform(130, 190) * W
        place('Background', rng.choice(('Rock_Large', 'Rock_Medium')), cx + math.cos(a) * r, cy + math.sin(a) * r * 0.7,
              zt + rng.uniform(-60, 120) * W / 2, rng.uniform(0, TAU), rng.uniform(3, 8))
        place('Background', rng.choice(('Cloud_A', 'Cloud_B', 'Cloud_C', 'Cloud_D')), cx + math.cos(a + 1) * r,
              cy + math.sin(a + 1) * r * 0.7, zt - rng.uniform(20, 80) * W, rng.uniform(0, TAU), rng.uniform(40, 80))


# ---------------------------------------------------------------- bridges ---
def bridge_frames(pts):
    """(point, tangent along the slope, horizontal side vector, deck normal) per point"""
    out = []
    for k in range(len(pts)):
        a = Vector(pts[max(k - 1, 0)]); b = Vector(pts[min(k + 1, len(pts) - 1)])
        t = (b - a).normalized()
        nrm = Vector((-t.y, t.x, 0)).normalized()
        out.append((Vector(pts[k]), t, nrm, t.cross(nrm)))
    return out


def resample(pts, step):
    P = [Vector(p) for p in pts]
    s = [0.0]
    for a, b in zip(P, P[1:]):
        s.append(s[-1] + (b - a).length)
    n = max(2, int(s[-1] / step) + 1)
    out, k = [], 0
    for m in range(n):
        t = s[-1] * m / (n - 1)
        while k < len(s) - 2 and s[k + 1] < t:
            k += 1
        f = (t - s[k]) / ((s[k + 1] - s[k]) or 1)
        out.append(P[k].lerp(P[k + 1], f))
    return out, s[-1]


def build_bridge(k, name, btype, w, pts):
    """wood plank / stone / rope bridge along a path span over open sky (deck = walking surface)"""
    rng = random.Random(500 + k)
    P, L = resample(pts, 4.0)
    if btype == 'rope':                                       # a little sag on the hidden rope bridges
        for m, p in enumerate(P):
            p.z -= math.sin(math.pi * m / (len(P) - 1)) * min(18.0, L * 0.03)
    fr = bridge_frames([tuple(p) for p in P])
    c = coll('F1_Bridge_Spans', 'F1_BRIDGES').name
    deck = Part(f'Bridge_{name}_{k}_Deck', c)
    rail = Part(f'Bridge_{name}_{k}_Rails', c)
    sup = Part(f'Bridge_{name}_{k}_Supports', c)
    hw = w / 2
    up = Vector((0, 0, 1))
    if btype in ('wood', 'rope'):
        for m, (p, t, nrm, upl) in enumerate(fr):                  # planks across the deck, slightly worn
            if m % 1 == 0:
                jit = rng.uniform(-0.35, 0.35)
                R = Matrix((t, nrm, upl)).transposed() @ Matrix.Rotation(rng.uniform(-0.02, 0.02), 3, 'Z')
                deck.box(p + upl * (-0.4 + jit * 0.2), (3.6, w + rng.uniform(-1.5, 1.0), 0.8),
                         'Wood_Plank' if rng.random() < 0.85 else 'Wood_Dark', R)
        step = 6 if btype == 'wood' else 8
        posts = [fr[m] for m in range(0, len(fr), step)] + [fr[-1]]
        for s in (-1, 1):
            tops = []
            for p, t, nrm, upl in posts:
                b = p + nrm * s * (hw - 0.8)
                rail.box(b + up * 3.2, (1.3, 1.3, 7.0), 'Wood_Dark')
                tops.append(b + up * 6.2)
            for a, b in zip(tops, tops[1:]):
                rail.beam(a, b, 0.7 if btype == 'wood' else 0.35, 0.7 if btype == 'wood' else 0.35,
                          'Wood_Plank' if btype == 'wood' else 'Rope_Tan')
                rail.beam(a - up * 3.0, b - up * 3.0, 0.5 if btype == 'wood' else 0.3, 0.5 if btype == 'wood' else 0.3,
                          'Wood_Plank' if btype == 'wood' else 'Rope_Tan')
        # stringers + braces underneath
        for s in (-1, 1):
            for a, b in zip(fr, fr[1:]):
                sup.beam(a[0] + a[2] * s * (hw - 3) - up * 2.2, b[0] + b[2] * s * (hw - 3) - up * 2.2, 2.0, 2.4,
                         'Wood_Dark')
        if btype == 'wood':
            for m in range(0, len(fr), 12):
                p, t, nrm, upl = fr[m]
                keel = p - up * 22
                for s in (-1, 1):
                    sup.beam(p + nrm * s * (hw - 3) - up * 3, keel, 1.6, 1.6, 'Wood_Dark')
                sup.box(keel, (2.2, 2.2, 2.2), 'Wood_Dark')
            for a, b in zip(fr[::12], fr[12::12]):
                sup.beam(a[0] - up * 22, b[0] - up * 22, 1.8, 1.8, 'Wood_Dark')
    else:                                                     # stone: slab deck, parapets, corbelled underside
        for m, (p, t, nrm, upl) in enumerate(fr[:-1]):
            if m % 3:
                continue
            q = fr[min(m + 3, len(fr) - 1)][0]
            mid = (p + q) / 2
            R = Matrix((t, nrm, upl)).transposed()
            seg = (q - p).length + 0.2
            deck.box(mid - upl * 1.5, (seg, w, 3.0), 'Bridge_Stone', R)
            for s in (-1, 1):
                rail.box(mid + nrm * s * (hw - 1.2) + up * 1.8, (seg - 0.3, 2.4, 3.6), 'Bridge_Stone', R)
                rail.box(mid + nrm * s * (hw - 1.2) + up * 3.8, (seg + 0.1, 2.9, 0.5), 'Ruin_Stone', R)
            sup.box(mid - up * 6.0, (seg, w * 0.8, 6.0), 'Bridge_Stone', R)
            if m % 12 == 0:
                sup.box(mid - up * 13.0, (6.0, w * 0.55, 8.0), 'Ruin_Stone', R)
                sup.cone(mid - up * 17.0, w * 0.25, -14.0, 'Ruin_Stone', 6)
    # stone foundations at both ends
    for p, t, nrm, upl in (fr[0], fr[-1]):
        for s in (-1, 1):
            sup.box(p + nrm * s * (hw + 1.5) - up * 4, (6.0, 5.0, 12.0), 'Bridge_Stone', Matrix.Rotation(
                math.atan2(t.y, t.x), 3, 'Z'))
    for part in (deck, rail, sup):
        part.finish()
    # lanterns at both ends
    for p, t, nrm, upl in (fr[1], fr[-2]):
        for s in (-1, 1):
            b = p + nrm * s * (hw + 4)
            place('Props', 'Lantern_Wood', b.x, b.y, p.z - 0.5, math.atan2(t.y, t.x), 1.6)
    return L


def build_bridges(T):
    out = []
    for k, (name, btype, w, pts) in enumerate(T.bridge_spans):
        L = build_bridge(k, name, btype, w, pts)
        out.append(dict(path=name, type=btype, length=round(L), width=w))
    # preview cameras on the longest stone and wood bridges
    for btype in ('stone', 'wood'):
        spans = [sp for sp in T.bridge_spans if sp[1] == btype]
        if not spans:
            continue
        name, _, w, pts = max(spans, key=lambda sp: len(sp[3]))
        a, b = Vector(pts[0]), Vector(pts[-1])
        mid = Vector(pts[len(pts) // 2])
        d = (b - a); d.z = 0; d.normalize()
        side = Vector((-d.y, d.x, 0))
        loc = mid + side * 260 - d * 160 + Vector((0, 0, 70))
        cam = bpy.data.cameras.new(f'CAM_F1_Bridge_{btype.title()}')
        cam.lens = 26; cam.clip_start = 2.0; cam.clip_end = 300000
        o = bpy.data.objects.new(cam.name, cam)
        o.location = loc
        o.rotation_euler = (mid - loc).to_track_quat('-Z', 'Y').to_euler()
        o['hide_collections'] = 'GUIDES'
        coll('CAMERAS').objects.link(o)
    return out


# ---------------------------------------------------------------- background
def dress_background(T, rng=None):
    rng = rng or random.Random(81)
    land = T.land
    cx, cy = float(T.X[land].mean()), float(T.Y[land].mean())
    ex = float(T.X[land].max() - T.X[land].min()) / 2
    ey = float(T.Y[land].max() - T.Y[land].min()) / 2
    n = 0
    # distant islands with trees and falls
    kinds = ('Large_Island', 'Medium_Island', 'Small_Island', 'Tall_Island', 'Crystal_Island', 'Medium_Island')
    spots = []
    while len(spots) < 34:
        a = rng.uniform(0, TAU)
        r = rng.uniform(1.25, 1.75)
        x, y = cx + math.cos(a) * ex * r, cy + math.sin(a) * ey * r
        if all(math.hypot(x - u, y - v) > 2600 for u, v in spots):
            spots.append((x, y))
    for x, y in spots:
        k = rng.choice(kinds)
        s = rng.uniform(8, 17) if k != 'Large_Island' else rng.uniform(8, 16)
        z = rng.uniform(-1500, 3500)
        rot = rng.uniform(0, TAU)
        place('Background', k, x, y, z, rot, s)
        ob = ASSETS[k]
        top = max(v[2] for v in ob.bound_box) * s
        rad = max(ob.dimensions.x, ob.dimensions.y) * s * 0.3
        for t in range(rng.randint(2, 5)):
            a = rng.uniform(0, TAU); r = rng.uniform(0, rad)
            place('Background', rng.choice(('Tree_Large_Low', 'Tree_Medium_Low', 'Tree_Tall_Thin_Low')),
                  x + math.cos(a) * r, y + math.sin(a) * r, z + top - 2, rng.uniform(0, TAU), s * rng.uniform(0.2, 0.32))
        if rng.random() < 0.45:
            place('Background', rng.choice(('Waterfall_Large', 'Waterfall_Medium')), x + math.cos(rot) * rad * 1.2,
                  y + math.sin(rot) * rad * 1.2, z + top - 4, rot + math.pi / 2, s * 0.9)
        n += 1
    # mountain spires rising from the cloud sea far outside
    for k in range(16):
        a = TAU * k / 16 + rng.uniform(-0.12, 0.12)
        r = rng.uniform(2.1, 2.6)
        x, y = cx + math.cos(a) * ex * r, cy + math.sin(a) * ey * r
        s = rng.uniform(48, 58)
        place('Background', 'Rock_Formation', x, y, F.CLOUD_Z - 300, rng.uniform(0, TAU), s)
        place('Background', 'Rock_Formation', x + rng.uniform(-200, 200), y + rng.uniform(-200, 200),
              F.CLOUD_Z - 300 + 33 * s * 0.85, rng.uniform(0, TAU), s * rng.uniform(0.55, 0.75))
    # cloud banks at several heights, outside the playable area and drifting below it
    for k in range(40):
        a = rng.uniform(0, TAU)
        r = rng.uniform(1.2, 2.1) if k < 32 else rng.uniform(0.3, 0.8)
        x, y = cx + math.cos(a) * ex * r, cy + math.sin(a) * ey * r
        z = rng.uniform(-200, 4200) if k < 32 else rng.uniform(-3200, -2400)
        place('Background', rng.choice(('Cloud_A', 'Cloud_B', 'Cloud_C', 'Cloud_D')), x, y, z, rng.uniform(0, TAU),
              rng.uniform(200, 340))
    return n


# ---------------------------------------------------------------- main ------
def build_detail(T, falls):
    PLACED.clear()
    coll(SCATTER, F.ROOT)
    for c in CATEGORIES:
        coll(f'Scatter_{c}', SCATTER)
    coll('F1_BRIDGES', F.ROOT)
    stats = {}
    stats['bridges'] = build_bridges(T)
    stats['scatter'] = scatter(T)
    stats['routes'] = dress_routes(T)
    stats['cliff_dressing'] = dress_cliffs(T)
    stats['falls_dressed'] = dress_falls(T, falls)
    dress_landmarks(T)
    import floor1_jungle
    stats['jungle'] = floor1_jungle.dress_jungle(T)
    stats['background_islands'] = dress_background(T)
    per_cat = {}
    for p in PLACED:
        per_cat[p[0]] = per_cat.get(p[0], 0) + 1
    stats['placements'] = per_cat
    stats['placements_total'] = len(PLACED)
    return stats
