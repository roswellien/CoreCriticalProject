"""Read-only independent audit of immutable MFC compiled control observations.

No provider execution, source mutation, API result substitution, or repaired
observations. The compiled fixture and each actual causal prefix are audited.
"""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from stages import verify_stage
from manifests import verify_manifest


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def physical_machine(path):
    raw = Path(path).read_bytes()
    if raw[:2] == b'MZ':
        pe = struct.unpack_from('<I', raw, 60)[0]
        need(raw[pe:pe+4] == b'PE\0\0', 'Actual PE signature')
        return struct.unpack_from('<H', raw, pe+4)[0]
    if raw[:4] == b'\0\0\xff\xff':
        return struct.unpack_from('<H', raw, 6)[0]
    return struct.unpack_from('<H', raw)[0]


def strict_hardware(sample):
    need(len(sample) == 9968, 'Exact packed actual hardware/State/owner sample')
    tags = struct.unpack_from('<32Q', sample)
    before, after = sample[8880:9424], sample[9424:9968]
    need(before[:5] == after[:5] and before[24:28] == after[24:28]
         and before[512:540] == after[512:540], 'Actual x87 CW/SW/tag/MXCSR and full legacy ENV28 preservation')
    need(struct.unpack_from('<H', before)[0] == 0xa7f
         and struct.unpack_from('<I', before, 24)[0] == 0x5fa5 and before[4],
         'Actual independently loaded nontrivial numerical input')
    need(all(before[32+n*16:42+n*16] == after[32+n*16:42+n*16] for n in range(8)),
         'Every physical raw80 x87 value is conserved at outside return')
    need(before[256:416] == after[256:416] and tags[13] == 0x4d573354
         and not ((tags[20]^tags[21]) & 0x400), 'Physical nonvolatile XMM6..15, LastError, and ABI DF conserved')
    return tags


def retry_conservation(sample):
    tags = strict_hardware(sample)
    need(not tags[3] and tags[19] and tags[9] == tags[10], 'Actual refused retry has no additional routed calls')
    need(sample[256:512] == sample[512:768] and sample[768:4272] == sample[4272:7776]
         and sample[7776:8288] == sample[8288:8800] and sample[8800:8840] == sample[8840:8880],
         'Actual retry preserves full owner summary, all3504 State bytes, FX512, and CPU40')
    return tags


def rows(raw, count, kind='Q'):
    width = struct.calcsize('<'+str(count)+kind)
    need(len(raw) % width == 0, 'Complete finite row encoding')
    return list(struct.iter_unpack('<'+str(count)+kind, raw))


def owned_replay(archive, prefix, witness, allocation, stores):
    """Replay actual literal private stores over the measured BEFORE extent."""
    guest, request, extent, mapped, generation = allocation[1:6]
    need(allocation[6] == 4 and (guest, request, extent, generation)
         == (witness[16], witness[7], witness[19], witness[18]),
         'Actual MFC record joins exact whole allocation and private generation')
    initial = archive.data(prefix+f'locale-allocation-{generation}-initial.bin')
    expected = archive.data(prefix+f'locale-allocation-{generation}-expected.bin')
    need(len(initial) == extent and len(expected) == mapped and 0 < request <= extent <= mapped,
         'Full actual initial native extent and complete finite guest mirror')
    reconstructed = bytearray(initial + bytes(mapped-extent))
    private, published = 0, 0
    for row in stores:
        if row[1] != witness[1]:
            continue
        need(row[0] == 1 and row[2] == witness[2], 'Exact original root for current store ledger')
        if row[7] == 1:
            offset = row[4]-guest
            need(0 <= offset and 0 < row[5] <= 8 and offset+row[5] <= request,
                 'Literal object store is wholly inside requested storage')
            reconstructed[offset:offset+row[5]] = row[6].to_bytes(8, 'little')[:row[5]]
            private += row[5]
        else:
            need(row[7] == 2 and row[5] == 4 and row[6] == guest,
                 'Exact whole guest alias is the source object publication')
            published += 1
    need(bytes(reconstructed) == expected and (private, published) == (witness[24], witness[23]),
         'All committed private stores, untouched native padding, full guest backing, and publication counts')
    if allocation[9]:
        need(archive.data(prefix+f'locale-allocation-{generation}-owned-page.bin') == expected,
             'Actual entire still-mapped guest page equals reconstructed literal effects')
    return dict(generation=generation, guest=guest, request=request, extent=extent,
                mapped=mapped, committed_private_bytes=private, publications=published,
                complete_expected_sha256=hashlib.sha256(expected).hexdigest())


def original_frames(witness, spec, instruction):
    """Entry retains the constructor CALL frame through the actual thunk JMP."""
    need((witness[2], witness[4], witness[7]) == (spec['root'], spec['CALL_pc'], spec['requested_size']),
         'Original root, real CALL PC, and exact raw requested size')
    need(witness[6] == witness[4]+instruction['width'], 'True constructor CALL return PC is retained')
    need(witness[8:16] == (0x78001498, 0x780012b3, 0x5f401ea1, 0x5f401eb5,
                           witness[5]-24, witness[7], 0x5f401ead, 0xffffffff),
         'Original raw imports, initialized handler, actual CALL EBX, and cdecl malloc frame')
    need(witness[16] and witness[17] and witness[18] and witness[20] == witness[16]
         and witness[21] == 1, 'Actual positive native malloc owner reaches literal MFC RET')
    if witness[25]:
        need(witness[25] == 0x5f401782 and witness[27] == witness[26]-8
             and witness[28:30] == (0x7800138a, 0x78001390),
             'Genuine original MFC825 wrapper retains exact cdecl CRTfree CALL frame')


def actual_identity(archive, stem, pin, parser):
    value = archive.words(stem+'.bin', 11, 'Q')
    target, named, owner, owner_named, base, size, allocated, state, kind, protect, _ = value
    need(target == named == owner_named and owner == allocated and base <= target < base+size
         and state == 0x1000 and kind == 0x1000000 and protect & 0xf0 and not protect & 0x101,
         'Measured actual full-width executable image target and module owner')
    path = archive.data(stem+'-module-path.bin').decode('utf-16-le').split('\0', 1)[0]
    digest = archive.data(stem+'-module-sha.bin').decode('ascii')
    pin(path, digest)
    need(owner+parser.named_export(path, 'HeapDestroy') == target,
         'Physical AMD64 direct named HeapDestroy resolves the measured target')
    return value, path, digest


def cause(case, guest, external):
    deliberate = 'Independent deliberate MFC source boundary observer failure'
    store = 'Checked actual source locale/parser store fault'
    free = 'MFC free entry requires exact live whole private object and generation'
    return {
        1:(0x5abd26,0x5bb4bc,45,'Exact game MFC ordinal823 source import relocation'),
        2:(0x5f401eb5,0x780039bf,71,'Heap creation observer changed State/FX or ownership/lifecycle ledgers'),
        3:(0x5f401ea0,0x5f498000,70,'Only committed source/API/research effects may change owned locale pages'),
        4:(0x5f401eb7,guest,72,'Checked complete current guest/native allocation backing and private generation required'),
        5:(0x4c7b91,guest,73,store), 6:(0x4c7b93,guest+4,73,store),
        7:(0x4c7b99,0x603fdc,73,store), 8:(0x5f401ea0,0,70,deliberate),
        9:(0x5f401eb5,0,71,deliberate), 10:(0x5f401eb7,0,72,deliberate),
        11:(0x4c7b91,0,75,deliberate), 12:(0x4c7b91,0,73,deliberate),
        13:(0x4c7b91,0,74,deliberate), 14:(0x78001390,0,76,deliberate),
        15:(0xffffff40,0,77,deliberate), 16:(0x5f401782,guest+4,45,free),
        17:(0x5f401782,0x603fd8,45,free), 18:(0x5f401782,guest,45,free),
        19:(0x5f401ea0,external,45,'Exact root/site/request for original MFC allocator CALL'),
        20:(0x4a8c55,guest+4,73,store),
    }[case]


def causal_case(archive, case, level, specs, instructions):
    stem = f'case-{case}/'
    live, clean = stem+'first-live/', stem+'first-cleaned/'
    first = strict_hardware(archive.data(stem+'first.bin'))
    retry = retry_conservation(archive.data(stem+'retry.bin'))
    need(first[:3] == (1,case,0) and retry[:3] == (1,case,1)
         and first[14] == retry[14] == 1 and first[10] == retry[10] and first[4] == retry[4],
         'Two true identified attempts; exact source route/prefix carried through refused retry')
    for name in ('locale-allocations.bin','locale-critical-sections.bin','mfc-allocation-witnesses.bin',
                 'mfc-store-ledger.bin','mfc-import-ledger.bin','locale-source-accesses.bin',
                 'locale-research-accesses.bin','locale-research-projections.bin'):
        need(archive.data(clean+name) == archive.data(stem+'retry-cleaned/'+name),
             'No owner/import/store/source/research ledger effects during retry: '+name)
    witnesses = rows(archive.data(live+'mfc-allocation-witnesses.bin'),32)
    final = rows(archive.data(clean+'mfc-allocation-witnesses.bin'),32)
    owned = rows(archive.data(live+'locale-allocations.bin'),16)
    released = rows(archive.data(clean+'locale-allocations.bin'),16)
    sections = rows(archive.data(clean+'locale-critical-sections.bin'),16)
    need(all(q[8:10] == (0,0) and (q[10] or q[11]) for q in released),
         'Every native owner truly released and its guest alias unmapped')
    need(all(q[5] == 0 and q[7:10] == (1,1,1) for q in sections),
         'All initialized private critical sections unlocked and deleted once')
    summary = archive.words(clean+'locale-summary.bin',32,'Q')
    need(summary[23] == 1 and summary[14] == summary[15] == summary[30] == 0,
         'Finished persistent source owner has no live allocation/section/heap handle')
    stores = rows(archive.data(live+'mfc-store-ledger.bin'),8)
    source = list(struct.iter_unpack('<IIQII',archive.data(live+'locale-source-accesses.bin')))
    replays = []
    for q in witnesses:
        need(q[0] == 1 and witnesses[q[1]] == q and (q[2],q[4]) in specs,
             'Exact current indexed witness is a declared original allocator site')
        spec = specs[q[2],q[4]]
        need(q[7] == spec['requested_size'] and q[6] == q[4]+instructions[q[4]]['width'],
             'Raw requested bytes and constructor return PC are source-derived')
        need((q[4],q[5],q[6],4,1) in source,
             'Genuine constructor CALL committed its return word; thunk JMP keeps the same frame')
        if q[16]:
            allocation = next(p for p in owned if p[5] == q[18])
            need(allocation[7] == q[17] and q[17] > 0xffffffff,
                 'Genuine acquired full AMD64 pointer matches current private generation')
            replays.append(owned_replay(archive,live,q,allocation,stores))
        if q[21]:
            original_frames(q,spec,instructions[q[4]])
        for write in (p for p in stores if p[1] == q[1]):
            need((write[3],write[4],write[6],write[5],1) in source,
                 'Each MFC object ledger store is an actual committed literal source memory write')
            if write[7] == 2:
                need(write[4] == spec['publication'], 'Exact original object field receives the whole alias')
    state = archive.data(stem+'first-causal-state.bin')
    stack = archive.data(stem+'first-causal-stack.bin')
    inputs = archive.words(stem+'first-causal-inputs.bin',3)
    probes = rows(archive.data(stem+'first-causal-probe-inputs.bin'),7)
    need(len(state) == 3504 and len(stack) == 4096, 'Actual immediate full State and active source stack before cleanup')
    detail = dict(level=level,case=case,source_prefix=first[4],owned_replays=replays,
                  genuine_probe_inputs=len(probes),source_witnesses=len(witnesses))
    if case == 0:
        need(first[3] == 1 and first[4] == first[12] == 103 and first[7] == 0 and first[8] == 1,
             'Ordinary connected103 completes and really refuses foreign-thread cleanup')
        need(len(witnesses) == len(final) == 35 and len(owned) == len(released) == 52
             and len([q for q in owned if q[6] == 4]) == 35 and not probes,
             '35 actual MFC owners carry 16 existing strings and one existing callback registry')
        need(all(q[21] == q[23] == q[30] == 1 and not q[31] for q in final)
             and all(q[10] and not q[11] for q in released),
             'Ordinary complete objects published once and every owner freed through source bodies')
        need(struct.unpack_from('<32Q',archive.data(stem+'first.bin'),512)[14] >= 1,
             'Actual ordinary source registry growth retained')
        return detail
    fault = archive.words(live+'locale-fault.bin',4)
    text = archive.data(live+'locale-fault-reason.bin').decode()
    observed = archive.words(live+'registry-summary.bin',32,'Q')
    trigger = archive.words(stem+'first-trigger-mfc.bin',32,'Q')
    current = witnesses[trigger[1]] if witnesses else None
    guest = current[16] if current else 0
    expected = cause(case,guest,probes[-1][6] if probes else 0)
    need((fault[1],fault[2],fault[3],text) == expected and observed[16:18] == fault[1:3]
         and fault[0] and not first[3] and first[5] and first[19] and first[7] == 1,
         'Intended intervention reaches exact source PC/address/stage/reason, rather than an earlier fixture fault')
    expected_completed = 56 if case == 20 else 1 if 14 <= case <= 19 else 0
    need(first[4] == first[12] == expected_completed, 'Literal source prefix stops exactly at intended refusal')
    detail.update(pc=fault[1],address=fault[2],stage=fault[3],reason=text)
    if case == 1:
        need(not witnesses and not any(trigger) and inputs[1] == 0x5f401ea0,
             'Raw game IAT mutation actually present and refuses before any MFC allocator entry')
        return detail
    need(trigger[:8] == current[:8] and trigger[2] == (0x4a8c20 if case == 20 else 0x40ffe0)
         and trigger[7] == (128 if case == 20 else 12), 'Intended real allocator invocation and original raw size')
    if case in (2,3,8,9):
        need(not guest and not any(q[6] == 4 for q in owned), 'Early refusal occurs before actual object HeapAlloc')
    else:
        need(guest and current[17] > 0xffffffff, 'Refusal preserves a genuine full-width private allocation')
    if case == 2:
        need(struct.unpack_from('<I',state,2232)[0] == 0x78001390, 'Actual EBX corruption retained before stable-observer refusal')
    if case == 3:
        need(inputs[2] == 0, 'Actual handler mutation retained; full provider-page guard is the reached cause')
    if case in (4,8,9,10):
        need(current[21] == current[23] == current[24] == 0, 'Allocation/CALL/RET frontier preserves actual incomplete prefix')
    if case == 11:
        need(current[21] == 1 and current[23] == current[24] == 0, 'Literal allocator RET completed before first object write')
    if case == 4:
        before = archive.data(stem+'first-trigger-native-before.bin')
        after = archive.data(stem+'first-trigger-native-after.bin')
        changed = bytearray(before); changed[0] ^= 0x55
        need(len(before) == current[19] and after == changed, 'Actual entire current native extent contains exactly the declared backing-byte mutation')
    if case in (5,6,7,12,13,20):
        count = {5:0,6:4,7:8,12:0,13:4,20:4}[case]
        need(current[24] == count and current[23] == int(case == 20),
             'Exact committed private prefix and genuine publication count at fault')
        native = archive.data(stem+'first-trigger-native-before.bin')
        mirror = archive.data(live+f'locale-allocation-{current[18]}-expected.bin')
        need(native == mirror[:current[19]], 'Entire native current backing agrees with independently replayed literal effects')
        if case == 7:
            need(inputs[0] == 0, 'Refused source publication leaves actual original BSS pointer zero')
        if case == 20:
            need(current[7] == current[19] == 128 and struct.unpack_from('<I',state,2216)[0] == guest+4
                 and struct.unpack_from('<I',state,2248)[0] == 31,
                 'Original MOV/ADD/DEC/JNE zero-fill loop committed one DWORD then refused next same-PC write')
        detail['actual_committed_prefix_bytes'] = count
    if 14 <= case <= 19:
        need(current[21] == current[23] == 1 and current[24] == 8,
             'First constructor fully initialized and published before research source-free/admission probe')
        need(len(probes) == (2 if case == 18 else 1) and first[22] == len(probes), 'Every genuine research probe has actual input evidence')
        argument = guest+4 if case == 16 else 0x603fd8 if case == 17 else 1048577 if case == 19 else guest
        for p in probes:
            need(p[0] == 1 and p[1] == (0x5f401ea0 if case == 19 else 0x5f401782)
                 and p[2] == p[3] and p[4] == argument and p[5] == 0xffffff40 and p[6] == p[2]-4,
                 'Declared research argument genuinely supplied at synchronized CPU/State external source frame')
        last = probes[-1]; at = last[6]-0x20001000
        need(0 <= at <= 4096-8 and stack[at:at+8] == struct.pack('<II',last[5],last[4]),
             'Immediate actual CALL frame contains exact committed marker and alias/request argument')
        if case in (15,18):
            need(current[30] == 1 and not current[31] and current[25] == 0x5f401782
                 and current[27] == current[26]-8 and current[28:30] == (0x7800138a,0x78001390),
                 'Actual literal MFC825/CRTfree source-free and unmap committed before later refusal')
        else:
            allocation = next(p for p in released if p[5] == current[18])
            need(not current[30] and allocation[11], 'Refused original free retains owner until actual private safeguard cleanup')
    return detail


def main(name):
    out = ROOT/'reports/m4-mfc-control-audit'/name
    need(not out.exists(), 'Fresh immutable independent audit receipt'); out.mkdir(parents=True)
    pins, cases, physical = {}, [], {}
    passed = False
    def pin(path, digest=None):
        path = Path(path).resolve(); key = str(path)
        actual = pins.get(key)
        if actual is None: actual = sha(path)
        need(digest is None or digest == actual, 'Exact independent physical input identity '+key)
        pins[key] = actual
        return path
    def receipt(path,digest):
        p = pin(ROOT/path,digest); result = json.loads(p.read_bytes())
        need(result['passed'] is True, 'Frozen successful receipt '+path)
        return result
    try:
        pin(__file__); pin(sys.executable)
        build = receipt('reports/m4-mfc-review/controls-build-r2/build.json','0664820d6ed94ec6d28024f1f0571b26d581f723e824b53777491d75c20e436c')
        execution = receipt('reports/m4-mfc-review/controls-execution-r2/report.json','61602e0a989e262300dadf1e102fbc44ce21166719cb3e769e8e6bddd3fea009')
        checked = receipt('reports/m4-mfc-review/controls-check-r1/report.json','4df258fd3d3b44021441167bc64e805f73515c45bf9b9ecdd5a674dbfb7d7977')
        seal = receipt('reports/m4-mfc-review/controls-source-seal-r1/report.json','ef7a24e0d67c4765e90e7d8ececf57d84680a208b318e898651a7f9b275ac45c')
        native = receipt('reports/m4-mfc-native/preparation-r1/report.json','3a2a6a2b43c4cc38c305e8f6965e4a56254f9677415c67cbb40091919072817e')
        for directory in ('controls-build-r2','controls-execution-r2','controls-check-r1'):
            closure = json.loads(pin(ROOT/'reports/m4-mfc-review'/directory/'pins.json').read_bytes())
            for pp,digest in closure['files'].items(): pin(pp,digest)
        for copy in seal['copied_sources']:
            need(pin(copy['source'],copy['sha256']).read_bytes() == pin(copy['copy'],copy['sha256']).read_bytes(),
                 'Byte-identical immutable compiled/checker source snapshot')
        specs_raw = json.loads(pin(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/allocation-inputs.json').read_bytes())
        specs = {(s['root'],s['CALL_pc']):s for s in specs_raw}
        contracts = json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json').read_bytes())
        instructions = {row['pc']:row for row in contracts['instructions']}
        need(len(specs) == 35 and instructions[0x4a8c55]['mnemonic'].lower() == 'mov',
             'Exact source allocation sites and honest ordinary MOV zero-fill loop attribution')
        reader = module('independent_mfc_archive',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'))
        parser = module('independent_physical_pe_parser',pin(ROOT/'tools/m4-strings-control-audit/audit_v9.py'))
        for mode in execution['levels']:
            level = mode['level']; worker = build['workers'][level]
            pin(worker['path'],worker['sha256'])
            need(physical_machine(worker['path']) == 0x8664, 'Actual compiled control worker is physical AMD64 PE')
            obj = set(worker['objects'])
            native_obj = {p for p in native['entry_objects'] if p.endswith('-'+level+'.obj')}
            need(len(obj) == 296 and len(native_obj) == 280 and native_obj <= obj,
                 'Complete unchanged296-object source closure includes all280 current provider/game COFFs')
            for pp in obj:
                pin(pp,native['entry_objects'].get(pp))
                need(physical_machine(pp) == 0x8664, 'Every actually linked source object is physical AMD64 COFF')
            physical[level] = dict(worker=worker['path'],worker_sha256=worker['sha256'],source_objects=len(obj),current_native_objects=len(native_obj))
            stage = json.loads(pin(mode['stage'],mode['stage_sha256']).read_bytes())
            verify_stage(Path(mode['stage']).parent,mode['stage_sha256'])
            need(stage['argv'][0] == worker['path'] and stage['input_sha256'][worker['path']] == worker['sha256']
                 and stage['artifact_sha256'][mode['capture']] == mode['capture_sha256'],
                 'Actual executed immutable control worker produced the exact direct archive receipt')
            archive = reader.DirectSet(pin(mode['capture'],mode['capture_sha256']),pin)
            try:
                need(archive.words('header.bin',6)[:4] == (1,21,42,9968)
                     and archive.data('COMPLETE.txt') == b'Independent connected103 MFC controls passed\n',
                     'Actual finite21-scenario/42-attempt semantic worker completion')
                for case in range(21):
                    result = causal_case(archive,case,level,specs,instructions)
                    prefix = f'case-{case}/first-cleaned/'
                    identities = [actual_identity(archive,prefix+'heap-destroy-api-'+point,pin,parser) for point in ('before','after')]
                    identities.append(actual_identity(archive,f'case-{case}/first-cleanup-api-after',pin,parser))
                    need(identities[0] == identities[1] == identities[2], 'Genuine pre/post HeapDestroy and independent immediate post-finish identity agree completely')
                    lifecycle = archive.words(prefix+'heap-create-registry.bin',18,'Q')
                    created = archive.words(prefix+'heap-create-witness.bin',16,'Q')
                    need(created[:6] == (1,0,1,0,4096,0) and created[6] and created[7] == 0x48450001
                         and created[11] == created[6] and lifecycle[2:11] == (1,0x48450001,created[6],1,1,0,1,1,1)
                         and lifecycle[12:] == (1,0,0,1,created[6],0),
                         'Actual single original HeapCreate and same full-width handle HeapDestroy success and zero remaining lifetime')
                    result['actual_heap_handle'] = created[6]
                    result['HeapDestroy_target'] = identities[0][0][0]
                    cases.append(result)
                    print(json.dumps(dict(level=level,case=case,passed=True)),flush=True)
            finally: archive.close()
        passed = True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); raise
    finally:
        result = dict(passed=passed,schema='mw34-mfc-independent-control-causal-audit-v1',cases=cases,
                      physical_workers=physical,files=pins,physical_closure=verify_manifest(pins),
                      scope='Read-only actual compiled causal observations, original CALL/thunk frames, source store replay over entire native-before and guest backing, exact refusal causes, full hardware/retry conservation and physical same-HANDLE HeapDestroy identity',
                      counts=dict(completed_cases=len(cases),actual_attempts=2*len(cases),actual_refusal_causes=sum(c['case']!=0 for c in cases),
                                  immediate_probe_inputs=sum(c['genuine_probe_inputs'] for c in cases),
                                  complete_MFC_owned_replays=sum(len(c['owned_replays']) for c in cases),
                                  outside_hardware_pairs=2*len(cases),full_machine_owner_retry_pairs=len(cases),destroy_identity_triplets=len(cases)),
                      findings=[],controls_execution_credit=True,auditor_executed_providers=False,
                      source_bodies_modified=False,API_response_injection=False,API_null_failure_claimed=False,
                      solely_oversize_guard_claimed=False,handler_execution_claimed=False,REP_transfer_claimed=False,
                      initializer_credit=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
        pins[str(out/'report.json')] = sha(out/'report.json')
        (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'))),flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
