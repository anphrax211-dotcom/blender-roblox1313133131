"""TOWER OF PETS - NPC animation set (shared by all 12 NPCs).

One source of truth for the NPC animations:
  * CLIPS below define every clip as keyframes per R15 joint, in CHARACTER space
    (X = character's right, Y = up, Z = character's back; degrees / metres).
  * This script opens TowerOfPets_NPCs.blend, gives every NPC an R15 armature (bones at the
    joint pivots, every part bone-parented), bakes all clips into Blender actions, lines them
    up on each NPC's NLA timeline as a demo reel, and saves TowerOfPets_NPCs_Animated.blend.
  * It also writes ../roblox/NPCAnimationData.lua with the same clips + per-NPC rig data, which
    the Roblox runtime (../roblox) plays on Motor6D joints - no animation uploads needed.

Clips (gesture clips are authored for the right arm and mirrored for left-handed NPCs):
    Idle        4.0 s loop   breathing, gentle sway, looking around
    IdleHover   4.0 s loop   Tower Entrance only: floats above the ground
    Talk        2.4 s loop   head nods / tilts, torso turns, hand gestures (mouth is procedural)
    Wave        2.4 s        greeting wave
    Point       2.0 s        "over here!" presenting gesture
    Nod         1.2 s        yes
    Shake       1.2 s        no
    Celebrate   1.8 s        hop with both arms up
    Think       2.6 s        hand to chin
    Bow         2.0 s        polite bow

Run:  python3 npc_animations.py   (bpy pip module)   or   blender -b -P npc_animations.py
"""
import bpy, math, os, json
from mathutils import Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
FPS = 30
R15 = ['LowerTorso', 'UpperTorso', 'Head',
       'RightUpperArm', 'RightLowerArm', 'RightHand', 'LeftUpperArm', 'LeftLowerArm', 'LeftHand',
       'RightUpperLeg', 'RightLowerLeg', 'RightFoot', 'LeftUpperLeg', 'LeftLowerLeg', 'LeftFoot']
PARENT = {'UpperTorso': 'LowerTorso', 'Head': 'UpperTorso',
          'RightUpperArm': 'UpperTorso', 'RightLowerArm': 'RightUpperArm', 'RightHand': 'RightLowerArm',
          'LeftUpperArm': 'UpperTorso', 'LeftLowerArm': 'LeftUpperArm', 'LeftHand': 'LeftLowerArm',
          'RightUpperLeg': 'LowerTorso', 'RightLowerLeg': 'RightUpperLeg', 'RightFoot': 'RightLowerLeg',
          'LeftUpperLeg': 'LowerTorso', 'LeftLowerLeg': 'LeftUpperLeg', 'LeftFoot': 'LeftLowerLeg'}


# ------------------------------------------------------------------ clip authoring
def K(t, rx=0.0, ry=0.0, rz=0.0, tx=0.0, ty=0.0, tz=0.0):
    """one key: time (s), rotation (deg, char axes), translation (m, char axes)"""
    return [t, rx, ry, rz, tx, ty, tz]


def sym(keys):
    """mirror right-side keys for the left side (x -> -x): negate ry, rz, tx"""
    return [[k[0], k[1], -k[2], -k[3], -k[4], k[5], k[6]] for k in keys]


def idle_clip(hover=False):
    lift = 0.07 if hover else 0.0
    bob = 0.035 if hover else 0.006
    j = {
        'LowerTorso': [K(0, ty=lift), K(1, rz=0.8, ty=lift + bob * 0.5), K(2, ty=lift + bob), K(3, rz=-0.8, ty=lift + bob * 0.5),
                       K(4, ty=lift)],
        'UpperTorso': [K(0), K(1, ry=-1.5, rx=0.8), K(2, rx=1.5), K(3, ry=1.5, rx=0.8), K(4)],
        'Head': [K(0), K(1, rx=2, ry=4, rz=-1.5), K(2), K(3, rx=-1, ry=-4, rz=1.5), K(4)],
        'RightUpperArm': [K(0, rz=3), K(2, rx=3, rz=5), K(4, rz=3)],
        'RightLowerArm': [K(0, rx=2), K(2, rx=5), K(4, rx=2)],
    }
    if hover:      # dangling feet while floating
        j['RightUpperLeg'] = [K(0, rx=4), K(2, rx=7), K(4, rx=4)]
        j['RightLowerLeg'] = [K(0, rx=-6), K(2, rx=-10), K(4, rx=-6)]
    return j


def talk_clip():
    return {
        'UpperTorso': [K(0), K(0.6, rx=-2, ry=4), K(1.2), K(1.8, rx=-2, ry=-3), K(2.4)],
        'Head': [K(0), K(0.3, rx=-6, ry=3, rz=-1.5), K(0.7, rx=2, ry=6, rz=-3), K(1.0, rx=-5, ry=6), K(1.4, ry=2, rz=1.5),
                 K(1.9, rx=-4, ry=-4, rz=3), K(2.4)],
        'RightUpperArm': [K(0, rx=22, rz=6), K(0.6, rx=35, rz=12), K(1.2, rx=18, rz=8), K(1.8, rx=30, rz=14), K(2.4, rx=22, rz=6)],
        'RightLowerArm': [K(0, rx=40), K(0.6, rx=60, ry=-10), K(1.2, rx=35), K(1.8, rx=55, ry=-12), K(2.4, rx=40)],
        'RightHand': [K(0), K(0.6, rx=10, rz=-8), K(1.2, rx=-5), K(1.8, rx=8, rz=-6), K(2.4)],
        'LeftUpperArm': [K(0, rx=4, rz=-4), K(1.2, rx=8, rz=-6), K(2.4, rx=4, rz=-4)],
        'LeftLowerArm': [K(0, rx=8), K(1.2, rx=14), K(2.4, rx=8)],
    }


def wave_clip():
    up, hold = 0.45, 1.95
    return {
        'UpperTorso': [K(0), K(up, rz=3, ry=-4), K(hold, rz=3, ry=-4), K(2.4)],
        'Head': [K(0), K(up, rz=-6, ry=-8, rx=3), K(1.2, rz=-3, ry=-6, rx=3), K(hold, rz=-6, ry=-8, rx=3), K(2.4)],
        'RightUpperArm': [K(0), K(up, rx=12, rz=140), K(hold, rx=12, rz=140), K(2.4)],
        'RightLowerArm': [K(0), K(up, rx=15), K(0.7, rx=15, rz=-25), K(0.95, rx=15, rz=20), K(1.2, rx=15, rz=-25),
                          K(1.45, rx=15, rz=20), K(1.7, rx=15, rz=-10), K(hold, rx=15), K(2.4)],
        'RightHand': [K(0), K(0.7, rz=-10), K(0.95, rz=10), K(1.2, rz=-10), K(1.45, rz=10), K(hold), K(2.4)],
        'LeftUpperArm': [K(0), K(up, rz=-6), K(hold, rz=-6), K(2.4)],
    }


def point_clip():
    up, hold = 0.45, 1.5
    return {
        'UpperTorso': [K(0), K(up, ry=-10), K(hold, ry=-10), K(2.0)],
        'Head': [K(0), K(up, ry=-16, rx=2), K(hold, ry=-16, rx=2), K(2.0)],
        'RightUpperArm': [K(0), K(up, rx=75, rz=25), K(hold, rx=78, rz=22), K(2.0)],
        'RightLowerArm': [K(0), K(up, rx=10), K(hold, rx=8), K(2.0)],
        'RightHand': [K(0), K(up, rx=-15), K(hold, rx=-15), K(2.0)],
        'LeftUpperArm': [K(0), K(up, rx=5, rz=-4), K(hold, rx=5, rz=-4), K(2.0)],
    }


def nod_clip():
    return {'Head': [K(0), K(0.25, rx=-14), K(0.5, rx=2), K(0.75, rx=-12), K(1.2)],
            'UpperTorso': [K(0), K(0.25, rx=-3), K(0.5), K(0.75, rx=-3), K(1.2)]}


def shake_clip():
    return {'Head': [K(0), K(0.2, ry=16), K(0.45, ry=-16), K(0.7, ry=12), K(0.9, ry=-8), K(1.2)],
            'UpperTorso': [K(0), K(0.45, ry=-3), K(0.9, ry=2), K(1.2)]}


def celebrate_clip():
    leg = lambda a, b, c: {'UpperLeg': a, 'LowerLeg': b, 'Foot': c}
    j = {'LowerTorso': [K(0), K(0.2, ty=-0.045), K(0.45, ty=0.14), K(0.72, ty=-0.03), K(0.9), K(1.8)],
         'UpperTorso': [K(0), K(0.2, rx=-6), K(0.45, rx=4), K(0.72, rx=-3), K(1.8)],
         'Head': [K(0), K(0.2, rx=-4), K(0.45, rx=12), K(1.3, rx=8), K(1.8)],
         'RightUpperArm': [K(0), K(0.2, rz=20), K(0.45, rz=150, rx=10), K(1.3, rz=150, rx=10), K(1.8)],
         'RightLowerArm': [K(0), K(0.45, rz=-10), K(0.9, rz=10), K(1.3, rz=-10), K(1.8)]}
    for nm, vals in (('UpperLeg', (25, 12)), ('LowerLeg', (-45, -22)), ('Foot', (20, 10))):
        j['Right' + nm] = [K(0), K(0.2, rx=vals[0]), K(0.45), K(0.72, rx=vals[1]), K(0.95), K(1.8)]
    for side in ('UpperArm', 'LowerArm', 'UpperLeg', 'LowerLeg', 'Foot'):
        j['Left' + side] = sym(j['Right' + side])
    return j


def think_clip():
    up, hold = 0.5, 2.1
    return {
        'Head': [K(0), K(up, rx=6, ry=10, rz=8), K(1.3, rx=8, ry=8, rz=10), K(hold, rx=6, ry=10, rz=8), K(2.6)],
        'UpperTorso': [K(0), K(up, rx=-2, ry=-4), K(hold, rx=-2, ry=-4), K(2.6)],
        'RightUpperArm': [K(0), K(up, rx=52, rz=-16), K(hold, rx=52, rz=-16), K(2.6)],
        'RightLowerArm': [K(0), K(up, rx=118, rz=-10), K(hold, rx=118, rz=-10), K(2.6)],
        'RightHand': [K(0), K(up, rx=-20), K(1.0, rx=-10), K(1.5, rx=-20), K(hold, rx=-15), K(2.6)],
        'LeftUpperArm': [K(0), K(up, rx=20, rz=8), K(hold, rx=20, rz=8), K(2.6)],
        'LeftLowerArm': [K(0), K(up, rx=70), K(hold, rx=70), K(2.6)],
    }


def bow_clip():
    down, hold = 0.6, 1.3
    return {
        'UpperTorso': [K(0), K(down, rx=-28), K(hold, rx=-28), K(2.0)],
        'Head': [K(0), K(down, rx=-10), K(hold, rx=-10), K(2.0)],
        'RightUpperArm': [K(0), K(down, rx=30, rz=-20), K(hold, rx=30, rz=-20), K(2.0)],
        'RightLowerArm': [K(0), K(down, rx=80), K(hold, rx=80), K(2.0)],
        'LeftUpperArm': [K(0), K(down, rx=10, rz=-3), K(hold, rx=10, rz=-3), K(2.0)],
    }


def build_clips():
    clips = {}
    for name, joints, loop, sided in (('Idle', idle_clip(), True, False), ('IdleHover', idle_clip(True), True, False),
                                      ('Talk', talk_clip(), True, True), ('Wave', wave_clip(), False, True),
                                      ('Point', point_clip(), False, True), ('Nod', nod_clip(), False, False),
                                      ('Shake', shake_clip(), False, False), ('Celebrate', celebrate_clip(), False, False),
                                      ('Think', think_clip(), False, True), ('Bow', bow_clip(), False, True)):
        if name.startswith('Idle'):              # symmetric idle arms / legs
            for side in ('UpperArm', 'LowerArm', 'UpperLeg', 'LowerLeg'):
                if 'Right' + side in joints and 'Left' + side not in joints:
                    joints['Left' + side] = sym(joints['Right' + side])
        length = max(k[0] for keys in joints.values() for k in keys)
        clips[name] = {'length': length, 'loop': loop, 'sided': sided, 'joints': joints}
    return clips


CLIPS = build_clips()


def smooth(u):
    return u * u * (3 - 2 * u)


def sample(keys, t):
    """ease-in-out interpolation between keys (identical to NPCAnimationCore.sampleKeys)"""
    if t <= keys[0][0]:
        return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            u = smooth((t - a[0]) / max(b[0] - a[0], 1e-6))
            return [x + (y - x) * u for x, y in zip(a[1:], b[1:])]
    return keys[-1][1:]


def mirror_name(n):
    return n.replace('Right', '#').replace('Left', 'Right').replace('#', 'Left')


def mirrored(joints):
    return {mirror_name(j): sym(keys) for j, keys in joints.items()}


# ------------------------------------------------------------------ per-NPC runtime config
NPC_CONFIG = {
    # gesture = arm used for Wave/Point/Talk/Think/Bow (the free hand); talkGesture plays when a player talks to it
    'Shop': dict(gesture='Right', idle='Idle', talkGesture='Point', display='Shop',
                 lines=["Welcome to my shop! Boosts, items and gamepasses - take a look!",
                        "Spend wisely, adventurer!"]),
    'Egg': dict(gesture='Left', idle='Idle', talkGesture='Celebrate', display='Eggs',
                floats=[dict(parts=['RightHand_PropEgg'], bob=0.02, spin=40)],
                lines=["Every egg holds a new friend. Which one will you open?",
                       "The shiniest eggs hatch the rarest pets!"]),
    'Trading': dict(gesture='Right', idle='Idle', talkGesture='Nod', display='Trading',
                    lines=["Looking to trade? Find a partner and let's make a deal!",
                           "Always check both sides before you accept."]),
    'Upgrades': dict(gesture='Right', idle='Idle', talkGesture='Point', display='Upgrades',
                     floats=[dict(parts=['LeftHand_PropCrystal'], bob=0.015, spin=60)],
                     lines=["Bring me your coins and I'll make your pets stronger!",
                            "Upgrades last forever - choose wisely."]),
    'Pets': dict(gesture='Left', idle='Idle', talkGesture='Nod', display='Pets',
                 floats=[dict(parts=['RightHand_PropLeafCrystal'], bob=0.015, spin=45)],
                 lines=["Equip your best pets here, and I'll look after the rest.",
                        "Happy pets are strong pets!"]),
    'Leaderboards': dict(gesture='Right', idle='Idle', talkGesture='Bow', display='Leaderboards',
                         lines=["Only the greatest tamers reach the top of my boards.",
                                "Will your name be next?"]),
    'Tower_Guide': dict(gesture='Left', idle='Idle', talkGesture='Point', display='Tower Guide',
                        floats=[dict(parts=['LeftHand_PropPawGlow'], bob=0.025, sway=12)],
                        lines=["This is the Tower of Pets! Climb floor by floor to find stronger pets.",
                               "Stuck on a floor? Upgrade your pets, then try again."]),
    'Tower_Entrance': dict(gesture='Right', idle='IdleHover', talkGesture='Bow', display='Tower Entrance',
                           lines=["The tower awaits... Are you ready to enter?",
                                  "Only the brave return with legendary pets."]),
    'Codes': dict(gesture='Right', idle='Idle', talkGesture='Celebrate', display='Codes',
                  floats=[dict(parts=['LeftHand_PropGift', 'LeftHand_PropGiftRibbon'], bob=0.025, spin=35),
                          dict(parts=['LeftHand_PropSparkles'], bob=0.012, spin=-60, phase=1.0)],
                  lines=["Got a secret code? Type it in for free rewards!",
                         "Follow the game to hear about new codes first!"]),
    'Daily_Rewards': dict(gesture='Right', idle='Idle', talkGesture='Wave', display='Daily Rewards',
                          floats=[dict(parts=['LeftHand_PropCalendar', 'LeftHand_PropCalendarGrid',
                                              'LeftHand_PropCalendarRings'], bob=0.025, sway=8)],
                          lines=["Welcome back! Your daily reward is ready.",
                                 "Come back tomorrow for an even better one!"]),
    'Index': dict(gesture='Right', idle='Idle', talkGesture='Think', display='Pet Index',
                  lines=["Every pet you discover is recorded in the Index.",
                         "Collect them all to complete your collection!"]),
    'Settings': dict(gesture='Right', idle='Idle', talkGesture='Think', display='Settings',
                     floats=[dict(parts=['LeftHand_PropHoloPanel_1', 'LeftHand_PropHoloIcons_1'], bob=0.02, sway=6),
                             dict(parts=['LeftHand_PropHoloPanel_2', 'LeftHand_PropHoloIcons_2'], bob=0.02, sway=6,
                                  phase=1.6)],
                     lines=["Need to change the graphics or UI? I can help with that.",
                            "Lower the graphics if your game feels laggy!"]),
}


# ------------------------------------------------------------------ Blender side
def b2c(v):
    """Blender world vector -> character space (x right, y up, z back); NPCs face -Y in Blender"""
    return Vector((-v.x, v.z, v.y))


def c2b(v):
    return Vector((-v[0], v[2], v[1]))


AX_X, AX_Y, AX_Z = c2b((1, 0, 0)), c2b((0, 1, 0)), c2b((0, 0, 1))


def rot_quat(rx, ry, rz):
    """character-space rotation Ry * Rx * Rz (degrees) as a Blender quaternion (same order as the Luau runtime)"""
    return (Quaternion(AX_Y, math.radians(ry)) @ Quaternion(AX_X, math.radians(rx)) @
            Quaternion(AX_Z, math.radians(rz)))


def npc_parts(coll):
    return [o for o in coll.all_objects if o.type == 'MESH']


def build_rig(coll, key):
    """R15 armature for one NPC; bones sit at the body-part pivots and point along +Y with
    zero roll, so pose rotations are expressed in world (= character) axes"""
    parts = {o.name[len(key) + 1:]: o for o in npc_parts(coll)}
    origin = parts['LowerTorso'].location.copy()
    origin.z = 0.0
    pivots = {b: list(b2c(parts[b].location - origin)) for b in R15}   # world pivots, before parenting
    arm = bpy.data.armatures.new(f'{key}_Rig')
    arm.display_type = 'STICK'
    rig = bpy.data.objects.new(f'{key}_Rig', arm)
    rig.location = origin
    rig.show_in_front = True
    coll.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for b in R15:
        eb = arm.edit_bones.new(b)
        eb.head = parts[b].location - origin
        eb.tail = eb.head + Vector((0, 0.08, 0))
        eb.roll = 0.0
    for b, p in PARENT.items():
        arm.edit_bones[b].parent = arm.edit_bones[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    bpy.context.view_layer.update()
    for name, ob in parts.items():
        mw = ob.matrix_world.copy()
        ob.parent = rig
        ob.parent_type = 'BONE'
        ob.parent_bone = ob['bone'] if ob['bone'] in R15 else name
        bpy.context.view_layer.update()
        ob.matrix_world = mw
    rig_info = {
        'pivots': pivots,
        'centers': {},
        'bend': {},
    }
    for side in ('Right', 'Left'):        # how far each forearm is bent forward in the rest pose (deg)
        v = Vector(pivots[side + 'Hand']) - Vector(pivots[side + 'LowerArm'])
        rig_info['bend'][side] = round(math.degrees(math.atan2(-v.z, -v.y)), 2)
    for b in ('LowerTorso', 'Head'):
        o = parts[b]
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        rig_info['centers'][b] = list(b2c(sum(pts, Vector()) / 8 - origin))
    return rig, rig_info


FADE_IN, FADE_OUT = 0.2, 0.25           # same overlay fades as the Luau runtime


def bake_action(name, joints, length, armature, straighten=None, loop=False):
    """bake a clip into an action on `armature` at FPS (every bone keyed every frame).
    straighten = (forearm bone, bend deg): unbend a forearm that is bent in the rest pose while
    the clip plays, faded like the runtime overlay weight (gesture clips are authored straight)"""
    armature.animation_data_create()
    armature.animation_data.action = None
    nframes = int(round(length * FPS))
    for f in range(nframes + 1):
        t = f / FPS
        for b in R15:
            pb = armature.pose.bones[b]
            v = list(sample(joints[b], t)) if b in joints else [0.0] * 6
            if straighten and b == straighten[0]:
                w = 1.0 if loop else max(0.0, min(1.0, t / FADE_IN, (length - t) / FADE_OUT))
                v[0] -= straighten[1] * w
            pb.rotation_quaternion = rot_quat(v[0], v[1], v[2])
            pb.location = c2b(v[3:6])
            pb.keyframe_insert('rotation_quaternion', frame=f + 1)
            pb.keyframe_insert('location', frame=f + 1)
    act = armature.animation_data.action
    act.name = name
    act.use_fake_user = True
    armature.animation_data.action = None
    for pb in armature.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    return act


def main():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'TowerOfPets_NPCs.blend'))
    sc = bpy.context.scene
    sc.render.fps = FPS
    rigs, rig_data = {}, {}
    for coll in bpy.data.collections['NPCs'].children:
        key = coll.name[:-4]
        rigs[key], rig_data[key] = build_rig(coll, key)
    write_fixture(rigs)                 # rest pose, before any animation is applied
    # bake every clip once (and a left-handed copy of the sided clips) on the first rig, share the actions
    first = next(iter(rigs.values()))
    actions = {}

    def action_for(clip, key):
        """shared action per clip / gesture side / forearm bend (bent arms get their own copy)"""
        c = CLIPS[clip]
        if not c['sided']:
            tag = clip
        else:
            side = NPC_CONFIG[key]['gesture']
            bend = rig_data[key]['bend'][side]
            bend = bend if bend > 1 else 0
            tag = f'{clip}_{side}' + (f'_Bent{round(bend)}' if bend else '')
        if tag not in actions:
            joints = c['joints'] if not c['sided'] or side == 'Right' else mirrored(c['joints'])
            st = (side + 'LowerArm', bend) if c['sided'] and bend else None
            actions[tag] = bake_action('NPC_' + tag, joints, c['length'], first, st, c['loop'])
        return actions[tag]
    # NLA demo reel per NPC: idle, then every clip with its own gesture side, back-to-back
    reel = ['Talk', 'Wave', 'Point', 'Nod', 'Shake', 'Celebrate', 'Think', 'Bow']
    end = 1
    for key, rig in rigs.items():
        cfg = NPC_CONFIG[key]
        rig.animation_data_create()
        track = rig.animation_data.nla_tracks.new()
        track.name = 'DemoReel'
        f = 1
        for clip in [cfg['idle']] + reel + [cfg['idle']]:
            a = action_for(clip, key)
            st = track.strips.new(f'{clip}', int(f), a)
            f = st.frame_end + 6
            st.blend_in = st.blend_out = 4 if st.frame_end - st.frame_start > 10 else 0
        end = max(end, int(f))
    sc.frame_start, sc.frame_end = 1, end
    path = os.path.join(HERE, 'TowerOfPets_NPCs_Animated.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print('Saved:', path)
    write_lua(rig_data)


# ------------------------------------------------------------------ Luau data export
def lua(v, ind=''):
    if isinstance(v, dict):
        items = []
        for k, x in v.items():
            kk = k if k.isidentifier() else f'["{k}"]'
            items.append(f'{ind}\t{kk} = {lua(x, ind + chr(9))},')
        return '{\n' + '\n'.join(items) + f'\n{ind}}}'
    if isinstance(v, (list, tuple)):
        if v and isinstance(v[0], (list, tuple, dict)):
            return '{\n' + '\n'.join(f'{ind}\t{lua(x, ind + chr(9))},' for x in v) + f'\n{ind}}}'
        return '{' + ', '.join(lua(x, ind) for x in v) + '}'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return f'{round(v, 4) + 0.0:g}'
    return json.dumps(v)


def write_lua(rig_data):
    clips = {n: {'length': c['length'], 'loop': c['loop'], 'sided': c['sided'], 'joints': c['joints']}
             for n, c in CLIPS.items()}
    npcs = {}
    for key, cfg in NPC_CONFIG.items():
        d = dict(cfg)
        d.update(rig_data[key])
        npcs[key] = d
    out = os.path.join(HERE, '..', 'roblox', 'NPCAnimationData.lua')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        f.write('--!strict\n-- GENERATED by blender/npc_animations.py - edit the clips there and re-run it.\n'
                '-- Character space: X = character right, Y = up, Z = character back.\n'
                '-- Keys: {time (s), rotX, rotY, rotZ (degrees), posX, posY, posZ (metres in the Blender model)}.\n'
                '-- Rotations compose as Ry * Rx * Rz. Sided clips are authored for the right arm and mirrored at\n'
                '-- runtime for NPCs whose gesture hand is the left one.\n\n'
                'local Data = {}\n\n')
        f.write(f'Data.Fps = {FPS}\n')
        f.write('Data.Clips = ' + lua(clips) + '\n\n')
        f.write('-- per NPC: gesture hand, idle clip, talk gesture, prop floats, dialogue lines and the joint\n'
                '-- pivots / part centres measured from the Blender model (metres, character space, feet at 0)\n')
        f.write('Data.NPCs = ' + lua(npcs) + '\n\nreturn Data\n')
    print('Wrote:', os.path.abspath(out))


def write_fixture(rigs):
    """test fixture for the Luau test-suite: every part's bounds centre / size in Roblox
    import space (studs, Y up, character facing +Z as the FBX importer brings it in)"""
    fx = {}
    for coll in bpy.data.collections['NPCs'].children:
        key = coll.name[:-4]
        parts = {}
        rig = rigs[key]
        for o in npc_parts(coll):
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            c = sum(pts, Vector()) / 8 - rig.location
            size = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
            parts[o.name[len(key) + 1:]] = {'c': [c.x / 0.28, c.z / 0.28, -c.y / 0.28],
                                            's': [size[0] / 0.28, size[2] / 0.28, size[1] / 0.28]}
        fx[key] = parts
    out = os.path.join(HERE, '..', 'roblox', 'tests', 'Fixture.lua')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        f.write('-- GENERATED by blender/npc_animations.py: part bounds of every NPC as imported (studs)\n'
                'return ' + lua(fx) + '\n')
    print('Wrote:', os.path.abspath(out))


if __name__ == '__main__':
    main()
