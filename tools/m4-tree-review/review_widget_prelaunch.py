"""Independent bounded original widget first-writer prelaunch review."""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PINS = {}
ROOTS = [0x40e250, 0x40ef50, 0x5a3c30, 0x5a3ff0, 0x5a66f0]
GDI = [(0x5a0142, bytes.fromhex('898658020000')),
       (0x5a0645, bytes.fromhex('c7865802000000000000')),
       (0x5a0751, bytes.fromhex('85c0898658020000'))]


def need(value, why):
    if not value:
        raise ValueError(why)


def eq(a, b, why):
    need(a == b, why + ' ' + str((a, b))[:600])


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def pin(path, digest=None):
    path = Path(path).resolve()
    need(path.suffix.lower() not in ('.mwb', '.iso', '.zip'), 'No archive reader')
    key = str(path)
    value = PINS.get(key)
    if value is None:
        value = sha(path)
        PINS[key] = value
    need(digest is None or digest == value, 'Exact physical input ' + key)
    return path


def raw(path):
    return pin(path).read_bytes()


def read(path, digest=None):
    return json.loads(pin(path, digest).read_bytes())


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, pin(path))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sparse(data):
    eq(data[:8], b'MW4J124P', 'Exact inherited sparse carrier')
    count = struct.unpack_from('<I', data, 8)[0]
    eq(len(data), 12 + count * 4104, 'Every complete sparse page record')
    result = {}
    for index in range(count):
        at = 12 + index * 4104
        address, permission = struct.unpack_from('<II', data, at)
        need(address not in result and address % 4096 == 0 and permission in (0, 1, 2), 'Unique legacy0RO/1RX/2RW page')
        result[address] = (permission, data[at + 8:at + 4104])
    return result


def expected_widget(api, side):
    """Whole original CPU/flags/FP/selector observer, independently assembled."""
    code, relocations = bytearray(), []
    def emit(value):
        code.extend(bytes.fromhex(value))
    def address(name, addend=0, typ=6):
        relocations.append((len(code), name, typ))
        code.extend(struct.pack('<I', addend))
    for index, op in enumerate(('a3', '890d', '8915', '891d', '8925', '892d', '8935', '893d')):
        emit(op); address('_widget_cpu', index * 4)
    if side:
        emit('c705'); address('_widget_cpu', 36); code.extend(struct.pack('<I', GDI[api][0]))
    else:
        emit('a1'); address('_widget_targets', api * 4)
        emit('a3'); address('_widget_cpu', 36)
    emit('c705'); address('_widget_kind'); code.extend(struct.pack('<I', api * 2 + side))
    emit('8b25'); address('_mixed_host_esp')
    emit('9c8f05'); address('_widget_cpu', 32)
    emit('fc64a100000000a3'); address('_widget_head')
    for op, name in (('668cd866a3', '_widget_ds'), ('668cc066a3', '_widget_es'), ('668cd066a3', '_widget_ss')):
        emit(op); address(name)
    emit('0fae05'); address('_widget_fx')
    emit('d935'); address('_widget_env'); emit('d925'); address('_widget_env')
    emit('e8'); address('_widget_observe', 0, 0x14)
    emit('0fae0d'); address('_widget_fx'); emit('d925'); address('_widget_env')
    emit('ff35'); address('_widget_cpu', 32); emit('9d')
    for index, op in enumerate(('a1', '8b0d', '8b15', '8b1d', '8b25', '8b2d', '8b35', '8b3d')):
        if index != 4:
            emit(op); address('_widget_cpu', index * 4)
    emit('8b25'); address('_widget_cpu', 16)
    if side:
        code.extend(GDI[api][1])
    emit('ff25'); address('_widget_continues' if side else '_widget_targets', api * 4)
    return bytes(code), relocations


def main(preparation, prep_sha, build_path, build_sha, name):
    out = R / 'reports/m4-tree-review' / name
    need(not out.exists(), 'Additive review output')
    out.mkdir()
    counts, linked, passed = collections.Counter(), [], False
    try:
        prep = read(preparation, prep_sha)
        build = read(build_path, build_sha)
        need(prep['passed'] and build['passed'], 'Current actual preparation and build')
        directory, builddir = Path(preparation).parent, Path(build_path).parent
        eq(Path(build['preparation']).resolve(), directory.resolve(), 'Current compiler preparation source path')
        eq(build['preparation_sha256'], prep_sha, 'Actual current compilation source identity')
        need(all(command['exit_code'] == 0 for command in build['commands']), 'All actual compiler/link commands passed')
        for report, key in ((prep, 'files'), (build, 'sources'), (read(builddir / 'pins.json'), 'files')):
            for path, digest in report[key].items():
                pin(path, digest)
        eq([build[k] for k in ('roots', 'sequences', 'phases', 'record_bytes', 'pages', 'external_pages', 'combined_pages', 'snapshot_bytes')], [5, 1, 5, 356992, 43, 21, 64, 266964], 'Exact finite original five-root shared normal schedule and immutable ABI')
        for key in ('original_executed', 'trace_executed', 'trace_admitted', 'source_after_seed', 'predicted_counts_supplied_to_execution', 'provider_preinvoked', 'initializer_credit'):
            eq(prep[key], False, 'No runtime/numerical/initializer credit before actual execution: ' + key)
        eq((prep['snapshot_count_bound'], prep['FS_event_bytes'], prep['FS_event_bound'], prep['FS_hooks']), (384, 1224, 2048, 72), 'Exact finite observer capacity and raw16B FS views')
        eq((prep['actual_GDI_selector_descriptor_bytes_per_boundary'], prep['whole_CRT_phase_endpoint_pages']), (40, 64), 'Complete prepared descriptor and CRT endpoint domains')
        need(prep['actual_DS_ES_SS_flatness_observation_prepared'] and prep['actual_registry_BEFORE_full_capacity'] and prep['authentic_producer_API_initial_inputs_retained'], 'Genuine selector/producer/registry BEFORE inputs will be retained')
        C = module(R / 'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py', 'widget_independent_linked_coff')
        F = module(R / 'tools/m4-fs-source/observer_attribution.py', 'widget_independent_fs_builder')
        P = module(R / 'tools/analysis/pe.py', 'widget_physical_image')
        game = P.PEImage(raw(R / 'MW3/Mech3.exe'))
        crt = P.PEImage(raw(R / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'))
        cp = P.PEImage(raw(R / 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'))
        worker = P.PEImage(raw(pin(build['worker'], build['worker_sha256'])))
        eq((worker.machine, worker.image_base), (0x14c, 0x18000000), 'Actual linked fixed-base PE32 worker')
        nt = struct.unpack_from('<I', worker.data, 60)[0]
        size = struct.unpack_from('<I', worker.data, nt + 24 + 56)[0]
        need(worker.image_base + size <= 0x20000000, 'All worker sections and observer BSS stay below guest stack')
        def physical(image, address, length):
            start, _ = image.rva_range(address - image.image_base, length)
            return image.data[start:start + length]
        contracts = read(directory / 'normal-contracts.json')
        eq([row['root'] for row in contracts['roots']], ROOTS, 'Exact five requested source registration roots')
        for row in contracts['roots']:
            eq(struct.unpack('<I', physical(game, row['slot'], 4))[0], row['root'], 'Physical original initializer table slot')
            need(not row['callback_executed'], 'Shutdown callback remains unexecuted')
        rows = contracts['instructions']
        eq(len(rows), 1081, 'Complete frozen49-body physical source inventory')
        eq(sum(row['width'] for row in rows), 3350, 'Every physical new game source byte')
        for row in rows:
            eq(physical(game, row['pc'], row['width']), bytes.fromhex(row['bytes_hex']), 'Exact whole original game instruction span')
            counts['physical_widget_game_instruction_rows'] += 1
        for key in ('strdup_owner_claim', 'registered_shutdown_callbacks_executed', 'source_failure_unwind_admitted', 'trace_admitted'):
            need(not contracts[key], 'Current unexecuted/unresolved source scope preserved: ' + key)
        need(contracts['normal_counts_are_unmeasured'] and contracts['normal_initial_heap_owners_unclassified'], 'Expected constructor/handle counts do not seed execution')
        patches = contracts['normal_patch_spans']
        eq(len(patches), 81, 'Complete72FS/3GDI/4CP/capture/sentinel normal code patch inventory')
        for index, a in enumerate(patches):
            for b in patches[index + 1:]:
                need(a['PC'] + a['size'] <= b['PC'] or b['PC'] + b['size'] <= a['PC'], 'All actually active source patch spans disjoint')
            if a['raw'] is not None:
                image = cp if a['PC'] >= 0x78100000 else crt if a['PC'] >= 0x78000000 else game
                eq(physical(image, a['PC'], a['size']), bytes.fromhex(a['raw']), 'Every declared physical normal source patch span')
        sparse_pages = sparse(raw(directory / 'pages.bin'))
        parent_pages = sparse(raw(R / 'reports/m4-startup130-original/preparation-r2/pages.bin'))
        eq(len(sparse_pages), 159, 'Exact current sparse page inventory')
        for address, value in parent_pages.items():
            eq(sparse_pages[address], value, 'All inherited genuine sparse inputs preserved')
        eq(set(contracts['whole_pages']), set(prep['observed_pages']) | set(prep['external_pages']), 'Exact43ordinary+21extra complete whole source page inventory')
        eq(len(contracts['whole_pages']), 64, 'No repeated page silently increases coverage')
        for address in contracts['whole_pages']:
            need(address in sparse_pages, 'Every captured source page has declared BEFORE backing')

        release = builddir / 'build-x86/mw34_joint_startup124_original.dir/Release'
        linkfiles = list(release.rglob('link.command.1.tlog'))
        eq(len(linkfiles), 1, 'One actual compiler final link command')
        linktext = pin(linkfiles[0]).read_text(encoding='utf-16').upper()
        widget_symbols, widget_sections = C.coff(raw(release / 'widget_observer_x86.obj'))
        defs = {v['name']: v for v in widget_symbols.values() if v['section'] > 0 and v['storage'] == 2 and v['type'] == 0x20}
        eq(len(defs), 6, 'Exactly six actual executable GDI observer bodies')
        resolved = {}
        for api, label in enumerate(('stock', 'delete', 'create')):
            for side, suffix in enumerate(('entry', 'return')):
                name = '_widget_' + label + '_' + suffix
                symbol = defs[name]
                section = widget_sections[symbol['section']]
                expected, relocs = expected_widget(api, side)
                eq(section['bytes'][symbol['value']:symbol['value'] + len(expected)], expected, 'Whole independent assembled CPU/flags/trueESP/FP/selector/replay byte proof')
                actual_relocs = [(item['offset'] - symbol['value'], item['symbol']['name'], item['type']) for item in section['relocations'] if symbol['value'] <= item['offset'] < symbol['value'] + len(expected)]
                eq(actual_relocs, relocs, 'All actual GDI observer relocation identities')
                function = C.linked_function(worker, widget_symbols, widget_sections, name)
                eq(function['bytes'], len(expected), 'No executable wrapper bytes omitted')
                for item in function['relocations']:
                    value = item['actual_symbol_address']
                    need(item['symbol'] not in resolved or resolved[item['symbol']] == value, 'Every actual shared observer relocation target agrees')
                    resolved[item['symbol']] = value
                linked.append(function)
                counts['compiled_linked_GDI_functions'] += 1
                counts['compiled_linked_GDI_bytes'] += len(expected)
                counts['compiled_linked_GDI_relocations'] += len(relocs)
        for api, (pc, replay) in enumerate(GDI):
            eq(struct.unpack('<I', physical(worker, resolved['_widget_continues'] + api * 4, 4))[0], pc + len(replay), 'Actual whole compiled GDI continuation DWORD')
        need('WIDGET_OBSERVER_X86.OBJ' in linktext, 'Actual reviewed GDI object in current final link')
        fs = read(directory / 'fs-hook-bindings.json')
        eq(len(fs), 72, 'All actual FS observer sites')
        fs_symbols, fs_sections = C.coff(raw(release / 'fs_observer_x86.obj'))
        fs_defs = {v['name']: v for v in fs_symbols.values() if v['section'] > 0 and v['storage'] == 2 and v['type'] == 0x20}
        for row in fs:
            name = '_' + row['declared_observer']
            symbol = fs_defs[name]
            section = fs_sections[symbol['section']]
            expected, relocs, marks = F.expected_function(row['PC'], row['kind'], bytes.fromhex(row['raw_bytes']))
            eq(section['bytes'][symbol['value']:symbol['value'] + len(expected)], expected, 'Whole compiled FS before/sourceMOV/after observer')
            actual = [(item['offset'] - symbol['value'], item['symbol']['name'], item['type']) for item in section['relocations'] if symbol['value'] <= item['offset'] < symbol['value'] + len(expected)]
            eq(actual, relocs, 'Every compiled FS relocation')
            function = C.linked_function(worker, fs_symbols, fs_sections, name)
            eq(function['bytes'], len(expected), 'Whole FS linked function extent')
            linked.append(function)
            counts['compiled_linked_FS_functions'] += 1
            counts['compiled_linked_FS_bytes'] += len(expected)
            counts['compiled_linked_FS_relocations'] += len(relocs)
        need('FS_OBSERVER_X86.OBJ' in linktext, 'All actual FS objects linked')
        cpp_symbols, cpp_sections = C.coff(raw(release / 'reference.obj'))
        observer = C.linked_function(worker, cpp_symbols, cpp_sections, '_widget_observe')
        eq(observer['address'], resolved['_widget_observe'], 'Whole actual C++ observer target called by all six compiled wrappers')
        linked.append(observer)
        counts['compiled_linked_GDI_CPP_observers'] += 1

        cpp = raw(directory / 'reference.cpp').decode()
        header = raw(directory / 'widget_observer.hpp').decode()
        asm = raw(directory / 'reference_x86.asm').decode()
        need(cpp.index('Bounded actual source producer API ledger') < cpp.index('producer-api-ledger.bin'), 'Producer ledger bound precedes every exported ledger read')
        need('cmp eax,256\n jae api_ledger_overflow\n imul eax,eax,104' in asm and 'api_ledger_overflow:\n mov fs_error,1' in asm, 'Actual assembly refuses out-of-bound API ledger write')
        need('const std::array<NullHook,0>null_hooks{};' in cpp and 'const std::array<VtableHook,0>vtable_hooks{};' in cpp, 'No inherited finite NULL or vtable hook claims for unobserved widgets')
        need('mixed_input=mixed_after;' in cpp and 'mixed_input.esp=frame;mixed_input.pc=entries[phase]' in cpp, 'One persistent normal sequence with only caller entry framing between roots')
        need('const std::array<std::array<unsigned,3>,1> cases{{{0,0x37f,0}}}' in cpp, 'One genuine fixed CW/TOP0 normal input case')
        for marker in ('producer-api-initial/', 'registry-before-meta.bin', 'registry-before-backing.bin', '/CRT-before/', '/CRT-after/', '-segments.bin', '-snapshots.bin'):
            need(marker in cpp, 'Complete prepared actual BEFORE/source boundary export ' + marker)
        need('if(phase)' in cpp and cpp.count('if(page_permissions[i]==2)std::memcpy') == 1, 'Writable source pages initialized only once for complete five-root sequence')
        need('Original registry producer CALL/RET' in cpp or 'Actual original registry producer CALL/RET' in cpp, 'Genuine loader and registry producer executed before selected widgets')
        need('GetThreadSelectorEntry' in header and 'descriptor.BaseLow' in header and 'descriptor.HighWord.Bits.Default_Big' in header and 'WidgetSegments)==40' in header, 'Raw actual selector/LDT capture and explicit finite observed domain guard')
        need('SetLastError(error)' in header and 'if(widget_cpu.flags&0x400)' in header, 'Guest DF input and actual LastError preserved by observation')
        need('r={1,widget_resource_count,fs_phase_root,s.cpu.esi,s.cpu.eax,widget_count,1,0xffffffff}' in header and 'if(widget_resources[i].live)' in cpp, 'Only actual successful CreateFont results enter owned manual research cleanup')
        need('manual_research_seam=1' in header and 'reinterpret_cast<BOOL(WINAPI*)(HGDIOBJ)>(widget_targets[1])' in header, 'Manual source-callback-independent cleanup calls genuine named DeleteObject target')
        need('source_after_seed' in prep and not prep['source_after_seed'], 'No numerical/native expected result input')
        controller = raw(R / 'tools/m4-widget-original/run.py').decode()
        need("q['files'].get(str(build.resolve()))!=digest" in controller and "q['files'].get(str(Path(b['worker']).resolve()))!=b['worker_sha256']" in controller, 'First-writer controller requires exact independently reviewed build and worker')
        need('timeout_seconds=240' in controller and 'verify_stage(' in controller, 'Finite single stage and fresh actual transport validation')
        stage = pin(R / 'tools/m4-pipeline/stages.py')
        compiletext = pin(builddir / 'compile.log').read_text()
        need('/MACHINE:X86' in compiletext and '/W4 /WX' in compiletext and '0 Warning(s)' in compiletext and '0 Error(s)' in compiletext, 'Actual clean strict x86 C++/MASM compilation')
        tlogs = list(release.rglob('CL.read.1.tlog'))
        eq(len(tlogs), 1, 'One actual compiler read-dependency log')
        readtext = pin(tlogs[0]).read_text(encoding='utf-16')
        consumed = set()
        for line in readtext.splitlines():
            candidate = line.strip().lstrip('^')
            if candidate and Path(candidate).is_absolute() and Path(candidate).is_file():
                consumed.add(pin(candidate))
        for suffix in ('widget_observer.hpp', 'spec.hpp', 'protocol.hpp', 'original_broker.hpp'):
            need((directory / suffix).resolve() in consumed, 'Actual compiler consumed current prepared header ' + suffix)
        counts['actual_compiler_consumed_inputs'] = len(consumed)
        pin(__file__); pin(sys.executable)
        (out / 'compiled-observers.json').write_text(json.dumps(linked, indent=2) + '\n')
        pin(out / 'compiled-observers.json')
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(passed=passed, scope='Independent physical source/compiler/whole linked observer prelaunch for one shared genuine five-widget normal sequence. Actual values, handles, selectors, lifetimes, virtual dispatch and source semantic equivalence require subsequent authentic observations and separate validators.',
            preparation_sha256=prep_sha, build_sha256=build_sha, counts=dict(counts), files=PINS,
            roots=5, sequences=1, phases=5, record_bytes=356992, observed_pages=43, external_pages=21,
            whole_source_pages=64, snapshot_bytes=266964, actual_snapshot_count_and_handle_counts_known=False,
            full_selector_effective_limit_acceptance_pending=True, whole_provider_internal_behavior_credit=0,
            source_callback_and_failure_unwind_credit=0, manual_font_cleanup_source_callback_credit=0,
            resource_cleanup_caller_hardware_conservation_credit=0,
            initializer_credit=0, archive_reader_opened=False, worker_launched=False,
            source_AFTER_seed=False, prelaunch_justified=passed, all_bounded_readers_closed=True)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, path=str(out / 'report.json'), sha256=sha(out / 'report.json'), files=len(PINS), counts=dict(counts))))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve(), sys.argv[4], sys.argv[5])
