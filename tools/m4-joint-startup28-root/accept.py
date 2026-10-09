"""Coordinator acceptance of literal connected28 and current compiled controls."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup28-root';PINS={};FACTS=[]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from stages import verify_stage
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000)
FRAME,OBJECT,OUT,IAT=0x20001800,0x608f88,0x608fa0,0x5bb6dc
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(b,s):
 if not b:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Input remained immutable');PINS[str(p)]=v;return p
def receipt(p,h):
 p=pin(ROOT/p,h);r=json.loads(p.read_bytes());need(r['passed'],'Passed receipt '+str(p));pp=p.parent/'pins.json'
 if pp.exists():
  for a,v in json.loads(pin(pp).read_bytes())['files'].items():pin(a,v)
 for a,v in r.get('files',{}).items():pin(a,v)
 FACTS.append(dict(receipt=str(p),sha256=h));return r
def words(b,off,n):return struct.unpack_from('<'+str(n)+'I',b,off)
def mo(a):return PAGES.index(a&~4095)*4096+(a&4095)
def hardware(b):
 # Packed Sample offsets after tags and two full State/FX/CPU views.
 x,y=b[8208:8720],b[8720:9232];e,f=b[9232:9260],b[9260:9288]
 need(x[:5]==y[:5]and x[24:28]==y[24:28]and e==f,'Outside-return CW/SW/FTW/MXCSR/fullENV28')
 need(all(x[32+i*16:42+i*16]==y[32+i*16:42+i*16]for i in range(8)),'Outside-return raw80 slots')
 need(x[256:416]==y[256:416],'Native nonvolatile XMM6..15')
 need(x[4]!=0 and int.from_bytes(x[24:28],'little')==0x5fa5,'Actual rich nonempty stack/sticky SIMD seed')
 need(x[256:416]==bytes((i*73+19)&255 for i in range(256,416)),'Actual diverse native SIMD seed')
def expected_events(cpu,memory):
 out=[]
 for pc,a,v in((0x482cc0,FRAME-4,cpu[3]),(0x482cc3,FRAME-8,cpu[6]),(0x482cc4,FRAME-12,cpu[7]),(0x482cc8,FRAME-16,0),(0x482cd6,FRAME-20,OUT),(0x482cd7,FRAME-24,0),(0x482cd9,FRAME-28,48)):out.append((pc,a,v,4,1))
 for i in range(6):v=words(memory,mo(0x5e6000+4*i),1)[0];out.extend(((0x482cdb,0x5e6000+4*i,v,4,0),(0x482cdb,OBJECT+4*i,v,4,1)))
 out.extend(((0x482cdd,IAT,0x1df20c,4,0),(0x482cdd,FRAME-32,0x482ce3,4,1),(0x482ce3,FRAME-12,cpu[7],4,0),(0x482ce6,FRAME-8,cpu[6],4,0),(0x482ce7,FRAME-4,cpu[3],4,0),(0x482ce8,FRAME,0x410a80,4,0)))
 return out
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh acceptance');out.mkdir(parents=True);passed=False;start=time.perf_counter();control_rows=[];checks=0
 try:
  parent=receipt('reports/m4-joint-startup27/root-acceptance-r1/report.json','ad1b2decb9d32d354120ae4ae53f4ebfd5db65bbec287cc9a8eb55f981b590a9');need(parent['connected_roots']==27,'Accepted parent count')
  lift=receipt('reports/m4-spi-literal/lifts-r2/report.json','c21820082d9720dbf65aa5c68b73273f3a98c51b689ef42a8305381f2b274682')
  native=receipt('reports/m4-joint-startup28-root/execution-r1/report.json','e7d301390898f62f577da18b4b4babd39392b66a10beeab0de80d75c66292166')
  original=receipt('reports/m4-joint-startup28-original/execution-r1/report.json','323cf25a2922b0a69c6a250c3f729fba8f531a51e202497465ad3c7d4fc9e083')
  model=receipt('reports/m4-joint-startup28-source-review/observation-r3/report.json','e9bc3a6d7b6c568c1f6211388d10c0ff4d4815082221f2048cb6778e3c43588c')
  live=receipt('reports/m4-joint-startup28-source-review/liveness-r2/report.json','634bedb6577c4fef0f086b6a8936cb4508bbb662edb95b9f46bb9b06f110b8f4')
  controls=receipt('reports/m4-joint-startup28-root/controls-execution-r3/report.json','1bd24886134b6ee774c5c542d2ad8778eb1685b4a6595249d0614039a3c93d9a')
  need(model['counts']==dict(native_phases=336,source_events=4764,whole_State_checks=672,original_phases=168,connected_sequences=6)and model['new_SPI_corruption_rejections']==216,'Independent changed corpus extent')
  need(len(live['suffix'])==13 and live['first_metadata_replacement_PC']==0x4adb60 and not live['whole_program'],'Bounded post-SPI volatility liveness')
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes()
  for s in lift['source_spans']:need(hashlib.sha256(game[s['file_offset']:s['file_offset']+s['size']]).hexdigest()==s['sha256'],'Literal original span')
  need(sum(s['size']for s in lift['source_spans'])==56 and lift['graph']['instruction_count']==22 and not lift['graph']['unresolved_controls'],'Complete literal source closure')
  for body in lift['source_bodies'].values():
   for row in body['objects'].values():need(pin(row['path'],row['sha256']).read_bytes()[:2]==b'\x64\x86','Physical AMD64 COFF')
  dsfile=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('strict_root_accept28',dsfile);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds)
  for r in(native,controls):
   for row in r['levels']:verify_stage(Path(row['stage']).parent,row['stage_sha256'])
  original_stage=ROOT/'reports/m4-joint-startup28-original/execution-r1/run/stage.json';verify_stage(original_stage.parent,PINS[str(original_stage.resolve())])
  expected_faults={1:(0x482cf0,IAT,0,3),2:(0x482cf0,IAT,0,3),3:(0x482cf0,0,0,1),4:(0x482cf0,0,0,1),5:(0x482cdb,OBJECT,8,3),6:(0x482cc3,FRAME-8,1,3),7:(IAT,FRAME-20,21,3),8:(IAT,OUT,21,3),9:(IAT,OUT,21,3),10:(0x12345678,0,25,3),11:(0x482ce8,0,25,3),12:(0x410a80,0,0,1),13:(0x482cdb,0x5e6000,7,3),14:(0x482cc0,0,1,3),15:(IAT,0,21,3),16:(0x482cdb,OBJECT+4,10,3)}
  for row in controls['levels']:
   reader=ds.DirectSet(row['capture'],pin)
   try:
    need(reader.words('header.bin',6)==(1,17,34,149172,17,159716),'Exact current compiled control schedule')
    count=reader.words('counts.bin',3);need(count[1:]==(17,34),'Actual independently compiled case count');checks+=count[0]
    for k in range(17):
     a=reader.data(f'case-{k}/first.bin');b=reader.data(f'case-{k}/retry.bin');at=words(a,0,24);bt=words(b,0,24);need(len(a)==len(b)==149172,'Exact outside-return sample');hardware(a);hardware(b)
     need(at[22]==bt[22]==0x4d573328,'LastError restoration including throwing controls')
     need(at[:3]==(k,0,int(k==0))and bt[:3]==(k,1,0),'Actual initial result and refused retry')
     need(at[3]==at[23]==bt[3]==bt[23]==(28 if k==0 else 15 if k==12 else 14),'Completed prefix retained without later roots')
     need(at[7:9]==bt[7:9]and (k==0 or at[9:14]==bt[9:14]),'First fault and dispatcher/source extents unchanged on retry')
     need(b[96:4152]==b[4152:8208]and b[9288:78920]==b[78920:148552]and bt[17]==bt[18],'Refused retry retains whole State/FX/CPU and present pages')
     need(at[14]==int(k==0 or 9<=k<=12 or k==15)and at[15]==int(k in(0,12)),'Actual API call/root return distinguished')
     if k:need(at[10:14]==expected_faults[k]and at[4]==1 and at[5]==int(k!=12)and at[16]==1,'Exact witnessed first-fault site/address/step/poison')
     prefix=reader.data(f'case-{k}/prefix-13.bin');cpu=words(prefix,76,10);memory=bytearray(prefix[71908:141540]);goal=expected_events(cpu,memory)
     events_raw=reader.data(f'case-{k}/events.bin');events=[words(events_raw,i,5)for i in range(0,len(events_raw),20)];need(len(events)==at[7],'Actual event prefix length')
     if k==10:goal[-1]=(0x482ce8,FRAME,0x12345678,4,0)
     need(events==goal[:len(events)],'Independent source-derived ordered access prefix')
     if k==1:memory[mo(0x482cf0)]^=1
     if k==2:struct.pack_into('<I',memory,mo(IAT),0x1df20d)
     for pc,address,value,width,write in events:
      if write:struct.pack_into('<I',memory,mo(address),value)
     if k==10:struct.pack_into('<I',memory,mo(FRAME),0x12345678)
     if k==7:struct.pack_into('<I',memory,mo(FRAME-20),0x12345678)
     transport_raw=reader.data(f'case-{k}/transports.bin');transport=[words(transport_raw,i,5)for i in range(0,len(transport_raw),20)]
     for pc,address,value,width,write in transport:
      need(pc==0x482cdd and width==4,'Checked API transports distinct from source')
      if write:struct.pack_into('<I',memory,mo(address),value)
      else:need(words(memory,mo(address),1)[0]==value,'Actual checked transport reads current source state')
     after=a[78920:148552]
     for page in range(17):
      if at[18]>>page&1:need(after[page*4096:(page+1)*4096]==memory[page*4096:(page+1)*4096],'Whole present page from committed literal/transport prefix')
     witness=reader.words(f'case-{k}/witness.bin',16,'Q')
     if k in(9,15):need(witness[0]==1 and witness[11:]==(FRAME-32,0x482ce3,16,0,0),'Actual API then checked refusal before output/return commitment')
     if k==16:need(len(events)==10 and events[8][4]==1 and words(after,mo(OBJECT),1)[0]==goal[8][2],'One source object DWORD committed before later write refusal')
     control_rows.append(dict(level=row['level'],case=k,completed=at[3],source_accesses=at[7],actual_calls=at[8],first_fault=list(at[9:14]),api_called=bool(at[14]),root_returned=bool(at[15])))
   finally:reader.close()
  pin(__file__);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Connected selected initializer research sequence, preserving accepted27 numerical scope; newly literal SPI service initializer accepted',connected_roots=28 if passed else 27,initializer_inventory_total=144,remaining_initializers=116 if passed else 117,new_root='0x482CF0',new_table_slot='0x5E0110',source_instructions=22,unique_original_bytes=56,new_literal_objects=6,observed_pages=17,State_bytes=3504,original_sequences=6,original_phases=168,native_sequences=12,native_phases=336,source_events_checked=4764,whole_State_comparisons=672,independent_control_scenarios=34,independent_control_attempts=68,compiled_assertions=checks,SPI_causal_corruption_rejections=216,controls=control_rows,receipts=FACTS,elapsed_seconds=time.perf_counter()-start,physical_dependencies=len(PINS),files=PINS,per_phase_reseed=False,direct_strict_archives=True,historical_suites_reexecuted=False,full_CRT_initialization=False,original_DLL_attach=False,native_window_menu=False,native_Training=False,whole_M4_complete=False,limits=['Actual finite desktop/work-area responses; serial flat DF=0 empty guest x87 domain','Original API volatile fields preserved and carried within each branch; native representatives constrained to selected suffix with no consumers','Prior27 measured numerical oracle policy retained; no new BEFORE-only FP proof','Host claim is outside Context invocation: legacyENV28/raw80/CW/SW/FTW/MXCSR/nativeXMM6..15/LastError; no volatileSIMD claim','Observer storage remains present in the authorized harness; standalone Session calls are not this acceptance scope'])
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=PINS|{str(out/'report.json'):sha(out/'report.json')}),indent=2)+'\n');print(json.dumps(dict(passed=passed,connected_roots=report['connected_roots'],physical_dependencies=len(PINS),sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
