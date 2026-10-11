"""Use measured runtime BSS target fields instead of nonexistent raw PE BSS."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2]
p=Path(__file__).with_name('review_full125_v2.py');s=p.read_text()
old="for name,cell in(('_lockit_actual_Enter',0x78146198),('_lockit_actual_Leave',0x78146184)):need(physical(worker,shared[name],4)==struct.pack('<I',named[cell])and struct.unpack_from('<I',boot[0x78146000],cell&4095)[0]==named[cell],'API wrapper tailcalls genuine loaded named Win32 target')"
new="""for name,cell,index in(('_lockit_actual_Enter',0x78146198,1),('_lockit_actual_Leave',0x78146184,4)):
            address=shared[name];need(any(s['writable']and worker.image_base+s['virtual_address']<=address<worker.image_base+s['virtual_address']+s['virtual_size']for s in worker.sections),'Tailcall pointer is owned current worker writable storage')
            actual=struct.unpack_from('<I',snap,index*12988+9*4)[0];need(actual==named[cell]and struct.unpack_from('<I',boot[0x78146000],cell&4095)[0]==actual,'Actual observed BSS target field equals genuine loaded named API; runtime BSS has no raw PE value')"""
assert s.count(old)==1;s=s.replace(old,new)
old="pin(R/'tools/m4-tree-original/derive_review_full125_v2.py');passed=True"
new="pin(R/'tools/m4-tree-original/derive_review_full125_v2.py');pin(R/'tools/m4-tree-original/review_full125_v2.py');pin(R/'tools/m4-tree-original/derive_review_full125_v3.py');passed=True"
assert s.count(old)==1;s=s.replace(old,new)
out=p.with_name('review_full125_v3.py');assert not out.exists();out.write_text(s);print(hashlib.sha256(out.read_bytes()).hexdigest())
