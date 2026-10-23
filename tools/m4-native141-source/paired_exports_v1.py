"""Bounded raw equality-target exports from the existing canonical reader.

This does not replace or cache canonical capture authentication. The producing
full source/provider gate still reads the original strict archives unchanged.
"""
from pathlib import Path
import hashlib,json,re,struct
def sha(path):
 with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def selected(key):
 if re.fullmatch(r'sequence-\d+/Constructors/.*',key):return True
 if re.fullmatch(r'sequence-\d+/phase-\d+-(?:before|after)-constructor-global5F2000\.bin',key):return True
 if re.fullmatch(r'sequence-\d+/(?:fs-frame-witnesses|fs-record-bytes)\.bin',key):return True
 if re.fullmatch(r'sequence-\d+/Widget/.*',key):return True
 if re.fullmatch(r'sequence-\d+/phase-\d+(?:\.bin|-(?:before|after)-page-\d+\.bin|-after-registry\.bin)',key):return True
 if re.fullmatch(r'sequence-\d+/MFC(?:/.*|-caller-hardware\.bin)',key):return True
 if key in('native-header.bin','selected-table.bin','COMPLETE.txt')or re.fullmatch(r'sequence-\d+/(?:summary\.bin|caller-projection-.*)',key):return True
 if re.match(r'sequence-\d+/(?:selected|grown|cleaned)/',key):
  hit=re.search(r'/registry-checkpoint-\d+-page-(\d+)\.bin$',key)
  return not hit or int(hit[1])==0x20001000
 return False
class Export:
 def __init__(self,directory,branch,transport,pin):
  self.directory=Path(directory)/branch;need(not self.directory.exists(),'Fresh bounded paired export');self.directory.mkdir(parents=True);self.path=self.directory/'payload.bin';self.stream=self.path.open('wb');self.entries={};self.offset=0;self.branch=branch;self.transport=Path(transport);self.pin=pin;self.closed=False
 def write(self,key,data):
  need(not self.closed and key not in self.entries,'Unique current raw logical equality target');need(isinstance(data,bytes),'Whole immutable raw equality target');self.entries[key]=dict(offset=self.offset,bytes=len(data),sha256=hashlib.sha256(data).hexdigest());self.stream.write(data);self.offset+=len(data)
 def copy(self,archive):
  for key in sorted(archive.entries):
   if self.branch=='original'or selected(key):self.write(key,archive.data(key))
 def finish(self):
  need(not self.closed,'One export seal');self.stream.close();self.closed=True;index=self.directory/'index.json';index.write_text(json.dumps(dict(version=1,logical_files=len(self.entries),payload_bytes=self.offset,entries=self.entries),indent=2)+'\n');self.pin(index);self.pin(self.path);return dict(branch=self.branch,transport_path=str(self.transport),transport_sha256=sha(self.transport),index_path=str(index),index_sha256=sha(index),payload_path=str(self.path),payload_sha256=sha(self.path),logical_files=len(self.entries),payload_bytes=self.offset,equality_targets_only=True)
 def close(self):
  if not self.closed:self.stream.close();self.closed=True
class Facade:
 def __init__(self,row,pin):
  self.pin=pin;self.path=pin(row['transport_path'],row['transport_sha256']);index=pin(row['index_path'],row['index_sha256']);self.payload=pin(row['payload_path'],row['payload_sha256']);self.payload_sha256=row['payload_sha256'];value=json.loads(index.read_bytes());need(value['version']==1,'Exact bounded raw export index');self.entries=value['entries'];self.bundles=[];self.value=value
  need(len(self.entries)==value['logical_files']==row['logical_files'],'Complete logical export extent');cursor=0
  for key,v in sorted(self.entries.items(),key=lambda q:q[1]['offset']):
   need(isinstance(key,str)and key and '\\'not in key and not key.startswith('/')and '..'not in key.split('/'),'Normalized relative raw logical name');need(v['offset']==cursor and isinstance(v['bytes'],int)and v['bytes']>=0 and re.fullmatch('[0-9a-f]{64}',v['sha256']),'Exact contiguous extent and individual payload digest');cursor+=v['bytes']
  need(cursor==value['payload_bytes']==row['payload_bytes']==self.payload.stat().st_size,'No missing or trailing export bytes');self.stream=self.payload.open('rb');self.closed=False
 def data(self,key):
  need(not self.closed and key in self.entries,'Required current bounded equality target '+key);v=self.entries[key];self.stream.seek(v['offset']);data=self.stream.read(v['bytes']);need(len(data)==v['bytes']and hashlib.sha256(data).hexdigest()==v['sha256'],'Exact per-access current equality target digest '+key);return data
 def words(self,key,count,kind='I'):
  data=self.data(key);need(len(data)==count*struct.calcsize(kind),'Entire bounded scalar extent');return struct.unpack('<'+str(count)+kind,data)
 def close(self):
  if not self.closed:self.stream.close();self.closed=True;need(sha(self.payload)==self.payload_sha256,'Whole bounded equality target payload stable after consumer closure')
