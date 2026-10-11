"""Finite native15-to19 extension review; historical fault observations stay historical."""
from pathlib import Path
import difflib,hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(current_controls,current_sha,name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh finite formatter applicability review');out.mkdir(parents=True);pins={};relations=[]
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix not in('.mwb','.zip'),'No archive reader');a=sha(p);need(h is None or a==h,'Exact finite extension identity '+str(p));pins[str(p)]=a;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 oldpath=R/'reports/m4-formatting-native/preparation-r15/report.json';newpath=R/'reports/m4-formatting-native/preparation-r19/report.json'
 old=read(oldpath,'bbe18a53a6c8c400f3274e470a28ded84d7c7c45c4fc860cf5e598ed4d5730aa');new=read(newpath,'1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')
 historical_path=R/'reports/m4-tree-review/formatting-controls-validation-r2/report.json'
 historical=read(historical_path,'a6f755471aec327792ffc9e379cc0ba8001b7e02f0416cc47e99acbda073933c')
 independent=read(R/'reports/m4-formatting-original/controls-review-r2/report.json','1fb9d64a7c50f75a1391f3d3b7bdc19c8e57be783f1e7309fd060d4e9276662f')
 controls=read(current_controls,current_sha);need(controls['passed'] and controls['native_preparation_sha256']==sha(newpath),'Fresh current19 actual mixed control proof')
 need(historical['passed'] and independent['passed'] and historical['counts']['causal_denials']==26 and historical['counts']['same_session_refusals']==28,'Exact historical native15 fault observations')
 need(controls['counts']['causal_denials']==18 and controls['counts']['same_session_refusals']==20 and controls['counts']['registered_positive_roots']==8 and controls['reader_closed'],'Both current19 four-root positives, faults, full retries and cleanup')
 equivalent=read(R/'reports/m4-tree-review/mixed-final-equivalence-r1/report.json','ec3533c584a0fded0d838a666ddc0598d236f09a24af4ea9e730bc1bf6b898c7');need(equivalent['passed'] and equivalent['whole_library_COFF_non_timestamp_equal'],'Current19 control and broad130 actual linked library identical outside timestamp')
 cleanup=read(R/'reports/m4-tree-review/cleanup19-r2/report.json','ba43095f791a7e16d2e747e2c1f3d414e15d29744588b91509fb1ee7122b4afb')
 od,nd=Path(old['native_include']),Path(new['native_include'])
 of={Path(p).name:(p,h)for p,h in old['files'].items()if Path(p).parent==od};nf={Path(p).name:(p,h)for p,h in new['files'].items()if Path(p).parent==nd}
 need(len(of)==67 and len(nf)==71 and set(of)<set(nf),'Complete actual frozen source inventories')
 for p,h in list(of.values())+list(nf.values()):pin(p,h)
 changed={n for n in of if Path(of[n][0]).read_bytes()!=Path(nf[n][0]).read_bytes()}
 expected={'locale_batch_operations.inc','lockit_contract.inc','formatting_contract.inc','session_impl.inc','registry_library.cpp','formatting_operations.inc','tree_contract.inc','fs_contract.inc','locale_batch.hpp'}
 need(changed==expected,'Exactly nine changed common source files, no unreviewed common mutation')
 diffs=[]
 for n in sorted(of):
  a,b=Path(of[n][0]).read_bytes(),Path(nf[n][0]).read_bytes();relations.append(dict(name=n,old_sha256=sha(of[n][0]),new_sha256=sha(nf[n][0]),byte_identical=a==b))
  if a!=b:diffs.extend(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),of[n][0],nf[n][0]))
 def text(n,branch='old'):return Path((of if branch=='old'else nf)[n][0]).read_text()
 # The only two operation deltas are a filter for newly nested MFC malloc
 # returns and admitting a fourth formatter. On the three old roots every
 # genuine pending malloc has the exact frame, so the new filter is false.
 a=text('formatting_operations.inc');b=text('formatting_operations.inc','new')
 filter_line=' if(entry==malloc_entry&&std::none_of(formatting_calls_.begin(),formatting_calls_.end(),[&](const auto&w){return w[1]==registry_root_&&w[3]==entry&&w[4]==frame&&!w[14];}))return;\n'
 need(b.count(filter_line)==1 and b.replace(filter_line,'').replace('formatting_completed_>=4','formatting_completed_>=3')==a,'Complete formatter operation delta is exact pending-frame filter and3-to4 bound')
 need('frame!=formatting_base_+spec->frame_offset' in a and '(*it)[4]!=frame||state.gpr.rsp.dword!=frame+4' in a and 'formatting_calls_.push_back(row)' in a,'Unchanged old exact CALL frame creates pending row consumed by RET')
 def array(s,n):return s.split(n+'[]{',1)[1].split('\n};',1)[0]
 ac,bc=text('formatting_contract.inc'),text('formatting_contract.inc','new')
 for n in('formatting_instructions','formatting_spans','formatting_imports'):
  need(array(ac,n)==array(bc,n),'Complete old literal instruction/span/import table preserved '+n)
 roots=array(ac,'formatting_roots').splitlines();newroots=array(bc,'formatting_roots').splitlines();owned=array(ac,'formatting_owned_order').splitlines();newowned=array(bc,'formatting_owned_order').splitlines()
 need(newroots[:-1]==roots and newroots[-1]=='{5119136,6338152,6338156,6199260,11,33,12},','Three whole original formatting roles retain exact source contracts; one precise fourth role')
 need(newowned[:len(owned)]==owned and len(newowned)-len(owned)==12,'All33 old exact causal owner operations preserved; only12 fourth-root operands appended')
 normalized=bc.replace('\n'+newroots[-1],'',1)
 for line in newowned[len(owned):]:
  # Remove the appended block as a block, because byte-value lines can recur.
  pass
 normalized=normalized.replace('\n'+'\n'.join(newowned[len(owned):]),'',1)
 for n in('instruction','source_spans','registration_callback','has_body','dispatch_body','generated_undefined_sites'):
  normalized=re.sub(r'\baccepted128_'+n+r'\b',n,normalized)
 need(normalized==ac,'Entire old formatter contract retained after exact fourth-role/operand addition and delegated naming')
 tree_old,tree_new=text('tree_contract.inc'),text('tree_contract.inc','new')
 need(tree_new.replace('accepted128_mfc_root_input','mfc_root_input')==tree_old,'Whole old tree contract only delegated helper rename')
 h_old,h_new=text('locale_batch.hpp'),text('locale_batch.hpp','new')
 extra='void mixed_format_enter();void mixed_format_owner_before(unsigned,std::uint64_t,unsigned,bool);void mixed_format_called(unsigned,unsigned,unsigned);void mixed_format_returned(unsigned);'
 need(h_new.count(extra)==1 and h_new.replace(extra,'')==h_old,'Entire class data layout/private history unchanged; only new member declarations')
 ops_old,ops_new=text('locale_batch_operations.inc'),text('locale_batch_operations.inc','new')
 normalized=ops_new.replace('live_allocations()>92','live_allocations()>88').replace('mixed_format_owner_before(a,0,n,false);','').replace('mixed_format_owner_before(a,v,n,true);','').replace('mixed_format_called(target,w.pc,w.address);','').replace('mixed_format_returned(f.entry);','').replace('\n#include "mixed_format_operations.inc"\n','')
 need(normalized==ops_old,'Whole existing memory/call/return guard chronology preserved with four root-filtered hooks and finite88-to92 bound')
 session_old,session_new=text('session_impl.inc'),text('session_impl.inc','new')
 need(session_new.replace('binding->mixed_format_enter();','').replace('  if(r.poisoned()&&!failed)poison();\n','')==session_old,'Only mixed entry and independently reviewed firstfault cleanup transition change session')
 need(cleanup['passed'] and session_new.index('if(r.poisoned()&&!failed)poison();')<session_new.index('InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();lb::admitted_binding=binding.get();',session_new.index(' void finish')),'Changed cleanup publishes current binding after poison transition')
 for name,count,prefixes in [('fs_contract.inc',15,{5119136,5120400,5132944}),('lockit_contract.inc',1,{5119136})]:
  a,b=text(name).splitlines(),text(name,'new').splitlines();inserted=[]
  for tag,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():
   need(tag in('equal','insert'),'Only additive literal '+name+' rows');inserted.extend(b[k:l]if tag=='insert'else [])
  need(len(inserted)==count and all(int(re.match(r'\{(\d+),',v).group(1))in prefixes for v in inserted),'Every appended static row belongs exactly to fourth mixed domain')
 cpp_old,cpp_new=text('registry_library.cpp'),text('registry_library.cpp','new')
 need(cpp_new.replace('#include "mixed_format_contract.inc"\n','').startswith(cpp_old),'Whole existing library translation unit preserved before exact new tail bridges')
 tail=cpp_new.replace('#include "mixed_format_contract.inc"\n','')[len(cpp_old):]
 functions=re.findall(r'extern "C" .*?\{(.*?)\}',tail)
 need(len(functions)==8 and sum(v=='return mw34::m4_onexit::called(p,s,a);'for v in functions)==5 and sum(v=='return mw34::m4_onexit::undefined();'for v in functions)==3,'Only five literal direct-call and three undefined-byte bridges appended')
 mixed=pin(nd/'mixed_format_operations.inc',new['files'][str((nd/'mixed_format_operations.inc').resolve())]).read_text()
 for method in('mixed_format_enter','mixed_format_owner_before','mixed_format_called'):
  body=mixed.split('void Binding::'+method+'(',1)[1].split('\n}',1)[0];need('if(registry_root_!=mixed_format_root)return;'in body,'Each inserted hook stutters on three original formatter roots '+method)
 need('if(registry_root_!=mixed_format_root||entry!=mixed_format_root)return;'in mixed,'Mixed root RET hook also stutters on old three roots')
 # All actual historical first reasons still occur in the exact unchanged old
 # operand/private/dispatch/permission/FX/frame predicates, rather than being
 # relabeled as new current observations.
 cp=historical_path.parent/'actual-causes.json';causes=read(cp,historical['files'][str(cp.resolve())]if str(cp.resolve())in historical['files']else None);need(len(causes)==26,'Whole historical actual cause inventory')
 current_text='\n'.join(text(n,'new')for n in nf if n.endswith(('.cpp','.inc','.hpp')))
 for case in causes:need(case['reason']in current_text,'Each actual historical first predicate is present in current physical source')
 oldbuild=read(R/'reports/m4-tree-review/formatting-controls-build-r1/build.json','7e9e62058ae0a749714c39b580bade5f3063c447e2e9b6997a873f255189c790');oldprep=read(oldbuild['preparation'],oldbuild['preparation_sha256'])
 finalbuild=read(R/'reports/m4-joint-startup130/build-r2/build.json','1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53');finalprep=read(finalbuild['preparation'],finalbuild['preparation_sha256'])
 for level in('O0','O2'):
  oldobjects=oldprep['objects'][level];newobjects=finalprep['objects'][level];need(len(oldobjects)==390 and len(newobjects)==397 and set(oldobjects)<set(newobjects),'Every historical literal input retained by full current family')
  for p in oldobjects:pin(p,oldbuild['sources'][str(Path(p).resolve())]);need(finalbuild['sources'][str(Path(p).resolve())]==sha(p),'Same actual old literal object identity in broad130')
 diff=out/'finite-extension.diff';diff.write_text(''.join(diffs));pin(diff);pin(__file__)
 report=dict(passed=True,scope='Exact finite source/contract extension applicability from historical formatter3 native15 faults to current native19; historical26 faults are not claimed rerun in final130. Current mixed19 actual four-root fault/cleanup/retry proof is separate and bound',historical_controls_sha256=sha(historical_path),current_native_preparation_sha256=sha(newpath),current_mixed_controls_sha256=current_sha,controls_equivalence_sha256=sha(R/'reports/m4-tree-review/mixed-final-equivalence-r1/report.json'),counts=dict(common_native_files=67,whole_byte_identical_common_files=58,enumerated_changed_common_files=9,new_mixed_files=4,preserved_formatter_roles=3,preserved_ordered_formatter_operands=33,preserved_historical_literal_COFFs_per_level=390,historical_actual_fault_rows=26,current_actual_mixed_faults=18,current_actual_same_session_retries=20,current_actual_positive_registered_roots=8),whole_source_relations=relations,whole_historical_actual_faults_rerun_in_current_library=False,old_predicates_preserved_in_finite_domain=True,changed_shared_cleanup_observed_in_current_controls=True,nested_MFC_malloc_filter_scope='New unmatched malloc RETs stutter; old three roots retain exact pending CALL row with actual frame before genuine RET',formatter_completed_bound_scope='3 to4 only admits additional fourth root; old three active completions0..2 unchanged',owner_bound_scope='88 to92 finite fourth-root extension, historical focused faults have fewer live owners',capture_payload_read=False,whole_library_15_to19_COFF_equal_claim=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),counts=report['counts'])))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
