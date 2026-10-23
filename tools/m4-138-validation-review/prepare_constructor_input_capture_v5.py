"""Unbuilt additive current37 constructor own-provider/segment capture supplement."""
from pathlib import Path
import json,hashlib,shutil,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 parent=R/'reports/m4-constructor-original/chronological-preparation-r10';out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};relations=[]
 def pin(p):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();pins[str(p)]=v;return v
 for p in parent.iterdir():
  if p.is_file()and p.name!='report.json':shutil.copyfile(p,out/p.name);pin(p)
 pin(parent/'report.json');src=(parent/'reference.cpp').read_text();changes=[]
 def replace(old,new):
  nonlocal src
  assert src.count(old)==1;src=src.replace(old,new);changes.append(dict(old=old,new=new))
 old='static std::uint32_t execute(){__try{registry_API_active=1;mixed_enter();'
 helper="""// Captured inside execute's existing SEH scope, before genuine guest entry.
static std::array<unsigned,34> constructor_input_segments{};
static void capture_constructor_input_segments(){
 const auto gle=GetLastError();unsigned cs{},ds{},es{},ss{},fs{},gs{};
 __asm {
  xor eax,eax
  mov ax,cs
  mov cs,eax
 }
}
"""
 # Distinct C++ variable names prevent selector/register ambiguity in MSVC ASM.
 helper="""// Own segment descriptor observations, inside existing execute SEH scope.
static std::array<unsigned,34> constructor_input_segments{};
static void capture_constructor_input_segments(){
 const auto gle=GetLastError();unsigned seg_cs{},seg_ds{},seg_es{},seg_ss{},seg_fs{},seg_gs{};
 __asm {
  xor eax,eax
  mov ax,cs
  mov seg_cs,eax
  mov ax,ds
  mov seg_ds,eax
  mov ax,es
  mov seg_es,eax
  mov ax,ss
  mov seg_ss,eax
  mov ax,fs
  mov seg_fs,eax
  mov ax,gs
  mov seg_gs,eax
 }
 constructor_input_segments={};constructor_input_segments[0]=1;constructor_input_segments[1]=fs_phase_root;constructor_input_segments[2]=GetCurrentThreadId();
 const std::array<unsigned,6>selectors{seg_cs,seg_ds,seg_es,seg_ss,seg_fs,seg_gs};
 for(unsigned i=0;i<6;++i){auto*w=constructor_input_segments.data()+4+5*i;w[0]=selectors[i];if(!selectors[i]){w[4]=1;continue;}LDT_ENTRY descriptor{};require(GetThreadSelectorEntry(GetCurrentThread(),selectors[i],&descriptor),"Own original selector descriptor query");w[1]=descriptor.BaseLow|(unsigned{descriptor.HighWord.Bytes.BaseMid}<<16)|(unsigned{descriptor.HighWord.Bytes.BaseHi}<<24);w[2]=descriptor.LimitLow|(unsigned{descriptor.HighWord.Bits.LimitHi}<<16);std::memcpy(&w[3],&descriptor.HighWord,4);w[4]=1;}
 unsigned self{},head{};__asm {
  mov eax,fs:[18h]
  mov self,eax
  mov eax,fs:[0]
  mov head,eax
 }
 require(constructor_input_segments[25]==self,"Own actual FS descriptor base equals TIB self");constructor_input_segments[3]=head;SetLastError(gle);
}
"""
 replace(old,helper+old.replace('registry_API_active=1;','registry_API_active=1;if(fs_phase_root==0x4103f0||fs_phase_root==0x410440||fs_phase_root==0x459b40)capture_constructor_input_segments();'))
 # Existing bounded all-readable CRT image snapshot machinery; no sparse guessed input.
 replace('if(format_phase){for(unsigned page=0x78000000;page<0x78040000;page+=4096)', 'if(format_phase||constructor_phase){for(unsigned page=0x78000000;page<0x78040000;page+=4096)')
 anchor='            if(constructor_phase){const unsigned actual=dword(0x5bb4bc);'
 binding="""            if(constructor_phase){
             const std::array<unsigned,8>cells{0x7802e094,0x7802e090,0x7802e1dc,0x7802e0b4,0x7802e03c,0x7802e044,0x7802e048,0x7802e040};
             const std::array<const char*,8>names{"HeapAlloc","HeapFree","HeapSize","HeapReAlloc","InitializeCriticalSection","EnterCriticalSection","LeaveCriticalSection","DeleteCriticalSection"};std::array<unsigned,56>bindings{};
             const auto gle=GetLastError();for(unsigned i=0;i<8;++i){const auto declared=GetModuleHandleW(L"kernel32.dll");const unsigned target=reinterpret_cast<unsigned>(GetProcAddress(declared,names[i]));HMODULE owner_module{};require(target==registry_API_targets[i]&&dword(cells[i])==reinterpret_cast<unsigned>(registry_shims[i])&&GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(target),&owner_module),"Own current constructor exact API named target and declared observer cell");auto*w=bindings.data()+7*i;w[0]=i;w[1]=cells[i];w[2]=dword(cells[i]);w[3]=target;w[4]=reinterpret_cast<unsigned>(registry_shims[i]);w[5]=reinterpret_cast<unsigned>(declared);w[6]=reinterpret_cast<unsigned>(owner_module);}out.append(phase_stem+"/constructor-input/named-API-bindings.bin",bindings.data(),sizeof(bindings));SetLastError(gle);
            }
"""
 replace(anchor,binding+anchor)
 anchor='            constructor_collect(phase,phase_stem);if(constructor_phase){'
 replace(anchor,'            if(constructor_phase){require(constructor_input_segments[0]==1&&constructor_input_segments[1]==entries[phase],"Own constructor input segment identity");out.append(phase_stem+"/constructor-input/segments-before.bin",constructor_input_segments.data(),sizeof(constructor_input_segments));}\n'+anchor)
 # Typed actual CRT critical-section24 API inputs/outputs; inline BEFORE copy is integer-only.
 replace('void registry_observe_allocation(){',"""extern unsigned fs_error;unsigned char registry_CS_before[256][24]{},registry_CS_after[256][24]{};unsigned registry_CS_seen_before[256]{};
void registry_observe_allocation(){
 if(registry_API_kind==5||registry_API_kind==6){const auto index=registry_API_count-1;if(index>=256||!registry_CS_seen_before[index]){fs_error=1;return;}std::memcpy(registry_CS_after[index],reinterpret_cast<void*>(registry_API_args[0]),24);}
""")
 anchor_CS='            require(registry_API_count<=256,"Bounded actualAPI ledger");'
 replace(anchor_CS,"""            if(constructor_phase){for(unsigned ai=0;ai<registry_API_count;++ai){const auto&e=registry_API_ledger[ai];if(e.kind!=5&&e.kind!=6)continue;require(registry_CS_seen_before[ai]==1,"Actual typed CRT CS API-before captured");const std::array<unsigned,5>cs_identity{1,ai,e.kind,e.args[0],e.ret};const auto stem=phase_stem+"/constructor-input/CS-API/"+std::to_string(ai);out.append(stem+"/identity.bin",cs_identity.data(),sizeof(cs_identity));out.append(stem+"/before.bin",registry_CS_before[ai],24);out.append(stem+"/after.bin",registry_CS_after[ai],24);}}
"""+anchor_CS)
 replace('            registry_API_count=0;std::memset(registry_API_ledger,0,sizeof(registry_API_ledger));', '            std::memset(registry_CS_seen_before,0,sizeof(registry_CS_seen_before));registry_API_count=0;std::memset(registry_API_ledger,0,sizeof(registry_API_ledger));')
 asm_parent=(parent/'reference_x86.asm').read_text();asm=asm_parent;asmchanges=[]
 def ar(old,new):
  nonlocal asm
  assert asm.count(old)==1;asm=asm.replace(old,new);asmchanges.append(dict(old=old,new=new))
 ar('EXTERN registry_observe_allocation:PROC', 'EXTERN registry_observe_allocation:PROC\nEXTERN registry_CS_before:BYTE\nEXTERN registry_CS_seen_before:DWORD')
 ar(' mov eax,registry_API_kind\n mov registry_API_active,0',""" ; Integer-only CS-before copy; every incoming register/flag restored before actual API.
 pushfd
 push eax
 push ecx
 push esi
 push edi
 mov eax,registry_API_kind
 cmp eax,5
 je cs_before_copy
 cmp eax,6
 jne cs_before_done
cs_before_copy:
 mov eax,registry_API_count
 cmp eax,256
 jae cs_before_overflow
 mov DWORD PTR registry_CS_seen_before[eax*4],1
 imul eax,eax,24
 lea edi,registry_CS_before[eax]
 mov esi,DWORD PTR registry_API_args[0]
 mov ecx,6
 cld
 rep movsd
 jmp cs_before_done
cs_before_overflow:
 mov fs_error,1
cs_before_done:
 pop edi
 pop esi
 pop ecx
 pop eax
 popfd
 mov eax,registry_API_kind
 mov registry_API_active,0""")
 reconstructed=asm
 for c in reversed(asmchanges):assert reconstructed.count(c['new'])==1;reconstructed=reconstructed.replace(c['new'],c['old'])
 assert reconstructed==asm_parent;(out/'reference_x86.asm').write_text(asm);(out/'asm-changes.json').write_text(json.dumps(asmchanges,indent=2));pin(out/'asm-changes.json')
 # Exact inverse and every untouched ordinary file preserved.
 recovered=src
 for c in reversed(changes):assert recovered.count(c['new'])==1;recovered=recovered.replace(c['new'],c['old'])
 assert recovered==(parent/'reference.cpp').read_text();(out/'reference.cpp').write_text(src)
 for p in parent.iterdir():
  if p.is_file()and p.name!='report.json':q=out/p.name;relations.append(dict(parent=str(p.resolve()),child=str(q.resolve()),parent_sha256=pin(p),child_sha256=pin(q),whole_equal=p.name not in('reference.cpp','reference_x86.asm')))
 (out/'changes.json').write_text(json.dumps(changes,indent=2));pin(out/'changes.json');pin(__file__)
 buildpins=json.loads((parent/'pins.json').read_text())['files']
 for file in out.iterdir():
  if file.is_file()and file.name!='pins.json':buildpins[str(file.resolve())]=pin(file)
 (out/'pins.json').write_text(json.dumps(dict(files=buildpins),indent=2));pin(out/'pins.json')
 plan=dict(passed=True,scope='Unbuilt current37 additive own constructor CRT-before/after, exact owning API/shim bindings and own segment descriptors inside existing execute SEH scope. Parent protocols/gates unchanged; build/prelaunch/controller/strict-validation adaptation still required.',parent_report=str((parent/'report.json').resolve()),source_relations=relations,exact_reference_inverse=True,changes=len(changes),asm_changes=len(asmchanges),asm_exact_inverse=True,CRT_CS24_API_inputs_outputs=True,physical_required_provider_pages=[0x5f498000,0x7802e000,0x78035000,0x78037000],already_captured_page=0x5f498000,dynamic_unknown_pages=[0x78035000,0x78037000],IAT_cell_not_static_reconstructible=True,IAT_observer_projection_requires_actual_named_binding=True,capture_CRT_interval=[0x78000000,0x78040000],maximum_additional_whole_CRT_page_bytes=18*64*4096*2,descriptor_schema=dict(words=34,header=['version','root','thread','head'],segment_order=['cs','ds','es','ss','fs','gs'],each=['selector','base','raw_limit','descriptor_high','observed']),FS_before_location='Inside existing execute __try immediately before mixed_enter; same source-visible exception chain scope. Compare head to first actual source FS-before event.',raw_CPU_PC_zero_retained=True,whole_original_State_claim=False,source_AFTER_seed=False,canonical_reader_opened=False,build_executed=False,worker_executed=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(plan,indent=2));print(pin(q))
if __name__=='__main__':main(sys.argv[1])
