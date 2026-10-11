"""Add exact actual native ownership/FS/scratch row joins to the isolated gate."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
base=ROOT/'tools/m4-tree-source/compare_native_fixture.py';s=base.read_text()
a="responses.lockit_complete();need(len(result['owned_accesses'])==172";b="responses.lockit_complete();relations=load('isolated_tree_native_relations',ROOT/'tools/m4-tree-source/native_tree_relations.py');counts.update(relations.verify(reader,'actual-after-root/',result,responses.lockit_relations,C,index));need(len(result['owned_accesses'])==172";assert s.count(a)==1;s=s.replace(a,b)
target=base.with_name('compare_native_fixture_v2.py');assert not target.exists();target.write_text(s)
