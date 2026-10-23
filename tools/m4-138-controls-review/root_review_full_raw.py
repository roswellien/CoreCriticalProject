"""Root independent bounded implementation admission; never opens captures."""
from pathlib import Path
import collections,hashlib,importlib.util,io,json,sqlite3,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-controls-review/full-raw-root-implementation-review-r1';assert not out.exists();out.mkdir();pins={};checks=[]
 prep=R/'reports/m4-138-controls-review/full-raw-implementation-preparation-r2/report.json'
 assert sha(prep)=='7b5e75c535441e9124af8ddda49d28bdfd40ad289f1a1594f0d03e92339403d0'
 d=json.loads(prep.read_bytes());assert d['passed']and d['full_real_raw_inventory_reviewed']is False
 for p,h in d['files'].items():assert sha(p)==h;pins[p]=h
 pins[str(prep)]=sha(prep);tool=R/'tools/m4-138-controls-review/full_raw_review_v2.py'
 assert sha(tool)=='88a5ef8671b190d18330267d54106b5e8d23c19a989dd1fa3b4ee18bc969941f'
 spec=importlib.util.spec_from_file_location('root_full_raw_review',tool);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 def reject(label,fn):
  try:fn()
  except (m.Refusal,ValueError):checks.append(label);return
  raise AssertionError(label)
 for s in['../escape','A/../B','/absolute','C:/drive','a\\b','a//b','a/./b','a\0b']:
  reject('unsafe-relative:'+repr(s),lambda s=s:m.relative(s))
 for chunk in[1,2,3,8]:
  s=m.StreamJSON(io.StringIO('{"abc":12345,"nested":{"x":7}}'),chunk)
  assert list(s.pairs())==[('abc',12345),('nested',{'x':7})];s.finish();checks.append('stream-boundary:'+str(chunk))
 reject('duplicate-nested-key',lambda:list(m.StreamJSON(io.StringIO('{"x":{"a":1,"a":2}}'),2).pairs()))
 root=out/'ordinary';root.mkdir();a=root/'before.bin';b=root/'after.bin';a.write_bytes(b'first whole extent');b.write_bytes(a.read_bytes())
 indexpath=out/'synthetic-proof.sqlite';idx=m.Index(indexpath)
 for p in[a,b]:idx.add(p,sha(p));idx.mark(p,sha(p),p.stat().st_size,0)
 reject('duplicate-physical',lambda:idx.add(a,sha(a)))
 m.equal_files(a,b);checks.append('whole-retry-equal');b.write_bytes(b'changed same bytes');reject('whole-retry-mutated',lambda:m.equal_files(a,b));b.write_bytes(a.read_bytes())
 # Recreate the index after the deliberate mutation so stat observations are genuine.
 idx.close();freshpath=out/'durable-proof.sqlite';idx=m.Index(freshpath)
 for p in[a,b]:idx.add(p,sha(p));idx.mark(p,sha(p),p.stat().st_size,0)
 count=idx.final(lambda *x:None);assert count==2
 def pin(p):pins[str(p.resolve())]=sha(p);return p.resolve()
 proof=m.seal_index(idx,freshpath,pin,collections.Counter(final_integrity_files_rehashed=2,whole_export_targets_authenticated=2))
 assert idx.closed and proof['physical_rows']==2 and proof['sqlite_closed_before_hash']
 db=sqlite3.connect(freshpath.as_uri()+'?mode=ro',uri=True)
 try:rows=list(db.execute(proof['expansion_query']));assert len(rows)==2;assert all(sha(p)==h and Path(p).stat().st_size==n for p,h,n,c in rows)
 finally:db.close()
 checks.append('durable-readonly-whole-content-expansion')
 original=pins[str(freshpath.resolve())]
 with freshpath.open('ab')as f:f.write(b'mutated')
 reject('durable-proof-mutated',lambda:m.authenticate(freshpath,original))
 # Mutated fixture is explicitly adverse evidence, not an accepted inventory.
 pins[str(freshpath.resolve())]=sha(freshpath)
 for p in[a,b,indexpath]:pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(Path(sys.executable).resolve())]=sha(sys.executable)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Root independently reviewed complete streaming/inventory/retry/final-closure/sealed-SQLite implementation and exercised bounded positive/adverse cases; real full raw review admitted separately',checks=checks,synthetic_cases=len(checks),implementation_sha256=sha(tool),complete_real_raw_inventory_reviewed=False,archive_reader_opened=False,worker_executed=False,initializer_credit=0,full_raw_review_implementation_admitted=True,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True)))
if __name__=='__main__':main()
