"""Run the NPC animation tests with the standalone Luau CLI (https://github.com/luau-lang/luau).

    python3 roblox/tests/run_tests.py            # uses `luau` from PATH, or set LUAU=/path/to/luau

Bundles Mock.lua + the real modules (wrapped so `script` / `require` behave like in Roblox) +
Fixture.lua + Tests.lua into one file and runs it. Also syntax-checks every script.
"""
import os, subprocess, sys, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LUAU = os.environ.get('LUAU') or shutil.which('luau') or 'luau'
SHARED = ['NPCAnimationCore', 'NPCAnimationData', 'NPCRig', 'NPCAnimator']
SERVER = ['NPCDirector']


def read(path):
    with open(path) as f:
        return f.read()


def module_body(src):
    # type exports are only legal at the top level of a real module file
    return src.replace('export type ', 'type ')


def build():
    out = ['local Mock = (function()\n' + read(os.path.join(HERE, 'Mock.lua')) + '\nend)()',
           'local Vector3, CFrame, Color3, Enum, Instance, typeof = Mock.Vector3, Mock.CFrame, Mock.Color3, '
           'Mock.Enum, Mock.Instance, Mock.typeof',
           'local function warn(...) print("WARN", ...) end',
           'local __src, __cache = {}, {}',
           'local function require(inst)\n'
           '\tlocal name = inst.Name\n'
           '\tif __cache[name] == nil then __cache[name] = assert(__src[name], name)(inst) end\n'
           '\treturn __cache[name]\nend',
           # services
           'local game = Instance.new("DataModel")',
           'local workspace = Instance.new("Workspace"); workspace.Parent = game; rawset(workspace, "DescendantAdded", Mock.signal())',
           'local ReplicatedStorage = Instance.new("Folder", {Name = "ReplicatedStorage"}); ReplicatedStorage.Parent = game',
           'local NPCFolder = Instance.new("Folder", {Name = "NPCAnimation"}); NPCFolder.Parent = ReplicatedStorage',
           'local ServerFolder = Instance.new("Folder", {Name = "ServerScriptService"}); ServerFolder.Parent = game',
           'local LocalCharacter = Instance.new("Model", {Name = "LocalCharacter"})',
           'do local h = Instance.new("Part", {Name = "Head"}); h.Parent = LocalCharacter end',
           'local LocalPlayer = {Name = "Tester", Character = LocalCharacter}',
           'local PreSimulation = Mock.signal()',
           'local Bubbles = {}',
           'local services = {ReplicatedStorage = ReplicatedStorage, ServerScriptService = ServerFolder,\n'
           '\tPlayers = {LocalPlayer = LocalPlayer, GetPlayers = function() return {LocalPlayer} end},\n'
           '\tRunService = {PreSimulation = PreSimulation},\n'
           '\tTextChatService = {DisplayBubble = function(_, head, text) table.insert(Bubbles, text) end},\n'
           '\tChat = {Chat = function() end}}',
           'rawset(game, "GetService", function(_, name) return assert(services[name], name) end)']
    for name in SHARED + SERVER:
        folder = 'NPCFolder' if name in SHARED else 'ServerFolder'
        out.append(f'do local m = Instance.new("ModuleScript", {{Name = "{name}"}}); m.Parent = {folder} end')
        out.append(f'__src["{name}"] = function(script)\n' + module_body(read(os.path.join(ROOT, name + '.lua')))
                   + '\nend')
    out.append('local function RunClient()\n\tlocal script = Instance.new("LocalScript")\n'
               + read(os.path.join(ROOT, 'NPCClient.client.lua')) + '\nend')
    out.append('local Fixture = (function()\n' + read(os.path.join(HERE, 'Fixture.lua')) + '\nend)()')
    out.append(read(os.path.join(HERE, 'Tests.lua')))
    return '\n'.join(out)


def main():
    ok = True
    compile_bin = os.path.join(os.path.dirname(LUAU), 'luau-compile')
    for f in sorted(os.listdir(ROOT)):
        if f.endswith('.lua') and os.path.exists(compile_bin):
            r = subprocess.run([compile_bin, '--null', os.path.join(ROOT, f)], capture_output=True, text=True)
            print(('syntax ok  ' if r.returncode == 0 else 'SYNTAX ERR ') + f, r.stderr.strip())
            ok &= r.returncode == 0
    with tempfile.NamedTemporaryFile('w', suffix='.luau', delete=False) as t:
        t.write(build())
    r = subprocess.run([LUAU, t.name], capture_output=True, text=True)
    print(r.stdout[-6000:], r.stderr[-6000:])
    ok &= r.returncode == 0 and 'tests failed' not in r.stdout + r.stderr
    print('ALL TESTS PASSED' if ok else 'TESTS FAILED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
