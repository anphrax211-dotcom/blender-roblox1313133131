"""TOWER_TEMPLATE: the visible exterior of the Tower of Pets (visual landmark / dead end).

Built from the reference sheets, bottom -> top (heights in studs, from the side-view sheet):
    0  Hub base / foundation   z -40 .. 200   (fortress walls round the gatehouse)
    1  Jungle                  200 .. 350
    2  Desert                  350 .. 500
    3  Ice                     500 .. 660
    4  Lava                    660 .. 830
    5  Crystal                 830 .. 990
    6  Shadow                  990 .. 1150
    7  Enchanted Forest       1150 .. 1320
    8  Ancient Kingdom        1320 .. 1500
    9  Cloud                  1500 .. 1660
   10  Celestial              1660 .. 1830
   11  Divine                 1830 .. 2010 (+ spire ~2190)

Every themed floor shares one 'shell' (overhanging ledge on corbels, buttressed lower wall,
terrace, recessed upper wall, cornice, turrets, balconies, a helical outer stair) whose
radius, rotation and proportions change per floor, and then gets its own theme pieces, so
the silhouette steps and varies instead of reading as stacked cylinders.
No interiors are built.
"""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
from common import (Part, coll, inst, paw, M_front, pointed_arch, round_arch, canopy, waterfall,
                    rock_blob, ASSETS, TAU)

TC = Vector((0.0, 475.0, 0.0))          # tower axis
R_FOUND = 300.0
ROOT = 'TOWER_TEMPLATE'
WF = 'WATERFALLS'

FLOORS = [  # key, collection, z0, z1, radius
    ('Jungle', 200, 350, 285), ('Desert', 350, 500, 272), ('Ice', 500, 660, 258),
    ('Lava', 660, 830, 262), ('Crystal', 830, 990, 242), ('Shadow', 990, 1150, 230),
    ('Forest', 1150, 1320, 222), ('Kingdom', 1320, 1500, 200), ('Cloud', 1500, 1660, 176),
    ('Celestial', 1660, 1830, 100), ('Divine', 1830, 2010, 180)]
LEDGES = {}            # floor -> (z, ledge radius) used by environment for bridges


def P(r, deg, z=0.0):
    a = math.radians(deg)
    return Vector((TC.x + r * math.cos(a), TC.y + r * math.sin(a), z))


def ngon(r, n, rot=0.0, jitter=0.0, rnd=None):
    out = []
    for i in range(n):
        rr = r + (rnd.uniform(-jitter, jitter) if jitter else 0)
        a = math.radians(rot + i * 360 / n)
        out.append((TC.x + rr * math.cos(a), TC.y + rr * math.sin(a)))
    return out


def face_M(r, deg, z):
    """local XY drawing on the outside of a wall at angle deg (local +Z points outward)"""
    x, y, _ = P(r, deg)
    return M_front(x, y, z, math.radians(deg) + math.pi / 2)


def rotz(deg):
    return Matrix.Rotation(math.radians(deg), 3, 'Z')


def point_light(name, loc, color, energy, radius=8.0):
    L = bpy.data.lights.new(name, 'POINT')
    L.color = color; L.energy = energy; L.shadow_soft_size = radius
    o = bpy.data.objects.new(name, L); o.location = loc
    coll('LIGHTING').objects.link(o)
    return o


# ---------------------------------------------------------------- annexes ---
def annex(p, th, deg, r_in, z, w, dep, h, roof, rnd):
    """block building pushed out from the wall: inner face at radius r_in, `dep` deep, standing at z.
    Overhanging parts get corbels and a pier so the silhouette steps out like the reference."""
    R = rotz(deg + 90)                      # local x = tangent, local -y = outward
    r_out = r_in + dep
    p.box(P(r_in + dep / 2, deg, z + h / 2), (w, dep, h), th['wall2'], R)
    p.box(P(r_in + dep / 2, deg, z + h + 1.0), (w + 2.4, dep + 2.4, 2.0), th['trim'], R)
    for s in (-1, 1):                                               # corner piers
        off = math.degrees((w / 2) / r_out) * s
        p.box(P(r_out, deg + off, z + h / 2), (3.4, 3.4, h + 1), th['trim'], R)
    # support: corbels + pier dropping below the floor line
    for s in (-1, 0, 1):
        off = math.degrees((w * 0.35) / r_out) * s
        p.beam(P(r_in - 2, deg + off, z - 22), P(r_out - 2, deg + off, z - 1), 3.0, 3.0, th['trim'])
    p.box(P(r_out - 4, deg, z - 18), (6, 6, 36), th['wall'], R)
    p.cone(P(r_out - 4, deg, z - 36), 3, -10, th['trim'], 4)
    # windows on the outer face (two rows)
    n_w = max(1, int(w / 9))
    for row in range(2):
        zz = z + h * (0.2 + 0.42 * row)
        for i in range(n_w):
            off = math.degrees(((i + 0.5) / n_w - 0.5) * w * 0.8 / r_out)
            M = face_M(r_out + 0.05, deg + off, zz)
            p.prism(pointed_arch(3.4, h * 0.18, 2.0), 0, 0.5, th['window'], M)
    top = z + h + 2.0
    c = P(r_in + dep / 2, deg, top)
    if roof == 'flat':
        for i in range(int(w / 5)):
            off = math.degrees(((i + 0.5) / int(w / 5) - 0.5) * w / r_out)
            p.box(P(r_out, deg + off, top + 1.4), (2.6, 2.6, 2.8), th['trim'], R)
    elif roof in ('cone', 'spire'):
        k = 0.9 if roof == 'cone' else 2.0
        p.cone(c, min(w, dep) * 0.62, min(w, dep) * k, th['roof'], 4 if roof == 'spire' else 8)
        p.cone(c + Vector((0, 0, min(w, dep) * k)), 0.6, 5, 'Gold', 6)
    elif roof == 'dome':
        p.uvsphere(c, min(w, dep) * 0.42, th['roof'], 14, 8, (1, 1, 1.1))
    elif roof == 'gable':
        M = Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg + 90), 4, 'Z') @ \
            Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        p.prism([(-w / 2 - 1.5, 0), (w / 2 + 1.5, 0), (0, w * 0.4)], -dep / 2 - 1.5, dep / 2 + 1.5, th['roof'], M)
    elif roof == 'spike':
        for i in range(4):
            off = math.degrees((i / 3 - 0.5) * w * 0.7 / r_out)
            p.cone(P(r_in + dep * rnd.uniform(0.3, 0.7), deg + off, top), 3.0, rnd.uniform(8, 16), th['roof'], 5)


# ---------------------------------------------------------------- shell -----
THEMES = {
    'Jungle': dict(wall='Jungle_Stone', wall2='Jungle_Stone', trim='Mossy_Stone', ledge='Mossy_Stone',
                   window='Window_Warm', roof='Leaf_Green', turret='dome', light=(0.4, 1.0, 0.35), rock='Cliff_Rock'),
    'Desert': dict(wall='Desert_Sandstone', wall2='Desert_Sandstone', trim='Desert_Sandstone',
                   ledge='Desert_Sandstone', window='Window_Warm', roof='Desert_Gold', turret='dome',
                   light=(1.0, 0.75, 0.35), rock='Desert_Sandstone'),
    'Ice': dict(wall='Ice', wall2='Ice', trim='Snow', ledge='Ice', window='Window_Blue', roof='Ice_Clear',
                turret='spire', light=(0.45, 0.75, 1.0), rock='Ice'),
    'Lava': dict(wall='Lava_Rock', wall2='Lava_Rock', trim='Iron', ledge='Lava_Rock', window='Lava',
                 roof='Lava_Rock', turret='spike', light=(1.0, 0.35, 0.08), rock='Lava_Rock'),
    'Crystal': dict(wall='Crystal_Rock', wall2='Crystal_Rock', trim='Shadow_Stone', ledge='Crystal_Rock',
                    window='Crystal_Pink', roof='Crystal_Purple', turret='spire', light=(0.7, 0.35, 1.0),
                    rock='Crystal_Rock'),
    'Shadow': dict(wall='Shadow_Stone', wall2='Shadow_Stone', trim='Shadow_Stone', ledge='Shadow_Stone',
                   window='Shadow_Glow', roof='Shadow_Stone', turret='spire', light=(0.55, 0.2, 1.0)),
    'Forest': dict(wall='Mossy_Stone', wall2='Forest_Wood', trim='Forest_Wood', ledge='Mossy_Stone',
                   window='Forest_Glow', roof='Leaf_Dark', turret='dome', light=(0.45, 1.0, 0.4), rock='Cliff_Rock_Dark'),
    'Kingdom': dict(wall='Kingdom_Stone', wall2='Kingdom_Stone', trim='Kingdom_Stone', ledge='Kingdom_Stone',
                    window='Window_Warm', roof='Roof_Blue', turret='cone', light=(1.0, 0.85, 0.6)),
    'Cloud': dict(wall='Cloud_Marble', wall2='Cloud_Marble', trim='Cloud_Marble', ledge='Cloud_Marble',
                  window='Window_Blue', roof='Gold', turret='dome', light=(0.75, 0.9, 1.0), rock='Cloud_Marble'),
}


def turret(p, base, rt, h, th, kind, n=10):
    """round tower standing on `base` with a theme roof"""
    base = Vector(base)
    p.cyl(base + Vector((0, 0, h / 2)), rt, h, th['wall'], n)
    p.cyl(base + Vector((0, 0, h - 1.2)), rt + 1.4, 2.4, th['trim'], n)
    top = base + Vector((0, 0, h))
    if kind == 'cone':
        p.cone(top, rt + 1.6, rt * 2.6, th['roof'], n)
        p.cone(top + Vector((0, 0, rt * 2.6)), 0.6, 4, 'Gold', 6)
    elif kind == 'spire':
        p.cone(top, rt + 0.8, rt * 4.0, th['roof'], 6)
    elif kind == 'dome':
        p.uvsphere(top, rt + 0.5, th['roof'], 12, 8, (1, 1, 1.15))
        p.cone(top + Vector((0, 0, rt * 1.1)), 0.8, 4, 'Gold', 6)
    elif kind == 'spike':
        for k in range(5):
            a = TAU * k / 5
            p.cone(top + Vector((math.cos(a) * rt * 0.6, math.sin(a) * rt * 0.6, 0)), rt * 0.4, rt * 1.4,
                   th['roof'], 5)
    # slit windows
    for k in range(4):
        a = TAU * k / 4 + 0.4
        w = base + Vector((math.cos(a) * (rt + 0.1), math.sin(a) * (rt + 0.1), h * 0.62))
        p.box(w, (1.4, 1.4, 4.0), th['window'], rotz(math.degrees(a)))


def tier_shell(key, z0, z1, r, rnd, n=16, lower=0.52, upper_k=0.84, ledge=16.0, turrets=4, balconies=2,
               ramp=True, win_rows=(1, 1), cornice=10.0, annexes=5, roof='flat', hanging=3, towers=2):
    th = THEMES[key]
    cname = key
    p = Part(f'{key}_Shell', cname)
    rot = rnd.uniform(0, 360 / n)
    H = z1 - z0
    zm = z0 + 2 + H * lower
    ru = r * upper_k
    # overhanging ledge on corbels -----------------------------------------------------------------
    radii = [r + ledge + rnd.uniform(-3, 3) for _ in range(n * 2)]
    for _ in range(3):                                   # a few extended platform sectors
        s0 = rnd.randrange(n * 2)
        for j in range(rnd.randint(2, 4)):
            radii[(s0 + j) % (n * 2)] += 24
    pts = [(TC.x + rr * math.cos(math.radians(rot + i * 180 / n)), TC.y + rr * math.sin(math.radians(rot + i * 180 / n)))
           for i, rr in enumerate(radii)]
    p.prism(pts, z0 - 5, z0 + 2, th['ledge'])
    p.prism([(TC.x + (x - TC.x) * 1.008, TC.y + (y - TC.y) * 1.008) for x, y in pts], z0 + 2, z0 + 3.0, th['trim'])
    if 'rock' in th:
        # rocky underside: each floor sits on its own floating-island style rock base
        n2 = n * 2
        rings = [[Vector((x, y, z0 - 5)) for x, y in pts]]
        for k, (s, dz) in enumerate(((0.93, 0.07), (0.78, 0.17), (0.6, 0.27))):
            ring = []
            for i, (x, y) in enumerate(pts):
                j = rnd.uniform(0.9, 1.06)
                ring.append(Vector((TC.x + (x - TC.x) * s * j, TC.y + (y - TC.y) * s * j,
                                    z0 - 5 - H * dz + rnd.uniform(-4, 4))))
            rings.append(ring)
        p.loft(rings, th['rock'], cap_top=False)
        for k in range(10):                                  # hanging rock chunks
            deg = rnd.uniform(0, 360)
            rock_blob(p, P((r + ledge) * rnd.uniform(0.75, 0.9), deg, z0 - H * rnd.uniform(0.12, 0.24)),
                      rnd.uniform(12, 22), th['rock'], rnd, 1, (1, 1, 1.5))
    else:
        for i in range(n * 2):
            deg = rot + (i + 0.5) * 180 / n
            p.beam(P(r - 2, deg, z0 - 22), P(r + ledge - 3, deg, z0 - 4.5), 4.0, 4.0, th['trim'])
    LEDGES[key] = (z0 + 2, r + ledge)
    # lower wall + buttresses -------------------------------------------------------------------------
    p.prism(ngon(r, n, rot), z0 + 2, zm, th['wall'])
    for i in range(n):
        deg = rot + i * 360 / n
        c = P(r + 2.5, deg, (z0 + 2 + zm) / 2)
        p.box(c, (r * 0.04, r * 0.045, zm - z0 - 2), th['wall'], rotz(deg + 90))
        p.cone(P(r + 2.5, deg, zm), r * 0.03, 8, th['trim'], 4)
    # terrace, recessed upper wall, cornice ----------------------------------------------------------
    p.prism(ngon(r + 7, n, rot), zm, zm + 2.5, th['trim'])
    p.prism(ngon(ru, n, rot + 180 / n), zm + 2.5, z1 - 5, th['wall2'])
    p.prism(ngon(ru + cornice, n, rot + 180 / n), z1 - 5, z1, th['trim'])
    # windows ----------------------------------------------------------------------------------------
    ap_l, ap_u = r * math.cos(math.pi / n), ru * math.cos(math.pi / n)
    wl = min(2 * r * math.sin(math.pi / n) * 0.16, 11.0)
    wu = min(2 * ru * math.sin(math.pi / n) * 0.16, 10.0)
    for i in range(n):
        deg_l = rot + (i + 0.5) * 360 / n
        deg_u = rot + 180 / n + (i + 0.5) * 360 / n
        hl = (zm - z0) * 0.42
        for k in range(win_rows[0]):
            zz = z0 + 2 + (zm - z0) * (0.18 + 0.45 * k / max(1, win_rows[0]))
            M = face_M(ap_l, deg_l, zz)
            for off in (-wl * 1.1, wl * 1.1):
                p.prism([(x + off, z) for x, z in pointed_arch(wl, hl / win_rows[0] * 0.8, wl * 0.6)], 0, 0.6,
                        th['window'], M)
            p.prism([(-wl * 1.8, -1.2), (wl * 1.8, -1.2), (wl * 1.8, 0), (-wl * 1.8, 0)], 0, 1.2,
                    th['trim'], M)
        hu = (z1 - zm) * 0.4
        for k in range(win_rows[1]):
            zz = zm + 2.5 + (z1 - zm) * (0.15 + 0.4 * k / max(1, win_rows[1]))
            p.prism(pointed_arch(wu, hu / win_rows[1] * 0.8, wu * 0.6), 0, 0.6, th['window'], face_M(ap_u, deg_u, zz))
    # turrets on the terrace -------------------------------------------------------------------------
    for k in range(turrets):
        deg = rot + 180 / n + k * 360 / turrets + rnd.uniform(-12, 12)
        rt = min(16.0, (r + 7 - ru) * 0.5)
        turret(p, P(ru + rt * 0.6, deg, zm + 2.5), rt, (z1 - zm) * rnd.uniform(1.0, 1.25), th, th['turret'])
    # balconies ---------------------------------------------------------------------------------------
    for k in range(balconies):
        deg = rot + (rnd.randrange(n) + 0.5) * 360 / n
        zb = z0 + 2 + (zm - z0) * rnd.uniform(0.45, 0.7)
        R = rotz(deg + 90)
        p.box(P(ap_l + 5, deg, zb), (16, 10, 1.6), th['trim'], R)
        for j in range(7):
            p.box(P(ap_l + 9.4, deg + (j - 3) * 2.3 * 57.3 / (ap_l + 9.4), zb + 1.8), (1, 1, 2.2), th['trim'], R)
        p.box(P(ap_l + 9.4, deg, zb + 3.1), (16, 1.0, 0.6), th['trim'], R)
        p.prism(pointed_arch(5, 7, 3), 0, 0.8, th['window'], face_M(ap_l, deg, zb + 0.8))
    # helical outer stair (exterior vertical connection) ------------------------------------------------
    if ramp:
        d0 = rot + rnd.uniform(0, 360)
        steps = 36
        for j in range(steps):
            deg = d0 + j * 110 / steps
            zz = z0 + 2 + (zm - z0 - 2) * j / steps
            R = rotz(deg + 90)
            p.box(P(r + 6, deg, zz + 0.6), (8.0, 9, 1.2), th['trim'], R)
            p.box(P(r + 10.2, deg, zz + 2.2), (1.0, 1.0, 3.2), th['trim'], R)
    # tall towers rising from the ledge through the floor above (breaks the horizontal banding) ---------
    for k in range(towers):
        deg = rot + rnd.uniform(0, 360)
        rt = r * rnd.uniform(0.055, 0.075)
        turret(p, P(r + ledge * 0.45, deg, z0 + 2), rt, H * rnd.uniform(1.05, 1.45), th, th['turret'], 12)
    # annex buildings breaking the silhouette (on the ledge and on the terrace) -------------------------
    for k in range(annexes):
        deg = rot + k * 360 / annexes + rnd.uniform(-20, 20)
        on_terrace = k % 3 == 2
        w, dep = r * rnd.uniform(0.12, 0.2), r * rnd.uniform(0.09, 0.15)
        h = rnd.uniform(0.35, 0.6) * (z1 - z0)
        if on_terrace:
            annex(p, th, deg, ru - 4, zm + 2.5, w * 0.8, (r - ru) + dep * 0.6, h * 0.8, roof, rnd)
        else:
            annex(p, th, deg, r - 4, z0 + 2, w, dep + ledge * 0.5, h, roof, rnd)
    # cages / lantern pods hanging under the ledge -----------------------------------------------------
    for k in range(hanging):
        deg = rnd.uniform(0, 360)
        top = P(r + ledge - 4, deg, z0 - 5)
        L = rnd.uniform(10, 24)
        for j in range(int(L / 2)):
            p.box(top - Vector((0, 0, j * 2 + 1)), (0.5, 0.5, 2.0), 'Iron')
        c = top - Vector((0, 0, L + 3))
        p.cyl(c, 3.2, 6, th['trim'], 8)
        p.cyl(c, 2.4, 4.6, th['window'], 8)
        p.cone(c + Vector((0, 0, 3)), 3.8, 3, th['trim'], 8)
    ob = p.finish()
    # coloured floor lights -----------------------------------------------------------------------------
    for k, deg in enumerate((235, 270, 305)):
        point_light(f'{key}_Light_{k}', P(r + 40, deg, (z0 + z1) / 2), th['light'], 120000, 12)
    return dict(p=ob, rot=rot, zm=zm, ru=ru, r=r, z0=z0, z1=z1, n=n, th=th)


# ---------------------------------------------------------------- foundation -
def build_foundation():
    c = 'Hub_Base'
    coll(c, ROOT)
    rnd = random.Random(100)
    th = dict(wall='Hub_Stone', wall2='Hub_Stone_Warm', trim='Stone_Trim', window='Window_Warm',
              roof='Roof_Blue')
    p = Part('HubBase_Fortress', c)
    n = 24
    rot = 270 + 7.5
    # lower massive wall from the hub level to the first terrace
    p.prism(ngon(R_FOUND, n, rot), -40, 110, 'Hub_Stone')
    p.prism(ngon(R_FOUND + 4, n, rot), 108, 112, 'Stone_Trim')
    for i in range(n):
        deg = rot + i * 360 / n
        p.box(P(R_FOUND + 3, deg, 35), (12, 13, 150), 'Hub_Stone_Warm', rotz(deg + 90))
        p.cone(P(R_FOUND + 3, deg, 108), 8.5, 10, 'Stone_Trim', 4)
        # arched windows between buttresses (upper half only, away from the gatehouse)
        degf = deg + 360 / n / 2
        if abs(((degf - 270) + 180) % 360 - 180) > 13:
            ap = R_FOUND * math.cos(math.pi / n)
            for zz in (52, 80):
                p.prism(pointed_arch(14, 14, 7), 0, 0.6, 'Window_Warm', face_M(ap, degf, zz))
                p.prism([(-9.5, -1.4), (9.5, -1.4), (9.5, 0), (-9.5, 0)], 0, 1.4, 'Stone_Trim',
                        face_M(ap, degf, zz))
    # upper wall to z=200 (recessed), cornice, crenellations
    ru = 276.0
    p.prism(ngon(ru, n, rot + 7.5), 112, 192, 'Hub_Stone_Warm')
    p.prism(ngon(ru + 10, n, rot + 7.5), 192, 200, 'Stone_Trim')
    ap = ru * math.cos(math.pi / n)
    for i in range(n):
        deg = rot + 7.5 + (i + 0.5) * 360 / n
        p.prism(round_arch(16, 16, 6), 0, 0.6, 'Window_Warm', face_M(ap, deg, 132))
        p.prism(pointed_arch(10, 12, 5), 0, 0.6, 'Window_Warm', face_M(ap, deg, 165))
    for i in range(n * 3):
        deg = rot + i * 120 / n
        p.box(P(R_FOUND + 2.5, deg, 115), (3, 3, 6), 'Hub_Stone', rotz(deg))
    # big corner bastions with blue roofs flanking the gatehouse
    for deg in (250, 290, 222, 318, 195, 345):
        turret(p, P(R_FOUND - 2, deg, -40), 20, 180 if deg in (250, 290) else 160,
               dict(wall='Hub_Stone_Warm', trim='Stone_Trim', roof='Roof_Blue', window='Window_Warm'), 'cone', 16)
    p.finish()
    # terrace greenery (tree-tops visible above the walls, as in the hub sheets)
    for k in range(40):
        deg = 180 + k * 180 / 39 + rnd.uniform(-2, 2)
        inst(rnd.choice(('Tree_A', 'Tree_B', 'Tree_C')), f'HubBase_Tree_{k}', c,
             P(rnd.uniform(ru + 6, R_FOUND - 4), deg, 112), rnd.uniform(0, TAU), rnd.uniform(1.6, 2.4))
    for k in range(20):
        deg = 200 + k * 140 / 19
        inst(rnd.choice(('Tree_A', 'Tree_B')), f'HubBase_TopTree_{k}', c,
             P(rnd.uniform(ru - 12, ru + 4), deg, 200), rnd.uniform(0, TAU), rnd.uniform(1.8, 2.6))
    # waterfalls pouring off the first terrace and the top (flanking the gatehouse)
    for k, (deg, z, w, drop) in enumerate(((222, 112, 14, 112), (318, 112, 14, 112), (250, 200, 10, 88),
                                           (290, 200, 10, 88), (196, 112, 12, 160), (344, 112, 12, 160))):
        lip = P(R_FOUND + 6 if z < 150 else ru + 10, deg, z)
        waterfall(f'Waterfall_HubBase_{k}', WF, lip, (math.cos(math.radians(deg)), math.sin(math.radians(deg))),
                  drop, w, seed=200 + k)
    point_light('HubBase_Light_Warm', P(R_FOUND + 50, 270, 90), (1.0, 0.8, 0.55), 60000, 10)


# ---------------------------------------------------------------- floors ----
def jungle(s, rnd):
    c = 'Jungle'
    z0, z1, r, zm, ru = s['z0'], s['z1'], s['r'], s['zm'], s['ru']
    p = Part('Jungle_Details', c)
    # ruined columns and moss slabs on the ledge
    for k in range(10):
        deg = rnd.uniform(0, 360)
        h = rnd.uniform(6, 16)
        p.cyl(P(r + 10, deg, z0 + 2 + h / 2), 1.8, h, 'Jungle_Stone', 8)
        p.box(P(r + 10, deg, z0 + 2 + h + 0.6), (4.5, 4.5, 1.2), 'Mossy_Stone', rotz(deg))
    # hanging vines from the cornice and terrace
    for k in range(110):
        deg = rnd.uniform(0, 360)
        top = (z1 - 4) if k % 2 else zm + 1
        rr = (ru + 6) if k % 2 else (r + 4.5)
        L = rnd.uniform(10, 40)
        for j in range(int(L / 3)):
            p.ico(P(rr + 0.5, deg + rnd.uniform(-0.3, 0.3), top - j * 3), rnd.uniform(1.0, 1.7),
                  rnd.choice(('Leaf_Green', 'Leaf_Dark', 'Leaf_Light')), 1, (1, 1, 1.3))
    # canopy masses spilling over the cornice and terrace edges
    for k in range(30):
        deg = k * 12 + rnd.uniform(-4, 4)
        canopy(p, P(ru + 8, deg, z1 + 2), rnd.uniform(9, 15), ('Leaf_Green', 'Leaf_Light', 'Leaf_Dark'), rnd, 4)
    for k in range(18):
        deg = k * 20 + rnd.uniform(-6, 6)
        canopy(p, P(r + 6, deg, zm + 4), rnd.uniform(5, 8), ('Leaf_Green', 'Leaf_Light'), rnd, 4)
    p.finish()
    for k in range(16):
        deg = k * 22.5 + rnd.uniform(-6, 6)
        inst(rnd.choice(('Tree_A', 'Tree_B')), f'Jungle_Tree_{k}', c, P(r + rnd.uniform(6, 16), deg, z0 + 2),
             rnd.uniform(0, TAU), rnd.uniform(2.0, 3.0))
    for k, deg in enumerate((215, 252, 293, 330, 40, 120)):
        a = math.radians(deg)
        waterfall(f'Waterfall_Jungle_{k}', WF, P(r + 6, deg, zm + 1), (math.cos(a), math.sin(a)),
                  rnd.uniform(70, 130), rnd.uniform(9, 14), seed=300 + k)


def desert(s, rnd):
    c = 'Desert'
    z0, z1, r, zm, ru, n, rot = s['z0'], s['z1'], s['r'], s['zm'], s['ru'], s['n'], s['rot']
    p = Part('Desert_Details', c)
    # arcade of round arches on the upper wall
    ap = ru * math.cos(math.pi / n)
    for i in range(n * 2):
        deg = rot + 180 / n + (i + 0.5) * 180 / n
        p.prism(round_arch(7, 10, 6), 0, 0.5, 'Stone_Dark', face_M(ap + 0.6, deg, zm + 6))
        p.box(P(ap + 1.5, deg + 90 / n, zm + 2.5 + 9), (2.4, 2.4, 18), 'Desert_Sandstone', rotz(deg))
    # domes and pyramids on the ledge, obelisks with gold tips
    for k in range(6):
        deg = k * 60 + 30 + rnd.uniform(-8, 8)
        b = P(r + 8, deg, z0 + 2)
        p.box(b + Vector((0, 0, 6)), (12, 12, 12), 'Desert_Sandstone', rotz(deg))
        p.uvsphere(b + Vector((0, 0, 12)), 6.5, 'Desert_Gold', 14, 8, (1, 1, 1.0))
    for k in range(5):
        deg = k * 72 + rnd.uniform(-10, 10)
        p.cone(P(r + 10, deg, z0 + 2), 8, 10, 'Desert_Sandstone', 4)
        o = P(r + 12, deg + 14, z0 + 2)
        p.cyl(o + Vector((0, 0, 9)), 1.6, 18, 'Desert_Sandstone', 4, r2=1.0)
        p.cone(o + Vector((0, 0, 18)), 1.1, 3, 'Desert_Gold', 4)
    # a big central temple gate on the front
    M = face_M(ru + 4, 270 + rnd.uniform(-20, 20), zm + 2.5)
    p.prism([(-14, 0), (14, 0), (14, 26), (-14, 26)], 0, 3, 'Desert_Sandstone', M)
    p.prism(round_arch(10, 10, 8), 0, 3.4, 'Window_Warm', M)
    p.prism([(-16, 26), (16, 26), (0, 36)], 0, 3, 'Desert_Gold', M)
    p.finish()
    for k in range(5):
        deg = rnd.uniform(0, 360)
        inst('Tree_C', f'Desert_Palm_{k}', c, P(r + 9, deg, z0 + 2), 0, 1.4)


def ice(s, rnd):
    c = 'Ice'
    z0, z1, r, zm, ru = s['z0'], s['z1'], s['r'], s['zm'], s['ru']
    p = Part('Ice_Details', c)
    # snow caps and icicles under the ledges
    for rr, zz in ((r + 16, z0 - 5), (r + 5, zm), (ru + 7, z1 - 5)):
        for k in range(int(rr / 2.2)):
            deg = k * 360 / int(rr / 2.2) + rnd.uniform(-1, 1)
            p.cone(P(rr - 1.5, deg, zz), rnd.uniform(0.9, 1.6), -rnd.uniform(3, 9), 'Ice_Clear', 5)
    for rr, zz in ((r + 16, z0 + 3.2), (r + 5, zm + 2.5), (ru + 7, z1)):
        p.prism(ngon(rr + 0.5, 32, 0, 0.8, rnd), zz, zz + 1.2, 'Snow')
    # frozen waterfalls down the walls
    for k in range(6):
        deg = k * 60 + 15 + rnd.uniform(-5, 5)
        top = P(ru + 6, deg, z1 - 6)
        bot = P(r + 15, deg, z0 - 30)
        p.beam(top, bot, 9, 2.0, 'Ice_Clear')
    # ice spikes on the ledge
    for k in range(18):
        deg = rnd.uniform(0, 360)
        b = P(r + rnd.uniform(6, 14), deg, z0 + 2)
        tilt = Euler((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0)).to_matrix()
        h = rnd.uniform(6, 16)
        p.cyl(b + tilt @ Vector((0, 0, h / 2)), 0, h, 'Ice_Clear', 6, r2=rnd.uniform(1.4, 2.6), rot=tilt)
    p.finish()
    for k in range(10):
        inst('Pine', f'Ice_Pine_{k}', c, P(r + rnd.uniform(6, 14), rnd.uniform(0, 360), z0 + 2), 0, 1.6)


def lava(s, rnd):
    c = 'Lava'
    z0, z1, r, zm, ru, n, rot = s['z0'], s['z1'], s['r'], s['zm'], s['ru'], s['n'], s['rot']
    p = Part('Lava_Details', c)
    # glowing cracks across the walls
    for k in range(60):
        deg = rnd.uniform(0, 360)
        upper = k % 2
        rr = (ru if upper else r) * math.cos(math.pi / n) + 0.3
        z = rnd.uniform(zm + 6, z1 - 10) if upper else rnd.uniform(z0 + 6, zm - 6)
        a, b = P(rr, deg, z), P(rr, deg + rnd.uniform(-2, 2), z - rnd.uniform(6, 16))
        p.beam(a, b, 0.9, 0.8, 'Lava')
    # lava falls pouring from the cornice + glowing lava moat on the ledge
    for k in range(7):
        deg = k * 360 / 7 + rnd.uniform(-6, 6)
        p.beam(P(ru + 7, deg, z1 - 3), P(ru + 8.5, deg, zm + 2), rnd.uniform(5, 8), 1.6, 'Lava')
        p.beam(P(r + 5.5, deg + 3, zm + 1), P(r + 17, deg + 3, z0 - 50), rnd.uniform(4, 7), 1.6, 'Lava')
    p.ring_sector(r + 6, r + 12, 0, TAU, z0 + 2, z0 + 2.6, 'Lava', 64, center=(TC.x, TC.y))
    # obsidian spikes and iron chains
    for k in range(24):
        deg = rnd.uniform(0, 360)
        p.cone(P(r + rnd.uniform(12, 15), deg, z0 + 2), rnd.uniform(1.5, 3), rnd.uniform(6, 14), 'Lava_Rock', 5)
    for k in range(8):
        deg = k * 45 + 10
        a, b = P(ru + 6, deg, z1 - 4), P(r + 15, deg + 4, z0 + 3)
        L = (b - a).length
        for j in range(int(L / 2.2)):
            q = a + (b - a) * (j / (L / 2.2)) - Vector((0, 0, math.sin(math.pi * j / (L / 2.2)) * 6))
            p.box(q, (0.8, 1.6, 2.2) if j % 2 else (1.6, 0.8, 2.2), 'Iron', rotz(deg))
    # volcano vents on the terrace
    for k in range(3):
        deg = k * 120 + 60
        b = P((r + ru) / 2, deg, zm + 2.5)
        p.cone(b, 9, 16, 'Lava_Rock', 8, r_top=3.5)
        p.cyl(b + Vector((0, 0, 16)), 3.4, 0.6, 'Lava', 8)
    p.finish()


def crystal(s, rnd):
    c = 'Crystal'
    z0, z1, r, zm, ru = s['z0'], s['z1'], s['r'], s['zm'], s['ru']
    for k in range(16):
        deg = k * 22.5 + rnd.uniform(-6, 6)
        z = (z0 + 2) if k % 2 == 0 else (zm + 2.5)
        rr = (r + rnd.uniform(4, 12)) if k % 2 == 0 else (ru + 4)
        inst(rnd.choice(('Crystals_A', 'Crystals_B')), f'Crystal_Cluster_{k}', c, P(rr, deg, z),
             rnd.uniform(0, TAU), rnd.uniform(9, 16))
    # giant crystals growing out of the walls at an angle
    p = Part('Crystal_Giants', c)
    for k in range(14):
        deg = k * 360 / 14 + rnd.uniform(-8, 8)
        b = P(r - 4, deg, rnd.uniform(z0 + 20, z1 - 30))
        out = Vector((math.cos(math.radians(deg)), math.sin(math.radians(deg)), rnd.uniform(0.5, 1.4))).normalized()
        q = out.to_track_quat('Z', 'Y').to_matrix()
        h = rnd.uniform(40, 75); rr = rnd.uniform(6, 11)
        m = rnd.choice(('Crystal_Purple', 'Crystal_Blue', 'Crystal_Pink'))
        p.cyl(b + out * h * 0.4, rr, h * 0.8, m, 6, rot=q)
        p.cyl(b + out * h * 0.9, 0, h * 0.2, m, 6, r2=rr, rot=q)
    p.finish()


def shadow(s, rnd):
    c = 'Shadow'
    z0, z1, r, zm, ru, n, rot = s['z0'], s['z1'], s['r'], s['zm'], s['ru'], s['n'], s['rot']
    p = Part('Shadow_Gothic', c)
    # flying buttresses from the ledge to the upper wall + spires on top of them
    for i in range(n):
        deg = rot + i * 360 / n
        a, b = P(r + 13, deg, z0 + 2), P(ru + 1, deg, z1 - 14)
        p.beam(a, b, 3.0, 3.0, 'Shadow_Stone')
        p.box(P(r + 13, deg, z0 + 14), (4, 4, 24), 'Shadow_Stone', rotz(deg))
        p.cone(P(r + 13, deg, z0 + 26), 3.0, 18, 'Shadow_Stone', 4)
    # tall pointed spires around the cornice
    for i in range(n):
        deg = rot + 180 / n + i * 360 / n
        p.cone(P(ru + 4, deg, z1), 2.6, rnd.uniform(16, 30), 'Shadow_Stone', 4)
    # big rose-like glowing windows on the front
    for deg in (270 - 40, 270, 270 + 40, 90):
        p.cyl(P(ru * math.cos(math.pi / n) + 0.5, deg, (zm + z1) / 2), 7, 0.8, 'Shadow_Glow', 12, axis='Y',
              rot=rotz(deg + 90))
    p.finish()


def forest(s, rnd):
    c = 'Forest'
    z0, z1, r, zm, ru = s['z0'], s['z1'], s['r'], s['zm'], s['ru']
    p = Part('Forest_GiantTree', c)
    # giant tree trunks rising through the floor, roots over the ledge
    for k in range(5):
        deg = k * 72 + 20
        base = P(ru * 0.75, deg, zm)
        top = P(ru * 0.6, deg + 15, z1 + 20)
        p.cyl((base + top) / 2, 22, (top - base).length, 'Forest_Wood', 10, r2=15,
              rot=(top - base).to_track_quat('Z', 'Y').to_matrix())
    for k in range(14):
        deg = k * 360 / 14 + rnd.uniform(-6, 6)
        a = P(ru * 0.9, deg, zm + 2)
        b = P(r + 14, deg + rnd.uniform(-5, 5), z0 + 1)
        p.beam(a, b, 4, 3, 'Forest_Wood')
    # glowing mushrooms / plants on the ledge
    for k in range(26):
        deg = rnd.uniform(0, 360)
        b = P(r + rnd.uniform(5, 14), deg, z0 + 2)
        h = rnd.uniform(2, 6)
        p.cyl(b + Vector((0, 0, h / 2)), 0.6, h, 'Fabric_Cream', 6)
        p.uvsphere(b + Vector((0, 0, h)), rnd.uniform(1.6, 3), 'Forest_Glow', 10, 5, (1, 1, 0.5))
    p.finish()
    q = Part('Forest_Canopy', c)
    for k in range(26):
        deg = k * 360 / 26 + rnd.uniform(-5, 5)
        canopy(q, P(ru * rnd.uniform(0.75, 1.2), deg, z1 + rnd.uniform(-10, 18)), rnd.uniform(22, 34),
               ('Leaf_Green', 'Leaf_Light', 'Leaf_Dark'), rnd, 4, 0.7)
    q.finish()
    for k, deg in enumerate((240, 300, 20, 160)):
        a = math.radians(deg)
        waterfall(f'Waterfall_Forest_{k}', WF, P(r + 6, deg, zm + 1), (math.cos(a), math.sin(a)),
                  rnd.uniform(80, 120), 10, seed=400 + k)


def kingdom(s, rnd):
    c = 'Kingdom'
    z0, z1, r, zm, ru, n, rot = s['z0'], s['z1'], s['r'], s['zm'], s['ru'], s['n'], s['rot']
    th = s['th']
    p = Part('Kingdom_Castle', c)
    # crenellations along the cornice and ledge
    for rr, zz, cnt in ((ru + 6, z1, 64), (r + 15, z0 + 3.2, 80)):
        for k in range(cnt):
            if k % 2:
                continue
            deg = k * 360 / cnt
            p.box(P(rr, deg, zz + 1.6), (3, 3.2, 3.2), 'Kingdom_Stone', rotz(deg))
    # round castle towers standing on the ledge
    for k in range(6):
        deg = k * 60 + 15 + rnd.uniform(-6, 6)
        turret(p, P(r + 9, deg, z0 + 2), 12, (zm - z0) * 1.2, th, 'cone', 12)
    # keep on top
    turret(p, P(ru * 0.45, rot, z1), 26, 40, th, 'cone', 16)
    # heraldic banners
    for k in range(8):
        deg = rot + (k + 0.5) * 45
        M = face_M(ru * math.cos(math.pi / n) + 0.6, deg, z1 - 8)
        p.prism([(-3.5, 0), (3.5, 0), (3.5, -20), (0, -24), (-3.5, -20)], 0, 0.4, 'Banner_Navy', M)
        paw(p, M @ Matrix.Translation((0, -12, 0.4)), 4.5, 0.3, 'Gold')
    p.finish()


def cloud(s, rnd):
    c = 'Cloud'
    z0, z1, r, zm, ru = s['z0'], s['z1'], s['r'], s['zm'], s['ru']
    p = Part('Cloud_Temple', c)
    # colonnade on the ledge and terrace
    for rr, zb, h, cnt in ((r + 11, z0 + 3.2, (zm - z0) * 0.55, 56), (ru + 4, z1, 26, 40)):
        for k in range(cnt):
            deg = k * 360 / cnt
            p.cyl(P(rr, deg, zb + h / 2), 1.4, h, 'Cloud_Marble', 10)
        p.prism(ngon(rr + 2.4, cnt, 0), zb + h, zb + h + 2, 'Cloud_Marble')
    # sky temple dome on top
    p.cyl(P(0, 0, z1 + 24), ru * 0.55, 6, 'Cloud_Marble', 24)
    p.uvsphere(P(0, 0, z1 + 27), ru * 0.5, 'Cloud_Marble', 24, 12, (1, 1, 0.75))
    p.cone(P(0, 0, z1 + 27 + ru * 0.37), 2, 14, 'Gold', 8)
    p.finish()
    for k in range(14):
        deg = k * 360 / 14 + rnd.uniform(-8, 8)
        inst(rnd.choice(('Cloud_A', 'Cloud_B', 'Cloud_C')), f'Cloud_Puff_{k}', c, P(r + rnd.uniform(5, 25), deg,
             z0 + rnd.uniform(-35, -5)), math.radians(deg + 90), rnd.uniform(16, 26))
    for k, deg in enumerate((230, 285, 340, 60, 140)):
        a = math.radians(deg)
        waterfall(f'Waterfall_Cloud_{k}', WF, P(r + 15, deg, z0 + 2), (math.cos(a), math.sin(a)),
                  rnd.uniform(140, 220), 8, seed=500 + k, foam=False)


def celestial(rnd):
    c = 'Celestial'
    coll(c, ROOT)
    z0, z1 = 1660, 1830
    p = Part('Celestial_Disc', c)
    # cosmic saucer: lofted rings
    profile = ((50, z0 - 10), (120, z0 + 8), (185, z0 + 30), (200, z0 + 40), (195, z0 + 48), (150, z0 + 55),
               (70, z0 + 60))
    rings = []
    for rr, zz in profile:
        rings.append([P(rr, i * 360 / 48, zz) for i in range(48)])
    p.loft(rings, 'Celestial_Stone', smooth=True)
    # core tower with blue windows
    p.prism(ngon(58, 12, 0), z0 + 58, z1 - 6, 'Celestial_Stone')
    p.prism(ngon(70, 12, 15), z1 - 6, z1, 'Celestial_Stone')
    for i in range(12):
        deg = (i + 0.5) * 30
        p.prism(pointed_arch(8, 30, 6), 0, 0.6, 'Window_Blue', face_M(58 * math.cos(math.pi / 12), deg, z0 + 80))
    # floating star shards around the disc
    for k in range(18):
        deg = rnd.uniform(0, 360)
        b = P(rnd.uniform(215, 300), deg, rnd.uniform(z0 - 20, z1 + 30))
        h = rnd.uniform(8, 18)
        p.cyl(b, rnd.uniform(2, 4), h, rnd.choice(('Crystal_Blue', 'Crystal_Purple')), 6)
        p.cone(b + Vector((0, 0, h / 2)), 3, 5, 'Crystal_Blue', 6)
        p.cone(b - Vector((0, 0, h / 2)), 3, -5, 'Crystal_Blue', 6)
    p.finish()
    q = Part('Celestial_Rings', c)
    q.torus(P(0, 0, z0 + 42), 208, 2.0, 'Celestial_Ring', 96, 6)
    q.torus(P(0, 0, z0 + 70), 240, 1.5, 'Celestial_Ring', 96, 6, rot=Euler((0.12, -0.08, 0)).to_matrix())
    q.torus(P(0, 0, z0 + 100), 130, 0.8, 'Magic_Glow', 72, 6, rot=Euler((-0.1, 0.15, 0)).to_matrix())
    # vertical beam of light through the centre (down toward the lower floors)
    q.cyl(P(0, 0, z0 + 40), 6, 260, 'Magic_Glow', 16)
    q.finish()
    LEDGES['Celestial'] = (z0 + 48, 195)
    for k, deg in enumerate((235, 305, 90)):
        point_light(f'Celestial_Light_{k}', P(250, deg, z0 + 60), (0.5, 0.35, 1.0), 200000, 14)


def divine(rnd):
    c = 'Divine'
    coll(c, ROOT)
    z0, z1 = 1830, 2010
    p = Part('Divine_Palace', c)
    # white marble foundation platform with gold trim and cloud skirt
    p.prism(ngon(160, 32, 0, 4, rnd), z0, z0 + 10, 'Divine_Marble')
    p.prism(ngon(162, 32, 0), z0 + 10, z0 + 12, 'Gold')
    p.cone(P(0, 0, z0), 160, -50, 'Divine_Marble', 32, r_top=80)
    # tiered palace: three stacked drums with colonnades
    for k, (rr, h) in enumerate(((120, 50), (88, 44), (58, 38))):
        zb = z0 + 12 + sum(hh for _, hh in ((120, 50), (88, 44), (58, 38))[:k])
        p.prism(ngon(rr, 24, 0), zb, zb + h - 3, 'Divine_Marble')
        p.prism(ngon(rr + 4, 24, 0), zb + h - 3, zb + h, 'Gold')
        for i in range(24):
            deg = (i + 0.5) * 15
            p.prism(round_arch(rr * 0.12, h * 0.4, 6), 0, 0.6, 'Window_Warm',
                    face_M(rr * math.cos(math.pi / 24), deg, zb + 6))
        # ring of golden-roofed towers
        cnt = (10, 8, 6)[k]
        for i in range(cnt):
            deg = i * 360 / cnt + k * 15
            t = P(rr + 2, deg, zb)
            p.cyl(t + Vector((0, 0, (h + 14) / 2)), 8 - k, h + 14, 'Divine_Marble', 10)
            p.cone(t + Vector((0, 0, h + 14)), 9.5 - k, 20 - k * 2, 'Gold', 10)
            p.cone(t + Vector((0, 0, h + 34 - k * 2)), 0.7, 6, 'Gold', 6)
    zt = z0 + 12 + 50 + 44 + 38
    # central golden dome and spire
    p.uvsphere(P(0, 0, zt), 42, 'Gold', 24, 12, (1, 1, 1.05))
    p.cyl(P(0, 0, zt + 46), 7, 12, 'Divine_Marble', 12)
    p.cone(P(0, 0, zt + 52), 7, 60, 'Gold', 12)
    p.uvsphere(P(0, 0, zt + 114), 3.2, 'Divine_Ring', 12, 6)
    # grand gate on the front
    M = face_M(120 * math.cos(math.pi / 24) + 0.5, 270, z0 + 12)
    p.prism(pointed_arch(20, 24, 10), 0, 1.0, 'Window_Blue', M)
    p.finish()
    q = Part('Divine_HaloRings', c)
    q.torus(P(0, 0, z0 + 130), 200, 2.0, 'Divine_Ring', 96, 6, rot=Euler((0.10, 0.05, 0)).to_matrix())
    q.torus(P(0, 0, z0 + 185), 150, 1.5, 'Divine_Ring', 96, 6, rot=Euler((-0.12, 0.1, 0)).to_matrix())
    q.torus(P(0, 0, z0 + 80), 230, 1.2, 'Magic_Glow', 96, 6, rot=Euler((0.05, -0.12, 0)).to_matrix())
    q.finish()
    for k in range(16):
        deg = k * 22.5
        inst(rnd.choice(('Cloud_A', 'Cloud_B', 'Cloud_D')), f'Divine_Cloud_{k}', c, P(rnd.uniform(140, 185), deg,
             z0 - rnd.uniform(5, 30)), math.radians(deg + 90), rnd.uniform(16, 26))
    LEDGES['Divine'] = (z0 + 12, 160)
    for k, deg in enumerate((240, 300)):
        point_light(f'Divine_Light_{k}', P(220, deg, z0 + 90), (1.0, 0.85, 0.55), 250000, 14)


def widen(collection, s):
    """scale a floor's geometry outward about the tower axis (XY only), keeping shared meshes intact"""
    T = Matrix.Translation(TC) @ Matrix.Diagonal((s, s, 1, 1)) @ Matrix.Translation(-TC)
    for o in coll(collection).objects:
        if o.type == 'MESH' and o.data.users == 1:
            o.data.transform(T)
        else:
            o.location = T @ o.location
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name.startswith(collection):
            o.location = T @ o.location
    key, (z, rl) = collection, LEDGES[collection]
    LEDGES[key] = (z, rl * s)


def build_core():
    p = Part('Tower_Core', ROOT)
    p.prism(ngon(110, 16, 0), 195, 1840, 'Kingdom_Stone')
    p.finish()


FLOOR_SPECS = {
    'Jungle': (jungle, dict(n=18, lower=0.5, ledge=18, turrets=4, balconies=2, annexes=6, roof='flat')),
    'Desert': (desert, dict(n=16, lower=0.45, ledge=16, turrets=4, balconies=3, annexes=7, roof='dome')),
    'Ice': (ice, dict(n=14, lower=0.5, ledge=16, turrets=5, balconies=2, upper_k=0.8, annexes=5, roof='spire')),
    'Lava': (lava, dict(n=12, lower=0.55, ledge=18, turrets=3, balconies=1, annexes=6, roof='spike')),
    'Crystal': (crystal, dict(n=10, lower=0.5, ledge=14, turrets=3, balconies=1, upper_k=0.86, annexes=4,
                              roof='spire')),
    'Shadow': (shadow, dict(n=12, lower=0.5, ledge=14, turrets=4, balconies=2, win_rows=(2, 1), annexes=6,
                            roof='spire')),
    'Forest': (forest, dict(n=14, lower=0.4, ledge=16, turrets=0, balconies=1, upper_k=0.82, annexes=3,
                            roof='dome')),
    'Kingdom': (kingdom, dict(n=16, lower=0.5, ledge=16, turrets=4, balconies=2, annexes=6, roof='cone')),
    'Cloud': (cloud, dict(n=16, lower=0.45, ledge=16, turrets=4, balconies=1, upper_k=0.82, annexes=5,
                          roof='dome')),
}


def build_tower():
    coll(ROOT, 'TOWER_OF_PETS')
    coll(WF, 'TOWER_OF_PETS')
    build_foundation()
    build_core()
    for i, (key, z0, z1, r) in enumerate(FLOORS):
        rnd = random.Random(1000 + i)
        if key == 'Celestial':
            celestial(rnd); widen('Celestial', 1.3); continue
        if key == 'Divine':
            divine(rnd); widen('Divine', 1.4); continue
        coll(key, ROOT)
        fn, kw = FLOOR_SPECS[key]
        s = tier_shell(key, z0, z1, r, rnd, **kw)
        fn(s, rnd)
