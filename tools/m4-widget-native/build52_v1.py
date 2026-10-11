"""Compile the52-entry additive component with actual dynamic object counts."""
from pathlib import Path
import hashlib,json,sys
P=Path(__file__).resolve().parent;prior=P/'build_v2.py';s=prior.read_text()
anchor="exec(compile(s,str(base),'exec'),globals())"
change="""s=s.replace("'literal_objects':51", "'literal_objects':len(data['IRs'])").replace('All 51 actual library literal definitions','All actual52 library literal definitions').replace('102 namespaced literal COFFs','104 namespaced literal COFFs')
s=s.replace("R/'tools/m4-widget-native/build_v2.ps1'", "R/'tools/m4-widget-native/build_v2.ps1',R/'tools/m4-widget-native/build_v3.ps1',prior")
exec(compile(s,str(base),'exec'),globals())"""
assert s.count(anchor)==1
exec(compile(s.replace(anchor,change),str(prior),'exec'),globals())
