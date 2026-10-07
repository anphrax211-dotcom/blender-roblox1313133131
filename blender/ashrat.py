"""ASHRAT - Fire / Common pet. Chunky low-poly toy-style ember rat for Roblox.

Game-scale dimensions (metric, 1 unit = 1 m; ~1 m = 3.5 studs in Roblox):
    overall          : ~1.65 m tall to the ear tops (1.77 m to the tail-flame tip)
                       ~1.29 m wide across the ears (1.70 m incl. the tail) x ~1.37 m deep
    body             : 0.88 m wide x 0.81 m deep x 0.78 m tall (z 0.08 - 0.86)
    head             : 0.92 m wide x 0.80 m deep x 0.73 m tall, centre at z = 1.04
    ears             : 0.58 m across each, tops at 1.65 m
    eyes             : ~0.34 m tall each
    feet             : 0.21 x 0.33 x 0.14 m, soles on z = 0 (the ground plane)
    tail             : curves back and up behind the creature's right side, flame at ~1.2 - 1.77 m
Creature is centred on the world origin, standing on the ground, facing -Y.
Every part is a separate editable mesh in the `Ashrat` collection, with rotation/scale
applied (identity transforms) and its origin at the centre of the part.
50 small mesh objects / ~4.7k triangles in total (incl. bevels) - light enough for Roblox Studio.

Run in Blender (Scripting tab -> Run Script) or headless:
    blender -b -P ashrat.py
    python3 ashrat.py          (with the `bpy` pip module)
Saves Ashrat.blend next to this script and prints the full path, then exports
Ashrat.fbx for Roblox Studio to ../exports (or next to the script if that folder is missing).
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

BODY_C, BODY_R = Vector((0.0, 0.02, 0.45)), Vector((0.46, 0.41, 0.41))
HEAD_C, HEAD_R = Vector((0.0, -0.10, 1.04)), Vector((0.47, 0.40, 0.37))
MUZZLE_C, MUZZLE_R = Vector((0.0, -0.42, 0.87)), Vector((0.2, 0.14, 0.135))

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
    material('Fur_Charcoal', (62, 45, 43))           # warm charcoal: head top, back, ears, arms, feet
    material('Fur_RedBrown', (140, 56, 38))          # reddish-brown: face, tail, head tuft
    material('Fur_LightRedBrown', (176, 84, 56))     # lighter red-brown: muzzle, belly
    material('Ear_GlowOrange', (255, 104, 6), 0.6, 0.0, emit=1.1, spec=0.1)
    material('Ear_GlowYellow', (255, 180, 30), 0.6, 0.0, emit=1.2, spec=0.1)
    material('Ember_Orange', (255, 122, 24), 0.35, 0.3, emit=0.6)    # ember markings / particles
    material('Ember_Brow', (214, 92, 46), 0.4, 0.3, emit=0.3)       # red-orange brow shards
    material('Eye_Rim', (48, 26, 20), 0.3, 0.4)
    material('Eye_Amber', (240, 138, 16), 0.25, 0.5, emit=0.15)
    material('Eye_Pupil', (24, 14, 12), 0.2, 0.5)
    material('Eye_Highlight', (255, 255, 255), 0.2, 0.0, emit=1.0)
    material('Nose_Dark', (122, 48, 44), 0.3, 0.5)
    material('Mouth_Dark', (58, 22, 20), 0.4, 0.2)
    material('Teeth_White', (248, 244, 234), 0.3, 0.5)
    material('Flame_Orange', (255, 112, 16), 0.4, 0.0, emit=1.2)
    material('Flame_Yellow', (255, 200, 60), 0.4, 0.0, emit=1.4)


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


def diamond(length, width, skew=0.0):
    """ember shard outline: long pointed diamond (6 points) along local Y"""
    return [(0, length * 0.5), (width * 0.42, length * (0.12 + skew)), (width * 0.5, -length * 0.05),
            (0, -length * 0.5), (-width * 0.5, -length * 0.02), (-width * 0.4, length * (0.18 + skew))]


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


# ------------------------------------------------------------------ body
def build_body():
    def pear(d):     # wider, rounder bottom; slightly narrower shoulders
        w = 1.0 + 0.08 * (-d.z) - 0.04 * max(d.z, 0)
        return Vector((w, w, 1.0))
    bm = ellipsoid_bm(BODY_C, BODY_R, 2, pear, 0.015, 1)
    for v in bm.verts:                      # flatten the underside a little
        v.co.z = max(v.co.z, 0.08)
    src = bm.copy()
    new_object('Body', bm, 'Fur_Charcoal', center=BODY_C.copy(), surface=True)
    # lighter red-brown belly over the front of the body
    shell('Belly', src, BODY_C, 1.018,
          lambda d: d.y < -0.3 and abs(d.x) < 0.7 and d.z < 0.55, 'Fur_LightRedBrown')
    # reddish-brown lower sides / hips wrapping round from the belly
    shell('Body_LowerFur', src, BODY_C, 1.009,
          lambda d: d.z < 0.3 - 0.6 * d.y and d.y < -0.05, 'Fur_RedBrown')
    src.free()


# ------------------------------------------------------------------ head
def build_head():
    def cheeks(d):   # puffy lower cheeks, slightly flattened crown
        w = 1.0 + 0.07 * max(0.0, 1 - abs(d.z + 0.25) * 2.5)
        return Vector((w, 1.0, 1.0 - 0.04 * max(d.z, 0)))
    bm = ellipsoid_bm(HEAD_C, HEAD_R, 2, cheeks, 0.012, 2)
    src = bm.copy()
    new_object('Head', bm, 'Fur_Charcoal', center=HEAD_C.copy(), surface=True)
    # reddish-brown face mask: lower head and around the eyes, charcoal V on the forehead
    def face(d):
        rise = -0.12 + 0.6 * max(0.0, -d.y) - 0.7 * max(0.0, d.y)
        if d.y < 0 and abs(d.x) < 0.16:
            rise -= 0.2                    # charcoal widow's peak between the eyes
        return d.z < rise
    shell('Face', src, HEAD_C, 1.012, face, 'Fur_RedBrown')
    src.free()

    # muzzle: short rounded snout on the lower front of the face
    def snout(d):
        return Vector((1.0 + 0.1 * max(0, -d.z), 1.0, 1.0))
    bm = ellipsoid_bm(MUZZLE_C, MUZZLE_R, 2, snout, 0.02, 3)
    new_object('Muzzle', bm, 'Fur_LightRedBrown', center=MUZZLE_C.copy(), surface=True)

    # small dark nose on the muzzle tip: rounded, slightly triangular
    p, n = hit('Muzzle', MUZZLE_C, (0, -0.85, 0.5))
    bm = ellipsoid_bm(p, (0.06, 0.04, 0.042), 1, lambda d: Vector((1 + 0.25 * max(d.z, 0), 1, 1)))
    new_object('Nose', bm, 'Nose_Dark', bevel=0.004, center=p)

    # open friendly smile: crescent set into the muzzle front
    smile = []
    for i in range(9):                      # top lip edge, gently curved up at the corners
        u = -0.12 + 0.24 * i / 8
        smile.append((u, 0.012 + 0.6 * u * u))
    for i in range(1, 8):                   # deep lower curve back to the start
        u = 0.11 - 0.22 * i / 8
        smile.append((u, -0.075 * math.cos(u / 0.12 * math.pi / 2) - 0.005))
    decal('Mouth', 'Muzzle', MUZZLE_C, (0, -1, -0.32), smile, 'Mouth_Dark',
          thick=0.02, sink=0.5, dome=-0.004)

    # two little white front teeth hanging from the top lip
    p, n = hit('Muzzle', MUZZLE_C, (0, -1, -0.3))
    for s, side in ((-1, 'Right'), (1, 'Left')):
        c = p + Vector((s * 0.024, -0.006, -0.018))
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * 0.042, v.co.y * 0.026, v.co.z * 0.058 + (0.0 if v.co.z < 0 else 0)))
            v.co = Matrix.Rotation(-0.35, 3, 'X') @ v.co + c
        new_object(f'Tooth_{side}', bm, 'Teeth_White', bevel=0.008, center=c)

    # head tuft: three short red-brown spikes on the crown between the ears
    for i, (dx, h, lean) in enumerate(((-0.05, 0.14, -0.35), (0.04, 0.17, 0.0), (0.12, 0.12, 0.4))):
        p, n = hit('Head', HEAD_C, Vector((dx, 0.18, 1)))
        tip = p + Vector((lean * 0.12, 0.09, h))
        bm = loft_bm([p - n * 0.03, p.lerp(tip, 0.5), tip], [0.06, 0.035, 0.004], segs=5)
        new_object(f'Head_Tuft_{i + 1}', bm, 'Fur_RedBrown', center=p)


def build_eyes():
    for s, side in ((-1, 'Right'), (1, 'Left')):
        d = dir_of(s * 31, -1)
        p, _ = hit('Head', HEAD_C, d)
        n = (d * 0.6 + Vector((0, -1, 0)) * 0.4).normalized()      # eyes look mostly forward
        inward = Vector((-s, 0, 0))
        lens(f'Eye_{side}_Rim', p - n * 0.006, n, 0.15, 0.168, 0.03, 'Eye_Rim', 16)
        lens(f'Eye_{side}', p + n * 0.006, n, 0.128, 0.146, 0.022, 'Eye_Amber', 16)
        lens(f'Eye_{side}_Pupil', p + n * 0.022 + inward * 0.018 + Vector((0, 0, -0.008)), n,
             0.072, 0.092, 0.014, 'Eye_Pupil', 14)
        xax = frame(n).col[0]
        up = frame(n).col[1]
        lens(f'Eye_{side}_Highlight', p + n * 0.034 + xax * 0.045 + up * 0.05, n, 0.03, 0.034, 0.008,
             'Eye_Highlight', 8)
        lens(f'Eye_{side}_Highlight_Small', p + n * 0.032 - xax * 0.02 - up * 0.045, n, 0.014, 0.014, 0.006,
             'Eye_Highlight', 6)


def build_ears():
    """oversized round cup ears: charcoal shell, glowing orange inner, yellow hot centre"""
    shell_prof = [(0, -0.045), (0.16, -0.05), (0.26, -0.03), (0.295, 0.0), (0.29, 0.04),
                  (0.255, 0.06), (0.225, 0.045), (0.2, 0.012), (0, 0.0)]
    for s, side in ((-1, 'Right'), (1, 'Left')):
        c = Vector((s * 0.37, 0.02, 1.36))
        n = Vector((s * 0.38, -0.88, 0.16)).normalized()
        up = Vector((s * 0.3, 0, 1))
        new_object(f'Ear_{side}', lathe_bm(shell_prof, 14, c, n, up), 'Fur_Charcoal', bevel=0.006, center=c)
        inner = lathe_bm([(0, 0.022), (0.12, 0.022), (0.21, 0.016), (0.215, -0.005), (0, -0.01)], 14, c, n, up)
        new_object(f'Ear_{side}_Inner', inner, 'Ear_GlowOrange', center=c)
        core = lathe_bm([(0, 0.03), (0.07, 0.028), (0.095, 0.02), (0, 0.012)], 10,
                        c + n * 0.0 + up.normalized() * -0.03, n, up)
        new_object(f'Ear_{side}_InnerGlow', core, 'Ear_GlowYellow', center=c)


# ------------------------------------------------------------------ limbs
def build_arms_and_feet():
    for s, side in ((-1, 'Right'), (1, 'Left')):
        sh = Vector((s * 0.32, -0.16, 0.66))
        elbow = Vector((s * 0.33, -0.36, 0.5))
        paw = Vector((s * 0.21, -0.5, 0.57))
        bm = loft_bm(bezier([sh, elbow, paw], 5), [0.1, 0.095, 0.09, 0.085, 0.08], segs=7)
        # stubby paw with three little fingers folded downward
        pb = ellipsoid_bm(paw + Vector((0, -0.02, -0.01)), (0.095, 0.08, 0.085), 1)
        for i in range(3):
            f = ellipsoid_bm(paw + Vector((s * (-0.045 + 0.045 * i) * 0.9, -0.075, -0.065)),
                             (0.034, 0.036, 0.036), 1)
            me = bpy.data.meshes.new('tmp')
            f.to_mesh(me)
            f.free()
            pb.from_mesh(me)
            bpy.data.meshes.remove(me)
        me = bpy.data.meshes.new('tmp')
        pb.to_mesh(me)
        pb.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        new_object(f'Arm_{side}', bm, 'Fur_Charcoal', center=sh)

        # small feet: flat soles on the ground, three toes poking out in front of the belly
        c = Vector((s * 0.23, -0.2, 0.06))
        bm = ellipsoid_bm(c, (0.12, 0.16, 0.08), 1, lambda d: Vector((1 + 0.15 * max(-d.y, 0), 1, 1)))
        for i in range(3):
            t = ellipsoid_bm(c + Vector((s * 0.0 + (-0.065 + 0.065 * i), -0.16, -0.015)), (0.04, 0.05, 0.045), 1)
            me = bpy.data.meshes.new('tmp')
            t.to_mesh(me)
            t.free()
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
        for v in bm.verts:
            v.co.z = max(v.co.z, 0.0)
        new_object(f'Foot_{side}', bm, 'Fur_Charcoal', bevel=0.006, center=c)


# ------------------------------------------------------------------ tail + flame
TAIL_PTS = [Vector(p) for p in ((-0.12, 0.30, 0.30), (-0.36, 0.56, 0.2), (-0.66, 0.68, 0.3),
                                  (-0.88, 0.66, 0.58), (-0.94, 0.56, 0.92), (-0.9, 0.46, 1.18),
                                  (-0.8, 0.4, 1.3))]


def build_tail():
    path = bezier(TAIL_PTS, 17)
    radii = []
    for i in range(len(path)):
        t = i / (len(path) - 1)
        r = 0.1 * (1 - t) + 0.042 * t
        radii.append(r * (1.07 if i % 2 else 0.95))     # subtle segment rings like the art
    new_object('Tail', loft_bm(path, radii, segs=7), 'Fur_RedBrown', center=path[0])
    return path


def build_flame(path):
    """simple low-poly flame tuft wrapped around the tail tip: orange outer + yellow core"""
    tip = path[-1]
    up = (path[-1] - path[-3]).normalized().lerp(Vector((0, 0, 1)), 0.6).normalized()
    side = Vector((0.35, -0.94, 0)).cross(up).normalized()     # roughly screen-horizontal, curls tip outward

    def flame(scale, seed):
        rnd = random.Random(seed)
        spine = [tip - up * 0.05 * scale, tip + up * 0.06 * scale,
                 tip + up * 0.17 * scale + side * 0.02 * scale,
                 tip + up * 0.28 * scale + side * 0.05 * scale, tip + up * 0.36 * scale + side * 0.1 * scale]
        rad = [0.05 * scale, 0.115 * scale, 0.105 * scale, 0.06 * scale, 0.006]
        bm = loft_bm(spine, rad, segs=7)
        for v in bm.verts:
            v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.012 * scale
        return bm, spine

    bm, spine = flame(1.25, 7)
    # two side tongues licking up off the main flame
    for k, (off, h, l) in enumerate(((-1, 0.11, 0.21), (1, 0.08, 0.16))):
        b = tip + up * h + side * off * 0.09
        t = b + up * l + side * off * 0.06
        tb = loft_bm([b, b.lerp(t, 0.5) + side * off * 0.02, t], [0.065, 0.045, 0.004], segs=5)
        me = bpy.data.meshes.new('tmp')
        tb.to_mesh(me)
        tb.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    new_object('Tail_Flame', bm, 'Flame_Orange', center=tip.copy())
    toward_cam = Vector((-0.45, -0.89, 0.0))
    core, _ = flame(0.7, 8)
    for v in core.verts:
        v.co += toward_cam * 0.045 + up * 0.0
    new_object('Tail_Flame_Core', core, 'Flame_Yellow', center=tip.copy())


# ------------------------------------------------------------------ embers
def build_markings():
    # brows: angled red-orange shards above each eye (outer end higher)
    for s, side in ((-1, 'Right'), (1, 'Left')):
        decal(f'Ember_Brow_{side}', 'Head', HEAD_C, dir_of(s * 30, 33), diamond(0.21, 0.065), 'Ember_Brow',
              thick=0.026, sink=0.3, dome=0.01, spin=math.radians(s * 68))
        decal(f'Ember_Cheek_{side}', 'Head', HEAD_C, dir_of(s * 66, -16), diamond(0.15, 0.085), 'Ember_Orange',
              thick=0.026, sink=0.3, dome=0.014, spin=math.radians(-s * 55))
    # back / shoulder ember shards (mostly on the creature's right side, as in the art)
    for name, th, ph, L, W, spin in (('Ember_Shoulder_Right', -78, 22, 0.2, 0.1, 30),
                                     ('Ember_Back_Right', -118, 8, 0.27, 0.12, -20),
                                     ('Ember_Hip_Right', -128, -26, 0.16, 0.08, 40),
                                     ('Ember_Back_Left', 115, 15, 0.22, 0.1, 25)):
        decal(name, 'Body', BODY_C, dir_of(th, ph), diamond(L, W), 'Ember_Orange',
              thick=0.024, dome=0.016, spin=math.radians(spin))


def build_particles(path):
    """a few tiny floating ember diamonds around the tail flame and body"""
    tip = path[-1]
    spots = [tip + Vector((-0.22, -0.05, 0.12)), tip + Vector((0.08, -0.1, 0.42)),
             tip + Vector((-0.24, 0.0, 0.42)), tip + Vector((0.22, -0.05, -0.05)),
             Vector((-0.62, 0.3, 0.55)), Vector((0.55, -0.3, 0.42))]
    for i, c in enumerate(spots):
        s = 0.028 if i < 4 else 0.024
        bm = bmesh.new()
        for co in ((0, 0, 1.5), (0, 0, -1.5), (1, 0, 0), (-1, 0, 0), (0, 0.5, 0), (0, -0.5, 0)):
            bm.verts.new(Vector(co) * s)
        bm.verts.ensure_lookup_table()
        V = bm.verts
        for a, b in ((2, 4), (4, 3), (3, 5), (5, 2)):
            bm.faces.new((V[0], V[a], V[b]))
            bm.faces.new((V[1], V[b], V[a]))
        R = Matrix.Rotation(0.4 * i, 3, 'Z') @ Matrix.Rotation(0.3, 3, 'Y')
        for v in bm.verts:
            v.co = R @ v.co + c
        new_object(f'Ember_Particle_{i + 1}', bm, 'Ember_Orange', center=c)


# ------------------------------------------------------------------ scene
def build_camera_and_lights():
    sc = bpy.context.scene
    lc = bpy.data.collections.new('CameraAndLights')
    sc.collection.children.link(lc)
    target = Vector((-0.15, 0.0, 0.84))
    cam = bpy.data.cameras.new('Camera_ThreeQuarter')
    cam.lens = 55
    co = bpy.data.objects.new('Camera_ThreeQuarter', cam)
    co.location = (-2.65, -4.75, 1.65)
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

    area('Light_Key', (-2.8, -3.2, 3.4), 320, 3.0, (1.0, 0.96, 0.92))    # soft warm key
    area('Light_Fill', (3.0, -3.0, 1.8), 130, 3.5, (0.93, 0.95, 1.0))    # soft cool fill
    area('Light_Rim', (0.8, 3.2, 3.0), 200, 2.5)                         # rim from behind
    w = bpy.data.worlds.new('World_Studio')
    sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.85, 0.83, 0.81, 1)
    bg.inputs['Strength'].default_value = 0.75
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
    """Roblox FBX: only the Ashrat meshes, bevels/solidify baked in, one colour per mesh,
    1 unit = 1 m (same settings as exports/Boulderbub.fbx). Goes to ../exports when it exists."""
    out_dir = os.path.join(HERE, '..', 'exports')
    out_dir = os.path.abspath(out_dir if os.path.isdir(out_dir) else HERE)
    path = os.path.join(out_dir, 'Ashrat.fbx')
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
    COLL = bpy.data.collections.new('Ashrat')
    sc.collection.children.link(COLL)
    build_materials()
    build_body()
    build_head()
    build_eyes()
    build_ears()
    build_arms_and_feet()
    path = build_tail()
    build_flame(path)
    build_markings()
    build_particles(path)
    build_camera_and_lights()
    path = os.path.join(HERE, 'Ashrat.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    meshes = [o for o in COLL.objects if o.type == 'MESH']
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    print(f'Ashrat: {len(meshes)} mesh objects, ~{tris} triangles (before bevels)')
    print('Saved:', path)
    print('Exported FBX:', export_fbx())


if __name__ == '__main__':
    main()
