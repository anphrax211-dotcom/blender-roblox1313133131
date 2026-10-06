"""Render a preview PNG of every *.fbx in a folder (Cycles CPU) + contact sheet.
    python3 render_previews.py <fbx_dir> <out_dir>"""
import bpy, sys, glob, os, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
src, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
pngs = []
for f in sorted(glob.glob(os.path.join(src, '*.fbx'))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    sc = bpy.context.scene
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (2.2, -7.0, 2.6)
    cam.rotation_euler = (Vector((0, 0, 1.3)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50
    w = bpy.data.worlds.new('w'); sc.world = w
    w.color = (0.55, 0.57, 0.62)
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.5; sun.rotation_euler = (0.8, 0.15, 0.6)
    sc.collection.objects.link(sun)
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.device = 'CPU'
    sc.render.resolution_x = sc.render.resolution_y = 480
    sc.render.film_transparent = False; sc.view_settings.view_transform = 'Standard'
    p = os.path.join(out, os.path.basename(f)[:-4] + '.png')
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    pngs.append(p)
try:
    from PIL import Image, ImageDraw
    cols = 3; rows = (len(pngs) + cols - 1) // cols
    sheet = Image.new('RGB', (480 * cols, 480 * rows), 'white')
    for i, p in enumerate(pngs):
        im = Image.open(p).convert('RGB')
        ImageDraw.Draw(im).text((10, 10), os.path.basename(p)[:-4], fill='white')
        sheet.paste(im, ((i % cols) * 480, (i // cols) * 480))
    sheet.save(os.path.join(out, 'contact_sheet.png'))
except ImportError:
    pass
