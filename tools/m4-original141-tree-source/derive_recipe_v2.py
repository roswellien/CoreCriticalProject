from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-original141-tree-source/prepare_admission_recipe_v1.py';s=p.read_text(encoding='utf-8').replace('admission-recipe-r1','admission-recipe-r2').replace('tree_source_v2.py','tree_source_v3.py').replace('run_ordinary_v1.py','run_ordinary_v2.py')
a="for d in reversed(json.loads(pin(source.parent/'deltas.json').read_bytes())):"
b="boundary,boundary_gate=report(R/'reports/m4-original141-tree-source/ordinary-boundary-preparation-r1/report.json','6a2656e3c55d00d931e3abfdccc8f39beec643716fd997fe9a46628593a1019b')\n controls,control_gate=report(R/'reports/m4-original141-tree-source/ordinary-boundary-controls-r1/report.json',CONTROL_SHA)\n for d in reversed(json.loads(pin(boundary.parent/'deltas.json').read_bytes())['tree_composed']):"
import hashlib
control=R/'reports/m4-original141-tree-source/ordinary-boundary-controls-r1/report.json';b=b.replace('CONTROL_SHA',repr(hashlib.sha256(control.read_bytes()).hexdigest()));assert s.count(a)==1;s=s.replace(a,b).replace('exact_eleven_delta_inverse=True,entire_ordinary','exact_fifteen_delta_inverse=True,entire_ordinary').replace('whole11 finite child inverse','whole15 finite child inverse plus one runner binding and all13 ordinary-only pin controls')
q=p.with_name('prepare_admission_recipe_v2.py');assert not q.exists();q.write_text(s,encoding='utf-8')
