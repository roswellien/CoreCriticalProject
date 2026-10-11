"""Independent light source/receipt/first-cause review; no archive reader."""
from pathlib import Path
import ast,collections,hashlib,json,sys,traceback
R=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()!='.mwb','No capture archive');v=sha(p);need(h is None or h==v,'Exact bounded review dependency '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main():
 out=R/'reports/m4-startup130-original/mixed-controls-review-r1';need(not out.exists(),'Fresh independent review');out.mkdir(parents=True);passed=False;counts=collections.Counter();reviewed=[]
 try:
  vp=R/'reports/m4-tree-review/mixed-controls-validation-r2/report.json';v=read(vp,'0d54d90ef2c01934d460d36a848c415b1753b4a2fc9cd7679e249c8844a140e3');need(v['passed']and v['reader_closed'],'Current causal reader closed')
  ep=R/'reports/m4-tree-review/mixed-controls-execution-r3/report.json';e=read(ep,'90e014b6d7018513452dfdc6d941f492e37fe45f9edfa290de259a0bbe3c2b9f');need(e['passed']and v['execution_sha256']==sha(ep),'Actual unchanged current19 writers')
  b=read(e['build_path'],'3975da7bc33a214275bf997d0bfafdf2bcc60e376dc8cadfc17223ff1f682ab9');p=read(b['preparation'],'ae501cbcb83550f33d05cac23a4114a4772a3015d133ea1be547a22d0b61488f');n=read(p['native_preparation'],'1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3');need(b['passed']and p['passed']and n['passed']and p['control_scenarios']==10 and p['control_attempts']==20 and p['actual_Runtime_selected_call'],'Actual public Runtime fixture and current library')
  need(v['build_sha256']==sha(Path(e['build_path']))and v['native_preparation_sha256']==b['native_preparation_sha256']==p['native_preparation_sha256']==sha(Path(p['native_preparation'])),'Exact immutable executed lineage')
  for q,h in b['sources'].items():pin(q,h)
  for q,h in n['files'].items():
   if Path(q).parent==Path(p['native_preparation']).parent:pin(q,h)
  for level in ('O0','O2'):need(e['workers'][level]['exit_code']==0,'Actual writer completion');pin(b['workers'][level]['path'],b['workers'][level]['sha256'])
  checker2=pin(R/'tools/m4-tree-review/check_mixed_controls_v2.py');checker1=pin(R/'tools/m4-tree-review/check_mixed_controls.py');base=pin(R/'tools/m4-tree-review/check_formatting_controls_v2.py');hw=pin(R/'tools/m4-tree-review/check_controls_v3.py');first=read(R/'reports/m4-tree-review/mixed-first-reasons-r1/report.json','0a097e693fca064f4d598fbd1ea981ff912dcb56b810b949d9dced12ac3bd3aa')
  for q in (checker2,checker1,base,hw):need(v['files'][str(q)]==sha(q),'Complete executed checker dependency pinned');ast.parse(q.read_text())
  text2=checker2.read_text();text1=checker1.read_text();textbase=base.read_text();need("reason=='Exact root and loaded-image named Lockit import projection required'and fault[1]==0x4e5389 and fault[2]==0x5bb4f4"in text2,'Only measured exact dtor import first-cause correction');need(text2.count('s=s.replace(a,b)')==2,'Exact additive first-cause hunk plus dependency pin')
  fixture=Path(b['preparation']).parent/'fixture.cpp';hooks=fixture.with_name('control_hooks.hpp');ft=pin(fixture,p['files'][str(fixture.resolve())]).read_text();ht=pin(hooks,p['files'][str(hooks.resolve())]).read_text();session=pin(Path(p['native_preparation']).parent/'session_impl.inc',n['files'][str((Path(p['native_preparation']).parent/'session_impl.inc').resolve())]).read_text()
  for fragment in ["(void)m4_onexit::write(s.token(),address,value,4)","const unsigned wanted=selected==6?87:86", "const unsigned at=(selected==6?11:6)*8",'if(selected==8){change(r,0x5bb4f4', 'change(r,head+4']:
   need(fragment in ht,'Actual public/private intervention source '+fragment)
  need('s.dump(&private_mutation,nullptr)'in ht and 'const_cast<std::byte*>(b.data())[at]^=std::byte{1}'in ht,'Private actual ledger single-bit mutation, separate from public write cases')
  need(session.index('if(r.poisoned()&&!failed)poison();')<session.index('InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();'),'Poison first occurs before cleanup authority binding, preventing stale cleared binding')
  for fragment in ['hardware(invocation_before);(void)invoke(t);hardware(invocation_after)', 'hardware(before);c.registry().finish();hardware(after)', 'data_boundary_call(&t,&before,&after,&rich)', 'sample.state_before==sample.state_after&&sample.fx_before==sample.fx_after&&sample.cpu_before==sample.cpu_after', 'need(gone,"Every actual owner guest alias unmapped by cleanup")']:
   need(fragment in ft,'Actual invocation/cleanup/retry host boundary '+fragment)
  for fragment in ['new[8:10]==(0,0)and sum(new[10:12])==1', "reason=='FS observer changed private source-frame/chain witnesses'", "reason=='Installed source FS predecessor/handler and active private frame identity'",'immediate_Context_architectural_hardware_pairs','whole_mixed_owner_backing_byteflows']:
   need(fragment in text1,'Exact executed controls predicate '+fragment)
  need('sample[768:4272]==sample[4272:7776]'in textbase and 'sample[7776:8288]==sample[8288:8800]'in textbase and 'sample[8800:8840]==sample[8840:8880]'in textbase,'Whole State3504/FX512/CPU40 same-session retry conservation')
  cp=vp.parent/'actual-causes.json';causes=read(cp,v['files'][str(cp.resolve())]);need(len(causes)==18 and {(r['level'],r['scenario'])for r in causes}=={(l,i)for l in ('O0','O2')for i in range(1,10)},'All actual eighteen first causes')
  for r in causes:
   case=r['scenario'];i=r['intervention'];PC=0x49cc95 if case in(1,2,6)else 0x4e532a if case==7 else 0x4e5360;need(r['hook_point']==(87 if case==6 else 86)and r['State_PC']==PC,'Actual precise hook witness')
   if case<=5:
    need(r['public_source_service']and i[0]==1 and i[5]and i[6]and i[7]==case and i[8]==PC and i[10]==4,'Real reentrant public source write and actual current owner generation')
    want='Mixed source scalar/pointer value derives from its exact role'if case==4 else'Mixed exact live MFC role/generation/PC/offset/width/order';need(r['reason']==want and r['fault_PC']==i[9]and r['fault_address']==i[1],'Exact current public role/value denial')
    if case==1:need(i[1]==i[2]==i[13]!=i[5],'Foreign generic allocation counterfactual')
    if case==2:need(i[1]==i[2]==i[5]+12,'Capacity-tail write beyond requested12B')
    if case==3:need(i[5]==i[12]and i[1]==i[11]+4 and i[11]!=i[12],'Distinct same24-byte header/sentinel roles')
    if case==4:need(i[1]==i[5]+4 and i[2]==i[12]==i[5]and i[4]==i[11]!=i[12],'Wrong parent source value at correct cell')
    if case==5:need(i[9]==0x4e532a and i[1]==i[5]+4 and not i[2],'Earlier header PC substituted for current sentinel')
    counts['public_source_first_causes']+=1
   elif case<=7:
    need(not r['public_source_service']and i[0]==2 and i[1]==(11 if case==6 else 6)*8 and i[2]==128 and r['reason']=='FS observer changed private source-frame/chain witnesses','Actual private generation ledger conservation first cause');counts['private_ledger_first_causes']+=1
   elif case==8:
    need(not r['public_source_service']and i[0]==4 and i[1]==0x5bb4f4 and i[3]==i[2]^4 and r['fault_PC']==0x4e5389 and r['fault_address']==0x5bb4f4 and r['reason']=='Exact root and loaded-image named Lockit import projection required','Actual late dtor source-IAT admission first cause');counts['named_IAT_first_causes']+=1
   else:need(not r['public_source_service']and i[0]==4 and i[3]==i[2]^1 and i[1]==r['fault_address']+4 and r['reason']=='Installed source FS predecessor/handler and active private frame identity','Actual complete FS handler integrity first cause');counts['FS_integrity_first_causes']+=1
   reviewed.append(r)
  expected=dict(causal_denials=18,same_session_refusals=20,registered_positive_roots=8,actual_acquisition_cleanup_joins=146,whole_retry_history_joins=960,whole_retry_page_joins=2800,immediate_Context_architectural_hardware_pairs=40,rich_caller_architectural_hardware_pairs=40,cleanup_architectural_hardware_pairs=40,positive_mixed_private16Q_access_joins=20,positive_mixed_private16Q_publication_joins=6)
  for k,value in expected.items():need(v['counts'][k]==value,'Complete executed measured controls extent '+k)
  need(v['full_caller_FX512_equality_claim']is False and all(v[k]for k in ('whole_guest_State_retry','whole_guest_CPU_retry','whole_guest_FX_retry')),'Host architectural FP vs full guest retry scope');pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  rp=out/'reviewed-causes.json';rp.write_text(json.dumps(reviewed,indent=2)+'\n');pin(rp);report=dict(passed=passed,scope='Independent bounded source/receipt and eighteen exported measured first-cause review. Full canonical raw sample checks remain the exact executed semantic gate; no second archive reader.',controls_validation_sha256=sha(vp)if'vp'in locals()else None,execution_sha256=sha(ep)if'ep'in locals()else None,native_preparation_sha256='1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3',counts=dict(counts),required_semantic_counts=locals().get('expected',{}),capture_reader_opened=False,public_source_cases=[1,2,3,4,5],private_generation_cases=[6,7],late_named_IAT_case=8,FS_handler_case=9,whole_guest_retry_bytes=[3504,40,512],full_caller_FX512_equality_claim=False,initializer_credit=0,files=PINS);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),counts=dict(counts))))
if __name__=='__main__':main()
