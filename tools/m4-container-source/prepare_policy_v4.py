"""Correct the actual compiled trampoline prefix assertion, preserve v3."""
from pathlib import Path
T=Path(__file__).resolve().parent
s=(T/'compare_paired_policy_v3.py').read_text()
old="need(worker_bytes[toff:toff+2]==bytes.fromhex('8905'),'Actual compiled trampoline begins saving source ESP before pushes')"
new="need(worker_bytes[toff:toff+2]==bytes.fromhex('c705')and words(worker_bytes,toff+6)[0]==hook['kind']and worker_bytes[toff+10]==0xa3,'Actual compiled trampoline begins declaring exact event direction and saving EAX; full ESP-before-push checked by pinned compiled observer gate')"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("  observer_gate=", "  loader_rows=[];loader_differences=delta(loaded_page,raw_page);observer_spans=[]\n  observer_gate=",1)
(T/'compare_paired_policy_v4.py').write_text(s)
