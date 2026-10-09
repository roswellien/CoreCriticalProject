"""Causal admission/publication controls against the exact positive carry workers."""
import hashlib, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-control-carry'

def sha(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))

def need(value, reason):
    if not value:
        raise ValueError(reason)

def run(build_path, out):
    need(not out.exists() and out.is_relative_to(BASE), 'Fresh private controls required')
    build = read(build_path)
    need(build['passed'], 'Exact successful carry build required')
    for group in ('sources', 'tools', 'artifacts'):
        for path, expected in build[group].items():
            need(sha(path) == expected, 'Frozen dependency ' + path)
    out.mkdir()
    commands, controls = [], []
    pack = pathlib.Path(build['generation']).parent / 'pack.bin'
    original = pathlib.Path(build['original_raw_path'])
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    image = ROOT / 'MW3/Mech3.exe'

    def execute(level, name, worker, args, diagnostic):
        cp = subprocess.run([worker] + args, capture_output=True, timeout=60)
        so, se = out / (level + '-' + name + '.stdout'), out / (level + '-' + name + '.stderr')
        so.write_bytes(cp.stdout)
        se.write_bytes(cp.stderr)
        commands.append({'level': level, 'name': name, 'program': worker, 'program_sha256': sha(worker),
                         'arguments': args, 'exit_code': cp.returncode, 'stdout': str(so), 'stdout_sha256': sha(so),
                         'stderr': str(se), 'stderr_sha256': sha(se), 'expected_diagnostic': diagnostic})
        need(cp.returncode == 1 and cp.stderr.decode().strip() == diagnostic, 'Intended causal denial ' + level + ' ' + name)
        controls.append({'level': level, 'name': name, 'passed': True, 'diagnostic': diagnostic})

    try:
        for level, worker in build['workers'].items():
            args = [str(image), str(provider), str(pack), str(original), str(out / (level + '-denied-result.bin'))]
            why = 'Carry native: exact-image exact-provider exact-pack exact-original fresh-output'
            execute(level, 'missing-argument', worker, args[:-1], why)
            execute(level, 'extra-argument', worker, args + ['extra'], why)
            for index, name in enumerate(('image', 'provider', 'pack', 'original')):
                missing = args.copy()
                missing[index] = str(out / ('absent-' + name))
                execute(level, 'missing-' + name, worker, missing, 'Input unavailable')
                need(not pathlib.Path(args[-1]).exists(), 'No result from missing input')
            sources = (image, provider, pack, original)
            diagnoses = ('Exact carry image required', 'Exact carry provider required',
                         'Exact carry pack required', 'Exact actual carry original stream required')
            for index, (name, source, diagnostic) in enumerate(zip(('image', 'provider', 'pack', 'original'), sources, diagnoses)):
                changed = out / ('changed-' + name + '.bin')
                if not changed.exists():
                    data = bytearray(source.read_bytes())
                    data[100] ^= 1
                    changed.write_bytes(data)
                argv = args.copy()
                argv[index] = str(changed)
                execute(level, 'changed-' + name, worker, argv, diagnostic)
                need(not pathlib.Path(args[-1]).exists(), 'No result from changed input')
            for name, directory in (('existing-file', False), ('existing-directory', True)):
                dest = out / (level + '-' + name)
                if directory:
                    dest.mkdir()
                    marker = dest / 'sentinel'
                else:
                    marker = dest
                marker.write_bytes(b'External carry control sentinel\n')
                before = marker.read_bytes()
                execute(level, name, worker, args[:-1] + [str(dest)], 'Output exists or cannot establish absence')
                need(marker.read_bytes() == before, 'Exact external destination preserved')
                controls[-1].update({'sentinel_path': str(marker), 'sentinel_sha256': sha(marker), 'sentinel_size_bytes': len(before)})
    except Exception as error:
        (out / 'failure.json').write_text(json.dumps({'passed': False, 'reason': str(error), 'commands': commands}, indent=2) + '\n')
        raise
    report = {'passed': True, 'scope': 'Exact native worker admission/publication controls; existing positive raw runs are not repeated',
              'build_path': str(build_path), 'build_sha256': sha(build_path), 'actual_controls': controls, 'commands': commands,
              'positive_raws': {level: {'path': str(build_path.parent / ('native-' + level + '.bin')),
                                      'sha256': sha(build_path.parent / ('native-' + level + '.bin'))}
                               for level in ('O0', 'O2')}, 'whole_M4_complete': False}
    rp = out / 'report.json'
    rp.write_text(json.dumps(report, indent=2) + '\n')
    files = {str(path.resolve()): sha(path) for path in out.rglob('*') if path.is_file()}
    files[str(pathlib.Path(__file__).resolve())] = sha(__file__)
    files[str(build_path)] = sha(build_path)
    (out / 'pins.json').write_text(json.dumps({'files': files}, indent=2) + '\n')
    print(len(controls), 'causal native worker denials passed', sha(rp))

if __name__ == '__main__':
    run(pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve())
