"""Mandatory whole-byte expansion of a sealed accepted138 parent union.

This supports future141 acceptance lineage. A passed parent receipt alone or
its small direct files map does not retain its complete physical inventory.
"""
from pathlib import Path
import json,sqlite3
import acceptance138_storage as S
SCHEMA='CREATE TABLE dependencies (path TEXT PRIMARY KEY, sha TEXT NOT NULL, measured INTEGER NOT NULL DEFAULT 0) WITHOUT ROWID'
def need(v,label):
 if not v:raise ValueError(label)
def measured(p,h,n=None):
 p=Path(p);need(p.is_absolute()and p.is_file(),'Absolute entire dependency');before=p.stat();actual=S.sha(p);after=p.stat();need((before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns)and actual==S.digest(h)and(n is None or before.st_size==n),'Stable whole dependency identity');return p.resolve()
def expand(report_path,expected_sha,register,progress=None):
 report_path=measured(report_path,expected_sha);report=json.loads(report_path.read_bytes(),object_pairs_hook=S.unique_object);proof=report['proof_inventory'];closure=report['physical_closure']
 need(report['passed']is True and report['connected_roots']==138 and report['acceptance_requires_inventory_expansion']is True,'Actual accepted138 physical union required')
 need(closure['passed']is True and closure['metadata_only_cache_used']is False and closure['unique_physical_dependencies']==proof['physical_rows']==closure['whole_dependency_rows_measured'],'Complete prior byte-rehashed union')
 need(proof['sqlite_closed_before_hash']is True and proof['every_row_whole_byte_rehashed']is True and proof['acceptance_requires_inventory_expansion']is True and proof['schema']==SCHEMA and proof['expansion_query']=='SELECT path,sha,measured FROM dependencies ORDER BY path','Exact closed union contract')
 need(report['files'][proof['path']]==proof['sha256'],'Parent whole union DB physical pin');database=measured(proof['path'],proof['sha256'],proof['bytes']);register(str(report_path),expected_sha)
 for p,h in report['files'].items():measured(p,h);register(p,h)
 count=0;previous=None;db=None
 try:
  db=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON')
  need(dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='table'"))=={'dependencies':SCHEMA},'Exact actual union schema')
  need([r[1]for r in db.execute('PRAGMA table_info(dependencies)')]==['path','sha','measured']and db.execute('PRAGMA quick_check').fetchone()==('ok',),'Whole readable union structure')
  for p,h,seen in db.execute(proof['expansion_query']):
   need(p==S.normalized(str(Path(p).resolve()))and(previous is None or previous<p)and type(seen)is int and seen==1,'All exact normalized prior measured rows');previous=p
   measured(p,h);register(p,h);count+=1
   if progress and count%5000==0:progress(count)
  need(count==proof['physical_rows'],'All-and-only complete parent union')
 finally:
  if db:db.close()
 measured(database,proof['sha256'],proof['bytes']);measured(report_path,expected_sha)
 return dict(passed=True,whole_dependency_rows_measured=count,database_reader_closed=True,metadata_only_cache_used=False,initializer_credit=0)
