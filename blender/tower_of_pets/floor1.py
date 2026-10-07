"""TOWER OF PETS - FLOOR 1: THE VERDANT KINGDOM - greybox base layout (terrain only).

Built from the Floor 1 map sheet as a spatial blueprint: the map image (1536 x 1024 px) is mapped onto a
~1,500 x 1,500 stud play area (image x -> world X, image up/north -> world +Y; px() converts). Every area of the
sheet is a noisy landmass at its own height; the max of all areas makes one heightfield with real cliffs between
levels and void (clouds) between islands. Ride-able ramps, natural bridges, rivers, waterfalls, lakes, flat
landmark pads and simple blockout markers are layered on top.

Five biomes (TERRAIN/<BIOME>, one Top / Cliffs / Underside mesh per area so each island can be refined later):
  VERDANT_FOREST    Floor_Entrance, Sunlit_Meadows, Verdant_Village, Whispering_Forest, Guardian_Grove, Mistfall secret
  WATERFALL_VALLEY  Riverfall_Valley, Emerald_Lake, Lotus_Swamp, Lotus Grotto secret
  ANCIENT_RUINS     Ancient_Ruins (plateau), Cloudridge_Peaks, Cloud Perch secret
  MYSTIC_WILDS      World_Tree_Grove, Mossy_Caverns, Beast_Cave
  JUNGLE_FORTRESS   Jungle_Fortress (biggest/highest plateau), Sky_Guardian_Ledge, Sky_Temple, Overlook secret
Paths are part of the terrain (dirt material); where they cross the void they become natural rock bridges
(TERRAIN/NATURAL_BRIDGES). Main paths 26-32 studs wide, secondary 22-24, secret 12; slopes kept under ~25 deg.

No buildings, trees, decorations or detailed assets - only terrain, water and landmark blockouts.
"""
import math, random, json
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from common import Part, MATS, mat_plain, mat_noise, coll, text_mesh, round_arch, TAU
from castle import frame_strip

ROOT = 'TOWER_OF_PETS_FLOOR_1'
S = 6.0                                   # grid spacing (studs)
EXT = 820.0                               # grid half extent
BIOMES = ('VERDANT_FOREST', 'WATERFALL_VALLEY', 'ANCIENT_RUINS', 'MYSTIC_WILDS', 'JUNGLE_FORTRESS')
VF, WV, AR, MW, JF = BIOMES
CLOUD_Z = -360.0
ZS = 1.3                                  # vertical exaggeration applied to every height below


def px(x, y):
    """map-sheet pixel -> world studs"""
    return (x - 768.0) * 0.977, (512.0 - y) * 1.465


# ---------------------------------------------------------------- layout data (map-sheet pixels) --------------
# name, biome, cx, cy, rx, ry (px), top z, noise amp, boundary irregularity, seed, dark rock, level range
AREAS = (
    ('Floor_Entrance', VF, 205, 885, 92, 66, 6, 0.0, 0.05, 1, False, 'Spawn'),
    ('Sunlit_Meadows', VF, 245, 680, 175, 112, 12, 3.5, 0.12, 2, False, 'Lv 1-10'),
    ('Verdant_Village', VF, 525, 765, 140, 82, 12, 1.2, 0.10, 3, False, 'Lv 1-20'),
    ('Whispering_Forest', VF, 295, 415, 165, 158, 40, 6.0, 0.15, 4, False, 'Lv 1-15'),
    ('Guardian_Grove', VF, 470, 440, 45, 38, 42, 0.8, 0.10, 5, False, 'Mini-Boss 1'),
    ('Secret_Mistfall_Isle', VF, 75, 330, 40, 35, 30, 1.5, 0.15, 6, False, 'Secret'),
    ('Riverfall_Valley', WV, 600, 595, 150, 100, 30, 2.5, 0.12, 7, False, 'Lv 10-25'),
    ('Emerald_Lake', WV, 950, 360, 160, 108, 58, 2.5, 0.10, 8, False, 'Lv 15-30'),
    ('Lotus_Swamp', WV, 880, 880, 178, 105, -4, 1.0, 0.14, 9, False, 'Lv 20-35'),
    ('Secret_Lotus_Grotto', WV, 1085, 990, 45, 30, -20, 1.0, 0.12, 10, False, 'Secret'),
    ('Ancient_Ruins', AR, 650, 390, 138, 92, 75, 1.5, 0.10, 11, False, 'Lv 20-35'),
    ('Cloudridge_Peaks', AR, 495, 170, 165, 95, 98, 6.0, 0.14, 12, False, 'Lv 35-50'),
    ('Secret_Cloud_Perch', AR, 290, 55, 40, 30, 150, 1.5, 0.12, 13, False, 'Secret'),
    ('World_Tree_Grove', MW, 775, 140, 122, 100, 120, 5.0, 0.12, 14, False, 'Lv 45-60'),
    ('Mossy_Caverns', MW, 895, 600, 118, 98, 64, 6.0, 0.14, 15, False, 'Lv 25-40'),
    ('Beast_Cave', MW, 1185, 330, 112, 118, 100, 9.0, 0.16, 16, True, 'Lv 30-45'),
    ('Jungle_Fortress', JF, 1205, 570, 160, 125, 150, 4.0, 0.12, 17, True, 'Lv 55-70'),
    ('Sky_Guardian_Ledge', JF, 1300, 215, 34, 28, 140, 0.0, 0.10, 18, True, 'Mini-Boss 3'),
    ('Sky_Temple', JF, 1235, 92, 105, 58, 200, 1.5, 0.10, 19, False, 'Lv 50-70'),
    ('Secret_Overlook', JF, 1440, 470, 40, 45, 120, 1.5, 0.12, 20, True, 'Secret'),
)
# peaks / hills / crags / spires added on top of an area: cx, cy (px), radius (studs), height, profile exponent
FEATURES = (
    (430, 130, 75, 115, 1.3), (525, 92, 95, 150, 1.2), (615, 155, 65, 85, 1.4), (385, 205, 50, 55, 1.5),
    (650, 95, 55, 60, 1.4),                                                     # Cloudridge Peaks
    (880, 615, 62, 34, 0.6),                                                    # Mossy Caverns cavern hill
    (1150, 255, 34, 55, 1.0), (1245, 395, 30, 48, 1.0), (1110, 395, 24, 34, 1.0), (1270, 300, 26, 40, 1.0),
    (1180, 420, 20, 30, 1.0),                                                   # Beast Cave crags
    (1060, 500, 22, 38, 0.5), (1350, 520, 26, 42, 0.5), (1330, 650, 24, 40, 0.5), (1090, 670, 20, 34, 0.5),
    (1210, 680, 22, 36, 0.5),                                                   # Jungle Fortress rim spires
    (700, 70, 30, 30, 1.0), (840, 75, 26, 24, 1.0),                             # World Tree grove knolls
)
# lakes / ponds: cx, cy, rx, ry (px), water z, depth, seed
LAKES = (
    ('Emerald_Lake_Water', 945, 360, 105, 68, 52.0, 12.0, 31),
    ('Riverfall_Pool', 565, 605, 28, 20, 28.4, 4.0, 32),
    ('Lotus_Pond_1', 820, 900, 45, 28, -4.6, 2.5, 33),
    ('Lotus_Pond_2', 930, 930, 38, 22, -4.6, 2.5, 34),
    ('Lotus_Pond_3', 990, 860, 30, 20, -4.6, 2.5, 35),
    ('Lotus_Pond_4', 760, 940, 28, 18, -4.6, 2.5, 36),
    ('Lotus_Pond_5', 890, 830, 26, 16, -4.6, 2.5, 37),
    ('World_Tree_Spring', 720, 175, 22, 15, 118.6, 3.0, 38),
)
# rivers: [(px, py, water z)], width studs
RIVERS = (
    ('Whispering_Stream', [(250, 300, 39.5), (300, 380, 39.5), (330, 470, 38.5), (332, 548, 38.5)], 14),
    ('Meadow_Brook', [(335, 600, 10.5), (370, 640, 10.5), (412, 650, 10.5)], 12),
    ('Meadow_West_Brook', [(170, 700, 10.5), (85, 715, 10.5)], 10),
    ('Riverfall_River', [(640, 498, 28.4), (618, 560, 28.4), (565, 605, 28.4), (618, 652, 28.0), (652, 690, 28.0)], 16),
    ('Village_Stream', [(660, 705, 10.5), (668, 745, 10.5)], 12),
    ('Lake_Outflow', [(905, 425, 52.0), (912, 470, 52.0)], 16),
    ('Beast_Stream', [(1160, 300, 98.0), (1100, 302, 98.0)], 10),
    ('Fortress_Fall_West', [(1150, 640, 148.5), (1142, 700, 148.5)], 12),
    ('Fortress_Fall_East', [(1262, 650, 148.5), (1272, 700, 148.5)], 12),
)
# extra waterfalls (no river): start px, direction (deg, world), water z, width
SPRINGS = (
    ('Ruins_Spring_Falls', (648, 455), -95, 74.0, 14),
    ('Sky_Temple_Falls', (1250, 130), -80, 199.0, 12),
    ('Cloudridge_Falls', (430, 245), -100, 97.0, 12),
)
# flattened pads: name, px, py, radius studs, z (None = keep terrain at the centre)
PADS = (
    ('Spawn', 205, 885, 48, 6), ('Village_Square', 525, 765, 70, 12), ('Ruins_Plaza', 650, 390, 62, 75),
    ('World_Tree_Pad', 775, 140, 48, 120), ('Sky_Temple_Pad', 1235, 92, 62, 200),
    ('Fortress_Arena', 1195, 520, 78, 150), ('MiniBoss_1', 470, 440, 34, 42), ('MiniBoss_2', 960, 690, 34, 64),
    ('MiniBoss_3', 1300, 215, 30, 140), ('Lake_Islet', 950, 360, 16, 58),
    ('CP_1', 400, 676, 14, 12), ('CP_2', 520, 560, 14, 30), ('CP_3', 830, 370, 14, 58), ('CP_4', 1160, 370, 14, 100),
    ('CP_5', 1235, 270, 14, 102), ('CP_6', 905, 640, 14, 64),
)
# path network: name, width studs, [(px, py, z)]
PATHS = (
    ('Entrance_Causeway', 32, [(205, 885, 6), (225, 830, 6), (235, 780, 12), (245, 690, 12)]),
    ('Meadow_Road', 30, [(245, 690, 12), (330, 720, 12), (420, 760, 12), (525, 765, 12)]),
    ('Riverfall_Bridge', 30, [(330, 720, 12), (400, 676, 12), (470, 640, 30), (540, 610, 30), (600, 595, 30)]),
    ('Village_Ramp', 26, [(525, 765, 12), (580, 690, 30), (600, 595, 30)]),
    ('Forest_Ramp', 28, [(245, 690, 12), (200, 610, 12), (225, 540, 40), (295, 415, 42)]),
    ('Guardian_Trail', 26, [(295, 415, 42), (400, 430, 42), (470, 440, 42)]),
    ('Guardian_Bridge', 24, [(470, 440, 42), (520, 470, 58), (565, 440, 75), (650, 390, 75)]),
    ('Ruins_Switchback', 26, [(600, 595, 30), (520, 560, 30), (560, 520, 50), (610, 470, 75), (650, 390, 75)]),
    ('Cloudridge_Pass', 26, [(650, 390, 75), (560, 322, 75), (470, 250, 98), (520, 160, 108), (610, 140, 108),
                             (700, 160, 120), (775, 140, 120)]),
    ('Forest_Highroad', 22, [(295, 415, 42), (290, 300, 45), (360, 300, 62), (390, 230, 98), (470, 250, 98)]),
    ('World_Tree_Climb', 26, [(650, 390, 75), (690, 320, 75), (750, 230, 118), (775, 140, 120)]),
    ('Lake_Road', 28, [(650, 390, 75), (760, 380, 75), (830, 370, 58), (900, 460, 58)]),
    ('Lake_Loop', 24, [(830, 370, 58), (900, 460, 58), (1000, 455, 58), (1075, 400, 58), (1050, 290, 58),
                       (940, 265, 58), (850, 290, 58), (830, 370, 58)]),
    ('World_Tree_Descent', 22, [(775, 140, 120), (870, 180, 115), (930, 215, 85), (960, 265, 58)]),
    ('Beast_Switchback', 24, [(1075, 400, 58), (1120, 430, 78), (1160, 370, 100), (1185, 330, 100)]),
    ('Mossy_North_Bridge', 26, [(900, 460, 58), (920, 520, 62), (895, 600, 64)]),
    ('Mossy_West_Bridge', 26, [(600, 595, 30), (720, 600, 30), (800, 600, 62), (895, 600, 64)]),
    ('Swamp_Bridge', 26, [(525, 765, 12), (640, 800, 12), (720, 840, -2), (880, 880, -3)]),
    ('Swamp_Ascent', 24, [(880, 880, -3), (980, 800, -3), (1010, 730, 30), (960, 690, 64), (895, 600, 64)]),
    ('Fortress_Canyon', 26, [(895, 600, 64), (990, 590, 64), (1060, 620, 95), (1100, 560, 125), (1150, 600, 150),
                             (1205, 570, 150)]),
    ('Fortress_North_Gate', 26, [(1185, 330, 100), (1200, 430, 100), (1250, 470, 125), (1220, 520, 150),
                                 (1205, 570, 150)]),
    ('Sky_Stair', 22, [(1185, 330, 100), (1235, 270, 102), (1300, 215, 140), (1330, 160, 170), (1300, 120, 200),
                       (1235, 92, 200)]),
    ('West_Cliff_Trail', 22, [(245, 690, 12), (130, 700, 12), (130, 610, 12), (150, 520, 40), (200, 440, 42),
                              (295, 415, 42)]),
    ('Secret_Mistfall_Path', 12, [(170, 380, 42), (115, 340, 36), (75, 330, 30)]),
    ('Secret_Overlook_Path', 12, [(1350, 560, 150), (1400, 500, 130), (1440, 470, 120)]),
)
# ---- apply the vertical exaggeration once (paths stay ride-able: steepest ramps ~27 deg) ----
AREAS = tuple(a[:6] + (a[6] * ZS,) + a[7:] for a in AREAS)
FEATURES = tuple(f[:3] + (f[3] * ZS,) + f[4:] for f in FEATURES)
LAKES = tuple(l[:5] + (l[5] * ZS, l[6]) + l[7:] for l in LAKES)
RIVERS = tuple((n, [(x, y, z * ZS) for x, y, z in pts], w) for n, pts, w in RIVERS)
SPRINGS = tuple((n, p, a, z * ZS, w) for n, p, a, z, w in SPRINGS)
PADS = tuple((n, x, y, r, z * ZS) for n, x, y, r, z in PADS)


def chaikin(pts, it=2):
    """round the corners of a path (end points kept); heights are re-spread along the new length so the
    climb stays as even as the original ramp"""
    def cum(p):
        c = [0.0]
        for a, b in zip(p, p[1:]):
            c.append(c[-1] + math.hypot(b[0] - a[0], (b[1] - a[1]) * 1.5))
        return [x / (c[-1] or 1) for x in c]
    f0, z0 = cum(pts), [p[2] for p in pts]
    xy = [p[:2] for p in pts]
    for _ in range(it):
        out = [xy[0]]
        for a, b in zip(xy, xy[1:]):
            out += [(a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25), (a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75)]
        out.append(xy[-1])
        xy = out
    return [(x, y, float(np.interp(g, f0, z0))) for (x, y), g in zip(xy, cum(xy))]


PATHS = tuple((n, w, chaikin([(x, y, z * ZS) for x, y, z in pts])) for n, w, pts in PATHS)
CHECKPOINTS = (('Checkpoint_1_Meadows', 400, 676), ('Checkpoint_2_Riverfall', 520, 560),
               ('Checkpoint_3_Lake', 830, 370), ('Checkpoint_4_Beast', 1160, 370),
               ('Checkpoint_5_Sky_Stair', 1235, 270), ('Checkpoint_6_Mossy', 905, 640))
MINIBOSSES = (('MiniBoss_1_Forest_Guardian', 470, 440), ('MiniBoss_2_Ancient_Beast', 960, 690),
              ('MiniBoss_3_Sky_Guardian', 1300, 215))
EGGS = (('World_Egg_1_Whispering', 200, 330), ('World_Egg_2_Riverfall', 680, 560), ('World_Egg_3_Cloudridge', 430, 215),
        ('World_Egg_4_Lake_Islet', 950, 360), ('World_Egg_5_Beast', 1230, 400), ('World_Egg_6_Lotus', 960, 960))
# caves: name, start px (inside the higher ground), direction (deg, world), floor z of the opening
CAVES = (('Cave_Beast_Main', (1185, 330), 180, None), ('Cave_Mossy_South', (880, 615), -80, None),
         ('Cave_Mossy_West', (880, 615), 190, None), ('Cave_Whispering_Hollow', (250, 440), -95, None),
         ('Cave_Cloudridge_Ice', (525, 92), -60, None), ('Cave_Fortress_Undergate', (1205, 520), 95, None),
         ('Cave_Ruins_Catacomb', (650, 390), -90, None))
SECRETS = (('Secret_Mistfall_Isle', 75, 330), ('Secret_Lotus_Grotto', 1085, 990), ('Secret_Cloud_Perch', 290, 55),
           ('Secret_Overlook', 1440, 470))
RESERVED = (('Reserved_Verdant_Village', 525, 765, 'rect', 210, 150), ('Reserved_Ancient_Ruins', 650, 390, 'circle', 105, 0),
            ('Reserved_World_Tree', 775, 140, 'circle', 46, 0), ('Reserved_Sky_Temple', 1235, 92, 'rect', 120, 90),
            ('Reserved_Jungle_Fortress', 1195, 520, 'rect', 150, 150), ('Reserved_Entrance_Gate', 205, 885, 'circle', 46, 0))


# ---------------------------------------------------------------- materials -
def build_floor1_materials():
    P, N = mat_plain, mat_noise
    N('F1_Grass_Verdant', (0.30, 0.72, 0.16), (0.36, 0.80, 0.20), 0.85, 0.02, 0.05, 1.0)
    N('F1_Grass_Valley', (0.18, 0.66, 0.30), (0.24, 0.74, 0.34), 0.85, 0.02, 0.05, 1.0)
    N('F1_Grass_Ruins', (0.52, 0.68, 0.22), (0.60, 0.74, 0.28), 0.85, 0.02, 0.05, 1.0)
    N('F1_Grass_Mystic', (0.08, 0.40, 0.20), (0.12, 0.46, 0.24), 0.85, 0.02, 0.05, 1.0)
    N('F1_Grass_Jungle', (0.06, 0.46, 0.10), (0.10, 0.54, 0.14), 0.85, 0.02, 0.05, 1.0)
    N('F1_Swamp', (0.28, 0.42, 0.16), (0.34, 0.48, 0.20), 0.9, 0.02, 0.05, 1.0)
    P('F1_Path', (0.78, 0.60, 0.36), 0.9)
    P('F1_Sand', (0.92, 0.82, 0.55), 0.9)
    P('F1_Lakebed', (0.30, 0.42, 0.40), 0.9)
    N('F1_Rock', (0.56, 0.50, 0.45), (0.62, 0.56, 0.50), 0.85, 0.03, 0.1, 1.0)
    N('F1_Rock_Dark', (0.20, 0.18, 0.22), (0.26, 0.23, 0.27), 0.85, 0.03, 0.1, 1.0)
    N('F1_Rock_Under', (0.42, 0.35, 0.32), (0.48, 0.40, 0.36), 0.9, 0.02, 0.1, 1.0)
    N('F1_Rock_Under_Dark', (0.17, 0.15, 0.18), (0.22, 0.19, 0.22), 0.9, 0.02, 0.1, 1.0)
    P('F1_Snow', (0.93, 0.95, 1.0), 0.7)
    P('F1_Water', (0.10, 0.52, 0.95), 0.08, emit=0.15)
    P('F1_Water_Swamp', (0.16, 0.48, 0.36), 0.15, emit=0.1)
    P('F1_Waterfall', (0.72, 0.90, 1.0), 0.2, emit=0.6)
    P('F1_Cloud', (0.97, 0.98, 1.0), 0.95, emit=0.25)
    P('F1_Cave', (0.03, 0.03, 0.05), 1.0)
    P('F1_Marker_Spawn', (0.25, 1.0, 0.55), 0.4, emit=0.8)
    P('F1_Marker_Checkpoint', (0.15, 0.55, 1.0), 0.4, emit=1.0)
    P('F1_Marker_MiniBoss', (1.0, 0.15, 0.15), 0.4, emit=1.0)
    P('F1_Marker_Boss', (1.0, 0.55, 0.05), 0.4, emit=1.0)
    P('F1_Marker_Egg', (1.0, 0.82, 0.30), 0.4, emit=0.9)
    P('F1_Marker_Secret', (0.70, 0.25, 1.0), 0.4, emit=1.0)
    P('F1_Reserved', (1.0, 1.0, 1.0), 0.5, emit=0.5)
    P('F1_Label', (1.0, 1.0, 1.0), 0.5, emit=1.2)
    P('F1_Label_Gold', (1.0, 0.80, 0.25), 0.5, emit=1.0)


GRASS = {VF: 'F1_Grass_Verdant', WV: 'F1_Grass_Valley', AR: 'F1_Grass_Ruins', MW: 'F1_Grass_Mystic',
         JF: 'F1_Grass_Jungle'}


# ---------------------------------------------------------------- helpers ---
def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ring_noise(theta, seed, irr):
    rng = np.random.default_rng(seed)
    out = np.zeros_like(theta)
    for k in range(2, 8):
        out += rng.uniform(0.4, 1.0) / math.sqrt(k) * np.sin(k * theta + rng.uniform(0, TAU))
    return irr * out / 1.6


def field_noise(X, Y, seed, wl=90.0):
    rng = np.random.default_rng(seed + 1000)
    out = np.zeros_like(X)
    for k, f in enumerate((1.0, 0.55, 0.3, 0.18)):
        a = rng.uniform(0, TAU)
        w = wl * f
        out += (0.6 ** k) * np.sin((X * math.cos(a) + Y * math.sin(a)) / w * TAU + rng.uniform(0, TAU))
    return out / 1.6


def ellipse_field(X, Y, cx, cy, rx, ry, seed, irr):
    """(normalised radius / noisy boundary radius, approx signed distance in studs)"""
    wx, wy = px(cx, cy)
    RX, RY = rx * 0.977, ry * 1.465
    u, v = (X - wx) / RX, (Y - wy) / RY
    f = np.sqrt(u * u + v * v)
    rb = 1.0 + ring_noise(np.arctan2(v, u), seed, irr)
    g = f / rb
    return g, (1.0 - g) * (0.5 * min(RX, RY) + 0.25 * (RX + RY) * 0.5)


def seg_dist(X, Y, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-9
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
    qx, qy = ax + t * dx, ay + t * dy
    return np.hypot(X - qx, Y - qy), t


# ---------------------------------------------------------------- terrain ---
class Terrain:
    def __init__(self):
        n = int(2 * EXT / S) + 1
        self.n = n
        g = np.linspace(-EXT, EXT, n)
        self.X, self.Y = np.meshgrid(g, g, indexing='ij')
        X, Y = self.X, self.Y
        H = np.full((n, n), -1e9)
        L = np.full((n, n), -1e9)
        own = np.full((n, n), -1, dtype=int)
        for k, (name, bio, cx, cy, rx, ry, z, amp, irr, seed, dark, lv) in enumerate(AREAS):
            g_, sd = ellipse_field(X, Y, cx, cy, rx, ry, seed, irr)
            h = z + amp * field_noise(X, Y, seed) * smooth(0, 30, sd)
            better = (sd > 0) & (h > H)
            H[better] = h[better]
            own[better] = k
            L = np.maximum(L, sd)
        land0 = L > 0
        for cx, cy, r, h, e in FEATURES:                        # peaks, hills, crags, spires
            wx, wy = px(cx, cy)
            d = np.hypot(X - wx, Y - wy)
            H = H + np.where(land0, h * np.clip(1 - d / r, 0, 1) ** e, 0)
        # lakes and ponds (bowl + soft banks)
        self.lake_f = np.full((n, n), 9.0)
        self.lake_z = np.zeros((n, n))
        for name, cx, cy, rx, ry, zw, depth, seed in LAKES:
            g_, sd = ellipse_field(X, Y, cx, cy, rx, ry, seed, 0.12)
            tgt = np.where(g_ < 1, zw - depth * (1 - g_ ** 2) - 0.6, zw - 0.6 + (g_ - 1) / 0.35 * (H - zw + 0.6))
            m = (g_ < 1.35) & land0
            H = np.where(m, np.minimum(H, tgt), H)
            closer = g_ < self.lake_f
            self.lake_f = np.where(closer, g_, self.lake_f)
            self.lake_z = np.where(closer, zw, self.lake_z)
        # river channels
        for name, pts, w in RIVERS:
            for (ax, ay, az), (bx, by, bz) in zip(pts, pts[1:]):
                d, t = seg_dist(X, Y, px(ax, ay), px(bx, by))
                zw = az + (bz - az) * t
                bed = zw - 2.5
                tgt = bed + smooth(w / 2, w / 2 + 7, d) * 40
                H = np.where((d < w / 2 + 7) & land0, np.minimum(H, tgt), H)
        # flat pads
        for name, cx, cy, r, z in PADS:
            wx, wy = px(cx, cy)
            d = np.hypot(X - wx, Y - wy)
            t = smooth(r, r + 14, d)
            Hb = np.where(H < -1e6, z, H)                       # pad edge over the void: keep it level
            H = np.where((d < r + 14) & (L > -20), z * (1 - t) + Hb * t, H)
            L = np.maximum(L, np.where(L > -20, r + 2 - d, -1e9))
        # paths: flat road in the corridor, banks blend into terrain, bridges over the void
        best = np.full((n, n), 1e9)
        pz = np.zeros((n, n))
        phw = np.zeros((n, n))
        for name, w, pts in PATHS:
            for (ax, ay, az), (bx, by, bz) in zip(pts, pts[1:]):
                d, t = seg_dist(X, Y, px(ax, ay), px(bx, by))
                e = d - w / 2
                m = e < best
                best = np.where(m, e, best)
                pz = np.where(m, az + (bz - az) * t, pz)
                phw = np.where(m, w / 2, phw)
        island = L > 0
        t = smooth(0, 14, best)
        Hp = np.where(island, pz * (1 - t) + H * t, pz)
        H = np.where(best < 14, Hp, H)
        L = np.maximum(L, 2.0 - best)
        self.path_e = best
        self.H, self.L = H, L
        self.land = L > 0
        own = np.where(self.land & (own < 0), len(AREAS), own)      # path-only cells = natural bridges
        self.own = own
        self._underside()
        self._snap_edges()

    def sample(self, wx, wy):
        i = int(round((wx + EXT) / S)); j = int(round((wy + EXT) / S))
        i = min(max(i, 0), self.n - 1); j = min(max(j, 0), self.n - 1)
        return float(self.H[i, j]), bool(self.land[i, j])

    def _underside(self):
        """inverted-mountain rock underside: deeper the further a point is from the island edge"""
        n = self.n
        q = self.land.copy()
        q[:-1, :-1] = self.land[:-1, :-1] & self.land[1:, :-1] & self.land[:-1, 1:] & self.land[1:, 1:]
        q[-1, :] = False; q[:, -1] = False
        self.quad = q
        INF = 1e9
        d = np.where(self.land, INF, 0.0)
        for _ in range(2):                                          # chamfer distance (two passes, twice)
            for i in range(1, n):
                d[i, :] = np.minimum(d[i, :], d[i - 1, :] + S)
            for i in range(n - 2, -1, -1):
                d[i, :] = np.minimum(d[i, :], d[i + 1, :] + S)
            for j in range(1, n):
                d[:, j] = np.minimum(d[:, j], d[:, j - 1] + S)
            for j in range(n - 2, -1, -1):
                d[:, j] = np.minimum(d[:, j], d[:, j + 1] + S)
        Hs = np.where(self.land, self.H, 0.0)
        for _ in range(6):                                          # blur the top for a calm underside
            Hs = (Hs + np.roll(Hs, 1, 0) + np.roll(Hs, -1, 0) + np.roll(Hs, 1, 1) + np.roll(Hs, -1, 1)) / 5
        dd = np.minimum(d, 400)
        zu = Hs - 40 - np.minimum(dd, 70) * 1.5 - np.maximum(dd - 70, 0) * 0.9 \
            + 10 * field_noise(self.X, self.Y, 77, 60)
        zu = np.maximum(zu, -520)
        self.zu = np.minimum(zu, self.H - 36)

    def _snap_edges(self):
        """move boundary vertices onto the land iso-line -> smooth coastlines instead of grid steps"""
        L = np.clip(self.L, -3 * S, 3 * S)
        gx, gy = np.gradient(L, S)
        g2 = gx * gx + gy * gy + 1e-6
        land = self.land
        nb = np.zeros_like(land)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                nb |= ~np.roll(np.roll(land, di, 0), dj, 1)
        edge = land & nb
        sx = -gx / g2 * L
        sy = -gy / g2 * L
        mag = np.hypot(sx, sy)
        k = np.where(mag > S * 0.9, S * 0.9 / (mag + 1e-9), 1.0)
        self.VX = self.X + np.where(edge, sx * k, 0)
        self.VY = self.Y + np.where(edge, sy * k, 0)

    def quad_material(self, i, j, area):
        H = self.H
        hs = (H[i, j], H[i + 1, j], H[i, j + 1], H[i + 1, j + 1])
        slope = max(abs(H[i + 1, j] - H[i, j]), abs(H[i, j + 1] - H[i, j]), abs(H[i + 1, j + 1] - H[i, j + 1]),
                    abs(H[i + 1, j + 1] - H[i + 1, j])) / S
        name = AREAS[area][0] if area < len(AREAS) else 'Natural_Bridges'
        dark = AREAS[area][10] if area < len(AREAS) else False
        if slope > 1.05:
            return 'F1_Rock_Dark' if dark else 'F1_Rock'
        if self.path_e[i, j] < -1.5 and self.path_e[i + 1, j + 1] < -1.5:
            return 'F1_Path'
        if name == 'Natural_Bridges':
            return 'F1_Rock'
        zmax = max(hs)
        if self.lake_f[i, j] < 1.0 and zmax < self.lake_z[i, j] - 0.4:
            return 'F1_Lakebed'
        if self.lake_f[i, j] < 1.3 and zmax < self.lake_z[i, j] + 1.6:
            return 'F1_Sand'
        if name == 'Cloudridge_Peaks' and zmax > 175:
            return 'F1_Snow'
        if name == 'Cloudridge_Peaks' and slope > 0.7:
            return 'F1_Rock'
        if name in ('Lotus_Swamp', 'Secret_Lotus_Grotto'):
            return 'F1_Swamp'
        return GRASS[AREAS[area][1]]


def build_terrain(T):
    """one Top / Cliffs / Underside mesh per area"""
    n = T.n
    quad = T.quad
    # quad owner = owner of its highest corner (cliff faces belong to the upper area)
    stack = np.stack([T.own[:-1, :-1], T.own[1:, :-1], T.own[:-1, 1:], T.own[1:, 1:]])
    hst = np.stack([T.H[:-1, :-1], T.H[1:, :-1], T.H[:-1, 1:], T.H[1:, 1:]])
    qown = np.take_along_axis(stack, hst.argmax(0)[None], 0)[0]
    names = [a[0] for a in AREAS] + ['Natural_Bridges']
    biome_of = [a[1] for a in AREAS] + ['NATURAL_BRIDGES']
    objs = {}
    for area in range(len(names)):
        cells = np.argwhere(quad[:-1, :-1] & (qown == area))
        if not len(cells):
            continue
        col = coll(f'{biome_of[area]}', 'TERRAIN')
        for part in ('Top', 'Cliffs', 'Underside'):
            vmap, verts, faces, mats = {}, [], [], []
            slots = []

            def V(i, j, under=False):
                key = (i, j, under)
                if key not in vmap:
                    vmap[key] = len(verts)
                    verts.append((float(T.VX[i, j]), float(T.VY[i, j]), float(T.zu[i, j] if under else T.H[i, j])))
                return vmap[key]

            def M(m):
                if m not in slots:
                    slots.append(m)
                return slots.index(m)

            dark = area < len(AREAS) and AREAS[area][10]
            for i, j in cells:
                ring = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                if part == 'Top':
                    faces.append([V(*c) for c in ring])
                    mats.append(M(T.quad_material(i, j, area)))
                elif part == 'Underside':
                    faces.append([V(*c, True) for c in ring[::-1]])
                    mats.append(M('F1_Rock_Under_Dark' if dark else 'F1_Rock_Under'))
                else:
                    for (a, b), (ni, nj) in zip(zip(ring, ring[1:] + ring[:1]),
                                                ((i, j - 1), (i + 1, j), (i, j + 1), (i - 1, j))):
                        if 0 <= ni < n - 1 and 0 <= nj < n - 1 and quad[ni, nj]:
                            continue
                        faces.append([V(*a), V(*a, True), V(*b, True), V(*b)])
                        mats.append(M('F1_Rock_Dark' if dark else 'F1_Rock'))
            if not faces:
                continue
            me = bpy.data.meshes.new(f'{names[area]}_{part}')
            me.from_pydata(verts, [], faces)
            for m in slots:
                me.materials.append(MATS[m])
            me.polygons.foreach_set('material_index', mats)
            me.update()
            ob = bpy.data.objects.new(f'{names[area]}_{part}', me)
            col.objects.link(ob)
            objs[(names[area], part)] = ob
    return objs


# ---------------------------------------------------------------- water -----
def ribbon(p, pts, w, mat, dz=0.0):
    """flat strip along a polyline of (x, y, z) world points"""
    bm = p.bm
    prev = None
    for k in range(len(pts)):
        a = Vector(pts[max(k - 1, 0)][:2]); b = Vector(pts[min(k + 1, len(pts) - 1)][:2])
        t = (b - a).normalized()
        nrm = Vector((-t.y, t.x)) * (w / 2)
        x, y, z = pts[k]
        l = bm.verts.new((x + nrm.x, y + nrm.y, z + dz)); r = bm.verts.new((x - nrm.x, y - nrm.y, z + dz))
        if prev:
            f = bm.faces.new((prev[1], r, l, prev[0]))
            f.material_index = p.mi(mat)
        prev = (l, r)


def densify(pts, step=8.0):
    out = []
    for (ax, ay, az), (bx, by, bz) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        k = max(1, int(L / step))
        out += [(ax + (bx - ax) * i / k, ay + (by - ay) * i / k, az + (bz - az) * i / k) for i in range(k)]
    return out + [pts[-1]]


def waterfall(p, T, start, ang, zw, w, name, falls):
    """walk from start along ang until the ground drops away, hang a water sheet there"""
    d = Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang))))
    q = Vector(start)
    for _ in range(200):
        q2 = q + d * 2.0
        h, land = T.sample(q2.x, q2.y)
        if not land or h < zw - 6:
            break
        q = q2
    else:
        return None
    hb, landb = T.sample(*(q + d * 14))
    zb = hb + 0.2 if landb and hb < zw - 4 else CLOUD_Z + 10
    top = zw + 0.3
    side = Vector((-d.y, d.x)) * (w / 2)
    c = q + d * 1.2
    bm = p.bm
    n = max(2, int((top - zb) / 12))
    rows = []
    for k in range(n + 1):
        z = top - (top - zb) * k / n
        bulge = d * (1.5 * math.sin(math.pi * k / n) + 3.0 * k / n)
        rows.append((bm.verts.new((c.x + side.x + bulge.x, c.y + side.y + bulge.y, z)),
                     bm.verts.new((c.x - side.x + bulge.x, c.y - side.y + bulge.y, z))))
    for (a0, b0), (a1, b1) in zip(rows, rows[1:]):
        f = bm.faces.new((a0, b0, b1, a1)); f.material_index = p.mi('F1_Waterfall')
    if landb and zb > CLOUD_Z + 20:                              # splash pool
        p.cyl(Vector((c.x + d.x * 5, c.y + d.y * 5, zb + 0.15)), w * 0.75, 0.3, 'F1_Waterfall', 16)
    falls.append(dict(name=name, top=round(top, 1), bottom=round(zb, 1), x=round(c.x, 1), y=round(c.y, 1)))
    return q


def build_water(T):
    coll('WATER', ROOT)
    falls = []
    rv = Part('F1_Rivers', coll('Rivers', 'WATER').name)
    wf = Part('F1_Waterfalls', coll('Waterfalls', 'WATER').name)
    for name, pts, w in RIVERS:
        wp = [(*px(x, y), z) for x, y, z in pts]
        ribbon(rv, densify(wp), w + 1.0, 'F1_Water')
        (ax, ay, _), (bx, by, zb) = wp[-2], wp[-1]
        ang = math.degrees(math.atan2(by - ay, bx - ax))
        waterfall(wf, T, (bx, by), ang, zb, w, name + '_Falls', falls)
    for name, (sx, sy), ang, zw, w in SPRINGS:
        waterfall(wf, T, px(sx, sy), ang, zw, w, name, falls)
    rv.finish(); wf.finish()
    lk = Part('F1_Lakes', coll('Lakes', 'WATER').name)
    for name, cx, cy, rx, ry, zw, depth, seed in LAKES:
        wx, wy = px(cx, cy)
        RX, RY = rx * 0.977 * 1.06, ry * 1.465 * 1.06
        th = np.linspace(0, TAU, 49)[:-1]
        rb = 1.0 + ring_noise(th, seed, 0.12)
        pts = [(wx + math.cos(a) * RX * r, wy + math.sin(a) * RY * r) for a, r in zip(th, rb)]
        mat = 'F1_Water_Swamp' if name.startswith('Lotus') else 'F1_Water'
        lk.prism([(x - wx, y - wy) for x, y in pts], zw - 0.2, zw, mat, Matrix.Translation((wx, wy, 0)))
    lk.finish()
    return falls


# ---------------------------------------------------------------- blockouts --
def ground(T, x, y):
    return T.sample(*px(x, y))[0]


def build_blockouts(T):
    coll('LANDMARK_BLOCKOUTS', ROOT)
    out = dict(checkpoints=[], miniboss=[], boss=None, eggs=[], caves=[], secrets=[])
    # floor entrance spawn footprint
    sp = Part('Floor_Entrance_Spawn', coll('Floor_Entrance_Spawn', 'LANDMARK_BLOCKOUTS').name)
    wx, wy = px(205, 885)
    z = ground(T, 205, 885)
    sp.cyl((wx, wy, z + 0.2), 12.0, 0.4, 'F1_Marker_Spawn', 32)
    sp.torus((wx, wy, z + 0.5), 44.0, 0.7, 'F1_Marker_Spawn', 48, 4)
    for k in range(4):
        a = TAU * k / 4 + TAU / 8
        sp.box((wx + math.cos(a) * 44, wy + math.sin(a) * 44, z + 6), (3, 3, 12), 'F1_Marker_Spawn')
    sp.finish()
    out['spawn'] = (wx, wy, z)
    cp = coll('Checkpoints', 'LANDMARK_BLOCKOUTS').name
    for name, x, y in CHECKPOINTS:
        wx, wy = px(x, y); z = ground(T, x, y)
        p = Part(name, cp)
        p.cyl((wx, wy, z + 0.4), 10.0, 0.8, 'F1_Marker_Checkpoint', 24)
        p.box((wx, wy, z + 8), (2.5, 2.5, 15), 'F1_Marker_Checkpoint')
        p.finish()
        out['checkpoints'].append((name, wx, wy, z))
    mb = coll('Mini_Bosses', 'LANDMARK_BLOCKOUTS').name
    for name, x, y in MINIBOSSES:
        wx, wy = px(x, y); z = ground(T, x, y)
        p = Part(name, mb)
        p.torus((wx, wy, z + 0.6), 30.0, 1.2, 'F1_Marker_MiniBoss', 40, 4)
        for k in range(4):
            a = TAU * k / 4
            p.box((wx + math.cos(a) * 30, wy + math.sin(a) * 30, z + 7), (3, 3, 14), 'F1_Marker_MiniBoss')
        p.finish()
        out['miniboss'].append((name, wx, wy, z))
    bs = coll('Main_Boss', 'LANDMARK_BLOCKOUTS').name
    wx, wy = px(1195, 520); z = ground(T, 1195, 520)
    p = Part('Main_Boss_Jungle_Overlord', bs)
    p.torus((wx, wy, z + 0.8), 52.0, 1.6, 'F1_Marker_Boss', 48, 4)
    for k in range(8):
        a = TAU * k / 8
        p.box((wx + math.cos(a) * 52, wy + math.sin(a) * 52, z + 10), (4, 4, 20), 'F1_Marker_Boss')
    p.finish()
    out['boss'] = ('Main_Boss_Jungle_Overlord', wx, wy, z)
    eg = coll('World_Eggs', 'LANDMARK_BLOCKOUTS').name
    for name, x, y in EGGS:
        wx, wy = px(x, y); z = ground(T, x, y)
        p = Part(name, eg)
        p.cyl((wx, wy, z + 0.4), 6.0, 0.8, 'F1_Marker_Egg', 20)
        p.box((wx, wy, z + 6), (1.6, 1.6, 11), 'F1_Marker_Egg')
        p.finish()
        out['eggs'].append((name, wx, wy, z))
    sc = coll('Secret_Areas', 'LANDMARK_BLOCKOUTS').name
    for name, x, y in SECRETS:
        wx, wy = px(x, y); z = ground(T, x, y)
        p = Part(name + '_Marker', sc)
        p.cyl((wx, wy, z + 0.4), 8.0, 0.8, 'F1_Marker_Secret', 20)
        p.box((wx, wy, z + 7), (2, 2, 13), 'F1_Marker_Secret')
        p.finish()
        out['secrets'].append((name, wx, wy, z))
    cv = coll('Cave_Entrances', 'LANDMARK_BLOCKOUTS').name
    for name, (x, y), ang, _ in CAVES:
        d = Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang))))
        q = Vector(px(x, y)); h0 = T.sample(*q)[0]
        for _ in range(250):
            q2 = q + d * 2.0
            h, land = T.sample(*q2)
            if not land or h < h0 - 10:
                break
            q = q2
        hb, landb = T.sample(*(q + d * 16))
        zf = hb if landb else T.sample(*q)[0] - 24
        top = T.sample(*q)[0]
        w = 30.0
        hh = min(26.0, max(12.0, top - zf - 3))
        M = Matrix.Translation((q.x - d.x * 3, q.y - d.y * 3, zf)) @ Matrix.Rotation(math.atan2(d.y, d.x) + math.pi / 2, 4, 'Z')
        FLIP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        p = Part(name, cv)
        arch = round_arch(w, max(1.0, hh - w / 2), 10)
        p.prism(arch, -3.0, 28.0, 'F1_Cave', M @ FLIP)
        frame_strip(p, M, round_arch(w + 7, max(1.0, hh - w / 2), 10), arch, -4.5, 1.5, 'F1_Rock')
        p.finish()
        wc = M @ Vector((0, 0, 0))
        out['caves'].append((name, wc.x, wc.y, zf))
    return out


# ---------------------------------------------------------------- clouds / guides --
def build_clouds():
    c = coll('CLOUDS', ROOT).name
    p = Part('F1_Cloud_Sea', c)
    p.cyl((0, 0, CLOUD_Z), 4500.0, 2.0, 'F1_Cloud', 64)
    p.finish()
    rnd = random.Random(42)
    q = Part('F1_Cloud_Puffs', c)
    for k in range(140):
        a = rnd.uniform(0, TAU); r = rnd.uniform(150, 1500)
        x, y = math.cos(a) * r, math.sin(a) * r
        s = rnd.uniform(28, 75)
        for j in range(3):
            q.ico((x + rnd.uniform(-1, 1) * s, y + rnd.uniform(-1, 1) * s, CLOUD_Z + rnd.uniform(4, 20) + j * 4),
                  s * rnd.uniform(0.6, 1.0), 'F1_Cloud', 2, (1.0, 1.0, 0.45))
    q.finish()


def build_guides(T, falls, marks):
    gc = coll('GUIDES', ROOT).name
    lc = coll('Map_Labels', gc).name
    for name, bio, cx, cy, rx, ry, z, amp, irr, seed, dark, lv in AREAS:
        wx, wy = px(cx, cy)
        h = T.sample(wx, wy)[0]
        title = name.replace('_', ' ').upper()
        for txt, dy, size, mat in ((title, 10, 28, 'F1_Label'), (lv, -26, 20, 'F1_Label_Gold')):
            o = text_mesh(f'Label_{name}_{dy}', txt, lc, size, 1.0, mat, (wx, wy + dy, h + 45), 0)
            o.matrix_world = Matrix.Translation((wx, wy + dy, h + 45)) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
    o = text_mesh('Label_Floor_Title', 'FLOOR 1 - THE VERDANT KINGDOM', lc, 40, 2.0, 'F1_Label_Gold', (0, 0, 0), 0)
    wx, wy = px(260, 60)
    o.matrix_world = Matrix.Translation((wx - 150, wy + 120, 320)) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
    rs = Part('Reserved_Footprints', gc)
    for name, cx, cy, kind, a, b in RESERVED:
        wx, wy = px(cx, cy)
        z = T.sample(wx, wy)[0] + 0.5
        if kind == 'circle':
            rs.torus((wx, wy, z), a, 0.7, 'F1_Reserved', 48, 4)
        else:
            for sx, sy, w_, h_ in ((0, -b / 2, a, 1.4), (0, b / 2, a, 1.4), (-a / 2, 0, 1.4, b), (a / 2, 0, 1.4, b)):
                rs.box((wx + sx, wy + sy, z), (w_, h_, 1.0), 'F1_Reserved')
    rs.finish()


def build_scale_refs(T):
    from common import avatar
    gc = coll('GUIDES', ROOT).name
    wx, wy = px(205, 885)
    z = T.sample(wx, wy)[0]
    avatar('SCALE_Avatar_5studs', gc, (wx + 20, wy - 10, z), 0)
    p = Part('SCALE_Pet_Mount_12studs', gc)
    p.box((wx + 30, wy - 10, z + 4.5), (5, 12, 5), 'F1_Marker_Egg')
    p.box((wx + 30, wy - 4, z + 8.5), (4, 4, 4), 'F1_Marker_Egg')
    p.finish()


# ---------------------------------------------------------------- cameras ---
def build_floor1_cameras(coll_name='CAMERAS'):
    out = {}
    specs = (('CAM_F1_Map_TopDown', (0, -15, 3000), (0, -15, 0), 'ORTHO', 2330),
             ('CAM_F1_Overview', (-900, -1300, 820), (60, 30, -40), 'PERSP', 28),
             ('CAM_F1_Entrance_Player', (px(190, 935)[0], px(190, 935)[1], 22), (px(300, 600)[0], px(300, 600)[1], 40), 'PERSP', 24),
             ('CAM_F1_Valley_View', (px(470, 700)[0], px(470, 700)[1], 70), (px(900, 380)[0], px(900, 380)[1], 60), 'PERSP', 24),
             ('CAM_F1_Fortress_View', (px(870, 760)[0], px(870, 760)[1], 120), (px(1200, 540)[0], px(1200, 540)[1], 140), 'PERSP', 26),
             ('CAM_F1_Side_Elevation', (150, -2300, 160), (150, 0, 40), 'PERSP', 34))
    for name, loc, tgt, kind, lens in specs:
        cam = bpy.data.cameras.new(name)
        cam.clip_start = 1.0; cam.clip_end = 60000
        if kind == 'ORTHO':
            cam.type = 'ORTHO'; cam.ortho_scale = lens
        else:
            cam.lens = lens
        o = bpy.data.objects.new(name, cam)
        o.location = loc
        o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        coll(coll_name).objects.link(o)
        out[name] = o
    out['CAM_F1_Map_TopDown']['hide_collections'] = 'CLOUDS'
    for k, o in out.items():
        if k != 'CAM_F1_Map_TopDown':
            o['hide_collections'] = 'Map_Labels'
    return out


# ---------------------------------------------------------------- main ------
def to_roblox(x, y, z):
    return [round(x, 1), round(z, 1), round(-y, 1)]


def build_floor1():
    coll(ROOT)
    coll('TERRAIN', ROOT)
    T = Terrain()
    build_terrain(T)
    falls = build_water(T)
    marks = build_blockouts(T)
    build_clouds()
    build_guides(T, falls, marks)
    build_scale_refs(T)
    # layout data for Roblox scripting (Roblox coordinates: X, Y up, Z = -Blender Y)
    areas = []
    for name, bio, cx, cy, rx, ry, z, amp, irr, seed, dark, lv in AREAS:
        wx, wy = px(cx, cy)
        areas.append(dict(name=name, biome=bio, levels=lv, center=to_roblox(wx, wy, T.sample(wx, wy)[0])))
    layout = dict(
        floor='Floor 1 - The Verdant Kingdom', units='studs', roblox_axes='X, Y up, Z = -Blender Y',
        spawn=to_roblox(*marks['spawn']), areas=areas,
        checkpoints=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['checkpoints']],
        mini_bosses=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['miniboss']],
        main_boss=dict(name=marks['boss'][0], position=to_roblox(*marks['boss'][1:])),
        world_eggs=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['eggs']],
        caves=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['caves']],
        secret_areas=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['secrets']],
        paths=[dict(name=n, width=w, waypoints=[to_roblox(*px(x, y), z) for x, y, z in pts]) for n, w, pts in PATHS],
        waterfalls=falls)
    land = T.land
    stats = dict(land_area_sq_studs=int(land.sum() * S * S), extent_x=[float(T.X[land].min()), float(T.X[land].max())],
                 extent_y=[float(T.Y[land].min()), float(T.Y[land].max())],
                 height_range=[float(T.H[land].min()), float(T.H[land].max())])
    return layout, stats
