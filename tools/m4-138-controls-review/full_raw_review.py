"""Independent sealed ordinary inventory/private-retry review. No archives/workers.

Production run is deliberately separate from preflight. Every content hash is
measured, including a final independent integrity pass. SQLite bounds memory;
it stores identity/inventory joins only and never supplies unmeasured payloads.
"""
from pathlib import Path,PurePosixPath,PureWindowsPath
import collections,contextlib,hashlib,json,os,re,sqlite3,struct,sys,time,traceback
R=Path(__file__).resolve().parents[2]
BAD={'.zip','.mwb','.mwc','.7z'}
HEX=re.compile('[0-9a-f]{64}\\Z')
class Refusal(ValueError):pass
def need(v,s):
 if not v:raise Refusal(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ordinary(p):
 p=Path(p).resolve();need(p.suffix.lower()not in BAD,'Archive target refused');need(p.is_file(),'Whole ordinary file exists');return p
def relative(s):
 need(isinstance(s,str)and s and '\\'not in s and ':'not in s and not s.startswith('/')and not any(ord(c)<32 for c in s),'Canonical safe relative name')
 p=PurePosixPath(s);need(p.as_posix()==s and all(x not in('','.','..')for x in s.split('/'))and not PureWindowsPath(s).is_absolute(),'Confined relative components');return s
def stable(p):
 s=Path(p).stat();return(s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def authenticate(p,expected,n=None):
 need(isinstance(expected,str)and HEX.fullmatch(expected),'Whole expectedSHA256');p=ordinary(p);before=stable(p);h=sha(p);need(stable(p)==before,'File changed during content hash');need(h==expected,'Whole physicalSHA256 '+str(p));need(n is None or before[0]==n,'Whole physical length '+str(p));return p,before
def equal_files(a,b):
 a=ordinary(a);b=ordinary(b);sa,sb=stable(a),stable(b);need(sa[0]==sb[0],'Whole retry length')
 with a.open('rb')as x,b.open('rb')as y:
  while True:
   u,v=x.read(1024*1024),y.read(1024*1024);need(u==v,'Whole streamed retry payload')
   if not u:break
 need(stable(a)==sa and stable(b)==sb,'Retry inputs stable')
class StreamJSON:
 """Incremental object reader, bounded per individual JSON value."""
 def __init__(self,f,chunk=1024*1024):self.f=f;self.chunk=chunk;self.buf='';self.eof=False;self.decoder=json.JSONDecoder(object_pairs_hook=self.unique)
 @staticmethod
 def unique(items):
  d={}
  for k,v in items:need(k not in d,'Duplicate nestedJSON key');d[k]=v
  return d
 def more(self):
  s=self.f.read(self.chunk);self.buf+=s;self.eof=not s;need(len(self.buf)<=32*1024*1024,'Bounded individual JSON value')
 def trim(self):
  self.buf=self.buf.lstrip()
  while not self.buf and not self.eof:self.more();self.buf=self.buf.lstrip()
 def expect(self,c):
  self.trim();need(self.buf.startswith(c),'ExactJSON delimiter '+c);self.buf=self.buf[len(c):]
 def value(self):
  self.trim()
  while True:
   try:v,n=self.decoder.raw_decode(self.buf)
   except json.JSONDecodeError:
    need(not self.eof,'CompleteJSON value');self.more();continue
   # A scalar split exactly at a chunk boundary must not be accepted early.
   if n==len(self.buf)and not self.eof:self.more();continue
   self.buf=self.buf[n:];return v
 def pairs(self):
  self.expect('{');first=True
  while True:
   self.trim()
   if self.buf.startswith('}'):self.buf=self.buf[1:];return
   if not first:self.expect(',')
   key=self.value();need(isinstance(key,str),'Object key string');self.expect(':');yield key,self.value();first=False
 def finish(self):
  self.trim();need(not self.buf and self.eof,'No trailingJSON bytes')
def object_pairs(path):
 with ordinary(path).open(encoding='utf-8')as f:
  s=StreamJSON(f)
  yield from s.pairs();s.finish()
def verification_pairs(path):
 """Stream only files map while retaining bounded top-level metadata."""
 with ordinary(path).open(encoding='utf-8')as f:
  s=StreamJSON(f);s.expect('{');first=True;found=False;keys=set()
  while True:
   s.trim()
   if s.buf.startswith('}'):s.buf=s.buf[1:];break
   if not first:s.expect(',')
   key=s.value();need(key not in keys,'Unique top-level receipt key');keys.add(key);s.expect(':')
   if key=='files':
    need(not found,'One physical receipt filesmap');found=True
    yield from s.pairs()
   else:s.value()
   first=False
  need(found,'Complete physical filesmap');s.finish()
class Index:
 def __init__(self,path):
  self.db=sqlite3.connect(path);self.closed=False
  self.db.execute('PRAGMA journal_mode=DELETE');self.db.execute('PRAGMA synchronous=FULL')
  self.db.execute('CREATE TABLE physical(k TEXT PRIMARY KEY,path TEXT NOT NULL,sha TEXT NOT NULL,rawcase INTEGER,bytes INTEGER,size INTEGER,mtime INTEGER,ctime INTEGER,seen INTEGER NOT NULL DEFAULT0)'.replace('DEFAULT0','DEFAULT 0'))
  self.db.execute('CREATE TABLE manifest(k TEXT PRIMARY KEY,rel TEXT NOT NULL,path TEXT NOT NULL,sha TEXT NOT NULL,bytes INTEGER NOT NULL,seen INTEGER NOT NULL DEFAULT0)'.replace('DEFAULT0','DEFAULT 0'))
 def close(self):
  self.db.close();self.closed=True
 def add(self,path,h,duplicate_ok=False):
  p=Path(path);need(p.is_absolute()and p.suffix.lower()not in BAD and HEX.fullmatch(h),'Absolute ordinary declaration')
  p=p.resolve();k=str(p).casefold();row=self.db.execute('SELECT path,sha FROM physical WHERE k=?',(k,)).fetchone()
  if row:need(duplicate_ok and row==(str(p),h),'Unique exact physical declaration');return
  self.db.execute('INSERT INTO physical(k,path,sha)VALUES(?,?,?)',(k,str(p),h))
 def mark(self,p,h,n=None,case=None):
  p,st=authenticate(p,h,n);k=str(p).casefold();row=self.db.execute('SELECT sha,seen FROM physical WHERE k=?',(k,)).fetchone();need(row is not None and row[0]==h,'Physical target belongs to exact declaration')
  need(not row[1],'Physical output occurs exactly once');self.db.execute('UPDATE physical SET seen=1,rawcase=?,bytes=?,size=?,mtime=?,ctime=? WHERE k=?',(case,n,*st,k));return p
 def load_manifest(self,root,path,case):
  self.db.execute('DELETE FROM manifest');count=0;root=Path(root).resolve()
  with contextlib.closing(object_pairs(path))as entries:
   for rel,v in entries:
    relative(rel);need(isinstance(v,dict)and set(v)=={'bytes','sha256'}and isinstance(v['bytes'],int)and not isinstance(v['bytes'],bool)and v['bytes']>=0 and isinstance(v['sha256'],str)and HEX.fullmatch(v['sha256']),'Whole exact manifest row')
    full=root.joinpath(*PurePosixPath(rel).parts).resolve();need(full.is_relative_to(root),'Resolved output path remains in root');k=str(full).casefold();row=self.db.execute('SELECT path,sha,rawcase FROM physical WHERE k=?',(k,)).fetchone();need(row and row[0]==str(full)and row[1]==v['sha256']and row[2]is None,'Manifest physical identity matches raw verification declaration')
    try:self.db.execute('INSERT INTO manifest(k,rel,path,sha,bytes)VALUES(?,?,?,?,?)',(rel.casefold(),rel,str(full),v['sha256'],v['bytes']))
    except sqlite3.IntegrityError:raise Refusal('Duplicate or casefold-colliding manifest name')
    count+=1
  need(count,'Nonempty full sealed manifest');self.db.commit();return count
 def inspect_root(self,root,case,progress):
  root=Path(root).resolve();count=0
  for folder,dirs,files in os.walk(root,followlinks=False):
   for n in dirs+files:
    q=Path(folder)/n;st=q.lstat();need(not q.is_symlink()and not(getattr(st,'st_file_attributes',0)&0x400),'No reparse/symlink ordinary alias')
   for name in files:
    p=Path(folder)/name;rel=p.relative_to(root).as_posix();relative(rel);row=self.db.execute('SELECT rel,path,sha,bytes,seen FROM manifest WHERE k=?',(rel.casefold(),)).fetchone();need(row and row[0]==rel and row[1]==str(p.resolve())and not row[4],'Every actual output occurs in manifest exactly once')
    self.mark(p,row[2],row[3],case);self.db.execute('UPDATE manifest SET seen=1 WHERE k=?',(rel.casefold(),));count+=1
    if count%5000==0:self.db.commit();progress('raw',case,count)
  need(count==self.db.execute('SELECT COUNT(*)FROM manifest').fetchone()[0]and not self.db.execute('SELECT1 FROM manifest WHERE seen=0 LIMIT1'.replace('SELECT1','SELECT 1').replace('LIMIT1','LIMIT 1')).fetchone(),'All-and-only complete ordinary inventory');self.db.commit();return count
 def retry(self,before,after,root,progress):
  relative(before.rstrip('/'));relative(after.rstrip('/'));need(before.endswith('/')and after.endswith('/'),'Whole retry prefix');bc=self.db.execute('SELECT COUNT(*)FROM manifest WHERE substr(rel,1,?)=?',(len(before),before)).fetchone()[0];ac=self.db.execute('SELECT COUNT(*)FROM manifest WHERE substr(rel,1,?)=?',(len(after),after)).fetchone()[0];need(bc and bc==ac,'Whole nonempty retry name inventories');count=0
  cursor=self.db.execute('SELECT rel,path,bytes,seen FROM manifest WHERE substr(rel,1,?)=? ORDER BY k',(len(before),before))
  for rel,path,n,seen in cursor:
   suffix=rel[len(before):];other=after+suffix;row=self.db.execute('SELECT rel,path,bytes,seen FROM manifest WHERE k=?',(other.casefold(),)).fetchone();need(seen and row and row[0]==other and row[2]==n and row[3],'Exact authenticated full retry relative inventory');equal_files(path,row[1]);count+=1
   if count%5000==0:progress('retry',before,count)
  need(count==bc,'All retry files compared');return count
 def final(self,progress):
  count=0
  for path,h,n,seen,size,mtime,ctime in self.db.execute('SELECT path,sha,bytes,seen,size,mtime,ctime FROM physical ORDER BY k'):
   need(seen,'Every declared physical dependency independently authenticated');need(stable(path)==(size,mtime,ctime),'Pinned metadata remained stable at final closure');authenticate(path,h,n);count+=1
   if count%5000==0:progress('final',None,count)
  return count
def main(recipe_path,recipe_sha,name):
 need(re.fullmatch('full-raw-inventory-review-r[1-9][0-9]*',name),'Fresh review namespace');out=R/'reports/m4-138-controls-review'/name;need(not out.exists(),'Immutable review output');out.mkdir();index=None;passed=False;closed=False;counts=collections.Counter();pins={};case_results=[];start=time.monotonic()
 def progress(phase,case,count):print(json.dumps(dict(progress=phase,case=case,files=count,elapsed_seconds=round(time.monotonic()-start,2))),flush=True)
 def pin(p,h=None):
  p=ordinary(p);actual=sha(p);need(h is None or actual==h,'Pinned ordinary identity '+str(p));pins[str(p)]=actual;return p
 try:
  recipe=json.loads(pin(recipe_path,recipe_sha).read_bytes());need(recipe['expected_full_raw_output_files']==10691866 and recipe['expected_full_retry_file_pairs']==3547696 and len(recipe['cases'])==16,'Exact prepared controls inventory domain')
  verification=pin(recipe['verification_report'],recipe['verification_report_expected_sha256']);execution=pin(recipe['execution_report'],recipe['execution_expected_sha256']);need(execution.stat().st_size<32*1024*1024,'Bounded execution metadata');e=json.loads(execution.read_bytes());need(e['passed']and e['all_workers_terminal']and e['actual_workers_launched']==16,'Actual historical workers closed');index=Index(out/'physical-index.sqlite')
  with contextlib.closing(verification_pairs(verification))as entries:
   for n,(path,h)in enumerate(entries,1):
    index.add(path,h)
    if n%50000==0:index.db.commit();progress('declarations',None,n)
  index.db.commit();counts['whole_verification_physical_declarations']=n
  for v in recipe['retained_independent_reviews'].values():
   q=pin(v['path'],v['sha256']);p=json.loads(q.read_bytes());need(p['passed'],'Retained independent semantic/source/resource proof');index.add(q,sha(q),True)
   for path,h in p['files'].items():index.add(path,h,True)
  for p,h in pins.items():index.add(p,h,True)
  index.add(__file__,sha(__file__),True);index.add(sys.executable,sha(sys.executable),True);index.db.commit();seen=set()
  for case_number,c in enumerate(recipe['cases']):
   key=c['level'],c['mode'];need(key not in seen,'Unique level/mode');seen.add(key);runs=[v for v in e['runs']if(v['level'],v['mode'])==key];need(len(runs)==1,'Actual execution case');run=runs[0]
   need(Path(run['capture']).resolve()==Path(c['ordinary_root']).resolve()and run['observed_files']==c['expected_output_files']and run['output_manifest_sha256']==c['manifest_sha256']and run['stage_sha256']==c['stage_sha256']and run['passed'],'Exact closed execution case binding')
   manifest=pin(c['sealed_manifest'],c['manifest_sha256']);stage=pin(c['stage'],c['stage_sha256']);index.add(manifest,sha(manifest),True);index.add(stage,sha(stage),True)
   count=index.load_manifest(c['ordinary_root'],manifest,case_number);need(count==c['expected_output_files'],'Exact full sealed output count');actual=index.inspect_root(c['ordinary_root'],case_number,progress);counts['whole_export_targets_authenticated']+=actual
   root=Path(c['ordinary_root']);component=[q for q in(root/'Widget').glob('root-*/*')if q.name=='same-context-before'];need(len(component)==1,'One exact failed source component private retry domain');b=component[0].relative_to(root).as_posix()+'/';a=component[0].with_name('same-context-after').relative_to(root).as_posix()+'/'
   pairs=0
   for b,a in [('Widget/same-context-before/','Widget/same-context-after/'),(b,a),('retry-before/Registry/','retry-after/Registry/')]:pairs+=index.retry(b,a,root,progress)
   counts['whole_exported_retry_files_equal']+=pairs;counts['same_actual_Context_retry_relations']+=1;case_results.append(dict(level=key[0],mode=key[1],whole_outputs=actual,whole_retry_pairs=pairs))
  need(seen=={(l,m)for l in('O0','O2')for m in range(1,9)}and counts['whole_export_targets_authenticated']==10691866 and counts['whole_exported_retry_files_equal']==3547696,'Entire declared raw/retry domain')
  cursor=index.db.execute('SELECT path,sha FROM physical WHERE seen=0')
  for path,h in cursor:index.mark(path,h);counts['whole_nonraw_dependencies_authenticated']+=1
  index.db.commit();counts['final_integrity_files_rehashed']=index.final(progress)
  for p,h in pins.items():authenticate(p,h)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if index:index.close()
  closed=index is None or index.closed
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Independent full sealed ordinary raw inventory and whole observable private retry closure; retained semantic/resource/source/equivalence proofs bound, no source/worker/archive execution',controls_verification_sha256='88e0a18bc8b32fb70c3fd460c828c44127613662fd4467cf3385ae78b56861cb',counts=dict(counts),cases=case_results,all_bounded_readers_closed=closed,raw_export_readers_closed=closed,raw_exports_all_logical_entries=passed,capture_archives_opened=0,worker_executed=False,source_machine_executed=False,whole_hidden_Runtime_frames_or_permissions_claim=False,whole_current138_positive_semantic_equivalence_claim=False,initializer_credit=0,elapsed_seconds=time.monotonic()-start,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),counts=dict(counts),readers_closed=closed)),flush=True)
if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2],sys.argv[3])
