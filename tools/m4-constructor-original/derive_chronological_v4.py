"""Additive observer protocol type and non-shadowing identifier correction."""
from pathlib import Path

here=Path(__file__).resolve().parent
old_header=here/'normal_observer.hpp'
new_header=here/'normal_observer_v2.hpp'
assert not new_header.exists()
header=old_header.read_text()
assert header.count('CPU')==2
header=header.replace('CPU','Cpu')
assert header.count('auto*owner=')==1 and header.count('owner->')==4
header=header.replace('auto*owner=','auto*member_owner=')
header=header.replace('owner!=nullptr','member_owner!=nullptr')
header=header.replace('owner->','member_owner->')
new_header.write_text(header)

source=here/'prepare_chronological_v3.py'
target=here/'prepare_chronological_v4.py'
assert not target.exists()
text=source.read_text()
def one(old,new):
    global text
    assert text.count(old)==1,old
    text=text.replace(old,new,1)
one("declarations+=text(HERE/'normal_observer.hpp')", "declarations+=text(HERE/'normal_observer_v2.hpp')")
one('const unsigned delta=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&delta,4);', 'const unsigned ctor_patch_delta=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&ctor_patch_delta,4);')
one("pin(HERE/'derive_chronological_v3.py');pin(ROOT/", "pin(HERE/'derive_chronological_v3.py');pin(HERE/'prepare_chronological_v3.py');pin(HERE/'derive_chronological_v4.py');pin(HERE/'normal_observer.hpp');pin(ROOT/")
target.write_text(text)
