#pragma once
// Genuine entry and first game return instruction; no expected numeric input.
extern "C" {
Cpu hypot_cpu{};unsigned hypot_head{},hypot_kind{},hypot_count{},hypot_target{};
unsigned hypot_continues[2]{0x4b58c3,0x4b58ee};
alignas(16) unsigned char hypot_fx[512]{};unsigned char hypot_env[28]{};
struct HypotSnapshot {unsigned header[16];Cpu cpu;unsigned char fx[512],env[28],frame[32],stack[4096],source_page[4096],CRT_pages[64*4096];};
static_assert(sizeof(HypotSnapshot)==271012);
HypotSnapshot hypot_snapshots[8]{};
void hypot_entry();void hypot_return_first();void hypot_return_second();
void hypot_observe(){
 const auto saved_error=GetLastError();
 if(fs_phase_root!=0x4b5910||hypot_count>=8||hypot_kind>2||hypot_cpu.esp<0x20001000||hypot_cpu.esp+32>0x20002000){fs_error=1;SetLastError(saved_error);return;}
 auto&s=hypot_snapshots[hypot_count];s={};
 s.header[0]=1;s.header[1]=hypot_count;s.header[2]=fs_phase_root;s.header[3]=hypot_kind;s.header[4]=hypot_cpu.pc;s.header[5]=hypot_head;s.header[6]=GetCurrentThreadId();s.header[7]=hypot_target;s.header[8]=hypot_cpu.esp;s.header[9]=GetLastError();s.header[10]=registry_API_count;
 s.cpu=hypot_cpu;std::memcpy(s.fx,hypot_fx,512);std::memcpy(s.env,hypot_env,28);std::memcpy(s.frame,reinterpret_cast<void*>(hypot_cpu.esp),32);std::memcpy(s.stack,reinterpret_cast<void*>(0x20001000),4096);std::memcpy(s.source_page,reinterpret_cast<void*>(0x4b5000),4096);
 for(unsigned i=0;i<64;++i)std::memcpy(s.CRT_pages+i*4096,reinterpret_cast<void*>(0x78000000+i*4096),4096);
 ++hypot_count;SetLastError(saved_error);
}
}
struct HypotHook {unsigned pc,size;void(*entry)();unsigned char raw[5];};
const std::array<HypotHook,2>hypot_hooks{{
 {0x4b58be,5,&hypot_return_first,{0xd9,0x46,0x08,0xd9,0xc9}},
 {0x4b58e9,5,&hypot_return_second,{0xd9,0x46,0x0c,0xd9,0xc9}}
}};
