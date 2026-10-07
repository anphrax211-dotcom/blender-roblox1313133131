"""TOWER OF PETS - ROBLOX TREES & FOLIAGE asset pack (built from the tree & foliage reference sheet).

Stylised low-poly, flat-shaded pieces:
    trees    Tree_Large_High / Tree_Large_Low, Tree_Medium_High / Tree_Medium_Low, Tree_Small, Tree_Tall_Thin
             (+ Tree_Small_Low, Tree_Tall_Thin_Low for far placements)
    foliage  Bush_01, Bush_02, Bush_03, Ground_Plant_01, Ground_Plant_02, Vine_Short / Vine_Medium / Vine_Long
    parts    Trunk_*, Branch_*, Root_*, Leaf_Cluster_A/B/C(+_Low), Leaf_Single, Vine_* (reusable components)
    planters Stone_Planter (filled), Stone_Planter_Empty, Planter_Wall_Block, Planter_Corner_Post

Look: thick faceted warm-brown trunks that fork into a few big curved limbs, visible chunky roots, crowns
made of rounded clusters of big folded kite-shaped leaves (lime / medium / yellow-green over a dark-green
core), small hanging vines of leaf pairs, light lavender-grey stone block planters.

Every piece is its own mesh in the asset library, so the lobby places linked duplicates. Units are studs;
each tree's origin is the centre of its trunk at ground level.
"""
import math, random
import bmesh
from mathutils import Vector, Matrix
from common import Part, MATS, mat_plain, mat_noise, coll, ASSETS, _register, TAU

FOLIAGE_ROOT = 'TOWER_OF_PETS_FOLIAGE'
LEAF_OUTER = ('Leaves_Light', 'Leaves_Mid', 'Leaves_Light', 'Leaves_Highlight')


# ---------------------------------------------------------------- materials -
def build_foliage_materials():
    import bpy
    P = mat_plain
    P('Leaves_Light', (0.28, 0.66, 0.02), 0.65)          # bright lime
    P('Leaves_Mid', (0.12, 0.44, 0.03), 0.65)            # medium green
    P('Leaves_Dark', (0.05, 0.25, 0.03), 0.75)           # dark core
    P('Leaves_Highlight', (0.46, 0.76, 0.04), 0.6)       # yellow-green tips
    P('Vine_Green', (0.20, 0.55, 0.06), 0.65)
    P('Trunk_Dark', (0.20, 0.09, 0.03), 0.85)
    # warm brown trunk with soft vertical streaks (no bark scan)
    m = P('Trunk', (0.46, 0.22, 0.08), 0.8)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.4, 1.4, 0.18)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (0.30, 0.13, 0.05, 1)
    ramp.color_ramp.elements[1].position = 0.65; ramp.color_ramp.elements[1].color = (0.52, 0.26, 0.10, 1)
    L = nt.links.new
    L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs['Vector'], nz.inputs['Vector'])
    L(nz.outputs['Fac'], ramp.inputs['Fac']); L(ramp.outputs['Color'], b.inputs['Base Color'])
    mat_noise('Planter_Stone', (0.58, 0.54, 0.58), (0.67, 0.63, 0.67), 0.8, 0.4, 0.15, 2.0)
    P('Planter_Stone_Dark', (0.47, 0.43, 0.47), 0.8)
    mat_noise('Dirt', (0.22, 0.12, 0.06), (0.32, 0.18, 0.09), 0.95, 0.8, 0.2, 3.0)
    mat_noise('Foliage_Rock', (0.45, 0.43, 0.44), (0.60, 0.58, 0.58), 0.85, 0.6, 0.2, 2.0)


# ---------------------------------------------------------------- primitives
def _frame(t):
    ref = Vector((0, 0, 1)) if abs(t.z) < 0.95 else Vector((1, 0, 0))
    u = t.cross(ref).normalized()
    return u, t.cross(u).normalized()


def tube(p, path, radii, mat, sides=7, cap=True, phase=0.0, squash=1.0):
    """faceted lofted limb along a polyline; flat shaded"""
    rings = []
    u_prev = None
    for i, (c, r) in enumerate(zip(path, radii)):
        if i == 0:
            t = path[1] - path[0]
        elif i == len(path) - 1:
            t = path[-1] - path[-2]
        else:
            t = path[i + 1] - path[i - 1]
        t.normalize()
        u, v = _frame(t)
        if u_prev is not None and u.dot(u_prev) < 0:        # keep the twist stable
            u, v = -u, -v
        u_prev = u
        ring = [c + (u * math.cos(phase + TAU * k / sides) * squash + v * math.sin(phase + TAU * k / sides)) * r
                for k in range(sides)]
        rings.append(ring)
    p.loft(rings, mat, cap_bottom=cap, cap_top=cap)


def curve(a, b, bend, n=5):
    """points from a to b bowed by the vector `bend` (quadratic)"""
    a, b, bend = Vector(a), Vector(b), Vector(bend)
    mid = (a + b) / 2 + bend
    return [(1 - t) ** 2 * a + 2 * (1 - t) * t * mid + t ** 2 * b for t in (i / (n - 1) for i in range(n))]


def leaf(p, base, d, nrm, L, W, mat, fold=0.22):
    """chunky folded broad leaf (closed, visible from both sides): 8 verts / 12 tris"""
    base, d = Vector(base), Vector(d).normalized()
    side = d.cross(Vector(nrm))
    if side.length < 1e-4:
        side = d.cross(Vector((0.3, 0.9, 0.1)))
    side.normalize()
    n = side.cross(d).normalized()
    mid = base + d * L * 0.45
    outline = [base, base + d * L * 0.28 + side * W * 0.44, base + d * L * 0.66 + side * W * 0.42, base + d * L,
               base + d * L * 0.66 - side * W * 0.42, base + d * L * 0.28 - side * W * 0.44]
    bm = p.bm
    v = [bm.verts.new(q) for q in outline]
    top, bot = bm.verts.new(mid + n * W * fold), bm.verts.new(mid - n * W * fold * 0.35)
    faces = []
    for i in range(6):
        j = (i + 1) % 6
        faces.append(bm.faces.new((v[i], v[j], top)))
        faces.append(bm.faces.new((v[j], v[i], bot)))
    p._faces(faces, mat)


def leaf_cluster(p, c, R, rnd, n=34, squash=0.82, low=False, droop=0.45, outer=LEAF_OUTER, core='Leaves_Dark'):
    """rounded clump of big faceted leaves over a dark core - the basic crown building block"""
    c = Vector(c)
    vs = p.ico(c, R * 0.8, core, 1, (1, 1, squash), smooth=False)
    for v in vs:
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * R * 0.06
    if low:
        n = 11
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 1.75 * (i + 0.5) / n                      # fibonacci sphere, skip the very bottom
        rr = math.sqrt(max(0.0, 1 - z * z))
        a = golden * i + rnd.uniform(-0.2, 0.2)
        u = Vector((math.cos(a) * rr, math.sin(a) * rr, z * squash)).normalized()
        down = Vector((0, 0, -1)) + u * u.z                   # downhill direction on the clump surface
        if down.length < 0.15:
            down = Vector((math.cos(a * 3.1), math.sin(a * 3.1), 0)) - u * u.dot(Vector((math.cos(a * 3.1), math.sin(a * 3.1), 0)))
        # leaves lie over the clump like shingles, tips slightly lifted and drooping outward
        uh = Vector((u.x, u.y, 0))
        uh = uh.normalized() if uh.length > 0.2 else down.normalized()
        # upper leaves follow the surface, side/lower leaves fan outward instead of hanging straight down
        d = (down.normalized() * (0.5 + 0.5 * max(0.0, u.z)) + uh * (0.9 - 0.4 * max(0.0, u.z)) + u * 0.3
             + Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), rnd.uniform(-0.05, 0.2))))
        L = R * rnd.uniform(0.58, 0.76) * (1.35 if low else 1.0)
        base = c + Vector((u.x, u.y, u.z * squash)) * R * 0.66
        leaf(p, base, d, u, L, L * rnd.uniform(0.78, 0.92), rnd.choice(outer), 0.16)


def vine(p, top, length, rnd, scale=1.0, stem='Vine_Green', mats=('Leaves_Mid', 'Leaves_Light')):
    """hanging vine: thin stem with alternating leaf pairs, slight sway"""
    top = Vector(top)
    n = max(3, int(length / (0.7 * scale)))
    sway = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized() * 0.25 * scale
    pts = [top + Vector((0, 0, -length * i / n)) + sway * math.sin(math.pi * i / n * 1.3) for i in range(n + 1)]
    tube(p, pts, [0.09 * scale] * (n + 1), stem, 4)
    for i in range(1, n + 1):
        q = pts[i]
        s = 1 if i % 2 else -1
        side = Vector((math.cos(i * 1.9), math.sin(i * 1.9), 0)) * s
        Lf = 0.55 * scale * (0.7 + 0.5 * (i / n))
        leaf(p, q, side + Vector((0, 0, -0.55)), Vector((0, 0, 1)).cross(side) + Vector((0, 0, 0.01)),
             Lf, Lf * 0.62, mats[i % 2], 0.18)


def roots(p, base_r, count, rnd, reach=2.4, z=1.2, mat='Trunk'):
    for k in range(count):
        a = TAU * k / count + rnd.uniform(-0.25, 0.25)
        d = Vector((math.cos(a), math.sin(a), 0))
        start = d * base_r * 0.4 + Vector((0, 0, z))
        end = d * (base_r + reach * rnd.uniform(0.8, 1.2)) + Vector((0, 0, -0.35))
        path = curve(start, end, d * reach * 0.1 + Vector((0, 0, z * 0.35)), 4)
        tube(p, path, [base_r * 0.42, base_r * 0.32, base_r * 0.2, base_r * 0.07], mat, 5)


# ---------------------------------------------------------------- trees -----
TREE_SPECS = {
    # H trunk height to fork, trunk radius, limbs (azimuth deg, length, rise), crown cluster radius,
    # extra clusters, vines, roots, top cluster
    'Large':  dict(fork=7.0, r=1.6, limbs=((20, 12.0, 5.5), (145, 11.5, 6.5), (262, 11.0, 6.0)),
                   R=6.4, extra=3, vines=10, roots=6, top=(0, 0, 18.0)),
    'Medium': dict(fork=7.0, r=1.05, limbs=((60, 5.6, 3.6), (230, 5.8, 4.2)),
                   R=4.9, extra=2, vines=5, roots=5, top=(0.6, 0.4, 15.8)),
    'Small':  dict(fork=4.6, r=0.85, limbs=((30, 3.4, 2.8), (200, 3.2, 3.0)),
                   R=3.9, extra=2, vines=2, roots=4, top=(0.8, 0, 10.0)),
    'Tall_Thin': dict(fork=9.0, r=0.8, limbs=((110, 3.6, 2.2),),
                      R=3.6, extra=0, vines=4, roots=4, top=(0.4, -0.3, 19.5)),
}


def build_tree(p, kind, rnd, low=False):
    s = TREE_SPECS[kind]
    sides = 6 if low else 8
    fork = Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), s['fork']))
    # trunk: flared, gently S-curved, faceted
    path = [Vector((0, 0, -0.4)), Vector((0, 0, s['fork'] * 0.22)),
            Vector((fork.x * 0.3 + 0.25, fork.y * 0.3, s['fork'] * 0.55)), fork]
    tube(p, path, [s['r'] * 1.55, s['r'] * 1.08, s['r'] * 0.92, s['r'] * 0.8], 'Trunk', sides, phase=0.3)
    if not low:
        roots(p, s['r'], s['roots'], rnd, reach=s['r'] * 1.9, z=s['r'] * 0.9)
    else:
        roots(p, s['r'], 3, rnd, reach=s['r'] * 1.5, z=s['r'] * 0.8)
    p.ico(fork, s['r'] * 0.95, 'Trunk_Dark', 1, (1, 1, 0.8), smooth=False)     # dark crotch between limbs
    clusters = []
    for az, length, rise in s['limbs']:
        a = math.radians(az + rnd.uniform(-10, 10))
        d = Vector((math.cos(a), math.sin(a), 0))
        end = fork + d * length + Vector((0, 0, rise))
        tube(p, curve(fork - Vector((0, 0, 0.6)), end, Vector((0, 0, rise * 0.45)) - d * length * 0.12, 5),
             [s['r'] * 0.78, s['r'] * 0.62, s['r'] * 0.48, s['r'] * 0.36, s['r'] * 0.26], 'Trunk', sides - 1)
        clusters.append((end + Vector((0, 0, s['R'] * 0.35)), s['R'] * rnd.uniform(0.92, 1.08)))
        # small side branch to a secondary clump
        if kind == 'Large':
            mid = fork + (end - fork) * 0.55
            sd = Vector((math.cos(a + 1.2), math.sin(a + 1.2), 0))
            e2 = mid + sd * length * 0.35 + Vector((0, 0, rise * 0.9))
            tube(p, [mid, (mid + e2) / 2 + Vector((0, 0, 0.6)), e2], [s['r'] * 0.32, s['r'] * 0.24, s['r'] * 0.16],
                 'Trunk', 5)
            clusters.append((e2 + Vector((0, 0, s['R'] * 0.25)), s['R'] * 0.78))
    top = Vector(s['top'])
    tube(p, curve(fork, top - Vector((0, 0, s['R'] * 0.4)), Vector((0.5, 0, 0)), 4),
         [s['r'] * 0.7, s['r'] * 0.5, s['r'] * 0.35, s['r'] * 0.22], 'Trunk', sides - 1)
    clusters.append((top, s['R'] * (1.1 if kind != 'Tall_Thin' else 1.15)))
    # extra clumps fill the crown between limbs (umbrella silhouette)
    for k in range(s['extra']):
        a = TAU * (k + 0.5) / max(1, s['extra']) + rnd.uniform(-0.3, 0.3)
        rr = s['R'] * rnd.uniform(1.0, 1.4)
        clusters.append((top + Vector((math.cos(a) * rr, math.sin(a) * rr, -s['R'] * rnd.uniform(0.3, 0.7))),
                         s['R'] * rnd.uniform(0.8, 0.95)))
    if kind == 'Tall_Thin':                 # second, lower pom like the reference
        clusters.append((fork + Vector((-0.3, 0.2, s['R'] * 0.1)) + Vector((math.cos(1.9), math.sin(1.9), 0)) * 3.6,
                         s['R'] * 0.9))
    for c, R in clusters:
        leaf_cluster(p, c, R, rnd, 34, low=low)
    # hanging vines from under the crown
    if not low:
        for k in range(s['vines']):
            c, R = clusters[k % len(clusters)]
            a = rnd.uniform(0, TAU)
            t = c + Vector((math.cos(a) * R * 0.55, math.sin(a) * R * 0.55, -R * 0.45))
            vine(p, t, rnd.uniform(2.5, 6.5) * (1.0 if kind == 'Large' else 0.75), rnd)
    return clusters


# ---------------------------------------------------------------- bushes ----
def bush_01(p, rnd):                 # round leafy dome
    leaf_cluster(p, (0, 0, 1.3), 2.1, rnd, 30, squash=0.78)


def bush_02(p, rnd):                 # fluffier bush from three clumps
    for x, y, z, R in ((-0.9, 0.2, 1.0, 1.5), (0.9, -0.1, 1.0, 1.45), (0.0, 0.3, 1.9, 1.5)):
        leaf_cluster(p, (x, y, z), R, rnd, 22, squash=0.85)


def broad_plant(p, rnd, n, L, W, rise, center_h=0.3, mats=('Leaves_Mid', 'Leaves_Light', 'Leaves_Highlight')):
    """rosette of big pointed leaves on short stems (tropical ground plants / bush 03)"""
    p.ico((0, 0, center_h), 0.35, 'Leaves_Dark', 1, (1, 1, 0.8), smooth=False)
    for k in range(n):
        a = TAU * k / n + rnd.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), 0))
        el = rise * rnd.uniform(0.8, 1.2)
        base = d * 0.2 + Vector((0, 0, center_h))
        mid = base + (d * 0.55 + Vector((0, 0, el))).normalized() * L * 0.45
        tube(p, [base, mid], [0.08, 0.05], 'Vine_Green', 4)
        # leaf blade: rises then droops (two segments)
        leaf(p, mid, d * 0.7 + Vector((0, 0, el * 0.6)), Vector((0, 0, 1)), L * 0.55, W, mats[k % len(mats)])
        tip_base = mid + (d * 0.7 + Vector((0, 0, el * 0.6))).normalized() * L * 0.4
        leaf(p, tip_base, d + Vector((0, 0, -0.35)), Vector((0, 0, 1)), L * 0.5, W * 0.8, mats[(k + 1) % len(mats)])


def bush_03(p, rnd):                 # big broad-leaf plant, leaves pointing up and out
    broad_plant(p, rnd, 9, 3.4, 1.4, 1.3, 0.4)


def ground_plant_01(p, rnd):         # long pointed leaf rosette
    broad_plant(p, rnd, 8, 2.4, 0.75, 0.9, 0.2, ('Leaves_Light', 'Leaves_Highlight', 'Leaves_Mid'))


def ground_plant_02(p, rnd):         # low wide-leaf plant
    broad_plant(p, rnd, 6, 2.0, 1.05, 0.45, 0.15, ('Leaves_Mid', 'Leaves_Light'))


# ---------------------------------------------------------------- planter ---
def stone_block(p, c, s, mat, bev=0.12):
    vs = p.box(c, s, mat)
    edges = list({e for v in vs for e in v.link_edges})
    bmesh.ops.bevel(p.bm, geom=edges + vs, offset=bev, segments=1, affect='EDGES')   # chamfer faces inherit


def planter_walls(p, w, d, h=2.0, t=1.1, rnd=None):
    """running-bond stone block walls with taller capped corner posts; inner size w x d"""
    rnd = rnd or random.Random(0)
    courses = 2
    ch = h / courses
    for side in range(4):
        horiz = side % 2 == 0
        length = w if horiz else d
        off = (d / 2 + t / 2) if horiz else (w / 2 + t / 2)
        sign = -1 if side < 2 else 1
        for row in range(courses):
            x = -length / 2 + (0 if row % 2 == 0 else -1.0)
            while x < length / 2 - 0.05:
                bl = min(rnd.uniform(1.8, 2.6), length / 2 - x)
                x0, x1 = max(x, -length / 2), x + bl
                if x1 - x0 > 0.2:
                    cx = (x0 + x1) / 2
                    cz = row * ch + ch / 2
                    c = (cx, sign * off, cz) if horiz else (sign * off, cx, cz)
                    s = (x1 - x0 - 0.08, t, ch - 0.08) if horiz else (t, x1 - x0 - 0.08, ch - 0.08)
                    stone_block(p, c, s, rnd.choice(('Planter_Stone', 'Planter_Stone', 'Planter_Stone_Dark')), 0.08)
                x = x1
        # cap course
        c = (0, sign * off, h + 0.2) if horiz else (sign * off, 0, h + 0.2)
        s = (length, t + 0.25, 0.4) if horiz else (t + 0.25, length, 0.4)
        stone_block(p, c, s, 'Planter_Stone', 0.08)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx * (w / 2 + t / 2), sy * (d / 2 + t / 2))
            stone_block(p, (*c, (h + 0.9) / 2), (t + 0.5, t + 0.5, h + 0.9), 'Planter_Stone', 0.1)
            stone_block(p, (*c, h + 1.1), (t + 0.8, t + 0.8, 0.45), 'Planter_Stone', 0.08)


def stone_planter(p, rnd, w=10.0, d=6.0, h=2.0, fill=True, plants=True):
    planter_walls(p, w, d, h, 1.1, rnd)
    p.box((0, 0, h * 0.45), (w, d, h * 0.9), 'Dirt')
    if not fill:
        return
    p.box((0, 0, h * 0.9 + 0.05), (w - 0.4, d - 0.4, 0.1), 'Grass')
    for k in range(3):                                            # rocks
        x, y = rnd.uniform(-w / 2 + 1, w / 2 - 1), rnd.uniform(-d / 2 + 0.8, d / 2 - 0.8)
        if not plants and abs(x) < 3 and abs(y) < 3:
            x += 4
        vs = p.ico((x, y, h * 0.95), rnd.uniform(0.5, 0.9), 'Foliage_Rock', 1, (1.2, 1, 0.75), smooth=False)
        for v in vs:
            v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.12
    # small bushes / plants inline so the filled planter is one mesh
    for k in range(int(w / 2.2) if plants else 0):
        x = -w / 2 + 1.2 + k * (w - 2.4) / max(1, int(w / 2.2) - 1)
        y = rnd.uniform(-d / 2 + 1.2, d / 2 - 1.2)
        leaf_cluster(p, (x, y, h + 0.6), rnd.uniform(1.0, 1.4), rnd, 12, squash=0.8)


# ---------------------------------------------------------------- library ---
def _lib(name, sub, builder, *a, **kw):
    p = Part('ASSET_' + name, sub)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def build_foliage_assets(parent):
    """create every foliage asset under `parent` (TOWER_OF_PETS_FOLIAGE hierarchy)"""
    coll(FOLIAGE_ROOT, parent)
    for c in ('TREES', 'FOLIAGE', 'TREE_PARTS', 'PLANTERS'):
        coll(c, FOLIAGE_ROOT)
    for c in ('Trunks', 'Branches', 'Leaves', 'Roots', 'Vines'):
        coll(c, 'TREE_PARTS')
    for c in ('Large_Lobby_Tree', 'Medium_Tree', 'Small_Tree', 'Tall_Thin_Tree'):
        coll(c, 'TREES')
    for c in ('Bush_01', 'Bush_02', 'Bush_03', 'Ground_Plant_01', 'Ground_Plant_02', 'Vine'):
        coll(c, 'FOLIAGE')
    coll('Stone_Planter', 'PLANTERS')

    R = random.Random
    # trees (high + low LOD) ---------------------------------------------------------------------
    for kind, cn in (('Large', 'Large_Lobby_Tree'), ('Medium', 'Medium_Tree'), ('Small', 'Small_Tree'),
                     ('Tall_Thin', 'Tall_Thin_Tree')):
        hi = f'Tree_{kind}_High' if kind in ('Large', 'Medium') else f'Tree_{kind}'
        _lib(hi, cn, lambda p, k=kind: build_tree(p, k, R(100 + len(k)), False))
        _lib(f'Tree_{kind}_Low', cn, lambda p, k=kind: build_tree(p, k, R(100 + len(k)), True))
    # reusable parts -----------------------------------------------------------------------------
    def trunk(p, r, h, sides):
        tube(p, [Vector((0, 0, -0.4)), Vector((0, 0, h * 0.25)), Vector((0.3, 0, h * 0.6)), Vector((0, 0, h))],
             [r * 1.55, r * 1.08, r * 0.92, r * 0.8], 'Trunk', sides, phase=0.3)
    _lib('Trunk_Thick', 'Trunks', trunk, 1.55, 8.5, 8)
    _lib('Trunk_Thin', 'Trunks', trunk, 0.8, 9.0, 7)
    _lib('Branch_Curved', 'Branches', lambda p: tube(p, curve((0, 0, 0), (9, 0, 6), (-1, 0, 2.7), 5),
                                                     [1.2, 0.95, 0.75, 0.55, 0.4], 'Trunk', 7))
    _lib('Branch_Small', 'Branches', lambda p: tube(p, curve((0, 0, 0), (3.5, 0, 3), (0, 0, 0.8), 4),
                                                    [0.5, 0.38, 0.28, 0.18], 'Trunk', 5))
    _lib('Root_Set', 'Roots', lambda p: roots(p, 1.55, 6, R(5), 2.9, 1.4))
    _lib('Root_Single', 'Roots', lambda p: tube(p, curve((0, 0, 1.4), (3.5, 0, -0.35), (0.3, 0, 0.5), 4),
                                                [0.65, 0.5, 0.3, 0.1], 'Trunk', 5))
    for k, n in enumerate((30, 26, 22)):
        _lib(f'Leaf_Cluster_{"ABC"[k]}', 'Leaves', lambda p, k=k, n=n: leaf_cluster(p, (0, 0, 0), 4.5, R(30 + k), n,
                                                                                     squash=(0.82, 0.9, 0.75)[k]))
    _lib('Leaf_Cluster_Low', 'Leaves', lambda p: leaf_cluster(p, (0, 0, 0), 4.5, R(40), low=True))
    _lib('Leaf_Single', 'Leaves', lambda p: leaf(p, (0, 0, 0), (1, 0, 0.2), (0, 0, 1), 2.0, 1.25, 'Leaves_Light'))
    for name, L, seed in (('Vine_Short', 2.5, 51), ('Vine_Medium', 4.5, 52), ('Vine_Long', 7.0, 53)):
        _lib(name, 'Vines', lambda p, L=L, seed=seed: vine(p, (0, 0, 0), L, R(seed)))
    # foliage ------------------------------------------------------------------------------------
    _lib('Bush_01', 'Bush_01', bush_01, R(61))
    _lib('Bush_02', 'Bush_02', bush_02, R(62))
    _lib('Bush_03', 'Bush_03', bush_03, R(63))
    _lib('Ground_Plant_01', 'Ground_Plant_01', ground_plant_01, R(64))
    _lib('Ground_Plant_02', 'Ground_Plant_02', ground_plant_02, R(65))
    _lib('Vine', 'Vine', lambda p: vine(p, (0, 0, 0), 5.0, R(66)))
    # planters -----------------------------------------------------------------------------------
    _lib('Stone_Planter', 'Stone_Planter', stone_planter, R(70), 10.0, 6.0, 2.0, True)
    _lib('Stone_Planter_Large', 'Stone_Planter', stone_planter, R(71), 14.0, 14.0, 2.0, True, False)
    _lib('Stone_Planter_Empty', 'Stone_Planter', stone_planter, R(72), 10.0, 6.0, 2.0, False)
    _lib('Planter_Wall_Block', 'Stone_Planter', lambda p: stone_block(p, (0, 0, 0.5), (2.2, 1.1, 1.0),
                                                                      'Planter_Stone', 0.08))
    _lib('Planter_Corner_Post', 'Stone_Planter', lambda p: (stone_block(p, (0, 0, 1.45), (1.6, 1.6, 2.9),
                                                                         'Planter_Stone', 0.1),
                                                             stone_block(p, (0, 0, 3.1), (1.9, 1.9, 0.45),
                                                                         'Planter_Stone', 0.08)))


def tree_in_planter(name, collection, loc, rot, kind='Tree_Large_High', planter='Stone_Planter_Large',
                    seed=0, parent=None, scale=1.0):
    """the reference's lobby composition: tree in a square stone planter with bushes, plants and rocks"""
    from common import inst
    rnd = random.Random(seed)
    c, s, r = Vector(loc), scale, Matrix.Rotation(rot, 3, 'Z')
    out = [inst(planter, f'{name}_Planter', collection, c, rot, s, parent),
           inst(kind, f'{name}_Tree', collection, c + Vector((0, 0, 2.0 * s)), rot + rnd.uniform(0, TAU), s, parent)]
    for k, (a, nm) in enumerate(((0.4, 'Bush_01'), (2.1, 'Ground_Plant_01'), (3.4, 'Bush_02'), (4.6, 'Ground_Plant_02'),
                                 (5.6, 'Bush_03'))):
        off = r @ Vector((math.cos(a) * 4.6, math.sin(a) * 4.6, 2.0)) * s
        out.append(inst(nm, f'{name}_{nm}_{k}', collection, c + off, rnd.uniform(0, TAU), s * rnd.uniform(0.7, 0.9),
                        parent))
    return out
