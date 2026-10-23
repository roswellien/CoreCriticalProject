"""Static exact1100-row preparation and finite lifecycle admission frontier."""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]

def main(name):
 out=R/'reports/m4-loader-message-review'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'and p.stat().st_size<32*1024*1024
  data=p.read_bytes();v=hashlib.sha256(data).hexdigest();assert h is None or h==v,(p,h,v);assert pins.setdefault(str(p),v)==v;return data
 def read(p,h=None):return json.loads(pin(p,h))
 def mod(path,name):
  pin(path);s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 base=R/'reports/m4-loader-message-review'
 physical=read(base/'physical-r4/report.json','138452ce77ef212ca239499794e0aa9e4a6034a64361a70fc71b0896205959e4')
 evaluation=read(base/'literal-sorter-evaluation-r4/report.json','a8b7f4c27d853db8724003c649a57bf7b1dc4e037f291e5382a3c524cb512de0')
 lifted=read(base/'literal-sorter-helper-lifts-r2/report.json','79ab43a6998939990dd2683f708a548833f32c7bf30bf3ffa4a7646ca46d8352')
 lifecycle=read(base/'lifecycle-source-preparation-r1/report.json','895683699f00ffe17fef4a07d96c1e22ac557a952362641674028546ae321ca2')
 for v in(physical,evaluation,lifted,lifecycle):
  assert v['passed']is True
  if 'DLL_loaded'in v:assert v['DLL_loaded']is False
 source=base/'literal-sorter-evaluation-r4/source-program.json';program=read(source,evaluation['files'][str(source)])['rows'];assert len(program)==952
 extra_path=base/'lifecycle-source-preparation-r1/entry-CRT-DllMain-extra-physical-rows.json';extra=read(extra_path,lifecycle['files'][str(extra_path)])
 recipe_path=extra_path.parent/'lifecycle-source-recipe.json';recipe=read(recipe_path,lifecycle['files'][str(recipe_path)])
 imports_path=extra_path.parent/'CRT-import-candidate-identities.json';imports=read(imports_path,lifecycle['files'][str(imports_path)])
 assert len(extra['physical_rows'])==148 and len({r['pc']for r in program})==952 and not {r['pc']for r in program}&{r['pc']for r in extra['physical_rows']}
 PE=mod(R/'tools/analysis/pe.py','lifecycle_static_PE');D=mod(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','lifecycle_static_decode')
 image=PE.PEImage(pin(R/'MW3/Mech3Msg.dll','8899fabb7e57383a9a483cb048636bcc027334b48941aa49835cdcc1c4715b8c'))
 decoded=[]
 for row in extra['physical_rows']:
  raw=bytes.fromhex(row['bytes']);assert image.read(image.rva_range(row['pc']-image.image_base,len(raw))[0],len(raw))==raw
  decoded.append(D.instruction_contract(dict(pc=row['pc'],mnemonic=row['mnemonic'],operands=re.sub(r'\s+<[^>]+>','',row['operands']),width=row['size'],bytes_hex=row['bytes'])))
 for row in program:
  raw=bytes.fromhex(row['bytes_hex']);assert image.read(image.rva_range(row['pc']-image.image_base,len(raw))[0],len(raw))==raw
 union=sorted(program+decoded,key=lambda r:r['pc']);assert len(union)==1100 and len({r['pc']for r in union})==1100
 for body in lifted['bodies'].values():
  for obj in body['objects'].values():pin(obj['path'],obj['sha256'])
 fd=R/'reports/m4-crt-fdiv-reference/observations-r1/report.json';fdiv=read(fd)
 assert fdiv['passed']is True and {r['direct_source_written_BOOL']for r in fdiv['pairs']}=={0}
 pin(R/'tools/m4-crt-fdiv/provider.hpp');pin(R/'tools/m4-loader-message-review/native_provider.cpp');pin(R/'tools/m4-loader-message-review/native_loader_provider.cpp')
 contract_path=R/'reports/m4-loader-source/service-obligations-r1/service-contract.json';contract=read(contract_path)
 assert contract['message']['export_called_on_normal_root']is False
 provider_frontier=[
  dict(id='provider_fdiv',source_IAT='0x10002008',source_read_PC='0x10001a83',source_store_PC='0x10001a85',destination='0x1000e2c0',candidate_export='0x78037c2c',candidate_file_DWORD=imports['_adjust_fdiv']['physical_file_initial_DWORD'],required='Bind current real loaded oldCRT module path/hash/base/generation, unique named data export and actual resolved source IAT; carry initialized DWORD from source-owned memory after its actual callback lifecycle. Existing FDIV original observation BOOL0 is a distinct direct-writer domain and cannot seed this DLL. No modern-host _adjust_fdiv assumption.',ready=False),
  dict(id='current_CRT_initterm',source_CALL='0x10001ac4',source_tail_JMP='0x10001be0',source_IAT='0x10002000',candidate_export='0x780014f8',source_range=['0x10003000','0x10003004'],required='Prove own persistent one-nullDWORD input from current image/relocations and all intervening writes, true two-argument cdecl CALL frame/tailJMP/RET+callercleanup; separately establish actual current oldCRT export/body/init lifecycle. A modern native _initterm array must use two wide host boundaries and own8-byte null entry, never cast32-bit guest pointers or pretend4-byte/8-byte ranges identical.',ready=False),
  dict(id='CRT128_own_birth',source_malloc_CALL='0x10001a92',source_malloc_return='0x10001a98',source_free_CALL='0x10001b11',required='Authentic owning wide host pointer/generation/request128/capacity/all128 initial bytes plus source typed alias, actual malloc failure path; publish only from real return then literal firstDWORD0/base/next stores. Existing candidate host128 allocation is distinct from source MSVCRT allocation and compilerCRT allocations.',ready=False),
  dict(id='literal_native_sorter_integration',required='Replace candidate independent insertion sort with exact existing f_10001000/f_10001740 O0/O2 literal bodies and complete checked guest memory/callback/sourcePC/undefined-flag bridge. Current compiled objects and952-PC attribution are reusable; native candidate still invokes insertion sort. Synthetic two persistent sorter calls do not prove actual DllMain State/CPU/FX/frame.',ready=False),
  dict(id='module_search_generation',source_bare_name='mech3Msg.dll',required='Bind source registry32/CWD branch and actual executable LoadLibrary selection to exact current1577-message PE32 identity and reviewed native64 derivative identity; real host HMODULE/FARPROC remain wide, guest aliases include active Context/thread/sourceframe/exportRVA0x1720/generation/lifetime. Record actual selected file/architecture/import owners/resource bytes and reuse/refcount/new-load distinction. Staged1540DLL cannot substitute.',ready=False),
  dict(id='DLL_notifications_lifecycle',required='Execute or independently model all148 entry/CRT/user rows on carried own image/State/CPU/FX/stack; attach CRT before sort, thread attach CRT before sort, thread detach sort before CRT, process detach sort before decrement/emptyexit/free. Prove rawhook null and emptyexit by source writes, preserve next dangling numeric value afterfree. No datafile load; source owner initialization/side effects and host compilerCRT lifecycle separately observed.',ready=False),
  dict(id='normal_root47F760_pair_carry',required='Current original/native registered source caller, full27loader-body typed CALL/store timing and allnormal registry/message/DirectX domains, imported owner resources and cleanup; original/native O0/O2 State/CPU/FX/own memory/source semantic/independent review+carried selected order. Normal message path resolves ZLocGetID but does not call it, and boolean depends module!=0 even if export0.',ready=False),
 ]
 plan=dict(scope='Exact static literal1100 program runway; all API/loaded provider/State/lifecycle admission frontiers remain open',source_program_rows=1100,inherited_sorter_rows=952,added_entry_CRT_user_rows=148,added_mnemonic_counts=dict(collections.Counter(r['mnemonic']for r in decoded)),dynamic_callback_frontiers=extra['unresolved_dynamic_edges'],known_reusable=dict(literal_sorter_two_synthetic_calls=evaluation['endpoints'],helper_lift_exact_two_functions=list(lifted['bodies']),loaded_DLL_or_currentCRT_proof=False,existing_REA_status=lifted['REA_status'],installed_Ghidra_reused_in_prior_physical_reports=True,current_REA_connection_not_rechecked_or_assumed=True),next_implementation=[
  'Review materialized1100 exact source contracts and merge148 integer rows into inherited persistent evaluator; replace no BEFORE/AFTER or provider operand data. Keep all raw callbacks and typed imported API calls explicit.',
  'Add provider_fdiv and initterm typed witnesses as required inputs without defaultvalues; attach allocation publishes only authenticated own source return and128-byte birth. Prepare source-only positive/adverse synthetic controls labelled synthetic before any DLL experiment.',
  'Integrate alreadycompiled two literal sorter bodies into a fresh native DLL derivative, preserve entire1577 metadata/data/resource bytes and shared sourcePC guards; compile and independent whole-link review before admission.',
  'Only after ROOT admission, one bounded real executable DLL experiment establishes own search/path/generation/attach/notification/resource/import owners/host State+FX. Keep actual oldCRT parity and native47F760 paired acceptance separate until fully proven.'
 ],provider_frontier=provider_frontier,full_source_native_acceptance=False)
 # Explicitly record the absence of execution rather than defaulting a missing witness.
 plan.update(native_provider_source_equivalence=False,source_lifecycle_evaluated=False,DLL_loaded=False,actual_CRT_provider_called=False,worker_executed=False,canonical_reader_opened=False,initializer_credit=0,accepted_function_credit=0)
 for leaf,data in [('literal1100-source-program.json',dict(rows=union)),('loader47F760-next-implementation.json',plan)]:
  p=out/leaf;p.write_text(json.dumps(data,indent=2)+'\n');pin(p)
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Bounded static current-bytes preparation/readiness; no synthetic or actual source machine run',source_rows=1100,added_physical_rows=148,pending_provider_frontiers=len(provider_frontier),source_lifecycle_evaluated=False,DLL_loaded=False,worker_executed=False,canonical_reader_opened=False,new_lift_attempted=False,new_install=False,current_REA_connection_claim=False,initializer_credit=0,accepted_function_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
