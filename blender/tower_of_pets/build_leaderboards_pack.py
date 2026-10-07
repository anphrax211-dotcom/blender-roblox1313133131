"""TOWER OF PETS - Leaderboards monument as its own scene (TowerOfPets_Leaderboards.blend).

    python3 blender/tower_of_pets/build_leaderboards_pack.py         (or blender -b -P ...)

The Leaderboards monument (leaderboard.py) on a patch of hub plaza with the lobby's light, a 5-stud avatar for scale, and the
cameras CAM_Leaderboards_Front (reference perspective), _Boards, _Side, _Player, _Top.
The same build is placed in the lobby on the hub slot the old Leaderboards stand used (225 deg).
"""
import os, sys, importlib, math, random
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import common, foliage, castle, shop, hatchery, trading, leaderboard
for m in (common, foliage, castle, shop, hatchery, trading, leaderboard):
    importlib.reload(m)

OUT = os.path.join(os.path.dirname(HERE), 'TowerOfPets_Leaderboards.blend')


def main(path=OUT):
    common.reset_scene()
    common.build_materials()
    foliage.build_foliage_materials()
    castle.build_castle_materials()
    shop.build_shop_materials()
    leaderboard.build_leaderboard_materials()
    common.coll(common.ASSET_COLL)
    common.build_assets()
    foliage.build_foliage_assets(common.ASSET_COLL)
    castle.build_castle_kit(common.ASSET_COLL)
    shop.build_shop_kit(common.ASSET_COLL)
    leaderboard.build_leaderboard_kit(common.ASSET_COLL)
    bpy.context.view_layer.layer_collection.children[common.ASSET_COLL].exclude = True
    leaderboard.build_leaderboards(None)
    # plaza patch, lawn, scale avatar
    g = common.Part('Ground_Plaza', 'GROUND')
    g.cyl((0, 0, -1.0), 70, 2.0, 'Plaza_Tile', 64)
    g.ring_sector(70, 140, 0, 6.2832, -1.6, -0.05, 'Grass', 64)
    g.box((0, -40, 0.03), (16, 44, 0.06), 'Plaza_Path')
    g.finish()
    common.avatar('SCALE_Avatar_5studs', 'GROUND', (4.0, -22.0, 0), math.pi * 0.9)
    common.avatar('SCALE_Avatar_5studs_Steps', 'GROUND', (-6.0, -2.0, 3.0), math.pi * 1.1)
    rnd = random.Random(2)
    for i in range(14):
        a = rnd.uniform(0, 6.283); r = rnd.uniform(48, 66)
        if 3.5 < a < 5.9 or 0.5 < a < 1.7:      # keep the front and rear camera views clear
            continue
        common.inst(rnd.choice(('Tree_Large_High', 'Tree_Medium_High', 'Tree_Small')), f'Plaza_Tree_{i}', 'GROUND',
                    (math.cos(a) * r, math.sin(a) * r, 0), rnd.uniform(0, 6.28), rnd.uniform(0.9, 1.2))
    for s in (-1, 1):
        common.inst('Castle_Lantern', f'Plaza_Lantern_{s}', 'GROUND', (s * 11, -30, 0), 0, 1.0)
    # sky + sun (same light as the lobby)
    sc = bpy.context.scene
    w = bpy.data.worlds.new('Sky'); sc.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.62, 0.86, 1.0, 1); ramp.color_ramp.elements[1].color = (0.06, 0.38, 1.0, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector']); nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    sun = bpy.data.objects.new('Sun_Key', bpy.data.lights.new('Sun_Key', 'SUN'))
    sun.data.energy = 2.6; sun.data.color = (1.0, 0.96, 0.88); sun.data.angle = math.radians(2.5)
    sun.rotation_euler = Vector((0.45, 0.75, -0.55)).normalized().to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(sun)
    cams = leaderboard.build_leaderboard_cameras(coll_name='CAMERAS')
    sc.camera = cams['Front']
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects
               if o.type == 'MESH' and o not in common.ASSETS.values() and o.name not in common.COLL)
    print(f'Leaderboards scene: ~{tris:,} triangles placed')
    print('Saved:', path)


if __name__ == '__main__':
    main()
