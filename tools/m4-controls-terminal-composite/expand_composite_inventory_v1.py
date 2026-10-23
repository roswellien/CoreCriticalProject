"""Distinct closed builder7 union expansion: actual bytes and scoped edges."""
from pathlib import Path
import collections,hashlib,json,re,sqlite3
HEX=re.compile(r'[0-9a-f]{64}\Z')
SCHEMA={
 'physical':'CREATE TABLE physical(path TEXT PRIMARY KEY,folded TEXT UNIQUE,sha TEXT NOT NULL,size INTEGER NOT NULL,seen INTEGER NOT NULL) WITHOUT ROWID',
 'edges':'CREATE TABLE edges(scope TEXT NOT NULL,path TEXT NOT NULL,sha TEXT NOT NULL,PRIMARY KEY(scope,path)) WITHOUT ROWID',
 'raw':'CREATE TABLE raw(scope TEXT NOT NULL,caseid TEXT NOT NULL,path TEXT UNIQUE NOT NULL,PRIMARY KEY(scope,caseid,path)) WITHOUT ROWID'}
COLS={'physical':['path','folded','sha','size','seen'],'edges':['scope','path','sha'],'raw':['scope','caseid','path']}
ROLES={'legacy24_aggregate','legacy24_admission','legacy24_union','current16_fullraw','current16_semantic_review','current8_preparation','current8_build','current8_execution','current8_scope_review','current8_physical_review','legacy12_preparation','legacy12_build','legacy_prelaunch_complete_review','named_CS24_TLS64_supplement'}
class Refusal(ValueError):pass
def need(v,s):
 if not v:raise Refusal(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def measured(p,h,n=None):
 p=Path(p);need(p.is_absolute()and p.is_file()and str(p.resolve())==str(p),'Canonical existing absolute physical path');need(type(h)is str and HEX.fullmatch(h),'Whole SHA256');a=p.stat();v=sha(p);b=p.stat();need((a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_size,b.st_mtime_ns,b.st_ctime_ns),'Stable wholebyte measurement');need(v==h and(n is None or type(n)is int and n==a.st_size),'Actual everybyte SHA/length');return p
def allowed_scope(s):
 if type(s)is not str:return False
 base=s[:-9]if s.endswith('-declared')else s
 return base in ROLES|{'manifest','metadata','legacy24-union','current16-whole-inventory'}or re.fullmatch(r'legacy(?:-execution)?-O[02]-(?:[1-9]|1[0-2])',base)is not None
def validate(connection,physical_rows,raw_rows,current_counts,legacy_counts,measure,register,register_edge,progress=None):
 """Same production validator used with synthetic in-memory SQLite controls."""
 need(type(physical_rows)is int and physical_rows>0 and type(raw_rows)is int and raw_rows>0,'Typed receipt counts')
 need(set(current_counts)=={str(i)for i in range(16)}and set(legacy_counts)=={f'{l}-{m}'for l in('O0','O2')for m in range(1,13)},'Exact16+24 case domains')
 need(all(type(v)is int and v>0 for v in list(current_counts.values())+list(legacy_counts.values())),'Positive actual percase counts')
 tables=dict(connection.execute("SELECT name,sql FROM sqlite_master WHERE type='table'"));need(tables==SCHEMA,'Exact distinct composite schema')
 need({n:[r[1]for r in connection.execute('PRAGMA table_info('+n+')')]for n in COLS}==COLS,'Exact column order')
 need(connection.execute("SELECT COUNT(*)FROM sqlite_master WHERE type IN('view','trigger')").fetchone()[0]==0,'No alternate view/trigger behavior')
 need(connection.execute('PRAGMA quick_check').fetchone()==('ok',),'Complete SQLite integrity')
 need(connection.execute('SELECT COUNT(*) FROM physical').fetchone()[0]==physical_rows,'Exact physical row extent')
 need(connection.execute('SELECT COUNT(*) FROM raw').fetchone()[0]==raw_rows,'Exact raw row extent')
 need(connection.execute('SELECT COUNT(*)FROM edges e LEFT JOIN physical p ON p.path=e.path WHERE p.path IS NULL OR e.sha<>p.sha').fetchone()[0]==0,'Every scoped edge owns same physical row/hash')
 need(connection.execute('SELECT COUNT(*)FROM physical p WHERE NOT EXISTS(SELECT 1 FROM edges e WHERE e.path=p.path)').fetchone()[0]==0,'No unscoped physical dependency')
 need(connection.execute('SELECT COUNT(*)FROM raw r LEFT JOIN physical p ON p.path=r.path WHERE p.path IS NULL').fetchone()[0]==0,'Raw membership physically measured')
 count=0;size_total=0
 for path,folded,h,size,seen in connection.execute('SELECT path,folded,sha,size,seen FROM physical ORDER BY path'):
  need(type(path)is str and str(Path(path).resolve())==path and Path(path).is_absolute()and folded==path.casefold(),'Canonical exact folded physical identity')
  need(Path(path).suffix.lower()not in('.mwb','.mwi','.mwc','.zip','.7z')and Path(path).name!='transport.json','Ordinary physical union only')
  need(type(h)is str and HEX.fullmatch(h)and type(size)is int and size>=0 and type(seen)is int and seen==1,'Every sealed row typed and seen')
  measure(path,h,size);register(path,h);count+=1;size_total+=size
  if progress and count%5000==0:progress(count)
 edges=0
 for scope,path,h in connection.execute('SELECT scope,path,sha FROM edges ORDER BY scope,path'):
  need(allowed_scope(scope),'Exact finite producer scope domain');register_edge(scope,path,h);edges+=1
 raw_counts=collections.Counter()
 for scope,caseid,path in connection.execute('SELECT scope,caseid,path FROM raw ORDER BY scope,caseid,path'):
  need(scope in('current16','legacy24')and type(caseid)is str,'Exact raw named scope/type')
  expected=current_counts if scope=='current16'else legacy_counts;need(caseid in expected,'Exact rawcase member')
  source_scope='current16-whole-inventory'if scope=='current16'else'legacy24-union-declared'
  need(connection.execute('SELECT COUNT(*)FROM edges WHERE scope=?AND path=?',(source_scope,path)).fetchone()[0]==1,'Raw belongs to exact own inventory scoped edge')
  if scope=='legacy24':need(connection.execute('SELECT COUNT(*)FROM edges WHERE scope=?AND path=?',('legacy-execution-'+caseid+'-declared',path)).fetchone()[0]==1,'Legacy raw belongs to exact producing case inventory')
  raw_counts[(scope,caseid)]+=1
 need({k[1]:v for k,v in raw_counts.items()if k[0]=='current16'}==current_counts and{k[1]:v for k,v in raw_counts.items()if k[0]=='legacy24'}==legacy_counts,'All and only exact percase physical raw outputs')
 need(sum(raw_counts.values())==raw_rows,'Whole unique raw membership')
 return dict(whole_dependency_rows_measured=count,physical_bytes_measured=size_total,raw_rows=raw_rows,current16_raw_rows=sum(current_counts.values()),legacy24_raw_rows=sum(legacy_counts.values()),scoped_edges_expanded=edges)
def expand(report_path,expected_sha,register,*,register_edge,progress=None):
 """Authenticate closed report/DB and every byte; retain per-scope provenance."""
 connection=None;result=None
 report=measured(Path(report_path).resolve(),expected_sha);need(report.stat().st_size<2*1024*1024,'Bounded composite receipt');d=json.loads(report.read_bytes());p=d['proof_inventory']
 need(d['passed']is True and d['scope_identity']=='current138_terminal_legacy24_current16_controls_composite_v1'and d['acceptance_requires_inventory_expansion']is True,'Exact completed composite role')
 need(d['initializer_credit']==0 and type(d['initializer_credit'])is int and d['raw_exports_all_logical_entries']is True and d['raw_export_readers_closed']is True and d['all_bounded_readers_closed']is True,'Actual whole raw and closed flags; credit0')
 need(d['whole_old_registry_private_retry_claim']is False and d['whole_permissions_retry_claim']is False,'Retained observation limits')
 need(p['sqlite_closed_before_hash']is True and p['every_row_whole_byte_rehashed']is True and p['expansion_query']=='SELECT path,sha,size,seen FROM physical ORDER BY path'and p['scope_edges_query']=='SELECT scope,path,sha FROM edges ORDER BY scope,path','Exact durable builder7 queries/closure')
 database=measured(Path(p['path']),p['sha256'],p['bytes']);need(d['files'][str(database)]==p['sha256'],'Report pins actual database')
 builder=Path(__file__).resolve().with_name('build_v7.py');need(str(builder)in d['files'],'Actual builder7 declaration');measured(builder,d['files'][str(builder)]);register(str(builder),d['files'][str(builder)])
 need(d['current16_counts']['whole_export_targets_authenticated']==10691866 and d['current16_counts']['whole_exported_retry_files_equal']==3547696,'Current16 output/retry domains preserved')
 try:
  connection=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True);connection.execute('PRAGMA query_only=ON')
  def role(scope):
   rows=list(connection.execute('SELECT path,sha FROM edges WHERE scope=?',(scope,)));need(len(rows)==1,'One physically scoped producer receipt '+scope);path,h=rows[0];rp=measured(Path(path),h);need(rp.stat().st_size<32*1024*1024,'Bounded named receipt');return json.loads(rp.read_bytes()),path,h
  raw,rp,rh=role('current16_fullraw');need(d['files'].get(rp)==rh and raw['passed']is True and raw['raw_export_readers_closed']is True and raw['all_bounded_readers_closed']is True,'Current16 same closed producing role')
  cc={str(x['rawcase']):x['whole_targets']for x in raw['proof_inventory']['case_inventory_counts']};need(len(raw['proof_inventory']['case_inventory_counts'])==16 and sum(cc.values())==10691866,'Actual16 complete case count witnesses')
  lc={};roots={}
  for l in('O0','O2'):
   for mode in range(1,13):
    case=l+'-'+str(mode);e,ep,eh=role('legacy-execution-'+case);need(e['passed']is True and e['worker_closed']is True and e['worker_executed']is True and(e['level'],e['mode'])==(l,mode)and e['facts']['exit_code']==0,'Closed exact producing legacy case')
    need(connection.execute('SELECT COUNT(*)FROM edges WHERE scope=?AND path=?AND sha=?',('legacy24_aggregate-declared',ep,eh)).fetchone()[0]==1,'Actual terminal legacy aggregate declares own case')
    root=Path(e['facts']['arguments'][5]).resolve();need(all(not root.is_relative_to(old)and not old.is_relative_to(root)for old in roots.values()),'Unique nonoverlapping rawcase root');roots[case]=root;n=0
    for path, in connection.execute('SELECT path FROM edges WHERE scope=?',('legacy-execution-'+case+'-declared',)):
     if Path(path).is_relative_to(root):
      need(connection.execute('SELECT scope,caseid FROM raw WHERE path=?',(path,)).fetchone()==('legacy24',case),'Every producer declared actual raw output covered once');n+=1
    lc[case]=n
    for path, in connection.execute("SELECT path FROM raw WHERE scope='legacy24'AND caseid=?",(case,)):need(Path(path).is_relative_to(root),'Every retained legacy membership belongs to own actual output root')
  result=validate(connection,p['physical_rows'],d['counts']['whole_export_targets_authenticated'],cc,lc,measured,register,register_edge,progress)
 finally:
  if connection is not None:connection.close()
 measured(database,p['sha256'],p['bytes']);measured(report,expected_sha);register(str(database),p['sha256']);register(str(report),expected_sha);tool=Path(__file__).resolve();register(str(tool),sha(tool))
 return dict(passed=True,**result,database_reader_closed=True,metadata_only_cache_used=False,scoped_provenance_preserved=True,initializer_credit=0)
