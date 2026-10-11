#include "component.hpp"
#include "literals.hpp"
#include <Windows.h>
#include <algorithm>
#include <cstring>
#include <exception>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

extern "C" void mw34_widget_native_api(void *,const std::uint64_t *,mw34::m4_widget_native::ApiHardware *);
extern "C" void mw34_widget_hardware_call(void *,mw34::m4_widget_native::HostBoundary *);
namespace mw34::m4_widget_native {
namespace {
void require(bool v,const char *m){if(!v)throw std::runtime_error(m);}
struct Access {unsigned pc,address;std::uint64_t value;unsigned width,writing;};
struct Frame {unsigned target,frame,ret,site;};
struct Vptr {unsigned pc,value,root,access;};
struct FSFrame {unsigned frame,previous,handler,scope,invocation;};
struct ArrayFrame {unsigned frame,base,stride,count,ctor,iteration,site;};
struct Font {unsigned guest,generation,instance,root;std::uint64_t native;bool owned,live;};
struct ApiRecord {
 std::array<std::uint64_t,16> metadata{};
 m4_runtime::Cpu32 before{},after{};
 std::array<unsigned,14> arguments{};
 std::array<std::byte,64> frame{};
 ApiHardware hardware{};
};
struct Invoke {Component::Impl *owner;unsigned root;bool cleanup;std::exception_ptr exception;};
thread_local Component::Impl *current{};
constexpr std::array<unsigned,6> import_PCs{0x5a013c,0x5a063f,0x5a074b,0x517287,0x5ac11e,0x5ac580};
constexpr std::array<unsigned,6> import_slots{0x5bb070,0x5bb074,0x5bb068,0x5bb064,0x5bb52c,0x5bb530};
constexpr std::array<unsigned,3> GDI_targets{0x71f00010,0x71f00020,0x71f00030};
m4_runtime::Cpu32 cpu(const State&s){return {s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,static_cast<unsigned>((s.rflag.flat&~0xcd5ULL)|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11)),s.gpr.rip.dword};}
void project(State&s,const m4_runtime::Cpu32&c){s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;s.gpr.rbx.dword=c.ebx;s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;s.gpr.rip.dword=c.eip;s.rflag.flat=c.eflags;s.aflag.cf=c.eflags&1;s.aflag.pf=(c.eflags>>2)&1;s.aflag.af=(c.eflags>>4)&1;s.aflag.zf=(c.eflags>>6)&1;s.aflag.sf=(c.eflags>>7)&1;s.aflag.df=(c.eflags>>10)&1;s.aflag.of=(c.eflags>>11)&1;}
void flags(State&s,std::uint64_t f){s.aflag.cf=f&1;s.aflag.pf=(f>>2)&1;s.aflag.af=(f>>4)&1;s.aflag.zf=(f>>6)&1;s.aflag.sf=(f>>7)&1;s.aflag.of=(f>>11)&1;}
} // namespace

struct Component::Impl {
 Runtime&r;Services&services;Inputs input;State&s;Sink sink;void*opaque;
 DWORD thread=GetCurrentThreadId();HMODULE GDI_module{};std::array<void*,3>providers{};
 unsigned selected{},root_frame{},saved_return{},GDI_cursor{},virtual_cursor{},FS_cursor{},operand_cursor{},generation{},FS_invocation{},last_return_PC{};
 const literal::Root*root{};bool active{},failed{},cleaned{};
 std::vector<Access>accesses;std::vector<Frame>frames;std::vector<FSFrame>FS_frames;
 std::map<unsigned,Vptr>vptrs;std::vector<ArrayFrame>array_frames;
 std::vector<std::array<unsigned,8>>virtuals,arrays,FS_events,imports;
 std::vector<Font>fonts;std::vector<ApiRecord>APIs;
 Impl(Runtime&rr,Services&ss,const Inputs&ii,Sink sk,void*op):r(rr),services(ss),input(ii),s(*reinterpret_cast<State*>(r.remill_state().data())),sink(sk),opaque(op){
  require(!current&&sink&&r.domain()==m4_runtime::Domain::admitted_game&&&services.runtime()==&r,"Unique admitted caller Runtime/widget component and sink");
  require(input.before_domain_gate_sha256.size()==64,"Explicit reviewed BEFORE mapping/permission identity required");
  for(unsigned k=0;k<6;++k){const auto&v=input.imports[k];require(v.pc==import_PCs[k]&&v.slot==import_slots[k]&&v.raw,"Six exact current own-branch widget IAT cells");require(r.memory().load<unsigned>({v.slot})==v.raw,"Complete current widget raw IAT preimage");if(k<3)require(v.projected==GDI_targets[k],"Three explicit typed native GDI routes");else if(k==4)require(v.projected==0x78004a36&&v.projected==services.resolve_import(v),"Exact current accepted CRT onexit provider route");else require(v.projected==v.raw,"Unused cold import stays raw and is never admitted");}
  GDI_module=LoadLibraryW(L"gdi32.dll");require(GDI_module!=nullptr,"Actual native Gdi32 provider");
  const std::array<const char*,3>names{"GetStockObject","DeleteObject","CreateFontA"};
  for(unsigned k=0;k<3;++k){providers[k]=reinterpret_cast<void*>(GetProcAddress(GDI_module,names[k]));require(providers[k],"Actual named GDI export resolution");}
  current=this;
 }
 ~Impl(){if(current==this)current=nullptr;if(GDI_module)FreeLibrary(GDI_module);}
 void authority(){require(current==this&&GetCurrentThreadId()==thread&&&services.runtime()==&r,"Current thread and persistent Runtime widget authority");services.authority();}
 void dump(std::string_view p,const void*b,std::size_t n){sink(p,std::span(static_cast<const std::byte*>(b),n),opaque);}
 void instruction(unsigned pc){require(active&&literal::admitted(pc)&&pc!=0x5ac24b&&pc!=0x5a075b,"Reached finite normal widget source PC; cold/failure branch denied");auto row=literal::instruction(pc);require(row,"Exact physical widget instruction exists");std::array<std::byte,16>b{};r.memory().read({pc},std::span(b.data(),row->size));for(unsigned k=0;k<row->size;++k)require(std::to_integer<unsigned>(b[k])==row->bytes[k],"Complete physical widget source instruction bytes");}
 unsigned word(unsigned a){return r.memory().load<unsigned>({a});}
 void access(unsigned pc,unsigned a,std::uint64_t value,unsigned width,bool writing){require(width&&width<=4&&accesses.size()<300000&&operand_cursor<root->operand_count,"Finite widget source scalar/access extent");const auto&e=literal::operands[root->operand_begin+operand_cursor];const auto expected=e.role==1?unsigned(std::int64_t(root_frame)+e.offset):e.role==2?r.fs_base().value:unsigned(e.offset);require(pc==e.pc&&a==expected&&width==e.width&&writing==e.writing,"Exact causal source PC/address role/offset/width/direction order; no value oracle");accesses.push_back({pc,a,value,width,unsigned(writing)});++operand_cursor;}
 void FS(unsigned pc,bool writing,unsigned value){
  require(FS_cursor<root->FS_count,"Current root finite source FS order");const auto&expected=literal::FSs[root->FS_begin+FS_cursor];require(pc==expected.pc&&writing==expected.writing,"Exact current root FS PC/direction order");const unsigned head=word(r.fs_base().value);unsigned kind=0;
  if(writing){
   if(!FS_frames.empty()&&value==FS_frames.back().previous){const auto&f=FS_frames.back();require(head==f.frame&&word(f.frame)==f.previous&&word(f.frame+4)==f.handler&&word(f.frame+8)==f.scope,"Whole current literal FS record and predecessor restoration");kind=2;FS_frames.pop_back();}
   else{require(value==s.gpr.rsp.dword&&value>=r.stack_low().value&&std::uint64_t(value)+12<=r.stack_top().value&&FS_frames.size()<32,"Actual current stack FS install frame");require(word(value)==head,"Current source-written FS predecessor");FS_frames.push_back({value,head,word(value+4),word(value+8),++FS_invocation});kind=1;}
  }else require(value==head,"Actual full FS head read");
  FS_events.push_back({root->root,pc,unsigned(writing),head,value,kind,FS_cursor,unsigned(FS_frames.size())});++FS_cursor;
 }
 std::uint64_t read(unsigned a,unsigned n){authority();const auto pc=s.gpr.rip.dword;instruction(pc);std::array<std::byte,4>b{};r.memory().read({a},std::span(b.data(),n));std::uint64_t v{};std::memcpy(&v,b.data(),n);access(pc,a,v,n,false);
  if(a==r.fs_base().value){require(n==4,"Full DWORD source FS access");FS(pc,false,unsigned(v));}
  if(virtual_cursor<root->virtual_count){const auto&e=literal::virtuals[root->virtual_begin+virtual_cursor];if(pc==e.pc){const auto instance=root->object+e.instance_offset;auto token=vptrs.find(instance);require(n==4&&a==e.slot&&v==e.target&&s.gpr.rcx.dword==instance,"Exact ordered virtual slot/target/current source instance");require(token!=vptrs.end()&&token->second.root==root->root&&token->second.pc==e.store&&token->second.value==e.vptr&&word(instance)==e.vptr,"Same instance most recent literal vptr provenance");require(std::int64_t(s.gpr.rsp.dword)-root_frame==e.frame_offset,"Exact source virtual caller frame");virtuals.push_back({root->root,pc,instance,e.store,e.vptr,a,unsigned(v),unsigned(accesses.size()-1)});++virtual_cursor;}}
  for(unsigned k=0;k<6;++k){const auto&i=input.imports[k];if(pc==i.pc){require(n==4&&a==i.slot&&v==i.raw,"Exact current owning IAT operand preimage");require(word(a)==i.raw,"Current retained raw import unchanged");imports.push_back({root->root,pc,a,unsigned(v),i.projected,unsigned(frames.size()),unsigned(accesses.size()-1),k});return i.projected;}}
  if(literal::instruction(pc)->ret)last_return_PC=pc;
  return v;
 }
 void write(unsigned a,std::uint64_t value,unsigned n){authority();const auto pc=s.gpr.rip.dword;instruction(pc);access(pc,a,value,n,true);
  if(a==r.fs_base().value){require(n==4,"Full DWORD source FS write");FS(pc,true,unsigned(value));}
  for(auto it=vptrs.begin();it!=vptrs.end();)if(std::uint64_t(a)<std::uint64_t(it->first)+4&&std::uint64_t(it->first)<std::uint64_t(a)+n)it=vptrs.erase(it);else++it;
  std::array<std::byte,4>b{};std::memcpy(b.data(),&value,n);r.memory().write({a},std::span(b.data(),n));
  if(n==4)for(const auto&e:literal::virtuals)if(pc==e.store&&value==e.vptr){vptrs[a]={pc,unsigned(value),root->root,unsigned(accesses.size()-1)};break;}
  for(auto&f:FS_frames)if(std::uint64_t(a)<std::uint64_t(f.frame)+12&&std::uint64_t(f.frame)<std::uint64_t(a)+n){require(word(f.frame)==f.previous,"Literal active FS predecessor remains unchanged");f.handler=word(f.frame+4);f.scope=word(f.frame+8);}
  if(literal::instruction(pc)->call){require(n==4&&a==s.gpr.rsp.dword-4&&value==pc+literal::instruction(pc)->size&&frames.size()<96,"Actual committed literal CALL return/frame");frames.push_back({0,a,unsigned(value),pc});}
 }
 void array_enter(unsigned target){
  if(target!=0x5ac2a0)return;
  require(!frames.empty(),"Actual vector helper committed CALL");const auto&f=frames.back();const literal::Array*match{};for(const auto&a:literal::arrays)if(a.root==root->root&&a.site==f.site){require(!match,"Unique source vector caller contract");match=&a;}
  require(match&&f.frame==s.gpr.rsp.dword,"Exact root/vector helper frame");const auto&a=*match;require(word(f.frame+4)==root->object+a.base_offset&&word(f.frame+8)==a.stride&&word(f.frame+12)==a.count&&word(f.frame+16)==a.ctor&&word(f.frame+20)==a.dtor,"Whole source vector base/stride/count/callback/destructor argument frame");array_frames.push_back({f.frame,word(f.frame+4),a.stride,a.count,a.ctor,0,f.site});
 }
 Font&font(unsigned guest){auto it=std::find_if(fonts.begin(),fonts.end(),[&](const Font&f){return f.guest==guest&&f.live;});require(it!=fonts.end(),"Live typed source GDI handle generation");return*it;}
 unsigned handle(std::uint64_t native,bool owned,unsigned instance){require(native,"Actual GDI creation/stock success; failure path not admitted");if(!owned)for(const auto&f:fonts)if(!f.owned&&f.live&&f.native==native)return f.guest;require(fonts.size()<128,"Finite source native-font ownership bound");const unsigned guest=0x72001000+(++generation)*16;fonts.push_back({guest,generation,instance,root->root,native,owned,true});return guest;}
 std::string string(unsigned a){std::string result;for(unsigned k=0;k<256;++k){auto v=r.memory().load<std::uint8_t>({a+k});if(!v)return result;result.push_back(char(v));}throw std::runtime_error("Bounded literal CreateFontA face string");}
 void GDI(unsigned index,unsigned target){require(GDI_cursor<root->GDI_count&&!frames.empty(),"Finite ordered actual source GDI call/frame");const auto&e=literal::GDIs[root->GDI_begin+GDI_cursor];auto f=frames.back();require(e.service==index&&target==GDI_targets[index]&&f.site==e.pc&&f.frame==s.gpr.rsp.dword&&std::int64_t(f.frame)-root_frame==e.frame_offset,"Exact source GDI service/order/current frame");require(!imports.empty()&&imports.back()[1]==e.pc&&imports.back()[4]==target,"Actual source owning GDI import read provenance");require(word(f.frame)==f.ret,"Full source GDI saved return bytes");
  ApiRecord rec;rec.before=cpu(s);r.memory().read({f.frame},rec.frame);std::array<std::uint64_t,14>args{};std::string face;Font*deleted{};const auto instance=root->object+e.instance_offset;
  for(unsigned k=0;k<e.argc;++k){auto v=word(f.frame+4+4*k);rec.arguments[k]=v;if(e.kinds[k]==1){require(v==word(instance+e.values[k]),"Current instance carried font-field argument");deleted=&font(v);args[k]=deleted->native;}else{require(v==e.values[k],"Exact literal source GDI argument");args[k]=std::uint64_t(std::int64_t(std::int32_t(v)));}}
  if(index==2){require(e.argc==14,"Whole fourteen-argument CreateFontA frame");face=string(rec.arguments[13]);args[13]=reinterpret_cast<std::uintptr_t>(face.c_str());}
  const auto error_before=GetLastError();mw34_widget_native_api(providers[index],args.data(),&rec.hardware);const auto error_after=GetLastError();unsigned result{};
  if(index==0)result=handle(rec.hardware.after.rax,false,instance);
  if(index==2)result=handle(rec.hardware.after.rax,true,instance);
  if(index==1){require(deleted,"DeleteObject actual typed current argument");result=unsigned(rec.hardware.after.rax);if(deleted->owned&&result)deleted->live=false;}
  // The native API's captured volatile projection is explicit. Guest virtual
  // FP is retained; raw native API FP is a separate output, not copied opaquely.
  s.gpr.rax.dword=result;s.gpr.rcx.dword=unsigned(rec.hardware.after.rcx);s.gpr.rdx.dword=unsigned(rec.hardware.after.rdx);flags(s,rec.hardware.after.rflags);s.gpr.rsp.dword=f.frame+4*(e.argc+1);s.gpr.rip.dword=f.ret;
  rec.after=cpu(s);rec.metadata={1,root->root,e.pc,index,GDI_cursor,f.frame,f.ret,e.argc,instance,result,rec.hardware.after.rax,reinterpret_cast<std::uintptr_t>(providers[index]),thread,error_before,error_after,generation};APIs.push_back(rec);frames.pop_back();++GDI_cursor;
 }
 void*dispatch(unsigned target,bool tail){authority();require(active&&!frames.empty(),"Actual current literal invocation/frame");auto&f=frames.back();if(!tail){require(f.target==0&&f.frame==s.gpr.rsp.dword,"Actual source CALL frame before routing");f.target=target;}
  if(f.site==0x5ac2db&&!tail){require(!array_frames.empty(),"Current actual vector iteration owner");auto&a=array_frames.back();require(s.gpr.rbp.dword==a.frame-4&&s.gpr.rsi.dword==a.iteration&&a.iteration<a.count&&s.gpr.rcx.dword==a.base+a.iteration*a.stride&&target==a.ctor&&word(s.gpr.rbp.dword+20)==a.ctor,"Same helper frame/ordered bounded iteration/element callback provenance");arrays.push_back({root->root,a.site,a.frame,a.base,a.iteration,s.gpr.rcx.dword,target,f.frame});++a.iteration;}
  for(unsigned k=0;k<3;++k)if(target==GDI_targets[k]){GDI(k,target);return this;}
  for(unsigned k=3;k<6;++k)if(target==input.imports[k].projected){require(k==4&&!tail,"Only genuine source onexit import is admitted; unused imports remain cold");require(!imports.empty()&&imports.back()[1]==input.imports[k].pc&&imports.back()[4]==target,"Exact caller-service import operand");const auto old=f;const auto fs=FS_frames;services.invoke(s,{root->root,input.imports[k].pc,target,f.frame,f.ret,tail});authority();require(s.gpr.rip.dword==old.ret&&s.gpr.rsp.dword==old.frame+4,"Caller actual cdecl service return/committed frame");for(const auto&v:fs)require(word(v.frame)==v.previous&&word(v.frame+4)==v.handler&&word(v.frame+8)==v.scope,"Caller service conserves complete active guest FS record");frames.pop_back();return this;}
  instruction(target);if(target==0x517680)require(!word(0x6384e8),"Current zero font registry source domain");if(target==0x5a2f40)require(!word(s.gpr.rsp.dword+8),"Current null format source domain");array_enter(target);auto body=literal::body(target);require(body,"Actual prepared literal body; foreign/cold target denied");return body(&s,target,this);
 }
 void returned(unsigned target){authority();require(!frames.empty()&&last_return_PC,"Actual literal RET frame/read provenance");instruction(last_return_PC);auto f=frames.back();require(target==f.ret&&!accesses.empty()&&accesses.back().pc==last_return_PC&&accesses.back().address==f.frame&&!accesses.back().writing&&accesses.back().width==4,"Whole actual source RET saved word");if(last_return_PC==0x5ac30c){require(!array_frames.empty(),"Successful vector RET owns current helper");auto&a=array_frames.back();require(a.frame==f.frame&&a.iteration==a.count&&s.gpr.rsp.dword==f.frame+24,"Actual full vector iteration count and RET14");array_frames.pop_back();}frames.pop_back();last_return_PC=0;}
 void invoke(unsigned address){authority();require(!failed&&!r.poisoned()&&!active&&selected<6,"Live serial finite widget selected-root invocation");root=&literal::roots[selected];require(address==root->root&&r.cpu().eip==address&&r.remill_seeded(),"Exact selected source root and actual Runtime route");require(s.addr.ds_base.dword==0&&s.addr.es_base.dword==0&&s.addr.ss_base.dword==0&&s.addr.fs_base.dword==r.fs_base().value,"Flat source DS/ES/SS/current owned minimal TIB");project(s,r.cpu());require(!s.aflag.df,"Source forward-string DF input");root_frame=s.gpr.rsp.dword;saved_return=word(root_frame);require(root_frame>=r.stack_low().value&&std::uint64_t(root_frame)+4<=r.stack_top().value,"Actual bounded root CALL frame");GDI_cursor=virtual_cursor=FS_cursor=operand_cursor=0;active=true;frames.push_back({address,root_frame,saved_return,0});const auto initialFS=word(r.fs_base().value);auto body=literal::body(address);require(body,"Actual selected literal source body");checkpoint("before");body(&s,address,this);require(frames.empty()&&array_frames.empty()&&FS_frames.empty()&&GDI_cursor==root->GDI_count&&virtual_cursor==root->virtual_count&&FS_cursor==root->FS_count&&operand_cursor==root->operand_count,"Complete actual root CALL/virtual/vector/GDI/FS finite closure");require(word(r.fs_base().value)==initialFS&&s.gpr.rsp.dword==root_frame+4&&s.gpr.rip.dword==saved_return,"Current source FS head and exact Runtime root return");r.cpu()=cpu(s);active=false;++selected;checkpoint("after");}
 void cleanup(){authority();require((!active||failed)&&!cleaned,"Serial explicit owned-font cleanup");for(auto it=fonts.rbegin();it!=fonts.rend();++it)if(it->owned&&it->live){std::array<std::uint64_t,14>args{};args[0]=it->native;ApiHardware hardware{};mw34_widget_native_api(providers[1],args.data(),&hardware);require(hardware.after.rax,"Actual owned font DeleteObject cleanup success");it->live=false;std::array<std::uint64_t,8>row{it->guest,it->generation,it->instance,it->root,it->native,thread,hardware.after.rax,1};const auto stem="manual-font-cleanup/"+std::to_string(it->generation);dump(stem+"-row.bin",row.data(),sizeof(row));dump(stem+"-hardware.bin",&hardware,sizeof(hardware));}cleaned=true;checkpoint("cleaned");}
 void checkpoint(std::string_view stem){std::string p=(root?"root-"+std::to_string(root->root)+"/":"bootstrap/")+std::string(stem);auto c=cpu(s);dump(p+"/State.bin",&s,sizeof(s));dump(p+"/CPU.bin",&c,sizeof(c));dump(p+"/FX.bin",r.fx().data(),512);dump(p+"/accesses.bin",accesses.data(),accesses.size()*sizeof(Access));dump(p+"/frames.bin",frames.data(),frames.size()*sizeof(Frame));dump(p+"/FS-frames.bin",FS_frames.data(),FS_frames.size()*sizeof(FSFrame));dump(p+"/FS-events.bin",FS_events.data(),FS_events.size()*sizeof(FS_events[0]));dump(p+"/virtuals.bin",virtuals.data(),virtuals.size()*sizeof(virtuals[0]));dump(p+"/arrays.bin",arrays.data(),arrays.size()*sizeof(arrays[0]));dump(p+"/imports.bin",imports.data(),imports.size()*sizeof(imports[0]));dump(p+"/fonts.bin",fonts.data(),fonts.size()*sizeof(Font));dump(p+"/APIs.bin",APIs.data(),APIs.size()*sizeof(ApiRecord));const std::array<std::uint64_t,12>w{thread,selected,root?root->root:0,root_frame,unsigned(active),unsigned(failed),unsigned(cleaned),GDI_cursor,virtual_cursor,FS_cursor,generation,FS_invocation};dump(p+"/status.bin",w.data(),sizeof(w));}
};
Component::Component(Runtime&r,Services&s,const Inputs&i,Sink sink,void*p):impl_(std::make_unique<Impl>(r,s,i,sink,p)){}
Component::~Component()=default;
Runtime&Component::runtime()noexcept{return impl_->r;}
void Component::authority(){impl_->authority();}
void Component::checkpoint(std::string_view p){impl_->authority();impl_->checkpoint(p);}
void Component::execute(unsigned root,HostBoundary&hardware){Invoke task{impl_.get(),root,false,{}};mw34_widget_hardware_call(&task,&hardware);if(task.exception)std::rethrow_exception(task.exception);}
void Component::cleanup_fonts(HostBoundary&hardware){Invoke task{impl_.get(),0,true,{}};mw34_widget_hardware_call(&task,&hardware);if(task.exception)std::rethrow_exception(task.exception);}
static void entry(Runtime&r,unsigned root){require(current&&&current->r==&r,"Exact registered widget callback/owned current Runtime");current->invoke(root);}
void Component::entry_40e250(Runtime&r){entry(r,0x40e250);}void Component::entry_40ef50(Runtime&r){entry(r,0x40ef50);}void Component::entry_5a3c30(Runtime&r){entry(r,0x5a3c30);}void Component::entry_5a3ff0(Runtime&r){entry(r,0x5a3ff0);}void Component::entry_5a66f0(Runtime&r){entry(r,0x5a66f0);}void Component::entry_479590(Runtime&r){entry(r,0x479590);}
static auto&owner(void*p){require(current&&p==current,"Actual widget bridge current private context");current->authority();return*current;}
} // namespace mw34::m4_widget_native
using namespace mw34::m4_widget_native;
extern "C" void mw34_widget_invoke_guarded(void*p)noexcept{auto&t=*static_cast<Invoke*>(p);try{if(t.cleanup)t.owner->cleanup();else t.owner->r.invoke({t.root});}catch(...){t.owner->failed=true;t.exception=std::current_exception();}}
extern "C" std::uint8_t mw34_widget_game_read8(void*p,unsigned a){return std::uint8_t(owner(p).read(a,1));}
extern "C" std::uint16_t mw34_widget_game_read16(void*p,unsigned a){return std::uint16_t(owner(p).read(a,2));}
extern "C" unsigned mw34_widget_game_read32(void*p,unsigned a){return unsigned(owner(p).read(a,4));}
extern "C" void*mw34_widget_game_write8(void*p,unsigned a,std::uint8_t v){owner(p).write(a,v,1);return p;}
extern "C" void*mw34_widget_game_write16(void*p,unsigned a,std::uint16_t v){owner(p).write(a,v,2);return p;}
extern "C" void*mw34_widget_game_write32(void*p,unsigned a,unsigned v){owner(p).write(a,v,4);return p;}
extern "C" void*mw34_widget_game_call(State*s,unsigned a,void*p){auto&c=owner(p);require(&c.s==s,"Exact current widget State");return c.dispatch(a,false);}
extern "C" void*mw34_widget_game_jump(State*s,unsigned a,void*p){auto&c=owner(p);require(&c.s==s,"Exact current widget State");return c.dispatch(a,true);}
extern "C" void*mw34_widget_game_missing(State*s,unsigned a,void*p){return mw34_widget_game_jump(s,a,p);}
extern "C" void*mw34_widget_game_return(State*s,unsigned a,void*p){auto&c=owner(p);require(&c.s==s,"Exact current widget State");c.returned(a);return p;}
#include "bridges.inc"
