"""PET MART - tropical pet shop exterior, built to match the Pet Mart concept art
and the existing PetClinic.blend (same materials, scale and bevel style).

Overall dimensions (metric, 1 unit = 1 m), building centred on the world origin,
entrance facing -Y:
    footprint incl. stone terrace & steps : ~16.4 m wide (X) x ~10.8 m deep (Y)
    main walls                            :  15.0 m x 8.0 m, 4.4 m to eaves
    roof                                  :  hip roof, ridge 7.3 m; front cross-gable ridge 8.3 m
    sign crest (paw emblem) top           : ~8.6 m
    palms at the back corners             : ~7.5 m tall

Run in Blender (Scripting tab -> Run Script) or headless:
    blender -b -P pet_mart.py
    python3 pet_mart.py              (with the `bpy` pip module)
Saves PetMart.blend next to this script and prints the full path.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

random.seed(7)
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

# ---------------------------------------------------------------- layout ----
W_X0, W_X1 = -7.5, 7.5        # main walls
W_YF, W_YB = -3.0, 5.0        # front / back wall planes
Z0 = 0.45                     # top of stone plinth = floor level
Z_EAVE = 4.4                  # wall top
BAY_X = 2.6                   # entrance bay half-width
BAY_Y = -3.8                  # entrance bay front plane
WALL_T = 0.25


# ---------------------------------------------------------------- scene -----
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.view_settings.view_transform = 'AgX'
    return sc


COLL = {}


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


# ---------------------------------------------------------------- materials -
MATS = {}


def _principled(m):
    nt = m.node_tree
    return nt, nt.nodes['Principled BSDF']


def mat_plain(name, rgb, rough=0.5, emit=0.0, alpha=1.0, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    nt, b = _principled(m)
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*rgb, alpha)
    MATS[name] = m
    return m


def mat_noise(name, rgb_a, rgb_b, rough, scale=2.5, bump_scale=14.0, bump=0.1):
    """mottled stucco / stone (same node setup as PetClinic)"""
    m = mat_plain(name, rgb_a, rough)
    nt, b = _principled(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = scale
    n1.inputs['Detail'].default_value = 3.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*rgb_a, 1)
    ramp.color_ramp.elements[1].color = (*rgb_b, 1)
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = bump_scale
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.02
    L = nt.links.new
    L(tc.outputs['Object'], n1.inputs['Vector']); L(tc.outputs['Object'], n2.inputs['Vector'])
    L(n1.outputs['Fac'], ramp.inputs['Fac']); L(ramp.outputs['Color'], b.inputs['Base Color'])
    L(n2.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_wood(name, rgb_a, rgb_b, rough=0.55):
    m = mat_plain(name, rgb_a, rough)
    nt, b = _principled(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 5.0
    wv.inputs['Distortion'].default_value = 4.0; wv.inputs['Detail'].default_value = 2.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*rgb_a, 1)
    ramp.color_ramp.elements[1].color = (*rgb_b, 1)
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.03
    L = nt.links.new
    L(tc.outputs['Object'], wv.inputs['Vector']); L(wv.outputs['Fac'], ramp.inputs['Fac'])
    L(ramp.outputs['Color'], b.inputs['Base Color'])
    L(wv.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_brick(name, c1, c2, rough, width, height, mortar, mortar_rgb, bump=0.35, scale=1.0):
    """tiles / stone blocks via Brick Texture (as PetClinic's Roof_TealTiles)"""
    m = mat_plain(name, c1, rough)
    nt, b = _principled(m)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = (*c1, 1)
    br.inputs['Color2'].default_value = (*c2, 1)
    br.inputs['Mortar'].default_value = (*mortar_rgb, 1)
    br.inputs['Scale'].default_value = scale
    br.inputs['Mortar Size'].default_value = mortar
    br.inputs['Brick Width'].default_value = width
    br.inputs['Row Height'].default_value = height
    br.offset = 0.5
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.03
    L = nt.links.new
    L(tc.outputs['Object'], br.inputs['Vector']); L(br.outputs['Color'], b.inputs['Base Color'])
    L(br.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def build_materials():
    # shared with PetClinic.blend (same names & colours)
    mat_brick('Roof_TealTiles', (0.05, 0.49, 0.4), (0.04, 0.42, 0.34), 0.5, 0.62, 0.34, 0.03,
              (0.02, 0.25, 0.2), bump=0.6, scale=0.6)      # chunky tiles like the concept art
    mat_plain('Trim_Coral', (0.85, 0.2, 0.11), 0.5)
    mat_noise('Stucco_Cream', (0.93, 0.83, 0.64), (0.86, 0.74, 0.55), 0.85, 1.3, 30.0, 0.06)
    mat_brick('Stone_Pale', (0.86, 0.75, 0.56), (0.8, 0.69, 0.5), 0.8, 0.55, 0.26, 0.02,
              (0.61, 0.48, 0.3), 0.2)
    mat_noise('Stone_Coping', (0.92, 0.84, 0.69), (0.85, 0.76, 0.6), 0.75, 2.5, 14.0, 0.1)
    mat_wood('Timber_Honey', (0.53, 0.21, 0.05), (0.62, 0.27, 0.07))
    mat_wood('Timber_Light', (0.67, 0.34, 0.11), (0.75, 0.42, 0.15))
    mat_plain('Timber_Dark', (0.22, 0.07, 0.02), 0.6)
    mat_plain('Glass_Warm', (0.66, 0.81, 0.85), 0.04, alpha=0.1)
    mat_plain('Window_Glow', (1.0, 0.65, 0.25), 0.4, emit=2.5)
    mat_plain('Lantern_Glow', (1.0, 0.56, 0.16), 0.4, emit=9.0)
    mat_plain('Cream_Emblem', (1.0, 0.9, 0.72), 0.4)
    mat_plain('Paint_Teal', (0.05, 0.46, 0.38), 0.5)
    mat_plain('Soil', (0.15, 0.07, 0.03), 0.95)
    for n, c in (('Leaf_DeepGreen', (0.03, 0.25, 0.05)), ('Leaf_Green', (0.08, 0.38, 0.04)),
                 ('Leaf_LimeGreen', (0.18, 0.53, 0.06)), ('Leaf_Palm', (0.05, 0.33, 0.07)),
                 ('Flower_Red', (0.76, 0.04, 0.07)), ('Flower_Orange', (0.92, 0.25, 0.03)),
                 ('Flower_Pink', (0.89, 0.14, 0.27)), ('Flower_Pollen', (1.0, 0.69, 0.1)),
                 ('Flower_White', (0.95, 0.93, 0.88))):
        mat_plain(n, c, 0.5)
    mat_plain('Palm_Trunk', (0.26, 0.13, 0.05), 0.8)
    # Pet Mart specific
    mat_plain('Awning_Coral', (0.9, 0.24, 0.13), 0.7)
    mat_plain('Awning_Cream', (0.95, 0.88, 0.74), 0.7)
    mat_noise('Interior_Warm', (0.98, 0.82, 0.55), (0.92, 0.72, 0.45), 0.8, 2.0, 10.0, 0.02)
    MATS['Interior_Warm'].node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (1, 0.75, 0.4, 1)
    MATS['Interior_Warm'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.35
    mat_plain('Metal_Gold', (1.0, 0.7, 0.25), 0.3, metal=1.0)
    mat_plain('Paw_Teal', (0.02, 0.6, 0.62), 0.45)
    for n, c in (('Product_Blue', (0.05, 0.25, 0.85)), ('Product_Orange', (0.95, 0.42, 0.08)),
                 ('Product_Yellow', (1.0, 0.72, 0.1)), ('Product_Coral', (0.92, 0.3, 0.2)),
                 ('Product_Green', (0.15, 0.6, 0.12)), ('Product_Purple', (0.45, 0.15, 0.6)),
                 ('Product_Teal', (0.1, 0.6, 0.65)), ('Product_Red', (0.8, 0.08, 0.06)),
                 ('Product_White', (0.95, 0.94, 0.9)), ('Product_Grey', (0.55, 0.6, 0.66)),
                 ('Basket_Wicker', (0.6, 0.36, 0.12)), ('Bone_Cream', (0.95, 0.88, 0.72))):
        mat_plain(n, c, 0.45)


# ---------------------------------------------------------------- mesh part -
class Part:
    """bmesh accumulator -> one named, editable mesh object"""

    def __init__(self, name, collection, bevel=0.02):
        self.name, self.coll, self.bevel = name, collection, bevel
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _tag(self, verts, mat):
        i = self.mi(mat)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = i

    def box(self, c, s, mat, rot=None):
        m = Matrix.Translation(Vector(c)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4)) \
            @ Matrix.Diagonal((*s, 1))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self._tag(r['verts'], mat)

    def cyl(self, c, r, depth, mat, segs=12, axis='Z', r2=None, rot=None, caps=True):
        R = {'Z': Matrix.Identity(4), 'X': Matrix.Rotation(math.pi / 2, 4, 'Y'),
             'Y': Matrix.Rotation(math.pi / 2, 4, 'X')}[axis]
        if rot is not None:
            R = rot.to_4x4() @ R
        m = Matrix.Translation(Vector(c)) @ R
        res = bmesh.ops.create_cone(self.bm, cap_ends=caps, segments=segs, radius1=r,
                                    radius2=r if r2 is None else r2, depth=depth, matrix=m)
        self._tag(res['verts'], mat)

    def ico(self, c, r, mat, sub=1):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r,
                                         matrix=Matrix.Translation(Vector(c)))
        self._tag(res['verts'], mat)

    def beam(self, a, b, w, h, mat, pad=0.0):
        a, b = Vector(a), Vector(b)
        d = b - a
        q = d.to_track_quat('Z', 'Y').to_matrix()
        self.box((a + b) / 2, (w, h, d.length + 2 * pad), mat, q)

    def prism_xz(self, pts, y0, y1, mat):
        """polygon in the XZ plane (front elevation) extruded from y0 to y1"""
        bm = self.bm
        f = [bm.verts.new((x, y0, z)) for x, z in pts]
        b = [bm.verts.new((x, y1, z)) for x, z in pts]
        n = len(pts)
        faces = [bm.faces.new(f[::-1]), bm.faces.new(b)]
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((f[i], f[j], b[j], b[i])))
        i = self.mi(mat)
        for fc in faces:
            fc.material_index = i

    def prism_xy(self, pts, z0, z1, mat):
        bm = self.bm
        lo = [bm.verts.new((x, y, z0)) for x, y in pts]
        hi = [bm.verts.new((x, y, z1)) for x, y in pts]
        n = len(pts)
        faces = [bm.faces.new(lo[::-1]), bm.faces.new(hi)]
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((lo[i], lo[j], hi[j], hi[i])))
        i = self.mi(mat)
        for fc in faces:
            fc.material_index = i

    def poly(self, verts, faces, mat):
        vs = [self.bm.verts.new(v) for v in verts]
        i = self.mi(mat)
        for f in faces:
            fc = self.bm.faces.new([vs[k] for k in f])
            fc.material_index = i

    def finish(self, smooth=False):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(MATS[m])
        if smooth:
            me.shade_smooth()
        ob = bpy.data.objects.new(self.name, me)
        coll(self.coll).objects.link(ob)
        if self.bevel:
            bv = ob.modifiers.new('Bevel', 'BEVEL')
            bv.width = self.bevel
            bv.segments = 1
            bv.limit_method = 'ANGLE'
            bv.harden_normals = False
        return ob


def arc(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cz + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def wall_with_holes(p, x0, x1, z0, z1, y0, y1, holes, mat):
    """rectangular wall built from blocks around rectangular holes (x0,x1,z0,z1)"""
    xs = sorted({x0, x1, *[h[0] for h in holes], *[h[1] for h in holes]})
    zs = sorted({z0, z1, *[h[2] for h in holes], *[h[3] for h in holes]})
    for i in range(len(xs) - 1):
        for k in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[k] + zs[k + 1]) / 2
            if any(h[0] < cx < h[1] and h[2] < cz < h[3] for h in holes):
                continue
            p.box((cx, (y0 + y1) / 2, cz), (xs[i + 1] - xs[i], y1 - y0, zs[k + 1] - zs[k]), mat)


# ---------------------------------------------------------------- building --
DISPLAY = (-6.6, -3.0, 1.15, 3.55)      # big display window opening (x0,x1,z0,z1)
SIDEWIN = (3.7, 6.5, 1.75, 3.45)        # small right display window
DOOR_W, DOOR_SPRING = 1.25, 2.35        # half width of arched door, z where the arch starts


def build_building():
    # stone plinth + terrace
    p = Part('Foundation_Plinth', 'Building', 0.03)
    p.box((0, 0.6, Z0 / 2), (16.0, 9.6, Z0), 'Stone_Pale')
    p.box((0, -4.6, Z0 / 2), (16.4, 2.0, Z0), 'Stone_Pale')
    p.box((0, -3.6, Z0 - 0.04), (16.5, 0.18, 0.1), 'Stone_Coping')
    p.finish()

    # front walls (left + right of the entrance bay) with window openings
    p = Part('Walls_Front', 'Building')
    wall_with_holes(p, W_X0, -BAY_X, Z0, Z_EAVE, W_YF - WALL_T, W_YF, [DISPLAY], 'Stucco_Cream')
    wall_with_holes(p, BAY_X, W_X1, Z0, Z_EAVE, W_YF - WALL_T, W_YF, [SIDEWIN], 'Stucco_Cream')
    p.finish()

    p = Part('Walls_SidesAndBack', 'Building')
    p.box((W_X0 + WALL_T / 2, 1.0, (Z0 + Z_EAVE) / 2), (WALL_T, 8.0, Z_EAVE - Z0), 'Stucco_Cream')
    p.box((W_X1 - WALL_T / 2, 1.0, (Z0 + Z_EAVE) / 2), (WALL_T, 8.0, Z_EAVE - Z0), 'Stucco_Cream')
    p.box((0, W_YB - WALL_T / 2, (Z0 + Z_EAVE) / 2), (15.0, WALL_T, Z_EAVE - Z0), 'Stucco_Cream')
    p.finish()

    # entrance bay: front wall with an arched opening, built as two mirrored halves
    p = Part('Walls_EntranceBay', 'Building')
    top = Z_EAVE + 0.2
    for s in (-1, 1):
        a = arc(0, DOOR_SPRING, DOOR_W, math.pi if s < 0 else 0, math.pi / 2, 8)
        pts = [(s * BAY_X, Z0), (s * DOOR_W, Z0)] + a + [(0, top), (s * BAY_X, top)]
        if s > 0:
            pts = pts[::-1]
        p.prism_xz(pts, BAY_Y - WALL_T, BAY_Y, 'Stucco_Cream')
    for s in (-1, 1):   # bay side walls back to the main front wall
        p.box((s * (BAY_X - WALL_T / 2), (BAY_Y + W_YF) / 2 - WALL_T / 2, (Z0 + top) / 2),
              (WALL_T, W_YF - BAY_Y, top - Z0), 'Stucco_Cream')
    # gable triangle above the bay
    p.prism_xz([(-BAY_X - 0.2, top), (BAY_X + 0.2, top), (0, 7.55)], BAY_Y - 0.1, BAY_Y + 0.3, 'Stucco_Cream')
    p.finish()

    # pale stone arch surround around the door (block ring, like the reference)
    p = Part('Entrance_StoneArch', 'Building', 0.025)
    n = 11
    for i in range(n):
        a0 = math.pi * i / n
        a1 = math.pi * (i + 1) / n
        r0, r1 = DOOR_W + 0.02, DOOR_W + 0.42
        pts = [(r0 * math.cos(a0), DOOR_SPRING + r0 * math.sin(a0)),
               (r1 * math.cos(a0), DOOR_SPRING + r1 * math.sin(a0)),
               (r1 * math.cos(a1), DOOR_SPRING + r1 * math.sin(a1)),
               (r0 * math.cos(a1), DOOR_SPRING + r0 * math.sin(a1))]
        pts = [(x * 0.985, z) for x, z in pts]
        p.prism_xz(pts[::-1], BAY_Y - WALL_T - 0.08, BAY_Y - WALL_T + 0.02, 'Stone_Coping')
    for s in (-1, 1):
        for k in range(4):
            z = Z0 + 0.05 + k * 0.48
            w = 0.42 if k % 2 == 0 else 0.32
            p.box((s * (DOOR_W + 0.02 + w / 2), BAY_Y - WALL_T - 0.03, z + 0.22), (w, 0.1, 0.44), 'Stone_Coping')
    p.finish()

    # honey timber frame: corner posts, top beam, bay posts, gable truss
    p = Part('Timber_Frame', 'Building', 0.015)
    for x in (W_X0, W_X1):
        p.box((x, W_YF - 0.15, (Z0 + Z_EAVE) / 2 + 0.1), (0.4, 0.4, Z_EAVE - Z0 + 0.2), 'Timber_Honey')
        p.box((x, W_YB - 0.1, (Z0 + Z_EAVE) / 2 + 0.1), (0.4, 0.4, Z_EAVE - Z0 + 0.2), 'Timber_Honey')
    for x in (-BAY_X, BAY_X):
        p.box((x, BAY_Y - 0.15, (Z0 + Z_EAVE) / 2 + 0.1), (0.42, 0.42, Z_EAVE - Z0 + 0.2), 'Timber_Honey')
    p.box((-(W_X1 + BAY_X) / 2, W_YF - 0.32, Z_EAVE - 0.05), (W_X1 - BAY_X + 0.4, 0.3, 0.38), 'Timber_Honey')
    p.box(((W_X1 + BAY_X) / 2, W_YF - 0.32, Z_EAVE - 0.05), (W_X1 - BAY_X + 0.4, 0.3, 0.38), 'Timber_Honey')
    p.box((0, BAY_Y - 0.32, Z_EAVE + 0.15), (2 * BAY_X + 0.5, 0.34, 0.42), 'Timber_Honey')
    for x in (W_X0, W_X1):
        p.box((x, 1.0, Z_EAVE - 0.05), (0.3, 8.4, 0.38), 'Timber_Honey')
    # gable truss (visible above the sign)
    yb = BAY_Y - 0.16
    p.beam((0, yb, Z_EAVE + 0.35), (0, yb, 7.45), 0.24, 0.2, 'Timber_Honey')
    for s in (-1, 1):
        p.beam((s * 1.9, yb, Z_EAVE + 0.35), (0, yb, 6.6), 0.2, 0.18, 'Timber_Honey')
    p.box((0, yb - 0.04, 6.9), (0.36, 0.3, 0.36), 'Timber_Light')
    # eave brackets
    for x in (-7.0, -5.0, -3.2, 3.2, 5.0, 7.0):
        p.beam((x, W_YF - 0.2, 3.85), (x, W_YF - 0.95, Z_EAVE + 0.15), 0.18, 0.18, 'Timber_Honey')
    for s in (-1, 1):
        p.beam((s * BAY_X, BAY_Y - 0.25, 3.95), (s * BAY_X, BAY_Y - 0.9, Z_EAVE + 0.3), 0.2, 0.2, 'Timber_Honey')
        p.box((s * (BAY_X - 0.55), BAY_Y - 0.35, 4.55), (0.32, 0.32, 0.32), 'Timber_Light')
    p.finish()

    # interior box seen through the windows and door
    p = Part('Interior_Room', 'Building', 0)
    p.box((0, -0.6, Z0 + 0.01), (14.6, 4.6, 0.02), 'Timber_Light')
    p.box((0, -0.6, Z_EAVE - 0.05), (14.6, 4.6, 0.1), 'Interior_Warm')
    p.box((0, 1.6, (Z0 + Z_EAVE) / 2), (14.6, 0.1, Z_EAVE - Z0), 'Interior_Warm')
    for x in (-7.2, 7.2, -2.4, 2.4):
        p.box((x, -0.6, (Z0 + Z_EAVE) / 2), (0.1, 4.6, Z_EAVE - Z0), 'Interior_Warm')
    p.finish()


# ---------------------------------------------------------------- roof ------
def build_roof():
    ov = 0.85
    x0, x1, y0, y1 = W_X0 - ov, W_X1 + ov, W_YF - ov, W_YB + ov
    ze, zr = Z_EAVE + 0.25, 7.3
    run = (y1 - y0) / 2
    ym = (y0 + y1) / 2
    rx0, rx1 = x0 + run, x1 - run
    p = Part('Roof_Main', 'Roof')
    p.poly([(x0, y0, ze), (x1, y0, ze), (x1, y1, ze), (x0, y1, ze), (rx0, ym, zr), (rx1, ym, zr)],
           [(0, 1, 5, 4), (2, 3, 4, 5), (3, 0, 4), (1, 2, 5)], 'Roof_TealTiles')
    ob = p.finish()
    so = ob.modifiers.new('Thickness', 'SOLIDIFY'); so.thickness = 0.3; so.offset = -1
    ob.modifiers.move(1, 0)

    # front cross gable over the entrance
    gw, gy0, gy1, gze, gzr = BAY_X + 0.9, BAY_Y - 1.0, ym, Z_EAVE + 0.45, 8.3
    p = Part('Roof_FrontGable', 'Roof')
    p.poly([(-gw, gy0, gze), (0, gy0, gzr), (gw, gy0, gze), (-gw, gy1, gze), (0, gy1, gzr), (gw, gy1, gze)],
           [(0, 1, 4, 3), (1, 2, 5, 4)], 'Roof_TealTiles')
    ob = p.finish()
    so = ob.modifiers.new('Thickness', 'SOLIDIFY'); so.thickness = 0.3; so.offset = -1
    ob.modifiers.move(1, 0)

    # chunky coral edging: eaves, hips, ridge, gable rakes + end blocks
    p = Part('Roof_CoralTrim', 'Roof', 0.03)
    W, H = 0.5, 0.32
    c = [(x0, y0, ze), (x1, y0, ze), (x1, y1, ze), (x0, y1, ze)]
    for i in range(4):
        a, b = Vector(c[i]), Vector(c[(i + 1) % 4])
        p.beam(a + Vector((0, 0, 0.05)), b + Vector((0, 0, 0.05)), W, H, 'Trim_Coral', 0.2)
    for i, r in ((0, (rx0, ym, zr)), (3, (rx0, ym, zr)), (1, (rx1, ym, zr)), (2, (rx1, ym, zr))):
        p.beam(Vector(c[i]) + Vector((0, 0, 0.1)), Vector(r) + Vector((0, 0, 0.1)), W * 0.85, H, 'Trim_Coral', 0.1)
    p.beam((rx0, ym, zr + 0.12), (rx1, ym, zr + 0.12), W, H, 'Trim_Coral', 0.15)
    for s in (-1, 1):
        p.beam((s * gw, gy0, gze + 0.1), (0, gy0, gzr + 0.1), 0.55, 0.38, 'Trim_Coral', 0.2)
        p.box((s * (gw + 0.05), gy0 + 0.1, gze + 0.05), (0.6, 0.6, 0.5), 'Trim_Coral')
        p.box((x1 if s > 0 else x0, y0, ze + 0.12), (0.62, 0.62, 0.5), 'Trim_Coral')
    p.beam((0, gy0, gzr + 0.12), (0, gy1, gzr + 0.12), 0.55, 0.36, 'Trim_Coral', 0.1)
    p.box((0, gy0 - 0.05, gzr + 0.2), (0.7, 0.7, 0.62), 'Trim_Coral')
    p.finish()


# ---------------------------------------------------------------- awning ----
def build_awning():
    x0, x1 = DISPLAY[0] - 0.25, DISPLAY[1] + 0.25
    yb, yf = W_YF - WALL_T, W_YF - WALL_T - 1.35
    zb, zf = 4.15, 3.45
    n = 9
    p = Part('Awning_Striped', 'Awning', 0.01)
    w = (x1 - x0) / n
    for i in range(n):
        m = 'Awning_Coral' if i % 2 == 0 else 'Awning_Cream'
        xa, xb = x0 + i * w, x0 + (i + 1) * w
        # sloped canopy strip (with thickness)
        p.poly([(xa, yb, zb), (xb, yb, zb), (xb, yf, zf), (xa, yf, zf),
                (xa, yb, zb - 0.06), (xb, yb, zb - 0.06), (xb, yf, zf - 0.06), (xa, yf, zf - 0.06)],
               [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], m)
        # scalloped valance: flat strip + half-disc
        valance = [(xa, zf), (xb, zf), (xb, zf - 0.28)] + arc((xa + xb) / 2, zf - 0.28, w / 2, 0, -math.pi, 6)[1:-1] + [(xa, zf - 0.28)]
        p.prism_xz(valance[::-1], yf - 0.04, yf + 0.02, m)
    p.finish()
    p = Part('Awning_Brackets', 'Awning', 0.01)
    for x in (x0 + 0.1, x1 - 0.1):
        p.beam((x, yb, 3.5), (x, yf + 0.1, zf - 0.02), 0.06, 0.06, 'Timber_Dark')
    p.box(((x0 + x1) / 2, yb - 0.05, zb + 0.05), (x1 - x0 + 0.1, 0.12, 0.14), 'Timber_Honey')
    p.finish()


# ---------------------------------------------------------------- windows ---
def window_frame(p, x0, x1, z0, z1, y, mat='Timber_Honey', t=0.16, mullions=()):
    d = 0.3
    p.box(((x0 + x1) / 2, y, z1 + t / 2), (x1 - x0 + 2 * t, d, t), mat)
    p.box(((x0 + x1) / 2, y - 0.08, z0 - t / 2), (x1 - x0 + 2 * t + 0.2, d + 0.16, t), mat)  # sill
    for x in (x0 - t / 2, x1 + t / 2):
        p.box((x, y, (z0 + z1) / 2), (t, d, z1 - z0), mat)
    for x in mullions:
        p.box((x, y, (z0 + z1) / 2), (t * 0.8, d * 0.8, z1 - z0), mat)


def build_windows_doors():
    y = W_YF - WALL_T / 2
    p = Part('Window_Display_Frame', 'WindowsAndDoors', 0.012)
    window_frame(p, *DISPLAY, y, mullions=(-4.05,))
    p.finish()
    g = Part('Window_Display_Glass', 'WindowsAndDoors', 0)
    g.box(((DISPLAY[0] + DISPLAY[1]) / 2, y + 0.06, (DISPLAY[2] + DISPLAY[3]) / 2),
          (DISPLAY[1] - DISPLAY[0], 0.02, DISPLAY[3] - DISPLAY[2]), 'Glass_Warm')
    g.finish()

    p = Part('Window_Side_Frame', 'WindowsAndDoors', 0.012)
    window_frame(p, *SIDEWIN, y)
    p.box(((SIDEWIN[0] + SIDEWIN[1]) / 2, y - 0.1, SIDEWIN[3] + 0.32), (SIDEWIN[1] - SIDEWIN[0] + 0.6, 0.4, 0.22), 'Timber_Honey')
    p.finish()
    g = Part('Window_Side_Glass', 'WindowsAndDoors', 0)
    g.box(((SIDEWIN[0] + SIDEWIN[1]) / 2, y + 0.06, (SIDEWIN[2] + SIDEWIN[3]) / 2),
          (SIDEWIN[1] - SIDEWIN[0], 0.02, SIDEWIN[3] - SIDEWIN[2]), 'Glass_Warm')
    g.finish()

    # arched timber door frame
    yd = BAY_Y - WALL_T / 2
    p = Part('Door_ArchFrame', 'WindowsAndDoors', 0.012)
    outer = arc(0, DOOR_SPRING, DOOR_W, 0, math.pi, 12)
    inner = arc(0, DOOR_SPRING, DOOR_W - 0.16, math.pi, 0, 12)
    p.prism_xz(outer + inner, yd - 0.18, yd + 0.12, 'Timber_Honey')
    for s in (-1, 1):
        p.box((s * (DOOR_W - 0.08), yd - 0.03, (Z0 + DOOR_SPRING) / 2), (0.16, 0.3, DOOR_SPRING - Z0), 'Timber_Honey')
    p.box((0, yd, Z0 + 0.03), (2 * DOOR_W, 0.32, 0.06), 'Timber_Dark')
    p.finish()

    # double doors: timber stiles/rails with glass panels, arched heads
    for s, side in ((-1, 'Left'), (1, 'Right')):
        p = Part(f'Door_{side}', 'WindowsAndDoors', 0.008)
        xi, xo = 0.0, s * (DOOR_W - 0.16)
        yy = yd + 0.04
        r = DOOR_W - 0.16
        a = arc(0, DOOR_SPRING, r, math.pi / 2, math.pi if s < 0 else 0, 6)
        leaf = [(0, Z0 + 0.06), (xo, Z0 + 0.06)] + a[::-1] + [(0, DOOR_SPRING + r)]
        if s > 0:
            leaf = leaf[::-1]
        # glass leaf, then timber framing on top of it
        p.prism_xz(leaf, yy - 0.01, yy + 0.01, 'Glass_Warm')
        st = 0.14
        p.box((s * st / 2, yy - 0.03, (Z0 + DOOR_SPRING + r) / 2), (st, 0.1, DOOR_SPRING + r - Z0), 'Timber_Honey')
        p.box((xo - s * st / 2, yy - 0.03, (Z0 + DOOR_SPRING) / 2), (st, 0.1, DOOR_SPRING - Z0), 'Timber_Honey')
        for z in (Z0 + 0.12, Z0 + 0.95, 1.85, DOOR_SPRING):
            p.box((xo / 2, yy - 0.03, z), (abs(xo), 0.1, 0.12), 'Timber_Honey')
        p.box((xo / 2, yy - 0.04, Z0 + 0.53), (abs(xo) - 0.1, 0.08, 0.75), 'Timber_Light')   # kick panel
        for k in range(1, 6):    # planks in the kick panel
            p.box((xo / 2, yy - 0.085, Z0 + 0.16 + k * 0.125), (abs(xo) - 0.16, 0.02, 0.02), 'Timber_Dark')
        p.box((xo / 2, yy - 0.03, (1.85 + DOOR_SPRING) / 2 + 0.25), (0.08, 0.09, 1.2), 'Timber_Honey')
        for k in range(4):      # arched head glazing bars
            ang = math.pi / 2 + s * (k + 1) * (math.pi / 2) / 5 * -1
            q1 = Vector((0, yy - 0.03, DOOR_SPRING))
            q2 = Vector((r * math.cos(ang), yy - 0.03, DOOR_SPRING + r * math.sin(ang)))
            if k % 2 == 0:
                p.beam(q1, q2, 0.06, 0.08, 'Timber_Honey')
        p.cyl((s * 0.16, yy - 0.12, 1.55), 0.035, 0.45, 'Metal_Gold', 8)
        p.finish()
    # warm glow behind the door glass: shelves of cans in the shop
    p = Part('Door_InteriorShelves', 'ShopDisplays', 0.01)
    for z in (1.2, 1.8, 2.4, 3.0):
        p.box((0, -2.2, z), (2.2, 0.4, 0.06), 'Timber_Honey')
        for i in range(6):
            x = -0.9 + i * 0.36
            p.cyl((x, -2.2, z + 0.14), 0.1, 0.22, random.choice(['Product_Teal', 'Product_Coral', 'Product_Yellow', 'Product_White']), 8)
    p.box((0, -2.0, 2.1), (2.4, 0.06, 2.6), 'Timber_Light')
    p.finish()


# ---------------------------------------------------------------- sign ------
def find_font():
    for f in (r'C:\Windows\Fonts\segoeuib.ttf', r'C:\Windows\Fonts\ariblk.ttf', r'C:\Windows\Fonts\arialbd.ttf',
              '/System/Library/Fonts/Supplemental/Arial Black.ttf',
              '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(f):
            return bpy.data.fonts.load(f)
    return None


def build_sign():
    ys = BAY_Y - 0.62          # sign front
    zc = Z_EAVE + 0.95
    # curved timber board: top & bottom edges arc gently upward in the middle
    p = Part('Sign_Board', 'Sign', 0.015)
    hw, n = 3.7, 14
    top = [(x, zc + 0.72 + 0.28 * (1 - (x / hw) ** 2)) for x in [-hw + 2 * hw * i / n for i in range(n + 1)]]
    bot = [(x, zc - 0.72 + 0.22 * (1 - (x / hw) ** 2)) for x in [hw - 2 * hw * i / n for i in range(n + 1)]]
    p.prism_xz(top + bot, ys, ys + 0.3, 'Timber_Dark')            # dark backing / border
    top_i = [(x * 0.95, z - 0.12) for x, z in top]
    bot_i = [(x * 0.95, z + 0.12) for x, z in bot]
    p.prism_xz(top_i + bot_i, ys - 0.06, ys + 0.1, 'Timber_Light')
    for k in (-1, 0, 1):                                          # plank seams
        p.box((0, ys - 0.065, zc + 0.08 + k * 0.33 + 0.22 * 0.6), (2 * hw * 0.92, 0.02, 0.025), 'Timber_Honey')
    for s in (-1, 1):                                             # end caps & pegs
        p.box((s * (hw + 0.05), ys + 0.1, zc + 0.05), (0.32, 0.5, 1.35), 'Timber_Honey')
        p.cyl((s * (hw - 0.3), ys - 0.08, zc + 0.5), 0.07, 0.06, 'Metal_Gold', 8, 'Y')
        p.cyl((s * (hw - 0.3), ys - 0.08, zc - 0.32), 0.07, 0.06, 'Metal_Gold', 8, 'Y')
    # arched crest for the paw emblem
    crest = arc(0, zc + 0.8, 1.05, 0, math.pi, 12)
    p.prism_xz(crest, ys + 0.05, ys + 0.3, 'Timber_Honey')
    inner = [(x * 0.84, zc + 0.8 + (z - zc - 0.8) * 0.84) for x, z in crest]
    p.prism_xz(inner, ys, ys + 0.1, 'Cream_Emblem')
    p.finish()

    # paw print emblem
    p = Part('Sign_PawEmblem', 'Sign', 0.01)
    zp = zc + 1.12
    for x, z, r in ((0, -0.02, 0.22), (-0.15, -0.1, 0.17), (0.15, -0.1, 0.17)):   # main pad
        p.cyl((x, ys - 0.05, zp + z), r, 0.12, 'Paw_Teal', 14, 'Y')
    for x, z, r in ((-0.36, 0.3, 0.12), (-0.13, 0.44, 0.13), (0.13, 0.44, 0.13), (0.36, 0.3, 0.12)):
        p.cyl((x, ys - 0.05, zp + z), r, 0.12, 'Paw_Teal', 12, 'Y')
    p.finish()

    # raised cream letters "PET MART"
    cu = bpy.data.curves.new('Sign_Lettering', 'FONT')
    cu.body = 'PET MART'
    f = find_font()
    if f:
        cu.font = f
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    cu.size = 1.0
    cu.space_character = 1.05
    cu.extrude = 0.06
    cu.bevel_depth = 0.018
    cu.bevel_resolution = 1
    cu.offset = 0.0 if f else 0.02
    cu.resolution_u = 3
    tob = bpy.data.objects.new('Sign_Lettering_tmp', cu)
    coll('Sign').objects.link(tob)
    tob.rotation_euler = (math.pi / 2, 0, 0)
    tob.location = (0, ys - 0.13, zc + 0.05)
    # curve the text with the board using a simple bend
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tob.evaluated_get(dg))
    for v in me.vertices:   # follow the board's arc (x is still in text space)
        v.co.y += 0.2 * (1 - (v.co.x / hw) ** 2)
    me.materials.clear()
    me.materials.append(MATS['Cream_Emblem'])
    ob = bpy.data.objects.new('Sign_Lettering', me)
    ob.matrix_world = tob.matrix_world
    coll('Sign').objects.link(ob)
    bpy.data.objects.remove(tob)
    bpy.data.curves.remove(cu)


# ---------------------------------------------------------------- products --
def bag(p, c, mat, s=(0.32, 0.16, 0.42)):
    x, y, z = c
    p.box((x, y, z + s[2] / 2), s, mat)
    p.box((x, y, z + s[2] + 0.03), (s[0] * 0.95, s[1] * 0.4, 0.06), mat)
    p.box((x, y - s[1] / 2 - 0.005, z + s[2] * 0.45), (s[0] * 0.55, 0.01, s[2] * 0.35), 'Product_White')
    p.cyl((x, y - s[1] / 2 - 0.012, z + s[2] * 0.45), 0.05, 0.01, 'Paw_Teal' if mat != 'Paw_Teal' else 'Product_Coral', 8, 'Y')


def bone(p, c, mat, L=0.36, r=0.05, rot=0.0):
    c = Vector(c)
    d = Vector((math.cos(rot), 0, math.sin(rot)))
    p.beam(c - d * L / 2, c + d * L / 2, r * 1.6, r * 1.6, mat)
    for e in (-1, 1):
        for o in (-1, 1):
            q = c + d * e * L / 2 + Vector((-d.z, 0, d.x)) * o * r
            p.ico(q, r * 1.1, mat, 1)


def basket(p, c, r=0.24, h=0.18, fill=()):
    x, y, z = c
    p.cyl((x, y, z + h / 2), r, h, 'Basket_Wicker', 10, r2=r * 0.8)
    p.cyl((x, y, z + h), r * 1.03, 0.04, 'Timber_Honey', 10)
    for i, m in enumerate(fill):
        a = i / max(1, len(fill)) * 2 * math.pi
        p.ico((x + 0.1 * math.cos(a), y + 0.08 * math.sin(a), z + h + 0.03), 0.09, m, 1)


def ball(p, c, r, mat, paw=False):
    p.ico(c, r, mat, 2)
    if paw:
        x, y, z = c
        p.cyl((x, y - r * 0.97, z - r * 0.08), r * 0.32, 0.02, 'Product_White', 8, 'Y')
        for dx, dz in ((-0.28, 0.32), (-0.1, 0.45), (0.1, 0.45), (0.28, 0.32)):
            p.cyl((x + dx * r, y - r * 0.9, z + dz * r), r * 0.12, 0.02, 'Product_White', 6, 'Y')


def build_shop_displays():
    rnd = random.Random(3)
    # main display: shelving on the left, leash rack on the right
    p = Part('Display_Shelves', 'ShopDisplays', 0.01)
    x0, x1 = DISPLAY[0] + 0.1, -4.2
    yb = -1.95
    p.box(((x0 + x1) / 2, yb + 0.05, 2.35), (x1 - x0 + 0.1, 0.08, 2.5), 'Timber_Light')
    for z in (1.85, 2.55, 3.2):
        p.box(((x0 + x1) / 2, yb - 0.25, z), (x1 - x0, 0.5, 0.06), 'Timber_Honey')
    for x in (x0, x1):
        p.box((x, yb - 0.25, 2.35), (0.08, 0.5, 2.4), 'Timber_Honey')
    p.box((-5.0, -2.25, 1.1), (3.6, 0.7, 0.12), 'Timber_Honey')       # low display ledge
    p.finish()

    p = Part('Display_Products', 'ShopDisplays', 0.006)
    # top shelf: jars / cans
    for i in range(6):
        x = x0 + 0.22 + i * 0.36
        p.cyl((x, -2.25, 3.23 + 0.12), 0.11, 0.24, rnd.choice(['Product_Coral', 'Product_Teal', 'Product_Yellow']), 8)
        p.cyl((x, -2.25, 3.23 + 0.26), 0.115, 0.04, 'Product_White', 8)
    # middle shelf: food bags + green bone
    bag(p, (x0 + 0.35, -2.2, 2.58), 'Product_Blue')
    bag(p, (x0 + 0.78, -2.2, 2.58), 'Product_Yellow')
    bone(p, (x0 + 1.4, -2.3, 2.7), 'Product_Green', 0.4, 0.06)
    bag(p, (x0 + 2.0, -2.2, 2.58), 'Product_Orange')
    # lower shelf: bags + cans + bone
    bag(p, (x0 + 0.3, -2.2, 1.88), 'Product_Blue', (0.3, 0.16, 0.38))
    bag(p, (x0 + 0.7, -2.2, 1.88), 'Product_Coral', (0.3, 0.16, 0.38))
    bone(p, (x0 + 1.25, -2.3, 2.0), 'Bone_Cream', 0.32, 0.05)
    for i in range(3):
        p.cyl((x0 + 1.75 + i * 0.22, -2.25, 1.88 + 0.1), 0.09, 0.2, 'Product_Teal', 8)
    # ledge: row of baskets with toys + a cream bone
    for i, x in enumerate((-6.25, -5.6, -4.95, -4.3, -3.6)):
        basket(p, (x, -2.35, 1.16), 0.25, 0.18,
               [rnd.choice(['Product_Red', 'Product_Blue', 'Product_Yellow', 'Product_Green', 'Product_Orange']) for _ in range(3)])
    bone(p, (-5.3, -2.55, 1.32), 'Product_Purple', 0.3, 0.045, 0.1)
    p.finish()

    # leash / collar rack on the right of the display window
    p = Part('Display_LeashRack', 'ShopDisplays', 0.006)
    p.box((-3.55, -2.15, 3.1), (0.95, 0.08, 0.08), 'Timber_Honey')
    for i, m in enumerate(('Product_Purple', 'Product_Red', 'Product_Teal', 'Product_Green')):
        x = -3.9 + i * 0.24
        p.cyl((x, -2.15, 3.1), 0.025, 0.12, 'Metal_Gold', 6, 'Y')
        p.beam((x, -2.15, 3.05), (x, -2.15, 2.35), 0.05, 0.03, m)          # leash strap
        bm_ring(p, (x, -2.15, 2.2), 0.13, 0.025, m)                         # collar loop
        p.box((x, -2.15, 2.05), (0.06, 0.06, 0.08), 'Metal_Gold')           # clip
    p.finish()

    # small side window: toy shelf
    p = Part('SideWindow_Toys', 'ShopDisplays', 0.006)
    xs0, xs1, zs0 = SIDEWIN[0], SIDEWIN[1], SIDEWIN[2]
    p.box(((xs0 + xs1) / 2, -2.25, zs0 + 0.05), (xs1 - xs0, 0.5, 0.06), 'Timber_Honey')
    p.box(((xs0 + xs1) / 2, -2.25, zs0 + 0.85), (xs1 - xs0, 0.5, 0.06), 'Timber_Honey')
    p.box(((xs0 + xs1) / 2, -2.0, zs0 + 0.6), (xs1 - xs0, 0.06, 1.4), 'Timber_Light')
    basket(p, (xs0 + 0.5, -2.3, zs0 + 0.08), 0.24, 0.16, ['Product_Red', 'Product_Green', 'Product_Yellow'])
    ball(p, (xs0 + 1.05, -2.35, zs0 + 0.2), 0.12, 'Product_Teal')
    bone(p, (xs0 + 1.6, -2.35, zs0 + 0.16), 'Product_Blue', 0.38, 0.055)
    basket(p, (xs1 - 0.45, -2.3, zs0 + 0.08), 0.24, 0.16, ['Product_Orange', 'Product_Blue', 'Product_Red'])
    for i, m in enumerate(('Product_Blue', 'Product_Red', 'Product_Yellow')):   # rope toy loops on top shelf
        bm_ring(p, (xs0 + 0.6 + i * 0.18, -2.3, zs0 + 1.08), 0.14, 0.03, m)
    p.ico((xs0 + 1.4, -2.3, zs0 + 1.0), 0.1, 'Product_Orange', 2)
    p.cyl((xs1 - 0.5, -2.3, zs0 + 1.0), 0.12, 0.24, 'Product_Coral', 8)
    p.finish()


def bm_ring(p, c, R, r, mat, segs=10, sides=4):
    """low-poly torus standing in the XZ plane"""
    verts, faces = [], []
    for i in range(segs):
        a = i / segs * 2 * math.pi
        cen = Vector((R * math.cos(a), 0, R * math.sin(a)))
        out = Vector((math.cos(a), 0, math.sin(a)))
        for j in range(sides):
            b = j / sides * 2 * math.pi
            verts.append(Vector(c) + cen + out * r * math.cos(b) + Vector((0, r * math.sin(b), 0)))
    for i in range(segs):
        for j in range(sides):
            a, b = i * sides + j, i * sides + (j + 1) % sides
            c2, d = ((i + 1) % segs) * sides + (j + 1) % sides, ((i + 1) % segs) * sides + j
            faces.append((a, b, c2, d))
    p.poly(verts, faces, mat)


# ---------------------------------------------------------------- porch -----
def lantern(name, pos, wall_dir, collection='Porch'):
    """hanging wall lantern + bracket + warm point light"""
    pos = Vector(pos)
    p = Part(name, collection, 0)
    p.box(pos, (0.34, 0.34, 0.46), 'Lantern_Glow')
    for dx in (-1, 1):
        for dy in (-1, 1):
            p.box(pos + Vector((dx * 0.17, dy * 0.17, 0)), (0.06, 0.06, 0.5), 'Timber_Dark')
    p.cyl(pos + Vector((0, 0, 0.33)), 0.31, 0.2, 'Timber_Dark', 4, r2=0.05, rot=Matrix.Rotation(math.pi / 4, 3, 'Z'))
    p.box(pos + Vector((0, 0, -0.27)), (0.4, 0.4, 0.07), 'Timber_Dark')
    p.cyl(pos + Vector((0, 0, -0.35)), 0.08, 0.12, 'Timber_Dark', 6, r2=0.0)
    w = Vector(wall_dir)
    top = pos + Vector((0, 0, 0.5))
    p.beam(top, top + w * 0.5, 0.06, 0.06, 'Timber_Dark')
    p.beam(top + w * 0.5, top + w * 0.5 + Vector((0, 0, -0.35)), 0.06, 0.06, 'Timber_Dark')
    p.cyl(top + Vector((0, 0, -0.03)), 0.03, 0.08, 'Timber_Dark', 6)
    p.finish()
    li = bpy.data.lights.new(name + '_Light', 'POINT')
    li.energy = 25
    li.color = (1.0, 0.7, 0.4)
    li.shadow_soft_size = 0.15
    lo = bpy.data.objects.new(name + '_Light', li)
    lo.location = pos
    coll(collection).objects.link(lo)


def crate(p, c, size=(1.1, 0.75, 0.5)):
    x, y, z = c
    sx, sy, sz = size
    p.box((x, y, z + sz / 2), (sx, sy, sz), 'Timber_Light')
    for k in range(3):   # slats
        zz = z + 0.08 + k * (sz - 0.16) / 2
        p.box((x, y - sy / 2 - 0.015, zz), (sx, 0.03, 0.07), 'Timber_Honey')
    for s in (-1, 1):
        p.box((x + s * (sx / 2 - 0.05), y - sy / 2 - 0.03, z + sz / 2), (0.1, 0.04, sz), 'Timber_Honey')


def build_porch():
    # steps down from the terrace in front of the door
    p = Part('Entrance_Steps', 'Porch', 0.025)
    for k, (yy, h) in enumerate(((-5.85, 0.3), (-6.35, 0.15))):
        p.box((0, yy, h / 2), (4.8 - k * 0.0, 0.5 + (0.5 if k == 0 else 0), h), 'Stone_Pale')
        p.box((0, yy - (0.25 if k else 0.5) + 0.04, h - 0.02), (4.8, 0.1, 0.05), 'Stone_Coping')
    p.finish()

    # low cream-stone planters along the front
    p = Part('Planters', 'Porch', 0.03)
    PL = [(-7.6, -6.1), (-3.2, -2.4), (2.4, 3.2), (6.1, 7.6)]
    for xa, xb in PL:
        cx, w = (xa + xb) / 2, xb - xa
        p.box((cx, -6.05, 0.48), (w, 1.25, 0.96), 'Stone_Pale')
        p.box((cx, -6.05, 0.99), (w + 0.12, 1.37, 0.1), 'Stone_Coping')
        p.box((cx, -6.05, 0.96), (w - 0.25, 1.0, 0.08), 'Soil')
    # low front kerb between the planters and the display window
    p.box((-4.65, -5.9, 0.27), (2.9, 0.5, 0.54), 'Stone_Pale')
    p.box((4.65, -5.9, 0.27), (2.9, 0.5, 0.54), 'Stone_Pale')
    p.finish()

    # supply crates in front of the display window
    p = Part('Porch_Crates', 'Porch', 0.012)
    crate(p, (-5.25, -4.85, Z0), (1.15, 0.8, 0.5))
    crate(p, (-3.85, -4.95, Z0), (1.0, 0.7, 0.42))
    crate(p, (3.75, -4.7, Z0), (0.9, 0.7, 0.4))
    p.finish()
    p = Part('Porch_CrateToys', 'Porch', 0.006)
    ball(p, (-5.6, -4.95, Z0 + 0.62), 0.2, 'Product_Orange')
    ball(p, (-5.15, -5.0, Z0 + 0.62), 0.19, 'Product_Red')
    ball(p, (-4.8, -4.95, Z0 + 0.6), 0.16, 'Product_Blue', paw=True)
    bone(p, (-5.25, -5.15, Z0 + 0.58), 'Product_Blue', 0.4, 0.06, 0.15)
    for i in range(3):
        p.cyl((-4.15 + i * 0.25, -4.95, Z0 + 0.54), 0.1, 0.22, ('Product_Teal', 'Product_Coral', 'Product_Teal')[i], 8)
        p.cyl((-4.15 + i * 0.25, -4.95, Z0 + 0.66), 0.105, 0.03, 'Product_White', 8)
    p.finish()

    # bowls, balls and food bag by the door
    p = Part('Porch_PetSupplies', 'Porch', 0.006)
    p.cyl((2.0, -4.9, Z0 + 0.09), 0.32, 0.18, 'Product_Coral', 14, r2=0.38)
    p.cyl((2.0, -4.9, Z0 + 0.17), 0.3, 0.02, 'Bone_Cream', 14)
    p.cyl((2.0, -5.25, Z0 + 0.09), 0.07, 0.01, 'Product_White', 8, 'Y')
    ball(p, (2.85, -5.0, Z0 + 0.3), 0.3, 'Product_Blue', paw=True)
    bag(p, (3.75, -4.75, Z0 + 0.4), 'Product_Coral', (0.42, 0.24, 0.55))
    p.finish()

    # lanterns
    lantern('Lantern_FrontLeftCorner', (W_X0 + 0.05, W_YF - 0.75, 3.3), (0, 0.5, 0))
    lantern('Lantern_Door_Left', (-BAY_X + 0.05, BAY_Y - 0.75, 3.15), (0, 0.5, 0))
    lantern('Lantern_Door_Right', (BAY_X - 0.05, BAY_Y - 0.75, 3.15), (0, 0.5, 0))
    lantern('Lantern_FrontRightCorner', (W_X1 - 0.05, W_YF - 0.75, 3.3), (0, 0.5, 0))
    for nm, loc, e in (('Interior_Light_Display', (-5, -1.5, 3.6), 60), ('Interior_Light_Door', (0, -1.0, 3.6), 50),
                       ('Interior_Light_Side', (5, -1.5, 3.6), 40)):
        li = bpy.data.lights.new(nm, 'POINT'); li.energy = e; li.color = (1, 0.72, 0.42)
        lo = bpy.data.objects.new(nm, li); lo.location = loc; coll('Porch').objects.link(lo)


# ---------------------------------------------------------------- plants ----
LEAVES = ('Leaf_DeepGreen', 'Leaf_Green', 'Leaf_LimeGreen')


def leaf(p, base, direction, length, width, mat):
    """single low-poly leaf with a raised mid-rib (6 verts)"""
    d = Vector(direction).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(d).normalized()
    b = Vector(base)
    tip = b + d * length + up * (-0.12 * length)          # droop
    v = [b, b + d * length * 0.35 + side * width / 2, b + d * length * 0.7 + side * width * 0.35 + up * 0.02,
         tip, b + d * length * 0.7 - side * width * 0.35 + up * 0.02, b + d * length * 0.35 - side * width / 2,
         b + d * length * 0.5 + up * 0.05]
    p.poly(v, [(0, 1, 6), (1, 2, 6), (2, 3, 6), (3, 4, 6), (4, 5, 6), (5, 0, 6)], mat)


def hibiscus(p, c, r, mat, facing=(0, -1, 0.5)):
    n = Vector(facing).normalized()
    q = n.to_track_quat('Z', 'Y').to_matrix()
    c = Vector(c)
    for k in range(5):
        a = k / 5 * 2 * math.pi
        a1, a2 = a - 0.5, a + 0.5
        pts = [c, c + q @ Vector((math.cos(a1) * r, math.sin(a1) * r, 0.04)),
               c + q @ Vector((math.cos(a) * r * 1.15, math.sin(a) * r * 1.15, 0.08)),
               c + q @ Vector((math.cos(a2) * r, math.sin(a2) * r, 0.04))]
        p.poly(pts, [(0, 1, 2, 3)], mat)
    p.cyl(c + n * 0.06, r * 0.12, r * 0.6, 'Flower_Pollen', 6, rot=q)


def plant_cluster(name, c, radius, n_leaves, flowers=(), height=1.0, seed=0):
    rnd = random.Random(seed)
    p = Part(name, 'Plants', 0)
    c = Vector(c)
    n_leaves, height, flowers = int(n_leaves * 1.8), height * 1.25, tuple(flowers) * 2   # lush, like the art
    for i in range(n_leaves):
        a = rnd.uniform(0, 2 * math.pi)
        tilt = rnd.uniform(0.35, 1.2)
        d = Vector((math.cos(a) * math.cos(tilt), math.sin(a) * math.cos(tilt), math.sin(tilt)))
        base = c + Vector((math.cos(a) * radius * 0.25, math.sin(a) * radius * 0.25, 0))
        leaf(p, base, d, rnd.uniform(0.55, 1.0) * height, rnd.uniform(0.22, 0.34) * height, rnd.choice(LEAVES))
    for i, m in enumerate(flowers):
        a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)        # mostly on the front side
        rr = rnd.uniform(0.2, 0.75) * radius
        pos = c + Vector((math.cos(a) * rr, math.sin(a) * rr, rnd.uniform(0.25, 0.65) * height))
        hibiscus(p, pos, rnd.uniform(0.13, 0.19), m, (math.cos(a) * 0.6, math.sin(a) * 0.6 - 0.4, 0.6))
    p.finish()


def palm(name, c, h, seed):
    rnd = random.Random(seed)
    p = Part(name, 'Plants', 0)
    c = Vector(c)
    lean = Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.1, 0.2), 1)).normalized()
    pts = [c + lean * h * k / 6 + Vector((0, 0, 0)) for k in range(7)]
    for k in range(6):
        p.beam(pts[k], pts[k + 1], 0.42 - k * 0.04, 0.42 - k * 0.04, 'Palm_Trunk', 0.04)
    top = pts[-1]
    for k in range(9):
        a = k / 9 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        d1 = Vector((math.cos(a), math.sin(a), 0.45))
        mid = top + d1.normalized() * 1.6
        leaf(p, top, d1, 1.7, 0.75, 'Leaf_Palm')
        leaf(p, mid, Vector((math.cos(a), math.sin(a), -0.5)), 1.5, 0.6, 'Leaf_Palm')
    p.finish()


def vine(name, start, length, seed):
    rnd = random.Random(seed)
    p = Part(name, 'Plants', 0)
    a = Vector(start)
    for k in range(int(length / 0.18)):
        b = a + Vector((rnd.uniform(-0.05, 0.05), -0.01, -0.18))
        p.beam(a, b, 0.03, 0.03, 'Leaf_DeepGreen')
        leaf(p, b, Vector((rnd.choice((-1, 1)) * 0.8, -0.6, -0.2)), 0.2, 0.13, rnd.choice(LEAVES))
        a = b
    p.finish()


def build_plants():
    F = ('Flower_Red', 'Flower_Orange', 'Flower_White', 'Flower_Pink')
    plant_cluster('Plant_PlanterLeft', (-6.85, -6.05, 1.0), 1.2, 16, (F[0], F[2], F[0]), 1.0, 1)
    plant_cluster('Plant_StepLeft', (-2.8, -6.05, 1.0), 1.0, 14, (F[0], F[1], F[2], F[0]), 1.0, 2)
    plant_cluster('Plant_StepRight', (2.8, -6.05, 1.0), 1.0, 12, (F[1], F[0]), 0.9, 3)
    plant_cluster('Plant_PlanterRight', (6.85, -6.05, 1.0), 1.2, 16, (F[0], F[3], F[0]), 1.0, 4)
    plant_cluster('Plant_CornerLeft', (-8.0, -4.3, Z0), 1.4, 18, (F[0],), 1.4, 5)
    plant_cluster('Plant_CornerRight', (8.0, -4.3, Z0), 1.4, 18, (F[0], F[1]), 1.4, 6)
    plant_cluster('Plant_DoorRight', (3.2, -4.3, Z0), 0.9, 12, (), 1.1, 7)
    plant_cluster('Plant_DoorLeft', (-3.0, -4.25, Z0), 0.8, 10, (F[0],), 0.9, 8)
    palm('Palm_BackLeft', (-8.6, 3.8, 0), 7.0, 9)
    palm('Palm_BackRight', (8.7, 3.5, 0), 7.4, 10)
    plant_cluster('Plant_BackLeft', (-8.6, 2.0, 0), 1.6, 14, (), 1.6, 11)
    plant_cluster('Plant_BackRight', (8.6, 1.5, 0), 1.6, 14, (), 1.6, 12)
    vine('Vine_PlanterLeft', (-7.4, -6.7, 0.95), 0.75, 13)
    vine('Vine_StepLeft', (-2.6, -6.7, 0.95), 0.8, 14)
    vine('Vine_PlanterRight', (7.2, -6.7, 0.95), 0.7, 15)


# ---------------------------------------------------------------- camera ----
def build_camera_and_lights():
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('Camera_ThreeQuarter')
    cam.lens = 40
    co = bpy.data.objects.new('Camera_ThreeQuarter', cam)
    co.location = (7.5, -26.0, 7.8)
    co.rotation_euler = (Vector((0.0, 0.0, 3.7)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    coll('CameraAndLights').objects.link(co)
    sc.camera = co
    sun = bpy.data.lights.new('Sun_Key', 'SUN'); sun.energy = 3.2; sun.angle = math.radians(12)
    so = bpy.data.objects.new('Sun_Key', sun); so.location = (-8, -12, 18)
    so.rotation_euler = (math.radians(50), 0, math.radians(-35))
    coll('CameraAndLights').objects.link(so)
    area = bpy.data.lights.new('Area_Fill', 'AREA'); area.energy = 1800; area.size = 12
    ao = bpy.data.objects.new('Area_Fill', area); ao.location = (6, -18, 6)
    ao.rotation_euler = (Vector((0, 0, 3)) - ao.location).to_track_quat('-Z', 'Y').to_euler()
    coll('CameraAndLights').objects.link(ao)
    # soft cream studio world (as PetClinic)
    w = bpy.data.worlds.new('World_Cream')
    sc.world = w
    nt = w.node_tree
    bg = nt.nodes['Background']
    bg.inputs['Color'].default_value = (0.965, 0.871, 0.723, 1)
    bg.inputs['Strength'].default_value = 0.9
    sc.render.resolution_x, sc.render.resolution_y = 1536, 1024
    # ground catcher so the building sits on something
    p = Part('Ground_Shadow', 'CameraAndLights', 0)
    p.box((0, 0, -0.01), (60, 60, 0.02), 'Stone_Coping')
    g = p.finish()
    g.is_shadow_catcher = True


# ---------------------------------------------------------------- main ------
def main():
    reset_scene()
    build_materials()
    for c in ('Building', 'Roof', 'Awning', 'WindowsAndDoors', 'Sign', 'ShopDisplays', 'Porch', 'Plants',
              'CameraAndLights'):
        coll(c)
    build_building()
    build_roof()
    build_awning()
    build_windows_doors()
    build_sign()
    build_shop_displays()
    build_porch()
    build_plants()
    build_camera_and_lights()
    path = os.path.join(HERE, 'PetMart.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    faces = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    print(f'Pet Mart: {len(bpy.data.objects)} objects, {faces} faces')
    print('Saved:', path)


if __name__ == '__main__':
    main()
