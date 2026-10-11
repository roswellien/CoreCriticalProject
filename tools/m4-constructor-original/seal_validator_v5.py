"""Freeze current strict getter/NULL-free checker before its sole reader."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-constructor-original'
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,build_hash,preflight,preflight_hash,name):
    out=B/name
    if out.exists():raise ValueError('Fresh additive controller preparation required')
    pins={}
    def pin(p,h=None):
        p=Path(p).resolve()
        if p.suffix.lower()in('.mwb','.zip'):raise ValueError('No capture reader')
        v=sha(p)
        if h is not None and v!=h:raise ValueError('Exact physical input '+str(p))
        if str(p)in pins and pins[str(p)]!=v:raise ValueError('No conflicting physical input')
        pins[str(p)]=v;return p
    def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
    b=read(build,build_hash);q=read(preflight,preflight_hash);prep=Path(b['preparation']);p=read(prep/'report.json',b['preparation_sha256']);contracts=read(prep/'contracts.json')
    if not b['passed']or not q['passed']or not p['passed']or q['files'].get(str(build.resolve()))!=build_hash or q['files'].get(str(Path(b['worker']).resolve()))!=b['worker_sha256']:raise ValueError('Exact current independently reviewed final worker')
    pin(b['worker'],b['worker_sha256'])
    if contracts['new_NULL_free_bindings']!=[dict(root=0x4103f0,CALL_PC=0x58af9a,return_PC=0x58af9f),dict(root=0x410440,CALL_PC=0x58af9a,return_PC=0x58af9f)]:raise ValueError('Exact two source-proven normal-zero bindings')
    for name in('run.py','derive_runner.py','validate.py','validate_v2.py','validate_v3.py','validate_v4.py','validate_v5.py','derive_validator_v2.py','derive_validator_v3.py','derive_validator_v4.py','derive_validator_v5.py'):
        f=pin(R/'tools/m4-constructor-original'/name);ast.parse(f.read_text(encoding='utf-8-sig'))
    for rel in('tools/m4-crt-allocation-root/run_v2.py','tools/m4-joint-startup131/paired_exports.py','reports/m4-constructor-original/entry-chain-r1/report.json','reports/m4-constructor-source/preparation-r1/contracts.json'):
        pin(R/rel)
    pin(__file__)
    report=dict(passed=True,scope='Unexecuted exact strict current constructor37 observer reader; no source or initializer credit',build_path=str(build),build_sha256=build_hash,preflight_path=str(preflight),preflight_sha256=preflight_hash,preparation_sha256=b['preparation_sha256'],worker_sha256=b['worker_sha256'],validator_path=str(R/'tools/m4-constructor-original/validate_v5.py'),validator_sha256=sha(R/'tools/m4-constructor-original/validate_v5.py'),
        roots=37,phases=222,normal_record_bytes=189108,getter_companion_row_bytes=40,new_NULL_snapshot_bytes=628,
        strict_relations=['All ordered actual allocation/free/reallocation occurrence transitions and whole cleanup metadata from validator3',
            'Complete actual source-owned PE receiver page and readonly vptr/slot/EDX target companion for every getter boundary',
            'Exactly one published non-sentinel receiver in own genuine complete balanced BEFORE graph and whole current allocation backing',
            'Exact actual normal-zero58AF9A CALL/58AF9F return frame plus original free entry/post-epilogue preRET CPU/FX/ENV/FS/APIcount boundaries',
            'No volatile or void-return expected values copied; no original postRET snapshot claim'],
        capture_reader_opened=False,writer_executed=False,actual_allocation_getter_counts_unmeasured=True,source_AFTER_seed=False,whole_literal_source_proof=False,initializer_credit=0,files=pins)
    out.mkdir();f=out/'report.json';f.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(f),validator_sha256=report['validator_sha256'])))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
