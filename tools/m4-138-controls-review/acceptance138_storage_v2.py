"""Retained whole-byte union plus exact per-report disk-backed lineage scope."""
from pathlib import Path
import sqlite3
import acceptance138_storage as base
from acceptance138_storage import Union,sha,load,normalized,digest,unique_object
class ScopedFiles:
 def __init__(self,index,scope):self.index=index;self.scope=scope
 def items(self):yield from self.index.db.execute('SELECT path,sha FROM edges WHERE scope=? ORDER BY path',(self.scope,))
 def get(self,path,default=None):
  row=self.index.db.execute('SELECT sha FROM edges WHERE scope=? AND path=?',(self.scope,normalized(str(Path(path).resolve())))).fetchone();return default if row is None else row[0]
class ScopeIndex:
 def __init__(self,path):
  self.path=Path(path).resolve();assert not self.path.exists();self.db=sqlite3.connect(self.path);self.db.execute('CREATE TABLE edges(scope TEXT NOT NULL,path TEXT NOT NULL,sha TEXT NOT NULL,PRIMARY KEY(scope,path)) WITHOUT ROWID');self.closed=False
 def add(self,scope,path,h):
  path=normalized(str(Path(path).resolve()));h=digest(h);old=self.db.execute('SELECT sha FROM edges WHERE scope=? AND path=?',(scope,path)).fetchone()
  if old is not None and old!=(h,):raise ValueError('Conflicting exact per-report physical edge')
  if old is None:self.db.execute('INSERT INTO edges VALUES (?,?,?)',(scope,path,h))
 def close(self):
  if not self.closed:self.db.commit();self.db.close();self.closed=True
def read_report(path,register,scopes=None):
 if scopes is None:return base.read_report(path,register)
 scope=normalized(str(Path(path).resolve()))
 def joined(p,h):register(p,h);scopes.add(scope,p,h)
 report=base.read_report(path,joined);report['files']=ScopedFiles(scopes,scope);return report
