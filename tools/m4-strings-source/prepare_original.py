"""Fresh original71, actual32 CRT string/registration execution and owner records."""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-strings-source';OLD=ROOT/'reports/m4-onexit-source/original-preparation-r8';REC=BASE/'recovery-r7'
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def one(s,a,b):need(s.count(a)==1,'Unique additive source '+a[:60]);return s.replace(a,b)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original71 preparation');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Pinned originalinput '+str(p));files[str(p)]=v;return p
 def read(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json').read_bytes());rec=json.loads(pin(REC/'report.json','972ec961d7617d2e7b789d23ab1ce82da0c33424b37c12e2dc94c23d1e154341').read_bytes());order=rec['order'];roots=rec['roots'];graphs=json.loads(pin(REC/'game-new-graphs.json').read_bytes())
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());oldpack=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',oldpack,12+i*4104)[0]:(struct.unpack_from('<I',oldpack,16+i*4104)[0],bytearray(oldpack[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',oldpack,8)[0])}
 provenance=[]
 for base in rec['data_pages']:
  if base in records:continue
  raw=bytearray(4096);pieces=[];permission=0
  for s in game.sections:
   a=game.image_base+s['virtual_address'];lo=max(base,a);hi=min(base+4096,a+s['raw_size'])
   if lo<hi:
    off=s['raw_offset']+lo-a;raw[lo-base:hi-base]=game.data[off:off+hi-lo];pieces.append(dict(section=s['name'],address=lo,size=hi-lo,file_offset=off))
   if max(base,a)<min(base+4096,a+max(s['virtual_size'],s['raw_size']))and s['writable']:permission=2
  records[base]=(permission,raw);provenance.append(dict(base=base,raw_pieces=pieces,zero_fill_bytes=4096-sum(p['size']for p in pieces),sha256=hashlib.sha256(raw).hexdigest()))
 oldspec=read(OLD/'spec.hpp');bindings=re.search(r'code_bindings\{\{([^;]+)\}\};',oldspec);need(bindings,'Frozen original sourcebindings')
 spans=[dict(zip(('pc','size','image_offset','origin'),map(lambda x:int(x,16),m)))for m in re.findall(r'\{(0x[0-9a-f]+),(0x[0-9a-f]+),(0x[0-9a-f]+),(0x[0-9a-f]+)\}',bindings[1])];need(spans,'Actual sourcebindings')
 rows={r['pc']:r for g in graphs.values()for r in g['instructions']}
 for r in rows.values():
  a=r['pc'];base=a&~4095;raw=bytes.fromhex(r['bytes']);off,_=game.rva_range(a-game.image_base,len(raw));need(game.data[off:off+len(raw)]==raw,'Every exact added row')
  if base not in records:records[base]=(1,bytearray(b'\xcc'*4096))
  records[base][1][a&4095:(a&4095)+len(raw)]=raw;spans.append(dict(pc=a,size=len(raw),image_offset=off,origin=0))
 addresses=list(records);observed=old['observed_pages']+[a for a in rec['data_pages']if a not in old['observed_pages']];need(len(observed)==32,'29 prior +3stringdata pages')
 pack=b'MW4J71P1'+struct.pack('<I',len(addresses))+b''.join(struct.pack('<2I',a,p)+raw for a,(p,raw)in records.items());(out/'pages.bin').write_bytes(pack)
 spec=read(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{sha(out/"pages.bin")}"',spec);spec=re.sub(r'pack_size=\d+',f'pack_size={len(pack)}',spec)
 for n,values in (('entries',[r['entry']for r in order]),('table_slots',[r['slot']for r in order]),('page_bases',addresses),('page_permissions',[p for p,b in records.values()])):
  spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+n+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+n+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(x[k])for k in('pc','size','image_offset','origin'))+'}'for x in spans)+'}};',spec)
 stringrows=[]
 for r in roots:
  need(len(r['objects'])==1,'Single fixed constructor object')
  stringrows.append(dict(entry=r['entry'],source=r['string']['source'],field=r['objects'][0]['address']+(0 if r['entry']==0x4e6a10 else 4),size=r['string']['size']))
 spec+='\nstruct StringBinding {unsigned entry,source,field,size;};\ninline constexpr std::array<StringBinding,17> string_bindings{{'+','.join('{'+','.join(hex(r[k])for k in('entry','source','field','size'))+'}'for r in stringrows)+'}};\n';(out/'spec.hpp').write_text(spec)
 protocol=read(OLD/'protocol.hpp').replace('roots=54','roots=71').replace('observed_page_count=29','observed_page_count=32').replace('sizeof(Record)==242304','sizeof(Record)==266880').replace('memory_size==118784','memory_size==131072');protocol=one(protocol,'0x9a1000};','0x9a1000,0x5e4000,0x5e5000,0x5e7000};');(out/'protocol.hpp').write_text(protocol)
 broker=read(OLD/'original_broker.hpp');m=re.search(r'std::array<std::uint32_t,\d+> bases\{([^;]+)\};',broker);need(m,'Brokerbaseinventory');bases=list(dict.fromkeys([int(x,16)for x in m[1].split(',')]+[a&~65535 for a in addresses]));broker=broker[:m.start()]+f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(a)for a in bases)+'};'+broker[m.end():];(out/'original_broker.hpp').write_text(broker)
 asm=read(OLD/'reference_x86.asm');asm=one(asm,'EXTERN registry_API_count:DWORD','EXTERN registry_API_count:DWORD\nEXTERN registry_API_ledger:BYTE')
 collect=''' mov eax,registry_API_count
 dec eax
 imul eax,eax,104
 lea edi,registry_API_ledger[eax]
 mov esi,OFFSET registry_API_before
 mov ecx,10
 cld
 rep movsd
 mov esi,OFFSET registry_API_after
 mov ecx,10
 rep movsd
 mov esi,OFFSET registry_API_args
 mov ecx,4
 rep movsd
 mov eax,registry_API_kind
 stosd
 mov eax,registry_API_ret
 stosd'''
 asm=one(asm,' mov DWORD PTR registry_API_after[16],edx',' mov DWORD PTR registry_API_after[16],edx\n'+collect);(out/'reference_x86.asm').write_text(asm)
 ref=read(OLD/'reference.cpp').replace('MW4J54','MW4J71').replace('Original54','Original71').replace('original54','original71').replace('Connected original54','Connected original71');ref=re.sub(r'std::array<void\*,65> pages',f'std::array<void*,{len(addresses)}> pages',ref)
 ref=one(ref,'std::uint32_t registry_API_active{},registry_API_entry_ecx{};','std::uint32_t registry_API_active{},registry_API_entry_ecx{};\nstruct RegistryAPIEntry {Cpu before,after;std::uint32_t args[4],kind,ret;};\nstatic_assert(sizeof(RegistryAPIEntry)==104);\nRegistryAPIEntry registry_API_ledger[32]{};')
 ref=one(ref,'    auto*crtbegin=', '    auto original_strdup=GetProcAddress(crt,"_strdup");require(reinterpret_cast<std::uintptr_t>(original_strdup)==0x78010a6d,"Actual32_strdup export identity");*reinterpret_cast<unsigned*>(0x5bb670)=reinterpret_cast<std::uintptr_t>(original_strdup);\n    auto*crtbegin=')
 ref=one(ref,'            registry_API_count=0;','            registry_API_count=0;std::memset(registry_API_ledger,0,sizeof(registry_API_ledger));')
 ref=one(ref,'            out.append("phase/"','''            require(registry_API_count<=32,"Bounded actualAPI ledger");out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/api-count.bin",&registry_API_count,4);out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/api-ledger.bin",registry_API_ledger,registry_API_count*sizeof(RegistryAPIEntry));
            const auto stringbase="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/strings/";
            for(const auto&binding:string_bindings){if(binding.entry>entries[phase])continue;const auto pointer=*reinterpret_cast<unsigned*>(binding.field);if(!pointer)continue;const auto cap=HeapSize(actual_heap,0,reinterpret_cast<void*>(pointer));require(cap!=SIZE_T(-1)&&cap>=binding.size&&cap<=512,"Actual bounded live duplicatedallocation");const std::array<unsigned,6> meta{binding.entry,binding.source,binding.field,pointer,binding.size,static_cast<unsigned>(cap)};out.append(stringbase+std::to_string(binding.entry)+"/meta.bin",meta.data(),sizeof(meta));out.append(stringbase+std::to_string(binding.entry)+"/bytes.bin",reinterpret_cast<void*>(pointer),cap);}
            out.append("phase/"''')
 # Both families register callbacks; keep duplicated allocation live through
 # all selected roots, then use the genuine original free before registryfree.
 ref=one(ref,'require(*crtnext-*crtbegin==26*4,"Exact26callback vectorextent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),26*4);','require(*crtnext-*crtbegin==43*4,"Exact43callback vectorextent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),43*4);')
 ref=one(ref,'registry_cleanup.restore();original_free(reinterpret_cast<void*>(*crtbegin));','''registry_cleanup.restore();for(const auto&binding:string_bindings){const auto pointer=*reinterpret_cast<unsigned*>(binding.field);require(binding.size?pointer!=0:pointer==0,"Measured duplicate or declared null constructor");const std::array<unsigned,3> meta{binding.entry,binding.field,pointer};out.append("cleanup/"+std::to_string(sequence)+"/string-"+std::to_string(binding.entry)+".bin",meta.data(),sizeof(meta));if(pointer)original_free(reinterpret_cast<void*>(pointer));*reinterpret_cast<unsigned*>(binding.field)=0;}original_free(reinterpret_cast<void*>(*crtbegin));''')
 ref=one(ref,'||(pc>=0x5ac3ec&&pc<0x5ac3f1)', '||(pc>=0x5ac3ec&&pc<0x5ac3f1)||(pc>=0x5bb670&&pc<0x5bb674)')
 ref=ref.replace('/324actual original initializer phases','/426 actual original initializer phases');(out/'reference.cpp').write_text(ref)
 (out/'preserve_x86.asm').write_text(read(OLD/'preserve_x86.asm'));(out/'CMakeLists.txt').write_text(read(OLD/'CMakeLists.txt').replace('Startup54','Startup71').replace('startup54','startup71'))
 (out/'string-bindings.json').write_text(json.dumps(stringrows,indent=2)+'\n');(out/'page-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(__file__);report=dict(passed=True,scope='Additive original71 literalgame source/actual32CRT string+registry execution preparation',parent_preparation=str(OLD),parent_sha256=sha(OLD/'report.json'),order=order,observed_pages=observed,page_count=len(addresses),source_spans=spans,pack_sha256=sha(out/'pages.bin'),record_bytes=266880,string_bindings=stringrows,typed_API_ledger_entry_bytes=104,string_lifetime='Live across whole selected71; genuine original free for each duplicate before vectorfree; stored callbacks never invoked',per_phase_reseed=False,original_executed=False,native_executed=False,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pages=len(addresses),observed=len(observed))))
if __name__=='__main__':main(sys.argv[1])
