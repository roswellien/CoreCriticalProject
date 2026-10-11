"""Fresh three-root original measurement; genuine inherited loader, no native or AFTER seeds."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OLD=ROOT/'reports/m4-lockit-original/original-preparation-r4';SRC=ROOT/'reports/m4-formatting-frontier/recovery-r1';BASE=ROOT/'reports/m4-formatting-original'
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
from observer import assembly
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(s,a,b):
 need(s.count(a)==1,'One exact source edit '+a[:70]);return s.replace(a,b,1)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh additive original formatting preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No inherited payload reader');v=sha(p);need(h is None or h==v,'Exact source '+str(p));pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json','6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b').read_bytes());src=json.loads(pin(SRC/'report.json','8a2c511e47eddce2cab0929b9ede59e81276957ace6e2926b38c5323325dca15').read_bytes())
 for parent in(old,src):
  for p,h in parent['files'].items():pin(p,h)
 contract=json.loads(pin(SRC/'instruction-contracts.json').read_bytes());roots=json.loads(pin(SRC/'roots.json').read_bytes());need(len(contract['instructions'])==199 and len(roots)==3,'Exact game graph')
 game=PEImage(pin(ROOT/'MW3/Mech3.exe').read_bytes());raw=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes()
 records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',raw,8)[0])}
 spans=list(old['source_spans']);known={r['pc']:r for r in spans}
 for r in contract['instructions']:
  pc=r['pc'];code=bytes.fromhex(r['bytes_hex']);offset,_=game.rva_range(pc-game.image_base,len(code));need(game.data[offset:offset+len(code)]==code,'Physical source bytes')
  if pc in known:need(known[pc]['size']==len(code) and known[pc]['image_offset']==offset,'Shared code agreement');continue
  page=pc&~4095
  if page not in records:records[page]=(1,bytearray(b'\xcc'*4096))
  records[page][1][pc&4095:(pc&4095)+len(code)]=code;spans.append(dict(pc=pc,size=len(code),image_offset=offset,origin=0));known[pc]=spans[-1]
 extra=[0x5cd000,0x5e3000,0x5e9000]
 for page in extra:
  need(page not in records,'New whole asset page');records[page]=(0,bytearray(pin(SRC/f'game-{page:08x}-raw-page.bin').read_bytes()));need(len(records[page][1])==4096,'Whole raw source page')
 out.mkdir(parents=True);pack=b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,permission)+data for p,(permission,data)in records.items());(out/'pages.bin').write_bytes(pack)
 spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
 for field,values in [('entries',[r['entry']for r in roots]),('table_slots',[r['slot']for r in roots]),('page_bases',list(records)),('page_permissions',[p for p,d in records.values()])]:spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(r[k])for k in('pc','size','image_offset','origin'))+'}'for r in spans)+'}};',spec);(out/'spec.hpp').write_text(spec)
 (out/'protocol.hpp').write_text(text(OLD/'protocol.hpp').replace('sequences=6, roots=124','sequences=1, roots=3'))
 broker=text(OLD/'original_broker.hpp');bases=list(dict.fromkeys([int(v,16)for v in re.search(r'bases\{([^;]+)\};',broker)[1].split(',')]+[p&~65535 for p in records]));broker=re.sub(r'std::array<std::uint32_t,\d+> bases\{[^;]+;',f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(v)for v in bases)+'};',broker);(out/'original_broker.hpp').write_text(broker)
 ref=text(OLD/'reference.cpp');ref=re.sub(r'std::array<void\*,118> pages',f'std::array<void*,{len(records)}> pages',ref)
 ref=one(ref,'const std::array<std::array<unsigned,3>,6> cases{{{0x0,0x7f,0x0},{0x0,0x37f,0x7},{0x0,0xf7f,0x0},{0x1,0x47f,0x7},{0x1,0xa7f,0x0},{0x1,0xe7f,0x7}}};','const std::array<std::array<unsigned,3>,1> cases{{{0,0x7f,0}}};')
 marker='static std::uint32_t execute()';ref=one(ref,marker,'#include "format_observer.hpp"\n'+marker)
 marker='unsigned sequence{};'
 if marker not in ref:marker='    unsigned sequence=0;'
 need(marker in ref,'Sequence declaration anchor')
 # Preserve the exact declared named source targets and separate hook identities.
 setup='''    const std::array<unsigned,3> format_iats{0x5bb5a8,0x5bb664,0x5bb658};const std::array<const char*,3> format_names{"strrchr","malloc","sprintf"};const std::array<void(*)(),3> format_entries{&format_entry_strrchr,&format_entry_malloc,&format_entry_sprintf};
    for(unsigned i=0;i<3;++i){format_targets[i]=reinterpret_cast<unsigned>(GetProcAddress(crt,format_names[i]));require(format_targets[i]==(i==0?0x780264a9u:i==1?0x780012b3u:0x78022b9au),"Exact named formatting CRT exports");DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(format_iats[i]),4,PAGE_READWRITE,&prior),"Format source IAT protect");*reinterpret_cast<unsigned*>(format_iats[i])=reinterpret_cast<unsigned>(format_entries[i]);require(VirtualProtect(reinterpret_cast<void*>(format_iats[i]),4,prior,&ignored),"Format source IAT protection restore");}
    for(const auto&hook:format_hooks){auto*code=reinterpret_cast<unsigned char*>(hook.pc);require(!std::memcmp(code,hook.raw,hook.size),"Exact formatting caller return span");DWORD prior{},ignored{};require(VirtualProtect(code,hook.size,PAGE_EXECUTE_READWRITE,&prior),"Format source span protect");code[0]=0xe9;const unsigned d=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&d,4);for(unsigned n=5;n<hook.size;++n)code[n]=0x90;require(VirtualProtect(code,hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),code,hook.size),"Format source span restore");}
    const std::array<unsigned,3> format_extra_pages{0x5cd000,0x5e3000,0x5e9000};
    out.append("formatting/import-targets.bin",format_targets,sizeof(format_targets));
'''
 ref=one(ref,marker,setup+marker)
 before='''            format_count=0;format_active_owner=0xffffffff;std::memset(format_snapshots,0,sizeof(format_snapshots));
            for(auto page:format_extra_pages)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/extra-before/"+std::to_string(page)+".bin",reinterpret_cast<void*>(page),4096);
'''
 ref=one(ref,'            r->tag.status=execute();',before+'            r->tag.status=execute();')
 marker='            const auto mfcbase=';start=ref.index(marker);end=ref.index('            const auto lockbase=',start);ref=ref[:start]+ref[end:]
 start=ref.index('            const auto stringbase=');end=ref.index('            out.append("phase/"',start);ref=ref[:start]+ref[end:]
 marker='            const auto lockbase='
 after='''            const auto format_stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/formatting/";
            out.append(format_stem+"count.bin",&format_count,4);out.append(format_stem+"events.bin",format_snapshots,format_count*sizeof(FormatSnapshot));out.append(format_stem+"owner-count.bin",&format_owner_count,4);
            for(unsigned i=0;i<format_owner_count;++i){const auto&o=format_owners[i];const auto cap=HeapSize(reinterpret_cast<HANDLE>(o.words[8]),0,reinterpret_cast<void*>(o.words[5]));require(cap==o.words[6],"Actual formatting backing persists");const unsigned object=o.words[2]==0x4df610?0x60b5e0:o.words[2]==0x4e0710?0x60b630:0x60b608;require(*reinterpret_cast<unsigned*>(object+4)==o.words[5],"Actual source published formatting owner");out.append(format_stem+"owner/"+std::to_string(i)+"/meta.bin",o.words,sizeof(o.words));out.append(format_stem+"owner/"+std::to_string(i)+"/initial.bin",o.initial,o.words[6]);out.append(format_stem+"owner/"+std::to_string(i)+"/bytes.bin",reinterpret_cast<void*>(o.words[5]),o.words[6]);}
            for(auto page:format_extra_pages)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/extra-after/"+std::to_string(page)+".bin",reinterpret_cast<void*>(page),4096);
'''
 ref=one(ref,marker,after+marker)
 # Exact source bytes restored before existing full-source/protected-page conservation checks.
 marker='        for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;bool hooked=false;'
 restore='''        for(const auto&hook:format_hooks){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,PAGE_EXECUTE_READWRITE,&prior),"Restore actual formatting return source");std::memcpy(reinterpret_cast<void*>(hook.pc),hook.raw,hook.size);require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(hook.pc),hook.size),"Formatting source restored");}
        for(unsigned i=0;i<3;++i){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(format_iats[i]),4,PAGE_READWRITE,&prior),"Restore formatting named source IAT");*reinterpret_cast<unsigned*>(format_iats[i])=format_targets[i];require(VirtualProtect(reinterpret_cast<void*>(format_iats[i]),4,prior,&ignored),"Formatting IAT restore protection");}
'''
 ref=one(ref,marker,restore+marker)
 ref=one(ref,'require(*crtnext-*crtbegin==96*4,"Exact96callback vectorextent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),96*4);','require(*crtnext-*crtbegin==3*4,"Actual three callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),3*4);')
 start=ref.index('        require(lockit_allocation_count==8,');end=ref.index('original_free(reinterpret_cast<void*>(*crtbegin));',start)
 cleanup='''        require(!lockit_allocation_count&&!container_allocation_count&&!fs_allocation_count,"No unrelated observed owners in formatting prefix");
        out.append("cleanup/formatting-owner-count.bin",&format_owner_count,4);
        for(unsigned i=0;i<format_owner_count;++i){const auto&o=format_owners[i];const auto stem="cleanup/formatting/"+std::to_string(i);out.append(stem+"/meta.bin",o.words,sizeof(o.words));out.append(stem+"/before.bin",reinterpret_cast<void*>(o.words[5]),o.words[6]);original_free(reinterpret_cast<void*>(o.words[5]));const unsigned returned=1;out.append(stem+"/returned.bin",&returned,4);}
        '''
 ref=ref[:start]+cleanup+ref[end:]
 ref=one(ref,'if((pc>=0x5bb6dc','if((pc>=0x5bb5a8&&pc<0x5bb5ac)||(pc>=0x5bb658&&pc<0x5bb65c)||(pc>=0x5bb664&&pc<0x5bb668)||(pc>=0x5bb6dc')
 ref=ref.replace('6 connected sequences /744 actual original initializer phases captured; full ledger and native equivalence remain open','Three genuine formatting prefixes measured; literal CRT narrow formatting proof remains open');(out/'reference.cpp').write_text(ref)
 for fn in('reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','fs_observer_x86.asm','fs-hook-bindings.json'):(out/fn).write_text(text(OLD/fn))
 (out/'format_observer.hpp').write_text(text(Path(__file__).parent/'format_observer.hpp'));(out/'format_observer_x86.asm').write_text(assembly());(out/'CMakeLists.txt').write_text(text(OLD/'CMakeLists.txt').replace(' lockit_observer_x86.asm',' lockit_observer_x86.asm format_observer_x86.asm'))
 pin(__file__);pin(Path(__file__).parent/'observer.py')
 for p in out.iterdir():pin(p)
 report=dict(passed=True,scope='Genuine three-root original formatting measurement, untouched BEFORE and full source string/allocation/caller-return observations; no native integration or formatter breadth claim',source_recovery_sha256=sha(SRC/'report.json'),parent_preparation_sha256=sha(OLD/'report.json'),source_spans=spans,pack_sha256=sha(out/'pages.bin'),observed_pages=old['observed_pages'],extra_whole_source_pages=extra,original_sequences=1,original_phases=3,record_bytes=356992,format_event_bytes=2244,format_owner_bytes=1088,format_observer_bound=64,format_owner_bound=16,source_instruction_rows=199,predicted_counts_supplied_to_execution=False,source_output_seed=False,native_executed=False,initializer_credit=False,inherited_capture_reader_opened=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),pages=len(records))))
if __name__=='__main__':main(sys.argv[1])
