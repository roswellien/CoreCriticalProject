"""Close the measured cached-path EH import and raw named API boundaries."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'preparation-r4';out=B/name;assert not out.exists();r=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='83d1e43eeb5da83680fb5b8973462884a3ce592949c01cd6bfd87de97002ec14';out.mkdir();pins={}
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 for p,h in r['files'].items():assert sha(p)==h;pins[p]=h
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(p.read_bytes())
 def load(p,tag):s=importlib.util.spec_from_file_location(tag,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 A=load(R/'tools/m4-service-initializers/recover.py','eh_PE');D=load(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','eh_operand');m=A.Module(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'));lookup=pin(R/'reports/m4-service-initializers/static-r1/MSVCRT.DLL.linear-lookup.txt')
 for line in lookup.read_text().splitlines():
  match=A.ROW.match(line)
  if not match:continue
  pc=int(match[1],16);asm=re.sub(r'\s+',' ',match[3].strip());op,_,args=asm.partition(' ');m.rows[pc]=dict(pc=pc,size=len(bytes.fromhex(match[2])),bytes=bytes.fromhex(match[2]).hex(),mnemonic=op,operands=args)
 g=A.walk(m,0x78001496);assert len(g['instructions'])==10
 contracts=json.loads((out/'instruction-contracts.json').read_bytes());regs=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
 for row in g['instructions']:
  raw=bytes.fromhex(row['bytes']);off,_=m.image.rva_range(row['pc']-m.base,len(raw));assert m.image.data[off:off+len(raw)]==raw
  n=dict(pc=row['pc'],width=row['size'],bytes_hex=row['bytes'],mnemonic=row['mnemonic'],operands=row['operands'].split(' <')[0]);c=D.instruction_contract(n);cells=[]
  for i,v in enumerate(c['decoded_operands']):
   if v['kind']!='memory':continue
   rd=i in c['explicit_memory_reads'];wr=i in c['explicit_memory_writes']
   if not(rd or wr):continue
   coef=[0]*8
   for term in v['terms']:coef[regs.index(term['register'])]+=term['scale']
   cells.append(dict(displacement=v['displacement'],coefficients=coef,width=v['bits']//8,read=int(rd),write=int(wr),segment=1 if v['segment']=='fs'else 0))
  for v in c['implicit_memory']:
   coef=[0]*8;coef[4]=1;wr=v['kind']=='stack-write';cells.append(dict(displacement=0xfffffffc if wr else 0,coefficients=coef,width=4,read=int(not wr),write=int(wr),segment=0))
  contracts['instructions'].append(dict(**n,module='CRT',cells=cells,opcode=raw[0]))
 contracts['instructions'].sort(key=lambda r:r['pc']);(out/'instruction-contracts.json').write_text(json.dumps(contracts,indent=2)+'\n');(out/'EH-prolog-graph.json').write_text(json.dumps(g,indent=2)+'\n')
 cell=lambda c:'{'+','.join([hex(c['displacement']),'{'+','.join(map(str,c['coefficients']))+'}',str(c['width']),str(c['read']),str(c['write']),str(c['segment'])])+'}'
 h='#pragma once\nstruct TraceMemory{unsigned displacement,coefficients[8],width,read,write,segment;};\nstruct TracePoint{unsigned pc,width,opcode,count;TraceMemory cells[4];};\ninline constexpr std::array<TracePoint,'+str(len(contracts['instructions']))+'> trace_points{{\n'
 for d in contracts['instructions']:h+='{'+','.join(map(str,[d['pc'],d['width'],d['opcode'],len(d['cells'])]))+',{'+','.join(cell(c)for c in d['cells'])+'}},\n'
 (out/'trace_points.hpp').write_text(h+'}};\n');(out/'api_boundaries.asm').write_bytes(pin(Path(__file__).with_name('api_boundaries.asm')).read_bytes())
 c=(out/'CMakeLists.txt').read_text();assert c.count('boundaries.asm)')==1;(out/'CMakeLists.txt').write_text(c.replace('boundaries.asm)','boundaries.asm api_boundaries.asm)'))
 p=out/'worker.cpp';s=p.read_text();a='#include "trace.hpp"';assert s.count(a)==1
 block='''
extern "C" {Cpu a_cpu{};alignas(16) unsigned char a_fx[512]{},a_env[28]{};unsigned api_kind{},api_phase{},api_resume{},named_targets[4]{},named_returns[4]{};void named_API_0();void named_API_1();void named_API_2();void named_API_3();}
struct NamedBoundary{Cpu cpu;unsigned char fx[512],env[28],frame[64];unsigned kind,phase,argc,thread,error,FShead;};
static NamedBoundary named_boundaries[16]{};static unsigned named_count{};
inline constexpr unsigned named_cells[4]{0x5f498330,0x7802e044,0x7802e0c8,0x7802e048};
inline constexpr const char* named_names[4]{"TlsGetValue","EnterCriticalSection","GetACP","LeaveCriticalSection"};
extern "C" void observe_named_API(){const auto gle=GetLastError();try{require(api_kind<4&&api_phase<=1&&named_count<16,"Bounded named API raw checkpoint");auto&b=named_boundaries[named_count++];a_cpu.pc=api_phase?named_returns[api_kind]:named_targets[api_kind];b.cpu=a_cpu;std::memcpy(b.fx,a_fx,512);std::memcpy(b.env,a_env,28);require(safe_read(reinterpret_cast<void*>(b.cpu.esp),b.frame,64),"Whole named API actual source frame");if(!api_phase)std::memcpy(&named_returns[api_kind],b.frame,4);b.kind=api_kind;b.phase=api_phase;b.argc=api_kind==2?0:1;b.thread=GetCurrentThreadId();b.error=gle;b.FShead=__readfsdword(0);}catch(...){observer_error=1;}SetLastError(gle);}
static void named_IAT(bool install){const void(*hooks[])(){named_API_0,named_API_1,named_API_2,named_API_3};for(unsigned i=0;i<4;++i){DWORD old{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(named_cells[i]),4,PAGE_READWRITE,&old),"Named actual owning IAT write");*reinterpret_cast<unsigned*>(named_cells[i])=install?reinterpret_cast<unsigned>(hooks[i]):named_targets[i];require(VirtualProtect(reinterpret_cast<void*>(named_cells[i]),4,old,&ignored),"Named actual owning IAT restore protection");}}
'''
 s=s.replace(a,block+'\n'+a)
 a='if(!tracing){\n  const unsigned char';assert s.count(a)==1
 before='''for(unsigned i=0;i<4;++i){named_targets[i]=dword(named_cells[i]);auto expected=GetProcAddress(GetModuleHandleW(L"kernel32.dll"),named_names[i]);require(reinterpret_cast<unsigned>(expected)==named_targets[i],"Actual named export/IAT identity");HMODULE owner{};require(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(expected),&owner),"Actual named API physical owner");std::array<wchar_t,32768>path{};require(GetModuleFileNameW(owner,path.data(),path.size())>0,"Actual API owner path");auto text=std::filesystem::path(path.data()).string();dump("named-API/"+std::to_string(i)+"-path.txt",text.data(),text.size());auto file=read(text.c_str(),32<<20);auto hash=sha256(file);dump("named-API/"+std::to_string(i)+"-sha256.txt",hash.data(),hash.size());dump("named-API/"+std::to_string(i)+"-entry64.bin",reinterpret_cast<void*>(named_targets[i]),64);}dump("named-API/targets.bin",named_targets,sizeof(named_targets));
 '''
 s=s.replace(a,before+'if(!tracing){\n  named_IAT(true);\n  const unsigned char')
 a='dump("boundaries/records.bin",boundaries,boundary_count*sizeof(Boundary));';assert s.count(a)==1
 s=s.replace(a,a+'dump("named-API/records.bin",named_boundaries,named_count*sizeof(NamedBoundary));if(!tracing){require(named_count==8,"Four real named API fullCPU/FX/ENV/frame pairs");named_IAT(false);}')
 p.write_text(s)
 for p in out.iterdir():pin(p)
 pin(__file__);pin(parent/'report.json');r.update(parent_preparation_sha256=sha(parent/'report.json'),correction='Add physically measured imported ten-row _EH_prolog plus four exact named source-owning IAT transparent return shims in normal mode. Trace mode keeps authentic unmodified API IATs. API actual return word substituted transiently with declared observer continuation, all arguments/CPU/FX/ENV and actual cleanup retained.',physical_rows=len(contracts['instructions']),trace_descriptors=len(contracts['instructions']),normal_named_API_pairs=4,files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
