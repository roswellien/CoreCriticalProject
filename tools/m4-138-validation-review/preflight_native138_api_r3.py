"""Import and API signature check only; never invokes main or archive constructors."""
from pathlib import Path
import ast,hashlib,importlib.util,inspect,json,sys,types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];P={}
def pin(p):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name not in('payload.bin','index.json');P[str(p)]=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();return p
p=pin(R/'reports/m4-joint-startup138-source/preparation-r9/compare_provider138.py');assert P[str(pin(p.parent/'report.json'))]=='142bce66d1d43448f674996d826371d897206cd695b40c3b9164efcae0b5207d' and P[str(p)]=='f2d82ab40687f74c0b010a64d1b6759054d3056a196114cb201aa974ed073e2a'
spec=importlib.util.spec_from_file_location('api_only_current138',p);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
scope=dict(vars(M));tree=ast.parse(p.read_text());failures=[];rows=[]
# Materialize only ordinary Python module loads specified in main, never models/main.
for node in ast.walk(tree):
 if not isinstance(node,ast.Assign)or not isinstance(node.value,ast.Call)or not isinstance(node.value.func,ast.Name)or node.value.func.id!='load':continue
 if len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name):continue
 try:path=eval(compile(ast.Expression(node.value.args[1]),'<preflight-path>','eval'),scope)
 except Exception:continue
 q=pin(path);s=importlib.util.spec_from_file_location('api_only_'+node.targets[0].id,q);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);scope[node.targets[0].id]=v
aliases={k:v for k,v in scope.items()if isinstance(v,types.ModuleType)}
for node in ast.walk(tree):
 if not isinstance(node,ast.Attribute)or not isinstance(node.value,ast.Name)or node.value.id not in aliases:continue
 mod=aliases[node.value.id]
 if not hasattr(mod,node.attr):failures.append(dict(line=node.lineno,expression=ast.unparse(node),reason='Missing imported module attribute'))
 else:rows.append(dict(line=node.lineno,expression=ast.unparse(node),resolved=True))
methods={'gdi':M.PG.GDIAdapter,'association':M.PW.JournalAssociation,'original_export':M.EX.Export,'export':M.EX.Export,'extension':M.MF.Extension}
calls=[]
for node in ast.walk(tree):
 if not isinstance(node,ast.Call)or not isinstance(node.func,ast.Attribute)or not isinstance(node.func.value,ast.Name):continue
 name=node.func.value.id;fn=None;extra=[]
 if name in aliases:fn=getattr(aliases[name],node.func.attr,None)
 elif name in methods:
  fn=getattr(methods[name],node.func.attr,None);extra=[object()]
  if fn is None:failures.append(dict(line=node.lineno,expression=ast.unparse(node.func),reason='Missing concrete instance API'));continue
 if fn is None or not callable(fn):continue
 if any(isinstance(a,ast.Starred)for a in node.args)or any(k.arg is None for k in node.keywords):continue
 try:sig=inspect.signature(fn)
 except (TypeError,ValueError):continue
 try:sig.bind(*extra,*[object()for a in node.args],**{k.arg:object()for k in node.keywords})
 except TypeError as error:failures.append(dict(line=node.lineno,expression=ast.unparse(node.func),reason=str(error)));continue
 calls.append(dict(line=node.lineno,expression=ast.unparse(node.func),signature=str(sig)))
assert M.PG.TARGETS==(0x71f00010,0x71f00020,0x71f00030)
assert Path(M.PW.__file__).name=='persistent_widgets_v5.py'and Path(M.PW.GAME_OWNERSHIP.__file__).name=='mapped_game_memory_v2.py'
assert Path(M.EX.__file__).resolve()==p.parent/'paired_exports.py'
for mod in aliases.values():
 q=getattr(mod,'__file__',None)
 if q and Path(q).is_file():pin(q)
pin(M.PW.GAME_OWNERSHIP.__file__);pin(__file__);out=R/'reports/m4-138-validation-review/native138-api-preflight-r2';assert not out.exists();out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=not failures,scope='Import, direct module API existence and inspect.signature binding preflight. No source execution or archive constructor invoked.',module_attribute_checks=rows,signature_checks=calls,failures=failures,explicit_bindings=dict(GDI_TARGETS=list(M.PG.TARGETS),widget_helper=M.PW.__file__,game_ownership=M.PW.GAME_OWNERSHIP.__file__,generated_export=M.EX.__file__),limits='Dynamically created source machine instance fields and runtime data domains remain execution gates.',archive_reader_opened=False,worker_launched=False,initializer_credit=0,files=P),indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest(),json.dumps(failures))
