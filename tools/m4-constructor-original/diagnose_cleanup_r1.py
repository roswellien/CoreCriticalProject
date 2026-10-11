"""Bounded current cleanup-key evidence; no worker or broad capture reader."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-constructor-original'
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=B/'cleanup-diagnostic-r1'
    if out.exists():raise ValueError('Fresh finite diagnostic required')
    pins={};rows=[]
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p)
        if h is not None and v!=h:raise ValueError('Exact physical current input')
        pins[str(p)]=v;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    e=read(B/'chronological-execution-r3/report.json','cac188db72cb1f5010d04706b52e95afaa4247fab577d6239e726a55bf6751b4')
    if not e['passed']:raise ValueError('Successful current writer only')
    source=pin(B/'chronological-preparation-r10/reference.cpp','699942d8a540ad655cd7a54d1a8abfe0cdf9f10e12cb46d14b5d00bd9bba8b4b').read_text()
    exact='const auto stem="cleanup/"+std::to_string(sequence)+"/constructor-owner-"+std::to_string(v.serial);out.append(stem+"/meta.bin",&v,sizeof(v));'
    if source.count(exact)!=1:raise ValueError('Exact genuine producer key')
    manifest=read(Path(e['original_capture']))
    if len(manifest['parts'])!=1:raise ValueError('Exact bounded single-part diagnostic')
    part=manifest['parts'][0];archive=pin(Path(e['original_capture']).parent/part['bundle'],part['sha256'])
    with archive.open('rb')as f:
        magic,n,h=struct.unpack('<8sQ32s',f.read(48));index_raw=f.read(n)
        if magic!=b'MW34CAP1'or n!=part['index_bytes']or hashlib.sha256(index_raw).digest()!=h or h.hex()!=part['index_sha256']:raise ValueError('Exact retained index')
        index=json.loads(index_raw);entries={v['path']:v for v in index['files']}
        if len(entries)!=part['logical_files']:raise ValueError('Unique complete index')
        position=0
        for v in index['files']:
            if v['offset']!=position:raise ValueError('Contiguous unchanged index')
            position+=v['size']
        if position!=part['payload_bytes']or archive.stat().st_size!=48+n+position:raise ValueError('Exact complete payload geometry')
        def data(k):
            v=entries[k];f.seek(48+n+v['offset']);raw=f.read(v['size'])
            if len(raw)!=v['size']or hashlib.sha256(raw).hexdigest()!=v['sha256']:raise ValueError('Whole finite cleanup evidence')
            return raw
        old=[k for k in entries if k.startswith('constructor-prerequisites/cleanup/')and '/constructor-owner-'in k]
        if old:raise ValueError('Unexpected alternate producer cleanup prefix')
        for k in sorted(k for k in entries if k.startswith('cleanup/')and '/constructor-owner-'in k and k.endswith('/meta.bin')):
            raw=data(k);v=struct.unpack('<12I',raw)
            before=data(k.replace('/meta.bin','/before.bin'));returned=data(k.replace('/meta.bin','/returned.bin'))
            if len(before)!=v[8]or returned!=struct.pack('<I',1):raise ValueError('Whole actual capacity and returned scalar')
            rows.append(dict(logical_key=k,metadata=list(v),before_bytes=len(before),before_sha256=hashlib.sha256(before).hexdigest(),returned_DWORD=1))
    if not rows or {int(v['logical_key'].split('/')[1])for v in rows}!=set(range(6)):raise ValueError('Actual cleanup evidence in all six sequences')
    pin(__file__);out.mkdir();p=out/'report.json';p.write_text(json.dumps(dict(passed=True,scope='Current producer-key and finite raw cleanup evidence only; exhaustive live ownership is the strict validator responsibility',producer_prefix='cleanup/<sequence>/constructor-owner-',wrong_checker_prefix='constructor-prerequisites/cleanup/<sequence>/constructor-owner-',actual_rows=rows,reader_closed=True,writer_executed=False,source_AFTER_seed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,reader_closed=True,sha256=sha(p),cleanup_rows=len(rows))))
if __name__=='__main__':main()
