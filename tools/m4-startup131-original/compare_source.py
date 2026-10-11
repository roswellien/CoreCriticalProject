"""Literal chronological cached-domain replay from genuine current BEFORE.

Normal source/API boundaries corroborate the derived path. This is not a new
per-instruction debugger trace, and does not assert opaque Win32 stack spills.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-startup131-original';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def eq(a,b,s):need(a==b,s+' '+str((a,b))[:650])
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact current input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Immutable input');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def load(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def w(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def main(validation,digest,name):
 out=B/name;need(not out.exists(),'Fresh source receipt');out.mkdir();passed=False;counts=collections.Counter();result={}
 try:
  v=read(validation,digest);need(v['passed']and v['reader_closed']and v['counts']['MFC_original_phases']==6 and v['counts']['phases']==786,'Actual chronological normal receipt closed')
  e=read(v['execution_path'],v['execution_sha256']);build=read(e['build_path'],e['build_sha256']);prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(prep['passed']and build['passed']and prep['source_frame']==0x20001800,'Current reviewed physical worker');pin(build['worker'],build['worker_sha256'])
  for p,h in prep['files'].items():pin(p,h)
  source_gate=read(R/'reports/m4-mfc1168-probe/validation-r6/report.json');need(source_gate['passed'],'Physical cached-domain source recovery')
  reached=read(R/'reports/m4-mfc1168-probe/validation-r6/reached-instruction-contracts.json',source_gate['files'][str((R/'reports/m4-mfc1168-probe/validation-r6/reached-instruction-contracts.json').resolve())]);program={x['pc']:x for x in reached['instructions']};eq(len(program),142,'Exactly recovered cached source union')
  current_cases=read(Path(validation).parent/'fresh-MFC-observations.json',v['files'][str((Path(validation).parent/'fresh-MFC-observations.json').resolve())]);need(len(current_cases)==6 and [x['sequence']for x in current_cases]==list(range(6)),'Exact six current original MFC domains')
  contracts=read(prep['contracts']);contract=dict(fixed_current_source_pages=prep['observed_pages'],external_source_pages=prep['extra_whole_source_pages']);need(len(contract['fixed_current_source_pages'])==43 and len(contract['external_source_pages'])==3,'Fixed original13146-page endpoint inventory')
  results=[]
  for seq,actual in enumerate(current_cases):
   phase={**actual,'slot':contracts['selected_order'][13]['slot']};boundaries=actual['boundaries'];api=actual['APIs'];domains=actual['domains'];eq((phase['root'],phase['slot']),(0x5ae3e4,0x5e0040),'Actual chronological source table cell')
   def raw(key):
    if key.startswith('MFC1168/'):key=f'phase/{seq}/13/'+key
    elif key.startswith('phase/0/13'):key=key.replace('phase/0/13',f'phase/{seq}/13',1)
    path=(Path(validation).parent/'actual-MFC-inputs'/key).resolve();need(str(path)in v['files'],'Exactly sealed current bounded source input '+key);return pin(path,v['files'][str(path)]).read_bytes()
   I=load(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py','chronological_mfc_integer');F=load(R/'tools/m4-formatting-source/flag_domain.py','chronological_mfc_flags')
   memory={};whole_targets={};record=raw('phase/0/13.bin')
   for i,address in enumerate(contract['fixed_current_source_pages']):
    memory[address]=bytearray(record[2276+i*4096:2276+(i+1)*4096]);whole_targets[address]=record[178404+i*4096:178404+(i+1)*4096]
   for address in contract['external_source_pages']:
    memory[address]=bytearray(raw(f'phase/0/13/extra-before/{address}.bin'));whole_targets[address]=raw(f'phase/0/13/extra-after/{address}.bin')
   for module in('MFC','CRT'):
    for address,protect,type_,owner in struct.iter_unpack('<4I',raw('MFC1168/BEFORE/'+module+'/metadata.bin')):
     b=raw(f'MFC1168/BEFORE/{module}/{address}.bin');need(address not in memory or memory[address]==b,'Overlapping genuine whole inputs agree');memory[address]=bytearray(b);whole_targets[address]=raw(f'MFC1168/AFTER/{module}/{address}.bin')
   # Two new immutable RX pages are not part of the inherited46 semantic
   # endpoint pages. Their input comes from the exact physically admitted pack;
   # current worker checks every whole source span before and after execution.
   pack=pin(Path(build['preparation'])/'pages.bin',prep['pack_sha256']).read_bytes();eq(pack[:8],b'MW4J124P','Physical source pack tag');n=w(pack,8)[0];eq(len(pack),12+n*4104,'Exact sparsepack geometry');packed={}
   for i in range(n):
    off=12+i*4104;address,permission=w(pack,off,2);packed[address]=(permission,pack[off+8:off+4104])
   missing={row['pc']&~4095 for row in program.values()if(row['pc']&~4095)not in memory};eq(missing,{0x5ab000,0x5ae000},'Only new immutable gamecode pages absent from inherited semantic inventory')
   for address in sorted(missing):
    permission,data_=packed[address];eq(permission,1,'Immutable executable sourcepage');eq(len(data_),4096,'Whole exact sourcepage');memory[address]=bytearray(data_);counts['physical_pack_readonly_source_code_input_pages']+=1
   pin(R/'tools/m4-mfc1168-connected-original/compare_source.py');pin(R/'tools/m4-mfc1168-connected-original/derive_compare_v2.py')
   teb_base=w(raw('phase/0/13/TEB-before-base.bin'))[0];teb=raw('phase/0/13/TEB-before.bin');eq(teb_base,domains['BEFORE']['metadata'][0],'Actual same-process coherent TEB identity');need(len(teb)==8192 and w(teb,0x18)[0]==teb_base,'Actual8KiB source-entry TIB');memory[teb_base]=bytearray(teb[:4096]);memory[teb_base+4096]=bytearray(teb[4096:])
   owner_inputs=[]
   for role in('manager-array','thread','thread-array','thread-object','global-object'):
    meta=w(raw('MFC1168/BEFORE/domain/'+role+'/meta.bin'),0,8);aftermeta=w(raw('MFC1168/AFTER/domain/'+role+'/meta.bin'),0,8);eq(meta,aftermeta,'Actual borrowed role extent identity');need(meta[7]and meta[6]>0,'Positive whole actual capacity');initial=raw('MFC1168/BEFORE/domain/'+role+'/bytes.bin');eq(len(initial),meta[6],'Actual complete borrowed input');memory[meta[0]]=bytearray(initial);owner_inputs.append(dict(role=role,address=meta[0],extent=meta[6],initial_hex=initial.hex()))
   lockmeta=w(raw('MFC1168/BEFORE/CRT-codepage-lock/meta.bin'),0,4);eq(lockmeta[0],0x7803708c,'Literal owning lock25 pointer cell');eq(lockmeta[2:],(24,1),'Complete actual CS24 input');memory[lockmeta[1]]=bytearray(raw('MFC1168/BEFORE/CRT-codepage-lock/bytes.bin'))
   state=bytearray(3504);first=tuple(phase['CPU_before'])
   for reg,val in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),first[:8]):struct.pack_into('<I',state,I.REG[reg],val)
   for flag,bit in F.BITS.items():state[I.FLAGS[flag]]=(first[8]>>bit)&1
   struct.pack_into('<I',state,2472,first[9]);struct.pack_into('<I',state,I.BASE['fs'],teb_base)
   class Literal(I.Machine):
    def cpu_now(self):
     flags=first[8]
     for flag,bit in F.BITS.items():flags=(flags&~(1<<bit))|(int(bool(self.flag(flag)))<<bit)
     return tuple(self.reg(k)for k in('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,self.cursor)
    def step(self):
     if self.cursor==0x780014b4:
      need(self.call_stack and self.call_stack[-1][0]==0x5f40107d and self.call_stack[-1][2]==0x5f4010b5,'Exact imported EH special-return frame');self.call_stack.pop();outer=self.call_stack;self.call_stack=[]
      try:return super().step()
      finally:self.call_stack=outer
     return super().step()
   m=Literal(state,bytes.fromhex(phase['FX_before_hex']),struct.pack('<10I',*first),memory,program=program,callbacks={});domain={};api_index=0;boundary_index=0;flag_rows=[];joins=[];api_relations=[]
   need(len(boundaries)==7 and len(api)==8,'Exactly current normal source/API observations')
   for row in program.values():eq(m.bytes(row['pc'],row['width']),bytes.fromhex(row['bytes_hex']),'Whole actual unpatched physical source definition '+hex(row['pc']))
   while m.cursor!=0x410a80:
    need(m.cursor in program,'No lazy/cold/unrecovered source frontier admitted');pc=m.cursor;row=program[pc]
    if boundary_index<7 and pc==boundaries[boundary_index]['CPU'][9]:
     b=boundaries[boundary_index];eq(F.project(m.cpu_now(),domain),F.project(tuple(b['CPU']),domain),'Complete source-derived normal boundary CPU/defined flags');eq(m.fx,bytes.fromhex(b['FX512_hex']),'Whole source-derived normal boundary FX512');eq(bytes.fromhex(phase['ENV_before_hex']),bytes.fromhex(b['ENV28_hex']),'No FP instruction; whole raw ENV28 normal boundary');eq(m.bytes(m.reg('esp'),64).hex(),b['frame64_hex'],'Whole normal source frame64 derived from current BEFORE')
     if boundary_index in(1,2,3,4):eq(m.bytes(b['metadata'][3],b['metadata'][4]).hex(),b['whole_provider_before_write_hex'],'Whole source-derived provider before each source write')
     joins.append(dict(index=boundary_index,PC=pc,source_CPU=m.cpu_now(),undefined_flags=dict(domain),derived_source_FS_head=w(m.bytes(teb_base,4))[0],actual_observer_owned_FS_head=b['metadata'][2],intermediate_source_FS_observation=False));counts['whole_normal_CPU_FX_ENV_frame64_boundary_joins']+=1;boundary_index+=1
    old=len(m.accesses);domain=F.advance(m,row,domain);m.step();flag_rows.append(dict(PC=pc,undefined_flags=dict(domain),new_source_accesses=m.accesses[old:]));counts['literal_source_instructions']+=1
    if m.cursor not in program and m.cursor!=0x410a80:
     need(api_index<4,'Only four admitted actual named API seams');a,z=api[api_index*2:api_index*2+2];eq(a['side'],0,'True API entry');eq(z['side'],1,'True API return');eq(m.cursor,a['CPU'][9],'Literal source loaded API target');eq(F.project(m.cpu_now(),domain),F.project(tuple(a['CPU']),domain),'Full API entry CPU40 from literal source');eq(m.bytes(m.reg('esp'),64).hex(),a['frame64_hex'],'Whole literal actual API frame64');eq(a['FShead'],z['FShead'],'Actual observer-owned host FS metadata unchanged')
     name=a['API'];args=w(bytes.fromhex(a['frame64_hex']),4,a['argc']) if a['argc']else()
     if name=='TlsGetValue':eq(args,(3,),'Actual source TLSindex3');eq(z['CPU'][0],domains['BEFORE']['metadata'][7],'True TLS return joins untouched actual raw slot')
     elif name=='GetACP':eq(z['CPU'][0],1252,'Measured finite ACP1252 input')
     else:eq(args,(lockmeta[1],),'Actual current initialized lock25 argument')
     eq(a['FX512_hex'],z['FX512_hex'],'Actual API whole FX512 conserved');eq(a['ENV28_hex'],z['ENV28_hex'],'Actual API whole ENV28 conserved');m.api_return(pc,a['argc'],z['CPU'][0]);m.reg('ecx',z['CPU'][1]);m.reg('edx',z['CPU'][2])
     for flag,bit in F.BITS.items():m.flag(flag,(z['CPU'][8]>>bit)&1)
     domain={};eq(m.cpu_now(),tuple(z['CPU']),'Entire typed actual volatile API result with literal cleanup');eq(m.bytes(m.reg('esp'),64).hex(),z['frame64_hex'],'Whole actual API returned source frame64');api_relations.append(dict(index=api_index,source_PC=pc,API=name,entry_CPU=a['CPU'],source_return_CPU=m.cpu_now(),args=args,actual_return_PC=z['CPU'][9],actual_observer_owned_FS_head=a['FShead'],derived_source_FS_head=w(m.bytes(teb_base,4))[0],intermediate_source_FS_observation=False,volatile_input_fields=['EAX','ECX','EDX','EFLAGS'],no_postRET_memory_seed=True));counts['whole_actual_named_API_entry_return_frame_joins']+=1;api_index+=1
   eq((boundary_index,api_index),(7,4),'Every actual normal source/API boundary joined');eq(m.PCs,read(R/'reports/m4-mfc1168-probe/validation-r6/source-derivations.json')['PCs'],'Literal current cached branch has same physically recovered142-PC closure');eq(m.cpu_now(),tuple(phase['CPU_after']),'Whole literal source-derived actual root CPU40');eq(m.fx,bytes.fromhex(phase['FX_after_hex']),'Whole source-derived actual root FX512');eq(phase['ENV_before_hex'],phase['ENV_after_hex'],'Whole current raw root ENV28 conserved')
   for owner in owner_inputs:
    goal=m.bytes(owner['address'],owner['extent']);eq(goal,raw('MFC1168/AFTER/domain/'+owner['role']+'/bytes.bin'),'Complete source-derived borrowed byteflow including untouched tail');owner['source_final_hex']=goal.hex();counts['whole_borrowed_backing_byteflows']+=1
   for address,goal in whole_targets.items():
    if address==0x20001000:continue
    eq(m.bytes(address,4096),goal,'Whole source-derived current/provider nonstack page '+hex(address));counts['whole_nonstack_source_provider_page_endpoint_joins']+=1
   eq(m.bytes(lockmeta[1],24),raw('MFC1168/AFTER/CRT-codepage-lock/bytes.bin'),'Complete opaque lock endpoint restored; internal OS lock writes untraced');counts['whole_balanced_opaque_CS24_endpoint_joins']+=1
   eq(m.call_stack,[],'Every literal imported/source frame returned');eq(w(m.bytes(teb_base,4))[0],w(teb)[0],'Exact literal source FS restored');actual_teb_after=raw('phase/0/13/TEB-after.bin');eq(w(actual_teb_after)[0],w(m.bytes(teb_base,4))[0],'Actual assembly root-return TIB head independently joins carried literal source');fs=[x for x in m.accesses if x[1]==teb_base and x[4]];eq(len(fs),2,'Literal imported EH install/restore pair');counts['source_FS_install_restore_writes']+=2;counts['ordered_source_operands']+=len(m.accesses)
   result=dict(sequence=seq,root=0x5ae3e4,phase=13,slot=0x5e0040,source_frame=0x20001800,source_CPU_BEFORE=first,source_CPU_AFTER=m.cpu_now(),source_FX_hex=m.fx.hex(),source_ENV_hex=phase['ENV_after_hex'],source_PCs=m.PCs,source_accesses=m.accesses,source_normal_boundary_relations=joins,source_API_relations=api_relations,source_borrowed_backings=owner_inputs,source_FS_writes=fs,source_TEB=teb_base,source_FS_BEFORE=w(teb)[0],source_FS_AFTER=w(m.bytes(teb_base,4))[0],flag_lifetimes=flag_rows,source_state_hex=bytes(m.state).hex(),derived_reached_path=True,actual_per_instruction_chronological_trace=False,intermediate_source_FS_observation=False,boundary_FS_header_scope='Read inside C++ observer after its compiler-owned host exception frame; retained raw, not source input or guest head expectation',whole_stack_endpoint_claim=False,whole_TEB_endpoint_claim=False,opaque_OS_CS_internal_writes_claim=False,source_AFTER_seed=False,actual_prefix_carried_BEFORE=True)
   results.append(result)
  eq((counts['literal_source_instructions'],counts['ordered_source_operands'],counts['whole_normal_CPU_FX_ENV_frame64_boundary_joins'],counts['whole_actual_named_API_entry_return_frame_joins'],counts['whole_borrowed_backing_byteflows']),(852,678,42,24,30),'Complete source-derived six current normal-domain extents')
  q=out/'source-derivations.json';q.write_text(json.dumps(results,indent=2)+'\n');pin(q)
  for module in list(sys.modules.values()):
   p=getattr(module,'__file__',None)
   if p and Path(p).resolve().is_relative_to(R):pin(p)
  pin(R/'tools/m4-mfc1168-connected-original/compare_source_v2.py');pin(R/'tools/m4-mfc1168-connected-original/derive_compare_v3.py');pin(R/'tools/m4-mfc1168-connected-original/compare_source_v3.py');pin(R/'tools/m4-startup131-original/prepare_source.py');pin(__file__);pin(sys.executable)
  for p,h in PINS.items():eq(sha(p),h,'Successful immutable bounded inputs')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Current genuine full131 six-domain MFC phase13 literal replay from each own carried BEFORE;42complete normal and24namedAPIpairs,30wholeborrowedbyteflows/nonstackpages. This is source-derived normal control, without new actual per-instruction trace,opaque OS stack/TEB/CS internal equivalence,lazy/cold or native acceptance.',original_validation_path=str(validation),original_validation_sha256=digest,execution_sha256=v['execution_sha256']if'v'in locals()else None,counts=dict(counts),source_AFTER_seed=False,capture_archive_reader_opened=False,all_bounded_readers_closed=True,initializer_credit=0,files=PINS);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
