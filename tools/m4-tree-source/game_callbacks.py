"""Recover each actual LLVM undefined callback against its original tree PC."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def main(lift_report,name):
    out=ROOT/'reports/m4-tree-source'/name
    assert not out.exists()
    pins={}
    def pin(path,expected=None):
        path=Path(path).resolve();h=hashlib.sha256(path.read_bytes()).hexdigest()
        assert expected is None or h==expected
        pins[str(path)]=h
        return path
    path=pin(ROOT/'tools/m4-crt-locale-batch-recovery/callbacks.py')
    spec=importlib.util.spec_from_file_location('tree_callback_decoder',path)
    decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    lift_report=pin(lift_report);lift=lift_report.parent
    data=json.loads(lift_report.read_bytes());assert data['passed']and len(data['source_bodies'])==8
    recovery=pin(ROOT/'reports/m4-tree-source/recovery-r1/instruction-contracts.json')
    rows={r['pc']:r for r in json.loads(recovery.read_bytes())['instructions']}
    bodies={};sites={}
    for key,body in data['source_bodies'].items():
        pre=pin(lift/(key+'-pre.ll'));guest=pin(lift/(key+'-baseline.ll'));pin(lift/(key+'-host.ll'),body['host_sha256'])
        calls,mapping=decoder.recover(decoder.function(pre.read_text(),body['entry']),decoder.function(guest.read_text(),body['entry']),body['entry'],rows)
        for call in calls:
            pc=call['pc'];value=call['State_offsets']
            assert pc not in sites or sites[pc]==value
            sites[pc]=value
        bodies[key]=dict(entry=body['entry'],callback_sites=calls,source_marker_map=mapping)
    out.mkdir(parents=True)
    payload=dict(schema='mw34-tree-original-callbacks-v1',bodies=bodies,State_offsets_by_original_PC={str(p):v for p,v in sorted(sites.items())},AFTER_seed=False)
    (out/'callbacks.json').write_text(json.dumps(payload,indent=2)+'\n');pin(out/'callbacks.json');pin(__file__)
    report=dict(passed=True,scope='Exact tree source/LLVM undefined flag attribution; no execution',bodies=8,unique_sites=len(sites),callbacks_sha256=pins[str((out/'callbacks.json').resolve())],files=pins)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),callbacks_sha256=report['callbacks_sha256'],sites=len(sites))))
if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2])
