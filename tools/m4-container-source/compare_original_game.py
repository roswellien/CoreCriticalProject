"""Original109 game prefixes and persistent shared owners from authentic BEFORE.

Each constructor prefix uses its actual complete BEFORE machine, as in the
accepted103 prefix gate. New allocated owners are never reseeded: their true API
initial backing and all source writes carry across the complete116-root order.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-container-source';PINS={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Frozen source input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable source input');PINS[str(p)]=v;return p
def own(p,n):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original source gate');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[];ownerrows=[];derivations=[];headerrows=[]
 try:
  O=own(ROOT/'tools/m4-mfc-source/compare_original_game.py','accepted103_prefix_helpers');G=own(ROOT/'tools/m4-container-source/game_model.py','original116_game_model');J=own(ROOT/'tools/m4-joint-startup27-review/observe.py','original116_numeric_projection');m,_,_,_=J.models();D=own(ROOT/'tools/m4-crt-allocation-root/run_v2.py','original116_saved_archive')
  pin(BASE/'original-validation-r1/report.json','4012b8c62c821131469e012f1e10ba31b621c524c6b0a9b042d5150dd2f3067b');O.PAGES=tuple(json.loads(pin(BASE/'original-preparation-r2/report.json','fc3ce8ef54040236bced7072b3c121a0a7121c19ca81ef6e19ae0f54d5a06c49').read_bytes())['observed_pages']);O.MEM0,O.MEM1,O.END=2276,153828,305380;m.PAGES=list(O.PAGES)
  reader=D.DirectSet(BASE/'original-execution-r1/original/transport.json',pin)
  roots=[]
  for path in('reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','reports/m4-strings-source/recovery-r7/string-roots.json','reports/m4-mfc-source/recovery-r4/mfc-roots.json','reports/m4-fs-source/recovery-r3/fs-roots.json','reports/m4-container-source/recovery-r3/container-roots.json'):roots+=json.loads(pin(ROOT/path).read_bytes())
  lookup={r['entry']:r for r in roots};need(len(roots)==88,'All88 original registration roots');contract=json.loads(pin(BASE/'recovery-r3/instruction-contracts.json').read_bytes());order=contract['selected_order'];fsbindings=json.loads(pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes());containerbindings=json.loads(pin(BASE/'allocation-interface-r1/allocation-inputs.json','d8e8e7c495f86700f8a274615d46976fd02f7eda7b8af031b80a12e89d7c2d71').read_bytes());oldbindings=json.loads(pin(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/allocation-inputs.json').read_bytes());program,callbacks=G.source_program();original_normalize=O.normalize_memory
  def normalize(data,spi):
   pages=original_normalize(data,spi)
   for address,actual,raw in ((0x5bb454,0x5f4020b4,0x8000021c),(0x5bb4c8,0x5f401782,0x80000339)):
    need(words(pages[0x5bb000],address&4095)[0]==actual,'Authentic new original owning ordinal import');struct.pack_into('<I',pages[0x5bb000],address&4095,raw)
   return pages
  O.normalize_memory=normalize;O.MFC_IMPORTS=[(v[0],v[1],v[2])for v in struct.iter_unpack('<7I',reader.data('mfc-import-ledger.bin'))];need(len(O.MFC_IMPORTS)==511,'Authenticated original MFC loaded imports')
  try:
   for seq in range(6):
    previous=None;seen=[];fsowners={};containerowners={};firstfs=next(i for i,v in enumerate(order)if v['entry']==0x46ab30);head=words(reader.data(f'phase/{seq}/{firstfs}/fs-events.bin'),16)[0];fsbytes=bytearray(struct.pack('<I',head));sequence_events=0
    for phase,item in enumerate(order):
     entry=item['entry'];b=reader.data(f'phase/{seq}/{phase}.bin');need(len(b)==307840 and words(b,0,5)==(seq,words(b,4)[0],phase,item['slot'],entry),'Actual complete original phase association')
     if previous is not None:
      need(b[O.MEM0:O.MEM1]==previous[O.MEM1:O.END],'All35 actual original game pages carry');need(b[116:628]==previous[628:1140]and b[2164:2192]==previous[2192:2220],'Whole original FX/ENV carry');cpu=list(words(previous,76,10));cpu[4]=0x20001800;cpu[9]=entry;need(words(b,36,10)==tuple(cpu),'Whole original CPU carries between roots')
     previous=b
     if entry in lookup:
      memory=O.normalize_memory(b[O.MEM0:O.MEM1],0x1df20c);after=O.normalize_memory(b[O.MEM1:O.END],0x1df20c);memory[0x7ffde000]=fsbytes
      for owner in list(fsowners.values())+list(containerowners.values()):memory[owner['pointer']]=owner['modeled_bytes']
      cpu=words(b,36,10);state=bytearray(O.original_state(m,G,cpu,b));struct.pack_into('<I',state,2168,0x7ffde000)
      actual_events=reader.data(f'phase/{seq}/{phase}/fs-events.bin');event_index=[0];event_derivations=[]
      def fs_event(model,address,value,size,pc,write):
       if address!=0x7ffde000:return
       need(size==4 and(event_index[0]+1)*1216<=len(actual_events),'Every modeled FS access joins actual original event');row=actual_events[event_index[0]*1216:(event_index[0]+1)*1216];v,r,apc,kind,bh,ah,record,captured=words(row,0,8);before=words(row,32,10);need(r==entry and pc==apc and write==(kind!=0),'Literal source FS PC/direction matches actual original MOV');need(model.reg('esp')==before[4],'Source-derived actual FS stack geometry');need(int.from_bytes(model.bytes(address,4),'little')==bh,'Authentic previous FS head from one actual initial scalar and source carry');need(value==(ah if write else bh),'Literal FS source load/store value');need(kind!=2 or model.reg('ecx')==before[1],'Literal saved predecessor source load');
       if captured:need(model.bytes(record,12)==row[112:124],'Every complete12B actual original frame derives from original BEFORE pushes/scope writes')
       event_derivations.append(dict(sequence=seq,phase=phase,root=entry,PC=pc,kind=kind,before_head=bh,after_head=ah,source_ESP=model.reg('esp'),record_address=record,record_hex=row[112:124].hex()if captured else None));event_index[0]+=1
      class PrefixMachine(G.Machine):
       def read(self,address,size=4,domain='source',pc=None):
        value=super().read(address,size,domain,pc);fs_event(self,address,value,size,self.word(2472) if pc is None else pc,False);return value
       def write(self,address,value,size=4,domain='source',pc=None):
        fs_event(self,address,value,size,self.word(2472) if pc is None else pc,True);return super().write(address,value,size,domain,pc)
      machine=PrefixMachine(state,b[116:628],b[36:76],memory,program=program,callbacks=callbacks);machine.call_stack.append((entry,0x20001800,0x410a80,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));allocation_calls=[];api=reader.data(f'phase/{seq}/{phase}/api-ledger.bin');allocs=[(k//104,words(api,k,26))for k in range(0,len(api),104)if words(api,k+96)[0]==0]
      def finite_malloc(model,target):
       site=model.PCs[-1];need(target==0x780012b3 and site in(0x78010a7e,0x5f401eb5),'Literal strdup/MFC malloc frontier');need(len(allocation_calls)<len(allocs),'Actual original malloc fact available');ai,fact=allocs[len(allocation_calls)];request=int.from_bytes(model.bytes(model.reg('esp')+4,4),'little');rounded=(request+15)&~15;need(fact[21]==0 and fact[22]==rounded and fact[10],'Actual HeapAlloc request/scalar');initial=reader.data(f'phase/{seq}/{phase}/api-initial/{ai}/bytes.bin');capacity=words(reader.data(f'phase/{seq}/{phase}/api-initial/{ai}/size.bin'))[0];need(len(initial)==capacity and capacity>=rounded,'True entire API initial backing before guest write');pointer=fact[10];need(not any(p<=pointer<p+len(v)for p,v in model.memory.items()),'Unique disjoint original heap owner');model.memory[pointer]=bytearray(initial);owner=dict(pointer=pointer,request=request,capacity=capacity,API_index=ai,site=site,modeled_bytes=model.memory[pointer],initial_sha256=hashlib.sha256(initial).hexdigest())
       if site==0x5f401eb5:
        frame=model.call_stack[-2];fs=[v for v in fsbindings if v['root']==entry and v['CALL_pc']==frame[3]];old=[v for v in oldbindings if v['root']==entry and v['CALL_pc']==frame[3]];container=[v for v in containerbindings if v['root']==entry and v['CALL_pc']==frame[3]];need(len(fs)+len(old)+len(container)==1,'One exact root/allocator CALL binding');binding=(fs+old+container)[0];need(request==binding['requested_size'],'Literal MFC requested size');owner['binding']=binding;owner['frame']=frame[1]
        if fs:
         fi=fsbindings.index(binding);meta=words(reader.data(f'phase/{seq}/{phase}/fs-allocation/{fi}/meta.bin'),0,9);need(meta==(1,fi,entry,frame[3],request,frame[1],ai,pointer,capacity),'True API/caller-stack-to-owner original join');owner['fs_index']=fi;need(fi not in fsowners,'One actual acquisition per exact successful site');fsowners[fi]=owner
       if site==0x5f401eb5 and container:
        ci=containerbindings.index(binding);meta=words(reader.data(f'phase/{seq}/{phase}/container-allocation/{ci}/meta.bin'),0,9);need(meta==(1,ci,entry,frame[3],request,frame[1],ai,pointer,capacity),'True original vector source frame/API owner join');owner['container_index']=ci;need(ci not in containerowners,'One actual new vector acquisition');containerowners[ci]=owner
       allocation_calls.append(owner);model.api_return(site,0,pointer)
      machine.run(stop=lambda x:x.cursor==0x78004a36,api=finite_malloc);need(event_index[0]*1216==len(actual_events),'No unmodeled original FS observation');sequence_events+=event_index[0];derivations+=event_derivations
      for carried_owner in list(fsowners.values())+list(containerowners.values()):carried_owner['modeled_bytes']=machine.memory[carried_owner['pointer']]
      fsbytes=machine.memory[0x7ffde000]
      if entry==0x4d4830:
       local=machine.accesses;writes=[(i,v)for i,v in enumerate(local)if v[0]==0x4d4922 and v[1]==0x60b51c and v[3:]==(1,1)];need(len(writes)==1,'One literal new FS header source write');wi,write=writes[0];reads=[(i,v)for i,v in enumerate(local[:wi])if v[0]==0x4d4914 and v[3:]==(1,0)];need(len(reads)==1,'Exact literal local byte read');ri,read=reads[0];need(write[2]==read[2],'Literal AL copy to static header');stores=[(i,v)for i,v in enumerate(local[:ri])if v[4]and v[1]<=read[1]<v[1]+v[3]]
       if stores:
        si,store=stores[-1];need((store[2]>>(8*(read[1]-store[1])))&255==read[2],'Exact last source store byte provenance');provenance=dict(kind='dominating_source_store',index=si,pc=store[0],address=store[1],value=store[2],width=store[3])
       else:
        offset=O.PAGES.index(0x20001000)*4096+read[1]-0x20001000;before_stack=b[O.MEM0:O.MEM1];need(before_stack[offset]==read[2],'Exact genuine original branch BEFORE stack byte provenance');provenance=dict(kind='genuine_branch_BEFORE_stack_byte',address=read[1],value=before_stack[offset],no_root_source_store_before_read=True)
       headerrows.append(dict(sequence=seq,phase=phase,root=entry,field=0x60b51c,write_pc=write[0],value=write[2],read_pc=read[0],read_address=read[1],branch_BEFORE_cpu=list(cpu),provenance=provenance))

      if 'string'in lookup[entry]:
       source=lookup[entry]['string'];need(len(allocation_calls)==int(source['actual_strdup_called']),'Actual null/string branch');
       if allocation_calls:
        owner=allocation_calls[0];raw=bytes.fromhex(source['bytes_hex']);need(owner['request']==len(raw)and machine.bytes(owner['pointer'],len(raw))==raw,'Literal original duplicated string byteflow');meta=words(reader.data(f'phase/{seq}/{phase}/strings/{entry}/meta.bin'),0,6);need(meta[:5]==(entry,source['source'],lookup[entry]['objects'][0]['address']+4,owner['pointer'],len(raw)),'Original duplicated string owner/field');counts['original_string_byteflows']+=1
       else:counts['original_null_descriptor_constructors']+=1
      for owner in allocation_calls:
       if 'binding'not in owner:continue
       binding=owner['binding']
       if 'fs_index'in owner:
        fi=owner['fs_index'];target=binding['publication']
        if not target:
         key=binding['publication_owner'];prior=next(v for v in fsowners.values()if v['binding']['root']==key['root']and v['binding']['CALL_pc']==key['CALL_pc']);target=prior['pointer']+key['offset']
        writes=[v for v in machine.accesses if v[0]==binding['publication_PC']and v[1]==target and v[2]==owner['pointer']and v[3]==4 and v[4]];need(len(writes)==1,'Exact source primary publication commit; later shared sentinel updates permitted by original source');ownerrows.append(dict(sequence=seq,index=fi,root=entry,CALL_pc=binding['CALL_pc'],request=owner['request'],pointer=owner['pointer'],capacity=owner['capacity'],publication_address=target,publication_PC=binding['publication_PC'],initial_sha256=owner['initial_sha256']));counts['new_FS_source_allocations']+=1
       elif 'container_index'in owner:
        ci=owner['container_index'];need(machine.bytes(binding['publication'],4)==struct.pack('<I',owner['pointer']),'Literal new vector primary pointer');need(bytes(owner['modeled_bytes'])==reader.data(f'phase/{seq}/{phase}/container-allocation/{ci}/bytes.bin'),'Entire untouched genuine new vector allocation bytes');writes=[v for v in machine.accesses if owner['pointer']<=v[1]<owner['pointer']+owner['capacity']and v[4]];need(not writes,'Empty vector source performs no owned-buffer write');ownerrows.append(dict(sequence=seq,index=ci,root=entry,CALL_pc=binding['CALL_pc'],request=owner['request'],pointer=owner['pointer'],capacity=owner['capacity'],publication_address=binding['publication'],publication_PC=binding['publication_PC'],initial_sha256=owner['initial_sha256'],kind='container'));counts['new_vector_source_allocations']+=1
       else:
        mi=oldbindings.index(binding);meta=words(reader.data(f'phase/{seq}/{phase}/mfc/{mi}/meta.bin'),0,8);need(meta[:5]==tuple(binding[k]for k in('root','CALL_pc','requested_size','object','publication'))and meta[5:]==(owner['pointer'],owner['capacity'],mi),'Old35 MFC owner join');need(machine.bytes(binding['publication'],4)==struct.pack('<I',owner['pointer']),'Literal old MFC publication');need(machine.bytes(owner['pointer'],owner['capacity'])==reader.data(f'phase/{seq}/{phase}/mfc/{mi}/bytes.bin'),'Old MFC complete actual owned backing from BEFORE');counts['old_MFC_source_owned_byteflows']+=1
      callback=lookup[entry]['registration']['callback'];frame=machine.reg('esp');need(machine.bytes(frame,8)==struct.pack('<2I',0x5ac124,callback),'Original literal callback CALL frame');seen.append(callback);need(words(b,307328,len(seen))==tuple(seen),'Actual source callback order');
      for p in O.PAGES:
       if p==0x20001000:continue
       need(machine.memory[p]==after[p],'Entire original nonstack game page '+hex(p)+' root '+hex(entry));counts['whole_nonstack_page_checks']+=1
      if entry==0x4c58c0:
       need(machine.fp_depth==0 and len(machine.FP_PCs)==26,'Original zero FP source path');fx,env=m.proj(machine.state);need(m.hardwarefx(fx)==b[628:1140]and env==b[2192:2220],'Whole literal zero FP projection');counts['BEFORE_only_zero_FP_checks']+=1
      rows.append(dict(sequence=seq,phase=phase,entry=entry,callback=callback,source_instructions=len(machine.PCs),source_accesses=len(machine.accesses),FS_events=event_index[0]));counts['constructor_prefixes']+=1
     for ci,owner in containerowners.items():
      meta=words(reader.data(f'phase/{seq}/{phase}/container-allocation/{ci}/meta.bin'),0,9);need(meta[7:]==(owner['pointer'],owner['capacity']),'Persistent original vector identity');need(bytes(owner['modeled_bytes'])==reader.data(f'phase/{seq}/{phase}/container-allocation/{ci}/bytes.bin'),'Whole persistent untouched true vector backing');counts['whole_vector_owner_carries']+=1
     for fi,owner in fsowners.items():
      meta=words(reader.data(f'phase/{seq}/{phase}/fs-allocation/{fi}/meta.bin'),0,9);need(meta[7:]==(owner['pointer'],owner['capacity']),'Shared owner lifetime identity');actual=reader.data(f'phase/{seq}/{phase}/fs-allocation/{fi}/bytes.bin');need(bytes(owner['modeled_bytes'])==actual,'Every persistent shared owned byte including unwritten true API padding');counts['whole_shared_owner_page_carries']+=1
    need(sequence_events==57 and len(fsowners)==10 and len(containerowners)==5,'All normal game/nested CRT FS events and persistent owners carried')
    for ci,owner in containerowners.items():need(bytes(owner['modeled_bytes'])==reader.data(f'cleanup/{seq}/container-allocation-{ci}-owned.bin'),'Full persistent new vector owner joins actual cleanup');counts['whole_vector_owner_cleanup_joins']+=1
    for fi,owner in fsowners.items():need(bytes(owner['modeled_bytes'])==reader.data(f'cleanup/{seq}/fs-allocation-{fi}-owned.bin'),'Full persistent shared owner joins actual cleanup');counts['whole_shared_owner_cleanup_joins']+=1
   for module in(O,m):
    for p,h in getattr(module,'PINS',{}).items():pin(p,h)
   pin(__file__);passed=True
  finally:reader.close()
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for filename,value in(('prefixes.json',rows),('owners.json',ownerrows),('FS-source-derivations.json',derivations),('new-header-derivations.json',headerrows)):(out/filename).write_text(json.dumps(value,indent=2)+'\n');pin(out/filename)
  report=dict(passed=passed,scope='Actual original116 constructor prefixes including genuine nested NULL-free source from their genuine complete BEFORE; all36 nonstack pages and original callback order. New ten-owner shared graph is derived once from authentic API initial backing, carried across all116 phases and joined to cleanup. Exact source FS normal frame bytes/heads derived from one opaque actual Windows FS0 scalar.',counts=dict(counts),per_phase_original_constructor_BEFORE_scope=True,persistent_new_owner_reseed=False,AFTER_machine_seed=False,AFTER_numeric_oracle_used=False,canonical_FS_operand_owner=0x7ffde000,actual_original_Windows_TEB_base_claimed=False,game_handler_execution=False,whole_original_provider_stack_or_volatile_return_equivalence=False,files=PINS);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
