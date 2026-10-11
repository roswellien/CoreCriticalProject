"""Four literal original prefixes and carried owners from genuine root BEFORE.

Observed Win32 API volatile results are a bounded external boundary.  No
captured constructor/destructor postRET machine is admitted or fabricated.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-startup138-original';PINS={}
VALIDATION=ROOT/'reports/m4-startup138-original/original-validation-r2/report.json'
VALIDATION_SHA='74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181'
PREP=ROOT/'reports/m4-startup138-original/preparation-r7'
PREP_SHA='e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2'
AUDITED_READS=set()
def audit_workspace_read(event,args):
 if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 path=Path(args[0]).resolve()
 if not path.is_relative_to(ROOT):return
 mode=args[1]if len(args)>1 else None
 flags=args[2]if len(args)>2 else 0
 reading=isinstance(mode,str)and'r'in mode or(mode is None and isinstance(flags,int)and not(flags&3))
 if not reading:return
 if path.suffix.lower()=='.mwb':need(False,'No archive may be opened by the current raw-export source gate')
 AUDITED_READS.add(str(path))
sys.addaudithook(audit_workspace_read)

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable input');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def own(p,n):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def equal(a,b,label):need(a==b,label+' '+str([(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:12]))
def prepare(name):
 out=BASE/name;need(not out.exists(),'Fresh preparation');out.mkdir(parents=True)
 v=read(VALIDATION,VALIDATION_SHA);p=read(PREP/'report.json',PREP_SHA);need(v['passed']and p['passed'],'Exact successful original inputs')
 own(ROOT/'tools/m4-lockit-source/game_model.py','Lockit_source_prepare').source_program()
 pin(__file__);report=dict(passed=True,scope='Prepared bounded original four-root source-prefix and whole owned-backing proof; no new execution or initializer credit',original_validation_sha256=VALIDATION_SHA,original_preparation_sha256=PREP_SHA,source_prefixes=24,actual_original_snapshots=144,source_derived_postRET=True,observed_original_postRET=False,API_seam='Actual external volatile EAX/ECX/EDX/EFLAGS and CS24 output only; nonvolatile GPR/ESP/returnPC and complete FP preserved',native_reader_opened=False,files=PINS)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
def verify(reader,out):
 counts=collections.Counter();prefixes=[];derivations=[];ownerrows=[];accessrows=[];owner_accesses=[];publication_rows=[]
 source_contract=read(ROOT/"reports/m4-lockit-source/owned-contracts-r1/report.json");need(source_contract["passed"],"Exact successful additive affine source contracts")
 authored_accesses=read(ROOT/"reports/m4-lockit-source/owned-contracts-r1/shared-owner-accesses.json",source_contract["files"][str((ROOT/"reports/m4-lockit-source/owned-contracts-r1/shared-owner-accesses.json").resolve())])
 authored_publications=read(ROOT/"reports/m4-lockit-source/owned-contracts-r1/allocation-inputs.json",source_contract["files"][str((ROOT/"reports/m4-lockit-source/owned-contracts-r1/allocation-inputs.json").resolve())])
 p=read(PREP/'report.json',PREP_SHA)
 inherited=read(ROOT/'reports/m4-lockit-original/original-preparation-r4/report.json','6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b')
 p['Lockit_roots']=inherited['Lockit_roots'];p['Lockit_allocations']=inherited['Lockit_allocations'];p['order']=p['selected_order'];pages=p['observed_pages'];need(len(pages)==43 and len(p['order'])==138,'Exact original138 order and43 fixed pages plus26 external whole pages')
 review=read(ROOT/'reports/m4-tree-review/original138-prelaunch-r5/report.json','efaa5d25802440f8cd47092d16a0368084cf5ea744d8c2cda5c826522f96122a');validation=read(VALIDATION,VALIDATION_SHA)
 need(review['passed']and review['build_sha256']==validation['build_sha256']=='748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69'and review['preparation_sha256']==validation['preparation_sha256']==PREP_SHA,'Fresh complete final linked observer gate and actual process validation')
 extra_pages=p['extra_whole_source_pages'];need(len(extra_pages)==26 and len(set(pages+extra_pages))==69 and {0x5cd000,0x5e3000,0x5e9000}<=set(extra_pages),'All26 complete physical additional source pages, retaining inherited three')
 suffix=own(ROOT/'tools/m4-startup138-original/registry_suffix_v1.py','old4_registry_suffix');transition_module=own(ROOT/'tools/m4-startup138-original/mfc_transition_v1.py','old4_hook_transition');transition_receipt=read(ROOT/'reports/m4-138-validation-review/mfc-transition-r3/report.json','56cc2983c3448cf872e9247cb315cede98a83fa9a63c831264d9008b7ad9e834');need(transition_receipt['passed']and transition_receipt['reader_closed'],'Exact independent whole hook-mode transitions');transitions=transition_module.Transition(read(ROOT/'reports/m4-138-validation-review/mfc-transition-r3/patch-identities.json','1f8768938aa8f2ebb938e6a782a93734bb569cea8634d634fe23d335d7b9b2ed'))
 iat_path=Path(VALIDATION).parent/'format-IAT-relations.json';read(iat_path,validation['files'][str(iat_path.resolve())])
 G=own(ROOT/'tools/m4-lockit-source/game_model.py','original124_prefix_model');program,callbacks=G.source_program();J=own(ROOT/'tools/m4-joint-startup27-review/observe.py','original124_numeric');m,_,_,_=J.models();m.PAGES=list(pages)
 O=own(ROOT/'tools/m4-mfc-source/compare_original_game.py','original124_prefix_helpers');O.PAGES=tuple(pages);O.MFC_IMPORTS=[tuple(v[:3])for v in struct.iter_unpack('<7I',reader.data('mfc-import-ledger.bin'))];need(len(O.MFC_IMPORTS)==511,'Exact original511 MFC IATs')
 PE=own(ROOT/'tools/analysis/pe.py','original124_prefix_PE');provider=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
 build=read(ROOT/'reports/m4-startup138-original/build-r4/build.json','748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69');worker=pin(build['worker'],build['worker_sha256']).read_bytes()
 hooks=read(ROOT/'reports/m4-lockit-original/original-preparation-r4/lockit-hook-bindings.json');patches=[]
 for h in hooks:
  pc,size=h['pc'],h['size'];raw=bytes.fromhex(h['raw']);offset,_=provider.rva_range(pc-provider.image_base,size);need(raw==provider.data[offset:offset+size],'Physical provider observer span')
  key=struct.pack('<2I',pc,size);matches=[i for i in range(len(worker))if worker.startswith(key,i)and worker[i+12:i+12+size]==raw];need(len(matches)==1,'One actual linked LockitHook row');target=words(worker,matches[0]+8)[0];patched=b'\xe9'+struct.pack('<I',(target-pc-5)&0xffffffff)+b'\x90'*(size-5);patches.append(dict(PC=pc,width=size,compiled_target=target,original_hex=patched.hex(),source_hex=raw.hex()))
 bootstrap={a:reader.data(f'lockit/post-DllMain/{a}-page.bin')for a in(0x7810a000,0x78145000,0x78146000)};imports={cell:target for cell,target,*tail in struct.iter_unpack('<5I',reader.data('lockit/import-ledger.bin'))}
 def normalized(raw):
  memory=O.normalize_memory(raw,0x1df20c)
  for address,actual,value in[(0x5bb454,0x5f4020b4,0x8000021c),(0x5bb4c8,0x5f401782,0x80000339),(0x5bb4f8,0x7810a290,0x1df582),(0x5bb4f4,0x7810a350,0x1df568)]:
   need(words(memory[address&~4095],address&4095)[0]==actual,'Exact actual owning game IAT');struct.pack_into('<I',memory[address&~4095],address&4095,value)
  for patch in patches:
   offset=patch['PC']&4095;equal(memory[0x7810a000][offset:offset+patch['width']],bytes.fromhex(patch['original_hex']),'Exact actual original compiled observer bytes');memory[0x7810a000][offset:offset+patch['width']]=bytes.fromhex(patch['source_hex'])
  for slot in(0x78146198,0x78146184):
   current=words(memory[0x78146000],slot&4095)[0];need(0x18000000<=current<0x19000000,'Original API IAT shim belongs to fixed x86 observer');struct.pack_into('<I',memory[0x78146000],slot&4095,imports[slot])
  equal(memory[0x78146000],bootstrap[0x78146000],'Whole loaded provider IAT restored by only two exact API observer cells')
  return memory
 roots={r['entry']:r for r in p['Lockit_roots']};bindings=p['Lockit_allocations'];owner_receipts={}
 for seq in range(6):
  owners={};previous=None;previous_extra={}
  for phase,item in enumerate(p['order']):
   entry=item['entry'];b=reader.data(f'phase/{seq}/{phase}.bin');need(len(b)==356992,'Exact original124 ABI')
   if previous is not None:equal(b[2276:178404],previous[178404:354532],'Complete original43 page carry')
   previous=b
   before_extra={a:reader.data(f'phase/{seq}/{phase}/extra-before/{a}.bin')for a in extra_pages};after_extra={a:reader.data(f'phase/{seq}/{phase}/extra-after/{a}.bin')for a in extra_pages}
   for a in extra_pages:
    need(len(before_extra[a])==len(after_extra[a])==4096,'Complete external source page endpoints')
    if previous_extra:
     if phase in(13,14):transitions.relation(previous_extra[a],before_extra[a],a,phase,seq)
     else:equal(before_extra[a],previous_extra[a],'Complete original external source page carry')
   previous_extra=after_extra
   if entry in roots:
    root=roots[entry];memory=normalized(b[2276:178404]);after=normalized(b[178404:354532]);snapshots=reader.data(f'phase/{seq}/{phase}/lockit-snapshots.bin');need(len(snapshots)==6*12988,'Six actual bounded snapshots')
    snaps=[snapshots[k*12988:(k+1)*12988]for k in range(6)];actualFS=reader.data(f'phase/{seq}/{phase}/fs-events.bin');need(len(actualFS)==3*1216,'Three actual normal FS observations')
    memory.update({a:bytearray(v)for a,v in before_extra.items()});after.update(after_extra)
    memory[0x7ffde000]=bytearray(struct.pack('<I',words(actualFS,16)[0]));memory.update({a:bytearray(o['bytes'])for a,o in owners.items()});state=bytearray(O.original_state(m,G,words(b,36,10),b));struct.pack_into('<I',state,2168,0x7ffde000);seen=[0];fi=[0];allocations=[];api=list(struct.iter_unpack('<26I',reader.data(f'phase/{seq}/{phase}/api-ledger.bin')));allocfacts=[(i,r)for i,r in enumerate(api)if r[24]==0]
    def boundary(machine,k):
     raw=snaps[k];expected=list(machine.projected_cpu());expected[9]=machine.cursor;actual=words(raw,64,10);equal(tuple(expected),actual,'Entire original source-derived Lockit boundary CPU '+str((seq,entry,k)))
     fx,env=m.proj(machine.state);equal(m.hardwarefx(fx),raw[104:616],'Entire original source-derived Lockit FX');equal(env,raw[616:644],'Entire original source-derived Lockit ENV');equal(machine.bytes(machine.reg('esp'),32),raw[644:676],'Whole actual32B source frame');equal(machine.bytes(0x78145640,24),raw[676:700],'Whole carried source CS24');counts['actual_original_source_boundary_joins']+=1
     derivations.append(dict(sequence=seq,phase=phase,root=entry,index=k,PC=machine.cursor,CPU=list(actual),FX_sha256=hashlib.sha256(raw[104:616]).hexdigest(),ENV_sha256=hashlib.sha256(raw[616:644]).hexdigest()))
    def fs(machine,address,value,size,pc,write):
     if address!=0x7ffde000:return
     raw=actualFS[fi[0]*1216:(fi[0]+1)*1216];need(len(raw)==1216,'Finite original FS');w=words(raw,0,8);need(w[1]==entry and w[2]==pc and write==(w[3]!=0)and size==4,'Exact original FS PC/direction');need(machine.reg('esp')==words(raw,32,10)[4]and machine.bytes(address,4)==struct.pack('<I',w[4])and value==(w[5]if write else w[4]),'Source-derived FS predecessor/frame');
     if w[7]:equal(machine.bytes(w[6],12),raw[112:124],'Complete original12B FS frame from genuine BEFORE')
     fi[0]+=1;counts['normal_original_FS_joins']+=1
    class Prefix(G.Machine):
     def step(self):
      if self.cursor in(0x7810a290,0x7810a311,0x7810a350,0x7810a364):
       k={0x7810a290:0,0x7810a311:2,0x7810a350:3,0x7810a364:5}[self.cursor];need(seen[0]==k,'Exact source six-boundary order');boundary(self,k);seen[0]+=1
      return super().step()
     def read(self,a,size=4,domain='source',pc=None):
      value=super().read(a,size,domain,pc);fs(self,a,value,size,self.word(2472)if pc is None else pc,False);return value
     def write(self,a,value,size=4,domain='source',pc=None):
      fs(self,a,value,size,self.word(2472)if pc is None else pc,True);return super().write(a,value,size,domain,pc)
    machine=Prefix(state,b[116:628],b[36:76],memory,program=program,callbacks=callbacks);machine.call_stack.append((entry,0x20001800,0x410a80,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0))
    def external(model,target):
     site=model.PCs[-1]
     if site in(0x7810a30b,0x7810a35e):
      k=1 if site==0x7810a30b else 4;need(seen[0]==k and target==imports[0x78146198 if k==1 else 0x78146184],'Exact source actual API target');boundary(model,k);seen[0]+=1;before,returned=snaps[k],snaps[k+1];ac=words(returned,64,10);bc=words(before,64,10)
      need(ac[3]==bc[3]and ac[5:8]==bc[5:8]and ac[4]==bc[4]+8 and ac[9]==(0x7810a311 if k==1 else 0x7810a364),'External API preserves nonvolatile GPRs and consumes actual stdcall2word frame');equal(before[104:644],returned[104:644],'Actual API preserves entire captured FX512/ENV28')
      cs=returned[676:700];d=struct.unpack('<6I',cs);prior=struct.unpack('<6I',before[676:700]);need(d[0]==prior[0]and d[4:]==prior[4:]and d[2]==(1 if k==1 else 0)and d[1]==(0xfffffffe if k==1 else 0xffffffff),'Bounded actual original held/unheld CS fields')
      model.api_return(site,1,ac[0],[(0x78145640,cs)]);projected=list(model.projected_cpu());projected[1:3]=ac[1:3];projected[8]=ac[8];m.statecpu(model.state,projected);counts['bounded_original_API_volatile_boundaries']+=1;return
     need(target==0x780012b3 and site==0x5f401eb5,'Only genuine positive MFC malloc scalar boundary');ai,fact=allocfacts[len(allocations)];request=int.from_bytes(model.bytes(model.reg('esp')+4,4),'little');need(fact[21]==0 and fact[22]==(request+15)&~15 and fact[10]and fact[25]==0x78001385,'Actual positive HeapAlloc source scalar');frame=model.call_stack[-2];binding=next(r for r in bindings if r['root']==entry and r['CALL_pc']==frame[3]);need(binding['requested']==request,'Exact source20B or24B PUSH');initial=reader.data(f'phase/{seq}/{phase}/api-initial/{ai}/bytes.bin');need(len(initial)==32,'Actual complete32B initial backing');pointer=fact[10];need(pointer not in model.memory,'Fresh owner');model.memory[pointer]=bytearray(initial);candidates=[]
     for name in reader.entries:
      if not(name.startswith(f'phase/{seq}/{phase}/lockit-allocation/')and name.endswith('/meta.bin')):continue
      candidate=words(reader.data(name),0,9)
      if candidate[2:5]==(entry,frame[3],request)and candidate[6:8]==(ai,pointer):candidates.append((int(name.split('/')[-2]),candidate))
     need(len(candidates)==1,'One actual current source CALL/API/generation owner metadata row');index,meta=candidates[0];need(meta==(1,index,entry,frame[3],request,frame[1],ai,pointer,32),'Exact original CALL/frame/owner receipt');owners[pointer]=dict(meta=meta,bytes=model.memory[pointer],binding=binding,initial=initial,index=index,creation_phase=phase);allocations.append(pointer);model.reg('edx',fact[12]);model.api_return(site,0,pointer);counts['actual_original_initial_owner_inputs']+=1
    machine.run(stop=lambda x:x.cursor==0x78004a36,api=external);need(seen[0]==6 and fi[0]==3 and len(allocations)==2,'Complete new source prefix and bounded seams');callback=root['registration']['callback'];equal(machine.bytes(machine.reg('esp'),8),struct.pack('<2I',0x5ac124,callback),'Literal source callback CALL/argument')
    registry_suffix=suffix.prove(reader,seq,phase,machine,callback,b,api)
    for page in pages+extra_pages:
     if page==0x20001000:continue
     equal(suffix.page(machine.bytes(page,4096),page,registry_suffix),after[page],'Entire original source prefix nonstack page plus independently proven registry suffix '+hex(page));counts['whole_original_prefix_page_relations']+=1
    current_specs=[];current_publications=[]
    accessrows.append(dict(sequence=seq,phase=phase,root=entry,rows=machine.accesses))
    for pc,address,value,width,writing in machine.accesses:
     if pc>=0x78000000:continue
     matching=[(pointer,owner)for pointer,owner in owners.items()if pointer<=address and address+width<=pointer+32]
     need(len(matching)<=1,'Unique source owner backing')
     if matching:
      pointer,owner=matching[0];binding=owner['binding'];spec=dict(root=entry,pc=pc,write=bool(writing),bytes=width,owner_root=binding['root'],owner_CALL_pc=binding['CALL_pc'],owner_offset=address-pointer)
      need(address+width<=pointer+binding['requested'],'Exact source access within authentic requested extent')
      current_specs.append(spec);owner_accesses.append(dict(sequence=seq,phase=phase,source_address=address,source_value=value,owner_pointer=pointer,owner_index=owner['index'],**spec));counts['source_owned_contract_corroborations']+=1
     for pub in authored_publications:
      if pub['root']!=entry or pub['publication_PC']!=pc:continue
      need(writing==1 and width==4 and address==pub['publication'],'Source exact static owner publication instruction')
      owner=owners[value];need(owner['binding']['root']==entry and owner['binding']['CALL_pc']==pub['CALL_pc'] and owner['binding']['requested']==pub['requested_size'],'Actual original owner generation and source publication')
      current_publications.append(pub);publication_rows.append(dict(sequence=seq,phase=phase,source_value=value,owner_index=owner['index'],**pub));counts['source_publication_contract_corroborations']+=1
    equal(current_specs,[r for r in authored_accesses if r['root']==entry],'Exact literal source owner rows match independent affine contracts in source order')
    equal(current_publications,[r for r in authored_publications if r['root']==entry],'Exact literal source publications match independent affine contracts in source order')
    for pointer,owner in owners.items():owner['bytes']=machine.memory[pointer]
    prefixes.append(dict(sequence=seq,phase=phase,root=entry,source_instructions=len(machine.PCs),source_accesses=len(machine.accesses),postRET_source_derived=True));counts['literal_original_new_root_prefixes']+=1
   for pointer,owner in owners.items():
    index=owner['index'];equal(reader.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/meta.bin'),struct.pack('<9I',*owner['meta']),'Carried original owner identity');equal(reader.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/bytes.bin'),owner['bytes'],'Whole source-derived32B owned backing and untouched API tail');counts['whole_original_owner_phase_carries']+=1
  need(len(owners)==8,'Eight exact original new owners');owner_receipts[seq]=owners
  for pointer,owner in owners.items():
   equal(reader.data(f'cleanup/{seq}/lockit-allocation-{owner["index"]}-owned.bin'),owner['bytes'],'Complete source-derived original owner cleanup join');counts['whole_original_owner_cleanup_joins']+=1;ownerrows.append(dict(sequence=seq,index=owner['index'],meta=list(owner['meta']),initial_hex=owner['initial'].hex(),source_owned_hex=bytes(owner['bytes']).hex(),binding=owner['binding']))
 for module in(O,m):
  for path,h in getattr(module,'PINS',{}).items():pin(path,h if isinstance(h,str)else h['sha256'])
 for filename,value in [('original-prefixes.json',prefixes),('original-Lockit-boundaries.json',derivations),('original-owned-source-relations.json',ownerrows),('provider-observer-spans.json',patches),('original-source-access-ledgers.json',accessrows),('original-source-owned-contract-corroborations.json',owner_accesses),('original-source-publication-contract-corroborations.json',publication_rows)]:
  (out/filename).write_text(json.dumps(value,indent=2)+'\n');pin(out/filename)
 need(counts['source_owned_contract_corroborations']==192 and counts['source_publication_contract_corroborations']==48,'All32 static owned rows and8 publications corroborated in6 actual original sequences')
 return dict(counts=dict(counts),prefixes=prefixes,source_owned_contracts=32,source_publication_contracts=8,source_contract_sha256=sha(ROOT/'reports/m4-lockit-source/owned-contracts-r1/report.json')),owner_receipts,patches
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original source gate');out.mkdir(parents=True);passed=False;result={}
 try:
  v=read(VALIDATION,VALIDATION_SHA);need(v['passed'],'Genuine original validation');E=own(ROOT/'tools/m4-startup138-original/export_reader_r2.py','original138_raw_export');reader=E.ExportReader(sys.argv[2],sys.argv[3],'original',pin);need(Path(reader.path).resolve()==Path(v['original_capture']).resolve(),'Current genuine original transport identity')
  try:result,_,_=verify(reader,out)
  finally:reader.close()
  pin(__file__);pin(ROOT/'tools/m4-startup130-original/derive_old4_source.py');pin(ROOT/'tools/m4-tree-original/old4_source_v3.py');pin(ROOT/'tools/m4-lockit-paired-provider/original_v2.py');pin(ROOT/'tools/m4-tree-original/derive_old4_source.py');pin(ROOT/'tools/m4-tree-original/old4_source.py');pin(ROOT/'tools/m4-tree-original/derive_old4_source_v2.py');pin(ROOT/'tools/m4-tree-original/old4_source_v2.py');pin(ROOT/'tools/m4-tree-original/derive_old4_source_v3.py')
  existing={path for path in AUDITED_READS if Path(path).is_file()}
  missing=sorted(AUDITED_READS-existing);need(all('__pycache__'in path and path.endswith('.pyc')for path in missing),'Only failed optional Python bytecode reads are excluded')
  for path in sorted(existing):pin(path)
  dependency_paths=sorted(existing)
  (out/'audited-workspace-reads.json').write_text(json.dumps(dependency_paths,indent=2)+'\n');pin(out/'audited-workspace-reads.json');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Literal four original root prefixes from genuine complete BEFORE with actual finite MFC allocation and Win32 volatile boundary facts; complete32B owned source byteflow carried across138 phases; all69 current source pages supplied from own genuine BEFORE. Original postRET is source-derived only.',original_build_sha256='748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69',original_preparation_sha256=PREP_SHA,independent_compiled_original_sha256='efaa5d25802440f8cd47092d16a0368084cf5ea744d8c2cda5c826522f96122a',recursive_workspace_source_reads_sealed=True,capture_archive_opened=False,raw_export_report_path=str(Path(sys.argv[2]).resolve()),raw_export_report_sha256=sys.argv[3],audited_input_paths=len(dependency_paths)if'dependency_paths'in locals()else 0,failed_optional_bytecode_read_attempts=missing if'missing'in locals()else [],reader_closed=True,original_validation_sha256=VALIDATION_SHA,AFTER_machine_seed=False,observed_original_postRET=False,whole_original_provider_stack_equivalence=False,initializer_credit=False,files=PINS,**result);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=result.get('counts',{}))))
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare(sys.argv[2])
 else:main(sys.argv[1])
