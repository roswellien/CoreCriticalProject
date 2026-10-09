"""Exact static registration-batch preparation; no target execution or lift.

Reuse pinned graphs, recheck every selected row against the admitted PE, and
decode only genuinely missing callback/registry boundaries. Original callback
targets remain data until a later measured dispatcher invokes them.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, struct, subprocess, sys
from collections import deque
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-service-initializers/static-r1'
sys.path.insert(0, str(ROOT / 'tools/m4-service-initializers'))
from recover import Module, ROW, DECODER, walk, relative_target, require, bind, save

IDENTITIES = {
 'MW3/Mech3.exe':'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',
 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL':'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
 'tools/analysis/pe.py':'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638',
 'tools/m4-service-initializers/recover.py':'21ae20b58d77c7a713c124a8b6506f373788398b700ea34ebc01206193bef09b',
 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe':'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a',
}

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def ingest(module, rows):
 for row in rows:
  off,_=module.image.rva_range(row['pc']-module.base,row['size'])
  require(module.image.read(off,row['size'])==bytes.fromhex(row['bytes']), 'Original row bytes changed')
  require(row['pc'] not in module.rows or module.rows[row['pc']]==row, 'Conflicting original instruction row')
  module.rows[row['pc']]=row

def decode(module, start, stop, out, commands):
 target=out/f'{module.path.name}-{start:08x}-{stop:08x}.txt'
 require(not target.exists(), 'Fresh exact decode only')
 command=[str(DECODER),'--disassemble','--x86-asm-syntax=intel',f'--start-address={start}',f'--stop-address={stop}',str(module.path)]
 result=subprocess.run(command,capture_output=True,check=True,timeout=30)
 target.write_bytes(result.stdout)
 rows=[]
 for line in result.stdout.decode('utf-8').splitlines():
  match=ROW.match(line)
  if not match:continue
  asm=re.sub(r'\s+',' ',match[3].strip()); m,_,o=asm.partition(' ');code=bytes.fromhex(match[2])
  rows.append(dict(pc=int(match[1],16),size=len(code),bytes=code.hex(),mnemonic=m,operands=o))
 ingest(module,rows);commands.append(dict(command=command,output=bind(target)))
 require(start in module.rows, 'Requested exact boundary was not decoded')

def complete_graph(module, entry, out, commands):
 # Normal instruction tails can be cold. Decode each missing exact boundary,
 # not a fictitious fallthrough beyond an import, RET or indirect dispatch.
 for _ in range(120):
  node=walk(module,entry)
  missing=[r['pc'] for r in node['unresolved_controls'] if r['reason']=='no exact file-backed decoded executable boundary' and module.executable(r['pc'])]
  if not missing:return node
  for pc in sorted(set(missing)):decode(module,pc,pc+512,out,commands)
 raise ValueError('Supplemental graph decode bound')

def closure(module, entries, out, commands, stops=(), maximum=260):
 todo=deque(entries);nodes={};deferred=set()
 while todo:
  entry=todo.popleft()
  if entry in nodes or entry in deferred:continue
  if entry in stops or not module.executable(entry) or len(nodes)>=maximum:
   deferred.add(entry);continue
  node=complete_graph(module,entry,out,commands);nodes[entry]=node
  todo.extend(r['target'] for r in node['direct_calls'])
 return nodes, sorted(deferred)

def descendants(nodes, entry):
 todo=[entry];seen=set()
 while todo:
  e=todo.pop()
  if e in seen:continue
  seen.add(e)
  if e in nodes:todo.extend(r['target'] for r in nodes[e]['direct_calls'])
 return sorted(seen)

def requirements(nodes, entries):
 bodies=[nodes[e] for e in entries if e in nodes]
 rows={r['pc']:r for n in bodies for r in n['instructions']}
 return dict(local_entries=entries,unique_instructions=len(rows),unique_bytes=sum(r['size'] for r in rows.values()),
  imported_services=sorted({r['symbol']['library']+':'+str(r['symbol'].get('name',r['symbol'].get('ordinal'))) for n in bodies for r in n['import_sites']}),
  import_sites=[r for n in bodies for r in n['import_sites']],FS_sites=sorted({r['pc'] for n in bodies for r in n['FS_sites']}),
  unresolved_controls=[r for n in bodies for r in n['unresolved_controls']],
  exact_rows_sha256=hashlib.sha256(b''.join(bytes.fromhex(rows[pc]['bytes']) for pc in sorted(rows))).hexdigest())

def main():
 ap=argparse.ArgumentParser();ap.add_argument('output');args=ap.parse_args();out=Path(args.output).resolve()
 require(out.parent==ROOT/'reports/m4-onexit-batch-recovery' and not out.exists(),'Fresh owned recovery output required')
 out.mkdir(parents=True); bindings=[]
 for p,h in IDENTITIES.items():
  q=ROOT/p;require(sha(q)==h,'Admitted source/tool identity changed');bindings.append(bind(q))
 # Freeze all pre-existing dossier dependencies by their existing receipt.
 frozen=json.loads((BASE/'final-pins.json').read_text())
 old=frozen.get('bindings',[])
 if not old:
  old=[dict(path=p,sha256=h)for p,h in frozen.get('files',{}).items()]
 require(bool(old),'Existing final pin map schema')
 for item in old:require(sha(item['path'])==item['sha256'],'Frozen dossier dependency changed')
 inputs=['final-report.json','final-pins.json','root-classification.json','game-all-initializer-graphs.json',
  'game-extra-callback-SEH-graphs.json','aligned-entry-handler-provider-supplement.json','MSVCRT.DLL.provider.json','next-native-closure-plan.json']
 bindings.extend(bind(BASE/p)for p in inputs)
 classes=json.loads((BASE/'root-classification.json').read_text())
 group=[g for g in classes['groups']if g['import_set']==['MSVCRT.dll:__dllonexit','MSVCRT.dll:_onexit'] and not g['FS'] and g['unresolved_controls_per_root']==0]
 require(len(group)==1 and group[0]['count']==26 and len(group[0]['roots'])==26,'Exact source registration group')
 roots=group[0]['roots'];game=Module(ROOT/'MW3/Mech3.exe');crt=Module(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL');commands=[]
 game_nodes=json.loads((BASE/'game-all-initializer-graphs.json').read_text())
 extra=json.loads((BASE/'game-extra-callback-SEH-graphs.json').read_text())['graphs']
 supplement=json.loads((BASE/'aligned-entry-handler-provider-supplement.json').read_text())
 provider=json.loads((BASE/'MSVCRT.DLL.provider.json').read_text())
 for n in list(game_nodes.values())+list(extra.values())+list(supplement['game_graphs'].values()):ingest(game,n['instructions'])
 for n in list(provider['graphs'].values())+list(supplement['MSVCRT_graphs'].values()):ingest(crt,n['instructions'])
 # Short fresh source checks independently bind the registry's real inputs.
 for start,stop in [(0x5AC110,0x5AC155),(0x5AC580,0x5AC586),(0x5AC3D8,0x5AC3EC)]:decode(game,start,stop,out,commands)
 for start,stop in [(0x78004482,0x780044A8),(0x78004A36,0x78004A7B),(0x78002FE5,0x7800304A),(0x78001514,0x7800151D),(0x7801E27B,0x7801E2EB),(0x78005516,0x780055AE)]:decode(crt,start,stop,out,commands)
 normal,deferred=closure(game,[r['entry']for r in roots],out,commands)
 require(not deferred,'Selected normal graph deferred')
 root_records=[];callback_entries=set()
 for r in roots:
  slot=r['slot'];off,_=game.image.rva_range(slot-game.base,4)
  require(struct.unpack('<I',game.image.read(off,4))[0]==r['entry'],'Original table slot changed')
  entries=descendants(normal,r['entry']);summary=requirements(normal,entries)
  require(not summary['FS_sites'] and not summary['unresolved_controls'] and summary['imported_services']==['MSVCRT.dll:__dllonexit','MSVCRT.dll:_onexit'],'Selected normal dependency group changed')
  require(summary['unique_instructions']==r['unique_instructions'],'Frozen normal source census changed')
  regs=[]
  for e in entries:
   n=normal[e];byend={a['pc']+a['size']:a for a in n['instructions']}
   for call in n['direct_calls']:
    if call['target']!=0x5AC140:continue
    prior=byend.get(call['site']);require(prior and prior['mnemonic']=='push' and prior['operands'].startswith('0x'),'Registration callback must come from literal source PUSH')
    callback=int(prior['operands'],16);require(game.executable(callback),'Guest callback is exact executable address')
    regs.append(dict(push_pc=prior['pc'],callback=callback,CALL_pc=call['site'],wrapper=call['target'],return_pc=call['return_pc']))
    callback_entries.add(callback)
  require(len(regs)==1,'Exactly one source registration per selected root')
  root_records.append(dict(**r,normal=summary,registration=regs[0],callback_execution_claimed=False))
 callbacks,callback_deferred=closure(game,sorted(callback_entries),out,commands,maximum=220)
 callback_records=[dict(entry=e,**requirements(callbacks,descendants(callbacks,e)),execution_claimed=False)for e in sorted(callback_entries)]
 crt_core,crt_deferred=closure(crt,[0x78004482,0x78004A36,0x78002FE5],out,commands,stops=(0x7800BADB,))
 termination=complete_graph(crt,0x78005516,out,commands)
 save(out/'game-normal-graphs.json',normal);save(out/'callback-graphs.json',callbacks);save(out/'provider-graphs.json',crt_core)
 save(out/'registration-roots.json',root_records);save(out/'callback-dependencies.json',dict(callbacks=callback_records,deferred=callback_deferred,scope='Source registered targets and static outgoing dependency closure; no dispatch or cleanup execution'))
 save(out/'termination-frontier.json',dict(core=termination,scope='Reverse-dispatch source and exact outgoing services only; full exit/flush/termination not claimed',unresolved_callback_site=0x78005560))
 sentinels=[game.rows[p]for p in(0x5AC3D8,0x5AC3E2)]
 require([r['operands'] for r in sentinels]==['dword ptr [0x9a17ec], 0xffffffff','dword ptr [0x9a17f0], 0xffffffff'],'Exact original sentinel stores')
 require(crt.data(0x78037C18,4)['initial_hex']==struct.pack('<I',0x78004482).hex(),'Original CRT table producer slot')
 save(out/'registry-inputs.json',dict(game_sentinel_rows=sentinels,game_sentinel_initial=[game.data(p,4)for p in(0x9A17EC,0x9A17F0)],
  game_wrappers=[normal[e]for e in(0x5AC110,0x5AC140,0x5AC580)],provider_table_slot=crt.data(0x78037C18,4),
  original_producer=crt_core[0x78004482],provider_data=[crt.data(p,4)for p in(0x78037888,0x7803788C,0x78035000,0x78035004,0x78037150)],
  provider_exports=[dict(requested=e['requested'],export=e['export'],preferred_va=e['preferred_va'],actual_loaded_module_known=False)for e in provider['requested_exports']if e['requested']in('_onexit','__dllonexit')],
  owning_game_IAT=[dict(address=p,raw=game.data(p,4),symbol=game.imports[p])for p in(0x5BB52C,0x5BB530)],
  new_native_API_contracts=[dict(source_pc=p,IAT=s,raw=crt.data(s,4),symbol=crt.imports[s])for p,s in((0x780015B5,0x7802E1DC),(0x78011C27,0x7802E0B4))]))
 # Machine plan distinguishes reusable semantics from still-unimplemented paths.
 plan=dict(scope='Complete researched callback-registration batch; not original DLL attach, full exit or native execution',roots=26,
  initial_state='Carry a fresh accepted live heap/critical-section run and original game entry sentinel source effects; no final capture reseed',
  producer=dict(entry=0x78004482,requested_bytes=128,begin_store=0x7800448F,first_zero_store=0x7800449A,next_store=0x780044A2,RET=0x780044A7,fatal_allocation_CALL=0x7801E2D4,fatal_target=0x7800BADB),
  normal_onexit=dict(entry=0x78004A36,lock_number=13,HeapSize_CALL=0x780015B5,append=0x78004A67,advance=0x78004A69,return_callback_or_zero=True),
  growth=dict(onexit_target=0x7801E27B,requested='actual source _msize capacity +16',realloc=0x780019F1,mode1_HeapReAlloc_CALL=0x78011C27,failure_preserves_old_table=True,relocate_begin_and_next_from_source=True),
  alternate_dllonexit=dict(entry=0x78002FE5,arguments=['callback','address of game begin','address of game next'],sentinel_selects_this_only_when_begin_not_minus_one=True,capacity_branch=0x78003004,failure_target=0x7801E2E4),
  ABI='Original 32-bit cdecl CALL/RET/stack cleanup and source FS frames; native heap/CS pointers remain privately full width, callback values remain checked guest code addresses',
  reuse=['Accepted mode-1 heap initializer/malloc/free bodies and checked multi-allocation ownership','Accepted normal FS/SEH registration and typed native critical sections; implement distinct lazy lock13 with actual source allocation, not a no-op','Literal original rows and current State3504/FX512/hardware boundary preservation','Direct bounded strict capture writer and source-derived independent model'],
  new_implementation=['Typed HeapSize returns actual size/error witness, never requested-size substitution','Typed HeapReAlloc commits alias relocation and byte preservation only on actual success; null retains original allocation','Literal table producer, _onexit/__dllonexit,_msize,realloc mode1, wrappers and all26 source root bodies','Callback identities, append order, failure0/-1 and source flag effects, poisoned fault cleanup and last-error ownership'],
  runtime_domains=['Actual mode1, newmode0, valid owned nonnull table/positive bounded growth. Modes2/3, reallocNULL/size0 and new-handler routes preserved as open dependencies unless separately admitted','Actual HeapSize may exceed requested128; exact growth trigger uses measured capacity. Directed repeated original roots may produce enough registrations, labelled research replay rather than original startup','Game alternate DLL table path needs separately owned source-established begin/next; two zero file globals do not establish a usable table'],
  required_native_checks=['Run26 roots in actual relative table order on persistent live ownership; compare actual State/FX/pages/ordered accesses and source/API checkpoints at O0/O2','Execute source growth when actual capacity is exceeded, preserving callback vector and real moved/unchanged pointer identity','Registration failure control keeps prior source constructor/global writes and returns source EAX-1; no fabricated rollback','Wrong/stale/foreign aliases, callback/IAT/source identities, permissions, owner/thread, partial relocation faults and cleanup/retry poisoning','Independently derive outputs from original BEFORE and actual API witness, no AFTER model seeding'],
  cleanup='Registry allocation cleanup uses genuine free through the owner after live registry/ordered callback vector observation; no call into OS using guest callback pointer. Reverse exit dispatch is separate unless fully implemented',
  callback_limits='Registered callbacks are fully inventoried separately. Their indirect destructors, remaining imports and eventual reverse dispatch are not established by successful registration.',
  provider_deferred=crt_deferred,full_startup=False,initializer_count_credit=False,native_execution=False)
 save(out/'whole-batch-contract.json',plan);save(out/'decode-commands.json',commands)
 bindings.append(bind(Path(__file__).resolve()))
 artifacts=[bind(p)for p in sorted(out.iterdir())if p.is_file()]
 report=dict(passed_static_recovery=True,scope='Exact26 registration roots, source registry inputs/normal provider and deferred termination contracts; no execution/lift/initializer admission',
  root_count=26,callback_targets=len(callback_entries),normal_graph_entries=len(normal),callback_graph_entries=len(callbacks),provider_graph_entries=len(crt_core),
  new_focused_decodes=len(commands),new_original_bytes=sum(sum(r['size']for r in n['instructions'])for n in callbacks.values()),
  callback_unresolved_sites=len({r['pc']for n in callbacks.values()for r in n['unresolved_controls']}),callback_deferred=callback_deferred,provider_deferred=crt_deferred,
  all_prior_dossier_bindings_rehashed=len(old),input_bindings=bindings,artifacts=artifacts,native_executed=False,game_launched=False,roots_admitted=0,whole_M4=False)
 save(out/'report.json',report)
 save(out/'pins.json',dict(files={a['path']:a['sha256']for a in bindings+artifacts+[bind(out/'report.json')]},scope='Private exact static preparation only'))
 print(json.dumps(dict(passed_static_recovery=True,report_sha256=sha(out/'report.json'),roots=26,callbacks=len(callback_entries),normal_entries=len(normal),callback_entries=len(callbacks),provider_entries=len(crt_core),new_decodes=len(commands),deferred=crt_deferred)))

if __name__=='__main__':main()
