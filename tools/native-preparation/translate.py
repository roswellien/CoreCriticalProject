"""Generate native body objects from user images and a source-free recipe.

This producer reads only its explicit recipe, tool bundle and user image paths.
It never reads developer reports, existing LLVM IR, translated objects or captures.
It does not execute an original game executable or original DLL.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

CONTEXT = {}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def resolve(root, relative):
    need(isinstance(relative, str) and not any(p in ('', '.', '..') for p in relative.split('/')) and
         not any(char in relative for char in '\\:'), 'Unsafe preparation path')
    path = root / relative
    for parent in (path, *path.parents):
        if parent.exists():
            need(not parent.is_symlink() and not (parent.stat().st_file_attributes & 0x400 if os.name == 'nt' else False),
                 'Preparation paths cannot contain links')
        if parent == root:
            break
    return path


def source_span(blob, start, end):
    need(len(blob) >= 64 and blob[:2] == b'MZ', 'Expected PE32 input')
    pe = struct.unpack_from('<I', blob, 0x3c)[0]
    need(pe + 24 <= len(blob) and blob[pe:pe+4] == b'PE\0\0', 'Truncated PE input')
    machine, sections = struct.unpack_from('<HH', blob, pe+4)
    optional_size = struct.unpack_from('<H', blob, pe+20)[0]
    optional = pe+24
    need(machine == 0x14c and optional_size >= 96 and optional+optional_size+40*sections <= len(blob), 'Unsupported PE layout')
    need(struct.unpack_from('<H', blob, optional)[0] == 0x10b, 'Expected PE32 optional header')
    base = struct.unpack_from('<I', blob, optional+28)[0]
    matches = []
    for index in range(sections):
        section = optional+optional_size+40*index
        _, rva, size, offset = struct.unpack_from('<IIII', blob, section+8)
        flags = struct.unpack_from('<I', blob, section+36)[0]
        if base+rva <= start < end <= base+rva+size:
            need(flags & 0x20000000 and offset+size <= len(blob), 'Source span outside raw executable bytes')
            matches.append(blob[offset+start-base-rva:offset+end-base-rva])
    need(len(matches) == 1, 'Source span must belong to exactly one executable section')
    return matches[0]


def initialize(tools, image_paths):
    tools = Path(tools)
    sys.path.insert(0, str(tools / 'sources'))
    import host_adapter as H
    import fp_lowering as F
    import x87_bridges as X
    import ir_cleanup as I
    import merge_x87 as M
    import codec_timing as T
    lower_text = (tools / 'sources/lower_base.py').read_text()
    lower_text = lower_text.replace('mw34_mainargs_', 'mw34_attach_').replace("and '__remill_missing_block' not in text", '')
    need(lower_text.count("for level in ('O0','O2'):") == 1, 'Reviewed lowering compile loop')
    lower_text = lower_text.replace("for level in ('O0','O2'):", "for level in ('O2',):")
    for old, new in F.PATCHES:
        need(lower_text.count(old) == 1, 'Reviewed FP lowering patch site')
        lower_text = lower_text.replace(old, new)
    bridges = {'__remill_' + x + '_memory_' + width for x in ('read', 'write') for width in ('8', '16', '32', '64')}
    bridges |= {'__remill_' + x for x in ('function_call', 'function_return', 'jump', 'missing_block',
                                       'error', 'atomic_begin', 'atomic_end', 'async_hyper_call')}
    scope = dict(c=c, re=re, sha=sha, LLVM=F.llvm_class(H.LLVM), HOST_LAYOUT=H.HOST_LAYOUT,
                 FUNCTION_INDEX=H.FUNCTION_INDEX, checked_state_offsets=H.checked_state_offsets,
                 need=need, BRIDGES=bridges | F.BRIDGES)
    exec(compile(lower_text, str(tools / 'sources/lower_base.py'), 'exec'), scope)
    CONTEXT.update(tools=tools, lower=scope['lower'], x87=X, cleanup=I, merge=M, timing=T,
                   lower_text=lower_text, lower_scope=scope, lowers={'mw34_attach_': scope['lower']},
                   upstream=(tools / 'sources/Run.cpp').read_text(),
                   images={name: Path(path).read_bytes() for name, path in image_paths.items()})


def build(task):
    component, output, keep_intermediates = task
    name = component['name']
    directory = resolve(Path(output), name)
    directory.mkdir(exist_ok=True)
    target = resolve(directory, name + '-O2.obj')
    expected = component['expected_object_sha256']
    if target.exists() and sha(target) == expected:
        return name, 'verified-cache', expected
    tools, llvm = CONTEXT['tools'], CONTEXT['tools'] / 'llvm'
    code = source_span(CONTEXT['images'][component['image']], component['start'], component['end'])
    need(hashlib.sha256(code).hexdigest() == component['source_sha256'], 'Original component source hash mismatch: ' + name)

    def run(program, arguments, label):
        result = subprocess.run([str(program), *map(str, arguments)], capture_output=True, timeout=120)
        (directory / (label + '.stderr')).write_bytes(result.stderr[-1024*1024:])
        need(result.returncode == 0, 'Preparation tool failed: ' + label + ': ' + result.stderr.decode(errors='replace')[-1000:])
        return result.stdout

    guest = directory / (name + '-guest.ll')
    semantics = 'mmx' if component['image'] == 'ir50' else 'control'
    run(tools / 'lifter/remill-lift-control-21.exe', ['--arch=x86', '--os=windows',
        '--address=' + str(component['start']), '--entry_address=' + str(component['entry']),
        '--bytes=' + code.hex(), '--semantics_dir=' + str(tools / 'semantics' / semantics),
        '--ir_out=' + str(guest)], name + '-lift')
    text = CONTEXT['x87'].rewrite(guest.read_text())[0]
    guest.write_text(text)
    calls = [dict(kind='direct', target=int(value, 16)) for value in re.findall(r'^declare ptr @sub_([0-9a-f]+)', text, re.M)]
    namespace = component.get('lower_namespace', 'mw34_attach_')
    need(re.fullmatch(r'mw34_[a-z_]+_', namespace) is not None, 'Unsupported lowering namespace')
    if namespace not in CONTEXT['lowers']:
        scope = dict(CONTEXT['lower_scope'])
        exec(compile(CONTEXT['lower_text'].replace('mw34_attach_', namespace), 'lower_base.py', 'exec'), scope)
        CONTEXT['lowers'][namespace] = scope['lower']
    CONTEXT['lowers'][namespace](directory, name, dict(entry=component['entry'], outgoing_calls=calls),
                                llvm / 'LLVM-C.dll', CONTEXT['upstream'], run, llvm)
    if component.get('ir_symbol_renames'):
        host = directory / (name + '-host.ll')
        text = host.read_text()
        for old, new in component['ir_symbol_renames'].items():
            need(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.$]*', old) is not None and
                 re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.$]*', new) is not None, 'Invalid startup symbol name')
            text, count = re.subn('@' + re.escape(old) + r'\b', '@' + new, text)
            need(count > 0, 'Missing startup symbol rename')
        host.write_text(text)
        run(llvm / 'clang.exe', ['--target=x86_64-pc-windows-msvc', '-O2', '-c', host, '-o', target], name + '-compile-symbols')
    optimization = component['optimization']
    if optimization != 'plain-O2':
        need(optimization in ('merge-r7', 'merge-r8-codec'), 'Unknown object optimization recipe')
        text, _ = CONTEXT['timing'].transform((directory / (name + '-host.ll')).read_text())
        text, _ = CONTEXT['cleanup'].transform(text)
        intermediate = directory / (name + '-clean.ll')
        intermediate.write_text(text)
        simplified = directory / (name + '-cfg.ll')
        run(llvm / 'opt.exe', ['-passes=simplifycfg', '-S', intermediate, '-o', simplified], name + '-cfg')
        text, _ = CONTEXT['merge'].transform(simplified.read_text())
        text, _ = CONTEXT['cleanup'].annotate(text)
        if optimization == 'merge-r7':
            text, _ = CONTEXT['cleanup'].strict_x87(text, 0x401000 <= component['entry'] < 0x5bb000)
            text = CONTEXT['cleanup'].flat_mem(text, {})
        intermediate.write_text(text)
        bitcode, first, second = (directory / (name + suffix) for suffix in ('-inline.bc', '-o1.bc', '-o2.bc'))
        run(llvm / 'llvm-link.exe', ['--only-needed', '--internalize', intermediate, '-o', bitcode], name + '-link')
        run(llvm / 'opt.exe', ['-passes=default<O2>', bitcode, '-o', first], name + '-opt1')
        run(llvm / 'opt.exe', ['-passes=dse,gvn,dse,instcombine<no-verify-fixpoint>,simplifycfg,dse', first, '-o', second], name + '-opt2')
        run(llvm / 'clang.exe', ['--target=x86_64-pc-windows-msvc', '-O2', '-c', second, '-o', target], name + '-compile-final')
    for old, new in component['renames'].items():
        run(llvm / 'llvm-objcopy.exe', ['--redefine-sym', old + '=' + new, target], name + '-rename')
    # llvm-objcopy records wall time in the COFF header. Restore the recipe's
    # non-executable timestamp so the complete output identity is reproducible.
    with target.open('r+b') as stream:
        header = stream.read(20)
        need(len(header) == 20 and struct.unpack_from('<H', header)[0] == 0x8664, 'Expected AMD64 COFF output')
        stream.seek(4)
        stream.write(struct.pack('<I', component['coff_timestamp']))
    actual = sha(target)
    need(actual == expected, 'Regenerated object differs from selected build: ' + name + ' expected ' + expected + ' got ' + actual)
    if not keep_intermediates:
        for suffix in ('-guest.ll', '-host.ll', '-clean.ll', '-cfg.ll', '-inline.bc', '-o1.bc', '-o2.bc'):
            temporary = directory / (name + suffix)
            if temporary.exists():
                temporary.unlink()
    return name, 'generated-from-original', actual


def main(args):
    tools = args.tools.resolve()
    tool_manifest = tools / 'tools.json'
    manifest = json.loads(tool_manifest.read_text())
    need(manifest['schema_version'] == 1, 'Unsupported tool manifest')
    for relative, pin in manifest['files'].items():
        path = resolve(tools, relative)
        need(path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'], 'Preparation tool changed: ' + relative)
    need(args.recipe.stat().st_size <= 64 * 1024**2, 'Excessive translation recipe size')
    recipe = json.loads(args.recipe.read_text())
    need(recipe['schema_version'] == 1 and recipe['contract'] == 'mw3-translated-bodies-v1', 'Unsupported body preparation contract')
    components = recipe['components']
    need(len({v['name'] for v in components}) == len(components), 'Duplicate component name')
    if args.components:
        names = set(args.components.split(','))
        components = [v for v in components if v['name'] in names]
        need({v['name'] for v in components} == names, 'Unknown requested component')
    image_paths = {}
    for name in {value['image'] for value in components}:
        image = recipe['images'][name]
        path = args.codec.resolve() if name == 'ir50' and args.codec else resolve(args.game.resolve(), image['path'])
        need(sha(path) == image['sha256'], 'Original input hash mismatch: ' + name)
        image_paths[name] = str(path)
    for component in components:
        need(re.fullmatch(r'[a-zA-Z0-9_]+', component['name']) is not None and
             component['start'] <= component['entry'] < component['end'] and
             component['end'] - component['start'] <= 1024**2, 'Invalid body source bounds/name')
    output = args.output.resolve()
    identity = dict(recipe_sha256=sha(args.recipe), tools_sha256=sha(tool_manifest), producer_sha256=sha(Path(__file__)),
                    selected=[value['name'] for value in components])
    if output.exists():
        need(args.resume and json.loads((output / 'session.json').read_text()) == identity,
             'Resume requires the exact recipe, producer, tools and component selection')
    else:
        need(not args.resume, 'No preparation exists to resume')
        output.mkdir(parents=True)
        (output / 'session.json').write_text(json.dumps(identity) + '\n')
    lock = (output / '.preparation-lock').open('a+b')
    try:
        if os.name == 'nt':
            import msvcrt
            lock.seek(0)
            if not lock.read(1):
                lock.write(b'\0')
                lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        completed = []
        tasks = iter((component, str(output), args.keep_intermediates) for component in components)
        with ProcessPoolExecutor(max_workers=args.jobs, initializer=initialize, initargs=(str(tools), image_paths)) as executor:
            pending = set()
            for _ in range(args.jobs * 2):
                task = next(tasks, None)
                if task is not None:
                    pending.add(executor.submit(build, task))
            while pending:
                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    result = future.result()
                    completed.append(result)
                    print(json.dumps(dict(completed=len(completed), total=len(components), component=result[0], result=result[1])), flush=True)
                    task = next(tasks, None)
                    if task is not None:
                        pending.add(executor.submit(build, task))
        (output / 'objects.txt').write_text('\n'.join(str(output / value['name'] / (value['name'] + '-O2.obj')) for value in components) + '\n')
        (output / 'generation.json').write_text(json.dumps(dict(contract=recipe['contract'], recipe_sha256=sha(args.recipe),
            tools_sha256=sha(tool_manifest), completed=len(completed), full_selected_body_set=len(completed) == len(recipe['components']),
            inputs={name: recipe['images'][name]['sha256'] for name in image_paths}, objects=completed), indent=2) + '\n')
    finally:
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--recipe', type=Path, required=True)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--codec', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--components', default='')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--keep-intermediates', action='store_true')
    parser.add_argument('--jobs', type=int, choices=(1, 2), default=2)
    main(parser.parse_args())
