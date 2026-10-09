"""Bounded original FS observers; source registers never spill on guest stack."""
HOOKS=[
 (0x4e78d7,0,'64a100000000'),(0x4e78de,1,'64892500000000'),(0x4e799f,2,'64890d00000000'),
 (0x48f297,0,'64a100000000'),(0x48f29e,1,'64892500000000'),(0x48f360,2,'64890d00000000'),
 (0x4d48f7,0,'64a100000000'),(0x4d48fe,1,'64892500000000'),(0x4d4948,2,'64890d00000000')]

CPP=r'''
// Fixed bounded observation arrays. No source computation or AFTER seed.
extern "C" {
Cpu fs_before_cpu{},fs_after_cpu{};unsigned fs_before_head{},fs_after_head{},fs_event_kind{},fs_phase_root{},fs_error{},fs_event_count{};
alignas(16) unsigned char fs_before_fx[512]{},fs_after_fx[512]{};unsigned char fs_before_env[28]{},fs_after_env[28]{};
struct FsEvent {unsigned version,root,pc,kind,head_before,head_after,record_address,record_captured;Cpu before,after;unsigned char record_before[12],record_after[12],fx_before[512],fx_after[512],env_before[28],env_after[28];};
static_assert(sizeof(FsEvent)==1216);
FsEvent fs_events[64]{};
void fs_observe_before(){
 if(fs_event_count>=64){fs_error=1;return;}auto&e=fs_events[fs_event_count];e={};e.version=1;e.root=fs_phase_root;e.pc=fs_before_cpu.pc;e.kind=fs_event_kind;e.head_before=fs_before_head;e.before=fs_before_cpu;
 const auto address=fs_event_kind==1?fs_before_cpu.esp:fs_before_head;e.record_address=address;
 if(address>=0x20001000&&address+12<=0x20002000){e.record_captured=1;std::memcpy(e.record_before,reinterpret_cast<void*>(address),12);}
 std::memcpy(e.fx_before,fs_before_fx,512);std::memcpy(e.env_before,fs_before_env,28);
}
void fs_observe_after(){
 if(fs_event_count>=64){fs_error=1;return;}auto&e=fs_events[fs_event_count];e.head_after=fs_after_head;e.after=fs_after_cpu;
 if(e.record_captured)std::memcpy(e.record_after,reinterpret_cast<void*>(e.record_address),12);
 std::memcpy(e.fx_after,fs_after_fx,512);std::memcpy(e.env_after,fs_after_env,28);
 bool transparent=e.before.ecx==e.after.ecx&&e.before.edx==e.after.edx&&e.before.ebx==e.after.ebx&&e.before.esp==e.after.esp&&e.before.ebp==e.after.ebp&&e.before.esi==e.after.esi&&e.before.edi==e.after.edi&&e.before.flags==e.after.flags;
 transparent=transparent&&(e.kind==0?e.after.eax==e.head_before:e.before.eax==e.after.eax);
 transparent=transparent&&(e.kind==0?e.head_after==e.head_before:e.kind==1?e.head_after==e.before.esp:e.head_after==e.before.ecx);
 transparent=transparent&&!std::memcmp(e.fx_before,e.fx_after,512)&&!std::memcmp(e.env_before,e.env_after,28)&&!std::memcmp(e.record_before,e.record_after,12);
 if(!transparent)fs_error=1;++fs_event_count;
}
}
'''

def asm():
 lines=['.686p','.xmm','.model flat, C','assume fs:nothing','option casemap:none']
 for name,typ in [('mixed_host_esp','DWORD'),('fs_before_cpu','BYTE'),('fs_after_cpu','BYTE'),('fs_before_head','DWORD'),('fs_after_head','DWORD'),('fs_event_kind','DWORD'),('fs_before_fx','BYTE'),('fs_after_fx','BYTE'),('fs_before_env','BYTE'),('fs_after_env','BYTE'),('fs_observe_before','PROC'),('fs_observe_after','PROC')]:lines.append('EXTERN '+name+':'+typ)
 lines+=['.code']
 registers=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
 def capture(prefix,pc):
  result=[f' mov DWORD PTR {prefix}_cpu[{i*4}],{r}'for i,r in enumerate(registers)]
  result += [f' mov DWORD PTR {prefix}_cpu[36],{pc:08x}h',' mov esp,mixed_host_esp',' pushfd',f' pop DWORD PTR {prefix}_cpu[32]',' mov eax,DWORD PTR fs:[0]',f' mov {prefix}_head,eax',f' fxsave {prefix}_fx',f' fnstenv {prefix}_env',f' fldenv {prefix}_env',f' call fs_observe_{prefix.removeprefix("fs_")}',f' fxrstor {prefix}_fx',f' fldenv {prefix}_env',f' push DWORD PTR {prefix}_cpu[32]',' popfd']
  result += [f' mov {r},DWORD PTR {prefix}_cpu[{i*4}]'for i,r in enumerate(registers)if r!='esp']
  result += [f' mov esp,DWORD PTR {prefix}_cpu[16]']
  return result
 for pc,kind,raw in HOOKS:
  lines.insert(lines.index('.code'),f'EXTERN fs_continue_{pc:x}:DWORD')
  name=f'fs_hook_{pc:x}';lines += ['PUBLIC '+name,name+' PROC',f' mov fs_event_kind,{kind}']
  lines += capture('fs_before',pc)
  lines += [' db '+','.join(f'0{x:02x}h'for x in bytes.fromhex(raw))]
  lines += capture('fs_after',pc)
  lines += [f' jmp DWORD PTR fs_continue_{pc:x}',name+' ENDP']
 lines+=['END'];return '\n'.join(lines)+'\n'

def declarations():return '\n'.join(f'extern "C" void fs_hook_{pc:x}();\nextern "C" const unsigned fs_continue_{pc:x}={hex(pc+len(bytes.fromhex(r)))};'for pc,k,r in HOOKS)+'\n'

def hook_table():
 return 'struct FsHook{unsigned pc,size,kind;void(*entry)();unsigned char raw[7];};\nconst std::array<FsHook,9> fs_hooks{{'+','.join('{'+f'{hex(pc)},{len(bytes.fromhex(raw))},{kind},&fs_hook_{pc:x},'+'{'+','.join(hex(x)for x in bytes.fromhex(raw))+'}}'for pc,kind,raw in HOOKS)+'}};\n'
