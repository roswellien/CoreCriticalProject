"""Fresh connected public-control candidate, derived from frozen strong5."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(t,a,b):assert t.count(a)==1,(a,t.count(a));return t.replace(a,b)
def main(name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};generated={};parent={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;(str(p)not in pins or pins[str(p)]==v)or(_ for _ in()).throw(ValueError('Stable input'));pins[str(p)]=v;return p
 def write(p,b):p.write_bytes(b if isinstance(b,bytes)else b.encode());generated[str(p.resolve())]=sha(p);pin(p)
 try:
  pp=pin(R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5/report.json','a7985e57a3a437fe6b19a600507ebeac33dac79ea0bae825b35133095f3f8924');parent=json.loads(pp.read_bytes());assert parent['passed']
  for p,h in parent['files'].items():pin(p,h)
  for key,digest in [('connected-source-r4','a22b94ca3a5ccf6f1fb57bbe40b03ee97ac8d7770f991a2cb80b3cecf354d30d'),('connected-resources-r1','abd7b109aa55654766e0a77ae0f2ffda8118c0a8f5388c9a88792dd49b714885')]:assert json.loads(pin(R/'reports/m4-mfc1168-native'/key/'report.json',digest).read_bytes())['passed']
  for p in pp.parent.rglob('*'):
   if p.is_file()and p.name!='report.json':q=out/p.relative_to(pp.parent);q.parent.mkdir(parents=True,exist_ok=True);write(q,pin(p).read_bytes().replace(pp.parent.as_posix().encode(),out.as_posix().encode()))
  text=(out/'native_main.cpp').read_text();text=one(text,' unsigned completed{};',' bool has_component()const noexcept{return bool(mfc_component_);}\n void control_checkpoint(std::string_view name){if(mfc_component_)mfc_component_->checkpoint(name);}\n void control_cleanup(){if(mfc_component_)mfc_component_->cleanup_failed();}\n unsigned completed{};')
  text=one(text,'std::vector<mw34::m4_mixed::Native>*records;bool completed;','std::vector<mw34::m4_mixed::Native>*records;bool completed,retry;')
  text=one(text,'p->completed=p->context->invoke_selected_table(p->sequence,p->repeat,p->top,*p->records);','if(p->retry){try{p->context->runtime().call_direct({mc::root},{mw34::m4_mixed::broker});p->completed=false;}catch(const mw34::m4_runtime::Fault&e){p->completed=e.reason()==mw34::m4_runtime::FaultReason::poisoned;}}else p->completed=p->context->invoke_selected_table(p->sequence,p->repeat,p->top,*p->records);')
  text=text[:text.index('int main(int argc,char**argv)')]+ '\n#include "connected_literals.hpp"\n#include "connected_controls.inc"\n';write(out/'native_main.cpp',text);write(out/'connected_controls.inc',pin(R/'tools/m4-mfc1168-native/connected_controls.inc').read_bytes())
  pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(parent);report.update(passed=passed,scope='Unexecuted candidate12 connected phase13 public denials, complete source component private/caller conservation and actual native cleanup',parent_positive_preparation=str(R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5/report.json'),control_cases=12,generated_sources=generated,files=pins,worker_executed=False,execution_admitted=False,initializer_credit=0,retry_entire_Runtime_hidden_private_claim=False,old_registry_private_vectors_retry_claim=False,full_memory_permission_snapshot_claim=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
