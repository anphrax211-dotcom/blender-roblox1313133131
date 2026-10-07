"""TOWER OF PETS - FLOATING ISLANDS asset pack (built from the floating-islands reference sheet).

Island bases (rock + grass cap + moss drapes + hanging vines, one mesh each):
    Large_Island (r~40 studs, walkable), Medium_Island (r~24), Small_Island (r~12), Tall_Island (narrow top,
    deep column), Rock_Formation (no grass), Crystal_Island (r~20, crystal-veined rock)
Modular pieces:
    Rock_Large / Rock_Medium / Rock_Small, Grass_Patch, Grass_Tuft, Moss_Drape_A/B,
    Waterfall_Small / _Medium / _Large / _Wide, Bridge_Short / _Medium / _Long, Lantern_Wood, Lantern_Stone_Post,
    Crystal_Small / _Medium / _Large / Crystal_Cluster, Stone_Block, Stone_Pillar, Paw_Banner, Wood_Fence
    (+ the trees, bushes, plants and vines of the foliage pack)
Island variations (collections, placed as collection instances): Island_A ... Island_H

Look: clean faceted cliff blocks in light warm grey with light/dark variation, stacked in layers that taper to
a point; a bright grass cap that overhangs the rim; moss drapes and vines; bright cyan waterfalls from the top.
Units are studs. Island origins are the centre of the grass top (z = 0); waterfalls originate at their lip and
flow toward -Y; bridges run from their origin along +Y.
"""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
from common import Part, MATS, mat_plain, mat_noise, coll, ASSETS, empty, paw, M_front, TAU
from foliage import leaf_cluster, vine, tube, curve

ROOT = 'TOWER_OF_PETS_FLOATING_ISLANDS'
# 'TREES' / 'WATERFALLS' are taken by the foliage pack and the lobby, so those two get a suffix
SUBS = ('ISLANDS', 'ROCKS', 'GRASS', 'TREES (foliage pack)', 'VINES', 'WATERFALLS (modules)', 'BRIDGES', 'LANTERNS',
        'CRYSTALS', 'DECORATIONS', 'ISLAND_VARIATIONS')
ROCK_MATS = ('Island_Rock', 'Island_Rock', 'Island_Rock_Light', 'Island_Rock_Dark')


# ---------------------------------------------------------------- materials -
def build_island_materials():
    P = mat_plain
    mat_noise('Island_Rock', (0.64, 0.55, 0.48), (0.71, 0.62, 0.54), 0.85, 0.08, 0.12, 0.6)
    mat_noise('Island_Rock_Light', (0.78, 0.69, 0.60), (0.84, 0.75, 0.66), 0.85, 0.08, 0.12, 0.6)
    mat_noise('Island_Rock_Dark', (0.46, 0.38, 0.34), (0.53, 0.44, 0.39), 0.85, 0.08, 0.12, 0.6)
    P('Island_Grass', (0.30, 0.80, 0.08), 0.8)
    P('Island_Grass_Dark', (0.16, 0.62, 0.06), 0.8)
    P('Moss', (0.20, 0.66, 0.06), 0.8)
    m = P('Waterfall_Water', (0.25, 0.75, 1.0), 0.1, emit=0.5, emit_rgb=(0.3, 0.8, 1.0), alpha=0.86)
    # vertical streaks of lighter water
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (0.6, 0.6, 0.03)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (0.10, 0.62, 1.0, 1)
    ramp.color_ramp.elements[1].position = 0.62; ramp.color_ramp.elements[1].color = (0.75, 0.96, 1.0, 1)
    L = nt.links.new
    L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs['Vector'], nz.inputs['Vector'])
    L(nz.outputs['Fac'], ramp.inputs['Fac']); L(ramp.outputs['Color'], b.inputs['Base Color'])
    L(ramp.outputs['Color'], b.inputs['Emission Color'])
    P('Water_Splash', (0.90, 0.98, 1.0), 0.5, emit=0.5)
    mat_noise('Wood_Plank', (0.55, 0.30, 0.12), (0.66, 0.38, 0.16), 0.8, 0.5, 0.2, 3.0)
    P('Wood_Dark', (0.30, 0.15, 0.06), 0.8)
    P('Rope_Tan', (0.78, 0.58, 0.32), 0.9)
    P('Crystal_Cyan', (0.02, 0.55, 0.95), 0.08, emit=0.35, emit_rgb=(0.1, 0.8, 1.0))
    P('Crystal_Deep', (0.03, 0.22, 0.90), 0.08, emit=0.35, emit_rgb=(0.1, 0.4, 1.0))
    P('Crystal_Violet', (0.28, 0.10, 0.85), 0.08, emit=0.3, emit_rgb=(0.5, 0.3, 1.0))


# ---------------------------------------------------------------- island base
def outline(rnd, R, n, jitter=0.12, squash=(1.0, 1.0)):
    pts = []
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.12, 0.12) * TAU / n
        r = R * rnd.uniform(1 - jitter, 1 + jitter)
        pts.append((a, r * squash[0], r * squash[1]))
    return pts


def cliff_layers(p, rnd, top, layers, mats=ROCK_MATS):
    """stacked rings of chunky faceted cliff blocks. `top` = [(angle, rx, ry)];
    layers = [(z_top, z_bot, scale_top, scale_bot, inner_frac)] from the rim downward"""
    n = len(top)
    for li, (zt, zb, st, sb, inner) in enumerate(layers):
        for i in range(n):
            a0, rx0, ry0 = top[i]
            a1, rx1, ry1 = top[(i + 1) % n]
            if i == n - 1:
                a1 += TAU
            j_out = rnd.uniform(0.94, 1.06)
            j_bot = rnd.uniform(0.85, 1.15)
            zbb = zb * rnd.uniform(0.9, 1.12)
            def ring(a, rx, ry, s, z):
                return Vector((math.cos(a) * rx * s, math.sin(a) * ry * s, z))
            st_i = st * j_out; sb_i = sb * j_out * j_bot
            q = [ring(a0, rx0, ry0, sb_i * inner, zbb), ring(a0, rx0, ry0, sb_i, zbb),
                 ring(a1, rx1, ry1, sb_i, zbb), ring(a1, rx1, ry1, sb_i * inner, zbb),
                 ring(a0, rx0, ry0, st_i * inner, zt), ring(a0, rx0, ry0, st_i, zt),
                 ring(a1, rx1, ry1, st_i, zt), ring(a1, rx1, ry1, st_i * inner, zt)]
            p.hexa(q, rnd.choice(mats))
            # a facet ridge on the outer face so blocks read as chiselled stone
            am = (a0 + a1) / 2
            rxm, rym = (rx0 + rx1) / 2, (ry0 + ry1) / 2
            ridge_t = ring(am, rxm, rym, st_i * 1.05, zt - (zt - zbb) * 0.15)
            ridge_b = ring(am, rxm, rym, sb_i * 1.07, zbb + (zt - zbb) * 0.25)
            bm = p.bm
            v = [bm.verts.new(x) for x in (q[5], q[6], q[2], q[1], ridge_t, ridge_b)]
            faces = [bm.faces.new((v[0], v[4], v[1])), bm.faces.new((v[1], v[4], v[5], v[2])),
                     bm.faces.new((v[2], v[5], v[3])), bm.faces.new((v[3], v[5], v[4], v[0]))]
            p._faces(faces, rnd.choice(mats))
    # pointed tip under the last layer
    zt, zb, st, sb, inner = layers[-1]
    rr = max(max(rx, ry) for _, rx, ry in top) * sb
    vs = p.cone((0, 0, zb * 1.05), rr * 0.9, -abs(zb) * 0.45, rnd.choice(mats), 7)
    for v in vs:
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)) * rr * 0.08


def grass_cap(p, top, thick, rnd, lip=0.06):
    """bright grass slab following the rim, with a lip hanging over the edge"""
    n = len(top)
    rim = [Vector((math.cos(a) * rx * 1.03, math.sin(a) * ry * 1.03, 0)) for a, rx, ry in top]
    lo = [Vector((math.cos(a) * rx * (1.03 + lip), math.sin(a) * ry * (1.03 + lip), -thick * rnd.uniform(0.9, 1.6)))
          for a, rx, ry in top]
    under = [Vector((math.cos(a) * rx * 0.92, math.sin(a) * ry * 0.92, -thick * 2.0)) for a, rx, ry in top]
    p.loft([under, lo, rim], 'Island_Grass', cap_bottom=True, cap_top=True)
    # a second, darker inner patch so the top is not flat-coloured
    inner = [Vector((math.cos(a) * rx * 0.55 + 0.1, math.sin(a) * ry * 0.5, 0.06)) for a, rx, ry in top]
    p.loft([[v - Vector((0, 0, 0.1)) for v in inner], inner], 'Island_Grass_Dark')


def moss_drapes(p, top, count, depth, rnd, R):
    """green moss sheets hanging over the cliff rim with jagged lower edges"""
    n = len(top)
    for k in range(count):
        i = rnd.randrange(n)
        a0, rx0, ry0 = top[i]
        a1, rx1, ry1 = top[(i + 1) % n]
        if i == n - 1:
            a1 += TAU
        seg = 5
        h = depth * rnd.uniform(0.4, 1.0)
        for s in range(seg):
            t0, t1 = s / seg, (s + 1) / seg
            pa = [Vector((math.cos(a0 + (a1 - a0) * t) * ((rx0 + rx1) / 2) * 1.07,
                          math.sin(a0 + (a1 - a0) * t) * ((ry0 + ry1) / 2) * 1.07, 0)) for t in (t0, t1)]
            tip = (pa[0] + pa[1]) / 2 * 0.985 - Vector((0, 0, h * rnd.uniform(0.5, 1.0)))
            out = (pa[0] + pa[1]).normalized() * R * 0.015
            q = [pa[0] + out - Vector((0, 0, 0.3)), pa[1] + out - Vector((0, 0, 0.3)), tip + out]
            bm = p.bm
            v = [bm.verts.new(x) for x in q] + [bm.verts.new(x - out * 1.6) for x in q]
            faces = [bm.faces.new((v[0], v[1], v[2])), bm.faces.new((v[5], v[4], v[3])),
                     bm.faces.new((v[0], v[3], v[4], v[1])), bm.faces.new((v[1], v[4], v[5], v[2])),
                     bm.faces.new((v[2], v[5], v[3], v[0]))]
            p._faces(faces, rnd.choice(('Moss', 'Island_Grass', 'Moss')))


def rim_vines(p, top, count, rnd, scale, length):
    for k in range(count):
        a, rx, ry = top[rnd.randrange(len(top))]
        a += rnd.uniform(-0.1, 0.1)
        vine(p, (math.cos(a) * rx * 1.06, math.sin(a) * ry * 1.06, -0.4), length * rnd.uniform(0.5, 1.2), rnd,
             scale)


def island_base(p, rnd, R, depth_k=1.0, n=12, squash=(1.0, 1.0), grass=True, moss=8, vines=6, tall=False,
                mats=ROCK_MATS):
    top = outline(rnd, R, n, 0.12, squash)
    d = R * depth_k
    if tall:
        layers = ((-0.25, -0.5 * d, 1.0, 0.95, 0.4), (-0.45 * d, -1.1 * d, 0.9, 0.8, 0.4),
                  (-1.05 * d, -1.8 * d, 0.75, 0.6, 0.4), (-1.7 * d, -2.4 * d, 0.55, 0.35, 0.4))
    else:
        layers = ((-0.25, -0.32 * d, 1.0, 0.94, 0.45), (-0.28 * d, -0.62 * d, 0.84, 0.66, 0.45),
                  (-0.58 * d, -0.92 * d, 0.58, 0.38, 0.45), (-0.88 * d, -1.15 * d, 0.34, 0.2, 0.45))
    cliff_layers(p, rnd, top, layers, mats)
    p.prism([(math.cos(a) * rx * 0.99, math.sin(a) * ry * 0.99) for a, rx, ry in top], -0.33 * d, -0.3, mats[0])
    if grass:
        grass_cap(p, top, max(0.6, R * 0.04), rnd)
        moss_drapes(p, top, moss, d * 0.35, rnd, R)
        rim_vines(p, top, vines, rnd, max(1.0, R / 16), max(3.0, R * 0.25))
    return top


def crystal(p, base, h, r, mat, tilt=(0, 0), sides=6, axis=None):
    """faceted hexagonal crystal with a pointed tip (axis: optional growth direction)"""
    R = Vector(axis).normalized().to_track_quat('Z', 'Y').to_matrix() if axis else Euler((tilt[0], tilt[1], 0)).to_matrix()
    base = Vector(base)
    p.cyl(base + R @ Vector((0, 0, h * 0.38)), r, h * 0.76, mat, sides, rot=R, r2=r * 0.92)
    p.cyl(base + R @ Vector((0, 0, h * 0.88)), 0.0, h * 0.24, mat, sides, rot=R, r2=r * 0.92)


def crystal_cluster(p, base, size, rnd, mats=('Crystal_Cyan', 'Crystal_Deep', 'Crystal_Violet')):
    base = Vector(base)
    crystal(p, base, size, size * 0.18, mats[0])
    for k in range(6):
        a = TAU * k / 6 + rnd.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), 0))
        crystal(p, base + d * size * 0.2, size * rnd.uniform(0.4, 0.7), size * rnd.uniform(0.08, 0.13),
                mats[k % len(mats)], (-d.y * 0.45, d.x * 0.45))


def moss_drape_piece(p, rnd, width, depth):
    """standalone moss sheet (hangs from its origin toward -Z, faces -Y) to dress cliff edges"""
    seg = max(3, int(width / 1.4))
    for s in range(seg):
        x0, x1 = -width / 2 + width * s / seg, -width / 2 + width * (s + 1) / seg
        tip = Vector(((x0 + x1) / 2, 0, -depth * rnd.uniform(0.45, 1.0)))
        q = [Vector((x0, 0, 0.4)), Vector((x1, 0, 0.4)), tip]
        bm = p.bm
        v = [bm.verts.new(x) for x in q] + [bm.verts.new(x + Vector((0, 0.5, 0))) for x in q]
        faces = [bm.faces.new((v[0], v[1], v[2])), bm.faces.new((v[5], v[4], v[3])),
                 bm.faces.new((v[0], v[3], v[4], v[1])), bm.faces.new((v[1], v[4], v[5], v[2])),
                 bm.faces.new((v[2], v[5], v[3], v[0]))]
        p._faces(faces, rnd.choice(('Moss', 'Island_Grass')))


def rock_formation(p, rnd):
    """grass-less floating rock cluster for the distant background"""
    TOPS['Rock_Formation'] = island_base(p, rnd, 15, 1.0, 8, grass=False)
    for k, (x, y, z, s) in enumerate(((4, 3, 5, 5.0), (-5, -2, 3, 3.5), (1, -6, 1.5, 2.5))):
        p.prism([(x + math.cos(TAU * i / 6) * s * rnd.uniform(0.8, 1.1), y + math.sin(TAU * i / 6) * s *
                  rnd.uniform(0.8, 1.1)) for i in range(6)], -1, z, rnd.choice(ROCK_MATS))
        p.cone((x, y, z), s * 0.9, s * 0.6, rnd.choice(ROCK_MATS), 6)


TOPS = {}


def rim(name, deg, s=1.0, inset=0.0):
    """point on an island's grass rim at angle deg (+ the rotation that faces outward for a -Y waterfall)"""
    top = TOPS[name]
    a = math.radians(deg) % TAU
    pts = sorted(top)
    for i in range(len(pts)):
        a0, rx0, ry0 = pts[i]
        a1, rx1, ry1 = pts[(i + 1) % len(pts)]
        if i == len(pts) - 1:
            a1 += TAU
        aa = a if a >= a0 else a + TAU
        if a0 <= aa <= a1:
            t = (aa - a0) / (a1 - a0)
            rx, ry = rx0 + (rx1 - rx0) * t, ry0 + (ry1 - ry0) * t
            break
    else:
        _, rx, ry = pts[0]
    k = 1.03 - inset
    return Vector((math.cos(a) * rx * k * s, math.sin(a) * ry * k * s, 0.0))


# ---------------------------------------------------------------- props -----
def rock(p, rnd, size, mats=ROCK_MATS):
    """chunky faceted floating rock: two stacked tapered blocks"""
    top = outline(rnd, size, 7, 0.18)
    cliff_layers(p, rnd, top, ((size * 0.35, -size * 0.3, 0.9, 1.0, 0.3), (-size * 0.25, -size * 0.8, 0.85, 0.5, 0.3)),
                 mats)
    p.prism([(math.cos(a) * rx * 0.88, math.sin(a) * ry * 0.88) for a, rx, ry in top], -size * 0.3, size * 0.4,
            rnd.choice(mats))


def waterfall_mesh(p, rnd, width, drop, stream=8.0, wide=False):
    """water stream across the top (from +Y) pouring over the lip at the origin and falling toward -Y/down"""
    t = 0.7
    # surface stream on the grass leading to the lip
    p.box((0, stream / 2, 0.1), (width * 0.8, stream, 0.25), 'Waterfall_Water')
    # curved pour + straight fall, widening slightly
    cl = [Vector((0, 0, 0.2)), Vector((0, -1.4, -0.4)), Vector((0, -2.4, -2.0)), Vector((0, -2.9, -4.5))]
    n = max(2, int(drop / 25))
    for k in range(1, n + 1):
        cl.append(Vector((0, -2.9 - k * 0.25, -4.5 - (drop - 4.5) * k / n)))
    for i in range(len(cl) - 1):
        a, b = cl[i], cl[i + 1]
        wa = width * (1 + 0.25 * i / len(cl)); wb = width * (1 + 0.25 * (i + 1) / len(cl))
        nrm = (b - a).cross(Vector((1, 0, 0))).normalized() * t / 2
        q = [a + Vector((-wa / 2, 0, 0)) - nrm, a + Vector((wa / 2, 0, 0)) - nrm, a + Vector((wa / 2, 0, 0)) + nrm,
             a + Vector((-wa / 2, 0, 0)) + nrm]
        r = [b + Vector((-wb / 2, 0, 0)) - nrm, b + Vector((wb / 2, 0, 0)) - nrm, b + Vector((wb / 2, 0, 0)) + nrm,
             b + Vector((-wb / 2, 0, 0)) + nrm]
        p.hexa(q + r, 'Waterfall_Water')
    # bright highlight ribbons down the face
    for k in range(3 if not wide else 5):
        x = (k - (1 if not wide else 2)) * width * 0.22
        p.box((x, -3.0 - 0.15, -4.5 - drop * 0.3), (width * 0.05, 0.15, drop * 0.55), 'Water_Splash')
    # splash foam at the lip and spray puffs at the bottom (where it meets the clouds)
    for k in range(5):
        p.ico((rnd.uniform(-0.45, 0.45) * width, -1.6 + rnd.uniform(-0.4, 0.4), -0.6), width * rnd.uniform(0.1, 0.16),
              'Water_Splash', 1, (1.2, 1, 0.7))
    end = cl[-1]
    for k in range(6):
        p.ico(end + Vector((rnd.uniform(-0.6, 0.6) * width, rnd.uniform(-0.3, 0.3) * width, rnd.uniform(-1, 2))),
              width * rnd.uniform(0.25, 0.4), 'Cloud', 2, (1, 1, 0.65))


def bridge_mesh(p, rnd, length, width=6.0, sag=None, a=None, b=None):
    """wooden rope bridge from a to b (default: origin to +Y*length) with chunky end posts"""
    a = Vector(a) if a is not None else Vector((0, 0, 0))
    b = Vector(b) if b is not None else Vector((0, length, 0))
    L = (b - a).length
    sag = L * 0.06 if sag is None else sag
    d = (b - a).normalized()
    side = Vector((-d.y, d.x, 0)).normalized()
    rot = Matrix.Rotation(math.atan2(d.y, d.x) - math.pi / 2, 3, 'Z')
    n = max(4, int(L / 1.3))
    pts = [a + (b - a) * (i / n) - Vector((0, 0, sag * math.sin(math.pi * i / n))) for i in range(n + 1)]
    for i, q in enumerate(pts[1:-1], 1):
        w = width * rnd.uniform(0.94, 1.0)
        p.box(q + side * rnd.uniform(-0.15, 0.15), (w, 1.0, 0.3), rnd.choice(('Wood_Plank', 'Wood_Plank', 'Wood_Dark')),
              rot @ Matrix.Rotation(rnd.uniform(-0.05, 0.05), 3, 'Z'))
    for s in (-1, 1):
        for i in range(n):                                   # under-ropes and hand ropes
            p.beam(pts[i] + side * s * width * 0.42 - Vector((0, 0, 0.2)),
                   pts[i + 1] + side * s * width * 0.42 - Vector((0, 0, 0.2)), 0.22, 0.22, 'Rope_Tan')
            h0 = 2.8 + sag * 0.15 * math.sin(math.pi * i / n)
            p.beam(pts[i] + side * s * width / 2 + Vector((0, 0, 3.0)),
                   pts[i + 1] + side * s * width / 2 + Vector((0, 0, 3.0)), 0.3, 0.3, 'Rope_Tan')
        for i in range(1, n, 3):                             # vertical rope ties
            p.beam(pts[i] + side * s * width / 2, pts[i] + side * s * width / 2 + Vector((0, 0, 3.0)), 0.15, 0.15,
                   'Rope_Tan')
        for q in (a, b):                                     # chunky end posts with rope wraps
            c = q + side * s * (width / 2 + 0.7)
            p.box(c + Vector((0, 0, 1.8)), (1.5, 1.5, 4.6), 'Wood_Dark', rot)
            p.box(c + Vector((0, 0, 4.25)), (1.8, 1.8, 0.4), 'Wood_Plank', rot)
            for z in (2.4, 2.9):
                p.cyl(c + Vector((0, 0, z)), 0.95, 0.35, 'Rope_Tan', 8)


def lantern_wood(p):
    p.box((0, 0, 0.6), (2.4, 2.4, 1.2), 'Island_Rock_Light')
    p.box((0, 0, 3.6), (1.0, 1.0, 5.0), 'Wood_Dark')
    p.cyl((0, 0, 2.4), 0.75, 0.35, 'Rope_Tan', 8); p.cyl((0, 0, 2.9), 0.75, 0.35, 'Rope_Tan', 8)
    p.box((0, 0, 6.3), (1.9, 1.9, 0.35), 'Wood_Dark')
    p.box((0, 0, 7.4), (1.4, 1.4, 1.9), 'Lantern_Glow')
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box((sx * 0.75, sy * 0.75, 7.4), (0.28, 0.28, 2.1), 'Wood_Dark')
    p.box((0, 0, 8.55), (2.1, 2.1, 0.35), 'Wood_Dark')
    p.cone((0, 0, 8.7), 1.5, 0.9, 'Wood_Dark', 4)


def paw_banner(p):
    p.box((0, 0, 0.5), (2.2, 2.2, 1.0), 'Island_Rock_Light')
    p.box((0, 0, 6.0), (0.9, 0.9, 11.0), 'Wood_Dark')
    p.box((0, -0.6, 10.6), (4.4, 0.5, 0.45), 'Gold')
    outline_ = [(-2, 0), (2, 0), (2, -6.5), (0, -8.0), (-2, -6.5)]
    p.prism(outline_, 0, 0.25, 'Banner_Navy', M_front(0, -0.7, 10.3))
    paw(p, M_front(0, -0.98, 7.4), 2.6, 0.12, 'Gold')
    p.box((0, -0.97, 10.0), (3.6, 0.1, 0.25), 'Gold')


def stone_pillar(p, rnd, h=8.0):
    p.box((0, 0, 0.5), (3.0, 3.0, 1.0), 'Island_Rock_Light')
    z = 1.0
    while z < h:
        bh = rnd.uniform(1.4, 2.2)
        p.box((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), z + bh / 2), (2.1, 2.1, bh - 0.08),
              rnd.choice(ROCK_MATS))
        z += bh
    p.box((0, 0, z + 0.3), (2.7, 2.7, 0.6), 'Island_Rock_Light')
    leaf_cluster(p, (0.8, 0.5, z + 0.6), 1.0, rnd, 10, squash=0.6)


def wood_fence(p, length=10.0):
    n = int(length / 2.5) + 1
    for i in range(n):
        x = -length / 2 + i * length / (n - 1)
        p.box((x, 0, 1.3), (0.6, 0.6, 2.6), 'Wood_Dark')
        p.cone((x, 0, 2.6), 0.45, 0.4, 'Wood_Dark', 4)
    for z in (1.0, 2.0):
        p.box((0, 0, z), (length, 0.3, 0.35), 'Wood_Plank')


def grass_patch(p, rnd, R=4.0):
    top = outline(rnd, R, 9, 0.2)
    rim = [Vector((math.cos(a) * rx, math.sin(a) * ry, 0.25)) for a, rx, ry in top]
    lo = [Vector((math.cos(a) * rx * 1.08, math.sin(a) * ry * 1.08, 0.0)) for a, rx, ry in top]
    p.loft([lo, rim], 'Island_Grass')
    grass_tufts(p, rnd, R * 0.8, 6, 0.25)


def grass_tufts(p, rnd, R, count, z=0.0):
    for k in range(count):
        a = rnd.uniform(0, TAU); d = rnd.uniform(0, R)
        c = Vector((math.cos(a) * d, math.sin(a) * d, z))
        for j in range(3):                               # three chunky blades per tuft
            b = rnd.uniform(0, TAU)
            off = Vector((math.cos(b), math.sin(b), 0)) * 0.25
            p.cone(c + off, 0.28, rnd.uniform(0.9, 1.6), rnd.choice(('Island_Grass', 'Leaves_Light', 'Moss')), 3)


# ---------------------------------------------------------------- library ---
def _lib(name, sub, builder, *a, **kw):
    p = Part('ASSET_' + name, sub)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def build_island_assets(parent):
    coll(ROOT, parent)
    for c in SUBS:
        coll(c, ROOT)
    for c in ('Large_Island', 'Medium_Island', 'Small_Island', 'Tall_Island', 'Rock_Formation', 'Crystal_Island'):
        coll(c, 'ISLANDS')
    for c in ('Rock_Large', 'Rock_Medium', 'Rock_Small'):
        coll(c, 'ROCKS')
    R = random.Random
    def base(name, *a, **kw):
        _lib(name, name, lambda p: TOPS.__setitem__(name, island_base(p, *a, **kw)))
    base('Large_Island', R(1), 40, 1.6, 16, (1.0, 0.85), moss=16, vines=12)
    base('Medium_Island', R(2), 24, 1.75, 12, (1.0, 0.9), moss=10, vines=8)
    base('Small_Island', R(3), 12, 1.9, 10, moss=6, vines=5)
    base('Tall_Island', R(4), 11, 1.6, 9, moss=6, vines=6, tall=True)
    _lib('Rock_Formation', 'Rock_Formation', rock_formation, R(5))
    def crystal_island(p):
        top = TOPS['Crystal_Island'] = island_base(p, R(6), 20, 1.7, 11, moss=6, vines=5,
                                                   mats=('Island_Rock', 'Island_Rock_Light', 'Island_Rock_Dark',
                                                         'Island_Rock'))
        rr = R(60)
        for k in range(5):                                   # crystals poking out of the cliff
            a, rx, ry = top[rr.randrange(len(top))]
            d = Vector((math.cos(a), math.sin(a), 0))
            crystal(p, d * rx * 0.8 + Vector((0, 0, -rr.uniform(6, 14))), rr.uniform(6, 10), rr.uniform(1.0, 1.6),
                    rr.choice(('Crystal_Cyan', 'Crystal_Deep', 'Crystal_Violet')), axis=d + Vector((0, 0, 0.9)))
    _lib('Crystal_Island', 'Crystal_Island', crystal_island)
    for name, s, seed in (('Rock_Large', 9.0, 11), ('Rock_Medium', 5.0, 12), ('Rock_Small', 2.4, 13)):
        _lib(name, name, rock, R(seed), s)
    _lib('Grass_Patch', 'GRASS', grass_patch, R(20))
    _lib('Grass_Tuft', 'GRASS', grass_tufts, R(21), 0.6, 3)
    for k in range(2):
        _lib(f'Moss_Drape_{"AB"[k]}', 'VINES', moss_drape_piece, R(30 + k), 6.0 + k * 3, 4.0 + k * 3)
    for name, w, drop, wide in (('Waterfall_Small', 3.5, 30, False), ('Waterfall_Medium', 6, 60, False),
                                ('Waterfall_Large', 10, 120, False), ('Waterfall_Wide', 18, 80, True)):
        _lib(name, 'WATERFALLS (modules)', waterfall_mesh, R(40 + len(name)), w, drop, 8.0, wide)
    for name, L in (('Bridge_Short', 20), ('Bridge_Medium', 40), ('Bridge_Long', 70)):
        _lib(name, 'BRIDGES', bridge_mesh, R(70 + L), L)
    _lib('Lantern_Wood', 'LANTERNS', lantern_wood)
    _lib('Crystal_Small', 'CRYSTALS', crystal, (0, 0, 0), 3.0, 0.55, 'Crystal_Cyan')
    _lib('Crystal_Medium', 'CRYSTALS', crystal, (0, 0, 0), 6.0, 1.0, 'Crystal_Deep')
    _lib('Crystal_Large', 'CRYSTALS', crystal, (0, 0, 0), 11.0, 1.8, 'Crystal_Violet')
    _lib('Crystal_Cluster', 'CRYSTALS', crystal_cluster, (0, 0, 0), 9.0, R(80))
    _lib('Stone_Block', 'DECORATIONS', lambda p: p.box((0, 0, 1.0), (3.0, 2.2, 2.0), 'Island_Rock_Light'))
    _lib('Stone_Pillar', 'DECORATIONS', stone_pillar, R(81))
    _lib('Paw_Banner', 'DECORATIONS', paw_banner)
    _lib('Wood_Fence', 'DECORATIONS', wood_fence, 10.0)


# ---------------------------------------------------------------- variations
def _place(vc, name, root, loc, rot=0.0, s=1.0):
    from common import inst
    return inst(name, f'{root.name}_{name}_{len(vc.objects)}', vc.name, loc, rot, s, root)


def build_variations():
    """Island_A..H: decorated islands assembled from the modular pieces (collection per variation, origin at
    the island top centre) so they can be placed anywhere as collection instances"""
    V = {}
    specs = {
        'Island_A': 'Large tree + waterfall + bridge',
        'Island_B': 'Multiple small trees + grass + lantern',
        'Island_C': 'Crystal formation + waterfall',
        'Island_D': 'Tall tree + vines',
        'Island_E': 'Open grassy platform',
        'Island_F': 'Rock-only formation',
        'Island_G': 'Large waterfall island',
        'Island_H': 'Bridge connection island',
    }
    for key, desc in specs.items():
        c = coll(key, 'ISLAND_VARIATIONS')
        root = empty(f'{key}_Root', key, (0, 0, 0), 0, 8)
        root['description'] = desc
        V[key] = (c, root)

    def P(key, asset, loc, rot=0.0, s=1.0):
        c, root = V[key]
        return _place(c, asset, root, loc, rot, s)

    def fall(key, island, asset, deg, s_isl=1.0, s=1.0):
        q = rim(island, deg, s_isl, 0.02)
        return P(key, asset, q + Vector((0, 0, 0.3)), math.radians(deg) + math.pi / 2, s)

    def bridge(key, island, asset, deg, s_isl=1.0):
        q = rim(island, deg, s_isl, 0.05)
        return P(key, asset, q + Vector((0, 0, 0.2)), math.radians(deg) - math.pi / 2)
    rnd = random.Random(90)
    # A: large island, big lobby tree, large waterfall, bridge leaving east, lanterns, path stones
    P('Island_A', 'Large_Island', (0, 0, 0))
    P('Island_A', 'Tree_Large_High', (-8, 6, 0), 0.6, 1.3)
    P('Island_A', 'Tree_Medium_High', (14, 14, 0), 2.0, 1.1)
    fall('Island_A', 'Large_Island', 'Waterfall_Large', 262)
    bridge('Island_A', 'Large_Island', 'Bridge_Medium', 0)
    for x, y in ((34, -5.5), (34, 5.5)):
        P('Island_A', 'Lantern_Wood', (x, y, 0))
    for k in range(5):
        P('Island_A', 'Stone_Block', (10 + k * 4.5, rnd.uniform(-1, 1), -0.8), rnd.uniform(-0.2, 0.2), (1.2, 1.0, 0.5))
    P('Island_A', 'Stone_Pillar', (-22, -12, 0)); P('Island_A', 'Paw_Banner', (-14, -20, 0), 0.3)
    P('Island_A', 'Crystal_Cluster', (24, 18, 0), 0.4, 0.6)
    for k, (x, y, a) in enumerate(((-26, 4, 'Bush_01'), (-4, -16, 'Bush_02'), (20, -12, 'Bush_03'),
                                   (2, 22, 'Ground_Plant_01'), (-18, 18, 'Bush_02'))):
        P('Island_A', a, (x, y, 0), rnd.uniform(0, TAU), 1.3)
    for k in range(5):
        P('Island_A', 'Grass_Tuft', (rnd.uniform(-25, 25), rnd.uniform(-20, 20), 0), rnd.uniform(0, TAU), 1.5)
    # B: medium island with several small trees, lantern and a fence
    P('Island_B', 'Medium_Island', (0, 0, 0))
    for k, (x, y) in enumerate(((-9, 4), (6, 9), (8, -6))):
        P('Island_B', ('Tree_Small', 'Tree_Medium_High', 'Tree_Small')[k], (x, y, 0), rnd.uniform(0, TAU), 0.9)
    P('Island_B', 'Lantern_Wood', (-4, -12, 0)); P('Island_B', 'Wood_Fence', (2, -17, 0), 0.0, 1.0)
    P('Island_B', 'Bush_01', (-14, -6, 0), 0, 1.1); P('Island_B', 'Ground_Plant_02', (13, 1, 0), 0, 1.2)
    P('Island_B', 'Grass_Patch', (0, 2, 0), 0.5, 1.2)
    # C: crystal island + waterfall
    P('Island_C', 'Crystal_Island', (0, 0, 0))
    P('Island_C', 'Crystal_Cluster', (-4, 2, 0), 0.0, 1.2)
    P('Island_C', 'Crystal_Large', (7, 6, 0), 0.4, 0.9); P('Island_C', 'Crystal_Medium', (10, -2, 0), 1.0)
    P('Island_C', 'Tree_Small', (3, 11, 0), 1.0, 0.9); fall('Island_C', 'Crystal_Island', 'Waterfall_Medium', 272)
    P('Island_C', 'Bush_02', (-12, -6, 0), 0, 1.0); P('Island_C', 'Stone_Pillar', (-11, 8, 0), 0, 0.8)
    # D: tall island with a tall thin tree and lots of vines
    P('Island_D', 'Tall_Island', (0, 0, 0))
    P('Island_D', 'Tree_Tall_Thin', (0, 1, 0), 0.7, 1.1)
    P('Island_D', 'Bush_01', (-5, -4, 0), 0, 0.9); P('Island_D', 'Crystal_Small', (5, -3, 0), 0.3)
    for k in range(5):
        a = TAU * k / 5
        P('Island_D', ('Vine_Long', 'Vine_Medium')[k % 2], (math.cos(a) * 11, math.sin(a) * 11, -0.3), a, 1.6)
    # E: open grassy platform (gameplay space)
    P('Island_E', 'Large_Island', (0, 0, 0))
    for k in range(7):
        P('Island_E', 'Grass_Patch', (rnd.uniform(-24, 24), rnd.uniform(-18, 18), 0), rnd.uniform(0, TAU), 1.3)
    for k in range(6):
        P('Island_E', ('Bush_01', 'Bush_03', 'Ground_Plant_01')[k % 3],
          (math.cos(k) * 30, math.sin(k) * 24, 0), rnd.uniform(0, TAU), 1.2)
    P('Island_E', 'Lantern_Wood', (-6, -26, 0)); P('Island_E', 'Lantern_Wood', (6, -26, 0))
    # F: rock-only formation
    P('Island_F', 'Rock_Formation', (0, 0, 0))
    P('Island_F', 'Rock_Large', (9, 4, 4), 0.5); P('Island_F', 'Rock_Medium', (-8, -3, 2), 1.4)
    P('Island_F', 'Rock_Small', (2, -10, -5), 0.2)
    # G: big waterfall island
    P('Island_G', 'Medium_Island', (0, 0, 0), 0.0, 1.3)
    fall('Island_G', 'Medium_Island', 'Waterfall_Wide', 270, 1.3)
    fall('Island_G', 'Medium_Island', 'Waterfall_Large', 335, 1.3, 0.8)
    P('Island_G', 'Tree_Large_High', (-6, 8, 0), 0.2, 1.0); P('Island_G', 'Tree_Small', (12, 10, 0), 0.0, 1.0)
    P('Island_G', 'Bush_02', (-20, -6, 0), 0, 1.2)
    # H: bridge connection island
    P('Island_H', 'Small_Island', (0, 0, 0), 0.0, 1.3)
    bridge('Island_H', 'Small_Island', 'Bridge_Short', 90, 1.3); bridge('Island_H', 'Small_Island', 'Bridge_Short', 270, 1.3)
    P('Island_H', 'Lantern_Wood', (-6, 4, 0)); P('Island_H', 'Paw_Banner', (6, -4, 0), 0.3)
    P('Island_H', 'Bush_01', (5, 6, 0), 0, 0.8); P('Island_H', 'Grass_Tuft', (-4, -6, 0), 0, 1.3)
    return {k: v[0] for k, v in V.items()}


def place_variation(key, name, collection, loc, rot=0.0, scale=1.0):
    """drop a collection instance of an island variation into the world"""
    e = bpy.data.objects.new(name, None)
    e.instance_type = 'COLLECTION'
    e.instance_collection = bpy.data.collections[key]
    e.empty_display_size = 10
    e.location = loc
    e.rotation_euler = (0, 0, rot)
    e.scale = (scale, scale, scale)
    coll(collection).objects.link(e)
    return e
