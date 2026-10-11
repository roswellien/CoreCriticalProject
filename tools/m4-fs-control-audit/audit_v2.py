"""Independent read-only audit of actual wrapped six-root FS controls.

Literal committed source accesses replay measured allocation BEFORE bytes.
No provider execution, repaired captures, API injection, or numerical AFTER oracle.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
from stages import verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def rows(b,n,k='Q'):
 width=struct.calcsize('<'+str(n)+k);need(len(b)%width==0,'Complete fixed record encoding');return list(struct.iter_unpack('<'+str(n)+k,b))
def hw(b,a):
 need(len(b)==len(a)==544,'Physical measured hardware extent')
 need(b[:5]==a[:5]and b[24:28]==a[24:28]and b[512:540]==a[512:540]
      and all(b[32+16*i:42+16*i]==a[32+16*i:42+16*i]for i in range(8))
      and b[256:416]==a[256:416],'Actual raw80/CW/SW/FTW/MXCSR/full legacyENV/XMM6..15 exact')
def sample(b,case,retry):
 need(len(b)==9968,'Exact compiled packed ABI');q=struct.unpack_from('<32Q',b)
 need(q[:3]==(1,case,retry)and q[6]==q[16]==1 and q[7]==0x4d573354 and not((q[8]^q[9])&0x400),'Actual identified completed-cleanup sample with strict boundary predicate/LastError/ABI DF')
 hw(b[8880:9424],b[9424:9968]);need(struct.unpack_from('<H',b,8880)[0]==0xa7f and struct.unpack_from('<I',b,8880+24)[0]==0x5fa5 and b[8884],'Nontrivial independently seeded actual caller hardware')
 need(b[8880+256:8880+416]==bytes((n*73+19)&255 for n in range(256,416)),'Exact authored nonvolatile SIMD sentinel was loaded')
 if retry:need(q[3]==0 and b[256:512]==b[512:768]and b[768:4272]==b[4272:7776]and b[7776:8288]==b[8288:8800]and b[8800:8840]==b[8840:8880],'Refused retry conserves every State/CPU/FX/owner-summary byte')
 return q
def identity(a,stem,pin,parser,custom=False):
 q=a.words(stem+'.bin',11,'Q');target,named,owner,owner_named,base,size,allocation,state,kind,protect,_=q
 need(target==named==owner_named and owner==allocation and base<=target<base+size and state==0x1000 and kind==0x1000000 and protect&0xf0 and not protect&0x101,'Measured full AMD64 executable API identity')
 path=a.data(stem+('-path.bin'if custom else'-module-path.bin')).decode('utf-16-le').split('\0',1)[0]
 digest=a.data(stem+('-sha.bin'if custom else'-module-sha.bin')).decode('ascii');pin(path,digest)
 need(owner+parser.named_export(path,'HeapDestroy')==target,'Physical direct named HeapDestroy matches measured executable owner')
 return q
def expected_cause(case,f,o):
 deliberate='Deliberate precise normal-FS/shared-owner boundary observer failure';store='Checked actual source locale/parser store fault';private='FS observer changed private source-frame/chain witnesses'
 cases={1:(0x4e78d7,0x780039bf,80,'Heap creation observer changed State/FX or ownership/lifecycle ledgers'),
  2:(0x4e78d7,0xfffffffb,80,'Normal FS chain retains the owned game predecessor or native sentinel'),
  3:(0x4e78de,0x20001000,81,'Only committed source/API/research effects may change owned locale pages'),
  4:(0x4e799f,f[9],83,'Installed source FS predecessor/handler and active private frame identity'),
  5:(0x4e78de,0x7ffde000,81,store),6:(0x4e799f,0x7ffde000,83,store),
  7:(0x4e7977,o[4],73,store),8:(0x4e797d,0,73,store),9:(0x4e7994,o[4],73,store),
  10:(0x4e796e,o[10],87,'Checked complete current guest/native allocation backing and private generation required'),
  11:(0x4e799f,0,84,deliberate),12:(0x4e78d7,0,80,deliberate),13:(0x4e78de,0,81,deliberate),
  14:(0x4e78de,0,82,deliberate),15:(0x4e799f,0,83,deliberate),16:(0x4e799f,0,84,deliberate),
  17:(f[6],0,85,deliberate),18:(0x4e7922,0,86,deliberate),19:(0x4e7922,0,87,deliberate),
  20:(0x4d4948,0x7ffde000,83,store),21:(0x4e7922,0x4e7922,86,private),22:(0x4e7922,0x4e7922,87,private),23:(0x4e78de,0x4e78de,81,private)}
 return cases[case]
def main(name):
 out=R/'reports/m4-fs-control-audit'/name;need(not out.exists(),'Fresh immutable audit');out.mkdir();pins={};cases=[];counts=collections.Counter();physical={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();key=str(p);v=pins.get(key)
  if v is None:v=sha(p)
  need(h is None or h==v,'Physical input identity '+key);pins[key]=v;return p
 try:
  pin(__file__);pin(sys.executable)
  build=json.loads(pin(R/'reports/m4-fs-controls/build-r5/build.json','81016bf834e2eab21490ecc64d34be9a1ee5f9be622519614c881268b51e7180').read_bytes());run=json.loads(pin(R/'reports/m4-fs-controls/execution-r2/report.json','ba68d95c8f8ed3027c5e6ce623123aed55b76d67b0dcf47fa9a97fae7c503503').read_bytes());need(build['passed']and run['passed'],'Frozen current successful build and execution')
  for p,h in json.loads(pin(R/'reports/m4-fs-controls/build-r5/pins.json').read_bytes())['files'].items():pin(p,h)
  native=json.loads(pin(R/'reports/m4-fs-native/preparation-r3/report.json').read_bytes());need(native['passed'],'Frozen source derivative preparation')
  fixture=pin(R/'reports/m4-fs-controls/build-r5/fixture.cpp').read_text();hook=pin(R/'reports/m4-fs-controls/build-r5/hooks.hpp').read_text();old=pin(R/'reports/m4-fs-controls/build-r3/fixture.cpp').read_text();asm=pin(R/'reports/m4-fs-controls/build-r5/capture.s').read_text()
  wrapper=fixture[fixture.index('[[clang::noinline]] unsigned invoke('):fixture.index('void dump(Context&')]
  need(wrapper.index('ErrorBoundary errors')<wrapper.index('NumericHostBoundary boundary')<wrapper.index('try{')<wrapper.index('catch(...)')<wrapper.index('return t.okay'),'Wrapper lifetimes lexically enclose all candidate calls and C++ catch')
  need('if(t.retry)t.c->registry().replay(fs_roots[0])'in wrapper and 't.c->registry().bootstrap();for(auto root:fs_roots)'in wrapper,'Both ordinary source and refused retry use same named numerical/error boundary')
  need('const bool boundary_equal=hardware_equal(before,after);restore.restore()'in fixture and 'unsigned(boundary_equal)'in fixture,'Immediate actual result is measured before diagnostic restoration and retained')
  need('Context c(std::as_bytes(std::span{game})'in fixture and fixture.index('auto game=old::read(')<fixture.index('Context c('),'Owned immutable complete provider inputs outlive every Context')
  need('fxrstor64 (%r9)'in asm and 'fldenv 512(%r9)'in asm and asm.index('fxsave64 (%rsi)')<asm.index('callq data_boundary_initialize')<asm.index('fxsave64 (%rdi)'),'Assembly loads actual rich input and takes raw current samples immediately around callback')
  need('throw'not in asm and 'std'not in asm.lower(),'Assembly is ABI caller with DF-clear input, not an invalid C++ DF1 test')
  reader=load('fs_audit_archive',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));parser=load('fs_audit_pe',pin(R/'tools/m4-strings-control-audit/audit_v9.py'));J=load('fs_guest_projection',pin(R/'tools/m4-joint-startup27-review/observe.py'));model,_,_,_=J.models();pins.update(J.PINS)
  specs=json.loads(pin(R/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes());specs={(q['root'],q['CALL_pc']):q for q in specs};contracts=json.loads(pin(R/'reports/m4-fs-source/recovery-r3/instruction-contracts.json').read_bytes());inst={q['pc']:q for q in contracts['instructions']}
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';pin(llvm/'llvm-nm.exe');pin(llvm/'llvm-objdump.exe')
  for row in run['levels']:
   level=row['level'];worker=build['workers'][level];pin(worker['path'],worker['sha256']);need(parser.machine(worker['path'])==0x8664,'Actual control worker is AMD64 PE');tree=Path(worker['path']).parent
   ninja=pin(tree/'build.ninja').read_text();link=next(x for x in ninja.splitlines()if x.startswith('build mw34_joint_startup109.exe:')).replace(chr(92),'/')
   declared=worker['objects'];objects=[p for p in declared if p.endswith('.obj')];proof=[p for p in declared if not p.endswith('.obj')]
   need(all(Path(p).as_posix().replace(':','$:')in link for p in objects),'Every declared literal COFF reaches final actual executable link')
   need(all(parser.machine(pin(p))==0x8664 for p in objects),'All actually linked source COFFs are physically AMD64')
   need('CMakeFiles/mw34_joint_startup109.dir/fixture.cpp.obj'in link and 'capture.obj'in link,'Compiled authored fixture and independent assembly sampler both reach actual final link')
   obj=pin(tree/'CMakeFiles/mw34_joint_startup109.dir/fixture.cpp.obj');nm=subprocess.run([str(llvm/'llvm-nm.exe'),str(obj)],capture_output=True,check=True,creationflags=0x08000000).stdout.decode();syms=[x.split()[-1]for x in nm.splitlines()if ' t ?invoke@'in x];need(len(syms)==1,'Distinct noinline actual compiled wrapper')
   dis=subprocess.run([str(llvm/'llvm-objdump.exe'),'-dr','--disassemble-symbols='+syms[0],str(obj)],capture_output=True,check=True,creationflags=0x08000000).stdout.decode();dest=out/(level+'-wrapper-bytecode.txt');dest.write_text(dis);pin(dest)
   need('Session' in dis and 'replay' in dis and ('NumericHostBoundary'in dis or('fxsave'in dis and'fxrstor'in dis)),'Actual compiled wrapper retains candidate CALL and caller numerical lifetime')
   stage=json.loads(pin(row['stage'],row['stage_sha256']).read_bytes());verify_stage(Path(row['stage']).parent,row['stage_sha256']);need(stage['argv'][0]==worker['path']and stage['input_sha256'][worker['path']]==worker['sha256']and stage['artifact_sha256'][row['capture']]==row['capture_sha256'],'Actual executed worker and returned artifact are physically bound')
   physical[level]=dict(declared_dependencies=len(declared),linked_literal_objects=len(objects),retained_prior_proof_archives=proof,worker_sha256=worker['sha256'],wrapper_symbol=syms[0])
   a=reader.DirectSet(pin(row['capture'],row['capture_sha256']),pin)
   try:
    need(a.words('header.bin',6)==(1,24,48,9968,6,10),'Exact native authored control header');need(a.data('COMPLETE.txt')==b'Bounded six-root normal-FS research controls passed; canonical109 is separate\n','Genuine complete finite executed workload')
    for case in range(24):
     stem=f'case-{case}/';live=stem+'first-live/';clean=stem+'first-cleaned/';trig=stem+'first-trigger/'
     first=sample(a.data(stem+'first.bin'),case,0);retry=sample(a.data(stem+'retry.bin'),case,1);counts['outside_hardware_pairs']+=2
     for attempt in('first','retry'):hw(a.data(stem+attempt+'-cleanup-hardware-before.bin'),a.data(stem+attempt+'-cleanup-hardware-after.bin'));counts['cleanup_hardware_pairs']+=1
     names={n[len(clean):]for n in a.entries if n.startswith(clean)};retry_names={n[len(stem+'retry-live/'):]for n in a.entries if n.startswith(stem+'retry-live/')};need(names==retry_names,'Exact complete retained logical same-Session retry domain')
     for n in names:need(a.data(clean+n)==a.data(stem+'retry-live/'+n),'Same finished/poisoned Session retry changes no raw captured source/API/owner/TIB/page/identity byte: '+n)
     counts['retry_equal_records']+=len(names);counts['full_machine_retries']+=1
     allocations=rows(a.data(live+'locale-allocations.bin'),16);released=rows(a.data(clean+'locale-allocations.bin'),16);mfc=rows(a.data(live+'mfc-allocation-witnesses.bin'),32);final=rows(a.data(clean+'mfc-allocation-witnesses.bin'),32);source=rows(a.data(live+'locale-source-accesses.bin'),24//4,'x')if False else list(struct.iter_unpack('<IIQII',a.data(live+'locale-source-accesses.bin')))
     need(len(allocations)==len(released)and all(p[:8]==q[:8]and q[8:10]==(0,0)and q[10]+q[11]==1 for p,q in zip(allocations,released)),'Every actual acquired owner retains provenance and is released/unmapped exactly once')
     need(all(q[30]+q[31]==1 for q in final),'Every MFC owner joins one actual source or explicit safeguard free')
     loc=a.words(clean+'locale-summary.bin',32);summary=a.words(clean+'registry-summary.bin',32,'Q');need(loc[23]==1 and loc[14]==loc[15]==loc[30]==0 and summary[4]==1 and summary[10]==summary[11]==summary[15]==0,'No owned allocation/CS/HANDLE remains after genuine cleanup')
     sections=rows(a.data(clean+'locale-critical-sections.bin'),16);need(all(q[5]==0 and q[6:10]==(1,1,1,1)for q in sections),'Actual initialized private critical sections leave and delete exactly once')
     heap=a.words(clean+'heap-create-registry.bin',18,'Q');need(heap[4]>0xffffffff and heap[7]==0 and heap[8:11]==(1,1,1)and heap[15]==1 and heap[16]==heap[4],'Actual same full-width acquired HANDLE destroyed successfully once')
     idb=identity(a,clean+'heap-destroy-api-before',pin,parser);ida=identity(a,clean+'heap-destroy-api-after',pin,parser);idi=identity(a,stem+'first-cleanup-api-after',pin,parser,True);need(idb==ida==idi,'Actual before/after/immediate-independent physical HeapDestroy triplet');counts['HeapDestroy_identity_triplets']+=1
     api_count=loc[18];apis=[a.words(clean+f'locale-api-{i}-witness.bin',32,'Q')for i in range(api_count)]
     for q in mfc:
      need(q[0]==1 and mfc[q[1]]==q and (q[2],q[4])in specs,'Reached MFC record is exact source-derived root/CALL');s=specs[q[2],q[4]]
      need(q[7]==s['requested_size']and q[6]==q[4]+inst[q[4]]['width']and(q[4],q[5],q[6],4,1)in source,'Literal raw requested size and genuine CALL return frame')
      need(q[8:16]==(0x78001498,0x780012b3,0x5f401ea1,0x5f401eb5,q[5]-24,q[7],0x5f401ead,0xffffffff)and q[21]==1,'True MFC import/handler and cdecl source malloc frame/RET')
      al=next(p for p in allocations if p[5]==q[18]);need(al[6]==4 and(al[1],al[2],al[3],al[7],al[8])==(q[16],q[7],q[19],q[17],q[17])and q[17]>0xffffffff,'Genuine full native owner/private whole guest alias generation')
      initial=a.data(live+f'locale-allocation-{q[18]}-initial.bin');expected=a.data(live+f'locale-allocation-{q[18]}-expected.bin');need(len(initial)==al[3]and len(expected)==al[4],'Complete actual BEFORE extent and mapped mirror')
      reconstructed=bytearray(initial+bytes(al[4]-len(initial)));stores=[]
      for pc,address,value,width,writing in source:
       if writing and al[1]<=address<al[1]+al[4]:
        need(0<width<=8 and address+width<=al[1]+al[2],'Literal object source store remains inside requested bytes');offset=address-al[1];reconstructed[offset:offset+width]=value.to_bytes(8,'little')[:width];stores.append((pc,address,value,width))
      need(bytes(reconstructed)==expected==a.data(live+f'locale-allocation-{q[18]}-owned-page.bin'),'Entire actual guest allocation/padding matches BEFORE plus only committed literal source stores')
      allocapis=[p for p in apis if p[3]==0x7802e088 and p[8]==q[17]];need(len(allocapis)==1 and allocapis[0][14]and allocapis[0][12:14]==(q[16],q[19]),'Real typed positive HeapAlloc result generated this private owner')
      k=allocapis[0][1];need(a.data(clean+f'locale-api-{k}-output-0.bin')==initial,'Actual full allocated BEFORE output is the replay input')
      counts['complete_owned_store_replays']+=1
     # Full software State projection of guest ENV, distinct from measured host ENV.
     for label in('first-causal','retry-causal'):
      state=a.data(stem+label+'-State.bin');fx=a.data(stem+label+'-FX.bin');cpu=a.data(stem+label+'-CPU.bin');env=a.data(stem+label+'-guest-ENV.bin');need(len(state)==3504 and len(fx)==512 and len(cpu)==40 and model.proj(state)[1]==env,'Captured guest legacy ENV is exact full-State serialization');counts['guest_ENV_projections']+=1
     detail=dict(level=level,case=case,completed=first[4],mfc_owners=len(mfc),retry_records=len(names))
     f=a.words(trig+'frame.bin',32,'Q');o=a.words(trig+'owner.bin',16,'Q');chain=a.words(trig+'chain.bin',16,'Q');frames=rows(a.data(live+'fs-frame-witnesses.bin'),32);active=rows(a.data(live+'fs-active-records.bin'),1,'I');tib=a.words(live+'fs-current-tib.bin',5);state=a.data(stem+'first-causal-State.bin');stack=a.data(stem+'first-causal-stack.bin');fault=a.words(live+'locale-fault.bin',4)
     for q in frames:
      need(q[0]==1 and frames[q[1]]==q and q[9]==q[5]-12 and q[24:26]==(0x7ffde000,0xffffffff),'Original complete12-byte guest frame and owned-native provenance')
      need((q[3],q[10],q[7],q[14],q[18],q[20])in[(0x4e78d0,0x5b986b,0x4e78d7,0x4e78de,0x4e799f,0x4e79aa),(0x48f290,0x5b5233,0x48f297,0x48f29e,0x48f360,0x48f36b),(0x4d48f0,0x5b8538,0x4d48f7,0x4d48fe,0x4d4948,0x4d4953)],'Three literal frame/handler/install/restore/RET geometries only')
     need(tib[0]==tib[4]==0x7ffde000 and tib[2:4]==(0x20002000,0x20001000),'Exact bounded owned native TIB identity')
     if case==0:
      need(first[3:6]==(1,6,0)and len(frames)==7 and len(mfc)==10 and all(q[15]==q[19]==q[21]==1 for q in frames)and not active and tib[1]==0xffffffff,'Actual six-root normal source execution fully restores seven frames')
      graphs=rows(a.data(live+'fs-shared-graph-witnesses.bin'),16);need([q[7]for q in graphs]==[1,2,3,4,5],'True persistent circular shared list grows exactly five times')
      need(all(q[30]==1 and q[31]==0 and q[25]==0x5f401782 and q[27]==q[26]-8 and q[28:30]==(0x7800138a,0x78001390)for q in final),'All10 MFC objects genuinely freed by literal MFC825/CRTfree normal paths')
     else:
      exp=expected_cause(case,f,o)
      if case==8:exp=(exp[0],a.words(trig+'mfc.bin',32,'Q')[16],exp[2],exp[3])
      need(first[3]==0 and first[5]==1 and first[14]==1 and fault==(1,*exp[:3])and a.data(live+'locale-fault-reason.bin').decode()==exp[3],'Exact intended reached causal PC/address/stage/reason')
      need(first[4]==(2 if case==8 else 5 if case in(11,20)else 0),'Genuine completed source prefix is exact');counts['intended_refusals']+=1;detail.update(pc=fault[1],address=fault[2],stage=fault[3],reason=exp[3])
      point={1:80,2:80,3:81,4:83,5:81,6:83,7:86,8:87,9:86,10:87,11:84,20:83,21:86,22:87,23:81}.get(case,80+case-12)
      if point<=85:need(chain[4]==point and chain[3]==f[1],'Actual exact frame-based trigger point/index')
      else:need(o[0]==1 and o[3]in inst and o[7]==1,'Actual original source-owned write trigger')
      if case in(3,4,5,6,13,14,15,16,20,23):
       raw=a.words(trig+'record.bin',3);need(raw[:2]==(f[8],f[10]),'True complete record saved predecessor/handler before intervention')
       at=f[9]-0x20001000;need(0<=at<=4096-12,'Bounded actual12-byte source frame')
       if case==3:need(struct.unpack_from('<3I',stack,at)[1]==(f[10]^4),'Actual handler corruption retained at owned stack-page guard')
       elif case==4:need(struct.unpack_from('<3I',stack,at)[0]==(f[8]^4),'Actual predecessor corruption retained at active chain guard')
       else:need(struct.unpack_from('<2I',stack,at)==(f[8],f[10]),'No invented source frame repair after refusal')
      if case in(5,13,23):need(f[15]==0 and tib[1]==f[8] and not any(p[0]==0x4e78de and p[4]for p in source),'Pre-install refusal commits no actual FS0 store')
      if case==14:need(f[15]==1 and f[19]==0 and tib[1]==f[9] and source[-1]==(0x4e78de,0x7ffde000,f[9],4,1),'Post-install throw retains genuine FS0/active-frame commit')
      if case in(6,15,20):need(f[15]==1 and f[19]==0 and tib[1]==f[9] and not any(p[0]==f[18]and p[4]for p in source),'Refused restore preserves installed source chain without fabricated unwind')
      if case in(16,17):need(f[19]==1 and tib[1]==f[8]and(f[18],0x7ffde000,f[8],4,1)in source,'Post-restore/RET trigger retains exact committed predecessor')
      if case==11:
       parent=frames[f[13]-1];need(f[13]>0 and f[19]==1 and not f[21]and parent[3]==0x4d48f0 and parent[15]==1 and parent[19]==0 and tib[1]==f[8]==parent[9]and [q[0]for q in active]==[parent[1]],'Nested inner restore genuinely leaves its same owned outer frame active')
      if point>=86:
       q=a.words(trig+'mfc.bin',32,'Q');need(q[17]>0xffffffff and q[19]and q[18],'Whole native owner was observed at actual source boundary');native_before=a.data(trig+'native-before.bin');need(len(native_before)==q[19],'Entire actual native extent retained before intervention');mirror=a.data(live+f'locale-allocation-{q[18]}-expected.bin');need(native_before==mirror[:q[19]],'Actual full native extent equals independently replayed committed source bytes')
       if case==10:
        after=a.data(trig+'native-after.bin');changed=bytearray(native_before);changed[-1]^=0x55;need(after==changed,'Actual complete backing shows exact declared private-native byte mutation')
       if case==7:need(not any(pc==0x4e7977 and writing for pc,_,_,_,writing in source),'RO first link refuses before source publication')
       if case==8:need(source[-2]==(0x4e7977,o[4],o[6],4,1) and source[-1][0]==0x4e797a and not source[-1][4]and not any(pc==0x4e797d and address==q[16] and writing for pc,address,_,_,writing in source),'Precise second-link failure retains earlier committed sentinel link and leaves old-head link unchanged')
       if case==9:need(not any(pc==0x4e7994 and writing for pc,_,_,_,writing in source),'RO count failure retains zero count after prior links')
       if case in(18,21):need(not any(pc==0x4e7922 and writing for pc,_,_,_,writing in source),'Pre-owned-write failure commits no source byte')
       if case in(19,22):need(source[-1]==(0x4e7922,o[4],o[6],1,1),'Post-owned-write failure retains exactly genuine one-byte commit')
      if case>=21:
       if case==21:need(a.words(live+'fs-owned-access-probe.bin',16,'Q')[6]==(o[6]^1),'Actual private owner-probe mutation retained')
       elif case==22:need(rows(a.data(live+'fs-owned-accesses.bin'),16)[-1][6]==(o[6]^1),'Actual private committed witness mutation retained; raw source ledger remains primary')
       else:need(a.words(live+'fs-native-input.bin',16,'Q')[8]==1,'Actual private provenance reserved-field mutation retained')
     counts['actual_scenarios']+=1;cases.append(detail)
     print(json.dumps(dict(level=level,case=case,passed=True,retry_equal_records=len(names))),flush=True)
   finally:a.close()
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  artifacts={str(p):sha(p)for p in out.rglob('*')if p.is_file()};pins.update(artifacts)
  report=dict(passed=passed,counts=dict(counts),cases=cases,physical_link=physical,scope='Actual isolated6 checked research roots and24 scenarios atO0/O2, each with same finished/poisoned Session retry. Source/native bytes and captures unchanged. Explicit caller NumericHostBoundary/ErrorBoundary surrounds the invocation AND C++ catch, matching connected Context. Full measured legacy ENV/raw80/CW/SW/FTW/MXCSR/nonvolatile XMM equality and ABI DF-clear/LastError apply only to that wrapped call and cleanup. Naked throwing Session API metadata preservation is excluded; its failed execution-r1 is retained. Fault-after-install may retain pending guest chain; no invented virtual unwind or handler/TLS behavior. Full109 source/paired/provider gates are separate; no initializer credit from this audit.',initializer_credit=0,native_executed_by_auditor=False,API_response_injection=False,files=pins,current_physical_closure=verify_manifest(pins))
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))),flush=True)
if __name__=='__main__':main(*sys.argv[1:])
