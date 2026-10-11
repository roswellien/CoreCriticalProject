"""Read-only integration continuity audit; source acceptance remains separate."""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, time, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PINS={}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable input');PINS[str(p)]=v;return p
def own(p,n):
 spec=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def cpu(b):return struct.unpack('<10I',b)
def host(fx,after,env,env_after):
 need(fx[:5]==after[:5] and fx[24:28]==after[24:28] and env==env_after,'Outside-return numerical and full legacy ENV preservation')
 need(all(fx[32+16*i:42+16*i]==after[32+16*i:42+16*i]for i in range(8)),'Outside-return all raw80 slots')
def main(execution,digest,name):
 started=time.perf_counter();out=ROOT/'reports/m4-joint-startup120-root'/name;need(not out.exists(),'Fresh audit');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[]
 try:
  report=json.loads(pin(execution,digest).read_bytes());need(report['passed'] and len(report['levels'])==2,'Complete structural O0/O2 run')
  pin(__file__);D=own(ROOT/'tools/m4-crt-allocation-root/run_v2.py','audit120_direct');old=own(ROOT/'tools/m4-joint-startup27-review/observe.py','audit120_projection');m,_,_,_=old.models()
  for level in report['levels']:
   reader=D.DirectSet(Path(level['capture']),pin)
   try:
    entries=reader.words('selected-table.bin',120);registration=set(reader.words('registration-roots.bin',92));raw=reader.data('extra-pages.bin');need(len(raw)%4==0,'Whole extra-page address words');pages=struct.unpack('<'+str(len(raw)//4)+'I',raw);need(len(set(pages))==len(pages)and 0x5f498000 in pages,'Unique current game/MFC extra pages');category=collections.Counter();category_bytes=collections.Counter();growth=[]
    for logical,bundle in reader.entries.items():
     # CaptureBundle and DirectSet already verify every complete payload. The
     # category metric uses their checked immutable extent rather than hashing
     # all records a third time just to obtain lengths.
     parts=logical.split('/');kind=parts[1]if len(parts)>1 else 'header';kind=kind if kind in('selected','grown','cleaned')else 'selected-phases-and-summary';category[kind]+=1;category_bytes[kind]+=bundle._entries[logical][1]
    del bundle
    for seq in range(6):
     prefix=f'sequence-{seq}/';summary=reader.data(prefix+'summary.bin');host(summary[48:560],summary[560:1072],summary[1072:1100],summary[1100:1128]);counts['selected_host_returns']+=1
     before=bytearray(reader.data(prefix+'caller-projection-before/State.bin'));after=reader.data(prefix+'caller-projection-after/State.bin');m.statecpu(before,cpu(reader.data(prefix+'caller-projection-after/CPU.bin')))
     need(before==after,'Single external CPU-only caller projection');need(reader.data(prefix+'caller-projection-before/FX.bin')==reader.data(prefix+'caller-projection-after/FX.bin'),'External projection preserves complete guest FX');counts['external_cpu_projections']+=1
     previous=None
     for phase,entry in enumerate(entries):
      record=reader.data(prefix+f'phase-{phase}.bin');sb=record[141540:145044];sa=record[145044:148548];actual=cpu(record[36:76]);previous_state=bytearray(previous[145044:148548]if previous else after);source_cpu=list(cpu(previous[76:120]if previous else reader.data(prefix+'caller-projection-after/CPU.bin')));source_cpu[4]-=4;source_cpu[9]=entry
      need(actual==tuple(source_cpu),'Actual scheduler CALL CPU continuity');m.statecpu(previous_state,source_cpu);previous_state=previous_state if entry in registration or entry==0x4c19f0 else m.beforestate(previous_state,source_cpu,entry);need(sb==previous_state,'Complete3504 State continuity '+str((seq,phase,entry,[(i,a,z)for i,(a,z)in enumerate(zip(previous_state,sb))if a!=z])));old.projection(m,record,sb);old.projection(m,record,sa,True);counts['complete_State_and_projection_checks']+=2
      if previous:
       need(previous[71908:141540]==record[2276:71908],'Whole17 fixed pages persist between roots');need(previous[628:1140]==record[120:628] and previous[2192:2220]==record[2164:2192],'Complete guest FX/ENV continuity');counts['whole_fixed_page_carries']+=17
       for page in pages:
        need(reader.data(prefix+f'phase-{phase-1}-after-page-{page}.bin')==reader.data(prefix+f'phase-{phase}-before-page-{page}.bin'),'Whole extra page persists between roots');counts['whole_extra_page_carries']+=1
       need(reader.data(prefix+f'phase-{phase-1}-after-registry.bin')==reader.data(prefix+f'phase-{phase}-before-registry.bin'),'Actual registry owner summary persists between roots');counts['registry_carries']+=1
      previous=record
     need(summary[4632:8136]==previous[145044:148548] and summary[77768:147400]==previous[71908:141540],'Selected summary describes actual final State/pages');counts['whole_selected_summaries']+=1
     host(reader.data(prefix+'growth-cleanup-host-before-FX.bin'),reader.data(prefix+'growth-cleanup-host-after-FX.bin'),reader.data(prefix+'growth-cleanup-host-before-ENV.bin'),reader.data(prefix+'growth-cleanup-host-after-ENV.bin'));counts['growth_cleanup_host_returns']+=1;growth.append(reader.words(prefix+'growth-replay-count.bin',1)[0])
    rows.append(dict(level=level['level'],growth_replays=growth,archive_records_by_stage=dict(category),archive_payload_bytes_by_stage=dict(category_bytes)))
   finally:
    reader.close()
    # Closed transport indexes remain large; release them before loading O2.
    del reader
  for path,h in m.PINS.items():pin(path,h['sha256']if isinstance(h,dict)else h)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  value=dict(passed=passed,scope='Actual native continuity and outside-return host observation only; no source semantic acceptance',counts=dict(counts),levels=rows,elapsed_seconds=time.perf_counter()-started,initializer_credit=False,whole_M4_complete=False,files=PINS);(out/'report.json').write_text(json.dumps(value,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
