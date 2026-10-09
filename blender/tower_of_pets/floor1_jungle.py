"""TOWER OF PETS - FLOOR 1 JUNGLE asset set (Jungle Fortress region) and its integration.

Reusable library assets in the hub's faceted low-poly style (foliage.py leaves, clusters, tubes and vines), each one
mesh, organised in sub-collections of the asset library and placed only as linked duplicates (the Roblox scatter):

  Jungle_Trees    Jungle_Canopy_Tree, Ancient_Jungle_Tree, Tropical_Palm, Banana_Tree, Flowering_Jungle_Tree
  Jungle_Plants   Monstera_Plant, Jungle_Bush, Red_Jungle_Plant, Pink_Jungle_Plant, Purple_Accent_Plant, Leafy_Shrub,
                  Ground_Cover, Jungle_Grass, Bamboo_Cluster, Jungle_Roots (+ the existing Tropical_Plant, Fern,
                  Mushrooms)
  Jungle_Vines    Vine_Cluster (hanging), Creeping_Vines (flat, for walls)
  Jungle_Rocks    Jungle_Rock_Large, Mossy_Boulder, Jungle_Rock_Formation, Flat_Rock, Root_Rock
  Jungle_Cliffs   Cliff_Segment, Cliff_Edge
  Ancient_Ruins   Ancient_Pillar, Broken_Pillar, Overgrown_Arch, Jungle_Statue, Ruin_Wall_Jungle, Obelisk,
                  Mossy_Stairs, Jungle_Gate, Buried_Blocks, Broken_Ruin_Rock, Jungle_Brazier
  Waterfalls_And_Water  Water_Plant

dress_jungle(T) then uses them where the map is jungle: denser mixed jungle on the Jungle Fortress landmass, ruins of
an older civilisation placed deliberately along the fortress roads, vines and cliff-edge pieces on the rims, banks
of the jungle rivers, and a mossy boulder field round the plateau foot.
"""
import math, random
import bpy
from mathutils import Vector, Matrix
from common import Part, mat_plain, mat_noise, coll, TAU, ASSETS
import foliage
from foliage import tube, curve, leaf, leaf_cluster, vine, roots, broad_plant
import castle
from castle import bevel_box
import floor1 as F

JUNGLE_COLLS = ('Jungle_Trees', 'Jungle_Plants', 'Jungle_Vines', 'Jungle_Rocks', 'Jungle_Cliffs', 'Ancient_Ruins',
                'Waterfalls_And_Water')
JF_AREAS = ('Jungle_Fortress', 'Fortress_Heights', 'Beast_Cave')
CANOPY = ('Leaves_Mid', 'Leaves_Light', 'JF_Leaf_Jungle', 'Leaves_Highlight')


def build_jungle_materials():
    P, N = mat_plain, mat_noise
    P('JF_Leaf_Jungle', (0.32, 0.70, 0.10), 0.65)             # the sheet's yellow-green
    P('JF_Leaf_Deep', (0.04, 0.32, 0.10), 0.7)
    P('JF_Leaf_Teal', (0.05, 0.45, 0.32), 0.65)
    P('JF_Flower_Red', (0.92, 0.12, 0.16), 0.55)
    P('JF_Flower_Pink', (1.0, 0.36, 0.62), 0.55)
    P('JF_Leaf_Purple', (0.48, 0.24, 0.80), 0.6)
    P('JF_Leaf_Red', (0.72, 0.10, 0.12), 0.6)
    P('JF_Bamboo', (0.56, 0.72, 0.22), 0.6)
    P('JF_Bamboo_Node', (0.36, 0.48, 0.12), 0.7)
    P('JF_Moss', (0.24, 0.52, 0.12), 0.9)
    P('JF_Root', (0.40, 0.26, 0.14), 0.85)
    P('JF_Jade', (0.06, 0.36, 0.20), 0.45)
    N('JF_Rock', (0.46, 0.44, 0.40), (0.54, 0.51, 0.46), 0.85, 0.06, 0.12, 0.8)
    N('JF_Rock_Dark', (0.30, 0.29, 0.28), (0.36, 0.34, 0.33), 0.85, 0.06, 0.12, 0.8)
    N('JF_Ruin_Stone', (0.62, 0.58, 0.50), (0.68, 0.64, 0.55), 0.85, 0.06, 0.12, 0.8)
    N('JF_Stone_Moss', (0.42, 0.50, 0.30), (0.48, 0.56, 0.34), 0.85, 0.06, 0.12, 0.8)
    P('JF_Brazier_Gold', (0.95, 0.66, 0.16), 0.3, metal=0.8)


def _jlib(name, sub, builder, *a, **kw):
    """library asset in its jungle sub-collection (hidden with the rest of the library)"""
    from floor1_detail import LIB
    coll(sub, LIB)
    p = Part('ASSET_' + name, sub)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def jitter_rock(p, c, r, rnd, scale=(1, 1, 1), mat='JF_Rock', amount=0.22):
    vs = p.ico(c, r, mat, 1, scale, smooth=False)
    for v in vs:
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.6))) * r * amount
        v.co.z = max(v.co.z, Vector(c).z - r * scale[2] * 0.55)       # flat-ish base sits on the ground
    return vs


def moss_cap(p, c, r, rnd, n=4, mat='JF_Moss'):
    for k in range(n):
        p.ico(Vector(c) + Vector((rnd.uniform(-r, r) * 0.5, rnd.uniform(-r, r) * 0.5, 0)), r * rnd.uniform(0.35, 0.55),
              mat, 1, (1.4, 1.4, 0.35), smooth=False)


# ---------------------------------------------------------------- trees ----
def canopy_tree(p, rnd):
    """main jungle tree: tall buttressed trunk, wide flat dense umbrella canopy"""
    top = 15.0
    tube(p, [Vector((0, 0, -0.4)), Vector((0.2, 0, 5)), Vector((-0.2, 0.3, 10)), Vector((0.3, 0, top))],
         [2.0, 1.3, 1.1, 0.9], 'Trunk', 8, phase=0.3)
    roots(p, 1.6, 7, rnd, reach=3.4, z=1.6, mat='Trunk')
    ends = []
    for k in range(5):
        a = TAU * k / 5 + rnd.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), 0))
        start = Vector((0, 0, top - 2.5 + k * 0.4))
        end = start + d * rnd.uniform(8.5, 10.5) + Vector((0, 0, rnd.uniform(2.5, 4.0)))
        tube(p, curve(start, end, Vector((0, 0, 1.5)), 4), [0.8, 0.6, 0.42, 0.28], 'Trunk', 6)
        ends.append(end)
    for e in ends:
        leaf_cluster(p, e + Vector((0, 0, 1.2)), 5.4, rnd, 30, squash=0.5, outer=CANOPY)
    for k in range(5):
        a = TAU * (k + 0.5) / 5
        leaf_cluster(p, Vector((math.cos(a) * 5.5, math.sin(a) * 5.5, top + 4.4)), 5.0, rnd, 26, squash=0.5,
                     outer=CANOPY)
    leaf_cluster(p, Vector((0, 0, top + 5.6)), 5.8, rnd, 30, squash=0.5, outer=CANOPY)
    for k in range(6):
        e = ends[k % len(ends)]
        vine(p, e + Vector((rnd.uniform(-2, 2), rnd.uniform(-2, 2), -1.5)), rnd.uniform(3, 7), rnd)


def ancient_tree(p, rnd):
    """thick gnarled trunk, big exposed roots, moss and many hanging vines"""
    tube(p, [Vector((0, 0, -0.6)), Vector((0.5, 0.2, 4)), Vector((-0.4, 0.4, 8)), Vector((0.2, 0, 11))],
         [3.4, 2.5, 2.2, 1.9], 'Trunk', 9, phase=0.2)
    roots(p, 3.0, 9, rnd, reach=5.5, z=2.6, mat='Trunk')
    for k in range(10):
        a = rnd.uniform(0, TAU); z = rnd.uniform(0.5, 9)
        p.ico(Vector((math.cos(a) * 2.3, math.sin(a) * 2.3, z)), rnd.uniform(0.7, 1.2), 'JF_Moss', 1, (1.2, 1.2, 0.5),
              smooth=False)
    clusters = []
    for k in range(4):
        a = TAU * k / 4 + rnd.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), 0))
        s = Vector((0, 0, 10.5))
        e = s + d * rnd.uniform(6, 8) + Vector((0, 0, rnd.uniform(3, 5)))
        tube(p, curve(s, e, Vector((0, 0, 1.5)) - d, 4), [1.4, 1.0, 0.7, 0.45], 'Trunk', 7)
        clusters.append(e + Vector((0, 0, 1.5)))
    clusters.append(Vector((0, 0, 17.5)))
    for c in clusters:
        leaf_cluster(p, c, 5.2, rnd, 30, squash=0.65, outer=('Leaves_Mid', 'JF_Leaf_Deep', 'Leaves_Light', 'JF_Leaf_Teal'),
                     core='JF_Leaf_Deep')
    for k in range(14):
        c = clusters[k % len(clusters)]
        vine(p, c + Vector((rnd.uniform(-3, 3), rnd.uniform(-3, 3), -2.6)), rnd.uniform(4, 9), rnd, 1.1)


def tropical_palm(p, rnd):
    """tall leaning ringed trunk, crown of long segmented fronds of broad leaflets, coconuts"""
    n = 10
    lean = Vector((rnd.uniform(0.8, 1.2), 0, 0))
    pts = [lean * (0.09 * i * i / n) + Vector((0, 0, 1.9 * i)) for i in range(n + 1)]
    tube(p, pts, [0.85 - 0.035 * i for i in range(n + 1)], 'Palm_Trunk', 7)
    for i in range(1, n, 1):
        p.torus(pts[i], 0.8 - 0.035 * i, 0.13, 'Trunk', 10, 4)
    top = pts[-1]
    for k in range(10):
        a = TAU * k / 10 + rnd.uniform(-0.12, 0.12)
        d = Vector((math.cos(a), math.sin(a), 0))
        path = [top + d * (6.5 * t) + Vector((0, 0, 1.8 * math.sin(math.pi * t * 0.75) - 2.8 * t * t)) for t in
                (j / 5 for j in range(6))]
        tube(p, path, [0.18, 0.15, 0.12, 0.09, 0.06, 0.03], 'Vine_Green', 4)
        for j in range(1, 6):
            q = path[j]
            tng = (path[j] - path[j - 1]).normalized()
            side = Vector((-d.y, d.x, 0))
            for s in (-1, 1):
                leaf(p, q, (side * s * 0.8 + tng * 0.6 + Vector((0, 0, -0.5))), Vector((0, 0, 1)),
                     2.4 - 0.25 * j, 0.7, ('Palm_Leaf', 'JF_Leaf_Jungle', 'Leaves_Mid')[(k + j) % 3], 0.12)
    for k in range(4):
        a = TAU * k / 4
        p.ico(top + Vector((math.cos(a) * 0.75, math.sin(a) * 0.75, -0.7)), 0.5, 'Trunk_Dark', 1)


def banana_tree(p, rnd):
    """clump of soft stems with huge paddle leaves"""
    for k in range(3):
        a = TAU * k / 3 + rnd.uniform(-0.3, 0.3)
        base = Vector((math.cos(a), math.sin(a), 0)) * 1.0
        h = rnd.uniform(6.5, 9.0)
        top = base + Vector((math.cos(a) * 0.6, math.sin(a) * 0.6, h))
        tube(p, [base, base + (top - base) * 0.5, top], [0.55, 0.45, 0.35], 'Palm_Trunk', 6)
        for j in range(6):
            b = rnd.uniform(0, TAU)
            d = Vector((math.cos(b), math.sin(b), 0))
            el = rnd.uniform(0.3, 1.2)
            leaf(p, top, d + Vector((0, 0, el)), Vector((0, 0, 1)), rnd.uniform(5.0, 6.5), 2.2,
                 ('JF_Leaf_Jungle', 'Leaves_Light', 'Leaves_Mid')[j % 3], 0.1)
    p.ico(Vector((0, 0, 0.8)), 1.6, 'JF_Leaf_Deep', 1, (1, 1, 0.6), smooth=False)


def flowering_tree(p, rnd):
    """medium jungle tree with pink / red flower clusters in the crown"""
    tube(p, [Vector((0, 0, -0.4)), Vector((0.3, 0, 4)), Vector((0, 0.3, 8))], [1.2, 0.9, 0.75], 'Trunk', 7)
    roots(p, 1.0, 5, rnd, reach=2.2, z=1.0)
    cs = [Vector((0, 0, 13))]
    for k in range(3):
        a = TAU * k / 3 + 0.4
        e = Vector((math.cos(a) * 4.5, math.sin(a) * 4.5, 10.5))
        tube(p, curve(Vector((0, 0, 7.5)), e, Vector((0, 0, 1)), 4), [0.6, 0.45, 0.32, 0.2], 'Trunk', 6)
        cs.append(e + Vector((0, 0, 1.0)))
    for c in cs:
        leaf_cluster(p, c, 4.4, rnd, 30, squash=0.75,
                     outer=('Leaves_Mid', 'JF_Flower_Pink', 'Leaves_Light', 'JF_Flower_Red', 'JF_Flower_Pink'))


# ---------------------------------------------------------------- plants ---
def monstera(p, rnd):
    """big split leaves (each blade drawn as two lobes either side of the midrib)"""
    for k in range(7):
        a = TAU * k / 7 + rnd.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), 0))
        stem_top = d * 1.4 + Vector((0, 0, rnd.uniform(1.8, 2.8)))
        tube(p, [Vector((0, 0, 0.1)), d * 0.6 + Vector((0, 0, 1.5)), stem_top], [0.12, 0.1, 0.07], 'Vine_Green', 4)
        side = Vector((-d.y, d.x, 0))
        for s in (-1, 1):
            for j in range(2):
                leaf(p, stem_top + d * (0.9 * j), d * 0.6 + side * s * 0.8 + Vector((0, 0, -0.25)), Vector((0, 0, 1)),
                     1.7 - 0.3 * j, 0.9, 'JF_Leaf_Deep' if k % 2 else 'Leaves_Mid', 0.1)


def jungle_bush(p, rnd):
    for x, y, z, R in ((-1.1, 0.0, 1.2, 1.7), (1.1, 0.2, 1.2, 1.6), (0.0, -0.8, 1.5, 1.6), (0.1, 0.6, 2.2, 1.6)):
        leaf_cluster(p, (x, y, z), R, rnd, 22, squash=0.8, outer=('Leaves_Mid', 'JF_Leaf_Deep', 'JF_Leaf_Jungle'),
                     core='JF_Leaf_Deep')


def red_plant(p, rnd):
    broad_plant(p, rnd, 9, 2.4, 0.6, 1.4, 0.2, ('JF_Leaf_Red', 'JF_Flower_Red', 'JF_Leaf_Red'))
    for k in range(4):
        a = TAU * k / 4
        leaf(p, Vector((0, 0, 0.2)), Vector((math.cos(a), math.sin(a), -0.2)), Vector((0, 0, 1)), 1.8, 0.9, 'Leaves_Mid')


def pink_plant(p, rnd):
    broad_plant(p, rnd, 7, 2.0, 0.9, 0.7, 0.2, ('Leaves_Mid', 'Leaves_Light'))
    for k in range(6):
        a = TAU * k / 6 + 0.3
        c = Vector((math.cos(a) * 0.9, math.sin(a) * 0.9, 1.4 + rnd.uniform(0, 0.5)))
        for j in range(5):
            b = TAU * j / 5
            leaf(p, c, Vector((math.cos(b), math.sin(b), 0.5)), Vector((0, 0, 1)), 0.6, 0.45, 'JF_Flower_Pink', 0.1)
        p.ico(c + Vector((0, 0, 0.15)), 0.18, 'Flower_Center', 1)


def purple_plant(p, rnd):
    broad_plant(p, rnd, 8, 2.2, 0.7, 1.2, 0.2, ('JF_Leaf_Purple', 'JF_Leaf_Purple', 'Leaves_Mid'))


def leafy_shrub(p, rnd):
    for x, y, z, R in ((-0.5, 0, 0.9, 1.2), (0.6, 0.2, 1.0, 1.1), (0.0, 0.0, 1.6, 1.0)):
        leaf_cluster(p, (x, y, z), R, rnd, 18, squash=0.9, outer=('JF_Leaf_Jungle', 'Leaves_Light', 'Leaves_Mid'))


def ground_cover(p, rnd):
    for k in range(7):
        a = rnd.uniform(0, TAU); r = rnd.uniform(0, 2.4)
        leaf_cluster(p, (math.cos(a) * r, math.sin(a) * r, 0.25), rnd.uniform(0.8, 1.1), rnd, 12, squash=0.35,
                     outer=('Leaves_Mid', 'JF_Leaf_Jungle', 'Leaves_Light'))


def jungle_grass(p, rnd):
    for k in range(22):
        a = rnd.uniform(0, TAU); r = rnd.uniform(0, 1.3)
        base = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        tip = base + Vector((math.cos(a) * rnd.uniform(0.3, 1.0), math.sin(a) * rnd.uniform(0.3, 1.0),
                             rnd.uniform(1.8, 3.2)))
        p.cone(base, 0.16, (tip - base).z, rnd.choice(('JF_Leaf_Jungle', 'Leaves_Mid', 'Leaves_Light')), 3)


def bamboo(p, rnd):
    for k in range(7):
        a = TAU * k / 7 + rnd.uniform(-0.3, 0.3); r = rnd.uniform(0.3, 1.4)
        b = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        h = rnd.uniform(9, 14)
        lean = Vector((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), 0))
        tube(p, [b, b + lean * 0.5 + Vector((0, 0, h / 2)), b + lean + Vector((0, 0, h))], [0.32, 0.28, 0.24],
             'JF_Bamboo', 6)
        for j in range(1, int(h / 1.8)):
            t = j * 1.8 / h
            p.torus(b + lean * t + Vector((0, 0, h * t)), 0.31 - 0.06 * t, 0.07, 'JF_Bamboo_Node', 8, 3)
        for j in range(4):
            q = b + lean * (0.6 + 0.1 * j) + Vector((0, 0, h * (0.6 + 0.1 * j)))
            c = rnd.uniform(0, TAU)
            leaf(p, q, Vector((math.cos(c), math.sin(c), -0.2)), Vector((0, 0, 1)), 1.6, 0.4, 'JF_Leaf_Jungle', 0.08)


def jungle_roots(p, rnd):
    p.ico(Vector((0, 0, 0.2)), 1.6, 'JF_Root', 1, (1.2, 1.2, 0.5), smooth=False)
    roots(p, 2.6, 8, rnd, reach=4.5, z=1.8, mat='JF_Root')
    moss_cap(p, Vector((0, 0, 1.0)), 1.6, rnd, 3)


def vine_cluster(p, rnd):
    """bundle of hanging vines (origin at the top, hangs down)"""
    for k in range(7):
        vine(p, Vector((rnd.uniform(-2.5, 2.5), rnd.uniform(-0.5, 0.5), 0)), rnd.uniform(5, 11), rnd, 1.4,
             mats=('Leaves_Mid', 'JF_Leaf_Jungle'))
    p.ico(Vector((0, 0, 0.2)), 1.6, 'JF_Moss', 1, (2.0, 0.8, 0.5), smooth=False)


def creeping_vines(p, rnd):
    """flat creeper mat for walls: zig-zag stems with leaves in the XZ plane, front facing -y (origin at the bottom)"""
    for k in range(8):
        x = (k - 3.5) * 1.5 + rnd.uniform(-0.4, 0.4)
        h = rnd.uniform(9, 16) * (1.0 - abs(k - 3.5) * 0.08)
        pts = [Vector((x + math.sin(j * 1.3 + k) * 0.7, -0.2, j * 1.0)) for j in range(int(h) + 1)]
        tube(p, pts, [0.14] * len(pts), 'Vine_Green', 4)
        for j, q in enumerate(pts[1:]):
            for s_ in ((-1, 1) if j % 3 == 0 else ((1,) if j % 2 else (-1,))):
                leaf(p, q + Vector((0, -0.1, 0)), Vector((s_ * 0.8, -0.2, 0.45)), Vector((0, -1, 0)),
                     rnd.uniform(1.1, 1.5), 0.9, ('Leaves_Mid', 'JF_Leaf_Jungle', 'Leaves_Light', 'JF_Leaf_Deep')[j % 4],
                     0.12)


# ---------------------------------------------------------------- rocks ----
def rock_large(p, rnd):
    jitter_rock(p, (0, 0, 2.2), 3.0, rnd, (1.2, 1.0, 0.95), 'JF_Rock')
    jitter_rock(p, (2.4, 0.6, 1.2), 1.7, rnd, (1, 1, 0.9), 'JF_Rock_Dark')
    moss_cap(p, (0, 0, 4.4), 2.0, rnd, 4)
    leaf(p, Vector((1.6, -1.6, 0.4)), Vector((0.6, -0.8, 0.6)), Vector((0, 0, 1)), 1.6, 0.8, 'Leaves_Mid')


def mossy_boulder(p, rnd):
    jitter_rock(p, (0, 0, 1.6), 2.2, rnd, (1.1, 1.0, 0.85), 'JF_Rock', 0.15)
    p.ico(Vector((0, 0, 2.8)), 2.0, 'JF_Moss', 1, (1.15, 1.05, 0.45), smooth=False)
    for k in range(3):
        a = TAU * k / 3
        p.ico(Vector((math.cos(a) * 1.8, math.sin(a) * 1.8, 1.2)), 0.7, 'JF_Moss', 1, (1, 1, 0.6), smooth=False)


def rock_formation(p, rnd):
    for k, (x, y, h, r) in enumerate(((0, 0, 9, 2.4), (2.6, 0.8, 6, 1.8), (-2.2, 1.0, 5, 1.7), (0.8, -2.0, 3.6, 1.5))):
        vs = p.cyl(Vector((x, y, h / 2)), r, h, 'JF_Rock' if k % 2 == 0 else 'JF_Rock_Dark', 6, r2=r * 0.7)
        for v in vs:
            v.co += Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(-0.2, 0.4)))
        moss_cap(p, (x, y, h), r, rnd, 2)
    broad_plant(p, rnd, 6, 1.6, 0.6, 0.6, 9.2)


def flat_rock(p, rnd):
    jitter_rock(p, (0, 0, 0.5), 2.6, rnd, (1.3, 1.0, 0.3), 'JF_Rock', 0.12)
    moss_cap(p, (0.6, 0.3, 0.9), 1.0, rnd, 2)


def root_rock(p, rnd):
    jitter_rock(p, (0, 0, 1.8), 2.4, rnd, (1, 1, 0.9), 'JF_Rock')
    for k in range(5):
        a = TAU * k / 5 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        tube(p, curve(Vector((0, 0, 4.0)) + d * 0.5, d * 3.6 + Vector((0, 0, -0.2)), d * 1.6 + Vector((0, 0, 0.6)), 5),
             [0.45, 0.4, 0.32, 0.22, 0.12], 'JF_Root', 5)
    moss_cap(p, (0, 0, 3.6), 1.4, rnd, 3)


def cliff_segment(p, rnd):
    """stacked angular slabs forming a cliff face piece (front -y)"""
    z = 0.0
    for k in range(5):
        h = rnd.uniform(2.2, 3.4)
        w = rnd.uniform(7, 9)
        vs = p.box(Vector((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.4, 0.4), z + h / 2)), (w, 4.0, h),
                   'JF_Rock' if k % 2 else 'JF_Rock_Dark')
        for v in vs:
            v.co += Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.5, 0.2), rnd.uniform(-0.15, 0.15)))
        z += h
        if k in (1, 3):
            p.ico(Vector((rnd.uniform(-2, 2), -2.0, z)), 0.9, 'JF_Moss', 1, (1.6, 0.6, 0.4), smooth=False)
    moss_cap(p, (0, 0, z), 3.0, rnd, 4)


def cliff_edge(p, rnd):
    """rock lip with a grassy top and ferns (origin at the top edge, rock hangs below)"""
    vs = p.box(Vector((0, 0, -2.2)), (8.0, 4.0, 4.6), 'JF_Rock')
    for v in vs:
        v.co += Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.4, 0.4), rnd.uniform(-0.6, 0.2)))
    p.box(Vector((0, 0.2, 0.15)), (8.6, 4.4, 0.5), 'F1_Grass_Jungle')
    for x in (-2.8, 0.0, 2.6):
        broad_plant_at(p, rnd, Vector((x, -0.6, 0.3)))
    vine(p, Vector((1.5, -2.2, -0.5)), 4.0, rnd)


def broad_plant_at(p, rnd, c):
    for k in range(5):
        a = TAU * k / 5 + rnd.uniform(-0.2, 0.2)
        leaf(p, c, Vector((math.cos(a), math.sin(a), 0.7)), Vector((0, 0, 1)), 1.3, 0.55, 'Leaves_Mid')


# ---------------------------------------------------------------- ruins ----
def glyph_panel(p, M, w, h, mat='JF_Jade', inlay='Gold'):
    bevel_box(p, M, (0, -0.05, 0), (w, 0.3, h), mat, 0.05)
    leaf(p, M @ Vector((0, -0.3, -h * 0.3)), (M.to_3x3() @ Vector((0, 0, 1))), M.to_3x3() @ Vector((0, -1, 0)),
         h * 0.6, w * 0.5, inlay, 0.05)


def ancient_pillar(p, rnd):
    bevel_box(p, Matrix.Identity(4), (0, 0, 0.6), (3.4, 3.4, 1.2), 'JF_Ruin_Stone', 0.2)
    z = 1.2
    for k in range(4):
        h = rnd.uniform(1.8, 2.3)
        bevel_box(p, Matrix.Identity(4), (0, 0, z + h / 2), (2.4, 2.4, h - 0.1),
                  rnd.choice(('JF_Ruin_Stone', 'JF_Ruin_Stone', 'JF_Stone_Moss')), 0.18)
        z += h
    glyph_panel(p, Matrix.Translation((0, -1.2, 4.6)), 1.2, 3.0)
    bevel_box(p, Matrix.Identity(4), (0, 0, z + 0.5), (3.2, 3.2, 1.0), 'JF_Ruin_Stone', 0.2)
    moss_cap(p, (0, 0, z + 1.0), 1.4, rnd, 2)
    vine(p, Vector((1.25, -1.0, z + 0.6)), 4.0, rnd)


def broken_pillar(p, rnd):
    bevel_box(p, Matrix.Identity(4), (0, 0, 0.6), (3.4, 3.4, 1.2), 'JF_Ruin_Stone', 0.2)
    bevel_box(p, Matrix.Identity(4), (0, 0, 2.4), (2.4, 2.4, 2.4), 'JF_Stone_Moss', 0.18)
    vs = p.box(Vector((0, 0, 4.2)), (2.4, 2.4, 1.2), 'JF_Ruin_Stone')
    for v in vs:
        if v.co.z > 4.3:
            v.co.z += rnd.uniform(-0.8, 0.6)
    glyph_panel(p, Matrix.Translation((0, -1.2, 2.4)), 1.2, 1.8)
    bevel_box(p, Matrix.Translation((2.6, 0.5, 0.5)) @ Matrix.Rotation(0.4, 4, 'Y'), (0, 0, 0), (2.4, 2.4, 2.0),
              'JF_Ruin_Stone', 0.18)
    moss_cap(p, (0, 0, 4.8), 1.2, rnd, 2)


def overgrown_arch(p, rnd):
    from common import round_arch
    for s in (-1, 1):
        z = 0.0
        for k in range(5):
            bevel_box(p, Matrix.Identity(4), (s * 6.0, 0, z + 1.1), (2.6, 2.6, 2.1), rnd.choice(('JF_Ruin_Stone', 'JF_Stone_Moss')), 0.18)
            z += 2.2
    castle.voussoirs(p, Matrix.Translation((0, -1.3, 11.0)), round_arch(14.6, 0.0, 12), round_arch(9.4, 0.0, 12),
                     0.0, 2.6, rnd, stone=2.4, mat='JF_Ruin_Stone', backing=False)
    for k in range(5):
        vine(p, Vector((rnd.uniform(-5, 5), -1.4, rnd.uniform(12, 17))), rnd.uniform(3, 7), rnd, 1.2)
    moss_cap(p, (0, 0, 17.6), 2.4, rnd, 4)
    glyph_panel(p, Matrix.Translation((0, -1.6, 16.0)), 1.6, 1.6)


def jungle_statue(p, rnd):
    """small idol: squat beast head on a block body, on a plinth"""
    bevel_box(p, Matrix.Identity(4), (0, 0, 0.7), (3.6, 3.6, 1.4), 'JF_Ruin_Stone', 0.2)
    bevel_box(p, Matrix.Identity(4), (0, 0, 3.0), (2.6, 2.2, 3.2), 'JF_Stone_Moss', 0.3)
    bevel_box(p, Matrix.Identity(4), (0, -0.2, 5.6), (3.0, 2.6, 2.2), 'JF_Ruin_Stone', 0.3)
    for s in (-1, 1):
        p.box(Vector((s * 0.7, -1.55, 5.9)), (0.6, 0.2, 0.45), 'JF_Jade')
        p.cone(Vector((s * 1.1, 0, 6.6)), 0.5, 1.0, 'JF_Ruin_Stone', 4)
    p.box(Vector((0, -1.55, 5.0)), (1.8, 0.25, 0.5), 'JF_Recess')
    p.box(Vector((0, -1.15, 3.8)), (2.0, 0.2, 0.4), 'Gold')
    moss_cap(p, (0, 0, 6.7), 1.0, rnd, 2)


def ruin_wall(p, rnd):
    for row in range(4):
        x = -6.0 + (1.2 if row % 2 else 0)
        while x < 6.0:
            w = rnd.uniform(2.2, 3.2)
            if row < 3 or abs(x) < 3:
                if not (row == 3 and rnd.random() < 0.4):
                    bevel_box(p, Matrix.Identity(4), (x + w / 2, 0, row * 1.8 + 0.9), (w - 0.12, 1.8, 1.7),
                              rnd.choice(('JF_Ruin_Stone', 'JF_Ruin_Stone', 'JF_Stone_Moss')), 0.18)
            x += w
    for k in range(3):
        broad_plant_at(p, rnd, Vector((rnd.uniform(-5, 5), -1.0, 0.1)))
    vine(p, Vector((-2.0, -1.0, 5.6)), 4.0, rnd)
    moss_cap(p, (1, 0, 5.4), 1.8, rnd, 3)


def obelisk(p, rnd):
    bevel_box(p, Matrix.Identity(4), (0, 0, 0.8), (4.0, 4.0, 1.6), 'JF_Ruin_Stone', 0.2)
    p.cyl(Vector((0, 0, 7.6)), 1.6 * math.sqrt(2), 12.0, 'JF_Ruin_Stone', 4, r2=1.0 * math.sqrt(2),
          rot=Matrix.Rotation(math.pi / 4, 3, 'Z'))
    p.cone(Vector((0, 0, 13.6)), 1.0 * math.sqrt(2), 2.2, 'Gold', 4)
    for k in range(4):
        a = k * math.pi / 2
        M = Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((0, -1.45, 6.0)) @ Matrix.Rotation(-0.04, 4, 'X')
        glyph_panel(p, M, 1.0, 3.6)
    moss_cap(p, (0, 0, 1.7), 1.8, rnd, 3)


def mossy_stairs(p, rnd):
    for k in range(6):
        bevel_box(p, Matrix.Identity(4), (0, k * 1.4, 0.35 + k * 0.7), (8.0, 1.5, 0.7 + k * 1.4 * 0.0 + 0.7),
                  rnd.choice(('JF_Ruin_Stone', 'JF_Stone_Moss')), 0.15)
        if k % 2:
            p.ico(Vector((rnd.uniform(-3, 3), k * 1.4 - 0.6, 0.8 + k * 0.7)), 0.5, 'JF_Moss', 1, (1.6, 0.6, 0.3),
                  smooth=False)
    for s in (-1, 1):
        bevel_box(p, Matrix.Identity(4), (s * 4.6, 3.5, 2.2), (1.2, 8.6, 4.4), 'JF_Ruin_Stone', 0.2)


def jungle_gate(p, rnd):
    for s in (-1, 1):
        bevel_box(p, Matrix.Identity(4), (s * 5.0, 0, 0.7), (3.4, 3.4, 1.4), 'JF_Ruin_Stone', 0.2)
        bevel_box(p, Matrix.Identity(4), (s * 5.0, 0, 5.4), (2.6, 2.6, 8.0), 'JF_Ruin_Stone', 0.2)
        glyph_panel(p, Matrix.Translation((s * 5.0, -1.3, 5.4)), 1.4, 4.0)
        tiered = Vector((s * 5.0, 0, 9.4))
        p.cone(tiered, 1.6, 1.6, 'JF_Ruin_Stone', 4)
    bevel_box(p, Matrix.Identity(4), (0, 0, 10.4), (14.0, 2.8, 1.6), 'JF_Ruin_Stone', 0.2)
    bevel_box(p, Matrix.Identity(4), (0, 0, 11.6), (11.0, 2.4, 0.9), 'JF_Ruin_Stone', 0.15)
    p.cyl(Vector((0, -1.5, 11.4)), 1.4, 0.4, 'JF_Jade', 12, axis='Y')
    leaf(p, Vector((0, -1.75, 10.6)), Vector((0, 0, 1)), Vector((0, -1, 0)), 1.7, 1.0, 'Gold', 0.05)
    for k in range(3):
        vine(p, Vector((rnd.uniform(-6, 6), -1.3, 10.0)), rnd.uniform(2, 5), rnd)


def buried_blocks(p, rnd):
    for k in range(5):
        a = rnd.uniform(0, TAU); r = rnd.uniform(0, 3.0)
        M = Matrix.Translation((math.cos(a) * r, math.sin(a) * r, 0.3)) @ Matrix.Rotation(rnd.uniform(-0.5, 0.5), 4, 'X') \
            @ Matrix.Rotation(rnd.uniform(0, TAU), 4, 'Z')
        bevel_box(p, M, (0, 0, 0), (rnd.uniform(1.8, 3.0), rnd.uniform(1.6, 2.4), rnd.uniform(1.2, 2.0)),
                  rnd.choice(('JF_Ruin_Stone', 'JF_Stone_Moss')), 0.18)
    moss_cap(p, (0, 0, 0.8), 2.0, rnd, 3)


def broken_ruin_rock(p, rnd):
    jitter_rock(p, (0, 0, 1.4), 2.0, rnd, (1, 1, 0.8), 'JF_Rock')
    bevel_box(p, Matrix.Translation((1.6, -0.6, 1.4)) @ Matrix.Rotation(0.35, 4, 'Y'), (0, 0, 0), (2.4, 2.0, 2.0),
              'JF_Ruin_Stone', 0.18)
    glyph_panel(p, Matrix.Translation((1.6, -1.7, 1.5)) @ Matrix.Rotation(0.35, 4, 'Y'), 1.0, 1.2)
    moss_cap(p, (0, 0, 2.6), 1.2, rnd, 2)


def jungle_brazier(p, rnd):
    bevel_box(p, Matrix.Identity(4), (0, 0, 0.6), (3.4, 3.4, 1.2), 'JF_Ruin_Stone', 0.2)
    bevel_box(p, Matrix.Identity(4), (0, 0, 2.6), (2.2, 2.2, 2.8), 'JF_Ruin_Stone', 0.2)
    glyph_panel(p, Matrix.Translation((0, -1.1, 2.6)), 1.0, 1.8)
    p.cyl(Vector((0, 0, 4.4)), 1.8, 0.8, 'JF_Brazier_Gold', 10, r2=2.4)
    p.cone(Vector((0, 0, 4.7)), 1.6, 2.6, 'Forge_Glow', 6)
    p.cone(Vector((0, 0, 5.0)), 0.9, 2.8, 'Fire_Core', 5)


def water_plant(p, rnd):
    for k in range(6):
        a = TAU * k / 6 + rnd.uniform(-0.2, 0.2)
        leaf(p, Vector((0, 0, 0.1)), Vector((math.cos(a), math.sin(a), 0.9)), Vector((0, 0, 1)), 2.2, 0.5,
             'JF_Leaf_Teal' if k % 2 else 'Leaves_Mid', 0.1)
    p.cyl(Vector((0, 0, 0.05)), 1.4, 0.1, 'Lily_Pad', 10)


def build_jungle_assets():
    build_jungle_materials()
    R = random.Random
    spec = (
        ('Jungle_Trees', (('Jungle_Canopy_Tree', canopy_tree), ('Ancient_Jungle_Tree', ancient_tree),
                          ('Tropical_Palm', tropical_palm), ('Banana_Tree', banana_tree),
                          ('Flowering_Jungle_Tree', flowering_tree))),
        ('Jungle_Plants', (('Monstera_Plant', monstera), ('Jungle_Bush', jungle_bush), ('Red_Jungle_Plant', red_plant),
                           ('Pink_Jungle_Plant', pink_plant), ('Purple_Accent_Plant', purple_plant),
                           ('Leafy_Shrub', leafy_shrub), ('Ground_Cover', ground_cover), ('Jungle_Grass', jungle_grass),
                           ('Bamboo_Cluster', bamboo), ('Jungle_Roots', jungle_roots))),
        ('Jungle_Vines', (('Vine_Cluster', vine_cluster), ('Creeping_Vines', creeping_vines))),
        ('Jungle_Rocks', (('Jungle_Rock_Large', rock_large), ('Mossy_Boulder', mossy_boulder),
                          ('Jungle_Rock_Formation', rock_formation), ('Flat_Rock', flat_rock), ('Root_Rock', root_rock))),
        ('Jungle_Cliffs', (('Cliff_Segment', cliff_segment), ('Cliff_Edge', cliff_edge))),
        ('Ancient_Ruins', (('Ancient_Pillar', ancient_pillar), ('Broken_Pillar', broken_pillar),
                           ('Overgrown_Arch', overgrown_arch), ('Jungle_Statue', jungle_statue),
                           ('Ruin_Wall_Jungle', ruin_wall), ('Obelisk', obelisk), ('Mossy_Stairs', mossy_stairs),
                           ('Jungle_Gate', jungle_gate), ('Buried_Blocks', buried_blocks),
                           ('Broken_Ruin_Rock', broken_ruin_rock), ('Jungle_Brazier', jungle_brazier))),
        ('Waterfalls_And_Water', (('Water_Plant', water_plant),)),
    )
    k = 600
    for sub, items in spec:
        for name, fn in items:
            _jlib(name, sub, fn, R(k))
            k += 1


# ---------------------------------------------------------------- integration
JUNGLE_TREES = (('Jungle_Canopy_Tree', 0.36), ('Ancient_Jungle_Tree', 0.10), ('Tropical_Palm', 0.16),
                ('Banana_Tree', 0.12), ('Flowering_Jungle_Tree', 0.10), ('Tree_Large_Low', 0.10), ('Palm_Tree', 0.06))
JUNGLE_BUSHES = ('Jungle_Bush', 'Monstera_Plant', 'Tropical_Plant', 'Leafy_Shrub', 'Jungle_Bush', 'Monstera_Plant',
                 'Red_Jungle_Plant', 'Purple_Accent_Plant', 'Pink_Jungle_Plant')
JUNGLE_GROUND = ('Fern', 'Ground_Cover', 'Jungle_Grass', 'Ground_Cover', 'Fern', 'Tropical_Plant', 'Jungle_Grass')


def pick_weighted(rng, table):
    r = rng.random() * sum(w for _, w in table)
    for k, w in table:
        r -= w
        if r <= 0:
            return k
    return table[-1][0]


def dress_jungle(T):
    """ruins along the fortress roads, vines / cliff edges on the jungle rims, river banks, bamboo groves"""
    from floor1_detail import place, ground_z, grid_index
    rng = random.Random(777)
    gz = lambda x, y: float(ground_z(T, x, y))
    jf = {F.AREA_INDEX[n] for n in JF_AREAS}
    n = dict(ruins=0, rims=0, banks=0, bamboo=0)

    def in_jungle(x, y):
        i, j = grid_index(T, x, y)
        return bool(T.land[i, j]) and int(T.own[i, j]) in jf

    def free(x, y, path_m=10.0, slope=0.6):
        i, j = grid_index(T, x, y)
        return bool(T.land[i, j] and T.path_e[i, j] > path_m and T.slope[i, j] < slope and T.lake_f[i, j] > 1.15
                    and T.river_d[i, j] > 10)
    # 1. an older civilisation along the fortress roads: pillar pairs, obelisks, statues, ruined walls, gates
    roads = ('Fortress_Grand_Ramp', 'Fortress_North_Road', 'Fortress_Canyon', 'Fortress_Keep_Approach', 'Beast_Road',
             'Swamp_Cliff_Trail', 'Mossy_Swamp_Trail')
    for name, kind, w, pts in T.paths:
        if name not in roads:
            continue
        acc, k = 0.0, 0
        for a, b in zip(pts, pts[1:]):
            acc += math.hypot(b[0] - a[0], b[1] - a[1])
            if acc < 330 or not in_jungle(b[0], b[1]):
                continue
            acc = 0.0
            t = Vector((b[0] - a[0], b[1] - a[1])).normalized()
            nrm = Vector((-t.y, t.x))
            rot = math.atan2(t.y, t.x) - math.pi / 2
            k += 1
            if k % 3 == 1:                                     # a pair of ancient pillars flanking the road
                for s in (-1, 1):
                    q = Vector(b[:2]) + nrm * s * (w / 2 + 12)
                    if free(q.x, q.y, 3.0, 0.8):
                        place('Ruins', rng.choice(('Ancient_Pillar', 'Ancient_Pillar', 'Broken_Pillar')), q.x, q.y,
                              gz(q.x, q.y) - 0.5, rot, rng.uniform(2.6, 3.2)); n['ruins'] += 1
            elif k % 3 == 2:                                   # a braziered gate or an obelisk beside the road
                s = rng.choice((-1, 1))
                q = Vector(b[:2]) + nrm * s * (w / 2 + 22)
                if free(q.x, q.y, 6.0, 0.7):
                    kind_ = rng.choice(('Obelisk', 'Jungle_Statue', 'Jungle_Brazier', 'Obelisk'))
                    place('Ruins', kind_, q.x, q.y, gz(q.x, q.y) - 0.4, rot + (math.pi if s > 0 else 0),
                          rng.uniform(2.4, 3.0)); n['ruins'] += 1
            else:                                              # abandoned remains back in the trees
                for j in range(2):
                    s = rng.choice((-1, 1))
                    q = Vector(b[:2]) + nrm * s * rng.uniform(w / 2 + 45, w / 2 + 110) + t * rng.uniform(-40, 40)
                    if free(q.x, q.y, 20.0, 0.6):
                        place('Ruins', rng.choice(('Ruin_Wall_Jungle', 'Buried_Blocks', 'Broken_Ruin_Rock',
                                                   'Broken_Pillar', 'Overgrown_Arch', 'Mossy_Stairs')),
                              q.x, q.y, gz(q.x, q.y) - 0.6, rng.uniform(0, TAU), rng.uniform(2.6, 3.6)); n['ruins'] += 1
    # gates where the roads climb onto the plateau and leave it
    for name, frac in (('Fortress_Grand_Ramp', 0.05), ('Fortress_North_Road', 0.5), ('Fortress_Canyon', 0.92)):
        pts = next(p_ for nm, k_, w_, p_ in T.paths if nm == name)
        i = int(len(pts) * frac)
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        t = Vector((b[0] - a[0], b[1] - a[1])).normalized()
        q = Vector(pts[i][:2])
        place('Ruins', 'Jungle_Gate', q.x, q.y, gz(q.x, q.y) - 0.4, math.atan2(t.y, t.x) - math.pi / 2, 5.6)
        for s in (-1, 1):
            r_ = q + Vector((-t.y, t.x)) * s * 36
            place('Ruins', 'Jungle_Brazier', r_.x, r_.y, gz(r_.x, r_.y), 0.0, 2.6)
        n['ruins'] += 3
    # 2. jungle rims: hanging vine clusters, cliff-edge pieces and cliff segments
    import numpy as np
    m = T.land & (T.edge_d <= 2 * F.S) & np.isin(T.own, list(jf))
    ii, jj = np.nonzero(m)
    for t_ in np.random.default_rng(778).permutation(ii.size)[:900]:
        i, j = ii[t_], jj[t_]
        x, y = float(T.VX[i, j]), float(T.VY[i, j])
        nx, ny = float(T.NX[i, j]), float(T.NY[i, j])
        if nx == 0 and ny == 0 or T.path_e[i, j] < 20:
            continue
        rot = math.atan2(-nx, ny)                             # local -y -> outward
        r = rng.random()
        if r < 0.5:
            place('Cliffs', 'Vine_Cluster', x + nx * 2, y + ny * 2, float(T.H[i, j]) - 0.5, rot, rng.uniform(3.0, 5.0))
        elif r < 0.75:
            place('Cliffs', 'Cliff_Edge', x - nx * 4, y - ny * 4, float(T.H[i, j]), rot, rng.uniform(2.6, 3.6))
        else:
            place('Cliffs', 'Cliff_Segment', x + nx * 3, y + ny * 3, float(T.H[i, j]) - rng.uniform(20, 40), rot,
                  rng.uniform(3.5, 5.0))
        n['rims'] += 1
    # 3. jungle river banks: tropical plants, mossy stones, water plants
    for name, pts, zw, w in F.RIVERS:
        if not any(in_jungle(*F.px(x, y)) for x, y in pts):
            continue
        wp = [Vector(F.px(x, y)) for x, y in pts]
        for a, b in zip(wp, wp[1:]):
            L = (b - a).length
            t = (b - a) / max(L, 1e-3)
            nrm = Vector((-t.y, t.x))
            for k in range(int(L / 26)):
                q0 = a + t * (k * 26 + rng.uniform(0, 20))
                s = rng.choice((-1, 1))
                q = q0 + nrm * s * (w / 2 + rng.uniform(4, 16))
                if not in_jungle(q.x, q.y):
                    continue
                kind = rng.choice(('Mossy_Boulder', 'Tropical_Plant', 'Monstera_Plant', 'Jungle_Rock_Large', 'Fern',
                                   'Red_Jungle_Plant'))
                cat = 'Rocks' if 'Rock' in kind or 'Boulder' in kind else 'Foliage'
                place(cat, kind, q.x, q.y, gz(q.x, q.y) - (1.0 if cat == 'Rocks' else 0), rng.uniform(0, TAU),
                      rng.uniform(1.6, 2.8))
                if rng.random() < 0.35:
                    q = q0 + nrm * s * (w / 2 - rng.uniform(2, 6))
                    place('Water', 'Water_Plant', q.x, q.y, zw + 0.05, rng.uniform(0, TAU), rng.uniform(1.6, 2.4))
                n['banks'] += 1
    # 4. bamboo groves and root clusters in clearings of the jungle ring
    x0, x1 = F.px(1060, 0)[0], F.px(1440, 0)[0]
    y0, y1 = F.px(0, 780)[1], F.px(0, 420)[1]
    for k in range(260):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if not in_jungle(x, y) or not free(x, y, 18.0, 0.5):
            continue
        place('Foliage', 'Bamboo_Cluster' if k % 3 else 'Jungle_Roots', x, y, gz(x, y) - 0.3, rng.uniform(0, TAU),
              rng.uniform(1.8, 2.8))
        n['bamboo'] += 1
    return n


# ---------------------------------------------------------------- asset showcase (render only, not exported)
SHOWCASE = (
    (('Jungle_Canopy_Tree', 2.0), ('Ancient_Jungle_Tree', 1.9), ('Tropical_Palm', 2.0), ('Banana_Tree', 2.4),
     ('Flowering_Jungle_Tree', 2.2), ('Bamboo_Cluster', 2.4)),
    (('Monstera_Plant', 3.0), ('Jungle_Bush', 2.6), ('Tropical_Plant', 2.8), ('Fern', 3.0), ('Red_Jungle_Plant', 3.0),
     ('Pink_Jungle_Plant', 3.0), ('Purple_Accent_Plant', 3.0), ('Leafy_Shrub', 3.0), ('Ground_Cover', 3.0),
     ('Jungle_Grass', 3.0), ('Jungle_Roots', 2.4), ('Mushrooms', 3.0), ('Water_Plant', 3.0)),
    (('Jungle_Rock_Large', 2.4), ('Mossy_Boulder', 2.6), ('Jungle_Rock_Formation', 2.2), ('Flat_Rock', 2.6),
     ('Root_Rock', 2.4), ('Cliff_Segment', 2.0), ('Cliff_Edge', 2.4), ('Vine_Cluster', 2.2), ('Creeping_Vines', 2.2)),
    (('Ancient_Pillar', 2.6), ('Broken_Pillar', 2.6), ('Overgrown_Arch', 2.0), ('Jungle_Statue', 2.6),
     ('Ruin_Wall_Jungle', 2.2), ('Obelisk', 2.2), ('Mossy_Stairs', 2.4), ('Jungle_Gate', 2.0), ('Buried_Blocks', 2.6),
     ('Broken_Ruin_Rock', 2.6), ('Jungle_Brazier', 2.6)),
)
SHOW_ORIGIN = Vector((0.0, 30000.0, 0.0))


def build_showcase():
    """the jungle asset set laid out in rows on a grass stage, with its own camera (CAM_F1_Jungle_Assets)"""
    c = coll('JUNGLE_SHOWCASE', F.ROOT)
    g = Part('Showcase_Ground', 'JUNGLE_SHOWCASE')
    g.box(SHOW_ORIGIN + Vector((0, 60, -1)), (620, 360, 2), 'F1_Grass_Jungle')
    for k, row in enumerate(SHOWCASE):
        y = SHOW_ORIGIN.y + 150 - k * 70
        n = len(row)
        width = {0: 400, 1: 360, 2: 380, 3: 440}[k]
        g.box(Vector((SHOW_ORIGIN.x, y, 0.05)), (width + 40, 22 if k else 40, 0.3), 'F1_Path_Stone' if k else 'F1_Jungle_Floor')
        for i, (name, s) in enumerate(row):
            x = SHOW_ORIGIN.x - width / 2 + width * (i + 0.5) / n
            ob = bpy.data.objects.new(name + '_Show', ASSETS[name].data)
            c.objects.link(ob)
            ob.location = (x, y, 6.0 if name == 'Vine_Cluster' else 0.0)
            ob.scale = (s, s, s)
            ob.rotation_euler = (0, 0, 0.25 if 'Vine' not in name and 'Cliff' not in name else 0.0)
    g.finish()
    cam = bpy.data.cameras.new('CAM_F1_Jungle_Assets')
    cam.lens = 34; cam.clip_end = 100000
    o = bpy.data.objects.new('CAM_F1_Jungle_Assets', cam)
    o.location = SHOW_ORIGIN + Vector((0, -215, 135))
    o.rotation_euler = (Vector(SHOW_ORIGIN + Vector((0, 70, 0))) - o.location).to_track_quat('-Z', 'Y').to_euler()
    coll('CAMERAS').objects.link(o)
    o['hide_collections'] = 'GUIDES'
    return o
