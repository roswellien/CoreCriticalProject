"""Compile a disjoint constructor fork using the immutable service compiler."""
from pathlib import Path
import hashlib
h=Path(__file__).resolve().parent;source=h.parent/'m4-version-source/build_service_v1.py';raw=source.read_text()
if hashlib.sha256(source.read_bytes()).hexdigest()!='7fff2a812180a24410fc8fc0c5db2c915c788cea2e241077bf61b4decd1c77f6':raise ValueError('Immutable actual service compiler')
s=raw
for a,b in [("pin(__file__);pin(R/'tools/m4-version-source/build_service_v1.ps1')","pin(__file__);pin(R/'tools/m4-version-source/build_service_v1.py');pin(R/'tools/m4-constructor-native/build_service.ps1')"),("['borrow_version_mfc','borrow_version_buffer','commit_version_buffer']","['borrow_constructor_mfc','constructor_owner','constructor_owner_read','constructor_source_write']"),("actual_service_methods=3","actual_service_methods=4")]:
 if s.count(a)!=1:raise ValueError('Exact service compiler source adaptation')
 s=s.replace(a,b,1)
s=s.replace('version_registry_service','constructor_registry_service').replace('mw34_version_registry_service.lib','mw34_constructor_registry_service.lib').replace('Fresh version service build','Fresh constructor service build').replace('Exact version service preparation','Exact constructor service preparation').replace('Three concrete compiled typed service methods','Four concrete compiled constructor service methods').replace('Both optimization levels compile concrete genuine borrowed MFC823/825 and same-generation entire native-buffer lease/commit. Static service libraries only; no initializer worker linked or executed','Both levels compile constructor MFC823/825, whole current owner inspection and literal per-store native/guest mirrors. Static libraries only; no worker/source/native acceptance')
exec(compile(s,str(source),'exec'),globals())
