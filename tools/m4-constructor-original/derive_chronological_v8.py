"""Retain strict legacy applicability and record exact first observer fault."""
from pathlib import Path
import ast
here=Path(__file__).resolve().parent
source=here/'prepare_chronological_v7.py';target=here/'prepare_chronological_v8.py'
if target.exists():raise ValueError('Fresh additive generator required')
t=source.read_text()
def one(a,b):
    global t
    if t.count(a)!=1:raise ValueError('Exact generator hunk '+a[:80])
    t=t.replace(a,b,1)
one("declarations+=text(HERE/'normal_observer_v2.hpp')", "declarations+=text(HERE/'normal_observer_v3.hpp')")
one("        ref=ref.replace('Original131'", """        oldnull='inline constexpr std::array<NullFreeBinding,5> nullfree_bindings{{{0x4ada90,0x4ad8d8},{0x4b12d0,0x4b1210},{0x4b12d0,0x4b1287},{0x4d84a0,0x4d82ec},{0x5a7dc0,0x5a87cf}}};'
        newnull='inline constexpr std::array<NullFreeBinding,7> nullfree_bindings{{{0x4ada90,0x4ad8d8},{0x4b12d0,0x4b1210},{0x4b12d0,0x4b1287},{0x4d84a0,0x4d82ec},{0x5a7dc0,0x5a87cf},{0x4103f0,0x58af9a},{0x410440,0x58af9a}}};'
        (out/'spec.hpp').write_text(one((out/'spec.hpp').read_text(),oldnull,newnull))
        # Every strict observer rejection still sets fs_error. Only the first
        # code line/root is retained; no observer prints or calls CRT services.
        need('ctor_record_fs_failure'not in ref,'Fresh first-fault diagnostic')
        ref=ref.replace('fs_error=1','ctor_record_fs_failure(__LINE__)')
        diag='unsigned ctor_fs_failure_line{},ctor_fs_failure_root{};\\nvoid ctor_record_fs_failure(unsigned line){if(!fs_error){ctor_fs_failure_line=line;ctor_fs_failure_root=fs_phase_root;}fs_error=1;}\\n'
        ref=one(ref,'FsEvent fs_events[256]{};','FsEvent fs_events[256]{};\\n'+diag)
        ref=one(ref,'constructor_occurrences.clear();registry_API_count=0;fs_error=0;', 'constructor_occurrences.clear();registry_API_count=0;fs_error=0;ctor_fs_failure_line=0;ctor_fs_failure_root=0;')
        ref=one(ref,'fs_event_count=0;fs_error=0;vtable_count=0;', 'fs_event_count=0;fs_error=0;ctor_fs_failure_line=0;ctor_fs_failure_root=0;vtable_count=0;')
        diagnostic='if(fs_error)std::cerr<<"Constructor37 first observer fault sequence="<<sequence<<" phase="<<phase<<" root="<<std::hex<<ctor_fs_failure_root<<" source-line="<<std::dec<<ctor_fs_failure_line<<" FS-count="<<fs_event_count<<" NULL-count="<<nullfree_count<<" NULL-PC="<<std::hex<<nullfree_cpu.pc<<" NULL-frame="<<nullfree_cpu.esp<<" vtable-PC="<<vtable_cpu.pc<<" normal-count="<<std::dec<<constructor_normal_count<<"\\\\n";'
        ref=one(ref,'fs_phase_root=0;require(!fs_error,"Exact FS observer/allocation transparency");','fs_phase_root=0;'+diagnostic+'require(!fs_error,"Exact FS observer/allocation transparency");')
        ref=ref.replace('Original131'""")
one("source_AFTER_seed=False,new_callback_shutdown_executed=False", "new_NULL_free_bindings=[dict(root=0x4103f0,CALL_PC=0x58af9a,return_PC=0x58af9f),dict(root=0x410440,CALL_PC=0x58af9a,return_PC=0x58af9f)],legacy_guards_unchanged=True,first_observer_fault_diagnostic=True,getter_whole_PE_receiver_and_readonly_slot=True,source_AFTER_seed=False,new_callback_shutdown_executed=False")
one("pin(HERE/'derive_chronological_v7.py');pin(HERE/'normal_observer.hpp');", "pin(HERE/'derive_chronological_v7.py');pin(HERE/'prepare_chronological_v7.py');pin(HERE/'derive_chronological_v8.py');pin(HERE/'normal_observer_v3.hpp');pin(HERE/'normal_observer.hpp');")
ast.parse(t);target.write_text(t)

base=(here/'normal_observer_v2.hpp').read_text();new=here/'normal_observer_v3.hpp'
if new.exists():raise ValueError('Fresh additive observer required')
base=base.replace('fs_error=1','ctor_record_fs_failure(__LINE__)')
old='''        if((vptr!=0x5bcc68&&vptr!=0x5cab60&&vptr!=0x5ca6d8)||dword(vptr+0x18)!=0x40a850){ctor_record_fs_failure(__LINE__);return;}'''
replacement='''        bool receiver_page=false,vptr_page=false;
        for(unsigned p:observed_pages){if((ctor_cpu.ecx&~4095U)==p)receiver_page=true;if((vptr&~4095U)==p)vptr_page=true;}
        MEMORY_BASIC_INFORMATION receiver_region{},vptr_region{};
        const bool geometry=receiver_page&&vptr_page&&(ctor_cpu.ecx&4095U)+8<=4096&&(vptr&4095U)+0x1c<=4096;
        if(!geometry||VirtualQuery(reinterpret_cast<void*>(ctor_cpu.ecx),&receiver_region,sizeof(receiver_region))!=sizeof(receiver_region)||VirtualQuery(reinterpret_cast<void*>(vptr),&vptr_region,sizeof(vptr_region))!=sizeof(vptr_region)||receiver_region.State!=MEM_COMMIT||vptr_region.State!=MEM_COMMIT||receiver_region.Protect!=PAGE_READWRITE||vptr_region.Protect!=PAGE_READONLY||ctor_cpu.edx!=vptr||dword(vptr+0x18)!=0x40a850){ctor_record_fs_failure(__LINE__);return;}
        // The receiver is source-owned PE memory retained as a whole page.
        // Its actual publication is a payload in the genuine current list.
        bool published=false;const unsigned header=dword(0x603fdc);unsigned node=header;
        for(unsigned n=0;node&&n<256;++n){unsigned raw[3]{};if(!safe_read(reinterpret_cast<void*>(node),raw,sizeof(raw))){ctor_record_fs_failure(__LINE__);return;}if(raw[2]==ctor_cpu.ecx)published=true;node=raw[0];if(node==header)break;if(n==255){ctor_record_fs_failure(__LINE__);return;}}
        if(!published){ctor_record_fs_failure(__LINE__);return;}
        constructor_getter_backings[constructor_normal_count]={1,constructor_normal_count,ctor_cpu.ecx,ctor_cpu.ecx&~4095U,vptr,vptr&~4095U,vptr+0x18,dword(vptr+0x18),receiver_region.Protect,vptr_region.Protect};'''
if base.count(old)!=1:raise ValueError('Exact getter admission hunk')
base=base.replace(old,replacement,1)
base=base.replace('static unsigned constructor_normal_count{};', 'static unsigned constructor_normal_count{};\nstatic std::array<unsigned,10>constructor_getter_backings[256]{};',1)
old='''    constructor_dump(stem+"/normal-records.bin",constructor_normal_records,constructor_normal_count*sizeof(ConstructorNormalSnapshot));'''
if base.count(old)!=1:raise ValueError('Exact companion export hunk')
base=base.replace(old,old+'\n    constructor_dump(stem+"/getter-backings.bin",constructor_getter_backings,constructor_normal_count*sizeof(constructor_getter_backings[0]));',1)
new.write_text(base)
