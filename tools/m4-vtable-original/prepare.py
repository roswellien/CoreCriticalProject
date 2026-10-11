"""Additive actual original120 with transparent genuine indirect target/RET observations."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;BASE=ROOT/'reports/m4-vtable-original';OLD=ROOT/'reports/m4-container-source/original-preparation-r2';SRC=ROOT/'reports/m4-next-source/recovery-r1'
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
S=importlib.util.spec_from_file_location('original120_fs',ROOT/'tools/m4-fs-source/fs_hooks_v2.py');F=importlib.util.module_from_spec(S);S.loader.exec_module(F)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,w):
 if not v:raise ValueError(w)
def one(s,a,b):need(s.count(a)==1,'One replacement '+a[:60]);return s.replace(a,b,1)
def mapped_page(pe,base):
 result=bytearray(4096);rva=base-pe.image_base
 for sec in pe.sections:
  lo=max(rva,sec['virtual_address']);hi=min(rva+4096,sec['virtual_address']+max(sec['virtual_size'],sec['raw_size']));end=min(hi,sec['virtual_address']+sec['raw_size'])
  if end>lo:result[lo-rva:end-rva]=pe.data[sec['raw_offset']+lo-sec['virtual_address']:sec['raw_offset']+end-sec['virtual_address']]
 return result
VTABLE_CPP=r'''
extern "C" {
Cpu vtable_cpu{};unsigned vtable_head{},vtable_point{},vtable_count{};
alignas(16) unsigned char vtable_fx[512]{};unsigned char vtable_env[28]{};
struct VtableSnapshot{unsigned words[16];Cpu cpu;unsigned char fx[512],env[28],stack[16];};
static_assert(sizeof(VtableSnapshot)==660);VtableSnapshot vtable_snapshots[12]{};
void vtable_observe(){
 if(!fs_phase_root)return;if(vtable_count>=12){fs_error=1;return;}
 const auto frame=vtable_cpu.esp;if(frame<0x20001000||frame+16>0x20002000){fs_error=1;return;}
 const auto*w=reinterpret_cast<const unsigned*>(frame);const VtableBinding*spec{};
 for(const auto&i:vtable_bindings)if(i.root==fs_phase_root&&i.return_pc==w[0]&&i.ECX==vtable_cpu.ecx){spec=&i;break;}
 if(!spec||(spec->argument!=0xffffffff&&w[1]!=spec->argument)||((vtable_count%2)==0)!=(vtable_point==0)){fs_error=1;return;}
 const auto raw=*reinterpret_cast<unsigned*>(spec->slot),vptr=spec->vtable?*reinterpret_cast<unsigned*>(spec->object):0;
 if(raw!=spec->target||(spec->vtable&&vptr!=spec->vtable)){fs_error=1;return;}
 auto&e=vtable_snapshots[vtable_count];e={};e.words[0]=1;e.words[1]=vtable_count;e.words[2]=fs_phase_root;e.words[3]=vtable_point;e.words[4]=vtable_cpu.pc;e.words[5]=spec->target;e.words[6]=spec->CALL_pc;e.words[7]=spec->slot;e.words[8]=raw;e.words[9]=spec->ECX;e.words[10]=spec->object;e.words[11]=vptr;e.words[12]=frame;e.words[13]=spec->return_pc;e.words[14]=spec->cleanup;e.words[15]=registry_API_count;e.cpu=vtable_cpu;
 std::memcpy(e.fx,vtable_fx,512);std::memcpy(e.env,vtable_env,28);std::memcpy(e.stack,w,16);
 if(vtable_point){const auto&prior=vtable_snapshots[vtable_count-1];if(prior.words[5]!=e.words[5]||prior.words[12]!=frame||prior.words[13]!=w[0]||prior.words[15]!=e.words[15])fs_error=1;}
 ++vtable_count;
}
}
'''
def vtable_asm(hooks):
 lines=['.686p','.xmm','.model flat, C','assume fs:nothing','option casemap:none']
 for n,t in [('mixed_host_esp','DWORD'),('vtable_cpu','BYTE'),('vtable_head','DWORD'),('vtable_point','DWORD'),('vtable_fx','BYTE'),('vtable_env','BYTE'),('vtable_observe','PROC')]:lines.append('EXTERN '+n+':'+t)
 for h in hooks:
  if h['kind']==0:lines.append('EXTERN vtable_continue_'+format(h['PC'],'x')+':DWORD')
 lines+=['.code'];regs=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
 for h in hooks:
  name=h['declared_observer'];pc=h['PC'];lines+=['PUBLIC '+name,name+' PROC']
  lines += [f' mov DWORD PTR vtable_cpu[{i*4}],{r}'for i,r in enumerate(regs)]
  lines += [f' mov DWORD PTR vtable_cpu[36],{pc:08x}h',f' mov vtable_point,{h["kind"]}',' mov esp,mixed_host_esp',' pushfd',' pop DWORD PTR vtable_cpu[32]',' mov eax,DWORD PTR fs:[0]',' mov vtable_head,eax',' fxsave vtable_fx',' fnstenv vtable_env',' fldenv vtable_env',' call vtable_observe',' fxrstor vtable_fx',' fldenv vtable_env',' push DWORD PTR vtable_cpu[32]',' popfd']
  lines += [f' mov {r},DWORD PTR vtable_cpu[{i*4}]'for i,r in enumerate(regs)if r!='esp'];lines+=[' mov esp,DWORD PTR vtable_cpu[16]']
  raw=bytes.fromhex(h['replayed_bytes']);lines+=[' db '+','.join(f'0{x:02x}h'for x in raw)]
  if h['kind']==0:lines+=[' jmp DWORD PTR vtable_continue_'+format(pc,'x')]
  lines += [name+' ENDP']
 return '\n'.join(lines+['END'])+'\n'
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical source '+str(p));need(str(p)not in pins or pins[str(p)]==v,'No pin conflict');pins[str(p)]=v;return p
 def read(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json','fc3ce8ef54040236bced7072b3c121a0a7121c19ca81ef6e19ae0f54d5a06c49').read_bytes())
 for p,h in old['files'].items():pin(p,h)
 rec=json.loads(pin(SRC/'report.json','99e59ac4b9adeb98f2227361f80db78e12eead87e35212d71b4147a8ba9effeb').read_bytes())
 for p,h in rec['files'].items():pin(p,h)
 pin(ROOT/'reports/m4-joint-startup116-root/acceptance-r1/report.json','de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6')
 gi=json.loads(pin(SRC/'instruction-contracts.json','a58e31641f42e8e37c1d66bad5e41dd57854b82a7a00bd86a02b1bc85aec9108').read_bytes());game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 need(len(gi['selected_order'])==120 and len(gi['static_indirect_inputs'])==6,'Four roots/six indirect calls');out.mkdir(parents=True)
 pack=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',pack,12+i*4104)[0]:(struct.unpack_from('<I',pack,16+i*4104)[0],bytearray(pack[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',pack,8)[0])}
 spans=list(old['source_spans']);oldpcs={s['pc']for s in spans}
 for r in gi['instructions']:
  pc=r['pc'];raw=bytes.fromhex(r['bytes_hex']);off,_=game.rva_range(pc-game.image_base,len(raw));need(game.data[off:off+len(raw)]==raw,'Literal PE instruction');base=pc&~4095;need((pc&4095)+len(raw)<=4096,'Single-page instruction')
  if base not in records:records[base]=(1,bytearray(b'\xcc'*4096))
  if pc in oldpcs:need(records[base][1][pc&4095:(pc&4095)+len(raw)]==raw,'Same accepted source bytes')
  else:records[base][1][pc&4095:(pc&4095)+len(raw)]=raw;spans.append(dict(pc=pc,size=len(raw),image_offset=off,origin=0))
 for a in rec['new_pages']:need(a not in records,'New table/object page');records[a]=(0 if a!=0x5fc000 else 2,mapped_page(game,a))
 observed=old['observed_pages']+rec['new_pages'];need(len(observed)==40,'40 observed pages');pack=b'MW4J120P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',a,p)+raw for a,(p,raw)in records.items());(out/'pages.bin').write_bytes(pack)
 spec=read(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{sha(out/"pages.bin")}"',spec);spec=re.sub(r'pack_size=\d+',f'pack_size={len(pack)}',spec)
 for key,vals in [('entries',[r['entry']for r in gi['selected_order']]),('table_slots',[r['slot']for r in gi['selected_order']]),('page_bases',list(records)),('page_permissions',[p for p,raw in records.values()])]:spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+key+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(vals)}> '+key+'{'+','.join(hex(v)for v in vals)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(s[k])for k in('pc','size','image_offset','origin'))+'}'for s in spans)+'}};',spec)
 spec+='\nstruct VtableBinding{unsigned root,CALL_pc,slot,target,ECX,argument,cleanup,object,vtable,return_pc;};\ninline constexpr std::array<VtableBinding,6>vtable_bindings{{'+','.join('{'+','.join(hex(v)for v in(r['root'],r['CALL_pc'],r['slot'],r['target'],r['entry_ECX'],r['argument']if r['argument']is not None else 0xffffffff,r['RET_cleanup'],r['source_object'],r.get('source_vtable',0),r['return_pc']))+'}'for r in gi['static_indirect_inputs'])+'}};\n';(out/'spec.hpp').write_text(spec)
 protocol=read(OLD/'protocol.hpp').replace('roots=116','roots=120').replace('observed_page_count=37','observed_page_count=40').replace('sizeof(Record)==307840','sizeof(Record)==332416');protocol=one(protocol,'0x736000,0x5f4cc000};','0x736000,0x5f4cc000,'+','.join(hex(p)for p in rec['new_pages'])+'};');(out/'protocol.hpp').write_text(protocol)
 broker=read(OLD/'original_broker.hpp');m=re.search(r'std::array<std::uint32_t,\d+> bases\{([^;]+)\};',broker);bases=list(dict.fromkeys([int(x,16)for x in m[1].split(',')]+[a&~65535 for a in records if a<0x78000000]));need(0x5f4c0000 not in bases,'No reserve of real loaded MFC data');broker=broker[:m.start()]+f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(a)for a in bases)+'};'+broker[m.end():];(out/'original_broker.hpp').write_text(broker)
 hooks=[(h['PC'],h['kind'],h['raw_bytes'])for h in json.loads(pin(OLD/'fs-hook-bindings.json').read_bytes())]
 hooks += [(0x4824a7,0,'64a100000000'),(0x4824ae,1,'64892500000000'),(0x4824ed,2,'64890d00000000')];need(len(hooks)==33 and len(set(p for p,k,r in hooks))==33,'33 transparent FS sites');F.HOOKS=hooks
 vh=[]
 for pc,size,kind,replay_size in [(0x40e820,7,0,7),(0x59ff00,5,0,5),(0x59ff80,6,0,6),(0x40e827,5,1,3),(0x59ff0d,5,1,1),(0x59ffa1,5,1,3)]:
  off,_=game.rva_range(pc-game.image_base,size);raw=game.data[off:off+size];base=pc&~4095;need(base in records,'Observed admitted helper code');records[base][1][pc&4095:(pc&4095)+size]=raw
  vh.append(dict(PC=pc,size=size,kind=kind,raw_bytes=raw.hex(),replayed_bytes=raw[:replay_size].hex(),continuation=pc+size if kind==0 else 0,declared_observer='vtable_hook_'+format(pc,'x'),physical_offset=off,padding_bytes=size-replay_size))
 # Pack includes bounded authentic padding touched only by the observer patch.
 pack=b'MW4J120P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',a,p)+raw for a,(p,raw)in records.items());(out/'pages.bin').write_bytes(pack);spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{sha(out/"pages.bin")}"',spec);(out/'spec.hpp').write_text(spec)
 ref=read(OLD/'reference.cpp').replace('MW4J116','MW4J120').replace('Original116','Original120').replace('original116','original120').replace('/696 actual','/720 actual').replace('88*4','92*4').replace('Exact88callback','Exact92callback')
 start=ref.index('void fs_hook_');end=ref.index('struct FsAllocation {',start);ref=ref[:start]+F.declarations()+F.hook_table().replace('std::array<FsHook,9>','std::array<FsHook,33>')+ref[end:]
 ref=re.sub(r'std::array<void\*,110> pages',f'std::array<void*,{len(records)}> pages',ref)
 declarations='extern "C" {\n'+''.join('void '+h['declared_observer']+'();\n'+('extern const unsigned vtable_continue_'+format(h['PC'],'x')+'='+hex(h['continuation'])+';\n'if h['kind']==0 else'')for h in vh)+'}\n'
 table='struct VtableHook{unsigned pc,size;void(*entry)();unsigned char raw[7];};const std::array<VtableHook,6>vtable_hooks{{'+','.join('{'+hex(h['PC'])+','+str(h['size'])+',&'+h['declared_observer']+',{'+','.join(hex(x)for x in bytes.fromhex(h['raw_bytes']))+'}}'for h in vh)+'}};\n'
 ref=one(ref,'static std::uint32_t execute()',VTABLE_CPP+'\n'+declarations+table+'\nstatic std::uint32_t execute()')
 installation='    for(const auto&hook:vtable_hooks){auto*code=reinterpret_cast<unsigned char*>(hook.pc);require(!std::memcmp(code,hook.raw,hook.size),"Exact vtable observer physical source span");DWORD prior{},ignored{};require(VirtualProtect(code,hook.size,PAGE_EXECUTE_READWRITE,&prior),"Vtable source observer protection");code[0]=0xe9;const unsigned delta=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&delta,4);for(unsigned n=5;n<hook.size;++n)code[n]=0x90;require(VirtualProtect(code,hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),code,hook.size),"Vtable observer permission restore");}\n'
 ref=one(ref,'    require(!std::memcmp(reinterpret_cast<void*>(0x5f4020b4)',installation+'    require(!std::memcmp(reinterpret_cast<void*>(0x5f4020b4)')
 ref=one(ref,'fs_phase_root=entries[phase];fs_event_count=0;fs_error=0;','fs_phase_root=entries[phase];fs_event_count=0;fs_error=0;vtable_count=0;std::memset(vtable_snapshots,0,sizeof(vtable_snapshots));')
 ref=one(ref,'            out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/fs-event-count.bin"','            const auto vbase="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/vtable";out.append(vbase+"-count.bin",&vtable_count,4);out.append(vbase+"-snapshots.bin",vtable_snapshots,vtable_count*sizeof(VtableSnapshot));require((vtable_count%2)==0,"Actual indirect target entry and preRET pairs");\n            out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/fs-event-count.bin"')
 # Integrity checks cover every original instruction/padding byte under an exact declared patch.
 needle='if(!hooked)require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Original selected source changed after checkpoint");'
 replacement='for(const auto&hook:vtable_hooks)if(hook.pc<=span.pc&&span.pc+span.size<=hook.pc+hook.size){const unsigned offset=span.pc-hook.pc;require(!std::memcmp(origin.data()+span.image_offset,hook.raw+offset,span.size),"Exact vtable observer physical instruction input");for(unsigned n=0;n<span.size;++n){const unsigned relative=offset+n,delta=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);const unsigned char expected=relative==0?0xe9:relative<5?static_cast<unsigned char>(delta>>(8*(relative-1))):0x90;require(*reinterpret_cast<unsigned char*>(span.pc+n)==expected,"Exact declared vtable observer patched instruction byte");}hooked=true;}'+needle
 ref=one(ref,needle,replacement)
 ref=one(ref,'if(fs_byte)continue;','if(fs_byte)continue;bool vtable_byte=false;for(const auto&hook:vtable_hooks)if(hook.pc<=pc&&pc<hook.pc+hook.size){const unsigned relative=pc-hook.pc,delta=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);const unsigned char value=relative==0?0xe9:relative<5?static_cast<unsigned char>(delta>>(8*(relative-1))):0x90;require(actual[byte]==value,"Exact protected vtable observer physical byte");vtable_byte=true;}if(vtable_byte)continue;')
 (out/'reference.cpp').write_text(ref)
 for n in ('reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','mfc-import-bindings.json','mfc-raw-page.bin','nullfree-hook-bindings.json'):(out/n).write_bytes(pin(OLD/n).read_bytes())
 (out/'fs_observer_x86.asm').write_text(F.asm());(out/'vtable_observer_x86.asm').write_text(vtable_asm(vh));(out/'CMakeLists.txt').write_text(read(OLD/'CMakeLists.txt').replace('Startup116','Startup120').replace('startup116','startup120').replace('nullfree_observer_x86.asm','nullfree_observer_x86.asm vtable_observer_x86.asm'))
 (out/'fs-hook-bindings.json').write_text(json.dumps([dict(PC=p,kind=k,raw_bytes=r,continuation=p+len(bytes.fromhex(r)),declared_observer='fs_hook_'+format(p,'x'))for p,k,r in hooks],indent=2)+'\n');(out/'vtable-hook-bindings.json').write_text(json.dumps(vh,indent=2)+'\n');(out/'vtable-inputs.json').write_text(json.dumps(gi['static_indirect_inputs'],indent=2)+'\n')
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(__file__);pin(F.__file__)
 report=dict(passed=True,scope='Actual original120 preparation with genuine untouched indirect CALL, fullCPU/FX/ENV target entry and immediate preRET observation; execution pending',parent_preparation=str(OLD),parent_sha256=sha(OLD/'report.json'),parent_acceptance_sha256='de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6',order=gi['selected_order'],observed_pages=observed,page_count=len(records),record_bytes=332416,pack_sha256=sha(out/'pages.bin'),source_spans=spans,mfc_bindings=old['mfc_bindings'],fs_allocations=old['fs_allocations'],container_allocations=old['container_allocations'],string_inputs=old['string_inputs'],FS_hooks=33,fs_event_record_bytes=1216,nullfree_snapshot_bytes=628,nullfree_snapshots_per_sequence=10,vtable_hooks=6,vtable_snapshot_bytes=660,vtable_snapshots_per_sequence=12,vtable_observation_scope='Actual target entry and preRET; postRET solely physical RET/frame-derived and joined to actual root endpoint',vtable_snapshot_words=['v','index','root','point','PC','target','CALLpc','slot','raw','ECX','object','vptr','frame','returnPC','cleanup','APIcount'],initial_backing_limit=1024,loader_page=old['loader_page'],offsets=dict(memory_before=2276,memory_after=166116,end=329956,registry_header=331888,registry_bytes=331904),ordinary_nonstack_pages=38,per_phase_reseed=False,AFTER_machine_seed=False,source_cleanup=old['source_cleanup'],original_executed=False,native_executed=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),pages=len(records),observed=len(observed))))
if __name__=='__main__':main(sys.argv[1])
