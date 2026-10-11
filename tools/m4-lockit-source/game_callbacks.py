"""Exact source-PC attribution of game undefined callbacks, no execution."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;need(not out.exists(),'Fresh game callback output');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen source callback input');pins[str(p)]=v;return p
 p=pin(ROOT/'tools/m4-crt-locale-batch-recovery/callbacks.py');sp=importlib.util.spec_from_file_location('onexit_game_callback_decoder',p);C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C)
 code=p.read_text().replace('offset in (2065,2067,2069,2071,2073,2077)', 'offset in (2065,2067,2069,2071,2073,2077,2737,2739,2741,2743,2745,2747,2749,2751,2753,2755,2757)')
 need(code!=p.read_text(),'Explicit x87 callback attribution extension');exec(compile(code,str(p),'exec'),C.__dict__)
 lift=ROOT/'reports/m4-lockit-source/lifts-r1';d=json.loads(pin(lift/'report.json','044316594ce299d04ff9e3aac5bd3bbc157c5ed758f7693db0238c1d727dcb0d').read_bytes())
 interface=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json').read_bytes());rows={r['pc']:r for r in interface['instructions']}
 bodies={};sites={}
 for n,b in d['source_bodies'].items():
  pre=pin(lift/(n+'-pre.ll'));guest=pin(lift/(n+'-baseline.ll'));pin(lift/(n+'-host.ll'),b['host_sha256'])
  calls,mapping=C.recover(C.function(pre.read_text(),b['entry']),C.function(guest.read_text(),b['entry']),b['entry'],rows)
  for c in calls:
   pc=c['pc'];value=c['State_offsets'];need(pc not in sites or sites[pc]==value,'One exact callback order per original PC');sites[pc]=value
  bodies[n]=dict(entry=b['entry'],callback_sites=calls,source_marker_map=mapping)
 out.mkdir(parents=True);payload=dict(schema='mw34-onexit-game-original-callbacks-v1',bodies=bodies,State_offsets_by_original_PC={str(p):v for p,v in sorted(sites.items())},AFTER_seed=False)
 (out/'callbacks.json').write_text(json.dumps(payload,indent=2)+'\n');pin(out/'callbacks.json');pin(__file__)
 report=dict(passed=True,scope='Exact source/LLVM undefined flag attribution; no execution',bodies=len(bodies),unique_sites=len(sites),callbacks_sha256=sha(out/'callbacks.json'),files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),callbacks_sha256=sha(out/'callbacks.json'),sites=len(sites))))
if __name__=='__main__':main(sys.argv[1])
