"""Independent bounded original130 source/FS-input review; no archive reads."""
from pathlib import Path
import collections,hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture/archive opened');a=sha(p);need(h is None or a==h,'Physical bounded dependency '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable bounded input');PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh bounded review');out.mkdir(parents=True);passed=False;counts=collections.Counter();excluded={};observations=[]
 try:
  p=R/'reports/m4-startup130-original/combined-source-r3/report.json';a=read(p,'2a12a3a3356c0009da916ddeaa2696431ec5131423fda9b4c9b880abaee90624')
  v=read(a['original_validation_path'],a['original_validation_sha256']);need(v['passed']and a['passed']and a['reader_closed']and a['archive_sessions_opened']==1,'Genuine current source execution sealed/closed')
  need(a['candidate_AFTER_machine_seed']is False and a['original_postRET_observed']is False and a['original_postRET_source_derived']is True and a['formatter_full_registration_provider_CPU_executed_by_model']is False,'Exact bounded source/registration/postRET scope')
  for receipt in [a]+[read(c['receipt'],c['sha256'])for c in a['cases']]:
   need(receipt['passed'],'Every current source child passed')
   for q,h in receipt['files'].items():
    if Path(q).suffix.lower()in('.mwb','.zip'):need(q not in excluded or excluded[q]==h,'Stable retained capture identity');excluded[q]=h
    else:pin(q,h)
  need(len(excluded)==1,'One retained current original capture, no reread')
  f=read(p.parent/'original-Formatting-source-derivations.json');t=read(p.parent/'original-Tree-source-derivations.json');need(len(f)==24 and len(t)==6,'All current four roots and tree sequences exported')
  actual=read(R/'reports/m4-startup130-original/validation-r2/fresh-cdecl.json');index={(r['sequence'],r['phase'],r['root'],r['index']):r for r in actual};need(len(index)==144,'All actual cdecl boundaries unique')
  source=pin(R/'tools/m4-startup130-original/format_source_v4.py').read_text();aggregate=pin(R/'tools/m4-startup130-original/current_source_v4.py').read_text();tree=pin(R/'tools/m4-startup130-original/tree_source.py').read_text()
  need("first_head=phase_boundaries[0]['header'][5]"in source and "root_head=fs_events[0]['header'][4]if fs_events else first_head"in source and "not any(r[1]==0x7ffde000 for r in self.accesses)"in source and "actual compiled observer fs head matches literal entry/return head"in source.lower(),'Scalar genuine FS input plus literal prefix and every actual boundary guard')
  need('reader.close();reader.entries.clear();reader.bundles.clear()'in aggregate and "phase=78"not in aggregate and "phase=78"not in tree,'Explicit shared reader closure; selected phase resolved by literal root')
  asm=pin(R/'reports/m4-startup130-original/preparation-r2/format_observer_x86.asm').read_text().lower();functions=[]
  for function in ('format_entry_strrchr','format_return_strrchr','format_entry_malloc','format_return_malloc','format_entry_sprintf','format_return_sprintf'):
   body=asm.split(function+' proc\n')[1].split(function+' endp')[0];need(body.index('mov esp,mixed_host_esp')<body.index('mov eax,dword ptr fs:[0]')<body.index('call format_observe'),'Actual measured FS head after ESP-only host switch, before observer call');need('mov format_head,eax'in body and 'fxrstor format_fx'in body and 'fldenv format_env'in body,'Actual whole architectural capture/restoration source');need(body[body.index('mov esp,mixed_host_esp'):body.index('mov eax,dword ptr fs:[0]')].split()==['mov','esp,mixed_host_esp','pushfd','pop','dword','ptr','format_cpu[32]','cld'],'Exactly ESP switch/PUSHFD/flag-save/CLD before FS head read, no FS write');functions.append(function)
  for row in f:
   need(row['no_post_source_seed']is True,'No source post state seed');heads=row['FS_initial_input'];boundaries=row['original_boundary_joins'];need(len(boundaries)==6 and heads['original_after_memory_seed']is False and heads['original_snapshot_header_index']==5,'One genuine scalar input with six exact cdecl observations')
   if row['root']!=0x4e1ca0:
    prefix=heads['source_PCs_before_observation'];need(heads['literal_no_FS_access_before_first_entry']is True and heads['actual_value']==heads['first_entry_observed_value']==boundaries[0]['header'][5]and prefix==row['source_PCs'][:len(prefix)],'Genuine first entry input unchanged throughout exact literal root prefix')
    prefix_set=set(prefix);need(not any(pc in prefix_set and address<0x7ffde004 and address+width>0x7ffde000 for pc,address,value,width,writing in row['source_accesses']),'No overlapping prefix FS-head memory operand');counts['first_entry_no_prior_FS_access_proofs']+=1
   else:
    need(len(row['FS_events'])==6 and heads['actual_value']==row['FS_events'][0]['header'][4]and heads['kind']=='genuine_first_game_FS_read','Mixed source has its genuine outer FS predecessor, not inner strrchr head');counts['mixed_genuine_initial_FS_inputs']+=1
   for b in boundaries:
    key=(row['sequence'],row['phase'],row['root'],b['index']);fact=index[key];need({k:b[k]for k in fact}==fact and len(b['CPU'])==10 and len(bytes.fromhex(b['frame32_hex']))==32 and len(bytes.fromhex(b['FX512_hex']))==512 and len(bytes.fromhex(b['ENV28_hex']))==28 and b['original_source_cleanup_after_RET_captured']is False,'All whole actual cdecl fields retained, no invented postRET capture');counts['actual_cdecl_FS_head_joins']+=1;counts['whole_cdecl_CPU_FX_ENV_frame_joins']+=1
   for owner in row['all_owners']:
    backing=bytearray.fromhex(owner['initial_hex']);base=owner['pointer'];need(len(backing)==owner['capacity'],'Entire genuine actual allocation input capacity')
    for pc,address,value,width,writing in row['source_accesses']:
     if address>=base+len(backing)or address+width<=base:continue
     offset=address-base;need(0<=offset and offset+width<=len(backing),'Every owner operand lies entirely in measured capacity');raw=(value&((1<<(width*8))-1)).to_bytes(width,'little')
     if writing:backing[offset:offset+width]=raw;counts['literal_owned_store_byteflows']+=1
     else:need(backing[offset:offset+width]==raw,'Literal owner read derives from actual initial bytes and only preceding source stores');counts['literal_owned_read_preimages']+=1
    need(backing.hex()==owner['source_final_hex']==owner['final_hex'],'Complete source backing, source final and actual final agree including untouched tails');counts['whole_owner_capacity_byteflows']+=1
   for api in row['API_inputs']:
    if 'initial_hex'in api:need(api['AFTER_machine_seed']is False and len(bytes.fromhex(api['initial_hex']))==api['initial_capacity'],'Finite actual API initial backing, no AFTER machine input');counts['finite_actual_allocation_inputs']+=1
    else:need(api['original_source_postRET_seed']is False and api['original_ctor_response_scope']in('pre-epilogue7810A311','actualpreRET7810A364'),'Bounded actual API volatile/CS24 response scope');counts['finite_actual_CS_API_inputs']+=1
   suffix=row['registration_suffix'];need(suffix['whole_vector_source_derived']is True and suffix['full_registration_provider_CPU_executed_by_model']is False and (suffix['literal_callback_store_PC'],suffix['literal_cursor_store_PC'])==(0x78004a67,0x78004a69),'Separate complete vector carry/two literal stores; no full registration CPU claim')
  for case in t:
   child=read(case['receipt'],case['sha256']);s=case['source'];need(case['phase']==78 and s['phase']==78 and s['sequence']==case['sequence']and s['candidate_AFTER_seed']is False,'Current tree phase/sequence exact, no AFTER seed')
   need(child['whole_provider_stack_compared']is False and child['original_unused_frame_bytes_seeded']is False and child['all_current_frame_source_written_bytes_compared']is True and child['opaque_disagreements_proven_unused_before_overwrite']is True,'Bounded original unused external-stack policy with exact source-written frame/forward-read checks')
   need(len(s['owners'])==7 and len(s['Lockit_calls'])==26 and len(s['FS_events'])==21 and len(s['original_boundary_joins'])==78,'Every genuine tree generation/API/FS/boundary occurrence retained');counts['tree_cases']+=1;counts['tree_whole_owner_backings']+=7;counts['tree_whole_FS_records']+=21;counts['tree_whole_CPU_FX_ENV_CS_frame_boundaries']+=78
  need(counts['first_entry_no_prior_FS_access_proofs']==18 and counts['mixed_genuine_initial_FS_inputs']==6 and counts['actual_cdecl_FS_head_joins']==144 and counts['whole_owner_capacity_byteflows']==counts['finite_actual_allocation_inputs']==42 and counts['finite_actual_CS_API_inputs']==12 and counts['tree_whole_owner_backings']==42 and counts['tree_whole_FS_records']==126 and counts['tree_whole_CPU_FX_ENV_CS_frame_boundaries']==468,'Exact measured bounded coverage')
  pin(__file__);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Independent physical bounded current original130 source/executed child/export review, literal original owner read/store byteflow replay and genuine scalar FS-input policy; no archive reread or new machine execution',original_combined_source_path=str(p.resolve()),original_combined_source_sha256=sha(p),original_validation_sha256=a['original_validation_sha256'],counts=dict(counts),source_FS_head_timing='Actual MOV EAX,FS:[0] after ESP-only host-stack switch and before format_observe; PUSHFD/CLD do not change FS head',whole_original_provider_stack_equal=False,full_registration_provider_CPU_modeled=False,individual_original_allocator_FS_events_observed=False,original_postRET_capture_claim=False,capture_archives_opened=0,retained_archive_inputs=excluded,initializer_credit=0,files=PINS)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,counts=dict(counts),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
