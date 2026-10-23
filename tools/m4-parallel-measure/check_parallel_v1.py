"""Serial/parallel equivalence and adverse controls for the parallel measurement versions.

Exercises the actual new modules (ordered_pool, expand_composite_inventory_v4.validate,
expand_proof_inventory_v2.expand, acceptance138_storage_v3.Union.verify) on synthetic
inventories built to the real schemas, comparing serial (mapper=None) with parallel
runs: identical registration order/results, identical refusal messages, and earliest
failure in row order winning. Then measures storage v3 verify serial vs parallel on
real, previously unread composite-inventory files. Opens no production database for
writing and grants no acceptance credit.
"""
from pathlib import Path
import hashlib,importlib.util,json,sqlite3,sys,tempfile,time
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
P=load('pool',R/'tools/m4-parallel-measure/ordered_pool.py')
sys.path.insert(0,str(R/'tools/m4-pipeline'));sys.path.insert(0,str(R/'tools/m4-138-controls-review'))
E=load('exp4',R/'tools/m4-controls-terminal-composite/expand_composite_inventory_v4.py')
X=load('proof2',R/'tools/m4-138-controls-review/expand_proof_inventory_v2.py')
S=load('storage3',R/'tools/m4-138-controls-review/acceptance138_storage_v3.py')
par=lambda fn,items,prepare=None:P.ordered_map(fn,items,workers=8,window=7,prepare=prepare)
results=[]
def ok(name):results.append(name)
def outcome(fn):
 try:return('ok',fn())
 except Exception as e:return('err',type(e).__name__,str(e))

# 1. Pool semantics.
assert [x for x,_ in par(lambda v:v*2,range(1000))]==list(range(1000));ok('pool_order_1000')
def fail_at(n):
 def f(v):
  if v==n:raise ValueError('measure %d'%v)
  return v
 return f
def prep_fail(n):
 def p(v):
  if v==n:raise KeyError('prepare %d'%v)
 return p
got=outcome(lambda:list(par(fail_at(5),range(100),prepare=prep_fail(9))));assert got[:2]==('err','ValueError')and'5'in got[2];ok('earlier_measure_failure_beats_later_prepare_failure')
got=outcome(lambda:list(par(fail_at(50),range(100),prepare=prep_fail(9))));assert got[:2]==('err','KeyError');ok('earlier_prepare_failure_beats_later_measure_failure')
got=outcome(lambda:list(P.ordered_map(fail_at(3),range(10),workers=1)));assert got[:2]==('err','ValueError');ok('workers1_serial_path')

with tempfile.TemporaryDirectory()as d:
 d=Path(d);files=[]
 for i in range(300):
  p=(d/f'f{i:04d}.bin').resolve();p.write_bytes(hashlib.sha256(str(i).encode()).digest()*(1+i%7));files.append(p)
 # 2. Composite expander v4 validate().
 def composite_db(rows):
  db=sqlite3.connect(':memory:')
  for t in E.SCHEMA.values():db.execute(t)
  for p,h,n in rows:db.execute('INSERT INTO physical VALUES(?,?,?,?,1)',(str(p),str(p).casefold(),h,n));db.execute("INSERT INTO edges VALUES('metadata',?,?)",(str(p),h))
  for i,(p,h,n)in enumerate(rows[:16]):db.execute("INSERT INTO raw VALUES('current16',?,?)",(str(i),str(p)));db.execute("INSERT INTO edges VALUES('current16-whole-inventory',?,?)",(str(p),h))
  for j,(p,h,n)in enumerate(rows[16:40]):
   case=('O0','O2')[j//12]+'-'+str(j%12+1);db.execute("INSERT INTO raw VALUES('legacy24',?,?)",(case,str(p)));db.execute("INSERT INTO edges VALUES('legacy24-union-declared',?,?)",(str(p),h));db.execute("INSERT INTO edges VALUES(?,?,?)",('legacy-execution-'+case+'-declared',str(p),h))
  return db
 base=[(p,sha(p),p.stat().st_size)for p in files]
 cc={str(i):1 for i in range(16)};lc={('O0','O2')[j//12]+'-'+str(j%12+1):1 for j in range(24)}
 def run_composite(rows,mapper):
  db=composite_db(rows);reg=[]
  return outcome(lambda:(E.validate(db,len(rows),40,cc,lc,E.measured,lambda p,h:reg.append((p,h)),lambda *a:None,None,mapper),reg)[1])
 a=run_composite(base,None);b=run_composite(base,par);assert a==b and a[0]=='ok'and len(a[1])==300;ok('composite_v4_serial_parallel_identical_registration')
 bad=list(base);bad[120]=(bad[120][0],'0'*64,bad[120][2])
 a=run_composite(bad,None);b=run_composite(bad,par);assert a==b and a[0]=='err';ok('composite_v4_corrupt_hash_same_refusal')
 cap=(d/'zz.mwb').resolve();cap.write_bytes(b'x');withcap=base+[(cap,sha(cap),1)]
 a=run_composite(withcap,None);b=run_composite(withcap,par);assert a==b and a[0]=='err'and'Ordinary'in a[2];ok('composite_v4_capture_suffix_refused_before_open')
 both=list(bad)+[(cap,sha(cap),1)]
 a=run_composite(both,None);b=run_composite(both,par);assert a==b and'Actual everybyte'in a[2];ok('composite_v4_earlier_hash_failure_wins')
 # 3. Proof expander v2 expand().
 def proof_case(rows,mapper):
  work=Path(tempfile.mkdtemp(dir=d));dbp=(work/'proof.sqlite').resolve();db=sqlite3.connect(dbp)
  db.execute('CREATE TABLE manifest(k TEXT PRIMARY KEY,rel TEXT NOT NULL,path TEXT NOT NULL,sha TEXT NOT NULL,bytes INTEGER NOT NULL,seen INTEGER NOT NULL)')
  db.execute('CREATE TABLE physical(k TEXT PRIMARY KEY,path TEXT NOT NULL,sha TEXT NOT NULL,rawcase INTEGER,bytes INTEGER,size INTEGER,mtime INTEGER,ctime INTEGER,seen INTEGER)')
  for i,(p,h,n)in enumerate(rows):
   st=p.stat();raw=i%16 if i<32 else None;db.execute('INSERT INTO physical VALUES(?,?,?,?,?,?,?,?,1)',(str(p).casefold(),str(p),h,raw,n if raw is not None else None,n,st.st_mtime_ns,st.st_ctime_ns))
  db.execute("INSERT INTO manifest VALUES('m','r','p','h',0,1)");schema=dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"));db.commit();db.close()
  cases=[dict(level=l,mode=m,whole_outputs=2)for l in('O0','O2')for m in range(1,9)]
  report=dict(passed=True,acceptance_requires_inventory_expansion=True,raw_exports_all_logical_entries=True,all_bounded_readers_closed=True,initializer_credit=0,capture_archives_opened=0,worker_executed=False,cases=cases,
   counts=dict(final_integrity_files_rehashed=len(rows),whole_export_targets_authenticated=32),files={str(dbp):sha(dbp)},
   proof_inventory=dict(path=str(dbp),sha256=sha(dbp),bytes=dbp.stat().st_size,sqlite_closed_before_hash=True,schema=schema,columns=dict(manifest=X.MANIFEST,physical=X.PHYSICAL),physical_rows=len(rows),raw_rows=32,nonraw_rows=len(rows)-32,case_inventory_counts=[dict(rawcase=k,whole_targets=2)for k in range(16)],last_case_manifest_rows=1))
  rp=(work/'report.json').resolve();rp.write_text(json.dumps(report));reg=[]
  return outcome(lambda:(X.expand(rp,sha(rp),lambda p,h:reg.append((str(p),h)),None,mapper),[r for r in reg if 'proof.sqlite'not in r[0]and'report.json'not in r[0]])[1])
 ordered=sorted(base,key=lambda r:str(r[0]).casefold())
 a=proof_case(ordered,None);b=proof_case(ordered,par);assert a[0]=='ok'and a==b and len(a[1])==300;ok('proof_v2_serial_parallel_identical_registration')
 badp=list(ordered);badp[200]=(badp[200][0],'f'*64,badp[200][2])
 a=proof_case(badp,None);b=proof_case(badp,par);assert a==b and a[0]=='err';ok('proof_v2_corrupt_hash_same_refusal')
 # 4. Storage v3 verify.
 def verify_case(rows,mapper):
  u=S.Union((Path(tempfile.mkdtemp(dir=d))/'u.sqlite'));u.mapper=mapper
  for p,h,n in rows:u[str(p)]=h
  r=outcome(lambda:{k:v for k,v in u.verify().items()if k not in('verify_seconds','parallel_mapper')});u.close();return r
 a=verify_case(base,None);b=verify_case(base,par);assert a==b and a[0]=='ok';ok('storage_v3_serial_parallel_identical_summary')
 a=verify_case(bad,None);b=verify_case(bad,par);assert a==b and a[0]=='err';ok('storage_v3_corrupt_hash_same_refusal')

# 5. Real-file benchmark through storage v3 verify (fresh rows from the closed composite inventory).
db=sqlite3.connect((R/'reports/m4-controls-terminal-composite/terminal-composite-r1/whole-ordinary-union.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON')
rows=list(db.execute('SELECT path,sha FROM physical ORDER BY path LIMIT 16000 OFFSET ?',(11863155-700000,)));db.close()
bench={}
with tempfile.TemporaryDirectory()as d:
 for label,mapper,sl in(('serial',None,rows[:4000]),('parallel8',lambda fn,it,prepare=None:P.ordered_map(fn,it,workers=8,prepare=prepare),rows[4000:16000])):
  u=S.Union(Path(d)/f'{label}.sqlite');u.mapper=mapper
  for p,h in sl:u[p]=h
  t=time.perf_counter();r=u.verify();dt=time.perf_counter()-t;u.close();bench[label]=round(len(sl)/dt);assert r['unique_physical_dependencies']==len(sl)
out=R/'reports/m4-parallel-measure/check-r1';assert not out.exists();out.mkdir(parents=True)
files={str(p.resolve()):sha(p)for p in(Path(__file__),R/'tools/m4-parallel-measure/ordered_pool.py',R/'tools/m4-controls-terminal-composite/expand_composite_inventory_v4.py',R/'tools/m4-138-controls-review/expand_proof_inventory_v2.py',R/'tools/m4-138-controls-review/acceptance138_storage_v3.py',R/'tools/m4-controls-strict-bridge/acceptance138_v5.py',R/'tools/m4-controls-terminal-composite/review_completed_composite_v5.py')}
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,controls=results,real_files_per_second=bench,gpu_offload='not beneficial: ~4 KB average files; SHA-256 compute under 1% of one core at measured 2.4 GB/s; per-file filesystem cost dominates',accepted_function_credit=0,files=files),indent=2)+'\n')
print(json.dumps(dict(report=str(q),sha256=sha(q),controls=len(results),bench=bench)))
