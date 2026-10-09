"""Freeze exact current proof identities and history without ancestral closures."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
BASE=ROOT/'reports/m4-crt-heap-return-root'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import unique_object
from paths import publish_bytes,workspace_path
FIXED={
 'recovery':('reports/m4-crt-heap-return-recovery/recovery-r1/report.json','c285ece7e08e2c152735629c48aae461d9f28d006895cf87e9f5157b23053684'),
 'source_contract':('reports/m4-crt-heap-return-review/source-r3/report.json','814f2fb571baf2c60f88905204bf28ae1552a4e1a1b0d4fe3a2584f8525a8904'),
 'preparation':('reports/m4-crt-heap-return/preparation-r2/report.json','7837c18f929bf37c1b7e08a84c433bf93b86bc7de41393acadfa7520ae81be82'),
 'build':('reports/m4-crt-heap-return/build-r2/build.json','6ea56b105e11b4a826e435cc0a66c391097adb1e9221eb0e38fe6f166ff219d8'),
 'source_audit':('reports/m4-crt-heap-return-review/audit-r1/report.json','634c63166c3ca327b5dbeb426ec50c09f21d28b80b42e741b862cbd8792dedb6'),
 'draft_model_audit':('reports/m4-crt-heap-return-root-audit/draft-r1/report.json','609a694c7060283c6092f36a99fbc1c4df07e053000ef52f62aa2dafec59f56f'),
 'compiled_build':('reports/m4-crt-heap-return-review/compiled-r1/flat-build.json','c5b05ccb5be8f41d547fd6d1f0f452cc5b5bd082b037f77d5f036386f0256402')}
DYNAMIC={'author_execution','root_model','model_audit','compiled_native','hardware_review','independent_seal'}
def main(catalog_path,catalog_sha,stage_sha,directory):
    out=workspace_path(directory,reports=True)
    if out.parent!=BASE or out.exists():raise ValueError('Fresh config output')
    def identity(path,digest=None):
        path=Path(path).absolute();actual=sha_file(path)
        if digest is not None and digest!=actual:raise ValueError('Fixed identity changed '+str(path))
        return dict(path=str(path),sha256=actual)
    identity(catalog_path,catalog_sha)
    catalog=json.loads(Path(catalog_path).read_bytes(),object_pairs_hook=unique_object)
    if set(catalog)!=DYNAMIC:raise ValueError('Exact completed runtime receipt catalog')
    receipts={name:identity(ROOT/path,digest) for name,(path,digest) in FIXED.items()}
    for name,item in catalog.items():
        if set(item)!={'path','sha256'}:raise ValueError('Exact runtime identity')
        receipts[name]=identity(item['path'],item['sha256'])
    pins=[]
    for item in receipts.values():
        path=Path(item['path']).parent/'pins.json'
        if path.exists():pins.append(identity(path))
    # Exactly these earlier receipt identities; their broad documentary closures are not reopened.
    history=[identity(ROOT/path,digest) for path,digest in (
        ('reports/m4-crt-heap-version-root/root-acceptance-r1/report.json','cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1'),
        ('reports/m4-crt-heap-version-root/final-check-r1/report.json','b4e30dc4298f70ef55b97de0119158da500656df9b51759753f1e646e755398d'),
        ('reports/m4-crt-heap-version-review/failed-native-r1/report.json','33b04d1f74afbbccb3cec2b33fb2f85119e7f1e29ba5837f9a3cef912a701811'),
        ('reports/m4-crt-heap-version-host-review/diagnosis-r1/report.json','231ab4795a86ebda9c33eea33ae78a3aa55ed6bb0120488e6e800928879764f6'),
        ('reports/m4-crt-heap-return/readiness-refusal-r1/report.json','b1393c0880653da456f637d2149982ff0eb0efb12635a8d098f00cd38bec6541'),
        ('reports/m4-crt-heap-return-review/readiness-r1/report.json','e9afee4c566d79665efeae6312fe6ab635c29131669a6b22ea1c8f56b01c8fb4'))]
    history.append(identity(ROOT/'reports/m4-crt-heap-return/execution-r1/report.json',
        '7e1c25565468f3d286e8262076825e616bd24c10b9ce1665fa06237a1be8d52b'))
    for path in ('reports/m4-crt-heap-return-review/history-r1/source-r1-superseded.json',
        'reports/m4-crt-heap-return/preparation-r1/report.json','reports/m4-crt-heap-return/preparation-r1/pins.json',
        'reports/m4-crt-heap-return/build-r1/build.json','reports/m4-crt-heap-return-root/draft-r1/report.json',
        'reports/m4-crt-heap-return-review/packaging-refusal-r1/report.json',
        'reports/m4-crt-heap-return-review/hardlink-refusal-r1/report.json',
        'reports/m4-crt-heap-return-review/check-preflight-r1/refusal.json',
        'reports/m4-crt-heap-return-root/draft-stage-r1/stage.json',
        'reports/m4-crt-heap-mode/build-r1/sources/runtime/graphics/README.md'):
        history.append(identity(ROOT/path))
    documents=[identity(ROOT/path) for path in (
        'docs/m4-progress-heap-return.md','docs/m4-crt-heap-return-review.md',
        'tools/m4-crt-heap-return-root/README.md','tools/m4-crt-heap-return/README.md',
        'tools/m4-crt-heap-return-review/README.md','tools/m4-crt-heap-return-recovery/README.md',
        'tools/m4-crt-heap-return-root-audit/README.md','tools/m4-crt-heap-return-root-audit/README-final.md')]
    review=identity(ROOT/'reports/m4-crt-heap-return-acceptance-review/review-r1/report.json')
    history.append(review)
    review_pins=Path(review['path']).parent/'pins.json'
    pins.append(identity(review_pins))
    stage=BASE/'observe-stage-r1';identity(stage/'stage.json',stage_sha)
    config=dict(receipts=receipts,pins=pins,history=history,documents=documents,
        observer_stage=dict(path=str(stage),sha256=stage_sha))
    out.mkdir();path=out/'config.json';publish_bytes(path,(json.dumps(config,indent=2)+'\n').encode())
    print(json.dumps(dict(path=str(path),sha256=sha_file(path))))
if __name__=='__main__':main(*sys.argv[1:])
