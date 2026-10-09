"""Independent read-only verification of the finite selected54 paired policy.

No worker is executed, no capture is produced, and no admitted source or
observation is modified. Archive bytes are checked directly, without invoking
the author's paired comparator. The separately reviewed literal insertion CFG
helper is reused only for the bounded consumer inventory.
"""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import re
import struct
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}
PAGES = (0x5c8000, 0x5c9000, 0x5cb000, 0x5cc000, 0x5e0000,
         0x5e1000, 0x5e8000, 0x604000, 0x605000, 0x60b000,
         0x20001000, 0x5bb000, 0x780c1000, 0x78115000, 0x5e6000,
         0x608000, 0x482000, 0x5ca000, 0x5ed000, 0x5f4000,
         0x603000, 0x606000, 0x609000, 0x638000, 0x63c000,
         0x63d000, 0x72c000, 0x730000, 0x9a1000)
IATS = {
    0x5bb4fc: (0x780c10f0, 0x1df59c, 'MSVCP50.dll', '?max@?$numeric_limits@M@std@@SAMXZ'),
    0x5bb52c: (0x78004a36, 0x1decb0, 'MSVCRT.dll', '_onexit'),
    0x5bb530: (0x78002fe5, 0x1deca2, 'MSVCRT.dll', '__dllonexit'),
    0x5bb6dc: (None, 0x1df20c, 'USER32.dll', 'SystemParametersInfoA'),
}
GATES = {
    'reports/m4-onexit-source/paired-initialization-policy-r3/report.json':
        '29153950456a890bc306a5d4c1aff2f5b0d3c1e9165dcb34ea2cbeee5f99b83a',
    'reports/m4-onexit-source/connected-native-source-r2/report.json':
        'c2f439bb528cdd8b660908909b835fed638bfc0190ba55cfd1cc89ee7e997188',
    'reports/m4-onexit-source/original-run-r5/report.json':
        'dbf50bb8d64645565b7b1f7ff6a622eae4257cb8fae5a188a06cb329b907143a',
    'reports/m4-joint-startup54-root/execution-r6/report.json':
        '796ed2ea41261b9949b6b1a12d963ce53d4d83bf4b0158c7f15559e3f4a9bafb',
    'reports/m4-onexit-source/field-analysis-r1/report.json':
        'bd127e908fe3056a986f3977e35e86bd1084086fb92a5e997bc36c49bdd9dfa0',
    'reports/m4-onexit-source/original-preparation-r8/report.json':
        'a70e53ed7b8867e514afc7342728cf549b740bd7d04de4b3a30657dd9f415476',
}


def need(value, why):
    if not value:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pin(path, expected=None):
    path = Path(path).resolve()
    key = str(path)
    if key not in PINS:
        PINS[key] = sha(path)
    need(expected is None or PINS[key] == expected, 'Frozen dependency ' + key)
    return path


def read(path, expected=None):
    return json.loads(pin(path, expected).read_bytes())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, pin(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def words(data, offset=0, count=1):
    return struct.unpack_from('<' + str(count) + 'I', data, offset)


def differences(a, b):
    need(len(a) == len(b), 'Equal observation extents')
    return [dict(offset=i, original=x, native=y)
            for i, (x, y) in enumerate(zip(a, b)) if x != y]


def insertion_aliases(function):
    """Finite literal CFG, including this aliases spilled to local stack slots.

    Derived from the other reviewer's stopped conservative helper, with LEA
    handled as address calculation rather than a read of its old destination.
    Any LEA using a precise object alias is rejected; this method only performs
    buffer/count calculations there. Unknown pointer domains remain unknown.
    """
    rows = {row['pc']: row for row in function['instructions']}
    work = [(function['entry'], 0, frozenset({'ECX'}), frozenset())]
    seen, members, calls, reached = set(), set(), set(), set()

    def location(text, sp, registers):
        match = re.search(r'\[([A-Z]+)(?: \+ (?:0x([0-9a-f]+)|-0x([0-9a-f]+)))?\]', text)
        if not match:
            return None
        base, positive, negative = match.groups()
        offset = int(positive or negative or '0', 16) * (-1 if negative else 1)
        if base == 'ESP':
            return 'stack', sp + offset
        if base in registers:
            return 'object', offset
        return 'unknown', offset

    while work:
        pc, sp, registers, slots = work.pop()
        key = (pc, sp, registers, slots)
        if key in seen:
            continue
        seen.add(key)
        need(pc in rows and len(seen) < 20000, 'Complete finite insertion CFG')
        reached.add(pc)
        row = rows[pc]
        operation, _, operand_text = row['text'].partition(' ')
        parts = operand_text.split(',')
        following = pc + len(bytes.fromhex(row['bytes_hex']))
        registers, slots = set(registers), set(slots)
        if operation != 'LEA':
            for part in parts:
                address = location(part, sp, registers)
                if address and address[0] == 'object':
                    need(address[1] in (4, 8, 12), 'Only this-object members +4/+8/+12 accessed')
                    members.add((pc, address[1]))
        if operation == 'MOV':
            destination, source = parts
            address = location(source, sp, registers)
            alias = source in registers or (address and address[0] == 'stack' and address[1] in slots)
            if destination in ('EAX', 'ECX', 'EDX', 'EBX', 'ESI', 'EDI', 'EBP'):
                registers.discard(destination)
                if alias:
                    registers.add(destination)
            else:
                address = location(destination, sp, registers)
                if address and address[0] == 'stack':
                    slots.discard(address[1])
                    if alias:
                        slots.add(address[1])
                else:
                    need(not alias, 'Precise this-object alias does not escape insertion method')
        elif operation == 'LEA':
            destination, source = parts
            need(not (set(re.findall(r'\b(?:EAX|ECX|EDX|EBX|ESI|EDI|EBP)\b', source)) & registers),
                 'No derived object address through unreviewed LEA')
            registers.discard(destination)
        elif operation == 'PUSH':
            address = location(parts[0], sp, registers)
            alias = parts[0] in registers or (address and address[0] == 'stack' and address[1] in slots)
            sp -= 4
            slots.discard(sp)
            if alias:
                slots.add(sp)
        elif operation == 'POP':
            registers.discard(parts[0])
            if sp in slots:
                registers.add(parts[0])
            slots.discard(sp)
            sp += 4
        elif operation in ('SUB', 'ADD') and parts[0] == 'ESP':
            sp += (1 if operation == 'ADD' else -1) * int(parts[1], 16)
        elif operation == 'CALL':
            target = int(parts[0], 16)
            need(target in (0x5abd26, 0x5abd1a) and sp not in slots,
                 'Only new/delete called without this alias as argument')
            calls.add((pc, target))
            registers.difference_update(('EAX', 'ECX', 'EDX'))
        elif operation not in ('CMP', 'TEST', 'RET', 'JMP') and not operation.startswith('J'):
            need(parts[0] not in registers, 'No unreviewed arithmetic on precise object alias')
        if operation == 'RET':
            continue
        if operation.startswith('J'):
            work.append((int(parts[0], 16), sp, frozenset(registers), frozenset(slots)))
            if operation == 'JMP':
                continue
        work.append((following, sp, frozenset(registers), frozenset(slots)))
    need(reached == set(rows), 'All physical insertion instructions covered by conservative CFG')
    return dict(CFG_states=len(seen), physical_instructions=len(rows),
                object_member_accesses=sorted(members), external_calls=sorted(calls),
                object_byte0_accesses=0, derived_object_LEA_allowed=False)


def input_provenance(preparation, pe, counts):
    base = ROOT / 'reports/m4-onexit-source/original-preparation-r8'
    old = ROOT / 'reports/m4-onexit-source/original-preparation-r7'
    current = pin(base / 'pages.bin', preparation['pack_sha256']).read_bytes()
    parent = read(old / 'report.json', preparation['parent_sha256'])
    previous = pin(old / 'pages.bin', parent['pack_sha256']).read_bytes()
    need(current[:12] == previous[:12] and current[:8] == b'MW4J54P1',
         'Same original page-pack shape')
    n = words(current, 8)[0]
    need(len(current) == len(previous) == 12 + n * 4104, 'Exact original pack extent')
    changed = []
    provenance = []
    for i in range(n):
        start = 12 + i * 4104
        address, permission = words(current, start, 2)
        need(current[start:start + 8] == previous[start:start + 8],
             'No page address or permission changed')
        new = current[start + 8:start + 4104]
        old_page = previous[start + 8:start + 4104]
        if new != old_page:
            changed.append(address)
        if address in preparation['observed_pages'][17:]:
            literal = bytearray(4096)
            raw_bytes = 0
            for section in pe.sections:
                source = pe.image_base + section['virtual_address']
                lo = max(address, source)
                hi = min(address + 4096, source + section['raw_size'])
                if lo < hi:
                    file_offset = section['raw_offset'] + lo - source
                    literal[lo - address:hi - address] = pe.data[file_offset:file_offset + hi - lo]
                    raw_bytes += hi - lo
            need(bytes(literal) == new, 'Each added observed page equals raw PE plus zero fill')
            provenance.append(dict(address=address, raw_bytes=raw_bytes,
                                   zero_fill_bytes=4096 - raw_bytes, sha256=hashlib.sha256(new).hexdigest()))
            counts['raw_PE_input_pages'] += 1
    need(changed == [0x5f4000], 'Exactly one corrected raw/BSS input page')
    for name in ('protocol.hpp', 'original_broker.hpp', 'reference_x86.asm',
                 'reference.cpp', 'preserve_x86.asm', 'CMakeLists.txt'):
        need(pin(base / name).read_bytes() == pin(old / name).read_bytes(),
             'Literal original sources unchanged: ' + name)
        counts['unchanged_original_source_files'] += 1
    return dict(changed_page_addresses=changed, added_page_provenance=provenance,
                derived_from_literal_PE=True, game_AFTER_used=False)


def static_consumers(pe, field, counts):
    static = read(ROOT / 'reports/m4-onexit-source/field-reference-r2/export.json')
    need(static['target_sha256'] == sha(ROOT / 'MW3/Mech3.exe'), 'Persisted export target identity')
    functions = {function['entry']: function for function in static['exports']}
    for function in functions.values():
        for row in function['instructions']:
            code = bytes.fromhex(row['bytes_hex'])
            offset, _ = pe.rva_range(row['pc'] - pe.image_base, len(code))
            need(pe.data[offset:offset + len(code)] == code, 'Literal consumer instruction bytes')
            counts['literal_consumer_instruction_checks'] += 1
    offset, _ = pe.rva_range(0x49d5d0 - pe.image_base, 10)
    need(pe.data[offset:offset + 10] == bytes.fromhex('518a442403a2e8996000'),
         'Literal PUSH ECX / MOV AL,[ESP+3] / byte store')
    references = [r for r in static['references'] if r['to'] == 0x6099e8]
    need({r['from'] for r in references} == {0x49d454, 0x49d487, 0x49d546, 0x49d5d5},
         'Four bounded direct-address references')
    hits = []
    cursor = 0
    while (cursor := pe.data.find(struct.pack('<I', 0x6099e8), cursor)) >= 0:
        section = next(s for s in pe.sections if s['raw_offset'] <= cursor < s['raw_offset'] + s['raw_size'])
        hits.append(pe.image_base + section['virtual_address'] + cursor - section['raw_offset'] - 1)
        cursor += 1
    need(set(hits) == {r['from'] for r in references}, 'Whole-file literal DWORD inventory agrees')
    for address in (0x6099e9, 0x6099ea, 0x6099eb):
        need(struct.pack('<I', address) not in pe.data, 'No literal padding-byte address')
    pin(ROOT / 'tools/m4-onexit-review/review_paired_policy.py')
    alias = insertion_aliases(functions[0x49da10])
    need(alias['physical_instructions'] == 225 and len(alias['object_member_accesses']) == 18
         and alias['object_byte0_accesses'] == 0, 'Bounded insertion CFG alias proof')
    no_op = functions[0x40baf0]['instructions']
    need(len(no_op) == 1 and no_op[0]['bytes_hex'] == 'c20800', 'Literal erasure helper reads no object')
    detail = read(ROOT / 'reports/m4-onexit-source/field-analysis-r1/field.json')
    cleanup = bytes.fromhex(detail['cleanup']['bytes_hex'])
    offset, _ = pe.rva_range(0x49d600 - pe.image_base, len(cleanup))
    need(pe.data[offset:offset + len(cleanup)] == cleanup and
         struct.pack('<I', 0x6099e8) not in cleanup, 'Literal cleanup lacks byte0 access')
    need(field['passed'] and not field['whole_game_liveness_proven'], 'Static liveness scope remains bounded')
    return dict(insertion_alias_CFG=alias, direct_reference_count=len(references),
                whole_file_literal_address_inventory=True,
                exact_source_language_type_known=False,
                incoming_ECX_copy_observed=True, uninitialized_allocator_intent_proven=False,
                whole_game_dynamic_alias_proof=False)


def main(name):
    out = ROOT / 'reports/m4-paired-policy-review' / name
    need(not out.exists(), 'Fresh independent review receipt')
    out.mkdir(parents=True)
    passed = False
    counts = collections.Counter()
    derivations = []
    inventory = collections.Counter()
    findings = []
    try:
        gate = {path: read(ROOT / path, digest) for path, digest in GATES.items()}
        for report in gate.values():
            need(report['passed'] is True, 'Required exact source gate passed')
            for path, digest in report.get('files', {}).items():
                pin(path, digest)
        paired = gate['reports/m4-onexit-source/paired-initialization-policy-r3/report.json']
        need(not paired['blanket_page_mask'] and not paired['original_and_native_bytes_modified']
             and not paired['whole_game_liveness_proven'], 'Honest finite relation scope')
        persistent = gate['reports/m4-onexit-source/connected-native-source-r2/report.json']
        need(persistent['counts']['persistent_phases'] == 648 and
             persistent['counts']['whole_page_BEFORE'] == persistent['counts']['whole_page_AFTER'] == 18792 and
             not persistent['per_phase_BEFORE_machine_seed'] and not persistent['candidate_AFTER_machine_seed'],
             'Separate persistent native full-machine source gate')
        # Preserve the prior genuine volatile-consumer counterexample, even
        # though this finite data relation now accounts for that byte explicitly.
        counterexample = read(ROOT / 'reports/m4-onexit-review/liveness-review-r1/report.json',
                              '6ed6bcb4cb55c6c1d4497a2ea560041b5cdf8b6e405276eb34be6fec73efa945')
        need(counterexample['inspection_passed'] and not counterexample['previous_liveness_scope_admissible'],
             'Discarded no-consumer claim is not resurrected')
        pin(ROOT / 'reports/m4-onexit-review/liveness-native-supplement-r1/report.json',
            '0851d0d8cb05c36f87aacfc3fa7794d9174c43c3c91b84301a9f217209b83e2c')
        PE = load('independent_policy_PE', ROOT / 'tools/analysis/pe.py')
        pe = PE.PEImage(pin(ROOT / 'MW3/Mech3.exe',
                            '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        imports = {pe.image_base + s['iat_rva']: (library['library'].lower(), s['name'])
                   for library in pe.imports() for s in library['symbols'] if 'name' in s}
        for address, (_, raw, library, symbol) in IATS.items():
            need(imports[address] == (library.lower(), symbol), 'Typed literal owning-IAT identity')
            offset, _ = pe.rva_range(address - pe.image_base, 4)
            need(words(pe.data, offset)[0] == raw, 'Exact raw PE thunk identity')
            counts['typed_owning_IAT_imports'] += 1
        provenance = input_provenance(gate['reports/m4-onexit-source/original-preparation-r8/report.json'], pe, counts)
        consumer = static_consumers(pe, gate['reports/m4-onexit-source/field-analysis-r1/report.json'], counts)
        order = read(ROOT / 'reports/m4-onexit-source/interface-r1/instruction-contracts.json',
                     '3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3')['selected_order']
        roots = {r['entry']: r['registration']['callback'] for r in read(
            ROOT / 'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json',
            '88979fcc7494e8ada7821bc4b2f804f7194ca43f3265621b86a50fb32ffe84fc')}
        need(len(order) == 54 and len(roots) == 26 and order[25]['entry'] == 0x482cf0
             and order[26]['entry'] == 0x49d5c0, 'Actual finite SPI/constructor seam association')
        observations = read(ROOT / 'reports/m4-onexit-source/paired-initialization-policy-r3/paired-observations.json')
        saved = {(r['level'], r['sequence'], r['phase']): r for r in observations}
        need(len(saved) == len(observations) == 648, 'All phase observations are distinct')
        D = load('independent_policy_direct_archive', ROOT / 'tools/m4-crt-allocation-root/run_v2.py')
        original_report = gate['reports/m4-onexit-source/original-run-r5/report.json']
        original = D.DirectSet(Path(original_report['original_capture']), pin)
        try:
            for level in ('O0', 'O2'):
                native = D.DirectSet(ROOT / f'reports/m4-joint-startup54-root/execution-r6/{level}/transport.json', pin)
                try:
                    for sequence in range(6):
                        callbacks = []
                        field_values = None
                        for phase, item in enumerate(order):
                            a = original.data(f'phase/{sequence}/{phase}.bin')
                            b = native.data(f'sequence-{sequence}/phase-{phase}.bin')
                            need(len(a) == 242304 and len(b) == 159716, 'Exact phase record extents')
                            need(a[:32] == b[:32] and words(a, 0, 5)[::2] ==
                                 (sequence, phase, item['entry']), 'Genuine paired phase association')
                            saved_phase = saved[(level, sequence, phase)]
                            need(saved_phase['entry'] == item['entry'], 'Saved phase entry agrees')
                            for side, co, fo, eo, original_memory, native_memory in (
                                ('before', 36, 116, 2164, 2276, 2276),
                                ('after', 76, 628, 2192, 121060, 71908)):
                                ca, cb = words(a, co, 10), words(b, co, 10)
                                for index in (0, 3, 4, 5, 6, 7, 9):
                                    need(ca[index] == cb[index], 'EAX/nonvolatile/SP/PC equality')
                                    counts['exact_CPU_field_checks'] += 1
                                if phase != (25 if side == 'after' else 26):
                                    need(ca[1] == cb[1] and ca[8] == cb[8], 'ECX/EFLAGS outside exact SPI seam')
                                    counts['additional_CPU_field_checks'] += 2
                                need(differences(a[co:co + 40], b[co:co + 40]) ==
                                     saved_phase['CPU_' + side + '_differences'], 'Retained raw CPU inventory')
                                original_fx, native_fx = a[fo:fo + 512], b[fo:fo + 512]
                                # Stronger than the source helper: metadata
                                # bytes 6..23 must equal physically, not merely
                                # become equal when projected to zero.
                                need(original_fx[:28] == native_fx[:28] and original_fx[32:] == native_fx[32:],
                                     'Raw FX equality everywhere outside exact capability-mask DWORD')
                                need(words(original_fx, 28)[0] == 0x2ffff and words(native_fx, 28)[0] == 0,
                                     'Exact physical versus software MXCSR_MASK representation')
                                fx_delta = differences(original_fx, native_fx)
                                need(fx_delta == saved_phase['FX_' + side + '_differences'], 'Retained raw FX inventory')
                                for difference in fx_delta:
                                    inventory['FX_difference_offset_' + str(difference['offset'])] += 1
                                counts['raw_FX_except_capability_mask_checks'] += 1
                                counts['whole_hardware_FX_projection_checks'] += 1
                                original_env, native_env = a[eo:eo + 28], b[eo:eo + 28]
                                need(original_env.hex() == saved_phase['ENV_' + side + '_original_hex'] and
                                     native_env.hex() == saved_phase['ENV_' + side + '_native_hex'], 'Retained raw ENV inventory')
                                need(original_env[:12] == native_env[:12], 'Exact x87 control/status/tag head')
                                counts['exact_x87_environment_head_checks'] += 1
                                if phase not in ((25, 26, 27) if side == 'after' else (26, 27, 28)):
                                    need(original_env == native_env, 'Complete ENV outside finite SPI metadata interval')
                                    counts['whole_ENV_checks'] += 1
                                if original_env != native_env:
                                    inventory['finite_SPI_ENV_' + side + '_phase_' + str(phase)] += 1
                                pages_saved = {r['page']: r for r in saved_phase['nonstack_pages'] if r['side'] == side}
                                need(len(pages_saved) == 28, 'Entire nonstack observation inventory')
                                for index, page in enumerate(PAGES):
                                    x = a[original_memory + index * 4096:original_memory + (index + 1) * 4096]
                                    y = b[native_memory + index * 4096:native_memory + (index + 1) * 4096] if index < 17 else native.data(
                                        f'sequence-{sequence}/phase-{phase}-{side}-page-{page}.bin')
                                    need(len(x) == len(y) == 4096, 'Whole physical page extents')
                                    if page == 0x20001000:
                                        continue
                                    allowed = set()
                                    if page == 0x5bb000:
                                        for address, (target, raw, _, _) in IATS.items():
                                            offset = address & 4095
                                            need(words(y, offset)[0] == raw and
                                                 (words(x, offset)[0] == target if target is not None else
                                                  words(x, offset)[0] not in (0, raw)), 'Actual typed IAT pointer representations')
                                            allowed.update(range(offset, offset + 4))
                                            counts['owning_IAT_identity_checks'] += 1
                                    if page == 0x609000:
                                        offset = 0x9e8
                                        if phase == 26 and side == 'before':
                                            spi = original.data(f'phase/{sequence}/25.bin')
                                            need(words(spi, 80)[0] == ca[1], 'Actual original SPI output carries to constructor ECX')
                                            field_values = (ca[1] >> 24, cb[1] >> 24)
                                        if phase == 26 and side == 'after':
                                            need((x[offset], y[offset]) == field_values, 'Literal own-BEFORE high-byte store')
                                            derivations.append(dict(level=level, sequence=sequence,
                                                original_BEFORE_ECX=words(a, 40)[0], native_BEFORE_ECX=words(b, 40)[0],
                                                original_derived=field_values[0], native_derived=field_values[1],
                                                original_actual=x[offset], native_actual=y[offset]))
                                            counts['own_branch_field_derivations'] += 2
                                        if phase > 26 or (phase == 26 and side == 'after'):
                                            need((x[offset], y[offset]) == field_values, 'Exact raw own-branch high-byte carry')
                                            allowed.add(offset)
                                            counts['indeterminate_field_carry_checks'] += 2
                                    changed = differences(x, y)
                                    need(all(d['offset'] in allowed for d in changed), 'No additional byte projection or page mask')
                                    page_saved = pages_saved[page]
                                    need(page_saved['differences'] == changed and
                                         page_saved['original_sha256'] == hashlib.sha256(x).hexdigest() and
                                         page_saved['native_sha256'] == hashlib.sha256(y).hexdigest(), 'Whole retained page inventory matches actual bytes')
                                    counts['whole_nonstack_page_relations'] += 1
                                    for difference in changed:
                                        inventory['page_' + hex(page) + '_offset_' + hex(difference['offset'])] += 1
                            if item['entry'] in roots:
                                callbacks.append(roots[item['entry']])
                                need(words(a, 76)[0] == words(b, 76)[0] == 0, 'Exact atexit wrapper success return')
                                need(words(a, 241792, len(callbacks)) == tuple(callbacks), 'Actual original ordered callback vector')
                                summary = struct.unpack('<32Q', native.data(
                                    f'sequence-{sequence}/phase-{phase}-after-registry.bin'))
                                need(summary[9] == len(callbacks) and summary[7] - summary[6] == 4 * len(callbacks)
                                     and summary[8] >= 4 * len(callbacks), 'Native owned vector count and extent')
                                counts['registration_return_order_checks'] += 1
                            counts['paired_phases'] += 1
                        need(len(callbacks) == 26 and original.data(f'cleanup/{sequence}/registry.bin') ==
                             struct.pack('<26I', *callbacks), 'All 26 actual original registrations carried')
                        counts['paired54_sequences'] += 1
                finally:
                    native.close()
        finally:
            original.close()
        for key, value in paired['counts'].items():
            need(counts[key] == value, 'Independent count matches source receipt: ' + key)
        findings = [
            'All 36,288 whole nonstack page relations admit only four typed owning-IAT DWORDs and one own-BEFORE-derived byte after its literal store.',
            'PUSH ECX writes the actual incoming register into the local slot. Its high-byte copy is observed, while an uninitialized allocator/dummy source-language interpretation remains unproved.',
            'The frozen hardwarefx helper zeroes metadata bytes 6..23 as well as importing MXCSR_MASK; direct raw checking establishes that metadata is already equal zero in both current branches. Only raw FX offsets 28..30 differ.',
            'Raw EDX is retained but excluded from cross-ABI equality throughout. ECX/EFLAGS equality is excluded only at the SPI return and immediate next input; x87 ENV metadata exclusion is limited to three carried phases.',
            'Persistent native source modeling is a separate gate and uses admitted finite old floating-point scalar/raw80/status oracles with checked source operands; this receipt does not claim an independent general FP implementation.',
            'Original API scratch-stack equality, broader nonzero FSQRT, exact whole original/native machine equality, and whole-game indirect byte liveness remain outside admission.',
        ]
        pin(__file__)
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise
    finally:
        for filename, value in (('field-derivations.json', derivations),
                                ('difference-inventory.json', dict(inventory)),
                                ('findings.json', findings)):
            (out / filename).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
            pin(out / filename)
        report = dict(
            passed=passed,
            scope='Independent finite selected54 initialization data/numeric relation, checked directly against unchanged genuine original and O0/O2 native archives',
            counts=dict(counts),
            corrected_original_input_provenance=locals().get('provenance'),
            bounded_field_consumer_review=locals().get('consumer'),
            raw_bytes_modified=False, blanket_page_mask=False,
            paired_comparator_executed=False, builds_or_captures_performed=False,
            whole_original_native_machine_equality=False,
            full_original_scratch_stack_equivalence=False,
            whole_game_dynamic_alias_liveness=False,
            field_values_hardcoded=False,
            actual_branch_field_values=sorted({(r['original_actual'], r['native_actual']) for r in derivations}),
            policy_acceptance_recommendation=(
                'Admit only the named finite selected-initialization relation, conditional on the separate strict native provider/ownership and fault-control gates. Do not claim raw byte identity, full CRT, native game launch, or whole-game byte liveness.'),
            concrete_unresolved_gaps_within_declared_scope=[],
            semantic_wording_correction='The local is physically initialized by PUSH ECX; the opaque source-language allocator intent is inferred only.',
            initializer_credit=0, whole_M4_complete=False, files=PINS)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        pin(out / 'report.json')
        (out / 'pins.json').write_text(json.dumps(dict(files=PINS), indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(passed=passed, report=str(out / 'report.json'),
                              report_sha256=sha(out / 'report.json'), counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1])
