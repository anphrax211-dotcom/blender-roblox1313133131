"""SPOOKY HARVEST - Halloween event market stall for Roblox, built from the stall reference image.

Every part is defined once, in Roblox space (studs, Y up, the stall's front faces -Z), and emitted as:
    exports/SpookyHarvestStall/BuildSpookyHarvestStall.lua   paste into the Studio Command Bar -> builds the model
    previews/SpookyHarvest_*.png                             Blender preview renders of the same part list

Only native Roblox features are used, so nothing has to be uploaded: Parts (Block / Ball / Cylinder),
SpecialMesh spheres for the rounded pumpkins, the WoodPlanks / Wood / Fabric / Metal / Glass / Neon materials,
a SurfaceGui for the sign text and a few soft PointLights.

    python3 spooky_stall.py              write the Lua builder
    python3 spooky_stall.py --render     also render the Blender previews (needs the `bpy` module)
"""
import math, os, sys, random
import bpy  # noqa: F401  (provides mathutils when run with the bpy pip module)
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'exports', 'SpookyHarvestStall')
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
I3 = Matrix.Identity(3)

# palette (sRGB 0-255)
WOOD_DARK = (74, 47, 30)        # posts, beams, counter top
WOOD = (101, 66, 41)            # planks
WOOD_B = (90, 58, 36)
WOOD_C = (112, 74, 46)
WOOD_TRIM = (150, 92, 48)       # carved trim boards
IRON = (46, 43, 41)
GOLD = (232, 170, 58)
PURPLE = (112, 52, 150)
PURPLE_DARK = (82, 36, 112)
ORANGE_CLOTH = (236, 132, 40)
ORANGE_DARK = (196, 98, 26)
PUMPKIN = (226, 108, 26)
PUMPKIN_B = (208, 94, 22)
GLOW = (255, 166, 64)
GLOW_DIM = (236, 128, 40)
VINE = (58, 104, 44)
VINE_DARK = (44, 82, 34)
WEB = (232, 230, 222)
LEAF_COLS = [(222, 84, 26), (236, 128, 30), (246, 170, 44), (196, 58, 26), (232, 104, 28)]


def rot(rx=0.0, ry=0.0, rz=0.0):
    """CFrame.Angles(rx, ry, rz) in degrees (Rx * Ry * Rz)"""
    return (Matrix.Rotation(math.radians(rx), 3, 'X') @ Matrix.Rotation(math.radians(ry), 3, 'Y')
            @ Matrix.Rotation(math.radians(rz), 3, 'Z'))


def axes(x_axis, up_hint=Y):
    """rotation whose local X points along x_axis (Roblox cylinders run along X)"""
    x = x_axis.normalized()
    if abs(x.dot(up_hint)) > 0.98:
        up_hint = Z
    z = x.cross(up_hint).normalized()
    y = z.cross(x).normalized()
    return Matrix((x, y, z)).transposed()


def basis(right, up):
    """rotation with local X = right and local Y = up (local Z completes the frame, Z = X x Y)"""
    r = right.normalized()
    u = (up - up.dot(r) * r).normalized()
    return Matrix((r, u, r.cross(u))).transposed()


class Stall:
    def __init__(self):
        self.parts = []
        self.rng = random.Random(31)

    def part(self, path, name, size, pos, R=None, color=WOOD, material='WoodPlanks', shape='Block',
             transparency=0.0, collide=True, mesh=None, light=None, sign=False, shadow=True):
        self.parts.append(dict(path=path, name=name, size=Vector(size), pos=Vector(pos), R=(R or I3).copy(),
                               color=color, material=material, shape=shape, transparency=transparency,
                               collide=collide, mesh=mesh, light=light, sign=sign, shadow=shadow))

    def deco(self, path, name, size, pos, R=None, color=WOOD, material='SmoothPlastic', **kw):
        """non-colliding decoration"""
        kw.setdefault('collide', False)
        self.part(path, name, size, pos, R, color, material, **kw)

    def rod(self, path, name, a, b, d, color=IRON, material='Metal', collide=False, **kw):
        a, b = Vector(a), Vector(b)
        self.part(path, name, ((b - a).length, d, d), (a + b) / 2, axes(b - a), color, material, 'Cylinder',
                  collide=collide, **kw)

    def ellipsoid(self, path, name, size, pos, R=None, color=PUMPKIN, material='SmoothPlastic', **kw):
        kw.setdefault('collide', False)
        self.part(path, name, size, pos, R, color, material, mesh='Sphere', **kw)

    def jitter(self, c, k=6):
        return tuple(max(0, min(255, v + self.rng.randint(-k, k))) for v in c)


# ------------------------------------------------------------------ decorations
CARVED = (150, 62, 16)            # carved rim around the glowing cut-outs
CARVE_GLOW = (232, 124, 34)       # dimmed Neon inside the carved face (warm, not blinding)


def _wedge_frame(right, up, side):
    """WedgePart frame for one half of a flat triangle facing the viewer.
    A WedgePart's triangular faces are its +-X sides: the right angle sits at local (-Y, +Z), the other
    corners at (-Y, -Z) and (+Y, +Z). side = +1 puts the right angle on the inner (centre) edge of a right half,
    -1 mirrors it for the left half."""
    zl = -right * side
    return Matrix((up.cross(zl), up, zl)).transposed()


def pumpkin(s, path, c, w, h, face=True, glow=True, light=0.0, ry=0.0, depth=1.0, stem=True):
    """squat pumpkin: core + 8 lobes (sphere meshes), curved stem with a tendril, and a carved jack-o'-lantern
    face (triangle eyes and nose, grin with upturned corners and two teeth) laid on the outer surface"""
    c = Vector(c)
    Ry = rot(0, ry, 0)
    ells = []

    def ell(name, centre, Rl, size, col, **kw):
        s.ellipsoid(path, name, size, c + Ry @ centre, Ry @ Rl, col, **kw)
        ells.append((centre, Rl, Vector(size) / 2))
    ell('Core', Vector(), I3, (w * 0.8, h * 0.9, w * 0.8 * depth), PUMPKIN_B,
        light=(GLOW, light, w * 3.2) if light else None)
    for k in range(8):
        a = math.radians(-90 + 45 * k)
        sa, ca = abs(math.sin(a)), abs(math.cos(a))
        radial = w * 0.5 * (1 - (1 - depth) * sa)
        tang = w * 0.43 * (1 - (1 - depth) * ca)
        centre = Vector((math.cos(a) * w * 0.27, 0, math.sin(a) * w * 0.27 * depth))
        ell(f'Lobe{k + 1}', centre, rot(0, 90 - math.degrees(a), 0), (tang, h * (1.0 if k % 2 == 0 else 0.95), radial),
            PUMPKIN if k % 2 == 0 else PUMPKIN_B)
    if stem:
        base = c + Vector((0, h * 0.42, 0))
        pts = [base, base + Ry @ Vector((0.0, h * 0.14, 0)), base + Ry @ Vector((w * 0.04, h * 0.25, 0)),
               base + Ry @ Vector((w * 0.1, h * 0.31, 0))]
        for i in range(3):
            s.rod(path, f'Stem{i + 1}', pts[i], pts[i + 1], w * (0.15 - 0.03 * i), (86, 104, 42), 'Wood')
        tip = pts[1]
        prev = None
        for i in range(15):                                   # smooth curling tendril
            t = i / 14
            a = 2.6 * math.pi * t
            r = w * (0.13 - 0.08 * t)
            q = tip + Ry @ Vector((-w * 0.13 - math.cos(a) * r + w * 0.13, h * 0.02 + math.sin(a) * r * 0.8, -w * 0.05))
            if prev is not None:
                s.rod(path, f'Tendril{i}', prev, q, w * 0.03, VINE, 'SmoothPlastic', shadow=False)
            prev = q
    if not face:
        return

    def hit(u, v):
        """front surface point and normal (pumpkin-local) at face coords (u, v): first lobe hit by a ray along +Z"""
        o, d = Vector((u, v, -10.0)), Vector((0, 0, 1.0))
        best = None
        for centre, Rl, r in ells:
            ol = Rl.transposed() @ (o - centre)
            dl = Rl.transposed() @ d
            os_, ds = Vector((ol.x / r.x, ol.y / r.y, ol.z / r.z)), Vector((dl.x / r.x, dl.y / r.y, dl.z / r.z))
            A, B, C = ds.dot(ds), 2 * os_.dot(ds), os_.dot(os_) - 1
            disc = B * B - 4 * A * C
            if disc < 0:
                continue
            t = (-B - math.sqrt(disc)) / (2 * A)
            if best is None or t < best[0]:
                pl = ol + dl * t
                nl = Vector((pl.x / r.x ** 2, pl.y / r.y ** 2, pl.z / r.z ** 2))
                best = (t, o + d * t, (Rl @ nl).normalized())
        return best[1], best[2]

    glow_col, glow_mat = (CARVE_GLOW, 'Neon') if glow else ((70, 30, 12), 'SmoothPlastic')

    def frame_at(u, v):
        p, n = hit(u, v)
        right = (X - X.dot(n) * n).normalized()
        up = (Y - Y.dot(n) * n - Y.dot(right) * right).normalized()
        return p, n, right, up

    def put(name, size, p, R, col, mat, shape='Block'):
        s.deco(path, name, size, c + Ry @ p, Ry @ R, col, mat, shape=shape, shadow=False)

    def triangle(name, u, v, b, t, col, mat, lift):
        """isosceles triangle (apex up) with its base centred at (u, v): two mirrored WedgeParts sharing one frame"""
        p, n, right, up = frame_at(u, v + t / 2)
        for side, tag in ((1, 'R'), (-1, 'L')):
            put(f'{name}{tag}', (0.07, t, b / 2), p + n * lift + right * side * b / 4, _wedge_frame(right * side, up, 1),
                col, mat, 'Wedge')

    def grin(name, col, mat, lift, k):
        """crescent grin: five overlapping segments along a smile curve, tapered ends, upturned corner points"""
        wm, hm, vm = w * 0.52 * k, w * 0.12 * k, -h * 0.25
        n_seg = 5
        for i in range(n_seg):
            t = (i - (n_seg - 1) / 2) / ((n_seg - 1) / 2)          # -1 .. 1
            u = t * wm * 0.4
            v = vm + t * t * w * 0.07
            slope = 2 * t * w * 0.07 / (wm * 0.4)
            p, n, right, up = frame_at(u, v)
            R = Matrix((right, up, right.cross(up))).transposed() @ rot(0, 0, math.degrees(math.atan(slope)))
            put(f'{name}{i + 1}', (wm / n_seg * 1.35, hm * (1 - 0.35 * abs(t)), 0.07), p + n * lift, R, col, mat)
        for side, tag in ((1, 'L'), (-1, 'R')):                     # pointed corners rising out of the ends
            u = side * wm * 0.5
            p, n, right, up = frame_at(u, vm + w * 0.07 + hm * 0.25)
            R = _wedge_frame(-right * side, up, 1) @ rot(-side * 25, 0, 0)
            put(f'{name}Corner{tag}', (0.07, hm * 0.9, w * 0.09 * k), p + n * lift, R, col, mat, 'Wedge')

    for layer, col, mat, lift, k in (('Rim', CARVED, 'SmoothPlastic', 0.012, 1.18), ('Glow', glow_col, glow_mat, 0.03, 1.0)):
        for sx, tag in ((1, 'L'), (-1, 'R')):
            triangle(f'{layer}Eye{tag}', sx * w * 0.19, -(k - 1) * w * 0.025, w * 0.22 * k, w * 0.19 * k, col, mat, lift)
        triangle(f'{layer}Nose', 0, -h * 0.1 - (k - 1) * w * 0.015, w * 0.1 * k, w * 0.08 * k, col, mat, lift)
        grin(f'{layer}Grin', col, mat, lift, k)
    vm, hm = -h * 0.25, w * 0.12
    for tag, u, dv in (('ToothTop', -w * 0.07, hm * 0.32), ('ToothBottom', w * 0.08, -hm * 0.3)):
        v = vm + (u / (w * 0.21)) ** 2 * w * 0.07 + dv
        p, n, right, up = frame_at(u, v)
        put(tag, (w * 0.065, hm * 0.42, 0.07), p + n * 0.05, Matrix((right, up, right.cross(up))).transposed(),
            PUMPKIN, 'SmoothPlastic')


def leaf(s, path, c, n, size, color, spin=0.0):
    """maple leaf: five pointed (diamond) lobes fanned in the plane facing n, plus a stem"""
    n = Vector(n).normalized()
    up = Y if abs(n.dot(Y)) < 0.9 else Z
    right = up.cross(n)
    if right.length < 1e-6:
        right = X.copy()
    R0 = basis(right, n.cross(right)) @ rot(0, 0, spin)   # local Z = n
    for k, (ang, L) in enumerate(((0, 1.0), (58, 0.86), (-58, 0.86), (122, 0.55), (-122, 0.55))):
        R = R0 @ rot(0, 0, ang)
        p = Vector(c) + (R @ Y) * size * L * 0.36 + n * (0.006 * (k + 1))
        d = size * (0.36 + 0.12 * L)
        s.deco(path, f'Lobe{k + 1}', (d, d, 0.05), p, R @ rot(0, 0, 45), color, 'SmoothPlastic', shadow=False)
    s.deco(path, 'Centre', (size * 0.42, size * 0.42, 0.06), Vector(c) + n * 0.04, R0 @ rot(0, 0, 45), color, 'SmoothPlastic',
           shadow=False)
    s.deco(path, 'Stem', (size * 0.06, size * 0.45, 0.05), Vector(c) - (R0 @ Y) * size * 0.32, R0,
           (120, 60, 24), 'SmoothPlastic', shadow=False)


def leaves(s, path, spots):
    for i, (c, n, size) in enumerate(spots):
        leaf(s, f'{path}/@Leaf{i + 1}', c, n, size, LEAF_COLS[i % len(LEAF_COLS)], spin=(i * 47) % 360 - 180)


def vine(s, path, pts, d=0.16, color=VINE):
    for i in range(len(pts) - 1):
        s.rod(path, f'Vine{i + 1}', pts[i], pts[i + 1], d, color, 'SmoothPlastic')


def curl(s, path, c, r, right, up, turns=1.25, d=0.14, start=0.0):
    """flat spiral curl in the plane (right, up)"""
    pts = []
    steps = int(10 * turns)
    for i in range(steps + 1):
        t = i / steps
        a = start + t * turns * 2 * math.pi
        rr = r * (1 - 0.75 * t)
        pts.append(Vector(c) + Vector(right) * math.cos(a) * rr + Vector(up) * math.sin(a) * rr)
    vine(s, path, pts, d)


def cobweb(s, path, corner, d1, d2, L):
    """corner cobweb: radial strands between the two edge directions plus three sagging rings"""
    corner, d1, d2 = Vector(corner), Vector(d1).normalized(), Vector(d2).normalized()
    nstr = 6
    dirs = [(d1 * math.cos(t * math.pi / 2) + d2 * math.sin(t * math.pi / 2)).normalized()
            for t in [i / (nstr - 1) for i in range(nstr)]]
    for i, dv in enumerate(dirs):
        s.rod(path, f'Strand{i + 1}', corner, corner + dv * L, 0.035, WEB, 'SmoothPlastic', transparency=0.25,
              shadow=False)
    for ring, f in enumerate((0.38, 0.66, 0.92)):
        for i in range(nstr - 1):
            a = corner + dirs[i] * L * f
            b = corner + dirs[i + 1] * L * f
            mid = (a + b) / 2 - (dirs[i] + dirs[i + 1]).normalized() * L * f * 0.08
            s.rod(path, f'Ring{ring + 1}_{i + 1}a', a, mid, 0.03, WEB, 'SmoothPlastic', transparency=0.3, shadow=False)
            s.rod(path, f'Ring{ring + 1}_{i + 1}b', mid, b, 0.03, WEB, 'SmoothPlastic', transparency=0.3, shadow=False)


def bat(s, path, c, span, color=PURPLE, material='SmoothPlastic', flip=1, thick=0.12):
    """flat bat silhouette facing -Z: body, ears and scalloped wings"""
    c = Vector(c)
    s.ellipsoid(path, 'Body', (span * 0.16, span * 0.3, thick * 1.6), c, I3, color, material)
    s.ellipsoid(path, 'Head', (span * 0.14, span * 0.13, thick * 1.6), c + Vector((0, span * 0.17, 0)), I3, color,
                material)
    for sx in (-1, 1):
        s.deco(path, f'Ear{"L" if sx > 0 else "R"}', (span * 0.05, span * 0.09, thick),
               c + Vector((sx * span * 0.045, span * 0.25, 0)), rot(0, 0, -sx * 12), color, material)
        for k, (dx, dy, ln, ang) in enumerate(((0.17, 0.06, 0.26, 22), (0.33, 0.07, 0.2, -8), (0.43, 0.02, 0.14, -40))):
            s.deco(path, f'Wing{"L" if sx > 0 else "R"}{k + 1}', (span * ln, span * (0.17 - 0.03 * k), thick),
                   c + Vector((sx * span * dx, span * dy, 0)), rot(0, 0, sx * ang), color, material)


def hanging_lantern(s, path, top, chain, light=0.7):
    """iron lantern with warm glass panes hanging on a short chain"""
    top = Vector(top)
    links = max(2, int(chain / 0.28))
    for i in range(links):
        R = rot(0, 90 * (i % 2), 90)
        s.deco(path, f'Chain{i + 1}', (chain / links * 1.15, 0.12, 0.12), top + Vector((0, -i * chain / links - chain / links / 2, 0)),
               R, IRON, 'Metal', shape='Cylinder', shadow=False)
    c = top - Vector((0, chain + 0.75, 0))
    s.deco(path, 'Ring', (0.08, 0.32, 0.32), c + Vector((0, 0.78, 0)), rot(0, 90, 0), IRON, 'Metal', shape='Cylinder')
    s.deco(path, 'Cap', (0.22, 0.95, 0.95), c + Vector((0, 0.55, 0)), rot(0, 0, 90), IRON, 'Metal', shape='Cylinder')
    s.deco(path, 'Roof', (0.25, 0.6, 0.6), c + Vector((0, 0.72, 0)), rot(0, 0, 90), IRON, 'Metal', shape='Cylinder')
    s.deco(path, 'Glass', (0.62, 0.86, 0.62), c, I3, GLOW_DIM, 'Neon', transparency=0.15,
           light=(GLOW, light, 10))
    for sx in (-1, 1):
        for sz in (-1, 1):
            s.deco(path, f'Bar{"L" if sx > 0 else "R"}{"F" if sz < 0 else "B"}', (0.1, 0.98, 0.1),
                   c + Vector((sx * 0.33, 0, sz * 0.33)), I3, IRON, 'Metal')
    for k, (sz, R) in enumerate(((-0.33, I3), (0.33, I3))):
        s.deco(path, f'Mullion{k + 1}', (0.05, 0.9, 0.05), c + Vector((0, 0, sz)), R, IRON, 'Metal')
        s.deco(path, f'MullionSide{k + 1}', (0.05, 0.9, 0.05), c + Vector((sz, 0, 0)), R, IRON, 'Metal')
    s.deco(path, 'Base', (0.82, 0.14, 0.82), c - Vector((0, 0.5, 0)), I3, IRON, 'Metal')
    s.deco(path, 'Foot', (0.2, 0.36, 0.36), c - Vector((0, 0.62, 0)), rot(0, 0, 90), IRON, 'Metal', shape='Cylinder')


def pumpkin_lantern(s, path, post_top, side):
    """jack-o'-lantern hanging from an iron bracket on the outside of a front post"""
    p = Vector(post_top)
    arm_end = p + Vector((side * 1.9, 0, 0))
    s.part(path, 'BracketArm', (1.9, 0.18, 0.18), (p + arm_end) / 2, I3, IRON, 'Metal', collide=False)
    s.rod(path, 'BracketBrace', p + Vector((side * 0.1, -0.9, 0)), p + Vector((side * 1.1, -0.05, 0)), 0.12)
    s.deco(path, 'BracketTip', (0.26, 0.26, 0.26), arm_end, I3, IRON, 'Metal', shape='Ball')
    top = arm_end - Vector((0, 0.1, 0))
    links = 4
    for i in range(links):
        s.deco(path, f'Chain{i + 1}', (0.32, 0.12, 0.12), top - Vector((0, 0.16 + i * 0.28, 0)),
               rot(0, 90 * (i % 2), 90), IRON, 'Metal', shape='Cylinder', shadow=False)
    c = top - Vector((0, 1.15 + 0.85, 0))
    s.deco(path, 'Cap', (0.3, 0.75, 0.75), c + Vector((0, 0.82, 0)), rot(0, 0, 90), IRON, 'Metal', shape='Cylinder')
    pumpkin(s, path, c, 1.8, 1.4, face=True, glow=True, light=0.6, stem=False)
    s.deco(path, 'Spike1', (0.3, 0.5, 0.5), c - Vector((0, 0.86, 0)), rot(0, 0, 90), IRON, 'Metal', shape='Cylinder')
    s.deco(path, 'Spike2', (0.3, 0.28, 0.28), c - Vector((0, 1.1, 0)), rot(0, 0, 90), IRON, 'Metal', shape='Cylinder')
    s.deco(path, 'SpikeTip', (0.16, 0.16, 0.16), c - Vector((0, 1.3, 0)), I3, IRON, 'Metal', shape='Ball')


def candy_jar(s, path, base, d, h, candy_cols, cubes=True):
    base = Vector(base)
    c = base + Vector((0, h / 2, 0))
    s.deco(path, 'Glass', (h, d, d), c, rot(0, 0, 90), (214, 232, 236), 'Glass', shape='Cylinder', transparency=0.55)
    s.deco(path, 'Lid', (0.16, d * 1.06, d * 1.06), base + Vector((0, h + 0.08, 0)), rot(0, 0, 90), (214, 232, 236),
           'Glass', shape='Cylinder', transparency=0.4)
    s.deco(path, 'LidTop', (0.2, d * 0.45, d * 0.45), base + Vector((0, h + 0.25, 0)), rot(0, 0, 90),
           (214, 232, 236), 'Glass', shape='Cylinder', transparency=0.4)
    s.deco(path, 'Knob', (d * 0.22,) * 3, base + Vector((0, h + 0.42, 0)), I3, (214, 232, 236), 'Glass',
           shape='Ball', transparency=0.35)
    rng = random.Random(int(d * 100 + h * 10))
    k = 0
    layers = int(h * 0.7 / (0.3 if cubes else 0.24))
    for layer in range(layers):
        n = 6 if cubes else 7
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * layer) / n
            r = d * (0.27 if i % 2 else 0.18)
            p = base + Vector((math.cos(a) * r, 0.2 + layer * (0.29 if cubes else 0.22), math.sin(a) * r))
            col = candy_cols[k % len(candy_cols)]
            k += 1
            if cubes:
                s.deco(path, f'Candy{k}', (0.24, 0.24, 0.24), p, rot(rng.uniform(-30, 30), rng.uniform(0, 90), 0), col,
                       'SmoothPlastic', shadow=False)
            else:
                s.deco(path, f'Candy{k}', (0.24, 0.24, 0.24), p, I3, col, 'SmoothPlastic', shape='Ball', shadow=False)


# ------------------------------------------------------------------ the stall
W_POST = 6.5        # post centres at x = +-6.5
Z_FRONT, Z_BACK = -2.5, 2.6
COUNTER_TOP = 3.4


def build():
    s = Stall()
    J = s.jitter
    # ---- structure
    st = 'Structure'
    s.part(f'{st}/Base', 'Plinth', (14.6, 0.4, 6.4), (0, 0.2, 0.05), color=WOOD_DARK)
    for sx in (-1, 1):
        for zz, hgt, tag in ((Z_FRONT, 13.4, 'Front'), (Z_BACK, 11.2, 'Back')):
            name = f'{tag}Post{"L" if sx < 0 else "R"}'
            s.part(f'{st}/Posts', name, (1.1, hgt, 1.1), (sx * W_POST, hgt / 2, zz), color=WOOD_DARK, material='Wood')
            for y, hh in ((0.55, 0.7), (COUNTER_TOP - 0.15, 0.4), (hgt - 0.25, 0.5)):
                s.part(f'{st}/Posts', f'{name}_Collar', (1.32, hh, 1.32), (sx * W_POST, y, zz), color=IRON,
                       material='Metal', collide=False)
        # finials on the front posts
        s.part(f'{st}/Posts', f'Finial{"L" if sx < 0 else "R"}_Base', (0.95, 0.3, 0.95),
               (sx * W_POST, 13.55, Z_FRONT), color=IRON, material='Metal', collide=False)
        s.part(f'{st}/Posts', f'Finial{"L" if sx < 0 else "R"}', (0.82, 0.82, 0.82), (sx * W_POST, 14.25, Z_FRONT),
               rot(-35.26, 0, 45), GOLD, 'Metal',
               collide=False)
    # back wall: vertical planks + battens
    for i in range(11):
        x = -6.0 + i * 1.2
        s.part(f'{st}/BackWall', f'Plank{i + 1}', (1.16, 10.4, 0.3), (x, 5.4, Z_BACK + 0.15 * (i % 2) * 0.1),
               color=J((WOOD, WOOD_B, WOOD_C)[i % 3], 5))
    for k, y in enumerate((4.2, 9.2)):
        s.part(f'{st}/BackWall', f'Batten{k + 1}', (12.2, 0.5, 0.2), (0, y, Z_BACK - 0.24), color=WOOD_DARK,
               material='Wood', collide=False)
    # side walls (counter height) and a back shelf ledge
    for sx in (-1, 1):
        for k in range(3):
            s.part(f'{st}/SideWalls', f'Side{"L" if sx < 0 else "R"}_Board{k + 1}', (0.3, 1.0, 4.6),
                   (sx * (W_POST + 0.1), 0.9 + k * 1.02, 0.05), color=J((WOOD, WOOD_C, WOOD_B)[k], 5))
    # top frame: header beams, side beams, flat plank roof (hidden behind the sign)
    s.part(f'{st}/Frame', 'FrontHeader', (12.0, 0.9, 0.9), (0, 10.05, Z_FRONT), color=WOOD_DARK, material='Wood')
    s.part(f'{st}/Frame', 'BackHeader', (12.0, 0.8, 0.8), (0, 10.7, Z_BACK), color=WOOD_DARK, material='Wood')
    for sx in (-1, 1):
        s.part(f'{st}/Frame', f'SideBeam{"L" if sx < 0 else "R"}', (0.8, 0.8, 5.1), (sx * W_POST, 10.5, 0.05),
               color=WOOD_DARK, material='Wood')
    for i in range(9):
        s.part(f'{st}/Frame', f'RoofPlank{i + 1}', (12.4, 0.2, 0.62), (0, 11.0, -2.3 + i * 0.6),
               color=J(WOOD_B, 5))
    # counter: top slab, front cabinet, iron corner straps
    ct = 'Counter'
    s.part(f'{ct}', 'CounterTop', (14.8, 0.45, 2.6), (0, COUNTER_TOP - 0.22, -2.55), color=WOOD_DARK, material='Wood')
    s.part(f'{ct}', 'CounterLip', (14.9, 0.2, 0.3), (0, COUNTER_TOP - 0.5, -3.85), color=WOOD_DARK, material='Wood')
    for k in range(3):
        s.part(f'{ct}/FrontBoards', f'Board{k + 1}', (13.9, 0.92, 0.3), (0, 0.9 + k * 0.92, -3.55),
               color=J((WOOD, WOOD_C, WOOD_B)[k], 5))
    for sx in (-1, 1):
        s.part(f'{ct}', f'CornerPost{"L" if sx < 0 else "R"}', (0.9, 3.0, 0.9), (sx * 6.95, 1.7, -3.55),
               color=WOOD_DARK, material='Wood')
        for y in (0.6, 2.75):
            s.part(f'{ct}/IronStraps', f'Strap{"L" if sx < 0 else "R"}{y}', (1.04, 0.32, 1.04), (sx * 6.95, y, -3.55),
                   color=IRON, material='Metal', collide=False)
            for bz in (-1, 1):
                s.deco(f'{ct}/IronStraps', 'Bolt', (0.14, 0.14, 0.14), (sx * 6.95 + bz * 0.25, y, -4.08), I3, IRON,
                       'Metal', shape='Ball')
    # carved trim frame on the counter front
    tr = f'{ct}/CarvedTrim'
    for k, (cx, w) in enumerate(((-4.3, 4.6), (4.3, 4.6))):
        s.deco(tr, f'PanelTop{k + 1}', (w, 0.22, 0.12), (cx, 2.55, -3.76), I3, WOOD_TRIM, 'Wood')
        s.deco(tr, f'PanelBottom{k + 1}', (w, 0.22, 0.12), (cx, 0.75, -3.76), I3, WOOD_TRIM, 'Wood')
        for sx in (-1, 1):
            s.deco(tr, f'PanelSide{k + 1}', (0.22, 2.0, 0.12), (cx + sx * w / 2, 1.65, -3.76), I3, WOOD_TRIM, 'Wood')
            s.deco(tr, f'PanelCorner{k + 1}', (0.9, 0.18, 0.12), (cx + sx * (w / 2 - 0.4), 2.33, -3.77),
                   rot(0, 0, sx * 35), WOOD_TRIM, 'Wood')
    s.deco(tr, 'PlaqueRing', (0.14, 1.9, 1.9), (-0.6, 1.15, -3.74), rot(0, 90, 0), WOOD_TRIM, 'Wood', shape='Cylinder')
    for sx in (-1, 1):
        s.deco(tr, 'PlaqueSweep', (1.6, 0.2, 0.12), (-0.6 + sx * 1.55, 1.75, -3.76), rot(0, 0, -sx * 22), WOOD_TRIM, 'Wood')
    pumpkin(s, f'{ct}/@PlaquePumpkin', (-0.6, 1.12, -3.78), 1.65, 1.2, glow=True, light=0.0, depth=0.35, stem=False)
    for sx in (-1, 1):
        vine(s, f'{ct}/FrontVines', [Vector((sx * 2.0, 1.35, -3.82)), Vector((sx * 3.0, 1.75, -3.82)),
                                    Vector((sx * 4.1, 1.55, -3.82)), Vector((sx * 5.1, 1.9, -3.82))])
        curl(s, f'{ct}/FrontVines', Vector((sx * 5.3, 1.6, -3.84)), 0.45, Vector((sx, 0, 0)), Y, 1.1, 0.13, start=1.6)
        curl(s, f'{ct}/FrontVines', Vector((sx * 2.9, 1.45, -3.84)), 0.32, Vector((-sx, 0, 0)), Y, 1.0, 0.12, start=-1.4)
    leaves(s, f'{ct}/FrontLeaves', [((-3.5, 2.1, -3.86), (0, 0, -1), 0.75), ((-5.8, 1.3, -3.86), (0, 0, -1), 0.65),
                                   ((3.6, 2.15, -3.86), (0, 0, -1), 0.75), ((5.6, 1.2, -3.86), (0, 0, -1), 0.65),
                                   ((-6.9, 3.1, -4.1), (0, 0.2, -1), 0.6), ((6.95, 0.6, -4.1), (0, 0.2, -1), 0.6)])
    # ---- canopy: 8 stripes sloping forward, seams, pennant valance with diamond cut-outs, side drops
    cn = 'Canopy'
    top_z, top_y, front_z, front_y = -2.1, 10.55, -4.75, 8.85
    dz, dy = front_z - top_z, front_y - top_y
    L = math.hypot(dz, dy)
    ang = math.degrees(math.atan2(-dy, -dz))         # tilt so the front edge is lower
    Rc = rot(-ang, 0, 0)
    n_str, width = 8, 15.0
    sw = width / n_str
    mid = Vector((0, (top_y + front_y) / 2, (top_z + front_z) / 2))
    for i in range(n_str):
        x = -width / 2 + sw * (i + 0.5)
        col = PURPLE if i % 2 == 0 else ORANGE_CLOTH
        s.part(f'{cn}/Stripes', f'Stripe{i + 1}', (sw + 0.02, 0.14, L), mid + Vector((x, 0, 0)), Rc, col, 'Fabric')
        if i:
            s.deco(f'{cn}/Seams', f'Seam{i}', (0.07, 0.17, L), mid + Vector((-width / 2 + sw * i, 0.01, 0)), Rc,
                   PURPLE_DARK, 'Fabric')
        # valance pennant: straight top band + pointed tip, with a diamond cut-out
        cx = Vector((x, front_y - 0.55, front_z - 0.02))
        s.part(f'{cn}/Valance', f'Flap{i + 1}', (sw - 0.04, 1.1, 0.1), cx, I3, col, 'Fabric', collide=False)
        tip = sw * 0.74
        s.part(f'{cn}/Valance', f'FlapTip{i + 1}', (tip, tip, 0.1), cx + Vector((0, -0.55, 0.01)), rot(0, 0, 45), col,
               'Fabric', collide=False)
        s.deco(f'{cn}/Valance', f'CutOut{i + 1}', (0.3, 0.3, 0.12), cx + Vector((0, -0.62, -0.01)), rot(0, 0, 45),
               (52, 30, 22), 'SmoothPlastic', shadow=False)
        s.deco(f'{cn}/Seams', f'Hem{i + 1}', (sw - 0.04, 0.07, 0.13), cx + Vector((0, 0.4, -0.01)), I3,
               PURPLE_DARK if i % 2 == 0 else ORANGE_DARK, 'Fabric')
    s.deco(f'{cn}/Valance', 'Roll', (width + 0.1, 0.32, 0.32), Vector((0, front_y + 0.02, front_z + 0.02)),
           I3, PURPLE_DARK, 'Fabric',
           shape='Cylinder')
    for sx in (-1, 1):                                   # side drops
        s.part(f'{cn}/SideDrops', f'SideDrop{"L" if sx < 0 else "R"}', (0.1, 1.0, L * 0.95),
               Vector((sx * (width / 2 + 0.02), mid.y - 0.45, mid.z)), Rc, PURPLE if sx < 0 else ORANGE_CLOTH,
               'Fabric', collide=False)
    for sx in (-1, 1):                                   # iron braces from the front posts to the canopy edge
        s.rod(f'{cn}/Supports', f'Brace{"L" if sx < 0 else "R"}', (sx * W_POST, 8.1, Z_FRONT - 0.55),
              (sx * (W_POST + 0.2), front_y + 0.05, front_z + 0.25), 0.14)
        s.rod(f'{cn}/Supports', f'EdgeBar{"L" if sx < 0 else "R"}', (sx * (W_POST + 0.2), front_y + 0.12, front_z + 0.2),
              (sx * (W_POST + 0.2), top_y, top_z), 0.12)
    s.deco(f'{cn}/Supports', 'FrontBar', (width - 0.4, 0.12, 0.12), (0, front_y + 0.12, front_z + 0.2), I3, IRON,
           'Metal', shape='Cylinder')
    # ---- sign
    sg = 'Sign'
    s.part(f'{sg}', 'SignBoard', (12.6, 2.5, 0.4), (0, 11.95, Z_FRONT - 0.15), color=(66, 42, 27), material='WoodPlanks',
           sign=True)
    s.part(f'{sg}/Frame', 'FrameTop', (12.9, 0.32, 0.55), (0, 13.25, Z_FRONT - 0.15), color=WOOD_DARK, material='Wood')
    s.part(f'{sg}/Frame', 'FrameBottom', (12.9, 0.32, 0.55), (0, 10.65, Z_FRONT - 0.15), color=WOOD_DARK,
           material='Wood')
    s.part(f'{sg}/Frame', 'CrestCentre', (5.2, 0.75, 0.5), (0, 13.6, Z_FRONT - 0.15), color=WOOD_DARK, material='Wood')
    for sx in (-1, 1):
        s.part(f'{sg}/Frame', f'CrestShoulder{"L" if sx < 0 else "R"}', (2.0, 0.42, 0.5),
               (sx * 3.25, 13.45, Z_FRONT - 0.15), rot(0, 0, sx * -18), WOOD_DARK, 'Wood')
        s.deco(f'{sg}/Frame', f'CrestTrim{"L" if sx < 0 else "R"}', (2.4, 0.12, 0.1),
               (sx * 1.6, 13.92, Z_FRONT - 0.45), I3, WOOD_TRIM, 'Wood')
        for y in (10.85, 13.05):
            for x in (5.9, 2.0):
                s.deco(f'{sg}/Frame', 'Bolt', (0.16, 0.16, 0.16), (sx * x, y, Z_FRONT - 0.45), I3, IRON, 'Metal',
                       shape='Ball')
    s.deco(f'{sg}/Frame', 'TrimLine', (12.3, 0.08, 0.06), (0, 13.02, Z_FRONT - 0.37), I3, WOOD_TRIM, 'Wood')
    s.deco(f'{sg}/Frame', 'TrimLine2', (12.3, 0.08, 0.06), (0, 10.88, Z_FRONT - 0.37), I3, WOOD_TRIM, 'Wood')
    for sx in (-1, 1):
        bat(s, f'{sg}/@Bat{"L" if sx < 0 else "R"}', (sx * 5.35, 12.0, Z_FRONT - 0.42), 1.5)
    pumpkin(s, f'{sg}/@CrestPumpkin', (0, 14.45, Z_FRONT - 0.2), 1.9, 1.35, glow=True, light=0.0)
    for sx in (-1, 1):
        curl(s, f'{sg}/Vines', Vector((sx * 1.7, 14.2, Z_FRONT - 0.35)), 0.5, Vector((sx, 0, 0)), Y, 1.15, 0.15,
             start=math.pi * 0.95)
        curl(s, f'{sg}/Vines', Vector((sx * 3.3, 13.95, Z_FRONT - 0.4)), 0.35, Vector((sx, 0, 0)), Y, 1.0, 0.13,
             start=math.pi)
        vine(s, f'{sg}/Vines', [Vector((sx * 0.7, 14.05, Z_FRONT - 0.35)), Vector((sx * 1.2, 13.95, Z_FRONT - 0.38)),
                               Vector((sx * 2.5, 13.9, Z_FRONT - 0.4)), Vector((sx * 3.5, 13.75, Z_FRONT - 0.42))], 0.14)
    # ---- lighting
    lg = 'Lanterns'
    for k, x in enumerate((-3.6, 3.6)):
        hanging_lantern(s, f'{lg}/@HangingLantern{k + 1}', (x, 10.88, -1.7), 2.2)
    for sx in (-1, 1):
        pumpkin_lantern(s, f'{lg}/@PumpkinLantern{"L" if sx < 0 else "R"}', (sx * (W_POST + 0.55), 9.6, Z_FRONT), sx)
    # ---- counter props (centre of the counter left free for the shop interaction)
    pr = 'CounterProps'
    pumpkin(s, f'{pr}/@BigJackOLantern', (4.6, COUNTER_TOP + 0.85, -2.35), 2.6, 1.75, glow=True, light=0.55, ry=-12)
    pumpkin(s, f'{pr}/@SmallPumpkin1', (6.1, COUNTER_TOP + 0.44, -2.95), 1.2, 0.9, face=True, glow=True, ry=-20)
    pumpkin(s, f'{pr}/@SmallPumpkin2', (2.85, COUNTER_TOP + 0.52, -2.7), 1.4, 1.05, face=True, glow=True, ry=15)
    candy_jar(s, f'{pr}/@CandyJarTall', (-4.3, COUNTER_TOP, -2.5), 1.55, 1.9,
              [(236, 120, 30), (130, 60, 170), (250, 160, 50), (100, 44, 140)], cubes=True)
    candy_jar(s, f'{pr}/@CandyJarSmall', (-5.9, COUNTER_TOP, -2.7), 1.05, 1.25, [(244, 128, 30), (250, 170, 60)],
              cubes=False)
    # table runner: purple cloth across the counter and down the front, orange border, gold bat
    rn = f'{pr}/@TableRunner'
    rx, rw = -0.6, 4.0
    s.deco(rn, 'Top', (rw, 0.06, 2.6), (rx, COUNTER_TOP + 0.03, -2.55), I3, PURPLE, 'Fabric')
    s.deco(rn, 'Drop', (rw, 0.85, 0.06), (rx, COUNTER_TOP - 0.4, -3.9), I3, PURPLE, 'Fabric')
    pt = 1.2
    yc = COUNTER_TOP - 0.82
    s.deco(rn, 'Point', (pt, pt, 0.06), (rx, yc, -3.91), rot(0, 0, 45), PURPLE, 'Fabric')
    for sx in (-1, 1):
        s.deco(rn, 'BorderSide', (0.16, 0.85, 0.08), (rx + sx * (rw / 2 - 0.08), COUNTER_TOP - 0.4, -3.94), I3,
               ORANGE_CLOTH, 'Fabric')
        a = pt / math.sqrt(2)
        s.deco(rn, 'BorderPoint', (pt, 0.14, 0.08), (rx + sx * a / 2, yc - a / 2, -3.94), rot(0, 0, sx * 45),
               ORANGE_CLOTH, 'Fabric')
        s.deco(rn, 'BorderTop', (0.16, 0.08, 2.6), (rx + sx * (rw / 2 - 0.08), COUNTER_TOP + 0.07, -2.55), I3,
               ORANGE_CLOTH, 'Fabric')
    bat(s, f'{rn}/@GoldBat', (rx, COUNTER_TOP - 0.55, -3.97), 1.2, GOLD, 'Metal', thick=0.06)
    s.deco(f'{pr}', 'ServingBoard', (0.22, 1.7, 1.7), (rx, COUNTER_TOP + 0.17, -2.45), rot(0, 0, 90), WOOD_TRIM, 'Wood',
           shape='Cylinder')
    leaves(s, f'{pr}/CounterLeaves', [((5.3, COUNTER_TOP + 0.08, -3.4), (0, 1, 0), 0.7),
                                      ((3.6, COUNTER_TOP + 0.08, -3.5), (0, 1, 0), 0.65),
                                      ((2.0, COUNTER_TOP + 0.08, -2.2), (0, 1, 0), 0.6),
                                      ((-3.2, COUNTER_TOP + 0.08, -3.35), (0, 1, 0), 0.6),
                                      ((-6.6, COUNTER_TOP + 0.08, -3.4), (0, 1, 0), 0.55)])
    # interaction zone in front of the free counter space (invisible; add a ProximityPrompt here)
    s.part('', 'ShopInteractZone', (5.0, 4.0, 3.0), (rx, 2.0, -5.6), I3, (255, 255, 255), 'SmoothPlastic',
           transparency=1.0, collide=False, shadow=False)
    # ---- decor: vines up the front posts, leaves, cobwebs
    dc = 'Decor'
    for sx in (-1, 1):
        pts = []
        for i in range(17):
            t = i / 16
            a = math.radians(-60 + t * 540) * sx
            pts.append(Vector((sx * W_POST + math.cos(a) * 0.62, 4.0 + t * 8.8, Z_FRONT + math.sin(a) * 0.62)))
        vine(s, f'{dc}/PostVines', pts)
        curl(s, f'{dc}/PostVines', pts[-1] + Vector((sx * 0.3, 0.25, -0.1)), 0.4, Vector((sx, 0, 0)), Y, 1.1, 0.13)
    leaves(s, f'{dc}/Leaves', [
        ((-7.2, 12.4, -3.15), (0, 0.1, -1), 0.85), ((-7.6, 11.4, -3.0), (-0.5, 0, -1), 0.75),
        ((-7.0, 9.5, -3.15), (0, 0, -1), 0.7), ((-7.4, 6.4, -3.1), (-0.4, 0, -1), 0.65),
        ((7.25, 12.2, -3.15), (0, 0.1, -1), 0.8), ((7.55, 10.8, -3.05), (0.5, 0, -1), 0.7),
        ((7.1, 7.0, -3.15), (0, 0, -1), 0.7), ((7.4, 5.0, -3.1), (0.4, 0, -1), 0.6),
        ((-6.4, 8.6, -4.85), (0, 0, -1), 0.6), ((6.5, 8.7, -4.85), (0, 0, -1), 0.6),
        ((-7.3, 0.7, -4.0), (0, 0.4, -1), 0.6), ((7.5, 1.6, -3.4), (0.5, 0.2, -1), 0.55),
        ((-4.0, 10.6, -3.2), (0, 0, -1), 0.6), ((4.6, 10.55, -3.2), (0, 0, -1), 0.55),
    ])
    for sx in (-1, 1):
        cobweb(s, f'{dc}/@Cobweb{"L" if sx < 0 else "R"}', (sx * (W_POST - 0.58), 7.75, Z_FRONT - 0.05),
               (0, -1, 0), (-sx, 0, 0), 1.9)
    return s


# ------------------------------------------------------------------ Lua emitter
LUA_HEAD = '''--[[ SPOOKY HARVEST - Halloween event market stall
     Generated by blender/spooky_stall.py. Paste this whole file into the Roblox Studio Command Bar
     (View > Command Bar) and press Enter. It builds Workspace.SpookyHarvestStall (replacing an old copy),
     selects it, and you can then move it with the Move tool or Model:PivotTo().

     Native Roblox parts only (no uploads): Parts, WedgeParts, SpecialMesh spheres, WoodPlanks / Wood / Fabric / Metal /
     Glass / Neon materials, a SurfaceGui sign and soft PointLights.
     Front of the stall faces -Z. Structure parts collide; decorations do not. Everything is Anchored. ]]

local ROOT_NAME = "SpookyHarvestStall"
local SIGN_TEXT = "SPOOKY HARVEST"
local old = workspace:FindFirstChild(ROOT_NAME)
if old then old:Destroy() end

local root = Instance.new("Model")
root.Name = ROOT_NAME
local containers = { [""] = root }

-- "A/B/@C" -> Folder A / Folder B / Model C (names starting with @ become Models)
local function container(path)
	if containers[path] then return containers[path] end
	local parentPath, name = string.match(path, "^(.*)/([^/]+)$")
	if not parentPath then parentPath, name = "", path end
	local isModel = string.sub(name, 1, 1) == "@"
	local inst = Instance.new(isModel and "Model" or "Folder")
	inst.Name = isModel and string.sub(name, 2) or name
	inst.Parent = container(parentPath)
	containers[path] = inst
	return inst
end

local function addSign(part)
	local gui = Instance.new("SurfaceGui")
	gui.Name = "SignGui"
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 60
	gui.LightInfluence = 0.35
	gui.Parent = part
	local label = Instance.new("TextLabel")
	label.Name = "Title"
	label.BackgroundTransparency = 1
	label.AnchorPoint = Vector2.new(0.5, 0.5)
	label.Position = UDim2.fromScale(0.5, 0.52)
	label.Size = UDim2.fromScale(0.7, 0.78)
	label.Font = Enum.Font.LuckiestGuy
	label.Text = SIGN_TEXT
	label.TextScaled = true
	label.TextColor3 = Color3.fromRGB(255, 196, 70)
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextYAlignment = Enum.TextYAlignment.Center
	label.Parent = gui
	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.fromRGB(58, 30, 12)
	stroke.Thickness = 4
	stroke.Parent = label
	local grad = Instance.new("UIGradient")
	grad.Color = ColorSequence.new(Color3.fromRGB(255, 214, 96), Color3.fromRGB(240, 150, 40))
	grad.Rotation = 90
	grad.Parent = label
end

-- path, name, shape, size xyz, position xyz, rotation matrix (9), colour rgb, material, transparency,
-- canCollide, castShadow, extra ("S" = sphere mesh, "L" = light rgb/brightness/range, "G" = sign gui)
local P = {
'''

LUA_TAIL = '''}

for _, d in ipairs(P) do
	local p
	if d[3] == "Wedge" then
		p = Instance.new("WedgePart")
	else
		p = Instance.new("Part")
		p.Shape = Enum.PartType[d[3]]
	end
	p.Name = d[2]
	p.Size = Vector3.new(d[4], d[5], d[6])
	p.CFrame = CFrame.new(d[7], d[8], d[9], d[10], d[11], d[12], d[13], d[14], d[15], d[16], d[17], d[18])
	p.Color = Color3.fromRGB(d[19], d[20], d[21])
	p.Material = Enum.Material[d[22]]
	p.Transparency = d[23]
	p.CanCollide = d[24]
	p.CanTouch = d[24]
	p.CastShadow = d[25]
	p.Anchored = true
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	local extra = d[26]
	if extra then
		if extra.S then
			local m = Instance.new("SpecialMesh")
			m.MeshType = Enum.MeshType.Sphere
			m.Parent = p
		end
		if extra.L then
			local l = Instance.new("PointLight")
			l.Color = Color3.fromRGB(extra.L[1], extra.L[2], extra.L[3])
			l.Brightness = extra.L[4]
			l.Range = extra.L[5]
			l.Shadows = false
			l.Parent = p
		end
		if extra.G then addSign(p) end
	end
	p.Parent = container(d[1])
end

root.PrimaryPart = root.Structure.Base.Plinth
root.Parent = workspace
pcall(function() game:GetService("Selection"):Set({ root }) end)
print(("SpookyHarvestStall built: %d parts"):format(#P))
'''


def fmt(v):
    s = f'{v:.3f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def lua_row(p):
    R = p['R']
    ex = []
    if p['mesh']:
        ex.append('S=true')
    if p['light']:
        (r, g, b), br, rg = p['light']
        ex.append(f'L={{{r},{g},{b},{fmt(br)},{fmt(rg)}}}')
    if p['sign']:
        ex.append('G=true')
    vals = [f'"{p["path"]}"', f'"{p["name"]}"', f'"{p["shape"]}"', *[fmt(v) for v in p['size']],
            *[fmt(v) for v in p['pos']], *[fmt(R[i][j]) for i in range(3) for j in range(3)],
            *[str(int(c)) for c in p['color']], f'"{p["material"]}"', fmt(p['transparency']),
            'true' if p['collide'] else 'false', 'true' if p['shadow'] else 'false',
            '{' + ','.join(ex) + '}' if ex else 'nil']
    return '{' + ','.join(vals) + '},'


def write_lua(s, path):
    with open(path, 'w') as f:
        f.write(LUA_HEAD)
        for p in s.parts:
            f.write(lua_row(p) + '\n')
        f.write(LUA_TAIL)


# ------------------------------------------------------------------ Blender preview
def render_preview(s, out_dir):
    import bpy, bmesh
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # Roblox (Y up, -Z front) -> Blender
    mats = {}

    def srgb(c):
        return tuple((v / 255) ** 2.2 for v in c)

    def mat(color, material, transparency):
        key = (color, material, round(transparency, 2))
        if key in mats:
            return mats[key]
        m = bpy.data.materials.new(f'{material}_{len(mats)}')
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*srgb(color), 1)
        rough = {'Fabric': 0.95, 'Metal': 0.4, 'Glass': 0.05, 'Neon': 0.5, 'Wood': 0.75, 'WoodPlanks': 0.8}.get(material, 0.5)
        b.inputs['Roughness'].default_value = rough
        if material == 'Metal':
            b.inputs['Metallic'].default_value = 0.6
        if material == 'Neon':
            b.inputs['Emission Color'].default_value = (*srgb(color), 1)
            b.inputs['Emission Strength'].default_value = 2.5
        if material == 'Glass':
            b.inputs['Transmission Weight'].default_value = 0.9
        if transparency > 0.01 and material != 'Glass':
            b.inputs['Alpha'].default_value = 1 - transparency
        if material in ('WoodPlanks', 'Wood'):        # restrained wood grain
            nt = m.node_tree
            tc = nt.nodes.new('ShaderNodeTexCoord')
            mp = nt.nodes.new('ShaderNodeMapping')
            mp.inputs['Scale'].default_value = (1.5, 1.5, 12.0) if material == 'Wood' else (3.0, 0.4, 3.0)
            wv = nt.nodes.new('ShaderNodeTexWave')
            wv.inputs['Scale'].default_value = 2.0
            wv.inputs['Distortion'].default_value = 6.0
            ramp = nt.nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].color = (*[v * 0.75 for v in srgb(color)], 1)
            ramp.color_ramp.elements[1].color = (*[min(1, v * 1.15) for v in srgb(color)], 1)
            nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
            nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
            nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac'])
            nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        mats[key] = m
        return m
    coll = bpy.data.collections.new('Stall')
    sc.collection.children.link(coll)
    for p in s.parts:
        if p['transparency'] >= 0.99:
            continue
        bm = bmesh.new()
        sx, sy, sz = p['size']
        if p['shape'] == 'Ball':
            d = min(sx, sy, sz)
            bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=d / 2)
        elif p['shape'] == 'Cylinder':
            d = min(sy, sz)
            bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=d / 2, radius2=d / 2, depth=sx)
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
        elif p['shape'] == 'Wedge':        # Roblox WedgePart: slope from the top-back edge down to the bottom-front edge
            vs = [bm.verts.new((x * sx / 2, y * sy / 2, z * sz / 2)) for x in (-1, 1)
                  for y, z in ((-1, -1), (-1, 1), (1, 1))]
            bm.faces.new((vs[0], vs[1], vs[2]))
            bm.faces.new((vs[3], vs[5], vs[4]))
            bm.faces.new((vs[0], vs[3], vs[4], vs[1]))
            bm.faces.new((vs[1], vs[4], vs[5], vs[2]))
            bm.faces.new((vs[2], vs[5], vs[3], vs[0]))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        elif p['mesh'] == 'Sphere':
            bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.5)
            bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
        else:
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
        me = bpy.data.meshes.new(p['name'])
        bm.to_mesh(me)
        bm.free()
        if p['shape'] != 'Block' or p['mesh']:
            for f in me.polygons:
                f.use_smooth = True
        me.materials.append(mat(p['color'], p['material'], p['transparency']))
        ob = bpy.data.objects.new(p['name'], me)
        ob.matrix_world = C @ (Matrix.Translation(p['pos']) @ p['R'].to_4x4())
        coll.objects.link(ob)
        if p['light']:
            (r, g, b), br, rg = p['light']
            li = bpy.data.lights.new('l', 'POINT')
            li.energy, li.color, li.shadow_soft_size = 60 * br, srgb((r, g, b)), 0.3
            lo = bpy.data.objects.new('l', li)
            lo.matrix_world = ob.matrix_world.copy()
            coll.objects.link(lo)
        if p['sign']:                     # SurfaceGui text stand-in
            cu = bpy.data.curves.new('SignText', 'FONT')
            cu.body = 'SPOOKY HARVEST'
            cu.align_x, cu.align_y = 'CENTER', 'CENTER'
            cu.size = 1.25
            cu.extrude = 0.02
            cu.offset = 0.03
            to = bpy.data.objects.new('SignText', cu)
            cu.materials.append(mat((255, 196, 70), 'SmoothPlastic', 0))
            to.matrix_world = C @ (Matrix.Translation(p['pos'] + Vector((0, 0.05, -sz / 2 - 0.03))) @
                                   Matrix.Rotation(math.pi, 4, 'Y'))
            to.scale = (0.98, 1.2, 1)
            coll.objects.link(to)
    # studio
    g = bpy.data.objects.new('Ground', bpy.data.meshes.new('Ground'))
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60)
    bm.to_mesh(g.data)
    bm.free()
    g.is_shadow_catcher = True
    coll.objects.link(g)
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (*srgb((214, 206, 196)), 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
    for name, loc, energy, size in (('Key', (-14, 22, 20), 9000, 10), ('Fill', (18, 14, 9), 3000, 12),
                                    ('Rim', (4, -20, 16), 2500, 10)):
        li = bpy.data.lights.new(name, 'AREA')
        li.energy, li.size = energy, size
        o = bpy.data.objects.new(name, li)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 6)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        coll.objects.link(o)
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = int(os.environ.get('SAMPLES', 48))
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'
    shots = (('ThreeQuarter', (9.5, 27, 11.5), (0.6, 0, 7.0), 33, 1400, 1200),
             ('Front', (0, 32, 7.5), (0, 0, 7.0), 30, 1400, 1100),
             ('Player', (-3.0, 15, 5.0), (0, -1, 5.0), 30, 1400, 1000))
    os.makedirs(out_dir, exist_ok=True)
    for name, loc, tgt, lens, rx, ry in shots:
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
        coll.objects.link(cam)
        cam.location = loc
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lens
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        sc.render.filepath = os.path.join(out_dir, f'SpookyHarvest_{name}.png')
        bpy.ops.render.render(write_still=True)


def main():
    s = build()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'BuildSpookyHarvestStall.lua')
    write_lua(s, path)
    print(f'{len(s.parts)} parts -> {path}')
    if '--render' in sys.argv:
        out = sys.argv[sys.argv.index('--render') + 1] if len(sys.argv) > sys.argv.index('--render') + 1 else \
            os.path.join(HERE, '..', 'previews')
        render_preview(s, os.path.abspath(out))


if __name__ == '__main__':
    main()
