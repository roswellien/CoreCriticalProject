"""Finite cached1168 relations between two independently derived branches.

The current original observations remain whole observations. Native snapshots
are literal proof snapshots, not intermediate hardware observations. The five
borrowed roles, seven imports, the precise FS predecessor chain, and one CMP's
pointer-parity bit are typed explicitly; no arbitrary memory/register mask is
introduced. Every other opaque input difference must be unconsumed and carried
exactly in its own branch until a literal write defines that byte.
"""
import collections
import hashlib
import struct

ROOT = 0x5ae3e4
PHASE = 13
ROLES = ('manager-array', 'thread', 'thread-array', 'thread-object', 'global-object')
PCS = (0x5f401083, 0x5ae3ad, 0x5ae3b7, 0x5ae3ba, 0x5ae3c0, 0x78003ddb, 0x5ae3ca)
IMPORT_ACCESSES = {5: 0, 15: 3, 27: 2, 60: 1, 74: 4, 86: 5, 97: 6}
ROLE_VALUES = {18: 'thread-array', 19: 'thread-object', 45: 'global-object', 46: 'global-object'}
FS_VALUES = {30, 31, 47, 50}
CS_VALUES = {71, 72, 73, 95, 96}
FLAG_BITS = {'CF': 0, 'PF': 2, 'AF': 4, 'ZF': 6, 'SF': 7, 'DF': 10, 'OF': 11}

def need(value, label):
    if not value:
        raise ValueError(label)

def eq(a, b, label):
    need(a == b, label + ' ' + str((a, b))[:700])

def u32(raw, offset=0):
    return struct.unpack_from('<I', raw, offset)[0]

def cpu(raw):
    return list(struct.unpack('<10I', raw))

def locate(memory, address, width):
    rows = [(a, b) for a, b in memory.items() if a <= address and address + width <= a + len(b)]
    eq(len(rows), 1, 'One exact complete source backing for an endpoint/access')
    return rows[0]

def get(memory, address, width):
    base, raw = locate(memory, address, width)
    return bytes(raw[address - base:address - base + width])

def write(memory, address, raw):
    base, backing = locate(memory, address, len(raw))
    backing[address - base:address - base + len(raw)] = raw

def role_address(address, width, owners, teb):
    for owner in owners:
        base = owner['address']
        if base <= address and address + width <= base + owner['extent']:
            return ('borrowed', owner['role'], address - base)
    if address == teb and width == 4:
        return ('source-FS', 0)
    return ('fixed', address)

def diffs(a, b):
    eq(len(a), len(b), 'Complete same-role extents')
    return [dict(offset=i, original=x, native=y) for i, (x, y) in enumerate(zip(a, b)) if x != y]

def reconstruct(initial, accesses, semantic_writes=()):
    result = {a: bytearray(b) for a, b in initial.items()}
    # Only phase region writes are replayed here. Source stack/code remain
    # independently proven by the two complete literal source gates.
    for pc, address, value, width, writing in accesses:
        if writing and any(a <= address and address + width <= a + len(b) for a, b in result.items()):
            write(result, address, int(value).to_bytes(width, 'little'))
    # Only the CS24's final semantic words require API writes; no subsequent
    # literal instruction reads CS24 internals, and Enter/Leave are balanced.
    for address, raw in semantic_writes:
        write(result, address, raw)
    return result

def own_byteflow(owner, accesses):
    initial = bytes.fromhex(owner['initial_hex'])
    final = bytes.fromhex(owner['source_final_hex'])
    eq(len(initial), owner['extent'], 'Whole genuine borrowed capacity input')
    eq(len(final), len(initial), 'Whole derived borrowed capacity output')
    result = bytearray(initial)
    reads = set()
    writes = set()
    rows = []
    for i, (pc, address, value, width, writing) in enumerate(accesses):
        if owner['address'] <= address < owner['address'] + owner['extent']:
            offset = address - owner['address']
            need(offset + width <= owner['extent'], 'Every borrowed operand stays within its genuine capacity')
            raw = int(value).to_bytes(width, 'little')
            if writing:
                result[offset:offset + width] = raw
                writes.update(range(offset, offset + width))
            else:
                eq(bytes(result[offset:offset + width]), raw, 'Exact own initial/store preimage of every borrowed read')
                reads.update(range(offset, offset + width))
            rows.append(dict(index=i, PC=pc, offset=offset, value=value, width=width, write=bool(writing)))
    eq(bytes(result), final, 'Complete borrowed backing is initial bytes plus literal writes')
    return initial, final, reads, writes, rows

def compare(original, actual, native, inputs, original_capture, native_capture, hardwarefx):
    counts = collections.Counter()
    eq((original['root'], original['phase'], native['root'], native['phase']), (ROOT, PHASE, ROOT, PHASE), 'Both exact current MFC roots')
    need(not original['source_AFTER_seed'] and original['actual_prefix_carried_BEFORE'] and not native['source_AFTER_seed'], 'Both phase effects derived without AFTER inputs')
    eq(original['sequence'], native['sequence'], 'Same genuine CW/TOP sequence')
    eq(original['source_PCs'], native['source_PCs'], 'All142 physical source PCs in exact order')
    eq(len(original['source_PCs']), 142, 'Finite cached path only')
    a_access = original['source_accesses']; b_access = native['source_accesses']
    eq(len(a_access), 113, 'All113 original operands'); eq(len(b_access), 113, 'All113 native operands')
    a_owners = original['source_borrowed_backings']
    b_owners = [dict(role=r['role'], address=r['new'], extent=r['extent'], initial_hex=r['initial_hex'], source_final_hex=r['source_final_hex']) for r in native['source_borrowed_backings']]
    eq([r['role'] for r in a_owners], list(ROLES), 'Exact original borrowed roles')
    eq([r['role'] for r in b_owners], list(ROLES), 'Exact native borrowed roles')
    a_by = {r['role']: r for r in a_owners}; b_by = {r['role']: r for r in b_owners}
    a_lock = actual['domains']['BEFORE']['lock25_metadata'][1]
    a_head = original['source_FS_BEFORE']
    before = native['source_computed_BEFORE']
    b_memory = {int(a): bytearray.fromhex(b) for a, b in before['memory'].items()}
    layout = native.get('TIB_region_representation', [])
    eq(len(layout), 1, 'One exact declared TIB representation adapter')
    adapter = layout[0]
    eq((adapter['address'], adapter['literal_extent']), (0x7ffde004, 8), 'Only source TIB004/008 may join')
    eq([(r['address'], r['bytes']) for r in adapter['original_parts']], [(0x7ffde004, 4), (0x7ffde008, 4)], 'Exact persistent four-byte parts')
    need(adapter['persistent_original_layout_restored'], 'Source restores original persistent region inventory')
    parts = []
    for part in adapter['original_parts']:
        raw = bytes(b_memory[part['address']])
        eq((len(raw), raw.hex()), (4, part['BEFORE_hex']), 'Each complete independent carried BEFORE part')
        parts.append(raw)
    joined = b''.join(parts)
    eq(joined.hex(), adapter['joined_BEFORE_hex'], 'Eight-byte literal input joins only computed BEFORE')
    b_memory[0x7ffde004] = bytearray(joined)
    del b_memory[0x7ffde008]
    b_head = u32(get(b_memory, 0x7ffde000, 4))
    projections = native['source_import_projections']
    eq(len(projections), 7, 'Exactly seven named owning import projections')
    imports = {r['access_index']: r for r in projections}
    eq(set(imports), set(IMPORT_ACCESSES), 'All and only fixed literal import operands')
    operand_rows = []
    for index, (a, b) in enumerate(zip(a_access, b_access)):
        eq((a[0], a[3], a[4]), (b[0], b[3], b[4]), 'Literal operand PC/width/direction/order')
        eq(role_address(a[1], a[3], a_owners, original['source_TEB']), role_address(b[1], b[3], b_owners, 0x7ffde000), 'Exact same-role source operand address')
        relation = 'exact scalar/source stack byte'
        if index in IMPORT_ACCESSES:
            projection = imports[index]; spec = inputs['imports'][IMPORT_ACCESSES[index]]
            eq((a[0], a[1], b[1], b[2]), (projection['PC'], projection['cell'], projection['cell'], projection['projected']), 'Actual owning source import operand')
            eq((projection['raw'], projection['projected']), (spec['raw'], spec['projected']), 'Physical raw/named native import contract')
            if IMPORT_ACCESSES[index] < 3:
                eq(a[2], b[2], 'Exact same physical game/CRT/MFC target')
            else:
                api = IMPORT_ACCESSES[index] - 3
                eq(a[2], original['source_API_relations'][api]['entry_CPU'][9], 'Actual original named API entry target')
                eq(b[2], native['source_API_relations'][api]['target'], 'Independent native named API source target')
            relation = 'exact named owning import'
        elif index in ROLE_VALUES:
            role = ROLE_VALUES[index]
            eq((a[2], b[2]), (a_by[role]['address'], b_by[role]['address']), 'Exact current borrowed role pointer value')
            relation = 'borrowed role pointer ' + role
        elif index in FS_VALUES:
            eq((a[2], b[2]), (a_head, b_head), 'Exact source-carried outer FS predecessor')
            relation = 'own coherent source FS predecessor'
        elif index in CS_VALUES:
            eq((a[2], b[2]), (a_lock, inputs['guest_CS']), 'Exact same semantic initialized lock25 argument')
            relation = 'same declared lock25 resource'
        else:
            eq(a[2], b[2], 'All other source operand scalar/stack values are exact')
        operand_rows.append(dict(index=index, original=a, native=b, relation=relation))
    counts['paired_MFC_source_PC_occurrences'] += 142
    counts['paired_MFC_ordered_operand_relations'] += 113
    owner_rows = []
    pointer_bytes = {'thread': set(range(12, 16)), 'thread-array': set(range(4, 8))}
    for a, b in zip(a_owners, b_owners):
        eq(a['extent'], b['extent'], 'Same-role measured full capacity')
        ai, af, ar, aw, ax = own_byteflow(a, a_access)
        bi, bf, br, bw, bx = own_byteflow(b, b_access)
        eq([(r['PC'], r['offset'], r['width'], r['write']) for r in ax], [(r['PC'], r['offset'], r['width'], r['write']) for r in bx], 'All same-role literal reads/writes')
        eq(aw, bw, 'Exact same initialized byte domain')
        if aw:
            eq(bytes(af[i] for i in sorted(aw)), bytes(bf[i] for i in sorted(bw)), 'Every source-written borrowed scalar byte is exact')
        initial_differences = diffs(ai, bi)
        typed = pointer_bytes.get(a['role'], set())
        for row in initial_differences:
            i = row['offset']
            if i in typed:
                continue
            need(i not in ar and i not in br, 'Every other opaque differing input byte is never source-read')
            if i not in aw:
                eq((af[i], bf[i]), (ai[i], bi[i]), 'Every untouched opaque difference carries exactly in each branch')
        stem = f'sequence-{native["sequence"]}/MFC/'
        eq(native_capture.data(stem + f'before/memory/{b["address"]}.bin'), bi, 'Whole actual native borrowed BEFORE equals independent input')
        eq(native_capture.data(stem + f'after/memory/{b["address"]}.bin'), bf, 'Whole actual native borrowed AFTER equals independent literal effect')
        owner_rows.append(dict(role=a['role'], original=a, native=b, initial_differences=initial_differences, original_accesses=ax, native_accesses=bx, untouched_opaque_difference_bytes=[r['offset'] for r in initial_differences if r['offset'] not in typed and r['offset'] not in aw]))
        counts['paired_MFC_whole_borrowed_role_byteflows'] += 1
        counts['paired_MFC_whole_borrowed_endpoint_pairs'] += 2
    stem = f'sequence-{native["sequence"]}/MFC/'
    for filename, raw in [('State.bin', bytes.fromhex(before['State_hex'])), ('CPU.bin', bytes.fromhex(before['CPU_hex'])), ('FX.bin', bytes.fromhex(before['FX_hex']))]:
        eq(native_capture.data(stem+'before/'+filename), raw, 'Whole native equality target joins persistent independently computed BEFORE')
    for filename, raw in [('State.bin', bytes.fromhex(native['source_State_hex'])), ('CPU.bin', struct.pack('<10I', *native['source_CPU'])), ('FX.bin', bytes.fromhex(native['source_FX_hex']))]:
        eq(native_capture.data(stem+'after/'+filename), raw, 'Whole native equality target joins independently derived AFTER')
    regions = native['whole_regions']
    eq(len(regions), 12, 'All twelve declared region endpoints')
    region_memory = {a: bytearray(get(b_memory, a, size)) for a, size, _ in regions}
    semantic = [(a, bytes.fromhex(raw)) for api in native['source_API_relations'] for a, raw in api['guest_semantic_writes']]
    region_final = reconstruct(region_memory, b_access, semantic)
    region_rows = []
    for address, size, access in regions:
        a = bytes(region_memory[address]); b = bytes(region_final[address])
        eq(native_capture.data(stem+f'before/memory/{address}.bin'), a, 'Every complete declared native BEFORE region')
        eq(native_capture.data(stem+f'after/memory/{address}.bin'), b, 'Every complete declared native AFTER region from source writes')
        region_rows.append(dict(address=address, bytes=size, access=access, initial_hex=a.hex(), source_final_hex=b.hex()))
        counts['paired_MFC_whole_region_endpoint_relations'] += 2
    derived_tib = get(region_final, 0x7ffde004, 8)
    eq(derived_tib.hex(), adapter['source_AFTER_joined_hex'], 'Whole derived TIB endpoint joins source layout witness')
    eq([(r['address'], r['bytes'], r['source_AFTER_hex']) for r in adapter['source_AFTER_parts']], [(0x7ffde004, 4, derived_tib[:4].hex()), (0x7ffde008, 4, derived_tib[4:].hex())], 'Exact inverse persistent projection of the independently derived endpoint')
    native_fs = native['source_FS_writes']; original_fs = original['source_FS_writes']
    eq(len(native_fs), 2, 'Native source EH install/restore writes'); eq(len(original_fs), 2, 'Original source EH install/restore writes')
    eq([r[0] for r in native_fs], [r[0] for r in original_fs], 'Exact source EH write PCs')
    eq(u32(get(region_final, 0x7ffde000, 4)), b_head, 'Native literal FS restores its own predecessor')
    eq(original['source_FS_AFTER'], a_head, 'Original literal FS restores actual coherent root predecessor')
    counts['paired_MFC_source_FS_install_restore_relations'] += 2
    boundary_rows = []
    eq(len(native['source_normal_boundaries']), 7, 'All seven independent native literal snapshots')
    for index, (a, observed, b) in enumerate(zip(original['source_normal_boundary_relations'], actual['boundaries'], native['source_normal_boundaries'])):
        eq((a['index'], a['PC'], b['PC'], observed['CPU'][9]), (index, PCS[index], PCS[index], PCS[index]), 'All normal boundary PCs/order')
        ac = a['source_CPU']; bc = b['CPU']
        amask = sum(1 << FLAG_BITS[k] for k in a['undefined_flags'])
        bmask = sum(1 << FLAG_BITS[k] for k in b['undefined_flags_before'])
        eq(ac[:8]+[ac[8]&~amask, ac[9]], observed['CPU'][:8]+[observed['CPU'][8]&~amask, observed['CPU'][9]], 'Entire original source-defined CPU joins actual normal boundary')
        for k in (0, 1, 3, 4, 5, 6, 7, 9):
            if index in (1, 2, 3, 4, 5) and k == 0:
                eq((ac[k], bc[k]), (a_by['global-object']['address'], b_by['global-object']['address']), 'MFC normal returned global-object role')
            elif index == 1 and k == 1:
                eq((ac[k], bc[k]), (a_head, b_head), 'MFC source EH predecessor survives in ECX')
            else:
                eq(ac[k], bc[k], 'Every other bounded nonvolatile/scalar normal CPU field')
        # EDX is the already scoped actual original API volatile/input carry;
        # both full CPU values are independently derived and retained.
        mask = amask | bmask
        flag_relation = 'exact defined flag bits'
        if index == 1:
            # Last flag writer is physical CMP [ESI],0 at5F4010C3. Its operand
            # is the translated current global-object pointer (access45).
            eq((a_access[45][0], a_access[45][2]), (0x5f4010c3, a_by['global-object']['address']), 'Exact original pointer CMP flag provenance')
            eq((b_access[45][0], b_access[45][2]), (0x5f4010c3, b_by['global-object']['address']), 'Exact native pointer CMP flag provenance')
            for c, value in [(ac, a_access[45][2]), (bc, b_access[45][2])]:
                eq((c[8] >> 2) & 1, int((value & 255).bit_count() % 2 == 0), 'Literal CMP result derives the exact branch pointer parity')
            mask |= 1 << 2
            flag_relation = 'exact defined bits plus literal same-role pointer CMP parity'
        eq(ac[8] & ~mask, bc[8] & ~mask, 'Every other source-defined normal flag bit')
        eq(hardwarefx(bytes.fromhex(b['FX_hex'])).hex(), observed['FX512_hex'], 'Whole native literal FX matches original hardware projection')
        eq(b['ENV28_hex'], observed['ENV28_hex'], 'Whole literal/source normal x87 environment')
        boundary_rows.append(dict(original_source=a, original_observation=observed, native_literal_snapshot=b, defined_flags_relation=flag_relation, undefined_flags_original=a['undefined_flags'], undefined_flags_native=b['undefined_flags_before'], EDX_scope='Full independently derived original real-API volatile/current input and native typed-service carry; cross-process equality is not claimed', native_intermediate_hardware_observation=False))
        counts['paired_MFC_normal_boundary_relations'] += 1
    eq(len(native['source_API_relations']), 4, 'All four independent native API CALL/RETs')
    eq(len(native['actual_API_relations']), 4, 'All four actual native provider witnesses')
    eq(len(original['source_API_relations']), 4, 'All four original bounded APIs')
    eq(len(actual['APIs']), 8, 'All eight original actual API sides')
    api_rows = []
    raw_apis = native_capture.data(stem+'after/APIs.bin')
    eq(len(raw_apis), 4*352, 'Whole native API transport geometry')
    for index, (a, b, witness) in enumerate(zip(original['source_API_relations'], native['source_API_relations'], native['actual_API_relations'])):
        ae, az = actual['APIs'][2*index:2*index+2]
        raw = raw_apis[index*352:(index+1)*352]; words = struct.unpack_from('<16Q', raw)
        eq(list(words), list(witness['words']), 'Whole actual current API identity witness')
        eq(a['source_PC'], b['spec']['source_PC'], 'Same source API CALL PC')
        eq(a['entry_CPU'], ae['CPU'], 'Whole genuine original API entry CPU')
        eq(a['source_return_CPU'], az['CPU'], 'Whole genuine original first source-return CPU')
        eq(list(struct.unpack_from('<10I', raw, 128)), b['CPU_before'], 'Whole actual native API entry joins literal CPU')
        eq(list(struct.unpack_from('<10I', raw, 168)), b['CPU_after'], 'Whole actual native source API return joins literal CPU')
        eq(raw[208:272].hex(), b['frame64_hex'], 'Whole actual native API frame joins literal source stack')
        eq((a['entry_CPU'][4], a['source_return_CPU'][4], a['actual_return_PC']), (b['CPU_before'][4], b['CPU_after'][4], b['spec']['return_PC']), 'Exact API CALL frame, callee consumption, source continuation')
        eq(u32(bytes.fromhex(ae['frame64_hex'])), b['spec']['return_PC'], 'Original source-saved API return PC')
        if index == 0:
            eq(a['args'], [3], 'Original actual TLS index3'); eq(b['typed_result'], b_by['thread']['address'], 'Native exact current guest thread role')
            eq(a['source_return_CPU'][0], a_by['thread']['address'], 'Actual original TLS lookup returns exact borrowed thread role')
            eq(words[8], words[11], 'Actual native TLS returns exact current real association')
        elif index == 2:
            eq((a['source_return_CPU'][0], b['typed_result'], words[8]), (1252, 1252, 1252), 'Finite actual ACP1252 domain')
        else:
            eq(a['args'], [a_lock], 'Actual original initialized lock25 argument')
            eq(u32(raw[208:272], 4), inputs['guest_CS'], 'Literal native guest lock25 argument')
        eq(ae['FX512_hex'], az['FX512_hex'], 'Whole original actual API FX conserved')
        eq(ae['ENV28_hex'], az['ENV28_hex'], 'Whole original actual API ENV conserved')
        for offset, depth in [(272, b['CS_depth_before']), (312, b['CS_depth_after'])]:
            cs = raw[offset:offset+40]
            eq((u32(cs, 12), struct.unpack_from('<Q', cs, 16)[0]), (depth, words[9] if depth else 0), 'Whole actual native CS40 recurrence/current-thread relation')
        api_rows.append(dict(index=index, original_source=a, original_actual_entry=ae, original_actual_source_return=az, native_literal=b, actual_native=witness, original_postRET_memory_seed=False, original_API_held_CS24_observed=False, original_API_CPU_volatile_scope=a['volatile_input_fields'], native_postRET_machine_source_derived=True))
        counts['paired_MFC_named_API_lifetimes'] += 1
    # Preserve complete true original FS endpoints and balanced opaque CS24.
    base = f'phase/{original["sequence"]}/13/'
    a_teb_before = original_capture.data(base+'TEB-before.bin')
    a_teb_after = original_capture.data(base+'TEB-after.bin')
    eq(len(a_teb_before), 8192, 'Whole actual original root BEFORE TIB')
    eq(len(a_teb_after), 8192, 'Whole actual original root AFTER TIB')
    eq((u32(a_teb_before), u32(a_teb_after)), (a_head, a_head), 'Actual coherent original source FS head endpoints')
    eq(u32(a_teb_before, 0xe1c), a_by['thread']['address'], 'Actual source-entry TEB TLSindex3 names the exact borrowed thread role')
    eq(u32(get(region_memory, 0x7ffdee1c, 4)), b_by['thread']['address'], 'Native semantic TLSindex3 mirror names its declared thread role')
    a_cs_before = original_capture.data(base+'MFC1168/BEFORE/CRT-codepage-lock/bytes.bin')
    a_cs_after = original_capture.data(base+'MFC1168/AFTER/CRT-codepage-lock/bytes.bin')
    eq(a_cs_before, a_cs_after, 'Whole actual original CS24 is balanced; opaque internal interval remains untraced')
    module_rows = []
    for page, provider in [(0x5f4cb000, 'MFC'), (0x78037000, 'CRT')]:
        ai = original_capture.data(base+f'MFC1168/BEFORE/{provider}/{page}.bin')
        af = original_capture.data(base+f'MFC1168/AFTER/{provider}/{page}.bin')
        bi = bytes(region_memory[page]); bf = bytes(region_final[page])
        eq(len(ai), 4096, 'Whole original current provider input page')
        expected = reconstruct({page: bytearray(ai)}, a_access)
        eq(bytes(expected[page]), af, 'Whole original provider page is genuine input plus literal writes')
        typed = set()
        for cell in inputs['pointer_cells'] + inputs['CRT_cells']:
            if page <= cell['address'] < page+4096:
                typed.update(range(cell['address']-page, cell['address']-page+4))
                eq(u32(bi, cell['address']-page), cell['projected'], 'Exact current native declared loader pointer/cache merge')
                target_roles = [r['role'] for r in b_owners if r['address'] == cell['projected']]
                need(len(target_roles) <= 1, 'Unique typed loader target role')
                expected_original = a_by[target_roles[0]]['address'] if target_roles else a_lock if cell['projected'] == inputs['guest_CS'] else cell['projected']
                eq(u32(ai, cell['address']-page), expected_original, 'Exact original measured same-role loader pointer/cache cell')
        differences = diffs(ai, bi)
        for row in differences:
            offset = row['offset']
            if offset in typed:
                continue
            need(not any(not r[4] and r[1] <= page+offset < r[1]+r[3] for r in a_access+b_access), 'Every other differing opaque provider input byte is unconsumed')
            need(not any(r[4] and r[1] <= page+offset < r[1]+r[3] for r in a_access+b_access), 'Opaque carried provider input has no source overwrite')
            eq((af[offset], bf[offset]), (ai[offset], bi[offset]), 'Entire opaque input difference carries in both branches')
        module_rows.append(dict(page=page, original_initial_hex=ai.hex(), original_source_final_hex=af.hex(), native_initial_hex=bi.hex(), native_source_final_hex=bf.hex(), exact_typed_loader_cell_offsets=sorted(typed), own_complete_input_differences=differences, ordinary_page_mask=False))
        counts['paired_MFC_whole_module_input_relations'] += 1
    return counts, dict(level=native['level'], sequence=native['sequence'], phase=13, root=ROOT,
        operand_relations=operand_rows, borrowed_roles=owner_rows, normal_boundaries=boundary_rows,
        API_lifetimes=api_rows, native_whole_regions=region_rows, whole_module_input_relations=module_rows,
        finite_TIB_region_representation=adapter,
        original_source_FS_writes=original_fs, native_source_FS_writes=native_fs,
        original_true_TIB_BEFORE_sha256=hashlib.sha256(a_teb_before).hexdigest(),
        original_true_TIB_AFTER_sha256=hashlib.sha256(a_teb_after).hexdigest(),
        original_whole_balanced_CS24_hex=a_cs_before.hex(),
        original_intermediate_FS_observed=False, original_API_held_CS24_observed=False,
        original_source_comparison_seed='Current own genuine chronological BEFORE only',
        native_source_comparison_seed='Persistent independently computed BEFORE only',
        original_postRET_observed=False, candidate_AFTER_machine_seed=False,
        original_whole_TIB_or_opaque_OS_CS_interval_equivalence=False)
