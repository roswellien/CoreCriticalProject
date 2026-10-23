"""Synthetic/adverse tests only; no project capture/native/source payload inputs."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,sys,tempfile,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-controls-review/full-raw-preflight-r2';assert not out.exists();out.mkdir();tool=R/'tools/m4-138-controls-review/full_raw_review_v2.py';spec=importlib.util.spec_from_file_location('independent_raw',tool);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);cases=[];passed=False
 def check(name,f):f();cases.append(dict(name=name,passed=True))
 def refused(name,f):
  try:f()
  except (m.Refusal,ValueError):cases.append(dict(name=name,refused=True));return
  raise AssertionError('Required adverse refusal '+name)
 try:
  with tempfile.TemporaryDirectory(prefix='synthetic-',dir=out)as d:
   tmp=Path(d);root=tmp/'ordinary';root.mkdir();payload=b'A'*(1024*1024)+b'BCDEFGH';a=root/'before/data.bin';b=root/'after/data.bin'
   for p in(a,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
   check('Whole matching bytepair crosses1MiB boundary',lambda:m.equal_files(a,b))
   b.write_bytes(payload[:-1]+b'X');refused('Late payload difference beyond1MiB boundary',lambda:m.equal_files(a,b));b.write_bytes(payload)
   b.write_bytes(payload+b'X');refused('Unequal wholeEOF/length',lambda:m.equal_files(a,b));b.write_bytes(payload)
   check('Correct fullSHA/length',lambda:m.authenticate(a,sha(a),len(payload)))
   refused('Wrong fullSHA',lambda:m.authenticate(a,'0'*64,len(payload)))
   refused('Wrong exactbytes',lambda:m.authenticate(a,sha(a),len(payload)-1))
   for bad in('../escape.bin','x/../escape.bin','/absolute.bin','C:/drive.bin','x\\bad.bin','x//bad.bin','x/./bad.bin','x:stream'):
    refused('Path escape/alias '+bad,lambda bad=bad:m.relative(bad))
   reader=m.StreamJSON(io.StringIO('{"escape\\\"key":{"bytes":1,"sha256":"'+('a'*64)+'"},"unicodeé":{"bytes":0,"sha256":"'+('b'*64)+'"}}'),chunk=2);values=list(reader.pairs());reader.finish();assert len(values)==2 and values[0][0]=='escape"key';cases.append(dict(name='Streaming escapedUnicode JSON split at2chars',passed=True))
   malformed=m.StreamJSON(io.StringIO('{"x":{"bytes":1,"bytes":2}}'),chunk=3);refused('Duplicate nested object key',lambda:list(malformed.pairs()))
   truncated=m.StreamJSON(io.StringIO('{"x":{"bytes":1}'),chunk=3);refused('Truncated JSON',lambda:list(truncated.pairs()))
   trailing=m.StreamJSON(io.StringIO('{"x":1}true'),chunk=3);list(trailing.pairs());refused('Trailing JSON',trailing.finish)
   verification=tmp/'verification.json';verification.write_text(json.dumps(dict(passed=True,files={str(a.resolve()):sha(a),str(b.resolve()):sha(b)}),indent=2));assert len(list(m.verification_pairs(verification)))==2;cases.append(dict(name='Stream nested giant-map shape without materialization',passed=True))
   manifest=tmp/'manifest.json';manifest.write_text(json.dumps({'before/data.bin':dict(bytes=len(payload),sha256=sha(a)),'after/data.bin':dict(bytes=len(payload),sha256=sha(b))},indent=2))
   with contextlib.closing(m.Index(tmp/'index.sqlite'))as idx:
    for p in(a,b):idx.add(p,sha(p))
    refused('Duplicate physical declaration',lambda:idx.add(a,sha(a)))
    assert idx.load_manifest(root,manifest,0)==2
    assert idx.inspect_root(root,0,lambda *x:None)==2
    assert idx.retry('before/','after/',root,lambda *x:None)==1
    assert idx.final(lambda *x:None)==2;cases.append(dict(name='Exact wholeinventory/privatepair/finalphysical rehash',passed=True))
    b.write_bytes(payload[:-1]+b'X');refused('Final integrity mutation after first authentication',lambda:idx.final(lambda *x:None));b.write_bytes(payload)
   assert idx.closed;cases.append(dict(name='SQLite index closes on context exit',passed=True))
   index_path=tmp/'durable.sqlite';index=m.Index(index_path);pinset={}
   def durable_pin(p):
    assert index.closed,'Close SQLite before any proof content hash'
    p=Path(p).resolve();pinset[str(p)]=sha(p);return p
   for p in(a,b):index.add(p,sha(p))
   index.load_manifest(root,manifest,0);index.inspect_root(root,0,lambda *x:None);final=index.final(lambda *x:None)
   proof=m.seal_index(index,index_path,durable_pin,dict(final_integrity_files_rehashed=final,whole_export_targets_authenticated=2))
   assert index.closed and proof['sqlite_closed_before_hash']and proof['physical_rows']==proof['raw_rows']==2 and proof['sha256']==pinset[str(index_path.resolve())]
   cases.append(dict(name='Durable SQLite closes before hashing/pinning with exactschema/counts',passed=True))
   import sqlite3
   conn=sqlite3.connect(index_path.as_uri()+'?mode=ro',uri=True)
   try:
    actual=list(conn.execute(proof['expansion_query']));assert len(actual)==2 and {Path(x[0])for x in actual}=={a.resolve(),b.resolve()}and all(sha(x[0])==x[1]and Path(x[0]).stat().st_size==x[2]for x in actual)
   finally:conn.close()
   cases.append(dict(name='Readonly durable proof expansion authenticates entire syntheticunion',passed=True))
   with index_path.open('r+b')as f:f.seek(-1,2);old=f.read(1);f.seek(-1,2);f.write(bytes([old[0]^1]))
   refused('Durable inventory mutation after closure',lambda:m.authenticate(index_path,proof['sha256'],proof['bytes']))
   for label,rows,extra in [('missing-target',{'before/data.bin':dict(bytes=len(payload),sha256=sha(a))},False),('extra-actual',{'before/data.bin':dict(bytes=len(payload),sha256=sha(a))},True),('missing-actual',{'before/data.bin':dict(bytes=len(payload),sha256=sha(a)),'missing.bin':dict(bytes=0,sha256=hashlib.sha256(b'').hexdigest())},False)]:
    manifest.write_text(json.dumps(rows));index=m.Index(tmp/(label+'.sqlite'))
    try:
     for rel,v in rows.items():index.add(root/rel,v['sha256'])
     index.load_manifest(root,manifest,0);refused('All-and-only inventory '+label,lambda:index.inspect_root(root,0,lambda *x:None))
    finally:index.close()
    assert index.closed
   collision=tmp/'collision.json';collision.write_text('{"before/data.bin":{"bytes":'+str(len(payload))+',"sha256":"'+sha(a)+'"},"before/data.bin":{"bytes":'+str(len(payload))+',"sha256":"'+sha(a)+'"}}');index=m.Index(tmp/'collision.sqlite')
   try:index.add(a,sha(a));refused('Duplicate streamed manifest row',lambda:index.load_manifest(root,collision,0))
   finally:index.close()
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  p=out/'report.json';p.write_text(json.dumps(dict(passed=passed,scope='Synthetic/adverse preflight only, no actual controls capture or native/source inputs',cases=cases,whole_real_inventory_reviewed=False,archive_reader_opened=False,worker_executed=False,source_machine_executed=False,all_bounded_readers_closed=True,initializer_credit=0,files={str(p.resolve()):sha(p)for p in(tool,Path(__file__),Path(sys.executable))}),indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(p),sha256=sha(p),cases=len(cases))))
if __name__=='__main__':main()
