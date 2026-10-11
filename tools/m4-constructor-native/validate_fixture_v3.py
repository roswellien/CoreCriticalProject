"""Strict bounded37 transport, source-witness, actual owner and hardware gate.

This gate does not substitute for literal source evaluation or original pairing.
Only this current native capture is opened, after both admitted writers close.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
R=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def rows(raw,fmt):
 width=struct.calcsize(fmt);need(len(raw)%width==0,'Whole typed record extent');return list(struct.iter_unpack(fmt,raw))
def host(raw):
 need(len(raw)==1632,'Entire measured caller hardware boundary');a=raw[:512];b=raw[1088:1600];need(a[:5]==b[:5]and a[24:28]==b[24:28]and raw[512:540]==raw[1600:1628]and a[160:416]==b[160:416]and all(a[32+16*i:42+16*i]==b[32+16*i:42+16*i]for i in range(8)),'Caller architectural CW/status/tag/MXCSR/raw80/XMM/ENV restoration')
def main(execution,digest,name):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh strict validation');out.mkdir();files={};results=[];closed=True;passed=False;e={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact bounded validation input '+str(p));need(str(p)not in files or files[str(p)]==v,'Current physical identity');files[str(p)]=v;return p
 try:
  e=json.loads(pin(execution,digest).read_bytes());need(e['passed']and e['all_workers_terminal']and e['actual_workers_launched']==2,'Two exact terminal admitted workers');p=json.loads(pin(R/'reports/m4-constructor-native/fixture-preparation-r4/report.json',e['preparation_sha256']).read_bytes());b=json.loads(pin(R/'reports/m4-constructor-native/fixture-build-r8/build.json',e['build_sha256']).read_bytes());need(p['passed']and b['passed'],'Current prepared linked recipe')
  for q,h in e['files'].items():pin(q,h)
  source=json.loads(pin(R/'reports/m4-constructor-source/preparation-r1/source-instructions.json').read_bytes());source={v['pc']:v for v in source};cold=set(v['pc']for v in source.values()if 0x56fea0<=v['pc']<0x56ff00)
  module=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('constructor_strict_direct',module);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds);pin(__file__);pin(sys.executable)
  cases=[(0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7)];roots=[0x4103f0,0x410440,0x459b40];order=p['selected_order'];expectedcalls=[(roots[0],0x58af12,0x5abd26,12),(roots[0],0x58af6a,0x5abd26,4),(roots[0],0x58af9a,0x5abd1a,0),(roots[1],0x58af12,0x5abd26,12),(roots[1],0x58af6a,0x5abd26,4),(roots[1],0x58af9a,0x5abd1a,0),(roots[2],0x58f2a2,0x5abd26,12),(roots[2],0x45b80e,0x5abd26,12)]
  for level in('O0','O2'):
   data=ds.DirectSet(Path(e['runs'][level]['capture']),pin);closed=False
   try:
    need(data.words('native-header.bin',6)==(1,6,37,222,17,159716)and data.words('sequences-header.bin',4)==(1,6,147400,17),'Unchanged full machine ABIs/current schedule');need(data.words('selected-table.bin',37)==tuple(v['entry']for v in order),'Exact original measured37 ordering');extra=data.words('extra-pages.bin',29)
    for seq,(repeat,cw,top)in enumerate(cases):
     prefix=f'sequence-{seq}/';summary=data.data(prefix+'summary.bin');need(len(summary)==147400 and struct.unpack_from('<12I',summary)==(seq,repeat,cw,top,1,37,0,0,0,0,0,0),'Whole current persistent source success');host(data.data(prefix+'MFC-caller-hardware.bin'))
     for phase,row in enumerate(order):
      raw=data.data(prefix+f'phase-{phase}.bin');need(len(raw)==159716,'Whole fixed Native159716');tags=struct.unpack_from('<9I',raw);need(tags[:7]==(seq,repeat,phase,row['slot'],row['entry'],cw,top)and tags[7]==0,'Exact current root/CW/TOP tags');need(struct.unpack_from('<2I',raw,148580)==(1,0),'Actual complete State seeding and no source domain error');before=struct.unpack_from('<10I',raw,36);after=struct.unpack_from('<10I',raw,76);need(before[4]==0x20001800 and before[9]==row['entry']and after[4]==0x20001804 and after[9]==0x410a80,'Literal current root CALL/RET machine frames')
      for side in('before','after'):
       for address in extra:need(len(data.data(prefix+f'phase-{phase}-{side}-page-{address}.bin'))==4096,'Complete external page endpoint')
       need(len(data.data(prefix+f'phase-{phase}-{side}-constructor-global5F2000.bin'))==4096,'Whole carried constructor PE global page')
     final=prefix+f'Constructors/root-{roots[-1]}/after/';access=rows(data.data(final+'accesses.bin'),'<IIQII');calls=rows(data.data(final+'calls.bin'),'<12I');getters=rows(data.data(final+'getters.bin'),'<12I');FS=rows(data.data(final+'FS-events.bin'),'<12I')
     need([(v[0],v[1],v[2],v[5])for v in calls]==expectedcalls,'Exactly six actual MFC allocations/two genuine NULL825 source calls');need(all(v[4]==v[1]+5 and v[3]>=0x20001000 and v[3]+8<=0x20002000 for v in calls),'Full direct source CALL frames/returns')
     for v in access:need(v[0]in source and v[0]not in cold and v[3]in(1,2,4)and v[4]in(0,1),'Only current physical admitted literal source operands')
     need(len(getters)==2 and all(v[0]==roots[1]and v[1]==0x58b183 and v[4:8]==(0x604008,0x5bcc68,0x5bcc80,0x40a850)and v[10]>0 and v[11]==v[9]+1 for v in getters),'Two exact current published non-sentinel readonly-vptr getters')
     need(sum(v[5]==1 for v in FS)==sum(v[5]==2 for v in FS)>0 and FS[-1][6]==0,'All actual normal source FS installations/restorations balanced')
     for i,root in enumerate(roots):
      stem=prefix+f'Constructors/root-{root}/after/';status=data.words(stem+'status.bin',8);need(status[0]==1 and status[2]==root and status[3]==0x20001800 and status[4:7]==(0,0,i+1),'Complete serial constructor status/own real root frame');need(len(data.data(stem+'State.bin'))==3504 and len(data.data(stem+'CPU.bin'))==40 and len(data.data(stem+'FX.bin'))==512 and data.data(stem+'frames.bin')==b''and data.data(stem+'FS-frames.bin')==b'','Whole current root source machine and empty frame stacks');host(data.data(prefix+f'Constructors/root-{root}/caller-hardware.bin'))
     mirror=rows(data.data(prefix+'selected/constructor-source-mirror-accesses.bin'),'<12Q');writes=[v for v in access if v[4]];privatewrites=[v for v in mirror if v[5]];need([(v[0],v[1],v[3],v[2])for v in writes]==[(v[1],v[2],v[3],v[4])for v in privatewrites],'Every complete literal store joins private typed preimage/mirror witness in exact order')
     start=data.words(prefix+'caller-projection-before/registry.bin',32,'Q');selected_summary=data.words(prefix+'selected/registry-summary.bin',32,'Q');need(selected_summary[9]==start[9]+25,'Exactly25 current source registrations from carried producer BEFORE');projection=rows(data.data(prefix+'selected/locale-research-projections.bin'),'<8I');new_registrations=[v for v in projection if v[0]==9];need(new_registrations==[(9,root,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,0x20001800-24,0x5ac124)for root in roots],'Three exact committed source onexit services and affine real frames');selected=rows(data.data(prefix+'selected/locale-allocations.bin'),'<16Q');cleaned=rows(data.data(prefix+'cleaned/locale-allocations.bin'),'<16Q');byguest={v[1]:v for v in selected};new=[]
     for v in calls:
      if v[2]!=0x5abd26:continue
      a=byguest.get(v[6]);need(a is not None and a[2]==v[5]and a[3]==16 and a[4]>=16 and a[6]==4 and a[8]and a[9]and not a[10]and not a[11],'Real current MFC generation/request/rounded source extent');generation=a[5];initial=data.data(prefix+f'selected/locale-allocation-{generation}-initial.bin');expected=data.data(prefix+f'selected/locale-allocation-{generation}-expected.bin');actual=data.data(prefix+f'selected/locale-allocation-{generation}-owned-page.bin');need(len(initial)==16 and len(expected)==a[4]and actual==expected and expected[a[2]:16]==initial[a[2]:16],'Complete source native extent/mapped mirror and untouched requested tail');new.append(a)
     need(len(new)==6 and len({v[5]for v in new})==6,'Six distinct measured current allocation generations');cleanup={v[5]:v for v in cleaned}
     for a in new:v=cleanup.get(a[5]);need(v is not None and v[1:7]==a[1:7]and not v[8]and v[10]and not v[11],'Actual genuine source MFC825 cleanup of same entire owner generation')
     state=data.words(prefix+'cleaned/registry-summary.bin',32,'Q');need(state[1]and not state[2]and not state[3]and state[4]and state[10:12]==(0,0)and not state[15],'All current Session heap/CS owners genuinely released');need(data.data(prefix+'growth-replay-count.bin')==bytes(4),'No replay or growth admitted in measured37 chronology')
     results.append(dict(level=level,sequence=seq,phases=37,new_allocator_calls=6,genuine_NULL_calls=2,getter_calls=2,whole_new_owner_cleanup=6,source_operands=len(access),private_mirror_records=len(mirror),literal_stores=len(writes),FS_events=len(FS),current_original_pair_pending=True))
    need(data.data('COMPLETE.txt')==b'Six measured37-root sequences and actual owned cleanup complete; fullM4 incomplete\n','Exact completion marker')
   finally:data.close();del data;closed=True
  need(len(results)==12,'All actual current two-level six-domain cases');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for q,h in files.items():need(sha(q)==h,'Input/output conservation after strict reader')
  d=dict(passed=passed,scope='Current constructor37 strict observed transport/source-frame/private owner/normal cleanup and architectural hostFP gate; independent literal source evaluator/original pairing/fault controls remain pending',execution_path=str(execution),execution_sha256=digest,build_sha256=e.get('build_sha256'),preparation_sha256=e.get('preparation_sha256'),cases=results,reader_closed=closed,initializer_credit=0,full_144_chronology_admitted=False,source_AFTER_seed=False,whole_literal_source_comparison_pending=True,files=files);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,reader_closed=closed,sha256=sha(q))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
