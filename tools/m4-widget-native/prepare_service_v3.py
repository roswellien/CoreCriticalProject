"""Admit live producer bytes before literal onexit measures its heap capacity."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def main():
 out=(R/sys.argv[1]).resolve();need(not out.exists(),'Fresh corrected widget service preparation');out.mkdir(parents=True);pins={};relations=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact physical service input '+str(p));pins[str(p)]=v;return p
 parent=pin(R/'reports/m4-widget-native/service-preparation-r2/report.json','d10b800a817dd3fc684f276d5df19154748b2b0735137d062d9bff05376a1fca');p=json.loads(parent.read_bytes());need(p['passed'],'Frozen prior borrowed service')
 for old in parent.parent.iterdir():
  if not old.is_file() or old.name=='report.json':continue
  pin(old,p['files'][str(old.resolve())]);q=out/old.name;shutil.copyfile(old,q);relations.append(dict(parent=str(old),child=str(q),parent_sha256=sha(old)))
 add=pin(R/'tools/m4-widget-native/borrowed_onexit_v2.inc');text=add.read_text()
 old='require(allocation&&allocation->guest==begin&&allocation->native&&allocation->mapped&&next>=begin&&std::uint64_t(next)+4<=std::uint64_t(begin)+allocation->capacity,"Current owned source producer callback capacity");'
 new='require(allocation&&allocation->guest==begin&&allocation->native&&allocation->mapped&&!allocation->pending&&next>=begin&&std::uint64_t(next)+4<=std::uint64_t(begin)+allocation->extent,"Current live producer full-byte extent before literal msize");'
 need(text.count(old)==1,'One exact premature measured-capacity guard');text=text.replace(old,new)
 old='require(r.memory().load<unsigned>({0x7803788c})==begin&&r.memory().load<unsigned>({0x78037888})==next+4&&r.memory().load<unsigned>({next})==callback,"Actual source-owned registry publication and complete capacity carry");'
 new='require(binding->allocation_for(begin)==allocation&&allocation->native&&allocation->mapped&&!allocation->pending&&allocation->capacity&&allocation->extent==allocation->capacity&&std::uint64_t(next)+4<=std::uint64_t(begin)+allocation->capacity&&r.memory().load<unsigned>({0x7803788c})==begin&&r.memory().load<unsigned>({0x78037888})==next+4&&r.memory().load<unsigned>({next})==callback,"Actual literal msize capacity and source-owned registry publication");'
 need(text.count(old)==1,'One source-provider publication guard');text=text.replace(old,new)
 original=text;implementation=out/'session_impl.inc';before=implementation.read_text();prior=add.read_text();need(before.count(prior)==1,'Exactly one whole borrowed service body');implementation.write_text(before.replace(prior,text))
 proof=out/'borrowed-service-correction.json';proof.write_text(json.dumps(dict(prior_body_sha256=sha(add),changed_guards=2,precondition='Actual live owned HeapAlloc extent and callback bytes; no claimed unmeasured capacity',postcondition='Literal provider HeapSize has measured capacity; exact same owner publication fits that actual capacity',no_extra_API_call=True,no_numerical_or_AFTER_seed=True),indent=2)+'\n')
 for row in relations:row['child_sha256']=sha(row['child']);row['unchanged']=row['parent_sha256']==row['child_sha256'];pin(row['child'])
 need([Path(q['child']).name for q in relations if not q['unchanged']]==['session_impl.inc'],'Only the exact two guards changed in one implementation')
 pin(proof);pin(__file__)
 report=dict(passed=True,scope='Additive pre-HeapSize service admission correction; complete live extent before original onexit and actual measured capacity after literal provider, no execution credit',parent_preparation=str(parent),parent_preparation_sha256=sha(parent),native_library=str(out/'registry_library.cpp'),native_include=str(out),source_relations=relations,copied_files=len(relations),unchanged_files=sum(q['unchanged']for q in relations),changed_files=['session_impl.inc'],roots=p['roots'],source_callbacks=p['source_callbacks'],service=p['service'],files=pins,native_executed=False,initializer_credit=0,host_onexit_or_noop_substitution=False,extra_provider_API_calls=0,premature_capacity_requirement_removed=True,actual_literal_msize_capacity_required_after_provider=True)
 f=out/'report.json';f.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(f),sha256=sha(f))))
if __name__=='__main__':main()
