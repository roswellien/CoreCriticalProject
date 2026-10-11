"""Independent bounded source, provider, caller and refusal evidence review.

This reader never launches a worker or opens a capture archive. Source replays
remain their own gates; this review binds their exact code and source contracts,
joins every retained exported observation to its raw output, and independently
checks physical native API exports, lifetimes, hardware and retry byte domains.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PINS = {}
EXPECTED = {
    'execution': ('resource-execution-r1', 'db93c7772c518460a1f35f692ac51bf9239aa1a3d6708106f5b8cc0143bd14e4'),
    'source': ('resource-source-r1', '9195e7107ec29ef8ee6b97694b1eae9a9c18aacdfe5a8aa27e5aca4d8f88d2aa'),
    'resource': ('resource-verification-r1', '4dfcf886d6a4c6c2dd0f86a04a8d7db87056db325a9fe7987ce59a416f8e38fb'),
    'prefix': ('resource-prefixes-r2', 'd4b3d38cf1e9b0dd9f8f9d5d2ad434dfb7f9655ded3680977b0c0f4550f6bb64'),
}
NAMES = ('TlsAlloc', 'TlsSetValue', 'TlsGetValue', 'TlsFree',
         'InitializeCriticalSection', 'EnterCriticalSection',
         'LeaveCriticalSection', 'DeleteCriticalSection', 'GetACP')
ALIASES = {4: ('InitializeCriticalSection', 'RtlInitializeCriticalSection'),
           5: ('EnterCriticalSection', 'RtlEnterCriticalSection'),
           6: ('LeaveCriticalSection', 'RtlLeaveCriticalSection'),
           7: ('DeleteCriticalSection', 'RtlDeleteCriticalSection')}
REASONS = {
    1: 'Exact causal source PC/operand/direction order',
    2: 'Exact causal source PC/operand/direction order',
    3: 'Exact causal source PC/operand/direction order',
    4: 'Exact typed source TLS/borrowed CS argument',
    5: 'Real native TlsGetValue returns current owned association',
    6: 'Exact named source target/current frame',
    7: 'Exact typed source TLS/borrowed CS argument',
    8: 'Normal lock25 enter depth0', 9: 'Guest access permission denied',
    10: 'Literal provider byte14 write',
    11: 'Unobserved source branch/callback is denied',
    12: 'Exact complete physical source span admission',
}


def need(value, why):
    if not value:
        raise ValueError(why)


def eq(a, b, why):
    need(a == b, why + ' ' + str((a, b))[:500])


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def pin(path, digest=None):
    path = Path(path).resolve()
    need(path.suffix.lower() not in ('.mwb', '.zip', '.iso'), 'No archive reader')
    key = str(path)
    value = PINS.get(key)
    if value is None:
        value = sha(path)
        PINS[key] = value
    need(digest is None or value == digest, 'Exact physical identity ' + key)
    return path


def raw(path):
    return pin(path).read_bytes()


def load(path, digest=None):
    return json.loads(pin(path, digest).read_bytes())


def words(path, n, kind='Q'):
    return struct.unpack('<' + kind * n, raw(path))


def files(receipt):
    for path, digest in receipt['files'].items():
        pin(path, digest)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, pin(path))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def pack(data):
    eq(data[:8], b'M4MFCNAT', 'Complete BEFORE pack carrier')
    count = struct.unpack_from('<I', data, 8)[0]
    result, cursor = {}, 12
    for _ in range(count):
        address, size, permission = struct.unpack_from('<III', data, cursor)
        cursor += 12
        need(size and address not in result and cursor + size <= len(data), 'Bounded unique BEFORE extent')
        result[address] = (size, permission, data[cursor:cursor + size])
        cursor += size
    eq(cursor, len(data), 'All BEFORE pack bytes consumed')
    eq(count, 284, 'Complete finite BEFORE domain')
    return result


def physical_export(proof, PE):
    """Independent PE export/relocation proof, separate from executed checker."""
    path = pin(proof['actual_owner'], proof['physical_sha256'])
    data = raw(path)
    pe = PE.PEImage(data)
    nt = struct.unpack_from('<I', data, 60)[0]
    optional = nt + 24

    def at(rva, size):
        start, _ = pe.rva_range(rva, size)
        return data[start:start + size]

    def text(rva):
        start, end = pe.rva_range(rva, 1)
        stop = data.find(b'\0', start, min(end, start + 1024))
        need(stop >= start, 'Bounded physical exported name')
        return data[start:stop].decode('ascii')

    export_rva, export_size = struct.unpack_from('<II', data, optional + 112)
    _, _, _, _, _, base, nf, nn, funcs, names, ords = struct.unpack('<IIHHIIIIIII', at(export_rva, 40))
    need(nf <= 65536 and nn <= 65536, 'Finite physical export inventory')
    exports = {}
    for index in range(nn):
        name = text(struct.unpack('<I', at(names + index * 4, 4))[0])
        ordinal_index = struct.unpack('<H', at(ords + index * 2, 2))[0]
        need(ordinal_index < nf, 'Physical named ordinal is bounded')
        value = struct.unpack('<I', at(funcs + ordinal_index * 4, 4))[0]
        exports[name] = value
    kind = NAMES.index(proof['requested'])
    target, owner, rva = proof['target'], proof['owner'], proof['RVA']
    eq(target - owner, rva, 'Actual image base to named export RVA')
    matches = [name for name in ALIASES.get(kind, (NAMES[kind],)) if exports.get(name) == rva]
    eq(matches, proof['matched_exports'], 'Actual owning named export/declared Rtl alias')
    need(matches and not export_rva <= rva < export_rva + export_size, 'Actual target is executable export, not forwarder string')
    need(any(s['executable'] and s['virtual_address'] <= rva and rva + 64 <= s['virtual_address'] + s['raw_size'] for s in pe.sections), 'Whole entry64 has physical executable backing')
    entry = bytearray(at(rva, 64))
    reloc_rva, reloc_size = struct.unpack_from('<II', data, optional + 112 + 5 * 8)
    cursor, applied = 0, []
    while cursor < reloc_size:
        page, size = struct.unpack('<II', at(reloc_rva + cursor, 8))
        need(size >= 8 and size % 2 == 0 and cursor + size <= reloc_size, 'Exact complete physical relocation directory')
        for item in struct.unpack('<' + 'H' * ((size - 8) // 2), at(reloc_rva + cursor + 8, size - 8)):
            typ, offset = item >> 12, item & 4095
            address = page + offset
            width = {10: 8, 3: 4}.get(typ)
            if typ == 0:
                continue
            if width is None:
                need(not rva <= address < rva + 64, 'No unsupported affected entry relocation')
                continue
            if address < rva + 64 and rva < address + width:
                need(rva <= address and address + width <= rva + 64, 'Entire relocation operand in retained entry64')
                offset = address - rva
                value = int.from_bytes(entry[offset:offset + width], 'little')
                value = (value + owner - pe.image_base) & ((1 << (width * 8)) - 1)
                entry[offset:offset + width] = value.to_bytes(width, 'little')
                applied.append(dict(RVA=address, kind=typ, width=width))
        cursor += size
    eq(cursor, reloc_size, 'No relocation directory tail omitted')
    eq(entry.hex(), proof['entry64'], 'Whole physically relocated actual named entry64')
    eq(applied, proof['relocations'], 'Exact affected typed relocation inventory')
    identity = proof['identity_words']
    eq(identity[:4], [1, kind, target, owner], 'Actual proof provider identity')
    _, _, _, _, mbase, msize, state, protect, typ = identity
    need(state == 0x1000 and typ == 0x1000000 and mbase <= target and target + 64 <= mbase + msize, 'Actual whole observed entry has committed owning image extent')
    need((protect & 255) in (0x10, 0x20, 0x40, 0x80) and not protect & 0x100, 'Actual named entry executable and unguarded')
    need(path.parent.name.lower() == 'system32' and path.name.lower() in ('kernel32.dll', 'kernelbase.dll', 'ntdll.dll'), 'Actual AMD64 owning system image')
    return kind


def main(name):
    out = R / 'reports/m4-tree-review' / name
    need(not out.exists(), 'Fresh independent review output')
    out.mkdir()
    passed, counts, cases = False, collections.Counter(), []
    try:
        receipts = {key: load(R / 'reports/m4-mfc1168-native' / folder / 'report.json', digest) for key, (folder, digest) in EXPECTED.items()}
        for key, receipt in receipts.items():
            need(receipt['passed'] and receipt['initializer_credit'] == 0 and not receipt['capture_archive_reader_opened'], 'Bounded actual prerequisite ' + key)
            files(receipt)
        e, s, v, prefix = (receipts[key] for key in ('execution', 'source', 'resource', 'prefix'))
        for receipt in (s, v, prefix):
            eq(receipt['execution_sha256'], EXPECTED['execution'][1], 'Same actual admitted execution')
            need(receipt['all_bounded_readers_closed'] and not receipt['source_AFTER_seed'], 'Closed bounded source/observation scope')
        eq(v['source_comparison_sha256'], EXPECTED['source'][1], 'Provider gate binds current complete literal proof')
        eq(prefix['source_receipt_sha256'], EXPECTED['source'][1], 'Causal gate binds current positive literal proof')
        eq(prefix['resource_receipt_sha256'], EXPECTED['resource'][1], 'Causal gate binds exact current physical resource proof')
        pre = load(R / 'reports/m4-tree-review/mfc1168-resource-prelaunch-r4/report.json', 'd5cf84c9af936ed0aca403d9da521009b2b90c19d35567e8c844648ee44dccba')
        b = load(e['build'], e['build_sha256'])
        p = load(b['preparation'], b['preparation_sha256'])
        need(pre['passed'] and e['all_workers_terminal'] and b['passed'] and p['passed'], 'Exactly admitted compiled actual finite workers')
        eq(e['admission_review_sha256'], sha(R / 'reports/m4-tree-review/mfc1168-resource-prelaunch-r4/report.json'), 'Actual writer admission edge')
        eq(e['build_sha256'], pre['build_sha256'], 'Actual current reviewed build')
        eq(b['preparation_sha256'], pre['preparation_sha256'], 'Actual current reviewed preparation')
        files(pre)
        inputs = pack(raw(p['input_pack']))
        contracts = load(p['relocated_contracts'])
        layout = load(Path(b['preparation']).parent / 'before-layout.json')
        policy = load(p['relocation_proof'])
        eq(len(layout), 284, 'Complete current finite backing inventory')
        program = {row['pc']: row for row in contracts['instructions']}
        eq(len(program), 142, 'Complete explicit literal normal source')
        eq([row['new'] for row in policy['owners']], [0x33001000, 0x33002000, 0x33003000, 0x33004000, 0x33005000], 'Five disjoint typed borrowed roles')
        eq(len(policy['pointer_cells']), 6, 'Exact six genuine typed source pointer cells')
        source_rows = load(Path(s['execution']).parent.parent / 'resource-source-r1/source-derivations.json')
        source_index = {row['level']: row for row in source_rows}
        eq(set(source_index), {'O0', 'O2'}, 'Both actual literal source levels')
        for level, row in source_index.items():
            base = Path(s['execution']).parent / level
            eq(len(row['source_PCs']), 142, 'Complete literal normal source order')
            need(all(pc in program for pc in row['source_PCs']) and row['call_stack_empty'] and row['no_AFTER_seed'], 'Normal source/final frame scope')
            accesses = [list(x) for x in struct.iter_unpack('<IIQII', raw(base / 'accesses.bin'))]
            eq(accesses, row['source_accesses'], 'All actual ordered source operands and values')
            eq(len(accesses), 113, 'Actual normal causal operand extent')
            for block in layout:
                address, size = block['address'], block['size']
                before = raw(base / f'before/blocks/{address}.bin')
                goal = bytearray(inputs[address][2])
                if address == 0x20000000:
                    struct.pack_into('<I', goal, 0x8000, 0xfffffff0)
                eq(before, goal, 'Whole BEFORE source input plus exact actual Runtime return token')
                eq(len(raw(base / f'after/blocks/{address}.bin')), size, 'Entire source-checked backing endpoint retained')
                counts['whole_BEFORE_and_retained_after_extents'] += 1
            for owner in row['borrowed_backings']:
                before = raw(base / f'before/blocks/{owner["guest"]}.bin')
                after = raw(base / f'after/blocks/{owner["guest"]}.bin')
                eq(before.hex(), owner['initial_hex'], 'Whole retained genuine initial owner capacity')
                eq(after.hex(), owner['source_final_hex'], 'Whole source-derived final owner capacity')
                expected = bytearray(before)
                if owner['role'] == 'global-object':
                    expected[20] = 0
                    struct.pack_into('<I', expected, 4160, 0x421)
                eq(after, expected, 'Only exact source14 and1040 writes affect five borrowed capacities')
                counts['whole_borrowed_capacity_byteflows'] += 1
            eq(raw(base / 'after/State.bin').hex(), row['source_State_hex'], 'Complete3504 source-derived endpoint')
            eq(raw(base / 'after/CPU.bin'), struct.pack('<10I', *row['source_CPU']), 'Complete40 source-derived endpoint')
            eq(raw(base / 'after/FX.bin').hex(), row['source_FX_hex'], 'Complete512 source-derived endpoint')
            api = raw(base / 'APIs.bin')
            eq(len(api), 4 * 352, 'Four complete actual typed APIs')
            for index, relation in enumerate(row['source_API_relations']):
                data = api[index * 352:(index + 1) * 352]
                eq(list(struct.unpack_from('<16Q', data)), relation['words'], 'Whole actual16Q typed API witness')
                eq(list(struct.unpack_from('<10I', data, 128)), relation['before'], 'Whole typed guest entryCPU')
                eq(list(struct.unpack_from('<10I', data, 168)), relation['after'], 'Whole typed guest returnCPU')
                for key, start, stop in (('frame64', 208, 272), ('CS_before', 272, 312), ('CS_after', 312, 352)):
                    eq(data[start:stop].hex(), relation[key], 'Whole typed source frame/nativeCS relation')
                spec = contracts['normal_APIs'][index]
                w = relation['words']
                eq(w[:5], [1, index, spec['source_PC'], spec['source_target'], spec['argc']], 'Exact actual source target and order')
                if index == 0:
                    need(w[8] == w[11] and w[7] == w[12], 'Actual host TLS pointer versus explicit distinct guest thread pointer')
                if index == 2:
                    eq((w[7], w[8]), (1252, 1252), 'Actual admitted finite ACP result')
                counts['whole_typed_API_records'] += 1
            counts['actual_normal_source_rows'] += 142
            counts['actual_normal_operand_rows'] += 113
            counts['whole_source_State_CPU_FX_endpoints'] += 1

        proofdir = R / 'reports/m4-mfc1168-native/resource-verification-r1'
        proofs = load(proofdir / 'unique-physical-API-proofs.json')
        joins = load(proofdir / 'actual-provider-identity-joins.json')
        lifetimes = load(proofdir / 'lifecycle-caller-refusal-relations.json')
        prefixes = load(R / 'reports/m4-mfc1168-native/resource-prefixes-r2/causal-prefix-relations.json')
        PE = module(R / 'tools/m4-tree-review/amd64_pe.py', 'mfc_independent_physical_pe')
        proof_map = {}
        for proof in proofs:
            kind = physical_export(proof, PE)
            key = (kind, proof['actual_owner'], proof['RVA'], proof['entry64'])
            need(key not in proof_map, 'Distinct actual named physical API proof')
            proof_map[key] = proof
        eq(len(proof_map), 9, 'All nine actual owning named exports')
        counts['independent_named_export_entry64_proofs'] = 9
        lifetime_index = {(row['level'], row['mode']): row for row in lifetimes}
        prefix_index = {(row['level'], row['mode']): row for row in prefixes}
        eq(len(lifetime_index), 26, 'Every positive/refusal lifetime exported')
        eq(len(prefix_index), 24, 'Every actual refusal prefix exported')
        join_index = {(row['level'], row['mode'], row['serial']): row for row in joins}
        eq(len(join_index), 242, 'Every actual API identity joined')
        all_cases = list(e['runs'].values()) + e['controls']
        for case in all_cases:
            level, mode, base = case['level'], case['mode'], Path(case['output'])
            eq(case['exit_code'], 0, 'Actual bounded worker completed')
            for path, digest in case['outputs'].items():
                pin(path, digest)
            lifetime = lifetime_index[level, mode]
            status = words(base / 'result/status.bin', 6, 'I')
            eq(status[:5], (mode, int(bool(mode)), int(bool(mode)), 0, 0), 'Actual precise fired/poison/closed-resource output')
            eq(len(lifetime['services']), status[5], 'Whole service observation extent')
            tls, association, cs_address, depth, thread, released, deleted = None, 0, None, 0, None, False, False
            for serial, event in enumerate(lifetime['services']):
                directory = base / 'resources' / str(serial)
                call = words(directory / 'call.bin', 8)
                eq(list(call), event['words'], 'Whole actual ordered service8Q')
                eq(call[:2], (1, serial), 'Actual contiguous lifecycle serial')
                kind, a0, a1, result, tid, _ = call[2:]
                thread = tid if thread is None else thread
                eq(tid, thread, 'Every service on actual owning host thread')
                identity = words(directory / 'before-identity.bin', 9)
                eq(identity, words(directory / 'after-identity.bin', 9), 'Whole provider identity stable during service')
                eq(list(identity[:2]), [1, kind], 'Actual service to actual provider kind')
                proof_key = tuple(join_index[level, mode, serial]['proof_identity'])
                proof = proof_map[proof_key]
                eq(list(identity), proof['identity_words'], 'Complete raw native identity to physical proof')
                eq(raw(directory / 'before-path.txt').decode(), proof['actual_owner'], 'Actual physical owner path')
                eq(raw(directory / 'after-path.txt'), raw(directory / 'before-path.txt'), 'Whole owner path conserved')
                eq(raw(directory / 'before-sha256.txt').decode(), proof['physical_sha256'], 'Actual physical module SHA')
                eq(raw(directory / 'after-sha256.txt'), raw(directory / 'before-sha256.txt'), 'Whole owner SHA conserved')
                eq(raw(directory / 'before-entry64.bin').hex(), proof['entry64'], 'Whole observed entry64 to independent physical export')
                eq(raw(directory / 'before-entry64.bin'), raw(directory / 'after-entry64.bin'), 'Whole actual entry64 conserved')
                before, after = raw(directory / 'CS-before40.bin'), raw(directory / 'CS-after40.bin')
                eq((before.hex(), after.hex()), (event['CS_before_hex'], event['CS_after_hex']), 'All whole40 native CS sides')
                def cs_bytes(data):
                    eq(len(data), 40, 'Complete actual nativeCS40')
                    return struct.unpack_from('<I', data, 12)[0], struct.unpack_from('<Q', data, 16)[0]
                if kind == 0:
                    need(tls is None and result != 0xffffffff, 'Own actual successful TLS acquisition')
                    tls = result
                elif kind == 1:
                    need(a0 == tls and result == 1 and not released, 'Actual live own TLS set')
                    association = a1
                elif kind == 2:
                    need(a0 == tls and not released and result == association, 'Actual own current TLS lookup')
                elif kind == 3:
                    need(a0 == tls and not released and association == 0 and result == 1, 'Actual cleared TLS released exactly once')
                    released = True
                elif kind == 4:
                    need(cs_address is None, 'One actual native CS initialization')
                    cs_address = a0
                    eq(cs_bytes(after), (0, 0), 'Actual initialized CS unowned')
                elif kind in (5, 6):
                    need(a0 == cs_address and not deleted, 'Own live nativeCS service')
                    eq(cs_bytes(before), (depth, thread if depth else 0), 'Actual recursion and thread before service')
                    depth += 1 if kind == 5 else -1
                    need(depth in (0, 1), 'Actual finite lock association')
                    eq(cs_bytes(after), (depth, thread if depth else 0), 'Actual recursion and thread after service')
                elif kind == 7:
                    need(a0 == cs_address and depth == 0 and not deleted, 'Actual unheld own CS deletion')
                    deleted = True
                elif kind == 8:
                    need(result == 1252 and depth == 1 and not deleted, 'Actual finite ACP query under owned lock')
                counts['raw_provider_identity_sides'] += 2
                counts['whole_native_CS40_sides'] += 2
            need(tls is not None and cs_address is not None and released and deleted and depth == 0, 'Complete actual owned resource cleanup')
            hardware = raw(base / 'host-hardware.bin')
            eq(len(hardware), 1632, 'Whole actual hardware boundary artifact')
            eq(hardware[:512], hardware[1088:1600], 'Whole actual outside caller FX512')
            eq(hardware[512:540], hardware[1600:1628], 'Whole actual outside caller ENV28')
            need(lifetime['caller_full_FX512_ENV28_equal'] and lifetime['caller_boundary'] == 'Runtime.invoke plus same-session retry and owned resource cleanup; construction outside boundary', 'Exact measured hardware boundary timing')
            counts['whole_caller_FX512_ENV28_pairs'] += 1
            counts['complete_owned_resource_lifetimes'] += 1
            refusal = raw(base / 'result/refusal.txt').decode()
            eq(refusal, lifetime['refusal'], 'Actual first refusal exported exactly')
            if mode:
                eq(refusal, 'memory_access site=0x005ae3e4 target=0x005ae3e4: Admitted native callback failed: ' + REASONS[mode], 'Actual precise refusal reason')
                before, after = base / 'retry/before', base / 'retry/after'
                names = {str(path.relative_to(before)) for path in before.rglob('*') if path.is_file()}
                eq(names, {str(path.relative_to(after)) for path in after.rglob('*') if path.is_file()}, 'Complete retry file domains')
                eq(names, set(lifetime['retry_complete_files']), 'Entire observed retry inventory exported')
                eq(len(names), 296, 'All284backings and12complete private machine/resource/route files')
                for item in names:
                    eq(raw(before / item), raw(after / item), 'Whole same poisoned session retry bytes ' + item)
                    counts['whole_retry_byte_file_pairs'] += 1
                causal = prefix_index[level, mode]
                accesses = [list(x) for x in struct.iter_unpack('<IIQII', raw(base / 'accesses.bin'))]
                eq(accesses, causal['accepted_source_operands'], 'Entire actual accepted/attempted refusal operand ledger')
                expected = source_index[level]['source_accesses'][:len(accesses)]
                if mode == 10:
                    expected = list(expected)
                    expected[-1] = [0x5ae3b7, 0x33005014, 1, 1, 1]
                    eq(raw(before / 'blocks/855658496.bin')[20], inputs[0x33005000][2][20], 'Recorded wrong final write never committed')
                eq(accesses, expected, 'Whole actual normal source prefix with only declared attempted write')
                eq(causal['resource_context'], list(words(before / 'resource-context.bin', 12)), 'Whole actual fault context12Q')
                if mode in (1, 2):
                    need('rejected operand payload not captured' in causal['mutation']['scope'], 'Local wrong read payload remains unobserved')
                counts['actual_causal_prefix_operand_rows'] += len(accesses)
                counts['whole_poisoned_session_retries'] += 1
                counts['actual_precise_refusal_reasons'] += 1
            else:
                eq(refusal, '', 'Actual positive source closure has no refusal')
                eq([event['words'][2] for event in lifetime['services']], [0, 2, 1, 4, 2, 5, 8, 6, 2, 1, 2, 3, 7], 'Full normal native resource chronology')
            cases.append(dict(level=level, mode=mode, service_calls=status[5], whole_caller_equal=True, resources_closed=True, first_reason=refusal))

        source_tool = raw(R / 'tools/m4-mfc1168-native/compare_fixture.py').decode()
        wrapper = raw(R / 'tools/m4-mfc1168-native/compare_resource_source.py').decode()
        interpreter = raw(R / 'tools/m4-crt-locale-batch-model-review/interpreter_v2.py').decode()
        need('m=Literal(before_state,before_fx,before_cpu,memory,program=program,callbacks={})' in source_tool, 'Explicit normal literal program seeded solely by actual BEFORE')
        need("contracts=read(prep['relocated_contracts']);pin(parent)" in wrapper, 'Only exact current typed source relocation override')
        need('self.memory={p:bytearray(b) for p,b in memory.items()' in interpreter, 'Source model owns copies; initial exported capacities remain genuine BEFORE')
        need('if program is None:program,callbacks=source_program()' in interpreter, 'Inherited default source inventory path not consumed with explicit program')
        need("m.api_return(spec['source_PC'],spec['argc'],w[7],transports)" in source_tool and "eq(m.cpu_now(),a['after']" in source_tool, 'Finite semantic API results and guestCS12 transport; complete native returnCPU is target')
        need('if self.cursor==0x780014b4:' in source_tool and "self.call_stack[-1][0]==0x5f40107d" in source_tool, 'Narrow genuine imported EH inner return frame without dropping outer frame')
        need("eq(bytes(m.state),raw(p/'after/State.bin')" in source_tool and "m.bytes(address,row['size']),raw(p/f'after/blocks/{address}.bin')" in source_tool, 'AFTER full machine and extents are comparison targets')
        causal_tool = raw(R / 'tools/m4-mfc1168-native/verify_resource_prefixes.py').decode()
        causal_adapter = raw(R / 'tools/m4-mfc1168-native/verify_resource_prefixes_v2.py').decode()
        need('except Stop:stop=True;m.cursor=m.word(2472)' in causal_adapter, 'Exact committed State PC, not decoder diagnostic cursor after failed access')
        need('m=Literal(initial,fx,cpu,memory,program=program,callbacks={},hook=hook)' in causal_tool and 'except Stop:stop=True' in causal_tool, 'Causal prefixes independently modeled from positive own BEFORE and stop before uncommitted access')
        need("if mode==3:m.word(2472,m.cursor+1);m.cursor+=1" in causal_tool and "if mode==10:prefix[-1]" in causal_tool, 'Exact finite State cursor mutation and separate final attempted byte')
        fixture = raw(R / 'tools/m4-mfc1168-native/fixture_resource_v3.cpp').decode()
        need('if(CS.RecursionCount)mf_LeaveCriticalSection(&CS)' in fixture, 'Failed cleanup owns actual native recursion, not corrupted private depth')
        need(fixture.index('Context c(r,blocks)') < fixture.index('mfc_hardware_call(&r,hardware.data())'), 'Resource construction explicitly outside measured invocation boundary')
        need('c.checkpoint("retry/before");private_dump("retry/before")' in fixture and 'c.checkpoint("retry/after");private_dump("retry/after")' in fixture, 'Same actual poisoned Runtime re-invocation and full private retry snapshots')
        need('rejected=f.reason()==FaultReason::poisoned' in fixture and 'c.cleanup_failed();' in fixture, 'Actual poisoned retry denied before full owned cleanup')
        for tool in ('verify_resource_fixture.py', 'run_resource_fixture.py', 'resource_witness.hpp'):
            pin(R / 'tools/m4-mfc1168-native' / tool)
        counts['source_refusal_whole_State_CPU_FX_derivations_reviewed'] = prefix['counts']['whole_source_refusal_State_CPU_FX_joins']
        counts['source_refusal_whole_memory_derivations_reviewed'] = prefix['counts']['whole_source_refusal_memory_endpoints']
        eq(dict(s['counts']), dict(BEFORE_only_block_joins=568, complete_typed_API_CPU_frame_joins=8, whole_State3504_CPU40_FX512_endpoint_joins=2, whole_declared_memory_endpoint_joins=568, ordered_literal_operand_joins=226, source_FS_install_restore_rows=4), 'Exact measured source gate extent')
        eq(counts['raw_provider_identity_sides'], v['counts']['actual_provider_identity_sides'], 'Exact actual provider identity extent')
        eq(counts['whole_retry_byte_file_pairs'], 7104, 'Exact complete current retry byte extent')
        eq(counts['actual_causal_prefix_operand_rows'], 908, 'Exact measured current accepted/attempted prefix extent')
        pin(__file__)
        pin(sys.executable)
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(passed=passed, scope='Independent bounded physical/script/raw-output review of admitted cached MFC1168 root at O0/O2, complete source contracts and borrowed capacities, actual named AMD64 resource exports/lifetimes, invocation-retry-cleanup caller restoration and precise finite refusals. Source replay credit remains in its separately pinned gates.',
            execution_sha256=EXPECTED['execution'][1], source_sha256=EXPECTED['source'][1], resource_sha256=EXPECTED['resource'][1], causal_prefix_sha256=EXPECTED['prefix'][1],
            counts=dict(counts), files=PINS, initializer_credit=0, connected130_alias_and_lifecycle_credit=0,
            original_API_volatile_equality_credit=0, unobserved_cold_or_lazy_source_credit=0,
            modes1_2_rejected_read_payload_observed=False, resource_construction_caller_restoration_credit=0,
            caller_boundary='Actual Runtime.invoke, poisoned-session retry, and owned TLS/nativeCS cleanup; construction excluded',
            whole_caller_FX512_ENV28=True, archive_reader_opened=False, worker_launched=False,
            source_AFTER_seed=False, all_bounded_readers_closed=True)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, path=str(out / 'report.json'), sha256=sha(out / 'report.json'), files=len(PINS), counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1])
