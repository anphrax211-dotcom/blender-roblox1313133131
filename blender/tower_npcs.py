"""TOWER OF PETS - redesigned NPC lineup (12 NPCs) as editable Roblox-style 3D models.

Reference: "Tower of Pets - NPC Lineup (Redesigned)" sheet (front / side / back per NPC).

Scale (Roblox R15 proportions; 1 stud = 0.28 m, the same scale as the pets in this repo):
    body             : ~1.49 m (5.3 studs) from the soles to the top of the head
    head             : 0.35 m rounded block, neck at z = 1.12 m
    torso            : 0.56 m wide x 0.28 m deep (2 x 1 studs), z 0.56 - 1.12 m
    arms / legs      : 0.27 / 0.275 m square blocks, 2 studs long; hands at z ~0.6 m
    hats / hair add up to ~0.5 m on top (Upgrades wizard hat is the tallest at 1.98 m)
Every NPC stands on the ground (z = 0) facing -Y. They are laid out in two rows of six,
in the reference order (row 1: 01-06 at y = 0, row 2: 07-12 at y = 3 m, staggered so the
back row shows between the front row).

Structure (rig-ready):
    NPCs collection -> one collection per NPC (Shop_NPC, Egg_NPC, ...) -> sub-collections
    Body / Face / Hair / Clothing / Hat / Accessories / Back / Hands / Shoes / Props.
    Body parts use Roblox R15 names (Head, UpperTorso, LowerTorso, Left/RightUpperArm,
    LowerArm, Hand, UpperLeg, LowerLeg, Foot) with their origin at the joint pivot.
    Every other part is named <NPC>_<Bone>_<Item> and carries a custom property "bone"
    naming the R15 part it should be welded/weighted to.
    Arms that hold a prop are bent forward at the elbow; all other limbs are in rest pose.

Run in Blender (Scripting tab -> Run Script) or headless:
    blender -b -P tower_npcs.py
    python3 tower_npcs.py          (with the `bpy` pip module)
Saves TowerOfPets_NPCs.blend next to this script and prints the full path, then exports
one FBX per NPC (centred on its feet, prefix-free part names) to ../exports/NPCs.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

S = 0.28                                   # one Roblox stud in metres
Z_SH, Z_WAIST, Z_HIP = 1.12, 0.728, 0.56   # shoulder top / waist / hips
Z_ELB, Z_WR = 0.86, 0.66                   # elbow / wrist pivots
Z_KNEE, Z_ANK = 0.294, 0.084               # knee / ankle pivots
ARM_X, LEG_X = 0.42, 0.14                  # arm / leg centre lines
HEAD_C, HH = Vector((0.0, 0.0, 1.305)), 0.175   # head centre / half size
FRONT = -HH                                # y of the face

MATS = {}
NPCS_COLL = None
SIDE = {-1: 'Right', 1: 'Left'}          # x sign -> character side


# ------------------------------------------------------------------ materials
def mat(name, srgb, rough=0.45, coat=0.25, emit=0.0, metal=0.0):
    """stylised toy material, created once. `srgb` = Roblox Color3.fromRGB values"""
    if name in MATS:
        return name
    lin = tuple(((c / 255) / 12.92) if c / 255 <= 0.04045 else (((c / 255) + 0.055) / 1.055) ** 2.4
                for c in srgb)
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*lin, 1)
        b.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = (*lin, 1)
    MATS[name] = m
    return name


def shared_materials():
    mat('Skin', (246, 204, 166), 0.5, 0.15)
    mat('Face_Black', (28, 24, 28), 0.3, 0.3)
    mat('Gold', (232, 178, 62), 0.3, 0.4, metal=0.35)
    mat('White', (242, 240, 234))
    mat('Glove_Black', (36, 33, 38), 0.5, 0.2)
    mat('Wood_Dark', (66, 44, 34), 0.6, 0.1)
    mat('Leather_Brown', (104, 64, 38), 0.55, 0.15)


# ------------------------------------------------------------------ mesh helpers
def bezier(pts, n):
    """Catmull-Rom spline through pts, sampled into n points"""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(n):
        u = i / (n - 1) * (len(pts) - 1)
        k = min(int(u), len(pts) - 2)
        t = u - k
        p0, p1, p2, p3 = P[k], P[k + 1], P[k + 2], P[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out


def merge(dst, src):
    me = bpy.data.meshes.new('tmp')
    src.to_mesh(me)
    src.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)
    return dst


def frame(normal, up=Vector((0, 0, 1))):
    """columns (side, up-ish, normal): local Z -> normal"""
    z = Vector(normal).normalized()
    x = Vector(up).cross(z)
    if x.length < 1e-5:
        x = Vector((1, 0, 0))
    x.normalize()
    return Matrix((x, z.cross(x), z)).transposed()


def box_bm(center, size, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    R = rot if rot is not None else Matrix.Identity(3)
    for v in bm.verts:
        v.co = R @ Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(center)
    return bm


def rbox_bm(center, half, p=4.0, cuts=3):
    """rounded block (superellipsoid) with an even grid of faces - heads, hair caps"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        d = v.co.normalized()
        k = (abs(d.x) ** p + abs(d.y) ** p + abs(d.z) ** p) ** (-1 / p)
        v.co = Vector((d.x * k * half[0], d.y * k * half[1], d.z * k * half[2])) + Vector(center)
    return bm


def ellipsoid_bm(center, radii, sub=2, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    R = rot if rot is not None else Matrix.Identity(3)
    for v in bm.verts:
        v.co = R @ Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2])) + Vector(center)
    return bm


def rp(a, hw, hd, p=4.0):
    """point on a rounded-rectangle ring; a = degrees from the front (-Y) towards +X"""
    s, c = math.sin(math.radians(a)), -math.cos(math.radians(a))
    return Vector((hw * math.copysign(abs(s) ** (2 / p), s), hd * math.copysign(abs(c) ** (2 / p), c), 0))


def rings_bm(rings, cx=0.0, cy=0.0, sector=None, n=24, p=4.0):
    """open shell lofted through horizontal rounded-rectangle rings (z, half_w, half_d[, dy]).
    `sector` = (a0, a1) keeps only that arc, e.g. (30, 330) leaves the front open."""
    bm = bmesh.new()
    if sector:
        angs = [sector[0] + (sector[1] - sector[0]) * i / n for i in range(n + 1)]
    else:
        angs = [360 * i / n for i in range(n)]
    rows = []
    for r in rings:
        z, hw, hd = r[:3]
        dy = r[3] if len(r) > 3 else 0.0
        rows.append([bm.verts.new(rp(a, hw, hd, p) + Vector((cx, cy + dy, z))) for a in angs])
    m = len(angs)
    for A, B in zip(rows, rows[1:]):
        for i in range(m if not sector else m - 1):
            j = (i + 1) % m
            bm.faces.new((A[i], A[j], B[j], B[i]))
    return bm


def lathe_bm(profile, segs, center, axis=(0, 0, 1), up=Vector((0, 1, 0)), bend=None):
    """revolve (radius, height) profile around `axis`; bend(h) -> offset bends cone tips"""
    bm = bmesh.new()
    M = frame(axis, up)
    rows = []
    for r, h in profile:
        off = bend(h) if bend else Vector()
        if r < 1e-6:
            rows.append([bm.verts.new(M @ (Vector((0, 0, h)) + off) + Vector(center))])
        else:
            rows.append([bm.verts.new(M @ (Vector((r * math.cos(a), r * math.sin(a), h)) + off) + Vector(center))
                         for a in (2 * math.pi * (i + 0.5) / segs for i in range(segs))])
    for A, B in zip(rows, rows[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(A) == 1:
                bm.faces.new((A[0], B[j], B[i]))
            elif len(B) == 1:
                bm.faces.new((A[i], A[j], B[0]))
            else:
                bm.faces.new((A[i], A[j], B[j], B[i]))
    return bm


def tube_bm(path, radii, segs=6):
    """round tube along a polyline, closed ends"""
    bm = bmesh.new()
    rows, nrm = [], None
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        nrm = t.orthogonal().normalized() if nrm is None else (nrm - t * nrm.dot(t)).normalized()
        b = t.cross(nrm)
        rows.append([bm.verts.new(p + (nrm * math.cos(a) + b * math.sin(a)) * max(radii[i], 1e-4))
                     for a in (2 * math.pi * k / segs for k in range(segs))])
    for A, B in zip(rows, rows[1:]):
        for k in range(segs):
            bm.faces.new((A[k], A[(k + 1) % segs], B[(k + 1) % segs], B[k]))
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])
    return bm


def strand_bm(path, widths, thick, hint):
    """flat faceted hair lock / ribbon: hexagonal cross-section `widths` wide, lying across
    `hint` (usually the head-outward direction); ends in a point when the last width is 0"""
    bm = bmesh.new()
    rows = []
    w0 = max(widths[0], 1e-4)
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = t.cross(Vector(hint))
        if side.length < 1e-4:
            side = t.orthogonal()
        side.normalize()
        nn = side.cross(t)
        w = widths[i]
        if w < 1e-5:
            rows.append([bm.verts.new(p)])
            continue
        th = max(thick * w / w0, 0.004)
        rows.append([bm.verts.new(p + side * sx * w + nn * nz * th)
                     for sx, nz in ((1, 0), (0.45, 1), (-0.45, 1), (-1, 0), (-0.45, -1), (0.45, -1))])
    for A, B in zip(rows, rows[1:]):
        if len(B) == 1:
            for k in range(6):
                bm.faces.new((A[k], A[(k + 1) % 6], B[0]))
        else:
            for k in range(6):
                bm.faces.new((A[k], A[(k + 1) % 6], B[(k + 1) % 6], B[k]))
    bm.faces.new(rows[0][::-1])
    if len(rows[-1]) > 1:
        bm.faces.new(rows[-1])
    return bm


def leaf_bm(L, W, thick=0.02, fold=0.15, n=6):
    """V-folded leaf (also feathers): base at origin, tip along +Y, front along +Z"""
    bm = bmesh.new()
    base = bm.verts.new((0, 0, 0))
    tip = bm.verts.new((0, L, 0))
    rows = []
    for i in range(1, n):
        t = i / n
        w = W * 0.5 * math.sin(math.pi * t) ** 0.7 * (1 - 0.2 * t)
        rows.append([bm.verts.new((x, t * L, fold * abs(x) + dz)) for x, dz in
                     ((-w, 0), (0, thick / 2), (w, 0), (0, -thick / 2))])
    for end, r in ((base, rows[0]), (tip, rows[-1])):
        for k in range(4):
            bm.faces.new((end, r[k], r[(k + 1) % 4]))
    for A, B in zip(rows, rows[1:]):
        for k in range(4):
            bm.faces.new((A[k], A[(k + 1) % 4], B[(k + 1) % 4], B[k]))
    return bm


def place(bm, M, origin):
    for v in bm.verts:
        v.co = M @ v.co + Vector(origin)
    return bm


def axes(up, facing):
    """local Y -> up, local Z -> facing (made perpendicular), X = Y x Z"""
    y = Vector(up).normalized()
    z = Vector(facing)
    z = (z - y * z.dot(y)).normalized()
    return Matrix((y.cross(z), y, z)).transposed()


def paw_bm(center, normal, size, up=Vector((0, 0, 1)), depth=0.02):
    """paw-print symbol: big pad + four toes, as flattened blobs facing `normal`"""
    M = frame(normal, up)
    bm = bmesh.new()
    for (u, w, rx, ry) in ((0, -0.18, 0.36, 0.3), (-0.42, 0.22, 0.13, 0.17), (-0.15, 0.45, 0.13, 0.17),
                           (0.15, 0.45, 0.13, 0.17), (0.42, 0.22, 0.13, 0.17)):
        merge(bm, ellipsoid_bm(Vector((u * size, w * size, 0)), (rx * size, ry * size, depth), 1))
    return place(bm, M, center)


# ------------------------------------------------------------------ NPC builder
class NPC:
    def __init__(self, key, offset):
        self.key = key
        self.off = Vector(offset)
        self.coll = bpy.data.collections.new(f'{key}_NPC')
        NPCS_COLL.children.link(self.coll)
        self.subs = {}
        self.parts = []                     # (object, bone)
        self.bent = {}                      # side -> forearm bend angle (deg)
        self.hair = None
        self.hair_mat = None

    # ---- object creation
    def add(self, name, bm, m, bone, cat, bevel=0.0, solid=0.0, center=None, smooth=False, seg=1):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if center is None:
            center = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
        for v in bm.verts:
            v.co -= center
        full = f'{self.key}_{name}'
        me = bpy.data.meshes.new(full)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(MATS[m])
        if smooth:
            me.shade_smooth()
        else:
            me.shade_flat()
        ob = bpy.data.objects.new(full, me)
        ob.location = center
        ob['bone'] = bone
        if cat not in self.subs:
            c = bpy.data.collections.new(f'{self.key}_{cat}')
            self.coll.children.link(c)
            self.subs[cat] = c
        self.subs[cat].objects.link(ob)
        if solid:
            so = ob.modifiers.new('Solidify', 'SOLIDIFY')
            so.thickness, so.offset = solid, 0.0
        if bevel:
            bv = ob.modifiers.new('Bevel', 'BEVEL')
            bv.width, bv.segments = bevel, seg
            bv.limit_method = 'ANGLE'
            bv.angle_limit = math.radians(40)
        self.parts.append((ob, bone))
        return ob

    def box(self, name, c, size, m, bone, cat, bevel=0.012, rot=None):
        return self.add(name, box_bm(c, size, rot), m, bone, cat, bevel=bevel, center=Vector(c), seg=2)

    def ring(self, name, rings, m, bone, cat, sector=None, cx=0.0, cy=0.0, thick=0.02, n=24, p=4.0):
        return self.add(name, rings_bm(rings, cx, cy, sector, n, p), m, bone, cat, solid=thick)

    def band(self, name, z0, z1, hw, hd, m, bone, cat, sector=None, cx=0.0, cy=0.0, thick=0.02, n=24):
        """trim band (a short straight ring)"""
        return self.ring(name, [(z0, hw, hd), (z1, hw, hd)], m, bone, cat, sector, cx, cy, thick, n)

    def edge_trims(self, name, rings, sector, m, bone, cat, cx=0.0, cy=0.0, r=0.013, p=4.0):
        """trim piping running down both edges of an open-front ring shell"""
        bm = bmesh.new()
        for a in sector:
            pts = [rp(a, rr[1], rr[2], p) + Vector((cx, cy + (rr[3] if len(rr) > 3 else 0), rr[0]))
                   for rr in rings]
            merge(bm, tube_bm(pts, [r] * len(pts), 5))
        return self.add(name, bm, m, bone, cat)

    def lathe(self, name, profile, m, bone, cat, center, axis=(0, 0, 1), segs=12, bend=None, bevel=0.0):
        return self.add(name, lathe_bm(profile, segs, center, axis, bend=bend), m, bone, cat, bevel=bevel,
                        center=Vector(center))

    def ell(self, name, c, radii, m, bone, cat, sub=2, rot=None, smooth=False):
        return self.add(name, ellipsoid_bm(c, radii, sub, rot), m, bone, cat, center=Vector(c), smooth=smooth)

    # ---- body
    def body(self, top, bottom=None, arm_u=None, arm_l=None, hand='Skin', leg_u=None, leg_l=None,
             foot='Glove_Black', head='Skin'):
        """Roblox R15 blocky body; colours are the base clothing on each part"""
        bottom = bottom or top
        arm_u = arm_u or top
        arm_l = arm_l or arm_u
        leg_u = leg_u or bottom
        leg_l = leg_l or leg_u
        self.add('Head', rbox_bm(HEAD_C, (HH, HH * 0.97, HH), 5.0, 3), head, 'Head', 'Body',
                 center=Vector((0, 0, Z_SH)))
        self.box('UpperTorso', (0, 0, (Z_WAIST + Z_SH) / 2), (0.56, 0.28, Z_SH - Z_WAIST), top,
                 'UpperTorso', 'Body', bevel=0.02)
        self._recentre(self.parts[-1][0], Vector((0, 0, Z_WAIST)))
        self.box('LowerTorso', (0, 0, (Z_HIP + Z_WAIST) / 2), (0.56, 0.28, Z_WAIST - Z_HIP), bottom,
                 'LowerTorso', 'Body', bevel=0.02)
        self._recentre(self.parts[-1][0], Vector((0, 0, Z_HIP)))
        for side, sx in (('Right', -1), ('Left', 1)):
            x = sx * ARM_X
            for nm, z0, z1, m, cat in (('UpperArm', Z_ELB, Z_SH, arm_u, 'Body'),
                                       ('LowerArm', Z_WR, Z_ELB, arm_l, 'Body'),
                                       ('Hand', Z_WR - 0.105, Z_WR, hand, 'Hands')):
                ob = self.box(side + nm, (x, 0, (z0 + z1) / 2), (0.27, 0.27, z1 - z0 + 0.004), m,
                              side + nm, cat, bevel=0.02)
                self._recentre(ob, Vector((x, 0, z1)))
            x = sx * LEG_X
            for nm, z0, z1, m, cat, dy, d in (('UpperLeg', Z_KNEE, Z_HIP, leg_u, 'Body', 0, 0.275),
                                              ('LowerLeg', Z_ANK, Z_KNEE, leg_l, 'Body', 0, 0.275),
                                              ('Foot', 0.0, Z_ANK, foot, 'Shoes', -0.02, 0.31)):
                ob = self.box(side + nm, (x, dy, (z0 + z1) / 2), (0.275, d, z1 - z0 + 0.004), m,
                              side + nm, cat, bevel=0.02)
                self._recentre(ob, Vector((x, 0, z1)))

    @staticmethod
    def _recentre(ob, pivot):
        """move an object's origin to `pivot` without moving its geometry"""
        d = ob.location - pivot
        ob.data.transform(Matrix.Translation(d))
        ob.location = pivot

    def face(self, eyes='Face_Black', smile=True, eye_size=(0.034, 0.068)):
        for sx in (-1, 1):
            self.add(f'Head_Eye_{"Right" if sx < 0 else "Left"}',
                     rbox_bm((sx * 0.062, FRONT - 0.002, HEAD_C.z + 0.012), (eye_size[0] / 2, 0.008, eye_size[1] / 2),
                             3.0, 2), eyes, 'Head', 'Face')
        if smile:
            pts = [Vector((x, FRONT - 0.003, HEAD_C.z - 0.07 - 0.016 * (1 - (x / 0.04) ** 2)))
                   for x in (-0.04, -0.02, 0.0, 0.02, 0.04)]
            self.add('Head_Smile', tube_bm(bezier(pts, 7), [0.006] * 7, 5), 'Face_Black', 'Head', 'Face')

    # ---- clothing helpers
    def sleeve(self, side, name, z0, z1, hw0, hw1, m, hd0=None, hd1=None, cat='Clothing', lower=False):
        """box-ish sleeve shell around an arm, z1 (top) -> z0 (bottom), flaring hw0 -> hw1"""
        sx = -1 if side == 'Right' else 1
        bone = side + ('LowerArm' if lower else 'UpperArm')
        return self.ring(f'{bone}_{name}', [(z1, hw0, hd0 or hw0), (z0, hw1, hd1 or hw1)], m, bone, cat,
                         cx=sx * ARM_X, n=16, p=5.0)

    def cuff(self, side, name, z0, z1, hw, m, lower=True, hd=None):
        sx = -1 if side == 'Right' else 1
        bone = side + ('LowerArm' if lower else 'UpperArm')
        return self.band(f'{bone}_{name}', z0, z1, hw, hd or hw, m, bone, 'Clothing', cx=sx * ARM_X, n=16)

    def coat_front(self, inner, trim, width=0.17, z0=Z_WAIST, z1=Z_SH - 0.02, depth=0.004, name='Shirt'):
        """inner shirt/vest panel showing through an open coat front, with trim piping"""
        y = -0.172 - depth
        self.box(f'UpperTorso_{name}', (0, y, (z0 + z1) / 2), (width, 0.012, z1 - z0), inner, 'UpperTorso',
                 'Clothing', bevel=0.004)
        if trim:
            bm = bmesh.new()
            for sx in (-1, 1):
                merge(bm, tube_bm([Vector((sx * width / 2, y - 0.004, z0)), Vector((sx * width / 2, y - 0.004, z1))],
                                  [0.012, 0.012], 5))
            self.add('UpperTorso_FrontTrim', bm, trim, 'UpperTorso', 'Clothing')

    def collar(self, m, h=0.07, hw=0.15, hd=0.11, open_front=60):
        self.ring('UpperTorso_Collar', [(Z_SH - 0.01, hw, hd), (Z_SH + h, hw * 0.92, hd * 0.92)], m,
                  'UpperTorso', 'Clothing', sector=(open_front / 2, 360 - open_front / 2), n=16, thick=0.018)

    def belt(self, m, buckle='Gold', z=Z_WAIST - 0.02, h=0.05, gem=None):
        self.band('LowerTorso_Belt', z - h / 2, z + h / 2, 0.295, 0.155, m, 'LowerTorso', 'Accessories', thick=0.016)
        self.box('LowerTorso_Buckle', (0, -0.168, z), (0.075, 0.016, h * 1.25), buckle, 'LowerTorso', 'Accessories',
                 bevel=0.006)
        if gem:
            self.ell('LowerTorso_BeltGem', (0, -0.18, z), (0.022, 0.012, 0.026), gem, 'LowerTorso', 'Accessories', 1)

    def skirt(self, name, rings, m, trim=None, open_front=0, bone='LowerTorso', cat='Clothing', thick=0.02,
              hem=0.03, cy=0.0, p=4.0):
        """robe / coat skirt from the waist down; optional open front + trim on hem and edges"""
        sector = (open_front / 2, 360 - open_front / 2) if open_front else None
        self.ring(f'{bone}_{name}', rings, m, bone, cat, sector=sector, cy=cy, thick=thick, p=p)
        if trim:
            z, hw, hd = rings[-1][:3]
            dy = rings[-1][3] if len(rings[-1]) > 3 else 0
            self.ring(f'{bone}_{name}Hem', [(z, hw + 0.006, hd + 0.006, dy), (z + hem, hw + 0.004, hd + 0.004, dy)],
                      trim, bone, cat, sector=sector, cy=cy, thick=thick + 0.006, p=p)
            if sector:
                self.edge_trims(f'{bone}_{name}EdgeTrim', [(r[0], r[1] + 0.004, r[2] + 0.004) + tuple(r[3:])
                                                          for r in rings], sector, trim, bone, cat, cy=cy, p=p)

    def cape(self, name, rings, m, trim=None, sector=(105, 255), bone='UpperTorso', hem=0.035):
        """back cape: arc of a ring shell behind the body"""
        self.ring(f'{bone}_{name}', rings, m, bone, 'Back', sector=sector, thick=0.022)
        if trim:
            z, hw, hd = rings[-1][:3]
            dy = rings[-1][3] if len(rings[-1]) > 3 else 0
            self.ring(f'{bone}_{name}Hem', [(z, hw + 0.006, hd + 0.006, dy), (z + hem, hw + 0.005, hd + 0.005, dy)],
                      trim, bone, 'Back', sector=sector, thick=0.028)
            self.edge_trims(f'{bone}_{name}EdgeTrim', [(r[0], r[1] + 0.003, r[2] + 0.003) + tuple(r[3:])
                                                      for r in rings], sector, trim, bone, 'Back')

    def mantle(self, name, m, trim=None, drop=0.2, reach=0.6, open_front=0, depth=0.24):
        """capelet over the shoulders, flaring out over the upper arms"""
        rings = [(Z_SH + 0.07, 0.15, 0.12), (Z_SH + 0.055, 0.33, 0.165), (Z_SH + 0.03, 0.5, 0.2),
                 (Z_SH - 0.02, reach - 0.01, depth - 0.005), (Z_SH - drop, reach + 0.02, depth + 0.01)]
        sector = (open_front / 2, 360 - open_front / 2) if open_front else None
        self.ring(f'UpperTorso_{name}', rings, m, 'UpperTorso', 'Clothing', sector=sector, thick=0.022, n=28, p=3.0)
        if trim:
            z = Z_SH - drop
            self.ring(f'UpperTorso_{name}Hem', [(z, reach + 0.026, depth + 0.016), (z + 0.03, reach + 0.024, depth + 0.015)],
                      trim, 'UpperTorso', 'Clothing', sector=sector, thick=0.028, n=28, p=3.0)
            if sector:
                self.edge_trims(f'UpperTorso_{name}EdgeTrim', [(r[0], r[1] + 0.004, r[2] + 0.004) for r in rings],
                                sector, trim, 'UpperTorso', 'Clothing', p=3.0)

    # ---- hair
    def hair_cap(self, m, back_low=-0.12, side_low=-0.04, hairline=0.085, half=(0.196, 0.19, 0.198),
                 dy=0.008, dz=0.012):
        """rounded shell over the skull, open at the face; low edges set where it stops"""
        c = HEAD_C + Vector((0, dy, dz))
        bm = rbox_bm(c, half, 3.5, 4)
        kill = []
        for f in bm.faces:
            r = f.calc_center_median() - HEAD_C
            if r.y < -0.09 and r.z < hairline:
                kill.append(f)
            elif r.z < (side_low if r.y < 0.06 else back_low):
                kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        self.add('Head_HairBase', bm, m, 'Head', 'Hair', solid=0.02)
        self.hair_mat = m

    def lock(self, p0, tip, w=0.05, bulge=Vector(), thick=0.024, n=6, hint=None, mid=None, end=0.0):
        """add one flat tapering hair lock from p0 (on the cap) to tip (all in metres);
        `end` > 0 keeps the tip blunt (that fraction of the root width)"""
        p0, tip = Vector(p0), Vector(tip)
        m = mid if mid is not None else (p0 + tip) / 2 + Vector(bulge)
        path = bezier([p0, Vector(m), tip], n)
        widths = [w * (1 - (1 - end) * (i / (n - 1)) ** 1.6) for i in range(n)]
        if not end:
            widths[-1] = 0.0
        h = Vector(hint) if hint is not None else (p0 - HEAD_C)
        bm = strand_bm(path, widths, thick, h.normalized())
        if self.hair is None:
            self.hair = bm
        else:
            merge(self.hair, bm)

    def hair_done(self, name='Head_Hair'):
        if self.hair is not None:
            self.add(name, self.hair, self.hair_mat, 'Head', 'Hair')
            self.hair = None

    # standard hair pieces ------------------------------------------------
    def bangs(self, n=5, span=0.15, tip_z=0.04, w=0.05, sweep=0.0, jag=0.03, y=None, seed=0):
        rnd = random.Random(seed)
        for i in range(n):
            u = -1 + 2 * i / (n - 1) if n > 1 else 0
            x = u * span
            p0 = HEAD_C + Vector((x * 0.7, -0.08, 0.2))
            tip = HEAD_C + Vector((x + sweep * 0.06 + rnd.uniform(-0.01, 0.01),
                                   (y if y is not None else FRONT - 0.03) + abs(u) * 0.02,
                                   tip_z + rnd.uniform(-jag, jag) + abs(u) * 0.01))
            self.lock(p0, tip, w, bulge=Vector((0, -0.05, 0.03)))

    def spikes(self, items, w=0.06, seed=0):
        """items: (theta, phi, length, up) radial spikes; theta 0 = front, +90 = left"""
        for th, ph, L, up in items:
            d = Vector((math.sin(math.radians(th)) * math.cos(math.radians(ph)),
                        -math.cos(math.radians(th)) * math.cos(math.radians(ph)), math.sin(math.radians(ph))))
            p0 = HEAD_C + Vector((d.x * 0.17, d.y * 0.17, d.z * 0.17 + 0.02))
            tip = p0 + d * L + Vector((0, 0, up))
            self.lock(p0, tip, w, bulge=d * 0.02 + Vector((0, 0, 0.015)))

    def messy(self, L=0.1, rows=((15, 45, -0.04), (40, 45, 0.0), (65, 70, 0.02)), w=0.065, back=0.03,
              front_gap=55, seed=0):
        """rows of chunky tufts sticking out around the head: (elevation, spacing deg, lift)"""
        rnd = random.Random(seed)
        for ph, step, up in rows:
            th = -180 + rnd.uniform(0, step)
            while th < 180:
                if not (abs(th) < front_gap and ph < 50):
                    d = Vector((math.sin(math.radians(th)) * math.cos(math.radians(ph)),
                                -math.cos(math.radians(th)) * math.cos(math.radians(ph)), math.sin(math.radians(ph))))
                    p0 = HEAD_C + d * 0.17 + Vector((0, 0, 0.02))
                    tip = p0 + d * L * rnd.uniform(0.8, 1.2) + Vector((0, back, up))
                    self.lock(p0, tip, w * rnd.uniform(0.85, 1.15), bulge=d * 0.025, thick=0.03)
                th += step

    def long_hair(self, length, n=9, spread=0.05, w=0.065, wave=0.0, arc=(110, 250), out=0.0, seed=0):
        """long locks hanging down the back from the crown"""
        rnd = random.Random(seed)
        self.lock(HEAD_C + Vector((0, 0.15, 0.1)), HEAD_C + Vector((0, 0.2 + spread, -length + 0.06)), 0.19,
                  thick=0.05, n=7, hint=(0, 1, 0), mid=HEAD_C + Vector((0, 0.235 + spread, -length * 0.35)), end=0.75)
        for i in range(n):
            a = math.radians(arc[0] + (arc[1] - arc[0]) * i / (n - 1))
            d = Vector((math.sin(a), -math.cos(a), 0))
            p0 = HEAD_C + d * 0.16 + Vector((0, 0, 0.13))
            tip = HEAD_C + d * (0.2 + spread + out) + Vector((rnd.uniform(-0.02, 0.02), 0.03, -length + rnd.uniform(-0.04, 0.04)))
            mid = HEAD_C + d * (0.24 + spread) + Vector((wave * (1 if i % 2 else -1), 0.02, -length * 0.4))
            self.lock(p0, tip, w, mid=mid, n=7)

    def side_locks(self, length, w=0.055, front=-0.08, out=0.215, count=1, z0=0.08):
        for sx in (-1, 1):
            for k in range(count):
                p0 = HEAD_C + Vector((sx * 0.17, front + 0.05 * k, z0))
                tip = HEAD_C + Vector((sx * (out + 0.02 * k), front + 0.04 * k - 0.02, -length + 0.03 * k))
                self.lock(p0, tip, w, bulge=Vector((sx * 0.03, 0, 0)))

    # ---- pose + props
    def bend(self, side, deg):
        """bend a forearm (and hand) forward at the elbow"""
        sx = -1 if side == 'Right' else 1
        piv = Vector((sx * ARM_X, 0, Z_ELB))
        R = Matrix.Rotation(math.radians(-deg), 3, 'X')
        for ob, bone in self.parts:
            if bone in (side + 'LowerArm', side + 'Hand'):
                ob.data.transform(R.to_4x4())
                ob.location = piv + R @ (ob.location - piv)
        self.bent[side] = deg

    def hand(self, side):
        """(centre, palm-up direction, forearm direction) of a hand in its current pose"""
        sx = -1 if side == 'Right' else 1
        piv = Vector((sx * ARM_X, 0, Z_ELB))
        R = Matrix.Rotation(math.radians(-self.bent.get(side, 0)), 3, 'X')
        c = piv + R @ Vector((0, 0, Z_WR - 0.055 - Z_ELB))
        return c, R @ Vector((0, -1, 0)), R @ Vector((0, 0, -1))

    def finish(self):
        """move the whole NPC to its lineup spot"""
        for ob, _ in self.parts:
            ob.location += self.off


# ------------------------------------------------------------------ shared NPC pieces
TORSO_SHELL = [(Z_WAIST - 0.005, 0.3, 0.156), (Z_SH + 0.004, 0.296, 0.152)]


def torso_shell(n, name, m):
    n.ring(f'UpperTorso_{name}', TORSO_SHELL, m, 'UpperTorso', 'Clothing', n=32, p=8.0)


def wizard_hat(n, m, band, brim_r=0.38, h=0.5, base_r=0.215, z=1.42, bend=(0.04, 0.16), tilt=0.0):
    """wide brim + bent cone + band"""
    n.lathe('Head_HatBrim', [(0, 0.014), (brim_r * 0.7, 0.008), (brim_r, -0.008), (brim_r + 0.01, -0.02),
                             (brim_r * 0.7, -0.012), (0, -0.006)], m, 'Head', 'Hat', (0, 0, z), segs=14)
    bx, by = bend
    n.lathe('Head_HatCone', [(base_r, 0.0), (base_r * 0.9, h * 0.2), (base_r * 0.66, h * 0.45),
                             (base_r * 0.4, h * 0.7), (base_r * 0.16, h * 0.9), (0, h)], m, 'Head', 'Hat',
            (0, 0, z), segs=10, bend=lambda hh: Vector((bx * (hh / h) ** 2, by * (hh / h) ** 2, 0)))
    if band:
        n.ring('Head_HatBand', [(z + 0.005, base_r + 0.006, base_r + 0.006), (z + 0.06, base_r * 0.93, base_r * 0.93)],
               band, 'Head', 'Hat', n=14, p=2.0, thick=0.014)


def circle_tube(center, radius, r, n=20, axis='Z'):
    pts = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        if axis == 'Z':
            pts.append(Vector(center) + Vector((math.cos(a) * radius, math.sin(a) * radius, 0)))
        else:     # circle facing -Y (in the XZ plane)
            pts.append(Vector(center) + Vector((math.cos(a) * radius, 0, math.sin(a) * radius)))
    return tube_bm(pts, [r] * len(pts), 5)


def diamond_bm(center, w, h, d, rot=None):
    """faceted gem / crystal: elongated octahedron"""
    bm = bmesh.new()
    V = [bm.verts.new(p) for p in ((0, 0, h), (0, 0, -h), (w, 0, 0), (-w, 0, 0), (0, d, 0), (0, -d, 0))]
    for a, b in ((2, 4), (4, 3), (3, 5), (5, 2)):
        bm.faces.new((V[0], V[a], V[b]))
        bm.faces.new((V[1], V[b], V[a]))
    R = rot if rot is not None else Matrix.Identity(3)
    for v in bm.verts:
        v.co = R @ v.co + Vector(center)
    return bm


def star_bm(center, size, normal=(0, -1, 0)):
    """flat 4-point sparkle"""
    M = frame(normal)
    bm = bmesh.new()
    pts = []
    for k in range(8):
        a = math.pi / 4 * k
        r = size if k % 2 == 0 else size * 0.3
        pts.append(Vector((math.sin(a) * r, math.cos(a) * r, 0)))
    top = [bm.verts.new(M @ (p + Vector((0, 0, 0.006))) + Vector(center)) for p in pts]
    bot = [bm.verts.new(M @ (p - Vector((0, 0, 0.006))) + Vector(center)) for p in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for i in range(8):
        j = (i + 1) % 8
        bm.faces.new((top[i], bot[i], bot[j], top[j]))
    return bm


def front_strip(n, name, x, z0, z1, y0, y1, w, m, bone='LowerTorso', cat='Clothing'):
    """thin vertical stripe that follows a flared skirt front from (z0, y0) down to (z1, y1)"""
    ang = math.atan2(y1 - y0, z0 - z1)
    c = Vector((x, (y0 + y1) / 2, (z0 + z1) / 2))
    n.box(name, c, (w, 0.01, math.hypot(z0 - z1, y1 - y0)), m, bone, cat, bevel=0.003,
          rot=Matrix.Rotation(ang, 3, 'X'))


def gem_emblem(n, name, c, size, outer, inner, bone='UpperTorso'):
    n.add(name, diamond_bm(c, size, size * 1.15, 0.02), outer, bone, 'Accessories', center=Vector(c))
    n.add(name + 'Gem', diamond_bm(Vector(c) + Vector((0, -0.012, 0)), size * 0.45, size * 0.55, 0.015), inner, bone,
          'Accessories', center=Vector(c))


def glove_cuffs(n, m, trim=None, z0=Z_WR - 0.004, z1=Z_WR + 0.085, hw=0.148):
    for side in ('Right', 'Left'):
        n.cuff(side, 'Glove', z0, z1, hw, m)
        if trim:
            n.cuff(side, 'GloveTrim', z1 - 0.004, z1 + 0.02, hw + 0.004, trim)


# ------------------------------------------------------------------ 01 SHOP
def build_shop(n):
    red = mat('Shop_Red', (206, 38, 36))
    blk = mat('Shop_Black', (40, 33, 35))
    hair = mat('Shop_Hair', (30, 28, 34))
    n.body(top=blk, bottom=blk, arm_u=red, arm_l=red, hand='Glove_Black', leg_u=blk, foot='Glove_Black')
    n.face()
    torso_shell(n, 'Coat', red)
    n.coat_front(blk, 'Gold', width=0.22, name='Vest')
    n.box('UpperTorso_ShirtCollar', (0, -0.18, Z_SH - 0.035), (0.07, 0.01, 0.07), 'White', 'UpperTorso', 'Clothing',
          bevel=0.003, rot=Matrix.Rotation(math.radians(45), 3, 'Y'))
    for k, z in enumerate((1.0, 0.92, 0.84)):     # gold lacing crosses on the vest
        for j, a in enumerate((35, -35)):
            n.box(f'UpperTorso_Lacing{2 * k + j + 1}', (0, -0.184, z), (0.1, 0.008, 0.012), 'Gold', 'UpperTorso',
                  'Accessories', bevel=0.002, rot=Matrix.Rotation(math.radians(a), 3, 'Y'))
    n.collar(blk, h=0.06)
    n.belt('Leather_Brown')
    for sx in (-1, 1):                   # belt pouches with gold clasps
        n.box(f'LowerTorso_Pouch{SIDE[sx]}', (sx * 0.19, -0.18, Z_WAIST - 0.04), (0.1, 0.05, 0.1), 'Leather_Brown',
              'LowerTorso', 'Accessories', bevel=0.012)
        n.box(f'LowerTorso_PouchClasp{SIDE[sx]}', (sx * 0.19, -0.207, Z_WAIST - 0.02), (0.035, 0.008, 0.03), 'Gold',
              'LowerTorso', 'Accessories', bevel=0.003)
    n.skirt('CoatTail', [(Z_WAIST, 0.3, 0.16), (0.5, 0.325, 0.19), (0.24, 0.35, 0.215)], red, trim='Gold', open_front=26)
    n.mantle('Capelet', red, trim='Gold', drop=0.17, reach=0.6, open_front=56)
    for side in ('Right', 'Left'):
        n.sleeve(side, 'Sleeve', Z_ELB, Z_SH, 0.15, 0.152, red)
    glove_cuffs(n, 'Glove_Black', trim='Gold')
    # merchant hat: wide red brim with black underside and gold rim, bent red crown, gold band
    z = 1.415
    n.lathe('Head_HatBrim', [(0, 0.016), (0.32, 0.008), (0.46, -0.004), (0.465, -0.012), (0, -0.004)], red,
            'Head', 'Hat', (0, 0, z), segs=16)
    n.lathe('Head_HatBrimUnder', [(0, -0.005), (0.462, -0.013), (0.455, -0.024), (0, -0.016)], blk, 'Head', 'Hat',
            (0, 0, z), segs=16)
    n.add('Head_HatRim', circle_tube((0, 0, z - 0.012), 0.466, 0.011, 24), 'Gold', 'Head', 'Hat')
    n.lathe('Head_HatCrown', [(0.235, 0.0), (0.215, 0.08), (0.17, 0.18), (0.11, 0.28), (0.05, 0.36), (0, 0.4)], red,
            'Head', 'Hat', (0, 0, z), segs=12, bend=lambda h: Vector((0.25 * h * h, 0.9 * h * h, 0)))
    n.ring('Head_HatBand', [(z + 0.005, 0.24, 0.24), (z + 0.065, 0.222, 0.222)], 'Gold', 'Head', 'Hat', n=16, p=2.0,
           thick=0.014)
    # gold flower ornament on the crown (character's left, front) and a plume of feathers
    fc, fn = Vector((0.165, -0.15, z + 0.08)), Vector((0.55, -0.8, 0.25)).normalized()
    M = frame(fn)
    bm = ellipsoid_bm(fc + fn * 0.02, (0.03, 0.03, 0.025), 1)
    for k in range(6):
        a = math.pi / 3 * k
        merge(bm, ellipsoid_bm(fc + M @ Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0)),
                               (0.04, 0.04, 0.016), 1, rot=M))
    n.add('Head_HatFlower', bm, 'Gold', 'Head', 'Hat', center=fc)
    for k, (up, L, m) in enumerate((((-0.6, 0.35, 0.75), 0.34, mat('Shop_FeatherOrange', (250, 150, 44))),
                                    ((-0.35, 0.5, 0.8), 0.3, mat('Shop_FeatherYellow', (255, 206, 72))),
                                    ((-0.75, 0.15, 0.6), 0.26, 'Shop_FeatherYellow'))):
        o = Vector((-0.18, 0.08, z + 0.07))
        n.add(f'Head_HatFeather_{k + 1}', place(leaf_bm(L, 0.11, 0.02, 0.2), axes(up, (0.3, -1, 0.1)), o), m,
              'Head', 'Hat', center=o)
    # messy black hair under the hat
    n.hair_cap(hair, back_low=-0.13, side_low=-0.05)
    n.bangs(n=6, span=0.16, tip_z=0.025, w=0.05, jag=0.03, seed=1)
    n.messy(0.08, rows=((-8, 34, -0.05), (18, 42, -0.04)), w=0.06, back=0.02, seed=1)
    n.hair_done()


# ------------------------------------------------------------------ 02 EGG
def build_egg(n):
    pur = mat('Egg_Purple', (130, 58, 192))
    pdk = mat('Egg_PurpleDark', (62, 30, 102))
    hair = mat('Egg_Hair', (214, 190, 238))
    glow = mat('Egg_EggGlow', (236, 140, 255), 0.3, 0.0, emit=1.0)
    gem = mat('Egg_Gem', (176, 86, 236), 0.2, 0.4, emit=0.6)
    n.body(top=pdk, bottom=pdk, arm_u=pur, arm_l=pur, hand='Glove_Black', leg_u='Glove_Black', foot='Glove_Black')
    n.face()
    torso_shell(n, 'Robe', pur)
    n.coat_front(pdk, 'Gold', width=0.2, name='RobeFront')
    gem_emblem(n, 'UpperTorso_Emblem', (0, -0.19, 0.96), 0.075, 'Gold', 'White')
    n.collar(pdk, h=0.09, hw=0.14, hd=0.11)
    n.belt(pdk, 'Gold', gem=gem)
    n.skirt('Underskirt', [(Z_WAIST - 0.01, 0.29, 0.15), (0.4, 0.31, 0.185), (0.04, 0.335, 0.215)], 'White')
    front_strip(n, 'LowerTorso_UnderskirtStripe', 0, Z_WAIST - 0.03, 0.05, -0.162, -0.228, 0.07, 'Glove_Black')
    n.skirt('Robe', [(Z_WAIST, 0.3, 0.16), (0.4, 0.33, 0.2), (0.03, 0.37, 0.24)], pur, trim='Gold', open_front=36)
    n.mantle('Mantle', pur, trim='Gold', drop=0.22, reach=0.62, open_front=56)
    n.cape('Cloak', [(Z_SH, 0.3, 0.17), (0.75, 0.38, 0.24), (0.03, 0.44, 0.3)], pur, trim='Gold')
    for side in ('Right', 'Left'):
        n.sleeve(side, 'Sleeve', Z_ELB, Z_SH, 0.15, 0.16, pur)
        n.sleeve(side, 'SleeveWide', Z_WR + 0.01, Z_ELB + 0.01, 0.16, 0.215, pur, lower=True)
        n.cuff(side, 'Cuff', Z_WR + 0.005, Z_WR + 0.05, 0.222, 'Gold')
    # long pale lavender hair with a big messy crown
    n.hair_cap(hair, back_low=-0.2, side_low=-0.07)
    n.bangs(n=5, span=0.15, tip_z=0.035, w=0.06, sweep=0.3, seed=2)
    n.messy(0.11, rows=((22, 38, -0.03), (50, 48, -0.02)), w=0.085, back=0.06, front_gap=40, seed=2)
    n.side_locks(0.33, w=0.06, count=2, out=0.23)
    n.long_hair(0.62, n=11, spread=0.08, w=0.075, wave=0.04, arc=(80, 280), seed=3)
    n.hair_done()
    # glowing egg held up in the right hand
    n.bend('Right', 70)
    c, up, fwd = n.hand('Right')
    n.ell('RightHand_PropEgg', c + up * 0.19, (0.085, 0.085, 0.11), glow, 'RightHand', 'Props', sub=2, smooth=True)


# ------------------------------------------------------------------ 03 TRADING
def build_trading(n):
    brn = mat('Trade_Brown', (78, 50, 32))
    brl = mat('Trade_BrownLight', (142, 90, 48))
    rust = mat('Trade_Rust', (168, 92, 40))
    hat = mat('Trade_HatBlack', (34, 30, 30))
    hair = mat('Trade_Hair', (130, 76, 40))
    brass = mat('Trade_Brass', (214, 164, 72), 0.3, 0.4, metal=0.5)
    lens = mat('Trade_Lens', (255, 214, 140), 0.15, 0.6, emit=0.5)
    n.body(top='White', bottom=brn, arm_u='White', arm_l='White', hand='Glove_Black', leg_u=brn, foot='Glove_Black')
    n.face()
    torso_shell(n, 'Coat', brn)
    n.coat_front('White', 'Gold', width=0.24)
    for sx in (-1, 1):                     # brown vest panels with gold buttons
        n.box(f'UpperTorso_Vest{SIDE[sx]}', (sx * 0.085, -0.182, 0.9), (0.07, 0.012, 0.32), brl, 'UpperTorso', 'Clothing',
              bevel=0.004)
        for k, z in enumerate((0.98, 0.9, 0.82)):
            n.box(f'UpperTorso_Button{SIDE[sx]}{k + 1}', (sx * 0.085, -0.19, z), (0.022, 0.01, 0.022), 'Gold',
                  'UpperTorso', 'Accessories', bevel=0.004)
    n.box('UpperTorso_Medal', (0, -0.186, 0.98), (0.05, 0.01, 0.05), 'Gold', 'UpperTorso', 'Accessories',
          bevel=0.006, rot=Matrix.Rotation(math.radians(45), 3, 'Y'))
    n.collar('White', h=0.06)
    n.belt('Leather_Brown')
    front_strip(n, 'LowerTorso_ShirtTail', 0, Z_WAIST - 0.03, 0.36, -0.166, -0.19, 0.2, 'White')
    n.skirt('CoatTail', [(Z_WAIST, 0.3, 0.16), (0.5, 0.315, 0.18), (0.34, 0.33, 0.195)], brn, trim='Gold', open_front=28)
    n.mantle('Capelet', rust, trim='Gold', drop=0.17, reach=0.6, open_front=64)
    n.ell('UpperTorso_ShoulderButton', (-0.38, -0.2, Z_SH - 0.06), (0.03, 0.012, 0.03), 'Gold', 'UpperTorso',
          'Accessories', 1)
    for side in ('Right', 'Left'):
        n.cuff(side, 'CuffTrim', Z_WR + 0.085, Z_WR + 0.115, 0.15, 'Gold')
    glove_cuffs(n, 'Glove_Black')
    # leather satchel on the left hip with a strap across the chest
    n.box('LowerTorso_Satchel', (0.31, -0.07, 0.6), (0.11, 0.2, 0.2), brl, 'LowerTorso', 'Accessories', bevel=0.02)
    n.box('LowerTorso_SatchelFlap', (0.37, -0.07, 0.65), (0.012, 0.19, 0.11), 'Leather_Brown', 'LowerTorso',
          'Accessories', bevel=0.004)
    n.box('LowerTorso_SatchelClasp', (0.38, -0.07, 0.62), (0.008, 0.035, 0.03), 'Gold', 'LowerTorso', 'Accessories',
          bevel=0.003)
    n.add('UpperTorso_SatchelStrap', tube_bm(bezier([Vector((-0.22, -0.176, Z_SH - 0.01)), Vector((0.0, -0.186, 0.92)),
                                                      Vector((0.3, -0.17, 0.7))], 8), [0.014] * 8, 5),
          'Leather_Brown', 'UpperTorso', 'Accessories')
    # black wide-brim hat with round crown and brass goggles
    z = 1.42
    n.lathe('Head_HatBrim', [(0, 0.012), (0.3, 0.004), (0.355, 0.018), (0.36, 0.006), (0.3, -0.012), (0, -0.006)],
            hat, 'Head', 'Hat', (0, 0, z), segs=16)
    n.lathe('Head_HatCrown', [(0.225, 0.0), (0.22, 0.12), (0.19, 0.17), (0.1, 0.19), (0, 0.192)], hat, 'Head', 'Hat',
            (0, 0, z), segs=16)
    n.ring('Head_HatBand', [(z + 0.006, 0.23, 0.23), (z + 0.05, 0.226, 0.226)], 'Leather_Brown', 'Head', 'Hat', n=16,
           p=2.0, thick=0.012)
    for sx in (-1, 1):
        c = Vector((sx * 0.075, -0.235, z + 0.095))
        ax = Vector((0, -1, 0.25))
        n.lathe(f'Head_Goggle{SIDE[sx]}', [(0, 0.0), (0.062, 0.0), (0.066, 0.025), (0.055, 0.045), (0, 0.042)], brass,
                'Head', 'Hat', c, axis=ax, segs=12)
        n.lathe(f'Head_GoggleLens{SIDE[sx]}', [(0, 0.05), (0.046, 0.044), (0.047, 0.038), (0, 0.038)], lens, 'Head', 'Hat',
                c, axis=ax, segs=12)
    n.box('Head_GoggleBridge', (0, -0.24, z + 0.1), (0.05, 0.02, 0.02), brass, 'Head', 'Hat', bevel=0.004)
    # brown messy hair
    n.hair_cap(hair, back_low=-0.13, side_low=-0.06)
    n.bangs(n=6, span=0.16, tip_z=0.02, w=0.052, jag=0.03, sweep=-0.3, seed=4)
    n.messy(0.08, rows=((-8, 34, -0.05), (18, 42, -0.04)), w=0.06, back=0.02, seed=4)
    n.hair_done()


# ------------------------------------------------------------------ 04 UPGRADES
def build_upgrades(n):
    blu = mat('Upg_Blue', (36, 80, 198))
    bld = mat('Upg_BlueDark', (22, 44, 118))
    hair = mat('Upg_Hair', (228, 232, 248))
    cry = mat('Upg_CrystalGlow', (70, 170, 255), 0.15, 0.3, emit=1.4)
    bow = mat('Upg_Bow', (248, 202, 82))
    gem = mat('Upg_Gem', (70, 150, 255), 0.2, 0.4, emit=0.8)
    n.body(top='White', bottom=blu, arm_u='White', arm_l='White', hand='Skin', leg_u=blu, foot=bld)
    n.face()
    torso_shell(n, 'Robe', blu)
    n.coat_front('White', 'Gold', width=0.16)
    gem_emblem(n, 'UpperTorso_Brooch', (0, -0.19, 1.04), 0.035, 'Gold', gem)
    n.belt(bld, 'Gold', gem=gem)
    n.add('RightUpperArm_Pauldron', rbox_bm((-0.43, 0, Z_SH - 0.005), (0.175, 0.165, 0.065), 3.0, 3), 'Gold',
          'RightUpperArm', 'Accessories')
    n.add('RightUpperArm_PauldronRidge', rbox_bm((-0.44, -0.0, Z_SH + 0.05), (0.13, 0.12, 0.03), 3.0, 2), 'Gold',
          'RightUpperArm', 'Accessories')
    n.skirt('Underskirt', [(Z_WAIST - 0.01, 0.29, 0.15), (0.4, 0.31, 0.185), (0.04, 0.335, 0.215)], 'White')
    n.skirt('Robe', [(Z_WAIST, 0.3, 0.16), (0.4, 0.33, 0.2), (0.03, 0.37, 0.24)], blu, trim='Gold', open_front=34)
    n.cape('Cloak', [(Z_SH, 0.3, 0.17), (0.75, 0.37, 0.24), (0.03, 0.43, 0.3)], 'White', trim='Gold')
    for side in ('Right', 'Left'):
        n.sleeve(side, 'Sleeve', Z_ELB, Z_SH, 0.15, 0.16, 'White')
        n.sleeve(side, 'SleeveWide', Z_WR + 0.02, Z_ELB + 0.01, 0.16, 0.22, 'White', lower=True)
        n.cuff(side, 'Cuff', Z_WR + 0.015, Z_WR + 0.08, 0.226, blu)
        n.cuff(side, 'CuffTrim', Z_WR + 0.08, Z_WR + 0.1, 0.222, 'Gold')
    wizard_hat(n, blu, None, brim_r=0.4, h=0.56, base_r=0.22, z=1.42, bend=(-0.03, 0.18))
    bc = Vector((-0.2, -0.1, 1.5))           # yellow bow on the hat (character's right)
    bm = ellipsoid_bm(bc, (0.035, 0.03, 0.035), 1)
    for s in (-1, 1):
        merge(bm, ellipsoid_bm(bc + Vector((0.0, s * 0.045, 0.04)), (0.03, 0.06, 0.045), 1,
                               rot=Matrix.Rotation(s * 0.5, 3, 'X')))
    n.add('Head_HatBow', bm, bow, 'Head', 'Hat', center=bc)
    # long straight white hair
    n.hair_cap(hair, back_low=-0.2, side_low=-0.08)
    n.bangs(n=5, span=0.15, tip_z=0.03, w=0.058, sweep=-0.2, seed=5)
    n.side_locks(0.34, w=0.06, count=2, out=0.22)
    n.long_hair(0.42, n=9, spread=0.05, w=0.07, arc=(85, 275), seed=6)
    n.hair_done()
    # staff with a glowing blue crystal in the left hand
    n.bend('Left', 55)
    c, up, fwd = n.hand('Left')
    n.add('LeftHand_PropStaff', tube_bm([Vector((c.x, c.y, 0.05)), Vector((c.x, c.y, 1.0)),
                                         Vector((c.x, c.y + 0.01, 1.42))], [0.024, 0.026, 0.03], 7),
          'Wood_Dark', 'LeftHand', 'Props')
    top = Vector((c.x, c.y + 0.01, 1.42))
    bm = bmesh.new()
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        merge(bm, tube_bm(bezier([top, top + d * 0.07 + Vector((0, 0, 0.05)), top + d * 0.045 + Vector((0, 0, 0.17))],
                                 6), [0.022, 0.02, 0.016, 0.012, 0.008, 0.004], 5))
    n.add('LeftHand_PropStaffClaws', bm, 'Wood_Dark', 'LeftHand', 'Props')
    n.add('LeftHand_PropCrystal', diamond_bm(top + Vector((0, 0, 0.17)), 0.065, 0.13, 0.045), cry, 'LeftHand', 'Props')


# ------------------------------------------------------------------ 05 PETS
def build_pets(n):
    grn = mat('Pets_Green', (40, 142, 64))
    gdk = mat('Pets_GreenDark', (24, 92, 44))
    cream = mat('Pets_Cream', (242, 232, 205))
    hair = mat('Pets_Hair', (36, 112, 50))
    leaf = mat('Pets_Leaf', (98, 186, 64))
    glow = mat('Pets_LeafGlow', (60, 230, 110), 0.2, 0.0, emit=1.3)
    gem = mat('Pets_Gem', (60, 210, 110), 0.2, 0.4, emit=0.6)
    n.body(top=grn, bottom=grn, arm_u='Skin', arm_l='Skin', hand=gdk, leg_u=gdk, foot=gdk)
    n.face()
    torso_shell(n, 'Dress', grn)
    n.coat_front(cream, None, width=0.2)
    bm = bmesh.new()                      # gold V trim from the shoulders to the waist
    for sx in (-1, 1):
        merge(bm, tube_bm([Vector((sx * 0.2, -0.176, Z_SH - 0.01)), Vector((0, -0.18, 0.78))], [0.014, 0.014], 5))
    n.add('UpperTorso_VTrim', bm, 'Gold', 'UpperTorso', 'Clothing')
    gem_emblem(n, 'UpperTorso_LeafBrooch', (0, -0.19, 0.95), 0.05, 'Gold', gem)
    n.belt('Leather_Brown', gem=gem)
    n.skirt('Underskirt', [(Z_WAIST - 0.01, 0.29, 0.15), (0.4, 0.31, 0.185), (0.04, 0.335, 0.215)], cream)
    n.skirt('Dress', [(Z_WAIST, 0.3, 0.16), (0.4, 0.33, 0.2), (0.03, 0.37, 0.24)], grn, trim='Gold', open_front=34)
    n.mantle('Capelet', grn, trim='Gold', drop=0.13, reach=0.58, open_front=70)
    for side in ('Right', 'Left'):
        n.cuff(side, 'Bracer', Z_WR - 0.004, Z_WR + 0.06, 0.15, 'Gold')
    # long wavy green hair
    n.hair_cap(hair, back_low=-0.2, side_low=-0.07)
    n.bangs(n=6, span=0.16, tip_z=0.005, w=0.06, sweep=0.4, jag=0.035, seed=7)
    n.side_locks(0.34, w=0.065, count=2, out=0.24)
    n.long_hair(0.55, n=11, spread=0.1, w=0.08, wave=0.05, arc=(75, 285), seed=8)
    n.messy(0.1, rows=((25, 40, -0.04), (55, 55, -0.01)), w=0.08, back=0.03, seed=8)
    n.hair_done()
    # leaf crown with golden antler horns
    z = 1.47
    bm = bmesh.new()
    for k in range(12):
        a = 2 * math.pi * k / 12
        d = Vector((math.sin(a), -math.cos(a), 0))
        o = Vector((0, 0.01, z)) + d * 0.19
        merge(bm, place(leaf_bm(0.13, 0.085, 0.016, 0.15), axes(d * 0.6 + Vector((0, 0, 0.8)), d), o))
    n.add('Head_LeafCrown', bm, leaf, 'Head', 'Hat', center=Vector((0, 0, z)))
    bm = bmesh.new()
    for th, L, lean in ((-25, 0.2, 0.15), (25, 0.2, 0.15), (-65, 0.17, 0.5), (65, 0.17, 0.5), (-110, 0.14, 0.7),
                        (110, 0.14, 0.7)):
        a = math.radians(th)
        d = Vector((math.sin(a), -math.cos(a), 0))
        b = Vector((0, 0.01, z + 0.02)) + d * 0.17
        tip = b + d * L * lean + Vector((0, 0, L))
        merge(bm, tube_bm(bezier([b, b + d * 0.06 + Vector((0, 0, L * 0.45)), tip], 6),
                          [0.022, 0.019, 0.015, 0.011, 0.007, 0.003], 5))
    n.add('Head_Antlers', bm, 'Gold', 'Head', 'Hat')
    # staff with a glowing leaf crystal (right hand), leafy branch (left hand)
    n.bend('Right', 50)
    n.bend('Left', 45)
    c, up, fwd = n.hand('Right')
    top = Vector((c.x, c.y, 1.3))
    n.add('RightHand_PropStaff', tube_bm([Vector((c.x, c.y, 0.06)), Vector((c.x, c.y, 0.8)), top],
                                         [0.024, 0.026, 0.03], 7), 'Wood_Dark', 'RightHand', 'Props')
    bm = bmesh.new()
    for k in range(4):
        a = 2 * math.pi * k / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        merge(bm, place(leaf_bm(0.13, 0.08, 0.016, 0.15), axes(d * 0.5 + Vector((0, 0, 0.8)), d), top - Vector((0, 0, 0.03))))
    n.add('RightHand_PropStaffLeaves', bm, leaf, 'RightHand', 'Props')
    gc = top + Vector((0, 0, 0.08))
    n.lathe('RightHand_PropLeafCrystal', [(0, 0), (0.05, 0.03), (0.06, 0.08), (0.04, 0.14), (0.015, 0.2), (0, 0.23)],
            glow, 'RightHand', 'Props', gc, segs=8)
    c, up, fwd = n.hand('Left')
    path = [c + Vector((0, 0.0, -0.08)), c + Vector((0.03, -0.02, 0.25)), c + Vector((0.07, -0.02, 0.55))]
    n.add('LeftHand_PropBranch', tube_bm(bezier(path, 6), [0.02, 0.018, 0.016, 0.013, 0.01, 0.006], 6), 'Wood_Dark',
          'LeftHand', 'Props')
    bm = bmesh.new()
    for t, sd, L in ((0.45, 1, 0.16), (0.6, -1, 0.17), (0.78, 1, 0.15), (0.9, -1, 0.14), (1.0, 0, 0.16)):
        p = bezier(path, 21)[int(t * 20)]
        up2 = Vector((sd * 0.8, -0.1, 0.6 if sd else 1.0))
        merge(bm, place(leaf_bm(L, 0.1, 0.018, 0.18), axes(up2, (0.2, -1, 0.1)), p))
    n.add('LeftHand_PropBranchLeaves', bm, leaf, 'LeftHand', 'Props')


# ------------------------------------------------------------------ 06 LEADERBOARDS
def build_leaderboards(n):
    roy = mat('Lead_Blue', (32, 66, 182))
    bld = mat('Lead_BlueDark', (22, 40, 120))
    hair = mat('Lead_Hair', (230, 196, 140))
    gem = mat('Lead_Gem', (90, 170, 255), 0.2, 0.4, emit=0.6)
    n.body(top=roy, bottom=roy, arm_u='White', arm_l='White', hand='Skin', leg_u=roy, foot=bld)
    n.face()
    torso_shell(n, 'Tunic', roy)
    n.coat_front(roy, 'Gold', width=0.12, name='TunicFront')
    gem_emblem(n, 'UpperTorso_Emblem', (0, -0.19, 1.0), 0.07, 'Gold', gem)
    for sx in (-1, 1):
        n.box(f'UpperTorso_EmblemWing{SIDE[sx]}', (sx * 0.09, -0.186, 1.03), (0.1, 0.012, 0.03), 'Gold', 'UpperTorso',
              'Accessories', bevel=0.004, rot=Matrix.Rotation(math.radians(-sx * 25), 3, 'Y'))
    n.collar(roy, h=0.08, hw=0.14, hd=0.11)
    n.belt('Gold', 'Gold', gem=gem)
    n.skirt('Skirt', [(Z_WAIST, 0.3, 0.16), (0.4, 0.33, 0.2), (0.03, 0.37, 0.24)], roy, trim='Gold')
    for k, x in enumerate((-0.13, -0.05, 0.05, 0.13)):
        front_strip(n, f'LowerTorso_SkirtStripe{k + 1}', x, Z_WAIST - 0.04, 0.06, -0.172, -0.25, 0.022, 'Gold')
    n.cape('Cape', [(Z_SH, 0.3, 0.17), (0.75, 0.38, 0.24), (0.03, 0.44, 0.3)], 'White', trim='Gold')
    n.ring('UpperTorso_CapeStripe', [(0.14, 0.432, 0.292), (0.22, 0.427, 0.287)], roy, 'UpperTorso', 'Back',
           sector=(105, 255), thick=0.028)
    n.mantle('FurMantle', 'White', trim='Gold', drop=0.17, reach=0.6, open_front=70)
    for side in ('Right', 'Left'):
        n.sleeve(side, 'Sleeve', Z_ELB, Z_SH, 0.15, 0.16, 'White')
        n.sleeve(side, 'SleeveWide', Z_WR + 0.02, Z_ELB + 0.01, 0.16, 0.22, 'White', lower=True)
        n.cuff(side, 'CuffBand', Z_WR + 0.02, Z_WR + 0.07, 0.226, roy)
        n.cuff(side, 'SleeveBand', Z_ELB - 0.07, Z_ELB - 0.03, 0.2, roy)
    # very long wavy blonde hair
    n.hair_cap(hair, back_low=-0.22, side_low=-0.07)
    n.bangs(n=5, span=0.15, tip_z=0.04, w=0.06, sweep=0.35, seed=9)
    n.side_locks(0.47, w=0.07, count=2, out=0.25)
    n.long_hair(0.74, n=12, spread=0.12, w=0.08, wave=0.06, arc=(70, 290), seed=10)
    n.hair_done()
    # royal crown: blue band, gold rims, gold spikes with orbs, gems
    z = 1.44
    n.ring('Head_CrownBand', [(z, 0.212, 0.212), (z + 0.1, 0.22, 0.22)], roy, 'Head', 'Hat', n=16, p=2.0, thick=0.02)
    for k, zz in enumerate((z, z + 0.09)):
        n.ring(f'Head_CrownRim{("Lower", "Upper")[k]}', [(zz - 0.008, 0.226, 0.226), (zz + 0.02, 0.228, 0.228)], 'Gold', 'Head', 'Hat',
               n=16, p=2.0, thick=0.02)
    bm = bmesh.new()
    orbs = bmesh.new()
    for th, h in ((0, 0.15), (-40, 0.11), (40, 0.11), (-85, 0.1), (85, 0.1), (-135, 0.09), (135, 0.09), (180, 0.09)):
        a = math.radians(th)
        d = Vector((math.sin(a), -math.cos(a), 0))
        b = Vector((0, 0, z + 0.1)) + d * 0.222
        merge(bm, lathe_bm([(0.045, 0), (0.0, h)], 4, b, axis=d * 0.12 + Vector((0, 0, 1)), up=d))
        merge(orbs, ellipsoid_bm(b + d * 0.015 + Vector((0, 0, h + 0.01)), (0.018, 0.018, 0.018), 1))
    n.add('Head_CrownSpikes', bm, 'Gold', 'Head', 'Hat')
    n.add('Head_CrownOrbs', orbs, 'Gold', 'Head', 'Hat')
    bm = bmesh.new()
    for th in (-50, -25, 0, 25, 50):
        a = math.radians(th)
        d = Vector((math.sin(a), -math.cos(a), 0))
        merge(bm, ellipsoid_bm(Vector((0, 0, z + 0.05)) + d * 0.232, (0.02, 0.02, 0.022), 1))
    n.add('Head_CrownGems', bm, gem, 'Head', 'Hat')


# ------------------------------------------------------------------ 07 TOWER GUIDE
def build_guide(n):
    blu = mat('Guide_Blue', (40, 94, 208))
    bdk = mat('Guide_BlueDark', (26, 56, 140))
    hair = mat('Guide_Hair', (238, 238, 244))
    book = mat('Guide_Book', (112, 66, 36))
    pages = mat('Guide_Pages', (246, 236, 212))
    paw = mat('Guide_PawGlow', (70, 180, 255), 0.2, 0.0, emit=1.5)
    n.body(top='White', bottom=blu, arm_u=blu, arm_l='White', hand='Skin', leg_u=blu, leg_l=blu, foot=bdk)
    n.face()
    torso_shell(n, 'Coat', blu)
    n.coat_front('White', 'White', width=0.2)
    n.belt('Leather_Brown')
    n.skirt('CoatTail', [(Z_WAIST, 0.3, 0.16), (0.45, 0.325, 0.19), (0.2, 0.35, 0.215)], blu, trim='White', open_front=26)
    n.cape('Cape', [(Z_SH, 0.3, 0.17), (0.8, 0.34, 0.22), (0.46, 0.37, 0.25)], 'White', trim=blu)
    for side in ('Right', 'Left'):
        n.cuff(side, 'SleeveCuff', Z_ELB - 0.04, Z_ELB + 0.03, 0.155, 'White', lower=False)
        sx = -1 if side == 'Right' else 1
        n.band(f'{side}LowerLeg_PantsCuff', Z_ANK, Z_ANK + 0.045, 0.148, 0.148, 'White', side + 'LowerLeg', 'Clothing',
               cx=sx * LEG_X, n=16)
    wizard_hat(n, blu, 'White', brim_r=0.34, h=0.48, base_r=0.215, z=1.42, bend=(0.03, 0.15))
    # long white hair with two long front locks
    n.hair_cap(hair, back_low=-0.2, side_low=-0.08)
    n.bangs(n=5, span=0.15, tip_z=0.03, w=0.058, sweep=0.25, seed=11)
    n.side_locks(0.42, w=0.055, count=2, out=0.22)
    n.long_hair(0.45, n=9, spread=0.05, w=0.07, arc=(85, 275), seed=12)
    n.hair_done()
    # book (right hand) and a glowing paw sign over the left hand
    n.bend('Right', 70)
    n.bend('Left', 60)
    c, up, fwd = n.hand('Right')
    bc = c + up * 0.17 + Vector((0, -0.02, 0))
    n.box('RightHand_PropBook', bc, (0.22, 0.07, 0.28), book, 'RightHand', 'Props', bevel=0.01)
    n.box('RightHand_PropBookPages', bc + Vector((0.012, 0, 0)), (0.205, 0.056, 0.27), pages, 'RightHand', 'Props',
          bevel=0.004)
    bm = bmesh.new()
    for (dx, dz, sx, sz) in ((0, 0.11, 0.17, 0.012), (0, -0.11, 0.17, 0.012), (-0.08, 0, 0.012, 0.22), (0.08, 0, 0.012, 0.22)):
        merge(bm, box_bm(bc + Vector((dx, -0.037, dz)), (sx, 0.006, sz)))
    n.add('RightHand_PropBookTrim', bm, 'Gold', 'RightHand', 'Props')
    c, up, fwd = n.hand('Left')
    n.add('LeftHand_PropPawGlow', paw_bm(c + up * 0.24, (-0.3, -1, 0.1), 0.13), paw, 'LeftHand', 'Props')


# ------------------------------------------------------------------ 08 TOWER ENTRANCE
def build_entrance(n):
    coat = mat('Ent_Coat', (28, 30, 50))
    hood = mat('Ent_Hood', (42, 72, 176))
    inner = mat('Ent_Inner', (34, 60, 150))
    trim = mat('Ent_Trim', (222, 144, 64), 0.35, 0.3)
    void = mat('Ent_FaceVoid', (6, 6, 14), 0.7, 0.0)
    eye = mat('Ent_EyeGlow', (110, 200, 255), 0.2, 0.0, emit=3.0)
    glow = mat('Ent_PawGlow', (80, 180, 255), 0.2, 0.0, emit=1.8)
    n.body(top=inner, bottom=coat, arm_u=coat, arm_l=coat, hand='Glove_Black', leg_u=coat, foot='Glove_Black', head=void)
    for sx in (-1, 1):                      # glowing slanted eyes in the shadowed face
        n.box(f'Head_EyeGlow_{"Right" if sx < 0 else "Left"}', (sx * 0.062, FRONT - 0.004, HEAD_C.z + 0.0),
              (0.075, 0.012, 0.03), eye, 'Head', 'Face', bevel=0.006, rot=Matrix.Rotation(math.radians(-sx * 16), 3, 'Y'))
    torso_shell(n, 'Coat', coat)
    n.coat_front(inner, trim, width=0.22)
    n.add('UpperTorso_PawEmblem', paw_bm(Vector((0, -0.192, 0.95)), (0, -1, 0), 0.085), glow, 'UpperTorso', 'Accessories')
    bm = bmesh.new()
    for a in (35, 145, 215, 325):
        d = Vector((math.cos(math.radians(a)), 0, math.sin(math.radians(a))))
        merge(bm, tube_bm([Vector((0, -0.19, 0.95)) + d * 0.08, Vector((0, -0.19, 0.95)) + d * 0.14 + Vector((0, 0, 0.02))],
                          [0.006, 0.004], 4))
    n.add('UpperTorso_RuneLines', bm, glow, 'UpperTorso', 'Accessories')
    n.skirt('InnerRobe', [(Z_WAIST - 0.01, 0.29, 0.15), (0.4, 0.31, 0.18), (0.05, 0.33, 0.205)], inner)
    n.skirt('LongCoat', [(Z_WAIST, 0.3, 0.16), (0.4, 0.33, 0.2), (0.04, 0.37, 0.24)], coat, trim=trim, open_front=34)
    for side in ('Right', 'Left'):
        n.sleeve(side, 'Sleeve', Z_ELB, Z_SH, 0.15, 0.155, coat)
        n.sleeve(side, 'SleeveFlare', Z_WR + 0.01, Z_ELB + 0.01, 0.155, 0.19, coat, lower=True)
        n.cuff(side, 'CuffTrim', Z_WR + 0.005, Z_WR + 0.035, 0.196, trim)
    n.mantle('HoodMantle', hood, trim=trim, drop=0.2, reach=0.58, open_front=60)
    # pointed hood around the head, open at the face
    c0 = HEAD_C + Vector((0, 0.02, 0.025))
    bm = rbox_bm(c0, (0.232, 0.228, 0.235), 3.0, 4)
    for v in bm.verts:
        r = v.co - c0
        k = max(0.0, r.z / 0.235) ** 3 * max(0.0, 1 - abs(r.x) / 0.235)
        v.co += Vector((0, 0.2 * k, 0.17 * k))
    kill = [f for f in bm.faces if (lambda r: r.y < -0.08 and abs(r.x) < 0.17 and -0.2 < r.z < 0.14)(f.calc_center_median() - c0)
            or (f.calc_center_median() - c0).z < -0.2]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    n.add('Head_Hood', bm, hood, 'Head', 'Hat', solid=0.024)
    pts = [Vector((0.165 * math.sin(t), -0.224 + 0.02 * (1 - math.cos(t)), HEAD_C.z - 0.03 + 0.17 * math.cos(t)))
           for t in (math.radians(-100 + 200 * i / 16) for i in range(17))]
    n.add('Head_HoodTrim', tube_bm(pts, [0.014] * len(pts), 5), trim, 'Head', 'Hat')


# ------------------------------------------------------------------ 09 CODES
def build_codes(n):
    lav = mat('Codes_Lavender', (206, 158, 238))
    pink = mat('Codes_Pink', (244, 178, 226))
    blk = mat('Codes_Black', (34, 28, 40))
    hair = mat('Codes_Hair', (94, 42, 158))
    gift = mat('Codes_GiftGlow', (170, 80, 250), 0.25, 0.0, emit=1.3)
    rib = mat('Codes_Ribbon', (255, 240, 255), 0.3, 0.0, emit=0.7)
    n.body(top=blk, bottom=blk, arm_u=lav, arm_l=blk, hand=blk, leg_u=blk, foot=blk)
    n.face()
    torso_shell(n, 'Jacket', lav)
    n.coat_front(blk, pink, width=0.22, name='Shirt')
    n.collar(pink, h=0.06)
    n.belt(blk, 'Gold')
    n.skirt('JacketHem', [(Z_WAIST, 0.3, 0.16), (0.52, 0.31, 0.172)], lav, trim='Gold', open_front=40)
    for side in ('Right', 'Left'):
        n.sleeve(side, 'PuffSleeve', Z_ELB - 0.01, Z_SH + 0.01, 0.155, 0.175, lav)
        n.cuff(side, 'SleeveTrim', Z_ELB - 0.03, Z_ELB + 0.01, 0.18, 'Gold', lower=False)
    # messy purple hair with a gold bow
    n.hair_cap(hair, back_low=-0.17, side_low=-0.08)
    n.bangs(n=6, span=0.16, tip_z=0.03, w=0.055, jag=0.04, sweep=0.3, seed=13)
    n.messy(0.1, rows=((-12, 34, -0.07), (18, 38, -0.05), (48, 48, -0.02), (75, 90, 0.0)), w=0.07, back=0.02, seed=13)
    n.hair_done()
    bc = Vector((0.13, -0.08, 1.52))
    bm = ellipsoid_bm(bc, (0.03, 0.025, 0.03), 1)
    for s in (-1, 1):
        merge(bm, ellipsoid_bm(bc + Vector((s * 0.05, 0, 0.012)), (0.05, 0.022, 0.035), 1,
                               rot=Matrix.Rotation(s * 0.35, 3, 'Y')))
    n.add('Head_HairBow', bm, 'Gold', 'Head', 'Hair', center=bc)
    # glowing gift box floating over the left hand + sparkles
    n.bend('Left', 70)
    c, up, fwd = n.hand('Left')
    g = c + up * 0.22
    n.box('LeftHand_PropGift', g, (0.16, 0.16, 0.15), gift, 'LeftHand', 'Props', bevel=0.012)
    bm = box_bm(g, (0.168, 0.035, 0.158))
    merge(bm, box_bm(g, (0.035, 0.168, 0.158)))
    for s in (-1, 1):
        merge(bm, ellipsoid_bm(g + Vector((s * 0.035, 0, 0.1)), (0.04, 0.015, 0.03), 1,
                               rot=Matrix.Rotation(-s * 0.5, 3, 'Y')))
    n.add('LeftHand_PropGiftRibbon', bm, rib, 'LeftHand', 'Props')
    bm = bmesh.new()
    for off, sz in (((0.14, -0.02, 0.14), 0.05), ((-0.12, -0.03, 0.1), 0.03), ((0.16, 0.0, -0.06), 0.025)):
        merge(bm, star_bm(g + Vector(off), sz))
    n.add('LeftHand_PropSparkles', bm, gift, 'LeftHand', 'Props')


# ------------------------------------------------------------------ 10 DAILY REWARDS
def build_daily(n):
    blk = mat('Daily_Black', (32, 28, 32))
    org = mat('Daily_Orange', (234, 124, 34))
    cream = mat('Daily_Cream', (242, 226, 200))
    hair = mat('Daily_Hair', (216, 104, 40))
    cal = mat('Daily_CalendarGlow', (255, 150, 40), 0.25, 0.0, emit=1.2)
    grid = mat('Daily_CalendarGrid', (255, 236, 180), 0.3, 0.0, emit=0.8)
    n.body(top=blk, bottom=blk, arm_u=blk, arm_l=blk, hand=blk, leg_u=blk, foot='Leather_Brown')
    n.face()
    torso_shell(n, 'Jacket', blk)
    n.coat_front(org, 'Gold', width=0.18, name='Vest')
    for k, z in enumerate((0.98, 0.9, 0.82)):
        n.box(f'UpperTorso_Embroidery{k + 1}', (0, -0.186, z), (0.05, 0.008, 0.05), 'Gold', 'UpperTorso', 'Accessories',
              bevel=0.005, rot=Matrix.Rotation(math.radians(45), 3, 'Y'))
    n.skirt('CoatTail', [(Z_WAIST, 0.3, 0.16), (0.5, 0.32, 0.18), (0.3, 0.34, 0.2)], blk, trim=org, open_front=24)
    for sx in (-1, 1):
        front_strip(n, f'LowerTorso_OrangeFlap{SIDE[sx]}', sx * 0.165, Z_WAIST - 0.01, 0.3, -0.172, -0.212, 0.14, org)
    n.mantle('Capelet', org, trim='Gold', drop=0.16, reach=0.58, open_front=90)
    for side in ('Right', 'Left'):
        n.cuff(side, 'CreamBand', Z_ELB - 0.08, Z_ELB - 0.01, 0.15, cream)
    # orange scarf: thick loop round the neck + tail hanging at the front
    n.ring('UpperTorso_Scarf', [(Z_SH - 0.02, 0.19, 0.155), (Z_SH + 0.03, 0.19, 0.16), (Z_SH + 0.075, 0.15, 0.13)],
           org, 'UpperTorso', 'Clothing', n=18, p=2.5, thick=0.045)
    n.add('UpperTorso_ScarfTail', strand_bm(bezier([Vector((-0.09, -0.19, Z_SH + 0.02)), Vector((-0.12, -0.215, 1.0)),
                                                    Vector((-0.13, -0.205, 0.86))], 6),
                                            [0.06, 0.062, 0.06, 0.058, 0.055, 0.05], 0.015, Vector((0, -1, 0))),
          org, 'UpperTorso', 'Clothing')
    # spiky orange hair
    n.hair_cap(hair, back_low=-0.13, side_low=-0.05)
    n.bangs(n=6, span=0.16, tip_z=0.04, w=0.052, jag=0.04, sweep=-0.3, seed=14)
    n.messy(0.13, rows=((5, 36, -0.03), (32, 36, 0.01), (58, 45, 0.03), (82, 120, 0.04)), w=0.07, back=0.04,
            front_gap=45, seed=14)
    n.hair_done()
    # glowing calendar over the left hand
    n.bend('Left', 70)
    c, up, fwd = n.hand('Left')
    g = c + up * 0.21
    n.box('LeftHand_PropCalendar', g, (0.18, 0.04, 0.17), cal, 'LeftHand', 'Props', bevel=0.014)
    bm = box_bm(g + Vector((0, -0.022, 0.05)), (0.15, 0.008, 0.03))
    for i in range(3):
        for j in range(2):
            merge(bm, box_bm(g + Vector((-0.05 + 0.05 * i, -0.022, -0.005 - 0.045 * j)), (0.035, 0.008, 0.03)))
    n.add('LeftHand_PropCalendarGrid', bm, grid, 'LeftHand', 'Props')
    bm = bmesh.new()
    for sx in (-1, 1):
        merge(bm, box_bm(g + Vector((sx * 0.05, 0, 0.095)), (0.022, 0.022, 0.05)))
    n.add('LeftHand_PropCalendarRings', bm, grid, 'LeftHand', 'Props')


# ------------------------------------------------------------------ 11 INDEX
def build_index(n):
    navy = mat('Index_Navy', (28, 34, 66))
    blk = mat('Index_Black', (24, 24, 30))
    hair = mat('Index_Hair', (24, 24, 34))
    glow = mat('Index_Glow', (70, 175, 255), 0.2, 0.0, emit=1.6)
    tab = mat('Index_TabletScreen', (34, 84, 214), 0.3, 0.3, emit=0.6)
    frm = mat('Index_TabletFrame', (40, 52, 112))
    n.body(top='White', bottom=navy, arm_u=navy, arm_l=navy, hand=blk, leg_u=blk, foot=blk)
    n.face()
    torso_shell(n, 'Coat', navy)
    n.coat_front('White', glow, width=0.2)
    n.add('UpperTorso_PawEmblem', paw_bm(Vector((0, -0.19, 0.97)), (0, -1, 0), 0.07), glow, 'UpperTorso', 'Accessories')
    n.belt('Leather_Brown')
    n.skirt('CoatTail', [(Z_WAIST, 0.3, 0.16), (0.5, 0.315, 0.18), (0.34, 0.33, 0.195)], navy, trim=glow, open_front=26,
            hem=0.012)
    for side in ('Right', 'Left'):
        sx = -1 if side == 'Right' else 1
        n.cuff(side, 'WhiteBand', Z_ELB - 0.09, Z_ELB - 0.04, 0.15, 'White')
        n.band(f'{side}LowerLeg_WhiteBand', Z_KNEE - 0.09, Z_KNEE - 0.04, 0.148, 0.148, 'White', side + 'LowerLeg',
               'Clothing', cx=sx * LEG_X, n=16)
    bc = Vector((0, 0.19, 0.7))               # glowing bow emblem on the lower back
    bm = ellipsoid_bm(bc, (0.025, 0.012, 0.025), 1)
    for s in (-1, 1):
        merge(bm, ellipsoid_bm(bc + Vector((s * 0.05, 0, 0.0)), (0.05, 0.012, 0.03), 1,
                               rot=Matrix.Rotation(s * 0.3, 3, 'Y')))
    n.add('LowerTorso_BackBow', bm, glow, 'LowerTorso', 'Back', center=bc)
    # messy black hair with a cowlick
    n.hair_cap(hair, back_low=-0.14, side_low=-0.06)
    n.bangs(n=6, span=0.16, tip_z=0.03, w=0.052, jag=0.035, sweep=0.2, seed=15)
    n.messy(0.09, rows=((0, 38, -0.04), (30, 42, -0.02), (60, 60, 0.0)), w=0.065, back=0.02, seed=15)
    n.lock(HEAD_C + Vector((0, -0.02, 0.19)), HEAD_C + Vector((0.03, -0.07, 0.33)), 0.035,
           bulge=Vector((-0.03, 0.03, 0.02)))
    n.hair_done()
    # round black glasses
    bm = bmesh.new()
    for sx in (-1, 1):
        merge(bm, circle_tube((sx * 0.064, FRONT - 0.016, HEAD_C.z + 0.012), 0.052, 0.008, 16, axis='Y'))
        merge(bm, tube_bm([Vector((sx * 0.116, FRONT - 0.014, HEAD_C.z + 0.02)), Vector((sx * 0.18, -0.12, HEAD_C.z + 0.03)),
                           Vector((sx * 0.182, 0.05, HEAD_C.z + 0.03))], [0.007] * 3, 4))
    merge(bm, tube_bm([Vector((-0.013, FRONT - 0.016, HEAD_C.z + 0.025)), Vector((0.013, FRONT - 0.016, HEAD_C.z + 0.025))],
                      [0.007, 0.007], 4))
    n.add('Head_Glasses', bm, 'Face_Black', 'Head', 'Accessories')
    # glowing index tablet in the left hand
    n.bend('Left', 70)
    c, up, fwd = n.hand('Left')
    g = c + up * 0.17
    n.box('LeftHand_PropTablet', g, (0.21, 0.03, 0.27), frm, 'LeftHand', 'Props', bevel=0.01)
    n.box('LeftHand_PropTabletScreen', g + Vector((0, -0.014, 0)), (0.17, 0.006, 0.23), tab, 'LeftHand', 'Props',
          bevel=0.003)
    n.add('LeftHand_PropTabletPaw', paw_bm(g + Vector((0, -0.02, 0)), (0, -1, 0), 0.07, depth=0.008), glow,
          'LeftHand', 'Props')


# ------------------------------------------------------------------ 12 SETTINGS
def build_settings(n):
    wht = mat('Set_White', (238, 238, 242))
    blk = mat('Set_Black', (30, 30, 36))
    grey = mat('Set_Grey', (152, 154, 164))
    hair = mat('Set_Hair', (236, 236, 244))
    lens = mat('Set_GoggleLens', (60, 122, 212), 0.1, 0.6, emit=0.4)
    strap = mat('Set_Strap', (30, 36, 62))
    holo = mat('Set_HoloGlow', (70, 175, 255), 0.2, 0.0, emit=1.4)
    holod = mat('Set_HoloPanel', (22, 64, 150), 0.3, 0.0, emit=0.5)
    n.body(top=wht, bottom=blk, arm_u=blk, arm_l=blk, hand=blk, leg_u=blk, foot=blk)
    n.face()
    torso_shell(n, 'Coat', blk)
    n.coat_front(wht, grey, width=0.2)
    for sx in (-1, 1):
        n.box(f'UpperTorso_WhitePanel{SIDE[sx]}', (sx * 0.2, -0.178, 1.0), (0.08, 0.01, 0.16), wht, 'UpperTorso', 'Clothing',
              bevel=0.004)
    n.belt(blk, 'Gold')
    n.skirt('CoatTail', [(Z_WAIST, 0.3, 0.16), (0.5, 0.32, 0.18), (0.3, 0.34, 0.2)], blk, trim=wht, open_front=26)
    n.box('RightUpperArm_ShoulderPad', (-0.42, 0, Z_SH - 0.06), (0.33, 0.33, 0.17), wht, 'RightUpperArm', 'Accessories',
          bevel=0.03)
    n.cuff('Right', 'PadStripe', Z_SH - 0.11, Z_SH - 0.09, 0.172, grey, lower=False)
    for side in ('Right', 'Left'):
        n.cuff(side, 'WhiteBand', Z_ELB - 0.1, Z_ELB - 0.04, 0.15, wht)
    n.cuff('Left', 'UpperBand', Z_ELB + 0.06, Z_ELB + 0.11, 0.15, wht, lower=False)
    # big spiky white hair with goggles on top
    n.hair_cap(hair, back_low=-0.14, side_low=-0.06)
    n.bangs(n=6, span=0.16, tip_z=0.03, w=0.055, jag=0.04, sweep=-0.25, seed=16)
    n.messy(0.15, rows=((-5, 32, -0.04), (22, 32, -0.01), (48, 40, 0.01), (75, 80, 0.02)), w=0.095, back=0.04,
            front_gap=45, seed=16)
    n.hair_done()
    zg = 1.47
    n.ring('Head_GoggleStrap', [(zg - 0.02, 0.222, 0.218), (zg + 0.02, 0.222, 0.218)], strap, 'Head', 'Accessories',
           n=20, p=2.5, thick=0.014)
    for sx in (-1, 1):
        cc = Vector((sx * 0.078, -0.2, zg + 0.04))
        ax = Vector((0, -0.75, 0.66))
        n.lathe(f'Head_GoggleFrame{SIDE[sx]}', [(0, 0), (0.066, 0), (0.07, 0.03), (0.06, 0.05), (0, 0.046)], strap, 'Head',
                'Accessories', cc, axis=ax, segs=12)
        n.lathe(f'Head_GoggleLens{SIDE[sx]}', [(0, 0.056), (0.05, 0.05), (0.051, 0.044), (0, 0.044)], lens, 'Head',
                'Accessories', cc, axis=ax, segs=12)
    # two floating holographic settings panels beside the left hand
    n.bend('Left', 60)
    c, up, fwd = n.hand('Left')
    for k, (off, w, h) in enumerate((((0.2, -0.05, 0.3), 0.3, 0.21), ((0.27, -0.02, 0.05), 0.18, 0.14))):
        pc = c + Vector(off)
        nrm = Vector((-0.35, -1, 0.05))
        M = frame(nrm)
        bm = place(box_bm((0, 0, 0), (w, h, 0.012)), M, pc)
        n.add(f'LeftHand_PropHoloPanel_{k + 1}', bm, holod, 'LeftHand', 'Props', center=pc)
        bm = bmesh.new()
        for (u, v, a, b) in ((0, h / 2, w, 0.01), (0, -h / 2, w, 0.01), (w / 2, 0, 0.01, h), (-w / 2, 0, 0.01, h)):
            merge(bm, place(box_bm((u, v, 0.008), (a, b, 0.008)), M, pc))
        gc = Vector((-w * 0.15, 0, 0.012))
        r = h * 0.28
        merge(bm, place(lathe_bm([(r * 0.45, 0.004), (r, 0.004), (r, -0.004), (r * 0.45, -0.004)], 16, gc), M, pc))
        for t in range(8):
            a = math.pi / 4 * t
            merge(bm, place(box_bm(gc + Vector((math.cos(a) * r * 1.15, math.sin(a) * r * 1.15, 0)), (r * 0.35, r * 0.35, 0.008),
                                   rot=Matrix.Rotation(a, 3, 'Z')), M, pc))
        if k == 0:
            for j in range(3):
                merge(bm, place(box_bm((w * 0.22, h * 0.22 - j * h * 0.2, 0.012), (w * 0.3, h * 0.07, 0.006)), M, pc))
        n.add(f'LeftHand_PropHoloIcons_{k + 1}', bm, holo, 'LeftHand', 'Props', center=pc)


# ------------------------------------------------------------------ scene
LINEUP = [('Shop', build_shop), ('Egg', build_egg), ('Trading', build_trading), ('Upgrades', build_upgrades),
          ('Pets', build_pets), ('Leaderboards', build_leaderboards), ('Tower_Guide', build_guide),
          ('Tower_Entrance', build_entrance), ('Codes', build_codes), ('Daily_Rewards', build_daily),
          ('Index', build_index), ('Settings', build_settings)]
SPACING, ROW_GAP = 1.7, 3.0


def lineup_offset(i):
    row = i // 6
    return Vector(((i % 6 - 2.5) * SPACING + (0.425 if row else -0.425), row * ROW_GAP, 0.0))


def build_camera_and_lights():
    sc = bpy.context.scene
    lc = bpy.data.collections.new('CameraAndLights')
    sc.collection.children.link(lc)
    target = Vector((0.0, 1.6, 0.9))
    cam = bpy.data.cameras.new('Camera_Lineup')
    cam.lens = 32
    co = bpy.data.objects.new('Camera_Lineup', cam)
    co.location = (0.0, -10.0, 4.6)
    co.rotation_euler = (target - co.location).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(co)
    sc.camera = co

    def area(name, loc, energy, size, color=(1, 1, 1)):
        li = bpy.data.lights.new(name, 'AREA')
        li.energy, li.size, li.color = energy, size, color
        o = bpy.data.objects.new(name, li)
        o.location = loc
        o.rotation_euler = (target - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        lc.objects.link(o)

    area('Light_Key', (-5.0, -6.0, 6.0), 2200, 6.0, (1.0, 0.96, 0.92))
    area('Light_Fill', (6.0, -5.0, 3.0), 900, 7.0, (0.92, 0.95, 1.0))
    area('Light_Rim', (0.0, 8.0, 5.0), 1200, 8.0)
    w = bpy.data.worlds.new('World_Studio')
    sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.6, 0.62, 0.68, 1)
    bg.inputs['Strength'].default_value = 0.5
    me = bpy.data.meshes.new('Ground')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=12)
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new('Ground_ShadowCatcher', me)
    g.is_shadow_catcher = True
    lc.objects.link(g)
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'


def export_fbx(npcs):
    """one FBX per NPC for Roblox Studio: centred on its feet, modifiers applied,
    names without the NPC prefix (so parts read Head, UpperTorso, Head_Hat..., Props...)"""
    out_dir = os.path.join(HERE, '..', 'exports')
    out_dir = os.path.join(os.path.abspath(out_dir if os.path.isdir(out_dir) else HERE), 'NPCs')
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for n in npcs:
        obs = [ob for ob, _ in n.parts]
        names = {ob: ob.name for ob in obs}
        for o in bpy.context.scene.objects:
            o.select_set(False)
        for ob in obs:
            ob.location -= n.off
            ob.select_set(True)
        for ob in obs:
            ob.name = names[ob][len(n.key) + 1:]
        path = os.path.join(out_dir, f'{n.key}_NPC.fbx')
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'}, use_mesh_modifiers=True,
                                 mesh_smooth_type='FACE', apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                                 add_leaf_bones=False, path_mode='STRIP', use_custom_props=True)
        for ob in obs:
            ob.name = names[ob]
            ob.location += n.off
            ob.select_set(False)
        paths.append(path)
    return out_dir, paths


def main():
    global NPCS_COLL
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    NPCS_COLL = bpy.data.collections.new('NPCs')
    sc.collection.children.link(NPCS_COLL)
    shared_materials()
    npcs = []
    for i, (key, fn) in enumerate(LINEUP):
        n = NPC(key, lineup_offset(i))
        fn(n)
        n.finish()
        npcs.append(n)
        tris = sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob, _ in n.parts)
        print(f'{key}_NPC: {len(n.parts)} parts, ~{tris} triangles (before bevels)')
    build_camera_and_lights()
    path = os.path.join(HERE, 'TowerOfPets_NPCs.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print('Saved:', path)
    out_dir, _ = export_fbx(npcs)
    print('Exported 12 FBX files to:', out_dir)


if __name__ == '__main__':
    main()
