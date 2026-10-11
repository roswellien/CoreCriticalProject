"""Keep actual context records distinct from API checkpoint observations."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'tools/m4-tree-source/native_tree_relations.py';s=p.read_text()
start=s.index("  for suffix,key in(('entered','entered'),('returned','returned')):")
end=s.index("  counts['whole_native_scratch_contexts']+=1",start)
s=s[:start]+"  need(all('locale-api-'+str(w[10])+'-'+suffix in index for suffix in ('before','after')),'Every real source API relation has whole State/CPU/FX/page observations in this capture')\n"+s[end:]
target=p.with_name('native_tree_relations_v2.py');assert not target.exists();target.write_text(s)
p=ROOT/'tools/m4-tree-source/compare_native_fixture_v2.py';s=p.read_text();assert s.count('native_tree_relations.py')==1;s=s.replace('native_tree_relations.py','native_tree_relations_v2.py');target=p.with_name('compare_native_fixture_v3.py');assert not target.exists();target.write_text(s)
