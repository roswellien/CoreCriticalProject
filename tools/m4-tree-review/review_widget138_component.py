"""Independent seven-root source permutation and new fault-cleanup boundary."""
from pathlib import Path
import collections,hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir();pins={};counts=collections.Counter()
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.zip','.mwb');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=R/'reports/m4-fps-native/component-preparation-r1';new=R/'reports/m4-fps-native/connected-component-preparation-r1'
 p=read(new/'report.json','17bce5443a2253a4af59c258ef54ea0f457deb0bf0b576d737c580d20a9472ae')
 b=read(R/'reports/m4-fps-native/connected-component-build-r1/build.json','602f8a769f74c3883c4bcfe08fbc384c844125f0130c6f2cc184fb41f1670c99')
 assert p['passed']and b['passed']and b['preparation_sha256']=='17bce5443a2253a4af59c258ef54ea0f457deb0bf0b576d737c580d20a9472ae'
 for report in(p,b):
  for path,h in report['files'].items():pin(path,h)
 before=pin(old/'literals.hpp').read_text();after=pin(new/'literals.hpp').read_text()
 marker='inline constexpr Root roots[]'
 assert marker in before and marker in after
 pre,rest=before.split(marker,1);body,post=rest.split('};',1)
 apre,arest=after.split(marker,1);abody,apost=arest.split('};',1)
 assert pre==apre and post==apost
 rows=re.findall(r'\{([0-9,]+)\}',body);arows=re.findall(r'\{([0-9,]+)\}',abody)
 assert len(rows)==len(arows)==7 and arows==sorted(rows,key=lambda x:int(x.split(',')[1]))
 assert set(arows)==set(rows);counts['whole_retained_root_headers_and_slices']=7
 slots=[int(row.split(',')[1])for row in arows]
 assert slots==[0x5e0048,0x5e004c,0x5e0050,0x5e00cc,0x5e0234,0x5e0238,0x5e023c]
 for row in p['copied_generated_files']:
  if row['name']in('component.cpp','component.hpp','contracts.json','literals.hpp'):continue
  assert pin(row['source'],row['source_sha256']).read_bytes()==pin(row['target'],row['current_sha256']).read_bytes()
  counts['whole_unchanged_generated_inputs']+=1
 cpp=pin(old/'component.cpp').read_text();current=pin(new/'component.cpp').read_text()
 old_cleanup='void cleanup(){authority();require((!active||failed)&&!cleaned,"Serial explicit owned-font cleanup");'
 new_cleanup='void cleanup(){require(current==this&&GetCurrentThreadId()==thread&&&services.runtime()==&r,"Current owned widget cleanup thread/Runtime");services.cleanup_authority();require((!active||failed)&&!cleaned&&(!r.poisoned()||failed),"Serial explicit owned-font cleanup after Context fault mark");'
 assert cpp.count(old_cleanup)==1;cpp=cpp.replace(old_cleanup,new_cleanup)
 anchor='void Component::authority(){impl_->authority();}'
 insert='\nvoid Component::context_fault(){require(current==impl_.get()&&GetCurrentThreadId()==impl_->thread,"Actual carried Context fault owner");impl_->failed=true;}'
 assert cpp.count(anchor)==1;cpp=cpp.replace(anchor,anchor+insert)
 old_entry='current->invoke(root);}'
 new_entry='try{current->invoke(root);}catch(...){current->failed=true;throw;}}'
 assert cpp.count(old_entry)==1;cpp=cpp.replace(old_entry,new_entry)
 assert cpp==current,'Only exact cleanup authority, fault marker and callback catch change'
 header=pin(old/'component.hpp').read_text()
 for before,after in [
 ('  virtual void authority() = 0;','  virtual void authority() = 0;\n  // Manual owned-font cleanup may follow the same Context fault; no source API.\n  virtual void cleanup_authority() { authority(); }'),
 ('  void authority();','  void authority();\n  // Called by the owning connected Context before any post-fault font cleanup.\n  void context_fault();')]:
  assert header.count(before)==1;header=header.replace(before,after)
 assert header==pin(new/'component.hpp').read_text()
 # This admission deliberately leaves the new actual Context lifetime proof open.
 assert p['current_fault_evidence_pending']and not p['connected_equivalence']
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Independent complete unchanged causal slice arrays/58 literal IRs and exact sorted seven-root headers, explicit source callback failure/cleanup authority delta; no current linked Context or runtime admission',preparation_sha256='17bce5443a2253a4af59c258ef54ea0f457deb0bf0b576d737c580d20a9472ae',build_sha256='602f8a769f74c3883c4bcfe08fbc384c844125f0130c6f2cc184fb41f1670c99',counts=dict(counts),actual_workers_launched=0,archive_reader_opened=False,current_Context_fault_lifecycle_proof_pending=True,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=dict(counts),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])

