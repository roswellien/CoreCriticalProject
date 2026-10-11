"""Independent connected142-row replay from current native BEFORE only.

The recorded AFTER is a comparison target. The three loaded CRT cells and
manager/TIB extents not separately observed by prep3 stay an explicit endpoint
scope gap; all113 reached operands are nevertheless independently derived.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def eq(a,b,s):need(a==b,s+' '+str((a,b))[:550])
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical input');PINS[str(p)]=v;return p
def raw(p,h=None):return pin(p,h).read_bytes()
def read(p,h=None):return json.loads(raw(p,h))
def load(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(b,n=1,o=0,kind='I'):return struct.unpack_from('<'+kind*n,b,o)
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000)
def main(execution,digest,name):
 out=R/'reports/m4-mfc1168-native'/name;need(not out.exists(),'Fresh current connected source comparison');out.mkdir();counts=collections.Counter();results=[];passed=False;closed=True
 try:
  e=read(execution,digest);need(e['passed']and e['all_workers_terminal']and e['all_bounded_readers_closed'],'Actual terminal current14 execution');b=read(e['build'],e['build_sha256']);p=read(b['preparation'],b['preparation_sha256']);inputs=p['inputs'];need(p['passed']and len(p['selected_order'])==14,'Current14 preparation')
  for q,h in b['files'].items():pin(q,h)
  contracts=read(R/'reports/m4-mfc1168-probe/native-contracts-r1/contracts.json','f7db9805f43e1eb7ef84ad8adb5ddb0f788b76844dbaadb736329787a410eb64');original=read(p['chronological_source'],p['chronological_source_sha256']);need(original['passed'],'Current chronological original literal proof');original_source=read(Path(p['chronological_source']).parent/'source-derivations.json');retained=read(Path(p['chronological_original']).parent/'retained-actual-inputs.json');need(not original_source['source_AFTER_seed'],'No original AFTER model seed')
  def genuine(key):
   need('/BEFORE/'in key,'Genuine BEFORE input only');r=retained[key];v=raw(r['path'],r['sha256']);eq(len(v),r['bytes'],'Whole genuine BEFORE extent');return v
  I=load(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py','connected_mfc_integer');F=load(R/'tools/m4-formatting-source/flag_domain.py','connected_mfc_flags');PE=load(R/'tools/analysis/pe.py','connected_mfc_source_PE');DS=load(R/'tools/m4-crt-allocation-root/run_v2.py','connected_mfc_direct')
  pin(R/'tools/m4-runtime/runtime.cpp');pin(R/'tools/m4-runtime/runtime.hpp')
  program={r['pc']:r for r in contracts['instructions']};eq(len(program),142,'Exact normal physical instruction union')
  images=[PE.PEImage(raw(R/q,h))for q,h in [('MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),('local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')]]
  def physical_page(address):
   im=next(x for x in images if x.image_base<=address< x.image_base+x.size_of_image);goal=bytearray(4096)
   for s in im.sections:
    lo=max(address,im.image_base+s['virtual_address']);hi=min(address+4096,im.image_base+s['virtual_address']+s['raw_size'])
    if lo<hi:o=s['raw_offset']+lo-im.image_base-s['virtual_address'];goal[lo-address:hi-address]=im.data[o:o+hi-lo]
   return goal
  class Literal(I.Machine):
   def cpu_now(self):
    flags=self.initial_flags
    for flag,bit in F.BITS.items():flags=(flags&~(1<<bit))|(int(bool(self.flag(flag)))<<bit)
    return tuple(self.reg(k)for k in('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,self.cursor)
   def read(self,address,size=4,domain='source',pc=None):
    source_pc=self.cursor if pc is None else pc;value=super().read(address,size,domain,pc)
    for v in inputs['imports']:
     if source_pc==v['pc']and address==v['cell']:
      eq((size,value),(4,v['raw']),'Exact source-owning raw IAT preimage');need(domain=='source','Owning projection is a source operand');self.projections.append(dict(access_index=len(self.accesses)-1,PC=source_pc,cell=address,raw=value,projected=v['projected']));self.accesses[-1]=(source_pc,address,v['projected'],size,0);return v['projected']
    return value
   def step(self):
    if self.cursor==0x780014b4:
     need(self.call_stack and self.call_stack[-1][0]==0x5f40107d and self.call_stack[-1][2]==0x5f4010b5,'Source-defined special imported EH return');self.call_stack.pop();outer=self.call_stack;self.call_stack=[]
     try:return super().step()
     finally:self.call_stack=outer
    return super().step()
  for level in('O0','O2'):
   row=next(x for x in e['levels']if x['level']==level);records=DS.DirectSet(Path(row['capture']),pin);closed=False
   try:
    stem='sequence-0/MFC/';phase=records.data('sequence-0/phase-13.bin');before_state=records.data(stem+'before/State.bin');before_cpu=records.data(stem+'before/CPU.bin');before_fx=records.data(stem+'before/FX.bin');entry=words(before_cpu,10);eq(entry[4],0x20001800,'Genuine current Context frame');eq(entry[9],0x5ae3e4,'Actual nonregistering root entered');eq(before_state,phase[141540:145044],'Whole current Runtime-entry State and component entry join');eq(before_cpu,phase[36:76],'Whole current Runtime-entry CPU and component entry join');eq(before_fx,phase[116:628],'Whole current Runtime guest FX and component entry join')
    pages=records.words('extra-pages.bin',len(records.data('extra-pages.bin'))//4);memory={a:physical_page(a)for a in {x['pc']&~4095 for x in program.values()}}
    for a in {v['cell']&~4095 for v in inputs['imports']}|{0x78037000}:memory[a]=physical_page(a)
    memory[0x5f4cb000]=bytearray(genuine('MFC1168/BEFORE/MFC/'+str(0x5f4cb000)+'.bin'))
    memory[0x7ffde000]=bytearray(struct.pack('<I',0xffffffff));memory[0x7ffdee1c]=bytearray(struct.pack('<I',inputs['role_owners'][1]['new']))
    # Every ordinary carried page comes from this native invocation BEFORE.
    for a in pages:memory[a]=bytearray(records.data(f'sequence-0/phase-13-before-page-{a}.bin'))
    for k,o in enumerate(inputs['role_owners']):
     source=bytearray(genuine('MFC1168/BEFORE/domain/'+o['role']+'/bytes.bin'))
     for cell in inputs['pointer_cells']:
      if o['new']<=cell['address'] and cell['address']+4<=o['new']+o['extent']:eq(words(source,o=cell['address']-o['new'])[0],cell['before'],'Authentic typed cell preimage');struct.pack_into('<I',source,cell['address']-o['new'],cell['projected'])
     actual=records.data(stem+f'before/borrowed/{k}.bin');eq(bytes(source),actual,'Whole genuine five-role chronological BEFORE plus declared typed rewrites');memory[o['new']]=bytearray(actual);counts['complete_genuine_relocated_role_BEFORE']+=1
    cs=inputs['guest_CS'];cs_before=records.data(stem+'before/guestCS24.bin');eq(cs_before,genuine('MFC1168/BEFORE/CRT-codepage-lock/bytes.bin'),'Entire genuine initialized guest CS24, separate from owned native40');memory[cs]=bytearray(cs_before)
    for cell in inputs['pointer_cells']:
     if cell['address']>=0x5f4cb000 and cell['address']<0x5f4cc000:offset=cell['address']-0x5f4cb000;eq(words(memory[0x5f4cb000],o=offset)[0],cell['before'],'Genuine manager cell preimage');struct.pack_into('<I',memory[0x5f4cb000],offset,cell['projected'])
    for cell in inputs['CRT_cells']:offset=cell['address']-0x78037000;eq(words(memory[0x78037000],o=offset)[0],cell['before'],'Current physical source CRT preimage');struct.pack_into('<I',memory[0x78037000],offset,cell['projected'])
    initial_memory={a:bytes(v)for a,v in memory.items()};m=Literal(before_state,before_fx,before_cpu,memory,program=program,callbacks={});m.initial_flags=entry[8];m.call_stack.append((0x5ae3e4,entry[4],0x410a80,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0));api_raw=records.data(stem+'after/APIs.bin');eq(len(api_raw),4*352,'Exactly four complete actual typed API records');api_rows=[];api_index=0;domain={};flags=[]
    for k in range(4):x=api_raw[k*352:(k+1)*352];api_rows.append(dict(words=words(x,16,kind='Q'),before=words(x,10,128),after=words(x,10,168),frame64=x[208:272],CS_before=x[272:312],CS_after=x[312:352]))
    while m.cursor!=0x410a80:
     need(m.cursor in program,'Unknown/lazy code frontier denied');r=program[m.cursor];eq(m.bytes(r['pc'],r['width']),bytes.fromhex(r['bytes_hex']),'Entire physical admitted source span');domain=F.advance(m,r,domain);m.step();flags.append(dict(PC=r['pc'],undefined_flags=dict(domain)))
     if m.cursor not in program and m.cursor!=0x410a80:
      need(api_index<4,'Finite named API frontier');a=api_rows[api_index];w=a['words'];spec=contracts['normal_APIs'][api_index];projection=inputs['imports'][api_index+3];result=inputs['role_owners'][1]['new']if api_index==0 else 1252 if api_index==2 else 0;eq(w[:8],(1,api_index,spec['source_PC'],projection['projected'],spec['argc'],m.reg('esp'),spec['return_PC'],result),'Actual exact source CALL/API identity');eq(m.cpu_now(),a['before'],'Whole source-derived guest API entry CPU40');eq(m.bytes(m.reg('esp'),64),a['frame64'],'Whole actual source cdecl/stdcall frame64');eq(w[12],inputs['role_owners'][1]['new'],'Exact declared guest-thread role association')
      if api_index==0:eq(w[8],w[11],'Actual native TLS association lookup equals whole current native mirror');eq(w[13],0,'TLS query under unheld host CS')
      if api_index==2:eq(w[8],1252,'Actual native ACP1252')
      pre=words(a['CS_before'],1,12)[0];post=words(a['CS_after'],1,12)[0];eq((pre,post),((0,0),(0,1),(1,1),(1,0))[api_index],'Whole native CS40 explicit depth relation');eq(words(a['CS_after'],1,16,'Q')[0],w[9]if post else 0,'Actual native CS40 current owner')
      outputs=[]
      if api_index in(1,3):depth=1 if api_index==1 else 0;values=(0xfffffffe if depth else 0xffffffff,depth,inputs['guest_thread']if depth else 0);outputs=[(cs+4+4*k,struct.pack('<I',v))for k,v in enumerate(values)]
      m.api_return(spec['source_PC'],spec['argc'],result,outputs);domain={};eq(m.cpu_now(),a['after'],'Whole source-derived explicit typed guest API return CPU40');api_index+=1;counts['complete_typed_API_CPU_frame_relations']+=1
    eq(api_index,4,'Four actual typed source APIs');eq(m.PCs,original_source['source_PCs'],'Exact142 genuine normal physical instruction order');eq(m.call_stack,[],'Source-defined ordinary/imported-EH frame closure');eq(bytes(m.state),records.data(stem+'after/State.bin'),'Entire3504 independently derived connected native State');eq(struct.pack('<10I',*m.cpu_now()),records.data(stem+'after/CPU.bin'),'Entire independently derived connected native CPU40');eq(m.fx,records.data(stem+'after/FX.bin'),'Entire512 guest FX unchanged');counts['whole_State3504_CPU40_FX512']+=1
    actual=list(struct.iter_unpack('<IIQII',records.data(stem+'after/accesses.bin')));eq(actual,m.accesses,'All113 independently derived causal PC/role/address/value/width/direction operands');counts['exact_ordered_source_operands']+=len(actual)
    projected=records.data(stem+'after/import-projections.bin');expected=[(v['access_index'],v['PC'],v['cell'],v['raw'],v['projected'])for v in m.projections];actual_projects=list(struct.iter_unpack('<6I',projected));eq([x[:5]for x in actual_projects],expected,'All seven raw owning IAT source projections without memory rewrite');counts['raw_IAT_projection_relations']+=len(expected)
    for k,o in enumerate(inputs['role_owners']):eq(m.bytes(o['new'],o['extent']),records.data(stem+f'after/borrowed/{k}.bin'),'Every complete source-derived borrowed role endpoint');counts['whole_borrowed_role_endpoints']+=1
    eq(m.bytes(cs,24),records.data(stem+'after/guestCS24.bin'),'Entire guest CS24 semantic endpoint');eq(m.bytes(0x78037000,4096),initial_memory[0x78037000],'Literal full modeled CRT25 page returns to declared input; actual full endpoint separately pending')
    for page in pages:eq(m.bytes(page,4096),records.data(f'sequence-0/phase-13-after-page-{page}.bin'),'Every entire ordinary carried source page endpoint');counts['whole_ordinary_source_page_endpoints']+=1
    eq(records.words(stem+'lifecycle.bin',8,'Q'),(1,api_rows[0]['words'][9],api_rows[0]['words'][10],4,0,1,1,1),'Actual owned TLS/CS cleanup receipt')
    fs=[x for x in m.accesses if x[1]==0x7ffde000 and x[4]];eq(len(fs),2,'Literal imported EH install/restore');eq(m.bytes(0x7ffde000,4),initial_memory[0x7ffde000],'Literal guest FS sentinel restored')
    # Carry is measured over all14 current records; no per-phase reseed here.
    for n in range(13):left=records.data(f'sequence-0/phase-{n}.bin');right=records.data(f'sequence-0/phase-{n+1}.bin');eq(words(left,10,76),tuple(list(words(right,10,36)[:4])+[0x20001804]+list(words(right,10,36)[5:9])+[0x410a80]),'Actual persistent caller CPU across next Runtime CALL');eq(left[628:1140],right[116:628],'Entire carried guestFX512 continuity');counts['full_guest_FX_continuity']+=1
    results.append(dict(level=level,root=0x5ae3e4,phase=13,source_PCs=m.PCs,source_accesses=m.accesses,source_API_relations=[{k:v.hex()if isinstance(v,bytes)else v for k,v in a.items()}for a in api_rows],source_import_projections=m.projections,source_FS_writes=fs,source_State_hex=bytes(m.state).hex(),source_CPU=m.cpu_now(),source_FX_hex=m.fx.hex(),source_borrowed_backings=[dict(**o,initial_hex=initial_memory[o['new']].hex(),source_final_hex=m.bytes(o['new'],o['extent']).hex())for o in inputs['role_owners']],flag_lifetimes=flags,source_AFTER_seed=False,unobserved_extra_whole_endpoints=['MFC manager5F4CB000','CRT78037000','guest FS fields'],old13_literal_replay_claim=False))
   finally:records.close();del records;closed=True
  target=out/'source-derivations.json';target.write_text(json.dumps(results,indent=2)+'\n');pin(target);pin(__file__);pin(sys.executable)
  for q,h in PINS.items():eq(sha(q),h,'Successful source inputs stable after reader close')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual current130 Context first13→MFC O0/O2 root142 literal source from own carried BEFORE, all113 causal operands, four complete typed APIs, full State/CPU/FX and five borrowed role capacities/46 ordinary page endpoints; extra manager/CRT/TIB whole endpoints pending',execution=str(execution),execution_sha256=digest,counts=dict(counts),files=PINS,source_AFTER_seed=False,per_phase_machine_reseed=False,all_bounded_readers_closed=closed,initializer_credit=0,current131_acceptance=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
