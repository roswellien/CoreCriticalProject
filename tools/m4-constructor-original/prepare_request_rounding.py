"""Physical CRT mode1 size projection; no execution or capture input seed."""
from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-constructor-original'
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=B/'request-rounding-r1'
    if out.exists():raise ValueError('Fresh physical contract required')
    pins={}
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p)
        if h is not None and v!=h:raise ValueError('Exact physical source '+str(p))
        pins[str(p)]=v;return p
    sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
    pin(R/'tools/analysis/pe.py');image=PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
    rows=[(0x780012c5,'837c2404e0'),(0x78001306,'a104500378'),(0x7800130b,'83f803'),(0x7800130e,'0f844eb90000'),(0x78001314,'83f802'),(0x78001317,'0f857ab90000'),
          (0x7800cc97,'8b4508'),(0x7800cc9a,'85c0'),(0x7800cc9c,'7503'),(0x7800cc9e,'6a01'),(0x7800cca0,'58'),(0x7800cca1,'83c00f'),(0x7800cca4,'24f0'),(0x7800cca6,'50'),(0x7800cca7,'e9cb46ffff'),
          (0x78001377,'6a00'),(0x78001379,'ff3500500378'),(0x7800137f,'ff1594e00278')]
    spans=[]
    for pc,raw in rows:
        data=bytes.fromhex(raw);offset,_=image.rva_range(pc-image.image_base,len(data))
        if image.data[offset:offset+len(data)]!=data:raise ValueError('Exact whole CRT source instruction '+hex(pc))
        spans.append(dict(PC=pc,raw_hex=raw,file_offset=offset,bytes=len(data)))
    if 0x78001317+6+struct.unpack('<i',bytes.fromhex('7ab90000'))[0]!=0x7800cc97 or 0x7800cca7+5+struct.unpack('<i',bytes.fromhex('cb46ffff'))[0]!=0x78001377:raise ValueError('Exact physical normal mode1 and HeapAlloc argument branch')
    for name in('malloc-size-decode.stdout','malloc-worker-hot-decode.stdout','malloc-round-mode1-decode.stdout'):
        pin(R/'reports/m4-crt-allocation-recovery/recovery-r1'/name)
    pin(__file__);out.mkdir();report=dict(passed=True,scope='Source-only finite original CRT mode1 requested-size projection, no reached trace or initializer credit',admitted_heap_mode=1,source_request_max=0xffffffe0,zero_normalization=1,rounding_addend=15,rounding_mask=0xfffffff0,formula='((source_request if source_request else 1)+15)&0xfffffff0',physical_spans=spans,actual_source_requested_and_API_requested_remain_distinct=True,source_AFTER_seed=False,capture_reader_opened=False,writer_executed=False,initializer_credit=0,files=pins)
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),physical_spans=len(spans))))
if __name__=='__main__':main()
