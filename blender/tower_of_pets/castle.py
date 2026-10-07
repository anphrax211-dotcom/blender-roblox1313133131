"""CASTLE BASE - the lower tower / main entrance rebuilt from the castle-base reference with real masonry.

Everything is geometry, not a brick texture:
  * walls are courses of individually chamfered stone blocks (running bond, varied width/height/depth/bevel)
    in front of a dark core, so the seams read as recessed grooves
  * corners get alternating quoin stones, arches are rings of separate voussoirs with a keystone
  * pillars are stacked from base, block shaft, banded middle, capital and cap
  * trims, cornices, gold strips, balustrades, steps and flagstones are separate bevelled pieces

Modular kit (CASTLE_KIT in the asset library, also used here as linked duplicates):
  Stone_Block_Small / _Medium / _Large, Wall_Straight, Wall_Corner, Wall_Trim, Pillar_Base, Pillar_Main,
  Pillar_Top, Arch_Small, Arch_Large, Decorative_Trim, Gold_Trim, Stair_Straight, Balcony, Ledge, Banner,
  Lantern (Castle_Lantern), Balustrade, Cat_Statue, Topiary_Cone
Build helpers take a 4x4 matrix M that maps a local frame (x across, z up, front face at y = 0 facing -Y,
the wall body toward +Y) into the world, so the same code builds the gatehouse, arcades and tower faces.
"""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
from common import (Part, MATS, mat_plain, mat_noise, coll, inst, ASSETS, paw, M_front, pointed_arch, round_arch,
                    TAU)

C = 'TOWER_ENTRANCE'
KIT = 'CASTLE_KIT'
STONES = ('Castle_Stone', 'Castle_Stone', 'Castle_Stone_Light', 'Castle_Stone_Warm')


# ---------------------------------------------------------------- materials -
def build_castle_materials():
    mat_noise('Castle_Stone', (0.62, 0.53, 0.49), (0.67, 0.58, 0.53), 0.8, 0.15, 0.1, 1.2)
    mat_noise('Castle_Stone_Light', (0.70, 0.62, 0.57), (0.74, 0.66, 0.61), 0.8, 0.15, 0.1, 1.2)
    mat_noise('Castle_Stone_Warm', (0.68, 0.56, 0.46), (0.72, 0.60, 0.50), 0.8, 0.15, 0.1, 1.2)
    mat_noise('Castle_Stone_Dark', (0.45, 0.38, 0.36), (0.50, 0.42, 0.39), 0.85, 0.15, 0.1, 1.2)
    mat_plain('Castle_Seam', (0.20, 0.16, 0.15), 0.9)
    mat_plain('Castle_Trim', (0.78, 0.71, 0.63), 0.7)
    mat_plain('Castle_Statue', (0.62, 0.59, 0.58), 0.7)


# ---------------------------------------------------------------- geometry --
def bevel_box(p, M, c, s, mat, bev=0.18):
    """chamfered box (24 verts / 44 tris) centred at local c with size s, transformed by M"""
    hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
    b = min(bev, hx * 0.45, hy * 0.45, hz * 0.45)
    cx, cy, cz = c
    bm = p.bm
    V = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                for ax, co in (('x', (sx * hx, sy * (hy - b), sz * (hz - b))),
                               ('y', (sx * (hx - b), sy * hy, sz * (hz - b))),
                               ('z', (sx * (hx - b), sy * (hy - b), sz * hz))):
                    V[(sx, sy, sz, ax)] = bm.verts.new(M @ Vector((cx + co[0], cy + co[1], cz + co[2])))
    F = []
    for s_ in (-1, 1):
        F.append([V[(s_, a, b_, 'x')] for a, b_ in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        F.append([V[(a, s_, b_, 'y')] for a, b_ in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        F.append([V[(a, b_, s_, 'z')] for a, b_ in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for sy in (-1, 1):
        for sz in (-1, 1):
            F.append([V[(-1, sy, sz, 'y')], V[(1, sy, sz, 'y')], V[(1, sy, sz, 'z')], V[(-1, sy, sz, 'z')]])
    for sx in (-1, 1):
        for sz in (-1, 1):
            F.append([V[(sx, -1, sz, 'x')], V[(sx, 1, sz, 'x')], V[(sx, 1, sz, 'z')], V[(sx, -1, sz, 'z')]])
        for sy in (-1, 1):
            F.append([V[(sx, sy, -1, 'x')], V[(sx, sy, 1, 'x')], V[(sx, sy, 1, 'y')], V[(sx, sy, -1, 'y')]])
            for sz in (-1, 1):
                F.append([V[(sx, sy, sz, 'x')], V[(sx, sy, sz, 'y')], V[(sx, sy, sz, 'z')]])
    faces = [bm.faces.new(f) for f in F]
    p._faces(faces, mat)


def inside(poly, x, z):
    """point-in-polygon (even-odd) for a closed (x, z) polygon"""
    n, c = len(poly), False
    for i in range(n):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
            c = not c
    return c


def masonry(p, M, x0, x1, z0, z1, rnd, course=3.2, bw=(4.5, 7.5), depth=1.4, gap=0.14, bev=(0.16, 0.24),
            mats=STONES, skip=None, proud=0.12, backing=True):
    """courses of chamfered blocks in running bond on the local XZ plane (front y = 0).
    skip(x, z, w, h) -> True drops a block (openings); backing adds a dark seam slab behind."""
    if backing:
        bevel_box(p, M, ((x0 + x1) / 2, depth * 0.55 + 0.25, (z0 + z1) / 2), (x1 - x0, depth * 1.1, z1 - z0),
                  'Castle_Seam', 0.0)
    z, row = z0, 0
    while z < z1 - 0.3:
        h = min(course * rnd.uniform(0.85, 1.15), z1 - z)
        if z1 - (z + h) < course * 0.4:
            h = z1 - z
        x = x0 - (rnd.uniform(0.3, 0.7) * bw[0] if row % 2 else 0)
        while x < x1 - 0.05:
            w = rnd.uniform(*bw)
            a, b = max(x, x0), min(x + w, x1)
            if b - a > 0.6 and not (skip and skip((a + b) / 2, z + h / 2, b - a, h)):
                dy = rnd.uniform(-proud, proud * 0.4)
                bevel_box(p, M, ((a + b) / 2, depth / 2 + dy - 0.35, z + h / 2),
                          (b - a - gap, depth, h - gap), rnd.choice(mats), rnd.uniform(*bev))
            x += w
        z += h
        row += 1


def quoins(p, M, z0, z1, rnd, long=5.5, short=3.0, course=3.2, side=1, proud=0.35, mat='Castle_Stone_Light'):
    """alternating long/short corner stones wrapping a corner at local x = 0 (wall runs toward +x*side,
    return wall runs toward +y)"""
    z, k = z0, 0
    while z < z1 - 0.3:
        h = min(course, z1 - z)
        if k % 2 == 0:
            c = (side * (long / 2 - proud), short / 2 - proud, z + h / 2)
            s = (long, short, h - 0.14)
        else:
            c = (side * (short / 2 - proud), long / 2 - proud, z + h / 2)
            s = (short, long, h - 0.14)
        bevel_box(p, M, c, s, mat, 0.22)
        z += h; k += 1


def resample(pts, n):
    pts = [Vector((x, 0, z)) for x, z in pts]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg)
    out = []
    for k in range(n + 1):
        d = total * k / n
        i = 0
        while i < len(seg) - 1 and d > seg[i]:
            d -= seg[i]; i += 1
        t = min(1.0, d / seg[i]) if seg[i] else 0
        out.append(pts[i].lerp(pts[i + 1], t))
    return out


def voussoirs(p, M, outer, inner, y0, y1, rnd, stone=4.2, mat=None, gap=0.16, bev=0.3, keystone=True,
              backing=True):
    """ring of separate wedge stones between two open arch polylines (local XZ), front at y0, back at y1"""
    L = sum((Vector(outer[i + 1]) - Vector(outer[i])).length for i in range(len(outer) - 1))
    n = max(3, int(L / stone)) | 1                                   # odd -> a centre keystone
    O, I = resample(outer, n), resample(inner, n)
    if backing:
        for k in range(n):
            q = [O[k], O[k + 1], I[k + 1], I[k]]
            pts = [M @ Vector((v.x, y1 - 0.25, v.z)) for v in q] + [M @ Vector((v.x, y1 + 0.2, v.z)) for v in q]
            p.hexa(pts, 'Castle_Seam')
    for k in range(n):
        ga = gap / max(1e-3, (O[k + 1] - O[k]).length)
        o0, o1 = O[k].lerp(O[k + 1], ga), O[k + 1].lerp(O[k], ga)
        i0, i1 = I[k].lerp(I[k + 1], ga), I[k + 1].lerp(I[k], ga)
        key = keystone and k == n // 2
        f = y0 - (0.7 if key else rnd.uniform(0, 0.12))
        if key:                                                     # keystone pokes out above the ring
            up = (o0 + o1) / 2 - (i0 + i1) / 2
            o0, o1 = o0 + up * 0.25, o1 + up * 0.25
        cen = (o0 + o1 + i0 + i1) / 4
        back = [o0, o1, i1, i0]
        front = [v.lerp(cen, bev / max(1e-3, (v - cen).length)) for v in back]
        pts = [M @ Vector((v.x, y1, v.z)) for v in back] + [M @ Vector((v.x, f, v.z)) for v in front]
        p.hexa(pts, mat or rnd.choice(('Castle_Stone_Light', 'Castle_Stone_Light', 'Castle_Trim')))


def frame_strip(p, M, outer, inner, y0, y1, mat):
    for i in range(len(outer) - 1):
        q = [outer[i], outer[i + 1], inner[i + 1], inner[i]]
        p.hexa([M @ Vector((x, y0, z)) for x, z in q] + [M @ Vector((x, y1, z)) for x, z in q], mat)


def trim_run(p, M, x0, x1, z, rnd=None, h=1.6, out=1.0, steps=2, mat='Castle_Trim', gold=False):
    """stepped cornice / string course along local x at height z (protrudes toward -y)"""
    for k in range(steps):
        hh = h / steps
        bevel_box(p, M, ((x0 + x1) / 2, -out * (k + 1) / steps / 2 + 0.5, z + hh * (k + 0.5)),
                  (x1 - x0 + out * (k + 1) / steps * 0.6, out * (k + 1) / steps + 1.0, hh), mat, 0.14)
    if gold:
        bevel_box(p, M, ((x0 + x1) / 2, -out - 0.05, z + h * 0.5), (x1 - x0, 0.3, 0.35), 'Gold', 0.08)


def pillar(p, M, w, z0, h, rnd, band=0.55, cap='pyramid', panel=True):
    """multi-part pillar centred at local (0, 0): base, block shaft, middle band, capital, cap"""
    bevel_box(p, M, (0, 0, z0 + 0.8), (w + 2.4, w + 2.4, 1.6), 'Castle_Trim', 0.25)
    bevel_box(p, M, (0, 0, z0 + 2.2), (w + 1.2, w + 1.2, 1.2), 'Castle_Stone_Light', 0.22)
    z, k = z0 + 2.8, 0
    zb = z0 + h * band
    top = z0 + h - 4.5
    while z < top - 0.4:
        ch = min(rnd.uniform(2.8, 3.6), top - z)
        if abs(z - zb) < 2.0:                               # banded middle section
            bevel_box(p, M, (0, 0, z + 0.9), (w + 1.4, w + 1.4, 1.8), 'Castle_Trim', 0.2)
            bevel_box(p, M, (0, -(w + 1.4) / 2 - 0.05, z + 0.9), (w + 1.0, 0.3, 0.5), 'Gold', 0.06)
            z += 1.8
            continue
        if k % 2 == 0:
            bevel_box(p, M, (0, 0, z + ch / 2), (w - 0.12, w - 0.12, ch - 0.14), rnd.choice(STONES), 0.22)
        else:                                               # two half blocks -> vertical seam
            for s in (-1, 1):
                bevel_box(p, M, (s * w / 4, 0, z + ch / 2), (w / 2 - 0.14, w - 0.12, ch - 0.14),
                          rnd.choice(STONES), 0.22)
        z += ch; k += 1
    if panel:                                               # recessed vertical groove panel on the front
        for s in (-1, 1):
            bevel_box(p, M, (s * w * 0.28, -w / 2 - 0.02, (zb + 2 + top) / 2), (0.35, 0.3, top - zb - 4), 'Castle_Seam',
                      0.0)
    bevel_box(p, M, (0, 0, top + 0.8), (w + 1.4, w + 1.4, 1.6), 'Castle_Trim', 0.25)
    bevel_box(p, M, (0, 0, top + 2.2), (w + 2.4, w + 2.4, 1.2), 'Castle_Stone_Light', 0.25)
    bevel_box(p, M, (0, -(w + 2.4) / 2 - 0.05, top + 2.2), (w + 2.0, 0.3, 0.4), 'Gold', 0.06)
    bevel_box(p, M, (0, 0, top + 3.6), (w + 0.6, w + 0.6, 1.8), 'Castle_Stone', 0.22)
    zc = top + 4.5
    if cap == 'pyramid':
        p.cyl(M @ Vector((0, 0, zc + w * 0.45)), w * 0.72, w * 0.9, 'Roof_Blue', 4, r2=0.0,
                   rot=M.to_3x3().normalized() @ Matrix.Rotation(math.pi / 4, 3, 'Z'))
        p.cyl(M @ Vector((0, 0, zc + w * 0.95)), 0.5, 1.6, 'Gold', 6)
        p.ico(M @ Vector((0, 0, zc + w * 0.95 + 1.2)), 0.6, 'Gold', 1)
    elif cap == 'ball':
        p.ico(M @ Vector((0, 0, zc + 1.0)), 1.1, 'Gold', 1)


def balustrade(p, M, x0, x1, z, rnd=None, h=3.4, post_every=10.0, mat='Castle_Trim'):
    """rail + vase balusters + posts along local x at height z (front y = 0)"""
    L = x1 - x0
    bevel_box(p, M, ((x0 + x1) / 2, 0, z + 0.3), (L, 1.4, 0.6), mat, 0.12)
    bevel_box(p, M, ((x0 + x1) / 2, 0, z + h - 0.3), (L, 1.6, 0.6), mat, 0.15)
    n = int(L / 1.6)
    for i in range(n):
        x = x0 + (i + 0.5) * L / n
        c = M @ Vector((x, 0, z + 0.6))
        p.cone(c, 0.3, (h - 1.2) * 0.45, mat, 6, r_top=0.48)
        p.cone(c + Vector((0, 0, (h - 1.2) * 0.45)), 0.48, (h - 1.2) * 0.55, mat, 6, r_top=0.26)
    for i in range(int(L / post_every) + 1):
        x = x0 + i * L / max(1, int(L / post_every))
        bevel_box(p, M, (x, 0, z + h / 2 + 0.3), (1.5, 1.9, h + 0.6), 'Castle_Stone_Light', 0.15)


def banner(p, M, w=9.0, length=40.0, rod=True):
    """navy pennant with gold border and gold paw, hanging from local origin (front y = 0) downward"""
    o = [(-w / 2, 0), (w / 2, 0), (w / 2, -length), (0, -length - w * 0.6), (-w / 2, -length)]
    Mb = M @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    p.prism(o, -0.35, 0.0, 'Banner_Navy', Mb)
    edge = [(-w / 2, 0), (-w / 2, -length), (0, -length - w * 0.6), (w / 2, -length), (w / 2, 0)]
    inner = [(-w / 2 + 0.7, 0), (-w / 2 + 0.7, -length + 0.3), (0, -length - w * 0.6 + 1.0), (w / 2 - 0.7, -length + 0.3),
             (w / 2 - 0.7, 0)]
    for (a0, a1), (b0, b1) in zip(zip(edge, edge[1:]), zip(inner, inner[1:])):
        q = [(a0[0], a0[1]), (a1[0], a1[1]), (b1[0], b1[1]), (b0[0], b0[1])]
        p.hexa([Mb @ Vector((x, z, 0.0)) for x, z in q] + [Mb @ Vector((x, z, 0.25)) for x, z in q], 'Gold')
    p.hexa([Mb @ Vector((x, z, 0.0)) for x, z in ((-w / 2, -1.2), (w / 2, -1.2), (w / 2, -2.0), (-w / 2, -2.0))] +
           [Mb @ Vector((x, z, 0.25)) for x, z in ((-w / 2, -1.2), (w / 2, -1.2), (w / 2, -2.0), (-w / 2, -2.0))], 'Gold')
    paw(p, Mb @ Matrix.Translation((0, -length * 0.62, 0.0)), w * 0.7, 0.3, 'Gold')
    if rod:
        p.cyl(M @ Vector((0, -0.6, 0.6)), 0.4, w + 2.0, 'Gold', 8, axis='X',
              rot=M.to_3x3().normalized())
        for s in (-1, 1):
            p.ico(M @ Vector((s * (w / 2 + 1.0), -0.6, 0.6)), 0.6, 'Gold', 1)


def castle_lantern(p, rnd=None):
    """stone pedestal (three block courses) with a black iron lantern - origin at the ground"""
    rnd = rnd or random.Random(3)
    I = Matrix.Identity(4)
    bevel_box(p, I, (0, 0, 0.5), (3.4, 3.4, 1.0), 'Castle_Trim', 0.18)
    for k in range(3):
        bevel_box(p, I, (0, 0, 1.0 + k * 1.4 + 0.7), (2.6, 2.6, 1.3), rnd.choice(STONES), 0.18)
    bevel_box(p, I, (0, 0, 5.4), (3.2, 3.2, 0.6), 'Castle_Trim', 0.15)
    bevel_box(p, I, (0, 0, 6.0), (1.6, 1.6, 0.6), 'Lantern_Metal', 0.08)
    p.box((0, 0, 7.6), (1.5, 1.5, 2.4), 'Lantern_Glow')
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box((sx * 0.8, sy * 0.8, 7.6), (0.3, 0.3, 2.6), 'Lantern_Metal')
    bevel_box(p, I, (0, 0, 9.0), (2.4, 2.4, 0.4), 'Lantern_Metal', 0.08)
    p.cyl((0, 0, 9.8), 1.7, 1.4, 'Lantern_Metal', 4, r2=0.2, rot=Matrix.Rotation(math.pi / 4, 3, 'Z'))
    p.ico((0, 0, 10.7), 0.3, 'Gold', 1)


def cat_statue(p, rnd=None):
    """sitting pet (cat) statue on a masonry pedestal, faceted stone - faces -Y, origin at the ground"""
    rnd = rnd or random.Random(5)
    I = Matrix.Identity(4)
    bevel_box(p, I, (0, 0, 0.6), (8.4, 8.4, 1.2), 'Castle_Trim', 0.2)
    masonry(p, I @ Matrix.Translation((0, -3.4, 0)), -3.4, 3.4, 1.2, 6.2, rnd, 1.7, (2.2, 3.4), 6.8, mats=STONES,
            backing=False)
    bevel_box(p, I, (0, 0, 6.7), (8.0, 8.0, 1.0), 'Castle_Trim', 0.2)
    bevel_box(p, I, (0, -4.05, 6.7), (7.2, 0.3, 0.35), 'Gold', 0.05)
    S, z = 'Castle_Statue', 7.2
    p.uvsphere((0, 0.6, z + 3.2), 2.6, S, 10, 7, (1.0, 1.15, 1.25), smooth=False)       # body
    for s in (-1, 1):
        p.uvsphere((s * 1.9, 1.4, z + 1.7), 1.6, S, 8, 6, (0.8, 1.3, 1.0), smooth=False)  # haunches
        p.cyl((s * 0.9, -1.4, z + 2.0), 0.55, 4.0, S, 6)                                  # front legs
        p.uvsphere((s * 0.9, -1.9, z + 0.4), 0.75, S, 8, 5, (1, 1.3, 0.6), smooth=False)  # paws
    p.uvsphere((0, -0.7, z + 7.0), 2.0, S, 10, 7, (1.05, 1.0, 0.95), smooth=False)      # head
    p.uvsphere((0, -2.3, z + 6.4), 0.95, S, 8, 5, (1.2, 0.8, 0.75), smooth=False)       # muzzle
    for s in (-1, 1):
        tilt = Euler((0, s * 0.35, 0)).to_matrix()
        p.cyl(Vector((s * 1.25, -0.6, z + 8.8)) + tilt @ Vector((0, 0, 0.9)), 0.9, 1.8, S, 4, r2=0.05, rot=tilt)
    p.torus((0, -0.4, z + 5.1), 1.6, 0.25, 'Gold', 16, 4, rot=Euler((0.35, 0, 0)).to_matrix())
    p.ico((0, -1.95, z + 4.6), 0.4, 'Gold', 1)
    tail = [Vector((1.8, 2.6, z + 0.8)), Vector((2.8, 1.0, z + 0.5)), Vector((2.6, -1.4, z + 0.5)),
            Vector((1.6, -2.4, z + 0.6))]
    from foliage import tube
    tube(p, tail, [0.6, 0.55, 0.45, 0.3], S, 5)


def topiary_cone(p, rnd, h=7.0, r=2.4):
    """conical clipped evergreen in the foliage-pack leaf style"""
    from foliage import leaf
    p.cone((0, 0, 0), 0.4, 0.8, 'Trunk', 5)
    vs = p.cone((0, 0, 0.6), r, h, 'Leaves_Dark', 8)
    rings = 6
    for k in range(rings):
        t = k / rings
        z = 0.6 + h * (t * 0.92)
        rr = r * (1 - t) * 0.95
        n = max(4, int(10 * (1 - t)) + 2)
        for i in range(n):
            a = TAU * i / n + k * 0.4
            u = Vector((math.cos(a), math.sin(a), r / h)).normalized()
            base = Vector((math.cos(a) * rr, math.sin(a) * rr, z))
            leaf(p, base, Vector((math.cos(a) * 0.6, math.sin(a) * 0.6, -0.8)) + Vector((0, 0, 1.4)), u,
                 r * 0.75 * (1 - t * 0.5), r * 0.6 * (1 - t * 0.5), rnd.choice(('Leaves_Mid', 'Leaves_Light')), 0.15)
    leaf(p, Vector((0, 0, h * 0.9)), Vector((0, 0, 1)), Vector((1, 0, 0)), r * 0.6, r * 0.4, 'Leaves_Light')


# ---------------------------------------------------------------- kit -------
def _lib(name, builder, *a, **kw):
    p = Part('ASSET_' + name, KIT)
    builder(p, *a, **kw)
    ob = p.finish()
    ob.data.name = 'ASSET_' + name
    ob.name = name
    ASSETS[name] = ob
    return ob


def build_castle_kit(parent):
    coll(KIT, parent)
    I = Matrix.Identity(4)
    R = random.Random
    _lib('Stone_Block_Small', lambda p: bevel_box(p, I, (0, 0, 1.0), (3.0, 1.6, 2.0), 'Castle_Stone', 0.16))
    _lib('Stone_Block_Medium', lambda p: bevel_box(p, I, (0, 0, 1.5), (5.5, 1.8, 3.0), 'Castle_Stone', 0.2))
    _lib('Stone_Block_Large', lambda p: bevel_box(p, I, (0, 0, 2.0), (8.0, 2.4, 4.0), 'Castle_Stone_Light', 0.25))
    _lib('Wall_Straight', lambda p: masonry(p, I, -10, 10, 0, 16, R(1)))
    def corner(p):
        masonry(p, I, 0, 12, 0, 16, R(2))
        masonry(p, Matrix.Rotation(-math.pi / 2, 4, 'Z'), -12, 0, 0, 16, R(3))
        quoins(p, I, 0, 16, R(4), side=1)
    _lib('Wall_Corner', corner)
    _lib('Wall_Trim', lambda p: trim_run(p, I, -10, 10, 0, h=1.8, out=1.2))
    _lib('Decorative_Trim', lambda p: trim_run(p, I, -10, 10, 0, h=2.4, out=1.6, steps=3, gold=True))
    _lib('Gold_Trim', lambda p: bevel_box(p, I, (0, 0, 0.2), (20, 0.4, 0.4), 'Gold', 0.08))
    _lib('Pillar_Base', lambda p: (bevel_box(p, I, (0, 0, 0.8), (12.4, 12.4, 1.6), 'Castle_Trim', 0.25),
                                   bevel_box(p, I, (0, 0, 2.2), (11.2, 11.2, 1.2), 'Castle_Stone_Light', 0.22)))
    _lib('Pillar_Main', lambda p: pillar(p, I, 10, 0, 40, R(5), cap=None))
    def pillar_top(p):
        bevel_box(p, I, (0, 0, 0.8), (11.4, 11.4, 1.6), 'Castle_Trim', 0.25)
        bevel_box(p, I, (0, 0, 2.2), (12.4, 12.4, 1.2), 'Castle_Stone_Light', 0.25)
        p.cyl((0, 0, 7.6), 7.2, 9, 'Roof_Blue', 4, r2=0.0, rot=Matrix.Rotation(math.pi / 4, 3, 'Z'))
        p.ico((0, 0, 12.6), 0.6, 'Gold', 1)
    _lib('Pillar_Top', pillar_top)
    for name, w, hs in (('Arch_Small', 10.0, 8.0), ('Arch_Large', 22.0, 14.0)):
        def arch(p, w=w, hs=hs):
            voussoirs(p, I, round_arch(w + 4.4, hs, 12), round_arch(w, hs, 12), -0.6, 1.4, R(7))
            for s in (-1, 1):                                    # jambs with block courses
                masonry(p, I, s * (w / 2) + (0 if s > 0 else -2.2), s * (w / 2) + (2.2 if s > 0 else 0), 0, hs, R(8),
                        2.6, (2.2, 2.2), 2.0, backing=False)
        _lib(name, arch)
    def stairs(p):
        for i in range(8):
            for j in range(3):
                bevel_box(p, I, (-6 + j * 6, i * 1.5 + 0.75, i * 1.0 + 0.5), (5.9, 1.48, 1.0), 'Castle_Stone_Light', 0.12)
    _lib('Stair_Straight', stairs)
    def balcony(p):
        bevel_box(p, I, (0, -3, 0.6), (16, 7, 1.2), 'Castle_Trim', 0.2)
        for x in (-6, 0, 6):
            p.beam(Vector((x, 0, -3.5)), Vector((x, -5.5, 0)), 1.4, 1.4, 'Castle_Stone_Light')
        balustrade(p, Matrix.Translation((0, -6, 1.2)), -8, 8, 0)
    _lib('Balcony', balcony)
    _lib('Ledge', lambda p: trim_run(p, I, -10, 10, 0, h=1.2, out=2.4, steps=2))
    _lib('Banner', lambda p: banner(p, I, 9, 36))
    _lib('Castle_Lantern', castle_lantern)
    _lib('Balustrade', lambda p: balustrade(p, I, -10, 10, 0))
    _lib('Cat_Statue', cat_statue)
    _lib('Topiary_Cone', topiary_cone, R(9))


# ---------------------------------------------------------------- reconstruction
def rect_minus_arch(p, M, x0, x1, z0, z1, arch_pts, y0, y1, mat):
    """two prisms filling a rectangle around an arch opening whose feet sit on z0 (local XZ, extruded y0..y1)"""
    mid = len(arch_pts) // 2
    for s in (-1, 1):
        half = arch_pts[:mid + 1] if s < 0 else arch_pts[mid:][::-1]
        xe = x0 if s < 0 else x1
        poly = [(xe, z0)] + list(half) + [(half[-1][0], z1), (xe, z1)]
        if s > 0:
            poly = poly[::-1]
        Mx = M @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        p.prism(poly, y0, y1, mat, Mx)


def lifted(pts, dx=0.0, dz=0.0):
    return [(x + dx, z + dz) for x, z in pts]


def build_stairs_and_landing(rnd):
    from entrance import STAIR_Y0, STAIR_Y1, RUN, RISE, N_STEPS, Z_LAND, FACADE_Y, STAIR_W
    I = Matrix.Identity(4)
    p = Part('Castle_Stairs', C)
    for i in range(N_STEPS):                                 # solid stepped flight, 4 slabs per tread
        y0 = STAIR_Y0 + i * RUN
        z1 = (i + 1) * RISE
        for j in range(4):
            x = -STAIR_W / 2 + (j + 0.5) * STAIR_W / 4
            bevel_box(p, I, (x, y0 + RUN / 2 + (STAIR_Y1 - y0 - RUN) / 2 + 0.0, z1 / 2),
                      (STAIR_W / 4 - 0.12, STAIR_Y1 - y0, z1), rnd.choice(('Castle_Stone_Light', 'Castle_Stone')), 0.14)
        p.box((0, y0 + RUN / 2, z1 + 0.02), (5.0, RUN - 0.3, 0.06), 'Blue_Inlay')
    for s in (-1, 1):                                        # stepped cheek walls with cap stones
        x = s * (STAIR_W / 2 + 2.6)
        for i in range(N_STEPS):
            y0 = STAIR_Y0 + i * RUN
            h = (i + 1) * RISE + 3.2
            bevel_box(p, I, (x, y0 + RUN / 2, h / 2), (5.0, RUN - 0.06, h), rnd.choice(STONES), 0.14)
            bevel_box(p, I, (x, y0 + RUN / 2, h + 0.3), (5.8, RUN + 0.1, 0.6), 'Castle_Trim', 0.12)
        for i in (0, N_STEPS - 1):
            y0 = STAIR_Y0 + i * RUN - (3 if i == 0 else -1)
            hh = (i + 1) * RISE + 5
            for k in range(int(hh / 2.6)):                   # newel posts: stacked blocks
                bevel_box(p, I, (x, y0, k * 2.6 + 1.3), (6.6, 6.6, 2.5), rnd.choice(STONES), 0.2)
            bevel_box(p, I, (x, y0, int(hh / 2.6) * 2.6 + 0.4), (7.4, 7.4, 0.8), 'Castle_Trim', 0.18)
            inst('Castle_Lantern', f'Castle_StairLantern_{s}_{i}', C, (x, y0, int(hh / 2.6) * 2.6 + 0.8), 0, 1.0)
        inst('Castle_Lantern', f'Castle_StairLantern_{s}_mid', C,
             (x, STAIR_Y0 + 10 * RUN + RUN / 2, 11 * RISE + 3.8), 0, 0.85)
        # terraced masonry planters with topiary cones beside the flight
        for k in range(4):
            yy = STAIR_Y0 + 2 + k * 7.5
            zz = (yy - STAIR_Y0) / RUN * RISE + 3
            cx = s * (STAIR_W / 2 + 11)
            Mp = Matrix.Translation((cx, yy - 3.75, 0))
            masonry(p, Mp, -6, 6, 0, zz, rnd, 2.6, (3, 5), 1.4, backing=False)
            bevel_box(p, I, (cx, yy, zz / 2), (11.6, 7.2, zz), 'Castle_Seam', 0.0)
            bevel_box(p, I, (cx, yy, zz + 0.25), (12.4, 8.0, 0.5), 'Castle_Trim', 0.15)
            p.box((cx, yy, zz + 0.55), (11, 6.6, 0.2), 'Grass')
            inst('Topiary_Cone', f'Castle_Topiary_{s}_{k}', C, (cx - s * 2.5, yy, zz + 0.6), 0, 1.0 + 0.1 * k)
            inst(('Bush_01', 'Bush_02', 'Ground_Plant_01', 'Bush_03')[k], f'Castle_StairBush_{s}_{k}', C,
                 (cx + s * 2.8, yy, zz + 0.6), rnd.uniform(0, TAU), 0.9)
    p.finish()
    from foliage import tree_in_planter
    for s in (-1, 1):                                        # big lobby trees flanking the flight (reference)
        tree_in_planter(f'Castle_LobbyTree_{s}', C, (s * 64.0, STAIR_Y0 + 12, 0), 0.0, 'Tree_Large_High', seed=400 + s)

    # landing: masonry front wall, flagstones, balustrades
    q = Part('Castle_Landing', C)
    yb = FACADE_Y + 4
    q.box((0, (STAIR_Y1 + yb) / 2, (Z_LAND - 0.6) / 2), (146, yb - STAIR_Y1, Z_LAND - 0.6), 'Castle_Seam')
    for s in (-1, 1):
        x0, x1 = (STAIR_W / 2 + 5.1, 73) if s > 0 else (-73, -STAIR_W / 2 - 5.1)
        Mf = Matrix.Translation((0, STAIR_Y1 - 0.6, 0))
        masonry(q, Mf, x0, x1, 0, Z_LAND - 2, rnd, 3.0, (4.5, 7), 1.6, backing=False)
        trim_run(q, Mf, x0, x1, Z_LAND - 2, h=2.0, out=1.2)
        quoins(q, Matrix.Translation((s * 73, STAIR_Y1 - 0.6, 0)), 0, Z_LAND - 2, rnd, side=-s)
        balustrade(q, Matrix.Translation((0, STAIR_Y1 + 0.4, 0)), x0 + 1, x1 - 1, Z_LAND, post_every=9)
    nx, ny = 24, 4
    for i in range(nx):
        for j in range(ny):
            x = -72 + (i + 0.5) * 144 / nx
            y = STAIR_Y1 + (j + 0.5) * (yb - STAIR_Y1) / ny
            bevel_box(q, I, (x, y, Z_LAND - 0.3), (144 / nx - 0.15, (yb - STAIR_Y1) / ny - 0.15, 0.6),
                      rnd.choice(('Castle_Stone_Light', 'Castle_Stone', 'Castle_Trim')), 0.1)
    q.finish()


def build_gatehouse(rnd):
    from entrance import FACADE_Y, Z_LAND, OPEN_W, arch
    z0 = Z_LAND
    G = Matrix.Translation((0, FACADE_Y, 0))            # local y = 0 is the facade plane, +y into the castle
    A = lambda w: lifted(arch(w), 0, z0)
    TOP = z0 + 104                                       # cornice line of the central bay
    # --- core (dark, shows through the seams) -------------------------------------------------------------
    k = Part('Castle_Gatehouse_Core', C)
    rect_minus_arch(k, G, -73, 73, z0, TOP, A(54), 2.0, 8.0, 'Castle_Seam')
    rect_minus_arch(k, G, -73, 73, z0, TOP, A(OPEN_W + 2), 8.0, 44.0, 'Castle_Seam')
    k.box(G @ Vector((0, 43, z0 + 30)), (OPEN_W, 2, 60), 'Castle_Seam')
    k.finish()
    # --- central bay masonry + stepped arch frames -------------------------------------------------------
    p = Part('Castle_Gatehouse_Facade', C)
    poly54 = A(52.5)
    masonry(p, G, -33, 33, z0, TOP, rnd, 3.2, (4.5, 7.5), 1.6,
            skip=lambda x, z, w, h: inside(poly54, x, z), backing=False)
    quoins(p, G @ Matrix.Translation((-33, 0, 0)), z0, TOP, rnd, side=1, mat='Castle_Trim')
    quoins(p, G @ Matrix.Translation((33, 0, 0)), z0, TOP, rnd, side=-1, mat='Castle_Trim')
    layers = ((54, 46, -3.5, 1.0, None), (44.4, 37, -1.0, 3.5, None), (35.6, 29.5, 1.0, 5.0, None))
    for w_out, w_in, y0, y1, mat in layers:
        voussoirs(p, G, A(w_out), A(w_in), y0, y1, rnd, 4.6)
    frame_strip(p, G, A(46), A(44.4), -2.4, 1.5, 'Gold')
    frame_strip(p, G, A(37), A(35.6), -0.2, 4.0, 'Gold')
    frame_strip(p, G, A(29.5), A(OPEN_W), 4.0, 7.6, 'Magic_Glow')
    # base course and cornice across the whole front
    trim_run(p, G, -73, 73, z0, h=1.6, out=1.4)
    trim_run(p, G, -34, 34, TOP, h=2.4, out=2.0, steps=3, gold=True)
    p.finish()
    # --- pediment with the gold crest ("top decoration") ---------------------------------------------------
    d = Part('Castle_Pediment', C)
    pz0, pz1, pw = TOP + 2.4, TOP + 36, 31
    tri = [(-pw, pz0), (pw, pz0), (0, pz1)]
    masonry(d, G @ Matrix.Translation((0, -2.4, 0)), -pw, pw, pz0, pz1, rnd, 3.0, (4, 6.5), 2.4,
            skip=lambda x, z, w, h: not inside(tri, x, z + h * 0.3), backing=False)
    d.prism([(-pw + 1, pz0 + 0.5), (pw - 1, pz0 + 0.5), (0, pz1 - 1)], -0.5, 1.0, 'Castle_Seam',
            G @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    for s in (-1, 1):                                     # raking cornices + gold edge
        ang = math.atan2(pz1 - pz0, pw)
        L = math.hypot(pw, pz1 - pz0) + 3
        Ms = G @ Matrix.Translation((s * pw / 2, -3.2, (pz0 + pz1) / 2 + 0.9)) @ Matrix.Rotation(s * ang, 4, 'Y')
        bevel_box(d, Ms, (0, 0, 0), (L, 3.2, 2.2), 'Castle_Trim', 0.25)
        bevel_box(d, Ms, (0, -1.7, -1.2), (L - 2, 0.4, 0.5), 'Gold', 0.08)
    # navy inset triangle with the gold paw crest and crown
    inset = [(-pw * 0.55, pz0 + 3), (pw * 0.55, pz0 + 3), (0, pz0 + 3 + (pz1 - pz0 - 3) * 0.55)]
    Mx = G @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    d.prism(inset, -3.4, -2.5, 'Banner_Navy', Mx)
    paw(d, M_front(0, FACADE_Y - 3.5, pz0 + 9.5), 8.0, 0.5, 'Gold')
    for i in range(5):                                     # crown above the paw
        x = -4 + i * 2
        d.cone(G @ Vector((x, -3.4, pz0 + 15.4)), 0.7, 1.6 + (1.2 if i == 2 else 0.4 * (i % 2)), 'Gold', 4)
    bevel_box(d, G, (0, -3.4, pz0 + 15.0), (10, 0.8, 1.0), 'Gold', 0.1)
    d.cone(G @ Vector((0, -1.0, pz1 + 0.6)), 1.6, 6, 'Gold', 6)
    d.ico(G @ Vector((0, -1.0, pz1 + 7.0)), 0.9, 'Gold', 1)
    d.finish()
    # --- big pillars with banners -------------------------------------------------------------------------
    pl = Part('Castle_Pillars', C)
    for s in (-1, 1):
        Mp = G @ Matrix.Translation((s * 40.5, -6.0, 0))
        pillar(pl, Mp, 13, z0, 132, rnd, band=0.62)
        banner(pl, G @ Matrix.Translation((s * 40.5, -13.2, z0 + 104)), 9.5, 46)
    pl.finish()
    # --- side wings with blind windows, quoins, cornices, balustrade -------------------------------------
    w = Part('Castle_Gatehouse_Wings', C)
    WT = z0 + 92
    for s in (-1, 1):
        x0, x1 = (47.5, 73) if s > 0 else (-73, -47.5)
        Mw = G @ Matrix.Translation((0, 0.6, 0))
        wins = []
        for zz in (z0 + 20, z0 + 54):
            cx = (x0 + x1) / 2
            outer = lifted(pointed_arch(9.5, 14, 4.5), cx, zz)
            inner = lifted(pointed_arch(6.0, 14, 3.0), cx, zz)
            wins.append((cx, zz, outer))
            voussoirs(w, Mw, outer, inner, -1.4, 1.2, rnd, 2.6)
            w.prism(pointed_arch(6.0, 14, 3.0), 0, 0.4, 'Window_Warm',
                    Mw @ Matrix.Translation((cx, 1.0, zz)) @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
            bevel_box(w, Mw, (cx, -1.4, zz - 0.6), (11, 2.6, 1.2), 'Castle_Trim', 0.15)         # sill
        masonry(w, Mw, x0, x1, z0 + 1.6, WT, rnd, 3.2, (4.5, 7), 1.6,
                skip=lambda x, z, ww, h, wins=wins: any(inside(o, x, z) for _, _, o in wins), backing=False)
        quoins(w, G @ Matrix.Translation((s * 73, 0.6, 0)), z0 + 1.6, WT, rnd, side=-s, mat='Castle_Trim')
        # masonry on the gatehouse's side return (runs back toward the tower)
        Ms = G @ Matrix.Translation((s * 73.4, 0, 0)) @ Matrix.Rotation(s * math.pi / 2, 4, 'Z')
        xa, xb = (3.0, 44.0) if s > 0 else (-44.0, -3.0)
        masonry(w, Ms, xa, xb, z0 + 1.6, WT, rnd, 3.2, (4.5, 7), 1.6, backing=False)
        trim_run(w, Ms, xa, xb, WT, h=2.2, out=1.8, steps=3)
        trim_run(w, Mw, x0, x1, z0 + 42, h=1.4, out=1.0)
        trim_run(w, Mw, x0 - 0.5, x1 + 0.5, WT, h=2.2, out=1.8, steps=3, gold=True)
        balustrade(w, G @ Matrix.Translation((0, 1.0, 0)), x0 + 1, x1 - 1, WT + 2.2, post_every=8)
        # pinnacles on the bay corners and wing ends
        for xp in (s * 33.5, s * 73):
            Mq = G @ Matrix.Translation((xp, 0.5, 0))
            for kk in range(4):
                bevel_box(w, Mq, (0, 0, TOP + 2.4 + kk * 2.6 + 1.3), (4.4, 4.4, 2.5), rnd.choice(STONES), 0.18)
            bevel_box(w, Mq, (0, 0, TOP + 13.4), (5.4, 5.4, 0.8), 'Castle_Trim', 0.15)
            w.cyl(Mq @ Vector((0, 0, TOP + 17.0)), 3.2, 6.6, 'Roof_Blue', 4, r2=0.0,
                  rot=Matrix.Rotation(math.pi / 4, 3, 'Z'))
            w.ico(Mq @ Vector((0, 0, TOP + 20.6)), 0.5, 'Gold', 1)
        # wall lantern sconces between pillar and wing
        for zz in (z0 + 34,):
            Ml = G @ Matrix.Translation((s * 50, 0.4, zz))
            bevel_box(w, Ml, (0, -1.0, 0), (2.4, 2.0, 1.0), 'Lantern_Metal', 0.08)
            w.box(Ml @ Vector((0, -1.6, 1.6)), (1.4, 1.4, 2.2), 'Lantern_Glow')
            bevel_box(w, Ml, (0, -1.6, 3.0), (2.0, 2.0, 0.5), 'Lantern_Metal', 0.06)
    # masonry under the wing cornice band between the bay and the wings (behind the pillars)
    for s in (-1, 1):
        x0, x1 = (33.5, 47.5) if s > 0 else (-47.5, -33.5)
        masonry(w, G @ Matrix.Translation((0, 1.0, 0)), x0, x1, z0 + 1.6, TOP, rnd, 3.2, (4, 6), 1.6, backing=False)
    w.finish()
    # --- statues, lanterns, greenery on the landing ------------------------------------------------------
    for s in (-1, 1):
        inst('Cat_Statue', f'Castle_CatStatue_{s}', C, (s * 58.0, FACADE_Y - 12, z0), 0.0, 1.0)
        inst('Castle_Lantern', f'Castle_LandingLantern_Inner_{s}', C, (s * 27.0, FACADE_Y - 16, z0), 0, 1.15)
        inst('Castle_Lantern', f'Castle_LandingLantern_Outer_{s}', C, (s * 70.0, FACADE_Y - 16, z0), 0, 1.15)
        inst('Topiary_Cone', f'Castle_LandingTopiary_{s}', C, (s * 47.0, FACADE_Y - 19, z0), 0, 1.3)
        inst('Bush_02', f'Castle_LandingBush_{s}', C, (s * 63.0, FACADE_Y - 5, z0), 0, 1.1)


def build_portal(rnd):
    """portal surface, paw, energy rim, particles and the invisible teleport trigger (recessed in the arch)"""
    from entrance import FACADE_Y, Z_LAND, OPEN_W, arch
    from foliage import vine
    yf, z0 = FACADE_Y, Z_LAND
    Mx = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    pt = Part('Entrance_Portal', C)
    pt.prism(lifted(arch(OPEN_W), 0, z0), yf + 7.0, yf + 7.6, 'Portal_Energy', Mx)
    pt.finish()
    pe = Part('Entrance_Portal_Paw', C)
    paw(pe, M_front(0, yf + 6.9, z0 + 25.0), 15.0, 0.6, 'Paw_White_Glow')
    pe.finish()
    sp = Part('Entrance_Portal_Particles', C)
    for k in range(70):
        x = rnd.uniform(-22, 22); y = rnd.uniform(yf - 24, yf + 5); z = rnd.uniform(z0 + 1, z0 + 50)
        sp.ico((x, y, z), rnd.uniform(0.12, 0.32), rnd.choice(('Magic_Glow', 'Magic_Purple', 'Paw_White_Glow')), 1)
    sp.finish()
    tr = Part('Portal_TeleportTrigger', C)
    tr.box((0, yf + 9, z0 + 22), (OPEN_W - 2, 4, 44), 'Magic_Glow')
    t = tr.finish()
    t.display_type = 'WIRE'
    t.hide_render = True
    v = Part('Castle_Vines', C)
    for x in (-72.5, -48, 48, 72.5):
        vine(v, (x, yf - 0.6, z0 + 94), rnd.uniform(14, 26), rnd, 1.6)
        vine(v, (x + 2, yf - 0.6, z0 + 94), rnd.uniform(8, 16), rnd, 1.6)
    v.finish()


def build_upper_gate(rnd):
    """smaller gate, balcony and banners high on the tower base, visible above the pediment"""
    from tower import TC, R_FOUND
    ru = 276.0
    ap = ru * math.cos(math.pi / 24)
    yface = TC.y - ap
    M = Matrix.Translation((0, yface - 0.3, 0))
    p = Part('Castle_UpperGate', C)
    zg = 160.0
    outer, inner = lifted(round_arch(24, 14, 12), 0, zg), lifted(round_arch(16, 14, 12), 0, zg)
    voussoirs(p, M, outer, inner, -2.6, 1.0, rnd, 3.2)
    p.prism(round_arch(16, 14, 12), 0.2, 0.8, 'Window_Blue',
            M @ Matrix.Translation((0, 0, zg)) @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    paw(p, M_front(0, yface - 0.4, zg + 10), 7.0, 0.3, 'Paw_White_Glow')
    for s in (-1, 1):
        pillar(p, M @ Matrix.Translation((s * 16, -3, 0)), 5, zg - 2, 32, rnd, cap='ball', panel=False)
        banner(p, M @ Matrix.Translation((s * 26, -0.9, zg + 28)), 6, 20)
        inst('Castle_Lantern', f'Castle_UpperLantern_{s}', C, (s * 9, yface - 9, zg - 1.2), 0, 0.8)
    # balcony on corbels with balustrade
    bevel_box(p, M, (0, -6, zg - 1.8), (44, 12, 1.6), 'Castle_Trim', 0.2)
    for x in range(-18, 19, 6):
        p.beam(M @ Vector((x, 0, zg - 10)), M @ Vector((x, -10.5, zg - 2.6)), 1.6, 1.6, 'Castle_Stone_Light')
    balustrade(p, M @ Matrix.Translation((0, -11.6, 0)), -21, 21, zg - 1.0)
    p.finish()


def build_foundation_masonry(rnd):
    """real masonry facing on the tower-base faces seen from the hub (lower and upper walls), with
    recessed arched windows; the plain foundation prism behind acts as the core"""
    from tower import TC, R_FOUND
    n = 24
    rot = 270 + 7.5
    for tier, (R, z0, z1, faces) in enumerate(((R_FOUND, 0.0, 108.0, (240, 255, 285, 300)),
                                               (276.0, 112.0, 192.0, (240, 255, 270, 285, 300)))):
        ap = R * math.cos(math.pi / n)
        chord = 2 * R * math.sin(math.pi / n)
        for deg in faces:
            a = math.radians(deg)
            c = Vector((TC.x + math.cos(a) * (ap + 0.3), TC.y + math.sin(a) * (ap + 0.3), 0))
            M = Matrix.Translation(c) @ Matrix.Rotation(a + math.pi / 2, 4, 'Z')
            p = Part(f'Castle_BaseMasonry_{"Lower" if tier == 0 else "Upper"}_{deg}', C)
            half = chord / 2 - (6.5 if tier == 0 else 0.6)
            wins = []
            if tier == 0:
                for zz in (48, 80):
                    wins.append((lifted(pointed_arch(15, 14, 7), 0, zz), lifted(pointed_arch(10, 14, 5), 0, zz), zz))
            elif deg != 270:
                wins.append((lifted(round_arch(16, 12, 10), 0, 140), lifted(round_arch(11, 12, 10), 0, 140), 140))
            else:
                wins.append((lifted(round_arch(25, 14, 12), 0, 160), None, 160))      # upper gate opening
            masonry(p, M, -half, half, z0, z1, rnd, 4.0, (6, 9.5), 1.8,
                    skip=lambda x, z, w, h, wins=wins: any(inside(o, x, z) for o, _, _ in wins))
            for o, i_, zz in wins:
                if i_ is None:
                    continue
                voussoirs(p, M, o, i_, -1.4, 1.0, rnd, 3.4)
                ip = [(x, z - zz) for x, z in i_]
                p.prism(ip, 0.0, 0.5, 'Window_Warm',
                        M @ Matrix.Translation((0, 0.2, zz)) @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
                bevel_box(p, M, (0, -1.2, zz - 0.5), (o[-1][0] - o[0][0] + 3, 2.4, 1.0), 'Castle_Trim', 0.15)
            trim_run(p, M, -half, half, z1 - 2.4, h=2.4, out=1.6, steps=2)
            p.finish()


def build_side_arcades(rnd):
    """two-tier masonry arcades curving round the north-east / north-west of the hub (replaces the old
    aqueducts): see-through round arches with voussoirs, pilasters with banners, balustraded walkways,
    stone spouts feeding waterfalls, trees and vines"""
    from hub import polar
    from foliage import vine
    ENV = 'ENVIRONMENT'
    R, n_bay, T = 192.0, 6, 6.0
    for side, (d0, d1) in (('East', (16.0, 66.0)), ('West', (114.0, 164.0))):
        step = (d1 - d0) / n_bay
        chord = 2 * R * math.sin(math.radians(step) / 2)
        for b in range(n_bay):
            mid = d0 + (b + 0.5) * step
            a = math.radians(mid)
            M = Matrix.Translation(Vector(polar(R, mid))) @ Matrix.Rotation(a - math.pi / 2, 4, 'Z')
            Mb = M @ Matrix.Translation((0, T, 0)) @ Matrix.Rotation(math.pi, 4, 'Z')      # outer face
            p = Part(f'Arcade_{side}_Bay{b}', ENV)
            hw = chord / 2
            s1 = chord - 9.0
            hs1 = 14.0
            t1 = hs1 + s1 / 2 + 5.0
            a1 = round_arch(s1, hs1, 10)
            # core with the opening, masonry both faces, voussoirs both faces
            rect_minus_arch(p, M, -hw, hw, 0, t1, a1, 1.0, T - 1.0, 'Castle_Stone_Dark')
            for MM in (M, Mb):
                masonry(p, MM, -hw, hw, 0, t1, rnd, 3.2, (4.5, 7), 1.4,
                        skip=lambda x, z, w, h: inside(round_arch(s1 + 3.0, hs1, 10), x, z), backing=False)
                voussoirs(p, MM, round_arch(s1 + 3.4, hs1, 10), a1, -0.8, 1.4, rnd, 3.6)
            # walkway slab + balustrade on tier 1
            bevel_box(p, M, (0, T / 2 - 1.5, t1 + 0.6), (chord + 0.2, T + 3.2, 1.2), 'Castle_Trim', 0.2)
            balustrade(p, M @ Matrix.Translation((0, -2.2, 0)), -hw, hw, t1 + 1.2, post_every=chord)
            # tier 2: two smaller arches, set back
            s2 = (chord - 9.0) / 2 - 1.5
            hs2 = 8.0
            t2 = t1 + 1.2 + hs2 + s2 / 2 + 4.0
            M2 = M @ Matrix.Translation((0, 1.6, 0))
            Mb2 = M2 @ Matrix.Translation((0, T - 2.0, 0)) @ Matrix.Rotation(math.pi, 4, 'Z')
            arches2 = [lifted(round_arch(s2, hs2, 8), dx, t1 + 1.2) for dx in (-chord / 4, chord / 4)]
            for MM in (M2, Mb2):
                masonry(p, MM, -hw, hw, t1 + 1.2, t2, rnd, 3.0, (4, 6.5), 1.3,
                        skip=lambda x, z, w, h: any(inside(lifted(round_arch(s2 + 2.8, hs2, 8), dx, t1 + 1.2), x, z)
                                                    for dx in (-chord / 4, chord / 4)), backing=False)
                for ar in arches2:
                    cx = (ar[0][0] + ar[-1][0]) / 2
                    voussoirs(p, MM, lifted(round_arch(s2 + 3.0, hs2, 8), cx, t1 + 1.2), ar, -0.6, 1.2, rnd, 3.0)
            # core of tier 2: three piers + lintel band (keeps the arches open)
            for xx in (-hw, 0, hw):
                bevel_box(p, M2, (xx, (T - 2.0) / 2, (t1 + 1.2 + t2) / 2), (3.0, T - 3.4, t2 - t1 - 1.2), 'Castle_Seam', 0)
            bevel_box(p, M2, (0, (T - 2.0) / 2, t2 - 1.6), (chord, T - 3.4, 3.2), 'Castle_Seam', 0)
            trim_run(p, M2, -hw, hw, t2, h=2.2, out=1.6, steps=2, gold=True)
            balustrade(p, M2 @ Matrix.Translation((0, 0.6, 0)), -hw, hw, t2 + 2.2, post_every=chord)
            # pilaster with banner on the bay's left pier (faces the plaza)
            Mp = M @ Matrix.Translation((-hw, -0.8, 0))
            for kk in range(int(t1 / 3.2)):
                bevel_box(p, Mp, (0, 0, kk * 3.2 + 1.6), (3.6, 1.6, 3.06), 'Castle_Stone_Light', 0.18)
            bevel_box(p, Mp, (0, -0.95, t1 * 0.6), (3.2, 0.3, 0.5), 'Gold', 0.06)
            banner(p, M @ Matrix.Translation((-hw, -1.8, t1 - 1.5)), 5.0, 17, rod=True)
            # piers continue down into the void on rock
            from common import rock_blob
            for xx in (-hw, hw):
                masonry(p, M @ Matrix.Translation((0, 0.4, 0)), xx - 2.5, xx + 2.5, -40, 0, rnd, 3.2, (5, 5), T - 0.8,
                        backing=False)
            rock_blob(p, M @ Vector((0, T / 2, -60)), 20, 'Cliff_Rock', rnd, 1, (1.1, 0.6, 1.8))
            p.finish()
            # greenery + vines + spout waterfalls
            if b % 2 == 0:
                inst(('Tree_Medium_High', 'Tree_Small')[b % 4 // 2], f'Arcade_{side}_Tree_{b}', ENV,
                     M @ Vector((hw * 0.4, T / 2, t2 + 2.2)), rnd.uniform(0, TAU), 0.8)
            else:
                inst('Topiary_Cone', f'Arcade_{side}_Topiary_{b}', ENV, M @ Vector((0, T / 2, t1 + 1.2)), 0, 1.0)
            vv = Part(f'Arcade_{side}_Vines{b}', ENV)
            for xx in (-hw * 0.6, hw * 0.3):
                vine(vv, M @ Vector((xx, -1.4, t2)), rnd.uniform(10, 22), rnd, 1.5)
            vv.finish()
            if b in (1, 4):
                lip = M @ Vector((chord / 4, T + 1.5, t1 + 1.0))
                sp = Part(f'Arcade_{side}_Spout{b}', ENV)
                Ms = Matrix.Translation(lip) @ Matrix.Rotation(a - math.pi / 2, 4, 'Z')
                bevel_box(sp, Ms, (0, 0.5, -0.4), (7.0, 4.0, 0.8), 'Castle_Trim', 0.15)
                for s in (-1, 1):
                    bevel_box(sp, Ms, (s * 3.2, 0.5, 0.4), (0.8, 4.0, 1.6), 'Castle_Trim', 0.12)
                sp.finish()
                inst('Waterfall_Medium', f'Arcade_{side}_Waterfall{b}', 'WATERFALLS', lip + Vector((0, 0, 0.2)),
                     a + math.pi / 2, 0.9)


def build_castle_base():
    rnd = random.Random(1717)
    coll(C, 'TOWER_OF_PETS')
    build_stairs_and_landing(rnd)
    build_gatehouse(rnd)
    build_portal(rnd)
    build_upper_gate(rnd)
    build_foundation_masonry(rnd)
