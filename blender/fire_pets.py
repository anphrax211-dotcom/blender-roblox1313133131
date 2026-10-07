"""FIRE PETS - Ashrat, Cinderkit, Flarecat and Smoulderat, built from the fire-pet turnaround sheet.

Stylised, game-ready pets: chunky bodies, short legs, smooth-shaded simple meshes, flat colour
materials (fire colours are slightly emissive so they stay bright and readable).

Scene layout (1 unit = 1 m, Z up, every pet faces -Y and stands on z = 0):
    PETS/<Pet>            one collection per pet; every part is its own editable mesh, parented to the
                          `<Pet>_Root` empty (move the empty to move the pet)
    STUDIO                ground plane, soft area lights (neutral grey world)
    CAMERAS/<Pet>_Cams    orthographic CAM_<Pet>_Front / _Side / _Back (side camera looks from the pet's
                          left, +X, so the head is on the left like the reference) + two overview cameras
    LABELS                pet names and FRONT / SIDE / BACK markers lying on the ground around each pet

    Ashrat x = -3.6   Cinderkit x = -1.2   Flarecat x = 1.2   Smoulderat x = 3.6

Part names: <Pet>_Body, _Head, _Ear_L/_R, _Leg_FL/FR/BL/BR, _Paw_FL/FR/BL/BR, _Tail, _Eye_L/_R,
_Nose, _Mouth/_Teeth, _Whiskers, plus the fire features (_FireCracks, _FlameTuft, _FlameMane,
_ChestRuff, _FlameMarkings, _LavaFissures, _BackCrystals, ...). L/R are the pet's own left/right
(left = +X).

Run in Blender (Scripting tab -> Run Script) or headless:
    python3 fire_pets.py                 (with the `bpy` pip module) -> saves FirePets.blend
    python3 fire_pets.py --render ../previews   also renders every turnaround camera + a contact sheet
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
PET_X = {'Ashrat': -3.6, 'Cinderkit': -1.2, 'Flarecat': 1.2, 'Smoulderat': 3.6}
CAM_H = 0.55          # height of the orthographic turnaround cameras
CAM_SCALE = 2.0       # ortho scale (same for every pet so their sizes compare 1:1)


# ------------------------------------------------------------------ materials
MATS = {}


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def material(name, hexcol, rough=0.5, emit=0.0, coat=0.0, vcol=False):
    m = bpy.data.materials.new(name)
    rgb = srgb(hexcol)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.15
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    if vcol:      # colour gradient stored in the mesh's 'Col' colour attribute
        a = nt.nodes.new('ShaderNodeVertexColor')
        a.layer_name = 'Col'
        nt.links.new(a.outputs['Color'], b.inputs['Base Color'])
        nt.links.new(a.outputs['Color'], b.inputs['Emission Color'])
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def build_materials():
    material('Fur_Charcoal', '#3b3739', 0.75)           # Ashrat
    material('Fur_Soot', '#29262a', 0.75)               # Cinderkit
    material('Fur_PaleGold', '#f3ddb2', 0.7)            # Flarecat
    material('Fur_DarkCharcoal', '#332f33', 0.8)        # Smoulderat
    material('Fur_EmberBelly', '#9a5530', 0.75)         # Ashrat / Smoulderat chest
    material('Paw_Orange', '#f7952a', 0.55)
    material('Paw_Amber', '#ffad22', 0.55)
    material('Paw_Red', '#d8392a', 0.55)
    material('Fire_Yellow', '#ffc21f', 0.45, emit=0.35)
    material('Fire_Orange', '#ff7012', 0.45, emit=0.45)
    material('Fire_Red', '#e2401c', 0.45, emit=0.5)
    material('Fire_Gradient', '#ff8a1e', 0.45, emit=0.55, vcol=True)
    material('Glow_Crack', '#ff7a12', 0.4, emit=1.6)
    material('Lava_Edge', '#f0451a', 0.4, emit=2.0)
    material('Lava_Core', '#ffd248', 0.4, emit=4.0)
    material('Crystal_Red', '#d9301e', 0.2, emit=0.35, coat=0.6)
    material('Crystal_Orange', '#ff6a1c', 0.2, emit=0.45, coat=0.6)
    material('Ear_Orange', '#f2853a', 0.6)
    material('Ear_Pink', '#f2a29c', 0.6)
    material('Eye_Black', '#141011', 0.25, coat=0.5)
    material('Eye_Iris', '#ee4a1c', 0.25, emit=0.3, coat=0.5)
    material('Eye_IrisGlow', '#ffb31e', 0.25, emit=0.5, coat=0.5)
    material('Eye_Highlight', '#ffffff', 0.2, emit=1.0)
    material('Nose_Dark', '#2a1c1d', 0.4)
    material('Mouth_Dark', '#3a1416', 0.5)
    material('Tongue_Pink', '#f07888', 0.45)
    material('Tooth_White', '#f5f1e8', 0.35)
    material('Whisker_Light', '#9a9696', 0.6)
    material('Whisker_Tan', '#b88e62', 0.6)
    material('Ground_Studio', '#8c8c8f', 0.9)
    material('Label_Dark', '#3c3c40', 0.8)


# ------------------------------------------------------------------ mesh primitives (all return bmesh)
def frame(n, up=Z):
    """3x3 matrix whose columns are (right, up, n) for a surface facing direction n"""
    n = n.normalized()
    r = up.cross(n)
    if r.length < 1e-6:
        r = X.copy()
    r.normalize()
    return Matrix((r, n.cross(r), n)).transposed()


def ellipsoid(c, r, M=None, seg=16, rings=10, ex=2.0):
    """superellipsoid (ex > 2 = boxier) with radii r, rotated by M, centred at c"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        if ex != 2.0:
            d *= (abs(d.x) ** ex + abs(d.y) ** ex + abs(d.z) ** ex) ** (-1 / ex)
        p = Vector((d.x * r[0], d.y * r[1], d.z * r[2]))
        v.co = (M @ p if M else p) + Vector(c)
    return bm


def catmull(pts, n_per=6):
    P = [Vector(p) for p in pts]
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(n_per):
            t = k / n_per
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1].copy())
    return out


def tube(pts, radii, seg=12, hint=Z, ex=2.0, colors=None):
    """loft rings along a path. radii[i] = (a, b): a across the path, b along `hint`
    (b ~ the flat direction). A zero radius makes a pointed pole; open ends get rounded caps."""
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new('Col') if colors else None
    n = len(pts)
    T = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    N = hint.cross(T[0])
    if N.length < 1e-6:
        N = X.cross(T[0])
    N.normalize()
    rings = []
    for i in range(n):
        if i:
            M2 = N - N.dot(T[i]) * T[i]
            if M2.length > 1e-6:
                N = M2.normalized()
        B = T[i].cross(N)
        a, b = radii[i]
        if max(a, b) < 1e-5:
            ring = [bm.verts.new(pts[i])]
        else:
            ring = []
            for k in range(seg):
                th = 2 * math.pi * k / seg
                c, s = math.cos(th), math.sin(th)
                c = math.copysign(abs(c) ** (2 / ex), c)
                s = math.copysign(abs(s) ** (2 / ex), s)
                ring.append(bm.verts.new(pts[i] + N * (a * c) + B * (b * s)))
        if col:
            for v in ring:
                v[col] = (*colors[i], 1.0)
        rings.append(ring)
    for i in range(n - 1):
        r0, r1 = rings[i], rings[i + 1]
        if len(r0) > 1 and len(r1) > 1:
            for k in range(seg):
                bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
        elif len(r1) > 1:
            for k in range(seg):
                bm.faces.new((r0[0], r1[(k + 1) % seg], r1[k]))
        elif len(r0) > 1:
            for k in range(seg):
                bm.faces.new((r0[k], r0[(k + 1) % seg], r1[0]))
    for idx, sgn in ((0, -1), (n - 1, 1)):            # rounded caps on open ends
        ring = rings[idx]
        if len(ring) > 1:
            a, b = radii[idx]
            pole = bm.verts.new(pts[idx] + T[idx] * sgn * min(a, b) * 0.6)
            if col:
                pole[col] = (*colors[idx], 1.0)
            for k in range(seg):
                bm.faces.new((ring[k], ring[(k + 1) % seg], pole))
    return bm


def body_bm(y_rear, y_front, z_rear, z_front, a, b, taper=0.1, q=2.4, ex=2.3, n=18, seg=24):
    """chunky rounded body loaf along Y (rear -> front)"""
    pts, radii = [], []
    for i in range(n + 1):
        t = (1 - math.cos(math.pi * i / n)) / 2
        f = max(0.0, 1 - abs(2 * t - 1) ** q) ** (1 / q)
        k = 1 - taper * t
        pts.append(Vector((0, y_rear + (y_front - y_rear) * t, z_rear + (z_front - z_rear) * t)))
        radii.append((a * f * k, b * f * k))
    return tube(pts, radii, seg, hint=Z, ex=ex)


def tongue(base, direction, length, width, flat=0.45, bend=Vector(), hint=Y, seg=8, n=3):
    """one flame tongue: swells from the base then tapers to a sharp tip, curving by `bend`"""
    d = direction.normalized()
    ctrl = [base, base + d * length * 0.35 + bend * 0.15, base + d * length * 0.7 + bend * 0.55,
            base + d * length + bend]
    pts = catmull(ctrl, n)
    radii = []
    for i in range(len(pts)):
        t = i / (len(pts) - 1)
        r = 0.6 + 0.4 * math.sin(t / 0.3 * math.pi / 2) if t < 0.3 else ((1 - t) / 0.7) ** 0.9
        radii.append((width * r, width * r * flat))
    return tube(pts, radii, seg, hint=hint)


def crystal(base, n, h, r, spin=0.0, sides=6):
    """faceted hexagonal crystal standing on `base` along direction n"""
    M = frame(n) @ Matrix.Rotation(spin, 3, 'Z')
    bm = bmesh.new()
    lo, hi = [], []
    for k in range(sides):
        a = 2 * math.pi * k / sides
        lo.append(bm.verts.new(base + M @ Vector((math.cos(a) * r * 0.8, math.sin(a) * r * 0.8, -0.04))))
        hi.append(bm.verts.new(base + M @ Vector((math.cos(a) * r, math.sin(a) * r, h * 0.62))))
    tip = bm.verts.new(base + M @ Vector((0, 0, h)))
    bm.faces.new(lo[::-1])
    for k in range(sides):
        bm.faces.new((lo[k], lo[(k + 1) % sides], hi[(k + 1) % sides], hi[k]))
        bm.faces.new((hi[k], hi[(k + 1) % sides], tip))
    return bm


def mirror(bm):
    """copy of a bmesh mirrored to the other side (x -> -x)"""
    m = bm.copy()
    for v in m.verts:
        v.co.x = -v.co.x
    bmesh.ops.reverse_faces(m, faces=m.faces)
    return m


# ------------------------------------------------------------------ surface helpers
def cast(bvh, c, d):
    """point + outward normal where the ray from far outside along -d toward c hits the surface"""
    d = d.normalized()
    loc, nor, _, _ = bvh.ray_cast(c + d * 4.0, -d)
    if loc is None:
        return c + d * 0.01, d
    if nor.dot(d) < 0:
        nor = -nor
    return loc, nor


def _orient_to(bm, c):
    """make the faces of an open surface patch point away from the projection centre"""
    bm.faces.ensure_lookup_table()
    if bm.faces:
        f = bm.faces[len(bm.faces) // 2]
        if f.normal.dot(f.calc_center_median() - c) < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)


def flame_outline():
    """closed 2D flame silhouette, base at (0,0), tip at about (0,1)"""
    pts = [(0.0, 0.0), (0.2, 0.04), (0.3, 0.18), (0.3, 0.36), (0.22, 0.55), (0.12, 0.72), (0.07, 0.88),
           (0.1, 1.0), (-0.04, 0.86), (-0.1, 0.72), (-0.24, 0.74), (-0.2, 0.56), (-0.3, 0.36),
           (-0.28, 0.16), (-0.18, 0.03), (0.0, 0.0)]
    return catmull(pts, 3)[:-1]


def decal(bvh, c, d, outline, size, angle=0.0, offset=0.005, up=Z, cuts=1):
    """2D outline wrapped onto a surface around the hit point of direction d"""
    hit, n = cast(bvh, c, d)
    M = frame(n, up)
    r, u = M.col[0], M.col[1]
    ca, sa = math.cos(angle), math.sin(angle)
    bm = bmesh.new()
    vs = [bm.verts.new(hit + r * ((x * ca - y * sa) * size) + u * ((x * sa + y * ca) * size)) for x, y in outline]
    es = [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es, normal=n)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        dd = (v.co - c).normalized()
        h, _ = cast(bvh, c, dd)
        v.co = h + dd * offset
    _orient_to(bm, c)
    return bm


def ribbon(bvh, c, dirs, width, offset=0.004, taper=True):
    """thin strip following a path of directions over a surface (cracks, fissures)"""
    hits = [cast(bvh, c, d) for d in dirs]
    pts = [h + d.normalized() * offset for (h, _), d in zip(hits, dirs)]
    bm = bmesh.new()
    left, right = [], []
    n = len(pts)
    for i in range(n):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        side = hits[i][1].cross(t).normalized()
        k = i / (n - 1)
        w = width * (math.sin(math.pi * k) ** 0.5 if taper else 1.0) * 0.5 + width * 0.08
        left.append(bm.verts.new(pts[i] + side * w))
        right.append(bm.verts.new(pts[i] - side * w))
    for i in range(n - 1):
        bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
    _orient_to(bm, c)
    return bm


def crack_walk(rng, start, heading, steps, step, wobble=0.5, branch=0.0, depth=0, zmin=-0.4, ymin=-9.0):
    """random walk over the unit sphere of directions; returns a list of paths (lists of Vectors)"""
    d = start.normalized()
    h = (heading - heading.dot(d) * d).normalized()
    path, paths = [d.copy()], []
    for _ in range(steps):
        h = Matrix.Rotation(rng.uniform(-wobble, wobble), 3, d) @ h
        d = (d + h * step).normalized()
        h = (h - h.dot(d) * d).normalized()
        if d.z < zmin or d.y < ymin:
            break
        path.append(d.copy())
        if depth < 2 and rng.random() < branch:
            bh = Matrix.Rotation(rng.choice((-1, 1)) * rng.uniform(0.6, 1.1), 3, d) @ h
            paths += crack_walk(rng, d, bh, max(2, steps // 2), step * 0.9, wobble, branch * 0.6,
                                depth + 1, zmin, ymin)
    if len(path) > 2:
        paths.append(path)
    return paths


# ------------------------------------------------------------------ pet assembly
class Pet:
    def __init__(self, name, parent_coll):
        self.name = name
        self.coll = bpy.data.collections.new(name)
        parent_coll.children.link(self.coll)
        self.root = bpy.data.objects.new(f'{name}_Root', None)
        self.root.empty_display_type = 'PLAIN_AXES'
        self.root.empty_display_size = 0.4
        self.coll.objects.link(self.root)
        self.bvh, self.center = {}, {}

    def obj(self, part, pieces, smooth=True):
        """pieces: [(bmesh, material) or (bmesh, material, smooth)] -> one object <Pet>_<part>"""
        bm, mats = bmesh.new(), []
        for piece in pieces:
            pbm, mname = piece[0], piece[1]
            sm = piece[2] if len(piece) > 2 else smooth
            if all(e.is_manifold for e in pbm.edges):
                bmesh.ops.recalc_face_normals(pbm, faces=pbm.faces)
            if mname not in mats:
                mats.append(mname)
            me = bpy.data.meshes.new('_tmp')
            pbm.to_mesh(me)
            pbm.free()
            n0 = len(bm.faces)
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
            for f in list(bm.faces)[n0:]:
                f.material_index = mats.index(mname)
                f.smooth = sm
        self.bvh[part] = BVHTree.FromBMesh(bm)
        lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
        hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
        c = (lo + hi) / 2
        self.center[part] = c
        for v in bm.verts:
            v.co -= c
        name = f'{self.name}_{part}'
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for m in mats:
            me.materials.append(MATS[m])
        if 'Col' in me.color_attributes:
            me.color_attributes.active_color_name = 'Col'
            me.color_attributes.render_color_index = me.color_attributes.active_color_index
        ob = bpy.data.objects.new(name, me)
        ob.location = c
        ob.parent = self.root
        self.coll.objects.link(ob)
        return ob

    def pair(self, part, pieces_l, smooth=True, sep='_'):
        """left (+X) part plus its mirror as <part>_L / <part>_R"""
        pieces_r = [(mirror(p[0]),) + tuple(p[1:]) for p in pieces_l]
        self.obj(part + sep + 'L', pieces_l, smooth)
        self.obj(part + sep + 'R', pieces_r, smooth)

    def place(self, x):
        self.root.location = (x, 0, 0)


# ---- shared features
def legs_and_paws(pet, fur, paw, front, back, thigh=None):
    """front/back: (x, y, top_z, radius); paws stand on z = 0; thigh = haunch radii"""
    for tag, (x, y, top, r) in (('F', front), ('B', back)):
        pieces = [(tube([Vector((x, y, top)), Vector((x, y - 0.005, (top + 0.08) / 2)),
                         Vector((x, y - 0.01, 0.07))], [(r, r), (r * 0.94, r * 0.94), (r * 0.9, r * 0.9)], 14), fur)]
        if tag == 'B' and thigh:
            pieces.append((ellipsoid((x - 0.005, y + 0.03, top - 0.02), thigh, seg=18, rings=12), fur))
        pet.pair(f'Leg_{tag}', pieces, sep='')
        pw = r * 1.18
        paw_pieces = [(ellipsoid((x, y - 0.025, pw * 0.58), (pw, pw * 1.22, pw * 0.58), seg=18, rings=10, ex=2.3), paw)]
        for dx in (-0.55, 0.0, 0.55):
            tr = pw * 0.4
            paw_pieces.append((ellipsoid((x + dx * pw, y - 0.025 - pw * 1.0, tr * 0.95), (tr, tr, tr * 0.95),
                                         seg=12, rings=8), paw))
        pet.pair(f'Paw_{tag}', paw_pieces, sep='')


def eyes(pet, c, d, s, head='Head'):
    """big glossy eyes: black rim, red-orange iris with a glowing lower half, pupil, two highlights"""
    hit, n = cast(pet.bvh[head], c, d)
    M = frame(n)
    r, u = M.col[0], M.col[1]

    def at(dr, du, dn):
        return hit + r * (dr * s) + u * (du * s) + n * ((dn - 0.18) * s)

    pieces = [
        (ellipsoid(at(0, 0, 0.0), (s, s * 1.12, s * 0.5), M), 'Eye_Black'),
        (ellipsoid(at(0, -0.04, 0.1), (s * 0.84, s * 0.95, s * 0.45), M), 'Eye_Iris'),
        (ellipsoid(at(0, -0.34, 0.3), (s * 0.6, s * 0.48, s * 0.3), M), 'Eye_IrisGlow'),
        (ellipsoid(at(0, 0.06, 0.36), (s * 0.36, s * 0.48, s * 0.3), M), 'Eye_Black'),
        (ellipsoid(at(0.3, 0.36, 0.6), (s * 0.22, s * 0.22, s * 0.12), M, seg=12, rings=8), 'Eye_Highlight'),
        (ellipsoid(at(-0.3, -0.26, 0.58), (s * 0.11, s * 0.11, s * 0.07), M, seg=10, rings=6), 'Eye_Highlight'),
    ]
    pet.obj('Eye_L', pieces)
    # mirror the left eye but keep the highlights on the same screen side
    hit, n = cast(pet.bvh[head], c, Vector((-d.x, d.y, d.z)))
    M = frame(n)
    r, u = M.col[0], M.col[1]
    pieces = [
        (ellipsoid(at(0, 0, 0.0), (s, s * 1.12, s * 0.5), M), 'Eye_Black'),
        (ellipsoid(at(0, -0.04, 0.1), (s * 0.84, s * 0.95, s * 0.45), M), 'Eye_Iris'),
        (ellipsoid(at(0, -0.34, 0.3), (s * 0.6, s * 0.48, s * 0.3), M), 'Eye_IrisGlow'),
        (ellipsoid(at(0, 0.06, 0.36), (s * 0.36, s * 0.48, s * 0.3), M), 'Eye_Black'),
        (ellipsoid(at(0.3, 0.36, 0.6), (s * 0.22, s * 0.22, s * 0.12), M, seg=12, rings=8), 'Eye_Highlight'),
        (ellipsoid(at(-0.3, -0.26, 0.58), (s * 0.11, s * 0.11, s * 0.07), M, seg=10, rings=6), 'Eye_Highlight'),
    ]
    pet.obj('Eye_R', pieces)


def round_ears(pet, c, offset, size, fur, inner):
    """big rounded rat ears: a thick disc with an orange inner disc on the front"""
    base = c + offset
    n = Vector((0.42, -1.0, 0.12)).normalized()
    M = frame(n, Vector((0.25, 0, 1)))
    pet.pair('Ear', [
        (ellipsoid(base, (size, size * 1.02, size * 0.26), M, seg=24, rings=12), fur),
        (ellipsoid(base + n * size * 0.13 - M.col[1] * size * 0.06, (size * 0.72, size * 0.74, size * 0.16), M,
                   seg=24, rings=12), inner),
    ])


def cat_ears(pet, base, tip, width, fur, inner, inner2=None):
    """pointed cat ear: flattened cone, inner cone poking out of the front"""
    n = Vector((0.3, -1.0, 0.05)).normalized()
    pts = [base + (tip - base) * (i / 6) for i in range(7)]
    rad = [(width * (1 - i / 6) ** 0.8, width * 0.42 * (1 - i / 6) ** 0.8) for i in range(7)]
    pieces = [(tube(pts, rad, 14, hint=n), fur)]
    ib, it = base + n * 0.035 + Z * 0.02, tip + (base - tip) * 0.16 + n * 0.012
    pts = [ib + (it - ib) * (i / 6) for i in range(7)]
    rad = [(width * 0.66 * (1 - i / 6) ** 0.8, width * 0.2 * (1 - i / 6) ** 0.8) for i in range(7)]
    pieces.append((tube(pts, rad, 14, hint=n), inner))
    if inner2:
        ib2, it2 = ib + n * 0.015 + Z * 0.01, it + (ib - it) * 0.3 + n * 0.008
        pts = [ib2 + (it2 - ib2) * (i / 6) for i in range(7)]
        rad = [(width * 0.38 * (1 - i / 6) ** 0.8, width * 0.12 * (1 - i / 6) ** 0.8) for i in range(7)]
        pieces.append((tube(pts, rad, 12, hint=n), inner2))
    pet.pair('Ear', pieces)


def curled_tail(pet, start, scale, r0, r1):
    """long fiery rat tail: goes back, rises and curls forward into a spiral (orange -> yellow)"""
    ctrl = [(0, 0, 0), (0.02, 0.16, -0.01), (0.05, 0.34, 0.05), (0.09, 0.48, 0.2), (0.13, 0.5, 0.4),
            (0.15, 0.38, 0.52), (0.16, 0.22, 0.48), (0.16, 0.17, 0.34), (0.16, 0.25, 0.27), (0.16, 0.33, 0.32)]
    pts = [start + Vector(p) * scale for p in catmull(ctrl, 5)]
    stops = [(0.0, srgb('#d8461c')), (0.3, srgb('#ff7a18')), (0.65, srgb('#ffa424')), (1.0, srgb('#ffd23a'))]

    def grad(t):
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t <= t1:
                k = (t - t0) / (t1 - t0)
                return tuple(a + (b - a) * k for a, b in zip(c0, c1))
        return stops[-1][1]
    n = len(pts)
    radii, cols = [], []
    for i in range(n):
        t = i / (n - 1)
        r = r0 + (r1 - r0) * math.sin(min(t / 0.55, 1) * math.pi / 2) if t < 0.55 else r1 * (1 - (t - 0.55) / 0.45 * 0.75)
        radii.append((r, r))
        cols.append(grad(t))
    pet.obj('Tail', [(tube(pts, radii, 14, hint=X, colors=cols), 'Fire_Gradient')])


def flame_tail(pet, base, scale):
    """cat flame tail: large yellow flame with orange and red cores, rising from the rump"""
    s = scale
    top = base + Vector((0, 0.1, 0.1)) * s
    pieces = [(tube(catmull([base - Vector((0, 0.05, 0)) * s, base + Vector((0, 0.05, 0.03)) * s, top], 3),
                    [(0.05 * s, 0.05 * s)] * 2 + [(0.06 * s, 0.06 * s)] * 5, 12), 'Fire_Red')]
    bigs = [  # (direction, length, width, bend): tips curl like the reference flame
        (Vector((0, 0.35, 1)), 0.58, 0.2, Vector((0, -0.2, 0.0))),
        (Vector((0, 1.0, 0.6)), 0.42, 0.16, Vector((0, 0.02, 0.18))),
        (Vector((0.45, 0.6, 0.8)), 0.36, 0.13, Vector((0, -0.05, 0.1))),
        (Vector((-0.45, 0.6, 0.8)), 0.36, 0.13, Vector((0, -0.05, 0.1))),
        (Vector((0, 1.0, -0.05)), 0.26, 0.11, Vector((0, 0.05, 0.12))),
    ]
    for d, L, w, b in bigs:
        pieces.append((tongue(top, d, L * s, w * s, 0.6, b * s, hint=X, seg=12), 'Fire_Yellow'))
    for d, L, w, b in bigs[:4]:      # thicker, shorter orange layer shows through both sides
        pieces.append((tongue(top, d, L * s * 0.74, w * s * 0.62, 1.25, b * s * 0.74, hint=X, seg=12), 'Fire_Orange'))
    pieces.append((tongue(top, Vector((0, 0.5, 1)), 0.25 * s, 0.1 * s, 1.45, Vector((0, -0.04, 0)) * s,
                          hint=X, seg=12), 'Fire_Red'))
    pet.obj('Tail', pieces)


def whiskers(pet, c, d, mat, length=0.17):
    hit, n = cast(pet.bvh['Head'], c, d)
    pieces = []
    for k, ang in enumerate((-0.28, 0.0, 0.26)):
        a = hit - n * 0.01
        out = (Vector((1, -0.25, ang)).normalized())
        b = a + out * length
        mid = (a + b) / 2 + Vector((0, 0, -0.01 + ang * 0.02))
        pts = catmull([a, mid, b], 3)
        rad = [(0.0045 * (1 - 0.6 * i / (len(pts) - 1)),) * 2 for i in range(len(pts))]
        pieces.append((tube(pts, rad, 6), mat))
    pieces += [(mirror(p[0]), p[1]) for p in pieces]
    pet.obj('Whiskers', pieces)


def flame_markings(pet, part, c, spots, mat='Fire_Orange', mat2=None):
    """flame-shaped decals: spots = [(direction, size, angle)]; optional mirrored copy"""
    out = flame_outline()
    pieces = []
    for d, size, ang in spots:
        pieces.append((decal(pet.bvh[part], c, d, out, size, ang), mat))
        if mat2:
            inner = [(x * 0.55, y * 0.6 + 0.02) for x, y in out]
            pieces.append((decal(pet.bvh[part], c, d, inner, size, ang, offset=0.008), mat2))
    return pieces


# ------------------------------------------------------------------ the four pets
def build_ashrat(pc):
    p = Pet('Ashrat', pc)
    fur = 'Fur_Charcoal'
    p.obj('Body', [(body_bm(0.44, -0.24, 0.36, 0.4, 0.27, 0.235), fur)])
    hc = Vector((0, -0.36, 0.57))
    p.obj('Head', [
        (ellipsoid(hc, (0.3, 0.27, 0.265), seg=28, rings=16, ex=2.2), fur),
        (ellipsoid((0, -0.6, 0.48), (0.16, 0.17, 0.125), seg=22, rings=12), fur),
        (ellipsoid((0, -0.47, 0.41), (0.14, 0.11, 0.09), seg=18, rings=10), fur),
    ])
    round_ears(p, hc, Vector((0.22, 0.05, 0.24)), 0.165, fur, 'Ear_Orange')
    legs_and_paws(p, fur, 'Paw_Orange', (0.16, -0.12, 0.3, 0.082), (0.19, 0.26, 0.26, 0.08),
                  thigh=(0.11, 0.16, 0.14))
    eyes(p, hc, Vector((0.5, -1.0, 0.08)), 0.078)
    sc = Vector((0, -0.6, 0.48))
    hit, n = cast(p.bvh['Head'], sc, Vector((0, -1, 0.5)))
    p.obj('Nose', [(ellipsoid(hit, (0.034, 0.026, 0.024), frame(n)), 'Nose_Dark')])
    teeth = []
    for x in (-0.017, 0.017):
        th, tn = cast(p.bvh['Head'], sc, Vector((x * 2, -1, -0.62)))
        teeth.append((ellipsoid(th + tn * 0.006 - Z * 0.02, (0.015, 0.007, 0.024), frame(tn), seg=12, rings=8,
                                ex=3.5), 'Tooth_White'))
    p.obj('Teeth', teeth)
    mh, mn = cast(p.bvh['Head'], sc, Vector((0, -1, -0.28)))
    p.obj('Mouth', [(ellipsoid(mh, (0.04, 0.01, 0.006), frame(mn), seg=12, rings=6), 'Mouth_Dark')])
    whiskers(p, sc, Vector((0.8, -0.7, 0.0)), 'Whisker_Light')
    curled_tail(p, Vector((0, 0.4, 0.35)), 1.0, 0.05, 0.072)
    # chest patch + subtle glowing cracks and cheek flame swirls
    bc = Vector((0, 0.1, 0.38))
    p.obj('ChestPatch', [(decal(p.bvh['Body'], bc, Vector((0, -1, -0.35)),
                                [(math.cos(a) * 0.5, math.sin(a) * 0.62) for a in
                                 [2 * math.pi * k / 24 for k in range(24)]], 0.28, offset=0.004), 'Fur_EmberBelly')])
    rng = random.Random(7)
    cracks = []
    for d, h in ((Vector((1, 0.55, 0.5)), Vector((0, -0.4, -1))), (Vector((1, -0.15, 0.25)), Vector((0, 0.3, -1))),
                 (Vector((0.85, 0.9, -0.05)), Vector((0, -1, -0.6))), (Vector((0.5, 0.3, 1)), Vector((1, 0.2, -0.3)))):
        for path in crack_walk(rng, d, h, 7, 0.07, 0.7, 0.3, zmin=-0.3):
            cracks.append((ribbon(p.bvh['Body'], bc, path, 0.016), 'Glow_Crack'))
    cracks += [(mirror(c[0]), c[1]) for c in cracks]
    leg_c = p.center['Leg_BL']
    cracks += flame_markings(p, 'Leg_BL', leg_c, [(Vector((1, 0.1, 0.2)), 0.11, 0.2)], 'Glow_Crack')
    cracks += [(mirror(cracks[-1][0]), 'Glow_Crack')]
    head_marks = flame_markings(p, 'Head', hc, [(Vector((0.62, -0.75, -0.2)), 0.085, 0.9)], 'Glow_Crack')
    head_marks += [(mirror(head_marks[0][0]), 'Glow_Crack')]
    p.obj('FireCracks', cracks + head_marks)
    return p


def build_cinderkit(pc):
    p = Pet('Cinderkit', pc)
    fur = 'Fur_Soot'
    p.obj('Body', [(body_bm(0.42, -0.22, 0.41, 0.45, 0.24, 0.215), fur)])
    hc = Vector((0, -0.36, 0.64))
    p.obj('Head', [
        (ellipsoid(hc, (0.29, 0.255, 0.255), seg=28, rings=16, ex=2.2), fur),
        (ellipsoid((0.15, -0.44, 0.55), (0.13, 0.12, 0.11), seg=18, rings=10), fur),
        (ellipsoid((-0.15, -0.44, 0.55), (0.13, 0.12, 0.11), seg=18, rings=10), fur),
        (ellipsoid((0, -0.56, 0.56), (0.11, 0.08, 0.075), seg=18, rings=10), fur),
    ])
    cat_ears(p, hc + Vector((0.16, 0.04, 0.17)), hc + Vector((0.27, 0.06, 0.45)), 0.115, fur, 'Fire_Orange',
             'Fire_Yellow')
    legs_and_paws(p, fur, 'Paw_Amber', (0.14, -0.12, 0.34, 0.077), (0.16, 0.25, 0.3, 0.076),
                  thigh=(0.1, 0.15, 0.13))
    eyes(p, hc, Vector((0.48, -1.0, 0.12)), 0.08)
    mc = Vector((0, -0.56, 0.56))
    hit, n = cast(p.bvh['Head'], mc, Vector((0, -1, 0.6)))
    p.obj('Nose', [(ellipsoid(hit, (0.028, 0.02, 0.018), frame(n)), 'Nose_Dark')])
    mh, mn = cast(p.bvh['Head'], mc, Vector((0, -1, -0.45)))
    p.obj('Mouth', [(ellipsoid(mh, (0.04, 0.026, 0.012), frame(mn), seg=14, rings=8), 'Mouth_Dark'),
                    (ellipsoid(mh + mn * 0.008 - Z * 0.012, (0.024, 0.02, 0.009), frame(mn), seg=12, rings=8),
                     'Tongue_Pink')])
    whiskers(p, mc, Vector((0.9, -0.6, -0.1)), 'Whisker_Light')
    # forehead flame tuft
    tb = hc + Vector((0, -0.02, 0.22))
    tuft = []
    for d, L, w, mat in ((Vector((0, 0.25, 1)), 0.26, 0.085, 'Fire_Yellow'), (Vector((0.6, 0.2, 1)), 0.18, 0.065, 'Fire_Orange'),
                         (Vector((-0.6, 0.2, 1)), 0.18, 0.065, 'Fire_Orange'), (Vector((0, -0.45, 1)), 0.15, 0.06, 'Fire_Orange'),
                         (Vector((0.3, 0.8, 0.7)), 0.17, 0.06, 'Fire_Yellow'), (Vector((-0.3, 0.8, 0.7)), 0.17, 0.06, 'Fire_Yellow')):
        tuft.append((tongue(tb, d, L, w, 0.55, Vector((0, -0.04, 0)), hint=Y), mat))
    tuft.append((tongue(tb, Vector((0, 0.15, 1)), 0.16, 0.055, 1.1, hint=Y), 'Fire_Red'))
    p.obj('FlameTuft', tuft)
    # yellow flame chest ruff under the chin
    ruff = []
    for x in (-0.13, -0.065, 0.0, 0.065, 0.13):
        ruff.append((tongue(Vector((x, -0.36, 0.43)), Vector((x * 0.9, -0.75, -1)), 0.115 - abs(x) * 0.25, 0.068, 0.4,
                            hint=Y), 'Fire_Yellow'))
    ruff.append((tongue(Vector((0, -0.38, 0.43)), Vector((0, -0.3, -1)), 0.07, 0.04, 0.9, hint=Y), 'Fire_Orange'))
    p.obj('ChestRuff', ruff)
    flame_tail(p, Vector((0, 0.4, 0.45)), 1.0)
    bc = Vector((0, 0.1, 0.42))
    marks = flame_markings(p, 'Body', bc, [(Vector((1, 0.55, 0.35)), 0.12, 0.25), (Vector((1, -0.2, 0.15)), 0.1, -0.2),
                                          (Vector((0.6, 0.2, 1)), 0.09, 0.4)], 'Fire_Orange', 'Fire_Yellow')
    for leg in ('Leg_FL', 'Leg_BL'):
        marks += flame_markings(p, leg, p.center[leg], [(Vector((1, -0.3, 0.1)), 0.09, 0.0)], 'Fire_Orange')
    marks += [(mirror(m[0]), m[1]) for m in marks]
    p.obj('FlameMarkings', marks)
    return p


def build_flarecat(pc):
    p = Pet('Flarecat', pc)
    fur = 'Fur_PaleGold'
    p.obj('Body', [(body_bm(0.45, -0.24, 0.43, 0.47, 0.25, 0.225), fur)])
    hc = Vector((0, -0.38, 0.67))
    p.obj('Head', [
        (ellipsoid(hc, (0.28, 0.25, 0.25), seg=28, rings=16, ex=2.2), fur),
        (ellipsoid((0.14, -0.46, 0.585), (0.12, 0.11, 0.1), seg=18, rings=10), fur),
        (ellipsoid((-0.14, -0.46, 0.585), (0.12, 0.11, 0.1), seg=18, rings=10), fur),
        (ellipsoid((0, -0.575, 0.59), (0.105, 0.075, 0.072), seg=18, rings=10), fur),
    ])
    cat_ears(p, hc + Vector((0.15, 0.05, 0.16)), hc + Vector((0.26, 0.07, 0.44)), 0.115, fur, 'Ear_Pink')
    legs_and_paws(p, fur, 'Paw_Orange', (0.145, -0.13, 0.36, 0.079), (0.165, 0.27, 0.32, 0.079),
                  thigh=(0.105, 0.155, 0.135))
    eyes(p, hc, Vector((0.48, -1.0, 0.12)), 0.077)
    mc = Vector((0, -0.575, 0.59))
    hit, n = cast(p.bvh['Head'], mc, Vector((0, -1, 0.6)))
    p.obj('Nose', [(ellipsoid(hit, (0.028, 0.02, 0.018), frame(n)), 'Ear_Pink')])
    mh, mn = cast(p.bvh['Head'], mc, Vector((0, -1, -0.45)))
    p.obj('Mouth', [(ellipsoid(mh, (0.04, 0.026, 0.012), frame(mn), seg=14, rings=8), 'Mouth_Dark'),
                    (ellipsoid(mh + mn * 0.008 - Z * 0.012, (0.024, 0.02, 0.009), frame(mn), seg=12, rings=8),
                     'Tongue_Pink')])
    whiskers(p, mc, Vector((0.9, -0.6, -0.1)), 'Whisker_Tan')
    # flame mane: two rings of tongues around the face, crest on top, bib below
    mane = []
    rc = hc + Vector((0, 0.1, -0.02))
    for k in range(16):
        a = 2 * math.pi * k / 16
        ca, sa = math.cos(a), math.sin(a)
        if sa < -0.75:
            continue                                          # bottom is the chest bib
        radial = Vector((ca, 0, sa))
        base = rc + Vector((ca * 0.22, 0, sa * 0.21))
        L = 0.2 + 0.06 * max(sa, 0)
        mane.append((tongue(base, radial + Y * 1.0, L * 1.1, 0.09, 0.5, Z * 0.05 * ca * ca, hint=Y), 'Fire_Orange'))
        b3 = rc + Vector((ca * 0.2, 0.12, sa * 0.19))
        mane.append((tongue(b3, radial * 0.7 + Y, L * 0.9, 0.08, 0.6, Z * 0.04, hint=Y), 'Fire_Red' if k % 2 else 'Fire_Orange'))
        b2 = rc + Vector((ca * 0.2, -0.05, sa * 0.19))
        mane.append((tongue(b2, radial + Y * 0.2, L * 0.62, 0.07, 0.55, hint=Y), 'Fire_Yellow'))
    for d, L, w in ((Vector((0, 0.1, 1)), 0.3, 0.1), (Vector((0.45, 0.25, 1)), 0.22, 0.08),
                    (Vector((-0.45, 0.25, 1)), 0.22, 0.08), (Vector((0, 0.9, 0.6)), 0.24, 0.08)):
        mane.append((tongue(hc + Vector((0, 0.02, 0.2)), d, L, w, 0.5, Vector((0, 0.05, 0)), hint=Y), 'Fire_Orange'))
        mane.append((tongue(hc + Vector((0, 0.0, 0.2)), d, L * 0.65, w * 0.65, 0.9, hint=Y), 'Fire_Yellow'))
    for x in (-0.2, 0.2):  # mane continues down the neck at the back
        mane.append((tongue(Vector((x * 0.6, -0.1, 0.6)), Vector((x, 0.6, 0.4)), 0.2, 0.08, 0.5, hint=Y), 'Fire_Orange'))
    p.obj('FlameMane', mane)
    bib = []
    for x in (-0.15, -0.075, 0.0, 0.075, 0.15):
        bib.append((tongue(Vector((x, -0.38, 0.46)), Vector((x * 0.9, -0.7, -1)), 0.15 - abs(x) * 0.3, 0.075, 0.42,
                           hint=Y), 'Fire_Yellow'))
    for x in (-0.06, 0.06):
        bib.append((tongue(Vector((x, -0.4, 0.47)), Vector((x, -0.3, -1)), 0.1, 0.045, 0.9, hint=Y), 'Fire_Orange'))
    p.obj('ChestRuff', bib)
    flame_tail(p, Vector((0, 0.43, 0.47)), 1.08)
    bc = Vector((0, 0.1, 0.45))
    marks = flame_markings(p, 'Body', bc, [(Vector((1, 0.6, 0.3)), 0.1, 0.25), (Vector((1, 0.15, 0.1)), 0.075, -0.15)],
                           'Fire_Orange')
    marks += flame_markings(p, 'Leg_BL', p.center['Leg_BL'], [(Vector((1, -0.2, 0.1)), 0.075, 0.0)], 'Fire_Orange')
    marks += [(mirror(m[0]), m[1]) for m in marks]
    p.obj('FlameMarkings', marks)
    return p


def build_smoulderat(pc):
    p = Pet('Smoulderat', pc)
    fur = 'Fur_DarkCharcoal'
    p.obj('Body', [(body_bm(0.48, -0.26, 0.4, 0.43, 0.36, 0.31, taper=0.12, q=2.2, ex=2.2), fur)])
    hc = Vector((0, -0.42, 0.56))
    p.obj('Head', [
        (ellipsoid(hc, (0.31, 0.27, 0.265), seg=28, rings=16, ex=2.2), fur),
        (ellipsoid((0, -0.66, 0.47), (0.17, 0.16, 0.125), seg=22, rings=12), fur),
        (ellipsoid((0, -0.53, 0.4), (0.15, 0.11, 0.09), seg=18, rings=10), fur),
    ])
    round_ears(p, hc, Vector((0.24, 0.06, 0.2)), 0.16, fur, 'Ear_Orange')
    legs_and_paws(p, fur, 'Paw_Red', (0.2, -0.16, 0.26, 0.092), (0.23, 0.3, 0.24, 0.092), thigh=(0.13, 0.18, 0.15))
    eyes(p, hc, Vector((0.5, -1.0, 0.06)), 0.076)
    sc = Vector((0, -0.66, 0.47))
    hit, n = cast(p.bvh['Head'], sc, Vector((0, -1, 0.5)))
    p.obj('Nose', [(ellipsoid(hit, (0.034, 0.026, 0.024), frame(n)), 'Nose_Dark')])
    teeth = []
    for x in (-0.017, 0.017):
        th, tn = cast(p.bvh['Head'], sc, Vector((x * 2, -1, -0.62)))
        teeth.append((ellipsoid(th + tn * 0.006 - Z * 0.02, (0.015, 0.007, 0.024), frame(tn), seg=12, rings=8,
                                ex=3.5), 'Tooth_White'))
    p.obj('Teeth', teeth)
    mh, mn = cast(p.bvh['Head'], sc, Vector((0, -1, -0.28)))
    p.obj('Mouth', [(ellipsoid(mh, (0.04, 0.01, 0.006), frame(mn), seg=12, rings=6), 'Mouth_Dark')])
    whiskers(p, sc, Vector((0.8, -0.7, 0.0)), 'Whisker_Light')
    curled_tail(p, Vector((0, 0.46, 0.36)), 1.08, 0.06, 0.082)
    bc = Vector((0, 0.1, 0.41))
    p.obj('ChestPatch', [(decal(p.bvh['Body'], bc, Vector((0, -1, -0.4)),
                                [(math.cos(a) * 0.5, math.sin(a) * 0.6) for a in
                                 [2 * math.pi * k / 24 for k in range(24)]], 0.34, offset=0.004), 'Fur_EmberBelly')])
    # crystal spikes along the spine (bigger in the middle), crown on the head
    rng = random.Random(3)
    cr = []
    K = 8
    for i in range(K):
        t = i / (K - 1)
        y = 0.34 - 0.62 * t
        h = 0.12 + 0.14 * math.sin(math.pi * (0.15 + 0.75 * t))
        hit, n = cast(p.bvh['Body'], bc, Vector((0, y * 1.6, 1)))
        tilt = (n + Y * 0.35).normalized()
        cr.append((crystal(hit, tilt, h, 0.045 + 0.02 * h, rng.uniform(0, 1)), 'Crystal_Red' if i % 2 else 'Crystal_Orange'))
        for sx in (-1, 1):
            hit2, n2 = cast(p.bvh['Body'], bc, Vector((sx * 0.38, y * 1.6 + 0.08, 1)))
            cr.append((crystal(hit2, (n2 + Y * 0.3 + X * sx * 0.25).normalized(), h * 0.62, 0.034 + 0.01 * h,
                               rng.uniform(0, 1)), 'Crystal_Orange' if i % 2 else 'Crystal_Red'))
    p.obj('BackCrystals', cr, smooth=False)
    crown = []
    for d, h, r, m in ((Vector((0, 0.15, 1)), 0.19, 0.05, 'Crystal_Red'), (Vector((0.3, 0.1, 1)), 0.13, 0.04, 'Crystal_Orange'),
                       (Vector((-0.3, 0.1, 1)), 0.13, 0.04, 'Crystal_Orange'), (Vector((0, -0.25, 1)), 0.11, 0.036, 'Crystal_Orange'),
                       (Vector((0.15, 0.45, 1)), 0.12, 0.036, 'Crystal_Red'), (Vector((-0.15, 0.45, 1)), 0.12, 0.036, 'Crystal_Red')):
        hit, n = cast(p.bvh['Head'], hc, d)
        crown.append((crystal(hit, (n + d.normalized()).normalized(), h, r, rng.uniform(0, 1)), m))
    p.obj('HeadCrystals', crown, smooth=False)
    # glowing lava fissures: branching cracks over body, head and haunches
    rng = random.Random(11)
    fis = []

    def lava(bvh, c, paths, w):
        for path in paths:
            fis.append((ribbon(bvh, c, path, w * 2.2, 0.004), 'Lava_Edge'))
            fis.append((ribbon(bvh, c, path, w, 0.007), 'Lava_Core'))
    for d, h in ((Vector((1, 0.7, 0.3)), Vector((0, -1, -0.3))), (Vector((1, 0.1, 0.5)), Vector((0, 0.2, -1))),
                 (Vector((1, -0.45, 0.05)), Vector((0, 0.6, 0.8))), (Vector((0.7, 0.95, -0.2)), Vector((0, -0.4, 1))),
                 (Vector((0.55, 0.0, 1)), Vector((0.2, 1, -0.2))), (Vector((1, 0.3, -0.25)), Vector((0, -1, 0.3)))):
        lava(p.bvh['Body'], bc, crack_walk(rng, d, h, 8, 0.075, 0.6, 0.35, zmin=-0.35), 0.013)
    lava(p.bvh['Head'], hc, crack_walk(rng, Vector((0.75, 0.2, 0.5)), Vector((0, -0.3, 1)), 5, 0.12, 0.6, 0.3), 0.011)
    lava(p.bvh['Head'], hc, crack_walk(rng, Vector((0.9, -0.3, -0.25)), Vector((0, 1, 0.2)), 4, 0.12, 0.5, 0.0), 0.01)
    lava(p.bvh['Leg_BL'], p.center['Leg_BL'], crack_walk(rng, Vector((1, -0.2, 0.3)), Vector((0, 0.3, -1)), 4, 0.25, 0.5, 0.0), 0.01)
    lava(p.bvh['Leg_FL'], p.center['Leg_FL'], crack_walk(rng, Vector((1, -0.4, 0.4)), Vector((0, 0.2, -1)), 4, 0.25, 0.5, 0.0), 0.009)
    fis += [(mirror(f[0]), f[1]) for f in fis]
    p.obj('LavaFissures', fis)
    return p


# ------------------------------------------------------------------ studio, cameras, labels
def link(coll, ob):
    coll.objects.link(ob)
    return ob


def look(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def build_studio(sc):
    st = bpy.data.collections.new('STUDIO')
    sc.collection.children.link(st)
    me = bpy.data.meshes.new('Studio_Ground')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=40)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS['Ground_Studio'])
    link(st, bpy.data.objects.new('Studio_Ground', me))
    for name, loc, energy, size, color in (
            ('Light_Key', (-4.0, -6.0, 6.0), 1100, 6.0, (1.0, 0.97, 0.93)),
            ('Light_Fill', (6.0, -4.0, 3.5), 450, 7.0, (0.94, 0.96, 1.0)),
            ('Light_Rim', (0.0, 6.0, 5.0), 650, 6.0, (1.0, 1.0, 1.0)),
            ('Light_SideFill', (9.0, 1.0, 2.5), 300, 5.0, (1.0, 1.0, 1.0))):
        li = bpy.data.lights.new(name, 'AREA')
        li.energy, li.size, li.color = energy, size, color
        o = link(st, bpy.data.objects.new(name, li))
        o.location = loc
        look(o, (0, 0, 0.4))
    w = bpy.data.worlds.new('World_NeutralStudio')
    sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (*srgb('#b4b4b6'), 1)
    bg.inputs['Strength'].default_value = 0.65


def build_cameras(sc):
    cc = bpy.data.collections.new('CAMERAS')
    sc.collection.children.link(cc)
    for pet, x in PET_X.items():
        sub = bpy.data.collections.new(f'{pet}_Cams')
        cc.children.link(sub)
        for view, loc, tgt, clip in (('Front', (x, -6.0, CAM_H), (x, 0, CAM_H), 30.0),
                                     ('Side', (x + 1.1, 0.12, CAM_H), (x - 5, 0.12, CAM_H), 2.0),
                                     ('Back', (x, 6.0, CAM_H), (x, 0, CAM_H), 30.0)):
            cam = bpy.data.cameras.new(f'CAM_{pet}_{view}')
            cam.type = 'ORTHO'
            cam.ortho_scale = CAM_SCALE
            cam.clip_start, cam.clip_end = 0.01, clip   # side cams clip away the neighbouring pets
            cam.display_size = 0.3
            o = link(sub, bpy.data.objects.new(cam.name, cam))
            o.location = loc
            look(o, tgt)
    cam = bpy.data.cameras.new('CAM_Overview_ThreeQuarter')
    cam.lens = 40
    o = link(cc, bpy.data.objects.new(cam.name, cam))
    o.location = (-6.5, -9.5, 4.2)
    look(o, (0, 0, 0.35))
    sc.camera = o
    cam = bpy.data.cameras.new('CAM_Lineup_Front')
    cam.type = 'ORTHO'
    cam.ortho_scale = 9.6
    o = link(cc, bpy.data.objects.new(cam.name, cam))
    o.location = (0, -12, CAM_H)
    look(o, (0, 0, CAM_H))


def build_labels(sc):
    lc = bpy.data.collections.new('LABELS')
    sc.collection.children.link(lc)

    def text(name, body, loc, size, rot=0.0):
        cu = bpy.data.curves.new(name, 'FONT')
        cu.body, cu.size, cu.align_x, cu.align_y = body, size, 'CENTER', 'CENTER'
        cu.materials.append(MATS['Label_Dark'])
        o = link(lc, bpy.data.objects.new(name, cu))
        o.location = loc
        o.rotation_euler = (0, 0, rot)
        return o
    for pet, x in PET_X.items():
        text(f'Label_{pet}_Name', pet.upper(), (x, -1.45, 0.005), 0.3)
        text(f'Label_{pet}_Front', 'FRONT  (-Y)', (x, -1.0, 0.005), 0.12)
        text(f'Label_{pet}_Side', 'SIDE  (+X)', (x + 0.9, 0.12, 0.005), 0.12, math.pi / 2)
        text(f'Label_{pet}_Back', 'BACK  (+Y)', (x, 1.3, 0.005), 0.12, math.pi)


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    build_materials()
    pc = bpy.data.collections.new('PETS')
    sc.collection.children.link(pc)
    for fn in (build_ashrat, build_cinderkit, build_flarecat, build_smoulderat):
        pet = fn(pc)
        pet.place(PET_X[pet.name])
    build_studio(sc)
    build_cameras(sc)
    build_labels(sc)
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    return sc


def render_previews(sc, out):
    os.makedirs(out, exist_ok=True)
    sc.cycles.samples = 40
    shots = []
    sc.render.resolution_x, sc.render.resolution_y = 640, 480
    for pet in PET_X:
        for view in ('Front', 'Side', 'Back'):
            sc.camera = bpy.data.objects[f'CAM_{pet}_{view}']
            sc.render.filepath = os.path.join(out, f'FirePets_{pet}_{view}.png')
            bpy.ops.render.render(write_still=True)
            shots.append(sc.render.filepath)
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.cycles.samples = 64
    for cam in ('CAM_Overview_ThreeQuarter', 'CAM_Lineup_Front'):
        sc.camera = bpy.data.objects[cam]
        sc.render.filepath = os.path.join(out, f'FirePets_{cam[4:]}.png')
        bpy.ops.render.render(write_still=True)
    sc.camera = bpy.data.objects['CAM_Overview_ThreeQuarter']
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return
    W, H, LW, TH = 640, 480, 380, 40
    sheet = Image.new('RGB', (LW + 3 * W, len(PET_X) * (H + TH)), (180, 180, 182))
    dr = ImageDraw.Draw(sheet)
    try:
        big = ImageFont.truetype('DejaVuSans-Bold.ttf', 44)
        small = ImageFont.truetype('DejaVuSans-Bold.ttf', 24)
    except OSError:
        big = small = ImageFont.load_default()
    for r, pet in enumerate(PET_X):
        y0 = r * (H + TH)
        dr.text((30, y0 + TH + H // 2 - 24), pet, fill=(40, 40, 44), font=big)
        for c, view in enumerate(('FRONT', 'SIDE', 'BACK')):
            sheet.paste(Image.open(shots[r * 3 + c]).convert('RGB'), (LW + c * W, y0 + TH))
            dr.text((LW + c * W + W // 2 - 40, y0 + 8), view, fill=(40, 40, 44), font=small)
        if r:
            dr.line((0, y0, sheet.width, y0), fill=(120, 120, 124), width=2)
    sheet.save(os.path.join(out, 'FirePets_Turnaround.png'))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    sc = build_scene()
    path = os.path.join(HERE, 'FirePets.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    for pet in PET_X:
        objs = [o for o in bpy.data.collections[pet].objects if o.type == 'MESH']
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
        print(f'{pet}: {len(objs)} mesh objects, {tris} tris')
    print('Saved:', path)
    if '--render' in argv:
        i = argv.index('--render')
        out = argv[i + 1] if i + 1 < len(argv) else os.path.join(HERE, '..', 'previews')
        render_previews(sc, os.path.abspath(out))


if __name__ == '__main__':
    main()
