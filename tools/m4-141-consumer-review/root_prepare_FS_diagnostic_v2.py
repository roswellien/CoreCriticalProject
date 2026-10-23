from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-141-consumer-review/root_extract_FS_v1.py';s=p.read_text()
s=s.replace('root-FS-diagnostic-r1','root-FS-diagnostic-r2').replace("'sequence-0/fs-frame-witnesses.bin','sequence-0/fs-record-bytes.bin'","'sequence-0/cleaned/fs-frame-witnesses.bin','sequence-0/cleaned/fs-record-bytes.bin'")
old=" for part in m['parts']:\n  p=manifest.parent/part['bundle'];assert f['files'][str(p.resolve())]==part['sha256']\n"
new=""" candidates=[];index_checks=[]
 for part in m['parts']:
  p=manifest.parent/part['bundle']
  # Navigation uses the independently SHA-bound index in the already pinned
  # manifest. Selected payloads still use the unchanged strict whole reader.
  with p.open('rb')as stream:
   magic,index_bytes,index_digest=struct.unpack('<8sQ32s',stream.read(48))
   assert magic==b'MW34CAP1'and index_bytes==part['index_bytes']and 0<index_bytes<=64*1024*1024
   raw=stream.read(index_bytes)
  assert hashlib.sha256(raw).hexdigest()==index_digest.hex()==part['index_sha256']
  idx=json.loads(raw);assert idx['format']=='mw34.capture.v1'
  names={v['path']for v in idx['files']}
  index_checks.append(dict(bundle=str(p),index_sha256=index_digest.hex(),index_bytes=index_bytes))
  if wanted.intersection(names):candidates.append(part)
 for part in candidates:
  p=manifest.parent/part['bundle'];assert f['files'][str(p.resolve())]==part['sha256']
"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('logical_outputs=found,elapsed_seconds=',"logical_outputs=found,index_navigation=index_checks if 'index_checks'in globals()else [],elapsed_seconds=")
q=p.with_name('root_extract_FS_v2.py');assert not q.exists();q.write_text(s)
