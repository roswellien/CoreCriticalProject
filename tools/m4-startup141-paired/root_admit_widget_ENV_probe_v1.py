"""ROOT narrow endpoint hypothesis admission, never lastwriter-policy acceptance."""
from pathlib import Path
import ast, hashlib, json, types, io, contextlib, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 recipe_path=R/'reports/m4-startup141-paired/widget-ENV-probe-preparation-r1/ROOT-admission-recipe.json'
 assert sha(recipe_path)=='b25e646e72e6c3d5c037ce02de91dc32028fe3f2bb234562ab69a40e8760eec2'
 recipe=json.loads(recipe_path.read_bytes());pins=dict(recipe['ordinary_inputs'])
 pins[str(recipe_path)]='b25e646e72e6c3d5c037ce02de91dc32028fe3f2bb234562ab69a40e8760eec2'
 cp=R/'tools/m4-startup141-paired/widget_ENV_relation141_controls_v2.py'
 pins[str(cp)]='0e762d297d7de05a53a4322f1648b8bbe441276b142c2bad0e097f4d7be1ad97'
 ip=R/'reports/m4-startup141-paired/widget-ENV-controls-preparation-r2/exact-inverse.json'
 pins[str(ip)]='8d5a5398e499497bfa506941175482109ba484aa078f32188efe63c4ee2f7a83'
 # Review and execute only pure controls; bypass project cached import loaders.
 for p,h in pins.items():assert sha(p)==h,(p,h)
 inv=json.loads(ip.read_bytes());child=cp.read_text();parent=Path(inv['parent']).read_text()
 assert child.count(inv['new'])==1 and child.replace(inv['new'],inv['old'])==parent
 def direct(name):
  p=R/'tools/m4-startup141-paired'/f'{name}.py';assert sha(p)==pins[str(p)]
  m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
 tree=ast.parse(child);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 loader=next(n for n in fn.body if isinstance(n,ast.FunctionDef) and n.name=='load')
 loader.body=ast.parse('return ROOT_direct(name)').body
 tree.body=[n for n in tree.body if not isinstance(n,ast.If)];ast.fix_missing_locations(tree)
 env={'__file__':str(cp),'ROOT_direct':direct};exec(compile(tree,str(cp),'exec'),env)
 buf=io.StringIO()
 with contextlib.redirect_stdout(buf):env['main']()
 result=ast.literal_eval(buf.getvalue().strip());assert result['passed'] is True and result['adverse_controls']==79
 out=R/'reports/m4-startup141-paired/root-widget-ENV-controls-r1';assert not out.exists();out.mkdir()
 result.update(independent_ROOT_execution=True,project_cached_loader_used=False,lastwriter_policy_admitted=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');pins[str(q)]=sha(q)
 # All selected ordinary export indices/payloads get fresh whole-file hashes.
 for row in recipe['future_exact_ordinary_inputs']:
  p=Path(row['path']);assert sha(p)==row['sha256'];pins[str(p)]=row['sha256']
 for p,h in pins.items():assert sha(p)==h,p
 pins[str(Path(__file__).resolve())]=sha(__file__)
 out=R/'reports/m4-startup141-paired/root-widget-ENV-probe-admission-r1';assert not out.exists();out.mkdir()
 a=dict(passed=True,independent_review=True,scope_identity='current141_widget_ENV_ordinary_probe',files=pins,source_lastwriter_policy_admitted=False,whole53_pair_admitted=False,initializer_credit=0,scope='Whole ordinary endpoint hypothesis only; source/API lastwriter closure remains outstanding')
 p=out/'report.json';p.write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),pure_controls=79)))
if __name__=='__main__':main()
