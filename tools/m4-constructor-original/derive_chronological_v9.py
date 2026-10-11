"""Reset companion observations and identify first-fault source unambiguously."""
from pathlib import Path
import ast
here=Path(__file__).resolve().parent
source=here/'prepare_chronological_v8.py';target=here/'prepare_chronological_v9.py'
if target.exists():raise ValueError('Fresh additive generator required')
t=source.read_text()
def one(a,b):
    global t
    if t.count(a)!=1:raise ValueError('Exact additive hunk '+a[:100])
    t=t.replace(a,b,1)
one("        ref=ref.replace('Original131'", """        ref=one(ref,'std::memset(constructor_normal_records,0,sizeof(constructor_normal_records));','std::memset(constructor_normal_records,0,sizeof(constructor_normal_records));std::memset(constructor_getter_backings,0,sizeof(constructor_getter_backings));')
        ref=ref.replace('ctor_record_fs_failure(__LINE__)','ctor_record_fs_failure(__LINE__,__FILE__)')
        ref=one(ref,'unsigned ctor_fs_failure_line{},ctor_fs_failure_root{};','unsigned ctor_fs_failure_line{},ctor_fs_failure_root{};const char*ctor_fs_failure_source{};')
        ref=one(ref,'void ctor_record_fs_failure(unsigned line){if(!fs_error){ctor_fs_failure_line=line;ctor_fs_failure_root=fs_phase_root;}fs_error=1;}','void ctor_record_fs_failure(unsigned line,const char*source){if(!fs_error){ctor_fs_failure_line=line;ctor_fs_failure_root=fs_phase_root;ctor_fs_failure_source=source;}fs_error=1;}')
        ref=one(ref,'<<" source-line="<<std::dec<<ctor_fs_failure_line','<<" source="<<(ctor_fs_failure_source?ctor_fs_failure_source:"none")<<" source-line="<<std::dec<<ctor_fs_failure_line')
        ref=ref.replace('Original131'""")
one("declarations+=text(HERE/'normal_observer_v3.hpp')", "declarations+=text(HERE/'normal_observer_v4.hpp')")
one("pin(HERE/'normal_observer_v3.hpp');pin(HERE/'normal_observer.hpp');", "pin(HERE/'normal_observer_v3.hpp');pin(HERE/'normal_observer_v4.hpp');pin(HERE/'prepare_chronological_v8.py');pin(HERE/'derive_chronological_v9.py');pin(HERE/'normal_observer.hpp');")
ast.parse(t);target.write_text(t)
new=here/'normal_observer_v4.hpp'
if new.exists():raise ValueError('Fresh additive observer required')
new.write_text((here/'normal_observer_v3.hpp').read_text().replace('ctor_record_fs_failure(__LINE__)','ctor_record_fs_failure(__LINE__,__FILE__)'))
