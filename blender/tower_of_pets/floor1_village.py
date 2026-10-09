"""TOWER OF PETS - FLOOR 1 VERDANT VILLAGE round the entrance plaza (placeholder NPC / quest houses).

Builds on floor1_entrance.py (portal, plaza, road, the hub Shop and Hatchery) without moving any of it:
  * seven cozy timber-frame houses, every one different (floor1.VILLAGE_HOUSES gives the pads): stone foundations,
    plaster walls, dark timber posts / rails / braces, jettied upper storeys, glowing windows with shutters and flower
    boxes, arched doors with porches, balconies, masonry chimneys, straight / bell-cast / thatched roofs in different
    colours, plus one signature extra each (forge shed, bread oven, round scholar's tower, pergola, net rack ...);
    each house has an NPC spot in front of its door (layout JSON + Floor1_Village.lua) for quest givers later;
  * two market stalls with striped awnings and produce, stepping-stone walks from the houses to the road;
  * village props (barrels, crates, firewood, flower pots, carts, baskets, hay, clotheslines, garden patches,
    benches, signs) kept beside the houses - never on the road or the riding routes;
  * the lake on the right of the village (terrain in floor1.py): shoreline rocks, reeds, flowers, bushes, lily pads,
    small trees, a fishing jetty, and mist / foam / rocks where the two falls from the mossy cliff land;
  * hillside dressing round the portal hill and the cliff: layered rocks, moss, vines, bushes and hub trees.
Local house frame: x across the front, z up, the front wall faces -y; origin at the ground centre of the pad.
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix
from common import Part, mat_plain, coll, round_arch, TAU
import castle
from castle import bevel_box, masonry, frame_strip
import floor1 as F
from floor1_entrance import FLIP, frame, leaf_pts

C = 'F1_VILLAGE'
LIGHTS = 'F1_VILLAGE_LIGHTS'
I4 = Matrix.Identity(4)
FLOWERS = ('Flower_Pink', 'Flower_Yellow', 'Flower_White', 'Flower_Purple')


def build_village_materials():
    P = mat_plain
    P('Plaster_Cream', (0.93, 0.86, 0.68), 0.85)
    P('Plaster_White', (0.95, 0.93, 0.88), 0.85)
    P('Plaster_Peach', (0.95, 0.74, 0.56), 0.85)
    P('Plaster_Sage', (0.78, 0.86, 0.68), 0.85)
    P('Wood_Timber', (0.26, 0.14, 0.07), 0.8)
    P('Wood_Door', (0.46, 0.25, 0.11), 0.75)
    P('Wood_Shutter_Green', (0.16, 0.45, 0.20), 0.7)
    P('Wood_Shutter_Blue', (0.18, 0.36, 0.62), 0.7)
    P('Wood_Shutter_Red', (0.62, 0.16, 0.12), 0.7)
    P('Window_Glow', (1.0, 0.80, 0.42), 0.4, emit=1.6, emit_rgb=(1.0, 0.72, 0.32))
    for name, rgb in (('Roof_Red', (0.72, 0.20, 0.12)), ('Roof_Blue', (0.20, 0.34, 0.62)),
                      ('Roof_Green', (0.18, 0.46, 0.20)), ('Roof_Brown', (0.48, 0.28, 0.14)),
                      ('Roof_Teal', (0.10, 0.48, 0.50)), ('Roof_Purple', (0.40, 0.22, 0.58)),
                      ('Roof_Orange', (0.84, 0.42, 0.14)), ('Thatch', (0.80, 0.62, 0.30))):
        P(name, rgb, 0.75)
        P(name + '_Dark', tuple(c * 0.68 for c in rgb), 0.8)
    P('Awning_Red', (0.86, 0.16, 0.14), 0.75)
    P('Awning_White', (0.96, 0.94, 0.88), 0.75)
    P('Awning_Blue', (0.16, 0.40, 0.80), 0.75)
    P('Awning_Yellow', (1.0, 0.80, 0.20), 0.75)
    P('Produce_Red', (0.90, 0.14, 0.10), 0.5)
    P('Produce_Orange', (1.0, 0.55, 0.08), 0.5)
    P('Produce_Green', (0.40, 0.75, 0.18), 0.5)
    P('Soil', (0.30, 0.18, 0.09), 0.95)
    P('Hay', (0.92, 0.76, 0.34), 0.9)
    P('Cloth_Blue', (0.30, 0.55, 0.90), 0.8)
    P('Cloth_Pink', (0.98, 0.62, 0.72), 0.8)
    P('Forge_Glow', (1.0, 0.42, 0.06), 0.4, emit=2.0)


# ---------------------------------------------------------------- house parts
def faces(M, w, dep):
    """(face matrix, span) for front, right, back, left: face plane at y = 0, outward -y, x along the face"""
    out = []
    for k, (half, span) in enumerate(((dep / 2, w), (w / 2, dep), (dep / 2, w), (w / 2, dep))):
        out.append((M @ Matrix.Rotation(k * math.pi / 2, 4, 'Z') @ Matrix.Translation((0, -half, 0)), span))
    return out


def window(p, Mf, x, z, ww, wh, rnd, shutter, box=False):
    """glowing window with timber frame, cross mullions, open shutters and (optionally) a flower box; z = sill"""
    T = 'Wood_Timber'
    p.box(Mf @ Vector((x, -0.08, z + wh / 2)), (ww, 0.3, wh), 'Window_Glow', Mf.to_3x3().normalized())
    R = Mf.to_3x3().normalized()
    for dx, dz, sx, sz in ((0, -0.3, ww + 1.0, 0.6), (0, wh + 0.3, ww + 1.0, 0.6), (-ww / 2 - 0.25, wh / 2, 0.5, wh),
                           (ww / 2 + 0.25, wh / 2, 0.5, wh), (0, wh * 0.55, ww, 0.25), (0, wh / 2, 0.25, wh)):
        p.box(Mf @ Vector((x + dx, -0.35, z + dz)), (sx, 0.5 if sz > 0.3 and sx > 0.3 else 0.3, sz), T, R)
    if shutter:
        for s in (-1, 1):
            a = s * 0.5
            Rs = R @ Matrix.Rotation(-a, 3, 'Z')
            c = Mf @ Vector((x + s * (ww / 2 + 0.5 + ww * 0.24), -0.55 - ww * 0.12, z + wh / 2))
            p.box(c, (ww * 0.48, 0.25, wh), shutter, Rs)
    if box:
        p.box(Mf @ Vector((x, -0.9, z - 0.55)), (ww + 0.8, 1.2, 0.9), 'Wood_Plank', R)
        for k in range(5):
            q = Mf @ Vector((x + (k - 2) / 4 * ww + rnd.uniform(-0.2, 0.2), -0.9 + rnd.uniform(-0.25, 0.25),
                             z + rnd.uniform(-0.05, 0.25)))
            p.ico(q, rnd.uniform(0.45, 0.65), 'Leaves_Mid' if k % 2 else rnd.choice(FLOWERS), 1, smooth=False)


def door(p, Mf, x, z, dw=4.0, dh=5.6, sign=None):
    """arched plank door with a stone frame; z = threshold"""
    M = Mf @ Matrix.Translation((x, 0, z))
    inner = round_arch(dw, dh, 8)
    outer = round_arch(dw + 1.6, dh, 8)
    p.prism(inner, -0.3, 0.05, 'Wood_Door', M @ FLIP)
    frame_strip(p, M, [(o[0], o[1]) for o in outer], inner, -0.75, 0.05, 'Castle_Trim')
    R = Mf.to_3x3().normalized()
    for dx in (-dw / 4, dw / 4):
        p.box(M @ Vector((dx, -0.38, (dh + dw / 2) * 0.45)), (0.25, 0.2, (dh + dw / 2) * 0.85), 'Wood_Timber', R)
    for zz in (dh * 0.25, dh * 0.75):
        p.box(M @ Vector((0, -0.4, zz)), (dw - 0.3, 0.2, 0.4), 'Iron_Band', R)
    p.ico(M @ Vector((dw * 0.3, -0.55, dh * 0.5)), 0.22, 'Gold', 1)
    if sign:                                                    # hanging shop-style sign beside the door
        p.box(M @ Vector((dw / 2 + 1.6, -1.6, dh + 2.2)), (0.3, 3.2, 0.3), 'Wood_Timber', R)
        p.box(M @ Vector((dw / 2 + 1.6, -2.4, dh + 0.9)), (0.25, 2.4, 1.8), 'Sign_Wood', R)
        p.cyl(M @ Vector((dw / 2 + 1.45, -2.4, dh + 0.9)), 0.6, 0.15, sign, 10, axis='X', rot=R)


def timber_storey(p, Mf, span, z0, z1, rnd, brace, door_x=None, door_w=0.0, shutter=None, boxes=0.5, upper=False):
    """posts, rails, braces and windows on one face of one storey"""
    T = 'Wood_Timber'
    R = Mf.to_3x3().normalized()
    n = max(2, round(span / 5.5))
    xs = [-span / 2 + span * i / n for i in range(n + 1)]
    for zz in (z0 + 0.4, z1 - 0.4):
        p.box(Mf @ Vector((0, -0.18, zz)), (span + 0.7, 0.55, 0.8), T, R)
    for x in xs:
        p.box(Mf @ Vector((x, -0.18, (z0 + z1) / 2)), (0.85, 0.55, z1 - z0), T, R)
    for i, (a, b) in enumerate(zip(xs, xs[1:])):
        m = (a + b) / 2
        if door_x is not None and abs(m - door_x) < (b - a) / 2 + door_w / 2 - 0.5:
            continue
        has_win = (b - a) > 3.8 and (upper or i % 2 == 0 or n <= 3 or brace == 'none')
        if has_win:
            ww = min(3.2, b - a - 1.6)
            wh = min(3.6, z1 - z0 - 2.6)
            window(p, Mf, m, z0 + (1.5 if upper else 1.9), ww, wh, rnd, shutter, rnd.random() < boxes)
        elif brace == 'x':
            for s in (-1, 1):
                p.beam(Mf @ Vector((m - s * ((b - a) / 2 - 0.5), -0.2, z0 + 0.8)),
                       Mf @ Vector((m + s * ((b - a) / 2 - 0.5), -0.2, z1 - 0.8)), 0.6, 0.45, T)
        elif brace == 'chevron':
            for s in (-1, 1):
                p.beam(Mf @ Vector((m + s * ((b - a) / 2 - 0.4), -0.2, z0 + 0.8)),
                       Mf @ Vector((m, -0.2, z1 - 0.8)), 0.6, 0.45, T)
        elif brace == 'diag':
            s = 1 if i % 2 else -1
            p.beam(Mf @ Vector((m - s * ((b - a) / 2 - 0.5), -0.2, z0 + 0.8)),
                   Mf @ Vector((m + s * ((b - a) / 2 - 0.5), -0.2, z1 - 0.8)), 0.6, 0.45, T)


def roof(p, M, span, length, z_e, rise, oh, mat, kind, thick=0.9, gable_mat='Plaster_Cream', rnd=None):
    """roof with the ridge along local y: 'gable' (straight), 'curved' (bell-cast, flared eaves), 'thatch' (rounded)
    -> also fills both gable ends in the wall planes y = +-length / 2"""
    a = {'gable': 1.0, 'curved': 0.55, 'thatch': 1.9}[kind]
    n = 1 if kind == 'gable' else 6
    h = span / 2
    umax = 1 + oh / h
    zf = lambda u: z_e + rise * (1 - u ** a)
    us = [umax * i / n for i in range(n + 1)]                      # ridge (u = 0) -> eave
    y0, y1 = -length / 2 - oh * 0.8, length / 2 + oh * 0.8
    for s in (-1, 1):
        for u0, u1 in zip(us, us[1:]):
            xa, xb = s * h * u0, s * h * u1
            za, zb = zf(u0), zf(u1)
            (xl, zl), (xr, zr) = sorted(((xa, za), (xb, zb)))
            top = [(xl, y0, zl), (xr, y0, zr), (xr, y1, zr), (xl, y1, zl)]
            p.hexa([M @ Vector((x, y, z - thick)) for x, y, z in top] + [M @ Vector(v) for v in top], mat)
        if kind != 'thatch':                                       # shingle courses
            k = 1
            while True:
                u = k * 2.1 / h
                if u > umax - 0.1:
                    break
                p.beam(M @ Vector((s * h * u, y0 + 0.2, zf(u) + 0.12)), M @ Vector((s * h * u, y1 - 0.2, zf(u) + 0.12)),
                       0.55, 0.5, mat + '_Dark')
                k += 1
    if kind == 'thatch':
        p.cyl(M @ Vector((0, 0, z_e + rise + 0.1)), 0.9, y1 - y0, mat + '_Dark', 8, axis='Y')
    else:
        p.box(M @ Vector((0, 0, z_e + rise + 0.25)), (1.4, y1 - y0 + 0.4, 1.0), mat + '_Dark')
    # gable ends (plaster, timber king post + collar)
    prof = [(h * u, zf(u) - thick) for u in [1 - i / 8 for i in range(9)]]
    poly = [(-h, z_e - 0.4), (h, z_e - 0.4)] + prof[1:] + [(-x, z) for x, z in reversed(prof[:-1])]
    for yy, out in ((-length / 2, -1), (length / 2, 1)):
        p.prism(poly, yy - 0.3, yy + 0.3, gable_mat, M @ FLIP)
        if kind != 'thatch':
            yo = yy + out * 0.45
            p.box(M @ Vector((0, yo, z_e + (rise - thick) / 2)), (0.8, 0.45, rise - thick), 'Wood_Timber')
            zc = z_e + (rise - thick) * 0.45
            xc = h * (1 - 0.45) ** (1 / a) if a != 1 else h * 0.55
            p.box(M @ Vector((0, yo, zc)), (2 * xc - 0.6, 0.45, 0.7), 'Wood_Timber')
            if rnd is not None:                                    # small gable window
                p.box(M @ Vector((0, yy + out * 0.5, z_e + rise * 0.2 + 0.4)), (1.6, 0.3, 1.8), 'Window_Glow')


def chimney(p, M, x, y, z0, z1, rnd, size=3.2):
    """stacked masonry courses, a cap and a dark flue"""
    z, k = z0, 0
    while z < z1:
        h = rnd.uniform(1.2, 1.6)
        bevel_box(p, M, (x + rnd.uniform(-0.1, 0.1), y, z + h / 2), (size + (0.3 if k % 2 else 0.0), size, h),
                  rnd.choice(castle.STONES), 0.2)
        z += h; k += 1
    bevel_box(p, M, (x, y, z + 0.4), (size + 1.0, size + 1.0, 0.8), 'Castle_Trim', 0.15)
    p.box(M @ Vector((x, y, z + 0.85)), (size * 0.5, size * 0.5, 0.2), 'Castle_Seam')


def porch(p, walk, Mf, x, z0, dw, rnd, roof_mat, deep=5.5, posts=True):
    """timber deck + stone steps in front of the door, lean-to roof on two posts"""
    R = Mf.to_3x3().normalized()
    W = dw + 7.0
    walk.box(Mf @ Vector((x, -deep / 2, z0 - 0.3)), (W, deep, 0.6), 'Wood_Plank', R)
    for k in range(int(W / 1.4)):                               # deck boards
        walk.box(Mf @ Vector((x - W / 2 + 0.7 + k * 1.4, -deep / 2, z0 + 0.02)), (1.2, deep - 0.2, 0.08), 'Wood_Plank', R)
    bevel_box(walk, Mf, (x, -deep / 2, z0 / 2 - 1.5), (W - 0.2, deep - 0.3, z0 + 2.4), 'Castle_Stone_Dark', 0.1)
    nst = max(1, round(z0 / 0.9))
    for k in range(nst):
        hz = z0 * (nst - k) / (nst + 1)
        bevel_box(walk, Mf, (x, -deep - 1.0 - k * 1.6, hz / 2 - 0.5), (dw + 3.0, 1.8, hz + 1.0),
                  rnd.choice(('Castle_Trim', 'Castle_Stone_Light')), 0.15)
    if posts:
        top = z0 + 7.6
        for s in (-1, 1):
            p.box(Mf @ Vector((x + s * (W / 2 - 0.6), -deep + 0.6, (z0 + top) / 2)), (0.7, 0.7, top - z0), 'Wood_Timber', R)
            p.beam(Mf @ Vector((x + s * (W / 2 - 0.6), -deep + 0.6, top - 1.6)),
                   Mf @ Vector((x + s * (W / 2 - 2.2), -deep + 0.6, top - 0.1)), 0.45, 0.45, 'Wood_Timber')
        p.box(Mf @ Vector((x, -deep + 0.6, top - 0.1)), (W, 0.7, 0.7), 'Wood_Timber', R)
        a, b = Vector((0, 0.2, top + 1.6)), Vector((0, -deep - 0.6, top - 0.2))
        q = [(x - W / 2 - 0.5, a.y, a.z), (x + W / 2 + 0.5, a.y, a.z), (x + W / 2 + 0.5, b.y, b.z),
             (x - W / 2 - 0.5, b.y, b.z)]
        p.hexa([Mf @ Vector((u, v, w_ - 0.5)) for u, v, w_ in q] + [Mf @ Vector(v) for v in q], roof_mat)
    return Mf @ Vector((x, -deep - 1.0 - nst * 1.6 - 1.5, 0))         # where the walk to the road starts


def balcony(p, Mf, x, z, bw, rnd):
    R = Mf.to_3x3().normalized()
    p.box(Mf @ Vector((x, -2.0, z)), (bw, 4.0, 0.5), 'Wood_Plank', R)
    for s in (-1, 1):
        for k in range(2):
            xx = x + s * (bw / 2 - 1.0 - k * (bw - 2) / 2)
            p.beam(Mf @ Vector((xx, -0.2, z - 2.6)), Mf @ Vector((xx, -3.6, z - 0.3)), 0.5, 0.5, 'Wood_Timber')
    n = int(bw / 1.3)
    for k in range(n + 1):
        xx = x - bw / 2 + 0.3 + (bw - 0.6) * k / n
        p.box(Mf @ Vector((xx, -3.8, z + 1.3)), (0.3, 0.3, 2.4), 'Wood_Timber', R)
    for s in (-1, 1):
        for k in range(4):
            yy = -0.4 - k * 1.1
            p.box(Mf @ Vector((x + s * (bw / 2 - 0.15), yy, z + 1.3)), (0.3, 0.3, 2.4), 'Wood_Timber', R)
        p.box(Mf @ Vector((x + s * (bw / 2 - 0.15), -2.0, z + 2.55)), (0.4, 4.0, 0.35), 'Wood_Timber', R)
    p.box(Mf @ Vector((x, -3.8, z + 2.55)), (bw, 0.45, 0.35), 'Wood_Timber', R)
    for k in range(int(bw / 2.2)):                              # flower box along the rail
        p.ico(Mf @ Vector((x - bw / 2 + 1.2 + k * 2.2, -4.2, z + 2.6)), 0.6,
              rnd.choice(FLOWERS) if k % 2 else 'Leaves_Mid', 1, smooth=False)


# ---------------------------------------------------------------- the seven houses
STYLES = (
    # w, dep, ground h, upper h (0 = none), jetty, roof kind, ridge axis, rise, roof, plaster, shutter, brace, extra
    dict(name='Elder', w=26, dep=20, h1=9.5, h2=8.5, jetty=1.3, roof='gable', ridge='x', rise=10, rmat='Roof_Red',
         plaster='Plaster_Cream', shutter='Wood_Shutter_Green', brace='x', chimney=(1, 0.2), balcony=True,
         sign='Gold', extra='dormer'),
    dict(name='Baker', w=22, dep=18, h1=10.0, h2=0, jetty=0, roof='curved', ridge='y', rise=11, rmat='Roof_Brown',
         plaster='Plaster_Peach', shutter='Wood_Shutter_Blue', brace='chevron', chimney=(-1, 0.3), balcony=False,
         sign='Produce_Orange', extra='oven'),
    dict(name='Smith', w=24, dep=18, h1=10.0, h2=0, jetty=0, roof='gable', ridge='x', rise=8, rmat='Roof_Blue',
         plaster='Plaster_White', shutter='Wood_Shutter_Red', brace='diag', chimney=(-1, -0.2), balcony=False,
         sign='Iron_Band', extra='forge', stone=True),
    dict(name='Weaver', w=18, dep=18, h1=9.0, h2=8.0, jetty=1.2, roof='curved', ridge='y', rise=12, rmat='Roof_Teal',
         plaster='Plaster_White', shutter='Wood_Shutter_Red', brace='chevron', chimney=(1, 0.3), balcony=True,
         sign='Cloth_Pink', extra='lean_to'),
    dict(name='Gardener', w=22, dep=17, h1=9.5, h2=0, jetty=0, roof='curved', ridge='x', rise=9, rmat='Roof_Green',
         plaster='Plaster_Sage', shutter='Wood_Shutter_Green', brace='x', chimney=(-1, 0.0), balcony=False,
         sign='Leaves_Mid', extra='pergola'),
    dict(name='Fisher', w=20, dep=16, h1=8.5, h2=0, jetty=0, roof='thatch', ridge='x', rise=10, rmat='Thatch',
         plaster='Plaster_White', shutter='Wood_Shutter_Blue', brace='diag', chimney=(1, -0.2), balcony=False,
         sign='Cloth_Blue', extra='nets'),
    dict(name='Scholar', w=22, dep=18, h1=9.5, h2=8.5, jetty=1.0, roof='gable', ridge='x', rise=11, rmat='Roof_Green',
         plaster='Plaster_Cream', shutter='Wood_Shutter_Blue', brace='diag', chimney=(1, 0.0), balcony=False,
         sign='Verdant_Emblem', extra='tower'),
    dict(name='Herbalist', w=18, dep=16, h1=9.0, h2=0, jetty=0, roof='gable', ridge='y', rise=12, rmat='Roof_Orange',
         plaster='Plaster_Sage', shutter='Wood_Shutter_Green', brace='x', chimney=(-1, 0.3), balcony=False,
         sign='Flower_Purple', extra='herbs'),
    # the three plaza houses (concept palette: warm orange, brown and dark green roofs)
    dict(name='Potter', w=20, dep=17, h1=9.5, h2=0, jetty=0, roof='gable', ridge='x', rise=10, rmat='Roof_Orange',
         plaster='Plaster_Peach', shutter='Wood_Shutter_Green', brace='diag', chimney=(1, 0.2), balcony=False,
         sign='Produce_Orange', extra='lean_to'),
    dict(name='Cooper', w=24, dep=19, h1=9.5, h2=8.0, jetty=1.1, roof='curved', ridge='x', rise=10, rmat='Roof_Brown',
         plaster='Plaster_Cream', shutter='Wood_Shutter_Red', brace='x', chimney=(-1, 0.1), balcony=True,
         sign='Wood_Plank', extra='dormer'),
    dict(name='Miller', w=22, dep=18, h1=9.0, h2=8.0, jetty=1.0, roof='gable', ridge='y', rise=12, rmat='Roof_Green',
         plaster='Plaster_White', shutter='Wood_Shutter_Blue', brace='chevron', chimney=(1, -0.2), balcony=False,
         sign='Leaves_Mid', extra='herbs'),
)


HOUSE_SCALE = 1.3                                   # houses are drawn at ~1:1 player scale, then scaled up a little


def build_house(name, st, M, rnd):
    """one house at frame M (front -y); returns the unfinished body / walk Parts and the NPC spot, walk start and
    lamp position in the same frame"""
    body = Part('Village_House_' + name, C)
    walk = Part('Village_Walk_' + name, C)
    w, dep, h1, h2, jet = st['w'], st['dep'], st['h1'], st['h2'], st['jetty']
    fh = 2.4
    stone = st.get('stone', False)
    # stone foundation
    bevel_box(body, M, (0, 0, (fh - 6) / 2), (w + 1.4, dep + 1.4, fh + 6), 'Castle_Stone_Dark', 0.1)
    for Mf, span in faces(M, w + 1.4, dep + 1.4):
        masonry(body, Mf, -span / 2, span / 2, -1.5, fh, rnd, 1.3, (1.8, 3.4), 0.7, backing=False)
    bevel_box(body, M, (0, 0, fh + 0.15), (w + 1.8, dep + 1.8, 0.5), 'Castle_Trim', 0.12)
    # ground storey
    z0, z1 = fh, fh + h1
    body.box(M @ Vector((0, 0, (z0 + z1) / 2)), (w, dep, h1), 'Castle_Stone' if stone else st['plaster'],
             M.to_3x3().normalized())
    fs = faces(M, w, dep)
    door_x = 0.0 if st['ridge'] == 'x' or w > 20 else -w * 0.18
    for k, (Mf, span) in enumerate(fs):
        dx = door_x if k == 0 else None
        if stone:
            masonry(body, Mf, -span / 2, span / 2, z0, z1, rnd, 2.0, (2.6, 4.4), 0.9, backing=False,
                    skip=lambda x, z, bw, bh, dx=dx, span=span: (dx is not None and abs(x - dx) < 3.4 and z < z0 + 7.5)
                    or (abs(x) % 6.0 < 2.2 and z0 + 1.6 < z < z0 + 6.2 and abs(x) < span / 2 - 2.5))
            for x in [v for v in (-6.0, 0.0, 6.0) if abs(v) < span / 2 - 2.5 and (dx is None or abs(v - dx) > 4)]:
                window(body, Mf, x, z0 + 2.0, 2.4, 3.6, rnd, st['shutter'], rnd.random() < 0.5)
        else:
            timber_storey(body, Mf, span, z0, z1, rnd, st['brace'], dx, 4.6, st['shutter'], 0.6)
    Mfront = fs[0][0]
    door(body, Mfront, door_x, z0, 4.0, 5.4, st['sign'])
    walk_start = porch(body, walk, Mfront, door_x, z0, 4.0, rnd, st['rmat'], posts=st['extra'] not in ('tower',))
    npc = Mfront @ Vector((door_x + 4.5, -3.2, z0))
    lamp = Mfront @ Vector((door_x - 3.6, -1.0, z0 + 6.6))
    body.box(lamp, (0.9, 0.9, 1.3), 'Window_Glow')
    body.box(Mfront @ Vector((door_x - 3.6, -0.5, z0 + 7.5)), (0.4, 1.4, 0.3), 'Iron_Band', Mfront.to_3x3().normalized())
    top = z1
    # upper storey (jettied)
    if h2:
        u0, u1 = z1, z1 + h2
        W2, D2 = w + 2 * jet, dep + 2 * jet
        body.box(M @ Vector((0, 0, (u0 + u1) / 2)), (W2, D2, h2), st['plaster'], M.to_3x3().normalized())
        body.box(M @ Vector((0, 0, u0 + 0.3)), (W2 + 0.6, D2 + 0.6, 0.9), 'Wood_Timber', M.to_3x3().normalized())
        for k, (Mf, span) in enumerate(faces(M, W2, D2)):
            timber_storey(body, Mf, span, u0 + 0.6, u1, rnd, st['brace'], shutter=st['shutter'], boxes=0.7, upper=True)
            if jet:
                n = max(2, int(span / 6))
                for i in range(n + 1):
                    x = -span / 2 + 1 + (span - 2) * i / n
                    body.beam(Mf @ Vector((x, jet + 0.2, u0 - 2.4)), Mf @ Vector((x, -0.1, u0 + 0.2)), 0.6, 0.6,
                              'Wood_Timber')
        if st['balcony']:
            balcony(body, faces(M, W2, D2)[0][0], 0.0, u0 + 0.6, min(12.0, W2 - 6), rnd)
        top, w_r, d_r = u1, W2, D2
    else:
        w_r, d_r = w, dep
    # roof
    if st['ridge'] == 'x':
        Mr, span, length = M @ Matrix.Rotation(math.pi / 2, 4, 'Z'), d_r, w_r
    else:
        Mr, span, length = M, w_r, d_r
    roof(body, Mr, span, length, top, st['rise'], 2.2, st['rmat'], st['roof'], 1.4 if st['roof'] == 'thatch' else 0.9,
         st['plaster'] if not stone else 'Castle_Stone_Light', rnd)
    if st['extra'] == 'dormer':                                 # small front gable dormer on the roof
        Md = M @ Matrix.Translation((-w_r * 0.22, -d_r / 2 + 2.6, top))
        body.box(Md @ Vector((0, 0, 2.2)), (5.0, 5.0, 4.4), st['plaster'])
        window(body, Md @ Matrix.Translation((0, -2.5, 0)), 0, 1.0, 2.2, 2.4, rnd, None)
        roof(body, Md, 5.0, 5.2, 4.4, 3.0, 0.8, st['rmat'], 'gable', 0.6, st['plaster'])
    sx, fy = st['chimney']
    half = (w_r if st['ridge'] == 'x' else w_r) / 2
    chimney(body, M, sx * (half - 2.4), fy * d_r / 2 * 0.6, fh, top + st['rise'] + 3.0, rnd)
    # signature extras
    extra = st['extra']
    Ms = faces(M, w, dep)[1 if extra != 'tower' else 3][0]
    if extra == 'forge':                                         # open forge shed on the side
        R = Ms.to_3x3().normalized()
        for x in (-5.0, 5.0):
            body.box(Ms @ Vector((x, -7.2, fh + 4.0)), (0.8, 0.8, 8.0), 'Wood_Timber', R)
        q = [(-6.5, 0.4, fh + 9.5), (6.5, 0.4, fh + 9.5), (6.5, -8.4, fh + 7.2), (-6.5, -8.4, fh + 7.2)]
        body.hexa([Ms @ Vector((u, v, w_ - 0.5)) for u, v, w_ in q] + [Ms @ Vector(v) for v in q], st['rmat'])
        bevel_box(walk, Ms, (0, -4.2, fh / 2 - 1.2), (13.0, 8.6, fh + 2.4), 'Castle_Stone_Dark', 0.1)
        bevel_box(body, Ms, (-2.5, -2.6, fh + 1.6), (4.6, 3.6, 3.2), 'Castle_Stone', 0.25)
        body.box(Ms @ Vector((-2.5, -2.6, fh + 3.25)), (3.0, 2.2, 0.3), 'Forge_Glow', R)
        body.box(Ms @ Vector((2.6, -4.0, fh + 1.0)), (1.0, 1.0, 2.0), 'Iron_Band', R)
        body.box(Ms @ Vector((2.6, -4.0, fh + 2.2)), (2.6, 1.1, 0.5), 'Iron_Band', R)
    elif extra == 'oven':                                        # domed bread oven against the side
        body.uvsphere(Ms @ Vector((0, -2.0, fh + 0.5)), 3.4, 'Castle_Stone_Warm', 10, 6, (1.0, 1.0, 0.85))
        bevel_box(body, Ms, (0, -2.0, fh / 2 - 0.5), (7.4, 7.0, fh + 1.0), 'Castle_Stone_Dark', 0.2)
        body.box(Ms @ Vector((0, -5.3, fh + 1.4)), (1.8, 0.3, 1.6), 'Forge_Glow', Ms.to_3x3().normalized())
    elif extra == 'lean_to':                                     # timber store lean-to with firewood
        R = Ms.to_3x3().normalized()
        for x in (-4.0, 4.0):
            body.box(Ms @ Vector((x, -5.0, fh + 3.0)), (0.6, 0.6, 6.0), 'Wood_Timber', R)
        q = [(-5.0, 0.4, fh + 7.6), (5.0, 0.4, fh + 7.6), (5.0, -6.0, fh + 5.8), (-5.0, -6.0, fh + 5.8)]
        body.hexa([Ms @ Vector((u, v, w_ - 0.4)) for u, v, w_ in q] + [Ms @ Vector(v) for v in q], st['rmat'])
        for r in range(4):
            for k in range(6):
                body.cyl(Ms @ Vector((-3.4 + k * 1.3, -2.6, fh - 0.6 + r * 1.15 + 0.5)), 0.55, 4.0, 'Trunk', 6,
                         axis='Y', rot=R)
    elif extra == 'pergola':                                     # vine pergola beside the house
        R = Ms.to_3x3().normalized()
        for x in (-5.0, 5.0):
            for y in (-1.5, -9.0):
                body.box(Ms @ Vector((x, y, 4.5)), (0.7, 0.7, 9.0), 'Wood_Timber', R)
        for y in (-1.5, -9.0):
            body.box(Ms @ Vector((0, y, 9.2)), (12.0, 0.6, 0.6), 'Wood_Timber', R)
        for k in range(6):
            body.box(Ms @ Vector((-5.0 + k * 2.0, -5.25, 9.7)), (0.4, 10.0, 0.4), 'Wood_Timber', R)
        for k in range(14):
            body.ico(Ms @ Vector((rnd.uniform(-5.5, 5.5), rnd.uniform(-9.5, -1.0), 10.0 + rnd.uniform(-0.2, 0.4))),
                     rnd.uniform(0.9, 1.4), rnd.choice(('Leaves_Mid', 'Leaves_Light', 'Flower_Pink')), 1,
                     (1.4, 1.4, 0.6), smooth=False)
    elif extra == 'herbs':                                       # herb drying rack + raised planter beds
        R = Ms.to_3x3().normalized()
        for k, y in enumerate((-2.5, -7.0)):
            bevel_box(body, Ms, (0, y, 0.8), (9.0, 3.2, 1.6), 'Wood_Plank', 0.1)
            for i in range(7):
                body.ico(Ms @ Vector((-3.8 + i * 1.27, y, 2.0)), 0.6,
                         ('Flower_Purple', 'Leaves_Mid', 'Flower_White', 'Leaves_Light')[(i + k) % 4], 1, smooth=False)
    elif extra == 'nets':                                        # drying rack with nets
        R = Ms.to_3x3().normalized()
        for x in (-4.0, 4.0):
            body.box(Ms @ Vector((x, -4.0, 3.5)), (0.5, 0.5, 7.0), 'Wood_Timber', R)
        body.box(Ms @ Vector((0, -4.0, 6.8)), (9.0, 0.4, 0.4), 'Wood_Timber', R)
        body.box(Ms @ Vector((0, -4.0, 4.6)), (7.6, 0.15, 4.2), 'Rope', R)
    elif extra == 'tower':                                       # the scholar's round stone tower with a spire
        Mt = M @ Matrix.Translation((-w / 2 - 1.0, -dep / 2 + 3.5, 0))
        th = top + 6.0
        z, k = -1.5, 0
        while z < th:
            hh = 1.6
            Mt_ = Mt @ Matrix.Rotation(0.2 * k, 4, 'Z')
            body.cyl(Mt_ @ Vector((0, 0, z + hh / 2)), 5.2 if k % 2 else 5.05, hh - 0.08,
                     rnd.choice(('Castle_Stone', 'Castle_Stone_Light', 'Castle_Stone_Warm')), 12)
            z += hh; k += 1
        body.cyl(Mt @ Vector((0, 0, th + 0.4)), 5.9, 0.8, 'Castle_Trim', 14)
        body.cone(Mt @ Vector((0, 0, th + 0.8)), 6.4, 11.0, st['rmat'], 12)
        body.ico(Mt @ Vector((0, 0, th + 12.2)), 0.7, 'Gold', 1)
        for a in (-2.2, -1.2, 0.2, 2.6):
            for zz in (fh + 3.0, z1 + 3.0):
                Rt = Matrix.Rotation(a, 4, 'Z')
                q = Mt @ Rt @ Vector((5.15, 0, zz))
                body.box(q, (0.4, 1.6, 2.6), 'Window_Glow', (Mt @ Rt).to_3x3().normalized())
    return body, walk, npc, walk_start, lamp


# ---------------------------------------------------------------- market stalls
def build_stall(p, M, rnd, colours):
    T = 'Wood_Timber'
    R = M.to_3x3().normalized()
    for x in (-5.5, 5.5):
        for y in (-3.0, 3.0):
            p.box(M @ Vector((x, y, 4.6 if y < 0 else 5.6)), (0.6, 0.6, 9.2 if y < 0 else 11.2), T, R)
    bevel_box(p, M, (0, -2.2, 1.9), (11.6, 2.6, 3.8), 'Wood_Plank', 0.1)
    p.box(M @ Vector((0, -2.2, 3.9)), (12.2, 3.2, 0.3), 'Wood_Door', R)
    n = 8                                                       # striped awning
    for k in range(n):
        x0 = -6.6 + 13.2 * k / n; x1 = -6.6 + 13.2 * (k + 1) / n
        q = [(x0, 3.6, 11.4), (x1, 3.6, 11.4), (x1, -5.2, 9.0), (x0, -5.2, 9.0)]
        p.hexa([M @ Vector((u, v, w_ - 0.25)) for u, v, w_ in q] + [M @ Vector(v) for v in q], colours[k % 2])
        p.prism([(x0, 9.0), (x1, 9.0), ((x0 + x1) / 2, 7.8)], -5.25, -5.05, colours[k % 2], M @ FLIP)
    for k in range(9):                                          # produce baskets / crates on the counter
        x = -4.8 + k * 1.2
        p.ico(M @ Vector((x, -2.2 + rnd.uniform(-0.6, 0.6), 4.5)), rnd.uniform(0.5, 0.7),
              rnd.choice(('Produce_Red', 'Produce_Orange', 'Produce_Green', 'Flower_Pink', 'Flower_Yellow')), 1)
    for x in (-3.5, 3.5):
        p.box(M @ Vector((x, -6.2, 1.0)), (2.2, 2.2, 2.0), 'Wood_Plank', R)
        for k in range(3):
            p.ico(M @ Vector((x + (k - 1) * 0.6, -6.2, 2.3)), 0.55, rnd.choice(('Produce_Red', 'Produce_Green')), 1)
    p.box(M @ Vector((0, -5.4, 10.4)), (5.0, 0.3, 1.6), 'Sign_Wood', R)


# ---------------------------------------------------------------- new library props
def firewood(p, rnd):
    for r in range(3):
        for k in range(4 - r):
            p.cyl((-1.5 + k * 1.0 + r * 0.5, 0, 0.5 + r * 0.85), 0.48, 3.4, 'Trunk', 6, axis='Y')
    for s in (-1, 1):
        p.box((s * 2.3, 0, 1.2), (0.3, 3.0, 2.4), 'Wood_Dark')


def flower_pot(p, rnd):
    p.cyl((0, 0, 0.6), 0.9, 1.2, 'Castle_Stone_Warm', 8, r2=0.7)
    p.cyl((0, 0, 1.18), 0.85, 0.1, 'Soil', 8)
    for k in range(5):
        a = TAU * k / 5
        p.ico((math.cos(a) * 0.45, math.sin(a) * 0.45, 1.5 + rnd.uniform(0, 0.3)), 0.38,
              FLOWERS[k % 4] if k % 2 else 'Leaves_Mid', 1, smooth=False)


def cart(p, rnd):
    p.box((0, 0, 2.2), (6.0, 3.6, 0.4), 'Wood_Plank')
    for s in (-1, 1):
        p.box((0, s * 1.75, 3.0), (6.0, 0.3, 1.6), 'Wood_Plank')
        p.box((s * 2.85, 0, 3.0), (0.3, 3.6, 1.6), 'Wood_Plank')
        p.cyl((-0.8, s * 2.1, 1.6), 1.6, 0.35, 'Wood_Dark', 10, axis='Y')
        p.cyl((-0.8, s * 2.1, 1.6), 0.35, 0.6, 'Iron_Band', 6, axis='Y')
        p.beam((3.0, s * 1.0, 2.2), (6.8, s * 0.6, 1.0), 0.3, 0.3, 'Wood_Dark')
    for k in range(5):
        p.ico((rnd.uniform(-2, 2), rnd.uniform(-1, 1), 3.2), 0.9, rnd.choice(('Hay', 'Produce_Orange', 'Produce_Green')), 1)


def basket(p, rnd):
    p.cyl((0, 0, 0.55), 0.9, 1.1, 'Wood_Plank', 10, r2=1.05)
    p.torus((0, 0, 1.1), 1.05, 0.12, 'Wood_Dark', 12, 4)
    for k in range(4):
        p.ico((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 1.2), 0.42,
              rnd.choice(('Produce_Red', 'Produce_Orange', 'Produce_Green')), 1)


def hay_bale(p, rnd):
    bevel_box(p, I4, (0, 0, 1.0), (3.6, 2.2, 2.0), 'Hay', 0.3)
    for x in (-1.0, 1.0):
        p.box((x, 0, 1.0), (0.15, 2.3, 2.1), 'Rope')


def clothesline(p, rnd):
    for x in (-6.0, 6.0):
        p.box((x, 0, 3.5), (0.4, 0.4, 7.0), 'Wood_Dark')
        p.box((x, 0, 6.6), (0.3, 1.6, 0.3), 'Wood_Dark')
    p.beam((-6, 0, 6.4), (6, 0, 6.4), 0.08, 0.08, 'Rope')
    for k, x in enumerate((-4.2, -1.8, 0.6, 3.2)):
        mat = ('Cloth_Blue', 'Awning_White', 'Cloth_Pink', 'Banner_Green')[k]
        p.box((x, 0, 5.1), (1.8 + 0.4 * (k % 2), 0.08, 2.6), mat)


def garden_patch(p, rnd):
    bevel_box(p, I4, (0, 0, 0.25), (8.0, 5.0, 0.5), 'Soil', 0.15)
    for s in (-1, 1):
        p.box((0, s * 2.6, 0.35), (8.4, 0.3, 0.7), 'Wood_Plank')
    for r in range(3):
        for k in range(6):
            p.ico((-3.2 + k * 1.3, -1.6 + r * 1.6, 0.8), rnd.uniform(0.45, 0.6),
                  'Produce_Orange' if (r == 1 and k % 2) else 'Leaves_Mid', 1, (1, 1, 0.8), smooth=False)


def flower_bed(p, rnd):
    """round stone-ringed flower bed for the plaza"""
    for k in range(12):
        a0 = TAU * k / 12; a1 = TAU * (k + 1) / 12 - 0.03
        p.ring_sector(3.4, 4.2, a0, a1, 0, 1.0, rnd.choice(castle.STONES), 2)
    p.cyl((0, 0, 0.75), 3.45, 0.2, 'Soil', 12)
    for k in range(16):
        a = rnd.uniform(0, TAU); r = rnd.uniform(0, 2.8)
        p.ico((math.cos(a) * r, math.sin(a) * r, 1.2), rnd.uniform(0.5, 0.8),
              FLOWERS[k % 4] if k % 3 else 'Leaves_Mid', 1, smooth=False)


def well(p, rnd):
    for k in range(10):
        a0 = TAU * k / 10; a1 = TAU * (k + 1) / 10 - 0.03
        p.ring_sector(2.6, 3.6, a0, a1, 0, 3.0, rnd.choice(castle.STONES), 2)
    p.cyl((0, 0, 2.4), 2.6, 0.2, 'F1_Water', 12)
    for s in (-1, 1):
        p.box((s * 3.1, 0, 5.2), (0.5, 0.5, 5.0), 'Wood_Dark')
    p.cyl((0, 0, 6.8), 0.3, 6.6, 'Wood_Dark', 6, axis='X')
    for s in (-1, 1):
        q = [(-4.0, 0, 9.6), (4.0, 0, 9.6), (4.0, s * 3.2, 7.6), (-4.0, s * 3.2, 7.6)]
        p.hexa([Vector((u, v, w_ - 0.35)) for u, v, w_ in q] + [Vector(v) for v in q], 'Roof_Red')


def jetty(p, rnd):
    """short fishing jetty (origin at the shore end, runs along +y)"""
    p.box((0, 9.0, 1.6), (5.0, 18.0, 0.5), 'Wood_Plank')
    for y in (1.0, 7.0, 13.0, 17.5):
        for s in (-1, 1):
            p.cyl((s * 2.3, y, -1.0), 0.4, 6.0, 'Wood_Dark', 6)
    for y in (6.0, 17.5):
        for s in (-1, 1):
            p.cyl((s * 2.3, y, 2.8), 0.3, 2.4, 'Wood_Dark', 6)


def build_village_assets():
    build_village_materials()
    from floor1_detail import _lib
    R = random.Random
    _lib('Firewood_Stack', firewood, R(201))
    _lib('Flower_Pot', flower_pot, R(202))
    _lib('Cart', cart, R(203))
    _lib('Basket', basket, R(204))
    _lib('Hay_Bale', hay_bale, R(205))
    _lib('Clothesline', clothesline, R(206))
    _lib('Garden_Patch', garden_patch, R(207))
    _lib('Flower_Bed', flower_bed, R(208))
    _lib('Village_Well', well, R(209))
    _lib('Fishing_Jetty', jetty, R(210))


# ---------------------------------------------------------------- build
def village_frame():
    """village centre (world), unit direction along the Village Road away from the Floor Entrance"""
    cx, cy = F.px(*F.VILLAGE_CENTER_PX)
    ax, ay = F.px(*F.VILLAGE_AXIS_PX)
    return Vector((cx, cy, 0)), Vector((ax - cx, ay - cy, 0)).normalized()


def nearest_road(T, q):
    pts = [p for n, k, w, pts in T.paths if n in ('Village_Road', 'Entrance_Road') for p in pts]
    return min((Vector((x, y, z)) for x, y, z in pts), key=lambda v: (v.xy - q.xy).length)


def stepping_stones(T, walk, a, b, rnd):
    from floor1_detail import ground_z
    d = (b - a).xy
    L = d.length
    if L < 4:
        return
    t = Vector((d.x, d.y, 0)) / L
    n = Vector((-t.y, t.x, 0))
    rot = math.atan2(t.y, t.x)
    for k in range(int(L / 3.6)):
        for s in (-1, 1):
            q = a + t * (k * 3.6 + 1.8) + n * (s * 1.7 + rnd.uniform(-0.4, 0.4))
            z = float(ground_z(T, q.x, q.y))
            bevel_box(walk, Matrix.Translation((q.x, q.y, z)) @ Matrix.Rotation(rot + rnd.uniform(-0.3, 0.3), 4, 'Z'),
                      (0, 0, 0.15), (rnd.uniform(2.4, 3.2), rnd.uniform(2.4, 3.0), 0.6),
                      rnd.choice(('Castle_Stone_Light', 'Castle_Trim', 'Castle_Stone')), 0.2)


def sites():
    """the two settlements: the hamlet round the Floor Entrance (original layout) and Verdant Village proper"""
    return (
        dict(key='entrance', prefix='Village', frame=frame, px=F.entrance_village_px, houses=F.ENTRANCE_HOUSES,
             stalls=F.ENTRANCE_STALLS, lake='Village_Lake', lake_c=F.ENTRANCE_LAKE_C, mesa=F.ENTRANCE_MESA,
             road='Entrance_Road', plaza=None, fr1=(-60, 360), fr2=(-120, 330), road_r=(70, 400), seed=301),
        dict(key='village', prefix='Verdant_Village', frame=village_frame, px=F.village_px, houses=F.VILLAGE_HOUSES,
             stalls=F.VILLAGE_STALLS, lake='Verdant_Village_Lake', lake_c=F.VILLAGE_LAKE_C, mesa=F.VILLAGE_MESA,
             road='Village_Road', plaza=F.VILLAGE_PLAZA, fr1=(-260, 260), fr2=(-260, 240), road_r=(0, 330), seed=302),
    )


SITE = None


def build_villages(T):
    """both settlements; returns the merged layout data (houses / stalls carry their site)"""
    global SITE
    out = dict(houses=[], stalls=[], plaza=None)
    for st in sites():
        SITE = st
        v = build_village(T)
        for h in v['houses'] + v['stalls']:
            h['site'] = st['key']
        out['houses'] += v['houses']; out['stalls'] += v['stalls']
        if v.get('plaza'):
            out['plaza'] = v['plaza']
    return out


def build_village(T):
    from floor1_detail import place, ground_z
    coll(C, F.ROOT)
    coll(LIGHTS, F.ROOT)
    rnd = random.Random(SITE['seed'])
    c, d = SITE['frame']()
    side = Vector((-d.y, d.x, 0))
    c0, d0 = frame()
    side0 = Vector((-d0.y, d0.x, 0))
    gz = lambda q: float(ground_z(T, q.x, q.y))
    W = lambda f, r: c + d * f + side * r
    houses = []
    walk_lines = []
    walks = Part(SITE['prefix'] + '_Walk_Paths', C)
    for (name, f, r, si) in SITE['houses']:
        st = STYLES[si]
        pos = W(f, r)
        z = T.sample(pos.x, pos.y)[0]
        road = nearest_road(T, pos)
        if SITE['plaza'] and name in F.VILLAGE_PLAZA_HOUSES:   # plaza houses face the fountain; their walk ends at the rim
            road = W(*F.VILLAGE_PLAZA)
            road.z = z
        fdir = (road - pos).xy.normalized()
        rot = math.atan2(fdir.x, -fdir.y)
        M = Matrix.Translation((pos.x, pos.y, z)) @ Matrix.Rotation(rot, 4, 'Z')
        Mw = M @ Matrix.Diagonal((HOUSE_SCALE, HOUSE_SCALE, HOUSE_SCALE, 1.0))
        body, walk, npc, wstart, lamp = build_house(name, st, I4, random.Random(400 + si))
        for part in (body, walk):                                # built in the local frame, placed and scaled here
            bmesh.ops.transform(part.bm, matrix=Mw, verts=part.bm.verts)
            part.finish()
        npc, wstart, lamp = Mw @ npc, Mw @ wstart, Mw @ lamp
        # walk from the porch steps to the road edge
        end = road + (pos - road).xy.normalized().to_3d() * (F.VILLAGE_PLAZA_R + 3 if name in F.VILLAGE_PLAZA_HOUSES
                                                             else 27.0)
        stepping_stones(T, walks, wstart, end, rnd)
        walk_lines.append((wstart.copy(), end.copy()))
        L = bpy.data.lights.new(f'Village_Light_{name}', 'POINT')
        L.color = (1.0, 0.68, 0.34); L.energy = 2200; L.shadow_soft_size = 1.0
        lo = bpy.data.objects.new(L.name, L)
        lo.location = lamp + Matrix.Rotation(rot, 3, 'Z') @ Vector((0, -1.5, 0))
        bpy.data.collections[LIGHTS].objects.link(lo)
        houses.append(dict(name=name, role=st['name'], pos=(pos.x, pos.y, z), npc=(npc.x, npc.y, npc.z),
                           facing=(fdir.x, fdir.y), M=M, w=st['w'] * HOUSE_SCALE, dep=st['dep'] * HOUSE_SCALE))
    walks.finish()
    # market stalls (face the road)
    sp = Part(SITE['prefix'] + '_Market_Stalls', C)
    colours = (('Awning_Red', 'Awning_White'), ('Awning_Blue', 'Awning_Yellow'), ('Awning_Red', 'Awning_Yellow'),
               ('Awning_Blue', 'Awning_White'))
    stalls = []
    for k, (name, f, r) in enumerate(SITE['stalls']):
        pos = W(f, r)
        z = T.sample(pos.x, pos.y)[0]
        road = nearest_road(T, pos) if k < 2 else W(*F.VILLAGE_PLAZA)    # plaza stalls face the fountain
        fd = (road - pos).xy.normalized()
        M = Matrix.Translation((pos.x, pos.y, z)) @ Matrix.Rotation(math.atan2(fd.x, -fd.y), 4, 'Z')
        build_stall(sp, M, rnd, colours[k])
        stalls.append(dict(name=name, pos=(pos.x, pos.y, z), npc=tuple(M @ Vector((0, 1.0, 0))), facing=(fd.x, fd.y)))
        for a, kind, s in ((-1, 'Barrel', 1.0), (1, 'Crate', 1.1), (1, 'Basket', 1.2)):
            q = M @ Vector((a * 8.5 + rnd.uniform(-0.6, 0.6), rnd.uniform(-1, 2), 0))
            place('Props', kind, q.x, q.y, gz(q), rnd.uniform(0, TAU), s)
    sp.finish()
    dress_houses(T, houses, place, gz, rnd)
    dress_greenery(T, houses, walk_lines, place, gz, rnd, c, d, side)
    dress_lake(T, place, gz, rnd, c, d, side)
    heart = None
    if SITE['key'] == 'entrance':
        dress_plaza(T, place, gz, rnd, c, d, side)
        dress_hillside(T, place, gz, rnd, c, d, side)           # the portal hill + the mesa over its lake
    else:
        dress_hillside(T, place, gz, rnd, c, d, side, mesa_only=True)
        heart = build_village_heart(T, place, gz, random.Random(611), c, d, side)
    return dict(plaza=heart, houses=[{k: v for k, v in h.items() if k not in ('M',)} for h in houses], stalls=stalls)


def clear_of_routes(T, q, margin):
    """True when q is off every path (edge + margin) and not in water"""
    from floor1_detail import grid_index
    i, j = grid_index(T, q.x, q.y)
    return bool(T.path_e[i, j] > margin and T.lake_f[i, j] > 1.1 and T.river_d[i, j] > 8 and T.land[i, j])


def dress_houses(T, houses, place, gz, rnd):
    """props round each house: beside and behind it, never in front of the door or on the road"""
    sets = {
        'Elder': (('Flower_Pot', 2), ('Bench', 1), ('Barrel', 2), ('Garden_Patch', 1), ('Flower_Bed', 1)),
        'Baker': (('Firewood_Stack', 2), ('Barrel', 2), ('Crate', 2), ('Basket', 2), ('Flower_Pot', 2)),
        'Smith': (('Crate', 3), ('Barrel', 2), ('Firewood_Stack', 1), ('Cart', 1)),
        'Weaver': (('Clothesline', 1), ('Basket', 3), ('Flower_Pot', 2), ('Bench', 1)),
        'Gardener': (('Garden_Patch', 3), ('Hay_Bale', 2), ('Basket', 2), ('Flower_Pot', 3), ('Cart', 1)),
        'Fisher': (('Barrel', 3), ('Crate', 2), ('Basket', 2), ('Clothesline', 1)),
        'Scholar': (('Bench', 1), ('Flower_Pot', 3), ('Crate', 1), ('Garden_Patch', 1)),
        'Herbalist': (('Flower_Pot', 4), ('Basket', 3), ('Garden_Patch', 1), ('Barrel', 1)),
        'Potter': (('Crate', 2), ('Basket', 2), ('Flower_Pot', 3), ('Firewood_Stack', 1)),
        'Cooper': (('Barrel', 4), ('Crate', 1), ('Cart', 1), ('Bench', 1)),
        'Miller': (('Hay_Bale', 3), ('Basket', 2), ('Garden_Patch', 2), ('Flower_Pot', 1)),
    }
    def crowded(q, me):                                         # keep props out of the neighbours' footprints
        return any((Vector(o['pos'][:2]) - q.xy).length < 24 for o in houses if o is not me) or \
            any((Vector(F.px(*SITE['px'](f, r))) - q.xy).length < 14 for n, f, r in SITE['stalls'])
    for h in houses:
        M = h['M']
        R = Matrix.Rotation(math.atan2(h['facing'][0], -h['facing'][1]), 3, 'Z')
        yaw = math.atan2(h['facing'][1], h['facing'][0])
        slots = []
        for s in (-1, 1):                                       # beside the house (front corners and sides)
            for y in (-h['dep'] * 0.15, h['dep'] * 0.25, h['dep'] * 0.55):
                slots.append(Vector((s * (h['w'] / 2 + rnd.uniform(5, 9)), y, 0)))
        for x in (-h['w'] * 0.3, 0.0, h['w'] * 0.3):           # behind it
            slots.append(Vector((x, h['dep'] / 2 + rnd.uniform(6, 10), 0)))
        rnd.shuffle(slots)
        for kind, n in sets[h['role']]:
            for _ in range(n):
                if not slots:
                    break
                q = M @ slots.pop()
                if not clear_of_routes(T, q, 6) or crowded(q, h):
                    continue
                rot = yaw + (math.pi / 2 if kind in ('Bench', 'Clothesline', 'Garden_Patch', 'Cart') else rnd.uniform(0, TAU))
                place('Props', kind, q.x, q.y, gz(q), rot, rnd.uniform(1.0, 1.2))
        # flowers and bushes hugging the foundation; a fence run behind
        for k in range(10):
            s = rnd.choice((-1, 1))
            q = M @ Vector((s * (h['w'] / 2 + rnd.uniform(1.5, 3.0)), rnd.uniform(-h['dep'] / 2, h['dep'] / 2), 0))
            place('Foliage', rnd.choice(('Bush_01', 'Bush_02', 'Flower_Cluster_Pink', 'Flower_Cluster_Yellow',
                                         'Flower_Cluster_White', 'Fern')), q.x, q.y, gz(q), rnd.uniform(0, TAU),
                  rnd.uniform(1.2, 1.8))
        for k in range(4):
            q = M @ Vector((-h['w'] / 2 - 4 + k * (h['w'] + 8) / 3, h['dep'] / 2 + 16, 0))
            if clear_of_routes(T, q, 4) and not crowded(q, h):
                place('Props', 'Wood_Fence', q.x, q.y, gz(q), yaw + math.pi / 2, 1.3)
        for k in range(2):                                      # a hub tree or two behind each house
            q = M @ Vector((rnd.uniform(-1, 1) * h['w'] * 0.6, h['dep'] / 2 + rnd.uniform(42, 54), 0))
            if clear_of_routes(T, q, 12) and not any((Vector(o['pos'][:2]) - q.xy).length < 58 for o in houses
                                                     if o is not h):
                place('Trees', rnd.choice(('Tree_Medium_High', 'Tree_Large_High', 'Tree_Small')), q.x, q.y, gz(q) - 1,
                      rnd.uniform(0, TAU), rnd.uniform(1.5, 2.0))
        place('Props', 'Lantern_Wood', *(M @ Vector((h['w'] / 2 + 3.0, -h['dep'] / 2 - 6.0, 0))).xy,
              gz(M @ Vector((h['w'] / 2 + 3.0, -h['dep'] / 2 - 6.0, 0))), yaw, 1.2)


def dress_lake(T, place, gz, rnd, c, d, side):
    """shoreline: rocks, reeds, flowers, bushes, small trees; lily pads; a fishing jetty"""
    from floor1_detail import grid_index
    lc = c + d * SITE['lake_c'][0] + side * SITE['lake_c'][1]
    li = next(k for k, l in enumerate(F.LAKES) if l[0] == SITE['lake'])
    zw = F.LAKES[li][2]
    # walk round the shore: find the water edge along rays from the centre
    for k in range(64):
        a = TAU * k / 64 + rnd.uniform(-0.03, 0.03)
        u = Vector((math.cos(a), math.sin(a), 0))
        r, edge = 20.0, None
        while r < 260:
            q = lc + u * r
            i, j = grid_index(T, q.x, q.y)
            if T.lake_f[i, j] >= 1.0 or T.lake_i[i, j] != li:
                edge = q
                break
            r += 4.0
        if edge is None:
            continue
        for kind, off, cat, sc in (('Rock_Medium', 2.0, 'Rocks', (1.2, 2.4)), ('Reeds', -3.0, 'Water', (2.0, 3.2)),
                                   ('Flower_Cluster_White', 9.0, 'Foliage', (1.6, 2.4)),
                                   ('Bush_01', 14.0, 'Foliage', (1.8, 2.6))):
            if rnd.random() < (0.45 if cat != 'Water' else 0.7):
                q = edge + u * (off + rnd.uniform(-1.5, 1.5))
                if cat != 'Water' and not clear_of_routes(T, q, 4) and T.lake_f[grid_index(T, q.x, q.y)] < 1.0:
                    continue
                zq = zw - 0.5 if cat == 'Water' else gz(q) - (1.0 if cat == 'Rocks' else 0.0)
                place(cat, kind if cat != 'Foliage' else rnd.choice((kind, 'Flower_Cluster_Pink', 'Fern', 'Bush_02')),
                      q.x, q.y, zq, rnd.uniform(0, TAU), rnd.uniform(*sc))
        if k % 9 == 4:                                          # small trees round the lake
            q = edge + u * rnd.uniform(24, 34)
            if clear_of_routes(T, q, 10) and not any((Vector(F.px(*SITE['px'](f, r))) - q.xy).length < 45
                                                     for n, f, r, *_ in SITE['houses']):
                place('Trees', rnd.choice(('Tree_Small', 'Tree_Medium_High')), q.x, q.y, gz(q) - 1, rnd.uniform(0, TAU),
                      rnd.uniform(1.6, 2.2))
    for k in range(26):                                         # lily pads
        a = rnd.uniform(0, TAU); r = rnd.uniform(15, 80)
        q = lc + Vector((math.cos(a), math.sin(a), 0)) * r
        i, j = grid_index(T, q.x, q.y)
        if T.lake_f[i, j] < 0.85 and T.lake_i[i, j] == li:
            place('Water', 'Lily_Pads_Flower' if rnd.random() < 0.35 else 'Lily_Pads', q.x, q.y, zw + 0.05,
                  rnd.uniform(0, TAU), rnd.uniform(1.8, 2.8))
    # the fishing jetty on the village side of the lake
    u = (c - lc).xy.normalized().to_3d()
    r = 20.0
    while r < 200:
        q = lc + u * r
        i, j = grid_index(T, q.x, q.y)
        if T.lake_f[i, j] >= 1.0:
            break
        r += 3.0
    q = lc + u * (r + 5.0)
    place('Props', 'Fishing_Jetty', q.x, q.y, zw - 0.6, math.atan2(-u.y, -u.x) - math.pi / 2, 1.2)


def dress_plaza(T, place, gz, rnd, c, d, side):
    """benches and flower beds round the plaza rim (the centre and the walk-ins stay open), banners on the road"""
    from floor1_entrance import PLAZA_R
    road = math.atan2(d.y, d.x)
    for a_off in (0.62, -0.62, 2.0, -2.0):                       # between the openings, facing the emblem
        a = road + a_off
        u = Vector((math.cos(a), math.sin(a), 0))
        q = c + u * (PLAZA_R - 5.0)
        place('Props', 'Bench', q.x, q.y, gz(q) + 0.6, a - math.pi / 2, 1.3)
        q2 = c + u * (PLAZA_R + 9.0)
        place('Props', 'Flower_Bed', q2.x, q2.y, gz(q2), rnd.uniform(0, TAU), 1.3)
    for a_off in (0.95, -0.95):
        a = road + a_off
        q = c + Vector((math.cos(a), math.sin(a), 0)) * (PLAZA_R + 5.5)
        place('Props', 'Flower_Pot', q.x, q.y, gz(q), 0.0, 1.4)
    # village well on the green between the shop side houses and the road
    q = c + d * 150 + side * -112
    if clear_of_routes(T, q, 8):
        place('Props', 'Village_Well', q.x, q.y, gz(q), road, 1.2)
    # road: occasional banner poles, grass tufts and flowers along the edges, a signpost at the village
    pts = next(pts for n, k, w, pts in T.paths if n == 'Entrance_Road')
    acc = 0.0
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        A, B = Vector(a), Vector(b)
        acc += (B - A).xy.length
        dist = (B.xy - c.xy).length
        if dist < 70 or dist > 900:
            continue
        t = (B - A).xy.normalized()
        n = Vector((-t.y, t.x))
        for s in (-1, 1):
            if rnd.random() < 0.55:
                q = B.xy + n * s * rnd.uniform(29, 34)
                q3 = Vector((q.x, q.y, 0))
                place('Foliage', rnd.choice(('Grass_Tuft', 'Flower_Cluster_Yellow', 'Flower_Cluster_Pink', 'Grass_Tuft',
                                             'Bush_02')), q.x, q.y, gz(q3), rnd.uniform(0, TAU), rnd.uniform(1.3, 2.0))
        if acc > 260 and dist < 700:
            acc = 0.0
            q = B.xy + n * 31
            place('Props', 'Verdant_Banner_Pole', q.x, q.y, gz(Vector((q.x, q.y, 0))), math.atan2(t.y, t.x), 1.15)


def dress_hillside(T, place, gz, rnd, c, d, side, mesa_only=False):
    """layered rocks, moss, vines, bushes, flowers and trees at different heights on the portal hill and the cliff"""
    from floor1_detail import grid_index
    zp = T.sample(c.x, c.y)[0]
    centres = ((-290, 0, 260), (-240, 160, 150), (-260, -180, 150), (SITE['mesa'][0], SITE['mesa'][1], 140))
    if mesa_only:
        centres = centres[3:]
    for fc, rc, rad in centres:
        o = c + d * fc + side * rc
        for k in range(70):
            a = rnd.uniform(0, TAU); r = rad * math.sqrt(rnd.random())
            q = o + Vector((math.cos(a), math.sin(a), 0)) * r
            i, j = grid_index(T, q.x, q.y)
            if not T.land[i, j] or T.path_e[i, j] < 10 or T.lake_f[i, j] < 1.2:
                continue
            if (q - c).xy.length < 120 or any((Vector(F.px(*SITE['px'](f, r))) - q.xy).length < 40
                                              for n, f, r, *_ in SITE['houses'] + SITE['stalls']):
                continue                                         # (plaza, stairs, buildings and houses stay clear)
            zq = gz(q)
            sl = T.slope[i, j]
            if zq < zp + 6:
                continue
            rr = rnd.random()
            if sl > 0.8:                                         # rock faces: moss, vines, roots, ledge rocks
                kind = rnd.choice(('Moss_Drape_A', 'Moss_Drape_B', 'Vine_Long', 'Rock_Formation'))
                place('Cliffs' if kind != 'Rock_Formation' else 'Rocks', kind, q.x, q.y, zq - (3 if kind == 'Rock_Formation' else 0),
                      rnd.uniform(0, TAU), rnd.uniform(2.0, 4.0))
            elif rr < 0.18:
                place('Trees', rnd.choice(('Tree_Large_High', 'Tree_Medium_High', 'Tree_Small')), q.x, q.y, zq - 1,
                      rnd.uniform(0, TAU), rnd.uniform(1.8, 2.8))
            elif rr < 0.42:
                place('Rocks', rnd.choice(('Rock_Large', 'Rock_Medium', 'Rock_Formation')), q.x, q.y, zq - 1.5,
                      rnd.uniform(0, TAU), rnd.uniform(1.2, 2.6))
            elif rr < 0.75:
                place('Foliage', rnd.choice(('Bush_01', 'Bush_02', 'Bush_03', 'Fern')), q.x, q.y, zq, rnd.uniform(0, TAU),
                      rnd.uniform(1.8, 3.0))
            else:
                place('Foliage', rnd.choice(('Flower_Cluster_Pink', 'Flower_Cluster_Purple', 'Flower_Cluster_White',
                                             'Flower_Cluster_Yellow')), q.x, q.y, zq, rnd.uniform(0, TAU),
                      rnd.uniform(1.6, 2.4))


TREES_HUB = ('Tree_Large_High', 'Tree_Medium_High', 'Tree_Small')
FLOWERS_HUB = ('Flower_Cluster_Pink', 'Flower_Cluster_Yellow', 'Flower_Cluster_White', 'Flower_Cluster_Purple')
GREENS_HUB = ('Bush_01', 'Bush_02', 'Bush_03', 'Fern', 'Ground_Plant_01', 'Ground_Plant_02', 'Grass_Patch')


def dress_greenery(T, houses, walk_lines, place, gz, rnd, c, d, side):
    """lush village greenery with the hub's trees, bushes and flowers: front gardens, trees between and behind the
    houses, flowers along the road edges and flower meadows on the open grass - all non-colliding foliage (trees
    only collide at their trunks), so riders can still cross the grass"""
    from floor1_detail import grid_index
    from floor1_entrance import PLAZA_R
    stalls = [Vector(F.px(*SITE['px'](f, r))) for n, f, r in SITE['stalls']]
    vp = c + d * SITE['plaza'][0] + side * SITE['plaza'][1] if SITE['plaza'] else c + d * 1e6
    bld = [Vector(F.px(*F.entrance_px(0, s_ * 104))) for s_ in (-1, 1)]         # entrance shop, hatchery

    def seg_d(q, a, b):
        ab = (b - a).xy
        t = max(0.0, min(1.0, (q.xy - a.xy).dot(ab) / max(ab.length_squared, 1e-6)))
        return (q.xy - (a.xy + ab * t)).length

    def free(q, house_r=24.0, walk_r=4.5, path_m=3.0):
        i, j = grid_index(T, q.x, q.y)
        if not (T.land[i, j] and T.path_e[i, j] > path_m and T.lake_f[i, j] > 1.08 and T.river_d[i, j] > 6):
            return False
        if (q - c).xy.length < PLAZA_R + 6 or (q - vp).xy.length < F.VILLAGE_PLAZA_R + 9:
            return False
        if any((Vector(h['pos'][:2]) - q.xy).length < house_r for h in houses):
            return False
        if any((s_ - q.xy).length < 13 for s_ in stalls) or any((b - q.xy).length < 42 for b in bld):
            return False
        return not any(seg_d(q, a, b) < walk_r for a, b in walk_lines)

    n = 0
    # 1. front gardens: flower beds and bushes either side of each porch, flowers hugging the walls
    for h in houses:
        M = h['M']
        for s_ in (-1, 1):
            for k in range(9):
                q = M @ Vector((s_ * rnd.uniform(9.5, h['w'] / 2 + 4), -h['dep'] / 2 - rnd.uniform(1.5, 9.0), 0))
                if free(q, house_r=0.0):
                    kind = rnd.choice(FLOWERS_HUB + ('Bush_01', 'Bush_03', 'Fern'))
                    place('Foliage', kind, q.x, q.y, gz(q), rnd.uniform(0, TAU), rnd.uniform(1.2, 1.9)); n += 1
        for k in range(8):                                       # along the back and sides
            a = rnd.uniform(0, TAU)
            q = M @ Vector((math.cos(a) * (h['w'] / 2 + 2.5), abs(math.sin(a)) * (h['dep'] / 2 + 2.5), 0))
            if free(q, house_r=0.0):
                place('Foliage', rnd.choice(GREENS_HUB[:4] + FLOWERS_HUB), q.x, q.y, gz(q), rnd.uniform(0, TAU),
                      rnd.uniform(1.4, 2.2)); n += 1
    # 2. trees between neighbouring houses (set back from the road) and a dense tree belt behind both rows
    for sgn in (-1, 1):
        row = sorted((h for h in houses if (Vector(h['pos'][:2]) - c.xy).dot(side.xy) * sgn > 0),
                     key=lambda h: (Vector(h['pos'][:2]) - c.xy).dot(d.xy))
        for a, b in zip(row, row[1:]):
            m = (Vector(a['pos'][:2]) + Vector(b['pos'][:2])) / 2
            road = nearest_road(T, m.to_3d())
            back = (m - road.xy).normalized()
            for off, kind, sc in ((16, 'Tree_Small', (1.2, 1.5)), (40, 'Tree_Medium_High', (1.4, 1.7))):
                q = (m + back * off).to_3d()
                if free(q, house_r=22.0):
                    place('Trees', kind, q.x, q.y, gz(q) - 1, rnd.uniform(0, TAU), rnd.uniform(*sc)); n += 1
    for k in range(260):                                         # the green backdrop behind the village rows
        f = rnd.uniform(*SITE['fr1'])
        sgn = rnd.choice((-1, 1))
        road = nearest_road(T, (c + d * f).to_3d())
        q = road + side * sgn * rnd.uniform(112, 190)
        q.z = 0
        if not free(q, house_r=58.0, walk_r=8.0, path_m=10.0) or any((b - q.xy).length < 70 for b in bld):
            continue
        r_ = rnd.random()
        if r_ < 0.3:
            place('Trees', rnd.choice(TREES_HUB), q.x, q.y, gz(q) - 1, rnd.uniform(0, TAU), rnd.uniform(1.4, 2.0))
        elif r_ < 0.75:
            place('Foliage', rnd.choice(GREENS_HUB[:3]), q.x, q.y, gz(q), rnd.uniform(0, TAU), rnd.uniform(2.0, 3.2))
        else:
            place('Foliage', rnd.choice(FLOWERS_HUB), q.x, q.y, gz(q), rnd.uniform(0, TAU), rnd.uniform(1.6, 2.4))
        n += 1
    # 3. flowers, grass and planters lining both road edges through the village
    pts = next(pts for nm, kk, w, pts in T.paths if nm == SITE['road'])
    for a, b in zip(pts, pts[1:]):
        A, B = Vector(a), Vector(b)
        dist = (B.xy - c.xy).length
        if dist < (PLAZA_R + 12 if SITE['key'] == 'entrance' else 20) or dist > SITE['road_r'][1]:
            continue
        t = (B - A).xy.normalized()
        nrm = Vector((-t.y, t.x))
        for s_ in (-1, 1):
            for k in range(3):
                q = (B.xy + t * rnd.uniform(-6, 6) + nrm * s_ * rnd.uniform(30.5, 36)).to_3d()
                if free(q, house_r=20.0, path_m=-1.0):
                    kind = rnd.choice(FLOWERS_HUB + FLOWERS_HUB + ('Grass_Tuft', 'Bush_02', 'Fern'))
                    place('Foliage', kind, q.x, q.y, gz(q), rnd.uniform(0, TAU), rnd.uniform(1.2, 1.8)); n += 1
    # 4. flower meadows: small mixed clusters on the open grass between the houses, the plaza and the lake
    for k in range(90):
        f = rnd.uniform(*SITE['fr2']); r = rnd.uniform(-220, 230)
        o = c + d * f + side * r
        if not free(o, house_r=30.0, path_m=6.0):
            continue
        for j in range(rnd.randint(4, 8)):
            q = o + Vector((rnd.uniform(-7, 7), rnd.uniform(-7, 7), 0))
            if free(q, house_r=26.0, path_m=4.0):
                kind = rnd.choice(FLOWERS_HUB) if j % 3 else rnd.choice(('Grass_Tuft', 'Fern', 'Bush_02'))
                place('Foliage', kind, q.x, q.y, gz(q), rnd.uniform(0, TAU), rnd.uniform(1.1, 1.7)); n += 1
    return n


# ---------------------------------------------------------------- the village heart (concept sheet)
def build_village_heart(T, place, gz, rnd, c, d, side):
    """central plaza with the Verdant fountain, the wooden village arch on the road, the lake islet with its big
    tree, an arched footbridge, shore railings, and lanterns / banners along the new lanes"""
    from floor1_entrance import leaf_emblem, verdant_banner
    from floor1_detail import grid_index
    W = lambda f, r: c + d * f + side * r
    pc = W(*F.VILLAGE_PLAZA)
    z = gz(pc)
    pc.z = z
    R_ = F.VILLAGE_PLAZA_R
    lanes = {n: [Vector(q) for q in pts] for n, k, w, pts in T.paths
             if n in ('Village_Plaza_Lane', 'Village_Lake_Lane', 'Village_Forest_Lane')}
    openings = []                                               # where the lanes meet the rim
    for n, pts in lanes.items():
        q = min(pts, key=lambda v: abs((v.xy - pc.xy).length - (R_ + 30)))
        openings.append(math.atan2(q.y - pc.y, q.x - pc.x))
    stall_dirs = [math.atan2(*(Vector(F.px(*F.village_px(f, r))) - pc.xy).yx) for n, f, r in F.VILLAGE_STALLS[2:]]
    # (the heart only exists at Verdant Village proper)
    gap = 0.42

    def in_gap(a, extra=0.0):
        return any(abs((a - o + math.pi) % TAU - math.pi) < gap + extra for o in openings)

    # --- paving, inner green, low stone border with openings
    p = Part('Village_Plaza', C)
    p.cyl((pc.x, pc.y, z - 1.2), R_ + 3.0, 2.6, 'Castle_Stone_Dark', 64)
    rings = ((0.0, 13.0, 'Castle_Trim'), (13.0, 21.0, None), (21.0, 22.2, 'Gold'), (22.2, 30.0, None),
             (30.0, R_, 'Castle_Trim'))
    for r0, r1, mat in rings:
        n = max(8, int(TAU * r1 / 7))
        for k in range(n):
            a0, a1 = TAU * k / n + 0.004, TAU * (k + 1) / n - 0.004
            p.ring_sector(r0 + 0.12, r1 - 0.12, a0, a1, z + 0.1, z + 0.32 + rnd.uniform(0, 0.08),
                          mat or rnd.choice(('Castle_Stone_Light', 'Castle_Stone_Light', 'Castle_Stone')), 2,
                          (pc.x, pc.y))
    nb = 48
    for k in range(nb):                                         # border: low wall + coping, broken by the openings
        a0, a1 = TAU * k / nb, TAU * (k + 1) / nb
        if in_gap((a0 + a1) / 2):
            continue
        p.ring_sector(R_, R_ + 2.4, a0 + 0.01, a1 - 0.01, z, z + 1.6, rnd.choice(castle.STONES), 2, (pc.x, pc.y))
        p.ring_sector(R_ - 0.2, R_ + 2.6, a0, a1, z + 1.6, z + 2.1, 'Castle_Trim', 2, (pc.x, pc.y))
    # --- the Verdant fountain: stone basin, water, pillar, upper bowl, golden leaf crown
    zf = z + 0.3
    p.cyl((pc.x, pc.y, zf + 1.4), 12.0, 2.8, 'Castle_Stone_Light', 40)
    p.ring_sector(11.0, 12.6, 0, TAU, zf + 2.8, zf + 3.5, 'Castle_Trim', 40, (pc.x, pc.y))
    p.cyl((pc.x, pc.y, zf + 2.45), 11.0, 0.3, 'F1_Water', 40)
    for k in range(8):                                          # carved panels round the basin
        a = TAU * k / 8
        Mk = Matrix.Translation((pc.x + math.cos(a) * 12.1, pc.y + math.sin(a) * 12.1, zf + 1.4)) @ \
            Matrix.Rotation(a + math.pi / 2, 4, 'Z')
        bevel_box(p, Mk, (0, 0, 0), (4.2, 0.4, 1.6), 'Banner_Green', 0.05)
    p.cyl((pc.x, pc.y, zf + 5.5), 2.0, 6.0, 'Castle_Stone', 12)
    p.cyl((pc.x, pc.y, zf + 8.6), 2.4, 1.6, 'Castle_Trim', 16, r2=5.6)
    p.cyl((pc.x, pc.y, zf + 9.5), 5.4, 0.25, 'F1_Water', 24)
    p.ring_sector(5.2, 6.0, 0, TAU, zf + 9.1, zf + 9.8, 'Castle_Trim', 24, (pc.x, pc.y))
    for k in range(4):                                          # four gold leaves back to back
        a = TAU * k / 4
        M = Matrix.Translation((pc.x, pc.y, zf + 13.6)) @ Matrix.Rotation(a, 4, 'Z')
        leaf_emblem(p, M, 7.0, 0.5)
    p.ico((pc.x, pc.y, zf + 17.6), 0.9, 'Gold', 1)
    for k in range(6):                                          # water spilling from the bowl
        a = TAU * k / 6 + 0.3
        q = (pc.x + math.cos(a) * 5.6, pc.y + math.sin(a) * 5.6)
        p.cyl((q[0], q[1], zf + 6.2), 0.45, 6.4, 'F1_Water', 6)
    p.finish()
    # benches, planters, pots, lanterns, banners, a few barrels / crates
    for k in range(10):
        a = TAU * k / 10
        if in_gap(a, 0.2):
            continue
        u = Vector((math.cos(a), math.sin(a), 0))
        q = pc + u * (R_ - 4.5)
        if k % 2 == 0:
            place('Props', 'Bench', q.x, q.y, z + 0.3, a - math.pi / 2, 1.3)
        q = pc + u * (R_ + 8.5)
        place('Props', 'Flower_Bed', q.x, q.y, gz(q), a, 1.4)
        q = pc + u * (R_ + 4.0)
        place('Foliage', rnd.choice(('Bush_01', 'Bush_02', 'Flower_Cluster_Pink', 'Flower_Cluster_Yellow')),
              q.x, q.y, gz(q), rnd.uniform(0, TAU), 1.6)
    for o in openings:
        for s_ in (-1, 1):
            a = o + s_ * (gap + 0.06)
            q = pc + Vector((math.cos(a), math.sin(a), 0)) * (R_ + 1.2)
            place('Props', 'Lantern_Wood', q.x, q.y, z + 2.1, a, 1.3)
            L = bpy.data.lights.new('Village_Plaza_Lamp', 'POINT')
            L.color = (1.0, 0.7, 0.38); L.energy = 1500; L.shadow_soft_size = 1.0
            lo = bpy.data.objects.new(L.name, L); lo.location = (q.x, q.y, z + 9)
            bpy.data.collections[LIGHTS].objects.link(lo)
        q = pc + Vector((math.cos(o), math.sin(o), 0)) * (R_ + 18) + \
            Vector((-math.sin(o), math.cos(o), 0)) * 34
        place('Props', 'Verdant_Banner_Pole', q.x, q.y, gz(q), o + math.pi / 2, 1.2)
    for a in stall_dirs:
        for k, kind in enumerate(('Barrel', 'Crate', 'Basket')):
            q = pc + Vector((math.cos(a + 0.28 + k * 0.07), math.sin(a + 0.28 + k * 0.07), 0)) * (R_ + 20)
            place('Props', kind, q.x, q.y, gz(q), rnd.uniform(0, TAU), 1.1)
    # --- the village arch over the road from the Floor Entrance
    vr = [Vector(q) for n, k, w, pts in T.paths if n == 'Village_Road' for q in pts]
    cand = [k for k, q in enumerate(vr) if (q - c).xy.dot(d.xy) < 0]          # the Floor Entrance side of the village
    ka = min(cand, key=lambda k: abs((vr[k] - c).xy.length - abs(F.VILLAGE_ARCH_F)))
    ra = vr[ka]
    rd = (vr[min(ka + 1, len(vr) - 1)] - vr[max(ka - 1, 0)]).xy.normalized()
    za = gz(ra)
    r3 = Vector((rd.x, rd.y, 0))
    toward = r3 if (ra + r3 - c).xy.length < (ra - c).xy.length else -r3      # into the village
    rg = Vector((ra.x, ra.y, 0))
    F.ARCH_VIEW = (tuple(rg - toward * 130 + Vector((0, 0, za + 9))), tuple(rg + toward * 60 + Vector((0, 0, za + 14))))
    Ma = Matrix.Translation((ra.x, ra.y, za)) @ Matrix.Rotation(math.atan2(rd.y, rd.x) - math.pi / 2, 4, 'Z')
    a_ = Part('Village_Arch', C)
    span = 38.0
    for s_ in (-1, 1):
        bevel_box(a_, Ma, (s_ * span, 0, 1.4), (6.0, 6.0, 2.8), 'Castle_Stone_Light', 0.3)
        bevel_box(a_, Ma, (s_ * span, 0, 14.0), (2.8, 2.8, 23.0), 'Wood_Timber', 0.2)
        for zz in (6.0, 18.0):
            bevel_box(a_, Ma, (s_ * span, 0, zz), (3.4, 3.4, 0.8), 'Wood_Dark', 0.1)
        a_.beam(Ma @ Vector((s_ * span, 0, 19.0)), Ma @ Vector((s_ * (span - 7), 0, 24.6)), 1.2, 1.2, 'Wood_Dark')
    bevel_box(a_, Ma, (0, 0, 25.6), (2 * span + 8, 3.2, 2.2), 'Wood_Timber', 0.2)
    a_.prism([(-span - 6, 26.6), (span + 6, 26.6), (span + 4, 28.4), (0, 31.0), (-span - 4, 28.4)], -3.2, 3.2,
             'Roof_Green', Ma @ FLIP)
    bevel_box(a_, Ma, (0, -1.8, 22.4), (26.0, 0.8, 5.0), 'Sign_Wood', 0.2)
    leaf_emblem(a_, Ma @ Matrix.Translation((0, -2.3, 22.4)), 4.2, 0.4)
    for s_ in (-1, 1):
        verdant_banner(a_, Ma @ Matrix.Translation((s_ * (span - 8), -1.8, 24.4)), 6.0, 9.0, rod=False)
    a_.finish()
    for s_ in (-1, 1):
        q = Ma @ Vector((s_ * (span + 6), -4, 0))
        place('Props', 'Lantern_Wood', q.x, q.y, gz(q), 0, 1.3)
        place('Props', 'Flower_Bed', *(Ma @ Vector((s_ * (span + 6), 6, 0))).xy, gz(Ma @ Vector((s_ * (span + 6), 6, 0))),
              0, 1.3)
    # --- lake: islet tree, arched footbridge from the lake lane, shore railings
    lc = W(*F.VILLAGE_LAKE_C)
    li = next(k for k, l in enumerate(F.LAKES) if l[0] == 'Verdant_Village_Lake')
    zw = F.LAKES[li][2]
    zi = gz(lc)
    for o in [o for o in bpy.data.objects if o.name.startswith(('Mist_Puff', 'Foam_Ring'))
              and (o.location.xy - lc.xy).length < 45]:            # keep the falls' mist off the islet
        bpy.data.objects.remove(o)
    place('Trees', 'Tree_Large_High', lc.x, lc.y, zi - 0.5, rnd.uniform(0, TAU), 2.4)
    for k in range(14):
        a = TAU * k / 14
        q = lc + Vector((math.cos(a), math.sin(a), 0)) * rnd.uniform(15, 22)
        place('Rocks' if k % 2 else 'Foliage', 'Rock_Medium' if k % 2 else rnd.choice(('Flower_Cluster_Pink',
              'Flower_Cluster_White', 'Bush_02')), q.x, q.y, zw - (0.8 if k % 2 else -0.4), rnd.uniform(0, TAU),
              rnd.uniform(1.4, 2.2))
    u = (pc - lc).xy.normalized().to_3d()
    r = 24.0
    while r < 300:
        i, j = grid_index(T, *(lc + u * r).xy)
        if T.lake_f[i, j] >= 1.0:
            break
        r += 2.0
    A = lc + u * 18.0
    B = lc + u * (r + 8.0)
    br = Part('Village_Lake_Bridge', C)
    L_ = (B - A).xy.length
    n = max(8, int(L_ / 2.2))
    yaw = math.atan2(u.y, u.x)
    zb0, zb1 = zi + 0.4, gz(B) + 0.4
    for k in range(n):
        t = (k + 0.5) / n
        q = A.lerp(B, t)
        zq = zb0 + (zb1 - zb0) * t + 5.0 * math.sin(math.pi * t)
        Mq = Matrix.Translation((q.x, q.y, zq)) @ Matrix.Rotation(yaw, 4, 'Z')
        bevel_box(br, Mq, (0, 0, 0), (L_ / n - 0.25, 13.0, 0.7), rnd.choice(('Wood_Plank', 'Wood_Plank', 'Wood_Timber')),
                  0.08)
        if k % 2 == 0:
            for s_ in (-1, 1):
                bevel_box(br, Mq, (0, s_ * 6.6, 2.4), (0.8, 0.8, 4.4), 'Wood_Dark', 0.1)
    for s_ in (-1, 1):                                          # hand rails following the arch
        for k in range(n - 1):
            t0, t1 = (k + 0.5) / n, (k + 1.5) / n
            q0, q1 = A.lerp(B, t0), A.lerp(B, t1)
            z0 = zb0 + (zb1 - zb0) * t0 + 5.0 * math.sin(math.pi * t0) + 4.4
            z1 = zb0 + (zb1 - zb0) * t1 + 5.0 * math.sin(math.pi * t1) + 4.4
            off = Vector((-u.y, u.x, 0)) * s_ * 6.6
            br.beam(Vector((q0.x, q0.y, z0)) + off, Vector((q1.x, q1.y, z1)) + off, 0.7, 0.7, 'Wood_Timber')
    for k in range(n):                                          # support posts into the water
        if k % 3 == 1:
            t = (k + 0.5) / n
            q = A.lerp(B, t)
            zq = zb0 + (zb1 - zb0) * t + 5.0 * math.sin(math.pi * t)
            for s_ in (-1, 1):
                off = Vector((-u.y, u.x, 0)) * s_ * 5.5
                br.cyl((q.x + off.x, q.y + off.y, (zq + zw - 3) / 2), 0.7, zq - zw + 3, 'Wood_Dark', 8)
    br.finish()
    for t in (0.0, 1.0):
        q = A.lerp(B, t) + Vector((-u.y, u.x, 0)) * 8.5
        place('Props', 'Lantern_Wood', q.x, q.y, gz(q), yaw, 1.2)
    # railings on the steep far shore (the village side stays open to the water)
    for k in range(40):
        a = TAU * k / 40
        v = Vector((math.cos(a), math.sin(a), 0))
        if v.dot(u) > -0.15:
            continue
        rr = 24.0
        while rr < 300:
            i, j = grid_index(T, *(lc + v * rr).xy)
            if T.lake_f[i, j] >= 1.0:
                break
            rr += 2.0
        q = lc + v * (rr + 3.0)
        if T.path_e[grid_index(T, q.x, q.y)] > 4:
            place('Props', 'Wood_Fence', q.x, q.y, gz(q), a + math.pi / 2, 1.2)
    # lanterns along the new lanes, alternate sides
    for n_, pts in lanes.items():
        acc, sgn = 0.0, 1
        for a0, b0 in zip(pts, pts[1:]):
            acc += (b0 - a0).xy.length
            if acc < 70 or (b0.xy - pc.xy).length < R_ + 20:
                continue
            acc = 0.0
            t = (b0 - a0).xy.normalized()
            w = 31 if n_ == 'Village_Plaza_Lane' else 23
            q = b0.xy + Vector((-t.y, t.x)) * sgn * w
            q3 = Vector((q.x, q.y, 0))
            place('Props', 'Lantern_Wood', q.x, q.y, gz(q3), math.atan2(t.y, t.x), 1.25)
            sgn = -sgn
    return dict(centre=(pc.x, pc.y, z), radius=R_, fountain=(pc.x, pc.y, z), arch=(ra.x, ra.y, za),
                bridge=((A.x, A.y), (B.x, B.y)))
