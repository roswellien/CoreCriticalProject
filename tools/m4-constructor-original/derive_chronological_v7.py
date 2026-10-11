"""Keep named-export observations at their existing writer publication point."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=here/'prepare_chronological_v6.py';target=here/'prepare_chronological_v7.py'
assert not target.exists();text=source.read_text()
def one(old,new):
    global text
    assert text.count(old)==1,old
    text=text.replace(old,new,1)
one('out.append("constructor/provider-entries.bin",ctor_named_entries.data(),sizeof(ctor_named_entries));','')
one("        # The same genuine source cleanup is restricted to roots that actually", """        ref=one(ref,'out.append("crt-api-targets.bin",registry_API_targets,sizeof(registry_API_targets));','out.append("crt-api-targets.bin",registry_API_targets,sizeof(registry_API_targets));out.append("constructor/provider-entries.bin",ctor_named_entries.data(),sizeof(ctor_named_entries));')
        # The same genuine source cleanup is restricted to roots that actually""")
one("pin(HERE/'derive_chronological_v6.py');pin(HERE/'normal_observer.hpp');pin(ROOT/", "pin(HERE/'derive_chronological_v6.py');pin(HERE/'prepare_chronological_v6.py');pin(HERE/'derive_chronological_v7.py');pin(HERE/'normal_observer.hpp');pin(ROOT/")
target.write_text(text)
