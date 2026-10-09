"""Read-only ranking from existing exact startup graphs and frozen decompiler exports."""
import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,why):
 if not ok:raise RuntimeError(why)
def main():
 out=ROOT/'reports/m4-onexit-native/next-family-r2'
 require(not out.exists(),'Fresh owned static report directory')
 files={}
 def read(rel,expected=None):
  p=ROOT/rel;value=sha(p);require(expected is None or expected==value,'Frozen input '+rel);files[str(p)]=value;return json.loads(p.read_bytes())
 accepted=read('reports/m4-joint-startup28-root/acceptance-r2/report.json','3f3f1486b94b28e15eb09572965bdd4e861b0a286375db8fbcaf9b0a4902140a')
 require(accepted['passed'] and accepted['connected_roots']==28,'Existing connected28 acceptance')
 inventory=read('reports/m4-rea-evaluation/initializer-inventory-r1.json')
 interface=read('reports/m4-onexit-source/interface-r1/instruction-contracts.json','3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3')
 selected={v['entry'] for v in interface['selected_order']}
 prospective={v['entry'] for v in interface['registration_roots']}
 require(len(selected)==54 and len(prospective)==26 and prospective<=selected,'Exact prospective54 table set')
 accepted_entries=selected-prospective
 require(len(accepted_entries)==28 and int(accepted['new_root'],16) in accepted_entries,'Accepted28 projection')
 base='reports/m4-service-initializers/static-r1/'
 classification=read(base+'root-classification.json');game_graphs=read(base+'game-all-initializer-graphs.json')
 recovery=read(base+'final-report.json');plan=read(base+'next-native-closure-plan.json')
 provider=read(base+'MSVCRT.DLL.provider.json');mfc=read(base+'MFC42.DLL.provider.json')
 game_export=read('reports/m4-rea-evaluation/game-headless-r1/warm-export.json')
 provider_export=read('reports/m4-rea-evaluation/provider-headless-r1/warm-export.json')
 fp_export=read('reports/m4-rea-evaluation/game-fp-followup-r1/export.json')
 roots={v['entry']:v for v in classification['roots']}
 all_roots={v['entry'] for v in inventory['roots']}
 require(len(all_roots)==144 and set(roots)==all_roots and len(all_roots-selected)==90,'Exact table/classification subtraction')
 families=[]
 for i,g in enumerate(classification['groups']):
  remaining=[v for v in g['roots'] if v['entry'] not in selected]
  if not remaining:continue
  local_entries={a for v in remaining for a in roots[v['entry']]['local_entries']}
  rows={r['pc']:r for a in local_entries for r in game_graphs[str(a)]['instructions']}
  families.append(dict(classification_group=i,count=len(remaining),roots=remaining,root_hex=[hex(v['entry'])for v in remaining],imports=g['import_set'],game_FS=g['FS'],unresolved_controls_per_root=g['unresolved_controls_per_root'],distinct_game_local_entries=len(local_entries),distinct_game_instructions=len(rows),status='Static candidate; no native executable/acceptance receipt attributed here'))
 require(sum(v['count']for v in families)==90,'Remaining root family partition')
 strdup=next(v for v in families if v['imports']==['MSVCRT.dll:__dllonexit','MSVCRT.dll:_onexit','MSVCRT.dll:_strdup'] and not v['game_FS'] and not v['unresolved_controls_per_root'])
 alloc=next(v for v in families if v['imports']==['MFC42.DLL:823','MSVCRT.dll:__dllonexit','MSVCRT.dll:_onexit'] and not v['game_FS'] and not v['unresolved_controls_per_root'])
 require(strdup['count']==17 and alloc['count']==32,'Exact simplest family counts')
 require(all(not roots[v['entry']]['FP_sites'] for v in strdup['roots']),'No game FP in recommended string family')
 game=ROOT/'MW3/Mech3.exe';crt=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';mfc_image=ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL'
 require(sha(game)==inventory['game_sha256'] and sha(crt)==provider['identity']['sha256'] and sha(mfc_image)==mfc['identity']['sha256'],'Exact original image identities')
 files[str(game)]=sha(game);files[str(crt)]=sha(crt);files[str(mfc_image)]=sha(mfc_image)
 def verify_rows(image,rows):
  pe=PEImage(image.read_bytes());count=0;total=0
  for pc,r in sorted(rows.items()):
   raw=bytes.fromhex(r['bytes']);offset,_=pe.rva_range(pc-pe.image_base,len(raw))
   require(pe.data[offset:offset+len(raw)]==raw and len(raw)==r['size'],'Exact existing decoded row '+hex(pc));count+=1;total+=len(raw)
  return dict(instructions=count,bytes=total,image_sha256=sha(image))
 candidate_rows={r['pc']:r for family in (strdup,alloc) for v in family['roots'] for a in roots[v['entry']]['local_entries'] for r in game_graphs[str(a)]['instructions']}
 game_bytes=verify_rows(game,candidate_rows)
 provider_new={str(a):provider['graphs'][str(a)]for a in(0x78010a6d,0x78002f32,0x78002fab)}
 require([provider_new[str(a)]['instruction_count']for a in(0x78010a6d,0x78002f32,0x78002fab)]==[23,43,51],'Exact three new integer provider body sizes')
 require(all(not g['FS_sites'] and not g['FP_sites'] and not g['unresolved_controls']for g in provider_new.values()),'New string bodies locally decode closed and integer')
 provider_bytes=verify_rows(crt,{r['pc']:r for g in provider_new.values()for r in g['instructions']})
 mfc_body=mfc['graphs'][str(0x5f401ea0)];mfc_bytes=verify_rows(mfc_image,{r['pc']:r for r in mfc_body['instructions']})
 strdup_export=next(v for v in provider['requested_exports']if v['requested']=='_strdup')
 mfc_export=next(v for v in mfc['requested_exports']if v['requested']==823)
 exported={v['entry']for v in game_export['exports']+fp_export['exports']}
 recommended=dict(rank=1,family='17 no-FS string constructors with _strdup',root_hex=strdup['root_hex'],count=17,first_small_root=hex(0x47f470),potential_connected_count_after_prospective54=71,shared_new_bodies=[dict(entry=hex(a),name=n,local_instructions=provider_new[str(a)]['instruction_count'])for a,n in[(0x78010a6d,'_strdup'),(0x78002f32,'strlen'),(0x78002fab,'strcpy')]],game_IAT=hex(0x5bb670),reuse=['Live registry owner, original _onexit/__dllonexit and registry growth/cleanup','Accepted mode1 malloc/free and private heap ownership','Persistent State, typed guest memory and exact source call/return ledger','Existing original/native comparison and fault-control archive pipeline'],required_gaps=['Focused export/recovery of three new provider bodies and17 constructor inputs; reuse current saved MSVCRT project','Exact fixed string pointers, bytes/NUL extents, object fields, callback literals and source stack cleanup per root','Literal strlen/strcpy aligned DWORD reads and byte writes through guest memory; no host strlen/strcpy replacement','Keep every allocated duplicated string live through scheduling; do not free a string while its object still refers to it','Exact malloc-call dispatch, source allocation failure/null-input branches and committed-prefix/copy permission controls','Original17+native O0/O2 persistent table-order comparison and independent controls before count credit'],reason='Fewest new provider ownership and numerical dependencies for a multi-root batch; three locally closed integer string bodies reuse current malloc and registration',domain_limit='Broad static _strdup closure includes allocation modes/new-handler/error paths with6 FS sites and22 unresolved controls. Candidate is executable only after its exact measured mode1 call frontier and original string inputs are established; no all-branch readiness inferred',static_provider_fullclosure=dict(entries=len(strdup_export['local_entries']),instructions=strdup_export['unique_instructions'],FS=len(strdup_export['FS_sites']),unresolved=len(strdup_export['unresolved_controls'])),existing_Ghidra_remaining_root_exports=sorted(hex(a)for a in exported&(all_roots-selected)),candidate_is_currently_native_executable=False)
 alternative=dict(rank=2,family='32 no-FS allocation/container constructors with MFC ordinal823',count=32,root_hex=alloc['root_hex'],potential_connected_count_after_string17_and_prospective54=103,shared_provider_entry=hex(0x5f401ea0),game_thunk=hex(0x5abd26),game_IAT=hex(0x5bb4bc),provider_allocator_IAT=hex(0x5f49814c),provider_allocator_CALL=hex(0x5f401eb5),new_handler_global=hex(0x5f498970),cold_new_handler_path=hex(0x5f41b01e),provider_local_body_instructions=33,static_provider_fullclosure=dict(entries=len(mfc_export['local_entries']),instructions=mfc_export['unique_instructions'],FS=len(mfc_export['FS_sites']),unresolved=len(mfc_export['unresolved_controls'])),readiness='More roots, but requires actual staged MFC provider identity/initialized import/global state, checked register-indirect allocator dispatch and private allocation ownership; TLS/new-handler/CxxThrow exceptional path remains a separate gate',ordinal825_free_entry=hex(0x5f401782),scope_limit='Storing callback addresses does not execute MFC deletion callbacks or establish full MFC module/thread initialization')
 out.mkdir(parents=True)
 report=dict(passed=True,scope='Existing frozen initializer inventory and decompiler export prioritization; no new import/analysis process, build, game execution or acceptance',accepted_roots=28,prospective_roots=54,prospective54_accepted=False,remaining_after_accepted28=116,remaining_after_prospective54=90,recommended=recommended,alternative=alternative,remaining_families=families,byte_rechecks=dict(game_two_candidate_families=game_bytes,new_CRT_string_bodies=provider_bytes,MFC_allocator_body=mfc_bytes),decompiler_coverage=dict(game_exports=len(game_export['exports']),FP_followup_exports=len(fp_export['exports']),provider_exports=len(provider_export['exports']),all144_seeded_entries_only=True,no_new_analysis_executed=True),prior_plan_rank4_source='32 allocation roots and17 _strdup roots are already statically prepared; this recommendation ranks them using current live mode1/registry availability',files=files,new_initializer_credit=0,native_executed=False,whole_M4_complete=False)
 report_path=out/'report.json';report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 notes='Recommend the 17 `_strdup` roots first, then the32 MFC allocation roots.\n\nCurrent acceptance stays28/144. Prospective54 is still under review; the17-root family could then target71/144 after real execution and independent validation.\n\nThe recommended family adds literal `_strdup`78010A6D (23rows), `strlen`78002F32 (43rows), and `strcpy`78002FAB (51rows) while reusing mode1 malloc/free and live registration. Its17 game closures contain no FP/FS or unresolved controls. Broader allocator/error branches remain open; measured inputs and exact source frontier are required.\n\nThe32 MFC family has more coverage but needs MFC provider state and checked indirect allocation/new-handler ownership. Decompiler exports currently cover only three wrappers among these remaining roots, not their full constructors.\n'
 (out/'assessment.md').write_text(notes,encoding='utf-8');files[str(Path(__file__).resolve())]=sha(__file__)
 files[str(report_path)]=sha(report_path);files[str(out/'assessment.md')]=sha(out/'assessment.md')
 (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps(dict(passed=True,report=str(report_path),report_sha256=sha(report_path),recommended_roots=17,alternative_roots=32)))
if __name__=='__main__':main()
