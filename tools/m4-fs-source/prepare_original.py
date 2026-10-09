"""Additive genuine original109 capture with transparent bounded FS observers."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fs-source';OLD=ROOT/'reports/m4-mfc-source/original-preparation-r1';REC=BASE/'recovery-r3'
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
sys.path.insert(0,str(Path(__file__).parent));import fs_hooks as F
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,w):
 if not v:raise ValueError(w)
def one(s,a,b):need(s.count(a)==1,'One additive replacement '+a[:60]);return s.replace(a,b)

ALLOCATION_CODE=r'''
struct FsAllocation {unsigned version,index,root,CALL_pc,request,source_frame,API_index,pointer,capacity;};
static_assert(sizeof(FsAllocation)==36);
FsAllocation fs_allocations[10]{};unsigned fs_allocation_count{};
void fs_observe_allocation(unsigned api_index,unsigned pointer,unsigned capacity){
 if(!fs_phase_root||registry_API_kind!=0||!pointer)return;
 // Exact normal MFC frame F = true CRT HeapAlloc frame A +104.
 const auto api_frame=registry_API_before.esp;const auto source_frame=api_frame+104;
 if(api_frame<0x20001000||source_frame+8>0x20002000){fs_error=1;return;}
 const auto source_return=*reinterpret_cast<unsigned*>(source_frame);
 const auto request=*reinterpret_cast<unsigned*>(source_frame+4);
 for(const auto&binding:fs_allocation_bindings){
  if(binding.root!=fs_phase_root||binding.CALL_pc+5!=source_return)continue;
  if(fs_allocation_count>=10||request!=binding.request||*reinterpret_cast<unsigned*>(api_frame)!=0x78001385||*reinterpret_cast<unsigned*>(api_frame+80)!=0x5f401eb7){fs_error=1;return;}
  auto&entry=fs_allocations[fs_allocation_count];entry={1,fs_allocation_count,fs_phase_root,binding.CALL_pc,request,source_frame,api_index,pointer,capacity};++fs_allocation_count;return;
 }
}
'''

def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original109 preparation');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact additive preparation input');pins[str(p)]=v;return p
 def read(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json','970b1ee3f6b2d7d375439579d7c5923df8ea2ab6022f466f5f297746120abb2f').read_bytes())
 rec=json.loads(pin(REC/'report.json','17c7840c58bcdce2a82989d141f202cbb25540b6c29b4f314c06c0d1c2bf3a6b').read_bytes())
 interface=json.loads(pin(BASE/'allocation-interface-r1/report.json','f7440d694771cc39c662a9842f7673c0c97d63274505b41894e325bcfde48a9b').read_bytes())
 bindings=json.loads(pin(BASE/'allocation-interface-r1/allocation-inputs.json',interface['allocation_inputs_sha256']).read_bytes())
 pin(ROOT/'reports/m4-joint-startup103-root/acceptance-r1/report.json','13cc2567f30f2dae2d12991a3a76aa6c953c70a49148dc4ed13df34837b14c7c')
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 pack=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',pack,12+i*4104)[0]:(struct.unpack_from('<I',pack,16+i*4104)[0],bytearray(pack[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',pack,8)[0])}
 spec=read(OLD/'spec.hpp');match=re.search(r'code_bindings\{\{([^;]+)\}\};',spec);spans=[dict(zip(('pc','size','image_offset','origin'),[int(x,16)for x in vals]))for vals in re.findall(r'\{(0x[0-9a-f]+),(0x[0-9a-f]+),(0x[0-9a-f]+),(0x[0-9a-f]+)\}',match[1])]
 oldpcs={s['pc']for s in spans};graphs=json.loads(pin(REC/'game-new-graphs.json').read_bytes());rows={r['pc']:r for g in graphs.values()for r in g['instructions']}
 for pc,row in rows.items():
  raw=bytes.fromhex(row['bytes']);off,_=game.rva_range(pc-game.image_base,len(raw));need(game.data[off:off+len(raw)]==raw,'Every new original instruction physical binding')
  base=pc&~4095;need((pc&4095)+len(raw)<=4096,'Bounded same-page instruction')
  if base not in records:records[base]=(1,bytearray(b'\xcc'*4096))
  if pc in oldpcs:need(records[base][1][pc&4095:(pc&4095)+len(raw)]==raw,'Unchanged existing sparse source')
  else:records[base][1][pc&4095:(pc&4095)+len(raw)]=raw;spans.append(dict(pc=pc,size=len(raw),image_offset=off,origin=0))
 observed=old['observed_pages'];need(len(observed)==35 and set(rec['data_pages'])<=set(observed),'No new fixed game data page; FS has actual Windows TIB domain')
 pack=b'MW4J109P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',a,p)+raw for a,(p,raw)in records.items());(out/'pages.bin').write_bytes(pack)
 spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{sha(out/"pages.bin")}"',spec);spec=re.sub(r'pack_size=\d+',f'pack_size={len(pack)}',spec)
 for key,values in [('entries',[r['entry']for r in rec['order']]),('table_slots',[r['slot']for r in rec['order']]),('page_bases',list(records)),('page_permissions',[p for p,raw in records.values()])]:
  spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+key+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+key+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(s[k])for k in('pc','size','image_offset','origin'))+'}'for s in spans)+'}};',spec)
 spec+='\nstruct FsAllocationBinding{unsigned root,CALL_pc,request;};\ninline constexpr std::array<FsAllocationBinding,10> fs_allocation_bindings{{'+','.join('{'+','.join(hex(r[k])for k in('root','CALL_pc','requested_size'))+'}'for r in bindings)+'}};\n'
 (out/'spec.hpp').write_text(spec)
 (out/'protocol.hpp').write_text(read(OLD/'protocol.hpp').replace('roots=103','roots=109'))
 broker=read(OLD/'original_broker.hpp');m=re.search(r'std::array<std::uint32_t,\d+> bases\{([^;]+)\};',broker);bases=list(dict.fromkeys([int(x,16)for x in m[1].split(',')]+[a&~65535 for a in records]));broker=broker[:m.start()]+f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(a)for a in bases)+'};'+broker[m.end():];(out/'original_broker.hpp').write_text(broker)
 ref=read(OLD/'reference.cpp').replace('MW4J103P','MW4J109P').replace('MW4J103O','MW4J109O').replace('MW4J103D','MW4J109D').replace('Original103','Original109').replace('original103','original109')
 ref=one(ref,'RegistryAPIEntry registry_API_ledger[32]{};','RegistryAPIEntry registry_API_ledger[32]{};\nvoid fs_observe_allocation(unsigned,unsigned,unsigned);')
 ref=one(ref,'std::memcpy(registry_initial_bytes[i],pointer,size);','std::memcpy(registry_initial_bytes[i],pointer,size);fs_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));')
 ref=one(ref,'static std::uint32_t execute()',F.CPP+F.declarations()+F.hook_table()+ALLOCATION_CODE+'\nstatic std::uint32_t execute()')
 ref=re.sub(r'std::array<void\*,103> pages',f'std::array<void*,{len(records)}> pages',ref)
 anchor='    owner=GetCurrentThreadId();'
 hook_install='''    for(const auto&hook:fs_hooks){auto*code=reinterpret_cast<unsigned char*>(hook.pc);require(!std::memcmp(code,hook.raw,hook.size),"Exact original FS observer source row");DWORD prior{},ignored{};require(VirtualProtect(code,hook.size,PAGE_EXECUTE_READWRITE,&prior),"FS observer source protection");code[0]=0xe9;const unsigned delta=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&delta,4);for(unsigned n=5;n<hook.size;++n)code[n]=0x90;require(VirtualProtect(code,hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),code,hook.size),"FS observer source permission restore");}
    owner=GetCurrentThreadId();'''
 ref=one(ref,anchor,hook_install)
 ref=one(ref,'mixed_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202,entries[0]};','fs_allocation_count=0;std::memset(fs_allocations,0,sizeof(fs_allocations));fs_phase_root=0;\n        mixed_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202,entries[0]};')
 ref=one(ref,'            r->tag.status=execute();','            fs_phase_root=entries[phase];fs_event_count=0;fs_error=0;\n            r->tag.status=execute();fs_phase_root=0;require(!fs_error,"Exact FS observer/allocation transparency");')
 phase_output='''            out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/fs-event-count.bin",&fs_event_count,4);out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/fs-events.bin",fs_events,fs_event_count*sizeof(FsEvent));
            for(unsigned fi=0;fi<fs_allocation_count;++fi){const auto&a=fs_allocations[fi];const auto cap=HeapSize(actual_heap,0,reinterpret_cast<void*>(a.pointer));require(cap==a.capacity,"Persistent actual FS allocation extent");const auto stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/fs-allocation/"+std::to_string(fi);out.append(stem+"/meta.bin",&a,sizeof(a));out.append(stem+"/bytes.bin",reinterpret_cast<void*>(a.pointer),cap);}
            const auto stringbase='''
 ref=one(ref,'            const auto stringbase=',phase_output)
 ref=ref.replace('75*4','81*4').replace('Exact75callback','Exact81callback')
 ref=one(ref,'registry_cleanup.restore();for(unsigned mi=0;','''registry_cleanup.restore();require(fs_allocation_count==10,"Exact ten genuine FS allocations");for(unsigned fi=0;fi<fs_allocation_count;++fi){const auto&a=fs_allocations[fi];const auto stem="cleanup/"+std::to_string(sequence)+"/fs-allocation-"+std::to_string(fi);out.append(stem+"-before.bin",&a,sizeof(a));out.append(stem+"-owned.bin",reinterpret_cast<void*>(a.pointer),a.capacity);mfc825(reinterpret_cast<void*>(a.pointer));const unsigned returned=1;out.append(stem+"-returned.bin",&returned,4);}for(unsigned mi=0;''')
 original_check='require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Original selected source changed after checkpoint");'
 instrumented_check='''bool hooked=false;for(const auto&hook:fs_hooks)if(span.pc==hook.pc){require(span.size==hook.size&&!std::memcmp(origin.data()+span.image_offset,hook.raw,hook.size),"Exact unchanged FS physical input");const auto*code=reinterpret_cast<unsigned char*>(hook.pc);require(code[0]==0xe9&&word<unsigned>(code+1)==reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5),"Exact declared FS observer JMP");for(unsigned n=5;n<hook.size;++n)require(code[n]==0x90,"Exact observer padding");hooked=true;}if(!hooked)require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Original selected source changed after checkpoint");'''
 ref=one(ref,original_check,instrumented_check)
 ref=ref.replace('/618 actual','/654 actual');(out/'reference.cpp').write_text(ref)
 for name_ in ('reference_x86.asm','preserve_x86.asm'):(out/name_).write_text(read(OLD/name_))
 (out/'fs_observer_x86.asm').write_text(F.asm())
 cmake=read(OLD/'CMakeLists.txt').replace('Startup103','Startup109').replace('startup103','startup109').replace('reference_x86.asm preserve_x86.asm','reference_x86.asm preserve_x86.asm fs_observer_x86.asm');(out/'CMakeLists.txt').write_text(cmake)
 for name_ in ('mfc-import-bindings.json','mfc-raw-page.bin'):(out/name_).write_bytes(pin(OLD/name_).read_bytes())
 (out/'allocation-inputs.json').write_text(json.dumps(bindings,indent=2)+'\n');(out/'fs-hook-bindings.json').write_text(json.dumps([dict(PC=pc,kind=kind,raw_bytes=raw,continuation=pc+len(bytes.fromhex(raw)),declared_observer='fs_hook_'+format(pc,'x'))for pc,kind,raw in F.HOOKS],indent=2)+'\n')
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(__file__);pin(Path(F.__file__));report=dict(passed=True,scope='Additive genuine original109 worker preparation, transparent exact FS source MOV observers and true initial HeapAlloc backing; execution pending',order=rec['order'],observed_pages=observed,page_count=len(records),record_bytes=291456,pack_sha256=sha(out/'pages.bin'),source_spans=spans,parent_preparation=str(OLD),parent_sha256=sha(OLD/'report.json'),fs_event_record_bytes=1216,fs_events_per_sequence=21,fs_allocations_per_sequence=10,fs_allocations=bindings,mfc_bindings=old['mfc_bindings'],FS_previous_windows_chain_identity_preserved=True,guest_stack_observer_spills=False,allocation_source_frame_relation='MFC F = actual mode1 HeapAlloc frame A+104; authenticate all three original return words/size',true_API_initial_backing=True,source_cleanup='Actual original MFC825 once per ten new aliases and35 inherited owners;16 strings/registry; destructor callbacks stored only',per_phase_reseed=False,AFTER_machine_seed=False,original_executed=False,native_executed=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),pages=len(records),observed=len(observed))))
if __name__=='__main__':main(sys.argv[1])
