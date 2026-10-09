"""Independent source/State ABI/COFF/current-build audit, no execution."""
import ctypes as C
import difflib
import hashlib
import json
import ntpath
import re
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
HERE = Path(__file__).absolute().parent
sys.path.insert(0, str(ROOT / 'tools/analysis'))
sys.path.insert(0, str(ROOT / 'tools/lifting'))
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from pe import PEImage
from host_adapter import LLVM, HOST_LAYOUT
from manifests import verify_manifest, unique_object


def need(value, why):
    if not value:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def key(path):
    return ntpath.normcase(ntpath.normpath(str(Path(path).absolute())))


def layouts(path, symbol, api):
    context = api.ContextCreate()
    module, buffer, error = C.c_void_p(), C.c_void_p(), C.c_void_p()
    data = None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(path).encode(), C.byref(buffer), C.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, C.byref(module), C.byref(error)), error)
        api.check(api.VerifyModule(module, 2, C.byref(error)), error)
        data = api.CreateTargetData(api.GetDataLayoutStr(module))
        types = {}
        for name in re.findall(r'^%([^ =]+) = type', path.read_text(), re.M):
            ty = api.GetTypeByName2(context, name.encode())
            need(ty and not api.IsOpaqueStruct(ty), 'Complete named source State type')
            types[name] = {'size': api.ABISizeOfType(data, ty), 'alignment': api.ABIAlignmentOfType(data, ty),
                'offsets': [api.OffsetOfElement(data, ty, index) for index in range(api.CountStructElementTypes(ty))]}
        need(api.signature(api.GetNamedFunction(module, symbol.encode())) == ('ptr', ['ptr', 'i32', 'ptr']), 'Exact State/GuestPC/opaque token ABI')
        return {'pointer_bytes': api.PointerSize(data), 'types': types}
    finally:
        if data:
            api.DisposeTargetData(data)
        if module.value:
            api.DisposeModule(module)
        api.ContextDispose(context)


def main(preparation, build_path, output):
    prep = Path(preparation).absolute()
    build_path = Path(build_path).absolute()
    out = Path(output).absolute()
    base = ROOT / 'reports/m4-crt-heap-init-review'
    need(out.parent == base and out.name.startswith('audit-') and not out.exists(), 'Fresh independent source audit')
    out.mkdir()
    files = {}
    def bind(path, expected=None):
        path = Path(path).absolute()
        actual = sha(path)
        need(expected is None or actual == expected, 'Current source/compiled physical identity: ' + str(path))
        normalized = key(path)
        need(normalized not in files or files[normalized] == actual, 'Conflict-free source association')
        files[normalized] = actual
        return actual
    for path in (Path(__file__), ROOT / 'tools/analysis/pe.py', ROOT / 'tools/lifting/host_adapter.py', ROOT / 'tools/m4-pipeline/manifests.py', Path(sys.executable)):
        bind(path)
    old_build_path = ROOT / 'reports/m4-crt-locale-default/build-r2/build.json'
    bind(old_build_path, 'b1cdebd498dbaa5aaa42e60bc66b2a53665346df1852ad63d1313d60d6e1dcca')
    bind(ROOT / 'reports/m4-crt-locale-default-root/root-acceptance-r2/report.json', '211a866900b2274aad08c5ac710e0b69c93c34e279a7bfe3745b837541edf65e')
    bind(prep / 'report.json')
    bind(prep / 'pins.json')
    bind(build_path)
    build, old_build = read(build_path), read(old_build_path)
    preparation_record = read(prep / 'report.json')
    need(build['passed'] is True and key(build['preparation_path']) == key(prep / 'report.json') and build['preparation_sha256'] == sha(prep / 'report.json'), 'Successful exact prepared production build')
    need(preparation_record['Runtime_CPU_preserved'] is True and preparation_record['Runtime_call_record_added'] is False and preparation_record['State_reseed_after_writer'] is False, 'Declared bounded scheduling domain')
    for category in ('sources', 'tools', 'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts'):
        for path, digest in build[category].items():
            bind(path, digest)
    for path, digest in read(prep / 'pins.json')['files'].items():
        bind(path, digest)
    need(build['libraries'] == old_build['libraries'] and len(build['libraries']) == 2, 'Both FDIV libraries unchanged')
    old_objects = {key(p): h for p, h in old_build['entry_objects'].items()}
    new_objects = {key(p): h for p, h in build['entry_objects'].items()}
    need(len(old_objects) == 22 and len(new_objects) == 26 and all(new_objects.get(p) == h for p, h in old_objects.items()), 'Twenty-two accepted guest COFF objects reused unchanged')
    addition = set(new_objects) - set(old_objects)
    need(addition == {key(prep / (kind + '-' + level + '.obj')) for kind in ('fragment', 'provider') for level in ('O0', 'O2')}, 'Exactly four new heap AMD64 objects')
    old = ROOT / 'reports/m4-crt-locale-default/preparation-r4'
    changed = {'composition.cpp', 'mainargs_binding.inc', 'observations.hpp', 'main_v2.inc'}
    unchanged, differences = [], {}
    for original in old.iterdir():
        if original.suffix not in ('.cpp', '.hpp', '.inc'):
            continue
        candidate = prep / original.name
        bind(original)
        bind(candidate)
        if original.name in changed:
            diff = ''.join(difflib.unified_diff(original.read_text().splitlines(True), candidate.read_text().splitlines(True), fromfile='accepted/' + original.name, tofile='heap/' + original.name))
            need(diff, 'Declared additive source difference')
            output_path = out / (original.name + '.diff')
            output_path.write_text(diff, encoding='utf-8')
            bind(output_path)
            differences[original.name] = {'path': str(output_path), 'sha256': sha(output_path)}
        else:
            need(original.read_bytes() == candidate.read_bytes(), 'Ancestor source remains byte-identical: ' + original.name)
            unchanged.append(original.name)
    composition = (prep / 'composition.cpp').read_text()
    mainargs = (prep / 'mainargs_binding.inc').read_text()
    driver = (prep / 'main_v2.inc').read_text()
    body = (prep / 'heap_binding.inc').read_text()
    header = (prep / 'heap.hpp').read_text()
    need('mainargs_checkpoint(r,"mainargs-before");mainargs_binding->heap.start(c);' in mainargs, 'Explicit heap seam before parent mainargs field/provider admission')
    need('hi::Binding heap;' in mainargs and 'heap(context,provider,mode)' in mainargs, 'Known genuine heap member with immutable parent association')
    need('mg::Context*const admitted_parent_' in header and 'parent!=admitted_parent_' in body and 'admitted_parent_->source_identity()' in body and 'admitted_parent_->first' in body, 'Public parent checked before dereference; firstfault uses private known parent')
    need('if(authority&&authority!=this)authority->deny' in body and 'auto*known=authority;' in body and 'p!=known||owner!=known||binding!=known||admitted_binding!=known' in body, 'Private active authority denies stale and opaque tokens before casts')
    need('owner=nullptr;authority=nullptr;' in body and 'struct Cleanup' in body, 'RAII clears public/private authority after terminal observers')
    need('state.gpr.rip.dword=fragment;' in body and 'state.gpr.rsp.dword=' not in body and 'runtime.cpu()=' not in body and 'runtime.cpu().eip=' not in body and 'runtime.cpu().esp=' not in body, 'Scheduler changes only carried StatePC and performs no ESP/CPU projection')
    need('runtime.memory().store' not in body[body.index('[[noreturn]]void Binding::start'):], 'No host guest-stack store in explicit source fragment bootstrap')
    need('std::array<unsigned,17>composition_pages' in (prep/'observations.hpp').read_text(), 'All prior seventeen mapped pages remain')
    need('memory().map({0x78035000}' not in driver, 'No heap-global page mapped before unresolved native API')
    need('hi::has_authority()' in composition, 'Typed dispatch retains private heap authority when public owner is null')
    need('access_count!=2||undefined_count||depth!=2' in body and 'undefined_sites[undefined_count++]=entry;return 0;' in body, 'Exact source XOR undefined-AF representative0 admitted once, not a universal architectural value')
    need('original_import(provider)!=raw_import' in body and '"HeapCreate"' in body and '"KERNEL32.dll"' in body and '!=411' in body, 'Original PE32 unique named import metadata admits exact raw target')
    need('const auto&r=accesses[6]' in body and 'access_count!=8' in body and 'runtime.memory().load<unsigned>({admitted_frame_-16})!=api_ret' in body, 'Actual IAT read and genuine CALL store retained before typed API refusal')
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    bind(provider, '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    pe = PEImage(provider.read_bytes())
    llvm = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    for program in ('LLVM-C.dll', 'llvm-readobj.exe'):
        bind(llvm / program)
    api = LLVM(llvm / 'LLVM-C.dll')
    source_records = {}
    for kind, entry, extent in (('fragment', 0x7800183c, 7), ('provider', 0x780039bf, 77)):
        path = prep / (kind + '-source.bin')
        raw = path.read_bytes()
        offset, _ = pe.rva_range(entry - pe.image_base, extent)
        need(len(raw) == extent and raw == pe.read(offset, extent), 'Exact literal unpatched compiled body extent')
        guest, host = prep / (kind + '-guest.ll'), prep / (kind + '-host.ll')
        guest_abi = layouts(guest, 'sub_' + format(entry, 'x'), api)
        host_abi = layouts(host, 'mw34_heap_init_' + kind + '_body', api)
        need(guest_abi['pointer_bytes'] == 4 and host_abi['pointer_bytes'] == 8 and guest_abi['types'] == host_abi['types'] and host_abi['types']['struct.State']['size'] == 3504, 'Every source guest32/host64 named State layout agrees')
        need(f'target datalayout = "{HOST_LAYOUT}"' in host.read_text(), 'Actual AMD64 host ABI')
        source_records[kind] = {'entry': entry, 'bytes': extent, 'sha256': sha(path), 'named_State_types': len(host_abi['types']), 'ABI': host_abi}
        for level in ('O0', 'O2'):
            obj = prep / (kind + '-' + level + '.obj')
            command = [str(llvm / 'llvm-readobj.exe'), '--file-headers', '--symbols', '--unwind', str(obj)]
            result = subprocess.run(command, capture_output=True, timeout=30)
            need(result.returncode == 0, 'Independent actual COFF reader zero exit')
            output_path = out / (kind + '-' + level + '-coff.txt')
            output_path.write_bytes(result.stdout)
            bind(output_path)
            text = result.stdout.decode()
            need('IMAGE_FILE_MACHINE_AMD64' in text and 'mw34_heap_init_' + kind + '_body' in text, 'Actual matching AMD64 object symbol')
            need('RuntimeFunction' in text, 'Actual object unwind data for throwing source call chain')
    need(sum(row['bytes'] for row in source_records.values()) == 84, 'Eighty-four literal compiled and guarded bytes; thirty prefix bytes executed')
    closure = verify_manifest(files)
    report = {'passed': True, 'scope': 'Independent exact source/current build/State ABI/COFF audit; no execution credit',
        'build_path': str(build_path), 'build_sha256': sha(build_path), 'preparation_path': str(prep / 'report.json'),
        'preparation_sha256': sha(prep / 'report.json'), 'preparation_pins_sha256': sha(prep / 'pins.json'),
        'unchanged_source_components': unchanged, 'additive_source_differences': differences,
        'unchanged_guest_objects': 22, 'new_guest_objects': 4, 'unchanged_FDIV_libraries': 2,
        'compiled_source_bytes': 84, 'executed_prefix_bytes': 30, 'heap_source_identity_bytes': 84, 'total_source_identity_bytes': 1940,
        'source_records': source_records, 'physical_closure': closure,
        'Runtime_CPU_preserved': True, 'Runtime_call_record_added': False, 'State_reseed_after_writer': False,
        'original_executed': False, 'native_executed': False, 'HeapCreate_executed': False, 'heap_initialized': False, 'heap_handle_published': False, 'source_artifact_undefined_AF_representative': 0,
        'table_initialization_proved': False, 'whole_M4_complete': False}
    report_path = out / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    bind(report_path)
    (out / 'pins.json').write_text(json.dumps({'files': files}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': True, 'report_sha256': sha(report_path), 'pins_sha256': sha(out / 'pins.json'), 'physical_dependencies': len(files)}))


if __name__ == '__main__':
    main(*sys.argv[1:])
