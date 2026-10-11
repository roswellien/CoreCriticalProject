"""Compile and execute both compound-FCOS levels over genuine BEFORE inputs."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-cosine-native'
VS = Path('C:/Program Files/Microsoft Visual Studio/18/Community')
LLVM = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(name):
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    started = time.perf_counter()
    pins, commands, workers, outputs = {}, [], {}, {}
    passed = False

    def pin(path, expected=None):
        path = Path(path).resolve()
        value = sha(path)
        assert expected is None or value == expected, path
        assert str(path) not in pins or pins[str(path)] == value
        pins[str(path)] = value
        return path

    def run(name, args):
        args = list(map(str, args))
        pin(args[0])
        before = time.perf_counter()
        result = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=180)
        path = out / (name + '.log')
        path.write_bytes(result.stdout + result.stderr)
        pin(path)
        commands.append(dict(arguments=args, exit_code=result.returncode,
                             elapsed_seconds=time.perf_counter() - before, log=str(path)))
        print(json.dumps(dict(command=name, exit_code=result.returncode)), flush=True)
        assert result.returncode == 0, result.stderr.decode(errors='replace')[-5000:]

    prep = AREA / 'fixture-preparation-r1'
    try:
        source = json.loads(pin(prep / 'report.json',
            '6e10d1bc883ab6fcd8597962f75e4c8660d028c637578ca39553bff034672643').read_bytes())
        assert source['passed'] and source['reader_closed'] and not source['source_after_seed']
        for path, digest in source['files'].items():
            pin(path, digest)
        candidate = json.loads(pin(source['host_candidate'], source['host_candidate_sha256']).read_bytes())
        assert candidate['passed'] and candidate['normal_raw80_pointer_ABI']
        for path, digest in candidate['files'].items():
            pin(path, digest)
        ir = pin(candidate['host_IR'], candidate['host_IR_sha256'])
        for path in (Path(__file__), Path(__file__).with_name('build.ps1'), Path(sys.executable)):
            pin(path)
        headers = ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill'
        for subtree in (headers / 'Arch/Runtime', headers / 'Arch/X86/Runtime'):
            for path in subtree.rglob('*.h'):
                pin(path)
        os.environ['TEMP'] = os.environ['TMP'] = str(out)
        cmake = VS / 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
        ninja = pin(VS / 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
        run('verify', [LLVM / 'opt.exe', '-passes=verify', '-S', ir, '-o', out / 'verified.ll'])
        run('optimize', [LLVM / 'opt.exe', '-passes=default<O2>,verify', '-S', ir, '-o', out / 'optimized.ll'])
        for level in ('O0', 'O2'):
            selected = out / ('verified.ll' if level == 'O0' else 'optimized.ll')
            obj = out / f'4b64f0-{level}.obj'
            run('llc-' + level, [LLVM / 'llc.exe', '-filetype=obj', '-' + level, selected, '-o', obj])
            tree = out / ('build-' + level)
            flags = ('/Od' if level == 'O0' else '/O2') + ' /DNDEBUG /showIncludes'
            run('configure-' + level, [cmake, '-G', 'Ninja', '-S', prep, '-B', tree,
                f'-DMW34_ROOT={ROOT}', f'-DMW34_HOST_OBJECT={obj}',
                f'-DCMAKE_MAKE_PROGRAM={ninja}', f'-DCMAKE_CXX_COMPILER={LLVM}/clang-cl.exe',
                '-DCMAKE_BUILD_TYPE=Release', f'-DCMAKE_CXX_FLAGS_RELEASE={flags}'])
            run('compile-' + level, [cmake, '--build', tree, '--parallel', '4'])
            worker = pin(tree / 'mw34_compound_cosine.exe')
            workers[level] = dict(path=str(worker), sha256=sha(worker), literal_object=str(obj),
                                  literal_object_sha256=sha(obj))
            output = out / f'native-{level}.bin'
            run('execute-' + level, [worker, prep, ROOT / 'MW3/Mech3.exe', output])
            pin(output)
            outputs[level] = dict(path=str(output), sha256=sha(output), bytes=output.stat().st_size)
        for path, digest in list(pins.items()):
            assert sha(path) == digest, ('Changed actual input', path)
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        for path in out.rglob('*'):
            if path.is_file():
                pin(path)
        report = dict(passed=passed, scope='Actual compound-FCOS O0/O2 six-case native execution only; comparison separate',
                      preparation=str(prep / 'report.json'), preparation_sha256=sha(prep / 'report.json'),
                      workers=workers, outputs=outputs, commands=commands,
                      elapsed_seconds=time.perf_counter() - started,
                      native_executed=bool(outputs), native_original_equivalence=False,
                      source_after_seed=False, initializer_credit=0, files=pins)
        path = out / 'report.json'
        path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(path), native_levels=len(outputs))))


if __name__ == '__main__':
    main(sys.argv[1])
