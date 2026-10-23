"""Stream sealed controls proof rows into a fresh acceptance dependency union.

This is an integrity utility, not an initializer acceptance implementation.
The default measures every declared byte again; metadata never replaces hashes.
"""
from pathlib import Path
import collections,hashlib,json,re,sqlite3
HEX=re.compile(r'[0-9a-f]{64}\Z')
PHYSICAL=['k','path','sha','rawcase','bytes','size','mtime','ctime','seen']
MANIFEST=['k','rel','path','sha','bytes','seen']
class Refusal(ValueError):pass
def need(v,label):
 if not v:raise Refusal(label)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def measured(p,h,n=None):
 p=Path(p);need(p.is_absolute()and p.is_file(),'Absolute existing dependency');need(HEX.fullmatch(h),'Exact SHA256');before=p.stat();actual=sha(p);after=p.stat()
 need((before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Dependency stable during whole content measurement')
 need(actual==h and(n is None or before.st_size==n),'Whole content identity and measured length');return p.resolve()
def expand(report_path,expected_sha,register,progress=None):
 """Authenticate report/DB, measure each row, register union dependencies, close."""
 report_path=measured(report_path,expected_sha);d=json.loads(report_path.read_bytes());p=d['proof_inventory']
 need(d['passed']is True and d['acceptance_requires_inventory_expansion']is True and d['raw_exports_all_logical_entries']is True and d['all_bounded_readers_closed']is True,'Completed sealed full inventory gate')
 need(d['initializer_credit']==0 and d['capture_archives_opened']==0 and d['worker_executed']is False,'Bounded integrity-only gate')
 need(p['sqlite_closed_before_hash']is True and d['files'][p['path']]==p['sha256'],'Closed proof database physical pin')
 database=measured(p['path'],p['sha256'],p['bytes']);register(str(report_path),expected_sha);register(str(database),p['sha256'])
 for path,h in d['files'].items():measured(path,h);register(path,h)
 connection=None;count=0;cases=collections.Counter()
 try:
  connection=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True);connection.execute('PRAGMA query_only=ON')
  schemas=dict(connection.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"))
  need(schemas==p['schema']and set(schemas)=={'manifest','physical'},'Exact sealed database schemas')
  columns={name:[r[1]for r in connection.execute('PRAGMA table_info('+name+')')]for name in['manifest','physical']}
  need(columns==p['columns']=={'manifest':MANIFEST,'physical':PHYSICAL},'Exact schema columns/order')
  need(connection.execute('PRAGMA quick_check').fetchone()==('ok',),'Complete SQLite structure')
  need(p['physical_rows']==d['counts']['final_integrity_files_rehashed']and p['raw_rows']==d['counts']['whole_export_targets_authenticated']and p['nonraw_rows']==p['physical_rows']-p['raw_rows'],'Whole measured inventory counts')
  need(len(d['cases'])==16 and{(c['level'],c['mode'])for c in d['cases']}=={(l,m)for l in['O0','O2']for m in range(1,9)},'Actual sixteen-case domain')
  previous=None
  for k,path,h,rawcase,n,size,mtime,ctime,seen in connection.execute('SELECT k,path,sha,rawcase,bytes,size,mtime,ctime,seen FROM physical ORDER BY k'):
   need(isinstance(k,str)and(previous is None or previous<k),'Unique ordered physical identity');previous=k
   target=Path(path);need(target.is_absolute()and str(target.resolve())==path and k==path.casefold(),'Exact canonical absolute identity')
   need(target.suffix.lower()not in{'.mwb','.mwc','.zip','.7z'},'Ordinary controls dependency')
   need(type(size)is int and size>=0 and type(mtime)is int and type(ctime)is int and seen==1,'Every row independently authenticated at review')
   if rawcase is not None:need(type(rawcase)is int and 0<=rawcase<16 and n==size,'Exact rawcase/length');cases[rawcase]+=1
   else:need(n is None,'Nonraw dependency schema')
   measured(target,h,size);register(path,h);count+=1
   if progress and count%5000==0:progress(count)
  need(count==p['physical_rows']and sum(cases.values())==p['raw_rows'],'All-and-only expanded rows')
  need([dict(rawcase=k,whole_targets=v)for k,v in sorted(cases.items())]==p['case_inventory_counts'],'Exact sealed per-case inventory')
  need(all(cases[i]==c['whole_outputs']for i,c in enumerate(d['cases'])),'Expanded cases match actual review case outputs')
  need(connection.execute('SELECT COUNT(*) FROM manifest').fetchone()[0]==p['last_case_manifest_rows']and connection.execute('SELECT COUNT(*) FROM manifest WHERE seen<>1').fetchone()[0]==0,'Final retained manifest complete')
 finally:
  if connection:connection.close()
 measured(database,p['sha256'],p['bytes']);measured(report_path,expected_sha)
 return dict(passed=True,whole_dependency_rows_measured=count,raw_rows=sum(cases.values()),database_reader_closed=True,metadata_only_cache_used=False,initializer_credit=0)
