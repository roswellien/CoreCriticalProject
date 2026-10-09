"""Post-build dependency/tool hashes, separate from invocation-time claims."""
import hashlib, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-control-carry'
VS = pathlib.Path('C:/Program Files/Microsoft Visual Studio/18/Community')

def sha(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def run(out):
    if out.exists() or not out.is_relative_to(BASE):
        raise ValueError('Fresh private tooling supplement required')
    out.mkdir()
    files, commands, headers = {}, [], {}
    ninja = VS / 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
    for name in ('native-build-r4-O0', 'native-build-r4-O2', 'context-build-r1'):
        directory = ROOT / ('build/m4-crt-control-carry-' + name)
        args = [str(ninja), '-C', str(directory), '-t', 'deps']
        cp = subprocess.run(args, capture_output=True, timeout=60)
        log, err = out / (name + '-deps.txt'), out / (name + '-deps.stderr')
        log.write_bytes(cp.stdout)
        err.write_bytes(cp.stderr)
        if cp.returncode:
            raise ValueError('Actual read-only Ninja dependency inventory failed')
        commands.append({'program': str(ninja), 'arguments': args[1:], 'exit_code': cp.returncode,
                         'stdout_path': str(log), 'stdout_sha256': sha(log), 'stderr_path': str(err), 'stderr_sha256': sha(err)})
        for line in cp.stdout.decode().splitlines():
            if line.startswith('    '):
                path = pathlib.Path(line.strip())
                if not path.is_file():
                    raise ValueError('Compiler-recorded dependency unavailable: ' + str(path))
                headers[str(path.resolve())] = sha(path)
        for path in (directory / 'CMakeCache.txt', directory / 'build.ninja', directory / 'CMakeFiles/rules.ninja'):
            files[str(path)] = sha(path)
    tools = [ninja, pathlib.Path(sys.executable), VS / 'MSBuild/Current/Bin/amd64/MSBuild.exe',
             VS / 'VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/lib.exe',
             VS / 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll',
             pathlib.Path('C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/rc.exe')]
    current = {str(path): sha(path) for path in tools}
    files.update(current)
    files.update(headers)
    report = {'passed': True, 'scope': 'Post-build actual compiler dependency inventory and current provider hashes',
              'commands': commands, 'compiler_recorded_dependencies': headers, 'supplemental_current_tools': current,
              'identity_note': 'All supplemental hashes are measured now, after the recorded builds. Primary build commands/maps remain unchanged. Ninja deps records actual compiler-read source/header paths. CMake rules declare RC/manifest providers; declarations alone do not prove RC execution. Current MSBuild/Lib/Python hashes are not historical invocation attestation.',
              'primary_native_build': str(BASE / 'native-build-r4/build.json'),
              'primary_native_build_sha256': sha(BASE / 'native-build-r4/build.json'),
              'primary_context_build': str(BASE / 'context-build-r1/build.json'),
              'primary_context_build_sha256': sha(BASE / 'context-build-r1/build.json'), 'whole_M4_complete': False}
    rp = out / 'report.json'
    rp.write_text(json.dumps(report, indent=2) + '\n')
    for path in out.iterdir():
        if path.is_file():
            files[str(path)] = sha(path)
    files[str(pathlib.Path(__file__).resolve())] = sha(__file__)
    (out / 'pins.json').write_text(json.dumps({'files': dict(sorted(files.items()))}, indent=2) + '\n')
    print(len(headers), 'actual compiler-recorded dependencies bound', sha(rp))

if __name__ == '__main__':
    run(pathlib.Path(sys.argv[1]).resolve())
