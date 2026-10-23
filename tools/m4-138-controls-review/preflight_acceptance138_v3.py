"""Fresh derivative selects the actual setattr module injection AST loop."""
from pathlib import Path
p=Path(__file__).with_name('preflight_acceptance138_v2.py');s=p.read_text();assert s.count('acceptance138-machinery-preflight-r2')==1;s=s.replace('acceptance138-machinery-preflight-r2','acceptance138-machinery-preflight-r3')
before="and isinstance(n.iter,ast.Tuple)];assert len(tuples)==1"
after="and isinstance(n.iter,ast.Tuple)and any(isinstance(x,ast.Expr)and isinstance(x.value,ast.Call)and isinstance(x.value.func,ast.Name)and x.value.func.id=='setattr'for x in n.body)];assert len(tuples)==1"
assert s.count(before)==1;s=s.replace(before,after)
exec(compile(s,str(p),'exec'))
