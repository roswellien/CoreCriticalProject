"""Close actual x86 WOW64 API/export attribution and borrowed CS endpoint."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2];p=R/'tools/m4-mfc1168-probe/validate_v5.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='6a82cb90776ad80147ce608eb60062bc61a93479d387679d36ef8f8be7b5d0fe'
s=p.read_text(encoding='utf-8-sig')
a="  for provider in named:pin(provider['module_path'],provider['module_sha256'])"
assert s.count(a)==1
s=s.replace(a,"  PE=load(R/'tools/analysis/pe.py','probe_physical_exports');ID=load(R/'tools/m4-mfc1168-probe/provider_identity.py','probe_actual_provider_identity');physical=ID.identities(named,root/'normal',PE,raw,pin,need,eq);counts['physical_actual_named_API_export_joins']=len(physical)\n  artifact=out/'actual-named-API-boundaries.json';artifact.write_text(json.dumps(named,indent=2)+'\\n');PINS[str(artifact.resolve())]=sha(artifact)\n  artifact=out/'actual-physical-API-proofs.json';artifact.write_text(json.dumps(physical,indent=2)+'\\n');pin(artifact)")
a="   eq(raw(p/'ENV-before.bin'),raw(p/'ENV-after.bin'),'Whole rootENV28 preserved');"
assert s.count(a)==1
s=s.replace(a,"   eq(raw(p/'BEFORE/CRT-codepage-lock/bytes.bin'),raw(p/'AFTER/CRT-codepage-lock/bytes.bin'),'Complete borrowed lock25 endpoint restored');counts['whole_borrowed_CS24_endpoint_pairs']+=1\n"+a)
a="  pin(R/'tools/m4-mfc1168-probe/derive_validation_v5.py');pin(__file__);"
assert s.count(a)==1;s=s.replace(a,"  pin(R/'tools/m4-mfc1168-probe/derive_validation_v5.py');pin(R/'tools/m4-mfc1168-probe/derive_validation_v6.py');pin(__file__);")
out=R/'tools/m4-mfc1168-probe/validate_v6.py';assert not out.exists();out.write_text(s,encoding='utf-8');print(hashlib.sha256(out.read_bytes()).hexdigest())
