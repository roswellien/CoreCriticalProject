"""Authentic mixed original prefix; no supplied outputs, allocation counts or backing bytes."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OLD=ROOT/'reports/m4-formatting-original/prefix-preparation-r3';SRC=ROOT/'reports/m4-mixed-format-original/recovery-r1';BASE=ROOT/'reports/m4-mixed-format-original'
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(s,a,b):
 need(s.count(a)==1,'Exact source derivation anchor '+a[:90]);return s.replace(a,b,1)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh additive preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No inherited capture reader');v=sha(p);need(h is None or h==v,'Physical source '+str(p));pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json','6a41ecc0684a7440b05bad9ff1eb78470422c2ae95d5b3d636d1b7ee1da41138').read_bytes());src=json.loads(pin(SRC/'report.json','5627b4234b16f5bdb493f4102f541166cbf8bde11c53c3b9a691a24d1230e5fa').read_bytes())
 for parent in(old,src):
  for p,h in parent['files'].items():pin(p,h)
 contract=json.loads(pin(SRC/'instruction-contracts.json').read_bytes());game=PEImage(pin(ROOT/'MW3/Mech3.exe').read_bytes());raw=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',raw,8)[0])};spans=list(old['source_spans']);known={r['pc']:r for r in spans}
 for r in contract['instructions']:
  pc=r['pc'];code=bytes.fromhex(r['bytes_hex']);offset,_=game.rva_range(pc-game.image_base,len(code));need(game.data[offset:offset+len(code)]==code,'Every exact mixed source byte')
  if pc in known:need(known[pc]['size']==len(code)and known[pc]['image_offset']==offset,'Shared source exact agreement');continue
  page=pc&~4095
  if page not in records:records[page]=(1,bytearray(b'\xcc'*4096))
  records[page][1][pc&4095:(pc&4095)+len(code)]=code;spans.append(dict(pc=pc,size=len(code),image_offset=offset,origin=0));known[pc]=spans[-1]
 out.mkdir(parents=True);pack=b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,permission)+data for p,(permission,data)in records.items());(out/'pages.bin').write_bytes(pack)
 spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
 for field,values in [('entries',[0x4e1ca0]),('table_slots',[0x5e01d4]),('page_bases',list(records)),('page_permissions',[p for p,d in records.values()])]:spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(r[k])for k in('pc','size','image_offset','origin'))+'}'for r in spans)+'}};',spec)
 spec=one(spec,'std::array<LockitRoot,4>lockit_roots','std::array<LockitRoot,5>lockit_roots');spec=one(spec,'{0x5968f0,0x731868,0x731894,0x731898,0x18}}};','{0x5968f0,0x731868,0x731894,0x731898,0x18},{0x4e1ca0,0x60b668,0x60b7d4,0x60b7d0,0x18}}};');(out/'spec.hpp').write_text(spec)
 (out/'protocol.hpp').write_text(one(text(OLD/'protocol.hpp'),'sequences=1, roots=3','sequences=1, roots=1'))
 broker=text(OLD/'original_broker.hpp');bases=list(dict.fromkeys([int(v,16)for v in re.search(r'bases\{([^;]+)\};',broker)[1].split(',')]+[p&~65535 for p in records]));broker=re.sub(r'std::array<std::uint32_t,\d+> bases\{[^;]+;',f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(v)for v in bases)+'};',broker);(out/'original_broker.hpp').write_text(broker)
 ref=text(OLD/'reference.cpp');ref=re.sub(r'std::array<void\*,\d+> pages',f'std::array<void*,{len(records)}> pages',ref)
 newhooks=[(f[k],kind,'64a100000000'if kind==0 else'64892500000000'if kind==1 else'64890d00000000')for f in contract['FS_frame_contracts']for k,kind in [('read',0),('install',1),('restore',2)]]
 oldhooks=json.loads(pin(OLD/'fs-hook-bindings.json').read_bytes());allhooks=[(x['PC'],x['kind'],x['raw_bytes'])for x in oldhooks]+newhooks
 p=pin(ROOT/'tools/m4-fs-source/fs_hooks_v2.py');s=importlib.util.spec_from_file_location('mixed_fs_generator',p);fs=importlib.util.module_from_spec(s);s.loader.exec_module(fs)
 fs.HOOKS=newhooks;ref=one(ref,'struct FsHook{',fs.declarations()+'struct FsHook{');fs.HOOKS=allhooks;table=fs.hook_table().replace('FsHook,9>','FsHook,'+str(len(allhooks))+'>');ref,n=re.subn(r'struct FsHook\{[^\n]+\nconst std::array<FsHook,45> fs_hooks\{\{[^;]+;',lambda m:table.rstrip(),ref);need(n==1,'Exact enlarged FS hook inventory');(out/'fs_observer_x86.asm').write_text(fs.asm());(out/'fs-hook-bindings.json').write_text(json.dumps([dict(PC=pc,kind=k,raw_bytes=b,continuation=pc+len(bytes.fromhex(b)),declared_observer=f'fs_hook_{pc:x}')for pc,k,b in allhooks],indent=2)+'\n')
 ref=one(ref,'void lockit_observe_allocation(unsigned,unsigned,unsigned);','void lockit_observe_allocation(unsigned,unsigned,unsigned);\nvoid mixed_observe_allocation(unsigned,unsigned,unsigned);')
 ref=one(ref,'lockit_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));','lockit_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));mixed_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));')
 implementation='''
struct MixedAllocation{unsigned version,index,root,CALL_pc,request,source_frame,API_index,pointer,capacity;unsigned frame32[8];};
static_assert(sizeof(MixedAllocation)==68);MixedAllocation mixed_allocations[8]{};unsigned mixed_allocation_count{};
void mixed_observe_allocation(unsigned ai,unsigned pointer,unsigned capacity){
 if(fs_phase_root!=0x4e1ca0||registry_API_kind!=0||!pointer)return;const auto A=registry_API_before.esp,F=A+104;
 if(A<0x20001000||F+32>0x20002000){fs_error=1;return;}const auto ret=*reinterpret_cast<unsigned*>(F);
 for(const auto pc:{0x49cc8du,0x4e5325u,0x4e535bu})if(ret==pc+5){
  if(mixed_allocation_count>=8||*reinterpret_cast<unsigned*>(A)!=0x78001385||*reinterpret_cast<unsigned*>(A+80)!=0x5f401eb7){fs_error=1;return;}
  auto&e=mixed_allocations[mixed_allocation_count];e={};e.version=1;e.index=mixed_allocation_count++;e.root=fs_phase_root;e.CALL_pc=pc;e.request=*reinterpret_cast<unsigned*>(F+4);e.source_frame=F;e.API_index=ai;e.pointer=pointer;e.capacity=capacity;std::memcpy(e.frame32,reinterpret_cast<void*>(F),32);return;
 }
}
'''
 ref=one(ref,'#include "format_observer.hpp"',implementation+'\n#include "format_observer.hpp"')
 ref=one(ref,'format_count=0;format_active_owner=0xffffffff;','mixed_allocation_count=0;std::memset(mixed_allocations,0,sizeof(mixed_allocations));format_count=0;format_active_owner=0xffffffff;')
 ref=one(ref,'o.words[2]==0x4df610?0x60b5e0:o.words[2]==0x4e0710?0x60b630:0x60b608','o.words[2]==0x4e1ca0?0x60b668:o.words[2]==0x4df610?0x60b5e0:o.words[2]==0x4e0710?0x60b630:0x60b608')
 dump='''            const auto mixed_stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/mixed/";out.append(mixed_stem+"owner-count.bin",&mixed_allocation_count,4);
            for(unsigned i=0;i<mixed_allocation_count;++i){const auto&a=mixed_allocations[i];const auto stem=mixed_stem+"owner/"+std::to_string(i);require(HeapSize(reinterpret_cast<HANDLE>(registry_API_ledger[a.API_index].args[0]),0,reinterpret_cast<void*>(a.pointer))==a.capacity,"Actual mixed full backing persists");out.append(stem+"/meta.bin",&a,sizeof(a));out.append(stem+"/initial.bin",registry_initial_bytes[a.API_index],a.capacity);out.append(stem+"/bytes.bin",reinterpret_cast<void*>(a.pointer),a.capacity);}
'''
 ref=one(ref,'            const auto format_stem=',dump+'            const auto format_stem=')
 ref=one(ref,'require(*crtnext-*crtbegin==3*4,"Actual three callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),3*4);','require(*crtnext-*crtbegin==1*4,"Actual mixed one callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),1*4);')
 cleanup='''        out.append("cleanup/mixed-owner-count.bin",&mixed_allocation_count,4);for(unsigned i=0;i<mixed_allocation_count;++i){const auto&a=mixed_allocations[i];const auto stem="cleanup/mixed/"+std::to_string(i);out.append(stem+"/meta.bin",&a,sizeof(a));out.append(stem+"/before.bin",reinterpret_cast<void*>(a.pointer),a.capacity);mfc825(reinterpret_cast<void*>(a.pointer));const unsigned returned=1;out.append(stem+"/returned.bin",&returned,4);}
'''
 ref=one(ref,'        out.append("cleanup/formatting-owner-count.bin"',cleanup+'        out.append("cleanup/formatting-owner-count.bin"')
 ref=ref.replace('Three genuine formatting prefixes measured; literal CRT narrow formatting proof remains open','One genuine mixed formatting prefix measured; literal source/native acceptance remains open');(out/'reference.cpp').write_text(ref)
 for fn in('reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','format_observer.hpp','format_observer_x86.asm','CMakeLists.txt'):(out/fn).write_text(text(OLD/fn))
 pin(__file__)
 for p in out.iterdir():pin(p)
 report=dict(passed=True,scope='Genuine bounded mixed original prefix preparation using untouched physical defaults and authentic CRT/CP/MFC DllMain state',source_recovery_sha256=sha(SRC/'report.json'),parent_preparation_sha256=sha(OLD/'report.json'),source_spans=spans,pack_sha256=sha(out/'pages.bin'),observed_pages=old['observed_pages'],extra_whole_source_pages=old['extra_whole_source_pages'],original_sequences=1,original_phases=1,record_bytes=356992,format_event_bytes=2244,format_owner_bytes=1088,mixed_owner_meta_bytes=68,format_observer_bound=64,format_owner_bound=16,mixed_owner_bound=8,source_instruction_rows=348,FS_hooks=len(allhooks),predicted_counts_supplied_to_execution=False,source_output_seed=False,native_executed=False,initializer_credit=False,inherited_capture_reader_opened=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),pages=len(records))))
if __name__=='__main__':main(sys.argv[1])
