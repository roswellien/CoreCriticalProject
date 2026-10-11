from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];p=R/'tools/m4-tree-review/review_original130_combined_v2.py';raw=p.read_text()
a='need(\'reader.close();reader.entries.clear();reader.bundles.clear()\'in aggregate and "phase=78"not in aggregate and "phase=78"not in tree,\'Explicit shared reader closure; selected phase resolved by literal root\')'
b='need(\'reader.close();reader.entries.clear();reader.bundles.clear()\'in aggregate and "tree_phase=next(i for i,x in enumerate(preparation[\'selected_order\'])if x[\'entry\']==0x4b7f70)"in tree and "need(tree_phase==78"in tree,\'Explicit shared reader closure; actual current selected phase resolved by literal root and asserted78\')'
assert raw.count(a)==1;raw=raw.replace(a,b)
a='pin(__file__);passed=True';b="pin(__file__);[pin(R/'tools/m4-tree-review'/q)for q in('review_original130_combined.py','review_original130_combined_v2.py','derive_original130_combined_v2.py','derive_original130_combined_v3.py')];passed=True"
assert raw.count(a)==1;raw=raw.replace(a,b)
target=p.with_name('review_original130_combined_v3.py');assert not target.exists();target.write_text(raw);print(json.dumps(dict(sha256=hashlib.sha256(target.read_bytes()).hexdigest())))
