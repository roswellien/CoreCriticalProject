"""Materialize inherited finite evaluator and overlays without nested escaping."""
from pathlib import Path
import ast
T=Path(__file__).parent
final="exec(compile(s,str(p),'exec'))"
ns={'__file__':str(T/'evaluate_literal_sorter_v3.py')}
first=(T/'evaluate_literal_sorter_v3.py').read_text();exec(compile(first.rsplit(final,1)[0],str(T/'evaluate_literal_sorter_v3.py'),'exec'),ns)
second=ns['s'];exec(compile(second.rsplit(final,1)[0],str(T/'evaluate_literal_sorter_v2.py'),'exec'),ns)
overlay=(T/'evaluate_literal_sorter_v4.py').read_text();before="derived.write_text(body+'\\n')";assert overlay.count(before)==1;overlay=overlay.replace(before,"derived.write_text(body+chr(10))")
tree=ast.parse(overlay);body=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='b'for t in n.targets))
ns['__file__']=str(Path(__file__));ns['p']=Path(__file__);exec(compile(body,str(Path(__file__)),'exec'),ns)
