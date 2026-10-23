"""UNEXECUTED pure exact-source controls, synthetic in-memory SQLite only."""
from pathlib import Path
import ast,collections,copy,hashlib,json,sqlite3,sys
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def typed(a,b):return type(a)is type(b)and a==b
def run(name):
 folder=R/'tools/m4-controls-terminal-composite';prepared=R/'reports/m4-controls-terminal-composite/current16-role-preparation-r1';files={};checks=[]
 for leaf in('build_v5.py','build_v6.py','build_v7.py','current16_semantic_v1.py','current16_semantic_v2.py'):
  p=folder/leaf;data=p.read_bytes();files[str(p)]=hashlib.sha256(data).hexdigest();ast.parse(data)
 inverse=json.loads((prepared/'builder-role-rawroot-deltas.json').read_text(encoding='utf-8-sig'));text=(folder/'build_v6.py').read_bytes().decode()
 for delta in reversed(inverse):assert text.count(delta['new'])==1;text=text.replace(delta['new'],delta['old'])
 assert text==(folder/'build_v5.py').read_bytes().decode();checks.append('Whole builder6 two-hunk inverse to5')
 for record in json.loads((prepared/'finite-semantic-scope-deltas.json').read_text(encoding='utf-8-sig')):
  text=(folder/record['file']).read_bytes().decode()
  for delta in reversed(record['changes']):assert text.count(delta['new'])==1;text=text.replace(delta['new'],delta['old'])
  assert text==(folder/record['parent']).read_bytes().decode();checks.append('Whole '+record['file']+' exact finite parent inverse')
 text=(folder/'build_v7.py').read_text();start=text.index('   sums.update(c)');end=text.index('  need(dict(sums)==legacy',start);code='\n'.join(line[3:]for line in text[start:end].splitlines());compiled=compile(ast.parse(code),'<exact producer-owned raw namespace source block>','exec');h='1'*64;path=lambda n:str(R/'synthetic-controls'/n);root=path('payload');ep=path('execution.json');worker=path('legacy12.exe');build=path('build.json');prep=path('preparation.json');base=dict(passed=True,worker_closed=True,worker_executed=True,level='O0',mode=1,facts=dict(exit_code=0,arguments=[worker,'game','cpp','crt','mfc',root,'admission','1']))
 def accepted(execution,rowextra=None,missing=False,wronglineage=False):
  db=sqlite3.connect(':memory:');db.execute('CREATE TABLE edges(scope,path,sha)');scope='legacy-execution-O0-1-declared';db.execute('INSERT INTO edges VALUES(?,?,?)',('legacy24_aggregate-declared',ep,h))
  for p in(build,prep,path('payload/one.bin'),path('payload/two.bin')):
   if missing and p==prep:continue
   db.execute('INSERT INTO edges VALUES(?,?,?)',(scope,p,'0'*64 if wronglineage and p==build else h))
  row=dict(level='O0',mode=1);row.update(rowextra or {});rawroots=[]
  env=dict(sums=collections.Counter(),c={},row=row,Path=Path,case=dict(execution=ep,execution_sha256=h),db=db,need=need,typed=typed,reports={'legacy12_build':dict(workers={'O0':dict(path=worker)})},roles={'legacy12_build':dict(path=build,sha256=h),'legacy12_preparation':dict(path=prep,sha256=h)},read=lambda *args:execution,rawroots=rawroots)
  try:exec(compiled,env);result=True
  except (ValueError,KeyError):result=False
  finally:db.close()
  if result:assert rawroots==[(Path(root).resolve(),'O0-1',2)]
  return result
 assert accepted(base);checks.append('Derive own producer argument5 root and full two-row output inventory without manifest defaults')
 for label,mutate in(('Wrong level',lambda e:e.update(level='O2')),('Wrong mode',lambda e:e.update(mode=2)),('Worker open',lambda e:e.update(worker_closed=False)),('Terminal failure',lambda e:e['facts'].update(exit_code=1)),('Other physical worker',lambda e:e['facts']['arguments'].__setitem__(0,path('current8.exe'))),('Other authored mode',lambda e:e['facts']['arguments'].__setitem__(7,'8'))):
  candidate=copy.deepcopy(base);mutate(candidate);assert not accepted(candidate);checks.append(label+' rejected')
 for label,extra in(('Alternate same-count manifest root',dict(ordinary_raw_root=path('alternate-payload'))),('Wrong manifest count',dict(actual_raw_files=3)),('Boolean manifest count',dict(actual_raw_files=True))):assert not accepted(base,extra);checks.append(label+' rejected')
 assert not accepted(base,missing=True);checks.append('Missing exact owning legacy12 preparation edge rejected');assert not accepted(base,wronglineage=True);checks.append('Wrong owning legacy12 build SHA rejected')
 tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');guard=next(n for n in ast.walk(main)if isinstance(n,ast.For)and isinstance(n.iter,ast.Tuple)and[elt.value for elt in n.iter.elts if isinstance(elt,ast.Constant)]==['current16_fullraw','current16_semantic_review','current8_scope_review']);guardcode=compile(ast.Module(body=[guard],type_ignores=[]),'<exact completed ROOT role bindings>','exec');roles={key:dict(path=path(key+'.json'),sha256=h)for key in('current16_fullraw','current16_semantic_review','current8_scope_review')};bindings=copy.deepcopy(roles);exec(guardcode,dict(A={'reviewed_role_bindings':bindings},roles=roles,need=need,Path=Path));checks.append('All exact completed ROOT role paths/SHAs accepted')
 for key in roles:
  for field,value in(('path',path('arbitrary-passed.json')),('sha256','0'*64)):
   bad=copy.deepcopy(roles);bad[key][field]=value
   try:exec(guardcode,dict(A={'reviewed_role_bindings':bindings},roles=bad,need=need,Path=Path))
   except ValueError:checks.append(key+' alternate '+field+' rejected')
   else:raise AssertionError(key)
 out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir();(out/'report.json').write_text(json.dumps(dict(pure_controls_completed=True,controls=checks,control_count=len(checks),composer_main_executed=False,semantic_adapter_main_executed=False,ordinary_raw_readers_opened=False,canonical_reader_opened=False,accepted_function_credit=0,files=files),indent=2)+'\n')
if __name__=='__main__':run(sys.argv[1])
