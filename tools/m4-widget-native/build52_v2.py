"""Compile precisely52 entries using the inherited DLL CRT ABI."""
from pathlib import Path
P=Path(__file__).resolve().parent;prior=P/'build_v2.py';s=prior.read_text()
a="exec(compile(s,str(base),'exec'),globals())"
b="""s=s.replace("'-fexceptions','-fcxx-exceptions'","'-fexceptions','-fcxx-exceptions','-fms-runtime-lib=dll'")
s=s.replace("'literal_objects':51", "'literal_objects':len(data['IRs'])").replace('All 51 actual library literal definitions','All actual52 library literal definitions').replace('102 namespaced literal COFFs','104 namespaced literal COFFs')
s=s.replace("R/'tools/m4-widget-native/build_v2.ps1'", "R/'tools/m4-widget-native/build_v2.ps1',R/'tools/m4-widget-native/build52_v2.ps1',prior,R/'tools/m4-widget-native/build_v3.py',R/'tools/m4-widget-native/build_v3.ps1'")
exec(compile(s,str(base),'exec'),globals())"""
assert s.count(a)==1
exec(compile(s.replace(a,b),str(prior),'exec'),globals())
