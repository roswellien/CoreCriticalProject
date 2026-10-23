"""Whole literal sorter pre/guest marker and undefined flag source attribution."""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-loader-message-review/literal-sorter-callbacks-r1';need(not out.exists(),'Fresh literal source attribution');out.mkdir(parents=True);pins={};passed=False;results={};sites={};maps=set()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical callback input');pins[str(p)]=v;return p
 try:
  path=pin(R/'reports/m4-loader-message-review/literal-sorter-helper-lifts-r2/report.json','79ab43a6998939990dd2683f708a548833f32c7bf30bf3ffa4a7646ca46d8352');lift=json.loads(path.read_bytes());need(lift['passed']and set(lift['bodies'])=={'f_10001000','f_10001740'},'Whole literal sorter compiled2-function closure')
  for p,h in lift['files'].items():pin(p,h)
  p=pin(R/'tools/m4-crt-locale-batch-recovery/callbacks.py');spec=importlib.util.spec_from_file_location('message_literal_callback_decoder',p);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
  rows={r['pc']:r for r in json.loads(pin(R/'reports/m4-loader-message-review/literal-sorter-evaluation-r4/source-program.json').read_bytes())['rows']}
  for key,b in lift['bodies'].items():
   folder=Path(b['objects']['O0']['path']).parent;pre=pin(folder/(key+'-pre.ll'));guest=pin(folder/(key+'-guest.ll'));host=pin(folder/(key+'-host.ll'),b['host_sha256']);calls,mapping=D.recover(D.function(pre.read_text(),b['entry']),D.function(guest.read_text(),b['entry']),b['entry'],rows)
   actual={m['pc']for m in mapping};need(actual==set(b['physical_PCs']),'Every physical function source PC represented in literal IR');maps.update(actual)
   for call in calls:
    need(call['pc']not in sites,'Unique whole source undefined callback ownership');sites[call['pc']]=call['State_offsets'];need(set(call['State_offsets'])<={2069,2077},'Only architectural AF/OF undefined sites')
   results[key]=dict(entry=b['entry'],whole_instruction_marker_rows=len(mapping),callbacks=calls,source_marker_map=mapping,host_sha256=b['host_sha256'],objects=b['objects'])
  need(maps==set(rows)and len(maps)==952,'Entire952 physical/IR source closure')
  p=out/'callbacks.json';p.write_text(json.dumps(dict(bodies=results,State_offsets_by_original_PC={str(k):v for k,v in sorted(sites.items())}),indent=2)+'\n');pin(p);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Whole physical/pre-IR/guest-IR sorter marker and undefined flag attribution; no host execution/link/provider equivalence',whole_source_PCs=len(maps),unique_callback_sites=len(sites),callback_scalar_calls=sum(len(v)for v in sites.values()),native_executed=False,DLL_loaded=False,archive_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),source_PCs=len(maps),callback_sites=len(sites))))
if __name__=='__main__':main()
