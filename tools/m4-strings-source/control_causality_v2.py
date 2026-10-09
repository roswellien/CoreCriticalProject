"""Independent read-only literal-source causality audit of compiled controls.

This never executes the candidate, repairs captures, or loads an AFTER machine
as a model seed. Local source footprints start from authored BEFORE states.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-strings-source'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))

def need(ok,why):
 if not ok:raise ValueError(why)
def sha(path):
 with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(control_path,control_hash,name):
 out=BASE/name;need(not out.exists(),'Fresh independent causality receipt');out.mkdir(parents=True)
 files={};rows=[];static={};passed=False
 def pin(path,digest=None):
  path=Path(path).resolve();actual=sha(path);need(digest is None or actual==digest,'Exact frozen physical input '+str(path));files[str(path)]=actual;return path
 def load(label,path):
  spec=importlib.util.spec_from_file_location(label,pin(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 try:
  controls=json.loads(pin(control_path,control_hash).read_bytes());need(controls['passed'],'Frozen completed control execution')
  buildpath=pin(controls['build'],controls['build_sha256']);build=json.loads(buildpath.read_bytes());need(build['passed'],'Exact successful control build')
  builddir=buildpath.parent;fixture=pin(builddir/'fixture.cpp');hooks=pin(builddir/'fixture_hooks_v2.hpp')
  for path in (fixture,hooks):need(build['sources'].get(str(path))==sha(path),'Physical fixture source is sealed in build')
  text=fixture.read_text();hooktext=hooks.read_text()
  need('const std::array<unsigned,14>points{0,50,50,50,52,54,50,51,52,53,54,55,0,52}'in hooktext,'Exact independently classified intervention sites')
  need('if(selected==5&&w[16]!=4)return;'in hooktext and 'r.memory().protect({0x5e0000},Permissions::none)'in hooktext,'Exact partial-write boundary and correct section Region protection')
  need('Independent deliberate string boundary observer failure'in hooktext,'Deliberate exceptions classified separately from guest source faults')
  strings=pin(ROOT/'reports/m4-strings-native/preparation-r5/strings_operations.inc');binding=pin(ROOT/'reports/m4-strings-native/preparation-r5/locale_batch_binding.inc');operations=pin(ROOT/'reports/m4-strings-native/preparation-r5/locale_batch_operations.inc');session=pin(ROOT/'reports/m4-strings-native/preparation-r5/session_impl.inc')
  source=strings.read_text();op=operations.read_text();bind=binding.read_text();sess=session.read_text()
  for path in(strings,binding,operations,session):need(build['sources'].get(str(path))==sha(path),'Audited Session source belongs to actual linked fixture build')
  need(source.index('Immutable NUL-inclusive source string before literal copy')<source.index('record->words[14]=destination;record->words[22]=frame;string_hook(52)'), 'Immutable input guard precedes entering strcpy and its copy hook')
  need(source.index('string_copy_probe_={')<source.index('string_hook(53)') and source.index('record->words[16]+=bytes;')<source.index('string_hook(54)'), 'Exact prewrite and postcommit observer placement')
  need('string_write_before(a,v,n);'in op and op.index('string_write_before(a,v,n);')<op.index('runtime.memory().write({a},std::span<const std::byte>')<op.index('expected_store(a,&v,n);source_access(a,v,n,true);string_write_after(a,n)'), 'Permission fault occurs before mirror/source commit and postwrite hook')
  need('fault_pc=pc?pc:state.gpr.rip.dword;fault_address=a;'in bind and 'if(!binding->failed)binding->first(exception_message.data())'in sess,'Source explicit CALL denial preserves PC/address while deliberate observer exceptions use current PC/zeroaddress')
  mem=pin(ROOT/'runtime/memory/guest_memory.cpp');loader=pin(ROOT/'tools/m4-startup/image_loader.cpp');memory=mem.read_text();lt=loader.read_text()
  need('regions_.find(start.value)'in memory and 'Protect requires the exact start of an existing region'in memory,'Protect identifies an entire exact mapped Region')
  need('find_access(address, source.size(), Permissions::write)'in memory and memory.index('find_access(address, source.size(), Permissions::write)')<memory.index('std::copy_n(source.data()'),'Whole transfer permission check precedes any guest write')
  need('result.memory.map(region.start, region.size'in lt and 'result.memory.protect(region.start, region.permissions)'in lt,'Image maps full original PE section regions')
  P=load('causality_primary_PE',ROOT/'tools/analysis/pe.py');game=P.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());crt=P.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
  sections={s['name']:s for s in game.sections};data=sections['.data'];rdata=sections['.rdata'];need(game.image_base+data['virtual_address']==0x5e0000 and data['writable']and game.image_base+rdata['virtual_address']==0x5bb000 and not rdata['writable'],'Physical input/data and IAT section permissions are distinct')
  SP=load('causality_literal_string_provider',ROOT/'tools/m4-strings-review/provider_model.py');contracts=pin(ROOT/'reports/m4-strings-review/interface-r2/instruction-contracts.json','b9fa4e6ec5693880cabef35c73305128cb96413cf06e855b9a049a4fdb694a40');program,callbacks=SP.source_program(contracts)
  for pc,row in program.items():
   raw=bytes.fromhex(row['bytes_hex']);off,_=crt.rva_range(pc-crt.image_base,len(raw));need(crt.data[off:off+len(raw)]==raw,'Physically exact original instruction causing read/write/CALL/RET')
  need(program[0x78002f52]['operands']=='eax, dword ptr [ecx]'and program[0x78002fde]['operands']=='dword ptr [edi], edx','Fault read/store operands are exact original DWORD instructions')
  inputrows=json.loads(pin(BASE/'recovery-r7/string-inputs.json','154ddc989e3f09bf9cbb8729b41a271f8bfc21db9a8623528805580c5ad10dce').read_bytes());first=next(q for q in inputrows if q['root']==0x4487e0);physical=bytes.fromhex(first['physical_bytes_hex']);sourceptr=first['source'];payload=bytes.fromhex(first['bytes_hex']);need(sourceptr==0x5e4240 and payload==b'Lab State\0'and len(physical)==12,'Exact first literal string and terminal DWORD padding')
  off,_=game.rva_range(sourceptr-game.image_base,len(physical));need(game.data[off:off+len(physical)]==physical,'Physically exact BEFORE source string')
  destination=0x35000100
  def model(body,args,corrupt=False):
   state=bytearray(3504)
   for n,reg in enumerate(SP.I.REG):struct.pack_into('<I',state,SP.I.REG[reg],0x41320100+n*0x10101)
   struct.pack_into('<I',state,SP.I.REG['esp'],0x20001800)
   for flag,value in dict(CF=1,PF=0,AF=1,ZF=0,SF=1,DF=0,OF=1).items():state[SP.I.FLAGS[flag]]=value
   page=bytearray(4096);page[sourceptr%4096:sourceptr%4096+len(physical)]=physical
   if corrupt:page[sourceptr%4096]^=1
   m=SP.Machine(state,bytes(512),bytes(40),{0x20001000:bytes(4096),sourceptr&~4095:page,destination&~4095:bytes([0xcd])*4096},program=program,callbacks=callbacks)
   for n,arg in enumerate(args):m.store_bytes(0x20001800+4*n,struct.pack('<I',arg))
   m.invoke_external(body,0xffffff01);return m
  normal_len=model(0x78002f32,(sourceptr,));corrupt_len=model(0x78002f32,(sourceptr,),True);copy=model(0x78002fab,(destination,sourceptr));writes=[r for r in copy.string_observations if r[4]and destination<=r[1]<destination+10];need(normal_len.reg('eax')==corrupt_len.reg('eax')==9,'Literal source proves length-preserving corruption still requests malloc10');need([q[3]for q in writes]==[4,4,2]and writes[0][0]==writes[1][0]==0x78002fde,'Literal first/next DWORD transfer and final NUL word are derived before captures')
  static=dict(physical_provider_rows=len(program),data_region=0x5e0000,IAT_region=0x5bb000,IAT_region_readonly=True,source=sourceptr,input_hex=payload.hex(),physical_input_hex=physical.hex(),literal_strlen_result=9,corrupted_literal_strlen_result=9,malloc_request=10,source_strlen_reads=normal_len.string_observations,source_strcpy_writes=writes,source_read_fault_instruction=program[0x78002f52],destination_fault_instruction=program[0x78002fde],length_corruption_refusal_before_strcpy=True,local_BEFORE_model=True,AFTER_machine_seed=False)
  D=load('causality_direct_archive',ROOT/'tools/m4-crt-allocation-root/run_v2.py')
  categories=['ordinary_source_sequence','argument_owner_guard','immutable_input_guard','source_read_permission','destination_write_permission','destination_next_write_permission','deliberate_observer_exception','deliberate_observer_exception','deliberate_observer_exception','deliberate_observer_exception','deliberate_observer_exception','deliberate_observer_exception','IAT_control','native_owner_guard']
  PCs={1:0x78010a6d,2:0x78010a8b,3:0x78002f52,4:0x78002fde,5:0x78002fde,6:0x78010a6d,7:0x78010a7c,8:0x78002fab,9:0x78002fde,10:0x78002fde,11:0x48eb28,13:0x78002fab}
  stages={1:50,2:43,3:50,4:53,5:53,6:50,7:51,8:52,9:53,10:54,11:55,13:52}
  progress={1:(0,0,0,0),2:(9,10,0,0),3:(0,0,0,0),4:(9,10,0,0),5:(9,10,4,0),6:(0,0,0,0),7:(9,0,0,0),8:(9,10,0,0),9:(9,10,0,0),10:(9,10,4,0),11:(9,10,10,1),13:(9,10,0,0)}
  issues=[]
  for level in controls['levels']:
   worker=build['workers'][level['level']];pin(worker['path'],worker['sha256']);pin(level['stage'],level['stage_sha256'])
   a=D.DirectSet(pin(level['capture'],level['capture_sha256']),pin)
   try:
    for selected in range(14):
     prefix=f'case-{selected}/first-live/';clean=f'case-{selected}/first-cleaned/';tags=struct.unpack_from('<32Q',a.data(f'case-{selected}/first.bin'));retry=struct.unpack_from('<32Q',a.data(f'case-{selected}/retry.bin'));fault=a.words(prefix+'locale-fault.bin',4);finalfault=a.words(clean+'locale-fault.bin',4);summary=a.words(prefix+'registry-summary.bin',32,'Q');message=a.data(prefix+'registry-exception-message.bin').decode();string_rows=list(struct.iter_unpack('<32Q',a.data(prefix+'strings-witnesses.bin')));owned=list(struct.iter_unpack('<16Q',a.data(prefix+'locale-allocations.bin')));cleanowned=list(struct.iter_unpack('<16Q',a.data(clean+'locale-allocations.bin')));access=list(struct.iter_unpack('<IIQII',a.data(prefix+'locale-source-accesses.bin')))
     need(tags[:3]==(1,selected,0)and retry[:3]==(1,selected,1),'Exact source case identifiers');need(tags[4]==tags[12]and retry[4]==tags[4]and retry[10]==tags[10]and (not selected or tags[15:20]==retry[15:20]),'Retry retains exact completed prefix and prior first fault without routes; ordinary success first establishes its consumed-context retry fault');need(finalfault==fault,'Cleanup retains the first precise source fault')
     need(all(not q[8]and not q[9]and (q[10]or q[11])for q in cleanowned),'All true owners released and unmapped after cleanup')
     duplicates=[q for q in owned if q[6]==3];copied=[];allocation=None
     if selected not in(0,12):
      need(tags[4]==20 and len(string_rows)==1,'Every first-string intervention retains exactly20 completed selected roots')
      q=string_rows[0];need(q[:5]==(1,0,0x4487e0,0x78010a6d,sourceptr)and q[6]==0x48eb28 and q[7]==10,'True source root/CALL/frame/input witness')
      need(fault==(1,PCs[selected],(0x20001000 if selected==1 else sourceptr if selected in(2,3)else q[10]+(4 if selected==5 else 0)if selected in(4,5,13)else 0),stages[selected]),'Independently derived exact source guard PC/address and stable stage')
      need((q[8],q[9],q[16],q[17])==progress[selected],'Exact strlen/malloc/copy/RET causal prefix')
      need(len(duplicates)==(0 if selected in(1,3,6,7)else 1),'No counterfeit or extra string allocation before source fault')
      copied=[r for r in access if r[4]and q[10]and q[10]<=r[1]<q[10]+10 and r[0]in program and r[0]in(0x78002fde,0x7800366b,0x7800368c,0x78003693,0x780036a5,0x780036ad,0x780036b6)]
      expected=[(pc,q[10]+address-destination,value,width,write)for pc,address,value,width,write in writes if address-destination<q[16]];need(copied==expected,'Actual entire committed copy ledger is the literal model prefix')
      need(not any(r[4]and r[1]==0x6059fc for r in access),'Fault does not publish object pointer after interrupted constructor')
      if selected in range(6,12):need(message=='Independent deliberate string boundary observer failure'and fault[2]==0,'Observer exception is not credited as a guest permission/API fault')
      if duplicates:
       allocation=duplicates[0];need(allocation[1]==q[10]and allocation[2]==10 and allocation[3]==q[13]==16 and allocation[5]==q[12]and allocation[7]==q[11]and allocation[8]and allocation[9],'Exact actual privately owned malloc10/capacity16 identity')
       stem=prefix+f'locale-allocation-{allocation[5]}';initial=a.data(stem+'-initial.bin');expected_bytes=a.data(stem+'-expected.bin');page=a.data(stem+'-owned-page.bin');need(len(initial)==allocation[3]and len(expected_bytes)==allocation[4]and expected_bytes[:10]==payload[:q[16]]+initial[q[16]:10]and expected_bytes[10:allocation[3]]==initial[10:]and expected_bytes[allocation[3]:]==bytes(allocation[4]-allocation[3])and page==expected_bytes,'Complete actual guest mirror keeps only committed source bytes, untouched native owner remainder and zero initialized extra mapped bytes')
     elif selected==0:
      need(tags[3]==1 and tags[4]==71 and not fault[0]and len(string_rows)==len(duplicates)==16,'Ordinary71 reaches16 true dup calls and no fault')
     else:
      # The original case12 lacks a permission transition. It fails inside
      # the fixture store and never reaches an initializer/IAT source guard.
      write='c.runtime().memory().store<unsigned>({0x5bb670},0x78010a6d);'
      need(write in text,'Case12 physical intervention is an exact IAT store')
      if 'protect({0x5bb000}'not in text:
       need(tags[4]==0 and tags[16]==0x410a80 and not tags[6]and fault[:3]==(0,0,0)and not string_rows and not duplicates,'Protected IAT observer write throws before all source execution')
       categories[12]='observer_attempted_readonly_IAT_write';issues.append(dict(level=level['level'],case=12,intended_identity_guard_reached=False,actual='GuestMemory permission_denied during fixture before_phase store into original read-only .rdata',Context_fault_PC=0x410a80,Context_fault_address=0,source_fault=False,completed_prefix=0))
      else:
       need(tags[4]==20 and fault[0]and fault[2]==0x5bb670 and not string_rows and not duplicates,'True changed IAT is rejected by owning source identity before first strdup');need(categories[12]=='IAT_control','Stable IAT control classification')
     rows.append(dict(level=level['level'],case=selected,category=categories[selected],completed_prefix=tags[4],Context_fault=list(tags[15:20]),source_fault=list(fault),exception_message=message,duplicate_allocations=len(duplicates),string_progress=list(progress[selected])if selected in progress else None,committed_source_copy_rows=copied,full_allocation_identity=list(allocation)if allocation else None,after_seed=False))
   finally:a.close()
  pin(__file__)
  for m in list(sys.modules.values()):
   p=getattr(m,'__file__',None)
   if p and Path(p).resolve().is_relative_to(ROOT/'tools')and Path(p).is_file():pin(p)
  passed=not issues
  (out/'issues.json').write_text(json.dumps(issues,indent=2)+'\n');pin(out/'issues.json')
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'literal-source-derivation.json').write_text(json.dumps(static,indent=2)+'\n');pin(out/'literal-source-derivation.json');(out/'case-causality.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'case-causality.json')
  report=dict(passed=passed,schema='mw34-strings-source-independent-control-causality-v1',scope='Read-only literal instruction/BEFORE footprint and direct compiled control prefix audit; no native recapture, candidate modifications, initializer credit or AFTER machine seed',control_execution=str(control_path),control_execution_sha256=control_hash,levels=2,cases=len(rows),all_intended_controls_reached=passed,guest_permission_fault_cases=[3,4,5],deliberate_observer_exception_cases=list(range(6,12)),full_state_seeded_from_AFTER=False,source_copy_prefix_derived_from_BEFORE=True,source_data_region_protection=0x5e0000,files=files)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),cases=len(rows))))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
