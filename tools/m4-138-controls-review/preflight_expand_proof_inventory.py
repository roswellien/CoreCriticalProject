"""Bounded adverse controls for final dependency expansion, no real gate run."""
from pathlib import Path
import collections,copy,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 out=R/'reports/m4-138-controls-review/proof-expansion-preflight-r1';assert not out.exists();out.mkdir();tool=R/'tools/m4-138-controls-review/expand_proof_inventory.py';m=load('union_expander',tool);v=load('sealed_inventory',R/'tools/m4-138-controls-review/full_raw_review_v2.py');pins={};controls=[]
 files=[]
 for n in range(16):p=out/f'raw-{n}.bin';p.write_bytes(bytes([n])*32);files.append(p)
 extra=out/'nonraw.txt';extra.write_text('Whole declared retained source proof');files.append(extra)
 idxpath=out/'inventory.sqlite';idx=v.Index(idxpath)
 for n,p in enumerate(files):idx.add(p,sha(p));idx.mark(p,sha(p),p.stat().st_size if n<16 else None,n if n<16 else None)
 idx.db.commit();count=idx.final(lambda *x:None)
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 proof=v.seal_index(idx,idxpath,pin,collections.Counter(final_integrity_files_rehashed=count,whole_export_targets_authenticated=16))
 base=dict(passed=True,scope='SYNTHETIC inventory only',proof_inventory=proof,files=dict(pins),cases=[dict(level=l,mode=n,whole_outputs=1)for l in['O0','O2']for n in range(1,9)],counts=dict(final_integrity_files_rehashed=17,whole_export_targets_authenticated=16),acceptance_requires_inventory_expansion=True,raw_exports_all_logical_entries=True,all_bounded_readers_closed=True,initializer_credit=0,capture_archives_opened=0,worker_executed=False)
 def run(label,data,refuse):
  p=out/(label+'.json');p.write_text(json.dumps(data,indent=2)+'\n');captured={}
  def register(path,h):assert path not in captured or captured[path]==h;captured[path]=h
  try:r=m.expand(p,sha(p),register)
  except m.Refusal:
   assert refuse,label;controls.append(dict(name=label,refused=True));return
  assert not refuse,label;assert r['whole_dependency_rows_measured']==17 and r['database_reader_closed']and not r['metadata_only_cache_used'];assert all(str(p.resolve())in captured for p in files);controls.append(dict(name=label,passed=True))
 run('whole-17row-expansion',base,False)
 for label,change in [('missing-completion',lambda x:x.update(passed=False)),('wrong-measured-total',lambda x:x['counts'].update(final_integrity_files_rehashed=18)),('missing-case',lambda x:x['cases'].pop()),('wrong-case-domain',lambda x:x['cases'][0].update(mode=9)),('wrong-case-count',lambda x:x['cases'][0].update(whole_outputs=2)),('wrong-schema',lambda x:x['proof_inventory']['columns'].update(physical=['path','sha'])),('missing-db-pin',lambda x:x['files'].clear())]:
  d=copy.deepcopy(base);change(d)
  if label=='missing-db-pin':
   # Missing structural pin is malformed input; require refusal before any row.
   try:run(label,d,True)
   except KeyError:controls.append(dict(name=label,refused=True))
  else:run(label,d,True)
 files[0].write_bytes(b'X'*32);run('same-size-raw-mutation',base,True);files[0].write_bytes(bytes(32))
 with idxpath.open('ab')as f:f.write(b'mutatedDB')
 run('database-mutation',base,True)
 for p in out.iterdir():
  if p.is_file():pin(p)
 for p in[tool,Path(__file__),R/'tools/m4-138-controls-review/full_raw_review_v2.py',Path(sys.executable)]:pin(p)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Synthetic sealed dependency-inventory expansion and adverse controls only; real controls inventory and acceptance not executed',controls=controls,synthetic_only=True,whole_real_inventory_expanded=False,initializer_credit=0,archive_reader_opened=False,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),cases=len(controls))))
if __name__=='__main__':main()
