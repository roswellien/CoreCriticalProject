"""Repair the inherited optional protocol control's current whole page count."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=here/'prepare_chronological_v4.py'
target=here/'prepare_chronological_v5.py'
assert not target.exists()
text=source.read_text()
old="        (out/'protocol.hpp').write_text(one(text(OLD/'protocol.hpp'),'sequences=6, roots=131','sequences=6, roots=37'))"
new="""        protocol=one(text(OLD/'protocol.hpp'),'sequences=6, roots=131','sequences=6, roots=37')
        protocol=one(protocol,'memory_size==151552','memory_size==176128')
        (out/'protocol.hpp').write_text(protocol)"""
assert text.count(old)==1
text=text.replace(old,new,1)
old="pin(HERE/'derive_chronological_v4.py');pin(HERE/'normal_observer.hpp');pin(ROOT/"
new="pin(HERE/'derive_chronological_v4.py');pin(HERE/'prepare_chronological_v4.py');pin(HERE/'derive_chronological_v5.py');pin(HERE/'normal_observer.hpp');pin(ROOT/"
assert text.count(old)==1
text=text.replace(old,new,1)
target.write_text(text)
