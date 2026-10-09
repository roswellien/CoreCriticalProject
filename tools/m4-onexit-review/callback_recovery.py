"""Independent original-PC attribution of actual lifted undefined flag callbacks."""
from pathlib import Path
import importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized,verify_manifest
from paths import publish_bytes,workspace_path
spec=importlib.util.spec_from_file_location('independent_onexit_callbacks',ROOT/'tools/m4-crt-locale-batch-recovery/callbacks.py')
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)

def main(lifts,expected_sha,output):
    source=workspace_path(lifts,reports=True);out=workspace_path(output,reports=True)
    C.need(source.parent==ROOT/'reports/m4-onexit-native' and out.parent==ROOT/'reports/m4-onexit-review' and not out.exists(),
           'Fresh independent callback attribution paths')
    files={}
    def pin(path,digest=None):
        path=Path(path).resolve();actual=sha_file(path)
        C.need(digest is None or actual==digest,'Exact actual callback source '+str(path));files[normalized(str(path))]=actual;return path
    report=json.loads(pin(source/'report.json',expected_sha).read_bytes());C.need(report['passed'] and not report['native_component_executed'],
                                                                                       'Frozen literal source-only lift report')
    for path,digest in report['files'].items():pin(path,digest)
    interface=pin(ROOT/'reports/m4-onexit-review/interface-r1/instruction-contracts.json',
                  '9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d')
    rows={r['pc']:r for r in json.loads(interface.read_bytes())['instructions']}
    baseline=pin(ROOT/'reports/m4-crt-locale-batch-recovery/callbacks-union-r1/callbacks.json',
                 'ce770b98b2dc1f25fa759b2ffa287d3870f367852a5ac406e86bf50e21774c1a')
    sites={};new={}
    def merge(site):
        value=tuple(site['State_offsets']);pc=site['pc']
        C.need(pc not in sites or sites[pc]==value,'Same original instruction has exact actual callback order')
        sites[pc]=value
    original=json.loads(baseline.read_bytes())
    for domain in ('new_bodies','baseline_bodies'):
        for body in original[domain].values():
            for site in body['callback_sites']:merge(site)
    for name,body in report['source_bodies'].items():
        pre=pin(source/(name+'-pre.ll'));guest=pin(source/(name+'-guest.ll'));host=pin(source/(name+'-host.ll'),body['host_sha256'])
        callbacks,mapping=C.recover(C.function(pre.read_text(),body['entry']),C.function(guest.read_text(),body['entry']),body['entry'],rows)
        for site in callbacks:merge(site)
        new[name]=dict(entry=body['entry'],callback_sites=callbacks,source_marker_map=mapping,
                       guest_path=str(guest),guest_sha256=sha_file(guest),host_path=str(host),host_sha256=sha_file(host))
    for p in (Path(__file__),Path(C.__file__),ROOT/'tools/m4-onexit-review/provider_responses.py',
              ROOT/'tools/m4-onexit-review/API-primary-references.json'):pin(p)
    out.mkdir(parents=True)
    payload=dict(schema='mw34-onexit-independent-generated-callbacks-v1',new_bodies=new,
                 State_offsets_by_original_PC={str(pc):list(v) for pc,v in sorted(sites.items())},
                 original_executed=False,native_executed=False)
    path=out/'callbacks.json';publish_bytes(path,(json.dumps(payload,indent=2)+'\n').encode());pin(path)
    result=dict(passed=True,schema='mw34-onexit-independent-callback-attribution-v1',
                lifts_sha256=expected_sha,callbacks_path=str(path),callbacks_sha256=sha_file(path),
                native_executed=False,original_executed=False,roots_admitted=0,body_count=len(new),
                files=files,physical_closure=verify_manifest(files))
    path=out/'report.json';publish_bytes(path,(json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,report_sha256=sha_file(path),callbacks_sha256=sha_file(out/'callbacks.json'),bodies=len(new))))

if __name__=='__main__':main(*sys.argv[1:])
