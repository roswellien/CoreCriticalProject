// One registered admitted-image native root. All game/provider logic is literal
// COFF. Windows resources are separate owned associations for borrowed guest data.
#include "fixture_spec.hpp"
#include "runtime.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <Windows.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <span>
#include <string>
#include <thread>
#include <vector>
using namespace mw34;using namespace mw34::m4_runtime;
namespace mf= mw34_mfc_fixture;
static_assert(sizeof(State)==3504&&sizeof(Cpu32)==40&&sizeof(CRITICAL_SECTION)==40);
static void require(bool v,const char*s){if(!v)throw std::runtime_error(s);}
static std::vector<std::byte>read_file(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);require(bool(f),"Bounded native input open");auto n=f.tellg();require(n>=0&&n<64*1024*1024,"Bounded native input size");std::vector<std::byte>b(static_cast<std::size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),b.size());require(bool(f),"Complete native input read");return b;}
static std::filesystem::path output;
static void dump(const std::string&name,const void*data,std::size_t size){auto p=output/name;std::filesystem::create_directories(p.parent_path());require(!std::filesystem::exists(p),"Fresh native output");std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(data),size);require(bool(f),"Whole native output write");}
struct Block{unsigned address,size,permissions;std::vector<std::byte>initial;};
struct Access{unsigned pc,address;std::uint64_t value;unsigned width,writing;};
struct Frame{unsigned target,frame,ret,site;};
struct ApiRecord{std::array<std::uint64_t,16>words{};Cpu32 before,after;std::array<std::byte,64>frame{};std::array<std::byte,40>CS_before{},CS_after{};};
struct Context;
static thread_local Context*current{};
struct Context {
 Runtime&r;State&s;const std::vector<Block>&blocks;DWORD host_thread=GetCurrentThreadId(),host_TLS=TLS_OUT_OF_INDEXES;bool TLS_live{},CS_live{},entered{},complete{};unsigned access_cursor{},API_cursor{},CS_depth{};CRITICAL_SECTION CS{};
 std::vector<std::byte>host_thread_backing;std::vector<Access>accesses;std::vector<ApiRecord>APIs;std::vector<Frame>frames;std::vector<std::array<unsigned,4>>controls;
 Context(Runtime&runtime,const std::vector<Block>&input):r(runtime),s(*reinterpret_cast<State*>(r.remill_state().data())),blocks(input){
  require(!current&&r.domain()==Domain::admitted_game,"Unique admitted native MFC context");auto found=std::find_if(blocks.begin(),blocks.end(),[](const auto&v){return v.address==mf::thread_pointer;});require(found!=blocks.end()&&found->size==16,"Exact borrowed current-thread backing");auto&b=*found;host_thread_backing=b.initial;
  host_TLS=TlsAlloc();require(host_TLS!=TLS_OUT_OF_INDEXES,"Real owned host TLS slot");TLS_live=true;require(TlsGetValue(host_TLS)==nullptr,"New actual host TLS slot starts empty");require(TlsSetValue(host_TLS,host_thread_backing.data()),"Actual current host-thread association");
  InitializeCriticalSection(&CS);CS_live=true;require(CS.RecursionCount==0&&CS.OwningThread==nullptr,"Actual owned native CS40 starts initialized/unheld");current=this;
 }
 ~Context(){if(current==this)current=nullptr;if(CS_live){if(CS_depth)LeaveCriticalSection(&CS);DeleteCriticalSection(&CS);}if(TLS_live){TlsSetValue(host_TLS,nullptr);TlsFree(host_TLS);}}
 void authority(){require(current==this&&GetCurrentThreadId()==host_thread&&TLS_live&&CS_live,"Exact active context/thread/native resources");}
 Cpu32 cpu()const{Cpu32 c{s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,mf::initial_flags,s.gpr.rip.dword};const unsigned values[]{s.aflag.cf,s.aflag.pf,s.aflag.af,s.aflag.zf,s.aflag.sf,s.aflag.df,s.aflag.of};constexpr unsigned bits[]{0,2,4,6,7,10,11};for(unsigned i=0;i<7;++i)c.eflags=(c.eflags&~(1U<<bits[i]))|(unsigned(bool(values[i]))<<bits[i]);return c;}
 void checkpoint(const char*stem){auto c=cpu();dump(std::string(stem)+"/State.bin",&s,sizeof(s));dump(std::string(stem)+"/CPU.bin",&c,sizeof(c));dump(std::string(stem)+"/FX.bin",r.fx().data(),512);for(const auto&b:blocks){std::vector<std::byte>x(b.size);r.memory().read({b.address},x);dump(std::string(stem)+"/blocks/"+std::to_string(b.address)+".bin",x.data(),x.size());}}
 void access(unsigned address,std::uint64_t value,unsigned width,bool writing){authority();require(access_cursor<mf::access_order.size(),"Finite source operand extent");auto e=mf::access_order[access_cursor];require(s.gpr.rip.dword==e.pc&&address==e.address&&width==e.width&&writing==bool(e.writing),"Exact causal source PC/operand/direction order");accesses.push_back({e.pc,address,value,width,unsigned(writing)});++access_cursor;}
 std::uint64_t read(unsigned a,unsigned n){authority();std::array<std::byte,8>b{};require(n<=8,"Bounded source scalar read");r.memory().read({a},std::span(b.data(),n));std::uint64_t v{};std::memcpy(&v,b.data(),n);access(a,v,n,false);return v;}
 void write(unsigned a,std::uint64_t v,unsigned n){authority();access(a,v,n,true);if(a==mf::global_pointer+0x14)require(n==1&&v==0&&s.gpr.rip.dword==0x5ae3b7,"Literal provider byte14 write");if(a==mf::global_pointer+0x1040)require(n==4&&v==0x421&&s.gpr.rip.dword==0x5ae3ba,"Literal provider DWORD1040 write");std::array<std::byte,8>b{};std::memcpy(b.data(),&v,n);r.memory().write({a},std::span(b.data(),n));
  if(auto i=mf::instruction(s.gpr.rip.dword);i&&i->call)frames.push_back({0,a,unsigned(v),i->pc});
 }
 void returned(unsigned target){authority();require(!frames.empty(),"Actual source return owns a current frame");auto f=frames.back();require(target==f.ret,"Exact current source saved return identity");if(f.target==0x5f40107d){require(f.site==0x5f4010b0&&target==0x5f4010b5&&s.gpr.rsp.dword==f.frame-12,"Exact imported EH prolog special source return");}else{auto last=accesses.back();require(last.pc&&mf::instruction(last.pc)->ret&&last.address==f.frame,"Ordinary literal source RET reads its current frame");}frames.pop_back();}
 void CS_transport(){std::array<unsigned,3>semantic{CS_depth?0xfffffffeU:0xffffffffU,CS_depth,CS_depth?mf::guest_thread:0U};require(CS.RecursionCount==CS_depth&&reinterpret_cast<std::uintptr_t>(CS.OwningThread)==(CS_depth?host_thread:0),"Actual native CS40 depth/current-thread relation");for(unsigned i=0;i<3;++i)r.memory().store<unsigned>({mf::CS_pointer+4+4*i},semantic[i]);}
 void API(unsigned index,unsigned target){authority();require(index==API_cursor&&index<4,"Exact four source API invocation order");const auto&spec=mf::APIs[index];require(target==spec.raw&&s.gpr.rip.dword==target&&!frames.empty(),"Exact named source target/current frame");auto&f=frames.back();require(f.site==spec.call_site&&f.frame==s.gpr.rsp.dword,"Exact source CALL frame including resolver tail JMP");require(accesses.size()>=(index==2?1U:2U),"Source IAT read ledger exists");const auto&iat=accesses[accesses.size()-(index==2?1:2)];require(iat.pc==spec.site&&iat.writing==0&&iat.width==4&&iat.value==target,"Actual final source IAT target read");if(index!=2){const auto&push=accesses.back();require(push.pc==spec.site&&push.writing==1&&push.address==f.frame&&push.width==4&&push.value==spec.ret,"Actual committed source API return push");}require(r.memory().load<unsigned>({s.gpr.rsp.dword})==spec.ret,"Exact source API saved return");if(spec.argc)require(r.memory().load<unsigned>({s.gpr.rsp.dword+4})==(index==0?3:mf::CS_pointer),"Exact typed source TLS/borrowed CS argument");
  ApiRecord rec;rec.before=cpu();r.memory().read({s.gpr.rsp.dword},rec.frame);std::memcpy(rec.CS_before.data(),&CS,40);std::uint64_t raw{};unsigned result{};const auto error_before=GetLastError();
  if(index==0){auto p=TlsGetValue(host_TLS);raw=reinterpret_cast<std::uintptr_t>(p);require(p==host_thread_backing.data(),"Real native TlsGetValue returns current owned association");std::vector<std::byte>x(16);r.memory().read({mf::thread_pointer},x);require(x==host_thread_backing,"Complete borrowed source thread/native association mirror");result=mf::thread_pointer;}
  if(index==1){require(CS_depth==0,"Normal lock25 enter depth0");EnterCriticalSection(&CS);CS_depth=1;CS_transport();}
  if(index==2){raw=GetACP();require(raw==1252,"Observed finite actual ACP1252 only");result=unsigned(raw);}
  if(index==3){require(CS_depth==1,"Normal lock25 leave depth1");LeaveCriticalSection(&CS);CS_depth=0;CS_transport();}
  // Typed guest ABI representatives for caller-clobbered VOID registers are
  // explicit: EAX0, ECX/EDX/flags retained. They are not original AFTER input.
  const auto error_after=GetLastError();std::memcpy(rec.CS_after.data(),&CS,40);s.gpr.rax.dword=result;s.gpr.rsp.dword+=4*(spec.argc+1);s.gpr.rip.dword=spec.ret;rec.after=cpu();rec.words={1,index,spec.site,spec.raw,spec.argc,rec.before.esp,spec.ret,result,raw,host_thread,host_TLS,reinterpret_cast<std::uintptr_t>(host_thread_backing.data()),mf::thread_pointer,CS_depth,error_before,error_after};APIs.push_back(rec);frames.pop_back();++API_cursor;
 }
 void*dispatch(unsigned target,bool tail){authority();if(!tail){require(!frames.empty()&&frames.back().target==0&&frames.back().frame==s.gpr.rsp.dword,"Actual committed source CALL frame before routing");frames.back().target=target;}
  for(unsigned i=0;i<4;++i)if(target==mf::APIs[i].raw){API(i,target);return this;}
  require(mf::body(target),"Unobserved source branch/callback is denied");return mf::dispatch(target,&s,this);
 }
 void finish(){authority();require(complete&&access_cursor==mf::access_order.size()&&API_cursor==4&&frames.empty()&&!CS_depth,"Complete142 normal source closure and balanced lifetime");require(TlsGetValue(host_TLS)==host_thread_backing.data(),"Actual TLS association retained until cleanup");require(TlsSetValue(host_TLS,nullptr)&&TlsGetValue(host_TLS)==nullptr,"Actual TLS association cleared");require(TlsFree(host_TLS),"Actual owned TLS slot released");TLS_live=false;DeleteCriticalSection(&CS);CS_live=false;current=nullptr;const std::array<std::uint64_t,8>lifecycle{1,host_thread,host_TLS,4,0,1,1,1};dump("lifecycle.bin",lifecycle.data(),sizeof(lifecycle));}
};
static Context&owner(void*p){require(current&&p==current,"Exact native bridge context");current->authority();return *current;}
extern "C" std::uint8_t mw34_mfc1168_read8(void*p,unsigned a){return static_cast<std::uint8_t>(owner(p).read(a,1));}
extern "C" std::uint16_t mw34_mfc1168_read16(void*p,unsigned a){return static_cast<std::uint16_t>(owner(p).read(a,2));}
extern "C" unsigned mw34_mfc1168_read32(void*p,unsigned a){return unsigned(owner(p).read(a,4));}
extern "C" std::uint64_t mw34_mfc1168_read64(void*p,unsigned a){return owner(p).read(a,8);}
extern "C" void*mw34_mfc1168_write8(void*p,unsigned a,std::uint8_t v){owner(p).write(a,v,1);return p;}
extern "C" void*mw34_mfc1168_write16(void*p,unsigned a,std::uint16_t v){owner(p).write(a,v,2);return p;}
extern "C" void*mw34_mfc1168_write32(void*p,unsigned a,unsigned v){owner(p).write(a,v,4);return p;}
extern "C" void*mw34_mfc1168_write64(void*p,unsigned a,std::uint64_t v){owner(p).write(a,v,8);return p;}
extern "C" void*mw34_mfc1168_call(State*s,unsigned a,void*p){auto&c=owner(p);require(&c.s==s,"Source bridge State identity");return c.dispatch(a,false);}
extern "C" void*mw34_mfc1168_jump(State*s,unsigned a,void*p){auto&c=owner(p);require(&c.s==s,"Source bridge State identity");return c.dispatch(a,true);}
extern "C" void*mw34_mfc1168_missing(State*s,unsigned a,void*p){return mw34_mfc1168_jump(s,a,p);}
extern "C" void*mw34_mfc1168_return(State*s,unsigned a,void*p){auto&c=owner(p);require(&c.s==s,"Source bridge State identity");c.returned(a);return p;}
extern "C" void*mw34_mfc1168_async_hyper_call(State*,unsigned,void*){throw std::runtime_error("Unentered padded or cold source instruction denied");}
#include "generated_bridges.inc"
static void native_root(Runtime&r){auto&c=owner(current);require(&c.r==&r&&!c.entered,"One registered native root invocation");c.entered=true;auto cpu=r.cpu();auto put=[&](unsigned at,unsigned v){std::memcpy(reinterpret_cast<std::byte*>(&c.s)+at,&v,4);};constexpr unsigned offsets[]{2216,2248,2264,2232,2312,2328,2280,2296,2472};const unsigned values[]{cpu.eax,cpu.ecx,cpu.edx,cpu.ebx,cpu.esp,cpu.ebp,cpu.esi,cpu.edi,cpu.eip};for(unsigned i=0;i<9;++i)put(offsets[i],values[i]);const unsigned flag_offsets[]{2065,2067,2069,2071,2073,2075,2077},bits[]{0,2,4,6,7,10,11};for(unsigned i=0;i<7;++i)reinterpret_cast<std::byte*>(&c.s)[flag_offsets[i]]=std::byte{static_cast<unsigned char>((cpu.eflags>>bits[i])&1)};put(2168,mf::TEB);r.mark_remill_seeded();c.frames.push_back({0x5ae3e4,cpu.esp,Runtime::external_return,0});c.checkpoint("before");mf::dispatch(0x5ae3e4,&c.s,&c);c.complete=true;r.cpu()=c.cpu();c.checkpoint("after");}
int main(int argc,char**argv){try{require(argc==4,"image BEFORE-pack fresh-output");output=argv[3];require(!std::filesystem::exists(output)&&std::filesystem::create_directory(output),"Fresh native fixture output");auto image=read_file(argv[1]);require(m4::sha256(image)==m4::admitted_image_hash,"Exact admitted original game image");Policy policy;policy.stack_bytes=65536;policy.teb={mf::TEB};auto r=Runtime::from_admitted_image(image,policy);auto pack=read_file(argv[2]);require(pack.size()>12&&!std::memcmp(pack.data(),"M4MFCNAT",8),"Exact BEFORE-only input pack");unsigned count{};std::memcpy(&count,pack.data()+8,4);std::size_t cursor=12;std::vector<Block>blocks;
 for(unsigned i=0;i<count;++i){require(cursor+12<=pack.size(),"Bounded block header");Block b{};std::memcpy(&b.address,pack.data()+cursor,4);std::memcpy(&b.size,pack.data()+cursor+4,4);std::memcpy(&b.permissions,pack.data()+cursor+8,4);cursor+=12;require(b.size&&cursor+b.size<=pack.size(),"Bounded BEFORE block");b.initial.assign(pack.begin()+cursor,pack.begin()+cursor+b.size);cursor+=b.size;blocks.push_back(std::move(b));}require(cursor==pack.size(),"Complete exact input pack");
 // Replace the runtime policy's tiny authored TEB fragments with the coherent
 // genuine complete root input. The source never dereferences its old handler.
 for(unsigned offset:std::array<unsigned,3>{0,4,0x18})r.memory().unmap({mf::TEB+offset});
 for(const auto&b:blocks){bool existing=false;if(b.address==0x20000000){r.memory().write({b.address},b.initial);existing=true;}for(const auto&region:r.image_metadata().mapped_regions)if(region.start.value<=b.address&&std::uint64_t(b.address)+b.size<=std::uint64_t(region.start.value)+region.size){r.memory().protect(region.start,Permissions::read|Permissions::write);r.memory().write({b.address},b.initial);r.memory().protect(region.start,region.permissions);existing=true;break;}if(!existing){r.memory().map({b.address},b.size,Permissions::read|Permissions::write);r.memory().write({b.address},b.initial);r.memory().protect({b.address},static_cast<Permissions>(b.permissions));}}
 auto cpu=mf::initial_cpu;cpu.esp+=4;r.cpu()=cpu;std::copy(mf::initial_FX.begin(),mf::initial_FX.end(),r.fx().begin());r.register_translation({{0x5ae3e4},{Abi::Cdecl,0,true},&native_root,"Finite native MFC1168 cached-root",{Domain::admitted_game,m4::admitted_image_hash,15,mf::root_sha,mf::native_object_sha,mf::lift_report_sha}});r.freeze_registry();Context c(r,blocks);r.invoke({0x5ae3e4});require(r.calls().size()==1&&r.calls()[0].completed&&!r.poisoned(),"Actual registered Runtime dispatcher completed");dump("accesses.bin",c.accesses.data(),c.accesses.size()*sizeof(Access));dump("APIs.bin",c.APIs.data(),c.APIs.size()*sizeof(ApiRecord));c.finish();const std::array<unsigned,10>schema{sizeof(Access),sizeof(ApiRecord),unsigned(c.accesses.size()),unsigned(c.APIs.size()),sizeof(State),sizeof(Cpu32),512,unsigned(blocks.size()),1,1};dump("schema.bin",schema.data(),sizeof(schema));dump("COMPLETE.txt","complete",8);std::cout<<"one registered native MFC1168 cached root completed\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
