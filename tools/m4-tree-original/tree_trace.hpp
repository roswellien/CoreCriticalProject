// Separate bounded debugger observation. Never supplies source data or effects.
#pragma once
#include "trace_points.hpp"
struct TreeTraceCell {
 unsigned address,width,read,write,owner_index,generation;
 unsigned before_value,after_value,before_valid,after_valid,segment,owner_offset;
};
struct TreeTraceEvent {
 unsigned index,source_pc,next_pc,instruction_kind,cell_count,owner_count_before;
 unsigned exception_eip,actual_first_opcode;
 CONTEXT before,after;
 TreeTraceCell cells[4];
};
static_assert(sizeof(TreeTraceCell)==48&&sizeof(TreeTraceEvent)==1656);
static TreeTraceEvent tree_trace_events[16384]{};
static unsigned tree_trace_count{},tree_trace_active{},tree_trace_owner{};
static unsigned char tree_trace_original[tree_trace_points.size()]{};

static unsigned tree_register(const CONTEXT&c,unsigned index){
 switch(index){case 0:return c.Eax;case 1:return c.Ecx;case 2:return c.Edx;
 case 3:return c.Ebx;case 4:return c.Esp;case 5:return c.Ebp;
 case 6:return c.Esi;case 7:return c.Edi;default:return 0;}
}
static void tree_trace_begin(){
 require(!tree_trace_active,"Trace inactive before measured prefix");
 tree_trace_count=0;tree_trace_owner=GetCurrentThreadId();
 for(unsigned i=0;i<tree_trace_points.size();++i){
  const auto&p=tree_trace_points[i];auto*byte=reinterpret_cast<unsigned char*>(p.pc);
  require(*byte==p.opcode,"Exact physical or accepted FS-observer first opcode");
  tree_trace_original[i]=*byte;DWORD old{},ignored{};
  require(VirtualProtect(byte,1,PAGE_EXECUTE_READWRITE,&old),"Trace source writable");
  *byte=0xcc;
  require(FlushInstructionCache(GetCurrentProcess(),byte,1)&&VirtualProtect(byte,1,old,&ignored),"Trace source breakpoint/protection");
 }
 tree_trace_active=1;
}
static void tree_trace_finish(){
 tree_trace_active=0;
 for(unsigned i=0;i<tree_trace_points.size();++i){
  auto*byte=reinterpret_cast<unsigned char*>(tree_trace_points[i].pc);DWORD old{},ignored{};
  require(VirtualProtect(byte,1,PAGE_EXECUTE_READWRITE,&old),"Trace restore writable");
  *byte=tree_trace_original[i];
  require(FlushInstructionCache(GetCurrentProcess(),byte,1)&&VirtualProtect(byte,1,old,&ignored),"Trace source restore/protection");
 }
}

static bool tree_trace_debug(HANDLE child,const DEBUG_EVENT&event){
 const auto&exception=event.u.Exception.ExceptionRecord;
 const auto code=exception.ExceptionCode;
 if(code!=EXCEPTION_BREAKPOINT&&code!=EXCEPTION_SINGLE_STEP&&code!=0x4000001fU)return false;
 auto get=[&](const void*a,void*b,SIZE_T n){SIZE_T copied{};require(ReadProcessMemory(child,a,b,n,&copied)&&copied==n,"Trace actual stopped child read");};
 auto put=[&](void*a,const void*b,SIZE_T n){SIZE_T copied{};require(WriteProcessMemory(child,a,b,n,&copied)&&copied==n,"Trace observer output write");};
 unsigned active{},thread_owner{};get(&tree_trace_active,&active,4);if(!active)return false;
 get(&tree_trace_owner,&thread_owner,4);require(thread_owner==event.dwThreadId,"Trace source owner thread");
 mw34::original_broker::Handle thread(OpenThread(THREAD_GET_CONTEXT|THREAD_SET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,event.dwThreadId));
 require(thread.value!=nullptr,"Trace stopped thread handle");
 CONTEXT context{};context.ContextFlags=CONTEXT_FULL|CONTEXT_FLOATING_POINT|CONTEXT_EXTENDED_REGISTERS;
 require(GetThreadContext(thread.value,&context),"Actual stopped full x86 CONTEXT");
 static unsigned pending=~0U;static TreeTraceEvent measured{};
 auto patch=[&](unsigned pc,unsigned char value){DWORD old{},ignored{};auto*a=reinterpret_cast<void*>(pc);
  require(VirtualProtectEx(child,a,1,PAGE_EXECUTE_READWRITE,&old),"Stopped trace source writable");put(a,&value,1);
  require(FlushInstructionCache(child,a,1)&&VirtualProtectEx(child,a,1,old,&ignored),"Stopped trace source cache/protection");};
 auto cell_read=[&](TreeTraceCell&cell,bool after){
  unsigned value{};SIZE_T copied{};const bool ok=ReadProcessMemory(child,reinterpret_cast<void*>(cell.address),&value,cell.width,&copied)&&copied==cell.width;
  if(after){cell.after_valid=ok?1U:0U;cell.after_value=value;}else{cell.before_valid=ok?1U:0U;cell.before_value=value;}
 };
 if(code==EXCEPTION_SINGLE_STEP){
  require(pending<tree_trace_points.size(),"Single step belongs to an actual pending source instruction");
  measured.after=context;measured.next_pc=context.Eip;
  for(unsigned i=0;i<measured.cell_count;++i)cell_read(measured.cells[i],true);
  patch(tree_trace_points[pending].pc,0xcc);
  put(&tree_trace_events[measured.index],&measured,sizeof(measured));unsigned count=measured.index+1;put(&tree_trace_count,&count,4);
  pending=~0U;context.EFlags&=~0x100U;
  require(SetThreadContext(thread.value,&context),"Continue actual source with observer TF removed");return true;
 }
 const auto pc=static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(exception.ExceptionAddress));
 unsigned point=~0U;for(unsigned i=0;i<tree_trace_points.size();++i)if(tree_trace_points[i].pc==pc){point=i;break;}
 if(point==~0U)return false;
 require(pending==~0U&&context.Eip==pc+1,"Bounded first-opcode breakpoint continuation");
 unsigned count{},owners{};get(&tree_trace_count,&count,4);get(&lockit_allocation_count,&owners,4);
 require(count<16384&&owners<=64,"Bounded actual source events and live owner inventory");
 FsAllocation allocations[64]{};get(lockit_allocations,allocations,owners*sizeof(FsAllocation));
 measured={};measured.index=count;measured.source_pc=pc;measured.instruction_kind=tree_trace_points[point].kind;
 measured.owner_count_before=owners;measured.exception_eip=context.Eip;measured.before=context;
 measured.actual_first_opcode=tree_trace_points[point].opcode;
 const auto&p=tree_trace_points[point];measured.cell_count=p.count;
 for(unsigned i=0;i<p.count;++i){
  const auto&m=p.cells[i];auto&c=measured.cells[i];c.address=m.displacement;
  for(unsigned r=0;r<8;++r)c.address+=tree_register(context,r)*m.coefficients[r];
  c.width=m.width;c.read=m.read;c.write=m.write;c.segment=m.segment;c.owner_index=~0U;c.owner_offset=~0U;
  // FS source rows execute an accepted transparent observer JMP. Their actual
  // complete FS operation is retained by the raw FsEvent array, not guessed here.
  require(m.segment==0,"No debugger-internal FS head admitted as source memory");
  for(unsigned o=0;o<owners;++o){const auto&a=allocations[o];if(c.address>=a.pointer&&c.address-a.pointer<=a.capacity&&c.width<=a.capacity-(c.address-a.pointer)){
   require(c.owner_index==~0U,"Unique physical live owner covers complete measured cell");c.owner_index=o;c.generation=o+1;c.owner_offset=c.address-a.pointer;
  }}
  cell_read(c,false);
 }
 unsigned char actual{};get(reinterpret_cast<void*>(pc),&actual,1);require(actual==0xcc,"Actual installed source breakpoint");
 patch(pc,static_cast<unsigned char>(p.opcode));context.Eip=pc;context.EFlags|=0x100U;pending=point;
 require(SetThreadContext(thread.value,&context),"Execute the genuine one source instruction with observer TF");return true;
}
