"""Production validator controls using SQLite :memory: and literal byte maps."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sqlite3,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(output):
 out=Path(output).resolve();assert not out.exists();out.mkdir(parents=True)
 path=R/'tools/m4-controls-terminal-composite/expand_composite_inventory_v3.py';s=importlib.util.spec_from_file_location('production_composite_validator',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 c=sqlite3.connect(':memory:')
 for sql in m.SCHEMA.values():c.execute(sql)
 payload={};current={str(i):1 for i in range(16)};legacy={f'{l}-{i}':1 for l in('O0','O2')for i in range(1,13)}
 for n,(scope,caseid)in enumerate([('current16',str(i))for i in range(16)]+[('legacy24',k)for k in legacy]):
  p=str((out/f'fixture-{n}.bin').resolve());b=('literal-'+str(n)).encode();h=hashlib.sha256(b).hexdigest();payload[p]=b;c.execute('INSERT INTO physical VALUES(?,?,?,?,1)',(p,p.casefold(),h,len(b)));c.execute('INSERT INTO raw VALUES(?,?,?)',(scope,caseid,p));edge='current16-whole-inventory'if scope=='current16'else'legacy24-union-declared';c.execute('INSERT INTO edges VALUES(?,?,?)',(edge,p,h))
  if scope=='legacy24':c.execute('INSERT INTO edges VALUES(?,?,?)',('legacy-execution-'+caseid+'-declared',p,h))
 c.commit();c.execute('PRAGMA cache_size=-4096');c.execute('PRAGMA temp_store=FILE');plan=list(c.execute('EXPLAIN QUERY PLAN SELECT COUNT(*)FROM(SELECT path FROM physical EXCEPT SELECT path FROM edges)'));details=[str(r[3])for r in plan];assert not any('CORRELATED'in x.upper()for x in details);assert sum('SCAN edges'in x for x in details)==1 and sum('SCAN physical'in x for x in details)==1;rejects=[];measured=[];edges=[];registered=[]
 def run(db,content=payload,physical=40,raw=40,cc=current,lc=legacy):
  def measure(p,h,n):
   m.need(p in content and hashlib.sha256(content[p]).hexdigest()==h and len(content[p])==n,'Every literal current wholebyte hash/size');measured.append(p)
  return m.validate(db,physical,raw,cc,lc,measure,lambda p,h:registered.append((p,h)),lambda scope,p,h:edges.append((scope,p,h)))
 positive=run(c);assert positive['whole_dependency_rows_measured']==40 and positive['scoped_edges_expanded']==64 and len(measured)==40 and len(set(measured))==40
 first=next(iter(payload))
 mutations=[('missing-physical','DELETE FROM physical WHERE path=?',(first,)),('bad-folded','UPDATE physical SET folded=?WHERE path=?',('bogus',first)),('unseen','UPDATE physical SET seen=0 WHERE path=?',(first,)),('wrong-size','UPDATE physical SET size=size+1 WHERE path=?',(first,)),('physical-sha','UPDATE physical SET sha=?WHERE path=?',('0'*64,first)),('edge-sha','UPDATE edges SET sha=?WHERE path=?',('0'*64,first)),('missing-scoped-owner','DELETE FROM edges WHERE path=?',(first,)),('unrecognized-edge-scope','UPDATE edges SET scope=?WHERE path=?',('global-union',first)),('raw-case-invented','UPDATE raw SET caseid=?WHERE path=?',('16',first)),('raw-scope-invented','UPDATE raw SET scope=?WHERE path=?',('universal',first)),('raw-case-missing','DELETE FROM raw WHERE path=?',(first,)),('raw-physical-missing','UPDATE raw SET path=?WHERE path=?',(str((out/'missing.bin').resolve()),first)),('schema-extra-table','CREATE TABLE unknown(x)',()),('schema-extra-view','CREATE VIEW alternate AS SELECT * FROM physical',())]
 for label,sql,args in mutations:
  db=sqlite3.connect(':memory:');c.backup(db);db.execute(sql,args)
  try:run(db)
  except m.Refusal:rejects.append(label)
  else:raise AssertionError('Expected adverse refusal '+label)
  finally:db.close()
 for label,kwargs in [('wrong-receipt-rows',dict(physical=41)),('wrong-receipt-raw',dict(raw=41)),('current-case-count',dict(cc={**current,'0':2})),('legacy-case-count',dict(lc={**legacy,'O0-1':2})),('same-length-physical-mutation',dict(content={**payload,first:b'X'*len(payload[first])}))]:
  try:run(c,**kwargs)
  except m.Refusal:rejects.append(label)
  else:raise AssertionError('Expected adverse refusal '+label)
 # Scoped provenance may not collapse into a same-hash global declaration.
 legacy_path=next(c.execute("SELECT path FROM raw WHERE scope='legacy24'"))[0];db=sqlite3.connect(':memory:');c.backup(db);db.execute('DELETE FROM edges WHERE scope=?AND path=?',('legacy-execution-O0-1-declared',legacy_path))
 try:run(db)
 except m.Refusal:rejects.append('owncase-edge-not-global-union')
 else:raise AssertionError('Must retain owncase producer edge')
 finally:db.close()
 c_temp_store=c.execute('PRAGMA temp_store').fetchone()[0];c_cache_size=c.execute('PRAGMA cache_size').fetchone()[0];assert c_temp_store==1 and c_cache_size==-4096;c.close();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,pure_in_memory_production_validator=True,unscoped_query_plan=plan,no_correlated_edges_per_physical=True,sqlite_temp_store=c_temp_store,sqlite_cache_size=c_cache_size,physical_positive_rows=40,physical_positive_scoped_edges=64,adverse_controls=rejects,actual_inventory_opened=False,actual_composer_run=False,raw16_expander_unchanged=True,acceptance_executed=False,accepted_function_credit=0,files={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in(path,Path(__file__).resolve())}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),adverses=len(rejects))))
if __name__=='__main__':main(sys.argv[1])
