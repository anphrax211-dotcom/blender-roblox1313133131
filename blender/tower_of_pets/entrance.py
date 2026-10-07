"""TOWER_ENTRANCE: grand stairs, landing, monumental gatehouse with the stepped pointed arch,
blue/purple portal with the white paw, navy paw banners, pillars, lanterns, greenery and
an invisible teleport trigger volume for Roblox.

World placement: centred on x = 0, stairs start at y = STAIR_Y0 on the plaza (z = 0) and rise
to the landing at z = Z_LAND; the facade's front plane is y = FACADE_Y.
"""
import math, random
from mathutils import Vector, Matrix
import bpy
from common import Part, coll, inst, paw, M_front, pointed_arch, text_mesh, TAU
from foliage import tree_in_planter, vine

C = 'TOWER_ENTRANCE'
STAIR_Y0, RUN, RISE, N_STEPS = 100.0, 1.5, 1.0, 20
Z_LAND = N_STEPS * RISE                         # 20
STAIR_Y1 = STAIR_Y0 + N_STEPS * RUN             # 130
FACADE_Y = 152.0
STAIR_W = 44.0

# arch outlines (x, z) measured from the landing; the portal opening is 26 wide, 58 tall
OPEN_W, OPEN_HS, OPEN_HT = 26.0, 40.0, 18.0


def arch(w, extra=0.0):
    """pointed arch outline scaled from the opening (extra widens all layers uniformly)"""
    k = (w / OPEN_W)
    return pointed_arch(w, OPEN_HS + extra * 0.3, OPEN_HT * k, chamfer=1.2 * k, n_side=1)


def lift(pts, dz):
    return [(x, z + dz) for x, z in pts]


def build_stairs():
    p = Part('Entrance_Stairs', C, 0.08)
    for i in range(N_STEPS):
        y0 = STAIR_Y0 + i * RUN
        z1 = (i + 1) * RISE
        p.box((0, (y0 + STAIR_Y1 + 2) / 2, z1 / 2), (STAIR_W, STAIR_Y1 + 2 - y0, z1), 'Hub_Stone')
        p.box((0, y0 + 0.25, z1 - 0.12), (STAIR_W, 0.5, 0.26), 'Stone_Trim')        # nosing
    # glowing centre runner (blue inlay) up the stairs
    for i in range(N_STEPS):
        y0 = STAIR_Y0 + i * RUN
        p.box((0, y0 + RUN / 2, (i + 1) * RISE + 0.03), (5.0, RUN - 0.3, 0.06), 'Blue_Inlay')
    # cheek walls / balustrades following the slope
    for s in (-1, 1):
        x = s * (STAIR_W / 2 + 2.5)
        a = (x - 2.5, STAIR_Y0 - 2, 0)
        pts = [(x - 2.5, STAIR_Y0 - 4, 0), (x + 2.5, STAIR_Y0 - 4, 0), (x + 2.5, STAIR_Y1 + 2, 0),
               (x - 2.5, STAIR_Y1 + 2, 0),
               (x - 2.5, STAIR_Y0 - 4, 4.5), (x + 2.5, STAIR_Y0 - 4, 4.5),
               (x + 2.5, STAIR_Y1 + 2, Z_LAND + 4.5), (x - 2.5, STAIR_Y1 + 2, Z_LAND + 4.5)]
        p.hexa(pts, 'Hub_Stone_Warm')
        cap = [(x - 3.0, STAIR_Y0 - 4.5, 4.5), (x + 3.0, STAIR_Y0 - 4.5, 4.5),
               (x + 3.0, STAIR_Y1 + 2.5, Z_LAND + 4.5), (x - 3.0, STAIR_Y1 + 2.5, Z_LAND + 4.5)]
        p.hexa(cap + [(u, v, w + 0.7) for u, v, w in cap], 'Stone_Trim')
        # newel blocks at the foot and the top
        p.box((x, STAIR_Y0 - 4, 3.5), (6.5, 6.5, 7.0), 'Hub_Stone')
        p.box((x, STAIR_Y0 - 4, 7.2), (7.2, 7.2, 0.6), 'Stone_Trim')
        p.box((x, STAIR_Y1 + 2, Z_LAND + 3.5), (6.5, 6.5, 7.0), 'Hub_Stone')
        p.box((x, STAIR_Y1 + 2, Z_LAND + 7.2), (7.2, 7.2, 0.6), 'Stone_Trim')
        # terraced planters stepping up beside the stairs
        for k in range(4):
            yy = STAIR_Y0 + 3 + k * 7.5
            zz = (yy - STAIR_Y0) / RUN * RISE
            p.box((s * (STAIR_W / 2 + 10), yy, (zz + 3) / 2), (10, 7.5, zz + 3), 'Hub_Stone')
            p.box((s * (STAIR_W / 2 + 10), yy, zz + 3.1), (9, 6.5, 0.4), 'Grass')
    p.finish()
    rnd = random.Random(31)
    for s in (-1, 1):
        x = s * (STAIR_W / 2 + 2.5)
        inst('Lantern_Post', f'Entrance_Lantern_Foot_{s}', C, (x, STAIR_Y0 - 4, 7.5), 0, 1.4)
        inst('Lantern_Post', f'Entrance_Lantern_Top_{s}', C, (x, STAIR_Y1 + 2, Z_LAND + 7.5), 0, 1.4)
        for k in range(4):
            yy = STAIR_Y0 + 3 + k * 7.5
            zz = (yy - STAIR_Y0) / RUN * RISE + 3.3
            inst(('Bush_01', 'Ground_Plant_01', 'Bush_02', 'Bush_03')[k], f'Entrance_StairBush_{s}_{k}', C,
                 (s * (STAIR_W / 2 + 10), yy, zz), rnd.uniform(0, TAU), 1.2)
        inst('Stone_Planter', f'Entrance_FootPlanter_{s}', C, (s * (STAIR_W / 2 + 13), STAIR_Y0 - 9, 0), 0, 1.2)


def build_landing():
    p = Part('Entrance_Landing', C, 0.1)
    yb = FACADE_Y + 4
    p.box((0, (STAIR_Y1 + yb) / 2, Z_LAND / 2), (100, yb - STAIR_Y1, Z_LAND), 'Hub_Stone')
    p.box((0, (STAIR_Y1 + yb) / 2, Z_LAND + 0.1), (99, yb - STAIR_Y1 - 1, 0.2), 'Plaza_Tile')
    p.box((0, STAIR_Y1 + 0.4, Z_LAND + 0.25), (99, 0.8, 0.5), 'Stone_Trim')
    # front wall of the landing either side of the stairs (with blind arches)
    for s in (-1, 1):
        x0, x1 = STAIR_W / 2 + 5, 50
        p.box((s * (x0 + x1) / 2, STAIR_Y1 - 0.5, Z_LAND / 2), (x1 - x0, 1.0, Z_LAND), 'Hub_Stone_Warm')
        for k in range(3):
            cx = s * (x0 + 5 + k * 8)
            ar = [(cx + x, z + 3) for x, z in pointed_arch(4.5, 8, 3)]
            p.prism_xz(ar, STAIR_Y1 - 1.3, STAIR_Y1 - 0.9, 'Stone_Dark')
    # glowing paw floor seal in front of the portal
    p.cyl((0, FACADE_Y - 10, Z_LAND + 0.2), 9.0, 0.2, 'Hub_Stone_Warm', 40)
    p.torus((0, FACADE_Y - 10, Z_LAND + 0.3), 8.6, 0.25, 'Gold', 40, 4)
    paw(p, Matrix.Translation((0, FACADE_Y - 9.6, Z_LAND + 0.3)), 11, 0.08, 'Magic_Glow')
    p.finish()


def build_gatehouse():
    z0 = Z_LAND
    yf, yb = FACADE_Y, FACADE_Y + 40
    p = Part('Entrance_Gatehouse', C, 0.12)
    # facade mass with the arch opening ----------------------------------------------------------
    hw = 17.0                                     # half width of the central bay behind the frames
    top = z0 + 92
    p.box((-(hw + 50) / 2 - 0, (yf + yb) / 2, (z0 + top) / 2), (50 - hw, yb - yf, top - z0), 'Hub_Stone')
    p.box(((hw + 50) / 2, (yf + yb) / 2, (z0 + top) / 2), (50 - hw, yb - yf, top - z0), 'Hub_Stone')
    op = lift(arch(OPEN_W), z0)
    apex = op[len(op) // 2]
    for s in (-1, 1):                              # spandrels around the opening
        half = op[:len(op) // 2 + 1] if s < 0 else op[len(op) // 2:][::-1]
        poly = [(s * hw, z0)] + half + [(0, top), (s * hw, top)]
        if s > 0:
            poly = poly[::-1]
        p.prism_xz(poly, yf, yb, 'Hub_Stone')
    p.box((0, yb - 1, z0 + 30), (OPEN_W, 2, 60), 'Stone_Dark')      # back of the passage
    # stepped arch frames (outer -> inner), each set further back -------------------------------
    layers = ((50, 42, yf - 6.0, yf, 'Hub_Stone_Warm'),
              (42, 40.4, yf - 6.6, yf - 5.6, 'Gold'),
              (40.4, 34, yf - 3.5, yf, 'Hub_Stone'),
              (34, 32.6, yf - 4.0, yf - 3.0, 'Gold'),
              (32.6, 28.4, yf - 1.5, yf, 'Hub_Stone_Warm'),
              (28.4, OPEN_W, yf - 0.6, yf + 2.0, 'Magic_Glow'))
    for w_out, w_in, y0, y1, m in layers:
        p.strip_xz(lift(arch(w_out), z0), lift(arch(w_in), z0), y0, y1, m)
    # gable crown above the outer frame with a paw medallion -------------------------------------
    ga = arch(50)
    gz = z0 + ga[len(ga) // 2][1]
    p.prism_xz([(-30, gz - 14), (30, gz - 14), (0, gz + 12)], yf - 4, yf + 1, 'Hub_Stone_Warm')
    p.strip_xz([(-31.5, gz - 14), (0, gz + 13.2), (31.5, gz - 14)],
               [(-29.0, gz - 14), (0, gz + 11.0), (29.0, gz - 14)], yf - 4.8, yf - 3.6, 'Gold')
    p.cyl((0, yf - 4.6, gz - 1), 4.6, 1.2, 'Banner_Navy', 24, axis='Y')
    p.torus((0, yf - 5.3, gz - 1), 4.6, 0.4, 'Gold', 24, 6, rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
    paw(p, M_front(0, yf - 5.2, gz - 0.8), 5.6, 0.5, 'Gold_Glow')
    p.cone((0, yf - 1.5, gz + 12), 1.4, 6, 'Gold', 6)
    # cornice & crenellations along the top of the gatehouse --------------------------------------
    p.box((0, yf + 1, top + 1.0), (102, yb - yf + 4, 2.0), 'Stone_Trim')
    for k in range(-12, 13):
        if abs(k) <= 3:
            continue
        p.box((k * 4.0, yf - 0.5, top + 3.5), (2.4, 2.4, 3.0), 'Hub_Stone')
    # blind arched windows on the wings, glowing warm --------------------------------------------
    for s in (-1, 1):
        for row, zz in enumerate((z0 + 42, z0 + 66)):
            for k in range(2):
                cx = s * (40 + k * 8)
                ar = [(cx + x, zz + z) for x, z in pointed_arch(4.0, 7.0, 3.0)]
                p.prism_xz(ar, yf - 0.4, yf + 0.5, 'Window_Warm')
                p.strip_xz([(cx + x, zz + z) for x, z in pointed_arch(5.6, 7.0, 4.0)],
                           ar, yf - 0.9, yf + 0.5, 'Stone_Trim')
    p.finish()

    # the portal surface (own object so its gradient fills the arch) ----------------------------
    pt = Part('Entrance_Portal', C)
    pt.prism_xz(lift(arch(OPEN_W), z0), yf + 1.0, yf + 1.6, 'Portal_Energy')
    pt.finish()
    pe = Part('Entrance_Portal_Paw', C)
    paw(pe, M_front(0, yf + 0.9, z0 + 25.0), 15.0, 0.6, 'Paw_White_Glow')
    # purple energy rim and wisps inside the arch
    rim_o = lift(arch(OPEN_W), z0); rim_i = lift(arch(OPEN_W - 1.6), z0)
    pe.strip_xz(rim_o, rim_i, yf + 0.6, yf + 1.0, 'Magic_Purple')
    pe.finish()
    rnd = random.Random(41)
    sp = Part('Entrance_Portal_Particles', C)
    for k in range(70):
        x = rnd.uniform(-22, 22); y = rnd.uniform(yf - 24, yf - 0.5); z = rnd.uniform(z0 + 1, z0 + 50)
        sp.ico((x, y, z), rnd.uniform(0.12, 0.32), rnd.choice(('Magic_Glow', 'Magic_Purple', 'Paw_White_Glow')), 1)
    sp.finish()
    # invisible teleport trigger for Roblox (Touched -> TeleportService)
    tr = Part('Portal_TeleportTrigger', C)
    tr.box((0, yf + 3, z0 + 22), (OPEN_W - 2, 4, 44), 'Magic_Glow')
    t = tr.finish()
    t.display_type = 'WIRE'
    t.hide_render = True

    # pillars with banners -------------------------------------------------------------------------
    p = Part('Entrance_Pillars', C, 0.12)
    for s in (-1, 1):
        x = s * 33.0
        yp = yf - 9
        p.box((x, yp, z0 + 2.0), (12, 12, 4), 'Stone_Trim')
        p.box((x, yp, z0 + 50), (9.5, 9.5, 96), 'Hub_Stone_Warm')
        for zz in (z0 + 30, z0 + 72):
            p.box((x, yp, zz), (10.6, 10.6, 1.2), 'Stone_Trim')
        p.box((x, yp, z0 + 99), (11.5, 11.5, 2.4), 'Stone_Trim')
        p.box((x, yp, z0 + 103), (8, 8, 6), 'Hub_Stone')
        p.cone((x, yp, z0 + 106), 5.6, 12, 'Roof_Blue', 4)
        p.cone((x, yp, z0 + 117.5), 0.6, 4, 'Gold', 6)
        for sx in (-1, 1):                           # corner pinnacles
            for sy in (-1, 1):
                p.cone((x + sx * 4.6, yp + sy * 4.6, z0 + 100.2), 1.0, 5, 'Hub_Stone', 4)
        # gold banner rod on brackets
        p.box((x, yp - 5.4, z0 + 86), (10, 1.0, 0.8), 'Gold')
        for sx in (-1, 1):
            p.cyl((x + sx * 5.2, yp - 5.4, z0 + 86), 0.7, 1.2, 'Gold', 8, axis='X')
    p.finish()
    b = Part('Entrance_Banners', C, 0.05)
    for s in (-1, 1):
        x = s * 33.0
        yb_ = yf - 9 - 5.6
        top_z, bw, bl = z0 + 85.5, 9.0, 46.0
        outline = [(-bw / 2, 0), (bw / 2, 0), (bw / 2, -bl), (0, -bl - 5.5), (-bw / 2, -bl)]
        M = M_front(x, yb_, top_z)
        b.prism(outline, 0, 0.35, 'Banner_Navy', M)
        trim_o = [(-bw / 2, 0), (-bw / 2, -bl), (0, -bl - 5.5), (bw / 2, -bl), (bw / 2, 0)]
        trim_i = [(-bw / 2 + 0.8, 0), (-bw / 2 + 0.8, -bl + 0.3), (0, -bl - 4.4), (bw / 2 - 0.8, -bl + 0.3),
                  (bw / 2 - 0.8, 0)]
        for o, i_ in zip(zip(trim_o, trim_o[1:]), zip(trim_i, trim_i[1:])):
            (a0, a1), (b0, b1) = o, i_
            q = [M @ Vector((*a0, 0.35)), M @ Vector((*a1, 0.35)), M @ Vector((*b1, 0.35)), M @ Vector((*b0, 0.35))]
            b.hexa(q + [v + Vector((0, -0.25, 0)) for v in q], 'Gold')
        b.box(M @ Vector((0, -1.5, 0.45)), (bw, 0.3, 1.0), 'Gold')
        paw(b, M_front(x, yb_ - 0.4, top_z - bl + 10.0), 6.5, 0.3, 'Gold_Glow')
        # small paw crest near the top
        b.box(M @ Vector((0, -7.0, 0.45)), (bw - 2.4, 0.3, 0.5), 'Gold')
    b.finish()

    # wall lanterns on the facade + lanterns on the landing -------------------------------------
    for s in (-1, 1):
        inst('Lantern_Post', f'Entrance_Lantern_Landing_{s}', C, (s * 21.0, yf - 13, z0), 0, 1.25)
        inst('Lantern_Post', f'Entrance_Lantern_Outer_{s}', C, (s * 46.0, yf - 13, z0), 0, 1.25)
        inst('Bush_02', f'Entrance_Bush_{s}', C, (s * 42.0, yf - 6, z0), 0, 1.3)
        inst('Ground_Plant_01', f'Entrance_Flowers_{s}', C, (s * 26.0, yf - 4, z0), 0, 1.0)
        inst('Tree_Small', f'Entrance_Tree_{s}', C, (s * 47.0, yf - 4, z0), 0.5 * s, 1.0)
        tree_in_planter(f'Entrance_LobbyTree_{s}', C, (s * 64.0, STAIR_Y0 + 14, 0), 0.0, 'Tree_Large_High', seed=400 + s)

    # hanging vines over the gatehouse cornice ----------------------------------------------------
    v = Part('Entrance_Vines', C)
    rnd = random.Random(43)
    for k in range(26):
        x = rnd.uniform(-50, 50)
        if abs(x) < 30:
            continue
        L = rnd.uniform(8, 26)
        zt = z0 + 92
        vine(v, (x, yf - 0.8, zt), L, rnd, 1.6)
    v.finish()


def build_portal_lights():
    lc = 'LIGHTING'
    L = bpy.data.lights.new('Portal_Glow_Blue', 'AREA')
    L.shape = 'RECTANGLE'; L.size, L.size_y = 24, 50
    L.color = (0.35, 0.6, 1.0); L.energy = 450000
    o = bpy.data.objects.new('Portal_Glow_Blue', L)
    o.location = (0, FACADE_Y - 3.0, Z_LAND + 26)
    o.rotation_euler = (math.radians(-90), 0, 0)             # emits toward -Y (onto the landing)
    o.visible_camera = False
    coll(lc).objects.link(o)
    L = bpy.data.lights.new('Portal_Glow_Purple', 'POINT')
    L.color = (0.65, 0.3, 1.0); L.energy = 250000; L.shadow_soft_size = 6
    o = bpy.data.objects.new('Portal_Glow_Purple', L)
    o.location = (0, FACADE_Y - 16, Z_LAND + 8)
    coll(lc).objects.link(o)
    for s in (-1, 1):                                           # warm lantern fill
        for i, (x, y, z) in enumerate(((s * 21.0, FACADE_Y - 13, Z_LAND + 14), (s * 24.5, STAIR_Y0 - 4, 21))):
            L = bpy.data.lights.new(f'Lantern_Warm_{s}_{i}', 'POINT')
            L.color = (1.0, 0.65, 0.3); L.energy = 9000; L.shadow_soft_size = 1.5
            o = bpy.data.objects.new(L.name, L); o.location = (x, y, z)
            coll(lc).objects.link(o)


def build_entrance():
    coll(C, 'TOWER_OF_PETS')
    build_stairs()
    build_landing()
    build_gatehouse()
    build_portal_lights()
