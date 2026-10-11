"""Independent bounded source/provider131 physical identity and seam review."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
sys.path.insert(0,str(R/'tools/m4-lockit-review'))
from provider_exports import Exports,exported,identity
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Physical bounded provider input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical input');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def output(r,p,name):
 q=p.parent/name;return read(q,r['files'][str(q.resolve())])
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh bounded provider/source review');out.mkdir(parents=True);passed=False;counts=collections.Counter();proof_rows=[]
 try:
  p=Path(sys.argv[2]).resolve();r=read(p,sys.argv[3]);closure=read(Path(sys.argv[4]).resolve(),sys.argv[5])
  need(r['passed']and r['reader_closed']and closure['passed']and closure['source_provider_sha256']==sha(p),'Current complete source/provider proof and independent actual input/closure gates')
  lineage=r['executed_lineage'];e=read(lineage['execution'],'e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57');b=read(lineage['build'],lineage['build_sha256']);j=read(lineage['joint_preparation'],lineage['joint_preparation_sha256']);n=read(lineage['inherited_native_preparation'],lineage['inherited_native_preparation_sha256']);need(all(x['passed']for x in(e,b,j,n))and b['preparation_sha256']==lineage['joint_preparation_sha256']and e['build_sha256']==lineage['build_sha256']and sha(Path(j['native_library']).parent/'report.json')==lineage['inherited_native_preparation_sha256'],'Exact corrected19 final build/prep/execution graph')
  pre=read(R/'reports/m4-formatting-source/provider131-preflight-r4/report.json','b50869b5af5beae7db10c9996d5b88601ffd6fde9c3e57031b47ae43812a313b');prep=read(R/'reports/m4-formatting-source/provider131-preparation-r8/report.json','ad08192d0f78ebcaa654b8809fd2568e56a910de347a5bcd4785462766c3c063');need(pre['passed']and prep['passed'],'Exact final prepared consumer code')
  boundary=['tools/m4-joint-startup131/compare_provider_v5.py','tools/m4-formatting-source/final_observer130_v2.py','tools/m4-formatting-source/final_observer130.py','tools/m4-formatting-source/formatting_derivations_v3.py','tools/m4-formatting-source/formatting_derivations_v2.py','tools/m4-formatting-source/formatting_derivations.py','tools/m4-tree-source/final_observer125_v2.py','tools/m4-tree-source/responses125.py','tools/m4-lockit-source/bridge_v2.py','tools/m4-joint-startup131/continuity131.py','tools/m4-lockit-source/identity_records.py','tools/m4-vtable-review/exact_equal.py','tools/m4-vtable-review/event_model.py','tools/m4-vtable-review/vtable_model.py']
  text={}
  for q in boundary:
   path=(R/q).resolve();text[q]=pin(path,r['files'][str(path)]).read_text();counts['reviewed_executed_boundary_tools']+=1
  entry=text[boundary[0]];need(entry.count('B2.bootstrap(')==1 and "root_access_start=len(machine.accesses)"in entry and "actual,b["not in entry,'Single bootstrap and explicit per-root source access chronology')
  for field in('per_phase_BEFORE_machine_seed','candidate_AFTER_machine_seed','canonical_reader_changed','duplicate_selected_source_reader','native_CS40_opaque_copy','native_DllMain_credit'):need(r[field]is False,'Exact persistent bounded source scope '+field)
  for field in('complete_selected_source','complete_private_mixed_publications','complete_private_mixed_FS32Q','complete_provider_lifecycle','worker_post_HeapDestroy_identity_observed','source_and_provider_combined'):need(r[field]is True,'Complete actual source/provider obligation '+field)
  observer=text[boundary[2]];need("owner['live']=False;m.memory.pop(owner['guest']);responses.index+=1"in observer and "for owner in reversed(responses.allocations)"in observer and "not owner.get('formatter',False)"in observer,'Four formatter allocations retained through source and separately freed once in reverse native cleanup order')
  cdecl=text[boundary[1]];need("source_access_entered_index=len(m.accesses)"in cdecl and "source_access_returned_index=len(m.accesses)"in cdecl and "source_State_before_hex=bytes(m.state).hex()"in cdecl and "source_State_after_hex=bytes(m.state).hex()"in cdecl,'Mixed literal full CALL/RET machine chronology is source-derived separately from API LastError')
  for marker in ('Whole32Q mixed FS source invocation and lifetime','Whole16Q mixed private owned operand source relation','Complete16Q mixed publication from actual source occurrence','Complete8Q mixed raw named owning import witness'):need(marker in text[boundary[5]],'Full actual private source witness guards retained '+marker)
  need("source_call['EAX_after']"in text[boundary[4]]and 'Complete source-derived mixed CALL/API/RET chronology'in text[boundary[4]]and 'Whole16Q raw mixed FS source ledger/head/depth/sentinel relation'in text[boundary[3]],'Current complete32Q/16Q source chronology, dtor EAX literal and entire raw snapshot guard')
  expected=dict(persistent131_sequences=12,persistent_phases=1572,whole_page_BEFORE=72312,whole_page_AFTER=72312,literal_registration_roots=1212,literal_Lockit_CALL_RET_pairs=432,actual_native_CS40_source_API_relations=432,native_FS_source_accesses=1008,actual_native12B_source_relations=672,literal_formatter_roots=48,whole_formatter_native_capacity_derivations=48,whole_mixed_native_capacity_derivations=36,literal_compound_cosine_roots=12,actual_generation_occurrence_joins=84,whole_owned_access_relations=2064,whole_publication_relations=84,whole_native_scratch_contexts=312,whole_native_tree_owner_backings=84,whole_mixed_private_owned_operands=120,whole_mixed_private_publications=36,whole_mixed_private_FS32Q_frames=24,whole_mixed_private_raw12B_records=48,whole_mixed_private_Lockit16Q_calls=24,whole_mixed_private_raw8Q_imports=24,actual_native_indirect_full_State_CPU_FX_boundary_joins=144)
  for key,value in expected.items():need(type(r['counts'][key])is int and r['counts'][key]==value,'Actual complete selected source coverage '+key)
  records=output(r,p,'API-identity-proofs.json');pin(R/'tools/m4-lockit-review/provider_exports.py','de71cd3549d50f0543ba0f7165b13b1a06594bc7e868a6fe44c65e6899562ecf');proofs={};cache={}
  for digest,proof in records['proofs'].items():
   need(hashlib.sha256(json.dumps(proof,sort_keys=True,separators=(',',':')).encode()).hexdigest()==digest,'Exact whole deduplicated physical identity proof');a=bytes.fromhex(proof['identity_before_hex']);z=bytes.fromhex(proof['identity_after_hex']);need(len(a)==len(z)==88 and a==z,'Complete unchanged actual11Q full-width identity');ident=identity(struct.unpack('<11Q',a),proof['owner_path'],proof['owner_sha256'],pin)
   if 'export_before_hex'in proof:
    x=bytes.fromhex(proof['export_before_hex']);y=bytes.fromhex(proof['export_after_hex']);need(x==y,'Entire4624 named/owner export witness conserved');proof_rows.append(exported(x,ident,proof['name'],pin,cache))
   else:
    key=ident[2],ident[3]
    if key not in cache:cache[key]=Exports(ident[2],ident[3],pin)
    rva,forward=cache[key].named(proof['name']);need(not forward and ident[1]+rva==ident[0],'Physical direct lifecycle export RVA/owning full-width target')
   proofs[digest]=proof;counts['independent_physical_named_owner_proofs']+=1
  cases={(level,seq)for level in('O0','O2')for seq in range(6)};observed={};services=collections.Counter()
  for row in records['observations']:
   case=row['level'],row['sequence'];need(case in cases and row['proof_sha256']in proofs and row['requested']==proofs[row['proof_sha256']]['name'],'Every actual case/requested API joins exact physical identity')
   if row['API_index']is None:need(row['service']in('create','query','destroy')and row['requested']=={'create':'HeapCreate','query':'GetVersionExA','destroy':'HeapDestroy'}[row['service']],'Exact lifecycle service');services[case+(row['service'],)]+=1;counts['actual_lifecycle_identity_pairs']+=1
   else:
    key=case+(row['API_index'],);w=row['witness_words'];need(key not in observed and len(w)==32 and w[:2]==[1,row['API_index']]and w[14:16]==[1,1]and 'export_before_hex'in proofs[row['proof_sha256']],'Unique whole32Q typed API witness through cleanup');observed[key]=row;counts['actual_typed_identity_pairs']+=1
  need(all(services[case+(service,)]==1 for case in cases for service in('create','query','destroy'))and counts['actual_typed_identity_pairs']==6996 and counts['actual_lifecycle_identity_pairs']==36,'All current6996 typed API and36 real lifecycle identities')
  seen=set();total=0
  for case_row in r['provider_sequences']:
   case=case_row['level'],case_row['sequence'];need(case in cases and case not in seen and case_row['actual_MFC_allocations']==68 and case_row['selected_used_bytes']==404 and case_row['all_resources_released']and case_row['actual_post_HeapDestroy_identity'],'Complete current68MFC/101callbacks/sameheap destroyed lifecycle');need(sorted(key[2]for key in observed if key[:2]==case)==list(range(case_row['cleaned_API_count'])),'Every actual API index through cleanup physically joined');capacity=case_row['first_replay_msize_capacity'];need(capacity>=404 and capacity%4==0 and case_row['actual_growth_replays']==case_row['predicted_growth_replays']==(capacity-404)//4+1,'Real queried MSIZE independently determines reached growth');total+=case_row['compared_checkpoints'];seen.add(case);counts['complete_actual_provider_sequences']+=1
  need(seen==cases and total==28140 and all(r['provider_counts'][key]==total for key in('whole_State_checkpoints','whole_CPU_checkpoints','whole_FX_checkpoints')),'All28140 complete machine checkpoints in12 current chains')
  provider_expected=dict(actual_MFC_allocations=816,actual_duplicate_allocations=228,actual_source_frees=1056,actual_MFC_source_frees=816,actual_formatter_cleanup_frees=48,actual_CS_deletes=60,actual_heap_destroys=12,selected_registration_closures=1212)
  for key,value in provider_expected.items():need(r['provider_counts'][key]==value,'Exact source/genuine cleanup total '+key);counts[key]=value
  pe_path=pin(R/'tools/analysis/pe.py',r['files'][str((R/'tools/analysis/pe.py').resolve())]);spec=importlib.util.spec_from_file_location('independent130_source_provider_PE',pe_path);PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE);provider_path=R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL';physical=PE.PEImage(pin(provider_path,r['files'][str(provider_path.resolve())]).read_bytes())
  for pc,slot in((0x7810a30b,0x78146198),(0x7810a35e,0x78146184)):
   offset=physical.rva_range(pc-physical.image_base,6)[0];need(physical.read(offset,6)==b'\xff\x15'+struct.pack('<I',slot),'Exact physical source indirect stdcall owning import');counts['physical_source_API_CALLs']+=1
  baseline=pin(n['loaded_input_page'],n['loaded_input_page_sha256']).read_bytes()[0x640:0x658];iat=pin(n['loaded_IAT_page'],n['loaded_IAT_page_sha256']).read_bytes();lockit=output(r,p,'Lockit-source-derivations.json')
  for case_row in lockit:
   case=case_row['level'],case_row['sequence'];need(len(case_row['state_reads'])==len(case_row['API_relations'])==36,'Every finite source API/state2 instance')
   for relation in case_row['API_relations']:
    pc=relation['source_PC'];slot,name={0x7810a30b:(0x78146198,'EnterCriticalSection'),0x7810a35e:(0x78146184,'LeaveCriticalSection')}[pc];raw=struct.unpack_from('<I',iat,slot-0x78146000)[0];w=relation['actual_API_words'];row=observed[case+(relation['API_index'],)];need(row['requested']==name and row['witness_words']==w and w[:8]==[1,relation['API_index'],pc,slot,raw,relation['frame'],relation['return_pc'],1],'Exact physical named API joins whole source CALL/IAT/frame witness');depth=relation['depth'];need(w[9]==w[11]and w[8]==w[12]==0 and w[16]==relation['native_owner']and w[17]==40 and w[18]==depth and depth in(0,1,2),'Actual VOID/LastError/native40 serial source domain');wanted=bytearray(baseline);struct.pack_into('<III',wanted,4,relation['LockCount'],depth,relation['OwningThread']);need(wanted.hex()==relation['derived_CS24_hex']and relation['LockCount']==(0xfffffffe if depth else 0xffffffff),'Entire typed guest24 from original opaque input and measured field effect');image=bytes.fromhex(relation['actual_native_CS40_hex']);need(len(image)==40 and struct.unpack_from('<II',image,8)==(relation['LockCount'],depth)and struct.unpack_from('<Q',image,16)[0]==relation['OwningThread'],'Separately observed actual native40 fields match source semantic depth/thread');counts['physical_actual_Lockit_API_relations']+=1
  need(counts['physical_actual_Lockit_API_relations']==432,'Every current old/tree/mixed actual Lockit API physically joined');counts.update(reviewed_full_source_phases=1572,reviewed_whole_source_page_endpoints=144624,reviewed_whole_State_CPU_FX_provider_checkpoints=total,reviewed_mixed_private16Q_owner_operands=120,reviewed_mixed_private16Q_publications=36,reviewed_mixed_private32Q_FS_frames=24,reviewed_mixed_private16Q_raw_records=48,reviewed_mixed_private16Q_Lockit_calls=24,reviewed_mixed_private8Q_imports=24)
  artifact=out/'physical-export-correspondence.json';artifact.write_text(json.dumps(proof_rows,indent=2)+'\n');pin(artifact);pin(__file__);pin(R/'tools/m4-tree-review/review_provider130_v2.py');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,source_provider_path=str(p.resolve()),source_provider_sha256=sha(p),scope='Independent bounded final actual source/provider131 receipt/code/private chronology review and physical wholeAPI export/identity/lifecycle verification; producing consumer owns capture equality, no archive repeated',counts=dict(counts),capture_archives_opened=0,source_machine_seed=False,generic_formatter_closed=False,independent_trigonometric_prediction=False,native_DllMain_credit=False,original_postRET_capture_claim=False,whole_original_provider_stack_equal=False,whole_host_FX512_equal_claim=False,initializer_credit=0,files=PINS)
  q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
