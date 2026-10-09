"""Fresh original28 hardware observer derivation; immutable original27 inputs."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup28-original'
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000)
CASES=((0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,s):
 if not ok:raise ValueError(s)
def main(name):
 out=BASE/name;need(not out.exists() and name.startswith('preparation-r'),'Fresh output');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);need(h is None or a==h,'Exact input '+str(p));pins[str(p)]=a;return p
 def read(rel):return pin(ROOT/rel).read_text(encoding='utf-8-sig')
 def replace(s,a,b):need(s.count(a)==1,'Unique derivation '+a[:80]);return s.replace(a,b)
 exdir=ROOT/'reports/m4-joint-startup27/original-extraction-r1';ex=json.loads(pin(exdir/'extraction.json').read_bytes());old=pin(exdir/'pages.bin',ex['pack_sha256']).read_bytes();need(old[:8]==b'MW4J27P1' and len(old)==12+26*4104,'Exact frozen27 pack')
 records=[(a,p,old[20+i*4104:4116+i*4104])for i in range(26)for a,p in [struct.unpack_from('<2I',old,12+i*4104)]]
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 def va(a,n):off,_=game.rva_range(a-game.image_base,n);return game.data[off:off+n]
 graph=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json').read_bytes())[str(0x482cf0)]
 code=bytearray(b'\xcc'*4096);spans=ex['bindings'].copy()
 for span in ((0x482cc0,41),(0x482cf0,5),(0x482d00,10)):
  a,n=span;off,_=game.rva_range(a-game.image_base,n);code[a&4095:(a&4095)+n]=va(a,n);spans.append(dict(pc=a,size=n,image_offset=off,origin=0))
 need(all(code[i['pc']&4095:(i['pc']&4095)+i['size']]==bytes.fromhex(i['bytes'])for i in graph['instructions']),'All22exact sourceinstructions')
 records.extend(((0x5e6000,0,va(0x5e6000,4096)),(0x608000,2,bytes(4096)),(0x482000,1,bytes(code))))
 entries={x['entry']for x in ex['order']}|{0x482cf0};order=[(0x5e0000+4*i,struct.unpack('<I',va(0x5e0000+4*i,4))[0])for i in range(145)if struct.unpack('<I',va(0x5e0000+4*i,4))[0]in entries];need(len(order)==28,'Actual original28 table order')
 pack=b'MW4J28P1'+struct.pack('<I',29)+b''.join(struct.pack('<2I',a,p)+b for a,p,b in records);(out/'pages.bin').write_bytes(pack)
 spec=read('reports/m4-joint-startup27/original-extraction-r1/spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{hashlib.sha256(pack).hexdigest()}"',spec);spec=re.sub(r'pack_size=\d+',f'pack_size={len(pack)}',spec)
 for n,values in (('entries',[e for s,e in order]),('table_slots',[s for s,e in order]),('page_bases',[a for a,p,b in records]),('page_permissions',[p for a,p,b in records])):
  spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+n+r'\{[^;]+;', 'inline constexpr std::array<std::uint32_t,'+str(len(values))+'> '+n+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;', 'inline constexpr std::array<CodeBinding,'+str(len(spans))+'> code_bindings{{'+','.join('{'+','.join(hex(x[k])for k in ('pc','size','image_offset','origin'))+'}'for x in spans)+'}};',spec)
 (out/'spec.hpp').write_text(spec)
 protocol=read('tools/m4-joint-startup27/original/protocol.hpp');protocol=protocol.replace('sequences=48, roots=27','sequences=6, roots=28').replace('observed_page_count=14','observed_page_count=17').replace('0x780c1000,0x78115000};','0x780c1000,0x78115000,0x5e6000,0x608000,0x482000};').replace('sizeof(Record)==117684','sizeof(Record)==143472').replace('memory_size==57344','memory_size==69632')
 service='struct Service {Cpu before,after;std::array<std::uint8_t,512> fx_before,fx_after;std::array<std::uint8_t,28> env_before,env_after;std::array<std::uint8_t,16> rect_before,rect_after;std::uint32_t called,BOOL_value,guest_cleanup,provider_ESP_before,provider_ESP_after;};\nstatic_assert(sizeof(Service)==1212);\n'
 protocol=replace(protocol,'struct Record {',service+'struct Record {');protocol=replace(protocol,'    std::uint32_t checkpoint_seen;','    std::uint32_t checkpoint_seen;\n    Service spi;');(out/'protocol.hpp').write_text(protocol)
 broker=read('tools/m4-joint-startup27/original/original_broker.hpp').replace('std::array<std::uint32_t,14>','std::array<std::uint32_t,15>').replace('0x460000,0x4a0000','0x460000,0x480000,0x4a0000');(out/'original_broker.hpp').write_text(broker)
 asm=read('tools/m4-joint-startup27/original/reference_x86.asm');oldspi=read('tools/m4-spi-workarea/reference_x86.asm');extern=oldspi[oldspi.index('EXTERN spi_service_before'):oldspi.index('PUBLIC spi_enter')];body=oldspi[oldspi.index('spi_service_entry PROC'):oldspi.index('spi_capture PROC')];body=body.replace('spi_host_esp','mixed_host_esp')
 body=replace(body,' push 0\n push 00608fa0h\n push 0\n push 30h',' mov eax,spi_service_esp\n push DWORD PTR [eax+16]\n push DWORD PTR [eax+12]\n push DWORD PTR [eax+8]\n push DWORD PTR [eax+4]')
 asm=replace(asm,'.code',extern+'PUBLIC spi_service_entry\n.code');asm=replace(asm,'\nEND\n','\n'+body+'END\n');(out/'reference_x86.asm').write_text(asm)
 ref=read('tools/m4-joint-startup27/original/reference.cpp');ref=replace(ref,'#include <memory>','#include <memory>\n#include "capture_direct_v3.hpp"')
 decl='Cpu spi_service_before{},spi_service_after{};\nstd::uint32_t spi_service_esp{},spi_actual_provider{},spi_resume{0x482ce3},spi_provider_esp_before{},spi_provider_esp_after{};\nalignas(16) std::uint8_t spi_service_fx_before[512]{},spi_service_fx_after[512]{};\nstd::uint8_t spi_service_env_before[28]{},spi_service_env_after[28]{},spi_service_rect_before[16]{},spi_service_rect_after[16]{};\nvoid spi_service_entry();\n'
 ref=replace(ref,'void mixed_enter();void mixed_capture();void mixed_restore();',decl+'void mixed_enter();void mixed_capture();void mixed_restore();')
 ref=replace(ref,'    std::array<void*,26> pages{};','    std::array<void*,29> pages{};')
 ref=ref.replace('"MW4J27P1"','"MW4J28P1"').replace('Connected original27','Connected original28')
 query='    auto user=LoadLibraryExW(L"user32.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);require(user!=nullptr,"System USER32 required");\n    auto proc=GetProcAddress(user,"SystemParametersInfoA");require(proc!=nullptr,"Actual SPI export required");spi_actual_provider=reinterpret_cast<std::uintptr_t>(proc);\n    std::array<wchar_t,32768> userpath{};const auto usern=GetModuleFileNameW(user,userpath.data(),static_cast<DWORD>(userpath.size()));require(usern&&usern<userpath.size(),"USER32 path extent");\n    const auto userdata=read(std::filesystem::path(userpath.data()).string().c_str(),8*1024*1024);require(sha256(userdata)=="'+sha(pin(Path('C:/Windows/SysWOW64/user32.dll')))+'","Actual USER32 identity");\n    *reinterpret_cast<unsigned*>(0x5bb6dc)=reinterpret_cast<std::uintptr_t>(&spi_service_entry);\n'
 ref=replace(ref,'    auto*stub=reinterpret_cast<std::uint8_t*>(capture_pc);',query+'    auto*stub=reinterpret_cast<std::uint8_t*>(capture_pc);')
 ref=replace(ref,'    Output out(argv[4]);Header header{};std::memcpy(header.magic,debugger?"MW4J27D1":"MW4J27O1",8);','    mw34::capture_direct::Writer out(argv[4]);Header header{};std::memcpy(header.magic,debugger?"MW4J28D1":"MW4J28O1",8);')
 ref=replace(ref,'header.record_size=sizeof(Record);out.write(header);','header.record_size=sizeof(Record);out.append("header.bin",&header,sizeof(header));\n    out.append("user32-image.bin",userdata.data(),userdata.size());out.append("user32-path.bin",userpath.data(),(usern+1)*sizeof(wchar_t));const std::array<unsigned,3> identity{reinterpret_cast<std::uintptr_t>(user),spi_actual_provider,0x5bb6dc};out.append("spi-identity.bin",identity.data(),sizeof(identity));')
 ref=replace(ref,'    for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:control_words)for(unsigned top:{0u,7u}){','    const std::array<std::array<unsigned,3>,6> cases{{'+','.join('{'+','.join(hex(v)for v in c)+'}'for c in CASES)+'}};\n    for(const auto& test:cases){const auto repeat=test[0],cw=test[1],top=test[2];')
 ref=replace(ref,'std::memcpy(mixed_guest_fx,&cw,2);','const auto cw16=static_cast<std::uint16_t>(cw);std::memcpy(mixed_guest_fx,&cw16,2);')
 ref=replace(ref,'            r->tag.status=execute();','            spi_service_before={};spi_service_after={};spi_service_esp=spi_provider_esp_before=spi_provider_esp_after=0;\n            std::memset(spi_service_fx_before,0,512);std::memset(spi_service_fx_after,0,512);std::memset(spi_service_env_before,0,28);std::memset(spi_service_env_after,0,28);std::memset(spi_service_rect_before,0,16);std::memset(spi_service_rect_after,0,16);\n            r->tag.status=execute();')
 append='r->spi.before=spi_service_before;r->spi.after=spi_service_after;std::memcpy(r->spi.fx_before.data(),spi_service_fx_before,512);std::memcpy(r->spi.fx_after.data(),spi_service_fx_after,512);std::memcpy(r->spi.env_before.data(),spi_service_env_before,28);std::memcpy(r->spi.env_after.data(),spi_service_env_after,28);std::memcpy(r->spi.rect_before.data(),spi_service_rect_before,16);std::memcpy(r->spi.rect_after.data(),spi_service_rect_after,16);r->spi.called=spi_service_after.pc==0x482ce3;r->spi.BOOL_value=spi_service_after.eax;r->spi.guest_cleanup=r->spi.called?16:0;r->spi.provider_ESP_before=spi_provider_esp_before;r->spi.provider_ESP_after=spi_provider_esp_after;\n            require(entries[phase]!=0x482cf0||(r->spi.called&&spi_provider_esp_before+20==spi_provider_esp_after&&r->spi.before.esp==frame-32&&r->spi.after.esp==frame-12),"Actual SPI stdcall16 witness");\n            out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+".bin",r.get(),sizeof(*r));'
 ref=replace(ref,'r->checkpoint_seen=checkpoint_seen;out.write(*r);','r->checkpoint_seen=checkpoint_seen;'+append)
 ref=ref.replace('out.commit();','out.finish();').replace('48 connected sequences / 1296 actual original initializer phases captured','6 connected sequences / 168 actual original initializer phases captured')
 ref=replace(ref,'pc>=capture_pc&&pc<capture_pc+5?broker_bytes[pc-capture_pc]:expected[byte]','pc>=capture_pc&&pc<capture_pc+5?broker_bytes[pc-capture_pc]:pc>=0x5bb6dc&&pc<0x5bb6e0?reinterpret_cast<const std::uint8_t*>(&spi_service_entry)[0]:expected[byte]')
 # IAT is an observer relocation; validate its full pointer separately instead of conflating executable bytes.
 ref=ref.replace('            require(actual[byte]==(','            if(pc>=0x5bb6dc&&pc<0x5bb6e0)continue;\n            require(actual[byte]==(')
 ref=replace(ref,'    out.finish();std::cout','    require(*reinterpret_cast<unsigned*>(0x5bb6dc)==reinterpret_cast<std::uintptr_t>(&spi_service_entry),"SPI owning IAT unchanged");out.append("COMPLETE.txt","complete",8);\n    out.finish();std::cout')
 (out/'reference.cpp').write_text(ref)
 cmake=read('tools/m4-joint-startup27/original/CMakeLists.txt').replace('Startup27','Startup28').replace('startup27','startup28').replace('reference.cpp reference_x86.asm','reference.cpp reference_x86.asm preserve_x86.asm "${MW34_WRITER_SOURCE}"').replace('"${MW34_ORIGINAL_INCLUDE}"','"${MW34_ORIGINAL_INCLUDE}" "${MW34_WRITER_INCLUDE}"');(out/'CMakeLists.txt').write_text(cmake)
 (out/'preserve_x86.asm').write_text(PRESERVE)
 for p in (Path(__file__),Path(sys.executable),ROOT/'tools/m4-capture-direct/capture_direct_v3.hpp',ROOT/'tools/m4-capture-direct/capture_direct_v3.cpp'):pin(p)
 for p in out.iterdir():
  if p.is_file():pin(p)
 report=dict(passed=True,scope='Fresh original28 observer preparation only; exact original27 prefix; actual SPI routing; no execution credit',order=[dict(slot=s,entry=e)for s,e in order],cases=CASES,observed_pages=PAGES,page_records=29,record_size=143472,Common_size=141540,service_size=1212,pack_sha256=sha(out/'pages.bin'),source_spans=spans,owning_IAT_relocations=[dict(address=0x5bb4fc,actual=0x780c10f0),dict(address=0x5bb6dc,actual='typed actual32SPI import observer shim')],files=pins,original_State_not_observed=True,original_accesses_not_observed=True,original_executed=False,native_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),SPI_phase=next(i for i,x in enumerate(order)if x[1]==0x482cf0))))
PRESERVE='''.686p
.xmm
.model flat,C
option casemap:none
PUBLIC mw34_capture_preserved_call
PUBLIC mw34_capture_save
PUBLIC mw34_capture_restore
.code
mw34_capture_preserved_call PROC
 pushfd
 pushad
 mov ebp,esp
 sub esp,576
 and esp,0fffffff0h
 fxsave [esp]
 fnstenv [esp+512]
 mov DWORD PTR [esp+544],01f80h
 fninit
 ldmxcsr [esp+544]
 cld
 mov eax,DWORD PTR [ebp+40]
 push DWORD PTR [ebp+44]
 call eax
 add esp,4
 fxrstor [esp]
 fldenv [esp+512]
 mov esp,ebp
 popad
 popfd
 ret
mw34_capture_preserved_call ENDP
mw34_capture_save PROC
 mov eax,DWORD PTR [esp+4]
 fxsave [eax]
 fnstenv [eax+512]
 fldenv [eax+512]
 ret
mw34_capture_save ENDP
mw34_capture_restore PROC
 mov eax,DWORD PTR [esp+4]
 fxrstor [eax]
 fldenv [eax+512]
 ret
mw34_capture_restore ENDP
END
'''
if __name__=='__main__':
 import re
 main(sys.argv[1])
