"""Separate explicit host LastError seam; prior sealed corpus files untouched."""
from pathlib import Path
HERE=Path(__file__).absolute().parent
s=(HERE/'controls.cpp').read_text()
anchor='struct ReviewFixture;thread_local ReviewFixture*review_fixture{};'
if anchor not in s:raise ValueError('Frozen current fixture declaration')
s=s.replace(anchor,'''void review_error_adapter(Runtime&r){require(mainargs_binding&& &mainargs_binding->context.runtime==&r&&!pp::owner&&!mg::owner&&!nt::owner&&!ci::owner&&!mn::owner,"Independent exact genuine mainargs service association");auto&c=mainargs_binding->context;mainargs_checkpoint(r,"mainargs-before");SetLastError(0xbeef0000U+review_scenarios);mainargs_binding->heap_create.start(c);}
'''+anchor)
s=s.replace('&mainargs_adapter,"Independent actual mainargs','&review_error_adapter,"Independent actual mainargs')
s=s.replace('last_job=job;auto&owned=','last_job=job;review_need(mainargs->heap_create.caller_error==0xbeef0000U+review_scenarios&&mainargs->heap_create.restored_error==0xbeef0000U+review_scenarios,"Separate explicitly seeded nonzero actual scheduler LastError is restored");auto&owned=')
old='void review_run(){for(unsigned index:{0U,5U,11U,12U,17U,23U}){ReviewFixture f(0,index);f.call();f.verify(true);}for(unsigned mode=121;mode<=132;++mode)review_negative(mode);for(unsigned mode=1;mode<=48;++mode)review_negative(mode);}'
new='void review_run(){for(unsigned index:{0U,23U}){ReviewFixture f(0,index);f.call();f.verify(true);}for(unsigned mode:{121U,122U,132U,39U})review_negative(mode);}'
if old not in s:raise ValueError('Exact frozen fixture request function')
s=s.replace(old,new)
(HERE/'caller_error.cpp').write_text(s,encoding='utf-8')
b=(HERE/'build_controls.ps1').read_text().replace('controls.cpp','caller_error.cpp').replace('generate.py','caller_error_generate.py')
b=b.replace('tools/m4-crt-heap-create-review/build_controls.ps1','tools/m4-crt-heap-create-review/build_caller_error.ps1')
b=b.replace('Independent authored fixtures on exact production composition','Separate explicit host LastError seam immediately after actual mainargs-before snapshot and before genuine heap_create.start; independent fixtures on exact production composition')
(HERE/'build_caller_error.ps1').write_text(b,encoding='utf-8')
