"""WATER PETS - Bogtoad, Bubbletoad, Puddlepup and Rainhound (Common, Water type), modelled from the
water-pet turnaround sheet in the same style and pipeline as fire_pets.py (whose helpers this reuses).

Proportions are measured off the sheet's front / side / back views on the same shared scale as the fire pets
(0.00508 m per sheet pixel). Every pet is built in the light game-budget format (fire_pets.LOW): seamless
remeshed heads and bodies, decal spots / raindrops, puffy inflated moss clovers, flush wrapped eyes.

Scene layout (1 unit = 1 m, Z up, every pet faces -Y and stands on z = 0):
    PETS/<Pet>            one collection per pet; parts parented to `<Pet>_Root` (move the empty to move it)
    STUDIO                shadow-catcher ground plane, soft area lights, neutral grey world
    CAMERAS/<Pet>_Cams    orthographic CAM_<Pet>_Front / _Side / _Back (+X side view, head on the left like
                          the sheet), CAM_Overview_ThreeQuarter, CAM_Lineup_Front
    LABELS                names + FRONT / SIDE / BACK ground markers (viewport only)

    Bogtoad x = -3.9   Bubbletoad x = -1.3   Puddlepup x = 1.3   Rainhound x = 3.9

Run:  python3 water_pets.py                       -> saves WaterPets.blend next to this file
      python3 water_pets.py --render ../previews  -> also renders the turnaround cameras + comparison sheet
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import fire_pets as fp
from fire_pets import (X, Y, Z, Pet, blob, ellipsoid, tube, catmull, body_bm, paint, grad, frame, mirror, cast,
                       cast_front, decal, outline, inflated, material, srgb, soft_triangle, ribbon_pts, whiskers)

WATER_X = {'Bogtoad': -3.9, 'Bubbletoad': -1.3, 'Puddlepup': 1.3, 'Rainhound': 3.9}

IRIS_AMBER = [(0, '#f6b84a'), (0.35, '#e8862a'), (0.7, '#b8521a'), (1, '#5a2410')]
IRIS_INDIGO = [(0, '#8ab8ff'), (0.35, '#3c6ae0'), (0.7, '#23339c'), (1, '#121a5c')]
IRIS_SKY = [(0, '#9fe6ff'), (0.35, '#3cb4f0'), (0.7, '#1f6ac8'), (1, '#10306e')]
MOSS = [(0, '#6eaa22'), (0.5, '#94d032'), (1, '#c0ef55')]
CLOUD = [(0, '#58a8e6'), (0.45, '#9fd2f4'), (1, '#eef8ff')]
EAR_HOUND = [(0, '#2246b2'), (0.55, '#2a5cc8'), (0.8, '#46a2e6'), (1, '#86d8f6')]


# ------------------------------------------------------------------ materials
def glass(name, hexcol, transmission=0.85, rough=0.04, emit=0.0, coat=0.8):
    """clear glossy water material (bubbles, the water-drop tail and topknot)"""
    m = bpy.data.materials.new(name)
    rgb = srgb(hexcol)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['IOR'].default_value = 1.33
    b.inputs['Transmission Weight'].default_value = transmission
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = 0.05
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = (*rgb, 1)
    fp.MATS[name] = m


def build_water_materials():
    fp.build_materials()                                   # eyes, mouth, tongue, ground, labels ...
    material('Vcol_Matte', '#ffffff', 0.6, vcol=True)
    material('Vcol_Glossy', '#ffffff', 0.35, coat=0.4, vcol=True)
    material('Eye_IrisV', '#3c6ae0', 0.25, emit=0.15, coat=0.8, vcol=True)
    material('Eye_White', '#ffffff', 0.25, coat=0.6)
    material('Nose_Black', '#1b1b24', 0.3, coat=0.5)
    material('Mouth_Red', '#6a1520', 0.5)
    # Bogtoad
    material('Skin_Bog', '#6c962f', 0.5, coat=0.15)
    material('Spot_Bog', '#4c6a22', 0.55)
    material('Belly_Bog', '#ebdea0', 0.55)
    material('Cheek_Bog', '#a6cc52', 0.55)
    material('Toe_Brown', '#6c4829', 0.55)
    # Bubbletoad
    material('Skin_Teal', '#1f93a8', 0.4, coat=0.3)
    material('Spot_Cyan', '#5ed4ee', 0.45, coat=0.3)
    material('Belly_Aqua', '#bdeee0', 0.5)
    material('Feet_Cyan', '#4fcaf0', 0.4, coat=0.3)
    glass('Bubble', '#8ad8ff', 0.85, 0.03, emit=0.08)
    # Puddlepup
    material('Fur_PupBlue', '#55a0ec', 0.55, sheen=0.2)
    material('Spot_PupBlue', '#2d60cc', 0.55)
    material('Ear_Navy', '#2a48b2', 0.55, sheen=0.2)
    material('Fur_PalePup', '#c9eef2', 0.6, sheen=0.2)
    material('Paw_Cyan', '#8edcf2', 0.5)
    glass('Water_Gel', '#62d2f4', 0.55, 0.06, emit=0.12)
    # Rainhound
    material('Fur_HoundBlue', '#1f40a8', 0.55, sheen=0.25)
    material('Drop_Aqua', '#5ccaf2', 0.4, emit=0.15)
    material('Paw_Sky', '#a2d8f4', 0.5)
    material('Muzzle_Sky', '#bfe6f8', 0.55)


# ------------------------------------------------------------------ shared parts
CIRCLE = [(math.cos(a), math.sin(a)) for a in [2 * math.pi * k / 20 for k in range(20)]]
DROP = [(0.0, 0.66), (0.12, 0.42), (0.3, 0.12), (0.4, -0.12), (0.38, -0.36), (0.28, -0.52), (0.12, -0.6),
        (0.0, -0.62), (-0.12, -0.6), (-0.28, -0.52), (-0.38, -0.36), (-0.4, -0.12), (-0.3, 0.12), (-0.12, 0.42)]


def spots(pet, spec, mat, shape=CIRCLE, mirror_them=True):
    """round spots / drops wrapped onto parts: spec = [(part, direction, size, aspect, angle)]"""
    pieces = []
    for part, d, size, aspect, ang in spec:
        pts = [(x * 0.5, y * 0.5 * aspect) for x, y in shape]
        if shape is DROP:
            pts = [(x, y) for x, y in shape]
        pieces.append((decal(pet.bvh[part], pet.center[part], d, outline(pts, 2), size, ang, 0.004), mat))
    if mirror_them:
        pieces += [(mirror(p[0]), p[1]) for p in pieces]
    return pieces


def wrapped_eyes(pet, x, z, s, iris, head='Head', look=0.0):
    """big friendly eyes, flush with the head: dark rim, white, gradient iris, pupil, two highlights.
    Every layer is a thin shell wrapped onto the head surface (no bulging)."""
    bvh = pet.bvh[head]
    hit, n = cast_front(bvh, x, z)
    M = frame(n)
    r, u = M.col[0], M.col[1]
    #        material        dr     du    lift  half-depth   rx    ry
    spec = (('Eye_Outline', 0.0, 0.0, 0.0, 0.05, 1.08, 1.12),
            ('Eye_White', 0.0, 0.0, 0.02, 0.05, 1.0, 1.04),
            ('Eye_IrisV', look - 0.05, 0.02, 0.045, 0.05, 0.8, 0.86),
            ('Eye_Pupil', look - 0.08, 0.06, 0.07, 0.045, 0.42, 0.48),
            ('Eye_Highlight', -0.3, 0.34, 0.11, 0.03, 0.2, 0.2),
            ('Eye_Highlight', 0.12, -0.3, 0.1, 0.025, 0.09, 0.09))
    pieces = []
    for mat, dr, du, lift, dep, rx, ry in spec:
        c = hit + r * (dr * s) + u * (du * s) + n * (lift * s)
        bm = ellipsoid(c, (s * rx, s * ry, s * dep), M, seg=fp.lod(28, 24), rings=fp.lod(14, 12))
        if mat == 'Eye_IrisV':
            paint(bm, lambda co, c=c: grad(iris, ((co - c).dot(u) / (s * 0.82) + 1) / 2))
        pieces.append((bm, mat))
    Mt = M.transposed()
    for bm, _ in pieces:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if (Mt @ (v.co - hit)).z < -0.01 * s], context='VERTS')
        for v in bm.verts:
            l = Mt @ (v.co - hit)
            loc, nor, _, _ = bvh.ray_cast(hit + r * l.x + u * l.y + n * 0.5, -n)
            if loc is None:
                loc, nor = hit + r * l.x + u * l.y, n
            if nor.dot(n) < 0:
                nor = -nor
            v.co = loc + nor * max(l.z, 0.003)
    pet.pair('Eye', pieces)
    return hit, n, M


def clover(bvh, c, d, R, lift=0.0, spin=0.0, thick=0.42):
    """puffy 5-lobed moss clover lying on a surface"""
    hit, n = cast(bvh, c, d)
    M = frame(n) @ Matrix.Rotation(spin, 3, 'Z')
    r, u = M.col[0], M.col[1]
    poly = []
    for k in range(40):
        a = 2 * math.pi * k / 40
        rr = R * (0.68 + 0.32 * abs(math.cos(2.5 * a)) ** 0.7)
        poly.append((rr * math.cos(a), rr * math.sin(a)))

    def place(px, py):
        p = hit + r * px + u * py
        loc, nor, _, _ = bvh.ray_cast(p + n * 0.3, -n)
        return (loc if loc is not None else p) + n * (R * (0.35 + lift))
    return inflated(poly, R * thick, place, n, lambda px, py, k: grad(MOSS, 0.35 * k + 0.3 + lift * 0.6),
                    step=R * fp.lod(0.2, 0.27))


def moss_clump(bvh, c, d, R, spin=0.0):
    R *= 1.55
    return [(clover(bvh, c, d, R, 0.0, spin, 0.55), 'Vcol_Matte'),
            (clover(bvh, c, d, R * 0.62, 0.7, spin + 0.6, 0.55), 'Vcol_Matte')]


def toad_feet(pet, mat, front, back, toe_len, toe_r, webbed=False, toes=4):
    """toad feet: palm + splayed round-tipped toes (webbed: thin webbing between the toes)"""
    for tag, (x, y, yaw) in (('F', front), ('B', back)):
        parts = []
        palm_c = Vector((x, y, toe_r * 1.1))
        parts.append(ellipsoid(palm_c, (toe_len * 0.75, toe_len * 0.8, toe_r * 1.15)))
        for i in range(toes):
            a = math.radians(yaw + (i - (toes - 1) / 2) * (24 if webbed else 30))
            d = Vector((math.sin(a), -math.cos(a), 0))
            tip = palm_c + d * toe_len * (1.5 if webbed else 1.05)
            tip.z = toe_r * (0.95 if webbed else 1.15)
            parts.append(tube([palm_c, palm_c.lerp(tip, 0.5), tip], [(toe_r * 0.8, toe_r * 0.7)] * 3, 12))
            parts.append(ellipsoid(tip, (toe_r * (1.25 if webbed else 1.15),) * 2 + (toe_r * (1.0 if webbed else 1.1),)))
            if webbed and i < toes - 1:
                a2 = math.radians(yaw + (i + 0.5 - (toes - 1) / 2) * 24)
                d2 = Vector((math.sin(a2), -math.cos(a2), 0))
                wc = palm_c + d2 * toe_len * 0.85
                wc.z = toe_r * 0.55
                parts.append(ellipsoid(wc, (toe_len * 0.42, toe_len * 0.42, toe_r * 0.35), frame(Z) @ Matrix.Rotation(-a2, 3, 'Z')))
        pet.pair(f'Paw_{tag}', [(blob(parts, fp.lod(900, 360), voxel=0.006, smooth=3), mat)], sep='')


def toad_mouth(pet, z, w, h, tongue=True):
    """wide open smile: dark-red D-shaped mouth with a pink tongue, set into the front of the head"""
    bvh = pet.bvh['Head']
    hit, n = cast_front(bvh, 0, z)
    M = frame(n)
    mouth = ellipsoid(hit - n * 0.004, (w, h, 0.03), M, seg=24, rings=12)
    Mt = M.transposed()
    for v in mouth.verts:                         # flatten the top into a smile ("D" upside down)
        l = Mt @ (v.co - hit)
        if l.y > 0:
            v.co -= M.col[1] * l.y * 0.7
        else:                                      # follow the head's curve sideways
            pass
        v.co -= n * (l.x / w) ** 2 * w * 0.12
    pieces = [(mouth, 'Mouth_Red')]
    if tongue:
        t = ellipsoid(hit + n * 0.014 - M.col[1] * h * 0.45, (w * 0.58, h * 0.42, 0.02), M, seg=18, rings=10)
        for v in t.verts:
            l = Mt @ (v.co - hit)
            v.co -= n * (l.x / w) ** 2 * w * 0.12
        pieces.append((t, 'Tongue_Pink'))
    pet.obj('Mouth', pieces)
    return hit, n


def nostrils(pet, z, dx, r=0.012):
    hit, n = cast_front(pet.bvh['Head'], dx, z)
    pieces = [(ellipsoid(hit, (r, r * 0.7, r * 0.5), frame(n), seg=10, rings=6), 'Mouth_Line')]
    pieces += [(mirror(pieces[0][0]), 'Mouth_Line')]
    pet.obj('Nostrils', pieces)


def dog_ears(pet, root, tip, width, out, stops=None, mat='Ear_Navy', thick=0.04):
    """long floppy ear: flat spoon-shaped tube hanging from `root` to `tip`, broad face toward `out`"""
    k = 12
    path = catmull([root, root.lerp(tip, 0.45) + out * 0.03, tip], 6)
    m = len(path) - 1
    rad, cols = [], []
    for i in range(m + 1):
        t = i / m
        if t < 0.65:
            wdt = width * (0.55 + 0.45 * math.sin(t / 0.65 * math.pi / 2))
        else:
            wdt = width * math.sqrt(max(0.0, 1 - ((t - 0.65) / 0.35) ** 2))
        rad.append((wdt, thick * (0.6 + 0.4 * wdt / width)))
        if stops:
            cols.append(grad(stops, t))
    bm = tube(path, rad, fp.lod(18, 14), hint=out, colors=cols if stops else None)
    pet.pair('Ear', [(bm, 'Vcol_Matte' if stops else mat)])


def puffs(centres, tris=1400, voxel=0.01, smooth=4):
    """soft cloud / fluff made of overlapping balls: centres = [(position, radius)]"""
    return blob([ellipsoid(c, (r, r, r)) for c, r in centres], tris, voxel=voxel, smooth=smooth)


def dog_face(pet, muzzle, tongue=True, mouth_w=0.07):
    """black button nose, smile line, optional tongue hanging out"""
    bvh = pet.bvh['Head']
    tip, tn = cast(bvh, muzzle, Vector((0, -1, 0.55)))
    M = frame(tn)
    pet.obj('Nose', [(soft_triangle(ellipsoid(tip + tn * 0.01, (0.045, 0.032, 0.03), M, seg=16, rings=10, ex=2.3),
                                    M, tip, 0.032, 0.4), 'Nose_Black')])
    mz = tip.z - 0.075
    pts = [cast_front(bvh, xx, mz - 0.01 + 0.03 * (xx / mouth_w) ** 2 - 0.008 * math.cos(xx / mouth_w * math.pi * 1.5))[0] for xx in
           [-mouth_w + 2 * mouth_w * i / 14 for i in range(15)]]
    pieces = [(ribbon_pts(bvh, muzzle, pts, 0.01, 0.003), 'Mouth_Line')]
    if tongue:
        th, tnn = cast_front(bvh, 0, mz - 0.012)
        path = [th - tnn * 0.01, th + tnn * 0.025 - Z * 0.04, th + tnn * 0.03 - Z * 0.085]
        pieces.append((tube(catmull(path, 3), [(0.03, 0.012), (0.034, 0.012), (0.034, 0.012), (0.032, 0.012),
                                               (0.028, 0.012), (0.02, 0.012), (0.0, 0.0)], 12, hint=-Y),
                       'Tongue_Pink'))
        pieces.append((ellipsoid(th - tnn * 0.004, (0.035, 0.012, 0.022), frame(tnn), seg=14, rings=8), 'Mouth_Dark'))
    pet.obj('Mouth', pieces)


# ------------------------------------------------------------------ the four pets
def build_bogtoad(pc):
    p = Pet('Bogtoad', pc)
    skin = 'Skin_Bog'
    p.obj('Body', [(blob([ellipsoid((0, 0.1, 0.38), (0.42, 0.45, 0.35), seg=32, rings=20),
                          ellipsoid((0, -0.18, 0.3), (0.38, 0.3, 0.28))], 2400), skin)])
    hc = Vector((0, -0.28, 0.6))
    p.obj('Head', [(blob([ellipsoid(hc, (0.4, 0.3, 0.23), seg=36, rings=20, ex=2.2),
                          ellipsoid((0.23, -0.34, 0.68), (0.15, 0.13, 0.14)),
                          ellipsoid((-0.23, -0.34, 0.68), (0.15, 0.13, 0.14)),
                          ellipsoid((0, -0.42, 0.5), (0.3, 0.16, 0.14))], 3000), skin)])
    p.obj('Belly', [(blob([ellipsoid((0, -0.33, 0.29), (0.31, 0.2, 0.24)),
                           ellipsoid((0, -0.4, 0.43), (0.27, 0.14, 0.1))], 1600), 'Belly_Bog')])
    # legs: front arms + big haunches with folded shins
    p.pair('Leg_F', [(tube([Vector((0.3, -0.26, 0.36)), Vector((0.35, -0.33, 0.2)), Vector((0.36, -0.38, 0.06))],
                           [(0.09, 0.09), (0.085, 0.085), (0.08, 0.08)], 16), skin)], sep='')
    p.pair('Leg_B', [(blob([ellipsoid((0.4, 0.22, 0.25), (0.17, 0.27, 0.22)),
                            ellipsoid((0.47, 0.1, 0.09), (0.1, 0.2, 0.09))], 1400), skin)], sep='')
    toad_feet(p, 'Toe_Brown', (0.36, -0.42, -15), (0.5, -0.06, -40), 0.07, 0.042)
    wrapped_eyes(p, 0.235, 0.665, 0.13, IRIS_AMBER)
    toad_mouth(p, 0.465, 0.19, 0.1)
    nostrils(p, 0.6, 0.035)
    hb, bb = p.bvh['Head'], p.bvh['Body']
    p.obj('Cheeks', spots(p, [('Head', Vector((0.9, -0.5, -0.5)), 0.1, 1.0, 0)], 'Cheek_Bog'))
    p.obj('Spots', spots(p, [
        ('Body', Vector((0.7, 0.2, 0.55)), 0.13, 0.9, 0.3), ('Body', Vector((0.35, 0.55, 0.75)), 0.1, 1.0, 0),
        ('Body', Vector((0.85, -0.2, 0.2)), 0.09, 1.0, 0), ('Body', Vector((0.45, 0.85, 0.2)), 0.12, 0.9, 0.5),
        ('Body', Vector((0.15, 0.9, 0.5)), 0.08, 1.0, 0), ('Head', Vector((0.55, 0.3, 0.75)), 0.08, 1.0, 0),
        ('Leg_BL', Vector((1, 0.1, 0.4)), 0.13, 0.9, 0.4), ('Leg_BL', Vector((0.7, 0.8, 0.1)), 0.11, 1.0, 0),
        ('Leg_BL', Vector((0.8, -0.6, 0.3)), 0.07, 1.0, 0), ('Leg_FL', Vector((1, -0.3, 0.2)), 0.07, 1.0, 0),
    ], 'Spot_Bog'))
    moss = []
    for d, R, sp in ((Vector((0, -0.2, 1)), 0.07, 0.0), (Vector((0.35, -0.1, 1)), 0.05, 0.4),
                     (Vector((-0.35, -0.1, 1)), 0.05, 1.1), (Vector((0, 0.6, 1)), 0.055, 0.7)):
        moss += moss_clump(hb, hc, d, R, sp)
    for d, R, sp in ((Vector((0, -0.35, 1)), 0.075, 0.2), (Vector((0.18, 0.0, 1)), 0.075, 0.9),
                     (Vector((-0.2, 0.15, 1)), 0.07, 1.6), (Vector((0.15, 0.45, 0.85)), 0.065, 0.3),
                     (Vector((-0.1, 0.7, 0.6)), 0.06, 1.2), (Vector((0, 0.95, 0.25)), 0.05, 0.5),
                     (Vector((0.95, -0.25, 0.45)), 0.05, 0.8), (Vector((-0.95, -0.25, 0.45)), 0.05, 0.1)):
        moss += moss_clump(bb, Vector((0, 0.1, 0.38)), d, R, sp)
    p.obj('Moss', moss)
    return p


def build_bubbletoad(pc):
    p = Pet('Bubbletoad', pc)
    skin = 'Skin_Teal'
    p.obj('Body', [(blob([ellipsoid((0, 0.1, 0.38), (0.4, 0.44, 0.35), seg=32, rings=20),
                          ellipsoid((0, -0.18, 0.31), (0.36, 0.3, 0.28))], 2400), skin)])
    hc = Vector((0, -0.27, 0.6))
    p.obj('Head', [(blob([ellipsoid(hc, (0.38, 0.3, 0.23), seg=36, rings=20, ex=2.2),
                          ellipsoid((0.22, -0.33, 0.68), (0.15, 0.13, 0.14)),
                          ellipsoid((-0.22, -0.33, 0.68), (0.15, 0.13, 0.14)),
                          ellipsoid((0, -0.42, 0.5), (0.28, 0.16, 0.14))], 3000), skin)])
    p.obj('Belly', [(blob([ellipsoid((0, -0.32, 0.29), (0.31, 0.2, 0.25)),
                           ellipsoid((0, -0.4, 0.43), (0.26, 0.14, 0.1))], 1600), 'Belly_Aqua')])
    p.pair('Leg_F', [(tube([Vector((0.29, -0.26, 0.36)), Vector((0.36, -0.33, 0.2)), Vector((0.39, -0.37, 0.05))],
                           [(0.085, 0.085), (0.075, 0.075), (0.065, 0.065)], 16), skin)], sep='')
    p.pair('Leg_B', [(blob([ellipsoid((0.38, 0.2, 0.25), (0.16, 0.26, 0.21)),
                            ellipsoid((0.47, 0.06, 0.08), (0.09, 0.2, 0.08))], 1400), skin)], sep='')
    toad_feet(p, 'Feet_Cyan', (0.4, -0.42, -18), (0.55, -0.14, -50), 0.075, 0.03, webbed=True)
    wrapped_eyes(p, 0.225, 0.665, 0.128, IRIS_INDIGO)
    toad_mouth(p, 0.465, 0.17, 0.09)
    nostrils(p, 0.6, 0.035)
    hb, bb = p.bvh['Head'], p.bvh['Body']
    p.obj('Spots', spots(p, [
        ('Head', Vector((0.9, -0.5, -0.5)), 0.09, 1.0, 0), ('Head', Vector((0.55, 0.2, 0.8)), 0.07, 1.0, 0),
        ('Head', Vector((0.2, -0.3, 1)), 0.05, 1.0, 0),
        ('Body', Vector((0.7, 0.2, 0.55)), 0.14, 0.85, 0.3), ('Body', Vector((0.4, 0.55, 0.75)), 0.08, 1.0, 0),
        ('Body', Vector((0.9, -0.2, 0.15)), 0.08, 1.0, 0), ('Body', Vector((0.45, 0.85, 0.25)), 0.13, 0.85, 0.5),
        ('Body', Vector((0.2, 0.95, 0.55)), 0.07, 1.0, 0), ('Body', Vector((0.6, 0.6, 0.1)), 0.05, 1.0, 0),
        ('Leg_BL', Vector((1, 0.1, 0.4)), 0.12, 0.9, 0.4), ('Leg_BL', Vector((0.7, 0.8, 0.1)), 0.09, 1.0, 0),
        ('Leg_BL', Vector((0.8, -0.6, 0.3)), 0.06, 1.0, 0), ('Leg_FL', Vector((1, -0.3, 0.2)), 0.07, 1.0, 0),
    ], 'Spot_Cyan'))
    # bubbles: a big one on the head with little ones, then a ridge shrinking down the back
    bub = []
    seg, rg = fp.lod(24, 18), fp.lod(14, 10)

    def bubble_on(bvh, c, d, r, sink=0.35):
        hit, n = cast(bvh, c, d)
        bub.append((ellipsoid(hit + n * r * (1 - sink), (r, r, r), seg=seg, rings=rg), 'Bubble'))
    bubble_on(hb, hc, Vector((0, -0.05, 1)), 0.135)
    for dx in (0.42, -0.42):
        bubble_on(hb, hc, Vector((dx, 0.0, 1)), 0.05)
    bubble_on(hb, hc, Vector((0.15, -0.35, 1)), 0.028)
    for t, r in ((0.0, 0.12), (0.22, 0.095), (0.45, 0.075), (0.65, 0.06), (0.82, 0.048), (0.95, 0.038)):
        bubble_on(bb, Vector((0, 0.1, 0.38)), Vector((0, -0.25 + 1.5 * t, 1 - 0.75 * t)), r)
    for d, r in ((Vector((0.12, 0.7, 0.75)), 0.03), (Vector((-0.1, 0.85, 0.45)), 0.028), (Vector((0.08, 0.95, 0.2)), 0.035),
                 (Vector((-0.15, 0.4, 0.95)), 0.025), (Vector((0.2, 0.2, 1)), 0.022)):
        bubble_on(bb, Vector((0, 0.1, 0.38)), d, r)
    p.obj('Bubbles', bub)
    return p


def build_puddlepup(pc):
    p = Pet('Puddlepup', pc)
    fur = 'Fur_PupBlue'
    p.obj('Body', [(blob([body_bm(0.4, -0.22, 0.36, 0.39, 0.23, 0.17),
                          ellipsoid((0.14, 0.3, 0.29), (0.11, 0.16, 0.15)),
                          ellipsoid((-0.14, 0.3, 0.29), (0.11, 0.16, 0.15)),
                          ellipsoid((0, -0.2, 0.37), (0.19, 0.17, 0.18))], 2200), fur)])
    hc = Vector((0, -0.33, 0.72))
    p.obj('Head', [(blob([ellipsoid(hc, (0.31, 0.27, 0.27), seg=36, rings=20, ex=2.15),
                          *[ellipsoid((s * 0.15, -0.42, 0.62), (0.14, 0.13, 0.12)) for s in (1, -1)]], 2600), fur)])
    muzzle = Vector((0, -0.57, 0.6))
    p.obj('Muzzle', [(blob([ellipsoid(muzzle, (0.13, 0.12, 0.09)), ellipsoid((0, -0.52, 0.55), (0.11, 0.1, 0.07))],
                           1200), 'Fur_PalePup')])
    p.bvh['Head'] = fp.BVHTree.FromPolygons(*_merged_polys(p, ('Head', 'Muzzle')))
    legs = fp.legs_and_paws
    legs(p, fur, 'Paw_Cyan', (0.15, -0.18, 0.28, 0.088), (0.15, 0.27, 0.26, 0.09), (0.11, 0.14, 0.1))
    wrapped_eyes(p, 0.14, 0.735, 0.097, IRIS_SKY, look=0.05)
    dog_face(p, muzzle, tongue=True)
    dog_ears(p, Vector((0.23, -0.27, 0.88)), Vector((0.43, -0.3, 0.5)), 0.155, Vector((0.55, -0.85, 0.1)).normalized(),
             thick=0.05)
    # pale chest fluff with little fur points
    fl = [ellipsoid((0, -0.34, 0.42), (0.15, 0.1, 0.17)), ellipsoid((0, -0.3, 0.3), (0.12, 0.09, 0.1))]
    for i in range(-2, 3):
        fl.append(fp.tongue(Vector((i * 0.05, -0.36, 0.3)), Vector((i * 0.4, -0.3, -1)), 0.08, 0.045, 0.6, stops=None))
    p.obj('ChestFluff', [(blob(fl, 1400, voxel=0.007, smooth=3), 'Fur_PalePup')])
    # water-drop topknot
    tb, tn = cast(p.bvh['Head'], hc, Vector((0, -0.1, 1)))
    knot = [ellipsoid(tb + tn * 0.04, (0.065, 0.065, 0.06))]
    for k in range(5):
        a = 2 * math.pi * k / 5
        knot.append(ellipsoid(tb + Vector((math.cos(a) * 0.07, math.sin(a) * 0.06, 0.005)), (0.035, 0.035, 0.03)))
    knot.append(ellipsoid(tb + tn * 0.12, (0.03, 0.03, 0.035)))
    p.obj('WaterTopknot', [(blob(knot, 900, voxel=0.006, smooth=3), 'Water_Gel')])
    # curled water-drop tail
    ctrl = [(0, 0.42, 0.42), (0, 0.55, 0.47), (0, 0.66, 0.6), (0, 0.68, 0.76), (0, 0.6, 0.86), (0, 0.5, 0.84),
            (0, 0.47, 0.76), (0, 0.52, 0.71)]
    pts = catmull(ctrl, 6)
    m = len(pts) - 1
    rad = []
    for i in range(m + 1):
        t = i / m
        r = 0.06 + 0.035 * math.sin(min(t / 0.45, 1) * math.pi / 2) if t < 0.6 else 0.095 * (1 - (t - 0.6) / 0.4) ** 0.6 + 0.012
        rad.append((r, r))
    tail = [(tube(pts, rad, fp.lod(18, 14)), 'Water_Gel')]
    drop = pts[int(m * 0.42)] + Vector((0.08, 0.05, -0.04))
    tail.append((blob([ellipsoid(drop, (0.028, 0.028, 0.03)),
                       tube([drop, drop + Vector((0, 0, 0.05))], [(0.02, 0.02), (0.0, 0.0)], 12)], 300, voxel=0.004,
                      smooth=2), 'Water_Gel'))
    p.obj('Tail', tail)
    p.obj('Spots', spots(p, [
        ('Body', Vector((1, 0.45, 0.5)), 0.14, 0.8, 0.3), ('Body', Vector((1, 0.0, 0.2)), 0.1, 1.0, 0),
        ('Body', Vector((0.55, 0.9, 0.6)), 0.11, 0.8, 0.5), ('Body', Vector((0.4, -0.6, 0.75)), 0.08, 1.0, 0),
        ('Leg_BL', Vector((1, 0.1, 0.4)), 0.1, 0.8, 0.4), ('Leg_FL', Vector((1, -0.3, 0.3)), 0.08, 0.8, 0),
        ('Leg_BL', Vector((0.5, 0.9, 0.2)), 0.07, 1.0, 0),
    ], 'Spot_PupBlue'))
    p.obj('Cheeks', spots(p, [('Head', Vector((0.8, -0.55, -0.25)), 0.07, 1.0, 0)], 'Fur_PalePup'))
    return p


def _merged_polys(p, parts):
    """vertices + polygons of several finished parts (pet-local) for one combined surface lookup"""
    verts, polys = [], []
    for part in parts:
        ob = bpy.data.objects[f'{p.name}_{part}']
        off = len(verts)
        verts += [ob.location + v.co for v in ob.data.vertices]
        polys += [[off + i for i in poly.vertices] for poly in ob.data.polygons]
    return verts, polys


def build_rainhound(pc):
    p = Pet('Rainhound', pc)
    fur = 'Fur_HoundBlue'
    neck = tube([Vector((0, -0.28, 0.62)), Vector((0, -0.36, 0.76)), Vector((0, -0.43, 0.9))],
                [(0.12, 0.12), (0.115, 0.11), (0.11, 0.1)], 20)
    p.obj('Body', [(blob([body_bm(0.5, -0.38, 0.56, 0.6, 0.17, 0.13, taper=0.05), neck,
                          ellipsoid((0.11, 0.36, 0.5), (0.085, 0.15, 0.17)),
                          ellipsoid((-0.11, 0.36, 0.5), (0.085, 0.15, 0.17)),
                          ellipsoid((0, -0.26, 0.58), (0.16, 0.16, 0.16))], 2400), fur)])
    hc = Vector((0, -0.46, 0.94))
    p.obj('Head', [(blob([ellipsoid(hc, (0.25, 0.235, 0.225), seg=36, rings=20, ex=2.15),
                          *[ellipsoid((s * 0.12, -0.55, 0.88), (0.12, 0.12, 0.1)) for s in (1, -1)]], 2600), fur)])
    muzzle = Vector((0, -0.68, 0.87))
    p.obj('Muzzle', [(blob([ellipsoid(muzzle, (0.1, 0.13, 0.075)), ellipsoid((0, -0.64, 0.82), (0.085, 0.1, 0.055))],
                           1000), 'Muzzle_Sky')])
    p.bvh['Head'] = fp.BVHTree.FromPolygons(*_merged_polys(p, ('Head', 'Muzzle')))
    fp.legs_and_paws(p, fur, 'Paw_Sky', (0.12, -0.3, 0.5, 0.072), (0.12, 0.38, 0.46, 0.075), (0.095, 0.12, 0.09))
    wrapped_eyes(p, 0.115, 0.975, 0.086, IRIS_SKY, look=0.05)
    dog_face(p, muzzle, tongue=False, mouth_w=0.06)
    dog_ears(p, Vector((0.19, -0.42, 1.08)), Vector((0.37, -0.45, 0.47)), 0.16, Vector((0.5, -0.85, 0.1)).normalized(),
             stops=EAR_HOUND, thick=0.045)
    # cloud tuft on the head and cloud chest fluff
    tb, tn = cast(p.bvh['Head'], hc, Vector((0, -0.05, 1)))
    tuft = [(tb + tn * 0.03, 0.065)]
    for k in range(6):
        a = 2 * math.pi * k / 6
        tuft.append((tb + Vector((math.cos(a) * 0.075, math.sin(a) * 0.065, 0.0)), 0.048))
    tuft.append((tb + tn * 0.09 + Vector((0, 0.02, 0)), 0.045))
    cl = puffs(tuft, 1200, voxel=0.007, smooth=3)
    paint(cl, lambda co: grad(CLOUD, 0.5 + (co.z - tb.z) * 4))
    p.obj('CloudTuft', [(cl, 'Vcol_Matte')])
    chest = []
    for zz, ww in ((0.86, 0.1), (0.78, 0.13), (0.69, 0.14), (0.6, 0.12), (0.52, 0.08)):
        for xx in (-1, 0, 1):
            if ww < 0.1 and xx != 0:
                continue
            c = Vector((xx * ww * 0.55, -0.4 - (0.05 if xx == 0 else 0.0) + (0.86 - zz) * 0.2, zz))
            chest.append((c, 0.065 if xx == 0 else 0.055))
    cf = puffs(chest, 1500, voxel=0.008, smooth=3)
    paint(cf, lambda co: grad(CLOUD, 0.75 + 0.25 * (co.z - 0.5) / 0.4))
    p.obj('ChestFluff', [(cf, 'Vcol_Matte')])
    # curved cloud tail: a swirl of puffs, blue inside, nearly white outside
    swirl_c = Vector((-0.22, 0.69, 0.83))
    tailc = []
    path = catmull([(-0.02, 0.48, 0.64), (-0.1, 0.62, 0.64), (-0.18, 0.8, 0.72), (-0.22, 0.86, 0.9),
                    (-0.23, 0.75, 1.02), (-0.22, 0.6, 0.98), (-0.21, 0.57, 0.87), (-0.21, 0.65, 0.82)], 5)
    for i, q in enumerate(path):
        t = i / (len(path) - 1)
        rr = 0.05 + 0.08 * math.sin(min(t / 0.5, 1) * math.pi / 2) - 0.04 * max(0.0, t - 0.7) / 0.3
        tailc.append((Vector(q), rr))
        if 0.25 < t < 0.85 and i % 2 == 0:              # puffs on the outside of the swirl
            out = (Vector(q) - swirl_c)
            out.x = 0
            tailc.append((Vector(q) + out.normalized() * rr * 0.75, rr * 0.75))
    tl = puffs(tailc, 2200, voxel=0.01, smooth=4)
    paint(tl, lambda co: grad(CLOUD, min(1.0, 0.15 + 2.6 * ((co - swirl_c) * Vector((0, 1, 1))).length)))
    p.obj('Tail', [(tl, 'Vcol_Matte')])
    p.obj('RainDrops', spots(p, [
        ('Body', Vector((1, 0.55, 0.3)), 0.12, 1, 0.15), ('Body', Vector((1, 0.15, 0.2)), 0.1, 1, 0.1),
        ('Body', Vector((1, -0.35, 0.1)), 0.09, 1, 0.0), ('Body', Vector((0.5, 0.8, 0.5)), 0.08, 1, 0.3),
        ('Leg_FL', Vector((1, -0.4, 0.6)), 0.09, 1, 0), ('Leg_FL', Vector((1, -0.3, -0.2)), 0.08, 1, 0),
        ('Leg_FL', Vector((0, -1, 0.2)), 0.07, 1, 0), ('Leg_BL', Vector((1, 0.2, 0.6)), 0.1, 1, 0.1),
        ('Leg_BL', Vector((1, 0.1, -0.1)), 0.08, 1, 0), ('Leg_BL', Vector((0.3, 1, 0.3)), 0.07, 1, 0),
        ('Ear_L', Vector((1, -0.1, 0.4)), 0.07, 1, 0), ('Ear_L', Vector((1, 0.05, -0.3)), 0.09, 1, 0),
        ('Ear_L', Vector((1, -0.5, -0.6)), 0.08, 1, 0), ('Body', Vector((0.8, 0.85, 0.1)), 0.08, 1, 0.3),
        ('Body', Vector((0.9, 0.35, -0.35)), 0.07, 1, 0.1), ('Leg_BL', Vector((1, 0.4, 0.2)), 0.07, 1, 0),
    ], 'Drop_Aqua', shape=DROP))
    return p


# ------------------------------------------------------------------ scene
def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    fp.PET_X = WATER_X
    fp.LOW = True                       # game-budget format for every water pet
    build_water_materials()
    pc = bpy.data.collections.new('PETS')
    sc.collection.children.link(pc)
    for fn in (build_bogtoad, build_bubbletoad, build_puddlepup, build_rainhound):
        pet = fn(pc)
        pet.place(WATER_X[pet.name])
    fp.LOW = False
    fp.build_studio(sc)
    fp.build_cameras(sc)
    fp.build_labels(sc)
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.view_settings.view_transform = 'Standard'
    return sc


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    sc = build_scene()
    path = os.path.join(HERE, 'WaterPets.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    for pet in WATER_X:
        objs = [o for o in bpy.data.collections[pet].objects if o.type == 'MESH']
        tris = sum(sum(len(q.vertices) - 2 for q in o.data.polygons) for o in objs)
        print(f'{pet}: {len(objs)} mesh objects, {tris} tris')
    print('Saved:', path)
    if '--render' in argv:
        i = argv.index('--render')
        out = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith('--') else os.path.join(HERE, '..', 'previews')
        only = argv[argv.index('--only') + 1].split(',') if '--only' in argv else None
        samples = int(argv[argv.index('--samples') + 1]) if '--samples' in argv else 48
        fp.render_previews(sc, os.path.abspath(out), only, samples, prefix='WaterPets')


if __name__ == '__main__':
    main()
