"""Additive preparation: guard the raw allocation ledger and enumerate all patches."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-widget-original';P=R/'reports/m4-widget-original/preparation-r2/report.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact unique derivation '+a[:90])
 return s.replace(a,b,1)
parent=json.loads(P.read_text());p=T/'prepare.py'
if sha(P)!='54597ffb3c9d84fd1ad92758be4b57fa5f92f5b171bed57b17882ba3e9f1556a' or sha(p)!=parent['files'][str(p.resolve())]:raise ValueError('Immutable preparation source')
s=p.read_text()
s=one(s," for fn in('original_broker.hpp','reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm'):(out/fn).write_text(text(OLD/fn))",''' for fn in('original_broker.hpp','reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm'):(out/fn).write_text(text(OLD/fn))
 registryasm=(out/'reference_x86.asm').read_text()
 registryasm=one(registryasm,'EXTERN registry_API_ledger:BYTE','EXTERN registry_API_ledger:BYTE\\nEXTERN fs_error:DWORD')
 registryasm=one(registryasm,' mov eax,registry_API_count\\n dec eax\\n imul eax,eax,104',' mov eax,registry_API_count\\n dec eax\\n cmp eax,256\\n jae api_ledger_overflow\\n imul eax,eax,104')
 registryasm=one(registryasm,' push DWORD PTR registry_API_after[32]',' jmp api_ledger_restore\\napi_ledger_overflow:\\n mov fs_error,1\\napi_ledger_restore:\\n push DWORD PTR registry_API_after[32]')
 (out/'reference_x86.asm').write_text(registryasm)''')
s=one(s," for i,a in enumerate(patches):",''' patches += [dict(family='Lockit',PC=p,size=n,raw=b)for p,n,b in[(0x7810a290,5,'a158561478'),(0x7810a311,5,'8bc75f5ec3'),(0x7810a350,7,'833d5856147802'),(0x7810a364,5,'c390909090')]]
 patches += [dict(family='capture-broker',PC=0x410a80,size=5,raw=None),dict(family='source-sentinel-terminal',PC=0x5ac3ec,size=5,raw=None)]
 for i,a in enumerate(patches):''')
s=one(s," pin(__file__);pin(R/'tools/m4-capture-direct/capture_direct_v3.cpp');", " pin(__file__);pin(R/'tools/m4-widget-original/prepare.py');pin(R/'tools/m4-widget-original/derive_prepare_v2.py');pin(R/'reports/m4-widget-original/preparation-r2/report.json','54597ffb3c9d84fd1ad92758be4b57fa5f92f5b171bed57b17882ba3e9f1556a');pin(R/'tools/m4-capture-direct/capture_direct_v3.cpp');")
q=T/'prepare_v2.py'
if q.exists():raise ValueError('Fresh additive source')
q.write_text(s)
print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
