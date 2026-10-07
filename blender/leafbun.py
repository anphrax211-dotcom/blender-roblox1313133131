"""LEAFBUN - Nature / Common pet. Chunky low-poly toy-style leaf bunny for Roblox.

Game-scale dimensions (metric, 1 unit = 1 m; ~1 m = 3.5 studs in Roblox):
    overall          : ~1.84 m tall to the ear-leaf tips (~6.4 studs)
                       ~1.06 m wide across the ears x ~1.10 m deep (nose to tail leaves)
    body             : 0.69 m wide x 0.66 m deep x 0.64 m tall (z 0.07 - 0.71) + two round haunches
    head             : 0.75 m wide x 0.68 m deep x 0.64 m tall, centre at z = 0.92
    ears             : leaf ~0.44 m wide x 0.66 m long on a cream ear, tips at 1.79 / 1.84 m
    eyes             : ~0.22 m tall each
    feet             : 0.21 x 0.30 x 0.16 m, soles on z = 0 (the ground plane)
    leaf tail        : ~0.31 x 0.37 x 0.47 m tuft on the lower back (z 0.25 - 0.72)
    flower bud       : ~0.15 m, at the front of the left ear base
59 small mesh objects / ~6.7k triangles in total (incl. bevels) - light enough for Roblox Studio.
Creature is centred on the world origin, standing upright on the ground, facing -Y.
Every part is a separate editable mesh in the `Leafbun` collection, with rotation/scale
applied (identity transforms) and its origin at the centre (or base) of the part.

Run in Blender (Scripting tab -> Run Script) or headless:
    blender -b -P leafbun.py
    python3 leafbun.py          (with the `bpy` pip module)
Saves Leafbun.blend next to this script and prints the full path, then exports
Leafbun.fbx for Roblox Studio to ../exports (or next to the script if that folder is missing).
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

BODY_C, BODY_R = Vector((0.0, 0.02, 0.37)), Vector((0.36, 0.33, 0.34))
HEAD_C, HEAD_R = Vector((0.0, -0.06, 0.92)), Vector((0.39, 0.34, 0.32))
MUZZLE_C, MUZZLE_R = Vector((0.0, -0.33, 0.82)), Vector((0.16, 0.08, 0.1))
CAM_DIR = Vector((-0.48, -0.88, 0.0))      # towards the three-quarter camera (for leaf facing)

MATS = {}
SURF = {}      # name -> BVHTree of a finished part (world space), for sticking parts onto it
COLL = None


# ------------------------------------------------------------------ materials
def material(name, srgb, rough=0.42, coat=0.3, emit=0.0, spec=0.5):
    """lightly glossy toy plastic. `srgb` is the 0-255 colour (= Roblox Color3.fromRGB)"""
    lin = tuple(((c / 255) / 12.92) if c / 255 <= 0.04045 else (((c / 255) + 0.055) / 1.055) ** 2.4
                for c in srgb)
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = 0.25
    b.inputs['Specular IOR Level'].default_value = spec
    if emit:
        b.inputs['Emission Color'].default_value = (*lin, 1)
        b.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = (*lin, 1)
    MATS[name] = m


def build_materials():
    material('Fur_Cream', (238, 228, 192), 0.45, 0.25)    # soft cream: head, body, arms, feet, ear backs
    material('Belly_LightGreen', (170, 214, 118), 0.45, 0.25)
    material('Paw_Green', (92, 172, 50), 0.4, 0.3)       # bright green paws / toes
    material('Leaf_Green', (86, 164, 48), 0.4, 0.3)       # ear leaves, patches, tail
    material('Leaf_DarkGreen', (58, 140, 40), 0.4, 0.3)
    material('Leaf_LightGreen', (150, 206, 82), 0.4, 0.3)
    material('Leaf_Vein', (214, 236, 140), 0.4, 0.3)
    material('Eye_Rim', (28, 86, 38), 0.3, 0.4)
    material('Eye_Green', (88, 178, 64), 0.25, 0.5, emit=0.1)
    material('Eye_Pupil', (16, 26, 16), 0.2, 0.5)
    material('Eye_Highlight', (255, 255, 255), 0.2, 0.0, emit=1.0)
    material('Nose_Pink', (240, 140, 160), 0.35, 0.4)
    material('Mouth_Dark', (128, 40, 52), 0.4, 0.2)
    material('Tongue_Pink', (238, 128, 140), 0.4, 0.3)
    material('Teeth_White', (250, 248, 240), 0.3, 0.5)
    material('Bud_White', (252, 238, 238), 0.4, 0.3)
    material('Bud_Pink', (242, 158, 180), 0.4, 0.3)


# ------------------------------------------------------------------ helpers
def new_object(name, bm, mat, bevel=0.0, center=None, surface=False, solidify=0.0):
    """bmesh (world coords) -> flat-shaded object with origin at `center` (or the
    vertex centroid) and identity rotation/scale"""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if surface:
        SURF[name] = BVHTree.FromBMesh(bm)
    if center is None:
        center = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    for v in bm.verts:
        v.co -= center
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS[mat])
    me.shade_flat()
    ob = bpy.data.objects.new(name, me)
    ob.location = center
    COLL.objects.link(ob)
    if solidify:
        so = ob.modifiers.new('Solidify', 'SOLIDIFY')
        so.thickness, so.offset = solidify, -1.0
    if bevel:
        bv = ob.modifiers.new('Bevel', 'BEVEL')
        bv.width, bv.segments = bevel, 1
        bv.limit_method = 'ANGLE'
        bv.angle_limit = math.radians(35)
    return ob


def frame(normal, up=Vector((0, 0, 1))):
    """3x3 matrix whose columns are (side, up-ish, normal): local Z -> normal"""
    z = Vector(normal).normalized()
    x = up.cross(z)
    if x.length < 1e-5:
        x = Vector((1, 0, 0))
    x.normalize()
    return Matrix((x, z.cross(x), z)).transposed()


def ellipsoid_bm(center, radii, sub=2, shape=None, jitter=0.0, seed=0):
    """low-poly icosphere -> ellipsoid; `shape(d)` returns a per-vertex scale vector
    from the unit direction d so the blob can be pear/cheek shaped"""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        s = shape(d) if shape else Vector((1, 1, 1))
        k = 1 + rnd.uniform(-jitter, jitter)
        v.co = Vector((d.x * radii[0] * s.x, d.y * radii[1] * s.y, d.z * radii[2] * s.z)) * k + Vector(center)
    return bm


def dir_of(theta, phi):
    """theta: around Z, 0 = front (-Y), +90 = creature's left (+X); phi: elevation (degrees)"""
    t, p = math.radians(theta), math.radians(phi)
    return Vector((math.sin(t) * math.cos(p), -math.cos(t) * math.cos(p), math.sin(p)))


def hit(surf, center, direction):
    """point + face normal where a ray from inside `surf` along `direction` leaves it"""
    tree = SURF[surf]
    d = Vector(direction).normalized()
    loc, nrm, _, _ = tree.ray_cast(Vector(center) + d * 3.0, -d)
    return loc, nrm


def decal(name, surf, center, direction, outline, mat, thick=0.02, sink=0.5, dome=0.012, spin=0.0,
          bevel=0.0):
    """flat faceted plate hugging a part: `outline` is a 2D polygon (metres) in the tangent
    plane at the point where `direction` leaves `surf`; every vertex is projected back onto
    the real faceted surface, half sunk in so it stays attached. A raised centre vertex gives
    it a gem-like facet."""
    p, n = hit(surf, center, direction)
    M = frame(n) @ Matrix.Rotation(spin, 3, 'Z')
    tree = SURF[surf]
    bm = bmesh.new()
    top, bot = [], []
    for (u, w) in outline:
        q = p + M @ Vector((u, w, 0))
        loc, nn, _, _ = tree.ray_cast(q + n * 0.5, -n)
        if loc is None:
            loc, nn = q, n
        top.append(bm.verts.new(loc + n * thick * (1 - sink)))
        bot.append(bm.verts.new(loc - n * thick * sink))
    apex = bm.verts.new(sum((v.co for v in top), Vector()) / len(top) + n * dome)
    k = len(outline)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((top[i], top[j], apex))
        bm.faces.new((bot[j], bot[i], top[i], top[j]))
    bm.faces.new(bot[::-1])
    return new_object(name, bm, mat, bevel=bevel, center=p)


def lens(name, center, normal, rx, rz, depth, mat, segs=14, up=Vector((0, 0, 1))):
    """low-poly rounded disc (eye parts), dome facing along `normal`"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=6, radius=1.0)
    M = frame(normal, up)
    for v in bm.verts:
        z = v.co.z
        v.co = M @ Vector((v.co.x * rx, v.co.y * rz, z * depth * (0.3 if z < 0 else 1.0))) + Vector(center)
    return new_object(name, bm, mat, center=Vector(center))


def lathe_bm(profile, segs, center, normal, up=Vector((0, 0, 1))):
    """revolve (radius, height) profile around local Z (=normal); first/last points on axis"""
    bm = bmesh.new()
    M = frame(normal, up)
    rings = []
    for r, h in profile:
        if r < 1e-6:
            rings.append([bm.verts.new(M @ Vector((0, 0, h)) + Vector(center))])
        else:
            rings.append([bm.verts.new(M @ Vector((r * math.cos(a), r * math.sin(a), h)) + Vector(center))
                          for a in (2 * math.pi * i / segs for i in range(segs))])
    for A, B in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(A) == 1:
                bm.faces.new((A[0], B[j], B[i]))
            elif len(B) == 1:
                bm.faces.new((A[i], A[j], B[0]))
            else:
                bm.faces.new((A[i], A[j], B[j], B[i]))
    return bm


def loft_bm(path, radii, segs=7, flat=None):
    """tube along a polyline with rotation-minimising frames; closed ends.
    `flat` optionally squashes the cross-section (x scale per ring)"""
    bm = bmesh.new()
    rings = []
    nrm = None
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        if nrm is None:
            nrm = t.orthogonal().normalized()
        nrm = (nrm - t * nrm.dot(t)).normalized()
        b = t.cross(nrm)
        sx = flat[i] if flat else 1.0
        rings.append([bm.verts.new(p + (nrm * math.cos(a) * sx + b * math.sin(a)) * radii[i])
                      for a in (2 * math.pi * k / segs for k in range(segs))])
    for A, B in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((A[k], A[(k + 1) % segs], B[(k + 1) % segs], B[k]))
    for ring, p, sgn in ((rings[0], path[0], -1), (rings[-1], path[-1], 1)):
        t = (path[-1] - path[-2]) if sgn > 0 else (path[0] - path[1])
        cap = bm.verts.new(p + t.normalized() * radii[0 if sgn < 0 else -1] * 0.6)
        for k in range(segs):
            bm.faces.new((ring[k], ring[(k + 1) % segs], cap) if sgn > 0 else (ring[(k + 1) % segs], ring[k], cap))
    return bm


def bezier(pts, n):
    """sample a Catmull-Rom spline through pts into n points"""
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


def shell(name, src_bm, center, scale, keep, mat, solidify=0.02):
    """colour patch: copy of a part's mesh inflated about `center`, keeping only the faces
    whose centre direction passes keep(d). The cut follows the facets, like the art."""
    bm = src_bm.copy()
    kill = [f for f in bm.faces if not keep((f.calc_center_median() - center).normalized())]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    for v in bm.verts:
        v.co = center + (v.co - center) * scale
    return new_object(name, bm, mat, center=Vector(center), solidify=solidify)


def merge(dst, src):
    """append bmesh `src` into `dst` (src is freed)"""
    me = bpy.data.meshes.new('tmp')
    src.to_mesh(me)
    src.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)
    return dst


def xform(bm, M, origin):
    for v in bm.verts:
        v.co = M @ v.co + Vector(origin)
    return bm


def axes(up, facing):
    """3x3 matrix: local Y -> `up`, local Z -> `facing` (made perpendicular), local X = Y x Z"""
    y = Vector(up).normalized()
    z = Vector(facing)
    z = (z - y * z.dot(y)).normalized()
    return Matrix((y.cross(z), y, z)).transposed()


# ------------------------------------------------------------------ leaves
def leaf_halfwidth(t, W):
    return W * 0.5 * math.sin(math.pi * t) ** 0.7 * (1 - 0.2 * t)


def leaf_z(x, t, L, fold, curl):
    """front surface height of a leaf: V-fold along the midrib, tip curling back"""
    return fold * abs(x) - curl * t * t * L


def leaf_bm(L, W, thick=0.04, fold=0.15, curl=0.05, n=7):
    """chunky broad leaf in local space: base at origin, tip along +Y, front along +Z.
    The V-fold along the midrib gives the two-tone faceted halves seen in the art."""
    bm = bmesh.new()
    base = bm.verts.new((0, 0, -thick * 0.3))
    tip = bm.verts.new((0, L, leaf_z(0, 1, L, fold, curl) - thick * 0.3))
    rows = []
    for i in range(1, n):
        t = i / n
        w = leaf_halfwidth(t, W)
        row = {}
        for key, x in (('L', -w), ('M', 0.0), ('R', w)):
            z = leaf_z(x, t, L, fold, curl)
            edge = key != 'M'
            row[key + 't'] = bm.verts.new((x, t * L, z + (thick * 0.2 if edge else thick * 0.5)))
            row[key + 'b'] = bm.verts.new((x, t * L, z - (thick * 0.2 if edge else thick * 0.5)))
        rows.append(row)
    F = bm.faces.new
    for end, row in ((base, rows[0]), (tip, rows[-1])):
        F((end, row['Lt'], row['Mt']))
        F((end, row['Mt'], row['Rt']))
        F((end, row['Mb'], row['Lb']))
        F((end, row['Rb'], row['Mb']))
        F((end, row['Lb'], row['Lt']))
        F((end, row['Rt'], row['Rb']))
    for a, b in zip(rows, rows[1:]):
        F((a['Lt'], b['Lt'], b['Mt'], a['Mt']))
        F((a['Mt'], b['Mt'], b['Rt'], a['Rt']))
        F((a['Lb'], a['Mb'], b['Mb'], b['Lb']))
        F((a['Mb'], a['Rb'], b['Rb'], b['Mb']))
        F((a['Lt'], a['Lb'], b['Lb'], b['Lt']))
        F((a['Rt'], b['Rt'], b['Rb'], a['Rb']))
    return bm


def veins_bm(L, W, thick, fold, curl, sides=(0.26, 0.44, 0.62), r=0.011):
    """raised vein lines lying on a leaf_bm front: midrib + angled side veins"""
    def on(x, t, lift=0.004):
        return Vector((x, t * L, leaf_z(x, t, L, fold, curl) + thick * 0.5 + lift))
    bm = loft_bm([on(0, t) for t in (0.05, 0.3, 0.55, 0.75, 0.9)], [r, r, r * 0.9, r * 0.75, r * 0.5], segs=4)
    for t0 in sides:
        for s in (-1, 1):
            t1 = t0 + 0.15
            x1 = s * 0.78 * leaf_halfwidth(t1, W)
            pts = [on(0, t0), on(x1 * 0.5, (t0 + t1) / 2 - 0.01), on(x1, t1)]
            merge(bm, loft_bm(pts, [r * 0.8, r * 0.7, r * 0.45], segs=4))
    return bm


def leaf_outline(L, W, n=5):
    """2D leaf outline (for flat leaf patches), centred, tip along +Y"""
    right = [(leaf_halfwidth(i / n, W), (i / n - 0.5) * L) for i in range(1, n)]
    left = [(-x, y) for x, y in right[::-1]]
    return [(0, -0.5 * L)] + right + [(0, 0.5 * L)] + left


def leaf_object(name, origin, up, facing, L, W, mat, thick=0.04, fold=0.15, curl=0.05, bevel=0.004):
    M = axes(up, facing)
    return new_object(name, xform(leaf_bm(L, W, thick, fold, curl), M, origin), mat, bevel=bevel,
                      center=Vector(origin))


# ------------------------------------------------------------------ body
def build_body():
    def pear(d):     # rounder, wider bottom; narrower shoulders under the head
        w = 1.0 + 0.1 * (-d.z) - 0.08 * max(d.z, 0)
        return Vector((w, w, 1.0))
    bm = ellipsoid_bm(BODY_C, BODY_R, 2, pear, 0.012, 1)
    for v in bm.verts:                      # flattened underside
        v.co.z = max(v.co.z, 0.07)
    src = bm.copy()
    new_object('Body', bm, 'Fur_Cream', center=BODY_C.copy(), surface=True)
    # big light-green belly oval on the front
    shell('Belly', src, BODY_C, 1.015,
          lambda d: d.y < -0.42 and abs(d.x) < 0.62 and -0.75 < d.z < 0.5, 'Belly_LightGreen')
    src.free()
    # round hind haunches bulging at the lower sides
    for s, side in ((-1, 'Right'), (1, 'Left')):
        c = Vector((s * 0.25, 0.08, 0.21))
        bm = ellipsoid_bm(c, (0.16, 0.23, 0.18), 2, None, 0.015, 5 + s)
        for v in bm.verts:
            v.co.z = max(v.co.z, 0.06)
        new_object(f'Haunch_{side}', bm, 'Fur_Cream', center=c, surface=True)


# ------------------------------------------------------------------ head
def build_head():
    def cheeks(d):   # slightly puffy lower cheeks
        w = 1.0 + 0.06 * max(0.0, 1 - abs(d.z + 0.3) * 2.5)
        return Vector((w, 1.0, 1.0))
    bm = ellipsoid_bm(HEAD_C, HEAD_R, 2, cheeks, 0.01, 2)
    new_object('Head', bm, 'Fur_Cream', center=HEAD_C.copy(), surface=True)

    # soft cream muzzle bump on the lower face
    bm = ellipsoid_bm(MUZZLE_C, MUZZLE_R, 2, None, 0.0, 3)
    new_object('Muzzle', bm, 'Fur_Cream', center=MUZZLE_C.copy(), surface=True)

    # tiny pink nose: small rounded downward triangle
    p, n = hit('Muzzle', MUZZLE_C, (0, -0.8, 0.6))
    c = p + n * 0.006
    bm = bmesh.new()
    M = frame(n)
    tri = [(-0.034, 0.016), (0.034, 0.016), (0.0, -0.022)]
    top = [bm.verts.new(M @ Vector((u, w, 0.012)) + c) for u, w in tri]
    bot = [bm.verts.new(M @ Vector((u * 0.8, w * 0.8, -0.016)) + c) for u, w in tri]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    new_object('Nose', bm, 'Nose_Pink', bevel=0.006, center=c)

    # open friendly smile (dark) with a pink tongue, just under the nose
    smile = [(-0.075, 0.018), (-0.04, 0.008), (0.0, 0.006), (0.04, 0.008), (0.075, 0.018),
             (0.06, -0.022), (0.03, -0.05), (0.0, -0.058), (-0.03, -0.05), (-0.06, -0.022)]
    mouth_dir = (0, -1, -0.42)
    decal('Mouth', 'Muzzle', MUZZLE_C, mouth_dir, smile, 'Mouth_Dark', thick=0.02, sink=0.5, dome=-0.004)
    p, n = hit('Muzzle', MUZZLE_C, mouth_dir)
    tongue = [(-0.035, -0.022), (0.0, -0.012), (0.035, -0.022), (0.025, -0.044), (0.0, -0.05), (-0.025, -0.044)]
    decal('Tongue', 'Muzzle', MUZZLE_C, mouth_dir, tongue, 'Tongue_Pink', thick=0.02, sink=0.2, dome=0.002)
    # two small front teeth hanging from the top lip
    for s, side in ((-1, 'Right'), (1, 'Left')):
        c = p + n * 0.012 + Vector((s * 0.019, 0, -0.014))
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * 0.034, v.co.y * 0.02, v.co.z * 0.042)) + c
        new_object(f'Tooth_{side}', bm, 'Teeth_White', bevel=0.007, center=c)

    # little cream tuft on the crown
    for i, (dx, lean) in enumerate(((-0.03, -0.5), (0.035, 0.4))):
        p, n = hit('Head', HEAD_C, (dx, -0.15, 1))
        tip = p + Vector((lean * 0.05, -0.02, 0.08))
        bm = loft_bm([p - n * 0.03, p.lerp(tip, 0.5), tip], [0.045, 0.028, 0.004], segs=5)
        new_object(f'Head_Tuft_{i + 1}', bm, 'Fur_Cream', center=p)


def build_eyes():
    for s, side in ((-1, 'Right'), (1, 'Left')):
        d = dir_of(s * 31, -4)
        p, _ = hit('Head', HEAD_C, d)
        n = (d * 0.55 + Vector((0, -1, 0)) * 0.45).normalized()
        inward = Vector((-s, 0, 0))
        lens(f'Eye_{side}_Rim', p - n * 0.01, n, 0.098, 0.112, 0.022, 'Eye_Rim', 16)
        lens(f'Eye_{side}', p + n * 0.0, n, 0.086, 0.1, 0.016, 'Eye_Green', 16)
        lens(f'Eye_{side}_Pupil', p + n * 0.011 + inward * 0.01, n, 0.056, 0.068, 0.01, 'Eye_Pupil', 14)
        F = frame(n)
        xax, up = F.col[0], F.col[1]
        lens(f'Eye_{side}_Highlight', p + n * 0.02 + xax * 0.03 + up * 0.035, n, 0.024, 0.026, 0.007,
             'Eye_Highlight', 8)
        lens(f'Eye_{side}_Highlight_Small', p + n * 0.018 - xax * 0.022 - up * 0.032, n, 0.011, 0.011, 0.005,
             'Eye_Highlight', 6)


# ------------------------------------------------------------------ ears
EAR = dict(L=0.66, W=0.44, thick=0.045, fold=0.16, curl=0.04)


def ear_frame(s):
    """ear base on the crown + axes. s = -1 creature's right (tilts out more, as in the art)"""
    tilt = math.radians(25 if s < 0 else 14)
    base = HEAD_C + Vector((s * 0.15, 0.03, 0.2))
    up = Vector((s * math.sin(tilt), 0.12, math.cos(tilt)))
    facing = Vector((s * 0.22, -1, 0))
    return base, axes(up, facing)


def build_ears():
    """oversized upright rabbit ears: a cream ear stalk with a broad green leaf over its
    front, plus raised light vein lines"""
    for s, side in ((-1, 'Right'), (1, 'Left')):
        base, M = ear_frame(s)
        inner = -s        # local X towards the head centre
        # cream ear (rounded, flattened petal) - shows along the inner edge and at the base
        bm = ellipsoid_bm(Vector((inner * 0.035, 0.27, -0.025)), (0.095, 0.33, 0.05), 2, None, 0.0, 9)
        new_object(f'Ear_{side}', xform(bm, M, base), 'Fur_Cream', center=base.copy())
        # broad leaf over the front, shifted outward so the cream edge peeks out
        lo = base + M @ Vector((-inner * 0.03, 0.1, 0.03))
        new_object(f'Ear_{side}_Leaf', xform(leaf_bm(**EAR), M, lo), 'Leaf_Green', bevel=0.004,
                   center=lo.copy())
        new_object(f'Ear_{side}_LeafVeins', xform(veins_bm(**EAR), M, lo), 'Leaf_Vein', center=lo.copy())


# ------------------------------------------------------------------ limbs
def build_arms_and_feet():
    for s, side in ((-1, 'Right'), (1, 'Left')):
        sh = Vector((s * 0.25, -0.13, 0.58))
        elbow = Vector((s * 0.27, -0.29, 0.46))
        wrist = Vector((s * 0.2, -0.36, 0.37))
        bm = loft_bm(bezier([sh, elbow, wrist], 5), [0.085, 0.08, 0.075, 0.07, 0.065], segs=7)
        new_object(f'Arm_{side}', bm, 'Fur_Cream', center=sh)
        # bright green mitten paw with three little toe bumps
        pc = wrist + Vector((0, -0.02, -0.04))
        bm = ellipsoid_bm(pc, (0.085, 0.075, 0.08), 1)
        for i in range(3):
            merge(bm, ellipsoid_bm(pc + Vector((-0.04 + 0.04 * i, -0.06, -0.045)), (0.028, 0.03, 0.03), 1))
        new_object(f'Paw_{side}', bm, 'Paw_Green', bevel=0.004, center=pc)

        # rounded cream foot with a green toe cap
        c = Vector((s * 0.21, -0.17, 0.07))
        bm = ellipsoid_bm(c, (0.12, 0.18, 0.085), 1)
        for v in bm.verts:
            v.co.z = max(v.co.z, 0.0)
        new_object(f'Foot_{side}', bm, 'Fur_Cream', bevel=0.005, center=c)
        tc = c + Vector((0, -0.13, -0.01))
        bm = ellipsoid_bm(tc, (0.11, 0.07, 0.065), 1)
        for i in range(3):
            merge(bm, ellipsoid_bm(tc + Vector((-0.055 + 0.055 * i, -0.045, -0.012)), (0.035, 0.035, 0.045), 1))
        for v in bm.verts:
            v.co.z = max(v.co.z, 0.0)
        new_object(f'Foot_{side}_Toes', bm, 'Paw_Green', bevel=0.004, center=tc)


# ------------------------------------------------------------------ leaf patches
def build_leaf_patches():
    # cheeks: two leaves on the creature's right cheek, two on the left (as in the art)
    for name, th, ph, L, W, spin in (('Leaf_Cheek_Right_1', -52, -18, 0.13, 0.07, 50),
                                     ('Leaf_Cheek_Right_2', -40, -34, 0.11, 0.06, -20),
                                     ('Leaf_Cheek_Left_1', 60, -14, 0.12, 0.065, -40),
                                     ('Leaf_Cheek_Left_2', 72, 2, 0.09, 0.05, -10)):
        decal(name, 'Head', HEAD_C, dir_of(th, ph), leaf_outline(L, W), 'Leaf_Green',
              thick=0.022, sink=0.3, dome=0.01, spin=math.radians(spin))
    # small green spots on the forehead
    dot = [(math.cos(a) * 0.022, math.sin(a) * 0.022) for a in (i * math.pi / 3 for i in range(6))]
    for i, (th, ph) in enumerate(((0, 40), (-20, 31), (24, 30))):
        decal(f'Forehead_Spot_{i + 1}', 'Head', HEAD_C, dir_of(th, ph), dot, 'Leaf_Green',
              thick=0.016, sink=0.3, dome=0.004)
    # leaves on the haunch, side and back
    for name, surf, c, th, ph, L, W, spin, mat in (
            ('Leaf_Haunch_Right_1', 'Haunch_Right', Vector((-0.25, 0.08, 0.21)), -95, 30, 0.17, 0.085, 30, 'Leaf_Green'),
            ('Leaf_Haunch_Right_2', 'Haunch_Right', Vector((-0.25, 0.08, 0.21)), -70, 5, 0.15, 0.075, -35, 'Leaf_LightGreen'),
            ('Leaf_Side_Right', 'Body', BODY_C, -80, 35, 0.15, 0.075, 60, 'Leaf_Green'),
            ('Leaf_Back_1', 'Body', BODY_C, 165, 30, 0.17, 0.085, 20, 'Leaf_Green'),
            ('Leaf_Back_2', 'Body', BODY_C, 205, 12, 0.15, 0.075, -30, 'Leaf_LightGreen'),
            ('Leaf_Haunch_Left', 'Haunch_Left', Vector((0.25, 0.08, 0.21)), 95, 25, 0.15, 0.075, -30, 'Leaf_Green')):
        decal(name, surf, c, dir_of(th, ph), leaf_outline(L, W), mat,
              thick=0.022, sink=0.3, dome=0.012, spin=math.radians(spin))


# ------------------------------------------------------------------ tail + bud
def build_tail():
    """small layered leaf tuft for a cotton tail: cream puff + five fanned leaves"""
    c = Vector((-0.07, 0.35, 0.46))
    bm = ellipsoid_bm(c, (0.1, 0.09, 0.1), 1, None, 0.04, 21)
    new_object('Tail', bm, 'Fur_Cream', center=c)
    back = Vector((-0.55, 0.84, 0.0)).normalized()
    for i, (elev, L, W, mat) in enumerate(((-42, 0.27, 0.17, 'Leaf_DarkGreen'), (-10, 0.34, 0.2, 'Leaf_Green'),
                                           (20, 0.36, 0.2, 'Leaf_LightGreen'), (50, 0.3, 0.18, 'Leaf_Green'),
                                           (80, 0.24, 0.15, 'Leaf_DarkGreen'))):
        e = math.radians(elev)
        up = back * math.cos(e) + Vector((0, 0, 1)) * math.sin(e)
        o = c + up * 0.03 + CAM_DIR * (0.015 * (i % 2))
        leaf_object(f'Tail_Leaf_{i + 1}', o, up, -CAM_DIR + Vector((0, 0, 0.2)), L, W, mat,
                    thick=0.035, fold=0.22, curl=0.06)


def build_flower_bud():
    """tiny pale bud with pink tips nestled in leaves at the front of the left ear base"""
    base, M = ear_frame(1)
    c = base + M @ Vector((0.15, 0.06, 0.1))
    a = Vector((0.55, -0.25, 0.8)).normalized()
    bud = lathe_bm([(0, -0.007), (0.05, 0.0), (0.073, 0.042), (0.07, 0.084), (0.045, 0.126), (0, 0.147)], 6, c, a)
    new_object('Flower_Bud', bud, 'Bud_White', bevel=0.003, center=c)
    tip = lathe_bm([(0, 0.07), (0.076, 0.077), (0.064, 0.112), (0.036, 0.147), (0, 0.17)], 6, c, a)
    new_object('Flower_Bud_Tip', tip, 'Bud_Pink', bevel=0.003, center=c)
    # green sepals cupping the bud + two small leaves behind it
    side = a.cross(Vector((0, -1, 0))).normalized()
    bm = bmesh.new()
    for k in range(3):
        ang = 2 * math.pi * k / 3 + 0.4
        out = (side * math.cos(ang) + a.cross(side) * math.sin(ang)).normalized()
        up = (a + out * 0.55).normalized()
        merge(bm, xform(leaf_bm(0.105, 0.07, 0.02, 0.1, 0.0, 4), axes(up, out), c + out * 0.028 - a * 0.007))
    for k, (dx, L) in enumerate(((-0.9, 0.2), (0.6, 0.17))):
        up = (a * 0.4 + side * dx).normalized()
        merge(bm, xform(leaf_bm(L, 0.11, 0.03, 0.15, 0.03, 5), axes(up, Vector((0, -1, 0.3))), c - a * 0.01))
    new_object('Flower_Leaves', bm, 'Leaf_Green', bevel=0.003, center=c)


# ------------------------------------------------------------------ scene
def build_camera_and_lights():
    sc = bpy.context.scene
    lc = bpy.data.collections.new('CameraAndLights')
    sc.collection.children.link(lc)
    target = Vector((-0.12, 0.0, 0.9))
    cam = bpy.data.cameras.new('Camera_ThreeQuarter')
    cam.lens = 62
    co = bpy.data.objects.new('Camera_ThreeQuarter', cam)
    co.location = (-2.6, -4.75, 1.6)
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

    area('Light_Key', (-2.8, -3.2, 3.4), 190, 3.0, (1.0, 0.97, 0.93))    # soft warm key
    area('Light_Fill', (3.0, -3.0, 1.8), 80, 3.5, (0.94, 0.96, 1.0))    # soft cool fill
    area('Light_Rim', (0.8, 3.2, 3.0), 150, 2.5)                         # rim from behind
    w = bpy.data.worlds.new('World_Studio')
    sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.86, 0.85, 0.83, 1)
    bg.inputs['Strength'].default_value = 0.5
    me = bpy.data.meshes.new('Ground_ShadowCatcher')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6)
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new('Ground_ShadowCatcher', me)
    g.is_shadow_catcher = True
    lc.objects.link(g)
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.render.resolution_x = sc.render.resolution_y = 1080
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'


def export_fbx():
    """Roblox FBX: only the Leafbun meshes, bevels/solidify baked in, one colour per mesh,
    1 unit = 1 m, identity transforms. Goes to ../exports when it exists."""
    out_dir = os.path.join(HERE, '..', 'exports')
    out_dir = os.path.abspath(out_dir if os.path.isdir(out_dir) else HERE)
    path = os.path.join(out_dir, 'Leafbun.fbx')
    for o in bpy.context.scene.objects:
        o.select_set(o.name in COLL.objects)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'},
                             use_mesh_modifiers=True, mesh_smooth_type='FACE', apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL',
                             add_leaf_bones=False, path_mode='STRIP')
    for o in bpy.context.scene.objects:
        o.select_set(False)
    return path


def main():
    global COLL
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    COLL = bpy.data.collections.new('Leafbun')
    sc.collection.children.link(COLL)
    build_materials()
    build_body()
    build_head()
    build_eyes()
    build_ears()
    build_arms_and_feet()
    build_leaf_patches()
    build_tail()
    build_flower_bud()
    build_camera_and_lights()
    path = os.path.join(HERE, 'Leafbun.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    meshes = [o for o in COLL.objects if o.type == 'MESH']
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    print(f'Leafbun: {len(meshes)} mesh objects, ~{tris} triangles (before bevels)')
    print('Saved:', path)
    print('Exported FBX:', export_fbx())


if __name__ == '__main__':
    main()
