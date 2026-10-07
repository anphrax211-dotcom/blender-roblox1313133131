"""KING RAINHOUND - Water / Mini-Boss. Chunky low-poly water hound for Roblox.

Game-scale dimensions (metric, 1 unit = 1 m; ~1 m = 3.5 studs in Roblox):
    overall height  : ~5.4 m to the crown droplet (about 3x Boulderbub's ~1.75 m)
    shoulder height : ~3.3 m        head top : ~4.9 m
    length          : ~6.6 m nose to tail curl (Y)      width : ~3.4 m across the paws/armour (X)
    paws            : ~1.4 x 1.5 m each, soles on z = 0
Creature stands on the ground plane at the world origin and faces -Y.
Every part is a separate, editable mesh (rotation/scale applied; each origin at the
centre of its part), grouped into the Body, Head, Legs, Water Armor, Mane and Tail,
Crown and Effects collections.

Run in Blender (Scripting tab -> Run Script) or headless:
    blender -b -P king_rainhound.py
    python3 king_rainhound.py          (with the `bpy` pip module)
Saves KingRainhound_Refined.blend next to this script and prints the full path
(the earlier KingRainhound.blend and KingRainhound_Improved.blend are left untouched).
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
COLLS = {}
MATS = {}


# ------------------------------------------------------------------ materials
def material(name, rgb, rough=0.5, coat=0.15, emit=0.0, alpha=1.0, srgb=None):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*rgb, alpha)
    MATS[name] = m


def build_materials():
    # linear values; comment = approx. sRGB / Roblox Color3
    material('Fur_Navy', (0.025, 0.045, 0.16), 0.6)                # ~44,60,111  main body
    material('Fur_SlateBlue', (0.08, 0.13, 0.33), 0.6)            # ~80,101,155 lighter body facets
    material('Fur_Gray', (0.25, 0.27, 0.33), 0.6)                    # ~138,143,155 (blue-grey, blends with the navy) chest / jaw
    material('Stone_LightBlue', (0.22, 0.33, 0.58), 0.55)         # ~130,155,200 toes / leg plates
    material('Armor_Slate', (0.11, 0.18, 0.4), 0.45, 0.25)        # ~93,118,170 slate-blue plates
    material('Armor_Aqua', (0.08, 0.5, 0.95), 0.3, 0.4, emit=0.25)       # ~80,188,250 armour & waves
    material('Armor_AquaLight', (0.35, 0.78, 1.0), 0.3, 0.4, emit=0.3)   # ~160,229,255 highlights
    material('Water_Clear', (0.2, 0.7, 1.0), 0.05, 0.6, emit=0.25, alpha=0.55)  # ~124,218,255 water
    material('Eye_Glow', (0.05, 0.85, 1.0), 0.2, 0.0, emit=1.6)    # ~137,255,255 glowing eyes
    material('Eye_Glint', (1.0, 1.0, 1.0), 0.2, 0.0, emit=3.0)
    material('Nose_Dark', (0.015, 0.015, 0.03), 0.25, 0.5)        # ~33,33,48
    material('Mouth_Dark', (0.03, 0.02, 0.06), 0.5)               # ~48,38,69
    material('Teeth_White', (0.85, 0.86, 0.88), 0.35, 0.3)        # ~239,240,242
    material('Crown_Navy', (0.02, 0.025, 0.09), 0.35, 0.4)        # ~38,44,85
    material('Crown_Droplet', (0.15, 0.75, 1.0), 0.05, 0.6, emit=1.2)    # ~108,225,255


# ------------------------------------------------------------------ builder
class Part:
    def __init__(self, name, coll, bevel=0.03):
        self.name, self.coll, self.bevel = name, coll, bevel
        self.bm = bmesh.new()
        self.mats = []

    def _mat(self, verts, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        i = self.mats.index(mat)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = i

    def blob(self, c, r, mat, rot=(0, 0, 0), sub=2, jitter=0.06, seed=0, flat_bottom=None):
        """faceted ellipsoid (jittered icosphere) - the core low-poly building block"""
        rnd = random.Random(seed)
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=1.0)
        M = Euler(rot).to_matrix()
        for v in res['verts']:
            v.co *= 1 + rnd.uniform(-jitter, jitter)
            v.co = M @ Vector((v.co.x * r[0], v.co.y * r[1], v.co.z * r[2])) + Vector(c)
            if flat_bottom is not None and v.co.z < flat_bottom:
                v.co.z = flat_bottom
        self._mat(res['verts'], mat)

    def box(self, c, s, mat, rot=(0, 0, 0)):
        M = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*s, 1))
        res = bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)
        self._mat(res['verts'], mat)

    def cone(self, base, direction, length, r1, mat, segs=4, r2=0.0, spin=0.0):
        d = Vector(direction).normalized()
        q = d.to_track_quat('Z', 'Y').to_matrix().to_4x4() @ Matrix.Rotation(spin, 4, 'Z')
        M = Matrix.Translation(Vector(base) + d * length / 2) @ q
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2,
                                    depth=length, matrix=M)
        self._mat(res['verts'], mat)

    def poly(self, verts, faces, mat):
        vs = [self.bm.verts.new(v) for v in verts]
        for f in faces:
            self.bm.faces.new([vs[i] for i in f])
        self._mat(vs, mat)

    def sweep(self, pts, widths, thick, normal, mat, closed_tip=True):
        """chunky ribbon along a (mostly planar) path: rectangle-ish section,
        width in the path plane, `thick` along `normal`. widths: one per point."""
        n = Vector(normal).normalized()
        rings = []
        for i, p in enumerate(pts):
            a = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
            a.normalize()
            side = a.cross(n).normalized()
            w, t = widths[i] / 2, thick * (0.35 + 0.65 * widths[i] / max(widths)) / 2
            ring = [p + side * w, p + n * t + side * w * 0.3, p + n * t - side * w * 0.3,
                    p - side * w, p - n * t - side * w * 0.3, p - n * t + side * w * 0.3]
            rings.append([self.bm.verts.new(v) for v in ring])
        k = len(rings[0])
        for i in range(len(rings) - 1):
            for j in range(k):
                self.bm.faces.new((rings[i][j], rings[i][(j + 1) % k], rings[i + 1][(j + 1) % k], rings[i + 1][j]))
        self.bm.faces.new(rings[0][::-1])
        self.bm.faces.new(rings[-1])
        self._mat([v for r in rings for v in r], mat)

    def loft(self, path, radii, mat, segs=8):
        """continuous tapered limb/neck: elliptical rings (rx, ry) along a path, capped"""
        rings = []
        for i, p in enumerate(path):
            t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
            a1 = Vector((1, 0, 0)) - t * t.x
            a1.normalize()
            a2 = t.cross(a1).normalized()
            rx, ry = radii[i]
            rings.append([self.bm.verts.new(p + a1 * rx * math.cos(k / segs * 2 * math.pi + math.pi / segs)
                                            + a2 * ry * math.sin(k / segs * 2 * math.pi + math.pi / segs))
                          for k in range(segs)])
        for i in range(len(rings) - 1):
            for k in range(segs):
                self.bm.faces.new((rings[i][k], rings[i][(k + 1) % segs], rings[i + 1][(k + 1) % segs], rings[i + 1][k]))
        self.bm.faces.new(rings[0][::-1])
        self.bm.faces.new(rings[-1])
        self._mat([v for r in rings for v in r], mat)

    def fin(self, pts, thick, mat):
        """solid blade from a (roughly planar) outline, `thick` across its plane"""
        pts = [Vector(q) for q in pts]
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0]).normalized()
        a = [self.bm.verts.new(q + n * thick / 2) for q in pts]
        b = [self.bm.verts.new(q - n * thick / 2) for q in pts]
        k = len(pts)
        self.bm.faces.new(a)
        self.bm.faces.new(b[::-1])
        for i in range(k):
            j = (i + 1) % k
            self.bm.faces.new((a[i], b[i], b[j], a[j]))
        self._mat(a + b, mat)

    def finish(self, smooth=False):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        vs = [v.co for v in bm.verts]
        c = (Vector([min(v[i] for v in vs) for i in range(3)]) + Vector([max(v[i] for v in vs) for i in range(3)])) / 2
        for v in bm.verts:
            v.co -= c
        me = bpy.data.meshes.new(self.name)
        bm.to_mesh(me)
        bm.free()
        for m in self.mats:
            me.materials.append(MATS[m])
        me.shade_smooth() if smooth else me.shade_flat()
        ob = bpy.data.objects.new(self.name, me)
        ob.location = c
        coll(self.coll).objects.link(ob)
        if self.bevel:
            bv = ob.modifiers.new('Bevel', 'BEVEL')
            bv.width, bv.segments, bv.limit_method = self.bevel, 1, 'ANGLE'
            bv.angle_limit = math.radians(30)
        return ob


def coll(name):
    if name not in COLLS:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLLS[name] = c
    return COLLS[name]


def curl_path(origin, u, v, length, curl, turns=1.25, n=14, lift=0.0):
    """wave-crest path in the plane (u, v): runs `length` along u while rising,
    then curls back over itself (spiral of radius `curl`)."""
    origin, u, v = Vector(origin), Vector(u).normalized(), Vector(v).normalized()
    pts = []
    straight = max(3, n // 3)
    for i in range(straight):
        t = i / straight
        pts.append(origin + u * length * t + v * (lift * t * t))
    c = origin + u * length + v * (lift + curl)
    for i in range(n - straight + 1):
        t = i / (n - straight)
        a = -math.pi / 2 + t * turns * 2 * math.pi
        r = curl * (1 - 0.55 * t)
        pts.append(c + u * (r * math.cos(a)) + v * (r * math.sin(a)))
    return pts


def taper(n, w0, w1, bulge=0.0):
    return [w0 + (w1 - w0) * (i / (n - 1)) + bulge * math.sin(math.pi * i / (n - 1)) for i in range(n)]


# ------------------------------------------------------------------ body
FRONT_X, FRONT_Y = 0.98, -1.05      # front leg / shoulder line
BACK_X, BACK_Y = 1.0, 1.9           # back leg / hip line


def build_body():
    # torso, shoulders and hips are ONE mesh so the legs grow out of real muscle masses
    p = Part('Body_Torso', 'Body')
    p.blob((0, -0.9, 2.78), (1.3, 1.1, 1.22), 'Fur_Navy', (0, 0, 0), 2, 0.03, 2)            # deep chest
    p.blob((0, 0.65, 2.62), (1.12, 1.85, 0.98), 'Fur_Navy', (0.08, 0, 0), 2, 0.03, 1)        # barrel / back
    p.blob((0, 1.85, 2.55), (1.08, 0.95, 0.98), 'Fur_Navy', (0, 0, 0), 2, 0.03, 3)           # rump
    for s in (-1, 1):
        p.blob((s * FRONT_X, FRONT_Y, 2.55), (0.62, 0.82, 0.95), 'Fur_Navy', (0.1, 0, 0), 2, 0.03, 4)   # shoulder
        p.blob((s * BACK_X, BACK_Y, 2.45), (0.7, 0.95, 1.0), 'Fur_Navy', (-0.15, 0, 0), 2, 0.03, 5)    # hip
    p.finish()
    p = Part('Body_ChestPatch', 'Body')
    p.blob((0, -1.68, 2.5), (0.8, 0.42, 1.0), 'Fur_Gray', (0.22, 0, 0), 2, 0.03, 6)           # chest blaze, set into the chest
    p.blob((0, 0.25, 1.68), (0.78, 1.35, 0.3), 'Fur_Gray', (0.04, 0, 0), 1, 0.03, 7)          # belly
    p.finish()
    # thick neck lofted from the chest up into the back of the skull
    p = Part('Body_Neck', 'Body')
    p.loft([Vector((0, -0.55, 2.95)), Vector((0, -1.25, 3.65)), Vector((0, -1.85, 4.2)), Vector((0, -2.15, 4.45))],
           [(1.08, 0.98), (0.95, 0.88), (0.84, 0.76), (0.7, 0.62)], 'Fur_Navy', segs=8)
    p.finish()


# ------------------------------------------------------------------ head
HEAD_C = Vector((0, -2.3, 4.45))


def build_head():
    """one hound head: navy skull, slate muzzle and brow band that overlap into each other,
    and a single grey lower face (cheeks + jaw + throat) that runs down into the chest"""
    hx, hy, hz = HEAD_C
    p = Part('Head', 'Head')
    p.blob(HEAD_C, (0.98, 0.92, 0.8), 'Fur_Navy', (0.08, 0, 0), 2, 0.03, 10)                      # skull
    p.blob((0, hy - 0.72, hz - 0.2), (0.64, 0.86, 0.42), 'Fur_SlateBlue', (0.1, 0, 0), 2, 0.03, 11)  # muzzle, sunk into skull
    p.blob((0, hy - 0.45, hz + 0.12), (0.46, 0.85, 0.24), 'Fur_Navy', (0.2, 0, 0), 1, 0.03, 12)       # nose bridge
    p.blob((0, hy - 0.6, hz + 0.33), (0.82, 0.3, 0.17), 'Fur_SlateBlue', (0.25, 0, 0), 1, 0.03, 13)   # brow band
    for s in (-1, 1):   # brows angle down toward the nose: confident look
        p.box((s * 0.42, hy - 0.8, hz + 0.32), (0.46, 0.24, 0.13), 'Fur_SlateBlue', (0.3, s * -0.1, s * 0.28))
    p.finish()
    p = Part('Head_Jaw', 'Head')
    p.blob((0, hy - 0.72, hz - 0.6), (0.58, 0.8, 0.25), 'Fur_Gray', (0.12, 0, 0), 1, 0.03, 15)       # lower jaw
    for s in (-1, 1):
        p.blob((s * 0.7, hy - 0.28, hz - 0.38), (0.38, 0.52, 0.42), 'Fur_Gray', (0, 0, s * -0.35), 1, 0.04, 14)  # cheek
    p.blob((0, hy + 0.15, hz - 0.85), (0.62, 0.62, 0.42), 'Fur_Gray', (0.3, 0, 0), 1, 0.03, 17)      # throat -> chest
    p.finish()
    p = Part('Head_Nose', 'Head')
    p.blob((0, hy - 1.5, hz - 0.02), (0.33, 0.2, 0.2), 'Nose_Dark', (0.25, 0, 0), 1, 0.03, 16)
    p.finish()
    # grin along the muzzle / jaw seam, corners lifted for a friendly-boss smirk
    p = Part('Head_Mouth', 'Head', 0)
    pts = []
    for i in range(11):
        t = -1 + 2 * i / 10
        x = 0.6 * t
        y = hy - 0.72 - 0.86 * math.sqrt(max(0.0, 1 - (x / 0.66) ** 2)) * 0.98
        pts.append(Vector((x, y, hz - 0.4 + 0.13 * t * t)))
    p.sweep(pts, [0.06] * len(pts), 0.06, (0, 0, 1), 'Mouth_Dark')
    p.finish()
    p = Part('Head_Teeth', 'Head', 0.008)
    for x, L, r in ((-0.28, 0.24, 0.075), (0.28, 0.24, 0.075), (-0.12, 0.1, 0.05), (0.12, 0.1, 0.05)):
        y = hy - 0.72 - 0.86 * math.sqrt(max(0.0, 1 - (x / 0.66) ** 2)) * 0.98 + 0.02
        p.cone((x, y, hz - 0.4 + 0.13 * (x / 0.6) ** 2), (0, -0.1, -1), L, r, 'Teeth_White', 4, spin=0.78)
    p.finish()
    for s, side in ((-1, 'Right'), (1, 'Left')):
        p = Part(f'Eye_{side}', 'Head', 0)
        p.blob((s * 0.45, hy - 0.78, hz + 0.14), (0.21, 0.08, 0.13), 'Eye_Glow', (0.3, s * 0.4, s * -0.28), 1, 0.0, 20)
        p.finish()
        p = Part(f'Eye_{side}_Glint', 'Head', 0)
        p.blob((s * 0.4, hy - 0.85, hz + 0.19), (0.045, 0.025, 0.045), 'Eye_Glint', (0, 0, 0), 1, 0.0, 21)
        p.finish()
    # two balanced, medium swept-back fin ears flanking the crown
    for s, side in ((-1, 'Right'), (1, 'Left')):
        p = Part(f'Ear_{side}', 'Head', 0.02)
        blade = [(s * 0.4, hy - 0.22, hz + 0.6), (s * 0.7, hy + 0.42, hz + 0.42),
                 (s * 1.0, hy + 1.05, hz + 1.3), (s * 0.6, hy + 0.05, hz + 1.05)]
        p.fin(blade, 0.2, 'Fur_Navy')
        memb = [(s * 0.5, hy - 0.05, hz + 0.68), (s * 0.7, hy + 0.42, hz + 0.56),
                (s * 0.93, hy + 0.9, hz + 1.2), (s * 0.62, hy + 0.12, hz + 0.98)]
        p.fin(memb, 0.24, 'Armor_Aqua')
        p.finish()


# ------------------------------------------------------------------ crown
def build_crown():
    """three-point crest centred on top of the skull between the ears, base sunk into the head"""
    hx, hy, hz = HEAD_C
    yb, zb = hy - 0.05, hz + 0.6
    prof = [(-0.42, 0.0), (0.42, 0.0), (0.42, 0.2), (0.3, 0.44), (0.2, 0.25), (0.0, 0.66),
            (-0.2, 0.25), (-0.3, 0.44), (-0.42, 0.2)]
    tilt = Matrix.Rotation(-0.18, 3, 'X')
    p = Part('Crown_Crest', 'Crown', 0.02)
    front = [Vector((x, -0.14, z)) for x, z in prof]
    verts = [tilt @ v + Vector((0, yb, zb)) for v in front] + \
            [tilt @ (v + Vector((0, 0.28, 0))) + Vector((0, yb, zb)) for v in front]
    n = len(prof)
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + \
            [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    p.poly(verts, faces, 'Crown_Navy')
    p.finish()
    p = Part('Crown_Droplets', 'Crown', 0)
    for x, z, r in ((0.0, 0.66, 0.12), (0.3, 0.44, 0.085), (-0.3, 0.44, 0.085)):
        c = tilt @ Vector((x, 0.0, z + r * 0.55)) + Vector((0, yb, zb))
        p.blob(c, (r, r, r), 'Crown_Droplet', (0, 0, 0), 2, 0.0, 31)
        p.cone(c + Vector((0, 0, r * 0.35)), (0, 0.15, 1), r * 1.8, r * 0.78, 'Crown_Droplet', 8)
    p.finish(smooth=True)


# ------------------------------------------------------------------ legs
def build_legs():
    LEGS = [('FrontLeft', 1, True), ('FrontRight', -1, True), ('BackLeft', 1, False), ('BackRight', -1, False)]
    for name, s, front in LEGS:
        if front:
            x, y = s * FRONT_X, FRONT_Y
            path = [Vector((x, y + 0.1, 2.75)), Vector((x * 1.02, y - 0.12, 1.65)),
                    Vector((x * 1.02, y - 0.3, 0.85)), Vector((x, y - 0.4, 0.45))]
            radii = [(0.64, 0.74), (0.56, 0.62), (0.47, 0.52), (0.5, 0.55)]
            paw_y = y - 0.55
        else:
            x, y = s * BACK_X, BACK_Y
            path = [Vector((x, y - 0.1, 2.65)), Vector((x * 1.02, y + 0.35, 1.6)),
                    Vector((x * 1.02, y + 0.15, 0.85)), Vector((x, y + 0.05, 0.45))]
            radii = [(0.7, 0.88), (0.56, 0.64), (0.46, 0.5), (0.5, 0.55)]
            paw_y = y - 0.15
        # one continuous tapered leg from inside the shoulder/hip down to the paw
        p = Part(f'Leg_{name}', 'Legs')
        p.loft(path, radii, 'Fur_Navy', segs=8)
        p.finish()
        # large, simple planted paw with four big toes
        p = Part(f'Paw_{name}', 'Legs')
        p.blob((x, paw_y, 0.3), (0.74, 0.82, 0.36), 'Fur_Navy', (0, 0, 0), 2, 0.03, 46, flat_bottom=0.0)
        for k, tx in enumerate((-0.5, -0.17, 0.17, 0.5)):
            p.blob((x + tx, paw_y - 0.68 + abs(tx) * 0.22, 0.22), (0.2, 0.26, 0.24), 'Stone_LightBlue',
                   (0.25, 0, 0), 1, 0.04, 47 + k, flat_bottom=0.0)
        p.finish()


# ------------------------------------------------------------------ water mane
def wave_collar(name, coll_name, center, axis, radius, a0, a1, width, flare, thick, mat,
                lobes=3, segs=14, rows=5, flick=0.18, phase=0.0):
    """broad curved wave layer wrapped around a body part.
    Its base hugs a ring of `radius` around `axis` (attached to the body); the blade flows
    back along `axis`, flares outward and flicks up at the edge. The free edge is
    scalloped into `lobes` wave crests. Angles in degrees: 0 = top, +90 = creature's left (+X)."""
    A = Vector(axis).normalized()
    up = (Vector((0, 0, 1)) - A * A.z).normalized()
    side = A.cross(up)
    C = Vector(center)
    p = Part(name, coll_name, 0.02)
    outer, inner = [], []
    for i in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * i / segs)
        r = up * math.cos(a) + side * math.sin(a)
        span = (i / segs)
        w = width * (0.6 + 0.4 * math.cos(lobes * 2 * math.pi * span + phase))     # wave crests
        w *= 0.55 + 0.45 * math.sin(math.pi * span) ** 0.5                         # taper at the ends
        orow, irow = [], []
        for k in range(rows + 1):
            t = k / rows
            crest = 0.5 + 0.5 * math.cos(lobes * 2 * math.pi * span + phase)            # crests flick out more
            rad = radius - 0.06 + flare * t ** 1.6 + flick * (0.5 + crest) * max(0.0, (t - 0.6) / 0.4) ** 2
            pos = C + r * rad + A * (w * t)
            th = thick * (1 - 0.65 * t)
            orow.append(p.bm.verts.new(pos))
            irow.append(p.bm.verts.new(pos - r * th))
        outer.append(orow)
        inner.append(irow)
    bm = p.bm
    for i in range(segs):
        for k in range(rows):
            bm.faces.new((outer[i][k], outer[i + 1][k], outer[i + 1][k + 1], outer[i][k + 1]))
            bm.faces.new((inner[i][k + 1], inner[i + 1][k + 1], inner[i + 1][k], inner[i][k]))
        bm.faces.new((outer[i][rows], outer[i + 1][rows], inner[i + 1][rows], inner[i][rows]))  # free edge
        bm.faces.new((inner[i][0], inner[i + 1][0], outer[i + 1][0], outer[i][0]))              # base
    for i, flip in ((0, False), (segs, True)):                                                  # arc ends
        for k in range(rows):
            f = (outer[i][k], outer[i][k + 1], inner[i][k + 1], inner[i][k])
            bm.faces.new(f[::-1] if flip else f)
    p._mat([v for row in outer + inner for v in row], mat)
    p.finish()


def build_armor():
    # the chest plate kept as a wave-shaped crest across the top of the chest (front arc of
    # the neck collar), plus low slate hip plates. No bars / bracers.
    wave_collar('Armor_ChestWave', 'Water Armor', (0, -1.9, 3.9), (0, 1, -0.55), 1.0, 132, 228,
                0.6, 0.22, 0.26, 'Armor_Aqua', lobes=2, segs=10, flick=0.15)
    for s, side in ((-1, 'Right'), (1, 'Left')):
        p = Part(f'Armor_Hip_{side}', 'Water Armor')
        p.blob((s * 1.56, BACK_Y - 0.05, 2.62), (0.14, 0.8, 0.58), 'Armor_Slate', (0.15, s * 0.22, 0), 2, 0.02, 62)
        p.finish()


def build_mane_and_tail():
    hx, hy, hz = HEAD_C
    # three layered wave collars stepping back from the head over the neck and shoulders;
    # each wraps the top and sides (the throat, face and chest stay open)
    wave_collar('Mane_Head', 'Mane and Tail', (0, hy + 0.5, hz + 0.02), (0, 1, -0.3), 0.88, -112, 112,
                0.95, 0.3, 0.26, 'Armor_Aqua', lobes=3, phase=0.4)
    wave_collar('Mane_Neck', 'Mane and Tail', (0, -1.5, 3.82), (0, 1, -0.55), 1.0, -122, 122,
                1.05, 0.38, 0.28, 'Armor_AquaLight', lobes=3, phase=1.4)
    wave_collar('Mane_Shoulders', 'Mane and Tail', (0, -0.8, 3.0), (0, 1, -0.45), 1.5, -100, 100,
                0.95, 0.4, 0.3, 'Armor_Aqua', lobes=3, phase=0.2, flick=0.28)
    # curled wave tail: sweeps back from the rump, rises and curls over (like a breaking wave)
    p = Part('Tail_Wave', 'Mane and Tail', 0.02)
    pts = curl_path((0, 2.55, 3.05), (0, 1, 0.35), (0, -0.25, 1), 1.0, 0.62, 0.82, 20, 0.45)
    p.sweep(pts, taper(len(pts), 0.95, 0.22, 0.3), 0.62, (1, 0, 0), 'Armor_Aqua')
    p.finish()
    p = Part('Tail_InnerWave', 'Mane and Tail', 0.02)
    pts2 = curl_path((0, 2.75, 3.15), (0, 1, 0.35), (0, -0.25, 1), 0.85, 0.42, 0.78, 16, 0.35)
    for sx in (0.3, -0.3):
        p.sweep([q + Vector((sx, 0, 0)) for q in pts2], taper(len(pts2), 0.5, 0.12, 0.12), 0.2, (1, 0, 0),
                'Armor_AquaLight')
    p.finish()


# ------------------------------------------------------------------ effects
def droplet(p, c, r):
    c = Vector(c)
    p.blob(c, (r, r, r), 'Water_Clear', (0, 0, 0), 2, 0.0, 0)
    p.cone(c + Vector((0, 0, r * 0.4)), (0, 0, 1), r * 1.7, r * 0.8, 'Water_Clear', 8)


def build_effects():
    # just a few small droplets near the mane and a front paw
    p = Part('Water_Droplets', 'Effects', 0)
    for c, r in (((1.85, -0.9, 4.35), 0.09), ((-1.8, -0.5, 4.0), 0.08), ((1.85, -2.5, 0.7), 0.07)):
        droplet(p, c, r)
    p.finish(smooth=True)


# ------------------------------------------------------------------ scene
def build_camera_and_lights():
    sc = bpy.context.scene
    lc = coll('CameraAndLights')
    cam = bpy.data.cameras.new('Camera_ThreeQuarter')
    cam.lens = 58
    co = bpy.data.objects.new('Camera_ThreeQuarter', cam)
    co.location = (9.0, -11.5, 4.6)
    co.rotation_euler = (Vector((0.0, 0.6, 2.65)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(co)
    sc.camera = co
    for name, loc, e, size, col in (('Light_Key', (6, -9, 9), 1300, 6, (1, 0.97, 0.93)),
                                    ('Light_Fill', (-9, -6, 4), 450, 7, (0.9, 0.95, 1.0)),
                                    ('Light_Rim', (-2, 9, 7), 1100, 5, (0.85, 0.95, 1.0))):
        li = bpy.data.lights.new(name, 'AREA')
        li.energy, li.size, li.color = e, size, col
        o = bpy.data.objects.new(name, li)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 2.5)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        lc.objects.link(o)
    w = bpy.data.worlds.new('World_Studio')
    sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.92, 0.9, 0.88, 1)
    bg.inputs['Strength'].default_value = 0.35
    me = bpy.data.meshes.new('Ground_ShadowCatcher')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=20)
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new('Ground_ShadowCatcher', me)
    g.is_shadow_catcher = True
    lc.objects.link(g)
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.render.resolution_x = sc.render.resolution_y = 1200
    sc.view_settings.view_transform = 'Standard'


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system, sc.unit_settings.scale_length = 'METRIC', 1.0
    build_materials()
    for c in ('Body', 'Head', 'Legs', 'Water Armor', 'Mane and Tail', 'Crown', 'Effects'):
        coll(c)
    build_body()
    build_head()
    build_crown()
    build_legs()
    build_armor()
    build_mane_and_tail()
    build_effects()
    build_camera_and_lights()
    path = os.path.join(HERE, 'KingRainhound_Refined.blend')      # earlier versions are kept
    bpy.ops.wm.save_as_mainfile(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Ground_ShadowCatcher']
    print(f'King Rainhound: {len(meshes)} mesh objects, {sum(len(o.data.polygons) for o in meshes)} faces')
    print('Saved:', path)


if __name__ == '__main__':
    main()
