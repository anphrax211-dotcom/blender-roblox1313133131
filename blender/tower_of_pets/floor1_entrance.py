"""TOWER OF PETS - FLOOR 1 ENTRANCE (The Verdant Kingdom): the portal, plaza and first stretch of forest path.

Built where the map puts the Floor Entrance, on the south-west of the Verdant mainland (one landmass with the meadows
and forest - no separate island). The terrain itself is shaped in floor1.py (flat plaza pad, portal pad cut into a
new rocky hill, a spring pool + brook that falls off the cliff edge, small knolls, placeholder cave / hidden paths);
this module builds the architecture and dressing on top, in the hub's language:

  * the portal: a dais and a wide staircase (stepped cheek walls, newel lanterns) up to a monumental arch of real
    masonry (castle.py helpers: chamfered block courses, a voussoir ring with keystone, banded pillars with gold trim,
    a stone pediment with the gold-framed Verdant leaf medallion, wing walls), green Verdant leaf banners, vines and
    moss, and a swirling cyan portal (bright core, darker cyan edges, spiral arms, sparkles) + an invisible trigger;
  * the plaza: flagstone rings round the Verdant emblem (green disc, gold ring, gold leaf), a low stone border open
    toward the stairs, the forest road and the hidden brook path;
  * dressing with existing hub assets (linked duplicates, recorded for the Roblox scatter): hub trees framing the
    portal and lining the road, Castle_Lantern / Lantern_Post / Lantern_Wood lights guiding to the portal, bushes,
    flowers, rocks, stone planters, wooden fences, Verdant banner poles, the hub rope bridge over the brook.
Local frame of the portal: x across, z up, the front of the portal wall at y = 0 facing the plaza (-y).
"""
import math, random
from mathutils import Vector, Matrix
from common import Part, mat_plain, coll, round_arch, ASSETS, TAU
import castle
from castle import bevel_box, masonry, voussoirs, pillar, inside, rect_minus_arch, trim_run
import floor1 as F

C = 'F1_ENTRANCE'
SPAWN_PX, TOWARD_PX = (215, 860), (290, 815)     # plaza centre (the spawn) and the first road waypoint
PLAZA_R = 50.0                                   # paved radius (studs)
STAIR_W, STEPS, RISE, TREAD = 56.0, 10, 0.8, 2.6
DAIS_D = 14.0                                    # landing depth in front of the portal
OPEN_W, OPEN_HS = 34.0, 30.0                     # portal opening: width, straight jamb height (apex = HS + W / 2)
STONES = castle.STONES


def frame():
    """plaza centre, unit direction plaza -> road (world), ground height in studs"""
    sx, sy = F.px(*SPAWN_PX)
    tx, ty = F.px(*TOWARD_PX)
    d = Vector((tx - sx, ty - sy, 0)).normalized()
    return Vector((sx, sy, 0)), d


def portal_dist():
    return PLAZA_R + 6 + STEPS * TREAD + DAIS_D                 # plaza centre -> front face of the portal wall


def portal_px(extra=0.0):
    """sheet-pixel position on the plaza -> portal axis, `extra` studs beyond the portal wall"""
    c, d = frame()
    p = c - d * (portal_dist() + extra)
    return p.x / (F.MAP_SCALE * F.WORLD) + F.MAP_CX, F.MAP_CY - p.y / (F.MAP_SCALE * F.WORLD)


def build_entrance_materials():
    P = mat_plain
    P('Banner_Green', (0.05, 0.38, 0.10), 0.6)
    P('Verdant_Emblem', (0.08, 0.50, 0.16), 0.5)
    P('F1_Portal_Edge', (0.00, 0.10, 0.40), 0.3, emit=0.8, emit_rgb=(0.0, 0.18, 0.65))
    P('F1_Portal_Mid', (0.00, 0.40, 0.85), 0.3, emit=1.1, emit_rgb=(0.0, 0.45, 1.0))
    P('F1_Portal_Inner', (0.10, 0.72, 1.0), 0.3, emit=1.3, emit_rgb=(0.1, 0.78, 1.0))
    P('F1_Portal_Core', (0.80, 0.97, 1.0), 0.2, emit=2.2, emit_rgb=(0.75, 0.97, 1.0))
    P('F1_Portal_Swirl', (0.55, 0.95, 1.0), 0.2, emit=1.8, emit_rgb=(0.55, 0.95, 1.0))
    P('F1_Rune_Glow', (0.2, 0.9, 1.0), 0.3, emit=2.5)
    P('Fire_Core', (1.0, 0.85, 0.35), 0.4, emit=2.6)


# ---------------------------------------------------------------- shapes ----
def leaf_pts(L, W, n=10):
    """pointed leaf outline (local x across, y along), tip at +L/2"""
    right = [(W / 2 * math.sin(math.pi * t) * (1 - 0.25 * t), -L / 2 + L * t) for t in (k / n for k in range(n + 1))]
    left = [(-x, y) for x, y in reversed(right[1:-1])]
    return right + left


FLIP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))       # prism in local XZ, extruded along y


def leaf_emblem(p, M, size, depth, mat='Gold', vein='Castle_Trim'):
    """gold leaf with a vein, prism in M's XZ plane (front at y = 0, extruded toward +y)"""
    p.prism(leaf_pts(size, size * 0.55), -depth, 0.0, mat, M @ Matrix.Rotation(-0.35, 4, 'Y') @ FLIP)
    p.prism([(-size * 0.03, -size * 0.45), (size * 0.03, -size * 0.45), (size * 0.015, size * 0.42),
             (-size * 0.015, size * 0.42)], -depth - 0.12, -depth + 0.05, vein,
            M @ Matrix.Rotation(-0.35, 4, 'Y') @ FLIP)


def verdant_banner(p, M, w=9.0, length=30.0, rod=True):
    """green Verdant pennant with gold border and a gold leaf, hanging from local origin downward (front y = 0)"""
    o = [(-w / 2, 0), (w / 2, 0), (w / 2, -length), (0, -length - w * 0.6), (-w / 2, -length)]
    Mb = M @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    p.prism(o, -0.35, 0.0, 'Banner_Green', Mb)
    edge = [(-w / 2, 0), (-w / 2, -length), (0, -length - w * 0.6), (w / 2, -length), (w / 2, 0)]
    inner = [(-w / 2 + 0.7, 0), (-w / 2 + 0.7, -length + 0.3), (0, -length - w * 0.6 + 1.0),
             (w / 2 - 0.7, -length + 0.3), (w / 2 - 0.7, 0)]
    for (a0, a1), (b0, b1) in zip(zip(edge, edge[1:]), zip(inner, inner[1:])):
        q = [a0, a1, b1, b0]
        p.hexa([Mb @ Vector((x, z, 0.0)) for x, z in q] + [Mb @ Vector((x, z, 0.25)) for x, z in q], 'Gold')
    leaf = leaf_pts(w * 0.62, w * 0.36)
    p.prism([(x, y - length * 0.58) for x, y in leaf], 0.0, 0.3, 'Gold', Mb)
    if rod:
        p.cyl(M @ Vector((0, -0.6, 0.6)), 0.4, w + 2.0, 'Gold', 8, axis='X', rot=M.to_3x3().normalized())
        for s in (-1, 1):
            p.ico(M @ Vector((s * (w / 2 + 1.0), -0.6, 0.6)), 0.6, 'Gold', 1)


def banner_pole(p, rnd=None):
    """wooden pole with a cross bar carrying a Verdant banner - origin at the ground"""
    p.box((0, 0, 0.6), (2.6, 2.6, 1.2), 'Castle_Stone_Light')
    p.cyl((0, 0, 9.5), 0.45, 18.0, 'Wood_Dark', 8)
    p.box((0, -0.2, 17.0), (10.5, 0.6, 0.6), 'Wood_Dark')
    p.ico((0, 0, 18.7), 0.7, 'Gold', 1)
    verdant_banner(p, Matrix.Translation((0, -0.6, 16.4)), 8.0, 11.0, rod=False)


def build_entrance_assets():
    build_entrance_materials()
    from floor1_detail import _lib
    _lib('Verdant_Banner_Pole', banner_pole)


# ---------------------------------------------------------------- the portal
def portal_matrix(T):
    c, d = frame()
    base = c - d * portal_dist()
    z = T.sample(c.x, c.y)[0]                                   # plaza level (the pads keep it flat)
    Y = -d                                                      # local +y: into the portal / hill
    X = Vector((-d.y, d.x, 0))                                  # local x (right, seen from the plaza)
    R = Matrix((X, Y, Vector((0, 0, 1)))).transposed().to_4x4()
    return Matrix.Translation((base.x, base.y, z)) @ R, z


def build_stairs(M, rnd):
    p = Part('Entrance_Walk_Stairs', C)
    H = STEPS * RISE
    y_top = -DAIS_D
    # dais: masonry faces + flagstone top
    for x0, x1 in ((-44.0, -STAIR_W / 2), (STAIR_W / 2, 44.0)):
        masonry(p, M @ Matrix.Translation((0, y_top, 0)), x0, x1, 0.0, H, rnd, 1.6, (2.4, 4.0), 1.2)
    for sx in (-1, 1):                                          # dais side walls
        Ms = M @ Matrix.Translation((sx * 44.0, -DAIS_D, 0)) @ Matrix.Rotation(-sx * math.pi / 2, 4, 'Z')
        masonry(p, Ms, -DAIS_D / 2 if sx > 0 else -DAIS_D / 2, DAIS_D / 2, 0.0, H, rnd, 1.6, (2.4, 4.0), 1.2)
    bevel_box(p, M, (0, -DAIS_D / 2, H / 2 - 0.4), (88.0, DAIS_D, H - 0.8), 'Castle_Stone_Dark', 0.0)
    for i in range(11):                                         # landing flagstones
        for j in range(3):
            w = 88.0 / 11
            bevel_box(p, M, (-44 + w * (i + 0.5), -DAIS_D + DAIS_D / 3 * (j + 0.5), H - 0.3),
                      (w - 0.2, DAIS_D / 3 - 0.2, 0.6), rnd.choice(('Castle_Trim', 'Castle_Stone_Light')), 0.12)
    bevel_box(p, M, (0, -DAIS_D - 0.3, H - 0.2), (STAIR_W + 1.0, 0.9, 0.5), 'Gold', 0.05)
    # the staircase: one tread per step, slightly varied stones
    for k in range(STEPS):
        y = y_top - (k + 0.5) * TREAD
        top = H - k * RISE
        for i in range(7):
            w = STAIR_W / 7
            bevel_box(p, M, (-STAIR_W / 2 + w * (i + 0.5), y, top / 2), (w - 0.15, TREAD - 0.12, top),
                      'Castle_Trim' if (i + k) % 3 else 'Castle_Stone_Light', 0.15)
    # stepped cheek walls with newel posts
    for sx in (-1, 1):
        x = sx * (STAIR_W / 2 + 2.2)
        for k in range(STEPS):
            y = y_top - (k + 0.5) * TREAD
            hh = H - k * RISE + 2.6
            bevel_box(p, M, (x, y, hh / 2), (4.4, TREAD + 0.05, hh), rnd.choice(STONES), 0.2)
        for y, h in ((y_top - STEPS * TREAD - 1.0, 4.0), (y_top - 0.5, H + 4.0)):
            bevel_box(p, M, (x, y, h / 2), (5.2, 5.2, h), 'Castle_Stone_Light', 0.25)
            bevel_box(p, M, (x, y, h + 0.4), (6.0, 6.0, 0.8), 'Castle_Trim', 0.2)
    p.finish()
    return H


def build_portal(T):
    rnd = random.Random(77)
    M, z = portal_matrix(T)
    H = build_stairs(M, rnd)
    Mz = M @ Matrix.Translation((0, 0, H))                      # portal stands on the dais
    arch_in = round_arch(OPEN_W, OPEN_HS, 14)
    arch_out = round_arch(OPEN_W + 12, OPEN_HS, 14)
    top = OPEN_HS + OPEN_W / 2 + 11                              # wall top
    # wall body round the opening: core + masonry face, with the opening cut out
    w = Part('Entrance_Portal_Arch', C)
    rect_minus_arch(w, Mz, -27, 27, 0, top, arch_out, 0.6, 9.0, 'Castle_Stone_Dark')
    closed_out = arch_out + [arch_out[0]]
    masonry(w, Mz, -27, 27, 0, top, rnd, 3.0, (4.0, 6.5), 1.4,
            skip=lambda x, zz, bw, bh: inside(closed_out, x, zz) or abs(x) < (OPEN_W + 12) / 2 and zz < OPEN_HS,
            backing=False)
    voussoirs(w, Mz, arch_out, arch_in, -1.6, 6.0, rnd, stone=4.4)
    gold_out = round_arch(OPEN_W + 1.6, OPEN_HS, 14)
    voussoirs(w, Mz, gold_out, arch_in, -1.8, -1.0, rnd, stone=6.0, mat='Gold', keystone=False, backing=False)
    trim_run(w, Mz, -28, 28, top - 1.6, rnd, 1.8, 1.2, 2)
    # pediment with the Verdant medallion
    w.prism([(-26, 0), (26, 0), (0, 15)], -0.8, 5.0, 'Castle_Stone_Light', Mz @ Matrix.Translation((0, 0, top)) @ FLIP)
    for s in (-1, 1):                                           # gold edging on the pediment slopes
        a, b = Vector((s * 26, -1.0, top)), Vector((0, -1.0, top + 15))
        w.beam(Mz @ a, Mz @ b, 1.2, 1.0, 'Gold')
    zc = top + 6.5
    w.cyl(Mz @ Vector((0, -1.2, zc)), 6.2, 1.2, 'Verdant_Emblem', 24, axis='Y', rot=Mz.to_3x3().normalized())
    w.torus(Mz @ Vector((0, -1.6, zc)), 6.5, 0.6, 'Gold', 32, 6,
            rot=Mz.to_3x3().normalized() @ Matrix.Rotation(math.pi / 2, 3, 'X'))
    leaf_emblem(w, Mz @ Matrix.Translation((0, -1.9, zc)), 8.0, 0.5)
    w.ico(Mz @ Vector((0, -0.5, top + 15.5)), 1.4, 'Gold', 1)
    # glowing runes on the arch ring
    for k in range(6):
        a = math.pi * (k + 1) / 7
        r = (OPEN_W + 6) / 2
        c = Vector((r * math.cos(a), -1.75, OPEN_HS + r * math.sin(a)))
        w.box(Mz @ c, (0.9, 0.2, 1.6), 'F1_Rune_Glow', Mz.to_3x3().normalized() @ Matrix.Rotation(a - math.pi / 2, 3, 'Y'))
    # layered outer ring: a second, proud course of pale voussoirs with its own cyan runes
    arch_out2 = round_arch(OPEN_W + 19, OPEN_HS, 16)
    voussoirs(w, Mz, arch_out2, arch_out, -3.6, -1.2, rnd, stone=5.2, mat='Castle_Stone_Light', backing=False)
    for k in range(11):
        a = math.pi * (k + 1) / 12
        r = (OPEN_W + 15.5) / 2
        c = Vector((r * math.cos(a), -3.75, OPEN_HS + r * math.sin(a)))
        w.box(Mz @ c, (0.8, 0.2, 1.4), 'F1_Rune_Glow', Mz.to_3x3().normalized() @ Matrix.Rotation(a - math.pi / 2, 3, 'Y'))
    for s in (-1, 1):                                           # rune columns down the jambs
        for k in range(5):
            w.box(Mz @ Vector((s * (OPEN_W + 15.5) / 2, -3.75, 4.0 + k * 5.0)), (0.8, 0.2, 1.4 + (k % 2) * 0.8),
                  'F1_Rune_Glow', Mz.to_3x3().normalized())
    w.finish()
    # pillars, wing walls, banners
    pl = Part('Entrance_Portal_Pillars', C)
    for s in (-1, 1):
        pillar(pl, Mz @ Matrix.Translation((s * 32.5, 0.5, 0)), 9.0, 0, top + 10, rnd, cap='ball')
        Mw = Mz @ Matrix.Translation((0, 1.0, 0))
        x0, x1 = (37.0, 46.0) if s > 0 else (-46.0, -37.0)
        masonry(pl, Mw, x0, x1, 0, 16.0, rnd, 3.0, (3.6, 5.2), 1.4)
        bevel_box(pl, Mw, ((x0 + x1) / 2, 0.6, 16.6), (x1 - x0 + 1.2, 3.2, 1.2), 'Castle_Trim', 0.2)
        masonry(pl, Mw, x0 + (3 if s > 0 else 0), x1 - (0 if s > 0 else 3), 16.0, 22.0, rnd, 3.0, (3.0, 4.6), 1.4)
        verdant_banner(pl, Mz @ Matrix.Translation((s * 32.5, -5.6, top - 2)), 8.0, 24.0)
    pl.finish()
    # vines and moss over the stone
    from foliage import vine
    v = Part('Entrance_Portal_Vines', C)
    for x in (-30, -24, -17, -9, 9, 17, 24, 30, -40, 41):
        zt = top + 4 if abs(x) < 28 else (22 if abs(x) > 36 else top + 8)
        vine(v, Mz @ Vector((x + rnd.uniform(-1, 1), -2.0, zt)), rnd.uniform(9, 20), rnd, 1.5)
    for k in range(26):
        x = rnd.uniform(-45, 45); zz = rnd.uniform(1, top)
        if abs(x) < OPEN_W / 2 + 6 and zz < OPEN_HS + OPEN_W / 2 + 6:
            continue
        v.ico(Mz @ Vector((x, -1.6, zz)), rnd.uniform(1.0, 2.2), rnd.choice(('Moss', 'Island_Grass')), 1,
              (1.4, 0.45, 0.8), smooth=False)
    v.finish()
    # the portal: dark cyan edges -> bright swirling core
    e = Part('Entrance_Portal_Energy', C)
    shell = [(x, zz) for x, zz in arch_in[1:-1]] + [(OPEN_W / 2, 0.0), (-OPEN_W / 2, 0.0)]
    e.prism(shell, 3.0, 3.4, 'F1_Portal_Edge', Mz @ FLIP)
    cz = OPEN_HS * 0.78
    for f, y, mat in ((0.84, 2.7, 'F1_Portal_Mid'), (0.55, 2.4, 'F1_Portal_Inner')):
        e.prism([(x * f, cz + (zz - cz) * f) for x, zz in shell], y, y + 0.25, mat, Mz @ FLIP)
    e.cyl(Mz @ Vector((0, 2.0, cz)), 3.2, 0.25, 'F1_Portal_Core', 24, axis='Y', rot=Mz.to_3x3().normalized())
    for arm in range(6):                                        # spiral arms
        a0 = TAU * arm / 6
        prev = None
        for i in range(24):
            t = i / 23
            a = a0 + t * 2.4
            r = 2.0 + t * (OPEN_W / 2 - 3.0)
            q = Vector((r * math.cos(a), 1.9, cz + r * math.sin(a) * 1.25))
            if prev is not None:
                e.beam(Mz @ prev, Mz @ q, 1.4 * (1 - t * 0.5), 0.15, 'F1_Portal_Swirl' if arm % 2 else 'F1_Portal_Core')
            prev = q
    e.torus(Mz @ Vector((0, 1.6, cz)), OPEN_W / 2 - 2.2, 0.35, 'F1_Portal_Swirl', 40, 4,
            rot=Mz.to_3x3().normalized() @ Matrix.Rotation(math.pi / 2, 3, 'X') @ Matrix.Diagonal((1.0, 1.25, 1.0)))
    for k in range(40):                                         # particles orbiting the opening
        a = rnd.uniform(0, TAU); r = rnd.uniform(OPEN_W / 2 - 4, OPEN_W / 2 + 1)
        zz = cz + r * math.sin(a) * 1.2
        if zz < 0.8:
            continue
        e.ico(Mz @ Vector((r * math.cos(a), rnd.uniform(-2.5, 1.0), zz)), rnd.uniform(0.2, 0.45), 'F1_Rune_Glow', 1)
    for k in range(70):                                         # sparkles drifting out of the portal
        x = rnd.uniform(-OPEN_W / 2, OPEN_W / 2); zz = rnd.uniform(1, OPEN_HS + 12); y = rnd.uniform(-14, 1.5)
        e.ico(Mz @ Vector((x, y, zz)), rnd.uniform(0.15, 0.4), rnd.choice(('F1_Portal_Core', 'F1_Portal_Swirl')), 1)
    e.finish()
    t = Part('Floor1_Portal_TeleportTrigger', C)                        # invisible touch volume (return to the hub)
    t.box(Mz @ Vector((0, 4.5, OPEN_HS * 0.6)), (OPEN_W - 2, 3.0, OPEN_HS * 1.2), 'Magic_Glow',
          Mz.to_3x3().normalized())
    tr = t.finish()
    tr.hide_render = True
    tr.display_type = 'WIRE'
    # stone fire braziers at the front corners of the dais + warm / cyan lamps
    import bpy
    b = Part('Entrance_Portal_Braziers', C)
    lights = coll('F1_VILLAGE_LIGHTS', F.ROOT).name
    for s in (-1, 1):
        q = Mz @ Vector((s * 40.0, -DAIS_D + 3.5, 0))
        Mb = Matrix.Translation(q)
        bevel_box(b, Mb, (0, 0, 1.2), (4.4, 4.4, 2.4), 'Castle_Stone_Light', 0.25)
        b.cyl(q + Vector((0, 0, 4.4)), 1.0, 4.0, 'Castle_Stone', 8)
        b.cyl(q + Vector((0, 0, 7.0)), 2.6, 1.4, 'Iron_Band', 10, r2=1.6)
        b.cone(q + Vector((0, 0, 7.6)), 2.0, 3.4, 'Forge_Glow', 7)
        b.cone(q + Vector((0, 0, 8.4)), 1.1, 3.6, 'Fire_Core', 6)
        L = bpy.data.lights.new(f'Portal_Brazier_Light_{s + 1}', 'POINT')
        L.color = (1.0, 0.62, 0.28); L.energy = 2600; L.shadow_soft_size = 1.0
        o = bpy.data.objects.new(L.name, L); o.location = q + Vector((0, 0, 11.0))
        bpy.data.collections[lights].objects.link(o)
    b.finish()
    L = bpy.data.lights.new('Portal_Glow_Light', 'POINT')
    L.color = (0.35, 0.85, 1.0); L.energy = 6000; L.shadow_soft_size = 4.0
    o = bpy.data.objects.new(L.name, L); o.location = Mz @ Vector((0, -6.0, OPEN_HS * 0.7))
    bpy.data.collections[lights].objects.link(o)
    return M, z, H


# ---------------------------------------------------------------- the plaza -
def build_plaza(T):
    rnd = random.Random(78)
    c, d = frame()
    z = T.sample(c.x, c.y)[0]
    road = math.atan2(d.y, d.x)
    gaps = ((road, 0.30), (road + math.pi, 0.42), (road + 2.35, 0.22),   # road, stairs, hidden brook path
            (road + math.pi / 2, 0.26), (road - math.pi / 2, 0.26))       # hatchery, shop walkways
    def in_gap(a):
        return any(abs((a - g + math.pi) % TAU - math.pi) < w for g, w in gaps)
    p = Part('Entrance_Walk_Plaza', C)
    p.cyl((c.x, c.y, z + 0.05), PLAZA_R + 0.5, 0.5, 'Castle_Stone_Dark', 48)
    rings = ((11.5, 18.0), (18.0, 26.0), (26.0, 34.0), (34.0, 42.0), (42.0, PLAZA_R))
    for k, (r0, r1) in enumerate(rings):
        n = max(8, int(TAU * (r0 + r1) / 2 / 9.0))
        off = rnd.uniform(0, TAU)
        for i in range(n):
            a0 = off + TAU * i / n + 0.012; a1 = off + TAU * (i + 1) / n - 0.012
            mat = rnd.choice(('Castle_Trim', 'Castle_Stone_Light', 'Castle_Stone_Light', 'Castle_Stone'))
            p.ring_sector(r0 + 0.15, r1 - 0.15, a0, a1, z + 0.3, z + 0.62, mat, 4, (c.x, c.y))
    for r0, r1 in ((17.6, 18.4), (41.6, 42.4)):                 # gold inlay rings
        p.ring_sector(r0, r1, 0, TAU, z + 0.3, z + 0.68, 'Gold', 64, (c.x, c.y))
    # the Verdant emblem in the centre
    p.cyl((c.x, c.y, z + 0.5), 11.4, 0.4, 'Verdant_Emblem', 32)
    p.torus((c.x, c.y, z + 0.72), 11.6, 0.45, 'Gold', 40, 6)
    p.prism(leaf_pts(15.0, 8.0), z + 0.7, z + 0.95, 'Gold', Matrix.Translation((0, 0, 0)) @
            Matrix.Translation((c.x, c.y, 0)) @ Matrix.Rotation(road - math.pi / 2 - 0.35, 4, 'Z'))
    # low stone border, open toward the stairs, the road and the hidden path
    n = 40
    for i in range(n):
        a0 = TAU * i / n; a1 = TAU * (i + 1) / n - 0.02
        if in_gap((a0 + a1) / 2):
            continue
        p.ring_sector(PLAZA_R, PLAZA_R + 2.6, a0, a1, z, z + 1.8, rnd.choice(STONES), 3, (c.x, c.y))
        p.ring_sector(PLAZA_R - 0.2, PLAZA_R + 2.8, a0, a1, z + 1.8, z + 2.3, 'Castle_Trim', 3, (c.x, c.y))
    p.finish()
    return c, d, z, gaps


# ---------------------------------------------------------------- dressing with hub assets
def dress(T, M, z0, H, c, d, gaps):
    from floor1_detail import place, ground_z
    rnd = random.Random(79)
    side = Vector((-d.y, d.x, 0))
    road = math.atan2(d.y, d.x)
    gz = lambda p: float(ground_z(T, p.x, p.y))
    L = lambda x, y: M @ Vector((x, y, 0))                      # portal-local ground point -> world
    # lanterns up the stairs and round the plaza (hub Castle_Lantern), lantern posts down the road (hub Lantern_Post)
    for sx in (-1, 1):
        for y, zz in ((-DAIS_D - STEPS * TREAD - 1.0, 4.8), (-DAIS_D - 0.5, H + 4.8)):
            q = L(sx * (STAIR_W / 2 + 2.2), y)
            place('Props', 'Castle_Lantern', q.x, q.y, z0 + zz, road, 0.75)
        q = L(sx * 41.0, -DAIS_D + 4)
        place('Props', 'Castle_Lantern', q.x, q.y, z0 + H, road, 1.0)
    for k in range(8):
        a = road + math.pi + (k + 0.5) * TAU / 8
        if any(abs((a - g + math.pi) % TAU - math.pi) < w + 0.08 for g, w in gaps):
            continue
        q = c + Vector((math.cos(a), math.sin(a), 0)) * (PLAZA_R + 6)
        place('Props', 'Castle_Lantern', q.x, q.y, gz(q), a, 0.9)
    road_pts = next(pts for n, k, w, pts in T.paths if n == 'Entrance_Road')
    meadow = next(pts for n, k, w, pts in T.paths if n == 'Meadow_Road')
    acc, s = 0.0, 1
    for a, b in zip(road_pts, road_pts[1:]):
        acc += math.hypot(b[0] - a[0], b[1] - a[1])
        dist = (Vector(b[:2]) - c.xy).length
        if dist < PLAZA_R + 20 or dist > 760 or acc < 85:
            continue
        acc = 0.0
        t = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
        n = Vector((-t.y, t.x, 0)) * s
        s = -s
        q = Vector((b[0], b[1], 0)) + n * 36
        place('Props', 'Lantern_Post' if dist < 420 else 'Lantern_Wood', q.x, q.y, gz(q), math.atan2(t.y, t.x),
              1.25 if dist < 420 else 1.6)
    # Verdant banner poles: either side of the road mouth, and at the first junction
    for sgn in (-1, 1):
        q = c + d * (PLAZA_R + 10) + side * sgn * 34
        place('Props', 'Verdant_Banner_Pole', q.x, q.y, gz(q), road - math.pi / 2, 1.3)
    j = Vector(meadow[0][:2] + (0,))
    for sgn in (-1, 1):
        q = j + side * sgn * 44 + d * 10
        place('Props', 'Verdant_Banner_Pole', q.x, q.y, gz(q), road - math.pi / 2, 1.3)
    # wooden fences on the outside of the road's curve (gaps left so riders can leave the path)
    for k in range(6, len(road_pts) - 2, 3):
        a, b = road_pts[k], road_pts[k + 1]
        dist = (Vector(a[:2]) - c.xy).length
        if dist < PLAZA_R + 40 or dist > 640 or (k // 3) % 4 == 3:
            continue
        t = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
        n = Vector((-t.y, t.x, 0))
        q = Vector((a[0], a[1], 0)) - n * 33
        place('Props', 'Wood_Fence', q.x, q.y, gz(q), math.atan2(t.y, t.x), 1.4)
    # hub trees framing the portal (never in front of it) and lining the road
    for sgn, back, out, kind, sc in ((-1, 40, 70, 'Tree_Large_High', 2.3), (1, 40, 72, 'Tree_Large_High', 2.2),
                                     (-1, 95, 95, 'Tree_Medium_High', 2.6), (1, 100, 100, 'Tree_Medium_High', 2.5),
                                     (-1, 150, 40, 'Tree_Large_High', 2.8), (1, 160, 50, 'Tree_Large_High', 2.7)):
        q = L(sgn * out, back)
        place('Trees', kind, q.x, q.y, gz(q) - 1, rnd.uniform(0, TAU), sc)
    for k, dist in enumerate((150, 240, 330, 430, 540)):
        for sgn in (-1, 1):
            if (k + (sgn > 0)) % 2:
                continue
            q = c + d * dist + side * sgn * rnd.uniform(70, 95)
            if any((Vector(F.px(*F.village_px(f, r))) - q.xy).length < 75 for n, f, r, *_ in
                   F.VILLAGE_HOUSES + F.VILLAGE_STALLS):
                continue                                        # (village houses and stalls stand there)
            place('Trees', rnd.choice(('Tree_Medium_High', 'Tree_Large_High', 'Tree_Small')), q.x, q.y, gz(q) - 1,
                  rnd.uniform(0, TAU), rnd.uniform(1.9, 2.6))
    # planters, bushes, flowers and rocks round the stairs and plaza
    for sgn in (-1, 1):
        q = L(sgn * (STAIR_W / 2 + 12), -DAIS_D - STEPS * TREAD - 6)
        place('Props', 'Stone_Planter', q.x, q.y, gz(q), road + math.pi / 2, 1.2)
    for k in range(34):
        a = rnd.uniform(0, TAU)
        if any(abs((a - g + math.pi) % TAU - math.pi) < w + 0.1 for g, w in gaps):
            continue
        q = c + Vector((math.cos(a), math.sin(a), 0)) * rnd.uniform(PLAZA_R + 5, PLAZA_R + 22)
        kind = rnd.choice(('Bush_01', 'Bush_02', 'Bush_03', 'Flower_Cluster_Pink', 'Flower_Cluster_White',
                           'Flower_Cluster_Yellow', 'Fern'))
        place('Foliage', kind, q.x, q.y, gz(q), rnd.uniform(0, TAU), rnd.uniform(1.6, 2.6))
    for sgn in (-1, 1):
        for k in range(5):
            q = L(sgn * rnd.uniform(46, 62), rnd.uniform(-34, 4))
            place('Foliage', rnd.choice(('Bush_03', 'Bush_01', 'Flower_Cluster_Purple', 'Fern')), q.x, q.y, gz(q),
                  rnd.uniform(0, TAU), rnd.uniform(1.8, 2.8))
        for k in range(3):
            q = L(sgn * rnd.uniform(48, 70), rnd.uniform(-30, 12))
            place('Rocks', rnd.choice(('Rock_Medium', 'Rock_Large')), q.x, q.y, gz(q) - 1, rnd.uniform(0, TAU),
                  rnd.uniform(0.8, 1.6))
    # the rocky ridge round the portal: boulders, outcrops, bushes, moss and vines (hub rocks and foliage)
    for k in range(40):
        a = rnd.uniform(-1.0, 1.0) * 2.4                       # around the ridge, never in front of the portal
        r = rnd.uniform(90, 300)
        q = L(math.sin(a) * r, 60 + math.cos(a) * r * 0.7)
        if T.sample(q.x, q.y)[0] < z0 + 12:
            continue
        rr = rnd.random()
        if rr < 0.35:
            place('Rocks', rnd.choice(('Rock_Formation', 'Rock_Large')), q.x, q.y, gz(q) - 4, rnd.uniform(0, TAU),
                  rnd.uniform(1.0, 2.2) if rr < 0.15 else rnd.uniform(2.0, 4.0))
        elif rr < 0.7:
            place('Foliage', rnd.choice(('Bush_01', 'Bush_02', 'Bush_03', 'Fern')), q.x, q.y, gz(q), rnd.uniform(0, TAU),
                  rnd.uniform(2.2, 3.4))
        else:
            place('Cliffs', rnd.choice(('Moss_Drape_A', 'Moss_Drape_B', 'Vine_Long')), q.x, q.y, gz(q),
                  rnd.uniform(0, TAU), rnd.uniform(3, 6))
    for sgn in (-1, 1):                                         # rock shoulders flanking the dais
        for k in range(3):
            q = L(sgn * rnd.uniform(52, 75), rnd.uniform(5, 40))
            place('Rocks', 'Rock_Large', q.x, q.y, gz(q) - 2, rnd.uniform(0, TAU), rnd.uniform(1.4, 2.4))
    # the hub rope bridge over the brook, between the two halves of the hidden brook path
    a_end = next(pts for n, k, w, pts in T.paths if n == 'Secret_Brook_Path')[-1]
    b_start = next(pts for n, k, w, pts in T.paths if n == 'Secret_Falls_Path')[0]
    A, B = Vector(a_end), Vector(b_start)
    span = (B - A).xy.length
    src_len = 70.0
    rot = math.atan2(B.y - A.y, B.x - A.x) - math.pi / 2
    place('Props', 'Bridge_Long', A.x, A.y, A.z + 0.4, rot, span / src_len)
    place('Water', 'Mist_Puff', B.x + (B.x - A.x) * 0.0, B.y, A.z - 4, 0.0, 3.0)


def build_road(T, c, d):
    """smooth paved start of the forest road over the terrain path: stone pavers at the plaza, thinning out into
    the dirt trail (the terrain under it is already path); curb stones along the first stretch"""
    from floor1_detail import ground_z
    rnd = random.Random(80)
    pts = next(pts for n, k, w, pts in T.paths if n == 'Entrance_Road')
    P, s = [], 0.0
    for a, b in zip(pts, pts[1:]):
        if (Vector(a[:2]) - c.xy).length < PLAZA_R - 2:
            continue
        P.append(Vector(a[:2]))
        s += (Vector(b[:2]) - Vector(a[:2])).length
        if s > 720:
            break
    p = Part('Entrance_Walk_Road', C)
    w = 50.0
    acc = 0.0
    for k in range(len(P) - 1):
        a, b = P[k], P[k + 1]
        t = (b - a).normalized()
        n = Vector((-t.y, t.x))
        seg = (b - a).length
        acc += seg
        stone_p = max(0.0, 1.0 - acc / 600)
        rows = max(1, int(seg / 4.5))
        for r in range(rows):
            m = a + (b - a) * ((r + 0.5) / rows)
            cols = 9
            for cc in range(cols):
                if rnd.random() > stone_p + 0.06:
                    continue
                off = (cc + 0.5) / cols - 0.5
                q = m + n * off * w + n * rnd.uniform(-0.6, 0.6)
                zq = float(ground_z(T, q.x, q.y))
                rot = Matrix.Rotation(math.atan2(t.y, t.x) + rnd.uniform(-0.08, 0.08), 3, 'Z')
                bevel_box(p, Matrix.Identity(4), (q.x, q.y, zq + 0.35), (seg / rows - 0.4, w / cols - 0.4, 0.55),
                          rnd.choice(('Castle_Trim', 'Castle_Stone_Light', 'Castle_Stone')), 0.12)
        if acc < 360 and k % 2 == 0:                               # curb stones along the stone stretch
            for sg in (-1, 1):
                q = a + n * sg * (w / 2 + 1.2)
                zq = float(ground_z(T, q.x, q.y))
                bevel_box(p, Matrix.Translation((q.x, q.y, zq)) @ Matrix.Rotation(math.atan2(t.y, t.x), 4, 'Z'),
                          (0, 0, 0.6), (seg * 2 - 0.5, 2.2, 1.4), rnd.choice(STONES), 0.2)
    p.finish()


BUILDING_GAP = 24.0                                  # walkway from the plaza border to a building's front


def build_buildings(T, c, d):
    """the hub's own Hatchery (Eggs) and Shop, either side of the plaza, fronts facing it, with paved walkways"""
    import shop, hatchery
    side = Vector((-d.y, d.x, 0))
    z = T.sample(c.x, c.y)[0]
    out = {}
    walk = Part('Entrance_Walk_Walkways', C)
    rnd = random.Random(81)
    # (the Shop first: the Hatchery renames its collections when the Shop already owns a name, as in the hub)
    for name, mod, sgn, front in (('Shop', shop, -1, 23.0), ('Hatchery', hatchery, 1, 20.0)):
        f = -side * sgn                                         # the building faces the plaza
        pos = c + side * sgn * (PLAZA_R + 2.6 + BUILDING_GAP + front)
        rot = math.atan2(f.x, -f.y)                              # local -y (the front) -> f
        if mod is shop:
            shop.build_shop(None, (pos.x, pos.y, z), rot)
        else:
            hatchery.build_hatchery(None, (pos.x, pos.y, z), rot)
        out[name] = (pos.x, pos.y, z)
        a = c + side * sgn * (PLAZA_R + 1.0)                    # paved walkway across the gap in the border
        L = BUILDING_GAP + 2.5
        for i in range(int(L / 4.2) + 1):
            for j in range(5):
                q = a + side * sgn * (i * 4.2 + 2.0) + d * ((j - 2) * 5.6)
                bevel_box(walk, Matrix.Translation((q.x, q.y, z + 0.3)) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, 'Z'),
                          (0, 0, 0), (5.4, 4.0, 0.6), rnd.choice(('Castle_Trim', 'Castle_Stone_Light', 'Castle_Stone')),
                          0.12)
    walk.finish()
    return out


def build_entrance(T):
    """portal + plaza + hub-asset dressing; returns positions for the layout JSON"""
    coll(C, F.ROOT)
    M, z, H = build_portal(T)
    c, d, zp, gaps = build_plaza(T)
    build_road(T, c, d)
    buildings = build_buildings(T, c, d)
    dress(T, M, z, H, c, d, gaps)
    front = M @ Vector((0, -DAIS_D - STEPS * TREAD, 0))
    return dict(plaza=(c.x, c.y, zp), portal=tuple(M @ Vector((0, 0, H))), stairs_bottom=tuple(front),
                facing=(d.x, d.y), hatchery=buildings['Hatchery'], shop=buildings['Shop'])
