"""Independent frozen-fixture, physical closure and causal string-control audit.

Reads genuine compiled-control observations. Does not execute providers, alter
source bodies, repair observations or substitute native API responses.
"""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from stages import verify_stage
from manifests import verify_manifest


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def module(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def machine(p):
    raw = Path(p).read_bytes()
    if raw[:8] == b'!<arch>\n':
        offset, machines = 8, []
        while offset < len(raw):
            header = raw[offset:offset+60]
            need(len(header) == 60 and header[58:60] == b'`\n', 'Physical COFF archive member header')
            name = header[:16].strip()
            count = int(header[48:58].strip())
            member = raw[offset+60:offset+60+count]
            need(len(member) == count, 'Complete physical COFF archive member')
            if name not in (b'/', b'//'):
                machines.append(struct.unpack_from('<H',member,6 if member[:4] == b'\0\0\xff\xff' else 0)[0])
            offset += 60+count+(count%2)
        need(machines and all(m == 0x8664 for m in machines), 'Each physical library member is AMD64 COFF')
        return 0x8664
    if raw[:2] == b'MZ':
        offset = struct.unpack_from('<I', raw, 0x3c)[0]
        need(raw[offset:offset+4] == b'PE\0\0', 'Physical PE signature')
        return struct.unpack_from('<H', raw, offset+4)[0]
    if raw[:4] == b'\0\0\xff\xff':
        return struct.unpack_from('<H',raw,6)[0]
    return struct.unpack_from('<H', raw)[0]


def named_export(path, wanted):
    data = Path(path).read_bytes()
    u16 = lambda n: struct.unpack_from('<H', data, n)[0]
    u32 = lambda n: struct.unpack_from('<I', data, n)[0]
    pe = u32(60)
    need(data[:2] == b'MZ' and data[pe:pe+4] == b'PE\0\0' and u16(pe+4) == 0x8664,
         'Physical loaded owner is AMD64 PE')
    optional = pe+24
    need(u16(optional) == 0x20b, 'PE32+ export table layout')
    export_rva, export_size = u32(optional+112), u32(optional+116)
    sections = [optional+u16(pe+20)+40*n for n in range(u16(pe+6))]
    def offset(rva, count):
        matches = [u32(s+20)+rva-u32(s+12) for s in sections
                   if u32(s+12) <= rva and rva+count <= u32(s+12)+u32(s+16)]
        need(len(matches) == 1 and matches[0]+count <= len(data), 'Unique bounded physical owner export RVA')
        return matches[0]
    def string(rva):
        start = offset(rva,1)
        end = data.find(b'\0',start,min(start+4096,len(data)))
        need(end >= start, 'Bounded physical owner export name')
        return data[start:end].decode('ascii')
    directory = offset(export_rva,40)
    funcs, names, ordinals = u32(directory+28), u32(directory+32), u32(directory+36)
    results = []
    for n in range(u32(directory+24)):
        if string(u32(offset(names+n*4,4))) != wanted:
            continue
        ordinal = u16(offset(ordinals+n*2,2))
        need(ordinal < u32(directory+20), 'Bounded physical owner named ordinal')
        result = u32(offset(funcs+ordinal*4,4))
        need(not export_rva <= result < export_rva+export_size, 'Owning module direct export, no forwarder substitution')
        results.append(result)
    need(len(results) == 1, 'Unique actual owning named HeapDestroy export')
    return results[0]


def audit(buildpath, digest, capturepath, name, control_digest):
    out = ROOT/'reports/m4-strings-control-audit'/name
    need(not out.exists(), 'Fresh audit receipt')
    out.mkdir(parents=True)
    pins, rows, findings, checks = {}, [], [], {}
    passed = False

    def pin(p, h=None):
        p = Path(p).resolve()
        value = sha(p)
        need(h is None or value == h, 'Exact current physical identity: '+str(p))
        need(str(p) not in pins or pins[str(p)] == value, 'Consistent physical input')
        pins[str(p)] = value
        return p

    try:
        pin(__file__)
        pin(sys.executable)
        b = json.loads(pin(buildpath, digest).read_bytes())
        need(b['passed'] is True, 'Actual control compilation succeeded')
        final_control = pin(Path(capturepath)/'report.json',control_digest)
        final_provider = pin(ROOT/'reports/m4-strings-review/provider-acceptance-r2/report.json',
                             'b2573dc26574b7efd0c56d3f071cdf84269d01dfe795e8f97d915efa30f68c1c')
        need(json.loads(final_control.read_bytes())['passed'] and json.loads(final_provider.read_bytes())['passed'],
             'Final independent source model and compiled controls report success')
        checks['final_review_receipts'] = dict(controls=str(final_control),controls_sha256=sha(final_control),
                                              provider=str(final_provider),provider_sha256=sha(final_provider))
        prior_audit = pin(ROOT/'reports/m4-strings-control-audit/audit-r8/report.json',
                          'e8371c08ae88bc9ce400eedc7229383e617f1109e9661fdf195ea254cac74f61')
        prior_case12 = [r for r in json.loads(prior_audit.read_bytes())['cases'] if r['case'] == 12]
        checks['superseded_case12_scope'] = dict(prior_audit=str(prior_audit),prior_audit_sha256=sha(prior_audit),
                                                prior_actual_faults=[r['registry_fault'] for r in prior_case12],
                                                correction='Earlier audit-r8 and controls-r3 checked a refusal but did not prove the intended changed-IAT import guard. New fixture reaches phase20 after temporarily opening the true rdata mapping, mutating the raw slot, and restoring read permissions; exact literal import guard identity is mandatory.')
        for p, h in json.loads(pin(Path(buildpath).parent/'pins.json').read_bytes())['files'].items():
            pin(p, h)
        parent = json.loads(pin(b['parent_build'], b['parent_build_sha256']).read_bytes())
        prep = json.loads(pin(b['preparation']).read_bytes())
        native = json.loads(pin(ROOT/'reports/m4-strings-native/preparation-r5/report.json',
                               '94382b5470bfe5d6bd1b0bbbabeca69df13c52de5a910c43de606c0db29524bf').read_bytes())
        builddir = Path(buildpath).parent
        fixture = pin(builddir/'fixture.cpp').read_text()
        frozen_hooks = list(builddir.glob('fixture_hooks*.hpp'))
        need(len(frozen_hooks) == 1, 'One frozen compiled hook header')
        hooks = pin(frozen_hooks[0]).read_text()
        assembly = pin(builddir/'capture.s').read_text()
        cmake = pin(builddir/'CMakeLists.txt').read_text()
        source_fixture = [Path(p) for p in b['sources'] if Path(p).parent == ROOT/'tools/m4-strings-review' and Path(p).name.startswith('fixture') and Path(p).suffix == '.inc']
        source_hooks = [Path(p) for p in b['sources'] if Path(p).parent == ROOT/'tools/m4-strings-review' and Path(p).name.startswith('fixture_hooks')]
        need(len(source_fixture) == len(source_hooks) == 1, 'One exact authored fixture and hooks')
        need(fixture.endswith(pin(source_fixture[0]).read_text()), 'Compiled fixture includes exact frozen authored source')
        need(hooks == pin(source_hooks[0]).read_text(), 'Compiled hooks are the exact frozen authored source')
        need('invoke_selected_table' in fixture and 'data_boundary_call(&task,&before,&after,&rich)' in fixture,
             'Actual candidate entry inside independent assembly hardware boundary')
        need(fixture.index('const unsigned okay=t.c->invoke_selected_table') < fixture.index('ni::NumericHostBoundary observer_boundary'),
             'Observer boundary begins only after candidate return; cannot repair candidate return')
        need('fxrstor64 (%r9)' in assembly and 'fldenv 512(%r9)' in assembly,
             'Actual rich hardware input loaded in physical assembly')
        need('"-trigger-native-before.bin"' in fixture and 'reinterpret_cast<unsigned char*>(w[11])' in hooks,
             'Corruption targets actual full-width owned native pointer with pre-intervention full extent')
        need('points{0,50,50,50,52,54,50,51,52,53,54,55,0,52}' in hooks,
             'Exact finite genuine hook points for fourteen cases')
        need('GetProcAddress' not in hooks[hooks.index('template<class Session>'):],
             'Intervention body does not replace imported API targets or responses')
        checks['compiled_fixture_and_hooks_exact'] = True
        checks['observer_boundary_after_actual_candidate_return'] = True
        checker = pin(ROOT/'tools/m4-strings-review/run_controls_v4.py').read_text()
        need("provider[16]==0x78002f52" in checker and "provider[17]==w[4]" in checker
             and "provider[16]==0x78002fde" in checker and "progress={6:(0,0,0)" in checker,
             'Current checker binds source-read and write refusals and exact observer prefixes')
        need("candidate_after_identity_observed=True" in checker and 'research_pressure_scope=' not in checker,
             'Current checker states actual measured HeapDestroy and no obsolete pressure scenario')
        checks['checker_semantic_causality_and_scope_reviewed'] = True
        need('phase!=20' in fixture and 'protect({0x5bb000},Permissions::read|Permissions::write)' in fixture
             and fixture.index('protect({0x5bb000},Permissions::read|Permissions::write)')
                 < fixture.index('store<unsigned>({0x5bb670},0x78010a6d)')
                 < fixture.index('protect({0x5bb000},Permissions::read)'),
             'IAT intervention opens actual rdata mapping, changes raw slot then restores read protection at first string phase')
        need("provider[16]==0x48eb22" in checker and "provider[17]==0x5bb670" in checker
             and "message=='Exact string source import relocation'" in checker, 'Final checker binds genuine changed-IAT guard cause')
        physical = {}
        for level in ('O0','O2'):
            worker = pin(b['workers'][level]['path'], b['workers'][level]['sha256'])
            need(machine(worker) == 0x8664, 'Actual AMD64 control executable')
            objects = b['workers'][level]['objects']
            need(objects == prep['objects'][level], 'Control uses full unchanged parent source-object closure')
            need(len(objects) == len(set(objects)), 'No duplicate physical source object')
            required = {p for p in native['entry_objects'] if p.endswith('-'+level+'.obj')}
            need(required.issubset(set(objects)), 'All native provider/game and inherited COFFs included')
            for obj in objects:
                pin(obj)
                need(machine(obj) == 0x8664, 'Physical AMD64 COFF input')
            for family, folder in (('provider','m4-strings-native/lifts-r1'),('game','m4-strings-source/lifts-r1')):
                found = [p for p in objects if '/'+folder+'/' in p.replace('\\','/')]
                need(len(found) == (3 if family == 'provider' else 39), 'Exact additional physical '+family+' bodies')
            physical[level] = dict(worker=str(worker), worker_sha256=sha(worker), objects=len(objects),
                                   provider_string_bodies=3, game_new_bodies=39, AMD64=True)
        checks['physical_compiled_closure'] = physical
        d = module('audit_strict_control_archive', pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'))
        pin(ROOT/'tools/m4-pipeline/stages.py')
        pin(ROOT/'tools/m4-pipeline/capture_bundle.py')
        for level in ('O0','O2'):
            transport = Path(capturepath)/level/'transport.json'
            if not transport.exists():
                findings.append(dict(level=level, severity='incomplete', message='No actual immutable control capture at this level'))
                continue
            stage = Path(capturepath)/(level+'-stage')/'stage.json'
            pin(stage)
            verify_stage(stage.parent, sha(stage))
            need(json.loads(stage.read_bytes())['passed'], 'Genuine actual control worker stage succeeded')
            archive = d.DirectSet(transport, pin)
            try:
                need(archive.words('header.bin',6)[:4] == (1,14,28,9968), 'Complete current control record schema')
                need(archive.data('COMPLETE.txt') == b'Independent connected71 onexit controls passed\n', 'Genuine semantic completion')
                for case in range(14):
                    prefix = f'case-{case}/first-cleaned/'
                    raw = archive.data(f'case-{case}/first.bin')
                    retry = archive.data(f'case-{case}/retry.bin')
                    tags = struct.unpack_from('<32Q',raw)
                    again = struct.unpack_from('<32Q',retry)
                    witness = archive.words(f'case-{case}/first-trigger-string.bin',32,'Q')
                    copy = archive.words(f'case-{case}/first-trigger-copy.bin',5,'Q')
                    witnesses = list(struct.iter_unpack('<32Q',archive.data(prefix+'strings-witnesses.bin')))
                    allocations = list(struct.iter_unpack('<16Q',archive.data(prefix+'locale-allocations.bin')))
                    provider = archive.words(prefix+'registry-summary.bin',32,'Q')
                    fault = (provider[3],provider[16],provider[17],0)
                    reason = archive.data(prefix+'registry-exception-message.bin').decode('utf-8')
                    need(tags[:3] == (1,case,0) and again[:3] == (1,case,1), 'Actual distinct identified attempts')
                    need(tags[14] and again[14], 'Actual cleanup completed on both attempts')
                    for sample in (raw,retry):
                        t = struct.unpack_from('<32Q',sample)
                        before_hw, after_hw = sample[8880:9424], sample[9424:9968]
                        need(len(before_hw) == len(after_hw) == 544 and before_hw[:5] == after_hw[:5]
                             and before_hw[24:28] == after_hw[24:28] and before_hw[512:540] == after_hw[512:540],
                             'Full genuine outside-return legacy ENV28 and CW/SW/tag/MXCSR preservation')
                        need(struct.unpack_from('<H',before_hw)[0] == 0xa7f
                             and struct.unpack_from('<I',before_hw,24)[0] == 0x5fa5 and before_hw[4],
                             'Actual loaded independent nontrivial numerical input')
                        need(all(before_hw[32+n*16:42+n*16] == after_hw[32+n*16:42+n*16] for n in range(8))
                             and before_hw[256:416] == after_hw[256:416]
                             and t[13] == 0x4d573354 and not ((t[20]^t[21])&0x400),
                             'All physical raw80 x87 slots, native nonvolatile XMM6..15, LastError and ABI DF preserved')
                    need(not again[3] and again[19] and again[9] == again[10], 'Consumed or poisoned retry refuses without routes')
                    need(retry[256:512] == retry[512:768] and retry[768:4272] == retry[4272:7776]
                         and retry[7776:8288] == retry[8288:8800] and retry[8800:8840] == retry[8840:8880],
                         'Exact retry owner, whole State, FX and CPU continuity')
                    need(all(a[8] == a[9] == 0 and (a[10] or a[11]) for a in allocations), 'All actual allocations released and unmapped')
                    identity_before = archive.words(prefix+'heap-destroy-api-before.bin',11,'Q')
                    identity_after = archive.words(prefix+'heap-destroy-api-after.bin',11,'Q')
                    identity_independent = archive.words(f'case-{case}/first-cleanup-api-after.bin',11,'Q')
                    need(identity_before == identity_after == identity_independent and identity_before[0]
                         and identity_before[0] == identity_before[1] == identity_before[3]
                         and identity_before[2] == identity_before[6] and identity_before[7] == 0x1000 and identity_before[8] == 0x1000000,
                         'Actual imported/named/owning HeapDestroy identity measured before, after and independently after finish')
                    for suffix in ('-module-path.bin','-module-sha.bin'):
                        need(archive.data(prefix+'heap-destroy-api-before'+suffix) == archive.data(prefix+'heap-destroy-api-after'+suffix)
                             == archive.data(f'case-{case}/first-cleanup-api-after'+suffix), 'Full physical owning module identity unchanged')
                    module_path = archive.data(prefix+'heap-destroy-api-before-module-path.bin').decode('utf-16-le').split('\0',1)[0]
                    module_sha = archive.data(prefix+'heap-destroy-api-before-module-sha.bin').decode('ascii')
                    module_file = pin(module_path,module_sha)
                    need(identity_before[2]+named_export(module_file,'HeapDestroy') == identity_before[0],
                         'Direct physical loaded owner HeapDestroy RVA equals actual full-width measured target')
                    row = dict(level=level,case=case,result=tags[3],completed_roots=tags[4],hits=tags[7],
                               registry_fault=dict(failed=fault[0],pc=fault[1],address=fault[2],stage=fault[3],reason=reason),
                               string_allocations=sum(a[6] == 3 for a in allocations),total_allocations=len(allocations),
                               trigger=list(witness),copy_probe=list(copy),retained_witnesses=[list(q) for q in witnesses],
                               retry_no_routes=True,retry_exact_machine_and_owner=True,actual_HeapDestroy_identity_triplet=True,
                               strict_outside_hardware_pairs=2)
                    if case == 0:
                        need(tags[3] and tags[4] == 71 and tags[8] == 1, 'Ordinary selected71 and actual foreign-thread refusal')
                        need(len(witnesses) == 16 and len(allocations) == 17, '16 genuine duplicates plus registry; null root remains allocation-free')
                        need(all(a[10] == 1 and a[11] == 0 for a in allocations), 'Ordinary exact genuine source free before HeapDestroy')
                        row['all_actual_owners_source_freed'] = True
                    else:
                        need(not tags[3] and tags[5] and tags[7] == 1 and tags[19], 'Actual intervention produced one refusal')
                        if case not in (12,):
                            need(len(witnesses) == 1 and witnesses[0][:8] == witness[:8], 'Exact genuine source invocation retained')
                    if case in (2,4,5,8,9,10,11,13):
                        need(sum(a[6] == 3 for a in allocations) == 1, 'One actual owned duplicate before refusal')
                    if case in (1,3,6,7):
                        need(not any(a[6] == 3 for a in allocations), 'Early refusal precedes source malloc')
                    if case in (2,4,5,8,9,10,11,13):
                        q = witnesses[0]
                        allocation = next(a for a in allocations if a[5] == q[12])
                        expected = archive.data(prefix+f'locale-allocation-{allocation[5]}-expected.bin')
                        initial = archive.data(prefix+f'locale-allocation-{allocation[5]}-initial.bin')
                        input_bytes = archive.data(prefix+'string-0-input.bin')
                        if case == 2:
                            need(q[8] == 9 and q[9] == 10 and q[16] == q[17] == 0 and expected[:allocation[3]] == initial,
                                 'Input mutation refuses after genuine malloc before any literal copy, preserving full untouched owner mirror')
                            need(reason == 'Immutable NUL-inclusive source string before literal copy' and fault[2] == 0x5e4240,
                                 'Exact immutable-input guard causes refusal')
                            row['full_owned_mirror_untouched'] = True
                        if case == 5:
                            before = archive.data(f'case-{case}/first-trigger-native-before.bin')
                            need(witness[16] == q[16] == 4 and q[17] == 0 and copy[2] == 4 and copy[4] == 0,
                                 'Exactly four literal committed bytes before next actual write refusal')
                            need(expected[:4] == input_bytes[:4] and expected[4:allocation[3]] == before[4:allocation[3]],
                                 'Exact committed prefix and unchanged full owner remainder')
                            row['full_owned_mirror_partial_commit_verified'] = True
                        if case == 13:
                            before = archive.data(f'case-{case}/first-trigger-native-before.bin')
                            need(witness[11] and len(before) == witness[13] and q[16] == 0,
                                 'Actual full-width native corruption targets associated live finite owner before copy')
                            row['actual_native_corruption_causal_guard'] = reason
                    if case == 3 and not (fault[1] == 0x78002f52 and fault[2] == 0x5e4240 and 'read fault' in reason):
                        findings.append(dict(level=level,case=case,severity='invalid_intervention',
                                             message='Source permission case did not fault on the intended genuine literal strlen read',actual_fault=row['registry_fault']))
                    if case in (4,5):
                        q = witnesses[0]
                        need(fault[1] == 0x78002fde and fault[2] == q[10]+(4 if case == 5 else 0) and 'store fault' in reason,
                             'RO destination refuses at exact first or next genuine literal strcpy store')
                    if case == 1:
                        need(fault[1] == 0x78010a6d and reason == 'Only committed source/API/research effects may change owned locale pages',
                             'Changed true source argument is rejected by actual carried owner mirror')
                    progress = {6:(0,0,0),7:(9,0,0),8:(9,0,0),9:(9,0,0),10:(9,4,0),11:(9,10,1)}
                    if case in progress:
                        q = witnesses[0]
                        need((q[8],q[16],q[17]) == progress[case] and reason == 'Independent deliberate string boundary observer failure',
                             'Actual hook50..55 exact strlen, committed-copy and source RET prefix')
                    if case == 12:
                        need(not witnesses and not any(witness) and not any(a[6] == 3 for a in allocations),
                             'Changed raw source IAT cannot fabricate a string invocation or native allocation')
                        need(tags[4] == 20 and fault[1] == 0x48eb22 and fault[2] == 0x5bb670
                             and reason == 'Exact string source import relocation',
                             'Changed true source IAT is refused at exact original import read after twenty completed roots')
                    if case == 13:
                        need(fault[1] == 0x78002fab and fault[2] == witness[10]
                             and reason == 'Checked complete current guest/native allocation backing and private generation required',
                             'Exact current full guest/native mirror and generation guard refuses actual native corruption')
                    rows.append(row)
            finally:
                archive.close()
        checks['all_actual_controls_present'] = len(rows) == 28
        passed = not findings and checks['all_actual_controls_present']
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(schema='mw34-independent-string-control-audit-v1',passed=passed,
                      build=str(buildpath),build_sha256=digest,capture=str(capturepath),checks=checks,
                      cases=rows,findings=findings,source_bodies_modified=False,API_response_injection=False,
                      observation_fabrication=False,initializer_credit=False,whole_M4_complete=False,
                      physical_inputs=pins,physical_closure=verify_manifest(pins))
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        (out/'pins.json').write_text(json.dumps(dict(files=pins|{str(out/'report.json'):sha(out/'report.json')}),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),cases=len(rows),findings=findings)))


if __name__ == '__main__':
    audit(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
