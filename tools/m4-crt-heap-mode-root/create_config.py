"""Bind frozen current heap-mode proof domains and authored documents."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from paths import publish_bytes,workspace_path

FIXED = {
    'recovery':('reports/m4-crt-heap-mode-recovery/recovery-r1/report.json','135ad3a9d2b24635d3f2547aa6904fef968daab02ae230302d1e3812914cd74c'),
    'source_contract':('reports/m4-crt-heap-mode-review/source-r1/report.json','813350c744665fc61435d9d7cf1d1ba3fb8c8fe8dc8944b6c4538ec7b7488ce0'),
    'preparation':('reports/m4-crt-heap-mode/preparation-r2/report.json','0791244218aa159177f3ea0ccd1b312085710b836af0e72da609e2f6870db3f3'),
    'build':('reports/m4-crt-heap-mode/build-r1/build.json','e1302754fc5f689fb79300e72c66b573d590a0d53f921a5b780234df99a00f4a'),
    'author_execution':('reports/m4-crt-heap-mode/execution-r1/report.json','3b262a0dd521ab1f602c1a026db55c55e10f5ca0330b4b69244eb061e411fdaa'),
    'root_model':('reports/m4-crt-heap-mode-root/observe-r1/report.json','0ac8693b798a8bd650a2f8529f92adfd562749d5ad9eabc5342d5fe5fc933cd0'),
    'source_audit':('reports/m4-crt-heap-mode-review/audit-r1/report.json','8ec61c385a275aaf6fca985020f8e057ce715628131d762a99aba2f56b48323f'),
    'draft_model_audit':('reports/m4-crt-heap-mode-root-audit/draft-r1/report.json','f6d403d7bf1404af63d93d8d79db4f34f930f0c7a4a4bdad0e4b5c72abc5795a')}


def main(model_sha,compiled_sha,native_sha,hardware_path,hardware_sha,seal_sha,directory):
    out=workspace_path(directory,reports=True)
    if out.exists() or out.parent!=ROOT/'reports/m4-crt-heap-mode-root':
        raise ValueError('Fresh config output')
    def identity(path,digest=None):
        path=Path(path).absolute(); actual=sha_file(path)
        if digest is not None and actual!=digest:
            raise ValueError('Fixed config input changed: '+str(path))
        return dict(path=str(path),sha256=actual)
    receipts={name:identity(ROOT/path,digest) for name,(path,digest) in FIXED.items()}
    for name,path,digest in (
        ('model_audit','reports/m4-crt-heap-mode-root-audit/final-r1/report.json',model_sha),
        ('compiled_build','reports/m4-crt-heap-mode-review/compiled-r1/flat-build.json',compiled_sha),
        ('compiled_native','reports/m4-crt-heap-mode-review/native-r1/report.json',native_sha),
        ('hardware_review',hardware_path,hardware_sha),
        ('independent_seal','reports/m4-crt-heap-mode-review/sealed-r1/report.json',seal_sha)):
        receipts[name]=identity(ROOT/path,digest)
    pins=[]
    for item in receipts.values():
        path=Path(item['path']).parent/'pins.json'
        if path.exists():
            pins.append(identity(path))
    history=[identity(ROOT/'reports/m4-crt-heap-create-root/root-acceptance-r1/report.json',
                      'e40df22e7b6263f75d9215cdaeadeb6a30030a4b07008c58442d8512d10c4326')]
    for path in ('reports/m4-crt-heap-mode/preparation-r1/report.json',
                 'reports/m4-crt-heap-mode/preparation-r1/pins.json',
                 'reports/m4-crt-heap-mode-root/draft-r1/report.json',
                 'reports/m4-crt-heap-mode-root/draft-stage-r1/stage.json',
                 'reports/m4-crt-heap-mode-review/history-r1/check-r1-refusal.json'):
        history.append(identity(ROOT/path))
    for folder in sorted((ROOT/'reports/m4-crt-heap-mode-review').glob('check-*')):
        path=folder/'report.json'
        if path.exists() and path.absolute()!=Path(receipts['hardware_review']['path']):
            history.append(identity(path))
    documents=[identity(ROOT/path) for path in (
        'docs/m4-progress-heap-mode.md','docs/m4-crt-heap-mode-review.md',
        'tools/m4-crt-heap-mode-root/README.md','tools/m4-crt-heap-mode/README.md',
        'tools/m4-crt-heap-mode-review/README.md','tools/m4-crt-heap-mode-recovery/README.md',
        'tools/m4-crt-heap-mode-root-audit/README.md','tools/m4-crt-heap-mode-root-audit/README-final.md')]
    stage=ROOT/'reports/m4-crt-heap-mode-root/observe-stage-r1'
    fixed=identity(stage/'stage.json','1a7d9b3b0a309f9cc8b7ef68cd6fe344fca1a4da62b899117dcf5ac8afbe64b0')
    config=dict(receipts=receipts,pins=pins,history=history,documents=documents,
                observer_stage=dict(path=str(stage),sha256=fixed['sha256']))
    out.mkdir();path=out/'config.json'
    publish_bytes(path,(json.dumps(config,indent=2)+'\n').encode())
    print(json.dumps(dict(path=str(path),sha256=sha_file(path))))


if __name__=='__main__':
    main(*sys.argv[1:])
