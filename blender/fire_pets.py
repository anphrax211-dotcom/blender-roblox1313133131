"""FIRE PETS - Ashrat, Cinderkit, Flarecat and Smoulderat, modelled to match the fire-pet turnaround sheet.

Proportions are measured off the sheet's front / side / back views (one shared scale, Ashrat is ~1 m tall
to the ear tips), so the four pets keep the sheet's relative sizes. Toy-like stylised forms: the head and
body are smooth seamless shells (overlapping volumes voxel-remeshed, smoothed and decimated), every other
part is its own simple mesh. Fire is coloured with a red -> orange -> yellow gradient stored in the mesh
('Col' colour attribute) and is slightly emissive so it stays bright.

Scene layout (1 unit = 1 m, Z up, every pet faces -Y and stands on z = 0):
    PETS/<Pet>            one collection per pet; parts parented to `<Pet>_Root` (move the empty to move it)
    STUDIO                ground plane, soft area lights, neutral grey world
    CAMERAS/<Pet>_Cams    orthographic CAM_<Pet>_Front / _Side / _Back, framed like the sheet (5 degrees
                          above level so the contact shadows read). The side camera looks from the pet's
                          left (+X), so the head is on the left like the sheet, and clips out the
                          neighbouring pets. Plus CAM_Overview_ThreeQuarter and CAM_Lineup_Front.
    LABELS                pet names + FRONT / SIDE / BACK markers on the ground (viewport only, not rendered)

    Ashrat x = -3.9   Cinderkit x = -1.3   Flarecat x = 1.3   Smoulderat x = 3.9

Part names: <Pet>_Body, _Head, _Ear_L/_R, _Leg_FL/FR/BL/BR, _Paw_FL/FR/BL/BR, _Tail, _Eye_L/_R, _Nose,
_Mouth, _Teeth, _Whiskers, _ChestPatch and the fire features (_FlameMarkings, _CheekSwirls, _FlameTuft,
_FlameMane, _ChestRuff, _LavaFissures, _BackCrystals, _HeadCrystals ...). L/R are the pet's own sides
(left = +X).

Run in Blender (Scripting tab -> Run Script) or headless:
    python3 fire_pets.py                       (with the `bpy` pip module) -> saves FirePets.blend
    python3 fire_pets.py --render ../previews  also renders every turnaround camera + the comparison sheet
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
PET_X = {'Ashrat': -3.9, 'Cinderkit': -1.3, 'Flarecat': 1.3, 'Smoulderat': 3.9}
CAM_H = 0.6           # aim height of the turnaround cameras
CAM_SCALE = 2.3       # ortho scale, identical for every pet so sizes compare 1:1
CAM_TILT = math.radians(5)
LOW = False           # True while a pet is built in the light game-budget format (Flarecat)


def lod(high, low):
    """pick the detailed or the light value depending on the format of the pet being built"""
    return low if LOW else high


# ------------------------------------------------------------------ colours & materials
def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def grad(stops, t):
    """colour at t along [(t0, '#hex'), ...]"""
    t = min(max(t, 0.0), 1.0)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            k = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            a, b = srgb(c0), srgb(c1)
            return tuple(x + (y - x) * k for x, y in zip(a, b))
    return srgb(stops[-1][1])


FIRE = [(0, '#c8221a'), (0.3, '#f4471a'), (0.6, '#ff8c1c'), (0.85, '#ffc22e'), (1, '#ffd84a')]
FIRE_YELLOW = [(0, '#ff7a18'), (0.35, '#ffa81e'), (0.75, '#ffcc30'), (1, '#ffdc50')]
FIRE_ORANGE = [(0, '#e0381a'), (0.45, '#ff6a14'), (1, '#ffa424')]
FIRE_DEEP = [(0, '#a0141a'), (0.5, '#d8281a'), (1, '#ff5a16')]
TAIL_FIRE = [(0, '#d8301a'), (0.25, '#f45016'), (0.55, '#ff8c1c'), (0.8, '#ffbe2c'), (1, '#ffd64a')]
IRIS = [(0, '#ffd23a'), (0.3, '#ff9a1e'), (0.62, '#f4461a'), (1, '#9c140e')]
TAIL_OUTER = [(0, '#e8401a'), (0.25, '#ff7a1a'), (0.55, '#ffb224'), (0.8, '#ffd23a'), (1, '#ffe05a')]
CRYSTAL = [(0, '#8c0e10'), (0.45, '#d8261a'), (0.8, '#ff5a1e'), (1, '#ff9a3a')]

MATS = {}


def material(name, hexcol, rough=0.55, emit=0.0, coat=0.0, vcol=False, sheen=0.0):
    m = bpy.data.materials.new(name)
    rgb = srgb(hexcol)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.12
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    if vcol:      # colour gradient stored in the mesh's 'Col' colour attribute
        a = m.node_tree.nodes.new('ShaderNodeVertexColor')
        a.layer_name = 'Col'
        m.node_tree.links.new(a.outputs['Color'], b.inputs['Base Color'])
        m.node_tree.links.new(a.outputs['Color'], b.inputs['Emission Color'])
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def build_materials():
    material('Fur_Charcoal', '#3d363b', 0.7, sheen=0.3)           # Ashrat
    material('Fur_Soot', '#2b262a', 0.7, sheen=0.3)               # Cinderkit
    material('Fur_PaleGold', '#f4cc9e', 0.65, sheen=0.2)          # Flarecat
    material('Fur_DarkCharcoal', '#38323a', 0.75, sheen=0.3)      # Smoulderat
    material('Fur_EmberBelly', '#b8682f', 0.7)                    # Ashrat chest
    material('Fur_BrownBelly', '#7c4029', 0.7)                    # Smoulderat chest
    material('Paw_Orange', '#ff9426', 0.5)
    material('Paw_Amber', '#ffb41e', 0.5)
    material('Paw_Tangerine', '#ff8a24', 0.5)
    material('Paw_Red', '#e8352a', 0.5)
    material('Fire_Gradient', '#ff8a1e', 0.45, emit=0.4, vcol=True)
    material('Flame_Orange', '#ff6a14', 0.45, emit=0.9)
    material('Flame_Yellow', '#ffc22e', 0.45, emit=0.9)
    material('Flame_Pale', '#f39448', 0.6, emit=0.15)
    material('Flame_PaleCore', '#f7bf7c', 0.6, emit=0.1)
    material('Lava_Glow', '#ff4612', 0.4, emit=2.2)
    material('Lava_Core', '#ffd248', 0.4, emit=5.0)
    material('Crystal_Gradient', '#e0301c', 0.22, emit=0.5, coat=0.7, vcol=True)
    material('Ear_Orange', '#ff8a2c', 0.8)
    material('Ear_Pink', '#f39a96', 0.6)
    material('Eye_Outline', '#1e1112', 0.3, coat=0.6)
    material('Eye_Iris', '#f04a1a', 0.25, emit=0.35, coat=0.8, vcol=True)
    material('Eye_Pupil', '#2a0a09', 0.25, coat=0.8)
    material('Eye_Highlight', '#ffffff', 0.2, emit=1.2)
    material('Nose_Orange', '#ff8a2a', 0.4)
    material('Nose_Pink', '#f07a7c', 0.4)
    material('Mouth_Dark', '#3a1416', 0.5)
    material('Mouth_Line', '#1e1314', 0.6)
    material('Tongue_Pink', '#f26e86', 0.4)
    material('Tooth_White', '#f7f3ea', 0.35)
    material('Whisker_Light', '#9e9a9c', 0.6)
    material('Whisker_Tan', '#b8946c', 0.6)
    material('Ground_Studio', '#9c9c9f', 0.85)
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


def ellipsoid(c, r, M=None, seg=24, rings=14, ex=2.0):
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


def paint(bm, fn):
    """per-vertex colour from fn(position) into the 'Col' attribute"""
    col = bm.verts.layers.float_color.get('Col') or bm.verts.layers.float_color.new('Col')
    for v in bm.verts:
        v[col] = (*fn(v.co), 1.0)
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


def revolve(profile, c, M, seg=40, sy=1.0):
    """surface of revolution around local +Z of M; profile = [(radius, height)], radius 0 = pole"""
    bm = bmesh.new()
    rings = []
    for r, h in profile:
        if r < 1e-6:
            rings.append([bm.verts.new(c + M @ Vector((0, 0, h)))])
        else:
            rings.append([bm.verts.new(c + M @ Vector((r * math.cos(a), r * sy * math.sin(a), h)))
                          for a in [2 * math.pi * k / seg for k in range(seg)]])
    for r0, r1 in zip(rings, rings[1:]):
        if len(r0) > 1 and len(r1) > 1:
            for k in range(seg):
                bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
        elif len(r1) > 1:
            for k in range(seg):
                bm.faces.new((r0[0], r1[(k + 1) % seg], r1[k]))
        else:
            for k in range(seg):
                bm.faces.new((r0[k], r0[(k + 1) % seg], r1[0]))
    return bm


def body_bm(y_rear, y_front, z_rear, z_front, a, b, taper=0.1, q=2.4, ex=2.3, n=24, seg=32):
    """rounded body loaf along Y (rear -> front)"""
    pts, radii = [], []
    for i in range(n + 1):
        t = (1 - math.cos(math.pi * i / n)) / 2
        f = max(0.0, 1 - abs(2 * t - 1) ** q) ** (1 / q)
        k = 1 - taper * t
        pts.append(Vector((0, y_rear + (y_front - y_rear) * t, z_rear + (z_front - z_rear) * t)))
        radii.append((a * f * k, b * f * k))
    return tube(pts, radii, seg, hint=Z, ex=ex)


def tongue(base, direction, length, width, flat=0.5, bend=Vector(), hint=Y, seg=None, n=None, stops=FIRE, swell=0.3):
    """one flame tongue: swells from the base then tapers to a sharp tip, curving by `bend`.
    stops = colour gradient base -> tip (None = no colour attribute)"""
    seg, n = seg or lod(10, 8), n or lod(4, 3)
    d = direction.normalized()
    ctrl = [base, base + d * length * 0.35 + bend * 0.12, base + d * length * 0.7 + bend * 0.5,
            base + d * length + bend]
    pts = catmull(ctrl, n)
    radii, cols = [], []
    for i in range(len(pts)):
        t = i / (len(pts) - 1)
        r = 0.55 + 0.45 * math.sin(t / swell * math.pi / 2) if t < swell else ((1 - t) / (1 - swell)) ** 0.85
        radii.append((width * r, width * r * flat))
        if stops:
            cols.append(grad(stops, t))
    return tube(pts, radii, seg, hint=hint, colors=cols if stops else None)


def crystal(base, n, h, r, spin=0.0, sides=6):
    """faceted crystal standing on `base` along n: slightly tapered prism + pyramid tip, red -> orange"""
    M = frame(n) @ Matrix.Rotation(spin, 3, 'Z')
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new('Col')
    lo, mid, hi = [], [], []
    for k in range(sides):
        a = 2 * math.pi * k / sides
        lo.append(bm.verts.new(base + M @ Vector((math.cos(a) * r * 0.78, math.sin(a) * r * 0.78, -0.05))))
        mid.append(bm.verts.new(base + M @ Vector((math.cos(a) * r, math.sin(a) * r, h * 0.3))))
        hi.append(bm.verts.new(base + M @ Vector((math.cos(a) * r * 0.9, math.sin(a) * r * 0.9, h * 0.66))))
    tip = bm.verts.new(base + M @ Vector((0, 0, h)))
    bm.faces.new(lo[::-1])
    for k in range(sides):
        k1 = (k + 1) % sides
        bm.faces.new((lo[k], lo[k1], mid[k1], mid[k]))
        bm.faces.new((mid[k], mid[k1], hi[k1], hi[k]))
        bm.faces.new((hi[k], hi[k1], tip))
    for v in bm.verts:
        hgt = (M.transposed() @ (v.co - base)).z / h
        v[col] = (*grad(CRYSTAL, hgt), 1.0)
    return bm


def mirror(bm):
    """copy of a bmesh mirrored to the other side (x -> -x)"""
    m = bm.copy()
    for v in m.verts:
        v.co.x = -v.co.x
    bmesh.ops.reverse_faces(m, faces=m.faces)
    return m


def blob(pieces, tris, voxel=0.011, smooth=10):
    """overlapping closed volumes -> one seamless smooth shell (voxel remesh, smooth, decimate to ~tris)"""
    bm = bmesh.new()
    for p in pieces:
        me = bpy.data.meshes.new('_tmp')
        p.to_mesh(me)
        p.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new('_blob')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('_blob', me)
    bpy.context.scene.collection.objects.link(ob)
    rm = ob.modifiers.new('Remesh', 'REMESH')
    rm.mode, rm.voxel_size = 'VOXEL', voxel
    sm = ob.modifiers.new('Smooth', 'SMOOTH')
    sm.factor, sm.iterations = 1.0, smooth
    dg = bpy.context.evaluated_depsgraph_get()
    n = len(ob.evaluated_get(dg).data.polygons) * 2
    dm = ob.modifiers.new('Decimate', 'DECIMATE')
    dm.ratio = min(1.0, tris / max(n, 1))
    dg = bpy.context.evaluated_depsgraph_get()
    out = bmesh.new()
    out.from_object(ob, dg)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    return out


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


def cast_front(bvh, x, z, back=False):
    """hit on the front (-Y) or back (+Y) of a surface at height z, side offset x"""
    s = 1 if back else -1
    loc, nor, _, _ = bvh.ray_cast(Vector((x, s * 5.0, z)), Vector((0, -s, 0)))
    if nor.dot(Vector((0, s, 0))) < 0:
        nor = -nor
    return loc, nor


def _orient_to(bm, c):
    """make the faces of an open surface patch point away from the projection centre"""
    bm.faces.ensure_lookup_table()
    if bm.faces:
        f = bm.faces[len(bm.faces) // 2]
        if f.normal.dot(f.calc_center_median() - c) < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)


FLAME = [(0.0, 0.0), (0.18, 0.03), (0.29, 0.14), (0.31, 0.3), (0.27, 0.45), (0.33, 0.58), (0.4, 0.86),
         (0.24, 0.71), (0.16, 0.63), (0.12, 0.82), (0.13, 1.25), (0.0, 1.0), (-0.08, 0.78), (-0.1, 0.66),
         (-0.18, 0.8), (-0.29, 0.99), (-0.24, 0.7), (-0.29, 0.5), (-0.31, 0.3), (-0.26, 0.13), (-0.15, 0.03)]
FLAME_CORE = [(0.0, 0.1), (0.1, 0.13), (0.15, 0.25), (0.13, 0.4), (0.08, 0.52), (0.06, 0.8), (-0.02, 0.6),
              (-0.08, 0.66), (-0.08, 0.48), (-0.13, 0.36), (-0.13, 0.22), (-0.08, 0.13)]


def outline(pts, n=2):
    return catmull(list(pts) + [pts[0]], n)[:-1]


def decal(bvh, c, d, shape, size, angle=0.0, offset=0.005, up=Z, step=None, flip=False):
    """2D outline wrapped onto a surface around the hit point of direction d (spherical projection from c)"""
    hit, n = cast(bvh, c, d)
    M = frame(n, up)
    r, u = M.col[0], M.col[1]
    ca, sa = math.cos(angle), math.sin(angle)
    step = step or lod(0.016, 0.026)
    pts2 = [((-x if flip else x) * size, y * size) for x, y in shape]
    pts2 = [(x * ca - y * sa, x * sa + y * ca) for x, y in pts2]
    verts, faces, _ = fill2d(pts2, step)
    bm = bmesh.new()
    vs = [bm.verts.new(hit + r * v.x + u * v.y) for v in verts]
    for f in faces:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    for v in bm.verts:
        loc, nor, _, _ = bvh.ray_cast(v.co + n * 0.25, -n)
        if loc is None:
            dd = (v.co - c).normalized()
            loc, _ = cast(bvh, c, dd)
        v.co = loc + n * offset
    _orient_to(bm, c)
    return bm


def flame_decal(bvh, c, d, size, angle=0.0, flip=False, outer='Flame_Orange', inner='Flame_Yellow'):
    """two-layer flame marking: orange flame with a yellow core"""
    centred = lambda pts: [(x, y - 0.55) for x, y in outline(pts)]     # aim point = middle of the flame
    return [(decal(bvh, c, d, centred(FLAME), size, angle, 0.004, flip=flip), outer),
            (decal(bvh, c, d, centred(FLAME_CORE), size, angle, 0.007, flip=flip), inner)]


def ribbon_pts(bvh, c, pts, width, offset=0.004, taper=True, closed=False):
    """strip following 3D points projected (from c) onto a surface"""
    hits = [cast(bvh, c, p - c) for p in pts]
    P = [h + (p - c).normalized() * offset for (h, _), p in zip(hits, pts)]
    if closed:
        P.append(P[0])
        hits.append(hits[0])
    bm = bmesh.new()
    left, right = [], []
    n = len(P)
    for i in range(n):
        if closed:
            t = (P[(i + 1) % (n - 1)] - P[(i - 1) % (n - 1)]).normalized()
        else:
            t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized()
        side = hits[i][1].cross(t).normalized()
        k = i / (n - 1)
        w = width * (math.sin(math.pi * k) ** 0.6 if taper else 1.0) * 0.5 + width * 0.06
        left.append(bm.verts.new(P[i] + side * w))
        right.append(bm.verts.new(P[i] - side * w))
    for i in range(n - 1):
        bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
    _orient_to(bm, c)
    return bm


def ribbon(bvh, c, dirs, width, offset=0.004, taper=True):
    return ribbon_pts(bvh, c, [c + d.normalized() for d in dirs], width, offset, taper)


def crack_walk(rng, start, heading, steps, step, wobble=0.5, branch=0.0, depth=0, zmin=-0.4):
    """random walk over the unit sphere of directions; returns a list of paths (lists of Vectors)"""
    d = start.normalized()
    h = (heading - heading.dot(d) * d).normalized()
    path, paths = [d.copy()], []
    for _ in range(steps):
        h = Matrix.Rotation(rng.uniform(-wobble, wobble), 3, d) @ h
        d = (d + h * step).normalized()
        h = (h - h.dot(d) * d).normalized()
        if d.z < zmin:
            break
        path.append(d.copy())
        if depth < 2 and rng.random() < branch:
            bh = Matrix.Rotation(rng.choice((-1, 1)) * rng.uniform(0.6, 1.1), 3, d) @ h
            paths += crack_walk(rng, d, bh, max(2, steps // 2), step * 0.9, wobble, branch * 0.6, depth + 1, zmin)
    if len(path) > 2:
        paths.append(path)
    return paths


def voronoi_paths(rng, n_seeds, keep, jitter=0.05, sub=6):
    """cell edges of a spherical Voronoi diagram (cracked-rock pattern) as paths of directions"""
    golden = math.pi * (3 - math.sqrt(5))
    pts = []
    for i in range(n_seeds):
        zz = 1 - 2 * (i + 0.5) / n_seeds
        rr = math.sqrt(1 - zz * zz)
        p = Vector((math.cos(golden * i) * rr, math.sin(golden * i) * rr, zz))
        p += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.22 / math.sqrt(n_seeds / 12)
        pts.append(p.normalized())
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    bmesh.ops.convex_hull(bm, input=vs)
    bm.faces.index_update()
    centre = {}
    for f in bm.faces:
        a, b, c = [v.co for v in f.verts[:3]]
        n = (b - a).cross(c - a).normalized()
        centre[f.index] = n if n.dot(a) > 0 else -n
    paths = []
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        p0, p1 = centre[e.link_faces[0].index], centre[e.link_faces[1].index]
        if not (keep(p0) or keep(p1)):
            continue
        ax = p0.cross(p1)
        if ax.length < 1e-6:
            continue
        side = ax.normalized()
        path = []
        for k in range(sub + 1):
            t = k / sub
            p = (p0 * (1 - t) + p1 * t).normalized()
            if 0 < k < sub:
                p = (p + side * rng.uniform(-jitter, jitter)).normalized()
            path.append(p)
        paths.append(path)
    bm.free()
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
        has_col = any(p[0].verts.layers.float_color.get('Col') is not None for p in pieces)
        bm, mats = bmesh.new(), []
        for piece in pieces:
            pbm, mname = piece[0], piece[1]
            sm = piece[2] if len(piece) > 2 else smooth
            if has_col and pbm.verts.layers.float_color.get('Col') is None:
                paint(pbm, lambda co: (1.0, 1.0, 1.0))
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
def legs_and_paws(pet, fur, paw, front, back, paw_size, toes=3):
    """front/back: (x, y, top_z, radius); paw_size = (half width, half length, height); paws stand on z = 0"""
    pw, pl, ph = paw_size
    for tag, (x, y, top, r) in (('F', front), ('B', back)):
        pts = [Vector((x, y + 0.01, top)), Vector((x, y, (top + ph) / 2)), Vector((x, y - 0.005, ph * 0.8))]
        pet.pair(f'Leg_{tag}', [(tube(pts, [(r, r * 1.05), (r * 0.95, r), (r * 0.98, r)], lod(20, 12)), fur)], sep='')
        pc = Vector((x, y - pl * 0.22, 0))
        parts = [ellipsoid(pc + Vector((0, 0.0, ph * 0.5)), (pw, pl * 0.82, ph * 0.52), ex=2.2),
                 ellipsoid(pc + Vector((0, pl * 0.3, ph * 0.62)), (pw * 0.86, pl * 0.5, ph * 0.6))]
        for i in range(toes):
            dx = (i - (toes - 1) / 2) * (2 * pw / toes) * 0.95
            parts.append(ellipsoid(pc + Vector((dx, -pl * 0.62, ph * 0.42)),
                                   (pw / toes * 1.08, pl * 0.36, ph * 0.43)))
        pet.pair(f'Paw_{tag}', [(blob(parts, lod(1100, 360), voxel=0.006, smooth=3), paw)], sep='')


def eyes(pet, x, z, s, head='Head', face_fwd=0.15, flush=False):
    """big glossy eyes: dark outline, red -> orange -> yellow iris, round pupil, two inner-upper highlights.
    flush=True: every layer is a thin shell wrapped onto the head surface (lifted 0-0.13 eye radii), so the
    eyes sit flush with the face instead of bulging out of it"""
    bvh = pet.bvh[head]
    hit, nrm = cast_front(bvh, x, z)
    n = (nrm + Vector((0, -(0.0 if flush else face_fwd), 0))).normalized()
    M = frame(n)
    r, u = M.col[0], M.col[1]
    es, er = lod(32, 30), lod(18, 16)
    #       material         dr     du    dn (bulged / flush)  rx    ry    rz (bulged / flush)  seg, rings
    spec = (('Eye_Outline', 0.0, 0.0, -0.1, 0.0, 1.06, 1.17, 0.42, 0.06, es, er),
            ('Eye_Iris', 0.0, 0.0, -0.04, 0.025, 0.98, 1.1, 0.42, 0.065, es, er),
            ('Eye_Pupil', 0.0, 0.1, 0.1, 0.06, 0.5, 0.56, 0.3, 0.05, lod(24, 20), lod(12, 10)),
            ('Eye_Highlight', -0.27, 0.38, 0.4, 0.1, 0.25, 0.25, 0.12, 0.035, 16, 8),
            ('Eye_Highlight', 0.32, -0.4, 0.33, 0.09, 0.1, 0.1, 0.06, 0.03, 12, 6))
    pieces = []
    for mat, dr, du, dn_b, dn_f, rx, ry, rz_b, rz_f, sg, rg in spec:
        dn, rz = (dn_f, rz_f) if flush else (dn_b, rz_b)
        c = hit + r * (dr * s) + u * (du * s) + n * (dn * s)
        bm = ellipsoid(c, (s * rx, s * ry, s * rz), M, seg=sg, rings=rg)
        if mat == 'Eye_Iris':
            paint(bm, lambda co, c=c: grad(IRIS, ((co - c).dot(u) / (s * 1.1) + 1) / 2))
        pieces.append((bm, mat))
    if flush:
        Mt = M.transposed()
        for bm, _ in pieces:
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if (Mt @ (v.co - hit)).z < -0.01 * s], context='VERTS')
            for v in bm.verts:            # wrap onto the head: same height above the surface everywhere
                l = Mt @ (v.co - hit)
                loc, nor, _, _ = bvh.ray_cast(hit + r * l.x + u * l.y + n * 0.5, -n)
                if loc is None:
                    loc, nor = hit + r * l.x + u * l.y, n
                if nor.dot(n) < 0:
                    nor = -nor
                v.co = loc + nor * max(l.z, 0.003)
    elif LOW:                     # back halves of the eye shells sit inside the head: drop them
        for bm, _ in pieces[:3]:
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if (v.co - hit).dot(n) < -0.22 * s], context='VERTS')
    pet.pair('Eye', pieces)
    return hit, n, M


def eye_ring(hit, M, s, a0=0, a1=360, rx=1.32, ry=1.42, extra=()):
    """points on a path around an eye (degrees, 0 = outer side), plus extra (dr, du) points in eye units"""
    r, u = M.col[0], M.col[1]
    pts = []
    steps = max(6, int(abs(a1 - a0) / 12))
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append(hit + r * (math.cos(a) * rx * s) + u * (math.sin(a) * ry * s))
    pts += [hit + r * (dr * s) + u * (du * s) for dr, du in extra]
    return pts


def rat_ears(pet, center, R, n, fur, inner='Ear_Orange'):
    """big round cupped ears: dark rim + back, orange bowl on the front"""
    M = frame(n, Vector((0.25, 0, 1)))
    T = 0.3 * R
    shell = [(0, 0.05 * T), (0.4 * R, 0.08 * T), (0.66 * R, 0.17 * T), (0.82 * R, 0.34 * T), (0.93 * R, 0.52 * T),
             (R, 0.18 * T), (0.97 * R, -0.35 * T), (0.82 * R, -0.62 * T), (0.45 * R, -0.75 * T), (0, -0.78 * T)]
    e = 0.006
    bowl = [(0, 0.05 * T + e), (0.4 * R, 0.08 * T + e), (0.66 * R, 0.17 * T + e), (0.8 * R, 0.31 * T + e)]
    b = revolve(bowl, center, M, sy=1.06)
    b.faces.ensure_lookup_table()
    b.normal_update()
    if b.faces[0].normal.dot(n) < 0:
        bmesh.ops.reverse_faces(b, faces=b.faces)
    pet.pair('Ear', [(revolve(shell, center, M, sy=1.06), fur), (b, inner)])


def cat_ears(pet, base, tip, width, n, fur, inner_stops, flame=None):
    """pointed cat ear: thick rounded cone, coloured inner panel and an optional inner flame"""
    k = 9
    pts = [base + (tip - base) * (i / k) for i in range(k + 1)]
    rad = [(width * (1 - i / k) ** 0.7, width * 0.36 * (1 - i / k) ** 0.7) for i in range(k + 1)]
    pieces = [(tube(pts, rad, lod(20, 12), hint=n), fur)]
    ib, it = base + n * (width * 0.24) + Z * 0.02, tip + (base - tip) * 0.14 + n * (width * 0.07)
    pts = [ib + (it - ib) * (i / k) for i in range(k + 1)]
    rad = [(width * 0.72 * (1 - i / k) ** 0.7, width * 0.14 * (1 - i / k) ** 0.7) for i in range(k + 1)]
    cols = [grad(inner_stops, i / k) for i in range(k + 1)]
    pieces.append((tube(pts, rad, lod(16, 10), hint=n, colors=cols), 'Fire_Gradient' if flame else 'Ear_Gradient'))
    if flame:
        fb = ib + n * (width * 0.08)
        d = (it - ib).normalized()
        pieces.append((tongue(fb, d, (it - ib).length * 0.72, width * 0.32, 0.25, hint=n, stops=flame), 'Fire_Gradient'))
        side = d.cross(n).normalized()
        for s in (-1, 1):
            pieces.append((tongue(fb + d * 0.04 + side * s * width * 0.18, (d + side * s * 0.5), 0.07, width * 0.16,
                                  0.25, hint=n, stops=flame), 'Fire_Gradient'))
    pet.pair('Ear', pieces)


# ---- inflated flame silhouettes traced off the sheet's side views ------------------------------
# Crop-pixel outlines (5x zoom of the sheet). sheet_px() maps them to metres: side-view y (front = -)
# and height z, using the sheet scale of 0.00508 m per sheet pixel.
def sheet_px(pts, x0, y0, side_x, ground_y):
    return [((x0 + px / 5 - side_x) * 0.00508, (ground_y - (y0 + py / 5)) * 0.00508) for px, py in pts]


CAT_TAIL = {   # Cinderkit side view, crop origin (830, 300) on the sheet
    'outer': [(130, 560), (100, 440), (110, 350), (135, 290), (165, 235), (180, 205), (200, 250), (230, 270),
              (255, 215), (262, 150), (245, 95), (222, 52), (285, 65), (350, 100), (405, 160), (440, 230),
              (455, 300), (452, 360), (480, 340), (505, 318), (520, 360), (522, 430), (510, 510), (480, 570),
              (445, 610), (400, 640), (330, 655), (250, 645), (180, 615)],
    'mid': [(175, 620), (160, 530), (190, 450), (215, 390), (250, 340), (290, 310), (318, 285), (330, 350),
            (335, 420), (350, 470), (405, 515), (385, 560), (330, 600), (270, 630)],
    'core': [(150, 650), (140, 560), (150, 450), (195, 520), (230, 470), (255, 560), (330, 610), (260, 660)],
}
RAT_TAIL = {   # Ashrat side view, crop origin (850, 50) on the sheet
    'outer': [(20, 480), (100, 495), (180, 500), (250, 480), (300, 440), (325, 390), (335, 330), (325, 280),
              (300, 230), (260, 205), (220, 205), (190, 225), (180, 260), (195, 290), (225, 300), (215, 325),
              (170, 320), (130, 295), (105, 250), (105, 200), (130, 150), (180, 110), (250, 95), (320, 100),
              (380, 130), (430, 180), (462, 240), (455, 255), (478, 330), (480, 400), (462, 455), (472, 470),
              (440, 520), (390, 590), (320, 630), (220, 665), (120, 665), (30, 650)],
    'mid': [(20, 520), (90, 535), (180, 530), (270, 500), (320, 450), (345, 390), (345, 320), (320, 260),
            (280, 225), (240, 225), (210, 250), (200, 230), (250, 180), (310, 190), (360, 230), (395, 290),
            (410, 370), (390, 450), (340, 520), (260, 570), (150, 590), (20, 560)],
    'core': [(0, 580), (120, 605), (230, 595), (335, 555), (250, 635), (130, 650), (0, 640)],
}


def _resample(poly, step):
    out = []
    for i in range(len(poly)):
        a, b = Vector(poly[i]), Vector(poly[(i + 1) % len(poly)])
        k = max(1, int((b - a).length / step))
        out += [a.lerp(b, j / k) for j in range(k)]
    return out


def _inside(p, poly):
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[i - 1]
        if (a.y > p.y) != (b.y > p.y) and p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x:
            c = not c
    return c


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (p - (a + ab * t)).length


def fill2d(poly, step):
    """even triangle fill of a 2D outline: resampled boundary + staggered interior grid, constrained Delaunay.
    returns (verts, faces, boundary)"""
    from mathutils.geometry import delaunay_2d_cdt
    bnd = _resample([Vector(p) for p in poly], step * 0.7)
    lo = Vector((min(p.x for p in bnd), min(p.y for p in bnd)))
    hi = Vector((max(p.x for p in bnd), max(p.y for p in bnd)))
    pts = list(bnd)
    nb = len(bnd)
    y = lo.y + step * 0.5
    row = 0
    while y < hi.y:
        x = lo.x + step * (0.5 + 0.5 * (row % 2))
        while x < hi.x:
            p = Vector((x, y))
            if _inside(p, bnd) and min(_seg_dist(p, bnd[i], bnd[i - 1]) for i in range(nb)) > step * 0.45:
                pts.append(p)
            x += step
        y += step * 0.87
        row += 1
    verts, _, faces, _, _, _ = delaunay_2d_cdt([p.to_tuple() for p in pts], [(i, (i + 1) % nb) for i in range(nb)],
                                               [], 2, 1e-7)
    return [Vector(v) for v in verts], faces, bnd


def inflated(poly, T, place, n, color, step=None):
    """puffy closed shell from a 2D outline: thickness T * circular profile of the distance to the edge.
    place(u, v) -> world point on the mid-plane, n = plane normal, color(u, v, k) -> rgb (k = 0 rim .. 1 middle)"""
    verts, faces, bnd = fill2d(outline(poly, 3), step or lod(0.015, 0.023))
    nb = len(bnd)
    dist = [min(_seg_dist(v, bnd[i], bnd[i - 1]) for i in range(nb)) for v in verts]
    dmax = max(dist)
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new('Col')
    front, back = [], []
    for v, d in zip(verts, dist):
        k = min(d / dmax, 1.0)
        w = T * math.sqrt(max(0.0, 1 - (1 - k) ** 2))
        c = (*color(v.x, v.y, k), 1.0)
        base = place(v.x, v.y)
        if d < 1e-6:
            fv = bv = bm.verts.new(base)
        else:
            fv, bv = bm.verts.new(base + n * w), bm.verts.new(base - n * w)
            bv[col] = c
        fv[col] = c
        front.append(fv)
        back.append(bv)
    for f in faces:
        try:
            bm.faces.new([front[i] for i in f])
            bm.faces.new([back[i] for i in f][::-1])
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def flame_shell_tail(pet, shapes, crop, base_uv, x_base, slant, scale=1.0, thick=(0.06, 0.082, 0.096)):
    """layered flame tail (yellow shell, orange inner flame, red core) on a slanted vertical plane so it
    reads in the front, side and back views; its side-view silhouette is the outline traced off the sheet"""
    x0, y0, sx, gy = crop
    nrm = Vector((1, -slant, 0)).normalized()
    ub, vb = base_uv

    def place(u, v):
        uu, vv = ub + (u - ub) * scale, vb + (v - vb) * scale
        return Vector((x_base + slant * (uu - ub), uu, vv))
    outer = sheet_px(shapes['outer'], x0, y0, sx, gy)
    vmin, vmax = min(v for _, v in outer), max(v for _, v in outer)
    yellow = [(0, '#f8641a'), (0.3, '#ff8e1e'), (0.62, '#ffb828'), (1, '#ffd84a')]
    pieces = [(inflated(outer, thick[0] * scale, place, nrm,
                        lambda u, v, k: grad(yellow, 0.25 * (1 - k) + 0.75 * (v - vmin) / (vmax - vmin))),
               'Fire_Gradient')]
    for key, T, stops in (('mid', thick[1], [(0, '#f04a1a'), (1, '#ff7a1a')]),
                          ('core', thick[2], [(0, '#a8121a'), (1, '#dc2c1a')])):
        pieces.append((inflated(sheet_px(shapes[key], x0, y0, sx, gy), T * scale, place, nrm,
                                lambda u, v, k, st=stops: grad(st, k)), 'Fire_Gradient'))
    pet.obj('Tail', pieces)


LEAF = [(0.0, -0.55), (0.12, -0.85), (0.32, -1.0), (0.52, -0.88), (0.72, -0.55), (0.88, -0.18), (1.0, 0.16),
        (0.84, 0.22), (0.66, 0.52), (0.44, 0.86), (0.24, 0.92), (0.07, 0.72), (0.0, 0.5)]
LEAF_ORANGE = [(0, '#d8461a'), (0.35, '#f86a16'), (0.7, '#ff9420'), (1, '#ffb62c')]
LEAF_YELLOW = [(0, '#ff8a1c'), (0.4, '#ffb024'), (0.75, '#ffcc34'), (1, '#ffe05a')]
LEAF_GLOW = [(0, '#e8521a'), (0.4, '#ff8a1e'), (0.75, '#ffb428'), (1, '#ffd84a')]


def leaf(base, direction, normal, length, width, stops=LEAF_GLOW, bend=0.0, thick=0.3, flip=False):
    """broad leaf-shaped flame: a puffy 2D flame leaf (S-curved tip) lying in the plane of `direction`
    with its broad face toward `normal`, curling toward the normal by `bend` (fraction of the length).
    Colour: darker at the base and rim, bright in the middle and toward the tip."""
    d = direction.normalized()
    n0 = (normal - normal.dot(d) * d).normalized()
    side = n0.cross(d)
    poly = [(u * length, (-v if flip else v) * width) for u, v in LEAF]

    def place(u, v):
        t = u / length
        return base + d * u + side * v + n0 * (bend * length * t * t)
    return inflated(poly, width * thick, place, n0,
                    lambda u, v, k: grad(stops, 0.5 * (u / length) + 0.5 * k), step=width * lod(0.22, 0.34))


def whiskers(pet, roots, mat, length=0.24):
    """roots: [(point, direction)] on the left side; mirrored to the right"""
    pieces = []
    for a, out in roots:
        b = a + out.normalized() * length
        mid = (a + b) / 2 + Vector((0, 0, -0.012))
        pts = catmull([a, mid, b], lod(4, 2))
        rad = [(0.0035 * (1 - 0.7 * i / (len(pts) - 1)),) * 2 for i in range(len(pts))]
        pieces.append((tube(pts, rad, lod(6, 4)), mat))
    pieces += [(mirror(p[0]), p[1]) for p in pieces]
    pet.obj('Whiskers', pieces)


def soft_triangle(bm, M, tip, depth, k=0.45):
    """pinch the lower half of a nose ellipsoid into a soft inverted triangle"""
    for v in bm.verts:
        lv = M.transposed() @ (v.co - tip)
        v.co -= M.col[0] * lv.x * max(0.0, -lv.y / depth) * k
    return bm


def rat_face(pet, hc, snout, whisker='Whisker_Light'):
    """orange nose at the snout tip, 'w' mouth line, two buck teeth, whiskers"""
    bvh = pet.bvh['Head']
    tip, tn = cast(bvh, snout, Vector((0, -1, 0.35)))
    M = frame(tn)
    pet.obj('Nose', [(soft_triangle(ellipsoid(tip + tn * 0.008, (0.042, 0.03, 0.028), M, ex=2.4), M, tip, 0.03),
                      'Nose_Orange')])
    mz = tip.z - 0.07
    pts = [cast_front(bvh, x, mz + 0.012 * math.cos(x / 0.045 * math.pi))[0] for x in
           [-0.075 + 0.15 * i / 12 for i in range(13)]]
    pet.obj('Mouth', [(ribbon_pts(bvh, hc, pts, 0.01, 0.003), 'Mouth_Line')])
    teeth = []
    for x in (-0.019, 0.019):
        th, _ = cast_front(bvh, x, mz - 0.03)
        teeth.append((ellipsoid(th + Vector((0, -0.008, 0)), (0.017, 0.03, 0.009), frame(Vector((0, -1, -0.25))),
                                seg=16, rings=10, ex=3.2), 'Tooth_White'))
    pet.obj('Teeth', teeth)
    roots = []
    for dz, ang in ((0.0, 0.1), (-0.02, -0.12), (-0.04, -0.3)):
        p, _ = cast_front(bvh, 0.11, tip.z - 0.05 + dz)
        roots.append((p, Vector((1, 0.15, ang))))
    whiskers(pet, roots, whisker)


def cat_face(pet, hc, muzzle, nose_mat, whisker):
    """small triangular nose, open smile with tongue, whiskers"""
    bvh = pet.bvh['Head']
    tip, tn = cast(bvh, muzzle, Vector((0, -1, 0.75)))
    M = frame(tn)
    pet.obj('Nose', [(soft_triangle(ellipsoid(tip + tn * 0.004, (0.034, 0.024, 0.022), M, seg=lod(24, 12), rings=lod(14, 8), ex=2.4), M, tip, 0.024, 0.5),
                      nose_mat)])
    mz = tip.z - 0.06
    mh, mn = cast_front(bvh, 0, mz)
    Mm = frame(mn)
    mouth = [(ellipsoid(mh - mn * 0.01, (0.05, 0.035, 0.02), Mm, seg=lod(20, 12), rings=lod(10, 8)), 'Mouth_Dark'),
             (ellipsoid(mh + mn * 0.004 - Z * 0.022, (0.032, 0.03, 0.016), Mm, seg=lod(18, 10), rings=lod(10, 6)), 'Tongue_Pink')]
    pts = [cast_front(bvh, x, tip.z - 0.03 + 0.01 * math.cos(x / 0.04 * math.pi))[0] for x in
           [-0.07 + 0.14 * i / 12 for i in range(13)]]
    mouth.append((ribbon_pts(bvh, hc, pts, 0.009, 0.003), 'Mouth_Line'))
    pet.obj('Mouth', mouth)
    roots = []
    for dz, ang in ((0.0, 0.12), (-0.025, -0.08), (-0.05, -0.28)):
        p, _ = cast_front(bvh, 0.12, tip.z - 0.035 + dz)
        roots.append((p, Vector((1, 0.2, ang))))
    whiskers(pet, roots, whisker, 0.26)


def markings(pet, spots, outer='Flame_Orange', inner='Flame_Yellow'):
    """flame decals: spots = [(part, direction from the part centre, size, angle, flip)], mirrored"""
    pieces = []
    for part, d, size, ang, flip in spots:
        pieces += flame_decal(pet.bvh[part], pet.center[part], d, size * 1.05, ang, flip, outer, inner)
    pieces += [(mirror(p[0]), p[1]) for p in pieces]
    return pieces


def chest_ruff(pet, y, z, rows):
    """hanging flame bib: rows = [(count, spacing, length, width, stops, dy)], back row first"""
    ruff = []
    for cnt, sp, L, w, st, dy in rows:
        h = (cnt - 1) / 2
        for i in range(cnt):
            x = (i - h) * sp
            ruff.append((tongue(Vector((x * 1.05, y + dy + abs(x) * 0.3, z)), Vector((x * 1.1, -0.15 - dy * 3, -1)),
                                L - abs(x) * 0.4, w, 0.38, Vector((0, -0.04, 0)), hint=Y, stops=st), 'Fire_Gradient'))
    pet.obj('ChestRuff', ruff)


def crest(hb, hc, d, spec):
    """flame crest on top of the head: spec = [(direction, length, width, bend)]"""
    tb, tn = cast(hb, hc, d)
    tb = tb - tn * 0.03
    return [(tongue(tb, dd, L, w, 0.75, b, hint=Y, stops=FIRE, swell=0.38), 'Fire_Gradient') for dd, L, w, b in spec]


# ------------------------------------------------------------------ the four pets
def build_ashrat(pc):
    p = Pet('Ashrat', pc)
    fur = 'Fur_Charcoal'
    p.obj('Body', [(blob([body_bm(0.45, -0.32, 0.3, 0.35, 0.27, 0.19),
                          ellipsoid((0.17, 0.28, 0.26), (0.13, 0.17, 0.16)),
                          ellipsoid((-0.17, 0.28, 0.26), (0.13, 0.17, 0.16)),
                          ellipsoid((0.15, -0.17, 0.27), (0.12, 0.14, 0.15)),
                          ellipsoid((-0.15, -0.17, 0.27), (0.12, 0.14, 0.15))], 4500), fur)])
    hc = Vector((0, -0.31, 0.53))
    snout = Vector((0, -0.57, 0.45))
    p.obj('Head', [(blob([ellipsoid(hc, (0.36, 0.28, 0.28), seg=40, rings=24, ex=2.15),
                          ellipsoid((0.17, -0.45, 0.43), (0.16, 0.14, 0.13)),
                          ellipsoid((-0.17, -0.45, 0.43), (0.16, 0.14, 0.13)),
                          ellipsoid(snout, (0.12, 0.14, 0.1))], 5000), fur)])
    rat_ears(p, Vector((0.33, -0.27, 0.79)), 0.215, Vector((0.5, -0.85, 0.12)), fur)
    legs_and_paws(p, fur, 'Paw_Orange', (0.19, -0.22, 0.24, 0.088), (0.19, 0.3, 0.2, 0.088), (0.105, 0.14, 0.11))
    hit, n, M = eyes(p, 0.155, 0.555, 0.1)
    rat_face(p, hc, snout)
    p.obj('ChestPatch', [(decal(p.bvh['Body'], p.center['Body'], Vector((0, -1, -0.45)),
                                outline([(math.cos(a) * 0.5, math.sin(a) * 0.62 - 0.1) for a in
                                         [2 * math.pi * k / 18 for k in range(18)]], 2), 0.46, offset=0.004),
                          'Fur_EmberBelly')])
    # glowing flame swirl hugging the outer edge of each eye and curling out onto the cheek
    hb = p.bvh['Head']
    sw = eye_ring(hit, M, 0.1, 20, -95, 1.28, 1.36, extra=((0.35, -1.55), (0.95, -1.75), (1.55, -1.6), (1.95, -1.2), (2.05, -0.8), (1.8, -0.62)))
    swirl = [(ribbon_pts(hb, hc, sw, 0.042), 'Flame_Orange'), (ribbon_pts(hb, hc, sw, 0.016, 0.007), 'Flame_Yellow')]
    swirl += [(mirror(s[0]), s[1]) for s in swirl]
    p.obj('CheekSwirls', swirl)
    flame_shell_tail(p, RAT_TAIL, (850, 50, 773, 234.7), (0.41, 0.37), 0.1, 1.5)
    p.obj('FlameMarkings', markings(p, [
        ('Body', Vector((1, -0.6, -0.1)), 0.19, 0.1, False),       # shoulder, down onto the front leg
        ('Body', Vector((1, 0.5, 0.2)), 0.18, -0.35, False),      # flank
        ('Leg_BL', Vector((0.5, 1.0, 0.5)), 0.12, -0.3, True),      # back of the hind leg
        ('Leg_BL', Vector((1, 0.2, 0.3)), 0.13, -0.2, False),
        ('Leg_FL', Vector((1, -0.4, 0.0)), 0.09, 0.0, True),
    ]))
    return p


def build_cinderkit(pc):
    p = Pet('Cinderkit', pc)
    fur = 'Fur_Soot'
    p.obj('Body', [(blob([body_bm(0.47, -0.27, 0.34, 0.36, 0.23, 0.17),
                          ellipsoid((0.14, 0.3, 0.28), (0.11, 0.16, 0.15)),
                          ellipsoid((-0.14, 0.3, 0.28), (0.11, 0.16, 0.15)),
                          ellipsoid((0, -0.2, 0.35), (0.19, 0.16, 0.17))], 4000), fur)])
    hc = Vector((0, -0.34, 0.64))
    muzzle = Vector((0, -0.57, 0.56))
    tufts = []
    for s in (1, -1):        # spiky cheek fluff
        for dz, L in ((0.0, 0.1), (-0.06, 0.08), (0.06, 0.07)):
            tufts.append(tongue(Vector((s * 0.34, -0.41, 0.55 + dz)), Vector((s, 0.05, -0.4 + dz * 4)), L, 0.05, 0.6,
                                stops=None, seg=10))
    p.obj('Head', [(blob([ellipsoid(hc, (0.36, 0.29, 0.27), seg=40, rings=24, ex=2.15),
                          *[ellipsoid((s * 0.22, -0.43, 0.55), (0.17, 0.15, 0.13)) for s in (1, -1)],
                          ellipsoid(muzzle, (0.1, 0.08, 0.075)), ellipsoid((0, -0.5, 0.5), (0.08, 0.07, 0.06)),
                          *tufts], 6000, voxel=0.009, smooth=6), fur)])
    ear_n = Vector((0.3, -1, 0.05)).normalized()
    cat_ears(p, Vector((0.21, -0.28, 0.8)), Vector((0.33, -0.25, 1.13)), 0.175, ear_n, fur,
             [(0, '#d8301a'), (1, '#ff6a14')], flame=FIRE_YELLOW)
    legs_and_paws(p, fur, 'Paw_Amber', (0.165, -0.2, 0.26, 0.08), (0.16, 0.31, 0.24, 0.082), (0.1, 0.13, 0.105))
    hit, n, M = eyes(p, 0.195, 0.62, 0.11)
    cat_face(p, hc, muzzle, 'Nose_Orange', 'Whisker_Light')
    hb = p.bvh['Head']
    glow = [(ribbon_pts(hb, hc, eye_ring(hit, M, 0.104, -120, 40, 1.2, 1.3, extra=((1.55, 0.95), (1.75, 1.35))), 0.026), 'Flame_Orange')]
    glow += [(mirror(g[0]), g[1]) for g in glow]
    peak = [(-0.17, 0.0), (0.17, 0.0), (0.06, -0.3), (0.0, -0.62), (-0.06, -0.3)]   # widow's peak under the crest
    glow.append((decal(hb, hc, Vector((0, -0.65, 0.78)), outline(peak, 2), 0.36, offset=0.005), 'Flame_Orange'))
    p.obj('FaceFlames', glow)
    p.obj('FlameTuft', crest(hb, hc, Vector((0, -0.35, 1)), [
        (Vector((0, 0.1, 1)), 0.33, 0.11, Vector((0, -0.06, 0))),
        (Vector((0.5, 0.05, 1)), 0.25, 0.09, Vector((0.05, 0, 0))),
        (Vector((-0.5, 0.05, 1)), 0.25, 0.09, Vector((-0.05, 0, 0))),
        (Vector((0.95, 0.1, 0.6)), 0.17, 0.075, Vector((0.03, 0, 0.03))),
        (Vector((-0.95, 0.1, 0.6)), 0.17, 0.075, Vector((-0.03, 0, 0.03))),
        (Vector((0, 0.8, 0.75)), 0.22, 0.09, Vector((0, 0, 0.05))),
        (Vector((0.45, 0.7, 0.6)), 0.17, 0.08, Vector((0, 0, 0.04))),
        (Vector((-0.45, 0.7, 0.6)), 0.17, 0.08, Vector((0, 0, 0.04))),
        (Vector((0, -0.6, 0.8)), 0.13, 0.08, Vector((0, -0.02, 0.02)))]))
    chest_ruff(p, -0.34, 0.44, [(7, 0.058, 0.2, 0.075, FIRE_ORANGE, 0.0), (5, 0.062, 0.17, 0.075, FIRE_YELLOW, -0.035)])
    flame_shell_tail(p, CAT_TAIL, (830, 300, 778, 493), (0.4, 0.41), 0.14, 1.3, thick=(0.06, 0.088, 0.105))
    p.obj('FlameMarkings', markings(p, [
        ('Body', Vector((1, -0.4, 0.05)), 0.16, 0.15, False),       # shoulder
        ('Body', Vector((1, 0.45, 0.15)), 0.17, -0.3, False),        # flank
        ('Leg_BL', Vector((0.5, 1.0, 0.4)), 0.12, -0.3, True),      # back of the hind leg
        ('Leg_FL', Vector((1, -0.5, -0.4)), 0.1, 0.0, False),      # flame socks rising from the paws
        ('Leg_BL', Vector((1, -0.2, -0.4)), 0.1, 0.1, True),
        ('Leg_FL', Vector((0, -1, -0.4)), 0.09, 0.0, False),
    ]))
    return p


def build_flarecat(pc):
    """pale-gold cat with a mane of broad leaf flames (crest, cheek flares, neck mane, lotus on the back
    of the head) and a two-layer chest ruff, built in the light game-budget format"""
    global LOW
    LOW = True
    p = Pet('Flarecat', pc)
    fur = 'Fur_PaleGold'
    p.obj('Body', [(blob([body_bm(0.5, -0.27, 0.35, 0.38, 0.26, 0.19),
                          ellipsoid((0.155, 0.32, 0.29), (0.13, 0.18, 0.17)),
                          ellipsoid((-0.155, 0.32, 0.29), (0.13, 0.18, 0.17)),
                          ellipsoid((0, -0.2, 0.37), (0.21, 0.18, 0.18))], 2000), fur)])
    hc = Vector((0, -0.35, 0.67))
    muzzle = Vector((0, -0.57, 0.58))
    p.obj('Head', [(blob([ellipsoid(hc, (0.35, 0.29, 0.27), seg=40, rings=24, ex=2.15),
                          *[ellipsoid((s * 0.21, -0.44, 0.57), (0.16, 0.15, 0.13)) for s in (1, -1)],
                          ellipsoid(muzzle, (0.105, 0.085, 0.078)), ellipsoid((0, -0.51, 0.52), (0.08, 0.07, 0.06))],
                         3000), fur)])
    ear_n = Vector((0.3, -1, 0.05)).normalized()
    cat_ears(p, Vector((0.21, -0.29, 0.83)), Vector((0.33, -0.26, 1.15)), 0.18, ear_n, fur,
             [(0, '#f07a76'), (0.6, '#f4928c'), (1, '#f8b0a4')])
    legs_and_paws(p, fur, 'Paw_Tangerine', (0.17, -0.2, 0.27, 0.095), (0.165, 0.33, 0.25, 0.097),
                  (0.112, 0.14, 0.11))
    eyes(p, 0.19, 0.645, 0.11, flush=True)
    cat_face(p, hc, muzzle, 'Nose_Pink', 'Whisker_Tan')
    hb = p.bvh['Head']
    marks = []
    for x, z in ((0.12, 0.8),):                                   # orange brow dots
        bh, bn = cast_front(hb, x, z)
        marks.append((ellipsoid(bh, (0.034, 0.02, 0.012), frame(bn), seg=12, rings=6), 'Flame_Orange'))
    marks += [(mirror(m[0]), m[1]) for m in marks]
    peak = [(-0.15, 0.0), (0.15, 0.0), (0.05, -0.28), (0.0, -0.55), (-0.05, -0.28)]   # flame point on the forehead
    marks.append((decal(hb, hc, Vector((0, -0.7, 0.75)), outline(peak, 2), 0.3, offset=0.005), 'Flame_Orange'))
    p.obj('BrowMarks', marks)

    mane = []
    # crest: broad leaves fanning up from the forehead, a second row sweeping back over the head
    tb, tn = cast(hb, hc, Vector((0, -0.3, 1)))
    tb = tb - tn * 0.04
    for ang, L, w, st in ((0, 0.34, 0.13, LEAF_YELLOW), (24, 0.29, 0.115, LEAF_GLOW), (-24, 0.29, 0.115, LEAF_GLOW),
                          (50, 0.22, 0.1, LEAF_ORANGE), (-50, 0.22, 0.1, LEAF_ORANGE)):
        a_ = math.radians(ang)
        d = Vector((math.sin(a_), 0.15, math.cos(a_)))
        mane.append((leaf(tb, d, Vector((0, -1, 0.1)), L, w, st, bend=0.18, flip=ang < 0), 'Fire_Gradient'))
    for ang, L, w in ((0, 0.3, 0.13), (30, 0.25, 0.11), (-30, 0.25, 0.11)):
        a_ = math.radians(ang)
        d = Vector((math.sin(a_) * 0.6, 0.75, 0.75))
        mane.append((leaf(tb + Vector((0, 0.06, 0.0)), d, Vector((math.sin(a_), 0.2, 1)), L, w, LEAF_ORANGE, bend=0.12),
                     'Fire_Gradient'))
    # cheek flares: broad orange leaves sweeping out and back from the sides of the face
    for s in (1, -1):
        for dz, L, w, dd in ((0.06, 0.2, 0.09, Vector((1, 0.35, 0.15))), (-0.04, 0.23, 0.1, Vector((1, 0.4, -0.2))),
                             (-0.13, 0.18, 0.085, Vector((1, 0.3, -0.55)))):
            b0 = Vector((s * 0.29, -0.37, 0.57 + dz))
            mane.append((leaf(b0, Vector((s * dd.x, dd.y, dd.z)), Vector((0, -1, 0.1)), L, w, LEAF_ORANGE, bend=-0.12,
                              flip=s < 0), 'Fire_Gradient'))
    # neck mane: big leaves behind the head sweeping back and down toward the shoulders (side view)
    for s in (1, -1):
        for zz, yy, L, w, st in ((0.72, -0.18, 0.26, 0.12, LEAF_GLOW), (0.58, -0.14, 0.27, 0.125, LEAF_ORANGE),
                                 (0.45, -0.17, 0.22, 0.11, LEAF_ORANGE)):
            b0 = Vector((s * 0.2, yy, zz))
            mane.append((leaf(b0, Vector((s * 0.45, 1, -0.35)), Vector((s, 0.1, 0.25)), L, w, st, bend=-0.1,
                              flip=s < 0), 'Fire_Gradient'))
    # lotus over the back of the head: rows of leaves rising upward, yellow on top
    rows = ((60, 3, 0.25, 0.13, LEAF_YELLOW), (36, 5, 0.25, 0.13, LEAF_GLOW), (10, 5, 0.23, 0.125, LEAF_ORANGE),
            (-16, 4, 0.2, 0.115, LEAF_ORANGE))
    for ri, (el, cnt, L, w, st) in enumerate(rows):
        for k in range(cnt):
            az = math.radians(-75 + 150 * (k + 0.5) / cnt)
            ce = math.cos(math.radians(el))
            d = Vector((math.sin(az) * ce, math.cos(az) * ce, math.sin(math.radians(el))))
            base, bn = cast(hb, hc, d)
            up = (Z + bn * 0.5 + Y * 0.2).normalized()
            mane.append((leaf(base - bn * 0.03, up, bn, L, w, st, bend=0.15, flip=k % 2 == 0), 'Fire_Gradient'))
    p.obj('FlameMane', mane)

    # chest ruff: outer orange leaves, inner yellow leaves, hanging from under the chin
    ruff = []
    for i in range(7):
        x = (i - 3) * 0.075
        b0 = Vector((x * 1.1, -0.36 + abs(x) * 0.35, 0.47))
        ruff.append((leaf(b0, Vector((x * 1.6, -0.25, -1)), Vector((x, -1, 0.1)), 0.27 - abs(x) * 0.3, 0.1,
                          LEAF_ORANGE, bend=-0.15, flip=x < 0), 'Fire_Gradient'))
    for i in range(5):
        x = (i - 2) * 0.072
        b0 = Vector((x, -0.42 + abs(x) * 0.35, 0.46))
        ruff.append((leaf(b0, Vector((x * 1.4, -0.4, -1)), Vector((x, -1, 0.2)), 0.22 - abs(x) * 0.35, 0.095,
                          LEAF_YELLOW, bend=-0.15, flip=x > 0), 'Fire_Gradient'))
    p.obj('ChestRuff', ruff)
    flame_shell_tail(p, CAT_TAIL, (830, 300, 778, 493), (0.4, 0.41), 0.14, 1.3, 1.06, thick=(0.06, 0.088, 0.105))
    p.obj('FlameMarkings', markings(p, [
        ('Body', Vector((1, 0.55, 0.15)), 0.15, -0.35, False),     # haunch
        ('Body', Vector((1, -0.35, 0.0)), 0.12, 0.15, False),      # shoulder
        ('Leg_BL', Vector((0.5, 1.0, 0.4)), 0.1, -0.3, True),
        ('Leg_FL', Vector((1, -0.5, -0.1)), 0.1, 0.0, False),
        ('Leg_BL', Vector((1, -0.1, 0.0)), 0.1, 0.1, True),
        ('Leg_FL', Vector((0, -1, -0.1)), 0.08, 0.0, True),
    ], 'Flame_Pale', 'Flame_PaleCore'))
    LOW = False
    return p


def build_smoulderat(pc):
    p = Pet('Smoulderat', pc)
    fur = 'Fur_DarkCharcoal'
    p.obj('Body', [(blob([body_bm(0.56, -0.42, 0.42, 0.44, 0.44, 0.33, taper=0.08, q=2.1, ex=2.15),
                          ellipsoid((0.3, 0.32, 0.3), (0.18, 0.22, 0.21)),
                          ellipsoid((-0.3, 0.32, 0.3), (0.18, 0.22, 0.21)),
                          ellipsoid((0.27, -0.27, 0.3), (0.16, 0.18, 0.19)),
                          ellipsoid((-0.27, -0.27, 0.3), (0.16, 0.18, 0.19))], 5500), fur)])
    hc = Vector((0, -0.48, 0.51))
    snout = Vector((0, -0.75, 0.42))
    p.obj('Head', [(blob([ellipsoid(hc, (0.38, 0.28, 0.28), seg=40, rings=24, ex=2.15),
                          ellipsoid((0.19, -0.62, 0.41), (0.17, 0.14, 0.13)),
                          ellipsoid((-0.19, -0.62, 0.41), (0.17, 0.14, 0.13)),
                          ellipsoid(snout, (0.12, 0.13, 0.1))], 5000), fur)])
    rat_ears(p, Vector((0.41, -0.43, 0.73)), 0.21, Vector((0.55, -0.82, 0.12)), fur)
    legs_and_paws(p, fur, 'Paw_Red', (0.3, -0.3, 0.24, 0.1), (0.3, 0.34, 0.22, 0.1), (0.13, 0.155, 0.12))
    eyes(p, 0.165, 0.5, 0.1)
    rat_face(p, hc, snout)
    p.obj('ChestPatch', [(decal(p.bvh['Body'], p.center['Body'], Vector((0, -1, -0.5)),
                                outline([(math.cos(a) * 0.6, math.sin(a) * 0.4) for a in
                                         [2 * math.pi * k / 18 for k in range(18)]], 2), 0.5, offset=0.004),
                          'Fur_BrownBelly')])
    # crystal crown on the head and a ridge of crystals along the spine (biggest at the shoulders)
    rng = random.Random(5)
    hb, bb = p.bvh['Head'], p.bvh['Body']
    crown = []
    for d, h, r in ((Vector((0, 0.05, 1)), 0.4, 0.095), (Vector((0.28, 0.0, 1)), 0.3, 0.08),
                    (Vector((-0.28, 0.0, 1)), 0.3, 0.08), (Vector((0.52, 0.1, 1)), 0.2, 0.062),
                    (Vector((-0.52, 0.1, 1)), 0.2, 0.062), (Vector((0.14, -0.32, 1)), 0.16, 0.055),
                    (Vector((-0.14, -0.32, 1)), 0.15, 0.055), (Vector((0, -0.58, 1)), 0.09, 0.04)):
        hit_c, nc = cast(hb, hc, d)
        crown.append((crystal(hit_c, (nc * 0.6 + d.normalized() * 0.4 + Z * 0.5).normalized(), h, r,
                              rng.uniform(0, 1)), 'Crystal_Gradient'))
    p.obj('HeadCrystals', crown, smooth=False)
    ridge = []
    bc = p.center['Body']
    K = 7
    for i in range(K):
        t = i / (K - 1)
        y = -0.2 + 0.68 * t
        h = 0.36 - 0.2 * t
        hit_r, nr = cast(bb, bc, Vector((0, y - bc.y, 0.5)))
        ridge.append((crystal(hit_r, (nr + Y * 0.45 + Z * 0.3).normalized(), h, 0.085 - 0.03 * t, rng.uniform(0, 1)),
                      'Crystal_Gradient'))
        if i in (0, 2):
            for s in (-1, 1):
                hit_s, ns = cast(bb, bc, Vector((s * 0.22, y - bc.y + 0.05, 0.5)))
                ridge.append((crystal(hit_s, (ns + Y * 0.4 + X * s * 0.3).normalized(), h * 0.55,
                                      0.045 - 0.015 * t, rng.uniform(0, 1)), 'Crystal_Gradient'))
    p.obj('BackCrystals', ridge, smooth=False)
    # glowing lava fissures: cracked-rock network over the body, cracks from the eyes, legs
    rng = random.Random(21)
    fis = []

    def lava(bvh, c, paths, w):
        for path in paths:
            fis.append((ribbon(bvh, c, path, w * 2.6, 0.003, taper=False), 'Lava_Glow'))
            fis.append((ribbon(bvh, c, path, w, 0.006, taper=False), 'Lava_Core'))
    lava(bb, bc, voronoi_paths(rng, 46, lambda d: d.z > -0.42 and d.x > 0.02, jitter=0.05, sub=7), 0.011)
    for d0, hd in ((Vector((1, -0.35, -0.1)), Vector((0.2, 1, -0.3))), (Vector((0.8, -0.6, -0.35)), Vector((0.5, 0.2, -1)))):
        lava(hb, hc, crack_walk(rng, d0, hd, 4, 0.12, 0.4, 0.4), 0.009)
    for leg in ('Leg_FL', 'Leg_BL'):
        lava(p.bvh[leg], p.center[leg], crack_walk(rng, Vector((1, -0.3, 0.6)), Vector((0, 0.2, -1)), 4, 0.35, 0.5), 0.009)
    fis += [(mirror(f[0]), f[1]) for f in fis]
    p.obj('LavaFissures', fis)
    flame_shell_tail(p, {k: [(x + 108, y) for x, y in v] for k, v in RAT_TAIL.items()}, (850, 50, 773, 234.7),
                     (0.52, 0.37), 0.12, 1.5, 1.18)
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
    g = link(st, bpy.data.objects.new('Studio_Ground', me))
    g.is_shadow_catcher = True      # renders as the grey backdrop with soft contact shadows
    for name, loc, energy, size, color in (
            ('Light_Key', (-5.0, -7.0, 7.0), 1500, 7.0, (1.0, 0.97, 0.93)),
            ('Light_Fill', (7.0, -5.0, 3.5), 600, 8.0, (0.94, 0.96, 1.0)),
            ('Light_Rim', (0.0, 7.0, 5.0), 900, 7.0, (1.0, 1.0, 1.0)),
            ('Light_SideFill', (10.0, 1.0, 3.0), 450, 6.0, (1.0, 1.0, 1.0)),
            ('Light_Top', (0.0, 0.0, 8.0), 700, 10.0, (1.0, 1.0, 1.0))):
        li = bpy.data.lights.new(name, 'AREA')
        li.energy, li.size, li.color = energy, size, color
        o = link(st, bpy.data.objects.new(name, li))
        o.location = loc
        look(o, (0, 0, 0.4))
    w = bpy.data.worlds.new('World_NeutralStudio')
    sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (*srgb('#a9a9ac'), 1)
    bg.inputs['Strength'].default_value = 0.75


def build_cameras(sc):
    cc = bpy.data.collections.new('CAMERAS')
    sc.collection.children.link(cc)
    t = math.tan(CAM_TILT)
    for pet, x in PET_X.items():
        sub = bpy.data.collections.new(f'{pet}_Cams')
        cc.children.link(sub)
        cx = x + 0.12
        for view, loc, tgt, clip in (('Front', (cx, -8.0, CAM_H + 8 * t), (cx, 0, CAM_H), 30.0),
                                     ('Side', (x + 1.35, 0.05, CAM_H + 1.35 * t), (x, 0.05, CAM_H), 2.3),
                                     ('Back', (cx, 8.0, CAM_H + 8 * t), (cx, 0, CAM_H), 30.0)):
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
    o.location = (-7.0, -10.5, 4.4)
    look(o, (0.2, 0, 0.4))
    sc.camera = o
    cam = bpy.data.cameras.new('CAM_Lineup_Front')
    cam.type = 'ORTHO'
    cam.ortho_scale = 10.4
    o = link(cc, bpy.data.objects.new(cam.name, cam))
    o.location = (0.2, -12, CAM_H + 12 * t)
    look(o, (0.2, 0, CAM_H))


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
        o.hide_render = True
        return o
    for pet, x in PET_X.items():
        text(f'Label_{pet}_Name', pet.upper(), (x, -1.55, 0.005), 0.3)
        text(f'Label_{pet}_Front', 'FRONT  (-Y)', (x, -1.12, 0.005), 0.12)
        text(f'Label_{pet}_Side', 'SIDE  (+X)', (x + 1.15, 0.05, 0.005), 0.12, math.pi / 2)
        text(f'Label_{pet}_Back', 'BACK  (+Y)', (x, 1.3, 0.005), 0.12, math.pi)


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    build_materials()
    material('Ear_Gradient', '#f39a96', 0.6, vcol=True)
    pc = bpy.data.collections.new('PETS')
    sc.collection.children.link(pc)
    for fn in (build_ashrat, build_cinderkit, build_flarecat, build_smoulderat):
        pet = fn(pc)
        pet.place(PET_X[pet.name])
    build_studio(sc)
    build_cameras(sc)
    build_labels(sc)
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    return sc


def render_previews(sc, out, only=None, samples=48, prefix='FirePets'):
    os.makedirs(out, exist_ok=True)
    sc.cycles.samples = samples
    shots = []
    W, H = 720, 500
    sc.render.resolution_x, sc.render.resolution_y = W, H
    for pet in PET_X:
        for view in ('Front', 'Side', 'Back'):
            sc.camera = bpy.data.objects[f'CAM_{pet}_{view}']
            sc.render.filepath = os.path.join(out, f'{prefix}_{pet}_{view}.png')
            if not only or pet in only:
                bpy.ops.render.render(write_still=True)
            shots.append(sc.render.filepath)
    if not only:
        sc.render.resolution_x, sc.render.resolution_y = 1600, 900
        sc.cycles.samples = 64
        for cam in ('CAM_Overview_ThreeQuarter', 'CAM_Lineup_Front'):
            sc.camera = bpy.data.objects[cam]
            sc.render.filepath = os.path.join(out, f'{prefix}_{cam[4:]}.png')
            bpy.ops.render.render(write_still=True)
    sc.camera = bpy.data.objects['CAM_Overview_ThreeQuarter']
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return
    LW, TH = 380, 40
    sheet = Image.new('RGB', (LW + 3 * W, len(PET_X) * (H + TH)), (170, 170, 172))
    dr = ImageDraw.Draw(sheet)
    try:
        big = ImageFont.truetype('DejaVuSans-Bold.ttf', 46)
        small = ImageFont.truetype('DejaVuSans-Bold.ttf', 24)
    except OSError:
        big = small = ImageFont.load_default()
    for r, pet in enumerate(PET_X):
        y0 = r * (H + TH)
        dr.text((30, y0 + TH + H // 2 - 26), pet, fill=(40, 40, 44), font=big)
        for c, view in enumerate(('FRONT', 'SIDE', 'BACK')):
            if os.path.exists(shots[r * 3 + c]):
                sheet.paste(Image.open(shots[r * 3 + c]).convert('RGB'), (LW + c * W, y0 + TH))
            dr.text((LW + c * W + W // 2 - 40, y0 + 8), view, fill=(40, 40, 44), font=small)
        if r:
            dr.line((0, y0, sheet.width, y0), fill=(120, 120, 124), width=2)
    sheet.save(os.path.join(out, f'{prefix}_Turnaround.png'))


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
        out = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith('--') else os.path.join(HERE, '..', 'previews')
        only = argv[argv.index('--only') + 1].split(',') if '--only' in argv else None
        samples = int(argv[argv.index('--samples') + 1]) if '--samples' in argv else 48
        render_previews(sc, os.path.abspath(out), only, samples)


if __name__ == '__main__':
    main()
