"""Independent actual container control causality, ownership and physical audit."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
from stages import verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def rows(b,n):
 need(len(b)%(8*n)==0,'Whole fixed records');return list(struct.iter_unpack('<'+str(n)+'Q',b))
def main(name,build_path,run_path):
 out=R/'reports/m4-container-control-audit'/name;need(not out.exists(),'Fresh independent audit');out.mkdir(parents=True);pins={};counts=collections.Counter();cases=[];physical={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=pins.get(str(p))
  if v is None:v=sha(p)
  need(h is None or h==v,'Physical file identity '+str(p));pins[str(p)]=v;return p
 try:
  build_path=Path(build_path).resolve();run_path=Path(run_path).resolve();build=json.loads(pin(build_path).read_bytes());run=json.loads(pin(run_path).read_bytes());need(build['passed']and run['passed'],'Frozen actual build and complete executions')
  for p,h in json.loads(pin(build_path.parent/'pins.json').read_bytes())['files'].items():pin(p,h)
  parent=json.loads(pin(R/'reports/m4-container-native/preparation-r2/report.json','4d1eb214d383b99a857e927e90768e3de4f87429f1c4def90c49067340e02164').read_bytes());need(parent['passed'],'Exact production derivative')
  H=load('accepted_fs_audit_helpers',pin(R/'tools/m4-fs-control-audit/audit_v6.py'));D=load('canonical_control_reader',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));PE=load('control_physical_PE',pin(R/'tools/m4-strings-control-audit/audit_v9.py'));J=load('complete_State_ENV_projection',pin(R/'tools/m4-joint-startup27-review/observe.py'));model,_,_,_=J.models();pins.update(J.PINS)
  fixture=pin(build_path.parent/'fixture.cpp').read_text();hook=pin(build_path.parent/'hooks.hpp').read_text();asm=pin(build_path.parent/'capture.s').read_text()
  wrapper=fixture[fixture.index('[[clang::noinline]] unsigned invoke('):fixture.index('struct NativeBackingSink')]
  need(wrapper.index('ErrorBoundary errors')<wrapper.index('NumericHostBoundary boundary')<wrapper.index('try{')<wrapper.index('catch(...)')<wrapper.index('return t.okay'),'Caller numerical/error boundaries lexically enclose calls and actual C++ catch')
  need('if(t.retry)t.c->registry().replay(container_roots[0])'in wrapper and 't.c->registry().bootstrap();for(auto root:container_roots)'in wrapper,'Same completed/poisoned Session invokes exact checked source research calls')
  need('const bool boundary_equal=hardware_equal(before,after);restore.restore()'in fixture and 'sample.tags='in fixture,'Actual immediate strict hardware sampled before diagnostic restoration')
  need('reinterpret_cast<const void*>(row[8]),row[3]'in fixture,'Actual complete full-width private native extent capture')
  need(fixture.index('auto game=old::read(')<fixture.index('Context c(')and 'std::as_bytes(std::span{mfc})'in fixture,'All original physical provider inputs outlive Context')
  need('fxrstor64 (%r9)'in asm and 'fldenv 512(%r9)'in asm and asm.index('fxsave64 (%rsi)')<asm.index('callq data_boundary_initialize')<asm.index('fxsave64 (%rdi)'),'Actual sampler loads rich input and immediately retains before/after raw hardware')
  need('container-null-active.bin'in hook and 'words[0]^=1'in hook and 'mutation_hits==1'in hook,'Private scalar mutation is actual underlying span')
  page_header=pin(build_path.parent/'current_pages.hpp').read_text();declared_pages=tuple(int(v,16)for v in re.search(r'current_pages\{([^}]+)\}',page_header)[1].split(','))
  need(len(declared_pages)==len(set(declared_pages))==59 and all(v%4096==0 for v in declared_pages)and 0x5f4ce000 not in declared_pages and 0x7ffde000 not in declared_pages,'Exact59 already-admitted full current pages; borrowed pointee and TIB holes excluded')
  native_contract=pin(R/'reports/m4-container-native/preparation-r2/container_contract.inc').read_text();source_pages={int(v)for v in re.findall(r'\{(\d+),[135]\}',native_contract[native_contract.index('std::span<const SourcePage>source_pages()'):])}
  registry_contract=pin(R/'reports/m4-container-native/preparation-r2/registry_contract.inc').read_text();game_pages={int(v)for v in re.search(r'registry_game_pages\[\]\{([^}]+)\}',registry_contract)[1].split(',')}
  need(source_pages|game_pages<=set(declared_pages)and {0x20000000,0x20001000}<=set(declared_pages),'Current inventory contains every exact provider/game input page and both source stack pages')
  need('c.runtime().memory().read({address},b);w.append(prefix+"current-page-"'in fixture,'Current pages measured directly from source memory rather than historical checkpoint mirrors')
  specs=json.loads(pin(R/'reports/m4-container-source/allocation-interface-r1/allocation-inputs.json').read_bytes());specs={(r['root'],r['CALL_pc']):r for r in specs}
  borrowed_specs=json.loads(pin(R/'reports/m4-container-source/allocation-interface-r1/borrowed-constructor-inputs.json').read_bytes());vector_specs=json.loads(pin(R/'reports/m4-container-source/allocation-interface-r1/vector-endpoints.json').read_bytes())
  contracts=json.loads(pin(R/'reports/m4-container-source/recovery-r3/instruction-contracts.json').read_bytes());inst={q['pc']:q for q in contracts['instructions']}
  physical_parser=load('independent_literal_PE',pin(R/'tools/analysis/pe.py'));game=physical_parser.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());mfc=physical_parser.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())
  for q in inst.values():need(game.read(game.rva_range(q['pc']-game.image_base,q['width'])[0],q['width'])==bytes.fromhex(q['bytes_hex']),'All literal game instruction rows physically bound')
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';pin(llvm/'llvm-nm.exe');pin(llvm/'llvm-objdump.exe')
  for r in run['levels']:
   level=r['level'];worker=build['workers'][level];pin(worker['path'],worker['sha256']);need(PE.machine(worker['path'])==0x8664,'Actual AMD64 control executable');tree=Path(worker['path']).parent;ninja=pin(tree/'build.ninja').read_text();link=next(x for x in ninja.splitlines()if x.startswith('build mw34_joint_startup116.exe:')).replace(chr(92),'/');objects=[q for q in worker['objects']if q.endswith('.obj')];proof=[q for q in worker['objects']if not q.endswith('.obj')]
   need(all(Path(q).as_posix().replace(':','$:')in link and PE.machine(pin(q))==0x8664 for q in objects),'Every declared literal AMD64 COFF actually reaches final link')
   need('CMakeFiles/mw34_joint_startup116.dir/fixture.cpp.obj'in link and 'capture.obj'in link,'Authored fixture and preserved assembly physically linked')
   obj=pin(tree/'CMakeFiles/mw34_joint_startup116.dir/fixture.cpp.obj');nm=subprocess.run([str(llvm/'llvm-nm.exe'),str(obj)],capture_output=True,check=True,creationflags=0x08000000).stdout.decode();syms=[x.split()[-1]for x in nm.splitlines()if ' t ?invoke@'in x];need(len(syms)==1,'Actual distinct noinline caller wrapper');start=int(next(x.split()[0]for x in nm.splitlines()if x.split()[-1:]==syms),16);dis=subprocess.run([str(llvm/'llvm-objdump.exe'),'-dr','--start-address='+str(start),'--stop-address='+str(start+0x900),str(obj)],capture_output=True,check=True,creationflags=0x08000000).stdout.decode();dest=out/(level+'-wrapper.txt');dest.write_text(dis);pin(dest);need('Session'in dis and 'replay'in dis and ('NumericHostBoundary'in dis or ('fxsave'in dis and 'fxrstor'in dis)),'Actual compiled calls and numerical lifetime')
   stage=json.loads(pin(r['stage'],r['stage_sha256']).read_bytes());verify_stage(Path(r['stage']).parent,r['stage_sha256']);need(stage['argv'][0]==worker['path']and stage['input_sha256'][worker['path']]==worker['sha256']and stage['artifact_sha256'][r['capture']]==r['capture_sha256'],'Actual stage binds worker and immutable transport')
   physical[level]=dict(linked_literal_COFFs=len(objects),retained_unlinked_proof_archives=proof,worker_sha256=worker['sha256'],wrapper_symbol=syms[0]);a=D.DirectSet(pin(r['capture'],r['capture_sha256']),pin)
   try:
    need(a.words('header.bin',6)==(1,34,68,9968,7,8)and a.data('COMPLETE.txt')==b'Bounded seven-root container/borrowed/null-free research controls passed; canonical116 is separate\n','Genuine complete isolated workload')
    for c in range(34):
     stem=f'case-{c}/';live=stem+'first-live/';clean=stem+'first-cleaned/';trig=stem+'first-trigger/';first=H.sample(a.data(stem+'first.bin'),c,0);retry=H.sample(a.data(stem+'retry.bin'),c,1);counts['outside_hardware_pairs']+=2
     for attempt in('first','retry'):H.hw(a.data(stem+attempt+'-cleanup-hardware-before.bin'),a.data(stem+attempt+'-cleanup-hardware-after.bin'));counts['cleanup_hardware_pairs']+=1
     names={n[len(clean):]for n in a.entries if n.startswith(clean)}
     for dest in(stem+'retry-live/',stem+'retry-cleaned/'):
      need({n[len(dest):]for n in a.entries if n.startswith(dest)}==names,'Entire retry dump domain, no omitted raw observation')
      for n in names:need(a.data(clean+n)==a.data(dest+n),'Refused same Session conserves every complete logical payload '+n)
     counts['retry_equal_records']+=2*len(names);counts['full_machine_retries']+=1
     firstb=a.data(stem+'first.bin');retryb=a.data(stem+'retry.bin');need(firstb[4272:7776]==retryb[768:4272]and firstb[8288:8800]==retryb[7776:8288]and firstb[8840:8880]==retryb[8800:8840],'Retry enters genuinely prior cleaned complete machine')
     for p in(live,clean):
      need(a.words(p+'current-page-addresses.bin',59)==declared_pages,'Actual current inventory exactly59 physical source/game/stack pages')
      need(all(len(a.data(p+'current-page-'+str(address)+'.bin'))==4096 for address in declared_pages),'Every current page retains all4096 bytes')
      counts['whole_current_page_records']+=len(declared_pages)
     def current(address,size=4):
      page=address&~4095;need(page in declared_pages and address+size<=page+4096,'Admitted bounded current-page read');return a.data(live+'current-page-'+str(page)+'.bin')[address-page:address-page+size]
     need(a.data(live+'current-page-'+str(0x20001000)+'.bin')==a.data(stem+'first-causal-stack.bin'),'Current entire stack is the actual first-refusal/source-return stack')
     source=list(struct.iter_unpack('<IIQII',a.data(live+'locale-source-accesses.bin')));allocs=rows(a.data(live+'locale-allocations.bin'),16);freed=rows(a.data(clean+'locale-allocations.bin'),16);mfcs=rows(a.data(live+'mfc-allocation-witnesses.bin'),32)
     need(len(allocs)==len(freed)and all(p[:8]==q[:8]and q[8:10]==(0,0)and q[10]+q[11]==1 for p,q in zip(allocs,freed)),'Every actual owner retains exact provenance and is released/unmapped once')
     for owner in allocs:
      p=live+f'locale-allocation-{owner[5]}';initial=a.data(p+'-initial.bin');expected=a.data(p+'-expected.bin');guest=a.data(p+'-owned-page.bin');native=a.data(live+f'native-full-{owner[5]}.bin');need(len(initial)==owner[3]and len(expected)==len(guest)==owner[4]and len(native)==owner[3]and owner[2]<=owner[3]<=owner[4]and owner[7]==owner[8]and owner[8]>0xffffffff and owner[9],'Complete actual native/guest/initial extents and full private pointer')
      reconstructed=bytearray(initial+bytes(owner[4]-owner[3]))
      if owner[6]in(3,4):
       for pc,address,value,width,writing in source:
        if writing and owner[1]<=address<owner[1]+owner[4]:need(address+width<=owner[1]+owner[2]and width in(1,2,4,8),'Source store respects exact requested bytes');reconstructed[address-owner[1]:address-owner[1]+width]=value.to_bytes(width,'little')
       need(bytes(reconstructed)==expected==guest,'Entire source-owned page reconstructed from actual acquired input plus only committed source writes');counts['full_owned_page_source_replays']+=1
      if c==13 and native!=expected[:owner[3]]:need(owner[6]==4 and native[:-1]==expected[:owner[3]-1]and native[-1]==expected[owner[3]-1]^0x55,'Only exact last native byte intervention changes genuine backing')
      else:need(native==expected[:owner[3]],'Actual entire live native extent equals committed guest mirror')
     for q in mfcs:
      spec=specs[q[2],q[4]];need(q[7]==spec['requested_size']and q[6]==q[4]+inst[q[4]]['width']and(q[4],q[5],q[6],4,1)in source,'Exact literal MFC request/source CALL frame')
      owner=next(o for o in allocs if o[5]==q[18]);need((owner[1],owner[2],owner[3],owner[7])==(q[16],q[7],q[19],q[17]),'Actual owner generation/request/alias/fullNative joins genuine allocator record')
     frames=rows(a.data(live+'fs-frame-witnesses.bin'),32);tib=a.words(live+'fs-current-tib.bin',5);need(tib[0]==tib[4]==0x7ffde000 and tib[2:4]==(0x20002000,0x20001000),'Minimal declared owned TIB identity')
     for raw in rows(a.data(live+'fs-record-bytes.bin'),16):
      rebuilt={}
      for pc,address,value,width,writing in source[:raw[11]]:
       if writing:
        for i in range(width):
         if raw[6]<=address+i<raw[6]+12:rebuilt[address+i-raw[6]]=(value>>(8*i))&255
      need(set(rebuilt)==set(range(12))and bytes(rebuilt[i]for i in range(12))==struct.pack('<3I',*raw[8:11]),'Complete12B FS records from latest genuine source writes');counts['complete12B_FS_records']+=1
     for label in('first-causal','retry-causal'):need(model.proj(a.data(stem+label+'-State.bin'))[1]==a.data(stem+label+'-guest-ENV.bin'),'Guest full ENV derives from entire3504B captured State');counts['guest_ENV_relations']+=1
     fault=a.words(live+'locale-fault.bin',4);reason=a.data(live+'locale-fault-reason.bin').decode()if c else '';identity=a.words(trig+'identity.bin',3);null=a.words(trig+'nullfree.bin',32,'Q');borrow=a.words(trig+'borrowed.bin',32,'Q');vec=a.words(trig+'vector.bin',16,'Q');string=a.words(trig+'string.bin',32,'Q');mf=a.words(trig+'mfc.bin',32,'Q')
     if c:
      observer='Deliberate precise container/borrowed/null-free boundary observer failure';store='Checked actual source locale/parser store fault';private='Container observer changed private import/borrowed/null-free/store witnesses';page='Only committed source/API/research effects may change owned locale pages'
      expected={1:(0x5abd1a,0x5bb4c8,75,'Exact container game owning ordinal source import relocation'),2:(0x5abdb0,0x5bb454,55,'Exact container game owning ordinal source import relocation'),3:(0x5f4020b4,0x5f4cc000,94,page),4:(0x5f4020be,borrow[7],97,store),5:(0x5f401782,0x20001000,90,page),6:(0x78001390,0,91,observer),7:(0x5f40178c,0,92,observer),8:(0x780013a6,0x7ffde000,91,store),9:(0x4ad8eb,0x60b11c,100,store),10:(0x4ad90c,0x60b114,73,store),11:(0x4ad91a,0x60b118,100,store),12:(0x78002fde,string[10]+4,53,store),13:(0x4ad8eb,mf[16],101,'Checked complete current guest/native allocation backing and private generation required'),14:(0x482b4e,0x7ffde000,81,store),15:(0x4ad91f,0x7ffde000,83,store)}
      for k,pc,point in((16,0x5f4020be,97),(17,0x78001390,91),(18,0x5f4020b4,94),(19,0x4ad8eb,100),(20,0x4ad8eb,101),(21,0x5f401782,90)):expected[k]=(pc,pc,point,private)
      points=(0x5f401782,0x78001390,0x5f40178c,0x4ad8dd,0x5f4020b4,0x5f4020bc,0x5f4020bc,0x5f4020be,0x5f4020be,0x482b7b,0x4ad8eb,0x4ad8eb)
      if c>=22:expected[c]=(points[c-22],0,c+68,observer)
      need(first[3]==0 and first[5]==1 and first[14]==1 and fault==(1,*expected[c][:3])and reason==expected[c][3],'Exact independently classified reached cause/PC/address/stage')
      if c in(4,8,9,10,11,12,14,15):need(not any(pc==fault[1]and address==fault[2]and writing for pc,address,_,_,writing in source),'Actual first refused source store uncommitted')
      if c in(3,5,6,7,13)or c>=16:need(a.data(trig+'State.bin')==a.data(stem+'first-causal-State.bin'),'Immediate direct observer/private/backing refusal conserves every source State byte');counts['complete_trigger_causal_State_relations']+=1
      if c in(1,2):
       slot=0x5bb4c8 if c==1 else 0x5bb454;raw=0x80000339 if c==1 else 0x8000021c;want=bytearray(game.read(game.rva_range(0x5bb000-game.image_base,4096)[0],4096));want[slot-0x5bb000:slot-0x5bb000+4]=struct.pack('<I',raw^1)
       need(fault[2]==slot and current(0x5bb000,4096)==want,'Actual whole raw game IAT page differs only at exact deliberate owning slot');counts['whole_current_mutation_pages']+=1
      if c==3:
       want=bytearray(mfc.read(mfc.rva_range(0x5f4cc000-mfc.image_base,4096)[0],4096));want[0xb54:0xb58]=struct.pack('<I',0x5f4cecec^4);need(current(0x5f4cc000,4096)==want,'Actual whole provider input page retains exact single DWORD corruption');counts['whole_current_mutation_pages']+=1
      if c==5:need(current(null[5]+4)==struct.pack('<I',1),'Actual checked null-free frame argument mutation was presented')
      if c in(4,9,10,11):
       address=fault[2];writes=[row for row in source if row[4]and row[1]==address and row[3]==4]
       if writes:value=writes[-1][2]
       else:
        rva=address-game.image_base;section=next(q for q in game.sections if q['virtual_address']<=rva and rva+4<=q['virtual_address']+max(q['virtual_size'],q['raw_size']));delta=rva-section['virtual_address']
        need(delta>=section['raw_size'],'Uncommitted protected constructor field has explicit PE zero-fill input');value=0
       need(current(address)==struct.pack('<I',value),'Actual protected publication/endpoint remains its exact input or earlier committed source value');counts['actual_refused_field_prefixes']+=1
      if c==12:
       owner=next(o for o in allocs if o[5]==string[12]);before=a.data(trig+'native-before.bin');initial=a.data(live+f'locale-allocation-{owner[5]}-initial.bin');want=bytearray(initial);want[:4]=a.data(live+'string-0-input.bin')[:4];need(string[16]==4 and before==bytes(want)==a.data(live+f'native-full-{owner[5]}.bin'),'Exactly4 real copied bytes plus every untouched trailing native byte');counts['actual_partial_copy_prefixes']+=1
      if c==13:
       before=a.data(trig+'native-before.bin');want=bytearray(before);want[-1]^=0x55;need(a.data(trig+'native-after.bin')==want==a.data(live+f'native-full-{mf[18]}.bin'),'Entire full-native before/after actual last-byte mutation');counts['actual_native_mutations']+=1
      for k,fn,width,index,want in((16,'container-borrowed-witnesses.bin',32,-14,borrow[18]^1),(17,'container-nullfree-witnesses.bin',32,-25,null[7]^1),(18,'container-import-ledger.bin',8,-2,0x5f4020b4^1),(19,'container-vector-probe.bin',16,6,vec[6]^1),(20,'container-vector-stores.bin',16,-10,vec[6]^1)):
       if c==k:values=struct.unpack('<'+'Q'*(len(a.data(live+fn))//8),a.data(live+fn));need(identity[2]==1 and values[index]==want,'Exact actual private span one-word flip retained');counts['actual_private_mutations']+=1
      if c==21:need(identity[2]==1 and a.words(live+'container-null-active.bin',1)==(0,),'Exact actual private active scalar flip');counts['actual_private_mutations']+=1
      if c==20:need(source[-1]==(vec[3],vec[4],vec[6],4,1),'Private committed ledger flip leaves actual store genuine')
      counts['intended_refusals']+=1;cases.append(dict(level=level,case=c,completed=first[4],PC=fault[1],address=fault[2],stage=fault[3],reason=reason))
     else:
      need(first[3:6]==(1,7,0)and first[10:12]==(7,5)and first[17]==1 and len(allocs)==9,'Actual ordinary7root/5MFC/3string/registry positive extent and real unmapped borrowed-pointee probe')
      nulls=rows(a.data(live+'container-nullfree-witnesses.bin'),32);borrows=rows(a.data(live+'container-borrowed-witnesses.bin'),32);stores=rows(a.data(live+'container-vector-stores.bin'),16);need(len(nulls)==5 and len(borrows)==3 and len(stores)==17,'Genuine five nullfree/three borrowed/17endpoint source units')
      for w in nulls:
       need(w[7]==0 and w[11]==w[16]==0x78001390 and w[12]==w[5]-8 and w[13]==0x5f40178c and w[17:19]==(1,1)and w[19]==w[20]==w[21]==w[22]==w[29]==w[30]and w[23]==w[24]and w[25]==w[26]and w[10]==w[31],'Exact genuine zero free frames/literal EAX/chain and zero owner/API/generation effects')
       seq=source[w[27]:w[28]];F=w[12];head=F-20
       for row in((0x78001395,F-12,0x7802e260,4,1),(0x7800139a,F-16,0x7800ef03,4,1),(0x780013a5,head,w[19],4,1),(0x780013a6,0x7ffde000,head,4,1),(0x78001419,0x7ffde000,w[19],4,1),(0x78001424,F,0x5f40178c,4,0)):need(row in seq,'Literal complete nested CRT FS/source RET unit')
       counts['actual_nested_nullfree_units']+=1
      for w in borrows:
       spec=next(s for s in borrowed_specs if s['root']==w[2]);need(w[7]==spec['object']and w[10]==w[5]-8 and w[11:16]==(0x5f4020bc,0x5f4ccb54,0x5f4ccb54,0x5f4020bc,0x5f4cecec)and w[16:20]==(w[7],0x5f4020be,0x5f4cecec,1)and w[20:23]==(0x5f4020c3,w[7],1),'Exact source borrowed read/store/object return and own module scalar provenance')
      footprint=[s for s in source if s[1]<0x5f4cd000 and s[1]+s[3]>0x5f4cc000];need(footprint==[(0x5f4020bc,0x5f4ccb54,0x5f4cecec,4,0)]*3 and not any(s[1]<0x5f4cf000 and s[1]+s[3]>0x5f4ce000 for s in source),'Entire data-page footprint exactly3DWORD reads, no pointee dereference')
      for w in stores:need(source[w[15]-1]==(w[3],w[4],w[6],4,1)and w[6]==w[9]+(w[11]if w[7]==3 else 0),'Every endpoint joins exact genuine source commit and owned begin/request');counts['actual_endpoint_source_joins']+=1
      for owner in allocs:
       if owner[6]==4:need(not any(s[4]and s[1]<owner[1]+owner[2]and s[1]+s[3]>owner[1]for s in source),'All five true acquired vector buffers stay entirely source-unchanged')
      need(all(o[10]==1 and o[11]==0 for o in freed),'Ordinary owners genuinely source freed once');counts['ordinary_sequences']+=1
     need(a.data(live+'fs-current-tib.bin')==a.data(clean+'fs-current-tib.bin')and a.data(live+'fs-active-records.bin')==a.data(clean+'fs-active-records.bin'),'Cleanup preserves actual source chain without invented unwind')
     heap=a.words(clean+'heap-create-registry.bin',18,'Q');need(heap[4]>0xffffffff and heap[7]==0 and heap[8:11]==(1,1,1)and heap[15]==1 and heap[16]==heap[4],'Same actual full-width native heap destroyed once')
     ids=[H.identity(a,clean+'heap-destroy-api-'+p,pin,PE)for p in('before','after')];ids.append(H.identity(a,stem+'first-cleanup-api-after',pin,PE,True));need(ids[0]==ids[1]==ids[2],'True pre/post/immediate-independent HeapDestroy identity triplet');counts['HeapDestroy_identity_triplets']+=1;counts['actual_scenarios']+=1
     print(json.dumps(dict(level=level,case=c,passed=True,retry_records=len(names))),flush=True)
   finally:a.close()
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  pin(__file__)
  for p in out.rglob('*'):
   if p.is_file():pin(p)
  report=dict(passed=passed,scope='Independent actual isolated7roots/34scenarios O0/O2 with same finished/poisoned Session retry. Exact authored caller NumericHostBoundary/ErrorBoundary through C++ catch; no naked throwing API metadata guarantee, virtual unwind, handler/TLS or initializer credit. Production and captures unchanged.',counts=dict(counts),cases=cases,physical_link=physical,initializer_credit=0,native_executed_by_auditor=False,files=pins,physical_closure=verify_manifest(pins));(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=counts)),flush=True)
if __name__=='__main__':main(*sys.argv[1:])
