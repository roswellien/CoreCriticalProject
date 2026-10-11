"""Compile the58 literal entries with frozen current DLL CRT/SDK ABI."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];base=R/'tools/m4-widget-native/build.py';prep=json.loads((R/sys.argv[1]).read_bytes());s=base.read_text()
s=s.replace("'-I',R/'tools/m4-runtime','-I',R/'runtime'","'-I',R/'tools/m4-runtime','-I',R/'tools/m4-startup','-I',R/'runtime'").replace("'-fexceptions','-fcxx-exceptions'","'-fexceptions','-fcxx-exceptions','-fms-runtime-lib=dll'").replace("'literal_objects':51","'literal_objects':len(data['IRs'])").replace('All 51 actual library literal definitions','All actual58 library literal definitions').replace('102 namespaced literal COFFs','116 namespaced literal COFFs').replace('Compile-only reusable six-root widget component','Compile-only reusable seven-root widget/FPS component')
s=s.replace("for p in (clang,lib,nm,Path(__file__).resolve(),R/'tools/m4-widget-native/build.ps1')","for p in (clang,lib,nm,base,Path(__file__).resolve(),R/'tools/m4-widget-native/build.ps1',R/'tools/m4-fps-native/build_component.ps1')")
assert len(prep['IRs'])==58 and prep['literal_bodies']==58
exec(compile(s,str(base),'exec'),globals())
