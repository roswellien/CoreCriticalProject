"""Exact literal formatter undefined callback/source-PC attribution."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True);pins={}
    def pin(p):
        p=Path(p).resolve();pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p
    path=pin(R/'tools/m4-crt-locale-batch-recovery/callbacks.py');s=importlib.util.spec_from_file_location('format_callback_decoder',path);D=importlib.util.module_from_spec(s);s.loader.exec_module(D)
    rows={r['pc']:r for p in(R/'reports/m4-formatting-source/provider-recovery-r2/instruction-contracts.json',R/'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json')for r in json.loads(pin(p).read_bytes())['instructions']}
    sites={};bodies={}
    for folder in('reports/m4-formatting-frontier/lifts-r1','reports/m4-formatting-source/lifts-r1'):
        lp=pin(R/folder/'report.json');lift=json.loads(lp.read_bytes());assert lift['passed']
        for key,b in lift['source_bodies'].items():
            if b['entry']in bodies:continue
            pre=pin(lp.parent/(key+'-pre.ll'));guest=pin(lp.parent/(key+'-baseline.ll'));host=pin(lp.parent/(key+'-host.ll'));assert pins[str(host)]==b['host_sha256']
            calls,mapping=D.recover(D.function(pre.read_text(),b['entry']),D.function(guest.read_text(),b['entry']),b['entry'],rows)
            for c in calls:
                assert c['pc']not in sites or sites[c['pc']]==c['State_offsets'];sites[c['pc']]=c['State_offsets']
            bodies[b['entry']]=dict(entry=b['entry'],callback_sites=calls,source_marker_map=mapping)
    p=out/'callbacks.json';p.write_text(json.dumps(dict(bodies=bodies,State_offsets_by_original_PC={str(k):v for k,v in sorted(sites.items())},AFTER_seed=False),indent=2)+'\n');pin(p);pin(__file__)
    report=dict(passed=True,scope='Physical source/LLVM flag callback attribution for new literal formatter bodies',bodies=len(bodies),unique_sites=len(sites),callbacks=str(p),callbacks_sha256=pins[str(p.resolve())],files=pins,native_executed=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
