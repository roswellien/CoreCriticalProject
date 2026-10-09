"""Measure exact retained payload repetition; never rewrite accepted captures."""
from pathlib import Path
import hashlib,json,struct,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-capture-sharing-evaluation'/name;out.mkdir(parents=True,exist_ok=False)
 accepted=ROOT/'reports/m4-joint-startup71-root/acceptance-r1/report.json'
 assert sha(accepted)=='64c010e01930d4f84d7df9cb8cd932669ce25b6f3f1dc21989f197282025fdfc'
 parent=json.loads(accepted.read_bytes());assert parent['passed'];files={str(accepted):sha(accepted),str(Path(__file__).resolve()):sha(__file__)};rows=[];started=time.perf_counter()
 for level in('O0','O2'):
  manifest=ROOT/'reports/m4-joint-startup71-root/execution-r1'/level/'transport.json';m=json.loads(manifest.read_bytes());assert sha(manifest)==parent['files'][str(manifest)];files[str(manifest)]=sha(manifest)
  identities={};names=set();payload=0;indexes=0;count=0
  for part in m['parts']:
   p=manifest.parent/part['bundle'];assert sha(p)==part['sha256']==parent['files'][str(p)];files[str(p)]=part['sha256']
   with p.open('rb')as stream:
    magic,n,digest=struct.unpack('<8sQ32s',stream.read(48));assert magic==b'MW34CAP1'and 0<n<=64*1024*1024
    raw=stream.read(n);assert hashlib.sha256(raw).digest()==digest and digest.hex()==part['index_sha256'];index=json.loads(raw)
   offset=0;indexes+=n;assert index['format']=='mw34.capture.v1'
   for item in index['files']:
    assert item['offset']==offset and item['path'].casefold()not in names
    names.add(item['path'].casefold());key=(item['sha256'],item['size']);identities[key]=identities.get(key,0)+1;offset+=item['size'];count+=1
   assert offset==part['payload_bytes']==index['total_bytes'];payload+=offset
  assert count==m['logical_files']and payload==m['payload_bytes']
  unique=sum(size for digest,size in identities);repeated=payload-unique
  rows.append(dict(level=level,logical_records=count,payload_bytes=payload,index_bytes=indexes,distinct_whole_payload_identities=len(identities),unique_payload_bytes=unique,repeated_payload_bytes=repeated,prospective_payload_reduction_fraction=repeated/payload))
 report=dict(passed=True,scope='Offline quantitative repetition analysis of accepted full-record SHA/size identities; no new transport, capture, execution or initializer credit',levels=rows,accepted_captures_modified=False,current_strict_reader_accepts_shared_offsets=False,new_format_reader_writer_validation_required=True,decision='Keep canonical strict transport for the current MFC semantic gate. Validate an additive shared-record format and all reader consumers separately before adoption; retain complete logical observations and fault records.',elapsed_seconds=time.perf_counter()-started,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=sha(out/'report.json'),levels=rows)),flush=True)
if __name__=='__main__':main(sys.argv[1])
