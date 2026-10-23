"""Pure in-memory final-conservation/progress controls; no production main."""
from pathlib import Path
import hashlib,importlib.util,json,sqlite3,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(output):
 out=Path(output).resolve();assert not out.exists();out.mkdir(parents=True);p=R/'tools/m4-controls-terminal-composite/review_completed_composite_v3.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='c1421d9c2a34390d637aa2d42bf46a79bf15b87834c0c3d34efb0537eb4d1d97';s=importlib.util.spec_from_file_location('sealed_final_conservation_only',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 db=sqlite3.connect(':memory:');db.execute('CREATE TABLE physical(path TEXT PRIMARY KEY,sha TEXT NOT NULL) WITHOUT ROWID');content={};hashes={}
 for n in range(5001):
  path=str((out/f'fixture-{n}.bin').resolve());data=('bytes-'+str(n)).encode();content[path]=data;hashes[path]=hashlib.sha256(data).hexdigest();db.execute('INSERT INTO physical VALUES(?,?)',(path,hashes[path]))
 direct={str((out/'ROOT-admission.json').resolve()):hashlib.sha256(b'admission').hexdigest(),str((out/'current-source.py').resolve()):hashlib.sha256(b'source').hexdigest()};content.update({list(direct)[0]:b'admission',list(direct)[1]:b'source'});reads=[];progress=[]
 def measure(path,h):
  path=str(path);assert path in content and hashlib.sha256(content[path]).hexdigest()==h,'Fresh literal complete bytehash';reads.append(path)
 positive=m.conserve_inputs(db,direct,measure,progress.append);assert positive==dict(physical_rows_rehashed=5001,direct_pins_rehashed=2,metadata_only_cache_used=False)and len(reads)==5003 and progress==[5000]
 rejects=[]
 for label,path in [('union-same-length-after-facet-mutation',next(iter(hashes))),('direct-receipt-after-facet-mutation',list(direct)[0]),('direct-code-after-facet-mutation',list(direct)[1])]:
  before=content[path];content[path]=b'X'*len(before)
  try:m.conserve_inputs(db,direct,measure)
  except AssertionError:rejects.append(label)
  else:raise AssertionError('Final input mutation must reject '+label)
  content[path]=before
 assert 'direct(sys.executable);direct(__file__)'in p.read_text();assert "Path(args[0]).suffix.lower()=='.pyc':raise FileNotFoundError"in p.read_text();assert p.read_text().index("pins={str(ap):admission_sha}")<p.read_text().index('for module_name in');assert 'record[\'preloaded_cache_reopened_after_hook\']=False'in p.read_text()
 db.close();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,production_conserve_function_used=True,synthetic_physical_rows=5001,synthetic_direct_rows=2,progress_callback_at_rows=progress,adverse_controls=rejects,stdlib_policy_static_guards_checked=True,production_main_executed=False,project_machinery_loaded=False,production_DB_opened=False,accepted_function_credit=0,files={str(x):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,Path(__file__).resolve())}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
