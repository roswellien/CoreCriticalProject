"""Correct two exact CRT registry page offsets; retain original validator."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-widget-original';p=T/'validate.py';q=T/'validate_v2.py'
if q.exists():raise ValueError('Fresh checker')
s=p.read_text();a="words(crt_before[0x78037000],0x88)==(registry_before[1],)and words(crt_before[0x78037000],0x8c)==(registry_before[0],)";b="words(crt_before[0x78037000],0x888)==(registry_before[1],)and words(crt_before[0x78037000],0x88c)==(registry_before[0],)"
if s.count(a)!=1:raise ValueError('Exact absolute78037888/8C fields')
s=s.replace(a,b,1);a='pin(__file__);pin(sys.executable);';b="pin(__file__);pin(R/'tools/m4-widget-original/derive_validate_v2.py');pin(R/'tools/m4-widget-original/validate.py','"+hashlib.sha256(p.read_bytes()).hexdigest()+"');pin(sys.executable);"
if s.count(a)!=1:raise ValueError('Exact checker lineage')
s=s.replace(a,b,1);q.write_text(s);print(hashlib.sha256(q.read_bytes()).hexdigest())
