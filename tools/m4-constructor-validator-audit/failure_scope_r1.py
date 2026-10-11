"""Small source-only exact additive constructor failure cleanup audit."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]

def need(v,m):
    if not v:raise ValueError(m)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def method(text,name):
    match=re.search(r'^ void '+re.escape(name)+r'\(',text,re.M);need(match is not None,'One private method definition '+name)
    begin=match.start();brace=text.index('{',match.end());depth=1;i=brace+1
    while depth:
        if text[i]=='{':depth+=1
        elif text[i]=='}':depth-=1
        i+=1
    return text[begin:i]

def main(name,service_name,service_sha,component_name,component_sha):
    out=ROOT/'reports/m4-constructor-validator-audit'/name;need(not out.exists(),'Fresh additive failure source audit');out.mkdir(parents=True);pins={}
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip')and p.name not in('payload.bin','index.json','transport.json'),'No archive/capture/raw reader')
        actual=sha(p);need(h is None or actual==h,'Exact frozen input '+str(p));pins[str(p)]=actual;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    service_path=ROOT/'reports/m4-constructor-native'/service_name/'report.json';component_path=ROOT/'reports/m4-constructor-native'/component_name/'report.json'
    service_report=read(service_path,service_sha);component_report=read(component_path,component_sha)
    need(service_report['passed']and component_report['passed'],'Current prepared sources identified; preparation passed is not compile success')
    def saved(report,path):return pin(path,report['files'][str(Path(path).resolve())]).read_text()
    impl_path=service_path.parent/'session_impl.inc';impl=saved(service_report,impl_path);header_path=service_path.parent/'session.hpp';header=saved(service_report,header_path)
    current_component_path=component_path.parent/'component.cpp';component=saved(component_report,current_component_path)
    timing_path=ROOT/'reports/m4-constructor-native/store-timing-all-r1/report.json';timing=read(timing_path,'1a15354021d7f68f2f6bee48b8502b63de64d7c2a0882db8cea0834f3d83c968')
    prior_tool_path=ROOT/'tools/m4-constructor-native/borrowed_constructor_v2.inc';prior=saved(timing,prior_tool_path)
    prior_component_path=ROOT/'tools/m4-constructor-native/component_v2.cpp';prior_component=saved(timing,prior_component_path)
    clear=method(impl,'clear_constructor_scope');abort=method(impl,'abort_constructor');poison=method(impl,'poison')
    need(clear==' void clear_constructor_scope()noexcept{constructor_active_root_=0;constructor_prior_root_=0;constructor_prior_read_={};++constructor_access_epoch_;}','Exact private four-field clear; no State/FX/memory access or operation')
    need('r.memory()'not in clear+abort and 'std::memcpy'not in clear+abort and 's.gpr.'not in clear+abort and 'r.fx()'not in clear+abort,'Failure clear/abort have no source CPU/FX or memory effects')
    owner_seam=' ConstructorOwner constructor_owner(unsigned guest,unsigned bytes){'
    addition=clear+'\n'+abort+'\n'
    expected_prior=prior.replace(owner_seam,addition+owner_seam,1)
    need(expected_prior.strip()in impl,'Entire previous reviewed constructor source preserved plus only exact clear/abort definitions')
    need(poison.count('clear_constructor_scope();')==1 and 'clear_constructor_scope();failed=true;'in poison,'Every normal poison completion clears constructor metadata before prior failed/pause machinery')
    old_poison=poison.replace('clear_constructor_scope();failed=true;','failed=true;',1)
    old_service_report=read(ROOT/'reports/m4-constructor-native/service-preparation-r2/report.json','38f27c0876542bc6bcdf881fa838b015309e41dcc0cbe916df1a39c13a4c8a51')
    old_impl_path=ROOT/'reports/m4-constructor-native/service-preparation-r2/session_impl.inc';old_impl=saved(old_service_report,old_impl_path)
    need(old_poison==method(old_impl,'poison'),'Inherited poison first-exception diagnosis/pause preserved exactly plus one clear call')
    old_catch='catch(...){t.owner->failed=true;t.exception=std::current_exception();}'
    new_catch='catch(...){const auto first=std::current_exception();t.owner->session.abort_constructor(t.owner->s,t.root);t.owner->active=false;t.owner->failed=true;t.exception=first;}'
    need(component==prior_component.replace(old_catch,new_catch,1)and prior_component.count(old_catch)==1,'Entire Component preserved plus exactly catch: retain first exception, abort private scope, mark inactive/failed, return original exception')
    need(' void abort_constructor(State&,unsigned root)noexcept;'in header and 'void Session::abort_constructor(State&s,unsigned root)noexcept{impl_->abort_constructor(s,root);}'in impl,'Public no-throw forwarding reaches exact private guard')
    need('std::thread::id thread=std::this_thread::get_id()'in impl,'Actual owning service thread has std::thread::id type')
    predicates=['&&&source==&s','&&constructor_root(root)','&&r.cpu().eip==root','&&(!constructor_active_root_||constructor_active_root_==root)']
    need(all(p in abort for p in predicates)and 'else failed=true;'in abort,'Same source/root/outer Runtime and balanced active-root authority, authority mismatch poisons private failure flag')
    findings=[];thread_correct='std::this_thread::get_id()==thread'in abort
    if not thread_correct:
        need('GetCurrentThreadId()==thread'in abort,'Concrete alternative thread comparison identified')
        line=impl[:impl.index('GetCurrentThreadId()==thread',impl.index(' void abort_constructor'))].count('\n')+1
        findings.append(dict(priority=1,kind='Compile-time thread identity type mismatch',path=str(impl_path.resolve()),line=line,actual='GetCurrentThreadId() returns DWORD; SessionImpl::thread is std::thread::id',required='std::this_thread::get_id()==thread',whole_state_memory_cleanup_semantics_otherwise_preserved=True))
    facts=dict(private_clear=clear,abort=abort,poison=poison,component_catch=new_catch,exact_previous_constructor_body_preserved=True,entire_Component_only_catch_changed=True,original_exception_identity_preserved=True,private_active_prior_epoch_only=True,source_State_effects=False,source_FX_effects=False,source_memory_effects=False,thread_authority_type_correct=thread_correct,source_root_outer_Runtime_and_scope_authority=True,prior_READ_epoch_clear_on_poison=True,prior_READ_epoch_clear_on_guarded_failure=thread_correct,positive_scope_timing_audit_preserved=True)
    p=out/'contracts.json';p.write_text(json.dumps(facts,indent=2)+'\n');pin(p);pin(__file__)
    for path,h in list(pins.items()):pin(path,h)
    report=dict(passed=not findings,scope='Independent exact additive failure-scope source audit; compile-time type validity and private-only clear/abort/poison/first-exception paths. No compiler, worker, capture reader, State/memory mutation or execution.',service_preparation=str(service_path.resolve()),service_preparation_sha256=service_sha,Component_preparation=str(component_path.resolve()),Component_preparation_sha256=component_sha,contracts_path=str(p.resolve()),contracts_sha256=sha(p),findings=findings,thread_authority_type_correct=thread_correct,failure_scope_source_cleanup_closed=not findings,compiler_executed=False,worker_executed=False,capture_reader_opened=False,payload_reader_opened=False,initializer_credit=0,files=pins)
    path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],report_sha256=sha(path),contracts_sha256=sha(p),findings=findings)))

if __name__=='__main__':main(*sys.argv[1:])
