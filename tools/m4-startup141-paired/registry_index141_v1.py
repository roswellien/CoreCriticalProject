"""Pure bounded original141 registry selector over an injected JSON stream."""
from pathlib import PurePosixPath
import hashlib,re

def selected(name):
 if name in('header.bin','COMPLETE.txt'):return True
 if re.fullmatch(r'cleanup/[0-5]/registry\.bin',name):return True
 hit=re.fullmatch(r'phase/([0-5])/(\d+)(\.bin|/api-ledger\.bin|/api-initial/\d+/(bytes|size)\.bin)',name)
 return hit is not None and int(hit[2])<141

def scan(stream,StreamJSON,logical_files,payload_bytes):
 s=StreamJSON(stream);s.expect('{');header={};entries={};count=0;cursor=0;previous=None
 while True:
  key=s.value();assert type(key)is str and key not in header;s.expect(':')
  if key=='entries':
   header[key]=True
   for name,item in s.pairs():
    assert type(name)is str and name and not name.startswith('/')and ':'not in name and '\\'not in name and '..'not in name.split('/')and PurePosixPath(name).as_posix()==name
    assert previous is None or previous<name,'Exact sorted original export producer names; duplicate keys rejected'
    previous=name
    assert type(item)is dict and set(item)=={'offset','bytes','sha256'}
    assert type(item['offset'])is int and type(item['bytes'])is int and item['offset']==cursor and item['bytes']>=0 and re.fullmatch('[0-9a-f]{64}',item['sha256'])
    cursor+=item['bytes'];count+=1;assert count<=logical_files
    if selected(name):
     assert len(entries)<8192 and name not in entries;entries[name]=item
  else:header[key]=s.value()
  s.trim()
  if s.buf.startswith('}'):s.expect('}');break
  s.expect(',')
 s.finish();assert set(header)=={'version','logical_files','payload_bytes','entries'}
 assert header['version']==1 and type(header['logical_files'])is int and type(header['payload_bytes'])is int
 assert header['logical_files']==count==logical_files and header['payload_bytes']==cursor==payload_bytes
 for seq in range(6):
  assert f'cleanup/{seq}/registry.bin'in entries
  for phase in range(141):assert f'phase/{seq}/{phase}.bin'in entries and f'phase/{seq}/{phase}/api-ledger.bin'in entries
 assert 'header.bin'in entries and 'COMPLETE.txt'in entries
 return entries

class Reader:
 def __init__(self,entries,payload):self.entries=entries;self.payload=payload;self.reads={};self.closed=False
 def data(self,key):
  assert not self.closed and key in self.entries;row=self.entries[key]
  self.payload.seek(row['offset']);raw=self.payload.read(row['bytes']);assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
  self.reads[key]=dict(row);return raw
 def words(self,key,n):
  import struct
  return struct.unpack('<'+'I'*n,self.data(key))
 def close(self):
  if not self.closed:self.payload.close();self.closed=True
