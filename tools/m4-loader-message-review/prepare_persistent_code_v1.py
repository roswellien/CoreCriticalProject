"""Static source-only lifecycle/literal provider derivative; no compilation."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-loader-message-review'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024 and p.suffix.lower()not in('.mwb','.mwi','.zip')
  b=p.read_bytes();v=hashlib.sha256(b).hexdigest();assert h is None or h==v;assert pins.setdefault(str(p),v)==v;return b
 def read(p,h=None):return json.loads(pin(p,h))
 runway_path=R/'reports/m4-loader-message-review/lifecycle-runway-r1/report.json';runway=read(runway_path,'e73e734088f577d96dc4a8b11b6e298d79a0aadb31c434bd0c883460e1a95d61')
 program_path=runway_path.parent/'literal1100-source-program.json';program=read(program_path,runway['files'][str(program_path)]);assert len(program['rows'])==1100
 parent=R/'tools/m4-loader-message-review/native_provider.cpp';source=pin(parent).decode();current=source;changes=[]
 def change(a,b):
  nonlocal current
  assert current.count(a)==1;current=current.replace(a,b);changes.append(dict(before=a,after=b))
 change('#include "source_table.hpp"','#include "source_table.hpp"\n#include "literal_owner_v1.hpp"')
 start=current.index('void sort_pairs() {');end=current.index('\n}\n}',start)+2;old=current[start:end]
 change(old,'bool sort_pairs() {\n  return mw34_message_literal::run_sort({table,0x10003010u,sizeof(table)});\n}')
 change('BOOL WINAPI DllMain(HINSTANCE,DWORD reason,LPVOID) {','BOOL WINAPI DllMain(HINSTANCE,DWORD reason,LPVOID) {\n  // Caller-owned backplane must exist before real loader entry. No synthetic State.\n  if(!mw34_message_literal::MW34MessageCurrentLiteralOwner())return FALSE;')
 change('  sort_pairs();++dll_notifications;','  if(!sort_pairs())return FALSE;\n  ++dll_notifications;')
 inverse=current
 for c in reversed(changes):assert inverse.count(c['after'])==1;inverse=inverse.replace(c['after'],c['before'])
 assert inverse==source and len(changes)==4
 p=out/'native_provider_literal_v1.cpp';p.write_text(current);pin(p)
 for leaf in('persistent_lifecycle_v1.py','literal_owner_v1.hpp','literal_sorter_bridge_v1.cpp'):
  raw=pin(R/'tools/m4-loader-message-review'/leaf);q=out/leaf;q.write_bytes(raw);pin(q)
  if leaf.endswith('.py'):ast.parse(raw)
 lifted=read(R/'reports/m4-loader-message-review/literal-sorter-helper-lifts-r2/report.json','79ab43a6998939990dd2683f708a548833f32c7bf30bf3ffa4a7646ca46d8352')
 objects={level:[dict(body=k,**v['objects'][level])for k,v in lifted['bodies'].items()]for level in('O0','O2')}
 for rows in objects.values():
  for v in rows:pin(v['path'],v['sha256'])
 callbacks_path=R/'reports/m4-loader-message-review/literal-sorter-callbacks-r1/report.json';callbacks=read(callbacks_path)
 assert callbacks['passed']is True and callbacks['whole_source_PCs']==952 and callbacks['unique_callback_sites']==160
 cp=callbacks_path.parent/'callbacks.json';pin(cp,callbacks['files'][str(cp)])
 for leaf in('bounded-integer.py','bounded-SAR.py'):
  path=R/'reports/m4-loader-message-review/literal-sorter-evaluation-r4'/leaf;pin(path)
 cl='C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/HostX64/x64/cl.exe'
 recipe=dict(scope='ROOT review then compile-only; no code/DLL execution and no implicit host backplane default',compiler=cl,working_directory=str(out),include_directories=[str(out),str(R/'reports/m4-loader-message-review/native-preparation-r1')],compile_commands={level:[[cl,'/nologo','/c','/MD','/EHsc','/std:c++17','/Od'if level=='O0'else'/O2','/I'+str(out),'/I'+str(R/'reports/m4-loader-message-review/native-preparation-r1'),'/Fo'+str(out/level/(Path(source).stem+'.obj')),str(out/source)]for source in('native_provider_literal_v1.cpp','literal_sorter_bridge_v1.cpp')]for level in('O0','O2')},literal_link_inputs=objects,required_link_frontier='MW34MessageCurrentLiteralOwner owning backplane implementation/import library must be independently reviewed and supplied before complete DLL link; no NULL/synthetic/default implementation permitted',source_frame_contract=dict(State_bytes=3504,State_align=8,PC_offset=2472,CPU_bytes=40,FX_bytes=512,source_pointer_bits=32,source_entry_args=3,source_entry_frame_bytes=16,source_RET_cleanup=12,source_sort_CALL='0x10001710',source_sort_return='0x10001715',source_table='0x10003010',source_table_bytes=12616,native_pointers_bits=64),admission_frontier=[
  'Required provider methods bind actual loaded CRT path/hash/base/generation/named IAT and current initialized fdiv DWORD; no file-zero or prior direct-writer replay value defaults.',
  'Current source Machine and flag/region/ledger authorities must retain full literal1100 instructions and callbacks, CALL/JMP/RET frames and causal permissions; no source State/memory/FX/bootstrap reseed in adapter.',
  'Source148 lifecycle new native IR/undefined callback equivalence is NOT prepared by sorter952 objects. Additional native body/source equality proof remains mandatory.',
  'Owner begin/finish/read/write/helper/return/undefined methods must enforce exact source PC/callback inventory, whole State/CPU/FX/frame, source/native whole table and authentic string/image backings, every native access and balanced frame/lifetime; interface declarations alone do not prove these predicates.',
  'Host backplane must supply carried caller state before actual DllMain, through admitted shared owning linkage. Export installer after LoadLibrary cannot provide process_attach input.',
  'Source MSVCRT128 allocation/all initial bytes and native compilerCRT/host128 ownership/lifecycle stay distinct. Actual LoadLibrary/GetProcAddress/search/generation/resource/State observation and normal47F760 original/native carried pair remain unadmitted.',
 ],inverse_source_hunks=4,compiler_invoked=False,source_evaluator_invoked=False,DLL_loaded=False)
 for leaf,data in [('exact-native-source-inverse.json',changes),('ROOT-compile-and-admission-recipe.json',recipe)]:
  p=out/leaf;p.write_text(json.dumps(data,indent=2)+'\n');pin(p)
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Immutable source/code preparation only; carried1100 adapter and literal two-object integration candidate with required owning backplane frontier',whole_native_parent_inverse=True,source_delta_hunks=4,literal_existing_functions=2,literal_952_only_not_native1100=True,source_program_rows=1100,persistent_adapter_no_State_or_memory_reseed=True,current_CRT_provider_witnesses_required_no_defaults=True,owning_backplane_implementation_pending=True,complete_DLL_link_admitted=False,compiler_invoked=False,source_evaluator_invoked=False,DLL_loaded=False,worker_executed=False,canonical_reader_opened=False,new_lift=False,new_install=False,initializer_credit=0,accepted_function_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
