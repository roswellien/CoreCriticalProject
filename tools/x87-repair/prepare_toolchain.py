"""Build a patched semantics overlay and explicit-semantics lifter in isolation.

Only new local/report paths are written. Existing Remill binaries, semantics
and all prior measurements retain their identities.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess

BASELINE_SEMANTICS = '138d370500c1f337e6e8fe8ddab09d91d85ea27456036c5bea0a18031b893d71'
BASELINE_LIFTER = 'd0973f5f42df6b37b2badbf4f698ad74a3e55e0dd080cd0554b5fe144cf8902f'
COMMIT = '0e324aee8c67a63ec759ef379dcfafa0b3cb1448'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(root, remill, llvm):
    original = remill / 'build'
    baseline_sem = original / 'lib/Arch/X86/Runtime/x86.bc'
    baseline_lifter = original / 'bin/lift/remill-lift-21.exe'
    if digest(baseline_sem) != BASELINE_SEMANTICS or digest(baseline_lifter) != BASELINE_LIFTER:
        raise ValueError('Baseline semantics/lifter identity differs')
    if subprocess.check_output(['git', '-C', str(remill), 'rev-parse', 'HEAD'], text=True).strip() != COMMIT:
        raise ValueError('Pinned Remill commit required')
    subprocess.run(['git', '-C', str(remill), 'diff', '--exit-code', '--',
                    'lib/Arch/X86/Semantics/X87.cpp', 'bin/lift/Lift.cpp'], check=True)
    output = root / 'local/tools/remill-x87-control-repair'
    shadow = output / 'source'
    if shadow.is_relative_to(remill) or remill.is_relative_to(shadow):
        raise ValueError('Overlay must be separate from admitted baseline')
    shadow.mkdir(parents=True, exist_ok=True)
    shutil.copytree(remill / 'lib/Arch/X86', shadow / 'lib/Arch/X86', dirs_exist_ok=True)
    (shadow / 'bin/lift').mkdir(parents=True, exist_ok=True)
    shutil.copy2(remill / 'bin/lift/Lift.cpp', shadow / 'bin/lift/Lift.cpp')
    patch = root / 'tools/x87-repair/remill-control-word.patch'
    prefix = shadow.relative_to(root).as_posix()
    for check in (True, False):
        command = ['git', 'apply', '--directory=' + prefix]
        if check:
            command.append('--check')
        subprocess.run(command + [str(patch)], cwd=root, check=True)
    overlay_hashes = {}
    changed = []
    for path in sorted(shadow.rglob('*')):
        if path.is_file():
            name = path.relative_to(shadow).as_posix()
            before, after = digest(remill / name), digest(path)
            overlay_hashes[name] = {'baseline': before, 'patched': after}
            if before != after:
                changed.append(name)
    if changed != ['bin/lift/Lift.cpp', 'lib/Arch/X86/Semantics/X87.cpp']:
        raise ValueError('Overlay changes more than the two reviewed source files')
    report_dir = root / 'reports/x87-repair/toolchain'
    report_dir.mkdir(parents=True, exist_ok=True)
    commands = []
    def run(arguments, cwd=original):
        commands.append({'argv': arguments, 'cwd': str(cwd)})
        subprocess.run(arguments, cwd=cwd, check=True)
    ninja = (original / 'build.ninja').read_text()
    match = re.search(r'^build lib/Arch/X86/Runtime/x86_Instructions.cpp.bc \|[^\n]*\n  COMMAND = (.+)$', ninja, re.M)
    if not match:
        raise ValueError('Pinned semantics compilation recipe missing')
    compile_text = match[1].split(' && ', 1)[1].removesuffix('"').replace('\\', '/')
    arguments = shlex.split(compile_text)
    if Path(arguments[0]).resolve() != (llvm / 'bin/clang++.exe').resolve():
        raise ValueError('Unexpected semantics compiler')
    original_source = (remill / 'lib/Arch/X86/Runtime/Instructions.cpp').as_posix()
    # Instructions.cpp includes semantics through repository-relative paths.
    # Resolve those against the patched overlay, retaining admitted headers.
    original_include = '-I' + remill.as_posix()
    arguments[arguments.index(original_include)] = '-I' + shadow.as_posix()
    arguments[arguments.index(original_source)] = (shadow / 'lib/Arch/X86/Runtime/Instructions.cpp').as_posix()
    instructions = output / 'x86_Instructions.cpp.bc'
    arguments[arguments.index('-o') + 1] = instructions.as_posix()
    run(arguments)
    components = [original / ('lib/Arch/X86/Runtime/x86_' + name + '.cpp.bc')
                  for name in ('BasicBlock', 'Intrinsics', 'HyperCall')]
    semantics_dir = output / 'semantics'
    semantics_dir.mkdir(exist_ok=True)
    repaired_sem = semantics_dir / 'x86.bc'
    run([str(llvm / 'bin/llvm-link.exe'), '--suppress-warnings', str(instructions),
         *(str(path) for path in components), '-o', str(repaired_sem)])
    entries = json.loads((original / 'compile_commands.json').read_text())
    candidates = [item for item in entries if item['file'].endswith('/bin/lift/Lift.cpp')]
    if len(candidates) != 1:
        raise ValueError('Pinned lifter compilation recipe missing')
    compiler = candidates[0]['command']
    obj = output / 'Lift.cpp.obj'
    compiler = re.sub(r'/Fo\S+', '/Fo' + obj.as_posix(), compiler)
    compiler = re.sub(r'/Fd\S+', '/Fd' + output.as_posix() + '/', compiler)
    compiler = compiler.replace(str(remill / 'bin/lift/Lift.cpp'), str(shadow / 'bin/lift/Lift.cpp'))
    compiler = compiler.replace((remill / 'bin/lift/Lift.cpp').as_posix(), (shadow / 'bin/lift/Lift.cpp').as_posix())
    if str(shadow / 'bin/lift/Lift.cpp') not in compiler and (shadow / 'bin/lift/Lift.cpp').as_posix() not in compiler:
        raise ValueError('Lifter source path was not retargeted')
    commands.append({'windows_command_line': compiler, 'cwd': str(original)})
    # This is a direct compiler invocation, never a shell command.
    subprocess.run(compiler, cwd=original, check=True)
    block = re.search(r'^build bin/lift/remill-lift-21.exe:[^\n]*\n((?:  [^\n]*\n)+)', ninja, re.M)
    if not block:
        raise ValueError('Pinned lifter link recipe missing')
    library_match = re.search(r'^  LINK_LIBRARIES = (.+)$', block[1], re.M)
    if not library_match:
        raise ValueError('Pinned lifter libraries missing')
    libraries = [word.strip('"') for word in shlex.split(library_match[1], posix=False)]
    library_paths, linker_options = [], []
    for name in libraries:
        if name.startswith('-'):
            linker_options.append('/' + name[1:])
            continue
        path = Path(name)
        resolved = path if path.is_absolute() else original / path
        library_paths.append(str(resolved.resolve()) if resolved.exists() else name)
    lifter = output / 'remill-lift-control-21.exe'
    link_args = [str(obj), *library_paths, '/link', '/machine:x64', '/INCREMENTAL:NO',
                 '/subsystem:console', *linker_options, '/OUT:' + str(lifter)]
    response = output / 'lifter-link.rsp'
    response.write_text(subprocess.list2cmdline(link_args), encoding='utf-8')
    run([str(llvm / 'bin/clang-cl.exe'), '@' + str(response)])
    if digest(baseline_sem) != BASELINE_SEMANTICS or digest(baseline_lifter) != BASELINE_LIFTER:
        raise ValueError('Baseline changed during isolated build')
    if digest(repaired_sem) == BASELINE_SEMANTICS:
        raise ValueError('Repair did not produce distinct semantics')
    if digest(lifter) == BASELINE_LIFTER:
        raise ValueError('Explicit-semantics lifter was not rebuilt')
    record = {
        'schema_version': 1, 'remill_commit': COMMIT, 'llvm_version': '21.1.8',
        'llvm_dll_sha256': digest(llvm / 'bin/LLVM-C.dll'),
        'baseline_semantics_path': str(baseline_sem), 'baseline_semantics_sha256': BASELINE_SEMANTICS,
        'repaired_semantics_path': str(repaired_sem), 'repaired_semantics_sha256': digest(repaired_sem),
        'baseline_remill_lifter_path': str(baseline_lifter), 'baseline_remill_lifter_sha256': BASELINE_LIFTER,
        'remill_lifter_path': str(lifter), 'remill_lifter_sha256': digest(lifter),
        'patch_path': str(patch), 'patch_sha256': digest(patch),
        'changed_source_files': changed, 'overlay_source_hashes': overlay_hashes,
        'semantics_component_hashes': {str(path): digest(path) for path in components},
        'compiler_sha256': digest(llvm / 'bin/clang++.exe'),
        'lifter_compiler_sha256': digest(llvm / 'bin/clang-cl.exe'),
        'link_libraries': {name: digest(name) for name in library_paths if Path(name).is_file()},
        'commands': commands, 'link_response_arguments': link_args,
    }
    (report_dir / 'repair.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Isolated control-word semantics and explicit-semantics lifter built; baseline unchanged')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--remill-root', type=Path, required=True)
    parser.add_argument('--llvm-root', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.root.resolve(), args.remill_root.resolve(), args.llvm_root.resolve())
