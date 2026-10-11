"""Exclude opaque sentinel payload from actual getter receiver ownership."""
from pathlib import Path
import ast
h=Path(__file__).resolve().parent;t=(h/'prepare_chronological_v9.py').read_text();out=h/'prepare_chronological_v10.py'
if out.exists():raise ValueError('Fresh additive generator required')
a="declarations+=text(HERE/'normal_observer_v4.hpp')";b="declarations+=text(HERE/'normal_observer_v5.hpp')"
if t.count(a)!=1:raise ValueError('Exact observer binding')
t=t.replace(a,b,1)
a="pin(HERE/'derive_chronological_v9.py');pin(HERE/'normal_observer.hpp');";b="pin(HERE/'derive_chronological_v9.py');pin(HERE/'prepare_chronological_v9.py');pin(HERE/'derive_chronological_v10.py');pin(HERE/'normal_observer_v5.hpp');pin(HERE/'normal_observer.hpp');"
if t.count(a)!=1:raise ValueError('Exact additive source lineage')
t=t.replace(a,b,1);ast.parse(t);out.write_text(t)
s=(h/'normal_observer_v4.hpp').read_text();out=h/'normal_observer_v5.hpp'
if out.exists():raise ValueError('Fresh additive observer required')
a='if(raw[2]==ctor_cpu.ecx)published=true;';b='if(node!=header&&raw[2]==ctor_cpu.ecx)published=true;'
if s.count(a)!=1:raise ValueError('Exact source-owned node predicate')
out.write_text(s.replace(a,b,1))
