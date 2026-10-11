"""Authenticate actual CRT instruction/memory/control trace, separate from literal semantics review."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mixed-format-original';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical identity '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def cpu(context):return [words(context,o)[0]for o in(176,172,168,164,196,180,160,156,192,184)]
def main(path,digest,normal_path,normal_digest,name):
 out=BASE/name;need(not out.exists(),'Fresh bounded trace validation');out.mkdir(parents=True);passed=False;bundle=None;counts=collections.Counter();events=[];phases=[];unique=set();writes=[];dispatch=[]
 try:
  execution=read(path,digest);need(execution['passed'],'Genuine trace execution');normal=read(normal_path,normal_digest);need(normal['passed']and normal['execution_sha256']==digest and normal['reader_closed'],'Same original trace-process raw boundary/owner proof');build=read(execution['build_path'],execution['build_sha256']);need(build['passed'],'Compiled trace worker');pin(build['worker'],build['worker_sha256']);prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(prep['provider_only_trace']and prep['segment_evidence_bytes']==60 and prep['trace_descriptors']==729,'Exact source/segment trace schema')
  for p,h in prep['files'].items():pin(p,h)
  descriptor={r['pc']:r for r in read(Path(build['preparation'])/'trace_points.json')};need(len(descriptor)==729,'Unique physical source trace descriptors');source=read(prep['source_trace_contract_path'],prep['source_trace_contract_sha256']);source_rows={r['pc']:r for r in read(source['instructions'],source['instructions_sha256'])['instructions']};need(set(descriptor)==set(source_rows),'Exact independent physical contract union')
  provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes();sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage;pe=PEImage(provider);need(pe.size_of_image==0x40000,'Exact loaded CRT physical image extent')
  spec=importlib.util.spec_from_file_location('format_trace_direct',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));direct=importlib.util.module_from_spec(spec);spec.loader.exec_module(direct);bundle=direct.DirectSet(Path(execution['original_capture']),pin)
  normal_events=read(Path(normal_path).parent/'actual-cdecl-boundaries.json');owner_rows=read(Path(normal_path).parent/'actual-owners.json');owners={r['index']:r for r in owner_rows};roots=[0x4e1ca0]
  for phase,root in enumerate(roots):
   stem=f'phase/0/{phase}/format-trace';n=words(bundle.data(stem+'/count.bin'))[0];raw=bundle.data(stem+'/events.bin');need(n and n<=16384 and len(raw)==n*1656,'Actual bounded complete trace extent');need(words(bundle.data(stem+'/segments-ready.bin'))==(1,),'Actual source selectors captured')
   segments=bundle.data(stem+'/segments.bin');need(len(segments)==60,'Whole actual data/extra/stack selector evidence');selector_values=[]
   for i in range(3):
    sel,base,limit=words(segments,i*20,3);need(sel and base==0 and limit==0xffffffff,'Genuine source flat32 DS/ES/SS descriptors');selector_values.append(sel)
   crt_stem=f'phase/0/{phase}/CRT-image';meta=bundle.data(crt_stem+'/metadata.bin');need(len(meta)%12==0,'Whole original mapped CRT page metadata');loaded={}
   for page,protect,type_ in struct.iter_unpack('<3I',meta):
    need(0x78000000<=page<0x78040000 and page%4096==0 and page not in loaded and not(protect&0x101)and type_==0x1000000,'Actual readable committed CRT image page');a=bundle.data(crt_stem+f'/before/{page}.bin');b=bundle.data(crt_stem+f'/after/{page}.bin');need(len(a)==len(b)==4096,'Complete actual loaded CRT page endpoints');loaded[page]=(a,b);counts['complete_loaded_CRT_page_endpoints']+=2
   def actual(side,address,size):
    need((address&4095)+size<=4096 and address&~4095 in loaded,'Whole original CRT source data domain');return loaded[address&~4095][side][address&4095:(address&4095)+size]
   for address,size in[(0x780103fa,32),(0x7802e2d0,89),(0x7802e2f0,128)]:
    off,_=pe.rva_range(address-pe.image_base,size);expected=provider[off:off+size];need(actual(0,address,size)==actual(1,address,size)==expected,'Complete authentic physical source dispatch/class/state tables');counts['complete_source_table_endpoints']+=2
   previous=None;phase_dispatch=[];components=[];phase_unique=set();owned_writes=0
   for i in range(n):
    b=raw[i*1656:(i+1)*1656];head=words(b,0,8);index,pc,next_pc,kind,cell_count,owner_count,exception_eip,first=head;need(index==i and pc in descriptor and kind==0 and exception_eip==pc+1 and first==descriptor[pc]['opcode']and cell_count==len(descriptor[pc]['cells'])and owner_count<=len(owners),'Actual genuine breakpoint/source descriptor binding');before_raw=b[32:748];after_raw=b[748:1464];before=cpu(before_raw);after=cpu(after_raw);need(before[9]==pc+1 and after[9]==next_pc,'Actual stopped original pre/after CONTEXT EIPs');need([words(before_raw,o)[0]for o in(152,148,200)]==selector_values and [words(after_raw,o)[0]for o in(152,148,200)]==selector_values,'Actual source instruction selector identity')
    r=source_rows[pc];code=bytes.fromhex(r['bytes_hex']);need(actual(0,pc,len(code))==actual(1,pc,len(code))==code,'Full actual observed instruction bytes equal physical source')
    if previous is None:need(pc==0x780264a9,'First original source strrchr instruction');components.append(pc)
    elif previous['next_pc']!=pc:
     need(previous['source_pc']==0x780264cb and previous['next_pc']==0x4dea1b and pc==0x78022b9a,'Only explicitly untraced original game/malloc interval between actual service pairs');components.append(pc);counts['bounded_original_game_malloc_intervals']+=1
    cells=[]
    for j in range(cell_count):
     c=words(b,1464+j*48,12);address,width,rd,wr,owner_index,generation,bv,av,valid_before,valid_after,segment,owner_offset=c;d=descriptor[pc]['cells'][j];expected_address=(d['displacement']+sum(before[k]*v for k,v in enumerate(d['coefficients'])))&0xffffffff;need(address==expected_address and (width,rd,wr,segment)==(d['width'],d['read'],d['write'],0)and valid_before==valid_after==1 and width<=4,'Actual complete source memory operand/address');need(bv<1<<(width*8)and av<1<<(width*8),'Actual bounded memory values')
     if rd and not wr:need(bv==av,'Actual pure source read conserved over one instruction')
     if owner_index!=0xffffffff:
      need(owner_index<owner_count and generation==owner_index+1 and owner_index in owners,'Actual finite owner occurrence identity');o=owners[owner_index];need(address==o['pointer']+owner_offset and owner_offset+width<=o['capacity'],'Whole actual owned access range')
      if wr:owned_writes+=1;writes.append(dict(phase=phase,root=root,event=i,PC=pc,owner_index=owner_index,generation=generation,offset=owner_offset,width=width,before=bv,after=av))
      counts['actual_owned_access_relations']+=1
     else:need(generation==0 and owner_offset==0xffffffff,'Actual unowned memory cell metadata')
     cells.append(dict(address=address,width=width,read=rd,write=wr,owner_index=owner_index,generation=generation,before=bv,after=av,before_valid=valid_before,after_valid=valid_after,segment=segment,owner_offset=owner_offset));counts['actual_memory_access_relations']+=1
    if pc==0x7800fcef:
     eax=before[0];need(eax<=7 and len(cells)==1 and cells[0]['address']==0x780103fa+eax*4 and cells[0]['before']==next_pc,'Actual bounded dispatch index/whole tablecell/control target');phase_dispatch.append(eax);dispatch.append(dict(phase=phase,event=i,index=eax,target=next_pc,table_address=cells[0]['address'],actual_full_cpu_before=before));counts['actual_output_dispatches']+=1
    normalized_before=list(before);normalized_before[8]&=~0x10100;normalized_before[9]=pc;normalized_after=list(after);normalized_after[8]&=~0x10100
    event=dict(phase=phase,index=i,root=root,source_pc=pc,next_pc=next_pc,instruction_kind=kind,owner_count_before=owner_count,actual_exception_EIP=exception_eip,actual_first_opcode=first,source_bytes_hex=code.hex(),mnemonic=r['mnemonic'],operands=r['operands'],CPU_before_projected=normalized_before,CPU_after_projected=normalized_after,raw_CONTEXT_before_hex=before_raw.hex(),raw_CONTEXT_after_hex=after_raw.hex(),cells=cells);events.append(event);previous=event;phase_unique.add(pc);unique.add(pc);counts['actual_original_instructions']+=1;counts['raw_full_debugger_CONTEXTs']+=2
   need(components==[0x780264a9,0x78022b9a] and previous['next_pc']==0x4dead7,'Entire actual two-provider path returns to original game boundaries');need(phase_dispatch and owned_writes,'Actual genuine dispatch and owned writes were reached')
   # Join entry and return GPR/flags to full normal observations, projecting only debugger TF/RF.
   for first_pc,target_kind,after_pc,ret_kind in[(0x780264a9,0,0x4dea1b,1),(0x78022b9a,4,0x4dead7,5)]:
    start=next(e for e in events if e['phase']==phase and e['source_pc']==first_pc);end=next(e for e in reversed(events)if e['phase']==phase and e['next_pc']==after_pc);entry=next(e for e in normal_events if e['phase']==phase and e['kind']==target_kind);ret=next(e for e in normal_events if e['phase']==phase and e['kind']==ret_kind)
    cp=list(entry['cpu']);cp[8]&=~0x10100;need(start['CPU_before_projected']==cp,'Actual trace entry joined complete normal CPU');cp=list(ret['cpu']);cp[8]&=~0x10100;need(end['CPU_after_projected']==cp,'Actual trace return joined complete normal CPU');counts['whole_actual_normal_CPU_boundary_joins']+=2
   phases.append(dict(phase=phase,root=root,instructions=n,unique_PCs=len(phase_unique),components=components,dispatch_indices=phase_dispatch,owned_write_relations=owned_writes,loaded_CRT_pages=len(loaded),selectors=selector_values,raw_segments_hex=segments.hex()));counts['actual_traced_root_phases']+=1
  counts['unique_genuine_provider_PCs']=len(unique);need(bundle.data('COMPLETE.txt')==b'complete','Actual trace completion');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if bundle:bundle.close()
  for fn,value in [('trace-observations.json',events),('actual-trace-phases.json',phases),('actual-owned-writes.json',writes),('actual-output-dispatches.json',dispatch)]:p=out/fn;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
  pin(__file__);report=dict(passed=passed,scope='Genuine original CRT physical reached instruction/control/full CONTEXT/memory evidence and same-process normal CPU/owner inputs; literal source semantics review remains separate, no general formatter or native credit',execution_path=str(path),execution_sha256=digest,normal_validation_path=str(normal_path),normal_validation_sha256=normal_digest,build_sha256=execution.get('build_sha256'),counts=dict(counts),explicit_debugger_projection={'TF_RF_mask':0x10100,'breakpoint_entry_EIP':'rawPC+1 retained; only source interface PC becomes actual breakpoint PC'},provider_only=True,actual_provider_return_observed=True,source_memory_effects_supplied=False,reader_closed=True,literal_source_validation_pending=True,native_executed=False,initializer_credit=False,files=PINS);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
