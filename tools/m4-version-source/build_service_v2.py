"""Add actual ABI-preserving version API assembly to the two compiled libraries."""
from pathlib import Path
import hashlib,sys
p=Path(__file__).with_name('build_service_v1.py');s=p.read_text()
assert hashlib.sha256(p.read_bytes()).hexdigest()=='7fff2a812180a24410fc8fc0c5db2c915c788cea2e241077bf61b4decd1c77f6'
a="archive=dst/'mw34_version_registry_service.lib';run([lib,'/out:'+str(archive),obj],level+'-archive');"
b="asm=dst/'native_version_api.obj';run([clang,'--target=x86_64-pc-windows-msvc','-c',prep.parent/'native_version_api.s','-o',asm],level+'-native-api-asm');pin(asm);archive=dst/'mw34_version_registry_service.lib';run([lib,'/out:'+str(archive),obj,asm],level+'-archive');"
assert s.count(a)==1;s=s.replace(a,b)
a="['borrow_version_mfc','borrow_version_buffer','commit_version_buffer']";assert s.count(a)==1;s=s.replace(a,"['borrow_version_mfc','borrow_version_buffer','commit_version_buffer','borrow_version_api','mw34_version_native_api']")
s=s.replace('actual_service_methods=3','actual_service_methods=4,actual_native_assembly=str(asm),actual_native_assembly_sha256=sha(asm)')
s=s.replace("pin(__file__);pin(R/'tools/m4-version-source/build_service_v1.ps1')","pin(__file__);pin(R/'tools/m4-version-source/build_service_v1.py');pin(R/'tools/m4-version-source/build_service_v2.ps1');pin(R/'tools/m4-version-source/build_service_v1.ps1')")
exec(compile(s,str(p),'exec'),globals())
