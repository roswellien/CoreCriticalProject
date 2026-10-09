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
    if raw[:2] == b'MZ':
        offset = struct.unpack_from('<I', raw, 0x3c)[0]
        need(raw[offset:offset+4] == b'PE\0\0', 'Physical PE signature')
        return struct.unpack_from('<H', raw, offset+4)[0]
    if raw[:4] == b'\0\0\xff\xff':
        return struct.unpack_from('<H',raw,6)[0]
    return struct.unpack_from('<H', raw)[0]


def audit(buildpath, digest, capturepath, name):
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
        for p, h in json.loads(pin(Path(buildpath).parent/'pins.json').read_bytes())['files'].items():
            pin(p, h)
        parent = json.loads(pin(b['parent_build'], b['parent_build_sha256']).read_bytes())
        prep = json.loads(pin(b['preparation']).read_bytes())
        native = json.loads(pin(ROOT/'reports/m4-strings-native/preparation-r5/report.json',
                               '94382b5470bfe5d6bd1b0bbbabeca69df13c52de5a910c43de606c0db29524bf').read_bytes())
        builddir = Path(buildpath).parent
        fixture = pin(builddir/'fixture.cpp').read_text()
        hooks = pin(builddir/'fixture_hooks.hpp').read_text()
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
            verify_stage(pin(stage), sha(stage))
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
                    need(not again[3] and again[19] and again[9] == again[10], 'Consumed or poisoned retry refuses without routes')
                    need(retry[256:512] == retry[512:768] and retry[768:4272] == retry[4272:7776]
                         and retry[7776:8288] == retry[8288:8800] and retry[8800:8840] == retry[8840:8880],
                         'Exact retry owner, whole State, FX and CPU continuity')
                    need(all(a[8] == a[9] == 0 and (a[10] or a[11]) for a in allocations), 'All actual allocations released and unmapped')
                    row = dict(level=level,case=case,result=tags[3],completed_roots=tags[4],hits=tags[7],
                               registry_fault=dict(failed=fault[0],pc=fault[1],address=fault[2],stage=fault[3],reason=reason),
                               string_allocations=sum(a[6] == 3 for a in allocations),total_allocations=len(allocations),
                               trigger=list(witness),copy_probe=list(copy),retained_witnesses=[list(q) for q in witnesses],
                               retry_no_routes=True,retry_exact_machine_and_owner=True)
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
                            need(q[8] == 9 and q[9] == 10 and q[16] == q[17] == 0 and expected == initial,
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
    audit(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])
