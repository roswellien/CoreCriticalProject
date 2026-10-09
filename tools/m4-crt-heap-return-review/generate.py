"""Create fresh independent return fixtures from immutable accepted version fixtures."""
import hashlib
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent;OLD=ROOT/'tools/m4-crt-heap-version-review'
def exact(path,digest):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Frozen fixture input changed '+str(path))
    return data.decode().replace('\r\n','\n')
def change(s,a,b):
    if a not in s:raise ValueError('Required immutable fixture fragment '+a)
    return s.replace(a,b)
def main():
    original=exact(OLD/'controls.cpp','26695a581ddc45e0ad2262e18054449e75ef4b4e23897860d50ddaebeb1dd3cf');prefix=original[:original.index(' void verify(bool clean)')]
    prefix=prefix.replace('MW34_CRT_HEAP_VERSION_NO_MAIN','MW34_CRT_HEAP_RETURN_NO_MAIN').replace('hv::','hr::').replace('mainargs->heap_version','mainargs->heap_return').replace('which>=145','which>=157').replace('duplicate_cleanup||mode==156','duplicate_cleanup||mode==168')
    prefix=change(prefix,'Job last_job{};','Job last_job{};std::array<std::byte,sizeof(hv::Binding)>unused_version_initial{};')
    prefix=change(prefix,'entry_context=std::make_unique<Context>(r,*fdiv,m4::sha256(review_object));','entry_context=std::make_unique<Context>(r,*fdiv,m4::sha256(review_object));std::memcpy(unused_version_initial.data(),&mainargs->heap_version,unused_version_initial.size());')
    prefix=change(prefix,'!hr::has_authority()&&!commandline','!hr::has_authority()&&!hv::has_authority()&&!commandline')
    prefix=change(prefix,'auto&owned=mainargs->heap_return;','review_need(!std::memcmp(unused_version_initial.data(),&mainargs->heap_version,unused_version_initial.size()),"Unused accepted version Binding stays entirely immutable through current source/fault exit");auto&owned=mainargs->heap_return;')
    prefix=change(prefix,'raw_output(row/"query-status.bin",qs);return job;','raw_output(row/"query-status.bin",qs);raw_output(row/"heap-return-progress.bin",h.progress());std::array<unsigned,6>public_return{unsigned(h.selector_unwound),unsigned(h.mode_store_before),unsigned(h.mode_published),h.mode_value,unsigned(h.initializer_return_before),unsigned(h.initializer_returned)};raw_output(row/"heap-return-public.bin",public_return);return job;')
    tail=exact(OLD/'controls_tail.inc','73239ee8c280cc43a6ef0a6b74c995d26cf14dd0598e1fa3fd34e0233d4c1e67').replace('hv::','hr::').replace('mainargs->heap_version','mainargs->heap_return')
    verify=tail[:tail.index('bool review_heap_member(')];tail=tail[tail.index('bool review_heap_member('):tail.index('void review_run()')]
    verify=change(verify,'!mainargs->heap_mode.used&&!c.used','!mainargs->heap_mode.used&&!mainargs->heap_version.used&&!mainargs->heap_version.active&&!c.used')
    verify=change(verify,'mg::slot+unsigned(mode==16)','mg::slot+unsigned(mode==16||mode==91)')
    verify=change(verify,'h.event_count==11','h.event_count==(h.initializer_returned?13U:11U)')
    verify=change(verify,'last_job.fault_pc==0x78003a7f&&last_job.fault_target==hr::mode_ret&&h.access_count==31','last_job.fault_pc==0x78003a0b&&last_job.fault_target==hr::ret&&h.access_count==35&&h.initializer_returned&&h.mode_published&&h.mode_value==1')
    verify=change(verify,'Genuine source selector RET stops before heap publication','Genuine source initializer RET stops before original fragment caller')
    verify=change(verify,'c.state.gpr.rip.dword==hr::mode_ret&&c.state.gpr.rsp.dword==0x20001858','c.state.gpr.rip.dword==hr::ret&&c.state.gpr.rsp.dword==0x2000185c')
    start=verify.index('const auto result=major-5;');end=verify.index('}',start)
    verify=verify[:start]+'review_need((cpu(c.state).eflags&0x8d5)==0x95,"Final source flags are authentic CMP1,2 preserved by PUSH/POP/RET");'+verify[end:]
    verify=change(verify,'  }retry();','if(mode1){\n'+(HERE/'verify_return.inc').read_text()+'\n}\n  }retry();')
    end=tail.index('\n}\nvoid review_negative(');tail=tail[:end]+'\n'+(HERE/'return_controls.inc').read_text()+tail[end:]
    tail=change(tail,'f.verify(false);',(HERE/'return_checks.inc').read_text()+'\nf.verify(false);')
    run='''void review_run(){for(unsigned index:{0U,5U,11U,12U,17U,23U}){ReviewFixture f(0,index);f.call();f.verify(true);}for(unsigned mode=157;mode<=168;++mode)review_negative(mode);for(unsigned mode=1;mode<=104;++mode)review_negative(mode);review_direct_queries();}\n}\n'''
    cli=original[original.index('int main('):].replace('hv::','hr::')
    (HERE/'controls_tail.inc').write_text(verify+tail+run,encoding='utf-8');(HERE/'controls.cpp').write_text(prefix+verify+tail+run+cli,encoding='utf-8')
    (HERE/'direct_query.inc').write_text(exact(OLD/'direct_query.inc','f43032dc5fac03e863c1b8ab4f810385d562ffb7f057bc978bedb3f6ddf1714f'),encoding='utf-8')
    b=exact(OLD/'build_controls.ps1','8b44512c2c1bb0ecb4bd5ecd743a62f40e2f03133fbfc1dec31d2bafd6186c11').replace('m4-crt-heap-version-review','m4-crt-heap-return-review')
    b=change(b,"'tools/m4-crt-heap-return-review/direct_query.inc',","'tools/m4-crt-heap-return-review/direct_query.inc','tools/m4-crt-heap-return-review/return_controls.inc','tools/m4-crt-heap-return-review/return_checks.inc','tools/m4-crt-heap-return-review/verify_return.inc','tools/m4-crt-heap-version-review/controls.cpp','tools/m4-crt-heap-version-review/controls_tail.inc','tools/m4-crt-heap-version-review/build_controls.ps1',")
    b=change(b,"Join-Path $reviewBase 'source-r1'","Join-Path $reviewBase 'source-r3'")
    b=change(b,'$o=Join-Path $reviewPrep "$kind-$level.obj"','$o=Join-Path $reviewRoot "reports/m4-crt-heap-version/preparation-r2/$kind-$level.obj"')
    b=change(b,"@('tools/m4-crt-heap-version',","@('tools/m4-crt-heap-return','tools/m4-crt-heap-version',")
    b=change(b,"Join-Path $reviewPrep 'heap_version.hpp'","Join-Path $reviewPrep 'heap_return.hpp'")
    b=b.replace('private actual GetVersionExA witness, finite guest output copy, real source selector continuation/RET and bounded post-selector or ENV frontier','private actual GetVersionExA witness, literal mode store and initializer RET, unchanged full-HANDLE/State/FX/CPU source composition and bounded fragment or ENV frontier')
    (HERE/'build_controls.ps1').write_text(b,encoding='utf-8');(HERE/'launch_fixture.py').write_text(exact(OLD/'launch_fixture.py','cdf2638b384cdf0d1857f59cf8e33a2f08d3569b399d1120070437dca6465fc0').replace('m4-crt-heap-version-review','m4-crt-heap-return-review'),encoding='utf-8')
    runner=exact(OLD/'run.py','654347e9f8c4b4eb12c2661c7ca407cb4f3c006f9241f200a0733842799d4448').replace('m4-crt-heap-version-review','m4-crt-heap-return-review')
    runner=change(runner,"result['scenarios'] != 98","result['scenarios'] != 122");runner=change(runner,"result['malformed_token_denials'] != 20","result['malformed_token_denials'] != 22");runner=runner.replace('explicit State-PC-only attach fragment/heap prefix seam','explicit State-PC-only attach fragment seam and genuine source heap initializer return')
    runner=change(runner,"'native_scenarios': 196","'native_scenarios': 244")
    (HERE/'run.py').write_text(runner,encoding='utf-8')
if __name__=='__main__':main()
