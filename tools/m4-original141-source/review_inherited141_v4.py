"""Independent bounded original131 source/FS-input review; no archive reads."""
from pathlib import Path
import collections,hashlib,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','No capture/archive/transport opened');a=sha(p);need(p.is_relative_to(OUTPUT)or ADMITTED.get(str(p))==a,'Every physical external reviewer input ROOT admitted, no fallback');need(h is None or a==h,'Physical bounded dependency '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable bounded input');PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(admission_path,admission_sha,configuration_path,configuration_sha,source_path,source_sha,name):
 global ADMITTED,OUTPUT
 ap=Path(admission_path).resolve();need(sha(ap)==admission_sha,'Exact ROOT independent post-source admission');ad=json.loads(ap.read_bytes());need(ad['passed']is True and ad['independent_review']is True and ad['scope_identity']=='original141_post_source_inherited_review'and ad['configuration_sha256']==configuration_sha and ad['original_source_sha256']==source_sha,'No cached original138 or self admission')
 ADMITTED={}
 for path,h in ad['files'].items():
  path=Path(path).resolve();need(path.suffix.lower()not in('.mwb','.mwi','.zip')and path.name!='transport.json','Ordinary closure only');need(str(path)not in ADMITTED and sha(path)==h,'Whole unique ROOT closure before any source record');ADMITTED[str(path)]=h
 OUTPUT=(R/'reports/m4-original141-source'/name).resolve();PINS[str(ap)]=admission_sha
 need(source_sha=='44a46bd0fda7776578232af60e2d9f0188275660350a239eb8c8def4790d9334'and Path(source_path).resolve()==R/'reports/m4-original141-source/source-r7/report.json'and configuration_sha=='451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0','Exactly sealed source7 and current configuration; no old original138 semantic row')
 C=read(configuration_path,configuration_sha)
 need(C['schema']=='mw34-original141-source-input-contract-v1','Actual current source configuration')
 out=OUTPUT;need(not out.exists(),'Fresh bounded review');out.mkdir(parents=True);passed=False;counts=collections.Counter();excluded={};observations=[]
 try:
  p=Path(source_path).resolve();a=read(p,source_sha);need(a['configuration_sha256']==configuration_sha and a['original_validation_sha256']==C['validation']['sha256']and a['counts']['phases']==846 and a['counts']['callbacks']==111,'Actual new original141 source report, all846 registry relations and111callbacks')
  v=read(a['original_validation_path'],a['original_validation_sha256']);need(v['passed']and a['passed']and a['reader_closed']and a['archive_sessions_opened']==0 and a['capture_archive_opened']is False,'Genuine current source execution sealed/closed')
  need(a['candidate_AFTER_machine_seed']is False and a['original_postRET_observed']is False and a['original_postRET_source_derived']is True and a['formatter_full_registration_provider_CPU_executed_by_model']is False,'Exact bounded source/registration/postRET scope')
  for receipt in [a]+[read(c['receipt'],c['sha256'])for c in a['children']]:
   need(receipt['passed'],'Every current source child passed')
   for q,h in receipt['files'].items():
    if Path(q).suffix.lower()in('.mwb','.mwi','.zip')or Path(q).name=='transport.json':need(q not in excluded or excluded[q]==h,'Stable retained capture identity');excluded[q]=h
    else:pin(q,h)
  need(not excluded,'Current raw-export comparers opened/pinned no canonical archive')
  producer=read(a['raw_export_report_path'],a['raw_export_report_sha256']);need(producer['passed']and producer['reader_closed']and producer['paired_export_readers_closed'],'Current full producing reader sealed all raw branches')
  continuity=read(R/'reports/m4-startup131-original/inherited-source-preparation-r3/report.json','3f21fbc601dd3b8dfea3ea4354e425f3aa6a368f1e1ddd77f06958bed656be97');need(continuity['passed']and continuity['counts']['inherited_exact_source_spans']==3955 and continuity['counts']['current_root_table_pairs']==131,'Historical accepted131 exact3955-span/table131 invariant retained; fresh current3980 physical source continuity separately required')
  for path,digest in continuity['files'].items():pin(path,digest)
  raw_export=next(row for row in producer['paired_exports']if row['branch']=='original');need(a['raw_export_report_sha256']==C['validation']['sha256']and raw_export['transport_path']==v['original_capture']and producer['counts']['phases']==846 and producer['callbacks']==111,'Same current original141 strict producer/transport metadata; no old138 export substitution')
  need(raw_export['logical_files']==261543 and raw_export['payload_bytes']==1540126431,'Exact current sealed ordinary geometry')
  for field in('index','payload'):pin(raw_export[field+'_path'],raw_export[field+'_sha256'])
  need(a['counts']['current_physical_131_root_table_pairs']==131 and a['counts']['current_exact_retained_source_spans']==3980 and a['counts']['current_total_source_spans']==6411,'Actual current source corpus retained3955 plus25declared spans, not historical result oracle')
  corpus=pin(R/'tools/m4-original141-source/retained_corpus141_v2.py').read_text();need("len(rows)==3980"in corpus and "len(current)==int(match[1])==6411"in corpus and "actual_offset==offset"in corpus and "packed[page][1][at&4095:(at&4095)+n]==raw"in corpus and "origin_counts=={0:3962,1:18}"in corpus,'Physical whole-span/table/byte continuity implementation explicitly retained')
  f=read(p.parent/'original-Formatting-source-derivations.json');t=read(p.parent/'original-Tree-source-derivations.json');need(len(f)==24 and len(t)==6,'All current four roots and tree sequences exported')
  actual=read(Path(C['validation']['path']).parent/'fresh-cdecl.json');index={(r['sequence'],r['phase'],r['root'],r['index']):r for r in actual};need(len(index)==144,'All actual cdecl boundaries unique')
  source=pin(R/'tools/m4-original141-source/format_source141_v2.py').read_text();aggregate=pin(R/'tools/m4-original141-source/replay_original141_v10.py').read_text();tree=pin(R/'tools/m4-original141-tree-source/tree_source_v3.py').read_text()
  need("first_head=phase_boundaries[0]['header'][5]"in source and "root_head=fs_events[0]['header'][4]if fs_events else first_head"in source and "not any(r[1]==0x7ffde000 for r in self.accesses)"in source and "actual compiled observer fs head matches literal entry/return head"in source.lower(),'Scalar genuine FS input plus literal prefix and every actual boundary guard')
  need('reader.close();reader.entries.clear();reader.bundles.clear()'in aggregate and "tree_phase=next(i for i,x in enumerate(preparation['selected_order'])if x['entry']==0x4b7f70)"in tree and "need(tree_phase==86"in tree,'Explicit shared reader closure; actual current selected phase resolved by literal root and asserted86')
  asm=pin(Path(C['source_preparation']['path']).parent/'format_observer_x86.asm').read_text().lower();functions=[]
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
   need(set(case)=={'sequence','path','sha256','source'},'Exact current TREE aggregate derivation schema');child=read(case['path'],case['sha256']);need(child['passed']and child['sequence']==case['sequence']and child['source_case_extent']==1 and child['original_validation_sha256']==C['validation']['sha256'],'Actual same-source current TREE child relation');s=case['source'];need(s['phase']==86 and s['sequence']==case['sequence']and s['candidate_AFTER_seed']is False,'Current tree phase/sequence exact, no AFTER seed')
   need(child['whole_provider_stack_compared']is False and child['original_unused_frame_bytes_seeded']is False and child['all_current_frame_source_written_bytes_compared']is True and child['opaque_disagreements_proven_unused_before_overwrite']is True,'Bounded original unused external-stack policy with exact source-written frame/forward-read checks')
   need(len(s['owners'])==7 and len(s['Lockit_calls'])==26 and len(s['FS_events'])==21 and len(s['original_boundary_joins'])==78,'Every genuine tree generation/API/FS/boundary occurrence retained');counts['tree_cases']+=1;counts['tree_whole_owner_backings']+=7;counts['tree_whole_FS_records']+=21;counts['tree_whole_CPU_FX_ENV_CS_frame_boundaries']+=78
  need(counts['first_entry_no_prior_FS_access_proofs']==18 and counts['mixed_genuine_initial_FS_inputs']==6 and counts['actual_cdecl_FS_head_joins']==144 and counts['whole_owner_capacity_byteflows']==counts['finite_actual_allocation_inputs']==42 and counts['finite_actual_CS_API_inputs']==12 and counts['tree_whole_owner_backings']==42 and counts['tree_whole_FS_records']==126 and counts['tree_whole_CPU_FX_ENV_CS_frame_boundaries']==468,'Exact measured bounded coverage')
  pin(__file__);[pin(R/'tools/m4-tree-review'/q)for q in('review_original130_combined.py','review_original130_combined_v2.py','derive_original130_combined_v2.py','derive_original130_combined_v3.py')];passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Independent physical bounded current original141 source/executed child/export review, literal original owner read/store byteflow replay and genuine scalar FS-input policy; no archive reread or new machine execution',original_combined_source_path=str(p.resolve()),original_combined_source_sha256=sha(p),original_validation_sha256=a['original_validation_sha256'],counts=dict(counts),source_FS_head_timing='Actual MOV EAX,FS:[0] after ESP-only host-stack switch and before format_observe; PUSHFD/CLD do not change FS head',whole_original_provider_stack_equal=False,full_registration_provider_CPU_modeled=False,individual_original_allocator_FS_events_observed=False,original_postRET_capture_claim=False,capture_archives_opened=0,retained_archive_inputs=excluded,initializer_credit=0,files=PINS)
  for path,h in PINS.items():need(sha(path)==h,'Final whole ordinary dependency conservation')
  report.update(ROOT_admission_path=str(ap),ROOT_admission_sha256=admission_sha,configuration_sha256=configuration_sha,canonical_transport_file_hashed=False,canonical_transport_identity_deferred_to_acceptance_union=True,current_source_report_only=True,full_original846_CPU_execution_claim=False)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,counts=dict(counts),sha256=sha(q))))
if __name__=='__main__':main(*sys.argv[1:])
