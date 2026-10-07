"""BOULDERBUB - Earth / Common pet. Low-poly toy-style rock creature for Roblox.

Game-scale dimensions (metric, 1 unit = 1 m; ~1 m = 3.5 studs in Roblox):
    overall          : ~1.55 m wide (X, incl. arms) x ~1.25 m deep (Y) x ~1.75 m tall (Z, incl. sprout)
    boulder body     : 1.30 m wide x 1.20 m deep x 1.18 m tall, centre at z = 0.80
    eyes             : 0.40 m tall each, set into the upper front of the body
    feet             : 0.50 x 0.44 x 0.26 m, standing on z = 0 (the ground plane)
    sprout           : top of the leaves at ~1.75 m
Creature is centred on the world origin, standing on the ground, facing -Y.
Every part is a separate editable mesh with rotation/scale applied (identity
transforms); each object's origin sits at the centre of its part.

Run in Blender (Scripting tab -> Run Script) or headless:
    blender -b -P boulderbub.py
    python3 boulderbub.py          (with the `bpy` pip module)
Saves Boulderbub.blend next to this script and prints the full path.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

# ------------------------------------------------------------------ body shape
BODY_C = Vector((0.0, 0.0, 0.80))     # body centre
BODY_R = Vector((0.65, 0.60, 0.59))   # body radii (slightly squat boulder)


def body_point(theta, phi, push=0.0):
    """Point + outward normal on the body ellipsoid.
    theta: angle around Z, 0 = front (-Y), +90deg = creature's left (+X)
    phi:   elevation, 0 = equator, +90deg = top"""
    d = Vector((math.sin(theta) * math.cos(phi), -math.cos(theta) * math.cos(phi), math.sin(phi)))
    p = BODY_C + Vector((d.x * BODY_R.x, d.y * BODY_R.y, d.z * BODY_R.z))
    n = Vector((d.x / BODY_R.x, d.y / BODY_R.y, d.z / BODY_R.z)).normalized()
    return p + n * push, n


# ------------------------------------------------------------------ materials
MATS = {}


def material(name, rgb, rough=0.45, coat=0.25, emit=0.0, variation=0.0):
    """lightly glossy toy material; optional subtle mottling for stone"""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = 0.2
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    if variation:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 6.0
        nz.inputs['Detail'].default_value = 2.0
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = tuple(c * (1 - variation) for c in rgb) + (1,)
        ramp.color_ramp.elements[1].color = tuple(min(1, c * (1 + variation)) for c in rgb) + (1,)
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m


def build_materials():
    # (linear colour values; the comment gives the sRGB / Roblox Color3 equivalent)
    material('Stone_Taupe', (0.23, 0.175, 0.135), 0.5, 0.2, variation=0.12)       # ~133,117,103 body
    material('Stone_WarmGray', (0.2, 0.16, 0.13), 0.5, 0.2, variation=0.12)     # ~124,112,101 plates
    material('Stone_Sandy', (0.36, 0.25, 0.15), 0.5, 0.2, variation=0.1)         # ~162,137,108 lighter plates
    material('Stone_TanBelly', (0.5, 0.36, 0.2), 0.45, 0.25, variation=0.08)   # ~188,162,124 belly patch
    material('Stone_Dark', (0.15, 0.12, 0.095), 0.5, 0.2, variation=0.12)         # ~108,97,87 arms & feet
    material('Eye_Socket', (0.10, 0.075, 0.06), 0.4, 0.3)                        # ~89,77,69 recessed rim
    material('Eye_Iris', (0.05, 0.022, 0.013), 0.22, 0.25)                          # ~53,33,25 glossy brown
    material('Eye_Pupil', (0.006, 0.004, 0.004), 0.2, 0.25)                     # ~13,11,11 glossy black
    material('Eye_Highlight', (1.0, 1.0, 1.0), 0.2, 0.0, emit=0.6)               # white
    material('Mouth_Dark', (0.05, 0.025, 0.018), 0.35, 0.4)                      # ~63,44,37
    material('Moss_Green', (0.17, 0.5, 0.012), 0.85, 0.0, variation=0.15)        # ~124,180,28 soft moss
    material('Moss_Light', (0.32, 0.6, 0.04), 0.85, 0.0)                         # ~153,203,56
    material('Leaf_Green', (0.12, 0.45, 0.04), 0.35, 0.5)                        # ~97,180,56 sprout
    material('Stem_Green', (0.10, 0.35, 0.03), 0.4, 0.3)                         # ~89,160,48


# ------------------------------------------------------------------ helpers
COLL = None


def new_object(name, bm, mat, smooth=False, bevel=0.0, center=None):
    """bmesh -> object, origin moved to `center` (or bbox centre); identity rot/scale"""
    if center is None:
        vs = [v.co for v in bm.verts]
        center = sum(vs, Vector()) / len(vs)
    for v in bm.verts:
        v.co -= center
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS[mat])
    if smooth:
        me.shade_smooth()
    else:
        me.shade_flat()
    ob = bpy.data.objects.new(name, me)
    ob.location = center
    COLL.objects.link(ob)
    if bevel:
        bv = ob.modifiers.new('Bevel', 'BEVEL')
        bv.width = bevel
        bv.segments = 1
        bv.limit_method = 'ANGLE'
        bv.angle_limit = math.radians(20)
    return ob


def rock_bm(size, seed, subdiv=1, jitter=0.12, flat_bottom=None):
    """chunky faceted stone: jittered icosphere scaled to `size` (x, y, z)"""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    for v in bm.verts:
        v.co *= 1.0 + rnd.uniform(-jitter, jitter)
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        if flat_bottom is not None and v.co.z < flat_bottom:
            v.co.z = flat_bottom
    return bm


def place(bm, location, rot=None, align=None, spin=0.0):
    """rotate (Euler or align local +Z to a normal, then spin about it) and move"""
    if align is not None:
        M = Vector(align).to_track_quat('Z', 'Y').to_matrix() @ Matrix.Rotation(spin, 3, 'Z')
    elif rot is not None:
        M = Euler(rot).to_matrix()
    else:
        M = Matrix.Identity(3)
    for v in bm.verts:
        v.co = M @ v.co + Vector(location)
    return bm


def rock(name, location, size, seed, mat, subdiv=1, jitter=0.12, rot=None, align=None, spin=0.0,
         flat_bottom=None, bevel=0.008):
    bm = place(rock_bm(size, seed, subdiv, jitter, flat_bottom), location, rot, align, spin)
    return new_object(name, bm, mat, smooth=False, bevel=bevel, center=Vector(location))


def plate(name, theta, phi, size, seed, mat, sink=0.35, spin=0.0, subdiv=1):
    """stone plate hugging the body: centred on the surface, local Z along the normal,
    sunk into the body by `sink` x thickness so it stays attached"""
    p, n = body_point(math.radians(theta), math.radians(phi))
    loc = p + n * size[2] * (1 - 2 * sink)
    return rock(name, loc, size, seed, mat, subdiv, 0.14, align=n, spin=spin)


# ------------------------------------------------------------------ parts
def build_body():
    rnd = random.Random(1)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    # merge into larger facets: dissolve shallow edges after jittering
    for v in bm.verts:
        v.co *= 1.0 + rnd.uniform(-0.025, 0.025)
        v.co = Vector((v.co.x * BODY_R.x, v.co.y * BODY_R.y, v.co.z * BODY_R.z))
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(5.5), verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    place(bm, BODY_C)
    new_object('Body', bm, 'Stone_Taupe', smooth=False, bevel=0.006, center=BODY_C.copy())

    # light tan patch on the lower front belly (big, flat, faceted, set into the body)
    p, n = body_point(math.radians(6), math.radians(-38))
    bm = rock_bm((0.4, 0.27, 0.1), 11, subdiv=2, jitter=0.07)
    place(bm, p - n * 0.025, align=n, spin=math.radians(6))
    new_object('Belly_Patch', bm, 'Stone_TanBelly', bevel=0.008, center=p)


def build_plates():
    # (name, theta, phi, size, seed, material, spin)  theta: 0 front, -90 = creature's right (viewer left)
    P = [
        ('Plate_ShoulderRight_Big', -62, 38, (0.27, 0.22, 0.13), 21, 'Stone_Sandy', 0.4),
        ('Plate_ShoulderRight_Back', -95, 30, (0.22, 0.2, 0.12), 22, 'Stone_WarmGray', 1.1),
        ('Plate_TopRight_Pebble', -32, 58, (0.12, 0.09, 0.07), 23, 'Stone_Sandy', 0.2),
        ('Plate_SideRight_Upper', -82, 8, (0.15, 0.13, 0.09), 24, 'Stone_WarmGray', 0.7),
        ('Plate_SideRight_Lower', -95, -14, (0.2, 0.17, 0.11), 25, 'Stone_WarmGray', 0.3),
        ('Plate_ShoulderLeft_Pebble', 52, 50, (0.15, 0.11, 0.08), 26, 'Stone_Sandy', -0.3),
        ('Plate_SideLeft', 82, 22, (0.11, 0.1, 0.07), 27, 'Stone_Sandy', 0.4),
        ('Plate_BackTop', 160, 45, (0.24, 0.2, 0.12), 28, 'Stone_WarmGray', 0.2),
        ('Plate_BackLower', 200, -5, (0.26, 0.2, 0.12), 29, 'Stone_WarmGray', 0.9),
        ('Plate_LowerFrontRight', -42, -38, (0.14, 0.12, 0.08), 30, 'Stone_WarmGray', 0.5),
    ]
    for name, th, ph, size, seed, mat, spin in P:
        plate(name, th, ph, size, seed, mat, 0.35, spin)


def build_arms_and_feet():
    # creature's right arm (viewer's left): two stacked chunky stones
    p, n = body_point(math.radians(-88), math.radians(-12))
    rock('Arm_Right', p + n * 0.1 + Vector((0, -0.08, -0.05)), (0.2, 0.19, 0.24), 41, 'Stone_Dark',
         rot=(0.3, 0.2, 0.4))
    p2, n2 = body_point(math.radians(-80), math.radians(12))
    rock('Arm_Right_Upper', p2 + n2 * 0.08 + Vector((0, -0.06, 0)), (0.17, 0.15, 0.14), 42, 'Stone_Sandy',
         rot=(0.5, -0.2, 0.9))
    # creature's left arm (viewer's right): one stubby stone + small cap plate
    p, n = body_point(math.radians(86), math.radians(-14))
    rock('Arm_Left', p + n * 0.09 + Vector((0, -0.04, -0.03)), (0.17, 0.16, 0.22), 43, 'Stone_Dark',
         rot=(-0.2, -0.3, -0.5))
    p2, n2 = body_point(math.radians(78), math.radians(8))
    rock('Arm_Left_Cap', p2 + n2 * 0.05, (0.1, 0.09, 0.08), 44, 'Stone_Sandy', rot=(0.4, 0.3, 0.2))
    # broad blocky feet (flat soles on the ground)
    for s, side, seed in ((-1, 'Right', 51), (1, 'Left', 52)):
        rock(f'Foot_{side}', (s * 0.3, -0.07, 0.15), (0.27, 0.24, 0.16), seed, 'Stone_Dark',
             rot=(0, 0, s * 0.12), flat_bottom=-0.15)


def disc(name, center, normal, rx, rz, depth, mat, segs=16, smooth=True, front_bulge=0.4):
    """low-poly rounded lens (eye / iris / pupil), facing along `normal` (outward)"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=8, radius=1.0)
    for v in bm.verts:
        z = v.co.z
        v.co = Vector((v.co.x * rx, v.co.y * rz, z * depth * (front_bulge if z < 0 else 1.0)))
    n = Vector(normal).normalized()
    # local Z -> outward normal, local Y -> world up
    zax = n
    xax = Vector((0, 0, 1)).cross(zax).normalized()
    yax = zax.cross(xax)
    M = Matrix((xax, yax, zax)).transposed()
    for v in bm.verts:
        v.co = M @ v.co + Vector(center)
    return new_object(name, bm, mat, smooth=smooth, center=Vector(center))


def build_face():
    for s, side in ((-1, 'Right'), (1, 'Left')):
        theta, phi = math.radians(s * 27), math.radians(15)
        p, n = body_point(theta, phi)
        disc(f'Eye_{side}_Socket', p - n * 0.02, n, 0.2, 0.225, 0.05, 'Eye_Socket', 18)
        disc(f'Eye_{side}', p + n * 0.01, n, 0.17, 0.195, 0.075, 'Eye_Iris', 18)
        disc(f'Eye_{side}_Pupil', p + n * 0.06, n, 0.115, 0.13, 0.035, 'Eye_Pupil', 16)
        # highlights: a big one up toward the centre + a small one below it
        xax = Vector((0, 0, 1)).cross(n).normalized()
        up = n.cross(xax)
        disc(f'Eye_{side}_Highlight', p + n * 0.1 + xax * (-s * 0.055) + up * 0.075, n,
             0.05, 0.05, 0.02, 'Eye_Highlight', 10)
        disc(f'Eye_{side}_Highlight_Small', p + n * 0.095 + xax * (-s * 0.095) + up * -0.005, n,
             0.022, 0.022, 0.012, 'Eye_Highlight', 8)
    # smile: small curved tube between and below the eyes
    bm = bmesh.new()
    pts = []
    for i in range(9):
        t = -1 + 2 * i / 8
        th, ph = math.radians(3 + t * 6), math.radians(2 - 4.0 * (1 - t * t))
        p, n = body_point(th, ph, 0.004)
        pts.append((p, n))
    r = 0.022
    rings = []
    for i, (p, n) in enumerate(pts):
        a = pts[min(i + 1, len(pts) - 1)][0] - pts[max(i - 1, 0)][0]
        a.normalize()
        b = n.cross(a).normalized()
        ring = []
        for k in range(6):
            ang = k / 6 * 2 * math.pi
            ring.append(bm.verts.new(p + (n * math.cos(ang) + b * math.sin(ang)) * r * (0.6 if i in (0, 8) else 1)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(6):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % 6], rings[i + 1][(k + 1) % 6], rings[i + 1][k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    new_object('Mouth', bm, 'Mouth_Dark', smooth=True)


def blob_cluster(name, center, normal, blobs, mat, seed):
    """soft moss: several flattened, lightly jittered spheres merged in one mesh"""
    rnd = random.Random(seed)
    n = Vector(normal).normalized()
    M = n.to_track_quat('Z', 'Y').to_matrix()
    bm = bmesh.new()
    for (dx, dy, r, h) in blobs:
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=2, radius=1.0)
        for v in tmp.verts:
            v.co *= 1.0 + rnd.uniform(-0.06, 0.06)
            v.co = Vector((v.co.x * r, v.co.y * r, max(v.co.z, -0.3) * h))
            v.co = M @ (v.co + Vector((dx, dy, 0))) + Vector(center)
        me = bpy.data.meshes.new('tmp')
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    return new_object(name, bm, mat, smooth=True, center=Vector(center))


def leaf_bm(length, width, cup=0.03, thick=0.012):
    """teardrop leaf in its own XY plane (base at origin, tip along +Y), slightly cupped"""
    n = 10
    outline = []
    for i in range(n + 1):
        t = i / n
        w = width * math.sin(math.pi * t) ** 0.8 * (1 - 0.35 * t)
        outline.append((t * length, w))
    pts = [(w, y) for y, w in outline] + [(-w, y) for y, w in outline[::-1][1:-1]]
    bm = bmesh.new()
    top = [bm.verts.new((x, y, cup * (x / max(width, 1e-6)) ** 2 + thick / 2)) for x, y in pts]
    bot = [bm.verts.new((x, y, cup * (x / max(width, 1e-6)) ** 2 - thick / 2)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((top[i], top[j], bot[j], bot[i]))
    # midrib fold
    for v in top + bot:
        v.co.z -= 0.012 * (1 - abs(v.co.x) / width) * (v.co.y / length)
    return bm


def build_moss_and_sprout():
    top, nt = body_point(math.radians(-5), math.radians(78))
    blob_cluster('Moss_Top', top + nt * -0.01, nt,
                 [(0, 0, 0.21, 0.14), (0.17, 0.05, 0.15, 0.12), (-0.16, 0.02, 0.15, 0.12), (0.06, 0.17, 0.15, 0.11),
                  (-0.06, -0.16, 0.14, 0.1), (0.2, -0.12, 0.1, 0.08), (-0.22, 0.14, 0.1, 0.07)], 'Moss_Green', 61)
    side, ns = body_point(math.radians(-78), math.radians(30))
    blob_cluster('Moss_Side', side + ns * 0.0, ns,
                 [(0, 0, 0.11, 0.07), (0.08, 0.07, 0.08, 0.06), (-0.07, -0.06, 0.08, 0.055)], 'Moss_Light', 62)

    # sprout stem: short curved tube rising from the moss
    base = top + nt * 0.06
    bm = bmesh.new()
    path = [base + Vector((0.012 * math.sin(t * 2.2), 0, 0.17 * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    rings = []
    for i, p in enumerate(path):
        r = 0.022 - 0.006 * i / 4
        rings.append([bm.verts.new(p + Vector((math.cos(k / 6 * 2 * math.pi) * r, math.sin(k / 6 * 2 * math.pi) * r, 0)))
                      for k in range(6)])
    for i in range(len(rings) - 1):
        for k in range(6):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % 6], rings[i + 1][(k + 1) % 6], rings[i + 1][k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    new_object('Sprout_Stem', bm, 'Stem_Green', smooth=True)
    tip = path[-1]
    # two leaves angling out left and right, slightly forward
    for s, side in ((-1, 'Right'), (1, 'Left')):
        bm = leaf_bm(0.25 if s < 0 else 0.22, 0.085)
        # leaf tip direction
        d = Vector((s * 0.85, -0.25, 0.45)).normalized()
        yax = d
        xax = Vector((0, 0, 1)).cross(yax).normalized()
        if xax.length < 1e-4:
            xax = Vector((1, 0, 0))
        zax = xax.cross(yax).normalized()
        M = Matrix((xax, yax, zax)).transposed()
        for v in bm.verts:
            v.co = M @ v.co + tip - Vector((0, 0, 0.01))
        new_object(f'Sprout_Leaf_{side}', bm, 'Leaf_Green', smooth=True, center=tip.copy())


# ------------------------------------------------------------------ scene
def build_camera_and_lights():
    sc = bpy.context.scene
    lc = bpy.data.collections.new('CameraAndLights')
    sc.collection.children.link(lc)
    cam = bpy.data.cameras.new('Camera_ThreeQuarter')
    cam.lens = 60
    co = bpy.data.objects.new('Camera_ThreeQuarter', cam)
    co.location = (-1.9, -4.6, 1.75)
    co.rotation_euler = (Vector((0.0, 0.0, 0.8)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(co)
    sc.camera = co

    def area(name, loc, energy, size, color=(1, 1, 1)):
        li = bpy.data.lights.new(name, 'AREA')
        li.energy, li.size, li.color = energy, size, color
        o = bpy.data.objects.new(name, li)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0.8)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        lc.objects.link(o)

    area('Light_Key', (-2.5, -3.0, 3.2), 260, 2.5, (1.0, 0.96, 0.9))     # soft warm key
    area('Light_Fill', (3.0, -2.5, 1.6), 110, 3.0, (0.92, 0.95, 1.0))    # cool fill
    area('Light_Rim', (0.5, 3.0, 2.8), 160, 2.0)                         # rim from behind
    w = bpy.data.worlds.new('World_Studio')
    sc.world = w
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.92, 0.88, 0.82, 1)
    bg.inputs['Strength'].default_value = 0.45
    # ground plane that only catches shadows
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
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'


def main():
    global COLL
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    COLL = bpy.data.collections.new('Boulderbub')
    sc.collection.children.link(COLL)
    build_materials()
    build_body()
    build_plates()
    build_arms_and_feet()
    build_face()
    build_moss_and_sprout()
    build_camera_and_lights()
    path = os.path.join(HERE, 'Boulderbub.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    meshes = [o for o in COLL.objects if o.type == 'MESH']
    print(f'Boulderbub: {len(meshes)} mesh objects, {sum(len(o.data.polygons) for o in meshes)} faces')
    print('Saved:', path)


if __name__ == '__main__':
    main()
