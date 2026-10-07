"""TOWER_ENTRANCE: shared entrance constants, the portal lights, and the castle-base build (castle.py:
grand stairs, landing, masonry gatehouse with the stepped pointed arch, blue portal with the white paw,
navy paw banners, pillars, statues, lanterns, pediment crest, upper gate, and the invisible teleport trigger).

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


def build_portal_lights():
    lc = 'LIGHTING'
    L = bpy.data.lights.new('Portal_Glow_Blue', 'AREA')
    L.shape = 'RECTANGLE'; L.size, L.size_y = 24, 50
    L.color = (0.35, 0.6, 1.0); L.energy = 60000
    o = bpy.data.objects.new('Portal_Glow_Blue', L)
    o.location = (0, FACADE_Y + 3.0, Z_LAND + 26)
    o.rotation_euler = (math.radians(-90), 0, 0)             # emits toward -Y (onto the landing)
    o.visible_camera = False
    coll(lc).objects.link(o)
    L = bpy.data.lights.new('Portal_Glow_Purple', 'POINT')
    L.color = (0.65, 0.3, 1.0); L.energy = 40000; L.shadow_soft_size = 6
    o = bpy.data.objects.new('Portal_Glow_Purple', L)
    o.location = (0, FACADE_Y - 14, Z_LAND + 10)
    coll(lc).objects.link(o)
    for s in (-1, 1):                                           # warm lantern fill
        for i, (x, y, z) in enumerate(((s * 27.0, FACADE_Y - 16, Z_LAND + 12), (s * 24.6, STAIR_Y0 - 3, 14))):
            L = bpy.data.lights.new(f'Lantern_Warm_{s}_{i}', 'POINT')
            L.color = (1.0, 0.65, 0.3); L.energy = 3000; L.shadow_soft_size = 1.5
            o = bpy.data.objects.new(L.name, L); o.location = (x, y, z)
            coll(lc).objects.link(o)


def build_entrance():
    import castle
    coll(C, 'TOWER_OF_PETS')
    castle.build_castle_base()
    build_portal_lights()
