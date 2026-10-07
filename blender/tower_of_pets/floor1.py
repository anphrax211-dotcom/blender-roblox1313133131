"""TOWER OF PETS - FLOOR 1: THE VERDANT KINGDOM - greybox base layout (terrain only).

Built 1:1 from the Floor 1 map sheet: every area's top surface is a polygon traced on the sheet (pixels), mapped
with one uniform scale (1.1 studs per pixel, north = +Y; px() converts), so the world keeps the sheet's
proportions (~1,600 x 1,080 studs of islands). Each area is a landmass at its own height; the max of all areas
makes one heightfield - areas that touch form one island (cliffs where heights differ, e.g. the central island of
Ancient Ruins + Emerald Lake + World Tree), gaps between outlines are open sky. Ride-able ramps, natural bridges, rivers, waterfalls, lakes, flat
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
EXT = 870.0                               # grid half extent
BIOMES = ('VERDANT_FOREST', 'WATERFALL_VALLEY', 'ANCIENT_RUINS', 'MYSTIC_WILDS', 'JUNGLE_FORTRESS')
VF, WV, AR, MW, JF = BIOMES
CLOUD_Z = -360.0
ZS = 1.3                                  # vertical exaggeration applied to every height below


MAP_SCALE = 1.1                           # studs per map-sheet pixel (uniform: the world keeps the sheet's proportions)
MAP_CX, MAP_CY = 690.0, 510.0             # sheet pixel at the world origin


def px(x, y):
    """map-sheet pixel -> world studs (1:1 with the sheet, north/up = +Y)"""
    return (x - MAP_CX) * MAP_SCALE, (MAP_CY - y) * MAP_SCALE


# ---------------------------------------------------------------- layout traced from the map sheet (pixels) ---
# Each area is a polygon traced around its top surface. Areas that touch form one island (cliffs where heights
# differ); gaps between polygons are open sky. Fields: name, biome, top z, noise amp, edge irregularity, seed,
# dark rock, level range, label position, outline.
AREAS = (
    # --- west continent: Whispering Forest above Sunlit Meadows + Verdant Village, Floor Entrance at the south-west
    ('Whispering_Forest', VF, 40, 5.0, 0.6, 4, False, 'Lv 1-15', (322, 395),
     [(150, 300), (195, 262), (260, 255), (340, 262), (420, 268), (478, 275), (505, 310), (510, 380), (505, 450),
      (495, 520), (470, 562), (400, 578), (320, 584), (240, 580), (170, 565), (150, 500), (140, 420)]),
    ('Sunlit_Meadows', VF, 12, 3.0, 0.6, 2, False, 'Lv 1-10', (237, 683),
     [(10, 600), (60, 572), (160, 560), (260, 568), (360, 572), (415, 595), (418, 650), (405, 705), (390, 760),
      (330, 792), (240, 792), (150, 782), (60, 770), (15, 720), (5, 650)]),
    ('Verdant_Village', VF, 12, 1.0, 0.5, 3, False, 'Lv 1-20', (557, 815),
     [(375, 700), (450, 688), (540, 692), (620, 700), (680, 712), (745, 712), (768, 742), (705, 768), (672, 822),
      (600, 848), (520, 852), (440, 842), (380, 805), (362, 745)]),
    ('Floor_Entrance', VF, 5, 0.0, 0.3, 1, False, 'Spawn', (215, 902),
     [(60, 822), (120, 788), (200, 778), (290, 786), (338, 818), (322, 882), (282, 925), (190, 936), (110, 926),
      (60, 882)]),
    ('Secret_Mistfall_Isle', VF, 32, 1.0, 0.5, 6, False, 'Secret', (95, 455),
     [(50, 430), (90, 410), (140, 420), (150, 465), (120, 495), (70, 492), (45, 465)]),
    # --- Riverfall Valley: its own plateau island between the meadows, the ruins and Mossy Caverns
    ('Riverfall_Valley', WV, 32, 2.0, 0.5, 7, False, 'Lv 10-25', (620, 607),
     [(445, 525), (500, 505), (560, 508), (640, 505), (700, 518), (730, 560), (722, 620), (716, 668), (680, 690),
      (600, 690), (540, 682), (482, 672), (448, 632), (436, 572)]),
    # --- the central island: Ancient Ruins + Emerald Lake + the World Tree in one landmass
    ('Ancient_Ruins', AR, 72, 1.5, 0.5, 11, False, 'Lv 20-35', (650, 408),
     [(520, 292), (565, 272), (640, 266), (720, 270), (795, 288), (822, 330), (818, 400), (802, 458), (760, 488),
      (680, 494), (600, 490), (540, 478), (518, 430), (512, 360)]),
    ('World_Tree_Grove', MW, 105, 4.0, 0.6, 14, False, 'Lv 45-60', (780, 128),
     [(612, 150), (650, 92), (700, 42), (780, 16), (870, 20), (940, 58), (962, 120), (955, 190), (905, 238),
      (830, 262), (750, 266), (680, 256), (630, 222)]),
    ('Emerald_Lake', WV, 64, 2.0, 0.5, 8, False, 'Lv 15-30', (955, 372),
     [(800, 262), (860, 236), (940, 228), (1010, 236), (1065, 262), (1092, 320), (1095, 400), (1062, 452),
      (995, 482), (900, 488), (830, 478), (802, 432), (796, 350)]),
    # --- Cloudridge Peaks: north-west, joined to the World Tree side of the central island
    ('Cloudridge_Peaks', AR, 95, 5.0, 0.6, 12, False, 'Lv 35-50', (470, 183),
     [(332, 192), (360, 122), (420, 62), (500, 40), (580, 48), (640, 80), (662, 140), (652, 200), (602, 236),
      (532, 246), (455, 246), (385, 236)]),
    ('Secret_Cloud_Perch', AR, 150, 1.0, 0.5, 13, False, 'Secret', (1025, 70),
     [(990, 50), (1030, 32), (1068, 52), (1062, 95), (1022, 108), (992, 88)]),
    # --- the dark east: Beast Cave crags and the Jungle Fortress (highest plateau), fused to the lake's east shore
    ('Beast_Cave', MW, 115, 8.0, 0.7, 16, True, 'Lv 30-45', (1180, 330),
     [(1088, 262), (1130, 232), (1200, 226), (1270, 236), (1322, 270), (1336, 332), (1322, 400), (1282, 440),
      (1200, 452), (1122, 446), (1090, 420), (1082, 340)]),
    ('Jungle_Fortress', JF, 150, 4.0, 0.6, 17, True, 'Lv 55-70', (1228, 603),
     [(1072, 452), (1130, 432), (1220, 428), (1300, 442), (1356, 482), (1362, 562), (1342, 640), (1282, 690),
      (1200, 700), (1120, 692), (1082, 640), (1068, 560)]),
    ('Sky_Temple', JF, 210, 1.5, 0.5, 19, False, 'Lv 50-70', (1245, 118),
     [(1126, 140), (1170, 110), (1240, 100), (1310, 108), (1350, 138), (1346, 182), (1312, 206), (1240, 212),
      (1166, 200), (1126, 172)]),
    ('Secret_Overlook', JF, 125, 1.0, 0.5, 20, True, 'Secret', (1425, 590),
     [(1395, 560), (1435, 548), (1462, 575), (1450, 618), (1408, 622), (1390, 595)]),
    # --- Mossy Caverns and Lotus Swamp: separate islands south of the lake
    ('Mossy_Caverns', MW, 55, 6.0, 0.6, 15, False, 'Lv 25-40', (905, 612),
     [(762, 522), (820, 502), (900, 498), (980, 508), (1042, 532), (1050, 600), (1040, 670), (1000, 720),
      (940, 746), (860, 752), (790, 736), (762, 690), (752, 600)]),
    ('Lotus_Swamp', WV, -4, 1.0, 0.6, 9, False, 'Lv 20-35', (868, 893),
     [(706, 822), (760, 782), (850, 768), (950, 764), (1040, 772), (1120, 792), (1180, 832), (1190, 900),
      (1160, 960), (1080, 986), (950, 992), (830, 986), (740, 962), (700, 900)]),
    ('Secret_Lotus_Grotto', WV, -20, 1.0, 0.5, 10, False, 'Secret', (555, 975),
     [(515, 955), (560, 940), (600, 955), (598, 990), (555, 1004), (515, 990)]),
)
DECOR_ISLETS = (                          # small floating rocks seen around the sheet (scenery, not on any route)
    ('Decor_Islet_West', VF, 20, (40, 330), 30), ('Decor_Islet_South', VF, -10, (415, 925), 38),
    ('Decor_Islet_SouthWest', VF, -30, (40, 960), 40), ('Decor_Islet_North', MW, 160, (1165, 45), 24),
    ('Decor_Islet_Lake', WV, 40, (1010, 1005), 30), ('Decor_Islet_East', JF, 100, (1400, 680), 30),
)
# peaks / hills / crags / spires added on top of an area: cx, cy (px), radius (studs), height, profile exponent
FEATURES = (
    (430, 112, 70, 115, 1.3), (500, 78, 85, 150, 1.2), (572, 100, 62, 105, 1.3), (388, 172, 46, 60, 1.5),
    (622, 92, 46, 70, 1.4),                                                     # Cloudridge Peaks
    (890, 610, 62, 34, 0.6),                                                    # Mossy Caverns cavern hill
    (1250, 255, 34, 60, 1.0), (1300, 300, 30, 50, 1.0), (1180, 262, 26, 44, 1.0), (1290, 390, 26, 40, 1.0),
    (1240, 420, 20, 30, 1.0),                                                   # Beast Cave crags
    (1092, 520, 22, 38, 0.5), (1345, 520, 26, 42, 0.5), (1325, 640, 24, 40, 0.5), (1100, 670, 20, 34, 0.5),
    (1230, 680, 22, 36, 0.5),                                                   # Jungle Fortress rim spires
    (700, 70, 30, 30, 1.0), (900, 70, 26, 24, 1.0),                             # World Tree grove knolls
)
# lakes / ponds: name, outline (px), water z, depth
LAKES = (
    ('Emerald_Lake_Water', [(842, 282), (900, 256), (980, 256), (1040, 285), (1058, 340), (1042, 410),
                            (1000, 450), (930, 462), (868, 446), (842, 400), (858, 350), (832, 312)], 60.0, 12.0),
    ('Ruins_Pond', [(705, 288), (745, 282), (770, 300), (752, 322), (712, 322)], 70.6, 3.0),
    ('Riverfall_Pond_West', [(455, 568), (510, 560), (535, 580), (512, 600), (462, 598)], 30.4, 4.0),
    ('Riverfall_Pond_East', [(618, 628), (668, 624), (695, 642), (668, 662), (622, 658)], 30.4, 4.0),
    ('Lotus_Pond_North', [(780, 812), (860, 795), (935, 805), (950, 845), (880, 868), (800, 860)], -4.6, 2.5),
    ('Lotus_Pond_Centre', [(845, 880), (930, 872), (1000, 890), (990, 940), (905, 955), (850, 930)], -4.6, 2.5),
    ('Lotus_Pond_East', [(1010, 815), (1080, 812), (1130, 845), (1110, 900), (1040, 905), (1005, 860)], -4.6, 2.5),
    ('Lotus_Pond_West', [(740, 880), (790, 875), (812, 910), (785, 940), (745, 925)], -4.6, 2.5),
)
LAKE_ISLETS = (('Lake_Islet', 960, 330, 20, 64),)
# rivers: [(px, py, water z)], width studs
RIVERS = (
    ('Whispering_Stream', [(250, 330, 38.6), (298, 420, 38.6), (310, 515, 38.0), (300, 568, 38.0)], 14),
    ('Meadow_Brook', [(300, 612, 10.6), (250, 652, 10.6), (150, 702, 10.6), (55, 745, 10.6)], 12),
    ('Riverfall_River_West', [(600, 512, 30.4), (560, 545, 30.4), (512, 580, 30.4), (470, 632, 30.0)], 14),
    ('Riverfall_River_East', [(560, 545, 30.4), (620, 600, 30.4), (668, 642, 30.4), (700, 686, 30.0)], 14),
    ('Lake_Outflow_West', [(845, 440, 60.0), (836, 482, 60.0)], 14),
    ('Lake_Outflow_South', [(975, 455, 60.0), (976, 488, 60.0)], 16),
    ('Beast_Stream', [(1150, 280, 113.0), (1095, 278, 113.0)], 10),
    ('Fortress_Fall_West', [(1112, 545, 148.5), (1064, 552, 148.5)], 12),
    ('Fortress_Fall_South', [(1155, 640, 148.5), (1155, 698, 148.5)], 12),
)
# extra waterfalls (no river): start px, direction (deg, world), water z, width
SPRINGS = (
    ('Sky_Temple_Falls', (1215, 185), -90, 209.0, 12),
    ('Whispering_West_Falls', (200, 560), -95, 39.0, 12),
    ('Cloudridge_Falls', (400, 236), -100, 94.0, 12),
    ('Beast_East_Falls', (1282, 330), -80, 113.0, 10),
)
# flattened pads: name, px, py, radius studs, z (None = keep terrain at the centre)
PADS = (
    ('Spawn', 215, 850, 48, 5), ('Village_Square', 520, 765, 62, 12), ('Ruins_Plaza', 650, 380, 56, 72),
    ('World_Tree_Pad', 810, 170, 48, 105), ('Sky_Temple_Pad', 1240, 155, 52, 210),
    ('Fortress_Arena', 1190, 505, 72, 150), ('MiniBoss_1', 465, 445, 32, 40), ('MiniBoss_2', 960, 690, 32, 55),
    ('MiniBoss_3', 1292, 192, 24, 210), ('Lake_Islet', 960, 330, 20, 64),
    ('CP_1', 400, 676, 14, 12), ('CP_2', 545, 540, 14, 32), ('CP_3', 810, 455, 14, 64), ('CP_4', 1108, 292, 14, 80),
    ('CP_5', 1200, 168, 14, 210), ('CP_6', 900, 690, 14, 55),
)
# path network traced from the sheet: name, width studs, [(px, py, z)]
PATHS = (
    ('Entrance_Road', 32, [(215, 850, 5), (270, 815, 5), (330, 780, 12), (372, 758, 12)]),
    ('Meadow_Loop', 26, [(372, 758, 12), (270, 720, 12), (180, 662, 12), (230, 610, 12), (330, 640, 12),
                         (400, 676, 12)]),
    ('Riverfall_Bridge', 30, [(400, 676, 12), (450, 640, 24), (500, 610, 32), (560, 585, 32)]),
    ('Forest_Climb', 28, [(230, 610, 12), (200, 560, 26), (250, 510, 40), (330, 450, 40), (380, 430, 40)]),
    ('Guardian_Trail', 26, [(380, 430, 40), (465, 445, 40)]),
    ('Guardian_Bridge', 24, [(465, 445, 40), (510, 430, 56), (560, 410, 72), (650, 380, 72)]),
    ('Cloudridge_Stair', 22, [(380, 430, 40), (330, 380, 40), (330, 330, 40), (380, 300, 60), (430, 275, 80),
                              (470, 245, 95)]),
    ('Cloudridge_Pass', 26, [(470, 245, 95), (530, 195, 100), (610, 170, 100), (660, 175, 105), (720, 180, 105),
                             (810, 170, 105)]),
    ('World_Tree_Climb', 26, [(650, 380, 72), (700, 330, 80), (760, 290, 95), (800, 240, 105), (810, 170, 105)]),
    ('Ruins_South_Ramp', 26, [(650, 380, 72), (625, 430, 72), (610, 475, 60), (575, 505, 45), (545, 540, 32),
                              (560, 585, 32)]),
    ('Lake_Road', 28, [(650, 380, 72), (720, 400, 72), (790, 440, 64), (810, 455, 64)]),
    ('Lake_Loop', 24, [(810, 455, 64), (880, 476, 64), (980, 472, 64), (1052, 428, 64), (1072, 340, 64),
                       (1042, 266, 64), (960, 244, 64), (872, 250, 64), (822, 300, 64), (812, 380, 64), (810, 455, 64)]),
    ('World_Tree_Descent', 22, [(810, 170, 105), (880, 200, 105), (950, 220, 88), (1010, 240, 72), (1042, 266, 64)]),
    ('Beast_Climb', 24, [(1072, 300, 64), (1108, 292, 80), (1150, 250, 98), (1200, 280, 115), (1190, 330, 115)]),
    ('Fortress_North_Gate', 26, [(1190, 330, 115), (1170, 400, 115), (1220, 440, 132), (1200, 480, 150),
                                 (1190, 505, 150)]),
    ('Fortress_Canyon', 26, [(980, 600, 55), (1045, 590, 70), (1100, 620, 90), (1140, 580, 110), (1180, 620, 130),
                             (1222, 580, 150), (1190, 505, 150)]),
    ('Riverfall_Mossy_Bridge', 26, [(560, 585, 32), (640, 545, 32), (700, 545, 40), (780, 560, 55), (900, 600, 55)]),
    ('Lake_Mossy_Bridge', 26, [(880, 476, 64), (890, 530, 55), (900, 600, 55)]),
    ('Village_Swamp_Bridge', 26, [(372, 758, 12), (480, 770, 12), (600, 790, 12), (650, 830, 12), (720, 850, -2),
                                  (800, 870, -4)]),
    ('Village_Mossy_Bridge', 24, [(600, 790, 12), (690, 748, 12), (740, 735, 12), (800, 715, 32), (860, 692, 55),
                                  (960, 690, 55)]),
    ('Mossy_Swamp_Descent', 24, [(960, 690, 55), (1000, 740, 40), (1020, 800, 20), (980, 840, -4), (880, 880, -4)]),
    ('Sky_Stair', 22, [(1200, 280, 115), (1160, 235, 130), (1110, 200, 150), (1070, 165, 170), (1105, 130, 190),
                       (1165, 142, 210), (1240, 155, 210)]),
    ('West_Cliff_Trail', 22, [(180, 662, 12), (80, 640, 12), (120, 580, 24), (170, 540, 40), (250, 510, 40)]),
    ('Secret_Mistfall_Path', 12, [(170, 470, 40), (125, 462, 36), (95, 455, 32)]),
    ('Secret_Overlook_Path', 12, [(1340, 600, 150), (1395, 592, 135), (1425, 588, 125)]),
)

# ---- apply the vertical exaggeration once (paths stay ride-able) ----
AREAS = tuple(a[:2] + (a[2] * ZS,) + a[3:] for a in AREAS)
DECOR_ISLETS = tuple(d[:2] + (d[2] * ZS,) + d[3:] for d in DECOR_ISLETS)
FEATURES = tuple(f[:3] + (f[3] * ZS,) + f[4:] for f in FEATURES)
LAKES = tuple((n, pts, z * ZS, d * ZS) for n, pts, z, d in LAKES)
LAKE_ISLETS = tuple((n, x, y, r, z * ZS) for n, x, y, r, z in LAKE_ISLETS)
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
CHECKPOINTS = (('Checkpoint_1_Meadows', 400, 676), ('Checkpoint_2_Riverfall', 545, 540),
               ('Checkpoint_3_Lake', 810, 455), ('Checkpoint_4_Beast', 1108, 292),
               ('Checkpoint_5_Sky_Temple', 1200, 168), ('Checkpoint_6_Mossy', 900, 690))
MINIBOSSES = (('MiniBoss_1_Forest_Guardian', 465, 445), ('MiniBoss_2_Ancient_Beast', 960, 690),
              ('MiniBoss_3_Sky_Guardian', 1292, 192))
MAIN_BOSS = ('Main_Boss_Jungle_Overlord', 1190, 505)
SPAWN = (215, 850)
EGGS = (('World_Egg_1_Beast_Cave', 1103, 413), ('World_Egg_2_Lake_Islet', 960, 330),
        ('World_Egg_3_Whispering', 200, 400), ('World_Egg_4_Cloudridge', 560, 150),
        ('World_Egg_5_Riverfall', 650, 600), ('World_Egg_6_Lotus', 1100, 940))
# caves: name, start px (inside the higher ground), direction (deg, world), floor z of the opening
CAVES = (('Cave_Beast_Main', (1190, 330), 205, None), ('Cave_Mossy_South', (890, 610), -80, None),
         ('Cave_Mossy_West', (890, 610), 190, None), ('Cave_Whispering_Hollow', (300, 500), -95, None),
         ('Cave_Cloudridge_Ice', (500, 78), -90, None), ('Cave_Fortress_Undergate', (1190, 505), 95, None),
         ('Cave_World_Tree_Roots', (810, 170), -100, None))
SECRETS = (('Secret_Mistfall_Isle', 95, 455), ('Secret_Lotus_Grotto', 555, 975), ('Secret_Cloud_Perch', 1025, 70),
           ('Secret_Overlook', 1425, 590))
RESERVED = (('Reserved_Verdant_Village', 520, 765, 'rect', 210, 140), ('Reserved_Ancient_Ruins', 650, 380, 'circle', 100, 0),
            ('Reserved_World_Tree', 810, 170, 'circle', 46, 0), ('Reserved_Sky_Temple', 1240, 155, 'rect', 150, 80),
            ('Reserved_Jungle_Fortress', 1190, 505, 'rect', 150, 140), ('Reserved_Entrance_Gate', 215, 850, 'circle', 46, 0))


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


def seg_dist(X, Y, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-9
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
    qx, qy = ax + t * dx, ay + t * dy
    return np.hypot(X - qx, Y - qy), t


def poly_sd(X, Y, pts):
    """signed distance (studs, + inside) to a closed polygon of world points"""
    inside = np.zeros(X.shape, dtype=bool)
    dist = np.full(X.shape, 1e9)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        cond = ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / ((y2 - y1) or 1e-9) + x1)
        inside ^= cond
        dist = np.minimum(dist, seg_dist(X, Y, (x1, y1), (x2, y2))[0])
    return np.where(inside, dist, -dist)


def islet_poly(cx, cy, r, seed):
    rng = np.random.default_rng(seed)
    return [(cx + math.cos(a) * r * rng.uniform(0.8, 1.15) / MAP_SCALE, cy + math.sin(a) * r * rng.uniform(0.8, 1.15) / MAP_SCALE)
            for a in np.linspace(0, TAU, 9)[:-1]]


DECOR_AREAS = tuple((n, b, z, 1.0, 0.4, 50 + k, False, '', c, islet_poly(c[0], c[1], r, 50 + k))
                    for k, (n, b, z, c, r) in enumerate(DECOR_ISLETS))
ALL_AREAS = AREAS + DECOR_AREAS


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
        for k, (name, bio, z, amp, irr, seed, dark, lv, lab, poly) in enumerate(ALL_AREAS):
            sd = poly_sd(X, Y, [px(*p) for p in poly]) + irr * 9.0 * field_noise(X, Y, seed, 45.0)
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
        for name, poly, zw, depth in LAKES:
            sd = poly_sd(X, Y, [px(*p) for p in poly])
            rr = max(12.0, float(sd.max()))
            g_ = 1.0 - sd / rr                                       # 0 at the deepest point, 1 on the shore line
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
        own = np.where(self.land & (own < 0), len(ALL_AREAS), own)      # path-only cells = natural bridges
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
        name = ALL_AREAS[area][0] if area < len(ALL_AREAS) else 'Natural_Bridges'
        dark = ALL_AREAS[area][6] if area < len(ALL_AREAS) else False
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
        return GRASS[ALL_AREAS[area][1]]


def build_terrain(T):
    """one Top / Cliffs / Underside mesh per area"""
    n = T.n
    quad = T.quad
    # quad owner = owner of its highest corner (cliff faces belong to the upper area)
    stack = np.stack([T.own[:-1, :-1], T.own[1:, :-1], T.own[:-1, 1:], T.own[1:, 1:]])
    hst = np.stack([T.H[:-1, :-1], T.H[1:, :-1], T.H[:-1, 1:], T.H[1:, 1:]])
    qown = np.take_along_axis(stack, hst.argmax(0)[None], 0)[0]
    names = [a[0] for a in ALL_AREAS] + ['Natural_Bridges']
    biome_of = [a[1] for a in ALL_AREAS] + ['NATURAL_BRIDGES']
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

            dark = area < len(ALL_AREAS) and ALL_AREAS[area][6]
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
    for name, poly, zw, depth in LAKES:
        pts = [px(*p) for p in poly]
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        pts = [(cx + (x - cx) * 1.05, cy + (y - cy) * 1.05) for x, y in pts]     # tuck the edge under the banks
        mat = 'F1_Water_Swamp' if name.startswith('Lotus') else 'F1_Water'
        lk.prism([(x - cx, y - cy) for x, y in pts], zw - 0.2, zw, mat, Matrix.Translation((cx, cy, 0)))
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
    wx, wy = px(*SPAWN)
    z = ground(T, *SPAWN)
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
    wx, wy = px(*MAIN_BOSS[1:]); z = ground(T, *MAIN_BOSS[1:])
    p = Part(MAIN_BOSS[0], bs)
    p.torus((wx, wy, z + 0.8), 52.0, 1.6, 'F1_Marker_Boss', 48, 4)
    for k in range(8):
        a = TAU * k / 8
        p.box((wx + math.cos(a) * 52, wy + math.sin(a) * 52, z + 10), (4, 4, 20), 'F1_Marker_Boss')
    p.finish()
    out['boss'] = (MAIN_BOSS[0], wx, wy, z)
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
    for name, bio, z, amp, irr, seed, dark, lv, (cx, cy), poly in AREAS:
        wx, wy = px(cx, cy)
        h = T.sample(wx, wy)[0]
        if h < -1e6:
            h = z
        title = name.replace('_', ' ').upper()
        for txt, dy, size, mat in ((title, 10, 28, 'F1_Label'), (lv, -26, 20, 'F1_Label_Gold')):
            o = text_mesh(f'Label_{name}_{dy}', txt, lc, size, 1.0, mat, (wx, wy + dy, h + 45), 0)
            o.matrix_world = Matrix.Translation((wx, wy + dy, h + 45)) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
    o = text_mesh('Label_Floor_Title', 'FLOOR 1 - THE VERDANT KINGDOM', lc, 40, 2.0, 'F1_Label_Gold', (0, 0, 0), 0)
    wx, wy = px(170, 30)
    o.matrix_world = Matrix.Translation((wx, wy, 330)) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
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
    wx, wy = px(*SPAWN)
    z = T.sample(wx, wy)[0]
    avatar('SCALE_Avatar_5studs', gc, (wx + 20, wy - 10, z), 0)
    p = Part('SCALE_Pet_Mount_12studs', gc)
    p.box((wx + 30, wy - 10, z + 4.5), (5, 12, 5), 'F1_Marker_Egg')
    p.box((wx + 30, wy - 4, z + 8.5), (4, 4, 4), 'F1_Marker_Egg')
    p.finish()


# ---------------------------------------------------------------- cameras ---
def build_floor1_cameras(coll_name='CAMERAS'):
    out = {}
    specs = (('CAM_F1_Map_TopDown', (45, 0, 3000), (45, 0, 0), 'ORTHO', 1700),
             ('CAM_F1_Overview', (-950, -1250, 820), (60, 20, -40), 'PERSP', 28),
             ('CAM_F1_Entrance_Player', (px(150, 930)[0], px(150, 930)[1], 26), (px(340, 640)[0], px(340, 640)[1], 40), 'PERSP', 24),
             ('CAM_F1_Valley_View', (px(560, 690)[0], px(560, 690)[1], 75), (px(800, 330)[0], px(800, 330)[1], 100), 'PERSP', 24),
             ('CAM_F1_Fortress_View', (px(900, 650)[0], px(900, 650)[1], 115), (px(1200, 520)[0], px(1200, 520)[1], 170), 'PERSP', 26),
             ('CAM_F1_Side_Elevation', (40, -2150, 170), (40, 0, 60), 'PERSP', 34))
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
    for name, bio, z, amp, irr, seed, dark, lv, (cx, cy), poly in AREAS:
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
