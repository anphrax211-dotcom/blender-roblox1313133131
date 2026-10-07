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
Saves KingRainhound_Refined_v2.blend next to this script and prints the full path
(earlier KingRainhound*.blend files are left untouched). Cameras: Camera_ThreeQuarter, Camera_Side.
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

    def sweep(self, pts, widths, thick, normal, mat, closed_tip=True, section='hex'):
        """ribbon along a path: width across the path, `thick` along `normal`
        (a vector, or a function (index, point) -> vector). section: 'hex' chunky or
        'round' (10-sided oval, for smooth water)."""
        rings = []
        for i, p in enumerate(pts):
            n = Vector(normal(i, p) if callable(normal) else normal).normalized()
            a = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
            a.normalize()
            side = a.cross(n).normalized()
            n = side.cross(a).normalized() if n.dot(side.cross(a)) >= 0 else -side.cross(a).normalized()
            w, t = widths[i] / 2, thick * (0.35 + 0.65 * widths[i] / max(widths)) / 2
            if section == 'round':
                ring = [p + side * w * math.cos(k / 10 * 2 * math.pi) + n * t * math.sin(k / 10 * 2 * math.pi)
                        for k in range(10)]
            else:
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
        if smooth:
            me.shade_smooth()
            if hasattr(me, 'set_sharp_from_angle'):
                me.set_sharp_from_angle(angle=math.radians(55))
        else:
            me.shade_flat()
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


def chaikin(pts, vals, iters=2):
    """round off a polyline (keeps the end points) - gives limbs soft, natural joint bends"""
    for _ in range(iters):
        np_, nv = [pts[0]], [vals[0]]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            va, vb = vals[i], vals[i + 1]
            for t in (0.25, 0.75):
                np_.append(a.lerp(b, t))
                nv.append(tuple(x + (y - x) * t for x, y in zip(va, vb)))
        np_.append(pts[-1]); nv.append(vals[-1])
        pts, vals = np_, nv
    return pts, vals


def taper(n, w0, w1, bulge=0.0):
    return [w0 + (w1 - w0) * (i / (n - 1)) + bulge * math.sin(math.pi * i / (n - 1)) for i in range(n)]


# ------------------------------------------------------------------ body
FRONT_X, FRONT_Y = 0.98, -1.05      # front leg / shoulder line
BACK_X, BACK_Y = 1.0, 1.9           # back leg / hip line


def build_body():
    # torso, shoulders and hips are ONE mesh so the legs grow out of real muscle masses
    p = Part('Body_Torso', 'Body')
    p.blob((0, -0.95, 2.92), (1.35, 1.12, 1.25), 'Fur_Navy', (0, 0, 0), 2, 0.03, 2)          # deep, high chest
    p.blob((0, 0.65, 2.7), (1.1, 1.9, 0.9), 'Fur_Navy', (0.06, 0, 0), 2, 0.03, 1)            # barrel / back (tucked belly)
    p.blob((0, 1.85, 2.55), (1.08, 0.95, 0.98), 'Fur_Navy', (0, 0, 0), 2, 0.03, 3)           # rump
    for s in (-1, 1):
        p.blob((s * FRONT_X, FRONT_Y, 2.72), (0.66, 0.85, 1.0), 'Fur_Navy', (0.1, 0, 0), 2, 0.03, 4)    # shoulder
        p.blob((s * BACK_X, BACK_Y, 2.45), (0.7, 0.95, 1.0), 'Fur_Navy', (-0.15, 0, 0), 2, 0.03, 5)    # hip
    p.finish()
    p = Part('Body_ChestPatch', 'Body')
    p.blob((0, -1.68, 2.62), (0.72, 0.4, 0.88), 'Fur_Gray', (0.22, 0, 0), 2, 0.03, 6)         # chest blaze, set into the chest
    p.blob((0, 0.1, 1.86), (0.7, 1.25, 0.24), 'Fur_Gray', (0.04, 0, 0), 1, 0.03, 7)           # belly
    p.finish()
    # thick neck lofted from the chest up into the back of the skull
    p = Part('Body_Neck', 'Body')
    path, radii = chaikin([Vector((0, -0.5, 3.05)), Vector((0, -1.4, 3.8)), Vector((0, -2.1, 4.35)),
                           Vector((0, -2.6, 4.68))],
                          [(1.08, 0.98), (0.94, 0.86), (0.82, 0.74), (0.7, 0.62)], 1)
    p.loft(path, radii, 'Fur_Navy', segs=10)
    p.finish()


# ------------------------------------------------------------------ head
HEAD_C = Vector((0, -2.85, 4.78))     # head projects forward from the shoulders


def build_head():
    """one hound head: navy skull, slate muzzle and brow band that overlap into each other,
    and a single grey lower face (cheeks + jaw + throat) that runs down into the chest"""
    hx, hy, hz = HEAD_C
    p = Part('Head', 'Head')
    p.blob(HEAD_C, (1.04, 0.95, 0.82), 'Fur_Navy', (0.08, 0, 0), 2, 0.03, 10)                      # skull
    p.blob((0, hy - 0.84, hz - 0.2), (0.62, 1.0, 0.41), 'Fur_SlateBlue', (0.1, 0, 0), 2, 0.03, 11)   # longer muzzle, sunk into skull
    p.blob((0, hy - 0.55, hz + 0.1), (0.44, 0.98, 0.24), 'Fur_Navy', (0.18, 0, 0), 1, 0.03, 12)       # nose bridge
    p.blob((0, hy - 0.6, hz + 0.33), (0.82, 0.3, 0.17), 'Fur_SlateBlue', (0.25, 0, 0), 1, 0.03, 13)   # brow band
    for s in (-1, 1):   # brows angle down toward the nose: confident look
        p.box((s * 0.42, hy - 0.8, hz + 0.32), (0.46, 0.24, 0.13), 'Fur_SlateBlue', (0.3, s * -0.1, s * 0.28))
    p.finish()
    p = Part('Head_Jaw', 'Head')
    p.blob((0, hy - 0.84, hz - 0.58), (0.56, 0.92, 0.24), 'Fur_Gray', (0.1, 0, 0), 1, 0.03, 15)      # lower jaw
    for s in (-1, 1):
        p.blob((s * 0.66, hy - 0.2, hz - 0.42), (0.3, 0.5, 0.32), 'Fur_Gray', (0.2, 0, s * -0.3), 2, 0.03, 14)   # cheek
    p.blob((0, hy + 0.3, hz - 0.85), (0.5, 0.62, 0.36), 'Fur_Gray', (0.45, 0, 0), 2, 0.03, 17)        # throat -> chest
    p.finish()
    p = Part('Head_Nose', 'Head')
    p.blob((0, hy - 1.76, hz - 0.03), (0.32, 0.2, 0.2), 'Nose_Dark', (0.25, 0, 0), 1, 0.03, 16)
    p.finish()
    # grin along the muzzle / jaw seam, corners lifted for a friendly-boss smirk
    p = Part('Head_Mouth', 'Head', 0)
    pts = []
    for i in range(11):
        t = -1 + 2 * i / 10
        x = 0.54 * t
        y = hy - 0.84 - 1.0 * math.sqrt(max(0.0, 1 - (x / 0.64) ** 2)) * 0.9
        pts.append(Vector((x, y, hz - 0.4 + 0.13 * t * t)))
    p.sweep(pts, [0.06] * len(pts), 0.06, (0, 0, 1), 'Mouth_Dark')
    p.finish()
    p = Part('Head_Teeth', 'Head', 0.008)
    for x, L, r in ((-0.28, 0.24, 0.075), (0.28, 0.24, 0.075), (-0.12, 0.1, 0.05), (0.12, 0.1, 0.05)):
        y = hy - 0.84 - 1.0 * math.sqrt(max(0.0, 1 - (x / 0.64) ** 2)) * 0.9 + 0.02
        p.cone((x, y, hz - 0.4 + 0.13 * (x / 0.54) ** 2), (0, -0.1, -1), L, r, 'Teeth_White', 4, spin=0.78)
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
        blade = [(s * 0.42, hy - 0.15, hz + 0.58), (s * 0.68, hy + 0.36, hz + 0.42),
                 (s * 0.88, hy + 0.98, hz + 0.95), (s * 0.58, hy + 0.08, hz + 0.88)]
        p.fin(blade, 0.2, 'Fur_Navy')
        memb = [(s * 0.51, hy + 0.0, hz + 0.63), (s * 0.68, hy + 0.37, hz + 0.53),
                (s * 0.83, hy + 0.86, hz + 0.9), (s * 0.6, hy + 0.14, hz + 0.82)]
        p.fin(memb, 0.24, 'Armor_Aqua')
        p.finish()


# ------------------------------------------------------------------ crown
def build_crown():
    """three-point crest centred on top of the skull between the ears, base sunk into the head"""
    hx, hy, hz = HEAD_C
    yb, zb = hy - 0.05, hz + 0.58
    prof = [(-0.42, 0.0), (0.42, 0.0), (0.42, 0.17), (0.3, 0.34), (0.2, 0.2), (0.0, 0.48),
            (-0.2, 0.2), (-0.3, 0.34), (-0.42, 0.17)]
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
    for x, z, r in ((0.0, 0.48, 0.11), (0.3, 0.34, 0.08), (-0.3, 0.34, 0.08)):
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
            # shoulder -> elbow tucked back -> wrist forward -> paw (dog foreleg)
            path = [Vector((x, y + 0.1, 2.95)), Vector((x * 1.03, y + 0.22, 1.78)),
                    Vector((x * 1.02, y - 0.22, 0.9)), Vector((x, y - 0.45, 0.45))]
            radii = [(0.66, 0.78), (0.52, 0.58), (0.4, 0.44), (0.5, 0.54)]
            paw_y = y - 0.6
        else:
            x, y = s * BACK_X, BACK_Y
            # hip -> stifle forward -> hock back -> paw (dog hind leg)
            path = [Vector((x, y - 0.05, 2.7)), Vector((x * 1.03, y - 0.35, 1.7)),
                    Vector((x * 1.02, y + 0.42, 0.95)), Vector((x, y + 0.2, 0.45))]
            radii = [(0.74, 0.94), (0.56, 0.64), (0.4, 0.44), (0.5, 0.54)]
            paw_y = y + 0.02
        # one continuous tapered leg from inside the shoulder/hip down to the paw
        p = Part(f'Leg_{name}', 'Legs')
        path, radii = chaikin(path, radii, 2)
        p.loft(path, radii, 'Fur_Navy', segs=10)
        p.finish()
        # large, simple planted paw with four big toes
        p = Part(f'Paw_{name}', 'Legs')
        p.blob((x, paw_y, 0.3), (0.74, 0.82, 0.36), 'Fur_Navy', (0, 0, 0), 2, 0.03, 46, flat_bottom=0.0)
        for k, tx in enumerate((-0.5, -0.17, 0.17, 0.5)):
            p.blob((x + tx, paw_y - 0.68 + abs(tx) * 0.22, 0.22), (0.2, 0.26, 0.24), 'Stone_LightBlue',
                   (0.25, 0, 0), 1, 0.04, 47 + k, flat_bottom=0.0)
        p.finish()


# ------------------------------------------------------------------ water mane
CHEST_C = Vector((0, -0.95, 2.92))      # centre of the chest mass (waves are pushed out from it)


def ribbon(name, coll_name, pts, widths, thick, normal, mat, bevel=0.015):
    """smooth, rounded water ribbon (oval section) - broad face outward, shade smooth"""
    p = Part(name, coll_name, bevel)
    p.sweep(pts, widths, thick, normal, mat, section='round')
    p.finish(smooth=True)


def ease_in(widths, k=4):
    """narrow, rounded root growing out of the body over the first k points"""
    return [w * (0.35 + 0.65 * math.sin(min(i / k, 1) * math.pi / 2)) for i, w in enumerate(widths)]


def side_wave(name, origin, u, v, length, curl, turns, width, thick, mat, lift=0.25, n=22):
    """one broad wave: grows out of the body, runs back, rises and curls over like a breaking wave"""
    origin = Vector(origin)
    root = origin - Vector((origin.x * 0.18, 0, 0))          # root starts a little inside the body
    pts = curl_path(root, u, v, length, curl, turns, n, lift)
    u_, v_ = Vector(u).normalized(), Vector(v).normalized()
    ribbon(name, 'Mane and Tail', pts, ease_in(taper(len(pts), width, width * 0.2, width * 0.32)), thick,
           u_.cross(v_), mat)


def build_armor():
    """the old cape / collar slabs are gone: the chest piece is now two smooth waves that
    wrap from the base of the throat around the chest and curl back over each shoulder"""
    hx, hy, hz = HEAD_C
    for s, side in ((-1, 'Right'), (1, 'Left')):
        pts = []
        for i in range(10):                      # around the chest, rising toward the shoulder
            t = i / 9
            phi = s * math.radians(8 + 72 * t)
            pts.append(CHEST_C + Vector((math.sin(phi) * 1.36, -math.cos(phi) * 1.3 - 0.02, 0.05 + 0.5 * t)))
        end = pts[-1]
        curl = curl_path(end, (0, 1, 0.15), (0, 0, 1), 0.2, 0.3, 0.85, 12, 0.05)[1:]
        pts += curl
        widths = [0.24 + 0.56 * math.sin(min(1, i / 6) * math.pi / 2) for i in range(10)] + taper(len(curl), 0.78, 0.16)

        def nrm(i, q, s=s):
            d = q - CHEST_C
            if i >= 10:
                return Vector((s, -0.15, 0.1)).normalized()
            return Vector((d.x, d.y, 0)).normalized()
        ribbon(f'Water_ChestWave_{side}', 'Water Armor', pts, widths, 0.26, nrm, 'Armor_Aqua')


def build_mane_and_tail():
    hx, hy, hz = HEAD_C
    # crest wave running from behind the crown down the top of the neck, curling up at the withers
    side_wave('Mane_Crest', (0, hy + 0.6, hz + 0.42), (0, 1, -0.55), (0, 0.45, 1), 1.65, 0.4, 0.66,
              1.0, 0.3, 'Armor_Aqua', lift=0.2)
    for s, side in ((-1, 'Right'), (1, 'Left')):
        # three staggered waves per side, with dark body showing between them
        side_wave(f'Mane_Upper_{side}', (s * 0.74, hy + 0.55, hz - 0.18), (s * 0.25, 1, -0.32), (0, 0.3, 1),
                  1.1, 0.36, 0.62, 0.95, 0.24, 'Armor_AquaLight')
        side_wave(f'Mane_Middle_{side}', (s * 0.88, -1.9, 3.85), (s * 0.22, 1, -0.42), (0, 0.35, 1),
                  1.3, 0.4, 0.62, 1.05, 0.26, 'Armor_Aqua')
        side_wave(f'Mane_Shoulder_{side}', (s * 1.12, -1.2, 3.2), (s * 0.15, 1, -0.3), (0, 0.3, 1),
                  1.4, 0.42, 0.62, 1.05, 0.26, 'Armor_AquaLight')
    # large curled wave tail sweeping back and up from the rump, breaking forward over itself
    pts = curl_path((0, 2.55, 3.0), (0, 1, 0.45), (0, -0.3, 1), 1.25, 0.82, 0.9, 30, 0.45)
    ribbon('Tail_Wave', 'Mane and Tail', pts, ease_in(taper(len(pts), 1.3, 0.3, 0.45), 5), 0.55, (1, 0, 0), 'Armor_Aqua', 0.02)
    pts2 = curl_path((0, 2.8, 3.15), (0, 1, 0.45), (0, -0.3, 1), 1.0, 0.56, 0.85, 24, 0.35)
    for sx, sd in ((0.3, 'Left'), (-0.3, 'Right')):
        ribbon(f'Tail_InnerWave_{sd}', 'Mane and Tail', [q + Vector((sx, 0, 0)) for q in pts2],
               taper(len(pts2), 0.7, 0.16, 0.22), 0.18, (1, 0, 0), 'Armor_AquaLight')


# ------------------------------------------------------------------ effects
def droplet(p, c, r):
    c = Vector(c)
    p.blob(c, (r, r, r), 'Water_Clear', (0, 0, 0), 2, 0.0, 0)
    p.cone(c + Vector((0, 0, r * 0.4)), (0, 0, 1), r * 1.7, r * 0.8, 'Water_Clear', 8)


def build_effects():
    # just a few small droplets near the mane and a front paw
    p = Part('Water_Droplets', 'Effects', 0)
    for c, r in (((1.6, -1.3, 4.6), 0.07), ((-1.6, -0.8, 4.3), 0.06), ((0.6, 4.7, 4.4), 0.07)):
        droplet(p, c, r)
    p.finish(smooth=True)


# ------------------------------------------------------------------ scene
def build_camera_and_lights():
    sc = bpy.context.scene
    lc = coll('CameraAndLights')
    cam = bpy.data.cameras.new('Camera_ThreeQuarter')
    cam.lens = 47
    co = bpy.data.objects.new('Camera_ThreeQuarter', cam)
    co.location = (-11.0, -10.0, 5.2)
    co.rotation_euler = (Vector((0.0, 0.25, 2.85)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(co)
    sc.camera = co
    side = bpy.data.cameras.new('Camera_Side')
    side.lens = 47
    so = bpy.data.objects.new('Camera_Side', side)
    so.location = (-17.5, 0.8, 3.3)
    so.rotation_euler = (Vector((0.0, 0.9, 2.85)) - so.location).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(so)
    for name, loc, e, size, col in (('Light_Key', (-8, -9, 9), 1400, 6, (1, 0.97, 0.93)),
                                    ('Light_Fill', (8, -7, 3.5), 450, 7, (0.9, 0.95, 1.0)),
                                    ('Light_Rim', (5, 9, 7), 1200, 5, (0.85, 0.95, 1.0))):
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
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1200
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
    path = os.path.join(HERE, 'KingRainhound_Refined_v2.blend')   # earlier versions are kept
    bpy.ops.wm.save_as_mainfile(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Ground_ShadowCatcher']
    print(f'King Rainhound: {len(meshes)} mesh objects, {sum(len(o.data.polygons) for o in meshes)} faces')
    print('Saved:', path)


if __name__ == '__main__':
    main()
