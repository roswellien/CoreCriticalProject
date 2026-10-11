"""Current borrowed registry provider plus literal widget tail, from own BEFORE.

The independently computed widget prefix must already match this provider entry.
Only finite actual WinAPI witnesses are inputs at recovered source API CALLs.
No provider AFTER State, stack or memory is transported to the model.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('widget_registry_io',R/'tools/m4-fps-native/compare_prefix_v2.py');C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C)
need=C.need;eq=C.eq;raw=C.raw;read=C.read;pin=C.pin;sha=C.sha
def checkpoint_memory(folder,n):
 result={}
 for f in folder.glob(f'registry-checkpoint-{n}-page-*.bin'):
  a=int(f.stem.split('-page-')[1]);b=raw(f);need(b and len(b)%4096==0,'Complete actual checkpoint page/capacity');result[a]=bytearray(b)
 return result
def facts(folder):
 values=[]
 for n,f in enumerate(sorted(folder.glob('locale-api-*-witness.bin'),key=lambda p:int(p.stem.split('-')[2]))):
  w=struct.unpack('<32Q',raw(f));need(w[0:2]==(1,n),'Complete actual global WinAPI index');stem=folder/f'locale-api-{n}';buffers=C.rows(raw(str(stem)+'-buffers.bin'),16,'<4I')
  def payload(kind):return [raw(q)for q in sorted(folder.glob(f'locale-api-{n}-{kind}-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))]
  sys.path.insert(0,str(R/'tools/m4-onexit-review'));import provider_responses_v2 as typed
  contracts=typed.B.contracts();contracts.update(typed.NEW_CONTRACTS)
  if w[31]==1:
   need(w[2]==0 and w[8]==1 and w[14:16]==(1,1),'Exact lifecycle observation marker/status')
   if (w[3],w[4])==(0x78146190,0x866ce):name_='MSVCP-resource-association'
   else:
    need((w[3],w[4])==(0x7802e040,0x3446a),'Only exact physical native DeleteCriticalSection cleanup identity');name_='unmodeled-native-cleanup-DeleteCriticalSection'
  else:
   need(w[2]in contracts,'Every actual API has a recovered literal contract');name_=contracts[w[2]]['name']
  values.append(dict(words=w,buffers=buffers,inputs=payload('input'),outputs=payload('output'),name=name_))
 return values
def main(execution,execution_sha,prefix_path,prefix_sha,name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh independent current service source receipt');out.mkdir();passed=False;counts=collections.Counter();results=[]
 try:
  pin(C.__file__);e=read(execution,execution_sha);p=read(prefix_path,prefix_sha);need(e['passed']and p['passed']and p['execution_sha256']==execution_sha,'Actual passed widget execution and its exact own-BEFORE prefix gate');need(p['AFTER_State_or_memory_seed']is False and p['whole_registration_provider_source_model']is False,'Prefix terminal scope explicitly bounded');derivations=read(Path(prefix_path).parent/'source-derivations.json',p['files'][str((Path(prefix_path).parent/'source-derivations.json').resolve())]);need(len(derivations)==14,'Fourteen physically bound prefix entry joins')
  G=C.load(R/'reports/m4-fps-original/source-preparation-r4/game_model.py','widget_registry_literal');program,callbacks=G.source_program();sys.path.insert(0,str(R/'tools/m4-onexit-review'));import provider_responses_v2 as responses_module
  provider=read(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d');need(provider['schema']=='mw34-onexit-independent-provider-source-v1'and not provider['AFTER_machine_seed'],'Frozen original-byte literal provider closure')
  for row in provider['instructions']:
   pc=row['pc'];need(pc not in program or program[pc]==row,'Identical shared literal game/provider row');program[pc]=row
  provider_callbacks=read(R/'reports/m4-onexit-review/callbacks-r1/callbacks.json','3c0a5fab10ec834c8e027ed88a8443b7d63d559c151d40ade6a045a71ce1565d')['State_offsets_by_original_PC']
  for pc,offsets in provider_callbacks.items():
   pc=int(pc);offsets=tuple(offsets);need(pc not in callbacks or callbacks[pc]==offsets,'Identical shared provider undefined callback attribution');callbacks[pc]=offsets
  need(0x78004a36 in program,'Literal onexit source entry exists before interpreter starts')
  game=raw(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');nt=struct.unpack_from('<I',game,0x3c)[0];ns=struct.unpack_from('<H',game,nt+6)[0];opt=struct.unpack_from('<H',game,nt+20)[0];base=struct.unpack_from('<I',game,nt+24+28)[0]
  exact_contract=read(R/'reports/m4-fps-native/component-preparation-r1/contracts.json');epilogue=exact_contract['registration_epilogues'][-1];need(epilogue['root']==0x40f000 and epilogue['source_read_PC_and_frame_offsets']==[[0x5ac127,-16,4,False],[0x5ac154,-8,4,False],[0x40f02d,0,4,False]],'Three literal saved-return reads use exact affine FPS frames')
  rows_={v['pc']:v for v in exact_contract['instructions']}
  for pc in epilogue['source_PCs']:
   row=rows_[pc];payload=bytes.fromhex(row['bytes_hex']);matches=[];rva=pc-base
   for i in range(ns):
    off=nt+24+opt+40*i;vs,va,rs,ro=struct.unpack_from('<IIII',game,off+8)
    if va<=rva and rva+len(payload)<=va+rs:matches.append(game[ro+rva-va:ro+rva-va+len(payload)])
   eq(matches,[payload],'Whole actual physical FPS ten-instruction registration epilogue');counts['physical_additive_FPS_tail_instruction_joins']+=1
  contract=read(R/'reports/m4-fps-native/component-preparation-r1/contracts.json');tail=read(R/'reports/m4-widget-original-review/registration-tail-r1/report.json','abaa48c8dd533c56cdbd48118676bf0800f0c942ce9319a537a03c4c4b4f3cb5');need(tail['passed'],'Exact independently reviewed prior six widget tails');need(len(contract['registration_epilogues'])==7,'Exact additive FPS tail contract')
  pin(R/'reports/m4-fps-native/service-preparation-r2/locale_batch_operations.inc');pin(R/'reports/m4-fps-native/service-preparation-r2/lockit_operations.inc')
  for level in('O0','O2'):
   folder=Path(e['runs'][level]['capture']);dump=folder/'cleanup';all_facts=facts(dump);index=C.checkpoint_index(dump);before=[n for n,label in index if label=='widget-onexit-before'];after=[n for n,label in index if label=='widget-onexit-after'];need(len(before)==len(after)==7 and all(b<a for b,a in zip(before,after)),'Seven ordered actual provider entry/return boundaries');source_ledger=C.rows(raw(dump/'locale-source-accesses.bin'),24,'<IIQII');allocs=C.rows(raw(dump/'locale-allocations.bin'),128,'<16Q');owner_by_guest={w[1]:w for w in allocs};last_source_cursor=0
   for phase,root in enumerate(contract['roots']):
    b,a=before[phase],after[phase];prefix=next(d for d in derivations if d['level']==level and d['phase']==phase);need(prefix['root']==root['root']and prefix['provider_checkpoint']==b,'Current prefix-to-provider entry identity');state=raw(dump/f'registry-checkpoint-{b}-state.bin');need(hashlib.sha256(state).hexdigest()==prefix['computed_provider_entry_State_sha256'],'Provider own BEFORE exactly equals computed source prefix State');fx=raw(dump/f'registry-checkpoint-{b}-fx.bin');cpu=raw(dump/f'registry-checkpoint-{b}-cpu.bin');memory=checkpoint_memory(dump,b);component_before=folder/f'phase-{phase}'/f"root-{root['root']}"/'before';component_state=raw(component_before/'State.bin');frame=struct.unpack_from('<I',component_state,G.I.REG['esp'])[0];CPU=C.words(cpu,10);need(CPU[4]==frame-24 and CPU[9]==0x78004a36,'Exact source borrowed-provider affine CALL frame')
    # The minimal Runtime TIB is supplied as its four actual own BEFORE fields.
    tib=C.words(raw(folder/f'phase-{phase}'/'before'/'TIB.bin'),5)
    for offset,value in ((0,tib[1]),(4,tib[2]),(8,tib[3]),(24,tib[4])):memory[tib[0]+offset]=bytearray(struct.pack('<I',value))
    names=[label for n,label in index if b<n<a];api_indices=[int(re.fullmatch(r'locale-api-(\d+)-before',v).group(1))for v in names if re.fullmatch(r'locale-api-(\d+)-before',v)];need(api_indices and api_indices==list(range(api_indices[0],api_indices[-1]+1)),'Finite chronological provider API interval');start,end=api_indices[0],api_indices[-1]+1
    cleanup=[v for v in all_facts if v['name']=='unmodeled-native-cleanup-DeleteCriticalSection'];need(len(cleanup)==5 and all(v['words'][1]>=end for v in cleanup),'All five native cleanup observations are beyond this modeled provider interval');counts['unmodeled_cleanup_after_interval_joins']+=len(cleanup)
    response=responses_module.ActualResponses(all_facts);response.index=start
    # Associate prior actual API-owned resources with current whole BEFORE bytes.
    # This is an explicit own-resource entry contract; bootstrap proof is separate.
    for fact in all_facts[:start]:
     w=fact['words']
     if w[31]==1 and w[2]==0 and w[3]==0x78146190:
      response.generation+=1;response.sections[0x78145640]=dict(generation=response.generation,depth=0,native=w[16],enters=0,leaves=0,initialized=True,deletes=0);continue
     c=response.contracts.get(w[2]);need(c is not None,'Each prior source resource API has an independent recovered contract');name_=c['name']
     if name_=='InitializeCriticalSection':
      response.generation+=1;response.sections[w[20]]=dict(generation=response.generation,depth=0,native=w[16],enters=0,leaves=0,initialized=True,deletes=0)
     elif name_=='EnterCriticalSection':response.sections[w[20]]['depth']+=1;response.sections[w[20]]['enters']+=1
     elif name_=='LeaveCriticalSection':response.sections[w[20]]['depth']-=1;response.sections[w[20]]['leaves']+=1
     elif name_=='HeapAlloc':
      owner=owner_by_guest.get(w[12]);need(owner and owner[0]==1 and owner[3]==w[13]and owner[4]%4096==0 and owner[5]==response.generation+1,'Exact prior native owner generation and mapped capacity');response.generation+=1;entry=dict(guest=w[12],requested=owner[2],extent=w[13],mapped=owner[4],generation=response.generation,native=w[8],live=True,initial=fact['outputs'][0],capacity=0,previous_native=0);response.allocations.append(entry);response.allocation_cursor=max(response.allocation_cursor,w[12]+owner[4]);need(w[12]in memory and len(memory[w[12]])==owner[4],'Prior live complete capacity is present in own provider BEFORE')
     else:need(name_ in('HeapSize',),'Prior registry domain contains only declared allocation/CS API effects')
    class Provider(G.Machine):
     def snapshot(self,name):
      # Serialization only; no callback or captured expected state enters source.
      self.phases[name]=dict(state=bytes(self.state).hex(),CPU=list(self.projected_cpu()),fx=self.fx.hex(),source_access_index=len(self.accesses))
    m=Provider(state,fx,cpu,memory,program=program,callbacks=callbacks);m.responses=response
    # These three saved words were written by independently reviewed literal CALLs.
    registration=root['registration'];site=registration.get('CALL_pc',registration.get('registration_CALL_pc'));returns=((root['root'],frame,0xfffffff0,0),(0x5ac140,frame-8,site+5,site),(0x5ac0e0,frame-16,0x5ac14a,0x5ac145),(0x78004a36,frame-24,0x5ac124,0x5ac11e))
    for target,sp_,ret,call in returns:
     need(int.from_bytes(m.bytes(sp_,4),'little')==ret,'Whole source-established current saved return word');m.call_stack.append((target,sp_,ret,call,CPU[5],CPU[3],CPU[6],CPU[7],0))
    m.run(lambda x:x.cursor==0x5ac124,api=response);need(response.index==end,'Complete exactly bounded provider actual API exhaustion');provider_accesses=list(m.accesses);eq(bytes(m.state),raw(dump/f'registry-checkpoint-{a}-state.bin'),'Whole provider State3504 independently derived from own entry');eq(tuple(m.projected_cpu()),C.words(raw(dump/f'registry-checkpoint-{a}-cpu.bin'),10),'Whole literal provider CPU40');eq(m.fx,raw(dump/f'registry-checkpoint-{a}-fx.bin'),'Whole guest provider FX512 unchanged')
    actual_pages=checkpoint_memory(dump,a)
    for address,payload in actual_pages.items():eq(m.bytes(address,len(payload)),bytes(payload),'Whole source/API-derived provider page/capacity '+hex(address));counts['whole_provider_page_or_capacity_relations']+=len(payload)//4096
    markers=[i for i,row in enumerate(source_ledger)if i>=last_source_cursor and row==(0x5ac11e,0x5bb52c,0x1decb0,4,0)];need(markers,'Actual source borrowed CALL witness exists');cursor=markers[0];borrow=[(0x5ac11e,0x5bb52c,0x1decb0,4,0),(0x5ac11e,frame-24,0x5ac124,4,1)];eq(source_ledger[cursor:cursor+2],borrow,'Exactly two declared borrowed source operands');eq(source_ledger[cursor+2:cursor+2+len(provider_accesses)],[tuple(v)for v in provider_accesses],'All genuine accepted provider source operands independently derived');last_source_cursor=cursor+2+len(provider_accesses);counts['literal_provider_operands']+=len(provider_accesses);counts['actual_source_API_joins']+=end-start
    tail_start=len(m.PCs);m.run(lambda x:x.cursor==0xfffffff0);tailPCs=m.PCs[tail_start:];need(tailPCs==next(v['source_PCs']for v in contract['registration_epilogues']if v['root']==root['root']),'Exact ten physical tail instructions execute after real provider return');after_component=folder/f'phase-{phase}'/f"root-{root['root']}"/'after';eq(bytes(m.state),raw(after_component/'State.bin'),'Whole source-derived final widget State3504');eq(tuple(m.projected_cpu()),C.words(raw(after_component/'CPU.bin'),10),'Whole source-derived widget final CPU40');eq(m.fx,raw(after_component/'FX.bin'),'Whole widget final FX512');eq(m.bytes(0x20001000,4096),raw(folder/f'phase-{phase}'/'after'/'stack.bin'),'Complete final root stack from source prefix, provider and literal tail');need(not m.call_stack and m.reg('esp')==frame+4,'Complete source root RET and all four real frames balanced');counts['whole_source_root_State3504_relations']+=1;counts['whole_source_root_stack4096_relations']+=1;counts['literal_tail_instructions']+=len(tailPCs);counts['literal_tail_RET_operand_relations']+=len(m.accesses)-len(provider_accesses)
    results.append(dict(level=level,phase=phase,root=root['root'],source_PCs=m.PCs,provider_source_accesses=provider_accesses,tail_source_accesses=m.accesses[len(provider_accesses):],source_API_indices=api_indices,source_API_phases=m.phases,source_computed_final_State_sha256=hashlib.sha256(bytes(m.state)).hexdigest(),bootstrap_resource_association_input=True,bootstrap_source_execution_modeled=False,AFTER_machine_seed=False))
  need(counts['whole_source_root_State3504_relations']==14 and counts['literal_tail_instructions']==140 and counts['literal_tail_RET_operand_relations']==42,'Exact seven-root both-level source tail extent');passed=True
 except BaseException:
  passed=False;(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'source-derivations.json';q.write_text(json.dumps(results,indent=2)+'\n');pin(q);pin(__file__);pin(sys.executable)
  for q in list(C.READS):pin(q)
  report=dict(passed=passed,scope='Current borrowed source onexit bodies and ten-instruction widget return tails from exact prefix-computed provider entry, current own-resource BEFORE contracts and literal API witnesses; bootstrap and teardown source proof remain separate',execution_sha256=execution_sha,prefix_source_sha256=prefix_sha,counts=dict(counts),successful_read_chain_pinned=C.READS<=set(C.PINS),actual_successful_read_dependencies=len(C.READS),AFTER_machine_or_memory_seed=False,bootstrap_resources_are_own_BEFORE_inputs=True,bootstrap_source_execution_modeled=False,cleanup_source_execution_modeled=False,connected_initializer_credit=0,archive_reader_opened=False,files=C.PINS);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=passed,counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
