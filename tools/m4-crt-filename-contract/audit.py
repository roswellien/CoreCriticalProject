"""Independent read-only association/source audit of the additive filename seam.

Runs only LLVM COFF metadata inspection; no original/provider/native worker is
executed. The API contract is distinct from unobserved original x86 volatility.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import ntpath
import re
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage


def need(condition, why):
    if not condition: raise ValueError(why)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def one(text, old, new):
    need(text.count(old) == 1, 'Exact unique derivative seam: ' + old[:80])
    return text.replace(old, new)


def main(prep_name, build_name, out_name):
    base = ROOT / 'reports/m4-crt-filename'
    prep, build, out = base / prep_name, base / build_name, base / out_name
    need(out.parent == base and out_name.startswith('independent-contract-') and not out.exists(), 'Fresh owned audit namespace')
    out.mkdir()
    pins, canonical, checks = {}, {}, []
    def bind(path, expected=None):
        path = Path(path); digest = sha(path)
        need(expected is None or digest == expected, 'Physical association changed: ' + str(path))
        key = ntpath.normcase(ntpath.normpath(str(path)))
        need(key not in canonical or canonical[key] == digest, 'Same physical path digest conflict')
        canonical[key] = digest; pins[str(path)] = digest
        return digest
    manifest = read(build / 'build.json'); previous = read(ROOT / 'reports/m4-crt-mainargs/build-r2/build.json')
    need(manifest['passed'] and previous['passed'], 'Passed literal builds required')
    build_sha = bind(build / 'build.json')
    bind(ROOT / 'reports/m4-crt-mainargs/build-r2/build.json', '9801c1ca6aa4a4b27f05515072b6ae29831d35d3786d9af92d80478389207cdf')
    bind(ROOT / 'reports/m4-crt-mainargs/root-acceptance-r1/report.json')
    for category in ['sources', 'tools', 'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts']:
        for path, digest in manifest[category].items(): bind(path, digest)
    for path, digest in read(prep / 'pins.json')['files'].items(): bind(path, digest)
    bind(prep / 'pins.json'); bind(prep / 'report.json', manifest['preparation_sha256'])
    need(ntpath.normcase(ntpath.normpath(manifest['preparation_path'])) == ntpath.normcase(str(prep / 'report.json')), 'Preparation/build association')
    for path, digest in manifest['sources'].items():
        preserved = build / 'sources' / Path(path).relative_to(ROOT)
        bind(preserved, digest)
    need(manifest['entry_objects'] == previous['entry_objects'], 'All twelve predecessor guest COFF objects must remain exact')
    need(manifest['libraries'] == previous['libraries'], 'Both predecessor FDIV libraries must remain exact')
    old = ROOT / 'reports/m4-crt-mainargs/preparation-r2'
    names = ['composition.cpp', 'main_v2.inc', 'observations.hpp', 'seed.hpp', 'matherr_context.hpp', 'control_context.hpp',
             'initterm_context.hpp', 'initterm_binding.inc', 'control_binding.inc', 'crt_services.cpp', 'crt_services.hpp',
             'mainargs_context.hpp', 'mainargs_binding.inc']
    for name in names:
        bind(old / name); bind(prep / (name + '.ancestor'))
        need((old / name).read_bytes() == (prep / (name + '.ancestor')).read_bytes(), 'Literal predecessor copy changed')
        if name not in ['composition.cpp', 'main_v2.inc']:
            need((old / name).read_bytes() == (prep / name).read_bytes(), 'Frozen context/Session/seed/observation component changed: ' + name)
    composed = (prep / 'composition.cpp').read_text()
    reverse = composed
    for after, before in [
        ('#include "mainargs_context.hpp"\n#include "filename.hpp"', '#include "mainargs_context.hpp"'),
        ('namespace mg=mw34::m4_crt_entry_mainargs;\nnamespace fn=mw34::m4_crt_filename;', 'namespace mg=mw34::m4_crt_entry_mainargs;'),
        ('#include "mainargs_binding.inc"\n#include "filename_binding.inc"', '#include "mainargs_binding.inc"'),
        ('if(fn::binding||fn::admitted_binding){auto*f=fn::current(*mg::owner);if(f->returned&&mg::owner->state.gpr.rip.dword==fn::stop_pc)f->stop(a,p);}return mg::owner->read(a);', 'return mg::owner->read(a);'),
        ('if(fn::binding||fn::admitted_binding){fn::current(*mg::owner)->invoke(s,a,p);return p;}mg::owner->called(s,a);', 'mg::owner->called(s,a);'),
    ]: reverse = one(reverse, after, before)
    need(reverse == (old / 'composition.cpp').read_text(), 'Composition is not the exact additive five-seam derivative')
    driver = (prep / 'main_v2.inc').read_text(); original_driver = (old / 'main_v2.inc').read_text()
    reversed_driver = driver
    substitutions = [
        ('namespace mw34::m4_crt_filename {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}\n', ''),
        ('fn::LastErrorBoundary errors(&fn::outer_error_after);fn::outer_error_before=errors.saved;InvocationHostBoundary host;', 'InvocationHostBoundary host;'),
        ('unsigned fault_reason{},fault_pc{},fault_target{};void(*unit)(){};', 'unsigned fault_reason{},fault_pc{},fault_target{};'),
        ('try {if(j->unit){j->unit();j->ok=true;return true;}if(j->writer)', 'try {if(j->writer)'),
        ('#include "units.inc"\n', ''),
        ('scenario<36', 'scenario<84'),
        ('scenario<24?0:scenario+37', 'scenario<24?0:scenario-23'),
        ('MainargsBinding mainargs(r,provider,mode);fn::Binding filename(mainargs.context,mode,0xa11c0000U+scenario);', 'MainargsBinding mainargs(r,provider,mode);'),
        ('mainargs_binding=&mainargs;fn::binding=&filename;fn::admitted_binding=&filename;boundary', 'mainargs_binding=&mainargs;boundary'),
        ('mainargs_binding=nullptr;fn::binding=nullptr;fn::admitted_binding=nullptr;', 'mainargs_binding=nullptr;'),
        ('FaultReason::unresolved_translation)&&entry_job.fault_pc==fn::stop_pc&&entry_job.fault_target==fn::commandline', 'FaultReason::unresolved_import)&&entry_job.fault_pc==mg::import_call&&entry_job.fault_target==mg::import_slot'),
        ('mainargs.context.event_count==6', 'mainargs.context.event_count==4'),
        ('"Literal builder resumes after native filename stdcall return and stops before command-line producer read"', '"Literal mainargs/helper source reaches named OS import before parser"'),
        ('} else require(entry_job.fault_pc!=fn::stop_pc||entry_job.fault_target!=fn::commandline', '} else require(entry_job.fault_pc!=mg::import_call||entry_job.fault_target!=mg::import_slot'),
    ]
    for after, before in substitutions: reversed_driver = one(reversed_driver, after, before)
    reversed_driver = reversed_driver.replace('MW34_CRT_FILENAME_NO_MAIN', 'MW34_ENTRY_MAINARGS_NO_MAIN')
    for expression in [r'filename_units_directory=directory/"units";[^\n]*\n ', r'std::array<unsigned,22>filename_job\{.*?\n  (?=require\(entry_job.denied&&r.poisoned\(\))']:
        reversed_driver, count = re.subn(expression, '', reversed_driver, count=1, flags=re.S)
        need(count == 1, 'Exact additive unit/POD evidence driver seam')
    if reversed_driver != original_driver:
        (out / 'driver-reversal-diff.txt').write_text(''.join(difflib.unified_diff(original_driver.splitlines(True), reversed_driver.splitlines(True))))
    need(reversed_driver == original_driver, 'Main driver differs beyond declared unit/control/evidence/LastError additions')
    game = ROOT / 'MW3/Mech3.exe'; provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    bind(game, '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    bind(provider, '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    image = PEImage(provider.read_bytes())
    def source(va, size): return image.data[image.rva_range(va-image.image_base,size)[0]:][:size]
    need(source(0x7800bbd0,6).hex() == 'ff1518e00278' and source(0x7800bbd6,5).hex() == 'a174710378', 'Exact provider CALL and immediate MOV EAX source')
    need(struct.unpack('<I', source(0x7802e018,4))[0] == 0x343b0, 'Literal API IAT raw target')
    llvm = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    inspector = llvm / 'llvm-readobj.exe'; bind(inspector)
    static_commands = []
    for level in ['O0', 'O2']:
        compile_commands = build / level / 'compile_commands.json'; bind(compile_commands)
        rows = read(compile_commands)
        association = [r for r in rows if Path(r['file']).name == 'composition.cpp']
        need(len(association) == 1, 'Unique compiled composition source')
        command = association[0]['command']
        need('/EHs' in command and '/EHsc' not in command and ('/Od' if level == 'O0' else '/O2') in command, 'Actual C++ exception and optimization flags')
        need('ADDRESS_SIZE_BITS=32' in command and str(prep).lower() in command.lower(), 'Compiler State ABI/header/source association')
        obj = next(Path(p) for p in manifest['artifacts'] if p.endswith('composition.cpp.obj') and '/' + level + '/' in p.replace('\\','/'))
        target = out / ('composition-' + level + '-coff.txt')
        args = [str(inspector), '--file-headers', '--unwind', '--symbols', '--relocations', str(obj)]
        process = subprocess.run(args, capture_output=True)
        need(process.returncode == 0, 'Read-only actual COFF inspection')
        target.write_bytes(process.stdout); (out / ('composition-' + level + '-coff.stderr')).write_bytes(process.stderr)
        content = process.stdout.decode()
        need('IMAGE_FILE_MACHINE_AMD64' in content and 'RuntimeFunction {' in content and '__CxxFrameHandler3' in content, 'Actual composition AMD64 language unwind closure')
        need('Binding@m4_crt_filename' in content and '__remill_read_memory_32' in content and '__remill_function_call' in content, 'Actual filename method/bridge COFF definitions')
        static_commands.append({'arguments': args, 'exit_code': process.returncode, 'output_sha256': bind(target), 'stderr_sha256': bind(out / ('composition-' + level + '-coff.stderr'))})
        worker = Path(manifest['workers'][level]); data = worker.read_bytes(); pe = struct.unpack_from('<I', data,0x3c)[0]
        need(data[pe:pe+4] == b'PE\0\0' and struct.unpack_from('<H',data,pe+4)[0] == 0x8664, 'Actual linked AMD64 worker')
    for path, digest in list(pins.items()): bind(path, digest)
    for path in [Path(__file__), ROOT / 'tools/analysis/pe.py', ROOT / 'reports/m4-crt-mainargs/recovery-r3/normal_argv-host.ll',
                 ROOT / 'reports/m4-crt-mainargs/recovery-r3/normal_argv-source.bin', ROOT / 'runtime/memory/guest_memory.cpp', ROOT / 'tools/m4-crt-fdiv/host_services.hpp']:
        bind(path)
    contract = {
        'source_call': {'PC':0x7800bbd0,'IAT':0x7802e018,'raw':0x343b0,'return_PC':0x7800bbd6,'frame':0x20001834,'arguments':[0,0x7803b3f0,260]},
        'service': {'actual_native_export':'GetModuleFileNameA','module':'NULL actual AMD64 process worker, not the guest Mech3 executable','scratch':'All260 bytes seeded from carried guest buffer; immediate actual DWORD result and thread LastError retained in private immutable witness','transfer':'GuestMemory validates entire260-byte range before copying; checked transfer precedes guest EAX/ESP/PC publication','return':'Declared x86 stdcall service ABI: EAX=result, ESP=20001844, PC=7800BBD6; source CALL return/argument words remain in stack memory','other_State_FX':'Explicit native representative preserves every other software State byte and distinct FX; no original x86 volatile effect equivalence asserted','LastError':'Authored incoming sentinel and immediate API outcome are proposed typed guest-thread metadata, not initialized guest TEB state; real enclosing host caller error restored'},
        'next_stop': {'PC':0x7800bbd6,'operand':0x78037174,'instruction':'MOV EAX,[78037174]','read_executed':False,'EAX_store_executed':False,'fault':'public unresolved_translation through enclosing Runtime poison/owner cleanup'},
        'whole_buffer_tail':'Actual provider observation includes all bytes, including untouched suffix; no invented filename or terminator/tail',
        'public_cleanup':'Filename active cleared on observer/host exceptions; nested depth unwinds and mainargs owner/activity cleared before outer checkpoints; worker clears both filename side-binding pointers after boundary',
        'ownership':'Global call/read dispatch validates binding==separately admitted_binding and binding.context==current mainargs owner before any stale Binding field/method access; direct guard attributes stale-context fault to actual current mg owner',
        'API_docs': [
            {'url':'https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-getmodulefilenamea','verified':'2026-10-08','contract':'NULL means current process executable; success length excludes NUL, modern truncation returns capacity and ERROR_INSUFFICIENT_BUFFER; historical XP differs.'},
            {'url':'https://learn.microsoft.com/en-us/windows/win32/api/errhandlingapi/nf-errhandlingapi-getlasterror','verified':'2026-10-08','contract':'Error is per-thread; capture immediately before subsequent calls can replace it; successful API behavior must be witnessed.'},
            {'url':'https://learn.microsoft.com/en-us/cpp/cpp/argument-passing-and-naming-conventions?view=msvc-170','verified':'2026-10-08','contract':'x86 DWORD return in EAX; stdcall callee cleans three DWORD arguments plus source return word.'}],
    }
    result = {'passed':True,'scope':'Independent read-only final filename additive source/API/ABI/COFF association audit; no original/provider/native worker executed by this audit',
              'preparation':str(prep),'build':str(build/'build.json'),'build_sha256':build_sha,
              'exact_composition_inverse_seams':5,'exact_driver_inverse':True,'unchanged_ancestor_components':11,
              'unchanged_guest_COFF_objects':12,'unchanged_FDIV_libraries':2,'physical_unique_associations':len(canonical),
              'new_maps':0,'State_reseed':False,'FX_reseed':False,'compiled_State_header_sha256':manifest['compiler_read_headers'][str(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h')],
              'source_contract':contract,'static_metadata_commands':static_commands,
              'limitations':['This is an API/representative-State contract and additive source/build review; actual native rows and independent BEFORE-only full-State/page oracle are separate required gates.',
                             'No original x86 filename import execution, native/original volatile CPU equality, successful command-line load/parser/argv/environment or full CRT/M4 credit.',
                             'SDK libraries are linked via recorded search environment, not file-open attestation; existing object/source/recipe identities remain the narrow association.']}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n')
    print(json.dumps({'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json'),'associations':len(canonical),'build_sha256':build_sha}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('preparation');parser.add_argument('build');parser.add_argument('out')
    args = parser.parse_args()
    main(args.preparation,args.build,args.out)
