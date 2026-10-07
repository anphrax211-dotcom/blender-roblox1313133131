"""FLOATING_ISLANDS, ENVIRONMENT, LIGHTING, CAMERAS: the hub's floating rock, aqueduct cliff
wings, hub-edge waterfalls, modular floating islands (3 meshes reused as linked duplicates),
rope bridges from tower ledges, karst mountains, sea + sea of clouds, sky clouds, sky/sun,
the six cameras and the compositor (atmospheric haze from the mist pass + bloom)."""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
from common import (Part, coll, inst, ASSETS, ASSET_COLL, canopy, waterfall, rock_blob, round_arch,
                    TAU, _asset_part, _register)
from hub import R_ISLAND, polar
from tower import TC, LEDGES, P as TP

ENV, ISL, WF, LIT, CAM = 'ENVIRONMENT', 'FLOATING_ISLANDS', 'WATERFALLS', 'LIGHTING', 'CAMERAS'
SKY = 'Sky_Clouds'


# ---------------------------------------------------------------- hub rock --
def _ray_circle_exit(p, d, c, R):
    m = c - p
    b = d.dot(m)
    disc = b * b - m.length_squared + R * R
    return b + math.sqrt(disc) if disc > 0 else 0.0


def build_hub_rock():
    """the floating rock the hub and the tower foundation stand on (one lofted mesh)"""
    rnd = random.Random(500)
    centre = Vector((0, 170, 0))
    n = 72
    outline = []
    for i in range(n):
        a = TAU * i / n
        d = Vector((math.cos(a), math.sin(a), 0))
        r = max(_ray_circle_exit(centre, d, Vector((0, 0, 0)), R_ISLAND + 5),
                _ray_circle_exit(centre, d, TC, 322))
        outline.append(r)
    prof = ((1.0, -3.4), (1.02, -14), (0.96, -40), (0.86, -90), (0.70, -150), (0.50, -215), (0.30, -270),
            (0.14, -320), (0.03, -360))
    rings = []
    for k, (s, z) in enumerate(prof):
        ring = []
        for i in range(n):
            a = TAU * i / n
            j = 1.0 if k == 0 else rnd.uniform(0.9, 1.08)
            r = outline[i] * s * j
            ring.append(centre + Vector((math.cos(a) * r, math.sin(a) * r, z + (rnd.uniform(-6, 6) if k else 0))))
        rings.append(ring)
    p = Part('Hub_Island_Rock', ENV)
    p.loft(rings, 'Cliff_Rock')
    # hanging roots / grassy overhang tufts on the rim
    for i in range(0, n, 2):
        a = TAU * i / n
        r = outline[i] * 1.0
        c = centre + Vector((math.cos(a) * r, math.sin(a) * r, -4))
        if (c - TC).length < 305:
            continue
        p.ico(c, rnd.uniform(3, 5), rnd.choice(('Leaf_Green', 'Leaf_Dark')), 1, (1, 1, 0.6))
    # big rock outcrops on the underside
    for k in range(14):
        a = rnd.uniform(0, TAU)
        r = rnd.uniform(60, 170)
        rock_blob(p, centre + Vector((math.cos(a) * r, math.sin(a) * r, rnd.uniform(-200, -60))),
                  rnd.uniform(25, 45), 'Cliff_Rock_Dark', rnd, 1, (1, 1, 1.4))
    p.finish()
    # waterfalls pouring off the hub rim into the clouds
    for k, deg in enumerate((205, 238, 302, 335, 172, 8)):
        a = math.radians(deg)
        waterfall(f'Waterfall_HubRim_{k}', WF, polar(R_ISLAND + 4, deg, -1.5), (math.cos(a), math.sin(a)),
                  300, rnd.uniform(9, 13), seed=600 + k, foam=False)


def build_aqueduct_wings():
    """two-tier arched stone aqueducts curving round the north-east and north-west of the hub (the
    arcaded cliffs of the hub sheets); water spills from them back down past the island rim"""
    rnd = random.Random(510)
    R, n, depth = 192.0, 7, 14.0
    for side, (d0, d1) in (('East', (16, 66)), ('West', (114, 164))):
        p = Part(f'Aqueduct_{side}', ENV)
        chord = 2 * R * math.sin(math.radians(d1 - d0) / n / 2)
        span = chord - 14.0
        tiers, zb = [], 0.0
        for hs in (16.0, 10.0):
            tiers.append((zb, hs))
            zb = zb + hs + span / 2 + 7
        top = zb
        for i in range(n + 1):
            deg = d0 + (d1 - d0) * i / n
            c = Vector(polar(R, deg))
            p.box(c + Vector((0, 0, (top - 130) / 2)), (depth - 2, 14, top + 130), 'Hub_Stone',
                  Matrix.Rotation(math.radians(deg), 3, 'Z'))
            rock_blob(p, c + Vector((0, 0, -120)), 22, 'Cliff_Rock', rnd, 1, (1, 1, 2.4))
        for i in range(n):
            mid = d0 + (d1 - d0) * (i + 0.5) / n
            M = Matrix.Translation(Vector(polar(R - depth / 2, mid))) @ \
                Matrix.Rotation(math.radians(mid + 90), 4, 'Z') @ \
                Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
            for zb, hs in tiers:
                ztop = zb + hs + span / 2 + 7
                pts = [(x, zb + z) for x, z in round_arch(span, hs, 10)][1:-1]
                for (xa, za), (xb, zb_) in zip(pts, pts[1:]):        # spandrel blocks over the arch
                    q = ((xa, za), (xb, zb_), (xb, ztop), (xa, ztop))
                    p.hexa([M @ Vector((u, v, 0)) for u, v in q] + [M @ Vector((u, v, depth)) for u, v in q],
                           'Hub_Stone')
                p.box(Vector(polar(R, mid, ztop - 0.6)), (depth + 1.5, chord + 1, 1.2), 'Stone_Trim',
                      Matrix.Rotation(math.radians(mid), 3, 'Z'))
            p.box(Vector(polar(R, mid, top + 0.25)), (6, chord, 0.5), 'Water',
                  Matrix.Rotation(math.radians(mid), 3, 'Z'))
            for s_ in (-1, 1):                                      # parapets either side of the channel
                p.box(Vector(polar(R + s_ * (depth / 2 - 1), mid, top + 1.5)), (1.6, chord, 3.0), 'Hub_Stone',
                      Matrix.Rotation(math.radians(mid), 3, 'Z'))
        p.finish()
        for i in range(n + 1):
            deg = d0 + (d1 - d0) * i / n
            inst(rnd.choice(('Tree_Medium_High', 'Tree_Small', 'Bush_02')), f'Aqueduct_{side}_Tree_{i}', ENV,
                 polar(R, deg, top), rnd.uniform(0, TAU), rnd.uniform(0.9, 1.4))
        for k in range(2):                       # falls spilling out of the channel, outward over the rim
            deg = d0 + (d1 - d0) * (k * 4 + 1.5) / n
            a = math.radians(deg)
            waterfall(f'Waterfall_Aqueduct_{side}_{k}', WF, polar(R + depth / 2, deg, top),
                      (math.cos(a), math.sin(a)), top + 160, 6, seed=520 + k + (side == 'West') * 5, foam=False)


# ---------------------------------------------------------------- islands ---
def build_island_assets():
    rnd = random.Random(700)
    for k, (r, depth, ntree, ruin) in enumerate(((1.0, 1.3, 5, False), (1.0, 1.7, 3, True), (1.0, 1.0, 6, False))):
        name = f'Island_{"ABC"[k]}'
        p = _asset_part(name)
        n = 14
        top = [(math.cos(TAU * i / n) * r * rnd.uniform(0.85, 1.1), math.sin(TAU * i / n) * r * rnd.uniform(0.85, 1.1))
               for i in range(n)]
        rings = []
        for j, (s, z) in enumerate(((1.0, 0.0), (0.92, -0.18), (0.7, -0.5 * depth), (0.42, -0.8 * depth),
                                    (0.15, -1.05 * depth), (0.02, -1.25 * depth))):
            ox, oy = rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06)
            rings.append([Vector((x * s * rnd.uniform(0.9, 1.08) + ox, y * s * rnd.uniform(0.9, 1.08) + oy, z))
                          for x, y in top])
        p.loft(rings, 'Cliff_Rock')
        p.prism([(x * 1.04, y * 1.04) for x, y in top], 0.0, 0.1, 'Grass')
        rr = random.Random(710 + k)
        for t in range(14):
            a = rr.uniform(0, TAU); d = rr.uniform(0.5, 1.0)
            p.ico((math.cos(a) * d, math.sin(a) * d, 0.12), rr.uniform(0.06, 0.1), 'Leaves_Mid', 1, (1, 1, 0.7))
        if ruin:
            for i in range(4):
                a = TAU * i / 4 + 0.3
                p.cyl((math.cos(a) * 0.35, math.sin(a) * 0.35, 0.22), 0.05, 0.25 + 0.1 * (i % 2), 'Hub_Stone', 8)
            p.box((0, 0, 0.47), (0.8, 0.8, 0.06), 'Hub_Stone')
            p.uvsphere((0, 0, 0.5), 0.3, 'Roof_Blue', 12, 6, (1, 1, 0.8))
        _register(name, p)
    for o in coll(ASSET_COLL).objects:
        o.hide_render = True


ISLANDS = []     # (location, radius) of placed islands


def place_island(name, loc, size, rot=0.0, falls=False, seed=0):
    kind = 'ABC'[seed % 3]
    ob = inst(f'Island_{kind}', name, ISL, loc, rot, size)
    ISLANDS.append((Vector(loc), size))
    # trees, bushes and hanging vines from the foliage pack (far islands use the low LODs)
    rnd = random.Random(seed)
    far = 'Hub' not in name
    loc = Vector(loc)
    s = max(0.6, min(2.4, size / 34))
    for t in range((3, 2, 4)[seed % 3]):
        a = rnd.uniform(0, TAU); d = rnd.uniform(0, 0.5) * size
        kind_t = rnd.choice(('Large', 'Medium', 'Small', 'Tall_Thin'))
        nm = {('Large', False): 'Tree_Large_High', ('Medium', False): 'Tree_Medium_High',
              ('Small', False): 'Tree_Small', ('Tall_Thin', False): 'Tree_Tall_Thin'}.get((kind_t, far),
                                                                                         f'Tree_{kind_t}_Low')
        inst(nm, f'{name}_Tree_{t}', ISL, loc + Vector((math.cos(a) * d, math.sin(a) * d, size * 0.1)),
             rnd.uniform(0, TAU), s * rnd.uniform(0.8, 1.2))
    for t in range(3):
        a = rnd.uniform(0, TAU); d = rnd.uniform(0.45, 0.8) * size
        inst(rnd.choice(('Bush_01', 'Bush_02', 'Bush_03')), f'{name}_Bush_{t}', ISL,
             loc + Vector((math.cos(a) * d, math.sin(a) * d, size * 0.1)), rnd.uniform(0, TAU), s * 1.2)
    for t in range(4):
        a = rot + TAU * t / 4 + rnd.uniform(-0.4, 0.4)
        inst(rnd.choice(('Vine_Medium', 'Vine_Long')), f'{name}_Vine_{t}', ISL,
             loc + Vector((math.cos(a) * size * 0.92, math.sin(a) * size * 0.92, size * 0.02)), rnd.uniform(0, TAU),
             s * 1.4)
    if falls:
        a = rot + 0.7
        d = (math.cos(a), math.sin(a))
        lip = Vector(loc) + Vector((d[0] * size * 0.85, d[1] * size * 0.85, size * 0.05))
        waterfall(f'Waterfall_{name}', WF, lip, d, size * 3.0, max(3.0, size * 0.18), seed=seed, foam=False)
    return ob


def build_floating_islands():
    rnd = random.Random(720)
    # around the tower, spiralling up with it
    k = 0
    for i in range(30):
        deg = i * 137.5 + rnd.uniform(-10, 10)
        if 250 < deg % 360 < 290 and i % 2:
            deg += 50                                        # keep the front sight-line mostly clear
        z = 160 + i * 68 + rnd.uniform(-30, 30)
        dist = rnd.uniform(400, 620) + (z / 2100) * rnd.uniform(0, 120)
        loc = TP(dist, deg, z)
        size = rnd.uniform(70, 110) if i % 4 == 1 else rnd.uniform(26, 50)
        place_island(f'Island_Tower_{i:02d}', loc, size, rnd.uniform(0, TAU), i % 3 == 0, 800 + i)
    # around the hub, below and to the sides (visible from the plaza)
    for i in range(14):
        deg = rnd.choice((rnd.uniform(-60, 45), rnd.uniform(135, 240)))
        dist = rnd.uniform(330, 560)
        loc = Vector(polar(dist, deg, rnd.uniform(-60, 240)))
        place_island(f'Island_Hub_{i:02d}', loc, rnd.uniform(12, 30), rnd.uniform(0, TAU), i % 3 == 1, 900 + i)


def rope_bridge(name, a, b, sag, width=7.0):
    a, b = Vector(a), Vector(b)
    p = Part(name, ISL)
    L = (b - a).length
    n = max(6, int(L / 2.2))
    d = (b - a).normalized()
    side = Vector((-d.y, d.x, 0)).normalized()
    pts = [a + (b - a) * (i / n) - Vector((0, 0, sag * math.sin(math.pi * i / n))) for i in range(n + 1)]
    for i, q in enumerate(pts):
        p.box(q, (width, 1.6, 0.35), 'Wood', Matrix.Rotation(math.atan2(d.y, d.x) + math.pi / 2, 3, 'Z'))
    for s in (-1, 1):
        for i in range(n):
            p.beam(pts[i] + side * s * width / 2 + Vector((0, 0, 3.2)),
                   pts[i + 1] + side * s * width / 2 + Vector((0, 0, 3.2)), 0.25, 0.25, 'Rope')
        for i in range(0, n + 1, 2):
            p.beam(pts[i] + side * s * width / 2, pts[i] + side * s * width / 2 + Vector((0, 0, 3.4)), 0.35, 0.35,
                   'Wood')
        for q in (a, b):
            p.box(q + side * s * (width / 2 + 0.6) + Vector((0, 0, 3)), (1.2, 1.2, 6.5), 'Wood')
    return p.finish()


def build_bridges():
    rnd = random.Random(730)
    for i, (key, deg) in enumerate((('Jungle', 205), ('Desert', 335), ('Ice', 150), ('Lava', 30), ('Crystal', 222),
                                    ('Shadow', 315), ('Forest', 190), ('Kingdom', 345), ('Cloud', 230),
                                    ('Celestial', 320))):
        z, rl = LEDGES[key]
        span = rnd.uniform(70, 110)
        size = rnd.uniform(26, 40)
        isl = TP(rl + span + size * 0.8, deg, z - 3)
        place_island(f'Island_Bridge_{key}', isl, size, math.radians(deg), i % 2 == 0, 950 + i)
        rope_bridge(f'Bridge_{key}', TP(rl - 2, deg, z + 0.3), TP(rl + span, deg, z - 2.6), span * 0.08)


# ---------------------------------------------------------------- far world -
def build_mountain_assets():
    rnd = random.Random(740)
    for k in range(3):
        name = f'Karst_{"ABC"[k]}'
        p = _asset_part(name)
        n = 10
        rings = []
        for j in range(7):
            t = j / 6
            r = (1.0 - 0.55 * t) * (1 + 0.1 * math.sin(t * 7 + k))
            rings.append([Vector((math.cos(TAU * i / n) * r * rnd.uniform(0.82, 1.12),
                                  math.sin(TAU * i / n) * r * rnd.uniform(0.82, 1.12), t * 4.0)) for i in range(n)])
        p.loft(rings, 'Mountain')
        for i in range(6):
            a = rnd.uniform(0, TAU)
            p.ico((math.cos(a) * 0.25, math.sin(a) * 0.25, 4.0), rnd.uniform(0.3, 0.45), 'Leaf_Dark', 1, (1, 1, 0.6))
        for i in range(26):
            a = rnd.uniform(0, TAU); zz = rnd.uniform(0.6, 3.8)
            rr = (1.0 - 0.55 * zz / 4) * 0.97
            p.ico((math.cos(a) * rr, math.sin(a) * rr, zz), rnd.uniform(0.14, 0.3), rnd.choice(('Leaf_Green', 'Leaf_Dark')),
                  1, (1, 1, 0.6))
        _register(name, p)
    for o in coll(ASSET_COLL).objects:
        o.hide_render = True


def build_far_world():
    rnd = random.Random(750)
    # karst mountains rising out of the cloud sea (the tower is visible from far away)
    for i in range(54):
        deg = rnd.uniform(0, 360)
        dist = rnd.uniform(1300, 4200)
        if 225 < deg < 315 and dist < 3000:          # keep the southern sight-line to the tower clear
            deg += 90 if deg < 270 else -90
        s = rnd.uniform(90, 200)
        h = s * rnd.uniform(0.6, 1.25)
        inst(f'Karst_{"ABC"[i % 3]}', f'Mountain_{i:02d}', ENV, polar(dist, deg, -760), rnd.uniform(0, TAU),
             (s, s, h * 0.95))
    # nearer cliff pillars flanking the hub (like the reference side cliffs)
    for i, (deg, dist, s, h) in enumerate(((10, 640, 70, 240), (170, 660, 80, 260), (30, 860, 90, 320),
                                           (150, 880, 90, 340))):
        inst(f'Karst_{"ABC"[i % 3]}', f'Cliff_Pillar_{i}', ENV, polar(dist, deg, -380), rnd.uniform(0, TAU),
             (s, s, (h + 380) / 4))
    # sea far below + sea of clouds
    p = Part('Sea', ENV)
    p.cyl((0, 0, -705), 9000, 2, 'Sea', 64)
    p.finish()
    for i in range(170):
        deg = rnd.uniform(0, 360)
        dist = math.sqrt(rnd.random()) * 3400
        inst(f'Cloud_{"ABCD"[i % 4]}', f'CloudSea_{i:03d}', ENV, polar(dist, deg, rnd.uniform(-420, -330)),
             rnd.uniform(0, TAU), rnd.uniform(70, 140))
    # sky clouds + cloud bands wrapping the tower (it vanishes into them from the hub)
    for i in range(46):
        deg = rnd.uniform(0, 360)
        dist = rnd.uniform(500, 2600)
        if 210 < deg < 330 and dist < 2200:
            deg += 120
        inst(f'Cloud_{"ABCD"[i % 4]}', f'SkyCloud_{i:02d}', SKY, polar(dist, deg, rnd.uniform(250, 2600)),
             rnd.uniform(0, TAU), rnd.uniform(40, 110))
    for band_z, cnt, rr in ((760, 10, (310, 380)), (1470, 12, (240, 320))):
        for i in range(cnt):
            deg = i * 360 / cnt + rnd.uniform(-10, 10)
            inst(f'Cloud_{"ABCD"[i % 4]}', f'TowerCloud_{band_z}_{i:02d}', SKY,
                 TP(rnd.uniform(*rr), deg, band_z + rnd.uniform(-25, 25)), math.radians(deg + 90), rnd.uniform(24, 40))


# ---------------------------------------------------------------- sky/light -
def build_sky_and_sun():
    sc = bpy.context.scene
    w = bpy.data.worlds.new('Sky_Fantasy')
    sc.world = w
    nt = w.node_tree
    bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = -0.05
    mr.inputs['From Max'].default_value = 0.75
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (0.78, 0.88, 1.0, 1)
    el[1].position = 1.0; el[1].color = (0.10, 0.30, 0.85, 1)
    e = el.new(0.25); e.color = (0.45, 0.68, 1.0, 1)
    L = nt.links.new
    L(tc.outputs['Generated'], sep.inputs['Vector']); L(sep.outputs['Z'], mr.inputs['Value'])
    L(mr.outputs['Result'], ramp.inputs['Fac']); L(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.8
    w.mist_settings.start = 450
    w.mist_settings.depth = 6500
    w.mist_settings.falloff = 'QUADRATIC'
    sun = bpy.data.lights.new('Sun_Key', 'SUN')
    sun.energy = 3.4; sun.color = (1.0, 0.92, 0.80); sun.angle = math.radians(2.5)
    so = bpy.data.objects.new('Sun_Key', sun)
    direction = Vector((0.45, 0.75, -0.55)).normalized()
    so.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    so.location = (-400, -600, 900)
    coll(LIT).objects.link(so)


def build_compositor():
    sc = bpy.context.scene
    sc.view_layers[0].use_pass_mist = True
    ng = bpy.data.node_groups.new('Comp_HazeBloom', 'CompositorNodeTree')
    sc.compositing_node_group = ng
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    N = ng.nodes.new
    rl = N('CompositorNodeRLayers')
    lt = N('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.999
    mul = N('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    k = N('ShaderNodeMath'); k.operation = 'MULTIPLY'; k.inputs[1].default_value = 0.6
    mix = N('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MIX'
    a_in = next(s for s in mix.inputs if s.identifier == 'A_Color')
    b_in = next(s for s in mix.inputs if s.identifier == 'B_Color')
    f_in = next(s for s in mix.inputs if s.identifier == 'Factor_Float')
    b_in.default_value = (0.70, 0.83, 1.0, 1.0)
    gl = N('CompositorNodeGlare')
    gl.inputs['Type'].default_value = 'Bloom'
    gl.inputs['Threshold'].default_value = 1.2
    gl.inputs['Strength'].default_value = 0.35
    gl.inputs['Size'].default_value = 0.6
    out = N('NodeGroupOutput')
    Lk = ng.links.new
    Lk(rl.outputs['Mist'], lt.inputs[0])
    Lk(rl.outputs['Mist'], mul.inputs[0]); Lk(lt.outputs[0], mul.inputs[1])
    Lk(mul.outputs[0], k.inputs[0]); Lk(k.outputs[0], f_in)
    Lk(rl.outputs['Image'], a_in)
    Lk(mix.outputs[2] if len(mix.outputs) > 2 else mix.outputs[0], gl.inputs['Image'])
    Lk(gl.outputs['Image'], out.inputs[0])


# ---------------------------------------------------------------- cameras ---
def camera(name, loc, target, lens=24, ortho=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 0.5
    cam.clip_end = 40000
    if ortho:
        cam.type = 'ORTHO'; cam.ortho_scale = ortho
    o = bpy.data.objects.new(name, cam)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    coll(CAM).objects.link(o)
    return o


def build_cameras():
    c1 = camera('CAM_1_MainPlayerView', (0, -76, 14), (0, 152, 46), 20)
    camera('CAM_2_HubOverview', (0, -300, 165), (0, 45, 8), 24)
    camera('CAM_3_TowerLowAngle', (0, -29, 3.5), (0, 475, 1000), 15)
    camera('CAM_4_EntranceCloseUp', (0, 90, 30), (0, 152, 50), 24)
    top = camera('CAM_5_TopDownHub', (0, 25, 1200), (0, 25, 0), 50, ortho=420)
    top.rotation_euler = (0, 0, 0)
    top.data.clip_start = 700            # hub only (render.py also hides the tower floors for this camera)
    top['hide_collections'] = 'Jungle,Desert,Ice,Lava,Crystal,Shadow,Forest,Kingdom,Cloud,Celestial,Divine,Sky_Clouds,FLOATING_ISLANDS'
    camera('CAM_6_HeroFullTower', (-300, -1750, 190), (0, 475, 960), 20)
    bpy.context.scene.camera = c1


def build_environment():
    for c in (ENV, ISL, CAM):
        coll(c, 'TOWER_OF_PETS')
    coll(SKY, ENV)
    build_hub_rock()
    build_aqueduct_wings()
    build_island_assets()
    build_floating_islands()
    build_bridges()
    build_mountain_assets()
    build_far_world()
    build_sky_and_sun()
    build_compositor()
    build_cameras()
