"""Tiny current equality-target export for the first failed MFC frame join."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-constructor-original'
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=B/'frame-diagnostic-r1'
    if out.exists():raise ValueError('Fresh bounded diagnostic required')
    pins={};reader=None;out.mkdir()
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p)
        if h is not None and h!=v:raise ValueError('Exact current diagnostic input')
        pins[str(p)]=v;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def words(b,o=0,n=1):return struct.unpack_from('<'+str(n)+'I',b,o)
    try:
        e=read(B/'chronological-execution-r3/report.json','cac188db72cb1f5010d04706b52e95afaa4247fab577d6239e726a55bf6751b4')
        if not e['passed']:raise ValueError('Actual current successful writer only')
        chain=read(B/'entry-chain-r1/report.json','80bc3b7041473bd8fb643aa0b5e0839bae1d185659adca2fc802728bcccd18a7')
        source=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('ctor_frame_diagnostic_direct',source);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
        reader=D.DirectSet(Path(e['original_capture']),pin);stem='phase/0/13';prefix='constructor-prerequisites/'+stem
        keys=[stem+'/api-count.bin',stem+'/api-ledger.bin',prefix+'/normal/normal-count.bin',prefix+'/normal/normal-records.bin',prefix+'/occurrences.bin']
        values={k:reader.data(k)for k in keys}
        for k,v in values.items():p=out/Path(k).name;p.write_bytes(v);pin(p)
        blob=values[prefix+'/normal/normal-records.bin'];n=words(values[prefix+'/normal/normal-count.bin'])[0];ledger=values[stem+'/api-ledger.bin'];api_count=words(values[stem+'/api-count.bin'])[0]
        if len(blob)!=n*189108 or len(ledger)!=api_count*104:raise ValueError('Whole current observation schema')
        facts=[];active=None
        for i in range(n):
            raw=blob[i*189108:(i+1)*189108];m=words(raw,0,12);c=words(raw,48,10);frame=raw[628:692]
            if m[3]==0:active=(m,c,frame)
            elif 1<=m[3]<=8:
                if active is None:raise ValueError('Actual balanced source allocation entry')
                am,ac,af=active
                candidates=[(ai,words(ledger,ai*104,26))for ai in range(am[10],m[10])if words(ledger,ai*104,26)[24]==0 and words(ledger,ai*104,26)[10]==c[0]]
                if len(candidates)!=1:raise ValueError('One actual current HeapAlloc')
                ai,api=candidates[0]
                facts.append(dict(entry_index=am[1],return_index=i,source_MFC_requested=words(af,4)[0],actual_HeapAlloc_requested=api[22],actual_HeapAlloc_ESP=api[4],actual_MFC_entry_ESP=ac[4],observed_ESP_delta=api[4]-ac[4],physically_declared_delta=chain['MFC823_entry_to_HeapAlloc_before_delta'],actual_saved_return=api[25],physically_declared_saved_return=chain['HeapAlloc_source_saved_return'],API_index=ai,API_count_entry=am[10],API_count_return=m[10],CPU_entry=list(ac),CPU_return=list(c),source_frame64_entry_hex=af.hex(),source_frame64_return_hex=frame.hex(),API26=list(api)))
                active=None
        if active is not None:raise ValueError('All pairs complete')
    finally:
        if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear();reader=None
    pin(__file__);p=out/'report.json';p.write_text(json.dumps(dict(passed=True,scope='Exact finite current raw scalar diagnostic; observations only, not native inputs or initializer credit',facts=facts,reader_closed=True,writer_rerun=False,source_AFTER_seed=False,files=pins),indent=2)+'\n')
    print(json.dumps(dict(passed=True,reader_closed=True,sha256=sha(p),facts=[{k:v for k,v in f.items()if k not in('CPU_entry','CPU_return','API26','source_frame64_entry_hex','source_frame64_return_hex')}for f in facts])))
if __name__=='__main__':main()
