"""TOWER OF PETS - FLOOR 1: THE VERDANT KINGDOM - base terrain pass (terrain only, no buildings or props).

Built on the layout traced from the Floor 1 map sheet (pixels; px() maps them with one uniform scale of 1.1 studs per
pixel, north = +Y) and then scaled up 10x (WORLD), so every region keeps its place on the sheet. The kingdom is four
big landmasses split by open sky and linked by natural rock bridges:
  * Verdant mainland (Entrance, Meadows, Village, Whispering Forest), Central highlands (Ruins, Cloudridge, World Tree,
    Emerald Lake, Riverfall Valley, Mossy Caverns), the Lotus Swamp, and the Jungle Fortress with Beast Cave; inside a
    landmass the regions' outlines are grown into the gaps and merged; the Sky Temple, four secret isles and two
    optional islets float on their own;
  * each region has its own height and terrain style (rolling fields, forest hills, terraced ruin foundations,
    mountain ridges, crags, jungle hills); where two regions meet at similar heights the ground slopes from one to the
    other (ride-able), where the height difference is large it becomes a cliff;
  * on top: Cloudridge peaks, a deep Waterfall Valley with three big falls, a ravine through the Whispering
    Forest, a rift across the ruins, the World Tree's root ridges, Beast Cave crags, and the Jungle Fortress as the
    largest region: a jungle ring at ~640 studs around a cliff-walled inner plateau at ~1,200 (final boss arena);
  * paths are organic (bowed, smoothed) and follow the ground with a grade limit, cutting canyons or raising
    causeways where they must; where a path crosses open sky it becomes a natural rock bridge.
Terrain, heights, water and landmarks are 10x; player-scale things (path widths, markers, checkpoint and mini-boss
pads, climb limits) are not, so the world is bigger to ride across, not bigger to stand in.

Five biomes (TERRAIN/<BIOME>, one Top / Cliffs / Underside mesh per area so each area can be refined later):
  VERDANT_FOREST    Floor_Entrance, Sunlit_Meadows, Verdant_Village, Whispering_Forest (+ Mistfall secret, treasure islet)
  WATERFALL_VALLEY  Riverfall_Valley, Emerald_Lake, Lotus_Swamp (+ Lotus Grotto secret)
  ANCIENT_RUINS     Ancient_Ruins, Cloudridge_Peaks (+ Cloud Perch secret)
  MYSTIC_WILDS      World_Tree_Grove, Mossy_Caverns, Beast_Cave
  JUNGLE_FORTRESS   Jungle_Fortress, Fortress_Heights, Sky_Temple (+ Overlook secret, rare-pet islet)
Greybox landmark massing (World Tree, fortress keep, ruin pillars) sits in LANDMARK_BLOCKOUTS so regions read from afar.
"""
import math, random, json
from collections import namedtuple
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from common import Part, MATS, mat_plain, mat_noise, coll, text_mesh, round_arch, TAU
from castle import frame_strip

ROOT = 'TOWER_OF_PETS_FLOOR_1'
WORLD = 10.0                              # world scale: the 1x sheet layout below is blown up 10x
S = 16.0                                  # grid spacing (studs)
EXT = 9984.0                              # grid half extent
BIOMES = ('VERDANT_FOREST', 'WATERFALL_VALLEY', 'ANCIENT_RUINS', 'MYSTIC_WILDS', 'JUNGLE_FORTRESS')
VF, WV, AR, MW, JF = BIOMES
CLOUD_Z = -380.0 * WORLD

MAP_SCALE = 1.1                           # studs per map-sheet pixel (uniform: the world keeps the sheet's proportions)
MAP_CX, MAP_CY = 690.0, 510.0             # sheet pixel at the world origin


def px(x, y):
    """map-sheet pixel -> world studs (north/up = +Y)"""
    return (x - MAP_CX) * MAP_SCALE * WORLD, (MAP_CY - y) * MAP_SCALE * WORLD


# the Floor 1 entrance: plaza (= spawn) and the portal axis (portal behind the plaza, the road in front)
ENTRANCE_SPAWN_PX, ENTRANCE_TOWARD_PX = (215, 860), (290, 815)


def entrance_px(dist, side=0.0):
    """sheet pixel `dist` studs behind the plaza centre (toward the portal), `side` studs to the right"""
    dx, dy = ENTRANCE_TOWARD_PX[0] - ENTRANCE_SPAWN_PX[0], ENTRANCE_TOWARD_PX[1] - ENTRANCE_SPAWN_PX[1]
    n = math.hypot(dx, dy)
    k = 1.0 / (MAP_SCALE * WORLD) / n
    return (ENTRANCE_SPAWN_PX[0] - dx * k * dist - dy * k * side, ENTRANCE_SPAWN_PX[1] - dy * k * dist + dx * k * side)


# ------------------------------------------ layout (map-sheet pixels; heights / sizes in 1x studs, x WORLD below) ---
# z: base height of the area's ground. style: (kind, amplitude, wavelength) - see style_height().
# irr: edge irregularity. grow: studs the outline is grown into the gaps inside its landmass. kind: 'land' areas
# merge with the other areas of their landmass (LANDMASS), 'inner' sits inside another area as a cliff-walled plateau,
# 'float' stays an island.
Area = namedtuple('Area', 'name biome z style irr seed dark levels label poly kind grow')
AREAS = (
    # --- Verdant Forest: the big starting region in the south-west
    Area('Floor_Entrance', VF, 12, ('flat', 1.0, 90), 0.3, 1, False, 'Spawn', (215, 925),
         [(60, 822), (120, 788), (200, 778), (290, 786), (338, 818), (322, 882), (282, 925), (190, 936), (110, 926),
          (60, 882)], 'land', 22),
    Area('Sunlit_Meadows', VF, 22, ('rolling', 9.0, 230), 0.6, 2, False, 'Lv 1-10', (150, 700),
         [(10, 600), (60, 572), (160, 560), (260, 568), (360, 572), (415, 595), (418, 650), (405, 705), (390, 760),
          (330, 792), (240, 792), (150, 782), (60, 770), (15, 720), (5, 650)], 'land', 22),
    Area('Verdant_Village', VF, 26, ('rolling', 3.0, 120), 0.5, 3, False, 'Lv 1-20', (520, 815),
         [(375, 700), (450, 688), (540, 692), (620, 700), (680, 712), (745, 712), (768, 742), (705, 768), (672, 822),
          (600, 848), (520, 852), (440, 842), (380, 805), (362, 745)], 'land', 22),
    Area('Whispering_Forest', VF, 62, ('hills', 22.0, 150), 0.6, 4, False, 'Lv 1-15', (245, 360),
         [(140, 300), (195, 262), (260, 250), (340, 262), (420, 268), (478, 275), (505, 310), (510, 380), (505, 450),
          (495, 520), (470, 562), (400, 578), (320, 584), (240, 580), (160, 565), (135, 500), (125, 420)], 'land', 22),
    # --- Waterfall Valley: the deep enclosed valley, the high lake and the low swamp
    Area('Riverfall_Valley', WV, -10, ('rolling', 5.0, 120), 0.5, 7, False, 'Lv 10-25', (600, 660),
         [(445, 525), (500, 505), (560, 508), (640, 505), (700, 518), (730, 560), (722, 620), (716, 668), (680, 690),
          (600, 690), (540, 682), (482, 672), (448, 632), (436, 572)], 'land', 22),
    Area('Emerald_Lake', WV, 100, ('rolling', 3.0, 120), 0.5, 8, False, 'Lv 15-30', (1000, 470),
         [(800, 262), (860, 236), (940, 228), (1010, 236), (1065, 262), (1092, 320), (1095, 400), (1062, 452),
          (995, 482), (900, 488), (830, 478), (802, 432), (796, 350)], 'land', 22),
    Area('Lotus_Swamp', WV, -24, ('flat', 1.5, 90), 0.6, 9, False, 'Lv 20-35', (900, 970),
         [(706, 822), (760, 782), (850, 768), (950, 764), (1040, 772), (1120, 792), (1180, 832), (1190, 900),
          (1160, 960), (1080, 986), (950, 992), (830, 986), (740, 962), (700, 900)], 'land', 22),
    # --- Ancient Ruins: the terraced plateau and the mountain ridge
    Area('Ancient_Ruins', AR, 118, ('terraced', 40.0, 22), 0.5, 11, False, 'Lv 20-35', (600, 455),
         [(520, 292), (565, 272), (640, 266), (720, 270), (795, 288), (822, 330), (818, 400), (802, 458), (760, 488),
          (680, 494), (600, 490), (540, 478), (518, 430), (512, 360)], 'land', 22),
    Area('Cloudridge_Peaks', AR, 140, ('ridged', 40.0, 110), 0.6, 12, False, 'Lv 35-50', (430, 225),
         [(320, 200), (350, 120), (420, 50), (500, 25), (590, 35), (645, 75), (662, 140), (652, 200), (602, 236),
          (532, 246), (455, 246), (380, 240)], 'land', 22),
    # --- Mystic Wilds: the World Tree's highland, the cavern hills and the dark crags
    Area('World_Tree_Grove', MW, 160, ('hills', 12.0, 140), 0.6, 14, False, 'Lv 45-60', (870, 30),
         [(612, 150), (640, 80), (700, 20), (780, -5), (870, 0), (950, 40), (975, 110), (960, 190), (905, 238),
          (830, 262), (750, 266), (680, 256), (630, 222)], 'land', 22),
    Area('Mossy_Caverns', MW, 72, ('crags', 16.0, 90), 0.6, 15, False, 'Lv 25-40', (905, 690),
         [(762, 522), (820, 502), (900, 498), (980, 508), (1042, 532), (1050, 600), (1040, 670), (1000, 720),
          (940, 746), (860, 752), (790, 736), (762, 690), (752, 600)], 'land', 22),
    Area('Beast_Cave', MW, 150, ('crags', 30.0, 80), 0.7, 16, True, 'Lv 30-45', (1250, 250),
         [(1088, 262), (1130, 232), (1200, 226), (1270, 236), (1322, 270), (1336, 332), (1322, 400), (1282, 440),
          (1200, 452), (1122, 446), (1090, 420), (1082, 340)], 'land', 22),
    # --- Jungle Fortress: the largest region - a jungle ring round a cliff-walled inner plateau
    Area('Jungle_Fortress', JF, 128, ('hills', 18.0, 130), 0.6, 17, True, 'Lv 55-70', (1340, 760),
         [(1050, 470), (1130, 420), (1230, 410), (1330, 425), (1410, 470), (1445, 560), (1430, 660), (1380, 735),
          (1290, 775), (1190, 780), (1110, 755), (1065, 700), (1050, 610)], 'land', 22),
    Area('Fortress_Heights', JF, 240, ('hills', 5.0, 100), 0.4, 18, True, 'Lv 60-70', (1230, 470),
         [(1110, 480), (1200, 455), (1290, 462), (1350, 505), (1365, 590), (1325, 665), (1240, 695), (1160, 688),
          (1112, 640), (1098, 560)], 'inner', 0),
    Area('Sky_Temple', JF, 310, ('flat', 2.0, 90), 0.3, 19, False, 'Lv 50-70', (1240, 60),
         [(1126, 115), (1170, 85), (1240, 75), (1310, 83), (1350, 113), (1346, 157), (1312, 181), (1240, 187),
          (1166, 175), (1126, 147)], 'float', 0),
    # --- secret isles (hidden paths) and two optional islets for treasure / rare pets (no path yet)
    Area('Secret_Mistfall_Isle', VF, 48, ('flat', 1.0, 90), 0.4, 6, False, '', None,
         [(0, 415), (40, 395), (85, 405), (95, 445), (70, 480), (20, 478), (-5, 450)], 'float', 0),
    Area('Secret_Cloud_Perch', AR, 190, ('flat', 1.0, 90), 0.4, 13, False, '', None,
         [(1030, 50), (1070, 32), (1108, 52), (1102, 95), (1062, 108), (1032, 88)], 'float', 0),
    Area('Secret_Overlook', JF, 150, ('flat', 1.0, 90), 0.4, 20, True, '', None,
         [(1505, 570), (1540, 558), (1567, 585), (1555, 628), (1513, 632), (1495, 605)], 'float', 0),
    Area('Secret_Lotus_Grotto', WV, -10, ('flat', 1.0, 90), 0.4, 10, False, '', None,
         [(515, 955), (560, 940), (600, 955), (598, 990), (555, 1004), (515, 990)], 'float', 0),
)


def islet_poly(cx, cy, r, seed):
    rng = np.random.default_rng(seed)
    return [(cx + math.cos(a) * r * rng.uniform(0.8, 1.15) / MAP_SCALE, cy + math.sin(a) * r * rng.uniform(0.8, 1.15) / MAP_SCALE)
            for a in np.linspace(0, TAU, 9)[:-1]]


OPTIONAL_ISLETS = (('Islet_Treasure', VF, -20, (10, 1000), 34), ('Islet_Rare_Pet', JF, 60, (1360, 930), 38))
AREAS += tuple(Area(n, b, z, ('flat', 1.0, 90), 0.4, 50 + k, False, '', None, islet_poly(c[0], c[1], r, 50 + k),
                    'float', 0) for k, (n, b, z, c, r) in enumerate(OPTIONAL_ISLETS))
AREA_INDEX = {a.name: k for k, a in enumerate(AREAS)}
LANDMASS = {  # areas that are joined; different landmasses are split by open sky (natural bridges cross it)
    'Floor_Entrance': 'Verdant_Mainland', 'Sunlit_Meadows': 'Verdant_Mainland', 'Verdant_Village': 'Verdant_Mainland',
    'Whispering_Forest': 'Verdant_Mainland',
    'Ancient_Ruins': 'Central_Highlands', 'Cloudridge_Peaks': 'Central_Highlands', 'World_Tree_Grove': 'Central_Highlands',
    'Emerald_Lake': 'Central_Highlands', 'Riverfall_Valley': 'Central_Highlands', 'Mossy_Caverns': 'Central_Highlands',
    'Lotus_Swamp': 'Lotus_Swamp',
    'Jungle_Fortress': 'Jungle_Fortress', 'Fortress_Heights': 'Jungle_Fortress', 'Beast_Cave': 'Jungle_Fortress'}
GAP = 46.0 * WORLD                        # open sky kept between two landmasses (narrowest)

# region pairs that must meet as a cliff even though their heights are close (otherwise: < SOFT_DH -> slope)
SOFT_DH = 46.0 * WORLD
FORCE_CLIFF = {frozenset(p) for p in (('Ancient_Ruins', 'World_Tree_Grove'), ('Riverfall_Valley', 'Mossy_Caverns'))}
REGIONS = (  # the five regions shown on the map: label, levels, label position (px)
    ('VERDANT FOREST', 'Lv 1-20', (250, 640)), ('WATERFALL VALLEY', 'Lv 10-35', (590, 590)),
    ('ANCIENT RUINS', 'Lv 20-50', (520, 160)), ('MYSTIC WILDS', 'Lv 25-60', (800, 110)),
    ('JUNGLE FORTRESS', 'Lv 55-70', (1235, 610)))

# peaks / hills / crags / spires / ledges: cx, cy (px), radius (studs), height, profile exponent (<1 = mesa)
FEATURES = (
    (430, 112, 95, 170, 1.2), (500, 65, 115, 240, 1.1), (585, 95, 85, 175, 1.2), (375, 175, 55, 80, 1.4),
    (635, 80, 55, 110, 1.3), (535, 160, 50, 60, 1.5),                           # Cloudridge Peaks (summit ~380)
    (905, 598, 70, 55, 0.6),                                                    # Mossy Caverns cavern hill
    (1250, 255, 40, 90, 1.0), (1300, 300, 34, 75, 1.0), (1175, 262, 30, 60, 1.0), (1295, 390, 30, 55, 1.0),
    (1150, 405, 26, 40, 1.0),                                                   # Beast Cave crags
    (1112, 520, 26, 70, 0.5), (1360, 525, 28, 80, 0.5), (1330, 655, 26, 70, 0.5), (1125, 665, 24, 60, 0.5),
    (1245, 700, 22, 55, 0.5),                                                   # Fortress Heights rim spires
    (1425, 690, 45, 40, 1.0), (1075, 735, 40, 35, 1.0), (1330, 445, 40, 30, 1.0),   # jungle knolls
    (520, 645, 40, 26, 0.25), (655, 545, 34, 36, 0.25),                         # valley ledges
    (690, 70, 40, 30, 1.0), (925, 70, 36, 26, 1.0),                             # World Tree highland knolls
    (*entrance_px(290), 24, 17, 1.1), (*entrance_px(240, -160), 15, 11, 1.2),   # rocky ridge behind the portal
    (*entrance_px(260, 180), 16, 12, 1.2), (*entrance_px(400, 60), 15, 10, 1.3),
    (150, 828, 9, 8, 1.0), (276, 896, 10, 10, 1.0),                             # knolls round the entrance plaza
)
WORLD_TREE = (800, 150)                    # px; trunk centre on the World Tree pad
ROOTS = ((-160, 230), (-115, 190), (-60, 240), (-20, 160), (25, 220), (70, 180), (120, 230), (165, 170), (205, 200))
# ravines / rifts / gorges: name, [(px, py, floor z)], width, bank width (studs)
RAVINES = (
    ('Whispering_Ravine', [(220, 330, 40), (290, 410, 38), (296, 416, 20), (445, 550, 18)], 44, 14),
    ('Ruins_Rift', [(545, 300, 84), (610, 335, 82), (690, 350, 84)], 30, 10),
)
# lakes / ponds: name, outline (px), water z, depth
LAKES = (
    ('Emerald_Lake_Water', [(842, 282), (900, 256), (980, 256), (1040, 285), (1058, 340), (1042, 410),
                            (1000, 450), (930, 462), (868, 446), (842, 400), (858, 350), (832, 312)], 97.0, 18.0),
    ('Ruins_Pond', [(705, 288), (745, 282), (770, 300), (752, 322), (712, 322)], 117.0, 4.0),
    ('Entrance_Spring_Pool', [(162, 862), (168, 859), (175, 862), (176, 868), (169, 872), (162, 870)], 10.0, 2.0),
    ('Riverfall_Pond_West', [(455, 568), (510, 560), (535, 580), (512, 600), (462, 598)], -11.0, 5.0),
    ('Riverfall_Pond_East', [(618, 628), (668, 624), (695, 642), (668, 662), (622, 658)], -11.0, 5.0),
    ('Lotus_Pond_North', [(780, 812), (860, 795), (935, 805), (950, 845), (880, 868), (800, 860)], -25.0, 3.0),
    ('Lotus_Pond_Centre', [(845, 880), (930, 872), (1000, 890), (990, 940), (905, 955), (850, 930)], -25.0, 3.0),
    ('Lotus_Pond_East', [(1010, 815), (1080, 812), (1130, 845), (1110, 900), (1040, 905), (1005, 860)], -25.0, 3.0),
    ('Lotus_Pond_West', [(740, 880), (790, 875), (812, 910), (785, 940), (745, 925)], -25.0, 3.0),
)
# river reaches (flat water, waterfall at the end): name, [(px, py)], water z, width
RIVERS = (
    ('Whispering_Stream_Upper', [(220, 330), (290, 410)], 37.0, 14),
    ('Whispering_Stream', [(296, 416), (380, 490), (447, 552)], 17.0, 16),
    ('Meadow_Brook', [(300, 612), (250, 652), (150, 702), (40, 752)], 13.0, 12),
    ('Entrance_Brook', [(163, 866), (145, 862), (128, 865), (110, 861), (90, 864), (70, 860), (48, 861)], 10.0, 4),
    ('Emerald_Spillway', [(850, 452), (790, 500), (732, 528)], 96.0, 18),
    ('Ruins_Cascade', [(612, 455), (602, 498)], 115.0, 12),
    ('Mossy_Spring', [(800, 600), (752, 592)], 68.0, 12),
    ('Riverfall_River', [(470, 575), (560, 605), (640, 640), (700, 680)], -11.0, 18),
    ('Lotus_Drain', [(995, 935), (1005, 995)], -25.0, 16),
    ('World_Tree_Falls', [(880, 215), (888, 245)], 157.0, 14),
    ('Beast_Stream', [(1150, 280), (1095, 278)], 146.0, 10),
    ('Fortress_Heights_Falls', [(1150, 565), (1100, 565)], 238.0, 14),
    ('Fortress_South_Falls', [(1245, 720), (1250, 790)], 124.0, 14),
)
# waterfalls without a river: start px, direction (deg, world), water z (None = ground at the start), width
SPRINGS = (
    ('Sky_Temple_Falls', (1215, 160), -90, 309.0, 12),
    ('Cloudridge_Falls', (400, 236), -100, None, 12),
    ('Beast_East_Falls', (1300, 330), 0, None, 10),
    ('Whispering_West_Falls', (170, 560), 200, None, 12),
    ('Fortress_East_Falls', (1420, 600), 0, None, 14),
)
# flattened pads: name, px, py, radius (1x studs), z (1x, None = keep the ground at the centre), radius scale
# (WORLD for region-sized pads, 2 for the boss arena, 1 for player-scale pads)
PADS = (
    ('Spawn', 215, 860, 64, 12, 1), ('Entrance_Portal', *entrance_px(84), 52, 12, 1),
    ('Entrance_Hatchery', *entrance_px(0, -104), 74, 12, 1), ('Entrance_Shop', *entrance_px(0, 104), 70, 12, 1), ('Village_Square', 520, 765, 70, 26, WORLD), ('Ruins_Plaza', 650, 380, 60, 118, WORLD),
    ('World_Tree_Pad', 800, 150, 80, 172, WORLD), ('Sky_Temple_Pad', 1240, 130, 56, 310, WORLD),
    ('Fortress_Arena', 1190, 600, 70, 240, 2), ('Fortress_Keep', 1300, 520, 58, 240, WORLD),
    ('Meadow_Riding_Field', 130, 690, 95, None, WORLD), ('Jungle_Clearing', 1380, 690, 48, None, WORLD),
    ('MiniBoss_1', 440, 430, 36, None, 2), ('MiniBoss_2', 970, 690, 36, None, 2), ('MiniBoss_3', 1170, 140, 28, 310, 2),
    ('Lake_Islet', 960, 330, 22, 101, WORLD),
    ('CP_1', 400, 676, 16, None, 1), ('CP_2', 560, 600, 16, None, 1), ('CP_3', 815, 455, 16, None, 1),
    ('CP_4', 1108, 292, 16, None, 1), ('CP_5', 1305, 160, 16, 310, 1), ('CP_6', 880, 700, 16, None, 1),
)
# paths: name, kind, [(px, py, z or None)] - None follows the ground. kind -> width, max grade, bank width
PATH_KINDS = {'main': (56, 0.42, 50), 'secondary': (40, 0.46, 36), 'hidden': (20, 0.55, 20)}
PATHS = (
    # main routes
    ('Entrance_Road', 'main', [(215, 860, 12), (290, 815, None), (360, 765, None)]),
    ('Village_Road', 'main', [(360, 765, None), (440, 775, None), (520, 765, 26), (620, 775, None), (675, 790, None)]),
    ('Meadow_Road', 'main', [(360, 765, None), (310, 700, None), (235, 660, None), (195, 600, None), (225, 530, None),
                             (265, 470, None)]),
    ('Valley_Road', 'main', [(360, 765, None), (400, 676, None), (455, 630, None), (500, 600, None), (560, 600, None),
                             (640, 630, None), (700, 650, None)]),
    ('Forest_Ruins_Road', 'main', [(265, 470, None), (350, 445, None), (440, 430, None), (520, 405, None),
                                   (580, 385, None), (650, 380, 118)]),
    ('Cloudridge_Road', 'main', [(265, 470, None), (200, 390, None), (225, 300, None), (295, 255, None),
                                 (360, 205, None), (470, 210, None), (600, 185, None), (700, 165, None),
                                 (800, 150, 172)]),
    ('World_Tree_Road', 'main', [(650, 380, 118), (700, 330, None), (745, 260, None), (800, 150, 172)]),
    ('Lake_Road', 'main', [(650, 380, 118), (730, 420, None), (815, 455, None)]),
    ('Mossy_Road', 'main', [(815, 455, None), (860, 520, None), (840, 640, None), (880, 700, None), (970, 690, None)]),
    ('Beast_Road', 'main', [(1055, 330, None), (1108, 292, None), (1150, 262, None), (1200, 320, None)]),
    ('Fortress_North_Road', 'main', [(1200, 320, None), (1215, 385, None), (1200, 440, None)]),
    ('Fortress_Grand_Ramp', 'main', [(1200, 440, None), (1300, 435, None), (1390, 480, None), (1412, 560, None),
                                     (1392, 632, 240), (1330, 622, 240), (1190, 600, 240)]),
    # secondary trails, shortcuts and alternate routes
    ('Village_Swamp_Road', 'secondary', [(675, 790, None), (790, 850, None), (880, 880, None)]),
    ('Lake_Loop', 'secondary', [(815, 455, None), (900, 480, None), (990, 468, None), (1045, 420, None),
                                (1055, 330, None), (1030, 270, None), (960, 245, None), (870, 255, None),
                                (825, 320, None), (815, 455, None)]),
    ('World_Tree_East_Trail', 'secondary', [(800, 150, 172), (880, 190, None), (960, 245, None)]),
    ('Mossy_Valley_Switchback', 'secondary', [(700, 650, None), (745, 600, None), (790, 640, None), (840, 640, None)]),
    ('Mossy_Swamp_Trail', 'secondary', [(970, 690, None), (1000, 770, None), (960, 840, None), (880, 880, None)]),
    ('Fortress_Canyon', 'secondary', [(970, 690, None), (1020, 650, None), (1085, 640, None), (1150, 700, None),
                                      (1240, 712, None), (1262, 660, None), (1190, 600, 240)]),
    ('Swamp_Cliff_Trail', 'secondary', [(880, 880, None), (1000, 900, None), (1110, 850, None), (1165, 800, None),
                                        (1215, 745, None), (1300, 730, None), (1385, 715, None)]),
    ('Meadow_West_Trail', 'secondary', [(235, 660, None), (110, 650, None), (60, 590, None), (130, 540, None),
                                        (195, 600, None)]),
    ('Cloudridge_Ruins_Trail', 'secondary', [(470, 210, None), (600, 250, None), (640, 320, None), (650, 380, 118)]),
    ('Whispering_Village_Trail', 'secondary', [(265, 470, None), (340, 560, None), (400, 676, None)]),
    ('Sky_Stair', 'secondary', [(1200, 320, None), (1130, 300, None), (1095, 250, None), (1125, 212, None),
                                (1195, 205, None), (1270, 213, None), (1325, 192, 310), (1300, 150, 310),
                                (1240, 130, 310)]),
    # hidden paths (not shown on the player map)
    ('Secret_Mistfall_Path', 'hidden', [(150, 450, None), (95, 445, None), (40, 440, 48)]),
    ('Secret_Overlook_Path', 'hidden', [(1420, 600, None), (1470, 600, None), (1530, 600, 150)]),
    ('Secret_Cloud_Perch_Path', 'hidden', [(950, 90, None), (1000, 75, None), (1068, 70, 190)]),
    ('Secret_Grotto_Path', 'hidden', [(540, 850, None), (550, 900, None), (555, 970, -10)]),
    ('Ruins_Undercroft_Path', 'hidden', [(560, 600, None), (600, 545, None), (615, 512, None)]),
    # entrance placeholders: a hidden brook path behind the bushes (rope bridge across), a cliffside shortcut
    ('Secret_Brook_Path', 'hidden', [(210, 859, None), (190, 852, None), (160, 850, None), (128, 857.5, None)]),
    ('Secret_Falls_Path', 'hidden', [(128, 871.5, None), (105, 878, None), (80, 876, None)]),
    ('Secret_Cliff_Path', 'hidden', [(228, 880, None), (280, 914, None), (322, 885, None), (348, 805, None)]),
)
GENTLE_RIVERS = {'Entrance_Brook'}
# pads that carry built floors (plaza, stairs, buildings): flattened again after every path / river so nothing pokes
# through, and set a hair under the floor meshes
HARD_PADS = ('Spawn', 'Entrance_Portal', 'Entrance_Hatchery', 'Entrance_Shop')


def bridge_type(name, kind):
    """how a path crosses open sky: 'rock' (natural terrain bridge) or a built wood / stone / rope bridge"""
    if name in ('Sky_Stair', 'Fortress_Grand_Ramp', 'Secret_Cloud_Perch_Path'):
        return 'rock'
    if kind == 'hidden':
        return 'rope'
    if kind == 'main':
        return 'stone' if sum(map(ord, name)) % 2 else 'wood'
    return 'wood'


CHECKPOINTS = (('Checkpoint_1_Meadows', 400, 676), ('Checkpoint_2_Riverfall', 560, 600),
               ('Checkpoint_3_Lake', 815, 455), ('Checkpoint_4_Beast', 1108, 292),
               ('Checkpoint_5_Sky_Temple', 1305, 160), ('Checkpoint_6_Mossy', 880, 700))
MINIBOSSES = (('MiniBoss_1_Forest_Guardian', 440, 430), ('MiniBoss_2_Ancient_Beast', 970, 690),
              ('MiniBoss_3_Sky_Guardian', 1170, 140))
MAIN_BOSS = ('Main_Boss_Jungle_Overlord', 1190, 600)
SPAWN = (215, 860)
EGGS = (('World_Egg_1_Beast_Crags', 1250, 405), ('World_Egg_2_Lake_Islet', 960, 330),
        ('World_Egg_3_Whispering_Ravine', 335, 465), ('World_Egg_4_Cloudridge', 560, 125),
        ('World_Egg_5_Behind_Spillway_Falls', 722, 548), ('World_Egg_6_Lotus', 1100, 940))
# caves: name, start px (inside the higher ground), direction (deg, world), mouth width
CAVES = (('Cave_Beast_Main', (1190, 330), 205, 200), ('Cave_Mossy_South', (905, 600), -80, 80),
         ('Cave_Mossy_West', (905, 600), 190, 80), ('Cave_Whispering_Hollow', (250, 330), -55, 70),
         ('Cave_Cloudridge_Ice', (500, 65), -90, 80), ('Cave_Fortress_Undergate', (1190, 600), 200, 100),
         ('Cave_World_Tree_Roots', (800, 150), -100, 90), ('Cave_Ruins_Undercroft', (615, 440), -90, 70),
         ('Cave_Entrance_Hollow', entrance_px(260), 235, 40))
# cave pairs to be joined by interior tunnels later (the heightfield has no overhangs)
CAVE_ROUTES = (('Cave_Mossy_South', 'Cave_Mossy_West'), ('Cave_Ruins_Undercroft', 'Cave_World_Tree_Roots'),
               ('Cave_Beast_Main', 'Cave_Fortress_Undergate'))
SECRETS = (('Secret_Mistfall_Isle', 40, 440), ('Secret_Lotus_Grotto', 555, 975), ('Secret_Cloud_Perch', 1068, 70),
           ('Secret_Overlook', 1530, 600), ('Islet_Treasure', 10, 1000), ('Islet_Rare_Pet', 1360, 930))
W_ = WORLD
RESERVED = (('Reserved_Verdant_Village', 520, 765, 'rect', 230 * W_, 150 * W_),
            ('Reserved_Ruins_Plaza', 650, 380, 'circle', 60 * W_, 0),
            ('Reserved_Ruins_West', 560, 340, 'circle', 40 * W_, 0), ('Reserved_Ruins_East', 760, 330, 'circle', 34 * W_, 0),
            ('Reserved_Ruins_Undercroft', 615, 470, 'circle', 60, 0),
            ('Reserved_World_Tree', 800, 150, 'circle', 80 * W_, 0), ('Reserved_Sky_Temple', 1240, 130, 'rect', 170 * W_, 90 * W_),
            ('Reserved_Fortress_Arena', 1190, 600, 'circle', 140, 0),
            ('Reserved_Fortress_Keep', 1300, 520, 'rect', 110 * W_, 110 * W_),
            ('Reserved_Entrance_Gate', 215, 860, 'circle', 60, 0))

# ---- blow the 1x layout up to world scale (player-scale sizes above stay as they are) ----
# LEVEL flattens the height differences between regions / islands (every base height, and everything tied to one:
# lakes, rivers, ravine floors, pads, path pins); peaks, crags and spires keep FEATURE_LEVEL of their height
LEVEL = 0.5
FEATURE_LEVEL = 0.75
ZL = WORLD * LEVEL
AREAS = tuple(a._replace(z=a.z * ZL, style=(a.style[0], a.style[1] * WORLD,
                                               a.style[2] if a.style[0] == 'terraced' else a.style[2] * WORLD),
                         grow=a.grow * WORLD) for a in AREAS)
FEATURES = tuple((x, y, r * WORLD, h * WORLD * FEATURE_LEVEL, e) for x, y, r, h, e in FEATURES)
ROOTS = tuple((a, l * WORLD) for a, l in ROOTS)
RAVINES = tuple((n, [(x, y, z * ZL) for x, y, z in pts], w * WORLD, b * WORLD) for n, pts, w, b in RAVINES)
LAKES = tuple((n, pts, z * ZL, d * ZL) for n, pts, z, d in LAKES)
def _chaikin_xy(pts, it=2):
    for _ in range(it):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25), (a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75)]
        out.append(pts[-1])
        pts = out
    return pts


RIVERS = tuple((n, _chaikin_xy(pts), z * ZL, w * 0.6 * WORLD) for n, pts, z, w in RIVERS)
SPRINGS = tuple((n, p, a, None if z is None else z * ZL, w * 0.6 * WORLD) for n, p, a, z, w in SPRINGS)
CAVES = tuple((n, p, a, w * WORLD / 5) for n, p, a, w in CAVES)            # widths above are given at 5x
PADS = tuple((n, x, y, r * k, None if z is None else z * ZL) for n, x, y, r, z, k in PADS)
PATHS = tuple((n, kind, [(x, y, None if z is None else z * ZL) for x, y, z in pts]) for n, kind, pts in PATHS)


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
    N('F1_Rock_Under_Strata', (0.52, 0.44, 0.38), (0.58, 0.49, 0.42), 0.9, 0.02, 0.1, 1.0)
    N('F1_Rock_Strata', (0.66, 0.58, 0.48), (0.72, 0.63, 0.52), 0.85, 0.03, 0.1, 1.0)
    N('F1_Rock_Light', (0.70, 0.66, 0.62), (0.76, 0.72, 0.68), 0.85, 0.03, 0.1, 1.0)
    N('F1_Rock_Dark_Strata', (0.30, 0.26, 0.30), (0.36, 0.31, 0.35), 0.85, 0.03, 0.1, 1.0)
    P('F1_Path_Light', (0.86, 0.70, 0.46), 0.9)
    P('F1_Path_Dark', (0.62, 0.45, 0.26), 0.9)
    N('F1_Path_Stone', (0.46, 0.43, 0.39), (0.54, 0.50, 0.45), 0.85, 0.08, 0.15, 0.4)
    P('F1_Mud', (0.36, 0.28, 0.18), 0.95)
    N('F1_Rock_Under_Dark', (0.17, 0.15, 0.22), (0.22, 0.19, 0.22), 0.9, 0.02, 0.1, 1.0)
    N('F1_Ruins_Stone', (0.70, 0.66, 0.56), (0.76, 0.72, 0.62), 0.85, 0.03, 0.1, 1.0)
    P('F1_Snow', (0.93, 0.95, 1.0), 0.7)
    P('F1_Water', (0.10, 0.52, 0.95), 0.08, emit=0.15)
    P('F1_Water_Swamp', (0.16, 0.48, 0.36), 0.15, emit=0.1)
    P('F1_Waterfall', (0.72, 0.90, 1.0), 0.2, emit=0.6)
    P('F1_Cloud', (0.97, 0.98, 1.0), 0.95, emit=0.25)
    P('F1_Cave', (0.03, 0.03, 0.05), 1.0)
    P('F1_Tree_Bark', (0.36, 0.22, 0.12), 0.9)
    N('F1_Tree_Canopy', (0.10, 0.50, 0.16), (0.16, 0.60, 0.20), 0.85, 0.03, 0.1, 1.0)
    P('F1_Blockout', (0.62, 0.58, 0.66), 0.8)
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


def field_noise(X, Y, seed, wl=90.0, octaves=4):
    rng = np.random.default_rng(seed + 1000)
    out = np.zeros_like(X)
    for k, f in enumerate((1.0, 0.55, 0.3, 0.18)[:octaves]):
        a = rng.uniform(0, TAU)
        w = wl * f
        out += (0.6 ** k) * np.sin((X * math.cos(a) + Y * math.sin(a)) / w * TAU + rng.uniform(0, TAU))
    return out / 1.6


def style_height(a, X, Y):
    """an area's ground: base height + its terrain style + subtle small-scale relief (hummocks, dips, shelves)"""
    kind = a.style[0]
    k = 0.35 if kind == 'flat' else 1.0
    micro = k * WORLD * (0.9 * field_noise(X, Y, a.seed + 50, 26 * WORLD, 3)
                         + 0.45 * field_noise(X, Y, a.seed + 51, 11 * WORLD, 2))
    return _style_height(a, X, Y) + micro


def _style_height(a, X, Y):
    kind, amp, wl = a.style
    n = field_noise(X, Y, a.seed, wl if kind != 'terraced' else 160.0 * WORLD, 2)     # broad shapes: ride-able
    if kind == 'flat' or kind == 'rolling':
        return a.z + amp * n
    if kind == 'hills':                                        # rolling hills with a second, shorter wave
        return a.z + amp * (n + 0.35 * field_noise(X, Y, a.seed + 7, wl * 0.6, 2))
    if kind == 'terraced':                                     # massive broken stone foundations: raised slabs
        rng = random.Random(a.seed)
        xs = [px(*p) for p in a.poly]
        x0, x1 = min(p[0] for p in xs), max(p[0] for p in xs); y0, y1 = min(p[1] for p in xs), max(p[1] for p in xs)
        h = a.z + 4.0 * WORLD * n
        for _ in range(int(wl)):
            cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
            hw, hh, ang = rng.uniform(18, 55) * WORLD, rng.uniform(14, 40) * WORLD, rng.uniform(0, math.pi)
            u = (X - cx) * math.cos(ang) + (Y - cy) * math.sin(ang)
            v = -(X - cx) * math.sin(ang) + (Y - cy) * math.cos(ang)
            inside = (np.abs(u) < hw) & (np.abs(v) < hh)
            h = np.where(inside, np.maximum(h, a.z + rng.choice((8, 12, 16, 24, 32)) * amp / 40), h)
        return h
    if kind == 'ridged':                                       # mountain ridges
        return a.z + amp * (1 - np.abs(n)) ** 2 - amp * 0.3
    if kind == 'crags':                                        # knobbly crags and hollows
        return a.z + amp * (np.maximum(n, -0.3) ** 2 * np.sign(n) + 0.25 * field_noise(X, Y, a.seed + 3, wl * 0.6, 2))
    raise ValueError(kind)


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


def smax(a, b, k):
    """smooth maximum: fills gaps narrower than ~k/2 between two shapes"""
    h = np.maximum(k - np.abs(a - b), 0.0)
    return np.maximum(a, b) + h * h / (4 * k)


def organic(pts, w, seed):
    """waypoints (world x, y, z|None) -> dense organic polyline: every segment bows sideways a little, corners are
    rounded; waypoints keep their position (junctions stay joined). Returns [(x, y)], pinned {index: z}."""
    rng = random.Random(seed)
    out, pins = [], {}
    for k, ((ax, ay, az), (bx, by, bz)) in enumerate(zip(pts, pts[1:])):
        L = math.hypot(bx - ax, by - ay)
        n = max(2, int(L / S))
        nx, ny = -(by - ay) / (L or 1), (bx - ax) / (L or 1)
        bow = rng.choice((-1, 1)) * rng.uniform(0.35, 1.0) * min(0.12 * L, 6 * w)
        wig = rng.uniform(0.0, 0.25) * min(0.12 * L, 6 * w)
        ph = rng.uniform(0, TAU)
        if k == 0 and az is not None:
            pins[0] = az
        for i in range(n):
            u = i / n
            if k and i == 0:
                continue
            o = bow * math.sin(math.pi * u) + wig * math.sin(math.pi * u) * math.sin(3 * math.pi * u + ph)
            out.append((ax + (bx - ax) * u + nx * o, ay + (by - ay) * u + ny * o))
        out.append((bx, by))
        if bz is not None:
            pins[len(out) - 1] = bz
    xy = np.array(out)
    keep = np.zeros(len(xy), dtype=bool); keep[0] = keep[-1] = True
    for _ in range(3):                                         # round the corners (ends fixed)
        sm = xy.copy()
        sm[1:-1] = (xy[:-2] + 2 * xy[1:-1] + xy[2:]) / 4
        xy = np.where(keep[:, None], xy, sm)
    return [tuple(p) for p in xy], pins


# ---------------------------------------------------------------- terrain ---
class Terrain:
    def __init__(self):
        n = int(2 * EXT / S) + 1
        self.n = n
        g = np.linspace(-EXT, EXT, n)
        self.X, self.Y = np.meshgrid(g, g, indexing='ij')
        X, Y = self.X, self.Y
        K = len(AREAS)
        sd = np.empty((K, n, n)); hs = np.empty((K, n, n)); real = np.empty((K, n, n))
        for k, a in enumerate(AREAS):
            d = poly_sd(X, Y, [px(*p) for p in a.poly]) + a.irr * 9.0 * WORLD * field_noise(X, Y, a.seed, 45.0 * WORLD) \
                + a.grow
            real[k] = d
            if a.kind == 'inner':                              # sits inside its parent: always wins where inside
                d = np.where(d > 0, d + 5000.0, d - 5000.0)
            sd[k] = d
            hs[k] = style_height(a, X, Y)
        land_k = [k for k, a in enumerate(AREAS) if a.kind != 'float']
        float_k = [k for k, a in enumerate(AREAS) if a.kind == 'float']
        # --- landmasses: smooth union of the grown outlines of each landmass (inner plateaus count with their real
        # distance); between two landmasses a channel of open sky at least GAP wide is kept
        masses = sorted({LANDMASS[AREAS[k].name] for k in land_k})
        Lm = np.full((len(masses), n, n), -1e9)
        for k in land_k:
            g = masses.index(LANDMASS[AREAS[k].name])
            Lm[g] = smax(Lm[g], real[k], 50.0 * WORLD)
        top2 = -np.sort(-Lm, axis=0)[:2]
        gap = GAP * (1 + 0.35 * field_noise(X, Y, 99, 120 * WORLD))
        Lc = np.minimum(top2[0], (top2[0] - top2[1] - gap) / 2)
        mass_of = np.array([masses.index(LANDMASS[AREAS[k].name]) for k in land_k])
        # --- heights: owner = best area, blended with the runner-up -> slope (similar heights) or cliff
        sdl = sd[land_k]
        order = np.argsort(-sdl, axis=0)
        ia, ib = order[0], order[1]
        sa = np.take_along_axis(sdl, ia[None], 0)[0]; sb = np.take_along_axis(sdl, ib[None], 0)[0]
        ha = np.take_along_axis(hs[land_k], ia[None], 0)[0]; hb = np.take_along_axis(hs[land_k], ib[None], 0)[0]
        zb = np.array([AREAS[k].z for k in land_k])
        cliff = np.abs(zb[ia] - zb[ib]) >= SOFT_DH
        for p in FORCE_CLIFF:
            u, v = (land_k.index(AREA_INDEX[q]) for q in p)
            cliff |= ((ia == u) & (ib == v)) | ((ia == v) & (ib == u))
        cliff |= mass_of[ia] != mass_of[ib]                    # never blend across open sky
        W = np.where(cliff, 2 * S, 130.0 * WORLD)
        wt = 0.5 * (1 - smooth(0.0, 1.0, np.minimum(sa - sb, 1e6) / W))
        H = ha + (hb - ha) * wt
        own = np.array(land_k)[ia]
        L = Lc
        for k in float_k:                                      # floating islands keep their own outline and height
            m = sd[k] > 0
            H = np.where(m, hs[k], H); own = np.where(m, k, own)
            L = np.maximum(L, sd[k])
        land0 = L > 0
        self.ia_cliff = cliff
        # --- peaks, crags, spires, ledges
        for cx, cy, r, h, e in FEATURES:
            wx, wy = px(cx, cy)
            d = np.hypot(X - wx, Y - wy)
            H = H + np.where(land0, h * np.clip(1 - d / r, 0, 1) ** e, 0)
        # --- the World Tree's roots: ridges spreading from the trunk across the highland
        tx, ty = px(*WORLD_TREE)
        for ang, length in ROOTS:
            a = math.radians(ang)
            b = (tx + math.cos(a) * length, ty + math.sin(a) * length)
            d, t = seg_dist(X, Y, (tx, ty), b)
            w = (30 - 18 * t) * WORLD
            H = H + np.where(land0, 26 * WORLD * (1 - t) ** 0.8 * np.clip(1 - (d / w) ** 2, 0, 1), 0)
        # --- ravines, rifts and gorges (steep banks)
        self.ravine = np.full((n, n), 1e9)
        for name, pts, w, bank in RAVINES:
            for (ax, ay, az), (bx, by, bz) in zip(pts, pts[1:]):
                d, t = seg_dist(X, Y, px(ax, ay), px(bx, by))
                tgt = az + (bz - az) * t + smooth(w / 2, w / 2 + bank, d) * 400 * WORLD
                H = np.where(land0 & (d < w / 2 + bank), np.minimum(H, tgt), H)
                self.ravine = np.minimum(self.ravine, d - w / 2)
        # --- lakes and ponds (bowl + soft banks)
        self.lake_f = np.full((n, n), 9.0)
        self.lake_z = np.zeros((n, n))
        self.lake_i = np.zeros((n, n), dtype=int)
        for li, (name, poly, zw, depth) in enumerate(LAKES):
            d = poly_sd(X, Y, [px(*p) for p in poly])
            rr = max(12.0 * WORLD, float(d.max()))
            g_ = 1.0 - d / rr
            tgt = np.where(g_ < 1, zw - depth * (1 - g_ ** 2) - 0.6, zw - 0.6 + (g_ - 1) / 0.35 * (H - zw + 0.6))
            m = (g_ < 1.35) & land0
            H = np.where(m, np.minimum(H, tgt), H)
            closer = g_ < self.lake_f
            self.lake_f = np.where(closer, g_, self.lake_f)
            self.lake_z = np.where(closer, zw, self.lake_z)
            self.lake_i = np.where(closer, li, self.lake_i)
        # --- river channels
        self.river_d = np.full((n, n), 1e9)
        for name, pts, zw, w in RIVERS:
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                d, t = seg_dist(X, Y, px(ax, ay), px(bx, by))
                self.river_d = np.minimum(self.river_d, d - w / 2)
                b = 7 * WORLD
                tgt = zw - 2.5 * WORLD + smooth(w / 2, w / 2 + b, d) * 60 * WORLD
                if name in GENTLE_RIVERS:                      # shallow brook with low grassy banks
                    tgt = zw - 0.8 * WORLD + smooth(w / 2, w / 2 + b, d) * 3.5 * WORLD
                H = np.where((d < w / 2 + b) & land0, np.minimum(H, tgt), H)
        # --- flat pads
        self.H, self.land = H, land0
        for name, cx, cy, r, z in PADS:
            wx, wy = px(cx, cy)
            if z is None:
                z = self.bilinear(wx, wy)
            d = np.hypot(X - wx, Y - wy)
            b = max(16.0, 0.3 * r)
            t = smooth(r, r + b, d)
            Hb = np.where(H < -1e6, z, H)
            H = np.where((d < r + b) & (L > -20), z * (1 - t) + Hb * t, H)
            L = np.maximum(L, np.where(L > -20, r + 2 - d, -1e9))
        self.H = H; self.land = L > 0
        # --- paths: profiles follow the ground (grade-limited), then cut / fill the corridor
        best = np.full((n, n), 1e9)
        pz = np.zeros((n, n)); bank = np.full((n, n), 16.0); pw = np.zeros((n, n))
        self.paths, self.path_grades, self.bridge_spans = [], {}, []
        island0 = L > 0
        for k, (name, kind, pts) in enumerate(PATHS):
            w, g, bw = PATH_KINDS[kind]
            wp = [(*px(x, y), z) for x, y, z in pts]
            xy, pins = organic(wp, w, 100 + k)
            zs = self.profile(xy, pins, g)
            self.paths.append((name, kind, w, [(x, y, z) for (x, y), z in zip(xy, zs)]))
            seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(xy, xy[1:])]
            self.path_grades[name] = max(abs(b - a) / (s or 1) for a, b, s in zip(zs, zs[1:], seg))
            # where the path crosses open sky: a built bridge (no terrain) unless it is a natural rock bridge
            ii = np.clip(np.rint((np.array(xy) + EXT) / S).astype(int), 0, n - 1)
            void = ~island0[ii[:, 0], ii[:, 1]]
            btype = bridge_type(name, kind)
            skip = np.zeros(len(xy), dtype=bool)
            if btype != 'rock':
                m = 0
                while m < len(xy):
                    if not void[m]:
                        m += 1
                        continue
                    e = m
                    while e + 1 < len(xy) and void[e + 1]:
                        e += 1
                    if e - m >= 1:
                        skip[m:e + 1] = True
                        a_, b_ = max(m - 3, 0), min(e + 3, len(xy) - 1)
                        self.bridge_spans.append((name, btype, w, [(xy[q][0], xy[q][1], zs[q]) for q in range(a_, b_ + 1)]))
                    m = e + 1
            for q, ((ax, ay), (bx, by), az, bz) in enumerate(zip(xy, xy[1:], zs, zs[1:])):
                if skip[q] and skip[q + 1]:
                    continue
                x0 = int((min(ax, bx) - w - bw + EXT) / S) - 1; x1 = int((max(ax, bx) + w + bw + EXT) / S) + 2
                y0 = int((min(ay, by) - w - bw + EXT) / S) - 1; y1 = int((max(ay, by) + w + bw + EXT) / S) + 2
                sl = (slice(max(x0, 0), min(x1, n)), slice(max(y0, 0), min(y1, n)))
                d, t = seg_dist(X[sl], Y[sl], (ax, ay), (bx, by))
                e = d - w / 2
                m = e < best[sl]
                best[sl] = np.where(m, e, best[sl])
                pz[sl] = np.where(m, az + (bz - az) * t, pz[sl])
                bank[sl] = np.where(m, bw, bank[sl])
                pw[sl] = np.where(m, w, pw[sl])
        island = L > 0
        t = smooth(0, 1, best / bank)
        Hp = np.where(island, pz * (1 - t) + H * t, pz)
        H = np.where(best < bank, Hp, H)
        L = np.maximum(L, 2.0 - best)
        self.path_e = best
        self.path_w = pw
        self.H, self.L = H, L
        self.land = L > 0
        own = np.where(self.land & ~island, K, own)            # path-only cells = natural bridges
        self.own = own
        for name, cx, cy, r, z in PADS:                        # built floors win over paths and rivers
            if name in HARD_PADS:
                wx, wy = px(cx, cy)
                self.H = H = np.where(np.hypot(X - wx, Y - wy) < r, z - 0.25, H)
        gx, gy = np.gradient(H, S)
        self.slope = np.where(self.land, np.hypot(gx, gy), 9.0)
        self.var = field_noise(X, Y, 555, 30 * WORLD, 3)      # material variation (path dirt / stone, strata)
        ex, ey = px(*ENTRANCE_SPAWN_PX)
        self.entr_d = np.hypot(X - ex, Y - ey)                 # distance from the entrance plaza
        self._underside()
        self._snap_edges()

    def bilinear(self, wx, wy):
        """ground height at a world point (NaN over the void)"""
        fi = (wx + EXT) / S; fj = (wy + EXT) / S
        i = min(max(int(fi), 0), self.n - 2); j = min(max(int(fj), 0), self.n - 2)
        u, v = fi - i, fj - j
        c = self.H[i:i + 2, j:j + 2]; m = self.land[i:i + 2, j:j + 2]
        if not m.all():
            return float(c[m].mean()) if m.any() else float('nan')
        return float(c[0, 0] * (1 - u) * (1 - v) + c[1, 0] * u * (1 - v) + c[0, 1] * (1 - u) * v + c[1, 1] * u * v)

    def profile(self, xy, pins, g):
        """path heights: the ground, smoothed, gaps (open sky) bridged, pinned points held, grade <= g"""
        z = np.array([self.bilinear(x, y) for x, y in xy])
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(np.array(xy), axis=0).T))])
        ok = ~np.isnan(z)
        for i, v in pins.items():
            z[i] = v; ok[i] = True
        z = np.interp(s, s[ok], z[ok])
        k = 20                                                 # ~240-stud moving average
        zp = np.pad(z, k, mode='edge')
        z = np.convolve(zp, np.ones(2 * k + 1) / (2 * k + 1), mode='same')[k:-k]
        for i, v in pins.items():
            z[i] = v
        for _ in range(3):
            for i in range(1, len(z)):
                if i not in pins:
                    ds = s[i] - s[i - 1]
                    z[i] = min(max(z[i], z[i - 1] - g * ds), z[i - 1] + g * ds)
            for i in range(len(z) - 2, -1, -1):
                if i not in pins:
                    ds = s[i + 1] - s[i]
                    z[i] = min(max(z[i], z[i + 1] - g * ds), z[i + 1] + g * ds)
        return [float(v) for v in z]

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
        self.edge_d = np.where(self.land, d, 0.0)
        Hs = np.where(self.land, self.H, 0.0)
        for _ in range(6):                                          # blur the top for a calm underside
            Hs = (Hs + np.roll(Hs, 1, 0) + np.roll(Hs, -1, 0) + np.roll(Hs, 1, 1) + np.roll(Hs, -1, 1)) / 5
        dd = np.minimum(d, 400 * WORLD)
        W_ = WORLD
        zu = Hs - 40 * W_ - np.minimum(dd, 70 * W_) * 1.5 - np.maximum(dd - 70 * W_, 0) * 0.9 \
            + 10 * W_ * field_noise(self.X, self.Y, 77, 60 * W_) + 5 * W_ * field_noise(self.X, self.Y, 78, 16 * W_, 3)
        zu = np.maximum(zu, -560 * W_)
        self.zu = np.minimum(zu, self.H - 36 * W_)

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
        gn = np.sqrt(g2)
        self.NX = np.where(edge, -gx / gn, 0.0)                # outward rim normal (cliff layering, dressing)
        self.NY = np.where(edge, -gy / gn, 0.0)

    def quad_material(self, i, j, area):
        H = self.H
        hs = (H[i, j], H[i + 1, j], H[i, j + 1], H[i + 1, j + 1])
        slope = max(abs(H[i + 1, j] - H[i, j]), abs(H[i, j + 1] - H[i, j]), abs(H[i + 1, j + 1] - H[i, j + 1]),
                    abs(H[i + 1, j + 1] - H[i + 1, j])) / S
        bridge = area >= len(AREAS)
        a = None if bridge else AREAS[area]
        dark = a is not None and a.dark
        v = self.var[i, j]
        zmax = max(hs)
        if slope > 1.05:                                       # cliffs: layered strata bands
            if a is not None and a.name == 'Ancient_Ruins':
                return 'F1_Ruins_Stone'
            band = int((sum(hs) / 4 + 18 * WORLD * v) // (5 * WORLD)) % 3
            if dark:
                return 'F1_Rock_Dark_Strata' if band == 1 else 'F1_Rock_Dark'
            return 'F1_Rock_Strata' if band == 1 else 'F1_Rock_Light' if band == 2 and v > 0.2 else 'F1_Rock'
        if self.path_e[i, j] < -1.5 and self.path_e[i + 1, j + 1] < -1.5 and self.path_w[i, j] > 30:   # (hidden
            # paths stay grass: they are meant to be found, not seen)
            p_stone = min(1.0, max(0.0, 1 - (self.entr_d[i, j] - 250) / 650)) if self.path_w[i, j] >= 50 else 0.0
            if (v + 1) / 2 < p_stone:
                return 'F1_Path_Stone'
            stony = a is not None and (a.biome in (AR, JF) or a.name == 'Verdant_Village')
            if stony and v > (0.05 if a.biome in (AR, JF) else 0.35):
                return 'F1_Path_Stone'
            return 'F1_Path_Light' if v > 0.4 else 'F1_Path_Dark' if v < -0.45 else 'F1_Path'
        if bridge:
            return 'F1_Rock'
        swampy = a.name in ('Lotus_Swamp', 'Secret_Lotus_Grotto')
        if self.lake_f[i, j] < 1.0 and zmax < self.lake_z[i, j] - 0.4:
            return 'F1_Lakebed'
        if self.lake_f[i, j] < 1.3 and zmax < self.lake_z[i, j] + 1.6 * WORLD:
            return 'F1_Mud' if swampy else 'F1_Sand'
        if a.name == 'Cloudridge_Peaks' and (zmax > 200 * WORLD or (zmax > 160 * WORLD and v > 0.25 and slope < 0.5)):
            return 'F1_Snow'
        if a.name == 'Cloudridge_Peaks' and slope > 0.7:
            return 'F1_Rock'
        if slope > 0.8:
            return 'F1_Rock_Dark' if dark else 'F1_Rock'
        if slope > 0.55 and v > 0.3:                           # exposed rock on the steeper hillsides
            return 'F1_Rock_Dark' if dark else 'F1_Rock_Light'
        if swampy:
            return 'F1_Swamp'
        return GRASS[a.biome]


def strata_offset(x, y, z):
    """how far a cliff band edge juts out (+) or steps back (-), studs"""
    h = math.sin(x * 0.0123 + z * 0.031) + math.sin(y * 0.0171 - z * 0.023) + 0.6 * math.sin((x + y) * 0.041)
    return WORLD * (0.55 * h + 0.2 * math.sin(z * 0.17))


def thin_underside(ob, ratio=0.2):
    """the rock underside is only seen from afar: decimate it, but keep its rim (shared with the cliff walls) exact"""
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    rim = {v.index for e in bm.edges if len(e.link_faces) < 2 for v in e.verts}
    bm.free()
    vg = ob.vertex_groups.new(name='decimate')
    vg.add(range(len(me.vertices)), 1.0, 'REPLACE')
    vg.add(list(rim), 0.0, 'REPLACE')
    m = ob.modifiers.new('Thin', 'DECIMATE')
    m.ratio = ratio; m.vertex_group = 'decimate'; m.vertex_group_factor = 1000.0
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.remove(m); ob.vertex_groups.remove(vg)
    ob.data = me2
    bpy.data.meshes.remove(me)
    me2.name = ob.name
    return ob


def build_terrain(T):
    """one Top / Cliffs / Underside mesh per area"""
    n = T.n
    quad = T.quad
    # quad owner = owner of its highest corner (cliff faces belong to the upper area)
    stack = np.stack([T.own[:-1, :-1], T.own[1:, :-1], T.own[:-1, 1:], T.own[1:, 1:]])
    hst = np.stack([T.H[:-1, :-1], T.H[1:, :-1], T.H[:-1, 1:], T.H[1:, 1:]])
    qown = np.take_along_axis(stack, hst.argmax(0)[None], 0)[0]
    names = [a.name for a in AREAS] + ['Natural_Bridges']
    biome_of = [a.biome for a in AREAS] + ['NATURAL_BRIDGES']
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

            dark = area < len(AREAS) and AREAS[area].dark
            for i, j in cells:
                ring = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                if part == 'Top':
                    faces.append([V(*c) for c in ring])
                    mats.append(M(T.quad_material(i, j, area)))
                elif part == 'Underside':
                    faces.append([V(*c, True) for c in ring[::-1]])
                    zc = float(T.zu[i, j])
                    strata = int((zc + 8 * WORLD * T.var[i, j]) // (9.0 * WORLD)) % 2
                    mats.append(M('F1_Rock_Under_Dark' if dark else ('F1_Rock_Under_Strata' if strata else
                                                                     'F1_Rock_Under')))
                else:
                    for (a, b), (ni, nj) in zip(zip(ring, ring[1:] + ring[:1]),
                                                ((i, j - 1), (i + 1, j), (i, j + 1), (i - 1, j))):
                        if 0 <= ni < n - 1 and 0 <= nj < n - 1 and quad[ni, nj]:
                            continue
                        # the wall is cut into rock strata (~60-stud bands, also keeps every face small for
                        # Roblox); each band edge juts out or steps back a little -> layered, irregular cliffs
                        ta, ba, tb, bb = verts[V(*a)], verts[V(*a, True)], verts[V(*b)], verts[V(*b, True)]
                        k = max(1, math.ceil(max(ta[2] - ba[2], tb[2] - bb[2]) / (6.0 * WORLD)))
                        col_a, col_b = [V(*a)], [V(*b)]
                        for m in range(1, k):
                            f = m / k
                            for side, (ci, cj), t_, b_ in ((col_a, a, ta, ba), (col_b, b, tb, bb)):
                                q = [t_[c] + (b_[c] - t_[c]) * f for c in range(3)]
                                o = strata_offset(q[0], q[1], q[2])
                                q[0] += T.NX[ci, cj] * o; q[1] += T.NY[ci, cj] * o
                                verts.append(tuple(q))
                                side.append(len(verts) - 1)
                        col_a.append(V(*a, True)); col_b.append(V(*b, True))
                        for m in range(k):
                            faces.append([col_a[m], col_a[m + 1], col_b[m + 1], col_b[m]])
                            zc = (ta[2] + tb[2]) / 2 - ((ta[2] - ba[2]) + (tb[2] - bb[2])) / 2 * (m + 0.5) / k
                            band = int(zc // (6.0 * WORLD)) % 3
                            mats.append(M(('F1_Rock_Dark', 'F1_Rock_Dark_Strata', 'F1_Rock_Dark')[band] if dark else
                                          ('F1_Rock', 'F1_Rock_Strata', 'F1_Rock_Light')[band]))
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
            if part == 'Underside' and names[area] != 'Natural_Bridges':
                ob = thin_underside(ob)
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
    for _ in range(1500):
        q2 = q + d * (S / 2)
        h, land = T.sample(q2.x, q2.y)
        if not land or h < zw - 20:
            break
        q = q2
    else:
        return None
    hb, landb = T.sample(*(q + d * 12 * WORLD))
    zb = hb + 0.2 if landb and hb < zw - 20 else CLOUD_Z + 10
    top = zw + 0.3
    side = Vector((-d.y, d.x)) * (w / 2)
    c = q + d * 4.0
    bm = p.bm
    n = max(2, int((top - zb) / 30))
    rows = []
    for k in range(n + 1):
        z = top - (top - zb) * k / n
        bulge = d * (6.0 * math.sin(math.pi * k / n) + 14.0 * k / n)
        rows.append((bm.verts.new((c.x + side.x + bulge.x, c.y + side.y + bulge.y, z)),
                     bm.verts.new((c.x - side.x + bulge.x, c.y - side.y + bulge.y, z))))
    for (a0, b0), (a1, b1) in zip(rows, rows[1:]):
        f = bm.faces.new((a0, b0, b1, a1)); f.material_index = p.mi('F1_Waterfall')
    if landb and zb > CLOUD_Z + 20:                              # splash pool
        p.cyl(Vector((c.x + d.x * 20, c.y + d.y * 20, zb + 0.15)), w * 0.75, 0.3, 'F1_Waterfall', 16)
    falls.append(dict(name=name, top=round(top, 1), bottom=round(zb, 1), x=round(c.x, 1), y=round(c.y, 1),
                      width=round(w, 1), dir=(round(d.x, 3), round(d.y, 3))))
    return q


def auto_cascades(T, count=16):
    """small extra waterfalls spilling over island rims (well apart, not near paths or pads)"""
    rng = np.random.default_rng(91)
    cand = T.land & (T.edge_d > 2.5 * S) & (T.edge_d < 4.5 * S) & (T.slope < 0.3) & (T.path_e > 80) \
        & (T.own < len(AREAS)) & (T.lake_f > 1.5) & (T.river_d > 60)
    ii, jj = np.nonzero(cand)
    out, used = [], []
    for t in rng.permutation(ii.size):
        i, j = ii[t], jj[t]
        x, y = float(T.X[i, j]), float(T.Y[i, j])
        if any(math.hypot(x - u, y - v) < 1600 for u, v in used):
            continue
        # outward direction: towards the nearest open sky (rim normal of the closest edge cell)
        win = (slice(max(i - 6, 0), i + 7), slice(max(j - 6, 0), j + 7))
        nx, ny = T.NX[win], T.NY[win]
        mag = np.hypot(nx, ny)
        if not (mag > 0).any():
            continue
        k = np.argmax(mag)
        ang = math.degrees(math.atan2(ny.ravel()[k], nx.ravel()[k]))
        sheet = (x / (MAP_SCALE * WORLD) + MAP_CX, MAP_CY - y / (MAP_SCALE * WORLD))    # back to sheet pixels
        out.append((f'Cliff_Cascade_{len(out) + 1}', sheet, ang,
                    float(T.H[i, j]) - 0.5, float(rng.uniform(2.5, 5.0) * WORLD)))
        used.append((x, y))
        if len(out) >= count:
            break
    return tuple(out)


def build_water(T):
    coll('WATER', ROOT)
    falls = []
    rv = Part('F1_Rivers', coll('Rivers', 'WATER').name)
    wf = Part('F1_Waterfalls', coll('Waterfalls', 'WATER').name)
    for name, pts, zw, w in RIVERS:
        wp = [(*px(x, y), zw) for x, y in pts]
        ribbon(rv, densify(wp, 24.0), w + 1.0, 'F1_Water')
        (ax, ay, _), (bx, by, _) = wp[-2], wp[-1]
        ang = math.degrees(math.atan2(by - ay, bx - ax))
        waterfall(wf, T, (bx, by), ang, zw, w, name + '_Falls', falls)
    for name, (sx, sy), ang, zw, w in SPRINGS + auto_cascades(T):
        wx, wy = px(sx, sy)
        if zw is None:
            zw = T.sample(wx, wy)[0] - 0.5
        waterfall(wf, T, (wx, wy), ang, zw, w, name, falls)
    rv.finish(); wf.finish()
    # lake surfaces on the terrain grid (edges tucked under the banks): small faces that split cleanly for Roblox
    lk = Part('F1_Lakes', coll('Lakes', 'WATER').name)
    wet = (T.lake_f < 1.12) & T.land
    q = wet[:-1, :-1] | wet[1:, :-1] | wet[:-1, 1:] | wet[1:, 1:]
    vmap = {}

    def LV(i, j, z):
        if (i, j, z) not in vmap:
            vmap[(i, j, z)] = lk.bm.verts.new((float(T.X[i, j]), float(T.Y[i, j]), z))
        return vmap[(i, j, z)]
    for i, j in np.argwhere(q):
        li = int(T.lake_i[i, j]); zw = LAKES[li][2]
        mat = 'F1_Water_Swamp' if LAKES[li][0].startswith('Lotus') else 'F1_Water'
        f = lk.bm.faces.new([LV(i, j, zw), LV(i + 1, j, zw), LV(i + 1, j + 1, zw), LV(i, j + 1, zw)])
        f.material_index = lk.mi(mat)
    lk.finish()
    return falls


# ---------------------------------------------------------------- blockouts --
def ground(T, x, y):
    return T.sample(*px(x, y))[0]


def build_landmarks(T):
    """landmark silhouettes so each region reads from a distance (environment hints, not final models)"""
    c = coll('Landmarks', 'LANDMARK_BLOCKOUTS').name
    rnd = random.Random(11)
    W_ = WORLD
    # the World Tree: hub-style flared trunk and limbs (its leaf-cluster canopy and roots are scatter, Landmarks)
    tx, ty = px(*WORLD_TREE)
    z0 = ground(T, *WORLD_TREE)
    # (one object per piece: each stays under Roblox's 2,048-stud MeshPart limit)
    for k, (r0, r1, za, zb) in enumerate(((70, 46, -6, 36), (46, 38, 36, 150), (38, 30, 150, 250))):
        p = Part(f'Landmark_World_Tree_Trunk_{k + 1}', c)
        p.cyl((tx, ty, z0 + (za + zb) / 2 * W_), r0 * W_, (zb - za) * W_, 'Trunk', 24, r2=r1 * W_)
        p.finish()
    p = Part('Landmark_World_Tree_Limbs', c)
    for k in range(7):
        a = TAU * k / 7 + 0.3
        tip = Vector((tx + math.cos(a) * 120 * W_, ty + math.sin(a) * 120 * W_, z0 + (290 + rnd.uniform(-20, 20)) * W_))
        p.beam(Vector((tx, ty, z0 + (200 + k * 7) * W_)), tip, 16 * W_, 16 * W_, 'Trunk')
    p.finish()
    # Jungle Fortress: a distant silhouette in the reserved keep footprint - curtain walls, corner towers and a
    # stepped keep with glowing windows (massing only; the real fortress comes in its own pass)
    kx, ky = px(1300, 520)
    kz = ground(T, 1300, 520)
    P = lambda x, y, z: (kx + x * W_, ky + y * W_, kz + z * W_)

    def merlons(p, half, z, step=6.0):
        n = int(2 * half / step)
        for m in range(n + 1):
            t = -half + 2 * half * m / n
            for x, y in ((t, -half), (t, half), (-half, t), (half, t)):
                if m % 2 == 0:
                    p.box(P(x, y, z + 1.5), (2.6 * W_, 2.6 * W_, 3 * W_), 'Fortress_Stone')
    for k, (half, z0_, h) in enumerate(((35, 0, 22), (25, 22, 20), (15, 42, 20))):
        p = Part(f'Landmark_Fortress_Keep_Tier_{k + 1}', c)
        p.box(P(0, 0, z0_ + h / 2), (2 * half * W_, 2 * half * W_, h * W_), 'Fortress_Stone')
        merlons(p, half, z0_ + h)
        for sd in (-1, 1):                                     # glowing window slits
            for m in range(-2, 3):
                p.box(P(m * half / 3, sd * (half + 0.2), z0_ + h * 0.55), (2 * W_, 0.6 * W_, h * 0.4 * W_), 'Fortress_Glow')
                p.box(P(sd * (half + 0.2), m * half / 3, z0_ + h * 0.55), (0.6 * W_, 2 * W_, h * 0.4 * W_), 'Fortress_Glow')
        if k == 2:
            p.cone(P(0, 0, z0_ + h), 13 * W_, 26 * W_, 'Fortress_Roof', 4)
        p.finish()
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = Part(f'Landmark_Fortress_Tower_{"WE"[sx > 0]}{"SN"[sy > 0]}', c)
            p.cyl(P(sx * 50, sy * 50, 30), 9 * W_, 60 * W_, 'Fortress_Stone', 12)
            p.cyl(P(sx * 50, sy * 50, 61), 10.5 * W_, 2 * W_, 'Fortress_Stone', 12)
            p.cone(P(sx * 50, sy * 50, 62), 11 * W_, 24 * W_, 'Fortress_Roof', 12)
            p.box(P(sx * 50, sy * 50 - 9.1 * sy, 40), (2 * W_, 0.6 * W_, 6 * W_), 'Fortress_Glow')
            p.finish()
    for k, (x0, y0, x1, y1) in enumerate(((-50, -50, -6, -50), (6, -50, 50, -50), (-50, 50, 50, 50),
                                          (-50, -50, -50, 50), (50, -50, 50, 50))):
        p = Part(f'Landmark_Fortress_Wall_{k + 1}', c)                 # (gate gap on the south side)
        a, b = Vector(P(x0, y0, 9)), Vector(P(x1, y1, 9))
        p.beam(a, b, 5 * W_, 18 * W_, 'Fortress_Stone')
        L = (b - a).length / W_
        for m in range(int(L / 6) + 1):
            q = a.lerp(b, m * 6 / max(L, 1)) + Vector((0, 0, 10.5 * W_))
            p.box(q, (2.6 * W_, 6 * W_, 3 * W_), 'Fortress_Stone')
        p.finish()
    # Ancient Ruins: ring of colossal broken pillars round the plaza
    rx, ry = px(650, 380)
    rz = ground(T, 650, 380)
    p = Part('Landmark_Ruins_Pillars', c)
    for k in range(10):
        a = TAU * k / 10 + 0.15
        h = rnd.choice((18, 30, 48, 62, 80))
        p.cyl((rx + math.cos(a) * 76 * W_, ry + math.sin(a) * 76 * W_, rz + (h / 2 - 2) * W_), 8 * W_, h * W_,
              'F1_Ruins_Stone', 12)
    p.box((rx, ry + 76 * W_, rz + 86 * W_), (60 * W_, 12 * W_, 10 * W_), 'F1_Ruins_Stone')   # the one lintel left
    p.finish()


def build_blockouts(T):
    coll('LANDMARK_BLOCKOUTS', ROOT)
    out = dict(checkpoints=[], miniboss=[], boss=None, eggs=[], caves=[], secrets=[])
    wx, wy = px(*SPAWN)                                         # (no marker: the entrance plaza emblem is the spawn)
    z = ground(T, *SPAWN)
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
    p.torus((wx, wy, z + 0.8), 60.0, 1.6, 'F1_Marker_Boss', 48, 4)
    for k in range(8):
        a = TAU * k / 8
        p.box((wx + math.cos(a) * 60, wy + math.sin(a) * 60, z + 10), (4, 4, 20), 'F1_Marker_Boss')
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
    for name, (x, y), ang, w in CAVES:
        d = Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang))))
        q = Vector(px(x, y)); h0 = T.sample(*q)[0]
        for _ in range(3000):
            q2 = q + d * (S / 2)
            h, land = T.sample(*q2)
            if not land or h < h0 - 40:
                break
            q = q2
        hb, landb = T.sample(*(q + d * 12 * WORLD))
        zf = hb if landb else T.sample(*q)[0] - 24 * WORLD
        top = T.sample(*q)[0]
        hh = min(w * 0.85, max(12.0, top - zf - 3))
        M = Matrix.Translation((q.x - d.x * 3, q.y - d.y * 3, zf)) @ Matrix.Rotation(math.atan2(d.y, d.x) + math.pi / 2, 4, 'Z')
        FLIP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        p = Part(name, cv)
        arch = round_arch(w, max(1.0, hh - w / 2), 10)
        p.prism(arch, -3.0, 0.9 * w, 'F1_Cave', M @ FLIP)
        frame_strip(p, M, round_arch(w + 7, max(1.0, hh - w / 2), 10), arch, -4.5, 1.5, 'F1_Rock')
        p.finish()
        wc = M @ Vector((0, 0, 0))
        out['caves'].append((name, wc.x, wc.y, zf))
    build_landmarks(T)
    return out


# ---------------------------------------------------------------- clouds / guides --
def build_clouds():
    c = coll('CLOUDS', ROOT).name
    p = Part('F1_Cloud_Sea', c)                                # flat tiles: MeshParts stay under 2,048 studs
    t, R_ = 1600.0, 1500.0 * WORLD
    for i in range(-10, 10):
        for j in range(-10, 10):
            x, y = (i + 0.5) * t, (j + 0.5) * t
            if math.hypot(x, y) < R_:
                vs = [p.bm.verts.new((x + dx * t / 2, y + dy * t / 2, CLOUD_Z)) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                p.bm.faces.new(vs).material_index = p.mi('F1_Cloud')
    p.finish()
    far = Part('F1_Cloud_Sea_Far', coll('CLOUDS_FAR', ROOT).name)  # render-only horizon (not exported)
    far.cyl((0, 0, CLOUD_Z - 4), 4500.0 * WORLD, 2.0, 'F1_Cloud', 96)
    far.finish()
    rnd = random.Random(42)
    q = Part('F1_Cloud_Puffs', c)
    for k in range(36):
        a = rnd.uniform(0, TAU); r = rnd.uniform(150, 1200) * WORLD
        x, y = math.cos(a) * r, math.sin(a) * r
        s = rnd.uniform(28, 75) * WORLD
        for j in range(3):
            q.ico((x + rnd.uniform(-1, 1) * s, y + rnd.uniform(-1, 1) * s,
                   CLOUD_Z + (rnd.uniform(4, 20) + j * 4) * WORLD),
                  s * rnd.uniform(0.6, 1.0), 'F1_Cloud', 2, (1.0, 1.0, 0.45))
    q.finish()


def label(name, txt, coll_name, size, mat, x, y, z):
    o = text_mesh(name, txt, coll_name, size, 1.0, mat, (x, y, z), 0)
    o.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
    o.visible_shadow = False                                   # no ghost copy of the text on the ground
    return o


def build_guides(T, falls, marks):
    gc = coll('GUIDES', ROOT).name
    lc = coll('Map_Labels', gc).name
    top = 700.0 * WORLD                                        # above the World Tree canopy
    for title, lv, (cx, cy) in REGIONS:                        # the five regions
        wx, wy = px(cx, cy)
        label(f'Label_Region_{title}', title, lc, 34 * WORLD, 'F1_Label_Gold', wx, wy + 12 * WORLD, top + 10)
        label(f'Label_Region_{title}_Lv', lv, lc, 20 * WORLD, 'F1_Label_Gold', wx, wy - 22 * WORLD, top + 10)
    for a in AREAS:                                            # smaller place names (secrets stay unlabelled)
        if a.label is None or a.name in ('Jungle_Fortress', 'Fortress_Heights'):   # the region label covers these
            continue
        wx, wy = px(*a.label)
        label(f'Label_{a.name}', a.name.replace('_', ' ').upper(), lc, 21 * WORLD, 'F1_Label', wx, wy, top)
    label('Label_Floor_Title', 'FLOOR 1 - THE VERDANT KINGDOM', lc, 40 * WORLD, 'F1_Label_Gold', *px(240, -60), top)
    rs = Part('Reserved_Footprints', gc)
    for name, cx, cy, kind, a, b in RESERVED:
        wx, wy = px(cx, cy)
        z = T.sample(wx, wy)[0] + 0.5
        if kind == 'circle':
            rs.torus((wx, wy, z), a, 0.7 * WORLD, 'F1_Reserved', 64, 4)
        else:
            t_ = 1.4 * WORLD
            for sx, sy, w_, h_ in ((0, -b / 2, a, t_), (0, b / 2, a, t_), (-a / 2, 0, t_, b), (a / 2, 0, t_, b)):
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
    W_ = WORLD
    P3 = lambda x, y, z: (*px(x, y), z * ZL)
    specs = (('CAM_F1_Map_TopDown', (70 * W_, -10 * W_, 4000 * W_), (70 * W_, -10 * W_, 0), 'ORTHO', 1950 * W_),
             ('CAM_F1_Overview', (-1150 * W_, -1450 * W_, 1000 * W_), (80 * W_, 20 * W_, -20 * W_), 'PERSP', 28),
             ('CAM_F1_Entrance_Player', (*px(*entrance_px(30)), 12 * ZL + 7), P3(330, 700, 70), 'PERSP', 22),
             ('CAM_F1_Entrance_Front', (*px(*entrance_px(-130)), 12 * ZL + 20),
              (*px(*entrance_px(100)), 12 * ZL + 34), 'PERSP', 24),
             ('CAM_F1_Entrance_Aerial', (*px(*entrance_px(-330)), 12 * ZL + 230),
              (*px(*entrance_px(30)), 12 * ZL), 'PERSP', 24),
             ('CAM_F1_Entrance_Plaza', (*px(*entrance_px(-260, 40)), 12 * ZL + 70), (*px(*entrance_px(20)), 12 * ZL + 12),
              'PERSP', 20),
             ('CAM_F1_Entrance_Brook', (*px(152, 846), 12 * ZL + 45), (*px(112, 872), 12 * ZL - 8), 'PERSP', 26),
             ('CAM_F1_Valley_View', P3(470, 660, 14), P3(700, 470, 60), 'PERSP', 22),
             ('CAM_F1_World_Tree_View', P3(1010, 470, 135), P3(800, 150, 250), 'PERSP', 24),
             ('CAM_F1_Fortress_View', P3(880, 720, 120), P3(1240, 560, 250), 'PERSP', 24),
             ('CAM_F1_Side_Elevation', (60 * W_, -2500 * W_, 220 * W_), (60 * W_, 0, 80 * W_), 'PERSP', 32))
    for name, loc, tgt, kind, lens in specs:
        cam = bpy.data.cameras.new(name)
        cam.clip_start = 2.0; cam.clip_end = 300000
        if kind == 'ORTHO':
            cam.type = 'ORTHO'; cam.ortho_scale = lens
        else:
            cam.lens = lens
        o = bpy.data.objects.new(name, cam)
        o.location = loc
        o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        coll(coll_name).objects.link(o)
        out[name] = o
    out['CAM_F1_Map_TopDown']['hide_collections'] = 'CLOUDS,CLOUDS_FAR,World_Eggs,Secret_Areas'
    out['CAM_F1_Map_TopDown']['no_haze'] = True   # hidden things stay hidden
    for k, o in out.items():
        if k != 'CAM_F1_Map_TopDown':
            o['hide_collections'] = 'GUIDES'                      # labels, reserved outlines, scale figures
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
    import floor1_detail, floor1_entrance
    detail = floor1_detail.build_detail(T, falls)
    entrance = floor1_entrance.build_entrance(T)
    # layout data for Roblox scripting (Roblox coordinates: X, Y up, Z = -Blender Y)
    areas = []
    for a in AREAS:
        if a.label is None:
            continue
        wx, wy = px(*a.label)
        cx = sum(p[0] for p in a.poly) / len(a.poly); cy = sum(p[1] for p in a.poly) / len(a.poly)
        wx, wy = px(cx, cy)
        areas.append(dict(name=a.name, biome=a.biome, levels=a.levels, center=to_roblox(wx, wy, T.sample(wx, wy)[0])))
    step = lambda pts: pts[::4] + ([pts[-1]] if (len(pts) - 1) % 4 else [])
    layout = dict(
        floor='Floor 1 - The Verdant Kingdom', units='studs', roblox_axes='X, Y up, Z = -Blender Y',
        spawn=to_roblox(*marks['spawn']),
        regions=[dict(name=t, levels=lv) for t, lv, _ in REGIONS], areas=areas,
        checkpoints=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['checkpoints']],
        mini_bosses=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['miniboss']],
        main_boss=dict(name=marks['boss'][0], position=to_roblox(*marks['boss'][1:])),
        world_eggs=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['eggs']],
        caves=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['caves']],
        cave_routes=[list(p) for p in CAVE_ROUTES],
        secret_areas=[dict(name=n, position=to_roblox(x, y, z)) for n, x, y, z in marks['secrets']],
        paths=[dict(name=n, kind=k, width=w, waypoints=[to_roblox(*p) for p in step(pts)])
               for n, k, w, pts in T.paths],
        waterfalls=falls, bridges=detail['bridges'],
        entrance=dict(plaza=to_roblox(*entrance['plaza']), portal=to_roblox(*entrance['portal']),
                      stairs_bottom=to_roblox(*entrance['stairs_bottom']), hatchery=to_roblox(*entrance['hatchery']),
                      shop=to_roblox(*entrance['shop'])))
    land = T.land
    stats = dict(land_area_sq_studs=int(land.sum() * S * S), extent_x=[float(T.X[land].min()), float(T.X[land].max())],
                 extent_y=[float(T.Y[land].min()), float(T.Y[land].max())],
                 height_range=[float(T.H[land].min()), float(T.H[land].max())],
                 steepest_paths={k: round(math.degrees(math.atan(v)), 1)
                                 for k, v in sorted(T.path_grades.items(), key=lambda kv: -kv[1])[:8]},
                 detail={k: v for k, v in detail.items() if k != 'bridges'}, bridges=len(detail['bridges']))
    return layout, stats
