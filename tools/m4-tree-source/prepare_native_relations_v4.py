"""Bind reused source FS record addresses by their reached invocation interval."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'tools/m4-tree-source/native_tree_relations_v3.py';s=p.read_text()
a="source_frames={f['record']:f for f in source['FS_frames']};native_frames={f[9]:f for f in frames};functions={f['index']:f for f in source['function_invocations']}"
b="functions={f['index']:f for f in source['function_invocations']};native_frames={f['index']:w for f,w in zip(source['FS_frames'],frames)}"
assert s.count(a)==1;s=s.replace(a,b)
a="f=source_frames[p['entered']['FS0']];nf=native_frames[f['record']]"
b="f=max((f for f in source['FS_frames']if f['record']==p['entered']['FS0']and functions[f['invocation']]['source_access_index']<p['entered']['source_access_index']),key=lambda f:functions[f['invocation']]['source_access_index']);nf=native_frames[f['index']]"
assert s.count(a)==1;s=s.replace(a,b)
target=p.with_name('native_tree_relations_v4.py');assert not target.exists();target.write_text(s)
p=ROOT/'tools/m4-tree-source/compare_native_fixture_v4.py';s=p.read_text();assert s.count('native_tree_relations_v3.py')==1;s=s.replace('native_tree_relations_v3.py','native_tree_relations_v4.py');target=p.with_name('compare_native_fixture_v5.py');assert not target.exists();target.write_text(s)
