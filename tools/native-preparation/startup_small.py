"""Regenerate checked command-line startup code and the authored ABI capture shim."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys

from translate import need, resolve, sha, source_span


def prepare(tools, provider, recipe, output):
    need(not output.exists(), 'Use a fresh startup output directory')
    manifest = json.loads((tools / 'tools.json').read_text())
    for name, pin in manifest['files'].items():
        path = resolve(tools, name)
        need(path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'], 'Startup tool changed: ' + name)
    output.mkdir(parents=True)
    llvm = tools / 'llvm'

    def run(tool, arguments, name):
        result = subprocess.run([str(tool), *map(str, arguments)], capture_output=True, timeout=120)
        (output / (name + '.stderr')).write_bytes(result.stderr[-1024*1024:])
        need(result.returncode == 0, 'Startup tool failed: ' + name)

    target = output / 'component-O2.obj'
    if recipe['contract'] == 'mw3-commandline-writer-v1':
        need(sha(provider) == recipe['image_sha256'], 'Original CRT input changed')
        code = source_span(provider.read_bytes(), recipe['start'], recipe['end'])
        import hashlib
        need(hashlib.sha256(code).hexdigest() == recipe['source_sha256'], 'Original command-line source changed')
        run(tools / 'lifter/remill-lift-control-21.exe', ['--arch=x86', '--os=windows', '--address='+str(recipe['start']),
            '--bytes='+code.hex(), '--semantics_dir='+str(tools / 'semantics/control'),
            '--ir_out='+str(output / 'guest.ll')], 'lift')
        sys.path.insert(0, str(tools / 'sources'))
        import commandline_adapt
        host = commandline_adapt.adapt_commandline(output, llvm / 'LLVM-C.dll')
        run(llvm / 'llc.exe', ['-mtriple=x86_64-pc-windows-msvc', '-filetype=obj', '-O2', host, '-o', target], 'compile')
    elif recipe['contract'] == 'mw3-authored-abi-capture-v1':
        need(sha(tools / 'sources/capture.s') == recipe['source_sha256'], 'Authored capture source changed')
        run(llvm / 'clang.exe', ['--target=x86_64-pc-windows-msvc', '-c', tools / 'sources/capture.s', '-o', target], 'compile')
    else:
        raise ValueError('Unsupported small-startup contract')
    with target.open('r+b') as stream:
        stream.seek(4)
        stream.write(struct.pack('<I', recipe['coff_timestamp']))
    need(sha(target) == recipe['expected_object_sha256'], 'Generated startup component differs from selected host')
    (output / 'generation.json').write_text(json.dumps(dict(contract=recipe['contract'],
        object_sha256=sha(target), captured_state_used=False, original_code_executed=False), indent=2)+'\n')
    return sha(target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--provider', type=Path)
    parser.add_argument('--recipe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.tools.resolve(), args.provider, json.loads(args.recipe.read_text()), args.output.resolve()))
