"""Export the fire pets from FirePets.blend to Roblox-ready FBX files.

Roblox MeshParts show one texture per part and ignore vertex colours and Blender's shader setups, so each
pet's look (fire gradients, flame markings, eyes, lava, crystals) is baked into one colour texture:

    exports/FirePets/<Pet>.fbx            three MeshParts: <Pet>_Body (body, legs, paws), <Pet>_Head (head,
                                          eyes, ears, face) and <Pet>_Fire (tail, flames, markings, lava,
                                          crystals); each under Roblox's 20k triangle limit
    exports/FirePets/<Pet>_Texture.png    the shared 1024x1024 colour texture (also embedded in the FBX)

Each pet is exported on its own at the origin: pivot between the feet on the ground, facing Roblox -Z
(the default front / LookVector), Y up, PET_STUDS studs per Blender metre (Ashrat ~3 studs tall).

    python3 export_fire_pets.py            (with the `bpy` pip module; reads FirePets.blend next to this file)
"""
import bpy, bmesh, math, os, json
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'exports', 'FirePets')
PETS = ('Ashrat', 'Cinderkit', 'Flarecat', 'Smoulderat')
PET_STUDS = 3.0          # studs per Blender metre
TEX = 1024               # Roblox's maximum texture size
HEAD_PARTS = ('Head', 'Eye', 'Ear', 'Nose', 'Mouth', 'Teeth', 'Whiskers')   # each part < 20k tris
FIRE_PARTS = ('Tail', 'FlameMarkings', 'CheekSwirls', 'FlameTuft', 'FaceFlames', 'FlameMane', 'ChestRuff',
              'LavaFissures', 'BackCrystals', 'HeadCrystals', 'BrowMarks')


def select_only(objs, active=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def merged(pet, parts, name, coll):
    """copy the pet's parts into one object, in pet-local space (pivot = the pet's root)"""
    root = bpy.data.objects[f'{pet}_Root']
    inv = root.matrix_world.inverted()
    bm = bmesh.new()
    mats = []
    for ob in parts:
        me = ob.data.copy()
        me.transform(inv @ ob.matrix_world)
        offset = len(mats)
        mats += list(me.materials)
        for p in me.polygons:
            p.material_index += offset
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def export_pet(pet, coll):
    objs = [o for o in bpy.data.collections[pet].objects if o.type == 'MESH']
    kind = lambda o: o.name.split('_', 1)[1]
    fire = [o for o in objs if kind(o) in FIRE_PARTS]
    head = [o for o in objs if o not in fire and kind(o).startswith(HEAD_PARTS)]
    body = [o for o in objs if o not in fire and o not in head]
    parts = [merged(pet, body, f'{pet}_Body_x', coll), merged(pet, head, f'{pet}_Head_x', coll),
             merged(pet, fire, f'{pet}_Fire_x', coll)]
    for o in objs:                    # the source parts are no longer needed; free their names
        bpy.data.objects.remove(o)
    for ob in parts:
        ob.name = ob.data.name = ob.name[:-2]

    # one shared UV atlas for both parts
    select_only(parts)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.0,
                             scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # bake the base colour (incl. the vertex-colour gradients) of every material into the atlas
    img = bpy.data.images.new(f'{pet}_Texture', TEX, TEX, alpha=False)
    for ob in parts:
        for m in ob.data.materials:
            nt = m.node_tree
            node = nt.nodes.get('_bake') or nt.nodes.new('ShaderNodeTexImage')
            node.name, node.image = '_bake', img
            nt.nodes.active = node
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 4
    sc.render.bake.use_pass_direct = False
    sc.render.bake.use_pass_indirect = False
    sc.render.bake.use_pass_color = True
    sc.render.bake.margin = 6
    select_only(parts)
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=6)
    png = os.path.join(OUT, f'{pet}_Texture.png')
    img.filepath_raw = png
    img.file_format = 'PNG'
    img.save()
    for m in {m for ob in parts for m in ob.data.materials}:     # materials are shared between parts
        m.node_tree.nodes.remove(m.node_tree.nodes['_bake'])

    # single textured material, face Roblox -Z, scale to studs, apply
    mat = bpy.data.materials.new(f'{pet}_Mat')
    bsdf = mat.node_tree.nodes['Principled BSDF']
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(png)
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.6
    tris = {}
    for ob in parts:
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        ob.data.transform(Matrix.Scale(PET_STUDS, 4) @ Matrix.Rotation(math.pi, 4, 'Z'))
        ob.data.update()
        tris[ob.name] = sum(len(p.vertices) - 2 for p in ob.data.polygons)

    path = os.path.join(OUT, f'{pet}.fbx')
    select_only(parts)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'},
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=False,
                             add_leaf_bones=False, bake_anim=False, path_mode='COPY', embed_textures=True,
                             use_custom_props=False)
    dims = [max(v.co[i] for o in parts for v in o.data.vertices) - min(v.co[i] for o in parts for v in o.data.vertices)
            for i in range(3)]
    info = dict(parts=tris, triangles=sum(tris.values()), size_studs_wide_long_tall=[round(d, 2) for d in dims],
                fbx_mb=round(os.path.getsize(path) / 1e6, 2))
    print(pet, info)
    for ob in parts:
        bpy.data.objects.remove(ob)
    return info


def main():
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'FirePets.blend'))
    coll = bpy.data.collections.new('_EXPORT')
    bpy.context.scene.collection.children.link(coll)
    manifest = {pet: export_pet(pet, coll) for pet in PETS}
    manifest['_notes'] = dict(studs_per_metre=PET_STUDS, texture_px=TEX, front='-Z', up='+Y', pivot='feet, ground')
    with open(os.path.join(OUT, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)


if __name__ == '__main__':
    main()
