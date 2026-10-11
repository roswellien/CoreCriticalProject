"""Bounded original138 recipe/consumed-source review. Never opens captures.

Linked observer attribution and first-writer admission are a separate root gate.
"""
from pathlib import Path
import hashlib, json, re, struct, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
P = R / 'reports/m4-startup138-original/preparation-r7'
O = R / 'reports/m4-startup131-original/preparation-r4'
F = R / 'reports/m4-fps-original/preparation-r1'
B = R / 'reports/m4-startup138-original/build-r4'
ROOTS = (0x40e250, 0x40ef50, 0x40f000, 0x479590, 0x5a3c30, 0x5a3ff0, 0x5a66f0)
PHASES = (15, 16, 17, 47, 134, 135, 136)
PINS = {}

def need(value, message):
    if not value:
        raise ValueError(message)

def pin(path, expected=None):
    path = Path(path).resolve()
    need(path.suffix.lower() not in ('.mwb', '.mwi', '.zip'), 'No archive input')
    need(path.name not in ('transport.json', 'manifest.json', 'bundle.json'), 'No capture metadata input')
    with path.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    need(expected is None or expected == digest, 'Exact physical input ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == digest, 'No conflicting identity')
    PINS[str(path)] = digest
    return path

def read(path, expected=None):
    return json.loads(pin(path, expected).read_text(encoding='utf-8-sig'))

def text(path):
    return pin(path).read_text(encoding='utf-8-sig')

def main(name):
    out = R / 'reports/m4-tree-review' / name
    need(not out.exists(), 'Fresh additive review only')
    out.mkdir(parents=True)
    passed = False
    counts = {}
    try:
        p = read(P/'report.json', 'e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2')
        b = read(B/'build.json', '748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69')
        old = read(O/'report.json', p['parent_preparation_sha256'])
        family = read(F/'report.json', p['family_preparation_sha256'])
        need(p['passed'] and b['passed'] and old['passed'] and family['passed'], 'Passed current recipes/build')
        need(b['preparation_sha256'] == PINS[str((P/'report.json').resolve())], 'Current preparation/build edge')
        need((p['original_roots'],p['original_phases'],p['original_sequences'],p['record_bytes']) == (138,828,6,356992), 'Exact original extent')
        need((b['roots'],b['phases'],b['sequences'],b['record_bytes'],b['combined_pages']) == (138,828,6,356992,69), 'Exact built extent')
        for receipt, field in ((p,'files'), (b,'sources')):
            for path, digest in receipt[field].items():
                pin(path, digest)
        pin(b['worker'], b['worker_sha256'])
        pin(B/'pins.json')
        pin(R/'tools/m4-startup138-original/build.ps1')
        run = text(R/'tools/m4-startup138-original/run.py')
        pin(R/'tools/m4-pipeline/stages_capture_storage.py')
        pin(R/'tools/m4-pipeline/paths_capture_storage.py')
        storage = read(R/'reports/m4-tree-review/capture-storage-r1/report.json', '74920256d02e000da908748ac96857a69cce60d20dad9ff9cd8e9ea87a3538b7')
        need(storage['passed'] and storage['hash_index_payload_limits_and_stable_close_unchanged'], 'Reviewed stable storage boundary')
        need("cwd=STORAGE_ROOT" in run and 'q[\'files\'].get(str(Path(b[\'worker\']).resolve()))' in run, 'Actual current worker/review/storage controller binding')

        # Independently reconstruct the entire generated reference from the
        # accepted parent plus all declared exact source hunks and two counts.
        deltas = read(P/'source-deltas.json')
        reference = text(O/'reference.cpp')
        for row in deltas:
            need(reference.count(row['before']) == 1, 'Unique exact declared source hunk')
            reference = reference.replace(row['before'], row['after'], 1)
        reference = reference.replace('/786 actual original initializer phases', '/828 actual original initializer phases')
        need(reference.count('std::array<void*,134> pages') == 1, 'Exact sparse page array expansion')
        reference = reference.replace('std::array<void*,134> pages', 'std::array<void*,161> pages', 1)
        for before, after in (('MW4J131D','MW4J138D'),('MW4J131O','MW4J138O'),('Original131','Original138'),('full131','full138'),('Exact101callback','Exact108callback')):
            reference = reference.replace(before, after)
        need(reference == text(P/'reference.cpp'), 'Whole generated reference exact relation')
        for path in P.iterdir():
            if path.is_file() and (O/path.name).exists() and path.suffix in ('.asm','.hpp') and path.name not in ('fs_observer_x86.asm','protocol.hpp','spec.hpp','original_broker.hpp'):
                need(pin(path).read_bytes() == pin(O/path.name).read_bytes(), 'Entire unchanged inherited observation source ' + path.name)
        for name_, old_size, new_size in (('widget_observer.hpp',266964,287444),('fps_observer.hpp',529700,550180)):
            expected = text(F/name_).replace(',pages[64*4096]', ',pages[69*4096]').replace('=='+str(old_size), '=='+str(new_size))
            need(expected == text(P/name_), 'Exact family observation page expansion')
        prior = R/'reports/m4-startup138-original/preparation-r6'
        for path in prior.iterdir():
            if path.is_file() and path.name not in ('report.json','pins.json','protocol.hpp'):
                need(pin(path).read_bytes() == pin(P/path.name).read_bytes(), 'Prep6 to7 unchanged generated input ' + path.name)
        need(text(P/'protocol.hpp') == text(prior/'protocol.hpp').replace('memory_size==151552','memory_size==176128'), 'Only latest diagnostic size correction')

        selected = p['selected_order']
        need(len(selected) == 138 and len({x['slot'] for x in selected}) == 138, 'Unique actual table cells')
        need([x['slot'] for x in selected] == sorted(x['slot'] for x in selected), 'Actual table chronology')
        need(tuple(selected[i]['entry'] for i in PHASES) == ROOTS, 'Exact seven sorted-root phases')
        need([x for x in selected if x['entry'] not in ROOTS] == old['selected_order'], 'All accepted131 relative root/slot records retained')
        page_union = read(P/'source-page-union.json')
        need(page_union['fixed_original'] == old['observed_pages'] and len(page_union['fixed_original']) == 43, 'Immutable fixed page order')
        need(page_union['whole'] == page_union['fixed_original'] + page_union['extra_original'], 'Complete explicit current page order')
        need(len(page_union['whole']) == len(set(page_union['whole'])) == 69 and len(page_union['extra_original']) == 26, '69 distinct complete pages')
        contracts = read(P/'contracts.json')
        need((contracts['inherited_FS_bytes'],contracts['inherited_FS_record_bytes'],contracts['widget_FS_bytes'],contracts['widget_FS_record_bytes'],contracts['GDI_snapshot_bytes'],contracts['FPS_snapshot_bytes']) == (1216,12,1224,16,287444,550180), 'Exact separate observer schemas')
        need(contracts['manual_owned_font_cleanup_research_only'] and not contracts['provider_preinvoked'] and not contracts['per_phase_reseed'] and not contracts['AFTER_machine_seed'], 'Finite source/input and cleanup scope')

        sys.path.insert(0,str(R/'tools/analysis'))
        pin(R/'tools/analysis/pe.py')
        from pe import PEImage
        game = PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        provider = PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        pack = pin(P/'pages.bin', p['pack_sha256']).read_bytes()
        n = struct.unpack_from('<I',pack,8)[0]
        need(pack[:8] == b'MW4J124P' and n == 161 and len(pack) == p['pack_bytes'] == 12 + n*4104, 'Whole sparse pack framing')
        pages = {}
        for i in range(n):
            base, perm = struct.unpack_from('<2I',pack,12+i*4104)
            need(base%4096 == 0 and base not in pages and perm in (0,1,2), 'Distinct declared source page')
            pages[base] = (perm,pack[20+i*4104:4116+i*4104])
        need(len(p['source_spans']) == 5040 and p['source_spans'][:len(old['source_spans'])] == old['source_spans'], 'Whole retained source span prefix')
        for span in p['source_spans']:
            image = provider if span['origin'] else game
            offset, _ = image.rva_range(span['pc']-image.image_base, span['size'])
            need(offset == span['image_offset'], 'Exact owning physical source offset')
            raw = image.data[offset:offset+span['size']]
            if span['origin'] == 0:
                need(bytes(pages[(span['pc']+i)&~4095][1][(span['pc']+i)&4095] for i in range(span['size'])) == raw, 'Complete physical instruction in sparse pack')
        for row in selected:
            offset, _ = game.rva_range(row['slot']-game.image_base,4)
            need(struct.unpack_from('<I',game.data,offset)[0] == row['entry'], 'Actual owning physical initializer slot')
        hooks = read(P/'source-hook-inventory.json')
        for i,a in enumerate(hooks['hooks']):
            for b_ in hooks['hooks'][i+1:]:
                need(a['pc']+a['bytes'] <= b_['pc'] or b_['pc']+b_['bytes'] <= a['pc'], 'Zero source patch overlap')
        need(sum(x['family']=='FS' for x in hooks['hooks']) == 93, 'All actual FS hooks retained')
        broker = text(P/'original_broker.hpp')
        match = re.search(r'array<std::uint32_t,\d+> bases\{([^}]+)\}',broker)
        need(match is not None, 'Declared sparse reservation bases')
        bases = {int(x,16) for x in match[1].split(',')}
        need(all(base >= 0x5f400000 or base&~65535 in bases for base in pages), 'Every lower sparse page has a reservation')

        # Real consumed compiler dependency evidence; it establishes source
        # identity, not byte attribution of the linked observer functions.
        deps, assembly, tlogs = set(), set(), []
        for filename, target in (('CL.read.1.tlog',deps),('Masm.read.1u.tlog',assembly)):
            matches = [x for x in (B/'build-x86').rglob(filename) if 'CompilerId' not in str(x)]
            need(len(matches) == 1, 'Exact actual compiler dependency journal')
            journal = pin(matches[0]);tlogs.append(str(journal))
            for row in journal.read_text(encoding='utf-16').splitlines():
                if row.startswith('^'):
                    row = row[1:]
                if row:
                    for part in row.split('|'):
                        target.add(str(pin(part)))
        expected_local = {str(x.resolve()).casefold() for x in P.iterdir() if x.suffix=='.asm'}
        need({x.casefold() for x in assembly} == expected_local, 'All eleven actual assembler source reads')
        need(str((P/'reference.cpp').resolve()).casefold() in {x.casefold() for x in deps}, 'Actual current primary C++ source read')
        for filename in ('widget_observer.hpp','fps_observer.hpp','protocol.hpp','spec.hpp','connected_observer.hpp'):
            need(str((P/filename).resolve()).casefold() in {x.casefold() for x in deps}, 'Actual current consumed header '+filename)
        for path in (B/'build-x86').rglob('*'):
            if path.is_file() and 'CompilerId' not in str(path) and (path.name in ('CL.command.1.tlog','CustomBuild.command.1.tlog','link.command.1.tlog') or path.suffix=='.vcxproj'):
                pin(path)

        # Explicitly distinct research cleanup seams. There is no predicate
        # demanding original/native order or hardware restoration equality.
        cleanup = 'for(unsigned i=0;i<widget_resource_count;++i)if(widget_resources[i].live)'
        c = reference.index(cleanup)
        need(reference.index('remove_CRT_hooks();registry_cleanup.restore();') < c, 'Original registry observation restoration precedes font cleanup')
        first_free = reference.index('original_free(reinterpret_cast<void*>(*crtbegin));*crtbegin=0;*crtnext=0;', reference.index('Exact108callback vector extent'))
        need(first_free < c and reference[reference.index('Exact108callback vector extent'):].count('original_free(reinterpret_cast<void*>(*crtbegin));*crtbegin=0;*crtnext=0;') == 2, 'Both actual inherited and copied NULL registry frees retained')
        counts = dict(original_roots=138, original_sequences=6, original_phases=828, callbacks=108, physical_source_spans=5040, physical_initializer_slots=138, whole_source_pages=69, fixed_Record_pages=43, external_whole_pages=26, sparse_pack_pages=161, source_patch_windows=len(hooks['hooks']), FS_hooks=93, declared_reference_hunks=len(deltas), actual_CXX_dependencies=len(deps), actual_assembler_dependencies=len(assembly), whole_reference_source_relation=True, latest_protocol_diagnostic_only=True)
        passed = True
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        pin(__file__)
        report = dict(passed=passed, scope='Independent ordinary-file original138 source recipe, physical source/table/pack and actual consumed compiler dependency review; linked observer attribution and launch admission are separate', preparation_sha256=PINS.get(str((P/'report.json').resolve())), build_sha256=PINS.get(str((B/'build.json').resolve())), counts=counts, original_manual_font_cleanup_order='ascending original WidgetResource index, after registry teardown', native_manual_font_cleanup_order='reverse native allocation generation, before Session.finish; separate source gate', original_copied_post_font_registry_free='NULL after earlier registry free; retained research-only seam', shared_original_native_cleanup_order=False, shared_original_native_cleanup_hardware=False, source_shutdown_callbacks_modeled=False, linked_observer_function_attribution=False, capture_archive_reader_opened=False, worker_launched=False, initializer_credit=0, files=PINS)
        path = out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),counts=counts)))

if __name__ == '__main__':
    main(sys.argv[1])
