"""Finite constructor preparation from physical source and authentic prefix inputs.

This does not execute a constructor, turn its static path into an observation,
or substitute captured AFTER bytes for source semantics.
"""
from pathlib import Path
from collections import deque
import hashlib, json, re, struct, sys, traceback

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-constructor-source'
STATIC = ROOT / 'reports/m4-remaining-service-source/preparation-r2'
VALIDATION = ROOT / 'reports/m4-startup131-original/validation-r2'
ROOTS = (0x4103f0, 0x410440, 0x459b40)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def need(value, message):
    if not value:
        raise ValueError(message)


def main(name):
    out = BASE / name
    need(not out.exists(), 'Fresh additive constructor preparation')
    out.mkdir(parents=True)
    files = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        need(path.suffix.lower() not in ('.mwb', '.zip'), 'Archive-free preparation')
        digest = sha(path)
        need(expected is None or digest == expected, 'Exact physical input ' + str(path))
        need(str(path) not in files or files[str(path)] == digest, 'One physical identity')
        files[str(path)] = digest
        return path

    def read(path, expected=None):
        return json.loads(pin(path, expected).read_bytes())

    def source(path, expected=None):
        return pin(path, expected).read_bytes()

    try:
        recovery = read(STATIC / 'report.json', 'e137cf7e923009c39de1ba3b6135e0e8ca5b43826f0ec993396f77bd82acc2c4')
        need(recovery['passed'], 'Exact frozen remaining-service recovery')
        graphs = read(STATIC / 'all-seven-graphs.json', recovery['files'][str((STATIC / 'all-seven-graphs.json').resolve())])
        liftpath = ROOT / 'reports/m4-remaining-service-source/lifts-r2/report.json'
        lifts = read(liftpath)
        need(lifts['passed'], 'Usable compiled corpus, not failed recursive build')
        validation = read(VALIDATION / 'report.json', '9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f')
        need(validation['passed'] and validation['reader_closed'], 'Authentic closed original131 run')
        prerequisites = read(VALIDATION / 'fresh-constructor-prerequisites.json', validation['files'][str((VALIDATION / 'fresh-constructor-prerequisites.json').resolve())])
        need(len(prerequisites) == 12, 'Six whole actual prefix input pairs')
        order = read(ROOT / 'reports/m4-startup131-original/preparation-r4/selected-order.json')
        need(len(order) == 131 and order[13]['entry'] == 0x5ae3e4, 'Current accepted relative-order prefix')

        sys.path.insert(0, str(ROOT / 'tools/analysis'))
        from pe import PEImage
        pin(ROOT / 'tools/analysis/pe.py')
        game = PEImage(source(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
        def physical(address, extent):
            off, _ = game.rva_range(address - game.image_base, extent)
            return game.data[off:off+extent]

        reached = set()
        pending = deque(ROOTS)
        missing = set()
        while pending:
            entry = pending.popleft()
            if entry in reached:
                continue
            reached.add(entry)
            if str(entry) not in graphs:
                missing.add(entry)
                continue
            pending.extend(row['target'] for row in graphs[str(entry)]['direct_calls'])
        need(not missing, 'All direct source graphs physically retained')
        # These targets are literal indirect source candidates. They still need
        # current list/vptr/register and actual CALL/RET corroboration.
        reached.update((0x40a850, 0x5733d0))
        rows = {}
        for entry in sorted(reached):
            for row in graphs[str(entry)]['instructions']:
                need(physical(row['pc'], row['size']).hex() == row['bytes'], 'Whole physical instruction')
                need(row['pc'] not in rows or rows[row['pc']] == row, 'Unique physical descriptor')
                rows[row['pc']] = row

        def whole_row(pc, mnemonic=None):
            row = rows[pc]
            need(mnemonic is None or row['mnemonic'] == mnemonic, 'Exact source operation')
            return row

        # The READONLY slots establish candidates, never live dispatch credit.
        dispatch = []
        for table, definition, root in ((0x5bcc68, 0x4c0350, 0x4103f0), (0x5cab60, 0x4c05b0, 0x410440), (0x5ca6d8, 0x4bf945, None)):
            need(physical(table + 0x18, 4) == struct.pack('<I', 0x40a850), 'Exact getter source slot')
            dispatch.append(dict(CALL_PC=0x58b183, source_vptr=table, field_offset=0x18,
                                 target=0x40a850, dominating_store_PC=definition, root=root,
                                 physical_slot_hex=physical(table+0x18,4).hex(),
                                 required_live_owner_and_vptr=True, actual_CALL_observed=False))
        dispatch.append(dict(CALL_PCs=[0x5560ec, 0x556100], held_register='EDI',
                             source_definition_PC=0x5733c0, target=0x5733d0,
                             source_owner_global=0x72c508, nonnull_route_observed=False))

        pages = read(ROOT / 'reports/m4-lockit-original/original-preparation-r4/report.json')['observed_pages']
        need(len(pages) == 43, 'Current fixed source page inventory')
        page_index = {address:index for index,address in enumerate(pages)}
        actual_inputs = []
        for sequence in range(6):
            pair = [r for r in prerequisites if r['sequence'] == sequence]
            before = next(r for r in pair if r['side'] == 'BEFORE-MFC')
            after = next(r for r in pair if r['side'] == 'AFTER-MFC')
            for key in ('metadata', 'occurrences', 'nodes', 'whole_5F2000_hex'):
                need(before[key] == after[key], 'Observed MFC leaves prefix prerequisites unchanged')
            meta = before['metadata']
            need(meta[:2] == [1, 0x603fdc] and meta[3] == 0x603fe0 and meta[5] == 0x5f2a48, 'Named actual metadata fields')
            need(struct.unpack_from('<I', bytes.fromhex(before['whole_5F2000_hex']), 0xa48)[0] == meta[6], 'Whole actual data page scalar')
            need(len(before['whole_5F2000_hex']) == 8192, 'Full data page, no scalar seed')
            phasepath = VALIDATION / f'actual-MFC-inputs/phase/{sequence}/13.bin'
            phase = source(phasepath, validation['files'][str(phasepath.resolve())])
            need(len(phase) == 356992 and struct.unpack_from('<I', phase, 16)[0] == 0x5ae3e4, 'Current untouched prefix record')
            cells = {}
            for address in (0x603fdc, 0x603fe0, 0x72c2ac, 0x72c2b0, 0x72c2c4, 0x72c2cc, 0x72c508):
                need(address & ~4095 in page_index, 'Actual fixed source page carries required cell')
                offset = 2276 + page_index[address & ~4095]*4096 + (address & 4095)
                cells[f'{address:08X}'] = dict(address=address, observed_DWORD=struct.unpack_from('<I', phase, offset)[0],
                                              phase_record_path=str(phasepath.resolve()), byte_offset=offset,
                                              scope='Actual prefix BEFORE-MFC; not constructor AFTER')
            need(cells['00603FDC']['observed_DWORD'] == meta[2] and cells['00603FE0']['observed_DWORD'] == meta[4], 'Actual page/list observation join')
            need(cells['0072C508']['observed_DWORD'] == meta[7] and cells['0072C2CC']['observed_DWORD'] == meta[8], 'Actual tree/list observation join')
            by_serial = {row[1]: row for row in before['occurrences']}
            need(len(by_serial) == len(before['occurrences']), 'Unique observed invocation occurrence IDs')
            owners = []
            for node in before['nodes']:
                values = node['meta']; occurrence = by_serial[values[4]]
                raw = bytes.fromhex(node['whole_bytes_hex'])
                need(len(raw) == values[3] == occurrence[8] and values[2] == occurrence[7] and occurrence[9] == 1, 'Complete live allocation occurrence/capacity identity')
                need(tuple(values[7:10]) == struct.unpack_from('<3I', raw), 'Whole actual current link/payload bytes')
                ordinal = occurrence[1]
                folder = 'bootstrap/'+str(sequence) if occurrence[2] == 0xffffffff else f'phase/{sequence}/{occurrence[2]}'
                base = VALIDATION / 'actual-constructor-inputs/constructor-prerequisites' / folder / f'allocation-{ordinal}'
                occurrence_path = base / 'occurrence.bin'
                initial_path = base / 'initial.bin'
                observed = source(occurrence_path, validation['files'][str(occurrence_path.resolve())])
                initial = source(initial_path, validation['files'][str(initial_path.resolve())])
                need(struct.unpack('<12I', observed) == tuple(occurrence), 'Same genuine initial allocator occurrence')
                need(len(initial) == occurrence[11] == occurrence[8], 'Complete actual initial HeapAlloc backing')
                owners.append(dict(role='carried-shared-header' if values[2] == meta[2] else 'carried-list-node',
                                   guest_address=values[2], capacity=len(raw), actual_occurrence=occurrence,
                                   initial_hex=initial.hex(), current_prefix_hex=raw.hex(), next=values[7], prev=values[8], payload=values[9],
                                   original_initial_path=str(initial_path.resolve()), occurrence_path=str(occurrence_path.resolve()),
                                   occurrence_is_OS_heap_generation=False))
            need(owners and owners[0]['guest_address'] == meta[2], 'Genuine live header, never fabricated zero-list')
            actual_inputs.append(dict(sequence=sequence, prefix_roots=13, source_frame=0x20001800,
                                      original_source_phase=13, constructor_executed=False,
                                      scalar_cells=cells, whole_5F2000_hex=before['whole_5F2000_hex'], identifier_base=meta[6],
                                      shared_list_header=meta[2], counter=meta[4], whole_live_owners=owners,
                                      typed_native_relocation_required=True, input_scope='Authentic carried prefix only'))

        allocations=[]
        for row in sorted(rows.values(), key=lambda r:r['pc']):
            if row['mnemonic'] == 'call' and row['operands'].startswith('0x5abd26'):
                allocations.append(dict(CALL_PC=row['pc'], return_PC=row['pc']+row['size'], row=row,
                                        argument_scope='Literal DWORD at MFC callee entry ESP+4; derived from current source stack',
                                        actual_new_occurrence_observed=False, full_capacity_initial_bytes_required=True,
                                        backing_role_bound_to_CALL_occurrence=True))
        free_sites=[dict(CALL_PC=row['pc'], return_PC=row['pc']+row['size'], row=row,
                         argument_scope='Literal current NULL or live owner; preserve distinct NULL admission',
                         actual_new_cleanup_observed=False) for row in sorted(rows.values(), key=lambda r:r['pc'])
                    if row['mnemonic']=='call' and row['operands'].startswith('0x5abd1a')]
        compiled=[]; reusable=[]; uncompiled=[]
        for entry in sorted(reached):
            paths=[ROOT/f'reports/m4-remaining-service-source/lifts-r2/f_{entry:x}-{level}.obj' for level in ('O0','O2')]
            if all(str(path.resolve()) in lifts['entry_objects'] for path in paths):
                compiled.append(dict(entry=entry,objects={level:dict(path=str(pin(path,lifts['entry_objects'][str(path.resolve())])),sha256=sha(path))for level,path in zip(('O0','O2'),paths)}))
            elif entry == 0x56fea0:
                uncompiled.append(dict(entry=entry, reason='Recursive physical graph deliberately retained uncompiled/unadmitted; null conditional path is not yet measured for constructors'))
            else:
                reusable.append(dict(entry=entry,accepted_provider_or_helper=True,
                                     actual_current_native_link_admission_required=True,
                                     body_is_new_original_observation=False))
        need(len(uncompiled)==1 and uncompiled[0]['entry']==0x56fea0, 'Exactly one retained recursive frontier')

        normal_contracts=dict(roots=[r for r in lifts['roots'] if r['entry'] in ROOTS],
                             source_frame=0x20001800, body_call_return_geometry='Full literal stack walk; actual source-defined RET/RETn, no CPU AFTER seed',
                             current_prefix_inputs=actual_inputs, dispatch_candidates=dispatch,
                             allocation_CALL_sites=allocations, free_CALL_sites=free_sites,
                             caller_owned_services=[
                                 dict(service='MFC ordinal823',game_trampoline=0x5abd26,IAT=0x5bb4bc,scope='Existing genuine allocator component, each new occurrence/role/capacity/initial bytes must be observed'),
                                 dict(service='MFC ordinal825',game_trampoline=0x5abd1a,IAT=0x5bb4c8,scope='Existing genuine NULL/owned free provider; exact physical owning IAT retained'),
                                 dict(service='Accepted _onexit',game_entry=0x5ac140,scope='Three distinct callbacks from literal roots, whole persistent registry growth/cleanup; shutdown callbacks unexecuted')],
                             shared_list_model=dict(header_cell=0x603fdc,counter_cell=0x603fe0,node_requested_bytes=12,
                                                    link_offsets=[0,4],object_offset=8,
                                                    insertion_function=0x58aec0,insertion_stores=[0x58af22,0x58af2c,0x58af2f,0x58af38,0x4d5116],counter_store=0x58af4a,
                                                    field_pointer_translation='Typed header/node role+offset and literal fixed game object; every other byte carries own exact prefix/initial input',
                                                    arbitrary_empty_list_seed=False),
                             vector_model=dict(element_bytes=4,object_offsets=[0xc,0x10,0x14],
                                               source_INIT=[0x58aee9,0x58aeec,0x58aeef],first_request_PC=0x58af6a,
                                               repeated_source_allocations_retained=True),
                             identifier_model=dict(base_cell=0x5f2a48,candidate_range='Literal [base,base+100) from actual whole data BEFORE, virtual getter derives occupied IDs',
                                                   minimum_helper=0x40a850,cross_root_carried_list_required=True),
                             member_list_model=dict(root=0x459b40,object=0x605ae0,header_offset=4,counter_offset=8,
                                                    header_allocator_CALL=0x58f2a2,node_allocator_CALL=0x45b80e,
                                                    required_lookup_flag=0x72c2c4,cold_recursive_entry=0x56fea0,
                                                    empty_lookup_admission='Only actual current own BEFORE flag and complete source branch can exclude cold path; prefix observation alone does not credit later chronology'),
                             current_state_policy='Own native Runtime must carry first13 source/registry outputs and locate admitted native shared-header role; original addresses are typed observations, not wholesale guest seeds',
                             new_constructor_execution_pending=True,root459B40_chronology_pending=True,
                             new_allocation_return_values_or_initial_bytes_supplied=False,source_AFTER_seed=False)
        # Pin the allocator import identities from the physical owning game cell.
        for service in normal_contracts['caller_owned_services'][:2]:
            service['physical_IAT_hex']=physical(service['IAT'],4).hex()
        fsrows=[row for row in sorted(rows.values(),key=lambda row:row['pc']) if 'fs:' in row['operands']]
        artifacts={'contracts.json':normal_contracts,'literal-bodies.json':dict(compiled=compiled,reusable=reusable,uncompiled=uncompiled,direct_graph_entries=sorted(reached)),
                   'source-instructions.json':list(sorted(rows.values(),key=lambda row:row['pc'])),
                   'FS-contracts.json':dict(rows=fsrows,whole_normal_active_frame_bytes=12,source_FS_input='Actual coherent TIB/carried predecessor; caller stack and normal observer host FS are distinct',actual_new_FS_observed=False)}
        for filename,value in artifacts.items():
            path=out/filename;path.write_text(json.dumps(value,indent=2)+'\n');pin(path)
        pin(__file__)
        report=dict(passed=True,scope='Three constructor literal/native prerequisites from physical source and genuine six-domain carried prefix; no new initializer execution/admission',
                    current_original_validation_sha256=sha(VALIDATION/'report.json'),recovery_sha256=sha(STATIC/'report.json'),lifts_sha256=sha(liftpath),
                    counts=dict(roots=3,genuine_prefix_domains=len(actual_inputs),whole_current_list_backings=sum(len(row['whole_live_owners'])for row in actual_inputs),
                                actual_prefix_initial_backings=sum(len(row['whole_live_owners'])for row in actual_inputs),
                                source_graph_entries=len(reached),source_instructions=len(rows),source_bytes=sum(row['size']for row in rows.values()),
                                usable_literal_bodies=len(compiled),usable_O0_O2_objects=2*len(compiled),reused_provider_or_helper_entries=len(reusable),
                                retained_uncompiled_recursive_frontiers=len(uncompiled),allocation_CALL_sites=len(allocations),free_CALL_sites=len(free_sites),source_FS_sites=len(fsrows)),
                    contracts_path=str((out/'contracts.json').resolve()),literal_bodies_path=str((out/'literal-bodies.json').resolve()),
                    original_constructor_executed=False,native_constructor_executed=False,archive_reader_opened=False,source_AFTER_seed=False,initializer_credit=0,files=files)
        path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(path),counts=report['counts'])))
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise


if __name__=='__main__':
    main(sys.argv[1])
