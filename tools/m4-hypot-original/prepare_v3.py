"""Prepare six authentic _hypot root probes; no capture or numeric prediction."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];OLD=R/'reports/m4-cosine-original/prefix-preparation-r2';BASE=R/'reports/m4-hypot-original'
sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact hypot derivation '+a[:100]);return s.replace(a,b,1)
def wrapper(name,pc,kind,tail):
 lines=[f'PUBLIC {name}',f'{name} PROC']
 for i,reg in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):lines.append(f' mov DWORD PTR hypot_cpu[{i*4}],{reg}')
 lines += [f' mov DWORD PTR hypot_cpu[36],0{pc:x}h',f' mov hypot_kind,{kind}',' mov esp,mixed_host_esp',' pushfd',' pop DWORD PTR hypot_cpu[32]',' cld',' mov eax,DWORD PTR fs:[0]',' mov hypot_head,eax',' fxsave hypot_fx',' fnstenv hypot_env',' fldenv hypot_env',' call hypot_observe',' fxrstor hypot_fx',' fldenv hypot_env',' push DWORD PTR hypot_cpu[32]',' popfd']
 for i,reg in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):
  if reg!='esp':lines.append(f' mov {reg},DWORD PTR hypot_cpu[{i*4}]')
 lines+=[' mov esp,DWORD PTR hypot_cpu[16]',tail,f'{name} ENDP']
 return '\n'.join(lines)+'\n'
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh hypot preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No inherited archive');v=sha(p);need(h is None or h==v,'Exact input '+str(p));pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json').read_bytes());need(old['passed'],'Authentic prior loader');rec=json.loads(pin(BASE/'recovery-r1/report.json','eac482b63a16938e9f931f34baa294e59aa8c216b861528426c24a988079eb77').read_bytes())
 for parent in(old,rec):
  for p,h in parent['files'].items():pin(p,h)
 graphs=json.loads(pin(BASE/'recovery-r1/game-graphs.json').read_bytes());game=PEImage(pin(R/'MW3/Mech3.exe').read_bytes());raw=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',raw,8)[0])};spans=list(old['source_spans']);known={r['pc']:r for r in spans};rows=[]
 specmod=importlib.util.spec_from_file_location('hypot_physical',pin(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py'));D=importlib.util.module_from_spec(specmod);specmod.loader.exec_module(D)
 saved_operand=D.operand
 def operand(value):
  v=value.strip();match=re.fullmatch(r'st\((\d)\)',v)
  if match:return dict(kind='x87-register',index=int(match[1]),bits=80)
  return saved_operand(value)
 D.operand=operand
 for graph in graphs.values():
  for v in graph['instructions']:
   pc=v['pc'];code=bytes.fromhex(v['bytes']);offset,_=game.rva_range(pc-game.image_base,len(code));need(game.data[offset:offset+len(code)]==code,'Each exact physical game instruction');r=D.instruction_contract(dict(pc=pc,width=len(code),bytes_hex=code.hex(),mnemonic=v['mnemonic'],operands=v['operands'].split(' <')[0]))
   if v['mnemonic'].startswith('f'):
    memory=[i for i,o in enumerate(r['decoded_operands'])if o['kind']=='memory'];store=v['mnemonic']in('fst','fstp')
    r['explicit_memory_reads']=[]if store else memory;r['explicit_memory_writes']=memory if store else [];r['x87_effects']='Literal source FP instruction; no numerical expected values supplied'
   rows.append(r)
   if pc in known:need(known[pc]['size']==len(code)and known[pc]['image_offset']==offset,'Shared source exact');continue
   page=pc&~4095
   if page not in records:records[page]=(1,bytearray(b'\xcc'*4096))
   records[page][1][pc&4095:(pc&4095)+len(code)]=code;spans.append(dict(pc=pc,size=len(code),image_offset=offset,origin=0));known[pc]=spans[-1]
 need(len(rows)==65 and sum(r['width']for r in rows)==211,'Exact finite game frontier')
 constants=json.loads(pin(BASE/'recovery-r1/physical-constants.json').read_bytes())
 for c in constants:
  address=c['address'];need(bytes(records[address&~4095][1][address&4095:(address&4095)+c['bytes']]).hex()==c['hex'],'Whole raw source constant input equals exact physical image')
 out.mkdir(parents=True);(out/'pages.bin').write_bytes(b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,perm)+data for p,(perm,data)in records.items()))
 spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str((out/'pages.bin').stat().st_size),spec)
 for field,values in [('entries',[0x4b5910]),('table_slots',[0x5e0154]),('page_bases',list(records)),('page_permissions',[v[0]for v in records.values()])]:spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(r[k])for k in('pc','size','image_offset','origin'))+'}'for r in spans)+'}};',spec);(out/'spec.hpp').write_text(spec)
 ref=text(OLD/'reference.cpp');ref=one(ref,'bool mw34::original_broker::handle_debug_checkpoint','#include "hypot_observer.hpp"\n\nbool mw34::original_broker::handle_debug_checkpoint')
 ref=re.sub(r'std::array<void\*,119> pages',f'std::array<void*,{len(records)}> pages',ref)
 ref=one(ref,'    auto*crtbegin=', '    hypot_target=reinterpret_cast<unsigned>(GetProcAddress(crt,"_hypot"));require(hypot_target==0x7802a122,"Exact genuine named _hypot export");*reinterpret_cast<unsigned*>(0x5bb5b0)=hypot_target;\n    auto*crtbegin=')
 install='''    {DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5bb5b0),4,PAGE_READWRITE,&prior),"Hypot game IAT observer protection");require(*reinterpret_cast<unsigned*>(0x5bb5b0)==hypot_target,"Actual named hypot target before observer");*reinterpret_cast<unsigned*>(0x5bb5b0)=reinterpret_cast<unsigned>(&hypot_entry);require(VirtualProtect(reinterpret_cast<void*>(0x5bb5b0),4,prior,&ignored),"Hypot game IAT observer protection restored");}
    for(const auto&hook:hypot_hooks){auto*code=reinterpret_cast<unsigned char*>(hook.pc);require(!std::memcmp(code,hook.raw,hook.size),"Exact physical hypot return span");DWORD prior{},ignored{};require(VirtualProtect(code,hook.size,PAGE_EXECUTE_READWRITE,&prior),"Hypot return observer protection");code[0]=0xe9;const unsigned d=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&d,4);require(VirtualProtect(code,hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),code,hook.size),"Hypot return observer restored protection");}
'''
 ref=one(ref,'    owner=GetCurrentThreadId();',install+'    owner=GetCurrentThreadId();')
 ref=one(ref,'    out.append("crt-image.bin",','    const std::array<unsigned,4> hypot_identity{0x5bb5b0,hypot_target,reinterpret_cast<unsigned>(&hypot_entry),reinterpret_cast<unsigned>(crt)};out.append("hypot/identity.bin",hypot_identity.data(),sizeof(hypot_identity));\n    out.append("crt-image.bin",')
 ref=one(ref,'            lockit_count=0;','            hypot_count=0;std::memset(hypot_snapshots,0,sizeof(hypot_snapshots));\n            lockit_count=0;')
 before='''            for(unsigned i=0;i<64;++i)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/hypot-CRT-before/"+std::to_string(0x78000000+i*4096)+".bin",reinterpret_cast<void*>(0x78000000+i*4096),4096);
'''
 ref=one(ref,'            r->tag.status=execute();',before+'            r->tag.status=execute();')
 after='''            require(hypot_count==4,"Actual two _hypot entry/first-game-return pairs");const auto hstem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/hypot";out.append(hstem+"-count.bin",&hypot_count,4);out.append(hstem+"-snapshots.bin",hypot_snapshots,hypot_count*sizeof(HypotSnapshot));
            for(unsigned i=0;i<64;++i)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/hypot-CRT-after/"+std::to_string(0x78000000+i*4096)+".bin",reinterpret_cast<void*>(0x78000000+i*4096),4096);
'''
 ref=one(ref,'            require(registry_API_count<=32,',after+'            require(registry_API_count<=32,')
 hookproof='''for(const auto&hook:hypot_hooks)if(hook.pc<=span.pc&&span.pc+span.size<=hook.pc+hook.size){const unsigned off=span.pc-hook.pc;require(!std::memcmp(origin.data()+span.image_offset,hook.raw+off,span.size),"Exact physical hypot source input");const unsigned d=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);for(unsigned n=0;n<span.size;++n){const unsigned relative=off+n;const unsigned char expected=relative==0?0xe9:static_cast<unsigned char>(d>>(8*(relative-1)));require(*reinterpret_cast<unsigned char*>(span.pc+n)==expected,"Exact declared hypot return observer byte");}hooked=true;}'''
 ref=one(ref,'if(!hooked)require(',hookproof+'if(!hooked)require(')
 restore='''    {DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5bb5b0),4,PAGE_READWRITE,&prior),"Hypot game IAT restoration protection");require(*reinterpret_cast<unsigned*>(0x5bb5b0)==reinterpret_cast<unsigned>(&hypot_entry),"Declared hypot observer before restoration");*reinterpret_cast<unsigned*>(0x5bb5b0)=hypot_target;require(VirtualProtect(reinterpret_cast<void*>(0x5bb5b0),4,prior,&ignored),"Hypot named game IAT restored protection");}
    for(const auto&hook:hypot_hooks){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,PAGE_EXECUTE_READWRITE,&prior),"Hypot restoration protect");std::memcpy(reinterpret_cast<void*>(hook.pc),hook.raw,hook.size);require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(hook.pc),hook.size),"Hypot exact return source restoration");}
'''
 ref=one(ref,'    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){',restore+'    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){')
 ref=one(ref,'            require(actual[byte]==(pc>=capture_pc', '            if(pc>=0x5bb5b0&&pc<0x5bb5b4){require(actual[byte]==reinterpret_cast<const unsigned char*>(&hypot_target)[pc-0x5bb5b0],"Exact measured named hypot IAT after restoration");continue;}\n            require(actual[byte]==(pc>=capture_pc')
 ref=ref.replace('Actual FCOS root','Actual hypot root').replace('Actual cosine prefix','Actual hypot prefix').replace('Six genuine FCOS initializer hardware endpoints captured','Six genuine hypot initializer hardware endpoints captured');(out/'reference.cpp').write_text(ref)
 for fn in('protocol.hpp','original_broker.hpp','reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','fs_observer_x86.asm','fs-hook-bindings.json'):(out/fn).write_text(text(OLD/fn))
 (out/'hypot_observer.hpp').write_text(text(R/'tools/m4-hypot-original/hypot_observer_v2.hpp'))
 asm='.686p\n.xmm\n.model flat,C\nassume fs:nothing\noption casemap:none\n'+'\n'.join('EXTERN '+n+':'+t for n,t in [('mixed_host_esp','DWORD'),('hypot_head','DWORD'),('hypot_cpu','BYTE'),('hypot_fx','BYTE'),('hypot_env','BYTE'),('hypot_kind','DWORD'),('hypot_target','DWORD'),('hypot_continues','DWORD'),('hypot_observe','PROC')])+'\n.code\n'
 asm+=wrapper('hypot_entry',0x7802a122,0,' jmp DWORD PTR hypot_target')+wrapper('hypot_return_first',0x4b58be,1,' db 0d9h,046h,008h,0d9h,0c9h\n jmp DWORD PTR hypot_continues[0]')+wrapper('hypot_return_second',0x4b58e9,2,' db 0d9h,046h,00ch,0d9h,0c9h\n jmp DWORD PTR hypot_continues[4]')+'END\n';(out/'hypot_observer_x86.asm').write_text(asm)
 cmake=one(text(OLD/'CMakeLists.txt'),'lockit_observer_x86.asm "','lockit_observer_x86.asm hypot_observer_x86.asm "');(out/'CMakeLists.txt').write_text(cmake)
 contract=dict(instructions=rows,raw_source_FP_inputs_not_AFTER=True,default_constants=constants,root=0x4b5910,slot=0x5e0154,helper=0x4b5860,object=0x60b2c8,object_extent=36,owning_IAT=0x5bb5b0,actual_preferred_provider=0x7802a122,return_hook_spans=[dict(PC=0x4b58be,width=5,bytes_hex='d94608d9c9'),dict(PC=0x4b58e9,width=5,bytes_hex='d9460cd9c9')],snapshot_bytes=271012,snapshot_layout=dict(header=0,CPU40=64,FX512=104,ENV28=616,frame32=644,stack4096=676,source4096=4772,CRT64pages=8868),original_return_scope='Actual first game instruction before literal FLD+FXCH replay; genuine provider RET consumed4B, source caller cleanup and subsequent FP remain actual source instructions',provider_preinvoked=False,numerical_result_expected_seed=False)
 (out/'instruction-contracts.json').write_text(json.dumps(contract,indent=2)+'\n');pin(__file__);pin(R/'tools/m4-hypot-original/prepare.py');pin(R/'tools/m4-hypot-original/derive_prepare_v2.py');pin(R/'tools/m4-hypot-original/prepare_v2.py');pin(R/'tools/m4-hypot-original/derive_prepare_v3.py')
 for p in out.iterdir():pin(p)
 report=dict(passed=True,scope='Physically prepared genuine six-case hypot root and bounded true cdecl observations; source/provider equivalence remains open',source_spans=spans,pack_sha256=sha(out/'pages.bin'),original_sequences=6,original_phases=6,observed_pages=old['observed_pages'],record_bytes=356992,snapshot_bytes=271012,game_rows=65,game_bytes=211,predicted_outputs_supplied_to_execution=False,provider_preinvoked=False,source_after_seed=False,archive_reader_opened=False,original_executed=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
