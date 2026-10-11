"""Separate the source caller invocation from the enclosing active FS frame."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'tools/m4-tree-source/native_tree_relations_v2.py';s=p.read_text()
a="function=functions[f['invocation']];frame=function['frame'];paired=";b="function=functions[p['invocation']];frame=function['frame'];paired=";assert s.count(a)==1;s=s.replace(a,b)
a="int(ctor),p['ECX'],f['entry'],frame[1],nf[1]+1";b="int(ctor),p['ECX'],function['entry'],frame[1],nf[1]+1";assert s.count(a)==1;s=s.replace(a,b)
target=p.with_name('native_tree_relations_v3.py');assert not target.exists();target.write_text(s)
p=ROOT/'tools/m4-tree-source/compare_native_fixture_v3.py';s=p.read_text();assert s.count('native_tree_relations_v2.py')==1;s=s.replace('native_tree_relations_v2.py','native_tree_relations_v3.py');target=p.with_name('compare_native_fixture_v4.py');assert not target.exists();target.write_text(s)
