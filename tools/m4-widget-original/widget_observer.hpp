#pragma once
// Hardware observations only. Counts and handles come from actual source calls.
inline constexpr std::array<unsigned,3> widget_IATs{0x5bb070,0x5bb074,0x5bb068};
inline constexpr std::array<unsigned,3> widget_return_PCs{0x5a0142,0x5a0645,0x5a0751};
inline constexpr std::array<unsigned,3> widget_argc{1,1,14};
extern "C" {
Cpu widget_cpu{};unsigned widget_head{},widget_kind{},widget_count{},widget_error{};
unsigned widget_targets[3]{},widget_continues[3]{0x5a0148,0x5a064f,0x5a0759};
alignas(16) unsigned char widget_fx[512]{};unsigned char widget_env[28]{};
struct WidgetSnapshot {unsigned header[16];Cpu cpu;unsigned char fx[512],env[28],frame[64],FS_view[16],source_page[4096],pages[64*4096];};
static_assert(sizeof(WidgetSnapshot)==266964);
WidgetSnapshot widget_snapshots[384]{};
struct WidgetResource {unsigned version,index,root,instance,handle,created_event,live,deleted_event;};
static_assert(sizeof(WidgetResource)==32);
WidgetResource widget_resources[128]{};unsigned widget_resource_count{};
void widget_stock_entry();void widget_stock_return();
void widget_delete_entry();void widget_delete_return();
void widget_create_entry();void widget_create_return();
void widget_observe(){
 const auto error=GetLastError();
 if(!fs_phase_root||widget_kind>5||widget_count>=384||widget_cpu.esp<0x20001000||widget_cpu.esp+64>0x20002000){widget_error=1;SetLastError(error);return;}
 const auto api=widget_kind/2;const auto side=widget_kind%2;
 auto&s=widget_snapshots[widget_count];s={};
 s.header[0]=1;s.header[1]=widget_count;s.header[2]=fs_phase_root;s.header[3]=widget_kind;s.header[4]=widget_cpu.pc;s.header[5]=widget_head;s.header[6]=GetCurrentThreadId();s.header[7]=widget_targets[api];s.header[8]=widget_cpu.esp;s.header[9]=error;s.header[10]=registry_API_count;s.header[11]=widget_cpu.esi;s.header[12]=widget_argc[api];s.header[13]=widget_resource_count;
 s.cpu=widget_cpu;std::memcpy(s.fx,widget_fx,512);std::memcpy(s.env,widget_env,28);std::memcpy(s.frame,reinterpret_cast<void*>(widget_cpu.esp),64);
 if(widget_head>=0x20001000&&widget_head+16<=0x20002000){s.header[14]=1;std::memcpy(s.FS_view,reinterpret_cast<void*>(widget_head),16);}
 std::memcpy(s.source_page,reinterpret_cast<void*>(0x5a0000),4096);
 for(unsigned i=0;i<widget_whole_pages.size();++i)std::memcpy(s.pages+i*4096,reinterpret_cast<void*>(widget_whole_pages[i]),4096);
 if(!side){if(*reinterpret_cast<unsigned*>(s.frame)!=widget_return_PCs[api]||s.cpu.pc!=widget_targets[api])widget_error=1;}
 else{
  if(!widget_count){widget_error=1;SetLastError(error);return;}
  const auto&e=widget_snapshots[widget_count-1];
  if(e.header[3]+1!=widget_kind||e.header[2]!=fs_phase_root||e.cpu.esi!=s.cpu.esi||e.cpu.esp+4*(widget_argc[api]+1)!=s.cpu.esp||s.cpu.pc!=widget_return_PCs[api])widget_error=1;
  if(api==2&&s.cpu.eax){
   if(widget_resource_count>=128)widget_error=1;
   else {auto&r=widget_resources[widget_resource_count];r={1,widget_resource_count,fs_phase_root,s.cpu.esi,s.cpu.eax,widget_count,1,0xffffffff};++widget_resource_count;}
  }
  if(api==1&&s.cpu.eax){const unsigned handle=*reinterpret_cast<const unsigned*>(e.frame+4);for(unsigned i=0;i<widget_resource_count;++i){auto&r=widget_resources[i];if(r.live&&r.handle==handle&&r.instance==s.cpu.esi){r.live=0;r.deleted_event=widget_count;}}}
 }
 ++widget_count;SetLastError(error);
}
}
struct WidgetHook {unsigned pc,size;void(*entry)();unsigned char raw[10];};
const std::array<WidgetHook,3> widget_hooks{{
 {0x5a0142,6,&widget_stock_return,{0x89,0x86,0x58,0x02,0x00,0x00}},
 {0x5a0645,10,&widget_delete_return,{0xc7,0x86,0x58,0x02,0x00,0x00,0x00,0x00,0x00,0x00}},
 {0x5a0751,8,&widget_create_return,{0x85,0xc0,0x89,0x86,0x58,0x02,0x00,0x00}}
}};
inline const std::array<void(*)(),3> widget_entries{&widget_stock_entry,&widget_delete_entry,&widget_create_entry};
struct WidgetCleanup {unsigned version,resource_index,instance,handle,BOOL_result,error_before,error_after,manual_research_seam;unsigned char fx_before[512],fx_after[512],env_before[28],env_after[28];};
static_assert(sizeof(WidgetCleanup)==1112);
inline WidgetCleanup widget_cleanup_resource(unsigned index){
 auto&r=widget_resources[index];require(r.live&&r.handle,"Actual owned created font cleanup admission");WidgetCleanup c{};c.version=1;c.resource_index=index;c.instance=r.instance;c.handle=r.handle;c.manual_research_seam=1;c.error_before=GetLastError();
 // Inline assembly names concrete aligned buffers; copies happen outside the API.
 alignas(16) unsigned char before[512]{},after[512]{};unsigned char benv[28]{},aenv[28]{};
 __asm fxsave before
 __asm fnstenv benv
 __asm fldenv benv
 const auto result=reinterpret_cast<BOOL(WINAPI*)(HGDIOBJ)>(widget_targets[1])(reinterpret_cast<HGDIOBJ>(r.handle));
 __asm fxsave after
 __asm fnstenv aenv
 __asm fldenv aenv
 c.BOOL_result=static_cast<unsigned>(result);c.error_after=GetLastError();std::memcpy(c.fx_before,before,512);std::memcpy(c.fx_after,after,512);std::memcpy(c.env_before,benv,28);std::memcpy(c.env_after,aenv,28);if(result){r.live=0;r.deleted_event=0xfffffffe;}return c;
}
