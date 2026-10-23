"""Disk-backed conflict-free complete acceptance union; no metadata shortcuts."""
from pathlib import Path
import hashlib,importlib.util,json,sqlite3,sys,tempfile,time
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import normalized,digest,unique_object
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Union:
 def __init__(self,path):
  self.path=Path(path).resolve();assert not self.path.exists();self.db=sqlite3.connect(self.path)
  self.db.execute('CREATE TABLE dependencies (path TEXT PRIMARY KEY, sha TEXT NOT NULL, measured INTEGER NOT NULL DEFAULT 0) WITHOUT ROWID');self.closed=False
 def __setitem__(self,path,h):
  path=normalized(str(Path(path).resolve()));h=digest(h);old=self.db.execute('SELECT sha FROM dependencies WHERE path=?',(path,)).fetchone()
  if old is not None and old!=(h,):raise ValueError('Conflict-free complete physical dependency '+path)
  if old is None:self.db.execute('INSERT INTO dependencies(path,sha) VALUES (?,?)',(path,h))
 def __contains__(self,path):return self.get(path) is not None
 def get(self,path,default=None):
  row=self.db.execute('SELECT sha FROM dependencies WHERE path=?',(normalized(str(Path(path).resolve())),)).fetchone();return default if row is None else row[0]
 def __getitem__(self,path):
  value=self.get(path)
  if value is None:raise KeyError(path)
  return value
 def __len__(self):return self.db.execute('SELECT COUNT(*) FROM dependencies').fetchone()[0]
 def items(self):yield from self.db.execute('SELECT path,sha FROM dependencies ORDER BY path')
 def commit(self):self.db.commit()
 def verify(self,progress=None):
  self.db.commit();start=time.monotonic();count=0
  for p,h in self.items():
   before=Path(p).stat();actual=sha(p);after=Path(p).stat()
   if actual!=h or (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):raise ValueError('Whole stable physical dependency '+p)
   self.db.execute('UPDATE dependencies SET measured=1 WHERE path=?',(p,));count+=1
   if progress and count%5000==0:progress(count)
  self.db.commit();assert count==len(self) and self.db.execute('SELECT COUNT(*) FROM dependencies WHERE measured<>1').fetchone()[0]==0
  return dict(passed=True,unique_physical_dependencies=count,whole_dependency_rows_measured=count,verify_seconds=time.monotonic()-start,metadata_only_cache_used=False)
 def close(self):
  if not self.closed:self.db.commit();self.db.close();self.closed=True
 def seal(self):
  count=len(self);self.close();return dict(path=str(self.path),sha256=sha(self.path),bytes=self.path.stat().st_size,sqlite_closed_before_hash=True,physical_rows=count,expansion_query='SELECT path,sha,measured FROM dependencies ORDER BY path',schema='CREATE TABLE dependencies (path TEXT PRIMARY KEY, sha TEXT NOT NULL, measured INTEGER NOT NULL DEFAULT 0) WITHOUT ROWID',acceptance_requires_inventory_expansion=True,every_row_whole_byte_rehashed=True)
def read_report(path,register):
 """Consume giant .files one entry at a time; retain bounded top-level values."""
 raw=load('acceptance138_stream',R/'tools/m4-138-controls-review/full_raw_review_v2.py');result={};seen=set()
 with Path(path).open('r',encoding='utf-8-sig')as f:
  s=raw.StreamJSON(f);s.expect('{');first=True
  while True:
   s.trim()
   if s.buf.startswith('}'):s.buf=s.buf[1:];break
   if not first:s.expect(',')
   key=s.value();raw.need(isinstance(key,str)and key not in seen,'Unique receipt top-level key');seen.add(key);s.expect(':');first=False
   if key=='files':
    # Literal duplicate map keys are refused without a ten-million-key set.
    with tempfile.TemporaryDirectory(prefix='mw34-acceptance-map-')as folder:
     keys=sqlite3.connect(str(Path(folder)/'keys.sqlite'))
     try:
      keys.execute('CREATE TABLE keys(k TEXT PRIMARY KEY) WITHOUT ROWID')
      for p,h in s.pairs():
       try:keys.execute('INSERT INTO keys VALUES (?)',(p,))
       except sqlite3.IntegrityError:raise ValueError('Duplicate physical receipt map key '+p)
       register(p,h)
     finally:keys.close()
    result[key]={}
   else:result[key]=s.value()
  s.finish()
 return result
