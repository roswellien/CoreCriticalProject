#pragma once
// Genuine cdecl formatter observations. No source output/handle is predicted.
extern "C" {
Cpu fps_cpu{};unsigned fps_head{},fps_kind{},fps_count{},fps_error{},fps_target{},fps_continue{0x5a2f74};
unsigned short fps_ds{},fps_es{},fps_ss{};
alignas(16) unsigned char fps_fx[512]{};unsigned char fps_env[28]{};
struct FpsSnapshot {unsigned header[16];Cpu cpu;unsigned char fx[512],env[28],frame[64],FS_view[16],source_page[4096],pages[64*4096],CRT_pages[64*4096],va_input[64],format_input[16],destination[512];};
static_assert(sizeof(FpsSnapshot)==529700);
FpsSnapshot fps_snapshots[8]{};WidgetSegments fps_segments[8]{};
void fps_entry();void fps_return();
void fps_observe(){
 const auto error=GetLastError();
 if(!fs_phase_root||fps_kind>1||fps_count>=8||fps_cpu.esp<0x20001000||fps_cpu.esp+64>0x20002000){fps_error=1;SetLastError(error);return;}
 auto&segments=fps_segments[fps_count];segments={};segments.index=fps_count;segments.DS=fps_ds;segments.ES=fps_es;segments.SS=fps_ss;
 const unsigned selectors[3]{fps_ds,fps_es,fps_ss};
 for(unsigned i=0;i<3;++i){LDT_ENTRY descriptor{};if(!GetThreadSelectorEntry(GetCurrentThread(),selectors[i],&descriptor)){fps_error=1;continue;}std::memcpy(segments.descriptors+i*8,&descriptor,8);const unsigned base=descriptor.BaseLow|(static_cast<unsigned>(descriptor.HighWord.Bytes.BaseMid)<<16)|(static_cast<unsigned>(descriptor.HighWord.Bytes.BaseHi)<<24);if(base!=0||!descriptor.HighWord.Bits.Pres||!descriptor.HighWord.Bits.Default_Big)fps_error=1;}
 if(fps_cpu.flags&0x400)fps_error=1;
 auto&s=fps_snapshots[fps_count];s={};s.header[0]=1;s.header[1]=fps_count;s.header[2]=fs_phase_root;s.header[3]=fps_kind;s.header[4]=fps_cpu.pc;s.header[5]=fps_head;s.header[6]=GetCurrentThreadId();s.header[7]=fps_target;s.header[8]=fps_cpu.esp;s.header[9]=error;s.header[10]=registry_API_count;s.header[11]=fps_cpu.esi;s.header[12]=3;
 s.cpu=fps_cpu;std::memcpy(s.fx,fps_fx,512);std::memcpy(s.env,fps_env,28);std::memcpy(s.frame,reinterpret_cast<void*>(fps_cpu.esp),64);
 if(fps_head>=0x20001000&&fps_head+16<=0x20002000)std::memcpy(s.FS_view,reinterpret_cast<void*>(fps_head),16);
 if(fps_kind){if(!fps_count||fps_snapshots[fps_count-1].header[3]!=0){fps_error=1;SetLastError(error);return;}const auto&e=fps_snapshots[fps_count-1];if(e.cpu.esp+4!=s.cpu.esp||s.cpu.pc!=0x5a2f6e||e.cpu.esi!=s.cpu.esi)fps_error=1;for(unsigned i=0;i<3;++i)s.header[13+i]=e.header[13+i];}
 else{const auto*f=reinterpret_cast<const unsigned*>(s.frame);if(f[0]!=0x5a2f6e||s.cpu.pc!=fps_target)fps_error=1;for(unsigned i=0;i<3;++i)s.header[13+i]=f[i+1];}
 const unsigned destination=s.header[13],format=s.header[14],va=s.header[15];
 const auto admitted=[](unsigned address,unsigned extent){for(unsigned page:widget_whole_pages)if(page<=address&&address+extent>=address&&address+extent<=page+4096)return true;return false;};
 if(!admitted(destination,512)||!admitted(format,16)||va<0x20001000||va+64>0x20002000){fps_error=1;SetLastError(error);return;}
 std::memcpy(s.destination,reinterpret_cast<void*>(destination),512);std::memcpy(s.format_input,reinterpret_cast<void*>(format),16);std::memcpy(s.va_input,reinterpret_cast<void*>(va),64);
 std::memcpy(s.source_page,reinterpret_cast<void*>(0x5a2000),4096);
 for(unsigned i=0;i<widget_whole_pages.size();++i)std::memcpy(s.pages+i*4096,reinterpret_cast<void*>(widget_whole_pages[i]),4096);
 for(unsigned i=0;i<64;++i)std::memcpy(s.CRT_pages+i*4096,reinterpret_cast<void*>(0x78000000+i*4096),4096);
 ++fps_count;SetLastError(error);
}
}
