"""Stage existing open-source compiler tools and authored translators for local tests.

No downloads and no original/generated game inputs. Publication still requires
dependency/license review. Original developer tools and pinned reports stay intact.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def stage(root, output, llvm_license=None):
    if output.exists():
        raise ValueError('Use a fresh tool bundle directory')
    output.mkdir(parents=True)
    files = {}

    def copy(source, relative):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha(source) != sha(target):
            raise ValueError('Tool changed while staging: ' + relative)
        files[relative] = dict(bytes=target.stat().st_size, sha256=sha(target))

    llvm = root / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc'
    for name in ('clang.exe', 'opt.exe', 'llvm-link.exe', 'llvm-objcopy.exe', 'llvm-nm.exe', 'llc.exe', 'lld-link.exe', 'LLVM-C.dll'):
        copy(llvm / 'bin' / name, 'llvm/' + name)
    copy(root / 'local/tools/remill-x87-control-repair/remill-lift-control-21.exe', 'lifter/remill-lift-control-21.exe')
    copy(root / 'local/tools/remill-x87-control-repair/semantics/x86.bc', 'semantics/control/x86.bc')
    copy(root / 'local/tools/remill-mmx-build/semantics/x86.bc', 'semantics/mmx/x86.bc')
    copy(root / 'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp', 'sources/Run.cpp')
    copy(root / 'tools/lifting/host_adapter.py', 'sources/host_adapter.py')
    for name in ('fp_lowering', 'x87_bridges', 'ir_cleanup', 'merge_x87', 'codec_timing'):
        copy(root / f'tools/m4-crt-heap-carry/{name}.py', f'sources/{name}.py')
    # Isolate the existing authored lowering function, excluding all historical
    # command-line recovery code and its private report/capture dependencies.
    original = (root / 'tools/m4-crt-mainargs-recovery/recover.py').read_text()
    node = next(n for n in ast.parse(original).body if isinstance(n, ast.FunctionDef) and n.name == 'lower')
    lower = ast.get_source_segment(original, node) + '\n'
    target = output / 'sources/lower_base.py'
    target.write_text(lower)
    files['sources/lower_base.py'] = dict(bytes=target.stat().st_size, sha256=sha(target))
    # The entry adapter's computational core is authored LLVM/ABI plumbing.
    # Exclude its old report validation, captures and historical output paths.
    original = (root / 'tools/m4-crt-entry/adapt.py').read_text()
    adapter = next(n for n in ast.parse(original).body if isinstance(n, ast.FunctionDef) and n.name == 'adapt')
    start = next(i for i, n in enumerate(adapter.body) if ast.get_source_segment(original, n).startswith('text, direct_sites ='))
    end = next(i for i in range(start, len(adapter.body)) if isinstance(adapter.body[i], ast.Try))
    statements = adapter.body[start:end+1]
    skeleton = ast.parse('import ctypes as c\nimport re\nimport traceback\n'
        'def need(value, message):\n    if not value: raise ValueError(message)\n'
        'def adapt_entry(original, out, helper, dll, entries):\n'
        '    api = helper.LLVM(dll)\n    preparation = {"entries": entries}\n')
    function = skeleton.body[-1]
    function.body.extend(statements)
    function.body.extend(ast.parse('return out / "candidate.ll"').body)
    generated = ast.unparse(ast.fix_missing_locations(skeleton)) + '\n'
    compile(generated, 'entry_adapt.py', 'exec')
    target = output / 'sources/entry_adapt.py'
    target.write_text(generated)
    files['sources/entry_adapt.py'] = dict(bytes=target.stat().st_size, sha256=sha(target))
    original = (root / 'tools/m4-crt-commandline-carry/adapt.py').read_text()
    adapter = next(n for n in ast.parse(original).body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    # Keep the checked retarget/wrapper logic, removing only developer-directory
    # requirements and the old diagnostic report writer.
    statements = adapter.body[4:]
    for index, statement in enumerate(statements):
        if isinstance(statement, ast.Assign) and isinstance(statement.targets[0], ast.Name) and statement.targets[0].id == 'api':
            statement.value = ast.parse('LLVM(dll)', mode='eval').body
        if isinstance(statement, ast.Try):
            report_index = next(i for i, node in enumerate(statement.body) if isinstance(node, ast.Assign) and
                isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'report')
            statement.body = statement.body[:report_index]
    skeleton = ast.parse('from pathlib import Path\nimport ctypes as c\nimport re\n'
        'from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, checked_state_offsets\n'
        'def adapt_commandline(folder, dll):\n    text = (folder / "guest.ll").read_text()\n')
    skeleton.body[-1].body.extend(statements)
    skeleton.body[-1].body.extend(ast.parse('return folder / "host.ll"').body)
    generated = ast.unparse(ast.fix_missing_locations(skeleton)) + '\n'
    compile(generated, 'commandline_adapt.py', 'exec')
    target = output / 'sources/commandline_adapt.py'
    target.write_text(generated)
    files['sources/commandline_adapt.py'] = dict(bytes=target.stat().st_size, sha256=sha(target))
    copy(root / 'tools/m4-crt-commandline-carry/capture.s', 'sources/capture.s')
    from startup_adapters import extract
    target = output / 'sources/startup_adapt.py'
    target.write_text(extract(root))
    files['sources/startup_adapt.py'] = dict(bytes=target.stat().st_size, sha256=sha(target))
    # Keep upstream notices with the tool payload when locally present.
    for directory, prefix in ((llvm, 'llvm'), (root / 'local/tools/remill-v6.0.1/remill-6.0.1', 'remill')):
        notices = [p for p in directory.iterdir() if p.is_file() and p.name.lower().startswith(('license', 'notice'))]
        if prefix == 'llvm' and llvm_license is not None:
            notices.append(llvm_license)
        if not notices:
            raise ValueError('Missing upstream tool license: ' + str(directory))
        for notice in notices:
            copy(notice, 'notices/' + prefix + '/' + notice.name)
    manifest = dict(schema_version=1, llvm_version='21.1.8', purpose='local-source-generation-tools', files=files)
    (output / 'tools.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return len(files), sum(pin['bytes'] for pin in files.values())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--llvm-license', type=Path)
    args = parser.parse_args()
    print(stage(args.root.resolve(), args.output.resolve(), args.llvm_license))
