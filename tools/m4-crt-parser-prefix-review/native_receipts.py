"""Associate each fixture capture with its exact completed direct native command."""
import pathlib
import subprocess
from transport import ROOT, T, need, read_json, sha_file
from manifests import normalized as normalize_string


def normalized(path):
    return normalize_string(str(path))


def validate(build_path, build, files):
    python = pathlib.Path('C:/Python314/python.exe')
    launcher = ROOT / 'tools/m4-crt-parser-prefix-review/launch_fixture.py'
    sources = {normalized(p): h for p, h in build['sources'].items()}
    tools = {normalized(p): h for p, h in build['tools'].items()}
    artifacts = {normalized(p): h for p, h in build['artifacts'].items()}
    need(normalized(launcher) in sources and normalized(python) in tools,
         'Native launcher and Python present in original watched build sources/tools')
    T.add(files, launcher, sources[normalized(launcher)])
    T.add(files, python, tools[normalized(python)])
    result = []
    for level in ('O0', 'O2'):
        directory = build_path.parent / level
        path = directory / 'native-command.json'
        native = read_json(path)
        T.add(files, path, artifacts[normalized(path)])
        argv = [str(directory / 'controls.exe'), str(ROOT/'MW3/Mech3.exe'),
                str(ROOT/f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj'),
                str(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),
                str(ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin'),
                str(ROOT/'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin'),
                str(directory/'actual')]
        need(native['argv'] == argv and native['exit_code'] == 0 and native['direct_argv'] is True
             and native['worker_unchanged'] is True and native['ordinary_game_launched'] is False
             and native['original_executed'] is False, 'Exact successful isolated native fixture command')
        need(native['worker_path'] == argv[0] and native['worker_sha256'] == artifacts[normalized(argv[0])],
             'Exact worker and watched pre/post executable identity')
        need(native['stdout_path'] == str(directory/'controls.log') and
             native['stdout_sha256'] == artifacts[normalized(native['stdout_path'])],
             'Exact actual child log digest')
        need(native['command_line'] == subprocess.list2cmdline(argv) and native['command_line'][0] == 'D',
             'Actual direct argv retains unquoted measured D-leading native input')
        a, b = native['monotonic_start_ns'], native['monotonic_end_ns']
        need(type(a) is int and type(b) is int and 0 <= a <= b and
             native['duration_seconds'] == (b-a)/1e9, 'Exact monotonic native timing')
        commands = [c for c in build['commands'] if normalized(c['program']) == normalized(python)
                    and c['arguments'] == [str(launcher)] + argv]
        need(len(commands) == 1, 'One exact actual launcher invocation per completed worker')
        command = commands[0]
        need(command['exit_code'] == 0 and command['log_path'] == str(directory/'native-launch.log')
             and command['log_sha256'] == artifacts[normalized(command['log_path'])]
             and command['duration_seconds'] >= native['duration_seconds'],
             'Actual zero-exit Python launcher and completed outer log/timing')
        T.add(files, command['log_path'], command['log_sha256'])
        need(sha_file(path) == artifacts[normalized(path)], 'Stable exact native command receipt')
        result.append(native)
    return result
