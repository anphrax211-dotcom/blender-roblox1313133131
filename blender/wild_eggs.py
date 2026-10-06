"""Explorer's Egg + the Wild egg tiers, built with the same voxel style and
builder as boss_eggs.py (same size, grid, emblem placement and naming).

    python3 wild_eggs.py --out ../exports            (or run in Blender)
    python3 wild_eggs.py --only Wild,EpicWild
"""
import sys, os, math, random, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: F401  (loads mathutils when run outside Blender)
from mathutils import Vector, Matrix
from boss_eggs import (C, Ctx, bands, noise, zig, surf, poly, scaled, circle, union, rect,
                       generate, hsh)

EGGS = {}


def egg(fn):
    EGGS[fn.__name__] = fn
    return fn


# --------------------------------------------------------------------------
def tile(B, part, mat, phi, z, w, h, t=0.06, off=0.03, spin=0.0):
    """flat block lying on the egg surface (leaf / armour plate)"""
    p, n = surf(phi, z, off)
    q = n.to_track_quat('Z', 'Y').to_matrix() @ Matrix.Rotation(spin, 3, 'Z')
    B.box(part, mat, p, (w, h, t), q)


def sparkle(B, part, mat, c, r):
    """floating 4-point diamond"""
    c = Vector(c)
    B.crystal(part, mat, c, (0, 0, 1), r * 1.6, r * 0.7, 4)
    B.crystal(part, mat, c, (0, 0, -1), r * 1.6, r * 0.7, 4)


def star(n, r_out, r_in, rot=0.0, cx=0.0, cz=0.0):
    pts = []
    for i in range(n * 2):
        a = rot + i * math.pi / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.sin(a), cz + r * math.cos(a)))
    return poly(pts)


# ---- Explorer's Egg: teal/tan checks, belt + buckles, compass, pouch, map scroll
@egg
def Explorer(B):
    pal = dict(Teal=C(0.02, 0.5, 0.55), TealDark=C(0.01, 0.32, 0.38),
               Tan=C(0.8, 0.65, 0.42), TanShade=C(0.62, 0.48, 0.3),
               Leather=C(0.28, 0.14, 0.05), LeatherDark=C(0.17, 0.08, 0.03),
               Gold=C(1.0, 0.72, 0.15, 0.0, 1.0), GoldDark=C(0.75, 0.45, 0.08, 0.0, 1.0),
               CompassRing=C(1.0, 0.75, 0.15, 0.6), CompassFace=C(0.05, 0.55, 0.75, 0.3),
               CompassStar=C(1.0, 0.92, 0.45, 1.6), Paper=C(0.9, 0.82, 0.62))

    def pat(c):
        if 0.6 <= c.z < 0.78:
            return c.shade('Leather', 'LeatherDark', 0.25)
        if 1.4 <= c.z < 1.52:
            return c.shade('Leather', 'LeatherDark', 0.25)
        if c.z >= 1.52:                       # explorer hat crown
            return c.shade('Tan', 'TanShade', 0.3)
        return c.shade('Teal', 'TealDark', 0.15) if c.brick2 < 0.5 else c.shade('Tan', 'TanShade', 0.2)
    B.body(pat, 1)
    B.emblem(circle(0, 0, 0.38), union(star(4, 0.36, 0.13), star(4, 0.22, 0.08, math.pi / 4)),
             ('CompassRing', 'CompassFace', 'CompassStar'), scale=0.9)
    # hat brim ring
    for n in range(28):
        phi = n / 28 * 2 * math.pi
        p0, nrm = surf(phi, 1.42, 0.0)
        p1, _ = surf(phi + 2 * math.pi / 28, 1.42, 0.0)
        B.beam('HatBrim', 'Leather', p0 + nrm * 0.04, p1 + nrm * 0.04, 0.1, 0.06, 0.2)
    # belt buckles
    for phi in (-1.25, 1.25, math.pi):
        p, n = surf(phi, 0.69, 0.04)
        q = n.to_track_quat('Z', 'Y').to_matrix()
        B.box('Buckles', 'Gold', p, (0.2, 0.22, 0.05), q)
        B.box('Buckles', 'GoldDark', p + n * 0.03, (0.1, 0.12, 0.04), q)
    # badge on the hat band
    p, n = surf(0.7, 1.46, 0.05)
    B.crystal('Badge', 'Gold', p - n * 0.02, n, 0.1, 0.13, 8)
    # pouch on the left
    p, n = surf(-1.6, 0.45, 0.12)
    B.box('Pouch', 'Leather', p, (0.18, 0.42, 0.4))
    B.box('Pouch', 'LeatherDark', p + Vector((-0.02, 0, 0.2)), (0.2, 0.44, 0.1))
    B.box('Pouch', 'Gold', p + Vector((-0.1, 0, 0.1)), (0.04, 0.1, 0.12))
    # rolled map on the right
    p, n = surf(1.55, 1.0, 0.12)
    B.beam('Map', 'Paper', p + Vector((0, -0.05, -0.25)), p + Vector((0, -0.05, 0.25)), 0.16)
    B.box('Map', 'TanShade', p + Vector((0, -0.05, 0)), (0.18, 0.18, 0.06))
    return pal


# ---- Wild Egg: leafy green over soil, glowing seed emblem, vine curl + flower
@egg
def Wild(B):
    pal = dict(Leaf=C(0.12, 0.55, 0.06), LeafLight=C(0.3, 0.75, 0.1), LeafDark=C(0.05, 0.35, 0.04),
               Soil=C(0.2, 0.1, 0.04), SoilDark=C(0.12, 0.06, 0.025),
               SeedOutline=C(0.8, 0.5, 0.05, 0.6), Seed=C(1.0, 0.8, 0.2, 1.3),
               SeedCore=C(1.0, 0.97, 0.6, 2.4), Vine=C(0.08, 0.45, 0.05),
               Petal=C(0.96, 0.96, 0.92), FlowerCentre=C(1.0, 0.75, 0.08, 0.3))

    def pat(c):
        if c.brick < 0.3 or noise(c.x * 4, c.y * 4, c.z * 4, 2) > 0.5:
            return c.shade('Soil', 'SoilDark', 0.4)
        return c.shade('Leaf', 'LeafLight', 0.3, 'LeafDark', 0.2)
    B.body(pat, 2)
    seed = union(circle(0, 0.14, 0.2),
                 poly([(-0.04, -0.06), (-0.34, 0.0), (-0.3, -0.24), (-0.08, -0.38)]),
                 poly([(0.04, -0.06), (0.34, 0.0), (0.3, -0.24), (0.08, -0.38)]),
                 rect(-0.03, 0.03, -0.42, 0.0))
    B.emblem(seed, circle(0, 0.14, 0.1), ('SeedOutline', 'Seed', 'SeedCore'))
    # leaf shingles around the lower half
    rnd = random.Random(2)
    for n in range(16):
        phi = n / 16 * 2 * math.pi
        if abs(math.sin(phi / 2)) < 0.35:
            continue
        for z in (0.35, 0.8, 1.25):
            tile(B, 'Leaves', rnd.choice(('Leaf', 'LeafLight', 'LeafDark')),
                 phi + rnd.uniform(-0.1, 0.1), z + rnd.uniform(-0.08, 0.08), 0.24, 0.32, spin=0.3)
    # vine stem + curl on top
    pts = [Vector((0, 0.05, 1.9)), Vector((0.02, 0.05, 2.15))]
    for t in range(1, 13):
        a = math.pi - t / 12 * 1.6 * math.pi
        r = 0.26 - t * 0.014
        pts.append(Vector((0.02 + 0.26 + r * math.cos(a), 0.05, 2.15 + r * math.sin(a))))
    for t in range(len(pts) - 1):
        B.beam('Vine', 'Vine', pts[t], pts[t + 1], 0.12 - t * 0.004)
    for a, d in ((-0.25, (-1, 0, 0.5)), (0.3, (1, 0, 0.7)), (-0.05, (-0.4, 0, 1))):
        B.box('VineLeaves', 'LeafLight', Vector((a, 0.05, 2.0)) + Vector(d) * 0.18,
              (0.24, 0.06, 0.16), Vector(d).to_track_quat('X', 'Z'))
    # white flower on the upper left
    p, n = surf(-0.6, 1.62, 0.05)
    q = n.to_track_quat('Z', 'Y').to_matrix()
    for k in range(5):
        a = k / 5 * 2 * math.pi
        B.box('Flower', 'Petal', p + q @ Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, 0)),
              (0.13, 0.13, 0.05), q)
    B.box('Flower', 'FlowerCentre', p + n * 0.03, (0.1, 0.1, 0.06), q)
    return pal


# ---- Rare Wild Egg: blue with silver armour, crescent moon, ice crystals
@egg
def RareWild(B):
    pal = dict(Shell=C(0.03, 0.2, 0.75), ShellDark=C(0.015, 0.11, 0.48),
               ShellLight=C(0.08, 0.38, 0.95), Armor=C(0.6, 0.64, 0.72), ArmorDark=C(0.38, 0.42, 0.5),
               MoonOutline=C(0.05, 0.4, 0.9, 0.6), Moon=C(0.3, 0.8, 1.0, 1.3),
               MoonCore=C(0.8, 0.97, 1.0, 2.2), Ice=C(0.25, 0.7, 1.0, 0.5),
               IceLight=C(0.65, 0.92, 1.0, 0.5))

    def pat(c):
        v = c.z - 0.3 * math.cos(c.phi)
        if 0.05 < v < 0.3 or (1.5 < c.z + 0.25 * abs(math.sin(c.phi)) < 1.66):
            return c.shade('Armor', 'ArmorDark', 0.3)
        return c.shade('Shell', 'ShellDark', 0.3, 'ShellLight', 0.15)
    B.body(pat, 3)
    moon = lambda x, z: circle(-0.04, 0, 0.38)(x, z) and not circle(0.17, 0.07, 0.27)(x, z)
    gem = poly([(0.14, 0.18), (0.24, 0.0), (0.14, -0.18), (0.04, 0.0)])
    B.emblem(union(moon, gem), gem, ('MoonOutline', 'Moon', 'MoonCore'))
    # armour plates with gems along the sides
    for s in (-1, 1):
        for z, w in ((0.35, 0.34), (0.85, 0.3), (1.3, 0.26)):
            phi = s * 1.35
            tile(B, 'Armor', 'Armor', phi, z, 0.34, w, 0.1, 0.04)
            p, n = surf(phi, z, 0.1)
            B.crystal('ArmorGems', 'IceLight', p, n, 0.1, 0.08, 4)
    rnd = random.Random(3)
    # crystals: big cluster on top and outward spikes on the sides
    for n in range(7):
        phi = (n - 3) / 3 * 2.0 + math.pi
        p, nrm = surf(phi, 1.72, -0.06)
        B.crystal('Crystals', 'IceLight' if n % 2 else 'Ice', p,
                  (nrm * 0.5 + Vector((0, 0, 1))).normalized(), rnd.uniform(0.45, 0.7), 0.14, 4, rnd.random())
    B.crystal('Crystals', 'Ice', (0.0, 0.05, 1.85), (0.1, 0, 1), 0.85, 0.18, 4)
    for s in (-1, 1):
        for z, ln in ((0.6, 0.55), (1.05, 0.65), (1.5, 0.5)):
            p, nrm = surf(s * 1.75, z, -0.05)
            B.crystal('Crystals', 'Ice', p, nrm + Vector((0, 0, 0.6)), ln, 0.13, 4, z)
    return pal


# ---- Epic Wild Egg: purple, gold star w/ pink gem, glowing ribbon, amethysts
@egg
def EpicWild(B):
    pal = dict(Shell=C(0.16, 0.03, 0.42), ShellDark=C(0.08, 0.01, 0.25),
               ShellLight=C(0.32, 0.08, 0.7), StarOutline=C(0.75, 0.45, 0.08, 0.4),
               Star=C(1.0, 0.75, 0.15, 1.0), StarGem=C(1.0, 0.6, 0.95, 2.2),
               Ribbon=C(0.9, 0.2, 1.0, 2.0), RibbonCore=C(1.0, 0.75, 1.0, 2.5),
               Amethyst=C(0.6, 0.15, 1.0, 0.6), AmethystLight=C(0.85, 0.45, 1.0, 0.6),
               Gold=C(1.0, 0.72, 0.15, 0.0, 1.0))
    B.body(lambda c: c.shade('Shell', 'ShellDark', 0.35, 'ShellLight', 0.2), 4, 0.05)
    B.emblem(union(star(4, 0.5, 0.17), star(4, 0.3, 0.12, math.pi / 4)), star(4, 0.2, 0.08),
             ('StarOutline', 'Star', 'StarGem'))
    # glowing ribbon spiralling around the egg
    n = 40
    pts = []
    for t in range(n + 1):
        u = t / n
        phi = -2.4 + u * 2 * math.pi * 1.15
        p, nrm = surf(phi, 0.18 + 1.55 * u, 0.15)
        pts.append((p, abs(math.sin(phi / 2)) < 0.28))
    for t in range(n):
        if pts[t][1] or pts[t + 1][1]:   # pass behind the emblem
            continue
        B.beam('Ribbon', 'Ribbon', pts[t][0], pts[t + 1][0], 0.16, 0.07, 0.2)
        if t % 2 == 0:
            B.beam('Ribbon', 'RibbonCore', pts[t][0], pts[t + 1][0], 0.05, 0.07, 0.2)
    rnd = random.Random(4)
    for k in range(7):
        phi = (k - 3) / 3 * 1.9 + math.pi
        p, nrm = surf(phi, 1.7, -0.06)
        B.crystal('Amethysts', 'AmethystLight' if k % 2 else 'Amethyst', p,
                  (nrm * 0.6 + Vector((0, 0, 1))).normalized(), rnd.uniform(0.5, 0.85), 0.15, 4, rnd.random())
    for s in (-1, 1):
        p, nrm = surf(s * 1.6, 1.25, -0.05)
        B.crystal('Amethysts', 'Amethyst', p, nrm + Vector((0, 0, 1)), 0.8, 0.15, 4)
    for phi, z in ((-0.75, 1.55), (0.75, 1.55), (-1.1, 0.75), (1.1, 0.75), (-0.5, 0.25), (0.5, 0.25)):
        p, nrm = surf(phi, z, 0.06)
        B.crystal('GoldSpikes', 'Gold', p, nrm, 0.3, 0.12, 4)
    return pal


# ---- Legendary Wild Egg: gold/white checks, sun emblem, fire crown, gold ring
@egg
def LegendaryWild(B):
    pal = dict(Gold=C(1.0, 0.68, 0.12, 0.0, 1.0), GoldDark=C(0.78, 0.45, 0.06, 0.0, 1.0),
               Ivory=C(0.96, 0.92, 0.8), IvoryShade=C(0.82, 0.74, 0.58),
               SunOutline=C(0.95, 0.5, 0.03, 0.8), Sun=C(1.0, 0.78, 0.15, 1.6),
               SunCore=C(1.0, 0.97, 0.65, 3.0), FlameRed=C(1.0, 0.18, 0.03, 0.8),
               FlameOrange=C(1.0, 0.45, 0.03, 0.8), Ring=C(1.0, 0.8, 0.2, 1.5),
               Sparkle=C(1.0, 0.85, 0.3, 1.5))
    B.body(lambda c: c.shade('Gold', 'GoldDark', 0.3) if c.brick2 < 0.55 else c.shade('Ivory', 'IvoryShade', 0.3), 5)
    B.emblem(union(star(8, 0.46, 0.27, math.pi / 8), circle(0, 0, 0.26)), circle(0, 0, 0.17),
             ('SunOutline', 'Sun', 'SunCore'))
    rnd = random.Random(5)
    # fire crown
    for k in range(9):
        a = k / 9 * 2 * math.pi
        x, y = 0.28 * math.sin(a), 0.28 * math.cos(a)
        B.crystal('Crown', 'FlameRed' if k % 2 else 'FlameOrange', (x, y, 1.82),
                  (x * 1.5, y * 1.5, 1), rnd.uniform(0.45, 0.7), 0.13, 4, rnd.random())
    B.crystal('Crown', 'FlameOrange', (0, 0, 1.88), (0, 0, 1), 0.85, 0.17, 4)
    for k in range(8):
        phi = k / 8 * 2 * math.pi + 0.2
        if abs(math.sin(phi / 2)) < 0.3:
            continue
        p, nrm = surf(phi, 1.45, -0.05)
        B.crystal('GoldCrystals', 'Gold', p, (nrm + Vector((0, 0, 0.9))).normalized(), 0.4, 0.11, 4)
    # tilted orbit ring
    R = Matrix.Rotation(math.radians(-22), 3, 'Y') @ Matrix.Rotation(math.radians(12), 3, 'X')
    ring = [Vector((0, 0, 0.85)) + R @ Vector((1.3 * math.cos(t / 36 * 2 * math.pi),
                                                1.3 * math.sin(t / 36 * 2 * math.pi), 0)) for t in range(37)]
    for t in range(36):
        B.beam('Ring', 'Ring', ring[t], ring[t + 1], 0.09, 0.09, 0.2)
    for c, r in (((-1.35, -0.4, 1.5), 0.09), ((1.4, -0.3, 1.65), 0.08), ((-1.2, -0.5, 0.2), 0.07),
                 ((1.25, -0.45, 0.35), 0.07), ((-0.75, -0.6, 2.15), 0.06), ((0.85, -0.5, 2.1), 0.06)):
        sparkle(B, 'Sparkles', 'Sparkle', c, r)
    return pal


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'exports'))
    ap.add_argument('--only', default='')
    ap.add_argument('--blend', action='store_true')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    allpal = {}
    for n in EGGS:
        if not a.only or n in a.only.split(','):
            allpal.update(generate(n, a.out, a.blend, EGGS, 'Egg'))
    with open(os.path.join(a.out, 'wild_palette.json'), 'w') as f:
        json.dump(allpal, f, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
