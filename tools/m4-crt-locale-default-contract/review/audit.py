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
ROOT = Path(__file__).absolute().parents[3]
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
    base = ROOT / 'reports/m4-crt-locale-default-contract/review'
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
    old_build_path = ROOT / 'reports/m4-crt-parser-prefix/build-r2/build.json'
    bind(old_build_path, '215cdc4fc04cbc2163250a1746f1a5d20411bc3f0a57f3680212682c1596654a')
    bind(ROOT / 'reports/m4-crt-parser-prefix/root-acceptance-r1/report.json', 'b78c296b69dc15abf6b88d4901c8742875ca25de417497233e0687ee2704b964')
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
    need(len(old_objects) == 16 and len(new_objects) == 22 and all(new_objects.get(p) == h for p, h in old_objects.items()), 'Sixteen accepted guest COFF objects reused unchanged')
    addition = set(new_objects) - set(old_objects)
    need(addition == {key(prep / (kind + '-' + level + '.obj')) for kind in ('mbinit', 'setmbcp', 'lock') for level in ('O0', 'O2')}, 'Exactly six new locale AMD64 objects')
    old = ROOT / 'reports/m4-crt-parser-prefix/preparation-r3'
    changed = {'composition.cpp', 'mainargs_binding.inc', 'observations.hpp', 'main_v2.inc'}
    unchanged, differences = [], {}
    for original in old.iterdir():
        if original.suffix not in ('.cpp', '.hpp', '.inc'):
            continue
        candidate = prep / original.name
        bind(original)
        bind(candidate)
        if original.name in changed:
            diff = ''.join(difflib.unified_diff(original.read_text().splitlines(True), candidate.read_text().splitlines(True), fromfile='accepted/' + original.name, tofile='locale/' + original.name))
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
    body = (prep / 'locale_binding.inc').read_text()
    header = (prep / 'locale.hpp').read_text()
    need('mainargs_checkpoint(r,"mainargs-before");mainargs_binding->locale.start(c);if(cm::binding' in mainargs, 'Explicit seam precedes both commandline producer and mainargs field admission')
    need('ld::Binding locale;' in mainargs and 'locale(context,provider,mode)' in mainargs, 'Locale has known immutable genuine parent member')
    need('mg::Context*const admitted_parent_' in header and 'parent!=admitted_parent_' in body and 'admitted_parent_->source_identity()' in body and 'admitted_parent_->first' in body, 'Compare public parent before dereference and firstfault through private association')
    need('if(authority&&authority!=this)authority->deny' in body and 'auto*known=authority;' in body and 'p!=known||owner!=known||binding!=known||admitted_binding!=known' in body, 'Current private authority controls stale/opaque admission before cast')
    need('owner=nullptr;authority=nullptr;' in body and 'struct Cleanup' in body, 'RAII clears public and private authority across terminal observer faults')
    need('state.gpr.rsp.dword=frame;state.gpr.rip.dword=entry;' in body and 'runtime.cpu()=' not in body and 'runtime.cpu().eip=' not in body and 'runtime.cpu().esp=' not in body, 'Scheduling changes only carried State EIP/ESP, preserving generic CPU')
    need('std::array<unsigned,17>composition_pages' in (prep / 'observations.hpp').read_text() and '0x5e0000,0x78001000,0x78003000};' in (prep / 'observations.hpp').read_text(), 'Seventeen pages with exactly one new source RX page')
    need('memory().map({0x78003000},4096' in driver and 'memory().protect({0x78003000},Permissions::read|Permissions::execute)' in driver, 'Explicit literal new raw source page mapping')
    need('if(ld::owner)' in composition or 'if(ld::has_authority())' in composition, 'Locale typed dispatch exists')
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    bind(provider, '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    pe = PEImage(provider.read_bytes())
    llvm = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    for program in ('LLVM-C.dll', 'llvm-readobj.exe'):
        bind(llvm / program)
    api = LLVM(llvm / 'LLVM-C.dll')
    source_records = {}
    for kind, entry, extent in (('mbinit', 0x78003dd2, 9), ('setmbcp', 0x78003ddb, 169), ('lock', 0x78001055, 43)):
        path = prep / (kind + '-source.bin')
        raw = path.read_bytes()
        offset, _ = pe.rva_range(entry - pe.image_base, extent)
        need(len(raw) == extent and raw == pe.read(offset, extent), 'Exact literal unpatched compiled body extent')
        guest, host = prep / (kind + '-guest.ll'), prep / (kind + '-host.ll')
        guest_abi = layouts(guest, 'sub_' + format(entry, 'x'), api)
        host_abi = layouts(host, 'mw34_locale_default_' + kind + '_body', api)
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
            need('IMAGE_FILE_MACHINE_AMD64' in text and 'mw34_locale_default_' + kind + '_body' in text, 'Actual matching AMD64 object symbol')
            need('RuntimeFunction' in text, 'Actual object unwind data for throwing source call chain')
    need(sum(row['bytes'] for row in source_records.values()) == 221, 'Bounded compiled source221 bytes; full source identity269 bytes')
    closure = verify_manifest(files)
    report = {'passed': True, 'scope': 'Independent exact source/current build/State ABI/COFF audit; no execution credit',
        'build_path': str(build_path), 'build_sha256': sha(build_path), 'preparation_path': str(prep / 'report.json'),
        'preparation_sha256': sha(prep / 'report.json'), 'preparation_pins_sha256': sha(prep / 'pins.json'),
        'unchanged_source_components': unchanged, 'additive_source_differences': differences,
        'unchanged_guest_objects': 16, 'new_guest_objects': 6, 'unchanged_FDIV_libraries': 2,
        'compiled_source_bytes': 221, 'locale_source_identity_bytes': 269, 'total_source_identity_bytes': 1856,
        'source_records': source_records, 'physical_closure': closure,
        'Runtime_CPU_preserved': True, 'Runtime_call_record_added': False, 'State_reseed_after_writer': False,
        'original_executed': False, 'native_executed': False, 'malloc_body_executed': False,
        'table_initialization_proved': False, 'whole_M4_complete': False}
    report_path = out / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    bind(report_path)
    (out / 'pins.json').write_text(json.dumps({'files': files}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': True, 'report_sha256': sha(report_path), 'pins_sha256': sha(out / 'pins.json'), 'physical_dependencies': len(files)}))


if __name__ == '__main__':
    main(*sys.argv[1:])
