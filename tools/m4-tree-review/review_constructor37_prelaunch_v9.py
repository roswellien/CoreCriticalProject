"""Additive constructor admission: exact NULL routes and published getter owner."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
prior=R/'tools/m4-tree-review/review_constructor37_prelaunch_v8.py'
assert hashlib.sha256(prior.read_bytes()).hexdigest()=='10da1e96022871d688747d3aa5f2591a5f8224941431b7056ff542b2c51f0c82'
text=prior.read_text()
# Keep the existing complete physical review and replace only its current input seals.
changes={
 '6d3f97e734647085ee51c00538527e3e82ad31880d1310f946839be0e15720a0':'22cc8626a26963643e2a56d600c282f128f6db46920353f4e7ac58f81580cefe',
 '60e23288b3067cc7d78bbef9e2ca1286c941142a576a781ad7c2ffd2b2a53ac7':'03b93dd8035e24f091408442662cdcb1cb44532cc8af4d1a137efd9106a9948c',
 'chronological-preparation-r7':'chronological-preparation-r10',
 'chronological-build-r5':'chronological-build-r7',
}
for a,b in changes.items():
 assert text.count(a)==1,a
 text=text.replace(a,b)
hook="exec(compile(text,str(review_source),'exec'),globals())"
assert text.count(hook)==1
extra=r'''
        olddir=R/'reports/m4-constructor-original/chronological-preparation-r7'
        oldprep=read(olddir/'report.json','6d3f97e734647085ee51c00538527e3e82ad31880d1310f946839be0e15720a0')
        for leaf in ('pages.bin','selected-order.json','constructor-hook-bindings.json','constructor_observer_x86.asm','boundaries_x86.asm','normal-bindings.hpp'):
            if (olddir/leaf).exists():assert pin(olddir/leaf).read_bytes()==pin(folder/leaf).read_bytes(),leaf
        oldspec=pin(olddir/'spec.hpp').read_text()
        old='inline constexpr std::array<NullFreeBinding,5> nullfree_bindings{{{0x4ada90,0x4ad8d8},{0x4b12d0,0x4b1210},{0x4b12d0,0x4b1287},{0x4d84a0,0x4d82ec},{0x5a7dc0,0x5a87cf}}};'
        new='inline constexpr std::array<NullFreeBinding,7> nullfree_bindings{{{0x4ada90,0x4ad8d8},{0x4b12d0,0x4b1210},{0x4b12d0,0x4b1287},{0x4d84a0,0x4d82ec},{0x5a7dc0,0x5a87cf},{0x4103f0,0x58af9a},{0x410440,0x58af9a}}};'
        assert oldspec.count(old)==1 and oldspec.replace(old,new)==pin(folder/'spec.hpp').read_text()
        call=physical(game,0x58af9a,5);assert call[0]==0xe8 and 0x58af9f+struct.unpack_from('<i',call,1)[0]==0x5abd1a
        counts['exact_new_NULL_free_source_CALLs']=2
        oldref=pin(olddir/'reference.cpp').read_text().replace('fs_error=1','ctor_record_fs_failure(__LINE__,__FILE__)')
        def one(before,after):
            nonlocal_dummy=None
            assert oldref.count(before)==1,before
            return oldref.replace(before,after,1)
        diag='unsigned ctor_fs_failure_line{},ctor_fs_failure_root{};const char*ctor_fs_failure_source{};\nvoid ctor_record_fs_failure(unsigned line,const char*source){if(!fs_error){ctor_fs_failure_line=line;ctor_fs_failure_root=fs_phase_root;ctor_fs_failure_source=source;}fs_error=1;}\n'
        oldref=one('FsEvent fs_events[256]{};','FsEvent fs_events[256]{};\n'+diag)
        oldref=one('constructor_occurrences.clear();registry_API_count=0;fs_error=0;','constructor_occurrences.clear();registry_API_count=0;fs_error=0;ctor_fs_failure_line=0;ctor_fs_failure_root=0;')
        oldref=one('fs_event_count=0;fs_error=0;vtable_count=0;','fs_event_count=0;fs_error=0;ctor_fs_failure_line=0;ctor_fs_failure_root=0;vtable_count=0;')
        oldref=one('std::memset(constructor_normal_records,0,sizeof(constructor_normal_records));','std::memset(constructor_normal_records,0,sizeof(constructor_normal_records));std::memset(constructor_getter_backings,0,sizeof(constructor_getter_backings));')
        diagnostic='if(fs_error)std::cerr<<"Constructor37 first observer fault sequence="<<sequence<<" phase="<<phase<<" root="<<std::hex<<ctor_fs_failure_root<<" source="<<(ctor_fs_failure_source?ctor_fs_failure_source:"none")<<" source-line="<<std::dec<<ctor_fs_failure_line<<" FS-count="<<fs_event_count<<" NULL-count="<<nullfree_count<<" NULL-PC="<<std::hex<<nullfree_cpu.pc<<" NULL-frame="<<nullfree_cpu.esp<<" vtable-PC="<<vtable_cpu.pc<<" normal-count="<<std::dec<<constructor_normal_count<<"\\n";'
        oldref=one('fs_phase_root=0;require(!fs_error,"Exact FS observer/allocation transparency");','fs_phase_root=0;'+diagnostic+'require(!fs_error,"Exact FS observer/allocation transparency");')
        assert oldref==cpp,'Only memory-first diagnostics, exact companion reset and strict legacy guards remain'
        oldobserver=pin(olddir/'constructor_normal.hpp').read_text().replace('fs_error=1','ctor_record_fs_failure(__LINE__,__FILE__)')
        oldobserver=oldobserver.replace('static unsigned constructor_normal_count{};','static unsigned constructor_normal_count{};\nstatic std::array<unsigned,10>constructor_getter_backings[256]{};',1)
        oldguard='        if((vptr!=0x5bcc68&&vptr!=0x5cab60&&vptr!=0x5ca6d8)||dword(vptr+0x18)!=0x40a850){ctor_record_fs_failure(__LINE__,__FILE__);return;}'
        start=observer.index('        bool receiver_page=false,vptr_page=false;')
        end=observer.index('\n    }',start)
        guard=observer[start:end]
        assert guard.count('VirtualQuery(')==2 and guard.count('safe_read(')==1 and 'PAGE_READWRITE' in guard and 'PAGE_READONLY' in guard
        for token in ('(ctor_cpu.ecx&4095U)+8<=4096','(vptr&4095U)+0x1c<=4096','ctor_cpu.edx!=vptr','dword(vptr+0x18)!=0x40a850','node!=header&&raw[2]==ctor_cpu.ecx','if(!published)','n<256','if(node==header)break','if(n==255)','constructor_getter_backings[constructor_normal_count]={1,constructor_normal_count,ctor_cpu.ecx,ctor_cpu.ecx&~4095U,vptr,vptr&~4095U,vptr+0x18,dword(vptr+0x18),receiver_region.Protect,vptr_region.Protect}'):
            assert token in guard,token
        # Whole current guard is the independently inspected additive header;
        # preserve every line outside that bounded ownership expansion.
        assert oldobserver.count(oldguard)==1
        oldobserver=oldobserver.replace(oldguard,guard,1)
        export='    constructor_dump(stem+"/normal-records.bin",constructor_normal_records,constructor_normal_count*sizeof(ConstructorNormalSnapshot));'
        oldobserver=oldobserver.replace(export,export+'\n    constructor_dump(stem+"/getter-backings.bin",constructor_getter_backings,constructor_normal_count*sizeof(constructor_getter_backings[0]));',1)
        assert oldobserver==observer,'Entire other original observer code unchanged'
        checker=pin(R/'tools/m4-constructor-original/validate_v5.py','e702b75020c12b15a3ade692e66484e5b29c8be4b74ae22ba8e22e93d5e6cb74').read_text()
        assert 'getter-backings.bin' in checker and 'NULL' in checker and 'header' in checker
        counts['whole_additive_observer_source_relations']=3
'''
replacement="""needle="        C=load(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','ctor37_actual_coff')"
assert text.count(needle)==1
text=text.replace(needle,EXTRA+needle)
pin_wrapper_source=__file__
exec(compile(text,str(review_source),'exec'),globals())"""
text=text.replace(hook,replacement)
text=text.replace('EXTRA',repr(extra))
# The wrapper review itself and frozen parent are consumed by the inner admission.
text=text.replace("pin(review_source);", "pin(review_source);pin(prior);")
exec(compile(text,str(prior),'exec'),globals())

