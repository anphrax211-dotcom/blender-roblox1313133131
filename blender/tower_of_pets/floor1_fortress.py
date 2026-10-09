"""TOWER OF PETS - FLOOR 1 JUNGLE FORTRESS: the ruler's castle on the Fortress Heights plateau.

Replaces the old massing blockout on the same keep pad (floor1.PADS 'Fortress_Keep'); the island, plateau, cliffs,
boss arena and roads are untouched. Built in the hub's castle language (castle.py: chamfered block courses,
voussoir arches, banded pillars, gold trim) at fortress scale:

  * a masonry podium with a monumental front staircase, braziers and carved pillars along the paved approach;
  * a curtain wall with battlements, a walkable wall walk, buttresses and height steps, linked by ten towers -
    four tall corner towers, side and rear towers and the twin gatehouse towers - all different in height and width,
    each with a block foundation, banded shaft, arrow slits / glowing windows, a corbelled gallery and a tall tiered
    copper roof with tile courses, hip ridges and a gold finial;
  * an arched gatehouse with a raised portcullis, a paved courtyard with planters and statues, an inner terrace with
    its own staircase;
  * the central keep in three stacked levels (heavy banded base with corner turrets; a middle level with arcaded
    arched windows, pilasters and a balcony; a tall upper tower with narrow glowing windows) under the most elaborate
    roof, side wings with gabled roofs, and a monumental entrance: concentric voussoir arches, flanking pillars, red
    and gold banners, braziers, a dark recessed doorway with a controlled warm glow;
  * identity: deep red banners with a gold jungle-crown emblem, warm torches and braziers (a few real lights), vines,
    moss and roots on selected walls only.
Everything is drawn in design units and scaled by SCALE (1 unit = SCALE studs) round the keep pad centre; the front
faces south (world -y), toward the approach path that joins the Fortress Grand Ramp.
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix
from common import Part, mat_plain, coll, round_arch, TAU
import castle
from castle import bevel_box, voussoirs, frame_strip, rect_minus_arch, balustrade
import floor1 as F

C = 'F1_FORTRESS'
LIGHTS = 'Environmental_Lighting'
SUBS = ('Castle_Main', 'Castle_Towers', 'Castle_Roofs', 'Castle_Walls', 'Castle_Entrance', 'Castle_Guardian_Statues',
        'Castle_Banners', 'Jungle_Vines')
ROOF, BAN = [None], [None]                     # the shared roof / banner Parts (Castle_Roofs, Castle_Banners)
SCALE = 6.5                                    # bigger than the first pass: the fortress dominates the north
KEEP_PX = (1300, 520)
FLIP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))       # prism in local XZ, extruded along y
I4 = Matrix.Identity(4)
STONES = ('JF_Sandstone', 'JF_Sandstone_Light', 'JF_Sandstone', 'Castle_Stone_Warm', 'JF_Sandstone_Dark', 'JF_Stone_Moss')
STONES_LOW = ('JF_Sandstone_Dark', 'JF_Stone_Moss', 'JF_Sandstone', 'JF_Stone_Moss', 'Castle_Stone_Dark')   # damp feet


def masonry(*a, **kw):
    """castle.masonry in the weathered jungle stone mix (warm grey, tan, moss)"""
    kw.setdefault('mats', STONES)
    return castle.masonry(*a, **kw)

# layout (design units): podium, curtain wall, towers, inner terrace, keep
POD_X, POD_Y, POD_H = 92.0, 76.0, 6.0          # podium half sizes and top height
WALL_X, WALL_Y, WALL_T = 84.0, 66.0, 6.0       # curtain wall (centre line) half sizes, thickness
RISE, TREAD = 1.6 / SCALE, 4.2 / SCALE         # stairs: 1.6-stud risers, 4.2-stud treads at any SCALE
TER_Y0, TER_Y1, TER_X, TER_H = -6.0, 56.0, 58.0, 12.0     # inner terrace (keep platform)
KEEP_Y = 30.0


def build_fortress_materials():
    P = mat_plain
    from common import mat_noise
    mat_noise('JF_Sandstone', (0.74, 0.58, 0.40), (0.79, 0.63, 0.44), 0.8, 0.15, 0.1, 1.2)
    mat_noise('JF_Sandstone_Light', (0.84, 0.71, 0.52), (0.88, 0.75, 0.56), 0.8, 0.15, 0.1, 1.2)
    mat_noise('JF_Sandstone_Dark', (0.58, 0.45, 0.32), (0.62, 0.49, 0.35), 0.85, 0.15, 0.1, 1.2)
    P('JF_Roof_Copper', (0.80, 0.30, 0.12), 0.6)                # terracotta tiles
    P('JF_Roof_Copper_Dark', (0.52, 0.16, 0.07), 0.65)
    P('JF_Eye_Glow', (1.0, 0.70, 0.15), 0.4, emit=1.8)
    P('JF_Roof_Underside', (0.20, 0.11, 0.06), 0.8)
    P('JF_Banner_Red', (0.62, 0.05, 0.05), 0.7)
    P('JF_Recess', (0.05, 0.035, 0.03), 0.9)
    P('JF_Window_Glow', (1.0, 0.55, 0.20), 0.4, emit=1.4, emit_rgb=(1.0, 0.46, 0.12))
    P('JF_Gate_Glow', (0.85, 0.30, 0.08), 0.5, emit=0.7, emit_rgb=(1.0, 0.38, 0.08))
    P('JF_Iron', (0.16, 0.15, 0.15), 0.5, metal=0.7)
    P('JF_Door_Wood', (0.24, 0.12, 0.06), 0.8)
    P('Fire_Core', (1.0, 0.85, 0.35), 0.4, emit=2.6)
    P('Forge_Glow', (1.0, 0.42, 0.06), 0.4, emit=2.0)
    P('Palm_Trunk', (0.55, 0.40, 0.24), 0.85)
    P('Palm_Leaf', (0.20, 0.55, 0.14), 0.65)
    P('Tropical_Leaf', (0.10, 0.48, 0.16), 0.6)
    P('Tropical_Leaf_Light', (0.30, 0.66, 0.20), 0.6)


# ---------------------------------------------------------------- generic pieces
def Mt(x, y, z=0.0, a=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(a, 4, 'Z')


def faces4(cx, cy, hx, hy):
    """face frames (plane at y = 0, outward -y, x along the face) of an axis-aligned box: front, right, back, left"""
    out = []
    for k, (half, span) in enumerate(((hy, 2 * hx), (hx, 2 * hy), (hy, 2 * hx), (hx, 2 * hy))):
        out.append((Mt(cx, cy, 0, k * math.pi / 2) @ Matrix.Translation((0, -half, 0)), span))
    return out


def crenels(p, M, x0, x1, z, depth, rnd, h=2.6, w=2.6, gap=1.8, mat=None):
    """merlons along local x on a wall top (front at y = 0, through `depth`)"""
    L = x1 - x0
    n = max(1, int((L + gap) / (w + gap)))
    step = L / n
    for i in range(n):
        x = x0 + step * (i + 0.5)
        bevel_box(p, M, (x, depth / 2, z + h / 2), (step - gap, depth, h), mat or rnd.choice(STONES), 0.2)


def arch_window(p, M, x, z, w, hs, glow, rnd, depth=1.1):
    """recessed arched window on a face frame: dark / glowing pane behind a proud stone frame, sill and keystone"""
    inner = round_arch(w, hs, 8)
    outer = round_arch(w + 1.6, hs, 8)
    Mx = M @ Matrix.Translation((x, 0, z))
    p.prism(inner, -0.15, 0.4, 'JF_Window_Glow' if glow else 'JF_Recess', Mx @ FLIP)
    frame_strip(p, Mx, [tuple(o) for o in outer], inner, -depth, 0.1, 'Castle_Trim')
    bevel_box(p, Mx, (0, -depth / 2 - 0.2, -0.35), (w + 2.6, depth + 0.6, 0.7), 'Castle_Trim', 0.12)
    bevel_box(p, Mx, (0, -depth / 2 - 0.15, hs + w / 2 + 0.55), (1.1, depth + 0.4, 1.4), 'JF_Sandstone_Light', 0.15)
    if glow and w > 2.5:                                       # mullion + transom
        p.box(Mx @ Vector((0, -0.25, (hs + w / 2) / 2)), (0.3, 0.3, hs + w / 2), 'JF_Iron', M.to_3x3().normalized())


def slit(p, M, x, z, h, glow, rnd):
    """narrow defensive window"""
    Mx = M @ Matrix.Translation((x, 0, z))
    R = M.to_3x3().normalized()
    p.box(Mx @ Vector((0, -0.1, h / 2)), (0.9, 0.5, h), 'JF_Window_Glow' if glow else 'JF_Recess', R)
    for sx in (-1, 1):
        bevel_box(p, Mx, (sx * 1.0, -0.45, h / 2), (1.1, 1.2, h + 1.2), 'Castle_Trim', 0.12)
    bevel_box(p, Mx, (0, -0.45, h + 0.6), (3.2, 1.2, 1.0), 'Castle_Trim', 0.12)
    bevel_box(p, Mx, (0, -0.45, -0.5), (3.2, 1.2, 0.8), 'Castle_Trim', 0.12)


def red_banner(p, M, w=6.0, length=18.0):
    """deep red banner with a restrained gold border and the gold jungle-crown emblem, hanging from a rod at the local
    origin (front y = 0) - same emblem everywhere"""
    Mb = M @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    o = [(-w / 2, 0), (w / 2, 0), (w / 2, -length), (w * 0.25, -length - w * 0.35), (0, -length),
         (-w * 0.25, -length - w * 0.35), (-w / 2, -length)]
    p.prism(o, -0.3, 0.0, 'JF_Banner_Red', Mb)
    for s in (-1, 1):                                          # fabric folds
        p.prism([(s * w * 0.18 - 0.25, -0.5), (s * w * 0.18 + 0.25, -0.5), (s * w * 0.18 + 0.25, -length + 0.3),
                 (s * w * 0.18 - 0.25, -length + 0.3)], -0.45, -0.25, 'JF_Banner_Red', Mb)
        p.prism([(s * (w / 2 - 0.45), 0), (s * (w / 2), 0), (s * (w / 2), -length), (s * (w / 2 - 0.45), -length)],
                0.0, 0.18, 'Gold', Mb)
    p.prism([(-w / 2, -1.0), (w / 2, -1.0), (w / 2, -1.5), (-w / 2, -1.5)], 0.0, 0.18, 'Gold', Mb)
    cw, cz = w * 0.62, -length * 0.45                          # the jungle crown: band + three leaf points
    crown = [(-cw / 2, cz - cw * 0.3), (cw / 2, cz - cw * 0.3), (cw / 2, cz + cw * 0.18), (cw * 0.3, cz + cw * 0.02),
             (cw * 0.16, cz + cw * 0.42), (0, cz + cw * 0.12), (-cw * 0.16, cz + cw * 0.42), (-cw * 0.3, cz + cw * 0.02),
             (-cw / 2, cz + cw * 0.18)]
    p.prism(crown, 0.0, 0.25, 'Gold', Mb)
    p.cyl(M @ Vector((0, -0.5, 0.4)), 0.3, w + 1.6, 'Gold', 8, axis='X', rot=M.to_3x3().normalized())
    for s in (-1, 1):
        p.ico(M @ Vector((s * (w / 2 + 0.8), -0.5, 0.4)), 0.5, 'Gold', 1)


def wall_torch(p, M, x, z, lights=None, light_name=None):
    """iron bracket torch on a face frame"""
    R = M.to_3x3().normalized()
    q = M @ Vector((x, -0.6, z))
    p.box(M @ Vector((x, -0.2, z - 0.6)), (0.9, 0.5, 2.2), 'JF_Iron', R)
    p.beam(M @ Vector((x, -0.3, z - 1.2)), M @ Vector((x, -1.6, z)), 0.3, 0.3, 'JF_Iron')
    p.cyl(M @ Vector((x, -1.6, z + 0.3)), 0.55, 0.7, 'JF_Iron', 6, r2=0.75)
    p.cone(M @ Vector((x, -1.6, z + 0.6)), 0.55, 1.6, 'Forge_Glow', 5)
    p.cone(M @ Vector((x, -1.6, z + 0.8)), 0.3, 1.5, 'Fire_Core', 5)
    if lights is not None:
        lights.append((light_name, M @ Vector((x, -2.6, z + 1.5)), 900))


def brazier(p, M, x, y, z0, lights=None, light_name=None, big=1.0):
    """stone pedestal brazier with a fire bowl"""
    Mb = M @ Matrix.Translation((x, y, z0)) @ Matrix.Diagonal((big, big, big, 1.0))
    bevel_box(p, Mb, (0, 0, 0.7), (3.4, 3.4, 1.4), 'Castle_Trim', 0.2)
    bevel_box(p, Mb, (0, 0, 2.6), (2.0, 2.0, 2.6), 'JF_Sandstone', 0.2)
    bevel_box(p, Mb, (0, 0, 4.1), (3.0, 3.0, 0.5), 'Castle_Trim', 0.15)
    p.cyl(Mb @ Vector((0, 0, 4.9)), 1.5, 1.2, 'JF_Brazier_Gold', 10, r2=2.3)
    p.torus(Mb @ Vector((0, 0, 5.5)), 2.3, 0.18, 'JF_Brazier_Gold', 12, 4)
    p.cone(Mb @ Vector((0, 0, 5.3)), 1.3, 2.6, 'Forge_Glow', 6)
    p.cone(Mb @ Vector((0, 0, 5.6)), 0.7, 2.8, 'Fire_Core', 5)
    if lights is not None:
        lights.append((light_name, Mb @ Vector((0, 0, 8.5)), 1800))


def tiered_roof(p, cx, cy, z, half, h, rnd, mat='JF_Roof_Copper', tiers=3, flare=2.4, square=True, finial=1.0):
    """tropical temple roof (reference sheet): stacked, broad flared hip roofs in terracotta, each tier with a short
    timber drum under the next, tile courses, upturned gold-tipped corners, a dark underside and a gold finial"""
    segs = 4 if square else 12
    rot = Matrix.Rotation(math.pi / 4, 3, 'Z') if square else None
    k_ = math.sqrt(2) if square else 1.0
    H = h * 0.62                                               # temple roofs sit lower than the old spires
    tiers = max(1, tiers)
    zt = z
    eave = half + flare
    for t in range(tiers):
        f = t / tiers
        e = eave * (1.0 - 0.24 * t)                            # eave half size of this tier
        top = e * 0.5
        ht = H / tiers * 0.62                                  # sloped part
        hd = H / tiers * 0.38                                  # drum under the next tier
        p.cyl(Vector((cx, cy, zt - 0.2)), (e - 0.3) * k_, 0.4, 'JF_Roof_Underside', segs, rot=rot)
        # gently concave slope: two frusta, flatter at the eave
        mid_r, mid_z = e * 0.72, ht * 0.38
        p.cyl(Vector((cx, cy, zt + mid_z / 2)), e * k_, mid_z, mat, segs, r2=mid_r * k_, rot=rot)
        p.cyl(Vector((cx, cy, zt + mid_z + (ht - mid_z) / 2)), mid_r * k_, ht - mid_z, mat, segs, r2=top * k_, rot=rot)
        zz = 0.9
        while zz < ht - 0.6:                                   # tile courses
            r = e + (mid_r - e) * zz / mid_z if zz < mid_z else mid_r + (top - mid_r) * (zz - mid_z) / (ht - mid_z)
            p.cyl(Vector((cx, cy, zt + zz)), (r + 0.16) * k_, 0.28, mat + '_Dark', segs, r2=(r + 0.04) * k_, rot=rot)
            zz += 1.6
        if square:                                             # hip ridges + upturned corners with gold tips
            for sx in (-1, 1):
                for sy in (-1, 1):
                    a0 = Vector((cx + sx * e, cy + sy * e, zt + 0.2))
                    a1 = Vector((cx + sx * mid_r, cy + sy * mid_r, zt + mid_z + 0.2))
                    a2 = Vector((cx + sx * top, cy + sy * top, zt + ht + 0.2))
                    p.beam(a1, a0, 0.45, 0.45, mat + '_Dark'); p.beam(a2, a1, 0.45, 0.45, mat + '_Dark')
                    tip = a0 + Vector((sx * 1.1, sy * 1.1, 1.4)) * max(0.6, e / 8)
                    p.beam(a0, tip, 0.5, 0.5, mat + '_Dark')
                    p.ico(tip, 0.35 * max(0.8, e / 10), 'Gold', 1)
        zt += ht
        if t < tiers - 1:                                      # timber drum carrying the next tier
            dr = top * 1.02
            p.cyl(Vector((cx, cy, zt + hd / 2)), dr * k_, hd, 'JF_Door_Wood', segs, rot=rot)
            p.cyl(Vector((cx, cy, zt + hd - 0.2)), (dr + 0.3) * k_, 0.4, 'Gold', segs, rot=rot)
            zt += hd
    # finial: stacked gold rings and a spike
    p.cyl(Vector((cx, cy, zt + 0.5 * finial)), 0.9 * finial, 1.0 * finial, 'Gold', 8, r2=0.5 * finial)
    p.ico(Vector((cx, cy, zt + 1.6 * finial)), 0.7 * finial, 'Gold', 1)
    p.cone(Vector((cx, cy, zt + 2.0 * finial)), 0.35 * finial, 3.2 * finial, 'Gold', 6)


def tower(name, cx, cy, half, top, rnd, roof_h, slits=True, glow=(), banner=None, gallery=True, z0=POD_H,
          lights=None, torch=False, roof_tiers=3):
    """square tower: block foundation, banded masonry shaft with corner pilasters, slits / windows, corbelled gallery
    with merlons, tall tiered roof"""
    p = Part(f'Fortress_Tower_{name}', 'Castle_Towers')
    bevel_box(p, I4, (cx, cy, (z0 + top) / 2 - 2), (2 * half - 0.6, 2 * half - 0.6, top - z0 + 4), 'Castle_Stone_Dark', 0.0)
    bevel_box(p, I4, (cx, cy, z0 + 1.5), (2 * half + 2.4, 2 * half + 2.4, 3.0), 'Castle_Stone_Dark', 0.3)   # plinth
    bevel_box(p, I4, (cx, cy, z0 + 3.4), (2 * half + 1.4, 2 * half + 1.4, 0.9), 'Castle_Trim', 0.2)
    bands = [z0 + 4 + (top - z0 - 4) * f for f in (0.36, 0.7)]
    for k, (Mf, span) in enumerate(faces4(cx, cy, half, half)):
        masonry(p, Mf, -span / 2 + 1.2, span / 2 - 1.2, z0 + 3.8, top, rnd, 3.6, (4.6, 7.6), 1.2, backing=False)
        for s in (-1, 1):                                      # reinforced corners
            bevel_box(p, Mf, (s * (span / 2 - 0.6), 0.1, (z0 + 3.8 + top) / 2), (1.9, 1.4, top - z0 - 3.8),
                      'JF_Sandstone_Light', 0.2)
        for zb in bands:
            bevel_box(p, Mf, (0, -0.2, zb), (span + 1.0, 1.4, 1.1), 'Castle_Trim', 0.15)
            bevel_box(p, Mf, (0, -0.95, zb - 0.9), (span - 1.0, 0.3, 0.5), 'JF_Jade', 0.05)
        if slits:
            for zb in bands:
                g = (k, zb) in glow or (k == 0 and zb == bands[1] and 'front' in glow)
                slit(p, Mf, 0, zb + 3.0, 6.0, g, rnd)
            slit(p, Mf, 0, z0 + 7.0, 5.0, False, rnd)
        if torch and k == 0:
            wall_torch(p, Mf, -half * 0.55, bands[0] - 2.5, lights, f'Fortress_Torch_{name}')
    if gallery:                                                # corbels + projecting gallery + merlons
        for Mf, span in faces4(cx, cy, half, half):
            n = max(3, int(span / 3.2))
            for i in range(n):
                x = -span / 2 + 1.0 + (span - 2) * i / (n - 1)
                bevel_box(p, Mf, (x, -0.6, top - 1.0), (1.0, 1.6, 2.0), 'Castle_Trim', 0.15)
        bevel_box(p, I4, (cx, cy, top + 0.6), (2 * half + 3.4, 2 * half + 3.4, 1.2), 'Castle_Trim', 0.2)
        for Mf, span in faces4(cx, cy, half + 1.7, half + 1.7):
            crenels(p, Mf, -span / 2 + 0.6, span / 2 - 0.6, top + 1.2, 1.2, rnd, h=2.2, w=2.0, gap=1.4)
        rz = top + 1.2
    else:
        bevel_box(p, I4, (cx, cy, top + 0.5), (2 * half + 2.0, 2 * half + 2.0, 1.0), 'Castle_Trim', 0.2)
        rz = top + 1.0
    tiered_roof(ROOF[0], cx, cy, rz + (2.6 if gallery else 0.0), half + (0.6 if gallery else 0.2), roof_h, rnd,
                tiers=roof_tiers)
    if banner:
        Mf = faces4(cx, cy, half, half)[0][0]
        mask(p, Mf @ Matrix.Translation((0, -1.0, banner[0] + 6.5)), half * 0.75)
        red_banner(BAN[0], Mf @ Matrix.Translation((0, -1.2, banner[0])), banner[1], banner[2])
    return p


def wall(name, A, B, z0, z1, rnd, thick=WALL_T, walk=None):
    """curtain wall segment A -> B (perimeter counter-clockwise, outside = right of travel): core, masonry outside,
    buttresses, wall walk with parapet merlons; returns the walkway Part"""
    p = Part(f'Fortress_Wall_{name}', 'Castle_Walls')
    A, B = Vector(A), Vector(B)
    L = (B - A).length
    u = (B - A) / L
    M = Mt(A.x, A.y, 0, math.atan2(u.y, u.x)) @ Matrix.Translation((0, -thick / 2, 0))   # front = outside
    bevel_box(p, M, (L / 2, thick / 2, (z0 + z1) / 2), (L, thick, z1 - z0), 'Castle_Stone_Dark', 0.0)
    masonry(p, M, 0, L, z0, z1, rnd, 3.4, (5.0, 8.5), 1.1, backing=False)
    masonry(p, M @ Mt(L, thick, 0, math.pi), 0, L, z0, z1, rnd, 3.4, (6.0, 9.5), 0.8, backing=False)
    n = max(1, int(L / 22))
    for i in range(1, n):                                      # buttresses
        x = L * i / n
        bevel_box(p, M, (x, -0.9, (z0 + z1 - 4) / 2), (3.0, 2.6, z1 - z0 - 4), 'JF_Sandstone_Light', 0.25)
        bevel_box(p, M, (x, -0.9, z1 - 3.4), (3.6, 3.0, 1.0), 'Castle_Trim', 0.2)
    bevel_box(p, M, (L / 2, -0.25, z1 - 1.0), (L, 1.2, 1.2), 'Castle_Trim', 0.15)        # cornice
    crenels(p, M, 0.4, L - 0.4, z1, 1.4, rnd)
    bevel_box(p, M, (L / 2, thick - 0.5, z1 + 0.6), (L, 1.0, 1.2), 'Castle_Trim', 0.12)   # inner parapet
    w = walk or Part(f'Fortress_Walk_Wall_{name}', 'Castle_Walls')
    bevel_box(w, M, (L / 2, thick / 2 + 0.2, z1 - 0.15), (L, thick - 2.4, 0.5), 'JF_Sandstone_Light', 0.1)
    return p, w, M, L


def flight(w, M, x, y_top, z_top, z_bot, width, rnd, cheeks=True, p=None):
    """straight staircase descending toward -y from (x, y_top, z_top) to z_bot; stepped cheek walls"""
    n = max(1, int(round((z_top - z_bot) / RISE)))
    rise = (z_top - z_bot) / n
    for k in range(n):
        y = y_top - (k + 0.5) * TREAD
        h = z_top - k * rise - z_bot
        for i in range(max(1, int(width / 8))):
            ww = width / max(1, int(width / 8))
            bevel_box(w, M, (x - width / 2 + ww * (i + 0.5), y, z_bot + h / 2 - 0.3), (ww - 0.12, TREAD - 0.08, h + 0.6),
                      'Castle_Trim' if (i + k) % 3 else 'JF_Sandstone_Light', 0.12)
    if p is not None:                                          # moss in a few step joints near the edges
        for k in range(1, n, 2):
            for s in (-1, 1):
                if rnd.random() < 0.55:
                    p.box(M @ Vector((x + s * (width / 2 - rnd.uniform(0.6, 3.0)), y_top - k * TREAD,
                                      z_top - k * rise + 0.05)), (rnd.uniform(1.0, 2.6), 0.35, 0.2), 'JF_Moss')
    if cheeks and p is not None:
        for s in (-1, 1):
            xx = x + s * (width / 2 + 1.6)
            for k in range(0, n, 2):
                y = y_top - (k + 1.0) * TREAD
                h = z_top - k * rise - z_bot + 2.2
                bevel_box(p, M, (xx, y, z_bot + h / 2 - 0.5), (3.2, 2 * TREAD + 0.05, h + 1.0), rnd.choice(STONES), 0.2)
    return y_top - n * TREAD


def paving(w, x0, x1, y0, y1, z, rnd, tile=(7.5, 7.5), mats=('Castle_Trim', 'JF_Sandstone_Light', 'JF_Sandstone'),
           skip=None):
    """flagstones: rows of tiles with a running offset, a few larger slabs"""
    y = y0
    row = 0
    while y < y1 - 0.5:
        th = min(tile[1] * rnd.uniform(0.85, 1.1), y1 - y)
        x = x0 - (tile[0] * 0.5 if row % 2 else 0)
        while x < x1 - 0.5:
            tw = tile[0] * rnd.uniform(0.8, 1.25)
            a, b = max(x, x0), min(x + tw, x1)
            if b - a > 1.0 and not (skip and skip((a + b) / 2, y + th / 2)):
                bevel_box(w, I4, ((a + b) / 2, y + th / 2, z - 0.2), (b - a - 0.25, th - 0.25, 0.6), rnd.choice(mats),
                          0.15)
            x += tw
        y += th
        row += 1


def leaf_relief(p, M, size, s=1):
    """carved stone leaf with a gold vein on a face frame"""
    from floor1_entrance import leaf_pts
    R = Matrix.Rotation(0.5 * s, 4, 'Y')
    p.prism(leaf_pts(size, size * 0.55), -0.5, 0.0, 'Castle_Trim', M @ R @ FLIP)
    p.prism([(-0.08 * size, -size * 0.42), (0.08 * size, -size * 0.42), (0.03 * size, size * 0.42),
             (-0.03 * size, size * 0.42)], -0.65, -0.45, 'Gold', M @ R @ FLIP)


def crest(p, M, size):
    """the fortress crest: jade shield, gold border and the gold jungle leaf-crown (front at y = 0)"""
    sh = [(-size / 2, size * 0.45), (size / 2, size * 0.45), (size / 2, -size * 0.1), (0, -size * 0.6),
          (-size / 2, -size * 0.1)]
    p.prism([(x * 1.16, z * 1.12 + 0.05) for x, z in sh], 0.0, 0.5, 'Gold', M @ FLIP)
    p.prism(sh, -0.25, 0.0, 'JF_Jade', M @ FLIP)
    from floor1_entrance import leaf_pts
    for a in (-0.55, 0.0, 0.55):
        Ml = M @ Matrix.Translation((math.sin(a) * size * 0.1, 0, size * 0.02)) @ Matrix.Rotation(-a, 4, 'Y')
        p.prism(leaf_pts(size * 0.62, size * 0.24), -0.45, -0.25, 'Gold', Ml @ FLIP)


def mask(p, M, size):
    """carved guardian mask relief: stone face, dark eye slots, gold brow, jade cheeks"""
    face = [(-size / 2, size * 0.5), (size / 2, size * 0.5), (size * 0.42, -size * 0.2), (0, -size * 0.62),
            (-size * 0.42, -size * 0.2)]
    p.prism(face, -0.7, 0.0, 'Castle_Trim', M @ FLIP)
    p.prism([(-size * 0.48, size * 0.5), (size * 0.48, size * 0.5), (size * 0.4, size * 0.3),
             (-size * 0.4, size * 0.3)], -1.0, -0.6, 'Gold', M @ FLIP)
    for s in (-1, 1):
        p.prism([(s * size * 0.08, size * 0.18), (s * size * 0.34, size * 0.22), (s * size * 0.3, size * 0.06),
                 (s * size * 0.1, size * 0.06)][::s], -0.9, -0.6, 'JF_Recess', M @ FLIP)
        p.prism([(s * size * 0.36, -size * 0.02), (s * size * 0.42, -size * 0.18), (s * size * 0.22, -size * 0.3),
                 (s * size * 0.18, -size * 0.1)][::s], -0.85, -0.6, 'JF_Jade', M @ FLIP)
    p.prism([(-size * 0.07, size * 0.04), (size * 0.07, size * 0.04), (size * 0.1, -size * 0.2), (-size * 0.1, -size * 0.2)],
            -1.1, -0.6, 'JF_Sandstone_Light', M @ FLIP)
    p.prism([(-size * 0.22, -size * 0.3), (size * 0.22, -size * 0.3), (size * 0.12, -size * 0.42), (-size * 0.12, -size * 0.42)],
            -0.9, -0.6, 'JF_Recess', M @ FLIP)


def jungle_pillar(p, M, w, h, rnd):
    """entrance pillar: stone base and capital, jade shaft panels with gold leaf, stone bands"""
    bevel_box(p, M, (0, 0, 0.9), (w + 2.6, w + 2.6, 1.8), 'Castle_Trim', 0.25)
    bevel_box(p, M, (0, 0, 2.3), (w + 1.4, w + 1.4, 1.0), 'JF_Sandstone_Light', 0.2)
    bevel_box(p, M, (0, 0, h / 2 + 1.4), (w, w, h - 2.8), 'Castle_Stone_Warm', 0.25)
    for k, (z0, z1) in enumerate(((3.6, h * 0.48), (h * 0.55, h - 3.6))):
        for a in range(4):
            Mf = M @ Matrix.Rotation(a * math.pi / 2, 4, 'Z') @ Matrix.Translation((0, -w / 2, 0))
            bevel_box(p, Mf, (0, -0.1, (z0 + z1) / 2), (w - 1.2, 0.5, z1 - z0), 'JF_Jade', 0.08)
            for s in (-1, 1):
                bevel_box(p, Mf, (s * (w / 2 - 0.45), -0.2, (z0 + z1) / 2), (0.3, 0.4, z1 - z0), 'Gold', 0.05)
            if a == 0:
                leaf_relief(p, Mf @ Matrix.Translation((0, -0.2, (z0 + z1) / 2)), min(z1 - z0, w) * 0.7, 1 - 2 * k)
    bevel_box(p, M, (0, 0, h * 0.515), (w + 0.8, w + 0.8, 1.0), 'Castle_Trim', 0.2)
    bevel_box(p, M, (0, 0, h - 1.6), (w + 1.4, w + 1.4, 1.2), 'Castle_Trim', 0.2)
    bevel_box(p, M, (0, 0, h - 0.5), (w + 2.4, w + 2.4, 1.0), 'JF_Sandstone_Light', 0.25)
    p.cone(M @ Vector((0, 0, h)), w * 0.45, w * 0.6, 'JF_Brazier_Gold', 6)


def guardian(p, M, rnd, side=1):
    """stylised stone jungle beast (tiger / lizard temple guardian) sitting on a plinth, facing -y"""
    B = lambda c, s_, mat, bev=0.35: bevel_box(p, M, c, s_, mat, bev)
    B((0, 0, 1.1), (8.0, 10.0, 2.2), 'Castle_Trim')                     # plinth
    B((0, 0, 2.6), (7.0, 9.0, 0.8), 'JF_Jade', 0.15)
    B((0, -4.55, 2.6), (6.0, 0.2, 0.4), 'Gold', 0.05)
    B((0, 0, 3.4), (7.4, 9.4, 0.8), 'JF_Sandstone_Light', 0.2)
    S = 'JF_Rock_Dark'
    B((0, 2.0, 6.0), (5.6, 5.6, 4.6), S)                               # haunches
    B((0, -0.4, 8.6), (4.8, 4.8, 6.2), S)                              # chest, upright
    for s in (-1, 1):
        B((s * 1.6, -2.6, 5.6), (1.6, 1.8, 4.4), S)                     # front legs
        B((s * 1.6, -3.3, 4.0), (2.0, 2.6, 1.0), 'JF_Sandstone')        # paws
        for t in (-0.6, 0.0, 0.6):
            p.cone(M @ Vector((s * 1.6 + t, -4.7, 3.8)), 0.25, -0.0 + 0.5, 'Gold', 4)
        B((s * 2.9, 2.6, 6.2), (0.9, 3.6, 3.4), 'JF_Jade', 0.15)       # armour plates on the flanks
    B((0, -1.6, 12.6), (4.6, 4.2, 3.6), S)                              # head
    B((0, -4.4, 12.0), (3.2, 2.6, 1.8), S)                              # snout / upper jaw
    p.box(M @ Vector((0, -4.0, 10.6)), (2.8, 2.4, 0.8), S,
          M.to_3x3().normalized() @ Matrix.Rotation(-0.35, 3, 'X'))                       # open lower jaw
    p.box(M @ Vector((0, -4.2, 11.2)), (2.4, 1.6, 0.6), 'JF_Recess')                      # mouth
    for t in (-0.9, 0.9):
        p.cone(M @ Vector((t, -5.4, 11.2)), 0.25, -0.9, 'Castle_Trim', 4)                  # fangs
    for s in (-1, 1):
        p.box(M @ Vector((s * 1.2, -3.75, 13.2)), (0.9, 0.3, 0.5), 'JF_Eye_Glow')         # eyes
        B((s * 1.25, -3.6, 13.75), (1.4, 0.8, 0.45), 'Gold', 0.08)                      # brow
        p.cone(M @ Vector((s * 1.8, -1.0, 14.3)), 0.8, 2.0, S, 4)                         # ears
    B((0, -1.4, 10.5), (5.2, 4.8, 0.7), 'JF_Brazier_Gold', 0.15)                       # collar
    p.cyl(M @ Vector((0, -3.85, 10.3)), 0.8, 0.4, 'JF_Jade', 8, axis='Y', rot=M.to_3x3().normalized())
    p.cone(M @ Vector((0, 4.6, 4.6)), 0.9, 4.0, S, 5)                  # tail stump
    for c, r in (((0, -1.6, 14.4), 1.6), ((0, 2.0, 8.3), 1.8), ((0, -0.4, 11.7), 1.1)):   # moss on the tops
        p.ico(M @ Vector(c), r, 'JF_Moss', 1, (1.3, 1.2, 0.3), smooth=False)
    from foliage import vine
    for t in (-3.2, 3.4):
        vine(p, M @ Vector((t, -4.2, 3.6)), 2.6, rnd, 0.9)


# ---------------------------------------------------------------- the fortress
def build_keep(rnd, lights, vines):
    """three stacked levels, corner turrets, side wings, the monumental entrance"""
    p = Part('Fortress_Keep', 'Castle_Main')
    z0 = TER_H
    bx, by = 30.0, 21.0                                        # base half sizes
    zb1 = z0 + 28.0
    mx, my = 23.0, 16.5                                        # middle level
    zm1 = zb1 + 24.0
    ux, uy = 12.5, 11.0                                        # upper tower
    zu1 = zm1 + 42.0
    cy = KEEP_Y
    # --- base: heavy foundation, banded masonry, recessed panels, corner turrets
    bevel_box(p, I4, (0, cy, (z0 + zb1) / 2), (2 * bx - 0.8, 2 * by - 0.8, zb1 - z0), 'Castle_Stone_Dark', 0.0)
    bevel_box(p, I4, (0, cy, z0 + 1.6), (2 * bx + 3.0, 2 * by + 3.0, 3.2), 'Castle_Stone_Dark', 0.35)
    bevel_box(p, I4, (0, cy, z0 + 3.6), (2 * bx + 1.8, 2 * by + 1.8, 1.0), 'Castle_Trim', 0.2)
    door_w, door_hs = 13.0, 12.0
    door_top = door_hs + door_w / 2
    for k, (Mf, span) in enumerate(faces4(0, cy, bx, by)):
        skip = None
        if k == 0:
            skip = lambda x, z, w_, h_: abs(x) < door_w / 2 + 6.5 and z < z0 + 4 + door_top + 4.5
        masonry(p, Mf, -span / 2 + 1.5, span / 2 - 1.5, z0 + 4.1, zb1, rnd, 3.4, (5.0, 8.0), 1.3, skip=skip,
                backing=False)
        for s in (-1, 1):
            bevel_box(p, Mf, (s * (span / 2 - 0.8), 0.0, (z0 + zb1) / 2), (2.6, 1.8, zb1 - z0), 'JF_Sandstone_Light', 0.25)
        bevel_box(p, Mf, (0, -0.3, zb1 - 9.0), (span + 1.4, 1.6, 1.2), 'Castle_Trim', 0.18)   # decorative band
        if k != 0:                                             # recessed panels + slits on the other faces
            for x in (-span / 4, span / 4):
                bevel_box(p, Mf, (x, -0.1, z0 + 13), (span / 4, 0.6, 10.0), 'Castle_Stone_Dark', 0.1)
                slit(p, Mf, x, z0 + 9.5, 7.0, k == 2, rnd)
    # base top: cornice, merlons, four corner turrets with small roofs
    bevel_box(p, I4, (0, cy, zb1 + 0.6), (2 * bx + 2.6, 2 * by + 2.6, 1.2), 'Castle_Trim', 0.2)
    for Mf, span in faces4(0, cy, bx + 1.3, by + 1.3):
        crenels(p, Mf, -span / 2 + 6, span / 2 - 6, zb1 + 1.2, 1.2, rnd)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tx, ty = sx * (bx - 1.0), cy + sy * (by - 1.0)
            p.cyl(Vector((tx, ty, zb1 + 4.0)), 3.4, 8.0, 'JF_Sandstone_Light', 10)
            p.cyl(Vector((tx, ty, zb1 + 8.4)), 3.9, 0.8, 'Castle_Trim', 10)
            for a in range(4):
                q = Vector((tx + math.cos(a * math.pi / 2 + 0.4) * 3.42, ty + math.sin(a * math.pi / 2 + 0.4) * 3.42,
                            zb1 + 4.5))
                p.box(q, (0.5, 0.5, 2.6), 'JF_Window_Glow' if a == 0 else 'JF_Recess',
                      Matrix.Rotation(a * math.pi / 2 + 0.4, 3, 'Z'))
            tiered_roof(ROOF[0], tx, ty, zb1 + 8.8, 3.6, 9.0, rnd, tiers=2, flare=1.0, square=False, finial=0.6)
    # --- middle level: arcaded arched windows between pilasters, balcony, banners
    bevel_box(p, I4, (0, cy, (zb1 + zm1) / 2), (2 * mx - 0.6, 2 * my - 0.6, zm1 - zb1), 'Castle_Stone_Dark', 0.0)
    for k, (Mf, span) in enumerate(faces4(0, cy, mx, my)):
        nwin = 4 if span > 40 else 3
        xs = [-span / 2 + span * (i + 0.5) / nwin for i in range(nwin)]
        masonry(p, Mf, -span / 2 + 1.2, span / 2 - 1.2, zb1, zm1, rnd, 3.0, (4.0, 6.5), 1.1, backing=False,
                skip=lambda x, z, w_, h_, xs=xs: any(abs(x - q) < 3.2 for q in xs) and zb1 + 4 < z < zb1 + 16.5)
        for x in xs:
            arch_window(p, Mf, x, zb1 + 4.5, 4.2, 7.5, (k == 0) or rnd.random() < 0.45, rnd)
        for i in range(nwin + 1):                              # pilasters between the windows
            x = -span / 2 + span * i / nwin
            bevel_box(p, Mf, (x, -0.5, (zb1 + zm1) / 2), (1.6, 1.4, zm1 - zb1), 'JF_Sandstone_Light', 0.2)
            bevel_box(p, Mf, (x, -0.8, zm1 - 1.6), (2.4, 2.0, 1.2), 'Castle_Trim', 0.15)
        bevel_box(p, Mf, (0, -0.6, zm1 - 0.5), (span + 2.0, 2.2, 1.2), 'Castle_Trim', 0.2)        # cornice
        bevel_box(p, Mf, (0, -0.95, zm1 - 0.5), (span + 1.0, 0.3, 0.45), 'Gold', 0.05)
        if k == 0:
            for s in (-1, 1):
                red_banner(BAN[0], Mf @ Matrix.Translation((s * span * 0.5 - s * 0.2, -1.6, zm1 - 2.0)), 4.6, 16.0)
    # pent roof skirt round the middle level, then the upper tower
    p.cyl(Vector((0, cy, zm1 + 1.6)), (mx + 2.6) * math.sqrt(2), 3.2, 'JF_Roof_Copper', 4, r2=(mx - 4.0) * math.sqrt(2),
          rot=Matrix.Rotation(math.pi / 4, 3, 'Z'))
    p.box(Vector((0, cy, zm1 + 1.5)), (2 * mx + 0.2, 2 * my + 4.6, 3.0), 'JF_Roof_Copper')
    bevel_box(p, I4, (0, cy, (zm1 + zu1) / 2), (2 * ux - 0.4, 2 * uy - 0.4, zu1 - zm1), 'Castle_Stone_Dark', 0.0)
    for k, (Mf, span) in enumerate(faces4(0, cy, ux, uy)):
        masonry(p, Mf, -span / 2 + 1.0, span / 2 - 1.0, zm1, zu1, rnd, 3.0, (3.6, 5.6), 1.0, backing=False,
                skip=lambda x, z, w_, h_: abs(abs(x) - span * 0.22) < 1.9 and zm1 + 7 < z < zm1 + 22)
        for x in (-span * 0.22, span * 0.22):
            slit(p, Mf, x, zm1 + 7.5, 13.0, True, rnd)
        for s in (-1, 1):                                      # ornamental columns at the corners
            p.cyl(Mf @ Vector((s * (span / 2 + 0.3), -0.3, (zm1 + zu1) / 2)), 1.0, zu1 - zm1, 'Castle_Trim', 8)
            bevel_box(p, Mf, (s * (span / 2 + 0.3), -0.3, zu1 - 0.8), (2.6, 2.6, 1.6), 'JF_Sandstone_Light', 0.2)
        bevel_box(p, Mf, (0, -0.4, zm1 + 4.5), (span + 0.8, 1.2, 1.0), 'Castle_Trim', 0.15)
        bevel_box(p, Mf, (0, -0.4, zu1 - 2.0), (span + 2.0, 2.0, 1.3), 'Castle_Trim', 0.18)
        bevel_box(p, Mf, (0, -1.45, zu1 - 2.0), (span + 1.0, 0.3, 0.5), 'Gold', 0.05)
        for i in range(5):                                     # roof brackets
            x = -span / 2 + 1.5 + (span - 3) * i / 4
            bevel_box(p, Mf, (x, -1.0, zu1 - 0.2), (1.0, 2.6, 1.6), 'Castle_Trim', 0.12)
    # the most elaborate roof: main spire, four corner pinnacles, front dormer
    tiered_roof(ROOF[0], 0, cy, zu1 + 0.6, ux + 1.2, 46.0, rnd, tiers=4, flare=3.0, finial=2.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tiered_roof(ROOF[0], sx * (ux + 0.3), cy + sy * (uy + 0.3), zu1 + 0.6, 1.6, 9.0, rnd, tiers=2, flare=0.6, finial=0.5)
    Mf = faces4(0, cy, ux, uy)[0][0]
    bevel_box(p, Mf, (0, -3.0, zu1 + 4.5), (6.0, 6.0, 7.0), 'JF_Sandstone_Light', 0.2)
    arch_window(p, Mf @ Matrix.Translation((0, -6.0, 0)), 0, zu1 + 2.2, 2.6, 2.8, True, rnd, depth=0.8)
    pts = [(-3.8, zu1 + 8.0), (3.8, zu1 + 8.0), (0, zu1 + 13.0)]
    p.prism(pts, -6.6, 0.0, 'JF_Roof_Copper', Mf @ FLIP)
    # --- balcony over the entrance
    Mf0 = faces4(0, cy, bx, by)[0][0]
    zbal = z0 + door_top + 6.5
    bevel_box(p, Mf0, (0, -3.2, zbal), (22.0, 6.4, 1.2), 'Castle_Trim', 0.2)
    for x in (-9.0, -4.5, 4.5, 9.0):
        p.beam(Mf0 @ Vector((x, -0.2, zbal - 4.2)), Mf0 @ Vector((x, -5.8, zbal - 0.6)), 1.2, 1.2, 'Castle_Trim')
    balustrade(p, Mf0 @ Matrix.Translation((0, -6.0, 0)), -10.8, 10.8, zbal + 0.6, rnd, 3.2, 7.2, 'Castle_Trim')
    for s in (-1, 1):
        balustrade(p, Mf0 @ Mt(s * 10.8, -3.0, 0, s * math.pi / 2), -2.8, 2.8, zbal + 0.6, rnd, 3.2, 6.0, 'Castle_Trim')
    arch_window(p, Mf0, 0, zbal + 0.6, 5.0, 6.5, True, rnd)
    # --- monumental entrance: concentric arches, pillars, banners, braziers, dark doorway with a warm glow
    pk, p = p, Part('Fortress_Keep_Entrance', 'Castle_Entrance')
    ent = p
    Md = Mf0 @ Matrix.Translation((0, 0, z0))
    inner = round_arch(door_w, door_hs, 12)
    p.prism(inner, -0.3, 0.45, 'JF_Recess', Md @ FLIP)
    p.prism(round_arch(door_w - 6.0, door_hs - 2.5, 10), -0.42, -0.3, 'JF_Gate_Glow', Md @ FLIP)
    for s in (-1, 1):                                          # half-open door leaves, the glow between them
        Mleaf = Md @ Mt(s * door_w / 2, -0.9, 0, s * 0.55)
        p.box(Mleaf @ Vector((-s * door_w * 0.21, 0, door_hs * 0.5)), (door_w * 0.4, 0.6, door_hs), 'JF_Door_Wood',
              Mleaf.to_3x3().normalized())
        for zz in (2.0, door_hs - 2.0):
            p.box(Mleaf @ Vector((-s * door_w * 0.21, -0.35, zz)), (door_w * 0.4, 0.2, 0.6), 'JF_Iron',
                  Mleaf.to_3x3().normalized())
    lay = [round_arch(door_w + 2 * k * 2.3, door_hs, 14) for k in range(4)]
    for k in range(3):
        voussoirs(p, Md, lay[k + 1], lay[k], -0.8 - k * 1.1, 1.0, rnd, stone=3.4,
                  mat=('JF_Sandstone_Light', 'Castle_Trim', 'JF_Sandstone_Light')[k], keystone=(k == 2),
                  backing=(k == 0))
    frame_strip(p, Md, round_arch(door_w + 2 * 2.3 + 0.5, door_hs, 14), lay[1], -2.1, -1.7, 'Gold')   # one gold inlay
    for s in (-1, 1):                                          # jambs
        bevel_box(p, Md, (s * (door_w / 2 + 3.4), -1.4, door_hs / 2), (6.8, 2.8, door_hs), 'JF_Sandstone_Light', 0.25)
    for s in (-1, 1):                                          # flanking pillars + banners
        jungle_pillar(p, Md @ Matrix.Translation((s * (door_w / 2 + 10.0), -2.6, 0)), 4.2, door_top + 6.0, rnd)
        red_banner(BAN[0], Md @ Matrix.Translation((s * (door_w / 2 + 10.0), -5.4, door_top + 1.0)), 4.4, 15.0)
        wall_torch(p, Md, s * (door_w / 2 + 5.5), door_hs + 1.0, lights, f'Fortress_Keep_Door_Torch_{s + 1}')
    lights.append(('Fortress_Keep_Door_Glow', Md @ Vector((0, 1.0, door_hs * 0.6)), 2500))
    crest(p, Md @ Matrix.Translation((0, -3.9, door_top + 3.4)), 5.0)          # jungle crest above the arch
    for s in (-1, 1):                                          # carved leaf ornaments either side of the arch
        leaf_relief(p, Md @ Matrix.Translation((s * (door_w / 2 + 5.0), -3.0, door_top - 1.0)), 3.0, s)
    p = pk
    crest(p, faces4(0, cy, ux, uy)[0][0] @ Matrix.Translation((0, -1.4, zu1 - 7.0)), 4.0)   # crest near the top
    # --- side wings with gabled roofs
    for s in (-1, 1):
        wx0, wx1 = s * bx, s * (bx + 22.0)
        wcx = (wx0 + wx1) / 2
        wy, wz1 = 13.0, z0 + 20.0
        bevel_box(p, I4, (wcx, cy + 2, (z0 + wz1) / 2), (22.0, 2 * wy, wz1 - z0), 'Castle_Stone_Dark', 0.0)
        for k, (Mf, span) in enumerate(faces4(wcx, cy + 2, 11.0, wy)):
            if k == (3 if s > 0 else 1):
                continue
            masonry(p, Mf, -span / 2 + 0.8, span / 2 - 0.8, z0, wz1, rnd, 3.2, (4.5, 7.5), 1.1, backing=False,
                    skip=lambda x, z, w_, h_: abs(abs(x) - span * 0.25) < 2.6 and z0 + 5 < z < z0 + 13)
            for x in (-span * 0.25, span * 0.25):
                arch_window(p, Mf, x, z0 + 5.5, 3.2, 4.5, rnd.random() < 0.6, rnd)
            bevel_box(p, Mf, (0, -0.3, wz1 - 0.6), (span + 1.0, 1.4, 1.2), 'Castle_Trim', 0.15)
        # gable roof (ridge along y)
        rh = 10.0
        for sg in (-1, 1):
            q = [(wcx + sg * 0.0, cy + 2 - wy - 1.5, wz1 + rh), (wcx + sg * 0.0, cy + 2 + wy + 1.5, wz1 + rh),
                 (wcx + sg * 12.8, cy + 2 + wy + 1.5, wz1 - 1.0), (wcx + sg * 12.8, cy + 2 - wy - 1.5, wz1 - 1.0)]
            p.hexa([Vector((x, y, z - 0.8)) for x, y, z in q] + [Vector(v) for v in q], 'JF_Roof_Copper')
            k = 1
            while k * 2.2 < 12.4:
                t = k * 2.2 / 12.8
                p.beam(Vector((wcx + sg * 12.8 * t, cy + 2 - wy - 1.3, wz1 + rh - (rh + 1) * t + 0.15)),
                       Vector((wcx + sg * 12.8 * t, cy + 2 + wy + 1.3, wz1 + rh - (rh + 1) * t + 0.15)), 0.45, 0.45,
                       'JF_Roof_Copper_Dark')
                k += 1
        p.box(Vector((wcx, cy + 2, wz1 + rh + 0.2)), (1.2, 2 * wy + 3.4, 1.0), 'JF_Roof_Copper_Dark')
        for sy in (-1, 1):
            p.prism([(wcx - 11.0, wz1), (wcx + 11.0, wz1), (wcx, wz1 + rh - 0.6)], cy + 2 + sy * wy - 0.4,
                     cy + 2 + sy * wy + 0.4, 'JF_Sandstone_Light', FLIP)
    # selected vines and moss (not over the entrance, windows or banners)
    for x, side_y, top_z, ln in ((-bx - 22.0, cy - 11.0, z0 + 19, 12), (bx + 22.0, cy - 11.0, z0 + 19, 10),
                                 (-bx + 0.5, cy - by - 1.0, z0 + 22, 14), (bx - 0.5, cy - by - 1.0, z0 + 20, 11),
                                 (-mx + 0.5, cy + my + 1.0, zm1 - 2, 16), (mx - 4, cy + my + 1.0, zm1 - 2, 12)):
        vines.append((Vector((x, side_y, top_z)), ln))
    return p, ent, zu1 + 46 + 5


def build_fortress(T):
    coll(C, F.ROOT)
    coll(LIGHTS, F.ROOT)
    for sub in SUBS:
        coll(sub, C)
    ROOF[0] = Part('Fortress_Roofs', 'Castle_Roofs')
    BAN[0] = Part('Fortress_Banners', 'Castle_Banners')
    rnd = random.Random(1300)
    kx, ky = F.px(*KEEP_PX)
    kz = T.sample(kx, ky)[0]
    Mw = Matrix.Translation((kx, ky, kz)) @ Matrix.Diagonal((SCALE, SCALE, SCALE, 1.0))
    lights, vines, parts = [], [], []
    # --- podium with a masonry face, the front staircase and the paved approach
    walk = Part('Fortress_Walk_Podium', 'Castle_Main')
    pod = Part('Fortress_Podium', 'Castle_Main')
    bevel_box(pod, I4, (0, 0, (POD_H - 4) / 2), (2 * POD_X - 0.8, 2 * POD_Y - 0.8, POD_H + 4), 'Castle_Stone_Dark', 0.0)
    for k, (Mf, span) in enumerate(faces4(0, 0, POD_X, POD_Y)):
        masonry(pod, Mf, -span / 2, span / 2, -2.5, POD_H - 0.6, rnd, 2.8, (5.0, 9.0), 1.2, backing=False,
                skip=(lambda x, z, w_, h_: abs(x) < 21) if k == 0 else None)
        bevel_box(pod, Mf, (0, -0.4, POD_H - 0.3), (span + 1.6, 1.8, 0.9), 'Castle_Trim', 0.15)
    paving(walk, -POD_X + 1, POD_X - 1, -POD_Y + 1, POD_Y - 1, POD_H + 0.3, rnd, (9.0, 9.0),
           skip=lambda x, y: (abs(x) < TER_X and TER_Y0 < y < TER_Y1) or abs(abs(x) - WALL_X) < 4.5
           or abs(abs(y) - WALL_Y) < 4.5)
    M0 = I4
    y_bot = flight(walk, M0, 0, -POD_Y, POD_H, 0.0, 34.0, rnd, True, pod)
    for s in (-1, 1):
        brazier(pod, M0, s * 20.5, y_bot + 1.0, 0.0, lights, f'Fortress_Stair_Brazier_{s + 1}', 1.3)
        brazier(pod, M0, s * 20.5, -POD_Y + 1.5, POD_H, None, None, 1.0)
    # approach: wide paving, carved pillars, braziers and planters to the plateau road
    paving(walk, -17, 17, y_bot - 34, y_bot, 0.25, rnd, (6.0, 6.0))
    for s in (-1, 1):
        for k, y in enumerate((y_bot - 9, y_bot - 25)):
            castle.pillar(pod, Mt(s * 22.0, y), 2.4, 0.0, 12.0 + 2 * k, rnd, cap='ball')
        brazier(pod, M0, s * 22.0, y_bot - 33.0, 0.0, lights if s > 0 else None, 'Fortress_Approach_Brazier', 1.1)
        for y in (y_bot - 4, y_bot - 17, y_bot - 30):
            bevel_box(pod, Mt(s * 25.5, y), (0, 0, 1.0), (4.0, 4.0, 2.0), 'JF_Sandstone', 0.25)
            vines.append(('planter', Vector((s * 25.5, y, 2.0))))
    # --- curtain wall with height steps, towers, gatehouse
    gate_half = 11.0
    corners = [(-WALL_X, -WALL_Y), (WALL_X, -WALL_Y), (WALL_X, WALL_Y), (-WALL_X, WALL_Y)]
    segs = [((-WALL_X + 9.5, -WALL_Y), (-gate_half - 7.5, -WALL_Y), 18.0, 'Front_W'),
            ((gate_half + 7.5, -WALL_Y), (WALL_X - 9.5, -WALL_Y), 18.0, 'Front_E'),
            ((WALL_X, -WALL_Y + 9.5), (WALL_X, -6.5), 26.0, 'East_S'), ((WALL_X, 6.5), (WALL_X, WALL_Y - 9.5), 28.0, 'East_N'),
            ((WALL_X - 9.5, WALL_Y), (36.5, WALL_Y), 30.0, 'North_E'), ((29.5, WALL_Y), (-29.5, WALL_Y), 32.0, 'North_C'),
            ((-36.5, WALL_Y), (-WALL_X + 9.5, WALL_Y), 30.0, 'North_W'),
            ((-WALL_X, WALL_Y - 9.5), (-WALL_X, 6.5), 28.0, 'West_N'), ((-WALL_X, -6.5), (-WALL_X, -WALL_Y + 9.5), 26.0, 'West_S')]
    wwalk = Part('Fortress_Walk_Walls', 'Castle_Walls')
    for A, B, h, nm in segs:
        wp, _, Mwl, L = wall(nm, A, B, POD_H, POD_H + h, rnd, walk=wwalk)
        parts.append(wp)
        if nm in ('Front_W', 'Front_E', 'North_C'):            # banners and torches on the main faces
            red_banner(BAN[0], Mwl @ Matrix.Translation((L * 0.5, -1.4, POD_H + h - 3.0)), 5.0, 14.0)
        if nm in ('Front_W', 'Front_E'):
            wall_torch(wp, Mwl, L * 0.22, POD_H + h - 9.0)
            wall_torch(wp, Mwl, L * 0.78, POD_H + h - 9.0)
            vines.append((Mwl @ Vector((L * 0.38, -1.4, POD_H + h - 1)), 12))
    T_ = (('Corner_SW', -WALL_X, -WALL_Y, 9.0, 56.0, 22.0, ('front',), (36.0, 5.6, 16.0), 3),
          ('Corner_SE', WALL_X, -WALL_Y, 9.5, 62.0, 24.0, ('front',), (40.0, 5.6, 16.0), 4),
          ('Corner_NE', WALL_X, WALL_Y, 10.0, 82.0, 26.0, (), None, 3),
          ('Corner_NW', -WALL_X, WALL_Y, 8.5, 70.0, 23.0, (), None, 3),
          ('East', WALL_X, 0.0, 6.5, 50.0, 16.0, (), None, 2), ('West', -WALL_X, 0.0, 6.5, 46.0, 15.0, (), None, 2),
          ('North_E', 33.0, WALL_Y, 6.0, 54.0, 17.0, (), None, 2),
          ('North_W', -33.0, WALL_Y, 6.0, 50.0, 18.0, (), None, 2),
          ('Gate_W', -gate_half - 3.5, -WALL_Y, 7.0, 40.0, 16.0, ('front',), (30.0, 5.0, 13.0), 2),
          ('Gate_E', gate_half + 3.5, -WALL_Y, 7.0, 40.0, 16.0, ('front',), (30.0, 5.0, 13.0), 2))
    for nm, x, y, half, top, rh, glow, ban, tiers in T_:
        tp = tower(nm, x, y, half, POD_H + top, rnd, rh, glow=glow, banner=ban, lights=lights,
                   torch=nm.startswith('Gate'), roof_tiers=tiers)
        parts.append(tp)
        if nm in ('Corner_SW', 'Corner_NE', 'West'):
            vines.append((Vector((x + (half + 0.6) * (1 if x > 0 else -1) * 0.0, y - half - 0.6, POD_H + top * 0.55),
                          ), 16))
    # gatehouse arch between the gate towers, portcullis, inner passage floor
    gp = Part('Fortress_Gatehouse', 'Castle_Entrance')
    Mg = Mt(0, -WALL_Y - WALL_T / 2)
    arch_in = round_arch(14.0, 14.0, 12)
    rect_minus_arch(gp, Mg, -gate_half + 0.5, gate_half - 0.5, POD_H, POD_H + 28.0,
                    [(x, z + POD_H) for x, z in arch_in], 0.0, WALL_T, 'Castle_Stone_Dark')
    voussoirs(gp, Mg @ Matrix.Translation((0, 0, POD_H)), round_arch(19.0, 14.0, 12), arch_in, -1.0, 1.0, rnd, stone=3.4)
    bevel_box(gp, Mg, (0, -0.6, POD_H + 25.5), (2 * gate_half + 1.0, 2.0, 1.4), 'Castle_Trim', 0.2)
    bevel_box(gp, Mg, (0, -1.0, POD_H + 25.5), (2 * gate_half - 2.0, 0.3, 0.5), 'Gold', 0.05)
    crenels(gp, Mg, -gate_half + 0.5, gate_half - 0.5, POD_H + 28.0, WALL_T, rnd)
    masonry(gp, Mg, -gate_half + 0.5, gate_half - 0.5, POD_H, POD_H + 25.0, rnd, 3.0, (3.5, 6.0), 1.0, backing=False,
            skip=lambda x, z, w_, h_: castle.inside([(x_, z_ + POD_H) for x_, z_ in round_arch(21.0, 14.0, 12)], x, z))
    red_banner(BAN[0], Mg @ Matrix.Translation((0, -1.6, POD_H + 24.6)), 6.0, 6.5)
    crest(gp, Mg @ Matrix.Translation((0, -1.4, POD_H + 21.2)), 2.6)
    for i in range(7):                                         # raised portcullis
        x = -6.0 + i * 2.0
        gp.box(Mg @ Vector((x, 1.5, POD_H + 18.5)), (0.45, 0.45, 6.0), 'JF_Iron')
        gp.cone(Mg @ Vector((x, 1.5, POD_H + 15.5)), 0.4, -1.2, 'JF_Iron', 4)
    for zz in (17.0, 20.0):
        gp.box(Mg @ Vector((0, 1.5, POD_H + zz)), (13.0, 0.4, 0.4), 'JF_Iron')
    parts.append(gp)
    # courtyard: central paved way, statues on pedestals, planters with shrubs, guard platforms
    yard = Part('Fortress_Courtyard', 'Castle_Main')
    for s in (-1, 1):
        for k, y in enumerate((-50.0, -36.0, -22.0)):
            bevel_box(yard, Mt(s * 15.0, y), (0, 0, POD_H + 1.2), (4.4, 4.4, 2.4), 'Castle_Trim', 0.25)
            castle.pillar(yard, Mt(s * 15.0, y), 2.0, POD_H + 2.4, 8.0, rnd, cap='ball')
        for y in (-44.0, -29.0):
            bevel_box(yard, Mt(s * 26.0, y), (0, 0, POD_H + 1.0), (8.0, 5.0, 2.0), 'JF_Sandstone', 0.25)
            vines.append(('planter', Vector((s * 26.0, y, POD_H + 2.0))))
        bevel_box(yard, Mt(s * 66.0, -40.0), (0, 0, POD_H + 4.0), (14.0, 12.0, 8.0), 'Castle_Stone_Dark', 0.3)   # guard
        crenels(yard, Mt(s * 66.0, -46.0), -7.0, 7.0, POD_H + 8.0, 1.2, rnd)                       # platforms
        brazier(yard, I4, s * 66.0, -40.0, POD_H + 8.0, lights if s < 0 else None, 'Fortress_Yard_Brazier')
    parts.append(yard)
    # --- inner terrace (keep platform) and its staircase
    ter = Part('Fortress_Terrace', 'Castle_Main')
    tw = Part('Fortress_Walk_Terrace', 'Castle_Main')
    bevel_box(ter, I4, (0, (TER_Y0 + TER_Y1) / 2, (POD_H + TER_H) / 2), (2 * TER_X - 0.6, TER_Y1 - TER_Y0 - 0.6,
              TER_H - POD_H), 'Castle_Stone_Dark', 0.0)
    for k, (Mf, span) in enumerate(faces4(0, (TER_Y0 + TER_Y1) / 2, TER_X, (TER_Y1 - TER_Y0) / 2)):
        masonry(ter, Mf, -span / 2, span / 2, POD_H, TER_H - 0.8, rnd, 2.4, (4.0, 7.0), 1.0, backing=False,
                skip=(lambda x, z, w_, h_: abs(x) < 15) if k == 0 else None)
        bevel_box(ter, Mf, (0, -0.4, TER_H - 0.4), (span + 1.2, 1.6, 0.8), 'Castle_Trim', 0.15)
        if k == 0:
            balustrade(ter, Mf @ Matrix.Translation((0, 0.2, 0)), -span / 2, -15.5, TER_H, rnd, 3.0, 8.0)
            balustrade(ter, Mf @ Matrix.Translation((0, 0.2, 0)), 15.5, span / 2, TER_H, rnd, 3.0, 8.0)
    paving(tw, -TER_X + 1, TER_X - 1, TER_Y0 + 1, KEEP_Y - 21.0, TER_H + 0.3, rnd, (6.0, 6.0))
    flight(tw, I4, 0, TER_Y0, TER_H, POD_H, 26.0, rnd, True, ter)
    for s in (-1, 1):
        brazier(ter, I4, s * 17.5, TER_Y0 - 1.0 - (TER_H - POD_H) / RISE * TREAD, POD_H, None, None, 0.9)
        brazier(ter, I4, s * 32.0, TER_Y0 + 3.0, TER_H, lights if s > 0 else None, 'Fortress_Terrace_Brazier', 1.2)
    parts += [ter, tw]
    # --- the keep
    kp, ent, apex = build_keep(rnd, lights, vines)
    parts += [kp, ent, pod, walk, wwalk, ROOF[0], BAN[0]]
    # --- the two jungle guardians flanking the terrace stairs
    for s in (-1, 1):
        g = Part(f'Fortress_Guardian_Statue_{"LR"[s > 0]}', 'Castle_Guardian_Statues')
        guardian(g, I4, rnd, s)                                # drawn at the origin, then placed 1.4x larger
        bmesh.ops.transform(g.bm, matrix=Mt(s * 22.0, TER_Y0 + 6.5, TER_H) @ Matrix.Diagonal((1.4, 1.4, 1.4, 1.0)),
                            verts=g.bm.verts)
        parts.append(g)

    # --- overgrowth: vines, moss and roots on selected walls; shrubs in the planters
    from foliage import vine
    planters = []
    vp = Part('Fortress_Vines', 'Jungle_Vines')
    for item in vines:
        if item[0] == 'planter':
            q = item[1]
            planters.append(q)
            continue
        top, ln = item
        for k in range(4):
            vine(vp, top + Vector((rnd.uniform(-3, 3), 0, rnd.uniform(-1, 0))), ln * rnd.uniform(0.6, 1.0), rnd, 1.6)
        for k in range(5):
            vp.ico(top + Vector((rnd.uniform(-4, 4), -0.2, rnd.uniform(-ln, 0))), rnd.uniform(0.6, 1.2),
                   rnd.choice(('Moss', 'Leaves_Mid')), 1, (1.3, 0.4, 0.9), smooth=False)
    for k in range(26):                                        # roots and moss round the podium foot
        side = rnd.randrange(4)
        t = rnd.uniform(-0.9, 0.9)
        x, y = [(t * POD_X, -POD_Y - 0.5), (POD_X + 0.5, t * POD_Y), (t * POD_X, POD_Y + 0.5), (-POD_X - 0.5, t * POD_Y)][side]
        if side == 0 and abs(x) < 26:
            continue
        vp.ico(Vector((x, y, rnd.uniform(-0.5, 2.5))), rnd.uniform(1.2, 2.4), rnd.choice(('Moss', 'Trunk', 'Leaves_Mid')),
               1, (1.6, 0.8, 0.7), smooth=False)
    parts.append(vp)
    # --- place: scale every part round the keep pad and finish
    for part in parts:
        bmesh.ops.transform(part.bm, matrix=Mw, verts=part.bm.verts)
        part.finish()
    for name, q, e in lights[:16]:                             # a limited number of real lights
        L = bpy.data.lights.new(name, 'POINT')
        L.color = (1.0, 0.55, 0.22); L.energy = e * SCALE; L.shadow_soft_size = 2.0
        o = bpy.data.objects.new(name, L)
        o.location = Mw @ q
        bpy.data.collections[LIGHTS].objects.link(o)
    dress_grounds(T, Mw, y_bot, rnd)
    dress_castle(Mw, rnd, planters)
    dress_island(T, random.Random(1717))
    gate = Mw @ Vector((0, y_bot - 34, 0))
    door = Mw @ Vector((0, KEEP_Y - 21.0 - 4.0, TER_H))
    return dict(keep=(kx, ky, kz), gate=tuple(gate), keep_door=tuple(door), height=apex * SCALE,
                footprint=(2 * POD_X * SCALE, 2 * POD_Y * SCALE))


def dress_castle(Mw, rnd, planters):
    """jungle on the architecture itself (reusable assets, linked duplicates): tropical plants in the planters,
    creeping vines up selected walls and tower faces, hanging vine clusters from wall tops and ledges, plants on the
    wall walks and the keep balcony, palms on the keep's lower roof - windows, banners and the entrance stay clear"""
    from floor1_detail import place
    S = SCALE

    def put(cat, kind, x, y, z, rot, sc):
        q = Mw @ Vector((x, y, z))
        place(cat, kind, q.x, q.y, q.z, rot, sc)
    for q in planters:
        for k in range(2):
            put('Foliage', rnd.choice(('Monstera_Plant', 'Tropical_Plant', 'Red_Jungle_Plant', 'Monstera_Plant')),
                q.x + rnd.uniform(-1, 1), q.y + rnd.uniform(-0.8, 0.8), q.z - 0.2, rnd.uniform(0, TAU), rnd.uniform(3.2, 4.2))
    creep = [(-27.0, 8.1, TER_H, 0.0), (27.0, 8.1, TER_H, 0.0), (-31.2, 26.0, TER_H, -math.pi / 2),
             (31.2, 36.0, TER_H, math.pi / 2), (-WALL_X - 3.0, -WALL_Y - 9.7, POD_H, 0.0),
             (WALL_X + 4.0, -WALL_Y - 10.2, POD_H, 0.0), (WALL_X + 7.2, -2.0, POD_H, math.pi / 2),
             (-WALL_X - 7.2, 2.5, POD_H, -math.pi / 2), (33.0, WALL_Y + 6.7, POD_H, math.pi),
             (-WALL_X + 1.0, WALL_Y + 9.2, POD_H, math.pi), (-46.0, -WALL_Y - 3.6, POD_H, 0.0),
             (52.0, -WALL_Y - 3.6, POD_H, 0.0), (-24.6, KEEP_Y - 17.0, TER_H + 28.0, 0.0, 3.4),
             (24.6, KEEP_Y - 17.0, TER_H + 28.0, 0.0, 3.4), (-12.2, KEEP_Y - 11.6, TER_H + 52.5, 0.0, 3.0),
             (24.0, KEEP_Y + 4.0, TER_H + 28.0, math.pi / 2)]
    for x, y, z, rot, *sc in creep:                            # (keep vines sit on the corners, clear of the windows)
        put('Cliffs', 'Creeping_Vines', x, y, z, rot, sc[0] if sc else rnd.uniform(5.0, 6.2))
    for x, y, z, sc in ((-58.0, -WALL_Y - 3.4, POD_H + 18.0, 2.6), (40.0, -WALL_Y - 3.4, POD_H + 18.0, 2.8),
                        (-23.0, KEEP_Y - 17.5, 64.0, 2.4), (23.0, KEEP_Y - 17.5, 64.0, 2.2),
                        (WALL_X + 3.4, 34.0, POD_H + 28.0, 3.0)):
        put('Cliffs', 'Vine_Cluster', x, y, z, 0.0 if abs(x) < WALL_X else math.pi / 2, sc)
    for x, y in ((-72.0, -WALL_Y), (72.0, -WALL_Y), (-WALL_X, -50.0), (WALL_X, 50.0), (-WALL_X, 40.0)):
        put('Foliage', rnd.choice(('Tropical_Plant', 'Jungle_Bush', 'Monstera_Plant')), x, y, POD_H + 24.0 if y == -WALL_Y
            else POD_H + 26.0, rnd.uniform(0, TAU), 2.4)
    for x in (-9.5, 9.5):                                       # balcony planters
        put('Foliage', 'Tropical_Plant', x, KEEP_Y - 21.0 - 5.0, TER_H + 18.5 + 7.2, rnd.uniform(0, TAU), 1.8)
    for x, y in ((-24.0, KEEP_Y - 18.0), (24.0, KEEP_Y - 18.0), (-26.0, KEEP_Y + 16.0), (26.0, KEEP_Y + 16.0)):
        put('Trees', 'Tropical_Palm', x, y, TER_H + 28.0 + 1.2, rnd.uniform(0, TAU), rnd.uniform(2.2, 2.8))


def dress_grounds(T, Mw, y_bot, rnd):
    """controlled jungle round the fortress: clusters of broad trees, palms, tropical plants, bushes and flowers on
    the open plateau ground round the podium - the approach, the walls' outline and the roofs stay clear"""
    from floor1_detail import place, ground_z, grid_index
    inv = Mw.inverted()
    n = 0
    for k in range(700):
        a = rnd.uniform(0, TAU)
        r = rnd.uniform(1.04, 1.9)
        q = Mw @ Vector((math.cos(a) * POD_X * r, math.sin(a) * POD_Y * r, 0))
        l = inv @ q
        if abs(l.x) < POD_X + 4 and abs(l.y) < POD_Y + 4:
            continue
        if abs(l.x) < 34 and l.y < -POD_Y + 6:                  # the approach and its view of the gate stay open
            continue
        i, j = grid_index(T, q.x, q.y)
        if not T.land[i, j] or T.path_e[i, j] < 12 or T.slope[i, j] > 0.6 or T.edge_d[i, j] < 40:
            continue
        z = float(ground_z(T, q.x, q.y))
        near = abs(l.x) < POD_X + 22 and abs(l.y) < POD_Y + 22
        u = rnd.random()
        if u < (0.10 if near else 0.28):
            kind = rnd.choice(('Jungle_Canopy_Tree', 'Tropical_Palm', 'Banana_Tree', 'Flowering_Jungle_Tree',
                               'Ancient_Jungle_Tree', 'Tropical_Palm', 'Jungle_Canopy_Tree'))
            place('Trees', kind, q.x, q.y, z - 1, rnd.uniform(0, TAU), rnd.uniform(2.6, 3.8))
        elif u < 0.62:
            place('Foliage', rnd.choice(('Monstera_Plant', 'Jungle_Bush', 'Tropical_Plant', 'Leafy_Shrub', 'Fern',
                                         'Bamboo_Cluster' if not near else 'Jungle_Bush')), q.x, q.y, z,
                  rnd.uniform(0, TAU), rnd.uniform(2.2, 3.4))
        elif u < 0.8:
            place('Foliage', rnd.choice(('Pink_Jungle_Plant', 'Red_Jungle_Plant', 'Purple_Accent_Plant', 'Ground_Cover',
                                         'Jungle_Grass')), q.x, q.y, z, rnd.uniform(0, TAU), rnd.uniform(2.0, 3.0))
        else:
            place('Rocks', rnd.choice(('Mossy_Boulder', 'Jungle_Rock_Large', 'Flat_Rock', 'Root_Rock')), q.x, q.y, z - 1.5,
                  rnd.uniform(0, TAU), rnd.uniform(1.8, 3.0))
        n += 1
    # the older civilisation under the fortress: ancient pillars and obelisks along the approach, ruined walls,
    # statues and buried blocks round the podium corners (maintained near the gate, abandoned further out)
    for s in (-1, 1):
        for y, kind, sc in ((y_bot - 46, 'Ancient_Pillar', 3.4), (y_bot - 62, 'Obelisk', 3.2), (y_bot - 80, 'Ancient_Pillar', 3.4)):
            q = Mw @ Vector((s * 26.0, y, 0))
            place('Ruins', kind, q.x, q.y, float(ground_z(T, q.x, q.y)) - 0.4, 0.0, sc)
        for x, y, kind in ((POD_X + 16, -POD_Y + 6, 'Jungle_Statue'), (POD_X + 26, 8, 'Ruin_Wall_Jungle'),
                           (POD_X + 18, POD_Y + 14, 'Buried_Blocks'), (POD_X + 34, -40, 'Broken_Pillar'),
                           (POD_X + 30, POD_Y - 12, 'Overgrown_Arch')):
            q = Mw @ Vector((s * x, y, 0))
            i, j = grid_index(T, q.x, q.y)
            if T.land[i, j] and T.edge_d[i, j] > 40:
                place('Ruins', kind, q.x, q.y, float(ground_z(T, q.x, q.y)) - 0.5,
                      (math.pi / 2 if s > 0 else -math.pi / 2) if kind != 'Buried_Blocks' else rnd.uniform(0, TAU), 3.2)
    return n


# ---------------------------------------------------------------- jungle plants for the scatter
def palm_tree(p, rnd):
    """curved trunk of stacked rings, a crown of drooping fronds and a few coconuts (origin at the ground)"""
    from foliage import tube
    n = 9
    lean = Vector((rnd.uniform(0.6, 1.0), rnd.uniform(-0.3, 0.3), 0))
    pts = [Vector((0, 0, 0)) + lean * (0.12 * i * i / n) + Vector((0, 0, 1.55 * i)) for i in range(n + 1)]
    tube(p, pts, [0.75 - 0.03 * i for i in range(n + 1)], 'Palm_Trunk', 7)
    for i in range(1, n):
        p.torus(pts[i], 0.72 - 0.03 * i, 0.12, 'Trunk', 10, 4)
    top = pts[-1]
    for k in range(9):
        a = TAU * k / 9 + rnd.uniform(-0.15, 0.15)
        d = Vector((math.cos(a), math.sin(a), 0))
        prev = top
        for j in range(4):
            t = (j + 1) / 4
            q = top + d * (5.6 * t) + Vector((0, 0, 1.4 * math.sin(math.pi * t * 0.8) - 2.2 * t * t))
            side = Vector((-d.y, d.x, 0)) * (1.1 * (1 - t * 0.6))
            p.hexa([prev - side, prev + side, q + side * 0.7, q - side * 0.7] +
                   [v + Vector((0, 0, 0.12)) for v in (prev - side, prev + side, q + side * 0.7, q - side * 0.7)],
                   'Palm_Leaf' if k % 2 else 'Leaves_Mid')
            prev = q
    for k in range(3):
        a = TAU * k / 3
        p.ico(top + Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, -0.6)), 0.45, 'Trunk', 1)


def tropical_plant(p, rnd):
    """clump of big broad leaves on short stems"""
    for k in range(7):
        a = TAU * k / 7 + rnd.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), 0))
        L = rnd.uniform(2.4, 3.4)
        base = Vector((0, 0, 0.2))
        tip = d * L + Vector((0, 0, rnd.uniform(1.2, 2.4)))
        mid = base + (tip - base) * 0.5 + Vector((0, 0, 0.6))
        side = Vector((-d.y, d.x, 0)) * L * 0.32
        mat = 'Tropical_Leaf' if k % 2 else 'Tropical_Leaf_Light'
        for a_, b_ in ((base, mid), (mid, tip)):
            w0 = side * (0.25 if a_ is base else 1.0)
            w1 = side * (1.0 if b_ is mid else 0.08)
            q = [a_ - w0, a_ + w0, b_ + w1, b_ - w1]
            p.hexa(q + [v + Vector((0, 0, 0.1)) for v in q], mat)


def build_fortress_assets():
    build_fortress_materials()
    from floor1_detail import _lib
    _lib('Palm_Tree', palm_tree, random.Random(501))
    _lib('Tropical_Plant', tropical_plant, random.Random(502))


# ---------------------------------------------------------------- the island round the fortress (reference sheet)
def dress_island(T, rnd):
    """emblem plaza in front of the castle stairs, the turquoise lagoon's shore (rocks, reeds, lily pads, palms, a
    small rock islet and a wooden pier) and ancient ruins along the jungle paths"""
    from floor1_detail import place, ground_z, grid_index
    gz = lambda x, y: float(ground_z(T, x, y))
    # --- the circular emblem plaza (the boss arena) at the foot of the approach
    ax, ay = F.px(*F.MAIN_BOSS[1:])
    az = gz(ax, ay)
    pz = Part('Fortress_Plaza', 'Castle_Main')
    R = 118.0
    for r0, r1, mat in ((0, 26, 'Castle_Trim'), (26, 30, 'Gold'), (30, 92, None), (92, 98, 'Castle_Trim'),
                        (98, R, None)):
        n = max(8, int(TAU * r1 / 26))
        for k in range(n):
            a0, a1 = TAU * k / n + 0.003, TAU * (k + 1) / n - 0.003
            pz.ring_sector(r0 + 0.4, r1 - 0.4, a0, a1, az + 0.3, az + 1.3 + rnd.uniform(0, 0.25),
                           mat or rnd.choice(('JF_Sandstone_Light', 'Castle_Stone_Warm', 'JF_Sandstone', 'JF_Stone_Moss')),
                           2, (ax, ay))
    pz.ring_sector(R, R + 6, 0, TAU, az - 1.0, az + 2.4, 'Castle_Trim', 64, (ax, ay))
    crest(pz, Matrix.Translation((ax, ay, az + 1.4)) @ Matrix.Rotation(-math.pi / 2, 4, 'X') @
          Matrix.Diagonal((1, 1, 1, 1)), 34.0)
    pz.finish()
    for k in range(8):                                        # braziers round the rim
        a = TAU * k / 8 + TAU / 16
        q = (ax + math.cos(a) * (R + 14), ay + math.sin(a) * (R + 14))
        if T.path_e[grid_index(T, *q)] > 0:
            place('Ruins', 'Ancient_Pillar', q[0], q[1], gz(*q) - 0.4, a, 2.4)
    # --- lagoon shore
    li = next(k for k, l in enumerate(F.LAKES) if l[0] == 'Fortress_Lagoon')
    poly = [F.px(*p) for p in F.LAKES[li][1]]
    lc = Vector((sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly), 0))
    zw = F.LAKES[li][2]
    edge = []
    for k in range(90):
        a = TAU * k / 90
        u = Vector((math.cos(a), math.sin(a), 0))
        r = 30.0
        while r < 2400:
            i, j = grid_index(T, *(lc + u * r).xy)
            if T.lake_f[i, j] >= 1.0 or T.lake_i[i, j] != li:
                break
            r += 12.0
        edge.append((a, u, r))
    for a, u, r in edge:
        q = lc + u * r
        on_path = T.path_e[grid_index(T, q.x, q.y)] < 8
        roll = rnd.random()
        if roll < 0.35:
            place('Rocks', rnd.choice(('Mossy_Boulder', 'Flat_Rock', 'Jungle_Rock_Large')), q.x, q.y, zw - 3,
                  rnd.uniform(0, TAU), rnd.uniform(2.0, 3.6))
        elif roll < 0.7:
            qq = lc + u * (r - 18)
            place('Water', 'Reeds', qq.x, qq.y, zw - 0.5, rnd.uniform(0, TAU), rnd.uniform(2.4, 3.6))
        if not on_path and rnd.random() < 0.28:
            qq = lc + u * (r + rnd.uniform(50, 110))
            if T.path_e[grid_index(T, qq.x, qq.y)] > 20:
                place('Trees', rnd.choice(('Tropical_Palm', 'Tropical_Palm', 'Banana_Tree', 'Flowering_Jungle_Tree')),
                      qq.x, qq.y, gz(qq.x, qq.y) - 1, rnd.uniform(0, TAU), rnd.uniform(2.6, 3.6))
        if not on_path and rnd.random() < 0.35:
            qq = lc + u * (r + rnd.uniform(20, 45))
            place('Foliage', rnd.choice(('Pink_Jungle_Plant', 'Red_Jungle_Plant', 'Monstera_Plant', 'Tropical_Plant',
                                         'Jungle_Grass')), qq.x, qq.y, gz(qq.x, qq.y), rnd.uniform(0, TAU),
                  rnd.uniform(2.0, 3.0))
    for k in range(70):                                       # lily pads (some flowering)
        a = rnd.uniform(0, TAU); r = rnd.uniform(0.15, 0.85)
        _, u, rr = min(edge, key=lambda e: abs((e[0] - a + math.pi) % TAU - math.pi))
        q = lc + u * rr * r
        place('Water', 'Lily_Pads_Flower' if rnd.random() < 0.35 else 'Lily_Pads', q.x, q.y, zw + 0.05,
              rnd.uniform(0, TAU), rnd.uniform(3.0, 4.6))
    # a small rock islet with a palm (not an island: a rock outcrop in the water) and a wooden pier
    a_, u_, r_ = edge[30]
    q = lc + u_ * r_ * 0.45
    for k in range(5):
        o = Vector((rnd.uniform(-30, 30), rnd.uniform(-22, 22), 0))
        place('Rocks', rnd.choice(('Mossy_Boulder', 'Jungle_Rock_Large', 'Flat_Rock')), q.x + o.x, q.y + o.y, zw - 6,
              rnd.uniform(0, TAU), rnd.uniform(3.0, 4.6))
    place('Trees', 'Tropical_Palm', q.x, q.y, zw + 2, 0.4, 3.0)
    place('Foliage', 'Tropical_Plant', q.x + 14, q.y - 6, zw + 2, 1.0, 2.6)
    a_, u_, r_ = edge[62]
    q = lc + u_ * (r_ + 8)
    place('Props', 'Fishing_Jetty', q.x, q.y, zw - 0.6, math.atan2(-u_.y, -u_.x) - math.pi / 2, 3.0)
    # --- ancient ruins along the island's paths (alternate sides, every few hundred studs)
    kinds = ('Overgrown_Arch', 'Ancient_Pillar', 'Broken_Pillar', 'Obelisk', 'Ruin_Wall_Jungle', 'Jungle_Statue',
             'Ancient_Pillar', 'Buried_Blocks')
    n = 0
    for name, kind, w, pts in T.paths:
        if name not in ('Fortress_Grand_Ramp', 'Fortress_Canyon', 'Lagoon_East_Trail', 'Lagoon_West_Trail',
                        'Swamp_Cliff_Trail', 'Fortress_North_Road'):
            continue
        acc, sgn = 0.0, 1
        for A, B in zip(pts, pts[1:]):
            A, B = Vector(A), Vector(B)
            acc += (B - A).xy.length
            if acc < 380:
                continue
            acc = rnd.uniform(-60, 60)
            t = (B - A).xy.normalized()
            nrm = Vector((-t.y, t.x))
            q = B.xy + nrm * sgn * (w / 2 + rnd.uniform(28, 46))
            i, j = grid_index(T, q.x, q.y)
            if not T.land[i, j] or T.edge_d[i, j] < 60 or T.lake_f[i, j] < 1.2 or T.path_e[i, j] < 10:
                continue
            a = F.AREA_INDEX.get('Jungle_Fortress')
            k = kinds[n % len(kinds)]
            place('Ruins', k, q.x, q.y, gz(q.x, q.y) - 0.5, math.atan2(t.y, t.x) + (math.pi / 2 if k == 'Overgrown_Arch' else 0),
                  rnd.uniform(2.8, 3.6))
            place('Foliage', rnd.choice(('Fern', 'Jungle_Grass', 'Leafy_Shrub')), q.x + 10, q.y + 6, gz(q.x, q.y),
                  rnd.uniform(0, TAU), 2.4)
            sgn = -sgn; n += 1
    return n
