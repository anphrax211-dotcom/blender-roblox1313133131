"""Generate the 9 voxel boss eggs in the same style as the existing
Celestial / Ember / Meadow eggs.

Conventions copied from the existing exports:
  * Z up, egg sits on z=0, 1.68 wide x 1.96 tall, 0.07 voxel grid
  * emblem on the front (-Y), raised to y=-0.98 / -1.04
  * one mesh object per material, named  <Egg>_<Part>__<Egg>_<Material>
  * material names are <Egg>_<Material>, colours listed in palette.json

Run inside Blender (Scripting tab) or headless:
    blender -b -P boss_eggs.py -- --out ../exports
    python3 boss_eggs.py --out ../exports          (with the `bpy` pip module)
Optional: --only Rainhound,Magmaw   --blend (also save a .blend per egg)
"""
import bpy, bmesh, math, random, sys, os, json, argparse
from collections import defaultdict
from mathutils import Vector, Matrix

VOX = 0.07
HALF = 12          # 24 voxels across
LAYERS = 28        # 28 voxels tall -> 1.96
ZW = 0.84          # height of widest point
RMAX = 0.84


# --------------------------------------------------------------------------
# egg shape
def egg_r(z):
    if z < ZW:
        t = (z - ZW) / ZW
    else:
        t = (z - ZW) / (1.96 - ZW)
    return RMAX * math.sqrt(max(0.0, 1 - t * t))


def egg_normal(x, y, z):
    h = ZW if z < ZW else (1.96 - ZW)
    n = Vector((x / RMAX ** 2, y / RMAX ** 2, (z - ZW) / h ** 2))
    return n.normalized()


def surf(phi, z, off=0.0):
    """Point on the egg surface. phi=0 is the front (-Y), +90deg is +X."""
    r = egg_r(z) + off
    x, y = r * math.sin(phi), -r * math.cos(phi)
    return Vector((x, y, z)), egg_normal(x, y, z)


def hsh(*a):
    h = 2166136261
    for v in a:
        h = ((h ^ (int(v) & 0xffffffff)) * 16777619) & 0xffffffff
    h ^= h >> 13
    h = (h * 1274126177) & 0xffffffff
    return (h & 0xffffff) / float(0x1000000)


def noise(x, y, z, s=0):
    return (math.sin(x * 3.1 + s) * math.sin(y * 2.7 + s * 1.7) +
            math.sin(z * 3.7 + x * 1.3 + s * 0.6) * 0.8 +
            math.sin((x + y) * 5.3 - z * 2.1 + s * 2.3) * 0.4) / 2.2


def zig(phi, n, amp):
    """stepped zig-zag around the egg"""
    t = (phi / (2 * math.pi) * n) % 1.0
    tri = 1 - abs(2 * t - 1)
    return round(tri * 3) / 3 * amp


class Ctx:
    """Info about a surface voxel passed to the body pattern."""
    def __init__(self, i, j, k, seed):
        self.x = (i + 0.5) * VOX
        self.y = (j + 0.5) * VOX
        self.z = (k + 0.5) * VOX
        self.phi = math.atan2(self.x, -self.y)          # 0 front, +-pi back
        self.k = k
        row = k // 2
        cols = 26
        col = math.floor((self.phi / (2 * math.pi) + 0.5) * cols + (0.5 if row % 2 else 0))
        self.brick = hsh(row, col, seed)
        self.brick2 = hsh(row, col, seed + 99)
        self.seed = seed

    def shade(self, base, alt=None, p=0.25, alt2=None, p2=0.0):
        if alt and self.brick < p:
            return alt
        if alt2 and self.brick > 1 - p2:
            return alt2
        return base


def bands(c, v, table):
    for top, base, alt, p in table:
        if v < top:
            return c.shade(base, alt, p)
    return c.shade(*table[-1][1:3], table[-1][3])


class Cracks:
    def __init__(self, seed, n=16):
        rnd = random.Random(seed)
        self.pts = []
        for _ in range(n):
            v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
            self.pts.append(v)

    def edge(self, c):
        p = Vector((c.x / RMAX, c.y / RMAX, (c.z - ZW) / 1.0)).normalized()
        d = sorted((p - q).length for q in self.pts)
        return d[1] - d[0]


# --------------------------------------------------------------------------
# mesh accumulation
class Builder:
    def __init__(self, prefix):
        self.P = prefix
        self.parts = defaultdict(lambda: ([], []))

    def key(self, part, mat):
        return (part, mat)

    def add(self, part, mat, verts, faces):
        V, F = self.parts[(part, mat)]
        o = len(V)
        V.extend(Vector(v) for v in verts)
        F.extend(tuple(i + o for i in f) for f in faces)

    def box(self, part, mat, c, size, rot=None):
        sx, sy, sz = (size, size, size) if isinstance(size, (int, float)) else size
        m = rot.to_matrix() if rot is not None and hasattr(rot, 'to_matrix') else (rot or Matrix.Identity(3))
        vs = []
        for dx in (-1, 1):
            for dy in (-1, 1):
                for dz in (-1, 1):
                    vs.append(Vector(c) + m @ Vector((dx * sx / 2, dy * sy / 2, dz * sz / 2)))
        F = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        self.add(part, mat, vs, F)

    def beam(self, part, mat, a, b, w, h=None, pad=0.35):
        """box from a to b; pad extends each end by pad*w so joints close up"""
        a, b = Vector(a), Vector(b)
        d = b - a
        q = d.to_track_quat('Z', 'Y')
        self.box(part, mat, (a + b) / 2, (w, h or w, d.length + 2 * pad * w), q)

    def crystal(self, part, mat, base, direction, length, radius, sides=4, spin=0.0):
        d = Vector(direction).normalized()
        q = d.to_track_quat('Z', 'Y').to_matrix()
        base = Vector(base)
        vs = []
        for ring, (t, r) in enumerate(((-0.15, radius * 0.55), (0.45, radius))):
            for s in range(sides):
                a = spin + s / sides * 2 * math.pi
                vs.append(base + q @ Vector((math.cos(a) * r, math.sin(a) * r, t * length)))
        vs.append(base + q @ Vector((0, 0, length)))
        tip = len(vs) - 1
        F = [tuple(reversed(range(sides)))]
        for s in range(sides):
            n = (s + 1) % sides
            F.append((s, n, sides + n, sides + s))
            F.append((sides + s, sides + n, tip))
        self.add(part, mat, vs, F)

    def sphere(self, part, mat, c, r, subdiv=1):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
        vs = [Vector(c) + v.co for v in bm.verts]
        F = [tuple(v.index for v in f.verts) for f in bm.faces]
        bm.free()
        self.add(part, mat, vs, F)

    def drop(self, part, mat, c, r):
        c = Vector(c)
        self.sphere(part, mat, c, r, 1)
        self.crystal(part, mat, c + Vector((0, 0, r * 0.3)), (0, 0, 1), r * 1.6, r * 0.8, 6)

    def mirror(self, fn):
        """call fn(sign, side) for both sides"""
        fn(-1, 'L')
        fn(1, 'R')

    # ---------------- voxel body ------------------------------------------
    def body(self, pattern, seed, bumps=0.03):
        solid = {}
        for k in range(LAYERS):
            z = (k + 0.5) * VOX
            r = egg_r(z) + 0.02
            for i in range(-HALF, HALF):
                for j in range(-HALF, HALF):
                    x, y = (i + 0.5) * VOX, (j + 0.5) * VOX
                    if x * x + y * y <= r * r:
                        solid[(i, j, k)] = None
        nb = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
        surface = [p for p in solid if any((p[0] + d[0], p[1] + d[1], p[2] + d[2]) not in solid for d in nb)]
        for p in surface:
            solid[p] = pattern(Ctx(*p, seed))
        # clean-up: a voxel whose colour no surface neighbour shares takes the
        # most common neighbour colour (removes lone speckles)
        for _ in range(2):
            fix = {}
            for p in surface:
                cnt = defaultdict(int)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            m = solid.get((p[0] + dx, p[1] + dy, p[2] + dz))
                            if m and (dx, dy, dz) != (0, 0, 0):
                                cnt[m] += 1
                if cnt and cnt.get(solid[p], 0) == 0:
                    fix[p] = max(cnt, key=cnt.get)
            solid.update(fix)
        # raised bricks for the chunky look
        rnd = random.Random(seed)
        for p in surface:
            c = Ctx(*p, seed)
            if 2 < p[2] < LAYERS - 3 and rnd.random() < bumps:
                n = egg_normal(c.x, c.y, c.z)
                if abs(n.z) < 0.6:
                    d = (1, 0) if abs(n.x) > abs(n.y) else (0, 1)
                    sx = int(math.copysign(1, n.x)) if d[0] else 0
                    sy = int(math.copysign(1, n.y)) if d[1] else 0
                    q = (p[0] + sx, p[1] + sy, p[2])
                    if q not in solid:
                        solid[q] = solid[p]
        # faces
        quads = {
            (1, 0, 0): ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)),
            (-1, 0, 0): ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)),
            (0, 1, 0): ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)),
            (0, -1, 0): ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)),
            (0, 0, 1): ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
            (0, 0, -1): ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)),
        }
        per_mat = defaultdict(lambda: ({}, []))
        for p, mat in solid.items():
            if mat is None:
                continue
            vidx, faces = per_mat[mat]
            for d, q in quads.items():
                if (p[0] + d[0], p[1] + d[1], p[2] + d[2]) in solid:
                    continue
                f = []
                for o in q:
                    key = (p[0] + o[0], p[1] + o[1], p[2] + o[2])
                    if key not in vidx:
                        vidx[key] = len(vidx)
                    f.append(vidx[key])
                faces.append(tuple(f))
        for mat, (vidx, faces) in per_mat.items():
            verts = [None] * len(vidx)
            for (i, j, k), n in vidx.items():
                verts[n] = (i * VOX, j * VOX, k * VOX)
            self.add('Body', mat, verts, faces)

    # ---------------- emblem ----------------------------------------------
    def emblem(self, fill_fn, core_fn, mats, zc=0.92, px=0.06, ext=0.48, outline=1, scale=0.85):
        """fill_fn/core_fn(x, z) -> bool in emblem-local coords.
        mats = (outline, fill, core).  Outline/core sit at y=-1.04, fill at -0.98."""
        n = int(ext / px)
        cells = {}
        for a in range(-n, n):
            for b in range(-n - 2, n + 2):
                x, z = (a + 0.5) * px / scale, (b + 0.5) * px / scale
                if fill_fn(x, z):
                    cells[(a, b)] = 'core' if core_fn and core_fn(x, z) else 'fill'
        fills = set(cells)
        for _ in range(outline):
            ring = set()
            for (a, b) in list(cells):
                for da in (-1, 0, 1):
                    for db in (-1, 0, 1):
                        if (a + da, b + db) not in cells:
                            ring.add((a + da, b + db))
            for r in ring:
                cells[r] = 'outline'
        depth = {'outline': -1.04, 'fill': -0.98, 'core': -1.04}
        mat = {'outline': mats[0], 'fill': mats[1], 'core': mats[2]}
        for (a, b), kind in cells.items():
            x0, x1 = a * px, (a + 1) * px
            z0, z1 = zc + b * px, zc + (b + 1) * px
            y0, y1 = depth[kind], -0.62
            m = mat[kind]
            V = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
                 (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
            F = [(0, 1, 2, 3)]
            # side walls only where the neighbour is lower or missing
            for (da, db), face in (((-1, 0), (4, 0, 3, 7)), ((1, 0), (1, 5, 6, 2)),
                                   ((0, -1), (4, 5, 1, 0)), ((0, 1), (3, 2, 6, 7))):
                nk = cells.get((a + da, b + db))
                if nk is None or depth[nk] > y0 + 1e-6:
                    F.append(face)
            self.add('Emblem', m, V, F)

    # ---------------- output ----------------------------------------------
    def build(self, palette):
        mats = {}
        for name, d in palette.items():
            m = bpy.data.materials.new(name)
            m.diffuse_color = (*d['rgb'], 1)
            nt = m.node_tree
            bsdf = nt.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value = (*d['rgb'], 1)
            bsdf.inputs['Metallic'].default_value = d['metal']
            bsdf.inputs['Roughness'].default_value = 0.35 if d['metal'] else 0.55
            if d['emit']:
                bsdf.inputs['Emission Color'].default_value = (*d['rgb'], 1)
                bsdf.inputs['Emission Strength'].default_value = d['emit']
            mats[name] = m
        coll = bpy.context.scene.collection
        objs = []
        for (part, mat), (V, F) in sorted(self.parts.items()):
            full = f'{self.P}_{mat}'
            name = f'{self.P}_{part}__{full}'
            me = bpy.data.meshes.new(name)
            me.from_pydata([tuple(v) for v in V], [], F)
            me.validate()
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me)
            bm.free()
            me.materials.append(mats[full])
            ob = bpy.data.objects.new(name, me)
            coll.objects.link(ob)
            objs.append(ob)
        return objs


# --------------------------------------------------------------------------
# geometry helpers for 2D emblem shapes
def poly(pts):
    def inside(x, z):
        c = False
        n = len(pts)
        for i in range(n):
            x1, z1 = pts[i]
            x2, z2 = pts[(i + 1) % n]
            if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
                c = not c
        return c
    return inside


def scaled(fn, s, dx=0.0, dz=0.0):
    return lambda x, z: fn((x - dx) / s, (z - dz) / s)


def circle(cx, cz, r):
    return lambda x, z: (x - cx) ** 2 + (z - cz) ** 2 <= r * r


def union(*fns):
    return lambda x, z: any(f(x, z) for f in fns)


def rect(x0, x1, z0, z1):
    return lambda x, z: x0 <= x <= x1 and z0 <= z <= z1


def C(r, g, b, emit=0.0, metal=0.0):
    return {'rgb': [r, g, b], 'emit': emit, 'metal': metal}


def stepped_fin(B, s, sd, light, mid, dark, length=1.05, height=1.1, z0=0.6, cells=10):
    """stepped triangular fin in the XZ plane on side s (-1 / 1)"""
    step = length / (cells - 1)
    for i in range(cells):
        for j in range(cells):
            u, v = i / (cells - 1), j / (cells - 1)      # u outward, v up
            top = 0.9 - 0.25 * u + 0.35 * u * u
            bot = 0.15 + 0.55 * u
            if bot <= v <= top:
                edge = v > top - 1.5 / cells
                m = light if edge else (dark if i % 3 == 2 else mid)
                B.box(f'Fin_{sd}', m, (s * (0.72 + u * length), 0.15, z0 + v * height),
                      (step * 1.02, 0.08, height / (cells - 1) * 1.02))


# ==========================================================================
#  EGGS
# ==========================================================================
EGGS = {}


def egg(fn):
    EGGS[fn.__name__] = fn
    return fn


# ---- 1. Rainhound (Lv 7): blue/white waves, lightning bolt, ears, raindrops
@egg
def Rainhound(B):
    pal = dict(Shell=C(0.02, 0.2, 0.72), ShellDark=C(0.01, 0.1, 0.45),
               Wave=C(0.08, 0.6, 1.0), WaveLight=C(0.4, 0.86, 1.0),
               Foam=C(0.92, 0.96, 1.0), FoamShade=C(0.7, 0.8, 0.93),
               BoltOutline=C(0.35, 0.8, 1.0, 0.8), Bolt=C(1.0, 0.86, 0.25, 1.6),
               BoltCore=C(1.0, 1.0, 0.85, 2.5), Ear=C(0.1, 0.5, 1.0),
               EarLight=C(0.45, 0.86, 1.0, 0.2), Droplet=C(0.4, 0.85, 1.0, 0.4))
    T = [(0.22, 'ShellDark', 'Shell', 0.3), (0.38, 'Wave', 'WaveLight', 0.2),
         (0.52, 'Foam', 'FoamShade', 0.2), (0.86, 'Shell', 'ShellDark', 0.25),
         (1.0, 'WaveLight', 'Wave', 0.25), (1.14, 'Foam', 'FoamShade', 0.2),
         (1.42, 'Shell', 'ShellDark', 0.25), (1.56, 'Wave', 'WaveLight', 0.2),
         (1.7, 'Foam', 'FoamShade', 0.2), (9, 'Shell', 'ShellDark', 0.25)]
    B.body(lambda c: bands(c, c.z + zig(c.phi, 8, 0.1), T), 7)
    bolt = poly([(0.06, 0.46), (-0.24, 0.0), (-0.03, 0.0), (-0.14, -0.46),
                 (0.25, 0.07), (0.04, 0.07), (0.2, 0.46)])
    B.emblem(bolt, scaled(bolt, 0.5, 0.0, 0.0), ('BoltOutline', 'Bolt', 'BoltCore'))

    def ears(s, side):
        p = f'Ear_{side}'
        base = Vector((s * 0.48, 0.05, 1.7))
        segs = [(Vector((s * 0.2, 0, 0.22)), 0.26), (Vector((s * 0.25, 0, 0.12)), 0.24),
                (Vector((s * 0.25, 0, -0.06)), 0.22), (Vector((s * 0.18, 0, -0.2)), 0.18)]
        a = base
        for n, (d, w) in enumerate(segs):
            b = a + d
            B.beam(p, 'EarLight' if n == len(segs) - 1 else 'Ear', a, b, w + 0.08, 0.26)
            a = b
    B.mirror(ears)
    for n, (x, y, z, r) in enumerate([(-1.15, -0.3, 0.55, 0.07), (-1.05, -0.5, 1.15, 0.06),
                                      (1.15, -0.3, 0.6, 0.07), (1.05, -0.5, 1.2, 0.06),
                                      (-0.95, -0.6, 0.15, 0.05), (0.95, -0.6, 0.18, 0.05)]):
        B.drop('Droplets', 'Droplet', (x, y, z), r)
    return pal


# ---- 2. Magmaw (Lv 10): brown rock, lava cracks, flame, crystal crown
@egg
def Magmaw(B):
    pal = dict(Rock=C(0.12, 0.07, 0.05), RockDark=C(0.06, 0.035, 0.03),
               Charcoal=C(0.05, 0.04, 0.038), Magma=C(1.0, 0.3, 0.02, 2.5),
               MagmaHot=C(1.0, 0.62, 0.05, 2.5), FlameOutline=C(0.85, 0.12, 0.02, 1.0),
               Flame=C(1.0, 0.45, 0.03, 1.6), FlameCore=C(1.0, 0.86, 0.25, 2.2),
               CrystalOrange=C(1.0, 0.32, 0.02, 0.8), CrystalYellow=C(1.0, 0.62, 0.05, 0.8))
    cr = Cracks(10, 14)

    def pat(c):
        e = cr.edge(c)
        if e < 0.035:
            return 'MagmaHot'
        if e < 0.08:
            return 'Magma'
        return c.shade('Rock', 'RockDark', 0.3, 'Charcoal', 0.2)
    B.body(pat, 10)
    flame = poly([(0, 0.5), (0.1, 0.26), (0.22, 0.34), (0.32, 0.05), (0.28, -0.22),
                  (0.15, -0.4), (0, -0.44), (-0.15, -0.4), (-0.28, -0.22), (-0.32, 0.05),
                  (-0.22, 0.34), (-0.1, 0.26)])
    B.emblem(flame, scaled(flame, 0.48, 0, -0.12), ('FlameOutline', 'Flame', 'FlameCore'))
    rnd = random.Random(10)
    for n in range(11):
        phi = n / 11 * 2 * math.pi + 0.15
        z = 1.62 + rnd.uniform(-0.08, 0.08)
        p, nrm = surf(phi, z, -0.05)
        d = (nrm + Vector((0, 0, 1.2))).normalized()
        B.crystal('Crystals', 'CrystalOrange' if n % 2 else 'CrystalYellow',
                  p, d, rnd.uniform(0.42, 0.6), 0.12, 4, rnd.random())
    for n in range(6):
        phi = (n / 6) * 2 * math.pi + 0.5
        p, nrm = surf(phi, 1.1 + 0.25 * (n % 2), -0.05)
        if abs(math.sin(phi / 2)) < 0.35:
            continue
        B.crystal('Crystals', 'CrystalOrange', p, nrm + Vector((0, 0, 0.5)), 0.4, 0.1, 4)
    B.crystal('Crystals', 'CrystalYellow', (0, 0, 1.85), (0, 0, 1), 0.65, 0.15, 4, 0.4)
    return pal


# ---- 3. Crystaltusk (Lv 13): white/blue, ice crystals, tusks
@egg
def Crystaltusk(B):
    pal = dict(Shell=C(0.04, 0.28, 0.85), ShellDark=C(0.02, 0.15, 0.6),
               Snow=C(0.92, 0.95, 1.0), SnowShade=C(0.7, 0.78, 0.9),
               Ice=C(0.3, 0.75, 1.0, 0.4), IceLight=C(0.7, 0.92, 1.0, 0.4),
               Tusk=C(0.93, 0.95, 0.98), TuskShade=C(0.68, 0.75, 0.86),
               GemOutline=C(0.05, 0.45, 0.95, 0.6), Gem=C(0.25, 0.8, 1.0, 1.2),
               GemCore=C(0.8, 0.97, 1.0, 2.0))
    T = [(0.3, 'Shell', 'ShellDark', 0.3), (0.5, 'Snow', 'SnowShade', 0.25),
         (0.95, 'Shell', 'ShellDark', 0.25), (1.15, 'Snow', 'SnowShade', 0.25),
         (1.45, 'Shell', 'ShellDark', 0.25), (9, 'Snow', 'SnowShade', 0.3)]
    B.body(lambda c: bands(c, c.z + zig(c.phi, 6, 0.12), T), 13)
    dia = poly([(0, 0.44), (0.3, 0), (0, -0.44), (-0.3, 0)])
    B.emblem(dia, scaled(dia, 0.5), ('GemOutline', 'Gem', 'GemCore'))
    rnd = random.Random(13)
    for n in range(9):
        phi = (n - 4) / 4 * 1.9 + math.pi
        p, nrm = surf(phi, 1.75, -0.08)
        d = (nrm * 0.6 + Vector((0, 0, 1))).normalized()
        B.crystal('Crystals', 'IceLight' if n % 3 == 0 else 'Ice', p, d,
                  rnd.uniform(0.45, 0.7), 0.13, 4, rnd.random())
    B.crystal('Crystals', 'IceLight', (0, 0, 1.85), (0, 0, 1), 0.75, 0.16, 4)

    def side(s, sd):
        for z, ln in ((0.75, 0.55), (1.2, 0.45)):
            p, nrm = surf(s * math.pi / 2, z, -0.05)
            B.crystal('Crystals', 'Ice', p, nrm + Vector((0, 0, 0.3)), ln, 0.12, 4)
        # tusk: curved chain of shrinking blocks
        pts = []
        for t in range(7):
            a = t / 6
            pts.append(Vector((s * (0.78 + 0.55 * math.sin(a * 1.9)), -0.25 - 0.15 * a,
                               0.45 + 0.75 * a * a)))
        for t in range(6):
            w = 0.24 - t * 0.03
            B.beam(f'Tusk_{sd}', 'TuskShade' if t % 2 else 'Tusk', pts[t], pts[t + 1], w)
        B.crystal(f'Tusk_{sd}', 'Tusk', pts[-1], pts[-1] - pts[-2], 0.22, 0.08, 4)
    B.mirror(side)
    return pal


# ---- 4. Granitram (Lv 29): stone & moss, gold gem, curled ram horns
@egg
def Granitram(B):
    pal = dict(Stone=C(0.17, 0.095, 0.045), StoneDark=C(0.09, 0.05, 0.025),
               StoneGray=C(0.28, 0.26, 0.24), Moss=C(0.14, 0.58, 0.05),
               MossLight=C(0.35, 0.8, 0.1), Horn=C(0.3, 0.17, 0.08),
               HornDark=C(0.17, 0.09, 0.04), GemOutline=C(0.85, 0.4, 0.02, 0.6),
               Gem=C(1.0, 0.72, 0.08, 1.2), GemCore=C(1.0, 0.95, 0.5, 2.0))

    def pat(c):
        m = noise(c.x * 2.2, c.y * 2.2, c.z * 2.2, 3) + (c.z - 1.0) * 0.45
        if m > 0.32:
            return c.shade('Moss', 'MossLight', 0.35)
        return c.shade('Stone', 'StoneGray', 0.25, 'StoneDark', 0.25)
    B.body(pat, 29, 0.1)
    hexa = poly([(0.36 * math.sin(a), 0.4 * math.cos(a)) for a in
                 [i * math.pi / 3 for i in range(6)]])
    B.emblem(hexa, scaled(hexa, 0.5), ('GemOutline', 'Gem', 'GemCore'))

    def horn(s, sd):
        cx, cz = s * 1.0, 1.42
        pts, n = [], 16
        for t in range(n + 1):
            a = t / n
            ang = math.radians(110 - 300 * a)   # start above, sweep out, down, back in
            r = 0.5 - 0.3 * a
            pts.append(Vector((cx - s * r * math.cos(ang) * -1, 0.05 - 0.25 * a,
                               cz + r * math.sin(ang))))
        pts[0] = Vector((s * 0.45, 0.1, 1.72))
        for t in range(n):
            w = 0.34 - 0.2 * t / n
            B.beam(f'Horn_{sd}', 'HornDark' if t % 3 == 2 else 'Horn', pts[t], pts[t + 1] , w)
        for t in (2, 5, 9):
            B.box(f'Horn_{sd}', 'MossLight', pts[t] + Vector((0, 0, 0.13)), (0.14, 0.14, 0.08))
    B.mirror(horn)
    return pal


# ---- 5. Pyrocrow (Lv 37): red/charcoal, phoenix emblem, feather wings
@egg
def Pyrocrow(B):
    pal = dict(Charcoal=C(0.06, 0.04, 0.04), CharcoalDark=C(0.03, 0.022, 0.022),
               Red=C(0.75, 0.05, 0.03), RedDark=C(0.45, 0.02, 0.02),
               EmblemOutline=C(1.0, 0.35, 0.02, 1.0), Emblem=C(1.0, 0.75, 0.1, 1.5),
               EmblemCore=C(1.0, 0.95, 0.6, 2.2), FeatherRed=C(0.85, 0.06, 0.03, 0.2),
               FeatherOrange=C(1.0, 0.35, 0.02, 0.4), FeatherYellow=C(1.0, 0.68, 0.05, 0.6))

    def pat(c):
        v = c.z + 0.28 * (1 - math.cos(c.phi))
        for lo, hi in ((0.25, 0.4), (0.8, 0.95), (1.35, 1.5), (1.8, 9)):
            if lo <= v < hi:
                return c.shade('Red', 'RedDark', 0.3)
        return c.shade('Charcoal', 'CharcoalDark', 0.3, 'RedDark', 0.08)
    B.body(pat, 37)
    bird = poly([(0, 0.36), (0.06, 0.26), (0.06, 0.14), (0.2, 0.26), (0.4, 0.32),
                 (0.33, 0.16), (0.4, 0.13), (0.27, 0.01), (0.33, -0.02), (0.13, -0.1),
                 (0.17, -0.38), (0, -0.25), (-0.17, -0.38), (-0.13, -0.1), (-0.33, -0.02),
                 (-0.27, 0.01), (-0.4, 0.13), (-0.33, 0.16), (-0.4, 0.32), (-0.2, 0.26),
                 (-0.06, 0.14), (-0.06, 0.26)])
    B.emblem(bird, circle(0, 0.02, 0.08), ('EmblemOutline', 'Emblem', 'EmblemCore'))

    def wing(s, sd):
        root = Vector((s * 0.72, 0.2, 1.15))
        for f in range(9):
            ang = math.radians(-15 + f * 10)
            ln = 0.65 + 0.55 * math.sin(f / 8 * math.pi * 0.85)
            d = Vector((s * math.cos(ang), 0.05, math.sin(ang)))
            a = root + Vector((0, 0.03 * f, 0.03 * f))
            cols = ('FeatherRed', 'FeatherOrange', 'FeatherYellow')
            seg = [0.0, 0.45, 0.78, 1.0]
            for n in range(3):
                p0, p1 = a + d * ln * seg[n], a + d * ln * seg[n + 1]
                B.beam(f'Wing_{sd}', cols[n], p0, p1, 0.26 - 0.05 * n, 0.09)
            B.crystal(f'Wing_{sd}', 'FeatherYellow', a + d * ln, d, 0.22, 0.1, 4)
    B.mirror(wing)
    rnd = random.Random(37)
    for n in range(7):
        x = (n - 3) * 0.13
        ln = 0.6 - abs(n - 3) * 0.1
        B.crystal('Crest', 'FeatherOrange' if n % 2 else 'FeatherRed',
                  (x, 0.0, 1.82 - abs(x) * 0.5), (x * 1.2, 0.05, 1), ln, 0.12, 4, rnd.random())
    return pal


# ---- 6. Volcanox (Lv 45): charcoal, glowing lava veins, crystals everywhere
@egg
def Volcanox(B):
    pal = dict(Charcoal=C(0.045, 0.04, 0.04), CharcoalDark=C(0.02, 0.018, 0.018),
               Ash=C(0.11, 0.1, 0.1), Magma=C(1.0, 0.36, 0.02, 2.5),
               MagmaHot=C(1.0, 0.75, 0.08, 2.8), CoreOutline=C(1.0, 0.32, 0.02, 1.2),
               Core=C(1.0, 0.65, 0.05, 2.0), CoreHot=C(1.0, 0.95, 0.45, 3.0),
               CrystalOrange=C(1.0, 0.32, 0.02, 0.8), CrystalYellow=C(1.0, 0.62, 0.05, 0.8),
               Spark=C(1.0, 0.55, 0.05, 3.0))
    cr = Cracks(45, 10)

    def pat(c):
        e = cr.edge(c)
        if e < 0.045:
            return 'MagmaHot'
        if e < 0.1:
            return 'Magma'
        return c.shade('Charcoal', 'CharcoalDark', 0.3, 'Ash', 0.2)
    B.body(pat, 45, 0.1)
    star = union(rect(-0.18, 0.18, -0.4, 0.4), rect(-0.36, 0.36, -0.2, 0.2),
                 rect(-0.28, 0.28, -0.3, 0.3))
    B.emblem(star, circle(0, 0, 0.15), ('CoreOutline', 'Core', 'CoreHot'))
    rnd = random.Random(45)
    for n in range(20):
        phi = n / 20 * 2 * math.pi + rnd.uniform(-0.1, 0.1)
        if abs(math.sin(phi / 2)) < 0.3:     # keep the emblem clear
            continue
        z = rnd.choice((0.55, 0.95, 1.35, 1.7)) + rnd.uniform(-0.1, 0.1)
        p, nrm = surf(phi, z, -0.05)
        d = (nrm + Vector((0, 0, 0.6))).normalized()
        B.crystal('Crystals', 'CrystalYellow' if n % 3 == 0 else 'CrystalOrange',
                  p, d, rnd.uniform(0.32, 0.55), rnd.uniform(0.09, 0.13), 4, rnd.random())
    for n in range(5):
        x = (n - 2) * 0.2
        B.crystal('Crystals', 'CrystalOrange' if n % 2 else 'CrystalYellow',
                  (x, 0.05, 1.83 - abs(x) * 0.4), (x, 0, 1), 0.55 - abs(n - 2) * 0.08, 0.13, 4)
    for n in range(10):
        a = n / 10 * 2 * math.pi
        B.box('Sparks', 'Spark', (1.25 * math.sin(a), -0.3 - 0.3 * math.cos(a),
                                  0.3 + rnd.random() * 2.0), 0.07)
    return pal


# ---- 7. Abyssray (Lv 59): deep blue waves, clam + pearl, crystal fins, bubbles
@egg
def Abyssray(B):
    pal = dict(Shell=C(0.01, 0.12, 0.5), ShellDark=C(0.005, 0.06, 0.3),
               Wave=C(0.05, 0.55, 0.95), WaveLight=C(0.3, 0.82, 1.0),
               Foam=C(0.92, 0.96, 1.0), ClamOutline=C(0.62, 0.68, 0.8),
               Clam=C(0.92, 0.92, 0.96), Pearl=C(0.98, 0.95, 1.0, 0.5),
               Fin=C(0.15, 0.7, 1.0, 0.2), FinLight=C(0.55, 0.9, 1.0, 0.3),
               FinDark=C(0.03, 0.35, 0.85), Bubble=C(0.4, 0.85, 1.0, 0.4))
    T = [(0.3, 'ShellDark', 'Shell', 0.3), (0.45, 'Wave', 'WaveLight', 0.2),
         (0.7, 'Shell', 'ShellDark', 0.25), (0.82, 'Foam', None, 0),
         (1.05, 'Shell', 'ShellDark', 0.25), (1.2, 'Wave', 'WaveLight', 0.2),
         (1.42, 'Shell', 'ShellDark', 0.25), (1.55, 'Foam', None, 0),
         (1.72, 'Wave', 'WaveLight', 0.25), (9, 'Shell', 'ShellDark', 0.25)]
    B.body(lambda c: bands(c, c.z - 0.18 * math.cos(c.phi) + zig(c.phi, 10, 0.07), T), 59)
    clam = union(lambda x, z: z >= -0.2 and x * x + (z + 0.2) ** 2 <= 0.4 ** 2,
                 rect(-0.12, 0.12, -0.34, -0.2))
    pearl = circle(0, -0.05, 0.17)
    B.emblem(clam, pearl, ('ClamOutline', 'Clam', 'Pearl'))
    for a in (-60, -25, 25, 60):          # shell ridges
        d = Vector((math.sin(math.radians(a)), 0, math.cos(math.radians(a))))
        o = Vector((0, -1.0, 0.92 - 0.17))
        B.beam('Emblem', 'ClamOutline', o + d * 0.17, o + d * 0.33, 0.05, 0.05, 0)

    B.mirror(lambda s, sd: stepped_fin(B, s, sd, 'FinLight', 'Fin', 'FinDark'))
    rnd = random.Random(59)
    for x, y, z, r in [(-0.9, -0.4, 2.05, 0.09), (0.95, -0.35, 2.15, 0.08), (-0.55, -0.6, 2.35, 0.06),
                       (0.6, -0.55, 2.3, 0.06), (-1.3, -0.4, 0.35, 0.09), (1.3, -0.4, 0.4, 0.08),
                       (-1.05, -0.6, 0.15, 0.05), (1.1, -0.65, 0.12, 0.05), (0.0, -0.3, 2.4, 0.05)]:
        B.sphere('Bubbles', 'Bubble', (x, y, z), r, 1)
    return pal


# ---- 8. Bogtoad (Lv 65): soil & dripping slime, crown emblem, lily pad, fins
@egg
def Bogtoad(B):
    pal = dict(Soil=C(0.16, 0.08, 0.03), SoilDark=C(0.09, 0.045, 0.018),
               Moss=C(0.12, 0.48, 0.04), Slime=C(0.35, 0.85, 0.08, 0.3),
               SlimeLight=C(0.6, 0.95, 0.2, 0.4), LilyPad=C(0.1, 0.6, 0.05),
               LilyPadDark=C(0.05, 0.38, 0.03), Fin=C(0.3, 0.75, 0.08, 0.1),
               FinDark=C(0.12, 0.45, 0.04), EmblemOutline=C(0.05, 0.4, 0.03, 0.3),
               Emblem=C(0.45, 0.95, 0.15, 1.2), EmblemCore=C(0.95, 1.0, 0.4, 2.0))

    def pat(c):
        col = math.floor((c.phi / (2 * math.pi) + 0.5) * 30)
        drip = hsh(col, 65) * 0.45
        if c.z > 1.68 - drip:
            return c.shade('Slime', 'SlimeLight', 0.3)
        if noise(c.x * 3, c.y * 3, c.z * 3, 5) > 0.45:
            return 'Moss'
        return c.shade('Soil', 'SoilDark', 0.35)
    B.body(pat, 65)
    crown = poly([(-0.34, -0.3), (0.34, -0.3), (0.34, 0.3), (0.18, 0.04), (0, 0.38),
                  (-0.18, 0.04), (-0.34, 0.3)])
    B.emblem(crown, scaled(crown, 0.5, 0, -0.05), ('EmblemOutline', 'Emblem', 'EmblemCore'))
    # lily pad on top, notched at the front
    for i in range(-8, 8):
        for j in range(-8, 8):
            x, y = (i + 0.5) * 0.08, (j + 0.5) * 0.08
            d = math.hypot(x, y)
            if d > 0.62 or (y < 0 and abs(x) < 0.06 + (-y) * 0.15):
                continue
            m = 'LilyPadDark' if d > 0.5 else 'LilyPad'
            B.box('LilyPad', m, (x, y, 1.98 - 0.08 * (d > 0.42)), (0.08, 0.08, 0.1))
    B.box('LilyPad', 'LilyPadDark', (0, 0, 1.9), (0.3, 0.3, 0.1))
    rnd = random.Random(65)
    for n in range(9):
        phi = rnd.uniform(-math.pi, math.pi)
        if abs(math.sin(phi / 2)) < 0.3:
            continue
        p, nrm = surf(phi, rnd.uniform(0.4, 1.5), 0.02)
        B.sphere('SlimeBlobs', 'SlimeLight', p, rnd.uniform(0.09, 0.14), 1)

    B.mirror(lambda s, sd: stepped_fin(B, s, sd, 'Fin', 'Fin', 'FinDark',
                                       length=0.6, height=0.65, z0=0.55, cells=6))
    return pal


# ---- 9. Elderstag (Lv 75): forest green with gold bands, leaf emblem, antlers
@egg
def Elderstag(B):
    pal = dict(Shell=C(0.03, 0.3, 0.06), ShellDark=C(0.015, 0.17, 0.035),
               Leaf=C(0.15, 0.6, 0.08), Gold=C(1.0, 0.72, 0.15, 0.0, 1.0),
               GoldDark=C(0.75, 0.45, 0.08, 0.0, 1.0), Ivory=C(0.92, 0.92, 0.85),
               Antler=C(0.33, 0.19, 0.08), AntlerDark=C(0.2, 0.11, 0.05),
               LeafCrystal=C(0.3, 0.85, 0.15, 0.3), EmblemOutline=C(0.75, 0.45, 0.08, 0.5),
               Emblem=C(1.0, 0.8, 0.3, 1.4), EmblemCore=C(1.0, 0.95, 0.7, 2.0))

    def pat(c):
        v = c.z - 0.15 * math.cos(c.phi)
        for lo, hi in ((0.3, 0.46), (1.32, 1.48)):
            if lo <= v < hi:
                return c.shade('Gold', 'Ivory', 0.3, 'GoldDark', 0.2)
        if noise(c.x * 2.5, c.y * 2.5, c.z * 2.5, 9) > 0.4:
            return 'Leaf'
        return c.shade('Shell', 'ShellDark', 0.3)
    B.body(pat, 75)
    leaf = poly([(0, 0.44), (0.08, 0.26), (0.24, 0.32), (0.18, 0.12), (0.34, 0.06),
                 (0.15, -0.04), (0.21, -0.2), (0.05, -0.12), (0.05, -0.42), (-0.05, -0.42),
                 (-0.05, -0.12), (-0.21, -0.2), (-0.15, -0.04), (-0.34, 0.06), (-0.18, 0.12),
                 (-0.24, 0.32), (-0.08, 0.26)])
    B.emblem(leaf, lambda x, z: abs(x) < 0.035 and -0.35 < z < 0.3,
             ('EmblemOutline', 'Emblem', 'EmblemCore'))

    def antler(s, sd):
        p = f'Antler_{sd}'
        S = lambda x, y, z: Vector((s * x, y, z))
        main = [S(0.4, 0.05, 1.72), S(0.62, 0.05, 2.05), S(0.85, 0.05, 2.35),
                S(1.05, 0.05, 2.62), S(1.15, 0.05, 2.85)]
        for n in range(len(main) - 1):
            B.beam(p, 'AntlerDark' if n % 2 else 'Antler', main[n], main[n + 1], 0.17 - 0.025 * n)
        tines = [(main[1], S(0.48, 0.05, 2.4)), (main[2], S(0.68, 0.05, 2.75)),
                 (main[3], S(1.4, 0.05, 2.7)), (main[1], S(1.0, 0.05, 2.0))]
        for a, b in tines:
            B.beam(p, 'Antler', a, b, 0.11)
        for a, b in tines + [(main[-2], main[-1])]:
            d = (b - a).normalized()
            B.crystal('Leaves', 'LeafCrystal', b + Vector((0, 0, -0.05)),
                      Vector((d.x * 0.3, 0, -1)), 0.32, 0.09, 4)
        for z in (0.7, 1.15):
            q, nrm = surf(s * 1.45, z, 0.0)
            B.crystal('Leaves', 'LeafCrystal', q + nrm * 0.15, Vector((s * 0.2, 0, -1)), 0.3, 0.08, 4)
    B.mirror(antler)
    return pal


# ==========================================================================
def generate(name, out, blend=False, eggs=None, suffix='BossEgg'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    B = Builder(name)
    pal = (eggs or EGGS)[name](B)
    palette = {f'{name}_{k}': v for k, v in pal.items()}
    B.build(palette)
    path = os.path.join(out, f'{name}{suffix}.fbx')
    bpy.ops.export_scene.fbx(filepath=path, use_selection=False, object_types={'MESH'},
                             mesh_smooth_type='FACE', apply_unit_scale=True)
    if blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f'{name}{suffix}.blend'))
    faces = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    print(f'{name}: {len(bpy.data.objects)} meshes, {faces} faces -> {path}')
    return palette


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'exports'))
    ap.add_argument('--only', default='')
    ap.add_argument('--blend', action='store_true')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    names = [n for n in EGGS if not a.only or n in a.only.split(',')]
    allpal = {}
    for n in names:
        allpal.update(generate(n, a.out, a.blend))
    with open(os.path.join(a.out, 'boss_palette.json'), 'w') as f:
        json.dump(allpal, f, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
