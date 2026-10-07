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
Saves KingRainhound.blend next to this script and prints the full path.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
COLLS = {}
HEAD_PIVOT, HEAD_SCALE = (0, -1.55, 3.8), 1.28     # head drawn at base size, then enlarged
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
    material('Fur_Gray', (0.3, 0.31, 0.34), 0.6)                    # ~149,151,157 chest / jaw
    material('Stone_LightBlue', (0.22, 0.33, 0.58), 0.55)         # ~130,155,200 toes / leg plates
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
    def __init__(self, name, coll, bevel=0.025):
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

    def scale_about(self, pivot, k):
        pivot = Vector(pivot)
        for v in self.bm.verts:
            v.co = pivot + (v.co - pivot) * k

    def finish(self, smooth=False):
        bm = self.bm
        if self.coll in ('Head', 'Crown'):
            self.scale_about(HEAD_PIVOT, HEAD_SCALE)
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
            bv.angle_limit = math.radians(25)
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
def build_body():
    p = Part('Body_Torso', 'Body')
    p.blob((0, 0.7, 2.45), (1.2, 1.95, 1.1), 'Fur_Navy', (0.12, 0, 0), 2, 0.05, 1)
    p.blob((0, -0.85, 2.75), (1.25, 1.05, 1.25), 'Fur_Navy', (0, 0, 0), 2, 0.05, 2)       # broad chest
    p.blob((0, 1.9, 2.5), (1.05, 0.95, 0.95), 'Fur_SlateBlue', (0, 0, 0), 2, 0.06, 3)       # haunch mass
    p.finish()
    p = Part('Body_ChestPatch', 'Body')
    p.blob((0, -1.55, 2.35), (0.85, 0.55, 1.1), 'Fur_Gray', (0.25, 0, 0), 2, 0.05, 4)
    p.blob((0, -0.3, 1.55), (0.75, 1.0, 0.35), 'Fur_Gray', (0, 0, 0), 1, 0.06, 5)           # belly
    p.finish()
    p = Part('Body_Neck', 'Body')
    p.blob((0, -1.45, 3.55), (0.85, 0.75, 0.95), 'Fur_Navy', (-0.35, 0, 0), 2, 0.05, 6)
    p.finish()
    p = Part('Body_BackSpikes', 'Body', 0.015)
    for i, (y, z, h) in enumerate(((0.05, 3.45, 0.5), (0.75, 3.35, 0.42), (1.4, 3.25, 0.34))):
        p.cone((0, y, z), (0, 0.45, 1), h, 0.2, 'Armor_Aqua', 4, spin=0.78)
    p.finish()


# ------------------------------------------------------------------ head
def build_head():
    p = Part('Head', 'Head')
    p.blob((0, -2.0, 4.3), (0.78, 0.72, 0.62), 'Fur_Navy', (0.1, 0, 0), 2, 0.05, 10)           # skull
    p.blob((0, -2.7, 4.12), (0.5, 0.62, 0.36), 'Fur_SlateBlue', (0.12, 0, 0), 1, 0.05, 11)     # muzzle top
    p.blob((-0.55, -2.25, 4.05), (0.3, 0.35, 0.3), 'Fur_Gray', (0, 0, 0.3), 1, 0.06, 12)       # cheeks
    p.blob((0.55, -2.25, 4.05), (0.3, 0.35, 0.3), 'Fur_Gray', (0, 0, -0.3), 1, 0.06, 13)
    for s in (-1, 1):                                                                            # brow ridges
        p.box((s * 0.36, -2.4, 4.62), (0.42, 0.3, 0.13), 'Fur_SlateBlue', (0.25, s * 0.25, s * 0.35))
    p.finish()
    p = Part('Head_Jaw', 'Head')
    p.blob((0, -2.6, 3.78), (0.44, 0.58, 0.2), 'Fur_Gray', (0.15, 0, 0), 1, 0.05, 14)
    p.finish()
    p = Part('Head_Nose', 'Head', 0.02)
    p.blob((0, -3.28, 4.22), (0.24, 0.17, 0.15), 'Nose_Dark', (0.2, 0, 0), 1, 0.04, 15)
    p.finish()
    # grin + teeth
    p = Part('Head_Mouth', 'Head', 0)
    pts = [Vector((x, -2.62 - 0.55 * math.cos(x * 1.6), 3.95 + 0.05 * (x / 0.5) ** 2 + 0.06 * x)) for x in
           [(-0.5 + i / 8) for i in range(9)]]
    p.sweep(pts, [0.05] * 9, 0.05, (0, 0, 1), 'Mouth_Dark')
    p.finish()
    p = Part('Head_Teeth', 'Head', 0.005)
    for x, L in ((-0.27, 0.2), (0.27, 0.2), (-0.12, 0.09), (0.12, 0.09)):
        p.cone((x, -3.1 + abs(x) * 0.6, 4.0), (0, -0.15, -1), L, 0.06, 'Teeth_White', 4)
    p.finish()
    # eyes: angled glowing aqua almonds + glints
    for s, side in ((-1, 'Right'), (1, 'Left')):
        p = Part(f'Eye_{side}', 'Head', 0)
        p.blob((s * 0.37, -2.6, 4.46), (0.2, 0.08, 0.13), 'Eye_Glow', (0.3, s * 0.35, s * -0.3), 1, 0.0, 20)
        p.finish()
        p = Part(f'Eye_{side}_Glint', 'Head', 0)
        p.blob((s * 0.33, -2.67, 4.5), (0.035, 0.02, 0.035), 'Eye_Glint', (0, 0, 0), 1, 0.0, 21)
        p.finish()
    # swept-back ear fins: big faceted blades, navy outside, slate inner face
    for s, side in ((-1, 'Right'), (1, 'Left')):
        p = Part(f'Ear_{side}', 'Head', 0.02)
        b0, b1, b2 = Vector((s * 0.35, -2.05, 4.75)), Vector((s * 0.72, -1.65, 4.6)), Vector((s * 0.55, -1.75, 4.9))
        tip = Vector((s * 0.95, -1.0, 5.75))
        mid = Vector((s * 0.82, -1.25, 5.25))
        p.poly([b0, b1, tip, b2, mid + Vector((s * 0.1, 0.05, 0))],
               [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], 'Fur_Navy')
        inner = [b0 + Vector((0, -0.06, 0.05)), b1 + Vector((-s * 0.08, -0.06, 0.05)), tip + Vector((-s * 0.06, -0.12, -0.15)),
                 mid + Vector((-s * 0.05, -0.14, 0))]
        p.poly(inner, [(0, 1, 3), (1, 2, 3)], 'Fur_SlateBlue')
        p.finish()


# ------------------------------------------------------------------ crown
def build_crown():
    p = Part('Crown_Band', 'Crown', 0.015)
    c = Vector((0, -1.95, 4.85))
    n = 10
    ring_o, ring_i = [], []
    for i in range(n):
        a = i / n * 2 * math.pi
        ring_o.append(c + Vector((0.42 * math.cos(a), 0.36 * math.sin(a), 0)))
    verts, faces = [], []
    # band (prism ring) with 5 spikes, front one tallest
    for i, q in enumerate(ring_o):
        verts += [q, q + Vector((0, 0, 0.22))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    p.poly(verts, faces, 'Crown_Navy')
    p.blob(c + Vector((0, 0, 0.11)), (0.4, 0.34, 0.1), 'Crown_Navy', (0, 0, 0), 1, 0.0, 30)
    spikes = [(-math.pi / 2, 0.75), (-math.pi / 2 - 0.9, 0.5), (-math.pi / 2 + 0.9, 0.5),
              (-math.pi / 2 - 1.9, 0.38), (-math.pi / 2 + 1.9, 0.38)]
    tips = []
    for a, h in spikes:
        base = c + Vector((0.4 * math.cos(a), 0.34 * math.sin(a), 0.18))
        p.cone(base, (math.cos(a) * 0.15, math.sin(a) * 0.15, 1), h, 0.15, 'Crown_Navy', 4, spin=0.78)
        tips.append((base, h, a))
    p.finish()
    p = Part('Crown_Droplets', 'Crown', 0)
    for base, h, a in tips[:3]:
        top = base + Vector((math.cos(a) * 0.15, math.sin(a) * 0.15, 1)).normalized() * (h * 0.8)
        r = 0.13 if h > 0.6 else 0.1
        p.blob(top + Vector((0, 0, r)), (r, r, r), 'Crown_Droplet', (0, 0, 0), 2, 0.0, 31)
        p.cone(top + Vector((0, 0, r * 1.3)), (0, 0, 1), r * 1.9, r * 0.75, 'Crown_Droplet', 8)
    p.finish(smooth=True)


# ------------------------------------------------------------------ legs
def build_legs():
    LEGS = [('FrontLeft', 1, -1.2), ('FrontRight', -1, -1.2), ('BackLeft', 1, 1.95), ('BackRight', -1, 1.95)]
    for name, s, y in LEGS:
        front = y < 0
        x = s * (0.95 if front else 1.0)
        p = Part(f'Leg_{name}', 'Legs')
        if front:
            p.blob((x, y, 2.1), (0.6, 0.65, 0.95), 'Fur_Navy', (0.1, 0, s * -0.08), 2, 0.05, 40)
            p.blob((x * 1.02, y - 0.25, 1.0), (0.48, 0.52, 0.8), 'Fur_Navy', (0.08, 0, 0), 2, 0.05, 41)
        else:
            p.blob((x, y, 2.0), (0.72, 1.0, 1.05), 'Fur_Navy', (-0.2, 0, 0), 2, 0.05, 42)
            p.blob((x * 1.02, y + 0.3, 0.95), (0.48, 0.55, 0.75), 'Fur_Navy', (-0.15, 0, 0), 2, 0.05, 43)
        p.finish()
        # light stone diamond plates on knees / thighs
        p = Part(f'Leg_{name}_Plates', 'Legs', 0.015)
        zc = 1.55 if front else 1.65
        p.blob((x + s * 0.42, y - (0.15 if front else -0.3), zc), (0.12, 0.28, 0.32), 'Stone_LightBlue', (0, 0, 0), 1, 0.08, 44)
        p.blob((x + s * 0.4, y + (0.2 if front else 0.55), 0.85), (0.1, 0.22, 0.26), 'Fur_Gray', (0, 0, 0), 1, 0.08, 45)
        p.finish()
        # oversized paw + 4 chunky light toes
        p = Part(f'Paw_{name}', 'Legs')
        py = y - (0.45 if front else 0.0)
        p.blob((x, py, 0.32), (0.72, 0.78, 0.34), 'Fur_Navy', (0, 0, 0), 2, 0.05, 46, flat_bottom=0.0)
        p.finish()
        p = Part(f'Paw_{name}_Toes', 'Legs', 0.02)
        for k, tx in enumerate((-0.48, -0.16, 0.16, 0.48)):
            p.blob((x + tx, py - 0.7 + abs(tx) * 0.25, 0.24), (0.19, 0.26, 0.26), 'Stone_LightBlue',
                   (0.3, 0, 0), 1, 0.06, 47 + k, flat_bottom=0.0)
        p.finish()


# ------------------------------------------------------------------ armour
def build_armor():
    for s, side in ((-1, 'Right'), (1, 'Left')):
        # big curved shoulder pauldron with a swirl
        p = Part(f'Armor_Shoulder_{side}', 'Water Armor')
        p.blob((s * 1.18, -1.0, 2.95), (0.38, 0.95, 0.75), 'Armor_Aqua', (0.35, s * 0.25, 0), 2, 0.05, 60)
        p.finish()
        p = Part(f'Armor_Shoulder_{side}_Swirl', 'Water Armor', 0.01)
        pts = curl_path((s * 1.5, -1.45, 2.65), (0, 1, 0.25), (0, -0.25, 1), 0.35, 0.28, 1.0, 12, 0.1)
        p.sweep(pts, taper(len(pts), 0.22, 0.08), 0.14, (s, 0, 0), 'Armor_AquaLight')
        p.finish()
        # forearm bracer
        p = Part(f'Armor_Bracer_{side}', 'Water Armor')
        p.blob((s * 0.98, -1.55, 1.35), (0.55, 0.5, 0.32), 'Armor_Aqua', (0.15, 0, 0), 1, 0.07, 61)
        p.finish()
        # thigh plate on the back leg
        p = Part(f'Armor_Thigh_{side}', 'Water Armor')
        p.blob((s * 1.55, 1.75, 2.35), (0.2, 0.75, 0.55), 'Armor_Aqua', (0.2, 0, 0), 1, 0.07, 62)
        p.finish()
    # V-shaped chest collar plate
    p = Part('Armor_ChestCollar', 'Water Armor')
    for s in (-1, 1):
        a = Vector((s * 1.1, -1.8, 3.35))
        b = Vector((0, -2.3, 2.7))
        p.sweep([a, a.lerp(b, 0.5) + Vector((0, -0.12, 0)), b], [0.75, 0.62, 0.5], 0.28,
                Vector((s * 0.3, -1, 0.2)), 'Armor_Aqua')
    p.blob((0, -2.38, 2.55), (0.3, 0.16, 0.3), 'Armor_AquaLight', (0.3, 0, 0.78), 1, 0.0, 63)
    p.finish()


# ------------------------------------------------------------------ mane & tail
def build_mane_and_tail():
    # chunky wave crests flowing back from the head over the neck and shoulders
    W = [  # (name, origin, u, v, length, curl, width, thick, mat, turns)
        ('Mane_Top', (0, -1.6, 4.75), (0, 1, -0.15), (0, 0.15, 1), 0.9, 0.35, 0.75, 0.3, 'Armor_Aqua', 1.0),
        ('Mane_TopBack', (0, -0.9, 4.15), (0, 1, -0.35), (0, 0.3, 1), 0.9, 0.32, 0.8, 0.3, 'Armor_AquaLight', 1.0),
    ]
    for s, side in ((-1, 'Right'), (1, 'Left')):
        W += [
            (f'Mane_Cheek_{side}', (s * 0.7, -2.15, 3.95), (s * 0.55, 0.8, -0.2), (s * 0.3, 0, 1), 0.55, 0.3, 0.5, 0.26, 'Armor_AquaLight', 1.1),
            (f'Mane_Upper_{side}', (s * 0.75, -1.75, 4.35), (s * 0.7, 0.7, -0.15), (0, 0.1, 1), 0.85, 0.42, 0.7, 0.32, 'Armor_Aqua', 1.05),
            (f'Mane_Lower_{side}', (s * 0.95, -1.55, 3.45), (s * 0.6, 0.8, -0.3), (s * 0.2, 0, 1), 0.9, 0.4, 0.75, 0.32, 'Armor_Aqua', 1.05),
            (f'Mane_Shoulder_{side}', (s * 1.1, -0.65, 3.25), (s * 0.35, 1, -0.2), (s * 0.2, 0, 1), 1.0, 0.42, 0.8, 0.32, 'Armor_AquaLight', 1.0),
        ]
    for name, o, u, v, L, curl, w, t, mat, turns in W:
        p = Part(name, 'Mane and Tail', 0.015)
        pts = curl_path(o, u, v, L, curl, turns * 0.8, 16, 0.25)
        u_, v_ = Vector(u).normalized(), Vector(v).normalized()
        p.sweep(pts, taper(len(pts), w * 1.25, w * 0.3, 0.12), t * 1.7, u_.cross(v_), mat)
        p.finish()
    # curled water tail: big outer wave + lighter inner layer
    p = Part('Tail_Curl', 'Mane and Tail', 0.015)
    pts = curl_path((0, 2.75, 2.8), (0, 0.55, 1), (0, 1, -0.35), 1.2, 0.85, 1.15, 22, 0.35)
    p.sweep(pts, taper(len(pts), 1.15, 0.35, 0.3), 0.8, (1, 0, 0), 'Armor_Aqua')
    p.finish()
    p = Part('Tail_InnerWave', 'Mane and Tail', 0.015)
    pts = curl_path((0, 3.0, 3.3), (0, 0.5, 1), (0, 1, -0.4), 0.8, 0.5, 1.0, 16, 0.2)
    p.sweep([q + Vector((0.32, 0, 0)) for q in pts], taper(len(pts), 0.55, 0.15, 0.1), 0.3, (1, 0, 0), 'Armor_AquaLight')
    p.sweep([q + Vector((-0.32, 0, 0)) for q in pts], taper(len(pts), 0.55, 0.15, 0.1), 0.3, (1, 0, 0), 'Armor_AquaLight')
    p.finish()


# ------------------------------------------------------------------ effects
def droplet(p, c, r):
    c = Vector(c)
    p.blob(c, (r, r, r), 'Water_Clear', (0, 0, 0), 2, 0.0, 0)
    p.cone(c + Vector((0, 0, r * 0.4)), (0, 0, 1), r * 1.7, r * 0.8, 'Water_Clear', 8)


def build_effects():
    p = Part('Water_Droplets', 'Effects', 0)
    for c, r in (((-1.9, -2.2, 3.9), 0.12), ((2.1, -2.0, 4.4), 0.1), ((-1.7, 1.4, 4.6), 0.13),
                 ((1.9, 3.3, 4.3), 0.11), ((-2.0, 3.0, 2.2), 0.1), ((2.2, -0.6, 1.4), 0.09),
                 ((-2.3, -0.9, 1.0), 0.1), ((0.9, -3.4, 3.2), 0.08), ((-0.4, 4.0, 1.4), 0.09)):
        droplet(p, c, r)
    p.finish(smooth=True)
    # low curling splash crowns around each paw (open at the front so the toes stay visible)
    for name, x, y in (('FrontLeft', 0.95, -1.65), ('FrontRight', -0.95, -1.65), ('BackLeft', 1.0, 1.95), ('BackRight', -1.0, 1.95)):
        p = Part(f'Splash_{name}', 'Effects', 0)
        for k in range(5):
            a = math.radians(10 + k * 72)
            if -0.35 < math.cos(a - math.pi / 2 * 3) and math.sin(a) < -0.75:
                continue
            o = Vector((x + 0.82 * math.cos(a), y + 0.82 * math.sin(a), 0.02))
            out = Vector((math.cos(a), math.sin(a), 0))
            tang = Vector((-math.sin(a), math.cos(a), 0))
            pts = curl_path(o, out + Vector((0, 0, 0.35)), Vector((0, 0, 1)) - out * 0.3, 0.3, 0.1, 0.7, 9, 0.05)
            p.sweep(pts, taper(len(pts), 0.6, 0.15), 0.06, tang, 'Water_Clear')
        p.finish(smooth=True)


# ------------------------------------------------------------------ scene
def build_camera_and_lights():
    sc = bpy.context.scene
    lc = coll('CameraAndLights')
    cam = bpy.data.cameras.new('Camera_ThreeQuarter')
    cam.lens = 55
    co = bpy.data.objects.new('Camera_ThreeQuarter', cam)
    co.location = (9.5, -11.0, 4.6)
    co.rotation_euler = (Vector((0.0, 0.3, 2.55)) - co.location).to_track_quat('-Z', 'Y').to_euler()
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
    path = os.path.join(HERE, 'KingRainhound.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Ground_ShadowCatcher']
    print(f'King Rainhound: {len(meshes)} mesh objects, {sum(len(o.data.polygons) for o in meshes)} faces')
    print('Saved:', path)


if __name__ == '__main__':
    main()
