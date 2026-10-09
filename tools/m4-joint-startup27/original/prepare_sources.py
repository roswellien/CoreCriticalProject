"""Auditable original observer-only derivative of frozen hardware ancestors."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];TARGET=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def replace(s,a,b):
 assert s.count(a)==1,repr(a);return s.replace(a,b)
def main(out):
 out=Path(out).resolve();assert out.parent==ROOT/'reports/m4-joint-startup27' and not out.exists();out.mkdir(parents=True)
 sources={};changes=[]
 def read(rel):
  p=ROOT/rel;sources[str(p)]=sha(p);return p.read_text(encoding='utf-8-sig')
 p=read('tools/m4-mixed-startup/original/protocol.hpp')
 p=replace(p,'roots=26','roots=27');p=replace(p,'observed_page_count=11','observed_page_count=14')
 p=replace(p,'0x5e8000,0x604000,0x605000,0x60b000,0x20001000};','0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000};')
 p=replace(p,'    std::array<std::uint8_t,memory_size> memory_before,memory_after;','    std::array<std::uint8_t,memory_size> memory_before,memory_after;\n    std::array<std::uint8_t,716> checkpoint_context;\n    std::uint32_t checkpoint_seen;')
 p=replace(p,'sizeof(Record)==92388','sizeof(Record)==117684');p=replace(p,'memory_size==45056','memory_size==57344')
 (TARGET/'protocol.hpp').write_text(p)
 s=read('tools/m4-mixed-startup/original/reference.cpp')
 s=replace(s,'sizeof(void*)==4','sizeof(void*)==4 && sizeof(CONTEXT)==716')
 s=replace(s,'    if(auto broker=mw34::original_broker::dispatch(argc,argv,4))return *broker;','    const bool debugger=argc>1&&std::string(argv[argc-1])=="--checkpoint";mw34::original_broker::checkpoint_mode=debugger;\n    if(auto broker=mw34::original_broker::dispatch(argc,argv,debugger?6:5))return *broker;');s=replace(s,'require(argc==4,"Connected original: exact-pack exact-image fresh-output");','require(argc==(debugger?6:5),"Connected original27: exact-pack exact-image exact-provider fresh-output [--checkpoint]");')
 s=replace(s,'    const auto image=read(argv[2],2384384);require(image.size()==2384384&&sha256(image)==image_sha,"Image identity rejected");','    const auto image=read(argv[2],2384384);require(image.size()==2384384&&sha256(image)==image_sha,"Image identity rejected");\n    const auto provider=read(argv[3],565760);require(provider.size()==565760&&sha256(provider)=="91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a","Provider identity rejected");')
 s=replace(s,'"MW4MXP01"','"MW4J27P1"')
 s=replace(s,'    for(const auto&span:code_bindings)require(std::uint64_t{span.image_offset}+span.size<=image.size()&&std::uint64_t{span.pack_offset}+span.size<=pack.size()&&\n        std::memcmp(image.data()+span.image_offset,pack.data()+span.pack_offset,span.size)==0,"Selected original instruction/image binding rejected");','    for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;require(std::uint64_t{span.image_offset}+span.size<=origin.size(),"Original source extent rejected");}')
 s=replace(s,'std::array<void*,22> pages','std::array<void*,26> pages')
 s=replace(s,'    auto*stub=reinterpret_cast<std::uint8_t*>(capture_pc);','    for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Original committed instruction/source binding rejected");}\n    require(*reinterpret_cast<unsigned*>(0x5bb4fc)==0x780c10f0,"Declared owning IAT relocation rejected");\n    auto*stub=reinterpret_cast<std::uint8_t*>(capture_pc);')
 s=replace(s,'    Output out(argv[3]);Header header{};std::memcpy(header.magic,"MW4MXO01",8);','    owner=GetCurrentThreadId();\n    Output out(argv[4]);Header header{};std::memcpy(header.magic,debugger?"MW4J27D1":"MW4J27O1",8);')
 s=replace(s,'            r->tag.status=execute();copy_capture(*r);copy_pages(r->memory_after);r->tag.host_restored=host_restored(*r)?1U:0U;out.write(*r);','            checkpoint={};checkpoint_seen=0;checkpoint_pending=debugger&&entries[phase]==0x4c19f0;checkpoint_error=0;\n            if(checkpoint_pending){protect(reinterpret_cast<void*>(0x4c1000),PAGE_EXECUTE_READWRITE);require(*reinterpret_cast<std::uint8_t*>(0x4c1a09)==0xd9,"Checkpoint instruction identity differs");*reinterpret_cast<std::uint8_t*>(0x4c1a09)=0xcc;require(FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(0x4c1a09),1),"Checkpoint cache flush failed");protect(reinterpret_cast<void*>(0x4c1000),PAGE_EXECUTE_READ);}\n            r->tag.status=execute();copy_capture(*r);copy_pages(r->memory_after);r->tag.host_restored=host_restored(*r)?1U:0U;\n            std::memcpy(r->checkpoint_context.data(),&checkpoint,sizeof(checkpoint));r->checkpoint_seen=checkpoint_seen;out.write(*r);')
 s=replace(s,'r->after.esp!=returned_esp){','r->after.esp!=returned_esp||checkpoint_error||checkpoint_seen!=(debugger&&entries[phase]==0x4c19f0)){')
 s=replace(s,'        ++sequence;','        for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Original selected source changed after checkpoint");}\n        ++sequence;')
 s=replace(s,'48 connected sequences / 1248 actual original initializer phases captured','48 connected sequences / 1296 actual original initializer phases captured')
 checkpoint=read('tools/m4-fp-numeric-max/reference.cpp')
 checkpoint=checkpoint[checkpoint.index('static CONTEXT checkpoint{};'):checkpoint.index('struct Region {')]
 s=replace(s,'struct Region {',checkpoint+'\nstruct Region {')
 (TARGET/'reference.cpp').write_text(s)
 broker=read('tools/m4-fp-numeric-max/original_broker.hpp')
 broker=replace(broker,'inline constexpr std::array<std::uint32_t,7> bases{0x4c0000,0x5b0000,0x600000,0x10000000,0x20000000,0x780c0000,0x78110000};','inline constexpr std::array<std::uint32_t,14> bases{0x400000,0x410000,0x430000,0x460000,0x4a0000,0x4b0000,0x4c0000,0x5b0000,0x5c0000,0x5e0000,0x600000,0x20000000,0x780c0000,0x78110000};')
 broker=replace(broker,'inline bool adopting{};','inline bool adopting{};\ninline bool checkpoint_mode{};')
 broker=replace(broker,'CREATE_SUSPENDED|CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT|DEBUG_ONLY_THIS_PROCESS','CREATE_SUSPENDED|CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT|(checkpoint_mode?DEBUG_ONLY_THIS_PROCESS:0)')
 broker=replace(broker,'    const auto started=GetTickCount64();bool exited{};unsigned checkpoints{};','    if(!checkpoint_mode){const auto waited=WaitForSingleObject(child.value,deadline_ms);if(waited!=WAIT_OBJECT_0){TerminateJobObject(job.value,1);WaitForSingleObject(child.value,5000);throw std::runtime_error("Original direct broker deadline/wait failed");}DWORD code{};require(GetExitCodeProcess(child.value,&code)&&code!=STILL_ACTIVE,"Original direct child exit unavailable");std::cerr<<"Original direct broker child finished: pid="<<process.dwProcessId<<" exit="<<code<<\'\\n\';return static_cast<int>(code);}\n    const auto started=GetTickCount64();bool exited{};unsigned checkpoints{};')
 (TARGET/'original_broker.hpp').write_text(broker)
 asm=read('tools/m4-mixed-startup/original/reference_x86.asm');(TARGET/'reference_x86.asm').write_text(asm)
 for p,h in sources.items():assert sha(p)==h
 generated={str(p):sha(p)for p in TARGET.iterdir()if p.is_file()}
 report={'passed':True,'scope':'Original-only observer derivative; expanded sparse image, real provider code, one IAT relocation, literal numeric continuation debugger checkpoint; CPU/FP entry/capture ASM unchanged','ancestors':sources,'generated':generated,'guest_execution':False,'native_execution':False,'original_State_not_observed':True,'parent_checkpoint_context_never_overwrites_guest_FP':True,'whole_M4_complete':False}
 (out/'derivation.json').write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps({'files':sources|generated},indent=2)+'\n')
 print(json.dumps({'passed':True,'sources':len(sources),'derived_files':len(generated)}))
if __name__=='__main__':main(sys.argv[1])
