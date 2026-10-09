"""Independent native-only FDIV source/object/fault closure. No guest execution."""
from pathlib import Path
import hashlib, json, re, subprocess, sys, traceback

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'reports/m4-crt-fdiv'
OUT = BASE / 'independent-native-closure-r2'
LLVM = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS, ASSOCIATIONS, COMMANDS = {}, [], []

def need(ok, why):
    if not ok:
        raise ValueError(why)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def pin(path, expected=None):
    p = Path(path).resolve()
    h = sha(p)
    need(expected is None or h == expected, 'Exact frozen identity: '+str(p))
    need(str(p) not in PINS or PINS[str(p)] == h, 'One physical identity: '+str(p))
    PINS[str(p)] = h
    return p

def data(path, expected=None):
    return json.loads(pin(path, expected).read_text())

def run(arguments, name):
    args = list(map(str, arguments))
    result = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=60)
    output = OUT / name
    output.write_bytes(result.stdout)
    pin(output)
    COMMANDS.append(dict(command=args, exit_code=result.returncode,
                         log=str(output), sha256=sha(output)))
    need(result.returncode == 0, 'Actual read-only decode/dependency step: '+name)
    return result.stdout.decode(errors='replace')

def flat_map(path, replacements=None):
    mapping = data(path)
    mapping = mapping.get('files', mapping)
    need(isinstance(mapping, dict), 'Explicit physical flat map')
    count = 0
    for p, h in mapping.items():
        target = Path(p)
        if replacements and str(target.resolve()) in replacements:
            physical = replacements[str(target.resolve())]
            pin(physical, h)
            ASSOCIATIONS.append(dict(map=str(Path(path).resolve()), original_path=p,
                                     physical_literal=str(physical), sha256=h))
        else:
            pin(p, h)
        count += 1
    return count

def runtime_blocks(text):
    return re.findall(r'  RuntimeFunction \{.*?(?=\n  RuntimeFunction \{|\n\])', text, re.S)

def main():
    need(not OUT.exists(), 'Fresh private independent closure')
    OUT.mkdir(parents=True)
    try:
        author_report = data(BASE/'author-review-r1/report.json',
            'c3398673510bc8ff28079173d486d8dfe73b1c481541927e37fccfbb94cc99e1')
        author = data(BASE/'author-review-r1/pins.json',
            '2d3272ed71e22449c4564cbfd728712a3cf9b00c69a2629c73f1369807123d42')
        need(author_report['passed'] and not author_report['original_dynamic_writer_execution'],
             'Native-only frozen candidate scope')
        for b in author['bindings']:
            p = pin(b['path'], b['sha256'])
            need(p.stat().st_size == b['bytes'], 'Physical author extent')
        need(len(author['bindings']) == 2328 and len(author['historical_replacements']) == 14,
             'Whole author closure and history extent')
        for h in author['historical_replacements']:
            pin(h['physical_literal'], h['sha256'])
            b = data(h['build'])
            need(b['sources'][h['original_path']] == h['sha256'],
                 'Historical build source links literal replacement')
            ASSOCIATIONS.append(dict(kind='author historical source', **h))
        for s in author['literal_sources']:
            pin(s['path'], s['sha256'])
        primary = data(BASE/'native-build-r3/build.json',
            '8ffaaeb454ba3e97337606863d2be03b928559e87b003fd1b3ed43dbf8a70ebf')
        boundary = data(BASE/'native-boundary-r3/build.json',
            '76814525708d98b8ca36c6dd9a6f389bd51a9d5dbf426d7b31dab76d8dd77099')
        for b in (primary, boundary):
            need(b['passed'], 'Final candidate build status')
            for category in ('sources', 'tools', 'artifacts'):
                for p, h in b[category].items():pin(p, h)
        for p, h in boundary['libraries'].items():pin(p, h)
        runtime_cpp = pin(ROOT/'tools/m4-runtime/runtime.cpp',
            '48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7')
        pin(ROOT/'tools/m4-runtime/runtime.hpp',
            '41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536')
        # Static and predictive raw models are independent prior stages, read
        # and physically bound here; never imported as this review's executor.
        models = [
            ('independent-static-scope-r1', 'c2be15964692046e118a8be890ac0bee140988aa356e401024d5141718aa138c',
             '465e5a40bee7a1aae08c5d04477e00501f984a01387dc43c16e0d3ca9fa431dd'),
            ('independent-static-continuation-r2', 'bcea15a582799dda4eea11fa04c01db9415c4e0e6db3b9cb87a39f46495fdc2b',
             'cd012ccd9b1132a5c0fd63ef00d99895bd560e40a21360775b8b1149b8112fc9'),
            ('independent-native-model-r2', '3a88302fcea65b0f68f981bc508c3146740185641cfd6a9ed293c4be0bb41792',
             'cb10c6fa7320dbfa16ee774a7526d8b8169a9827c0bcd860ba4833dad4346463'),
            ('independent-compiled-r3', '068d696869323293decb17fd134f49542db6f5b701b32d753cb2090c16205c6b',
             '101fd6052fefe6c9921b2234d03a59a082d84294a10437d980bedc5727ddda22'),
        ]
        for name, report_h, pins_h in models:
            need(data(BASE/name/'report.json', report_h)['passed'], 'Frozen independent positive stage')
            pin(BASE/name/'pins.json', pins_h)
            flat_map(BASE/name/'pins.json')
        # Earlier own compiled sources changed only after each literal capture.
        for name in ('independent-compiled-r1', 'independent-compiled-r2'):
            for p in (BASE/name).rglob('*'):
                if p.is_file():pin(p)
        old = BASE/'independent-compiled-r2'
        replacement = {str((ROOT/'tools/m4-crt-fdiv-independent/compiled'/p.name).resolve()):p
                       for p in (old/'sources').iterdir() if p.is_file()}
        flat_map(old/'pins.json', replacement)
        for name in ('independent-native-model-r1', 'independent-static-continuation-r1',
                     'independent-native-closure-r1'):
            need((BASE/name).exists(), 'Retained literal independent failure/history')
            for p in (BASE/name).rglob('*'):
                if p.is_file():pin(p)
        api = data(BASE/'independent-api-association-r1/report.json')
        need(api['passed'] and api['native_records'] == 48 and
             sum(len(c['rejected']) for c in api['controls']) == 40 and
             not api['past_loaded_memory_attestation'], 'Independent API metadata association scope')
        flat_map(BASE/'independent-api-association-r1/pins.json')
        # Bind the actual new compiled source and exact source saved prebuild.
        src = Path(__file__).resolve().parent
        literal = OUT/'sources'
        literal.mkdir()
        for p in src.iterdir():
            if p.is_file():
                pin(p);(literal/p.name).write_bytes(p.read_bytes());pin(literal/p.name)
        checks = []
        ir = (BASE/'native-derived-r1/host.ll').read_text()
        entries = [0x78004254,0x7800426b,0x780042a3,0x780042cf,
                   0x780042e1,0x780042f7,0x7800432c,0x7800439f]
        need({int(x,16) for x in re.findall(r'^define ptr @mw34_fdiv_sub_([0-9a-f]+)\(',ir,re.M)} == set(entries),
             'Complete exact eight source function translations')
        need('nounwind' not in ir and 'willreturn' not in ir and 'setjmp' not in ir and
             'longjmp' not in ir, 'Faultable LLVM routes retain actual unwind capability')
        registry = (ROOT/'tools/m4-crt-fdiv/registry.cpp').read_text()
        h = (ROOT/'tools/m4-crt-fdiv/host_services.hpp').read_text()
        fnclex = (ROOT/'tools/m4-crt-fdiv/fnclex.hpp').read_text()
        need('bool Registry::initialize()noexcept' in registry and
             'catch(const MemoryFault&)' in registry and 'catch(...)' in registry and
             'restore_host(host_before_,env_before_);SetLastError(host_error);return success;' in registry,
             'Enclosing C++ catch and numerical restoration precede returned status')
        need('if(!fault_)fault_=Fault' in registry and 'if(fault_)return false' in registry and
             'owned_[i]' in registry and 'runtime_.memory().unmap({bases[i]})' in registry,
             'First error terminal registry and acquired-page-only cleanup')
        need('using Query=BOOL(WINAPI*)(DWORD)' in h and 'reinterpret_cast<Query>(feature_)(argument)' in h and
             'GetProcAddress(module_,"IsProcessorFeaturePresent")' in h and
             'GetModuleHandleA("KERNEL32")' in h and 'FreeLibrary(' not in h,
             'Actual named Windows query, borrowed module, typed target')
        need('0x80ff' in fnclex.lower(), 'FNCLEX exact defined 80FF clear mask')
        checks.append(dict(name='Source/ABI/ownership/fault policy',passed=True,
            complete_source_function_entries=entries, guest_host_pointer_conversion=False,
            source_import_words_preserved=True, query_result_is_external_input=True,
            native_volatile_representative=True, source_parent_execution=False))
        readobj, objdump = pin(LLVM/'llvm-readobj.exe'), pin(LLVM/'llvm-objdump.exe')
        substantive = []
        for level in ('O0','O2'):
            substantive.append((f'guest-{level}',BASE/'native-build-r3'/f'writer-{level}.obj'))
            folder = ROOT/f'build/m4-fdiv-native-build-r3-{level}'/'CMakeFiles'
            substantive.extend((f'{role}-{level}',next(folder.rglob(filename))) for role,filename in
                [('registry','registry.cpp.obj'),('runtime','runtime.cpp.obj'),
                 ('guest-memory','guest_memory.cpp.obj'),('guest-cw','guest_cw.cpp.obj'),
                 ('image-loader','image_loader.cpp.obj'),('author-worker','native_tests.cpp.obj')])
            substantive.append((f'author-boundary-{level}',next((ROOT/f'build/m4-fdiv-native-boundary-r3-{level}').rglob('boundary.cpp.obj'))))
            substantive.append((f'own-control-{level}',next((BASE/'independent-compiled-r3'/level).rglob('controls.cpp.obj'))))
        substantive += [('author-assembly',BASE/'native-boundary-r3/capture.obj'),
                        ('own-assembly',BASE/'independent-compiled-r3/boundary.obj')]
        need(len(substantive)==20, 'Substantive compiled-object review extent')
        object_checks = []
        for label, p in substantive:
            pin(p)
            metadata = run([readobj,'--unwind','--relocations','--symbols',p],label+'-coff.txt')
            code = run([objdump,'-d','--print-imm-hex',p],label+'-code.txt')
            need('Format: COFF-x86-64' in metadata and 'Arch: x86_64' in metadata,
                 'Actual compiled AMD64 object')
            blocks = runtime_blocks(metadata)
            if label in ('guest-O0','guest-O2'):
                for entry in entries:
                    need(any(f'StartAddress: mw34_fdiv_sub_{entry:x} ' in b for b in blocks),
                         'Every full guest source function has real unwind record')
                for symbol in ('mw34_fdiv_enter','mw34_fdiv___remill_read_memory_32',
                    'mw34_fdiv___remill_write_memory_32','mw34_fdiv___remill_function_call',
                    'mw34_fdiv_fnclex','mw34_fdiv_mw34_cf_store_cw','mw34_fdiv_mw34_cf_load_cw'):
                    need(symbol in metadata, 'Real compiled typed dependency relocation')
            if label.startswith('registry-'):
                found = [b for b in blocks if 'StartAddress: ?initialize@Registry@' in b]
                need(len(found)==1 and 'Handler: __CxxFrameHandler3' in found[0],
                     'Actual enclosing initialize EH handler')
                need('fxsave' in code and 'fxrstor' in code and 'fldenv' in code,
                     'Actual compiled numerical/legacy host restoration instructions')
            if label == 'own-assembly':
                need('StartAddress: own_fd_boundary' in metadata and
                     all(f'SAVE_XMM128 reg=XMM{i}' in metadata for i in range(6,16)) and
                     'own_fd_initialize' in metadata and 'fdiv' in code and 'fldenv' in code,
                     'Real own outside-return assembly fixture/unwind/call route')
            object_checks.append(dict(name=label,path=str(p),sha256=sha(p),
                                      runtime_functions=len(blocks),passed=True))
        checks.append(dict(name='Fresh independent full compiled object/decode review',passed=True,
                           objects=object_checks, count=len(object_checks),
                           real_guest_unwind_entries=16, enclosing_Registry_EH_handlers=2))
        # Read Ninja's real consumed source/header dependency log, without build.
        vs=Path('C:/Program Files/Microsoft Visual Studio/18/Community')
        ninja=pin(vs/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
        deps = set()
        occurrences = 0
        for level in ('O0','O2'):
            folder = BASE/'independent-compiled-r3'/level
            text=run([ninja,'-C',folder,'-t','deps'],f'own-{level}-consumed-deps.txt')
            pin(folder/'.ninja_deps');pin(folder/'build.ninja');pin(folder/'CMakeFiles/rules.ninja')
            for line in text.splitlines():
                if line.startswith('    '):
                    path=Path(line.strip())
                    if not path.is_absolute():path=folder/path
                    need(path.is_file(), 'Actual consumed own compiler dependency exists')
                    deps.add(str(pin(path)));occurrences+=1
        checks.append(dict(name='Own current compiler-read dependency association',passed=True,
            occurrences=occurrences,unique_files=len(deps),scope='Post-build disk hashes of actual Ninja consumed headers; no execution-time process/file attestation'))
        compiled = data(BASE/'independent-compiled-r3/report.json')
        need(all(x['result']['checks']==67288 and x['result']['scenarios']==50 for x in compiled['results']),
             'Own actual compiled causal extent unchanged')
        raw = data(BASE/'independent-native-model-r2/report.json')
        report = dict(passed=True,acceptance=True,
            scope='Native-only exact FDIV writer and owned Registry successful Windows lookup route; no original differential or complete CRT/startup acceptance',
            author_report_sha256=sha(BASE/'author-review-r1/report.json'),
            author_pins_sha256=sha(BASE/'author-review-r1/pins.json'),author_bindings_rehashed=2328,
            historical_author_source_associations=14,author_literal_sources_rehashed=len(author['literal_sources']),
            own_prior_source_associations=len(ASSOCIATIONS)-14,
            native_records=raw['native_records'],actual_source_PCs=raw['executed_source_PCs'],
            static_source_PCs=raw['source_PCs'],whole_State_bytes=3504,whole_pages=9,
            actual_events=raw['actual_events'],actual_stdcall_routes=raw['actual_stdcall_routes'],
            raw_independent_corruptions=raw['observer_corruption_rejects'],
            own_compiled_results=compiled['results'],own_API_association=api,
            compiled_object_decodes=len(object_checks),checks=checks,
            numeric_host_boundary='Own assembly observes after actual Registry.initialize returns before restoring harness state: occupied TOP6/depth2/PE/CW0B7F, complete ENV28/x87/raw80/MXCSR and seeded ABI XMM6-15 on actual success and faults',
            undefined_fields='FNCLEX C0/C1/C2/C3 and native AF are representatives/observations, not broad architectural guarantees; source external API volatile ECX/EDX/flags retain original measurement distinction',
            first_fault='Terminal Registry retains first typed PC/address/reason and full State/softwareFX/pages/access prefix; generic raw GuestMemory-integrity failures retain the existing coarser diagnostics',
            partial_ownership='Only successful owned page mappings released; all seven foreign whole-page sentinels survive partial admission; stable serial constructing thread required',
            actual_API_scope='Own compiled current-process pointer/module/VirtualQuery/path/disk SHA query; all48 prior records independently associate serialized named exports via recorded ASLR-relative RVA with current hash-identical disk PE RX/export metadata. No past in-memory/process-time attestation.',
            no_author_comparator_model_fixture_or_executor_imports=True,
            original_dynamic_writer_execution=False,source_parent_execution=False,
            full_CRT=False,whole_M4_complete=False,
            preserved_own_seal_failure='r1 incorrectly applied the guest-function unwind requirement to the guest-memory object because its label also started guest-. Exact r1 source/failure/decodes retained; only label selection corrected.',
            limitations=author_report['limitations']+[
                'Broad exhaustive typed FNCLEX status primitive controls do not expand the writer beyond12 masked IC0/empty TOP0/SW0 cases',
                'Isolated late-negative bridge fixtures are not actual OS NULL observations or a complete compiled arithmetic fallback',
                'Volatile host XMM0-5 and reserved FX transport padding excluded from caller ABI preservation',
                'State/software CW transport is distinct from complete numerical hardware CW synchronization',
            ],commands=COMMANDS,physical_bindings_before_report=len(PINS))
        (OUT/'historical-associations.json').write_text(json.dumps(ASSOCIATIONS,indent=2)+'\n')
        pin(OUT/'historical-associations.json')
        (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(OUT/'report.json')
        for p,h in PINS.items():need(sha(p)==h,'Final immutable rehash: '+p)
        (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,report_sha256=sha(OUT/'report.json'),
            pins_sha256=sha(OUT/'pins.json'),physical_bindings=len(PINS),compiled_objects=len(object_checks))))
    except Exception:
        (OUT/'failure.txt').write_text(traceback.format_exc())
        raise

if __name__ == '__main__':main()
