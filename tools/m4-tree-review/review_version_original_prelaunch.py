"""Physical one-root x86 VERSION observer admission; never run/read a capture."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH='7718e1cadfb8619b504ee5246ea9ade5d2e60b4ea89e11537db29ec04cf70529'
BH='fd5caff7e35d7ab8e6a10e9d00f41c4ca7ddfcee7ee9261692f54e1fad68a292'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir();pins={};counts=Counter();links=[];passed=False;worker_sha=None
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip','.iso');v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 def module(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def sparse(p,h):
  raw=pin(p,h).read_bytes();n=struct.unpack_from('<I',raw,8)[0];assert raw[:8]==b'MW4J124P'and len(raw)==12+4104*n
  rows={struct.unpack_from('<I',raw,12+4104*i)[0]:(struct.unpack_from('<I',raw,16+4104*i)[0],raw[20+4104*i:4116+4104*i])for i in range(n)};assert len(rows)==n;return rows
 try:
  folder=R/'reports/m4-version-source/original-preparation-r4';bf=R/'reports/m4-version-source/original-build-r4'
  prep=read(folder/'report.json',PH);build=read(bf/'build.json',BH);assert prep['passed']and build['passed']and build['preparation_sha256']==PH
  for d in(prep,build):
   for p,h in d['files'].items():pin(p,h)
  assert(prep['original_sequences'],prep['original_roots'],prep['original_phases'],prep['sparse_pack_pages'],prep['record_bytes'])==(1,1,1,121,356992)
  assert not prep['original_executed']and not prep['archive_reader_opened']and prep['initializer_credit']==0
  assert prep['required_process_cwd']==str((R/'MW3').resolve())and prep['explicit_writer_reports_root']==str((R/'reports').resolve())
  oldfolder=R/'reports/m4-cosine-original/prefix-preparation-r2';old=read(oldfolder/'report.json',prep['parent_preparation_sha256'])
  for row in prep['source_relations']:assert pin(row['parent'],row['sha256']).read_bytes()==pin(row['child'],row['sha256']).read_bytes();counts['whole_retained_original_inputs']+=1
  P=module(R/'tools/analysis/pe.py','version32_pe');C=module(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','version32_coff')
  game=P.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  cp=P.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
  def physical(image,pc,n):start,_=image.rva_range(pc-image.image_base,n);return image.data[start:start+n]
  pack=sparse(folder/'pages.bin',prep['pack_sha256']);oldpack=sparse(oldfolder/'pages.bin',old['pack_sha256']);assert len(pack)==121 and len(oldpack)==119
  native=read(R/'reports/m4-version-source/preparation-r2/report.json','137c214307a28b0e120b600ee53f14fcfacac0a72a7ef64b437178f3b3b17c75')
  source=read(R/'reports/m4-version-source/preparation-r2/source-rows.json');assert len(source)==132
  expected={row['pc']+i:b for row in source for i,b in enumerate(bytes.fromhex(row['bytes']))}
  for pc,value in expected.items():assert pack[pc&~4095][1][pc&4095]==value
  for pc,(rights,data)in pack.items():
   assert pc%4096==0 and rights in(0,1,2)and len(data)==4096
   if pc in oldpack:
    assert rights==oldpack[pc][0]
    for n,(before,after)in enumerate(zip(oldpack[pc][1],data)):
     if before!=after:assert rights==1 and before==0xcc and expected.get(pc+n)==after;counts['exact_new_source_overlay_bytes']+=1
   else:
    assert pc in(0x4af000,0x4ea000)and rights==1
    for n,value in enumerate(data):assert value==expected.get(pc+n,0xcc)
   counts['whole_sparse_pack_pages']+=1
  for row in prep['source_spans']:
   image=cp if row['origin']else game;data=physical(image,row['pc'],row['size']);assert image.data[row['image_offset']:row['image_offset']+row['size']]==data
   if not row['origin']:
    for n,value in enumerate(data):assert pack[(row['pc']+n)&~4095][1][(row['pc']+n)&4095]==value
   counts['whole_physical_source_spans']+=1
  assert struct.unpack('<I',physical(game,0x5e0140,4))[0]==0x4af240 and physical(game,0x5e867c,10)==b'mech3.exe\0'and physical(game,0x5e8664,2)==b'\\\0'
  seams=[(0x4af113,bytes.fromhex('85c08907747e'),0x4af197,0x4af119),(0x4af131,bytes.fromhex('85c0750f8bcf'),0x4af144,0x4af137),(0x4af16c,bytes.fromhex('85c074278b4c2414'),0x4af197,0x4af174)]
  for pc,raw,target,fall in seams:assert physical(game,pc,len(raw))==raw;counts['whole_conditional_return_spans']+=1
  asm=text(folder/'version_observer_x86.asm')
  regs=('eax','ecx','edx','ebx','esp','ebp','esi','edi')
  for i,label in enumerate(('size','info','query')):
   prefix='version_'+label;argc=2 if i==0 else 4;ret=seams[i][0]
   for side in('entry','return'):
    block=asm[asm.index(prefix+'_'+side+' PROC'):asm.index(prefix+'_'+side+' ENDP')]
    for j,reg in enumerate(regs):assert ' mov DWORD PTR version_cpu[%d],%s'%(4*j,reg)in block
    for j,reg in enumerate(regs):
     if reg!='esp':assert ' mov %s,DWORD PTR version_cpu[%d]'%(reg,4*j)in block
    for token in ('mov esp,mixed_host_esp','pushfd','pop DWORD PTR version_cpu[32]','fxsave version_fx','fnstenv version_env','fldenv version_env','call version_observe','fxrstor version_fx','push DWORD PTR version_cpu[32]','popfd','mov esp,DWORD PTR version_cpu[16]'):assert token in block,token
    if side=='entry':
     actual=' call DWORD PTR version_targets[%d]'%(i*4);assert block.count(actual)==1
     for arg in range(argc,0,-1):assert ' push DWORD PTR [eax+%d]'%(4*arg)in block
     for token in ('mov eax,DWORD PTR fs:[34h]','mov DWORD PTR fs:[34h],eax','mov version_API_before_error,eax','mov version_API_after_error,eax','fxsave version_hardware[48]','fnstenv version_hardware[560]','fldenv version_hardware[560]','fxsave version_hardware[640]','fnstenv version_hardware[1152]','fldenv version_hardware[1152]','lea eax,[eax+%d]'%(4*(argc+1)),'jmp DWORD PTR version_return_PCs[%d]'%(4*i)):assert token in block,token
     assert block.index('mov DWORD PTR fs:[34h],eax')<block.index(actual)<block.index('mov version_API_after_error,eax')<block.rindex('call version_observe')
    counts['complete_source_and_API_wrapper_bodies']+=1
  assert 'test eax,eax\n mov DWORD PTR [edi],eax\n jnz version_size_fallthrough\n jmp DWORD PTR version_branch_targets[0]'in asm
  assert 'test eax,eax\n jz version_info_fallthrough\n jmp DWORD PTR version_branch_targets[4]'in asm and 'version_info_fallthrough:\n mov ecx,edi\n jmp DWORD PTR version_return_continues[4]'in asm
  assert 'test eax,eax\n jz version_query_failure\n mov ecx,DWORD PTR [esp+14h]\n jmp DWORD PTR version_return_continues[8]'in asm and 'version_query_failure:\n jmp DWORD PTR version_branch_targets[8]'in asm
  observer=text(folder/'version_observer.hpp');assert observer==text(R/'tools/m4-version-source/original_observer_v3.hpp')
  for token in ('sizeof(Version32HardwareSide)==592&&sizeof(Version32Hardware)==1184','ha.cpu.esp==hb.cpu.esp+4*(version_argc[API]+1)','ha.cpu.ebx==hb.cpu.ebx','ha.cpu.ebp==hb.cpu.ebp','ha.cpu.esi==hb.cpu.esi','ha.cpu.edi==hb.cpu.edi','version_cpu.flags==ha.cpu.flags','!std::memcmp(version_fx,ha.fx,512)','!std::memcmp(version_env,ha.env,28)','error==version_API_after_error','version_incoming_error==version_API_before_error','capacity==(*allocation_owner)[5]','output-pointer<version_dword(0x60b198)','length<=version_dword(0x60b198)-(output-pointer)','version_same(entry.identity,v.identity)&&version_same(entry.file,v.file)','v.sha==image_sha','GetProcAddress(version_module,version_names[index])','region.Type==MEM_IMAGE','std::memcpy(v.entry.data(),reinterpret_cast<void*>(target),64)'):assert token in observer,token
  cpp=text(folder/'reference.cpp')
  for token in ('out(argv[4],"'+str((R/'reports').resolve()).replace('\\','/')+'")','LoadLibraryExW(L"version.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32)','version_count=version_error=version_allocation_count=0','Whole actual original VERSION return seam raw bytes','Whole original VERSION return bytes restored','version_emit(out,','require(!version_error','Actual original source onexit4AF270 publication','manual-version-MFC825.bin','Entire declared VERSION observer patch bytes'):assert token in cpp,token
  protocol=text(folder/'protocol.hpp');assert protocol==text(oldfolder/'protocol.hpp').replace('sequences=6, roots=1','sequences=1, roots=1')
  spec=text(folder/'spec.hpp')
  for field,value in [('entries',0x4af240),('table_slots',0x5e0140)]:assert 'std::array<std::uint32_t,1> '+field+'{'+hex(value)+'}'in spec
  worker_sha=build['worker_sha256'];worker=P.PEImage(pin(build['worker'],worker_sha).read_bytes());assert(worker.machine,worker.image_base)==(0x14c,0x18000000)
  symbols_by_object={}
  for obj in build['objects']:
   q=pin(obj['path'],obj['sha256']);sy,se=C.coff(q.read_bytes());symbols_by_object[q.name]=(sy,se)
   if q.name in('reference.obj','capture_direct_v3.obj'):continue
   exe=[i for i,section in se.items()if section['flags']&0x20000000 and section['bytes']];assert len(exe)==1
   fake={0:dict(name=q.stem+' whole assembly section',value=0,section=exe[0],type=32,storage=2)}
   proof=C.linked_function(worker,fake,se,fake[0]['name']);links.append(proof);counts['whole_linked_assembly_sections']+=1;counts['whole_linked_assembly_bytes']+=proof['bytes']
  sy,se=symbols_by_object['reference.obj'];names=[v['name']for v in sy.values()if v['section']>0 and v['type']==32 and(v['name']in('_main','_observe_boundary','_observe_named_API','_registry_observe_allocation','_version_observe','_nullfree_observe')or v['name'].startswith('?version_'))]
  assert {'_main','_observe_boundary','_observe_named_API','_registry_observe_allocation','_version_observe','_nullfree_observe'}<=set(names)
  for n in names:links.append(C.linked_function(worker,sy,se,n));counts['whole_linked_version_CPP_functions']+=1
  targets={}
  for proof in links:
   for row in proof['relocations']:
    if 'actual_symbol_address'not in row:continue
    name=row['symbol'];value=row['actual_symbol_address'];assert name not in targets or targets[name]==value,(name,targets.get(name),value);targets[name]=value;counts['actual_linked_symbol_joins']+=1
  for proof in links:
   if proof['symbol']in targets:assert targets[proof['symbol']]==proof['address']
  for n,values in [('_version_return_PCs',(0x4af113,0x4af131,0x4af16c)),('_version_return_continues',(0x4af119,0x4af137,0x4af174)),('_version_branch_targets',(0x4af197,0x4af144,0x4af197))]:assert physical(worker,targets[n],12)==struct.pack('<3I',*values)
  for c in build['commands']:assert c['exit_code']==0;pin(c['argv'][0]);pin(c['stdout']);pin(c['stderr'])
  link=[c for c in build['commands']if Path(c['argv'][0]).name.lower()=='link.exe'];assert len(link)==1
  args=link[0]['argv'];assert '/MACHINE:X86'in args and all(any(str(Path(o['path']).resolve()).casefold()==a.casefold()for a in args)for o in build['objects'])
  for p in build['actual_compiler_headers']:pin(p);counts['actual_compiler_header_paths']+=1
  assert str((folder/'version_observer.hpp').resolve())in build['actual_compiler_headers']
  for p in build['actual_linker_libraries']:pin(p['path'],p['sha256']);counts['actual_linker_library_inputs']+=1
  controller=read(R/'reports/m4-version-source/original-controller-preparation-r1/report.json','d1b1faf63ff581b3141fe9ddc0032a8abd315e47440406d16ec96341d3571246')
  for p,h in controller['files'].items():pin(p,h)
  pin(R/'tools/m4-version-source/run_original_v1.py','90e05b415bf8925b8d9aa17ec9b55deb694c09b91e6bd6a261408dcf1b05369f');pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h,p
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'physical-links.json';q.write_text(json.dumps(links,indent=2)+'\n');pin(q)
  d=dict(passed=passed,prelaunch_justified=passed,preparation_sha256=PH,build_sha256=BH,worker_sha256=worker_sha,counts=dict(counts),files=pins,worker_launched=False,archive_reader_opened=False,initializer_credit=0,scope='One genuine version root with whole conditional source branch relocation, actual32 API hardware/LastError/owner/file observations; source equivalence and carried startup remain separate')
  q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),counts=dict(counts),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])
