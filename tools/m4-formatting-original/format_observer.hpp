#pragma once
// Actual source-call observations. Bounds are storage limits, not expected counts.
extern "C" {
Cpu format_cpu{};unsigned format_head{},format_kind{},format_count{},format_owner_count{};
alignas(16) unsigned char format_fx[512]{};unsigned char format_env[28]{};
unsigned format_targets[3]{},format_continues[3]{0x4dea20,0x4deabc,0x4deade};
struct FormatString {unsigned pointer,length;unsigned char bytes[128];};
struct FormatSnapshot {unsigned words[16];Cpu cpu;unsigned char fx[512],env[28],frame[32];FormatString strings[4];unsigned char owned[1024];};
struct FormatOwner {unsigned words[16];unsigned char initial[1024];};
static_assert(sizeof(FormatSnapshot)==2244&&sizeof(FormatOwner)==1088);
FormatSnapshot format_snapshots[64]{};FormatOwner format_owners[16]{};
unsigned format_entry_args[3][5]{},format_entry_API[3]{},format_active_owner=0xffffffff;
void format_entry_strrchr();void format_return_strrchr();void format_entry_malloc();void format_return_malloc();void format_entry_sprintf();void format_return_sprintf();
void format_string(FormatString&s,unsigned pointer){
 s.pointer=pointer;if(!pointer)return;
 for(unsigned i=0;i<128;++i){const auto b=*reinterpret_cast<const unsigned char*>(pointer+i);s.bytes[i]=b;s.length=i+1;if(!b)return;}
 fs_error=1;
}
void format_observe(){
 const auto last_error=GetLastError();
 if(!fs_phase_root||format_count>=64||format_kind>=6){fs_error=1;return;}
 const auto type=format_kind/2,F=format_cpu.esp;
 if(F<0x20001000||F+32>0x20002000){fs_error=1;return;}
 auto&s=format_snapshots[format_count];s={};s.words[0]=1;s.words[1]=format_count;s.words[2]=fs_phase_root;s.words[3]=format_kind;s.words[4]=format_cpu.pc;s.words[5]=format_head;s.words[6]=GetCurrentThreadId();s.words[7]=format_targets[type];s.words[8]=type==0?0x4dea15:type==1?0x4deab1:0x4dead1;
 s.words[12]=format_entry_API[type];s.words[13]=registry_API_count;s.words[14]=0xffffffff;s.cpu=format_cpu;
 std::memcpy(s.fx,format_fx,512);std::memcpy(s.env,format_env,28);std::memcpy(s.frame,reinterpret_cast<void*>(F),32);
 if(!(format_kind&1)){std::memcpy(format_entry_args[type],reinterpret_cast<void*>(F),20);format_entry_API[type]=registry_API_count;s.words[12]=registry_API_count;s.cpu.pc=format_targets[type];s.words[4]=s.cpu.pc;}
 const auto*w=format_entry_args[type];
 if(type==0){format_string(s.strings[0],w[1]);}
 if(type==1){s.words[9]=w[1];if(format_kind&1){
  if(!format_cpu.eax||format_owner_count>=16){fs_error=1;return;}
  unsigned ai=0xffffffff;for(unsigned i=format_entry_API[type];i<registry_API_count;++i)if(registry_API_ledger[i].kind==0&&registry_API_ledger[i].after.eax==format_cpu.eax){if(ai!=0xffffffff){fs_error=1;return;}ai=i;}
  if(ai==0xffffffff||registry_initial_sizes[ai]<w[1]||registry_initial_sizes[ai]>1024){fs_error=1;return;}
  auto&o=format_owners[format_owner_count];o={};o.words[0]=1;o.words[1]=format_owner_count;o.words[2]=fs_phase_root;o.words[3]=0x4deab1;o.words[4]=w[1];o.words[5]=format_cpu.eax;o.words[6]=registry_initial_sizes[ai];o.words[7]=ai;o.words[8]=registry_API_ledger[ai].args[0];o.words[9]=registry_API_ledger[ai].args[2];o.words[10]=format_cpu.esp;o.words[11]=format_cpu.pc;
  std::memcpy(o.initial,registry_initial_bytes[ai],o.words[6]);format_active_owner=format_owner_count++;
 }}
 if(type==2){format_string(s.strings[0],w[2]);format_string(s.strings[1],w[3]);format_string(s.strings[2],w[4]);}
 if(type>=1&&format_active_owner!=0xffffffff){const auto&o=format_owners[format_active_owner];s.words[10]=o.words[5];s.words[11]=o.words[6];s.words[14]=o.words[7];s.words[15]=o.words[6];std::memcpy(s.owned,reinterpret_cast<void*>(o.words[5]),o.words[6]);}
 ++format_count;SetLastError(last_error);
}
}
struct FormatHook {unsigned pc,size;void(*entry)();unsigned char raw[7];};
const std::array<FormatHook,3> format_hooks{{
 {0x4dea1b,5,&format_return_strrchr,{0x83,0xc4,0x08,0x3b,0xc3}},
 {0x4deab7,5,&format_return_malloc,{0x83,0xc4,0x04,0x3b,0xc3}},
 {0x4dead7,7,&format_return_sprintf,{0x83,0xc4,0x10,0x8b,0x44,0x24,0x20}}
}};
