"""Freeze the strict observation checker without opening a capture."""
from pathlib import Path
import ast, hashlib, json

R=Path(__file__).resolve().parents[2]
B=R/'reports/m4-constructor-original'
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=B/'controller-preparation-r3'
    if out.exists():raise ValueError('Additive fresh controller receipt required')
    pins={}
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p)
        if h is not None and h!=v:raise ValueError('Exact physical identity '+str(p))
        pins[str(p)]=v;return p
    prep=pin(B/'chronological-preparation-r7/report.json','6d3f97e734647085ee51c00538527e3e82ad31880d1310f946839be0e15720a0')
    build=pin(B/'chronological-build-r5/build.json','60e23288b3067cc7d78bbef9e2ca1286c941142a576a781ad7c2ffd2b2a53ac7')
    preflight=pin(R/'reports/m4-tree-review/constructor37-prelaunch-r8/report.json','7c952fa555c798a3cc85c5ef209f382eb918f271d2f978ccd001e831f476f6ac')
    b=json.loads(build.read_bytes());q=json.loads(preflight.read_bytes())
    if not b['passed']or not q['passed']or q['files'].get(str(build))!=sha(build):raise ValueError('Exact reviewed current candidate')
    worker=pin(b['worker'],b['worker_sha256'])
    if q['files'].get(str(worker))!=sha(worker):raise ValueError('Exact current linked worker')
    for name in('run.py','derive_runner.py','validate.py','validate_v2.py','validate_v3.py','derive_validator_v2.py','derive_validator_v3.py'):
        p=pin(R/'tools/m4-constructor-original'/name);ast.parse(p.read_text(encoding='utf-8-sig'))
    for name in('tools/m4-crt-allocation-root/run_v2.py','tools/m4-joint-startup131/paired_exports.py','tools/m4-pipeline/stages.py','reports/m4-constructor-original/entry-chain-r1/report.json'):
        pin(R/name)
    pin(__file__)
    report=dict(passed=True,scope='Unexecuted strict current constructor37 raw observation validator; no source or initializer credit',
        preparation_sha256=sha(prep),build_sha256=sha(build),preflight_sha256=sha(preflight),worker_sha256=sha(worker),
        validator_path=str(R/'tools/m4-constructor-original/validate_v3.py'),validator_sha256=sha(R/'tools/m4-constructor-original/validate_v3.py'),
        roots=37,phases=222,normal_record_bytes=189108,normal_record_offsets=dict(metadata=0,CPU=48,FX512=88,ENV28=600,frame64=628,pages46=692,end=189108),
        exact_validator_changes=['Pin and compare actual seven named owning MFC/CRT export and import observations',
            'Replay every successful HeapAlloc/HeapFree/HeapReAlloc occurrence in raw API order; reject missing serials and aliases',
            'Derive MFC HeapAlloc frame join and saved return from physical entry-chain proof',
            'Admit getter ECX+4 only from its genuine whole declared BEFORE source page',
            'Reject duplicate cleanup and require exact whole final live owner metadata',
            'Pin unchanged validator2 and exact additive derivation source'],
        writer_executed=False,capture_reader_opened=False,actual_allocation_getter_counts_unmeasured=True,
        whole_literal_source_proof=False,initializer_credit=0,files=pins)
    out.mkdir();p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,sha256=sha(p),validator_sha256=report['validator_sha256'])))
if __name__=='__main__':main()
