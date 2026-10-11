"""Independent light review of the actual linked tree control fixture.

No transport/archive is opened. Causal payload validation remains the separately
executed controls reader. This gate authenticates source, build and scope.
"""
from pathlib import Path
import hashlib, json, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def need(v, s):
    if not v:
        raise ValueError(s)

def main(name):
    out = R / 'reports/m4-tree-original' / name
    need(not out.exists(), 'Fresh independent review directory')
    out.mkdir(parents=True)
    pins, findings = {}, []
    def pin(p, h=None):
        p = Path(p).resolve()
        need(p.suffix.lower() != '.mwb', 'No capture payload reader')
        a = sha(p)
        need(h is None or a == h, 'Exact reviewed physical file: ' + str(p))
        need(str(p) not in pins or pins[str(p)] == a, 'Consistent source identity')
        pins[str(p)] = a
        return p
    def read(p, h=None):
        return json.loads(pin(p, h).read_bytes())
    def check(v, s):
        need(v, s)
        findings.append(s)
    p = read(R/'reports/m4-tree-review/controls-preparation-r2/report.json',
             'a435e21179471f1f8915c8cce85f571a983db005c979f398bad27566a80aefc1')
    b = read(R/'reports/m4-tree-review/controls-build-r3/build.json',
             'ce9c498c654f9711c11873f457d7aafa38eae37a4b9e2c000a659bfec9a792c5')
    e = read(R/'reports/m4-tree-review/controls-execution-r2/report.json',
             '4e679098198d27ec24d08bd9b55ed3b8e036f3fc90d2786359234acce9670a6f')
    n = read(p['native_preparation'], p['native_preparation_sha256'])
    check(p['passed'] and b['passed'] and e['passed'] and n['passed'],
          'Current preparation, build, execution and native source receipts passed')
    check(b['preparation_sha256'] == sha(R/'reports/m4-tree-review/controls-preparation-r2/report.json')
          and e['build_sha256'] == sha(R/'reports/m4-tree-review/controls-build-r3/build.json'),
          'Exact current preparation to build to execution lineage')
    check(p['native_preparation_sha256'] == b['native_preparation_sha256']
          == e['native_preparation_sha256']
          == '9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2',
          'Every receipt binds actual native preparation5')
    check(p['control_scenarios'] == 18 and p['control_attempts'] == 36
          and p['selected_calls'] == 1 and p['root'] == 0x4b7f70,
          '18 scenarios with same-session retry, one actual selected tree root')
    check(p['CPU_after'] == [76,116] and p['FX_before'] == [116,628]
          and p['total_current_pages'] == 65 and len(set(p['current_pages'])) == 65,
          'Packed CPU/FX offsets and complete65 current-page inventory are retained')
    for q,h in (p['sources'] | p['files'] | b['sources']).items():
        pin(q,h)
    check(all(w['exit_code'] == 0 for w in e['workers'].values())
          and set(e['workers']) == set(b['workers']) == {'O0','O2'},
          'Actual O0/O2 workers exited successfully')
    for level, w in b['workers'].items():
        pin(w['path'], w['sha256'])
        check(w['literal_objects'] == p['objects'][level]
              and len(w['literal_objects']) == len(set(w['literal_objects'])) == 371,
              level + ':371 exact distinct literal COFF objects in final linked build')
    for command in b['commands']:
        need(command['exit_code'] == 0, 'Every retained compiler/link command succeeded')
        log = Path(e['build_path']).parent / command['log']
        pin(log,b['artifacts'][str(log)])
    hooks = pin(R/'tools/m4-tree-review/control_hooks_v2.hpp').read_text()
    prepdir = Path(b['preparation']).parent
    check((prepdir/'control_hooks.hpp').read_text() == hooks,
          'The compiled generated hook is byte-identical to corrected v2 source')
    fixture = pin(R/'tools/m4-tree-review/control_fixture.inc').read_text()
    check((prepdir/'fixture.cpp').read_text().endswith(fixture),
          'Final compiled fixture includes the independently read caller boundary source')
    for token in ('n.starts_with("locale-api-")', 'b.size()==256',
                  'API_site=unsigned(row[2])', 's.dump(&latest_api,nullptr)',
                  'if(API_site!=0x7810a30b)return'):
        need(token in hooks, 'Actual source-API witness selection: '+token)
    check('point!=(selected==15?41U:40U)' in hooks,
          'API pre/post seams selected from actual32-Q source witness, raw StatePC retained')
    check('point!=86||pc!=0x4bab44' in hooks
          and 'state->gpr.rdi.dword=next' in hooks
          and 'm4_onexit::write(s.token(),a,state->gpr.rax.dword,4)' in hooks,
          'Cases1-4 call the public owner write service at the actual decoded4BAB44 operand')
    check('next=old+20' in hooks and 'next=unsigned(rows[2][16])' in hooks
          and 's.mfc_witnesses().size()<4' in hooks,
          'Requested-tail and prior allocator occurrence controls use real current owner metadata')
    check('selected>=5&&selected<=10' in hooks
          and 'const_cast<std::byte*>(b.data())[offset]^=std::byte{1}' in hooks,
          'Cases5-10 mutate actual private records; integrity and conservation scope is distinct')
    check('restore_resource->RecursionCount^=1' in hooks
          and 'std::memcpy(resource_before.data(),restore_resource,40)' in hooks
          and 'std::memcpy(resource_after.data(),restore_resource,40)' in hooks
          and 'std::memcpy(restore_resource,resource_before.data(),40)' in hooks,
          'Case15 retains genuine full40-byte native CS before/after and restores the resource')
    check(fixture.index('mw34_tree_controls::restore_actual();')
          < fixture.index('c.registry().finish();'),
          'Real CS40 restoration occurs before Windows resource cleanup')
    check('c.registry().test_hook=nullptr;attempt(c,w,1)' in fixture
          and 'sample.owner_before==sample.owner_after' in fixture
          and 'sample.state_before==sample.state_after&&sample.fx_before==sample.fx_after&&sample.cpu_before==sample.cpu_after' in fixture,
          'Retry uses the same cleaned Context and compares whole guest State3504, FX512 and CPU40')
    check('a.env==b.env' in fixture and 'a.fx.data()+24' in fixture
          and 'a.fx.data()+256,b.fx.data()+256,160' in fixture
          and 'k*16,10' in fixture,
          'Host FP comparison is explicit architectural x87/ENV/MXCSR/XMM6-15, not fullFX equality')
    check('error==0x4d573354' in fixture and '(flags_before^flags_after)&0x400' in fixture,
          'Actual outside-return caller LastError and direction flag are checked')
    check(not p['source_bodies_modified'] and not p['API_response_injection']
          and p['initializer_credit'] == b['initializer_credit'] == e['initializer_credit'] == 0,
          'Control fixture claims no initializer credit, source-body mutation or API response injection')
    pin(__file__)
    for q,h in pins.items():
        need(sha(q) == h, 'Review inputs remained physically immutable')
    report = dict(passed=True,
        scope='Independent light physical source/build/scope review of actual linked tree controls; causal payloads remain separately validated',
        preparation_sha256=sha(R/'reports/m4-tree-review/controls-preparation-r2/report.json'),
        build_sha256=sha(R/'reports/m4-tree-review/controls-build-r3/build.json'),
        execution_sha256=sha(R/'reports/m4-tree-review/controls-execution-r2/report.json'),
        native_preparation_sha256=p['native_preparation_sha256'],
        predicates_reviewed=len(findings),findings=findings,
        public_owner_service_cases=[1,2,3,4],
        private_integrity_or_conservation_cases=[5,6,7,8,9,10],
        native_resource_case=15,whole_guest_retry=True,
        full_host_FX512_equality_claim=False,host_FP_architectural_scope=True,
        archive_reader_opened=False,causal_payload_validation_claim=False,
        initializer_credit=0,files=pins)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),predicates=len(findings),physical_files=len(pins))))

if __name__ == '__main__':
    main(sys.argv[1])
