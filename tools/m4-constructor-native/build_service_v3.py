"""Six concrete constructor service methods, including balanced private scope."""
from pathlib import Path
p=Path(__file__).resolve().parent/'build_service.py';s=p.read_text()
for a,b in [("['borrow_constructor_mfc','constructor_owner','constructor_owner_read','constructor_source_write']","['borrow_constructor_mfc','constructor_owner','constructor_owner_read','constructor_source_write','constructor_scope','abort_constructor']"),("actual_service_methods=4","actual_service_methods=6"),("Four concrete compiled constructor service methods","Six concrete compiled constructor service methods"),("pin(__file__);pin(R/'tools/m4-version-source/build_service_v1.py')","pin(__file__);pin(R/'tools/m4-constructor-native/build_service_v3.ps1');pin(R/'tools/m4-constructor-native/build_service.py');pin(R/'tools/m4-version-source/build_service_v1.py')")]:
 if s.count(a)!=1:raise ValueError('Exact five-method compiler derivative')
 s=s.replace(a,b,1)
exec(compile(s,str(p),'exec'),globals())
