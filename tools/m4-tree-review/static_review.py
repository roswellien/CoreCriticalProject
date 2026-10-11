"""Independent bounded physical tree closure and admission design review.

This reads PE/static JSON only. It grants no execution or initializer credit.
"""
from __future__ import annotations
from collections import Counter, deque
import hashlib, importlib.util, json, re, struct, sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
GAME_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
ACCEPTANCE_SHA = '6bd35e55bca15e1a0537044bf59a1c3ced5e9ef8b30a8a169b71c78824811462'


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def need(v, reason):
    if not v:
        raise ValueError(reason)


def main(name):
    out = ROOT/'reports/m4-tree-review'/name
    need(not out.exists(), 'Fresh additive review revision required')
    out.mkdir(parents=True)
    pins, counts = {}, Counter()

    def pin(p, expected=None):
        p = Path(p).resolve(); actual = sha(p)
        need(expected is None or expected == actual, 'Exact review input ' + str(p))
        need(str(p) not in pins or pins[str(p)] == actual, 'Immutable review input')
        pins[str(p)] = actual
        return p

    def read(p, expected=None):
        return json.loads(pin(p, expected).read_bytes())

    def emit(n, value):
        p = out/n
        p.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
        pin(p)

    accepted = read(ROOT/'reports/m4-joint-startup124-root/acceptance-r1/report.json', ACCEPTANCE_SHA)
    need(accepted['passed'], 'Accepted124 baseline remains passed')
    physical = ROOT/'reports/m4-lockit-source/complex-plan-r1'
    plan = read(physical/'execution-plan.json', 'a972f30e1c707bf6645ff608313b581395a62b347c3cb0c9c8e91d02ba19ec24')
    graphs = read(physical/'game-normal-graphs.json', '9c85ae7f569f07129c5fd11f5fb39eebe73c5e0c6b10a7cba11133928c3416d3')
    contracts = read(ROOT/'reports/m4-lockit-source/complex-next-plan-r1/contracts.json', '0dcf91ac338a85e6b907805f394f8b11a6854d598874f803146e9fb2e3595cfb')
    for directory in (physical, ROOT/'reports/m4-lockit-source/complex-next-plan-r1'):
        receipt = read(directory/'report.json')
        need(receipt['passed'], 'Passed static planning input')
        for p, h in receipt['files'].items():
            pin(p, h)
    pe_path = pin(ROOT/'tools/analysis/pe.py', 'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
    spec = importlib.util.spec_from_file_location('independent_tree_pe', pe_path)
    pe_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(pe_module)
    game = pe_module.PEImage(pin(ROOT/'MW3/Mech3.exe', GAME_SHA).read_bytes())
    need(game.image_base == 0x400000, 'Exact preferred game base')
    rows = {}
    for graph in graphs.values():
        for row in graph['instructions']:
            code = bytes.fromhex(row['bytes'])
            need(len(code) == row['size'] and 0 < len(code) <= 15, 'Physical instruction length')
            offset, _ = game.rva_range(row['pc']-game.image_base, len(code))
            need(game.read(offset, len(code)) == code, 'Physical game instruction ' + hex(row['pc']))
            need(row['pc'] not in rows or rows[row['pc']] == row, 'Overlapping literal row equality')
            rows[row['pc']] = row
    need(len(rows) == 613 and sum(r['size'] for r in rows.values()) == 1894, 'Complete static closure extent')
    counts.update(physical_source_rows=613, physical_source_bytes=1894, declared_new_minimal_entries=7,
                  declared_new_conservative_entries=8, reused_entries=4, syntactic_allocation_sites=3,
                  syntactic_Lockit_calls=17, syntactic_register_import_calls=9, syntactic_FS_frames=4)

    def branch(row):
        b = bytes.fromhex(row['bytes'])
        if len(b) == 5 and b[0] in (0xE8, 0xE9): d = int.from_bytes(b[1:], 'little', signed=True)
        elif len(b) == 2 and (b[0] == 0xEB or 0x70 <= b[0] <= 0x7F): d = int.from_bytes(b[1:], 'little', signed=True)
        elif len(b) == 6 and b[0] == 0x0F and 0x80 <= b[1] <= 0x8F: d = int.from_bytes(b[2:], 'little', signed=True)
        else: raise ValueError('Unsupported direct branch ' + hex(row['pc']))
        target = (row['pc']+len(b)+d) & 0xFFFFFFFF
        printed = re.match(r'^0x([0-9a-f]+)', row['operands'])
        need(printed and int(printed[1], 16) == target, 'Physical relative branch target')
        return target

    def edges(row):
        m, o = row['mnemonic'], row['operands']; nxt = row['pc']+row['size']
        if m == 'ret': return []
        if m == 'call': return [nxt]
        if m == 'jmp': return [branch(row)] if o.startswith('0x') else []
        if m.startswith('j'): return [branch(row), nxt]
        return [nxt]

    independent_edges = {}
    for pc, row in rows.items():
        independent_edges[pc] = edges(row)
        if (row['mnemonic'] in ('call', 'jmp') or row['mnemonic'].startswith('j')) and row['operands'].startswith('0x'):
            branch(row); counts['physical_relative_controls'] += 1
    for graph in graphs.values():
        todo, seen = deque([graph['entry']]), set()
        while todo:
            pc = todo.popleft()
            if pc in seen: continue
            need(pc in rows, 'Complete independent local source walk')
            seen.add(pc); todo.extend(independent_edges[pc])
        need(seen == {r['pc'] for r in graph['instructions']}, 'Declared graph equals independent physical control walk')
        counts['physical_local_graphs'] += 1
    off, _ = game.rva_range(0x5E0168-game.image_base, 4)
    need(struct.unpack('<I', game.read(off, 4))[0] == 0x4B7F70, 'Exact initializer slot')
    need(rows[0x4B7F90]['bytes'] == '68a07f4b00' and branch(rows[0x4B7F95]) == 0x5AC140,
         'Literal one callback4B7FA0 registration')
    for site, push in ((0x4BA306, 0x4BA304), (0x4BA33C, 0x4BA32D), (0x4BAB32, 0x4BAB2C)):
        need(branch(rows[site]) == 0x5ABD26 and rows[push]['bytes'] == '6a18', 'Actual syntactic request24')

    # Independently transport LEA ESP-affine value along the exact short physical
    # path, including CALL's committed return push. This is a static constraint,
    # not proof that an original/native run actually reached the LEA.
    affine = []
    for call in contracts['Lockit_scratch_contracts']:
        derived = []
        for lea in call['source_LEA_pcs']:
            row = rows[lea]
            match = re.fullmatch(r'ecx, \[esp \+ 0x([0-9a-f]+)\]', row['operands'])
            need(row['mnemonic'] == 'lea' and match, 'Exact ESP-derived ECX LEA')
            ecx, sp = int(match[1], 16), 0
            pc, path = lea+row['size'], [lea]
            while pc != call['CALL_pc']:
                need(len(path) < 32 and pc not in path, 'Short finite LEA-to-CALL path')
                r = rows[pc]; path.append(pc); m, o = r['mnemonic'], r['operands']
                need(m not in ('call','ret') and not (m.startswith('j') and m != 'jmp'), 'No unknown callee or ambiguous branch after LEA')
                need(not (o.startswith('ecx,') and m not in ('cmp','test')), 'No intervening scratch ECX definition')
                if m == 'push': sp -= 4
                elif m == 'pop':
                    need(o != 'esp', 'No nonlinear popESP'); sp += 4
                elif m in ('add','sub') and o.startswith('esp, '):
                    amount = int(o.split(', ')[1], 0); sp += amount if m == 'add' else -amount
                else:
                    need(not (o.startswith('esp,') and m not in ('cmp','test')), 'No nonlinear ESP mutation')
                nxt = edges(r); need(len(nxt) == 1, 'Unique physical affine path'); pc = nxt[0]
            need(rows[pc]['mnemonic'] == 'call', 'Affine endpoint is literal CALL')
            offset = ecx-(sp-4)
            derived.append(offset)
            affine.append(dict(CALL_pc=pc, LEA_pc=lea, path=path+[pc], ECX_minus_target_ESP=offset,
                               actual_branch_reached=False))
        need(sorted(set(derived)) == sorted(call['ECX_minus_target_entry_ESP']), 'Independent affine offsets equal source plan')
    need(len(affine) == 20, 'Seventeen calls with shared endpoint four origins')
    counts['independent_affine_LEA_paths'] = len(affine)

    # Exact normal shared endpoint proof, obtainable with existing memory hooks.
    expected = {0x4BADC7:'8938', 0x4BADC9:'894704', 0x4BADCC:'8d4c2414', 0x4BADD0:'ff15f4b45b00'}
    for pc, code in expected.items(): need(rows[pc]['bytes'] == code, 'Exact branch suffix physical bytes')
    incoming = {pc:[] for pc in rows}
    for pc, destinations in independent_edges.items():
        for d in destinations:
            if d in incoming: incoming[d].append(pc)
    need(incoming[0x4BADC9] == [0x4BADC7] and incoming[0x4BADCC] == [0x4BADC9], 'Unambiguous terminal write then LEA')
    need(sorted(incoming[0x4BADD0]) == [0x4BACC1,0x4BACDB,0x4BACEC,0x4BADCC], 'Distinct four actual dtor incoming edges')
    # Constructor -> normal endpoint has no post-return stack change and no
    # nested CALL. Its branches only choose ordinary source parent-edge writes.
    todo, rotation = deque([0x4BAD91]), set()
    while todo:
        pc = todo.popleft()
        if pc == 0x4BADD0 or pc in rotation: continue
        r = rows[pc]; rotation.add(pc)
        need(r['mnemonic'] not in ('call','ret','push','pop','leave') and
             not (r['operands'].startswith('esp,') and r['mnemonic'] not in ('cmp','test')),
             'Outer-left rotation preserves caller ESP after ctor RET')
        todo.extend(independent_edges[pc])
    need(0x4BADC7 in rotation and 0x4BADC9 in rotation and 0x4BADCC in rotation and
         not ({0x4BACBD,0x4BACD7,0x4BACE8} & rotation), 'Normal rotation only reaches +24 origin')
    shared = dict(CALL_pc=0x4BADD0, admitted_LEA_pc=0x4BADCC, ECX_minus_target_ESP=24,
                  constructor_CALL_pc=0x4BAD8F, constructor_LEA_pc=0x4BAD7E,
                  same_live_scratch_and_caller_invocation_required=True,
                  required_called_ledger_suffix=[dict(pc=0x4BADC7,write=True,width=4),
                                                dict(pc=0x4BADC9,write=True,width=4),
                                                dict(pc=0x4BADD0,address=0x5BB4F4,write=False,width=4,raw=0x1DF568),
                                                dict(pc=0x4BADD0,address='actual target frame',write=True,width=4,value=0x4BADD6)],
                  read_time_suffix_omits_uncommitted_CALL_push=True,
                  corresponding_owner_addresses_values_required=True,
                  other_static_origins=[0x4BACBD,0x4BACD7,0x4BACE8],
                  other_static_offset=60, those_origins_admitted=False,
                  intervening_normal_rotation_rows=sorted(rotation),
                  actual_execution_verified=False)

    imports = plan['register_import_calls']
    need(len(imports) == 9, 'Nine actual syntactic register calls')
    for imp in imports:
        r, d = rows[imp['pc']], rows[imp['definition_PC']]
        need(r == imp['source_call'] and d == imp['source_definition'], 'Physical register import source rows')
        need(r['mnemonic'] == 'call' and r['operands'] == imp['register'] and
             d['mnemonic'] == 'mov' and d['operands'] == f"{imp['register']}, dword ptr [0x{imp['IAT']:x}]",
             'Register load/call relation')
        # Nonvolatile preservation is separately enforced on each real CALL/RET;
        # do not treat this source relation as its runtime proof.
    fs = []
    for frame in contracts['FS_frames']:
        entry = frame['entry']; a,b,r = rows[entry], rows[entry+2], rows[frame['read']]
        need(a['bytes'] == '6aff' and b['bytes'] == '68'+struct.pack('<I',frame['handler']).hex(), 'Exact -1/handler PUSH prefix')
        need(r['bytes'] == '64a100000000' and frame['read_entry_ESP_bias'] == 8, 'FS read after exactly two PUSHes')
        need(rows[frame['install']]['bytes'] == '64892500000000' and rows[frame['restore']]['mnemonic'] == 'mov', 'Complete actual source FS install/restore')
        ret = rows[frame['RET_pc']]
        cleanup = int(ret['operands'], 0) if ret['operands'] else 0
        need(ret['mnemonic'] == 'ret' and cleanup == frame['RET_cleanup'], 'Physical RET cleanup')
        fs.append(dict(entry=entry, handler=frame['handler'], read=frame['read'], install=frame['install'],
                       saved_previous=frame['saved_previous'], restore=frame['restore'], RET_pc=frame['RET_pc'],
                       cleanup=cleanup, record_bytes=12, identity='actual caller frame plus monotonically assigned invocation',
                       invocation_count_observed=False))

    baseline_ops = pin(ROOT/'reports/m4-lockit-native/preparation-r5/locale_batch_operations.inc')
    need('live_allocations()>80' in baseline_ops.read_text(), 'Accepted124 actual eighty-owner safety bound')
    design = dict(root=0x4B7F70, slot=0x5E0168, accepted_base=124, proposed_after_gates=125,
                  minimal_new_entries=contracts['minimal_fixed_normal_dispatch'],
                  predecessor_entry_4BAE30_exclusion_requires_actual_reached_trace=True,
                  repeated_site=0x4BAB32, declared_request=24, actual_count_known=False,
                  owner_identity=['root','allocation CALLpc','per-site invocation','guest pointer','native pointer','generation'],
                  allocation_primary_publication={'header':0x4BA315,'sentinel':0x4BA347,'node':[0x4BAB9C,0x4BABAC]},
                  owner_access_resolution='actual live unique containing owner, requested-size offset/width; never first(root,site)',
                  primary_publication_resolution='actual value owner generation; once per allocation; ordinary rotation writes not primary publications',
                  entire_actual_capacity_and_tails_required=True, raw_guest_pointer_pairing_allowed=False,
                  scratch_identity=['caller invocation','actual frame','scratch address','constructor source site','private generation','active LIFO lifetime'],
                  imports_require_actual_definition_and_all_intervening_nonvolatile_RET_proofs=True,
                  borrowed_field_16_source_pointers_only=True, source_stack_bytes_0_1_independent_provenance_required=True,
                  expected_ordinary_owner_count_static_only=85, accepted_bound=80,
                  new_finite_bound_must_be_at_least_measured_peak=True,
                  registry_growth_499_API_and_one_replay_constants_reusable=False,
                  callback_execution_allowed=False, loaded_state2_native_resource_reused=True,
                  fixed_CPU_after=[76,116], fixed_FX_before=[116,628], State_bytes=3504, CPU_bytes=40, FX_bytes=512,
                  pages_must_be_freshly_measured=True, expected_existing_pages_static_only=43)
    negatives = [
        ('repeated-owner-first-match','At fourth/fifth repeated node source access, substitute an earlier live node from the same CALLpc; require actual generation/key/link refusal.'),
        ('stale-generation','Alter selected node generation/publication privately, restoring actual native resource before teardown; refuse before write or API.'),
        ('foreign-parent','Replace a parent/child pointer with a foreign or dead allocation; refuse the first exact requested owner access.'),
        ('requested-extent','Attempt DWORD offset24 of a24B tree owner even if actual rounded capacity is32; refuse before memory operation.'),
        ('duplicate-primary-publication','Replay a primary edge for the same owner; refuse, while retaining ordinary legitimate rotation updates.'),
        ('scratch-other-branch','At shared4BADD0 set ECX to frame+60 or alter terminal write origin; refuse because normal4BADCC/+24 is source-bound.'),
        ('scratch-other-invocation','Use scratch from an earlier recursive search/insertion invocation at an otherwise valid site; refuse active LIFO identity mismatch.'),
        ('raw-IAT','Change raw5BB4F8/F4 before the corresponding source read; refuse without native Enter/Leave.'),
        ('retained-register-import','After the genuine4BAB1A load and intervening allocation RET, alter EBP at a register CALL; refuse exact retained definition target.'),
        ('source-FS-invocation','Substitute prior4BAB00 frame or scope/handler/previous head from another invocation; refuse complete12B relation.'),
        ('loaded-provider-state','Alter source state78145658 or opaque loaded guestCS bytes; refuse before API.'),
        ('native-resource-depth-thread','Alter actual native40 RecursionCount or owner thread under a held resource; refuse; restore before cleanup.'),
        ('whole-capacity-tail','Alter an untouched allocation tail byte or full current guest/native backing; refuse owner carry conservation.'),
        ('private-ledger','Alter retained owner/publication/scratch/import witness data through an observer; refuse private witness integrity.'),
        ('readonly-owner','Make a soon-to-be-written owner page readonly; refuse committed write, preserve failure state and retry evidence.'),
        ('hardware-FX','Alter a protected hardware FP/environment field at an observer; refuse according to existing strict host conservation scope.'),
    ]
    emit('physical-affine-paths.json', affine)
    emit('shared-dtor-normal-proof.json', shared)
    emit('FS-invocation-contracts.json', fs)
    emit('finite-admission-design.json', design)
    emit('negative-control-catalog.json', [dict(id=k, requirement=v, actual_native_execution=False) for k,v in negatives])
    counts.update(shared_normal_suffix_memory_rows=4, independent_FS_prefixes=4, planned_negative_controls=len(negatives))
    pin(__file__)
    report = dict(passed=True, scope='Independent physical static closure, branch-specific scratch proof and future control requirements; no source/native execution credit',
                  accepted_base=124, proposed_root=0x4B7F70, initializer_credit=0,
                  actual_owner_count_known=False, actual_path_measured=False, control_execution_passed=False,
                  current_acceptance_modified=False, full_capture_reader_opened=False,
                  counts=dict(counts), files=pins)
    emit('report.json', report)
    print(json.dumps(dict(passed=True, sha256=sha(out/'report.json'), counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1])
