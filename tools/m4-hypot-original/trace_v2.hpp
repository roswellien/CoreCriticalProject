// Separate stopped-thread observations of genuine instructions. No guest inputs.
#pragma once
#include "trace_points.hpp"
#include "api_imports.hpp"
struct HypotTraceCell {unsigned address,width,read,write,segment,before_valid,after_valid;unsigned char before[16],after[16];};
struct HypotTraceEvent {unsigned index,pc,next_pc,exception_eip,opcode,count,thread,kind;CONTEXT before,after;HypotTraceCell cells[4];unsigned char frame_before[64],frame_after[64];unsigned head_before,head_after;};
struct HypotTraceApi {unsigned index,source_pc,target,return_pc,import_index,argc,returned,thread,error_before,error_after,head_entry,head_after;CONTEXT entry,after;unsigned char frame[64],returned_frame[64],stack_entry[4096],stack_after[4096];};
static_assert(sizeof(HypotTraceCell)==60&&sizeof(HypotTraceEvent)==1840&&sizeof(HypotTraceApi)==9800);
static HypotTraceEvent hypot_trace_events[32768]{};static HypotTraceApi hypot_trace_apis[256]{};
static unsigned hypot_trace_count{},hypot_trace_api_count{},hypot_trace_active{},hypot_trace_owner{},hypot_trace_epoch{},hypot_trace_teb{};
static unsigned hypot_trace_targets[hypot_trace_imports.size()]{};
static unsigned char hypot_trace_original[hypot_trace_points.size()]{};
struct HypotTraceSegment {unsigned selector,base,limit;LDT_ENTRY descriptor;};
static_assert(sizeof(HypotTraceSegment)==20);
static HypotTraceSegment hypot_trace_segments[3]{};static unsigned hypot_trace_segments_ready{};
static unsigned hypot_trace_register(const CONTEXT&c,unsigned i){switch(i){case 0:return c.Eax;case 1:return c.Ecx;case 2:return c.Edx;case 3:return c.Ebx;case 4:return c.Esp;case 5:return c.Ebp;case 6:return c.Esi;case 7:return c.Edi;default:return 0;}}
static void hypot_trace_begin(){
 require(!hypot_trace_active,"Separate trace inactive before genuine root");
 hypot_trace_owner=GetCurrentThreadId();hypot_trace_count=hypot_trace_api_count=0;++hypot_trace_epoch;hypot_trace_segments_ready=0;std::memset(hypot_trace_segments,0,sizeof(hypot_trace_segments));
 __asm {
  mov eax,dword ptr fs:[18h]
  mov hypot_trace_teb,eax
 }
 for(unsigned i=0;i<hypot_trace_imports.size();++i)std::memcpy(&hypot_trace_targets[i],reinterpret_cast<void*>(hypot_trace_imports[i].iat),4);
 for(unsigned i=0;i<hypot_trace_points.size();++i){const auto&p=hypot_trace_points[i];auto*b=reinterpret_cast<unsigned char*>(p.pc);require(*b==p.opcode,"Exact physical source first opcode before trace");hypot_trace_original[i]=*b;DWORD old{},ignored{};require(VirtualProtect(b,1,PAGE_EXECUTE_READWRITE,&old),"Separate trace source writable");*b=0xcc;require(FlushInstructionCache(GetCurrentProcess(),b,1)&&VirtualProtect(b,1,old,&ignored),"Separate trace initial breakpoint/permission");}
 hypot_trace_active=1;
}
static void hypot_trace_finish(){
 hypot_trace_active=0;
 for(unsigned i=0;i<hypot_trace_points.size();++i){auto*b=reinterpret_cast<unsigned char*>(hypot_trace_points[i].pc);DWORD old{},ignored{};require(VirtualProtect(b,1,PAGE_EXECUTE_READWRITE,&old),"Separate source restoration writable");*b=hypot_trace_original[i];require(FlushInstructionCache(GetCurrentProcess(),b,1)&&VirtualProtect(b,1,old,&ignored),"Separate source restored breakpoint/permission");}
}
static bool hypot_trace_debug(HANDLE child,const DEBUG_EVENT&event){
 const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;if(code!=EXCEPTION_BREAKPOINT&&code!=EXCEPTION_SINGLE_STEP&&code!=0x4000001fU)return false;
 auto get=[&](const void*a,void*b,SIZE_T n){SIZE_T got{};require(ReadProcessMemory(child,a,b,n,&got)&&got==n,"Stopped actual child read");};auto put=[&](void*a,const void*b,SIZE_T n){SIZE_T got{};require(WriteProcessMemory(child,a,b,n,&got)&&got==n,"Trace observation output write");};
 unsigned active{},owner{},teb{},epoch{};get(&hypot_trace_active,&active,4);if(!active)return false;get(&hypot_trace_owner,&owner,4);get(&hypot_trace_teb,&teb,4);get(&hypot_trace_epoch,&epoch,4);require(owner==event.dwThreadId&&teb,"Exact actual source owner and TEB");
 mw34::original_broker::Handle thread(OpenThread(THREAD_GET_CONTEXT|THREAD_SET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,owner));require(thread.value!=nullptr,"Actual stopped source handle");CONTEXT c{};c.ContextFlags=CONTEXT_FULL|CONTEXT_FLOATING_POINT|CONTEXT_EXTENDED_REGISTERS;require(GetThreadContext(thread.value,&c),"Whole actual stopped x86 CONTEXT");
 static unsigned previous_epoch{},pending=~0U;static HypotTraceEvent measured{};static std::vector<HypotTraceApi> APIs;
 if(epoch!=previous_epoch){require(pending==~0U,"Prior trace epoch finished its genuine instruction");APIs.clear();previous_epoch=epoch;}
 auto maybe=[&](unsigned a,void*p,unsigned n){SIZE_T got{};return ReadProcessMemory(child,reinterpret_cast<void*>(a),p,n,&got)&&got==n;};
 auto head=[&](){unsigned v{};require(maybe(teb,&v,4),"Actual stopped FS head");return v;};
 auto patch=[&](unsigned pc,unsigned char b){DWORD old{},ignored{};auto*p=reinterpret_cast<void*>(pc);require(VirtualProtectEx(child,p,1,PAGE_EXECUTE_READWRITE,&old),"Stopped source writable");put(p,&b,1);require(FlushInstructionCache(child,p,1)&&VirtualProtectEx(child,p,1,old,&ignored),"Stopped source exact permission/cache");};
 auto cell=[&](HypotTraceCell&v,bool after){require(v.width&&v.width<=16,"Whole bounded FP/integer operand");auto*b=after?v.after:v.before;const bool ok=maybe(v.address,b,v.width);if(after)v.after_valid=ok;else v.before_valid=ok;};
 auto publish_API=[&](const HypotTraceApi&a){put(&hypot_trace_apis[a.index],&a,sizeof(a));unsigned n=a.index+1;put(&hypot_trace_api_count,&n,4);};
 unsigned segments_ready{};get(&hypot_trace_segments_ready,&segments_ready,4);
 if(!segments_ready){HypotTraceSegment rows[3]{};const unsigned selectors[3]{c.SegDs,c.SegEs,c.SegSs};for(unsigned i=0;i<3;++i){auto&o=rows[i];o.selector=selectors[i];require(GetThreadSelectorEntry(thread.value,o.selector,&o.descriptor),"Actual stopped data/extra/stack descriptors");const auto&b=o.descriptor.HighWord.Bits;o.base=o.descriptor.BaseLow|(b.BaseMid<<16)|(b.BaseHi<<24);o.limit=o.descriptor.LimitLow|(b.LimitHi<<16);if(b.Granularity)o.limit=(o.limit<<12)|0xfff;require(o.base==0&&o.limit==0xffffffff,"Actual flat32 DS/ES/SS address admission");}put(hypot_trace_segments,rows,sizeof(rows));segments_ready=1;put(&hypot_trace_segments_ready,&segments_ready,4);}
 if(code==EXCEPTION_SINGLE_STEP){
  require(pending<hypot_trace_points.size(),"One pending genuine source instruction");measured.after=c;measured.next_pc=c.Eip;measured.head_after=head();require(maybe(c.Esp,measured.frame_after,64),"Whole actual post-instruction stack window");for(unsigned i=0;i<measured.count;++i)cell(measured.cells[i],true);patch(hypot_trace_points[pending].pc,0xcc);put(&hypot_trace_events[measured.index],&measured,sizeof(measured));unsigned n=measured.index+1;put(&hypot_trace_count,&n,4);
  unsigned targets[hypot_trace_imports.size()]{};get(hypot_trace_targets,targets,sizeof(targets));unsigned ai=~0U;
  for(unsigned i=0;i<hypot_trace_imports.size();++i)if(targets[i]==c.Eip){if(ai==~0U||hypot_trace_imports[i].iat==0x5bb5b0)ai=i;}
  if(ai!=~0U){require(APIs.size()<256,"Bounded actual named import intervals");HypotTraceApi a{};a.index=APIs.size();a.source_pc=measured.pc;a.target=c.Eip;a.import_index=ai;a.argc=hypot_trace_imports[ai].argc;a.thread=owner;a.entry=c;a.head_entry=head();require(maybe(c.Esp,a.frame,64)&&maybe(0x20001000,a.stack_entry,4096),"Complete actual entered cdecl frame/live stack");std::memcpy(&a.return_pc,a.frame,4);require(maybe(teb+0x34,&a.error_before,4),"Actual entered LastError");APIs.push_back(a);publish_API(a);}
  pending=~0U;c.EFlags&=~0x100U;require(SetThreadContext(thread.value,&c),"Continue actual source removing instrumentation TF only");return true;
 }
 const auto pc=reinterpret_cast<unsigned>(event.u.Exception.ExceptionRecord.ExceptionAddress);unsigned point=~0U;for(unsigned i=0;i<hypot_trace_points.size();++i)if(hypot_trace_points[i].pc==pc){point=i;break;}if(point==~0U)return false;require(pending==~0U&&c.Eip==pc+1,"Actual source breakpoint continuation");
 for(auto it=APIs.rbegin();it!=APIs.rend();++it)if(!it->returned&&it->return_pc==pc){auto&a=*it;a.returned=1;a.after=c;a.after.Eip=pc;a.head_after=head();require(maybe(c.Esp,a.returned_frame,64)&&maybe(0x20001000,a.stack_after,4096),"Complete actual returned cdecl frame/live stack");require(maybe(teb+0x34,&a.error_after,4),"Actual returned LastError");publish_API(a);break;}
 unsigned n{};get(&hypot_trace_count,&n,4);require(n<32768,"Bounded genuine instruction events");measured={};measured.index=n;measured.pc=pc;measured.exception_eip=c.Eip;measured.opcode=hypot_trace_points[point].opcode;measured.before=c;measured.thread=owner;measured.count=hypot_trace_points[point].count;measured.head_before=head();require(maybe(c.Esp,measured.frame_before,64),"Complete actual incoming stack window");
 const auto&p=hypot_trace_points[point];for(unsigned i=0;i<p.count;++i){const auto&m=p.cells[i];auto&v=measured.cells[i];v.address=m.displacement;for(unsigned r=0;r<8;++r)v.address+=hypot_trace_register(c,r)*m.coefficients[r];if(m.segment)v.address+=teb;v.segment=m.segment;v.width=m.width;v.read=m.read;v.write=m.write;cell(v,false);}
 patch(pc,static_cast<unsigned char>(p.opcode));c.Eip=pc;c.EFlags|=0x100U;pending=point;require(SetThreadContext(thread.value,&c),"Execute actual one source instruction with observer TF");return true;
}
