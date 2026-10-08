"""Render the lobby cameras to PNGs.
    python3 render.py <file.blend> <out_dir> [samples] [scale%] [CAM_NAME ...]"""
import bpy, sys, os
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
blend, out = argv[0], argv[1]
samples = int(argv[2]) if len(argv) > 2 else 64
scale = int(argv[3]) if len(argv) > 3 else 100
only = argv[4:]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
sc.cycles.samples = samples
sc.cycles.device = 'CPU'
sc.render.compositor_device = 'CPU'
sc.render.resolution_percentage = scale
os.makedirs(out, exist_ok=True)
for cam in sorted((o for o in bpy.data.objects if o.type == 'CAMERA'), key=lambda o: o.name):
    if only and cam.name not in only:
        continue
    sc.camera = cam
    hidden = [c for c in cam.get('hide_collections', '').split(',') if c]
    for c in hidden:
        bpy.data.collections[c].hide_render = True
    sc.render.filepath = os.path.join(out, f'TowerOfPets_{cam.name}.png')
    comp = getattr(sc, 'compositing_node_group', None)
    if cam.get('no_haze') and comp is not None:          # e.g. the high top-down map camera
        sc.compositing_node_group = None
    bpy.ops.render.render(write_still=True)
    if cam.get('no_haze') and comp is not None:
        sc.compositing_node_group = comp
    for c in hidden:
        bpy.data.collections[c].hide_render = False
    print('rendered', sc.render.filepath, flush=True)
